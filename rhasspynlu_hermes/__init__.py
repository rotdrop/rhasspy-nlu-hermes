"""MQTT Rhasspy"""
import json
import logging
import typing

import attr
import networkx as nx

from rhasspyhermes.base import Message
from rhasspyhermes.nlu import NluQuery, NluIntent, NluIntentNotRecognized, NluError
from rhasspyhermes.intent import Intent, Slot, SlotRange

from rhasspynlu import recognize, Sentence

_LOGGER = logging.getLogger(__name__)


class NluHermesMqtt:
    def __init__(
        self,
        client,
        graph: nx.DiGraph,
        default_entities: typing.Dict[str, typing.Iterable[Sentence]] = None,
        siteId: str = "default",
    ):
        self.client = client
        self.graph = graph
        self.default_entities = default_entities or {}
        self.siteId = siteId

    # -------------------------------------------------------------------------

    def handle_query(self, query: NluQuery):
        recognitions = recognize(query.input, self.graph)
        if recognitions:
            # Recognized

            # Use first recognition only.
            # TODO: Add alternatives.
            recognition = recognitions[0]

            self.publish(
                NluIntent(
                    input=query.input,
                    id=query.id,
                    sessionId=query.sessionId,
                    intent=Intent(
                        intentName=recognition.intent.name,
                        confidenceScore=recognition.confidence,
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
                        for e in recognition.intent.entities
                    ],
                ),
                intent_name=recognition.intent.name,
            )
        else:
            # Not recognized
            self.publish(
                NluIntentNotRecognized(
                    input=query.input, id=query.id, sessionId=query.sessionId
                )
            )

    # -------------------------------------------------------------------------

    def on_connect(self, client, userdata, flags, rc):
        try:
            topics = [NluQuery.TOPIC]
            for topic in topics:
                self.client.subscribe(topic)
                _LOGGER.debug("Subscribed to %s", topic)
        except Exception:
            _LOGGER.exception("on_connect")

    def on_message(self, client, userdata, msg):
        try:
            _LOGGER.debug("Received %s byte(s) on %s", len(msg.payload), msg.topic)
            if msg.topic == NluQuery.TOPIC:
                json_payload = json.loads(msg.payload)

                # Check siteId
                payload_siteId = json_payload.get("siteId", "default")
                if payload_siteId != self.siteId:
                    _LOGGER.debug(
                        "Discarding query for site %s (not %s)",
                        payload_siteId,
                        self.siteId,
                    )
                    return

                try:
                    query = NluQuery(**json_payload)
                    _LOGGER.debug("<- %s", query)
                    self.handle_query(query)
                except Exception as e:
                    _LOGGER.exception("nlu query")
                    self.publish(
                        NluError(
                            sessionId=json_payload.get("sessionId", ""),
                            error=str(e),
                            context="",
                        )
                    )
        except Exception:
            _LOGGER.exception("on_message")

    def publish(self, message: Message, **topic_args):
        try:
            _LOGGER.debug("-> %s", message)
            topic = message.topic(**topic_args)
            payload = json.dumps(attr.asdict(message))
            _LOGGER.debug("Publishing %s char(s) to %s", len(payload), topic)
            self.client.publish(topic, payload)
        except Exception:
            _LOGGER.exception("on_message")
