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
from magick_mind.models.v1.trait import (
    Trait,
    CreateTraitRequest,
    UpdateTraitRequest,
    PatchTraitRequest,
    ListTraitsResponse,
)


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

from polyfactory.factories.pydantic_factory import ModelFactory


class ChatSendRequestFactory(ModelFactory):
    __model__ = ChatSendRequest
    config = ConfigSchema(
        fast_model_id="gpt-4", smart_model_ids=["gpt-4"], compute_power=50
    )


class CreateProjectRequestFactory(ModelFactory):
    __model__ = CreateProjectRequest


class UpdateProjectRequestFactory(ModelFactory):
    __model__ = UpdateProjectRequest


class CreateCorpusRequestFactory(ModelFactory):
    __model__ = CreateCorpusRequest
    name = "Test Corpus"
    description = "Corpus Desc"
    artifact_ids = []


class UpdateCorpusRequestFactory(ModelFactory):
    __model__ = UpdateCorpusRequest


class CreateEndUserRequestFactory(ModelFactory):
    __model__ = CreateEndUserRequest


class UpdateEndUserRequestFactory(ModelFactory):
    __model__ = UpdateEndUserRequest
    name = "Updated User"
    external_id = "ext-456"


class CreateMindSpaceRequestFactory(ModelFactory):
    __model__ = CreateMindSpaceRequest
    type = "PRIVATE"  # Constrained Literal field


class UpdateMindSpaceRequestFactory(ModelFactory):
    __model__ = UpdateMindSpaceRequest


class CreateApiKeyRequestFactory(ModelFactory):
    __model__ = CreateApiKeyRequest


class UpdateApiKeyRequestFactory(ModelFactory):
    __model__ = UpdateApiKeyRequest
    key = "key-1"
    models = ["gpt-4"]
    key_alias = "Updated Key"


class DeleteApiKeyRequestFactory(ModelFactory):
    __model__ = DeleteApiKeyRequest


class PresignArtifactRequestFactory(ModelFactory):
    __model__ = PresignArtifactRequest


class FinalizeArtifactRequestFactory(ModelFactory):
    __model__ = FinalizeArtifactRequest


class LoginRequestFactory(ModelFactory):
    __model__ = LoginRequest


class RefreshRequestFactory(ModelFactory):
    __model__ = RefreshRequest


class CreateTraitRequestFactory(ModelFactory):
    __model__ = CreateTraitRequest
    namespace = "SYSTEM"
    type = "NUMERIC"
    visibility = "PUBLIC"
    category = "personality"
    display_name = "Test"
    description = "desc"


class UpdateTraitRequestFactory(ModelFactory):
    __model__ = UpdateTraitRequest
    type = "NUMERIC"
    visibility = "PUBLIC"
    category = "personality"
    display_name = "Test"
    description = "desc"


class PatchTraitRequestFactory(ModelFactory):
    __model__ = PatchTraitRequest


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
    # Trait - Skipped: Apidog spec has garbled enums (e.g. "YSTEM|USER|ORG|PROMOTE")
    # and all nullable fields incorrectly marked required. Models are correct per trait.api.
    ContractDef(
        "TraitSchema",
        Trait,
        status=SchemaStatus.SKIPPED,
        reason="Apidog spec corrupted - garbled enums, wrong required fields",
    ),
    ContractDef(
        "ListTraitsResponse",
        ListTraitsResponse,
        status=SchemaStatus.SKIPPED,
        reason="Apidog spec corrupted - garbled enums in nested TraitSchema",
    ),
]

# =============================================================================
# REQUESTS
# =============================================================================
REQUESTS = [
    # --- TESTED ---
    # Chat
    ContractDef("ChatRequest", ChatSendRequest, factory=ChatSendRequestFactory.build),
    ContractDef(
        "CreateProjectRequest",
        CreateProjectRequest,
        factory=CreateProjectRequestFactory.build,
    ),
    ContractDef(
        "UpdateProjectRequest",
        UpdateProjectRequest,
        factory=UpdateProjectRequestFactory.build,
    ),
    # Corpus
    ContractDef(
        "CreateCorpusRequest",
        CreateCorpusRequest,
        factory=CreateCorpusRequestFactory.build,
    ),
    ContractDef(
        "UpdateCorpusRequest",
        UpdateCorpusRequest,
        factory=UpdateCorpusRequestFactory.build,
    ),
    # End User
    ContractDef(
        "CreateEndUserRequest",
        CreateEndUserRequest,
        factory=CreateEndUserRequestFactory.build,
    ),
    ContractDef(
        "UpdateEndUserRequest",
        UpdateEndUserRequest,
        factory=UpdateEndUserRequestFactory.build,
    ),
    # MindSpace - Skipped: Apidog spec requires "user_ids" but Bifrost was
    # refactored to "participant_ids". SDK model is correct per mindspace.api.
    ContractDef(
        "CreateMindspaceRequest",
        CreateMindSpaceRequest,
        status=SchemaStatus.SKIPPED,
        reason="Apidog spec outdated - requires user_ids, Bifrost uses participant_ids",
    ),
    ContractDef(
        "UpdateMindSpaceRequest",
        UpdateMindSpaceRequest,
        factory=UpdateMindSpaceRequestFactory.build,
    ),
    # API Keys
    ContractDef(
        "CreateApiKeyReq", CreateApiKeyRequest, factory=CreateApiKeyRequestFactory.build
    ),
    ContractDef(
        "UpdateApiKeyReq", UpdateApiKeyRequest, factory=UpdateApiKeyRequestFactory.build
    ),
    ContractDef(
        "DeleteApiKeyReq", DeleteApiKeyRequest, factory=DeleteApiKeyRequestFactory.build
    ),
    # Artifact
    ContractDef(
        "GenericPresignReq",
        PresignArtifactRequest,
        factory=PresignArtifactRequestFactory.build,
    ),
    ContractDef(
        "PresignArtifactUploadReq",
        PresignArtifactRequest,
        factory=PresignArtifactRequestFactory.build,
    ),
    ContractDef(
        "ClientFinalizeArtifactUploadReq",
        FinalizeArtifactRequest,
        factory=FinalizeArtifactRequestFactory.build,
    ),
    # Auth
    ContractDef("LoginRequest", LoginRequest, factory=LoginRequestFactory.build),
    ContractDef("RefreshRequest", RefreshRequest, factory=RefreshRequestFactory.build),
    # Trait - Skipped: CreateTraitRequest absent from Apidog spec entirely;
    # Update/Patch have garbled enums. Models are correct per trait.api.
    ContractDef(
        "CreateTraitRequest",
        CreateTraitRequest,
        status=SchemaStatus.SKIPPED,
        reason="Apidog spec corrupted - schema absent from spec export",
    ),
    ContractDef(
        "UpdateTraitRequest",
        UpdateTraitRequest,
        status=SchemaStatus.SKIPPED,
        reason="Apidog spec corrupted - garbled enums",
    ),
    ContractDef(
        "PatchTraitRequest",
        PatchTraitRequest,
        status=SchemaStatus.SKIPPED,
        reason="Apidog spec corrupted - garbled enums",
    ),
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
