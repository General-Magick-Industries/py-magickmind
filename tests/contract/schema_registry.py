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
)
from magick_mind.models.v1.project import (
    CreateProjectResponse,
    UpdateProjectResponse,
    GetProjectResponse,
    GetProjectListResponse,
)
from magick_mind.models.v1.api_keys import (
    UpdateApiKeyResponse,
    CreateApiKeyResponse,
    ListApiKeysResponse,
    DeleteApiKeyResponse,
)
from magick_mind.models.v1.corpus import (
    CreateCorpusResponse,
    GetCorpusResponse,
    ListCorpusResponse,
    UpdateCorpusResponse,
)
from magick_mind.models.v1.end_user import (
    CreateEndUserResponse,
    GetEndUserResponse,
    QueryEndUserResponse,
    UpdateEndUserResponse,
)
from magick_mind.models.v1.mindspace import (
    CreateMindSpaceResponse,
    GetMindSpaceListResponse,
    UpdateMindSpaceResponse,
)
from magick_mind.models.v1.history import HistoryResponse
from magick_mind.models.auth import TokenResponse


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
    # (Will add in PR 2)
    # --- INTENTIONAL SKIPS ---
    ContractDef(
        "ArtifactWebhookReq", status=SchemaStatus.SKIPPED, reason="Internal Webhook"
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
