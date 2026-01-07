"""
CONTRACT REGISTRY
The Single Source of Truth for SDK <-> API Contract mapping.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Type, Optional, Callable, Any

# SDK Models
from magick_mind.models.v1.chat import ChatSendResponse, ChatSendRequest
from magick_mind.models.v1.artifact import (
    FinalizeArtifactResponse,
    PresignArtifactResponse,
    PresignArtifactRequest,
    FinalizeArtifactRequest,
)
from magick_mind.models.v1.project import (
    CreateProjectResponse,
    UpdateProjectResponse,
    GetProjectResponse,
    GetProjectListResponse,
    CreateProjectRequest,
    UpdateProjectRequest,
)
from magick_mind.models.v1.api_keys import (
    UpdateApiKeyResponse,
    CreateApiKeyResponse,
    ListApiKeysResponse,
    DeleteApiKeyResponse,
    CreateApiKeyRequest,
    UpdateApiKeyRequest,
    DeleteApiKeyRequest,
)
from magick_mind.models.v1.corpus import (
    CreateCorpusResponse,
    GetCorpusResponse,
    ListCorpusResponse,
    UpdateCorpusResponse,
    CreateCorpusRequest,
    UpdateCorpusRequest,
)
from magick_mind.models.v1.end_user import (
    CreateEndUserResponse,
    GetEndUserResponse,
    QueryEndUserResponse,
    UpdateEndUserResponse,
    CreateEndUserRequest,
    UpdateEndUserRequest,
)
from magick_mind.models.v1.mindspace import (
    CreateMindSpaceResponse,
    GetMindSpaceListResponse,
    UpdateMindSpaceResponse,
    CreateMindSpaceRequest,
    UpdateMindSpaceRequest,
)
from magick_mind.models.v1.history import HistoryResponse
from magick_mind.models.auth import TokenResponse, LoginRequest, RefreshRequest


class SchemaStatus(Enum):
    TESTED = "tested"
    SKIPPED = "skipped"


@dataclass
class ContractDef:
    schema_name: str
    model: Optional[Type] = None
    status: SchemaStatus = SchemaStatus.TESTED
    reason: str = ""
    factory: Optional[Callable[[], Any]] = None

    def __post_init__(self):
        # Auto-skip if no model provided (Safety net)
        if self.model is None and self.status == SchemaStatus.TESTED:
            self.status = SchemaStatus.SKIPPED
            if not self.reason:
                self.reason = "Auto-skipped: No SDK Model"


# =============================================================================
# FACTORIES (Requests Only)
# =============================================================================


def _chat_request_factory() -> ChatSendRequest:
    return ChatSendRequest(
        api_key="sk-test",
        mindspace_id="ms-1",
        message="hello",
        enduser_id="u-1",
        fast_brain_model_id="gpt-4",
        model_ids=["gpt-4"],
    )


def _create_project_factory() -> CreateProjectRequest:
    return CreateProjectRequest(name="Test Project", api_key="sk-test")


def _update_project_factory() -> UpdateProjectRequest:
    return UpdateProjectRequest(name="Updated Project")


def _create_corpus_factory() -> CreateCorpusRequest:
    return CreateCorpusRequest(name="Test Corpus", project_id="proj-1")


def _update_corpus_factory() -> UpdateCorpusRequest:
    return UpdateCorpusRequest(name="Updated Corpus")


def _create_end_user_factory() -> CreateEndUserRequest:
    return CreateEndUserRequest(external_id="ext-123", name="Test User")


def _update_end_user_factory() -> UpdateEndUserRequest:
    return UpdateEndUserRequest(name="Updated User")


def _create_mindspace_factory() -> CreateMindSpaceRequest:
    return CreateMindSpaceRequest(
        project_id="proj-1",
        name="Test MindSpace",
        type="PRIVATE",
    )


def _update_mindspace_factory() -> UpdateMindSpaceRequest:
    return UpdateMindSpaceRequest(name="Updated MindSpace")


def _create_api_key_factory() -> CreateApiKeyRequest:
    return CreateApiKeyRequest(project_id="proj-1", key_alias="Test Key")


def _update_api_key_factory() -> UpdateApiKeyRequest:
    return UpdateApiKeyRequest(key_alias="Updated Key")


def _delete_api_key_factory() -> DeleteApiKeyRequest:
    return DeleteApiKeyRequest(key_id="key-1")


def _presign_artifact_factory() -> PresignArtifactRequest:
    return PresignArtifactRequest(
        filename="test.pdf",
        content_type="application/pdf",
        project_id="proj-1",
    )


def _finalize_artifact_factory() -> FinalizeArtifactRequest:
    return FinalizeArtifactRequest(
        artifact_id="art-1",
        s3_key="uploads/test.pdf",
    )


def _login_request_factory() -> LoginRequest:
    return LoginRequest(email="test@example.com", password="password123")


def _refresh_request_factory() -> RefreshRequest:
    return RefreshRequest(refresh_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")


# =============================================================================
# RESPONSES
# =============================================================================
RESPONSES = [
    # --- TESTED (The "Green" List) ---
    # Chat
    ContractDef("ChatResp", ChatSendResponse),
    # Artifact
    ContractDef("ClientFinalizeArtifactUploadResp", FinalizeArtifactResponse),
    ContractDef("GenericPresignResp", PresignArtifactResponse),
    ContractDef("PresignArtifactUploadResp", PresignArtifactResponse),
    # Project
    ContractDef("CreateProjectResp", CreateProjectResponse),
    ContractDef("UpdateProjectResp", UpdateProjectResponse),
    ContractDef("GetProjectByIdResp", GetProjectResponse),
    ContractDef("GetProjectListResp", GetProjectListResponse),
    # API Keys
    ContractDef("UpdateApiKeyResp", UpdateApiKeyResponse),
    ContractDef("CreateApiKeyResp", CreateApiKeyResponse),
    ContractDef("GetApiKeyListResp", ListApiKeysResponse),
    ContractDef("DeleteApiKeyResp", DeleteApiKeyResponse),
    # Corpus
    ContractDef("CreateCorpusRes", CreateCorpusResponse),
    ContractDef("GetCorpusByIdRes", GetCorpusResponse),
    ContractDef("GetCorpusListRes", ListCorpusResponse),
    ContractDef("UpdateCorpusRes", UpdateCorpusResponse),
    # End User
    ContractDef("CreateEndUserResp", CreateEndUserResponse),
    ContractDef("GetEndUserByIdResp", GetEndUserResponse),
    ContractDef("QueryEndUserResp", QueryEndUserResponse),
    ContractDef("UpdateEndUserResp", UpdateEndUserResponse),
    # History
    ContractDef("MindspaceMessagesResp", HistoryResponse),
    # MindSpace (spec mismatches - tests will fail and expose bugs)
    ContractDef("CreateMindSpaceResp", CreateMindSpaceResponse),
    ContractDef("GetMindSpaceListResp", GetMindSpaceListResponse),
    ContractDef("UpdateMindSpaceResp", UpdateMindSpaceResponse),
    # Auth
    ContractDef("LoginResp", TokenResponse),
    ContractDef("RefreshResp", TokenResponse),
    # --- INTENTIONAL SKIPS (Internal/Irrelevant) ---
    ContractDef("BaseResponse", status=SchemaStatus.SKIPPED, reason="Generic Base"),
    ContractDef(
        "ArtifactWebhookResp", status=SchemaStatus.SKIPPED, reason="Internal Webhook"
    ),
]

# =============================================================================
# REQUESTS
# =============================================================================
REQUESTS = [
    # --- TESTED ---
    # Chat
    ContractDef("ChatReq", ChatSendRequest, factory=_chat_request_factory),
    # Project
    ContractDef(
        "CreateProjectReq", CreateProjectRequest, factory=_create_project_factory
    ),
    ContractDef(
        "UpdateProjectReq", UpdateProjectRequest, factory=_update_project_factory
    ),
    # Corpus
    ContractDef("CreateCorpusReq", CreateCorpusRequest, factory=_create_corpus_factory),
    ContractDef("UpdateCorpusReq", UpdateCorpusRequest, factory=_update_corpus_factory),
    # End User
    ContractDef(
        "CreateEndUserReq", CreateEndUserRequest, factory=_create_end_user_factory
    ),
    ContractDef(
        "UpdateEndUserReq", UpdateEndUserRequest, factory=_update_end_user_factory
    ),
    # MindSpace
    ContractDef(
        "CreateMindSpaceReq", CreateMindSpaceRequest, factory=_create_mindspace_factory
    ),
    ContractDef(
        "UpdateMindSpaceReq", UpdateMindSpaceRequest, factory=_update_mindspace_factory
    ),
    # API Keys
    ContractDef(
        "CreateApiKeyReq", CreateApiKeyRequest, factory=_create_api_key_factory
    ),
    ContractDef(
        "UpdateApiKeyReq", UpdateApiKeyRequest, factory=_update_api_key_factory
    ),
    ContractDef(
        "DeleteApiKeyReq", DeleteApiKeyRequest, factory=_delete_api_key_factory
    ),
    # Artifact
    ContractDef(
        "GenericPresignReq", PresignArtifactRequest, factory=_presign_artifact_factory
    ),
    ContractDef(
        "PresignArtifactUploadReq",
        PresignArtifactRequest,
        factory=_presign_artifact_factory,
    ),
    ContractDef(
        "ClientFinalizeArtifactUploadReq",
        FinalizeArtifactRequest,
        factory=_finalize_artifact_factory,
    ),
    # Auth
    ContractDef("LoginReq", LoginRequest, factory=_login_request_factory),
    ContractDef("RefreshReq", RefreshRequest, factory=_refresh_request_factory),
    # --- INTENTIONAL SKIPS ---
    # Internal/RPC
    ContractDef(
        "ArtifactWebhookReq", status=SchemaStatus.SKIPPED, reason="Internal Webhook"
    ),
    ContractDef(
        "CentrifugoRpcRequest", status=SchemaStatus.SKIPPED, reason="Internal RPC"
    ),
    ContractDef(
        "CustomSubscribeRequest", status=SchemaStatus.SKIPPED, reason="Internal RPC"
    ),
    ContractDef(
        "CustomUnsubscribeRequest", status=SchemaStatus.SKIPPED, reason="Internal RPC"
    ),
    ContractDef(
        "ChatCompletionsReq", status=SchemaStatus.SKIPPED, reason="OpenAI Compat Layer"
    ),
    # Path Param Only (no JSON body)
    ContractDef(
        "GetCorpusByIdReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "DeleteCorpusReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "GetEndUserByIdReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "DeleteEndUserReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "GetMindSpaceByIdReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "GetMindSpaceListReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "DeleteMindSpaceReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "GetProjectByIdReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "GetProjectListReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "DeleteProjectReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "GetApiKeyListReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "MindspaceMessagesReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
    ContractDef(
        "QueryEndUserReq", status=SchemaStatus.SKIPPED, reason="Path Param Only"
    ),
]

# =============================================================================
# SHARED MODELS (Components)
# =============================================================================
SHARED_MODELS = [
    ContractDef("ApiKeySchema", status=SchemaStatus.SKIPPED, reason="Component"),
]


# =============================================================================
# HELPERS - Used by tests
# =============================================================================


def get_tested_responses():
    return [
        (r.model, r.schema_name) for r in RESPONSES if r.status == SchemaStatus.TESTED
    ]


def get_tested_requests():
    return [r for r in REQUESTS if r.status == SchemaStatus.TESTED]


def get_skipped_schemas():
    all_defs = RESPONSES + REQUESTS + SHARED_MODELS
    return {
        r.schema_name: r.reason for r in all_defs if r.status == SchemaStatus.SKIPPED
    }
