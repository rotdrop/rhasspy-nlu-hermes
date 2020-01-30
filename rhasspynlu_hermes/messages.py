"""Provisional Hermes messages for NLU"""
import re
import typing

import attr
from rhasspyhermes.base import Message


@attr.s(auto_attribs=True, slots=True)
class NluTrain(Message):
    """Request to retrain from sentences"""

    TOPIC_PATTERN = re.compile(r"^hermes/nlu/([^/]+)/train$")

    id: str
    sentences: str

    @classmethod
    def topic(cls, **kwargs) -> str:
        siteId = kwargs.get("siteId", "default")
        return f"hermes/nlu/{siteId}/train"

    @classmethod
    def is_topic(cls, topic: str) -> bool:
        """True if topic matches template"""
        return re.match(NluTrain.TOPIC_PATTERN, topic) is not None

    @classmethod
    def get_siteId(cls, topic: str) -> str:
        """Get siteId from a topic"""
        match = re.match(NluTrain.TOPIC_PATTERN, topic)
        assert match, "Not a train topic"
        return match.group(1)


@attr.s(auto_attribs=True, slots=True)
class NluTrainSuccess(Message):
    """Result from successful training"""

    TOPIC_PATTERN = re.compile(r"^hermes/nlu/([^/]+)/trainSuccess$")

    id: str
    graph_dict: typing.Dict[str, typing.Any]

    @classmethod
    def topic(cls, **kwargs) -> str:
        siteId = kwargs.get("siteId", "default")
        return f"hermes/nlu/{siteId}/trainSuccess"

    @classmethod
    def is_topic(cls, topic: str) -> bool:
        """True if topic matches template"""
        return re.match(NluTrainSuccess.TOPIC_PATTERN, topic) is not None

    @classmethod
    def get_siteId(cls, topic: str) -> str:
        """Get siteId from a topic"""
        match = re.match(NluTrainSuccess.TOPIC_PATTERN, topic)
        assert match, "Not a trainSuccess topic"
        return match.group(1)
