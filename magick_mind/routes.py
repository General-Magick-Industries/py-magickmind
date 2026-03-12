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
    CHAT = "/v1/chat/magickmind"
    MODELS = "/v1/models"

    # Mindspace endpoints
    MINDSPACES = "/v1/mindspaces"
    MINDSPACE_MESSAGES = "/v1/mindspaces/messages"

    @staticmethod
    def mindspace(mindspace_id: str) -> str:
        """Get path for a specific mindspace."""
        return f"/v1/mindspaces/{mindspace_id}"

    @staticmethod
    def mindspace_users(mindspace_id: str) -> str:
        """Get path to add users to a specific mindspace."""
        return f"/v1/mindspaces/{mindspace_id}/users"

    @staticmethod
    def mindspace_context(mindspace_id: str) -> str:
        """Get path for mindspace context preparation."""
        return f"/v1/mindspaces/{mindspace_id}/context"

    @staticmethod
    def mindspace_livekit_token(mindspace_id: str) -> str:
        """Get path for LiveKit token generation."""
        return f"/v1/mindspaces/{mindspace_id}/livekit-token"

    @staticmethod
    def mindspace_livekit_join(mindspace_id: str) -> str:
        """Get path for LiveKit agent join signalling."""
        return f"/v1/mindspaces/{mindspace_id}/livekit-join"

    # Runtime endpoints
    RUNTIME_INVALIDATE_CACHE = "/v1/runtime/invalidate-cache"

    @staticmethod
    def runtime_effective_personality(persona_id: str) -> str:
        """Get path for effective personality."""
        return f"/v1/runtime/effective-personality/{persona_id}"

    # Blueprint endpoints
    BLUEPRINTS = "/v1/blueprints"
    BLUEPRINTS_VALIDATE = "/v1/blueprints/validate"
    BLUEPRINTS_BY_KEY = "/v1/blueprints/by-key"

    @staticmethod
    def blueprint(blueprint_id: str) -> str:
        """Get path for a specific blueprint."""
        return f"/v1/blueprints/{blueprint_id}"

    @staticmethod
    def blueprint_clone(blueprint_id: str) -> str:
        """Get path to clone a blueprint."""
        return f"/v1/blueprints/{blueprint_id}/clone"

    @staticmethod
    def blueprint_hydrate(blueprint_id: str) -> str:
        """Get path to hydrate a blueprint."""
        return f"/v1/blueprints/{blueprint_id}/hydrate"

    # Persona endpoints
    PERSONAS = "/v1/persona"
    PERSONA_FROM_BLUEPRINT = "/v1/persona/from-blueprint"

    @staticmethod
    def persona(persona_id: str) -> str:
        """Get path for a specific persona."""
        return f"/v1/persona/{persona_id}"

    @staticmethod
    def persona_versions(persona_id: str) -> str:
        """Get path for persona versions."""
        return f"/v1/persona/{persona_id}/version"

    @staticmethod
    def persona_version(persona_id: str, version: str) -> str:
        """Get path for a specific persona version."""
        return f"/v1/persona/{persona_id}/version/{version}"

    @staticmethod
    def persona_active_version(persona_id: str) -> str:
        """Get path for persona active version."""
        return f"/v1/persona/{persona_id}/version/active"

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

    @staticmethod
    def corpus_artifacts(corpus_id: str) -> str:
        """Get path for corpus artifacts management."""
        return f"/v1/corpus/{corpus_id}/artifacts"

    @staticmethod
    def corpus_artifact(corpus_id: str, artifact_id: str) -> str:
        """Get path for a specific corpus artifact."""
        return f"/v1/corpus/{corpus_id}/artifacts/{artifact_id}"

    @staticmethod
    def corpus_artifacts_status(corpus_id: str) -> str:
        """Get path for listing artifact statuses within a corpus."""
        return f"/v1/corpus/{corpus_id}/artifacts/status"

    @staticmethod
    def corpus_artifact_status(corpus_id: str, artifact_id: str) -> str:
        """Get path for a single artifact's ingestion status within a corpus."""
        return f"/v1/corpus/{corpus_id}/artifacts/{artifact_id}/status"

    @staticmethod
    def corpus_query(corpus_id: str) -> str:
        """Get path for querying a corpus."""
        return f"/v1/corpus/{corpus_id}/query"

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
