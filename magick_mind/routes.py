"""Centralized API route constants.

All API endpoint paths are defined here to ensure consistency
across the SDK and make updates easier when the API changes.
"""


class Routes:
    """API v1 route paths for Bifrost."""

    # Auth endpoints
    AUTH_LOGIN = "/v1/auth/login"
    AUTH_REFRESH = "/v1/auth/refresh"

    # Chat endpoints
    CHAT = "/v1/magickmind/chat"

    # Mindspace endpoints
    MINDSPACES = "/v1/mindspaces"
    MINDSPACE_MESSAGES = "/v1/mindspaces/messages"

    @staticmethod
    def mindspace(mindspace_id: str) -> str:
        """Get path for a specific mindspace."""
        return f"/v1/mindspaces/{mindspace_id}"

    # Project endpoints
    PROJECTS = "/v1/projects"

    @staticmethod
    def project(project_id: str) -> str:
        """Get path for a specific project."""
        return f"/v1/projects/{project_id}"

    # End User endpoints
    END_USERS = "/v1/end-users"

    @staticmethod
    def end_user(end_user_id: str) -> str:
        """Get path for a specific end user."""
        return f"/v1/end-users/{end_user_id}"

    # Corpus endpoints
    CORPUS = "/v1/corpus"

    @staticmethod
    def corpus(corpus_id: str) -> str:
        """Get path for a specific corpus."""
        return f"/v1/corpus/{corpus_id}"

    @staticmethod
    def corpus_artifacts_finalize(corpus_id: str) -> str:
        """Get path for corpus artifact finalization."""
        return f"/v1/corpus/{corpus_id}/artifacts/finalize"

    # Artifact endpoints
    ARTIFACTS = "/v1/artifacts"
    ARTIFACTS_PRESIGN = "/v1/artifacts/presign"
    ARTIFACTS_FINALIZE = "/v1/artifacts/finalize"

    @staticmethod
    def artifact(artifact_id: str) -> str:
        """Get path for a specific artifact."""
        return f"/v1/artifacts/{artifact_id}"

    # API Keys endpoints
    KEYS = "/v1/keys"

    # History endpoints (alias for mindspace messages)
    HISTORY_MESSAGES = "/v1/mindspaces/messages"
