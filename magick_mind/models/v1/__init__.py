"""V1 API models."""

from magick_mind.models.v1.artifact import (
    Artifact,
    ArtifactWebhookPayload,
    DeleteArtifactResponse,
    FinalizeArtifactRequest,
    FinalizeArtifactResponse,
    GetArtifactResponse,
    ListArtifactsResponse,
    PresignArtifactRequest,
    PresignArtifactResponse,
)
from magick_mind.models.v1.chat import ChatPayload, ChatSendRequest, ChatSendResponse
from magick_mind.models.v1.corpus import (
    Corpus,
    CreateCorpusRequest,
    ListCorpusResponse,
    UpdateCorpusRequest,
)
from magick_mind.models.v1.end_user import (
    CreateEndUserRequest,
    EndUser,
    QueryEndUserResponse,
    UpdateEndUserRequest,
)
from magick_mind.models.v1.history import ChatHistoryMessage, HistoryResponse
from magick_mind.models.v1.api_keys import (
    ApiKey,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    DeleteApiKeyResponse,
    KeyResponse,
    ListApiKeysResponse,
    UpdateApiKeyRequest,
    UpdateApiKeyResponse,
)
from magick_mind.models.v1.project import (
    CreateProjectRequest,
    GetProjectListResponse,
    Project,
    UpdateProjectRequest,
)
from magick_mind.models.v1.model import Model, ModelsListResponse


__all__ = [
    "ChatSendRequest",
    "ChatPayload",
    "ChatSendResponse",
    "ChatHistoryMessage",
    "HistoryResponse",
    "Project",
    "CreateProjectRequest",
    "GetProjectListResponse",
    "EndUser",
    "CreateEndUserRequest",
    "QueryEndUserResponse",
    "UpdateEndUserRequest",
    "Artifact",
    "PresignArtifactRequest",
    "PresignArtifactResponse",
    "GetArtifactResponse",
    "ListArtifactsResponse",
    "DeleteArtifactResponse",
    "FinalizeArtifactRequest",
    "FinalizeArtifactResponse",
    "ArtifactWebhookPayload",
    "Corpus",
    "CreateCorpusRequest",
    "ListCorpusResponse",
    "UpdateCorpusRequest",
    "ApiKey",
    "KeyResponse",
    "CreateApiKeyRequest",
    "CreateApiKeyResponse",
    "ListApiKeysResponse",
    "UpdateApiKeyRequest",
    "UpdateApiKeyResponse",
    "DeleteApiKeyResponse",
    "Model",
    "ModelsListResponse",
]
