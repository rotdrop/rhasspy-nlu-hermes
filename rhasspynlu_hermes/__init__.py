"""Hermes MQTT server for Rhasspy NLU"""
import asyncio
import logging
import typing
from pathlib import Path

import networkx as nx
import rhasspynlu
from rhasspyhermes.base import Message
from rhasspyhermes.client import GeneratorType, HermesClient, TopicArgs
from rhasspyhermes.intent import Intent, Slot, SlotRange
from rhasspyhermes.nlu import (
    NluError,
    NluIntent,
    NluIntentNotRecognized,
    NluIntentParsed,
    NluQuery,
    NluTrain,
    NluTrainSuccess,
)
from rhasspynlu import Sentence, recognize

_LOGGER = logging.getLogger("rhasspynlu_hermes")

# -----------------------------------------------------------------------------


class NluHermesMqtt(HermesClient):
    """Hermes MQTT server for Rhasspy NLU."""

    def __init__(
        self,
        client,
        intent_graph: typing.Optional[nx.DiGraph] = None,
        graph_path: typing.Optional[Path] = None,
        default_entities: typing.Dict[str, typing.Iterable[Sentence]] = None,
        word_transform: typing.Optional[typing.Callable[[str], str]] = None,
        fuzzy: bool = True,
        replace_numbers: bool = False,
        language: typing.Optional[str] = None,
        siteIds: typing.Optional[typing.List[str]] = None,
        loop=None,
    ):
        super().__init__("rhasspynlu_hermes", client, siteIds=siteIds, loop=loop)

        self.subscribe(NluQuery, NluTrain)

        self.graph_path = graph_path
        self.intent_graph = intent_graph
        self.default_entities = default_entities or {}
        self.word_transform = word_transform
        self.fuzzy = fuzzy
        self.replace_numbers = replace_numbers
        self.language = language

        # Event loop
        self.loop = loop or asyncio.get_event_loop()

    # -------------------------------------------------------------------------

    async def handle_query(
        self, query: NluQuery
    ) -> typing.AsyncIterable[
        typing.Union[
            NluIntentParsed,
            typing.Tuple[NluIntent, TopicArgs],
            NluIntentNotRecognized,
            NluError,
        ]
    ]:
        """Do intent recognition."""
        try:
            if not self.intent_graph and self.graph_path and self.graph_path.is_file():
                # Load graph from file
                _LOGGER.debug("Loading %s", self.graph_path)
                with open(self.graph_path, mode="rb") as graph_file:
                    self.intent_graph = rhasspynlu.gzip_pickle_to_graph(graph_file)

            if self.intent_graph:

                def intent_filter(intent_name: str) -> bool:
                    """Filter out intents."""
                    if query.intentFilter:
                        return intent_name in query.intentFilter
                    return True

                original_input = query.input

                # Replace digits with words
                if self.replace_numbers:
                    # Have to assume whitespace tokenization
                    words = rhasspynlu.replace_numbers(
                        query.input.split(), self.language
                    )
                    query.input = " ".join(words)

                input_text = query.input

                # Fix casing for output event
                if self.word_transform:
                    input_text = self.word_transform(input_text)

                # Pass in raw query input so raw values will be correct
                recognitions = recognize(
                    query.input,
                    self.intent_graph,
                    intent_filter=intent_filter,
                    word_transform=self.word_transform,
                    fuzzy=self.fuzzy,
                )
            else:
                _LOGGER.error("No intent graph loaded")
                recognitions = []

            if recognitions:
                # Use first recognition only.
                recognition = recognitions[0]
                assert recognition is not None
                assert recognition.intent is not None

                intent = Intent(
                    intentName=recognition.intent.name,
                    confidenceScore=recognition.intent.confidence,
                )
                slots = [
                    Slot(
                        entity=e.entity,
                        slotName=e.entity,
                        confidence=1.0,
                        value=e.value,
                        raw_value=e.raw_value,
                        range=SlotRange(
                            start=e.start,
                            end=e.end,
                            raw_start=e.raw_start,
                            raw_end=e.raw_end,
                        ),
                    )
                    for e in recognition.entities
                ]

                # intentParsed
                yield NluIntentParsed(
                    input=recognition.text,
                    id=query.id,
                    siteId=query.siteId,
                    sessionId=query.sessionId,
                    intent=intent,
                    slots=slots,
                )

                # intent
                yield (
                    NluIntent(
                        input=recognition.text,
                        id=query.id,
                        siteId=query.siteId,
                        sessionId=query.sessionId,
                        intent=intent,
                        slots=slots,
                        asrTokens=recognition.tokens,
                        rawAsrTokens=original_input.split(),
                        wakewordId=query.wakewordId,
                    ),
                    {"intentName": recognition.intent.name},
                )
            else:
                # Not recognized
                yield NluIntentNotRecognized(
                    input=query.input,
                    id=query.id,
                    siteId=query.siteId,
                    sessionId=query.sessionId,
                )
        except Exception as e:
            yield NluError(
                siteId=query.siteId,
                sessionId=query.sessionId,
                error=str(e),
                context=original_input,
            )

    # -------------------------------------------------------------------------

    async def handle_train(
        self, train: NluTrain, siteId: str = "default"
    ) -> typing.AsyncIterable[
        typing.Union[typing.Tuple[NluTrainSuccess, TopicArgs], NluError]
    ]:
        """Transform sentences to intent graph"""
        try:
            _LOGGER.debug("Loading %s", train.graph_path)
            with open(train.graph_path, mode="rb") as graph_file:
                self.intent_graph = rhasspynlu.gzip_pickle_to_graph(graph_file)

            yield (NluTrainSuccess(id=train.id), {"siteId": siteId})
        except Exception as e:
            yield NluError(
                siteId=siteId, sessionId=train.id, error=str(e), context=train.id
            )

    # -------------------------------------------------------------------------

    async def on_message(
        self,
        message: Message,
        siteId: typing.Optional[str] = None,
        sessionId: typing.Optional[str] = None,
        topic: typing.Optional[str] = None,
    ) -> GeneratorType:
        """Received message from MQTT broker."""
        if isinstance(message, NluQuery):
            async for query_result in self.handle_query(message):
                yield query_result
        elif isinstance(message, NluTrain):
            assert siteId, "Missing siteId"
            async for train_result in self.handle_train(message, siteId=siteId):
                yield train_result
        else:
            _LOGGER.warning("Unexpected message: %s", message)
