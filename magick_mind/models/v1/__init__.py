"""V1 API models."""

from magick_mind.models.v1.chat import ChatPayload, ChatSendRequest, ChatSendResponse
from magick_mind.models.v1.history import ChatHistoryMessage, HistoryResponse
from magick_mind.models.v1.project import (
    CreateProjectRequest,
    CreateProjectResponse,
    GetProjectListResponse,
    GetProjectResponse,
    Project,
    UpdateProjectRequest,
    UpdateProjectResponse,
)

__all__ = [
    "ChatSendRequest",
    "ChatPayload",
    "ChatSendResponse",
    "ChatHistoryMessage",
    "HistoryResponse",
    "Project",
    "CreateProjectRequest",
    "CreateProjectResponse",
    "GetProjectResponse",
    "GetProjectListResponse",
    "UpdateProjectRequest",
    "UpdateProjectResponse",
]
