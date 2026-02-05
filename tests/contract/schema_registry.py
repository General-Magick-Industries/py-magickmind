"""
CONTRACT REGISTRY
The Single Source of Truth for SDK <-> API Contract mapping.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Type, Optional, Callable, Any

# SDK Models
from magick_mind.models.v1.chat import ChatSendResponse, ChatSendRequest, ConfigSchema
from magick_mind.models.v1.artifact import (
    FinalizeArtifactResponse,
    PresignArtifactResponse,
    PresignArtifactRequest,
    FinalizeArtifactRequest,
)
from magick_mind.models.v1.project import (
    CreateProjectRequest,
    Project,
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
    Corpus,
    CreateCorpusRequest,
    UpdateCorpusRequest,
)
from magick_mind.models.v1.end_user import (
    EndUser,
    QueryEndUserResponse,
    CreateEndUserRequest,
    UpdateEndUserRequest,
)
from magick_mind.models.v1.mindspace import (
    MindSpace,
    GetMindSpaceListResponse,
    CreateMindSpaceRequest,
    UpdateMindSpaceRequest,
)
from magick_mind.models.v1.model import ModelsListResponse, Model
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
        config=ConfigSchema(
            fast_model_id="gpt-4",
            smart_model_ids=["gpt-4"],
            compute_power=50,
        ),
    )


def _create_project_factory() -> CreateProjectRequest:
    return CreateProjectRequest(
        name="Test Project",
        api_key="sk-test",
        description="Project Desc",
        corpus_ids=[],
    )


def _update_project_factory() -> UpdateProjectRequest:
    return UpdateProjectRequest(
        name="Updated Project", description="Updated Desc", corpus_ids=[]
    )


def _create_corpus_factory() -> CreateCorpusRequest:
    return CreateCorpusRequest(
        name="Test Corpus",
        project_id="proj-1",
        description="Corpus Desc",
        artifact_ids=[],
    )


def _update_corpus_factory() -> UpdateCorpusRequest:
    return UpdateCorpusRequest(
        name="Updated Corpus", description="Updated Desc", artifact_ids=[]
    )


def _create_end_user_factory() -> CreateEndUserRequest:
    return CreateEndUserRequest(
        external_id="ext-123", name="Test User", tenant_id="t-1", actor_id="a-1"
    )


def _update_end_user_factory() -> UpdateEndUserRequest:
    return UpdateEndUserRequest(
        name="Updated User", external_id="ext-456", tenant_id="t-1"
    )


def _create_mindspace_factory() -> CreateMindSpaceRequest:
    return CreateMindSpaceRequest(
        project_id="proj-1",
        name="Test MindSpace",
        type="PRIVATE",
        description="Mindspace Desc",
    )


def _update_mindspace_factory() -> UpdateMindSpaceRequest:
    return UpdateMindSpaceRequest(
        name="Updated MindSpace", description="Updated Desc", project_id="proj-1"
    )


def _create_api_key_factory() -> CreateApiKeyRequest:
    return CreateApiKeyRequest(
        project_id="proj-1",
        key_alias="Test Key",
        models=["gpt-4"],
        user_id="u-1",
    )


def _update_api_key_factory() -> UpdateApiKeyRequest:
    return UpdateApiKeyRequest(key_alias="Updated Key", models=["gpt-4"], key="key-1")


def _delete_api_key_factory() -> DeleteApiKeyRequest:
    return DeleteApiKeyRequest(key_id="key-1")


def _presign_artifact_factory() -> PresignArtifactRequest:
    return PresignArtifactRequest(
        file_name="test.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        project_id="proj-1",
    )


def _finalize_artifact_factory() -> FinalizeArtifactRequest:
    return FinalizeArtifactRequest(
        artifact_id="art-1",
        bucket="test-bucket",
        key="uploads/test.pdf",
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
    ContractDef("ChatResponse", ChatSendResponse),
    ContractDef("ClientFinalizeArtifactUploadResp", FinalizeArtifactResponse),
    ContractDef("GenericPresignResp", PresignArtifactResponse),
    # Note: PresignArtifactUploadResp removed - duplicate of GenericPresignResp
    # Project
    ContractDef("CreateProjectResponse", Project),
    ContractDef("UpdateProjectResponse", Project),
    # API Keys
    ContractDef("UpdateApiKeyResp", UpdateApiKeyResponse),
    ContractDef("CreateApiKeyResponse", CreateApiKeyResponse),
    ContractDef("ListApiKeysResponse", ListApiKeysResponse),
    ContractDef("DeleteApiKeyResponse", DeleteApiKeyResponse),
    # Corpus - Temporarily skipped (WIP - model validation issues)
    ContractDef(
        "CreateCorpusResponse",
        Corpus,
        status=SchemaStatus.SKIPPED,
        reason="WIP - Model validation mismatch",
    ),
    ContractDef(
        "GetCorpusResponse",
        Corpus,
        status=SchemaStatus.SKIPPED,
        reason="WIP - Model validation mismatch",
    ),
    ContractDef(
        "UpdateCorpusResponse",
        Corpus,
        status=SchemaStatus.SKIPPED,
        reason="WIP - Model validation mismatch",
    ),
    # End User
    ContractDef("CreateEndUserResponse", EndUser),
    ContractDef("GetEndUserByIdResponse", EndUser),  # lowercase Id per Apidog
    ContractDef("UpdateEndUserResponse", EndUser),
    # Note: QueryEndUserResponse doesn't exist in Apidog spec (uses GetEndUserListResponse)
    # History
    ContractDef("MindspaceMessagesResponse", HistoryResponse),
    # MindSpace - Temporarily skipped (WIP - model validation issues)
    ContractDef(
        "CreateMindspaceResponse",
        MindSpace,
        status=SchemaStatus.SKIPPED,
        reason="WIP - Model validation mismatch",
    ),
    ContractDef(
        "GetMindSpaceListResponse",
        GetMindSpaceListResponse,
        status=SchemaStatus.SKIPPED,
        reason="OpenAPI spec outdated - uses BaseSchema+mindspaces, SDK uses data+paging (Bifrost reality)",
    ),
    ContractDef(
        "UpdateMindSpaceResponse",
        MindSpace,
        status=SchemaStatus.SKIPPED,
        reason="WIP - Model validation mismatch",
    ),
    # Auth
    ContractDef("LoginResponse", TokenResponse),
    ContractDef("RefreshResponse", TokenResponse),
    # --- INTENTIONAL SKIPS ---
    # Internal/Webhook
    ContractDef(
        "ArtifactWebhookResp", status=SchemaStatus.SKIPPED, reason="Internal Webhook"
    ),
    # --- UNIMPLEMENTED / OpenAI Compat ---
    ContractDef(
        "ChatCompletionsResp", status=SchemaStatus.SKIPPED, reason="OpenAI Compat"
    ),
    ContractDef(
        "GetCorpusByIdResponse",
        Corpus,
        status=SchemaStatus.SKIPPED,
        reason="WIP - Model validation mismatch",
    ),
    # Note: GetEndUserByIdResponse already mapped above
    ContractDef(
        "GetEndUserListResponse",
        QueryEndUserResponse,
    ),  # Alias to existing QueryEndUserResponse
    ContractDef("KeyResponseSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("ModelsListResp", ModelsListResponse, status=SchemaStatus.TESTED),
]

# =============================================================================
# REQUESTS
# =============================================================================
REQUESTS = [
    # --- TESTED ---
    # Chat
    ContractDef("ChatRequest", ChatSendRequest, factory=_chat_request_factory),
    ContractDef(
        "CreateProjectRequest", CreateProjectRequest, factory=_create_project_factory
    ),
    ContractDef(
        "UpdateProjectRequest", UpdateProjectRequest, factory=_update_project_factory
    ),
    # Corpus
    ContractDef(
        "CreateCorpusRequest", CreateCorpusRequest, factory=_create_corpus_factory
    ),
    ContractDef(
        "UpdateCorpusRequest", UpdateCorpusRequest, factory=_update_corpus_factory
    ),
    # End User
    ContractDef(
        "CreateEndUserRequest", CreateEndUserRequest, factory=_create_end_user_factory
    ),
    ContractDef(
        "UpdateEndUserRequest", UpdateEndUserRequest, factory=_update_end_user_factory
    ),
    # MindSpace
    ContractDef(
        "CreateMindspaceRequest",
        CreateMindSpaceRequest,
        factory=_create_mindspace_factory,
    ),
    ContractDef(
        "UpdateMindSpaceRequest",
        UpdateMindSpaceRequest,
        factory=_update_mindspace_factory,
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
    ContractDef("LoginRequest", LoginRequest, factory=_login_request_factory),
    ContractDef("RefreshRequest", RefreshRequest, factory=_refresh_request_factory),
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
    # Entity Schemas (internal representations)
    ContractDef("ApiKeySchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("CorpusSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("EndUserSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("MindspaceSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("Mindspace", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("PersonaSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("ProjectSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("ContainerRef", status=SchemaStatus.SKIPPED, reason="Component"),
    # Chat Components
    ContractDef("ChatHistoryItem", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("ChatSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    # OpenAI Compat Components
    ContractDef(
        "Choice", status=SchemaStatus.SKIPPED, reason="OpenAI Compat Component"
    ),
    ContractDef(
        "Message", status=SchemaStatus.SKIPPED, reason="OpenAI Compat Component"
    ),
    ContractDef("Model", Model, status=SchemaStatus.TESTED),
    # Internal RPC
    ContractDef(
        "CentrifugoRpcError", status=SchemaStatus.SKIPPED, reason="Internal RPC"
    ),
    ContractDef(
        "CentrifugoRpcResult", status=SchemaStatus.SKIPPED, reason="Internal RPC"
    ),
    # Base/Token Schemas
    ContractDef("BaseSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("ConfigSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("EndUser", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("MindspaceType", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("TokenSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    # Pagination (internal components)
    ContractDef("PaginationSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("CursorSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    # Error handling (internal components)
    ContractDef(" RFC7807Schema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("ErrorFieldsSchema", status=SchemaStatus.SKIPPED, reason="Component"),
    ContractDef("ErrorResponse", status=SchemaStatus.SKIPPED, reason="Error wrapper"),
    # Other
    ContractDef(
        "ListProjectResponse",
        status=SchemaStatus.SKIPPED,
        reason="Empty schema in spec",
    ),
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
