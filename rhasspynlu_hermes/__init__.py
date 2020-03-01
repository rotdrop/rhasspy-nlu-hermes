"""Hermes MQTT server for Rhasspy NLU"""
import json
import logging
import typing
from pathlib import Path

import attr
import networkx as nx
import rhasspynlu
from rhasspyhermes.base import Message
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

_LOGGER = logging.getLogger(__name__)


class NluHermesMqtt:
    """Hermes MQTT server for Rhasspy NLU."""

    def __init__(
        self,
        client,
        intent_graph: typing.Optional[nx.DiGraph] = None,
        graph_path: typing.Optional[Path] = None,
        write_graph: bool = False,
        default_entities: typing.Dict[str, typing.Iterable[Sentence]] = None,
        word_transform: typing.Optional[typing.Callable[[str], str]] = None,
        siteIds: typing.Optional[typing.List[str]] = None,
    ):
        self.client = client
        self.graph_path = graph_path
        self.intent_graph = intent_graph
        self.write_graph = write_graph
        self.default_entities = default_entities or {}
        self.word_transform = word_transform
        self.siteIds = siteIds or []

    # -------------------------------------------------------------------------

    def handle_query(self, query: NluQuery):
        """Do intent recognition."""
        if not self.intent_graph and self.graph_path and self.graph_path.is_file():
            # Load graph from file
            with open(self.graph_path, "r") as graph_file:
                self.intent_graph = rhasspynlu.json_to_graph(json.load(graph_file))

        if self.intent_graph:

            def intent_filter(intent_name: str) -> bool:
                """Filter out intents."""
                if query.intentFilter:
                    return intent_name in query.intentFilter
                return True

            input_text = query.input

            # Fix casing for outpu event
            if self.word_transform:
                input_text = self.word_transform(input_text)

            # Pass in raw query input so raw values will be correct
            recognitions = recognize(
                query.input,
                self.intent_graph,
                intent_filter=intent_filter,
                word_transform=self.word_transform,
            )
        else:
            _LOGGER.error("No intent graph loaded")
            recognitions = []

        if recognitions:
            # Use first recognition only.
            recognition = recognitions[0]
            assert recognition is not None
            assert recognition.intent is not None

            # intentParsed
            self.publish(
                NluIntentParsed(
                    input=input_text,
                    id=query.id,
                    siteId=query.siteId,
                    sessionId=query.sessionId,
                    intent=Intent(
                        intentName=recognition.intent.name,
                        confidenceScore=recognition.intent.confidence,
                    ),
                    slots=[
                        Slot(
                            entity=e.entity,
                            slotName=e.entity,
                            confidence=1,
                            value=e.value,
                            raw_value=e.raw_value,
                            range=SlotRange(start=e.raw_start, end=e.raw_end),
                        )
                        for e in recognition.entities
                    ],
                )
            )

            # intent
            self.publish(
                NluIntent(
                    input=input_text,
                    id=query.id,
                    siteId=query.siteId,
                    sessionId=query.sessionId,
                    intent=Intent(
                        intentName=recognition.intent.name,
                        confidenceScore=recognition.intent.confidence,
                    ),
                    slots=[
                        Slot(
                            entity=e.entity,
                            slotName=e.entity,
                            confidence=1,
                            value=e.value,
                            raw_value=e.raw_value,
                            range=SlotRange(start=e.raw_start, end=e.raw_end),
                        )
                        for e in recognition.entities
                    ],
                    asrTokens=query.input.split(),
                ),
                intentName=recognition.intent.name,
            )
        else:
            # Not recognized
            self.publish(
                NluIntentNotRecognized(
                    input=query.input,
                    id=query.id,
                    siteId=query.siteId,
                    sessionId=query.sessionId,
                )
            )

    # -------------------------------------------------------------------------

    def handle_train(
        self, train: NluTrain, siteId: str = "default"
    ) -> typing.Union[NluTrainSuccess, NluError]:
        """Transform sentences to intent graph"""
        _LOGGER.debug("<- %s(%s)", train.__class__.__name__, train.id)

        try:
            self.intent_graph = rhasspynlu.json_to_graph(train.graph_dict)

            if self.graph_path:
                # Write graph as JSON
                with open(self.graph_path, "w") as graph_file:
                    json.dump(train.graph_dict, graph_file)

                    _LOGGER.debug("Wrote %s", str(self.graph_path))

            return NluTrainSuccess(id=train.id)
        except Exception as e:
            return NluError(siteId=siteId, error=str(e), context=train.id)

    # -------------------------------------------------------------------------

    def on_connect(self, client, userdata, flags, rc):
        """Connected to MQTT broker."""
        try:
            topics = [NluQuery.topic()]

            if self.siteIds:
                # Specific siteIds
                topics.extend(
                    [NluTrain.topic(siteId=siteId) for siteId in self.siteIds]
                )
            else:
                # All siteIds
                topics.append(NluTrain.topic(siteId="+"))

            for topic in topics:
                self.client.subscribe(topic)
                _LOGGER.debug("Subscribed to %s", topic)
        except Exception:
            _LOGGER.exception("on_connect")

    def on_message(self, client, userdata, msg):
        """Received message from MQTT broker."""
        try:
            _LOGGER.debug("Received %s byte(s) on %s", len(msg.payload), msg.topic)
            if msg.topic == NluQuery.topic():
                json_payload = json.loads(msg.payload)

                # Check siteId
                if not self._check_siteId(json_payload):
                    return

                try:
                    query = NluQuery(**json_payload)
                    _LOGGER.debug("<- %s", query)
                    self.handle_query(query)
                except Exception as e:
                    _LOGGER.exception("nlu query")
                    self.publish(
                        NluError(
                            siteId=query.siteId,
                            sessionId=json_payload.get("sessionId", ""),
                            error=str(e),
                            context="",
                        )
                    )
            elif NluTrain.is_topic(msg.topic):
                siteId = NluTrain.get_siteId(msg.topic)
                if self.siteIds and (siteId not in self.siteIds):
                    return

                json_payload = json.loads(msg.payload)
                train = NluTrain(**json_payload)
                result = self.handle_train(train)
                self.publish(result)
        except Exception:
            _LOGGER.exception("on_message")

    def publish(self, message: Message, **topic_args):
        """Publish a Hermes message to MQTT."""
        try:
            _LOGGER.debug("-> %s", message)
            topic = message.topic(**topic_args)
            payload = json.dumps(attr.asdict(message))
            _LOGGER.debug("Publishing %s char(s) to %s", len(payload), topic)
            self.client.publish(topic, payload)
        except Exception:
            _LOGGER.exception("on_message")

    # -------------------------------------------------------------------------

    def _check_siteId(self, json_payload: typing.Dict[str, typing.Any]) -> bool:
        if self.siteIds:
            return json_payload.get("siteId", "default") in self.siteIds

        # All sites
        return True
