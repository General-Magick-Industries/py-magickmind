"""V1 API models."""

from magick_mind.models.v1.chat import ChatPayload, ChatSendRequest, ChatSendResponse
from magick_mind.models.v1.history import ChatHistoryMessage, HistoryResponse

__all__ = [
    "ChatSendRequest",
    "ChatPayload",
    "ChatSendResponse",
    "ChatHistoryMessage",
    "HistoryResponse",
]
