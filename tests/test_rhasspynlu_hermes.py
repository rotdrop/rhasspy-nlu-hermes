"""Unit tests for rhasspynlu_hermes"""
import json
import unittest
import uuid
from unittest.mock import MagicMock, Mock

from rhasspyhermes.intent import Intent, Slot, SlotRange
from rhasspyhermes.nlu import NluIntent, NluIntentNotRecognized, NluQuery
from rhasspynlu import intents_to_graph, parse_ini

from rhasspynlu_hermes import NluHermesMqtt


class RhasspyNluHermesTestCase(unittest.TestCase):
    """Tests for rhasspynlu_hermes"""

    def setUp(self):
        self.siteId = str(uuid.uuid4())
        self.sessionId = str(uuid.uuid4())

        ini_text = """
        [SetLightColor]
        set the (bedroom | living room){name} light to (red | green | blue){color}
        """

        self.graph = intents_to_graph(parse_ini(ini_text))
        self.client = MagicMock()
        self.hermes = NluHermesMqtt(self.client, self.graph, siteIds=[self.siteId])

    def test_subscribe(self):
        """Verify topic subscriptions."""
        self.hermes.on_connect(self.client, None, None, None)

        for topic in ["hermes/nlu/query", f"rhasspy/nlu/{self.siteId}/train"]:
            self.client.subscribe.assert_any_call(topic)

    def test_handle_query(self):
        """Verify valid input leads to a query message."""
        query_id = str(uuid.uuid4())
        text = "set the bedroom light to red"

        self.hermes.handle_query = MagicMock()
        self.hermes.on_message(
            self.client,
            None,
            Mock(
                topic="hermes/nlu/query",
                payload=json.dumps(
                    {
                        "input": text,
                        "id": query_id,
                        "siteId": self.siteId,
                        "sessionId": self.sessionId,
                    }
                ),
            ),
        )

        self.hermes.handle_query.assert_called_with(
            NluQuery(
                input=text, id=query_id, siteId=self.siteId, sessionId=self.sessionId
            )
        )

    def test_handle_query_wrong_site(self):
        """Verify query with wrong site id is discarded."""
        wrong_siteId = str(uuid.uuid4())
        query_id = str(uuid.uuid4())
        text = "set the bedroom light to red"

        self.hermes.handle_query = MagicMock()
        self.hermes.on_message(
            self.client,
            None,
            Mock(
                topic="hermes/nlu/query",
                payload=json.dumps(
                    {
                        "input": text,
                        "id": query_id,
                        "siteId": wrong_siteId,
                        "sessionId": self.sessionId,
                    }
                ),
            ),
        )

        self.hermes.handle_query.assert_not_called()

    def test_recognized(self):
        """Verify valid input leads to a recognition."""
        query_id = str(uuid.uuid4())
        text = "set the bedroom light to red"

        self.hermes.publish = MagicMock()
        self.hermes.handle_query(
            NluQuery(
                input=text, id=query_id, siteId=self.siteId, sessionId=self.sessionId
            )
        )

        self.hermes.publish.assert_called_with(
            NluIntent(
                input=text,
                id=query_id,
                intent=Intent(intentName="SetLightColor", confidenceScore=1.0),
                slots=[
                    Slot(
                        entity="name",
                        slotName="name",
                        value="bedroom",
                        raw_value="bedroom",
                        confidence=1,
                        range=SlotRange(8, 15),
                    ),
                    Slot(
                        entity="color",
                        slotName="color",
                        value="red",
                        raw_value="red",
                        confidence=1,
                        range=SlotRange(25, 28),
                    ),
                ],
                siteId=self.siteId,
                sessionId=self.sessionId,
            ),
            intentName="SetLightColor",
        )

    def test_not_recognized(self):
        """Verify invalid input leads to a not recognized error."""
        text = "set the garage light to red"
        self.hermes.publish = MagicMock()
        self.hermes.handle_query(
            NluQuery(input=text, siteId=self.siteId, sessionId=self.sessionId)
        )

        self.hermes.publish.assert_called_with(
            NluIntentNotRecognized(
                input=text, siteId=self.siteId, sessionId=self.sessionId
            )
        )
