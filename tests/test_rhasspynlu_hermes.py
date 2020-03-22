"""Unit tests for rhasspynlu_hermes"""
import asyncio
import json
import logging
import unittest
import uuid
from unittest.mock import MagicMock, Mock

from rhasspyhermes.intent import Intent, Slot, SlotRange
from rhasspyhermes.nlu import (
    NluIntent,
    NluIntentParsed,
    NluIntentNotRecognized,
    NluQuery,
)
from rhasspynlu import intents_to_graph, parse_ini

from rhasspynlu_hermes import NluHermesMqtt

_LOGGER = logging.getLogger(__name__)
_LOOP = asyncio.get_event_loop()


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
        self.hermes = NluHermesMqtt(
            self.client, self.graph, siteIds=[self.siteId], loop=_LOOP
        )

    def tearDown(self):
        self.hermes.stop()

    async def async_test_handle_query(self):
        """Verify valid input leads to a query message."""
        query_id = str(uuid.uuid4())
        text = "set the bedroom light to red"

        query = NluQuery(
            input=text, id=query_id, siteId=self.siteId, sessionId=self.sessionId
        )

        intent = Intent(intentName="SetLightColor", confidenceScore=1.0)
        slots = [
            Slot(
                entity="name",
                slotName="name",
                value="bedroom",
                raw_value="bedroom",
                confidence=1.0,
                range=SlotRange(start=8, end=15, raw_start=8, raw_end=15),
            ),
            Slot(
                entity="color",
                slotName="color",
                value="red",
                raw_value="red",
                confidence=1.0,
                range=SlotRange(start=25, end=28, raw_start=25, raw_end=28),
            ),
        ]

        results = []
        async for result in self.hermes.handle_query(query):
            results.append(result)

        self.assertEqual(
            results,
            [
                NluIntentParsed(
                    input=text,
                    id=query_id,
                    siteId=self.siteId,
                    sessionId=self.sessionId,
                    intent=intent,
                    slots=slots,
                ),
                (
                    NluIntent(
                        input=text,
                        id=query_id,
                        siteId=self.siteId,
                        sessionId=self.sessionId,
                        intent=intent,
                        slots=slots,
                        asrTokens=text.split(),
                        rawAsrTokens=text.split(),
                    ),
                    {"intentName": intent.intentName},
                ),
            ],
        )

    def test_handle_query(self):
        """Call async_test_handle_query."""
        _LOOP.run_until_complete(self.async_test_handle_query())
