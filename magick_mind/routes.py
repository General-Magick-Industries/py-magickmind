"""Centralized API route constants.

All API endpoint paths are defined here to ensure consistency
across the SDK and make updates easier when the API changes.
"""

from functools import partial
from urllib.parse import quote

# Path segments are percent-encoded so an id taken off the wire cannot splice
# a query string, fragment, or extra path component into a credential-bearing
# request.
_seg = partial(quote, safe="")


class Routes:
    """API v1 route paths for the Magick Mind API."""

    # Auth endpoints
    AUTH_LOGIN = "/v1/auth/login"
    AUTH_REFRESH = "/v1/auth/refresh"

    # Chat endpoints
    CHAT = "/v1/chat/magickmind"

    # Magickspaces endpoints
    MAGICKSPACES = "/v1/magickspaces"
    MINDSPACES = MAGICKSPACES
    END_USER_MAGICKSPACES = "/v1/end-user/magickspaces"

    @staticmethod
    def end_user_magickspace_context(magickspace_id: str) -> str:
        """Context preparation for the calling agent (end-user JWT)."""
        return f"/v1/end-user/magickspaces/{_seg(magickspace_id)}/context"

    @staticmethod
    def end_user_magickspace_messages(magickspace_id: str) -> str:
        """Messages of a magickspace the calling agent participates in (end-user JWT)."""
        return f"/v1/end-user/magickspaces/{_seg(magickspace_id)}/messages"

    @staticmethod
    def magickspace(magickspace_id: str) -> str:
        """Get path for a specific magickspace."""
        return f"/v1/magickspaces/{_seg(magickspace_id)}"

    @staticmethod
    def mindspace(mindspace_id: str) -> str:
        """Deprecated alias for :meth:`magickspace`."""
        return Routes.magickspace(mindspace_id)

    @staticmethod
    def magickspace_messages(magickspace_id: str) -> str:
        """Get path for magickspace messages."""
        return f"/v1/magickspaces/{_seg(magickspace_id)}/messages"

    @staticmethod
    def mindspace_messages(mindspace_id: str) -> str:
        """Deprecated alias for :meth:`magickspace_messages`."""
        return Routes.magickspace_messages(mindspace_id)

    @staticmethod
    def magickspace_users(magickspace_id: str) -> str:
        """Get path to add users to a specific magickspace."""
        return f"/v1/magickspaces/{_seg(magickspace_id)}/users"

    @staticmethod
    def mindspace_users(mindspace_id: str) -> str:
        """Deprecated alias for :meth:`magickspace_users`."""
        return Routes.magickspace_users(mindspace_id)

    @staticmethod
    def magickspace_context(magickspace_id: str) -> str:
        """Get path for magickspace context preparation."""
        return f"/v1/magickspaces/{_seg(magickspace_id)}/context"

    @staticmethod
    def mindspace_context(mindspace_id: str) -> str:
        """Deprecated alias for :meth:`magickspace_context`."""
        return Routes.magickspace_context(mindspace_id)

    @staticmethod
    def magickspace_livekit_token(magickspace_id: str) -> str:
        """Get path for LiveKit token generation."""
        return f"/v1/magickspaces/{_seg(magickspace_id)}/livekit-token"

    @staticmethod
    def mindspace_livekit_token(mindspace_id: str) -> str:
        """Deprecated alias for :meth:`magickspace_livekit_token`."""
        return Routes.magickspace_livekit_token(mindspace_id)

    @staticmethod
    def magickspace_livekit_join(magickspace_id: str) -> str:
        """Get path for LiveKit agent join signalling."""
        return f"/v1/magickspaces/{_seg(magickspace_id)}/livekit-join"

    @staticmethod
    def mindspace_livekit_join(mindspace_id: str) -> str:
        """Deprecated alias for :meth:`magickspace_livekit_join`."""
        return Routes.magickspace_livekit_join(mindspace_id)

    # Runtime endpoints
    RUNTIME_INVALIDATE_CACHE = "/v1/runtime/invalidate-cache"

    @staticmethod
    def runtime_effective_personality(agent_id: str) -> str:
        """Get path for an agent's effective personality (keyed by agent id)."""
        return f"/v1/runtime/effective-personality/{_seg(agent_id)}"

    # Blueprint endpoints
    BLUEPRINTS = "/v1/blueprints"
    BLUEPRINTS_VALIDATE = "/v1/blueprints/validate"
    BLUEPRINTS_BY_KEY = "/v1/blueprints/by-key"

    @staticmethod
    def blueprint(blueprint_id: str) -> str:
        """Get path for a specific blueprint."""
        return f"/v1/blueprints/{_seg(blueprint_id)}"

    @staticmethod
    def blueprint_clone(blueprint_id: str) -> str:
        """Get path to clone a blueprint."""
        return f"/v1/blueprints/{_seg(blueprint_id)}/clone"

    @staticmethod
    def blueprint_hydrate(blueprint_id: str) -> str:
        """Get path to hydrate a blueprint."""
        return f"/v1/blueprints/{_seg(blueprint_id)}/hydrate"

    # Persona endpoints
    PERSONAS = "/v1/persona"
    PERSONA_PREPARE_OWN = "/v1/end-user/persona/prepare"
    PERSONA_FROM_BLUEPRINT = "/v1/persona/from-blueprint"

    @staticmethod
    def persona(persona_id: str) -> str:
        """Get path for a specific persona."""
        return f"/v1/persona/{_seg(persona_id)}"

    @staticmethod
    def persona_versions(persona_id: str) -> str:
        """Get path for persona versions."""
        return f"/v1/persona/{_seg(persona_id)}/version"

    @staticmethod
    def persona_version(persona_id: str, version: str) -> str:
        """Get path for a specific persona version."""
        return f"/v1/persona/{_seg(persona_id)}/version/{_seg(version)}"

    @staticmethod
    def persona_prepare(persona_id: str) -> str:
        """Get path for preparing a persona's system prompt (legacy path).

        Keyed by persona ID. See :meth:`end_user_persona_prepare` for the
        agent-keyed path, which returns richer resolution metadata.
        """
        return f"/v1/persona/{_seg(persona_id)}/prepare"

    @staticmethod
    def persona_active_version(persona_id: str) -> str:
        """Get path for persona active version."""
        return f"/v1/persona/{_seg(persona_id)}/version/active"

    @staticmethod
    def persona_activate_version(persona_id: str, version: str) -> str:
        """Get path for activating a specific persona version."""
        return f"/v1/persona/{_seg(persona_id)}/version/{_seg(version)}/activate"

    # Episode endpoints
    EPISODES_PROCESS = "/v1/episodes/process"
    EPISODES_PROCESS_OWN = "/v1/end-user/episodes/process"
    EPISODES_SEARCH = "/v1/episodes/search"
    EPISODES_SEARCH_OWN = "/v1/end-user/episodes/search"
    EPISODES_RANGE = "/v1/episodes/range"
    EPISODES_RANGE_OWN = "/v1/end-user/episodes/range"

    # Project endpoints
    PROJECTS = "/v1/projects"

    @staticmethod
    def project(project_id: str) -> str:
        """Get path for a specific project."""
        return f"/v1/projects/{_seg(project_id)}"

    # End User endpoints
    END_USERS = "/v1/end-users"
    END_USER_TOKENS = "/v1/end-users/tokens"
    END_USER_TOKENS_REFRESH = "/v1/end-user/tokens/refresh"
    END_USER_TOKENS_REVOKE = "/v1/end-user/tokens/revoke"

    @staticmethod
    def end_user(end_user_id: str) -> str:
        """Get path for a specific end user."""
        return f"/v1/end-users/{_seg(end_user_id)}"

    @staticmethod
    def end_user_persona(agent_id: str) -> str:
        """Attach a persona to an agent (service-user credentials)."""
        return f"/v1/end-users/{_seg(agent_id)}/persona"

    @staticmethod
    def end_user_persona_version(agent_id: str) -> str:
        """Change an agent's active persona version (service-user credentials)."""
        return f"/v1/end-users/{_seg(agent_id)}/persona/version"

    @staticmethod
    def end_user_persona_prepare(agent_id: str) -> str:
        """Get path for preparing an agent's persona system prompt.

        Keyed by agent ID, not persona ID. Called with service-user credentials.
        See :attr:`PERSONA_PREPARE_OWN` for the end-user-JWT path.
        """
        return f"/v1/end-users/{_seg(agent_id)}/persona/prepare"

    # Trait endpoints
    TRAITS = "/v1/traits"

    @staticmethod
    def trait(trait_id: str) -> str:
        """Get path for a specific trait."""
        return f"/v1/traits/{_seg(trait_id)}"

    # Corpus endpoints
    CORPUS = "/v1/corpus"

    @staticmethod
    def corpus(corpus_id: str) -> str:
        """Get path for a specific corpus."""
        return f"/v1/corpus/{_seg(corpus_id)}"

    @staticmethod
    def corpus_artifacts_finalize(corpus_id: str) -> str:
        """Get path for corpus artifact finalization."""
        return f"/v1/corpus/{_seg(corpus_id)}/artifacts/finalize"

    @staticmethod
    def corpus_artifacts(corpus_id: str) -> str:
        """Get path for corpus artifacts management."""
        return f"/v1/corpus/{_seg(corpus_id)}/artifacts"

    @staticmethod
    def corpus_artifact(corpus_id: str, artifact_id: str) -> str:
        """Get path for a specific corpus artifact."""
        return f"/v1/corpus/{_seg(corpus_id)}/artifacts/{_seg(artifact_id)}"

    @staticmethod
    def corpus_artifacts_status(corpus_id: str) -> str:
        """Get path for listing artifact statuses within a corpus."""
        return f"/v1/corpus/{_seg(corpus_id)}/artifacts/status"

    @staticmethod
    def corpus_query(corpus_id: str) -> str:
        """Get path for querying a corpus."""
        return f"/v1/corpus/{_seg(corpus_id)}/query"

    @staticmethod
    def end_user_corpus_query(corpus_id: str) -> str:
        """Query a corpus with the calling agent's end-user JWT."""
        return f"/v1/end-user/corpus/{_seg(corpus_id)}/query"

    # Artifact endpoints
    ARTIFACTS = "/v1/artifacts"
    ARTIFACTS_PRESIGN = "/v1/artifacts/presign"
    ARTIFACTS_FINALIZE = "/v1/artifacts/finalize"

    @staticmethod
    def artifact(artifact_id: str) -> str:
        """Get path for a specific artifact."""
        return f"/v1/artifacts/{_seg(artifact_id)}"

    @staticmethod
    def artifact_download(artifact_id: str) -> str:
        """Get path for retrieving an artifact's presigned download URL."""
        return f"/v1/artifacts/{_seg(artifact_id)}/download"

    @staticmethod
    def magickspace_artifacts_presign(magickspace_id: str) -> str:
        """Presign an upload into a magickspace (service-user credentials)."""
        return f"/v1/magickspaces/{_seg(magickspace_id)}/artifacts/presign"

    @staticmethod
    def end_user_magickspace_artifacts(magickspace_id: str) -> str:
        """Artifacts attached to messages in a magickspace (end-user JWT)."""
        return f"/v1/end-user/magickspaces/{_seg(magickspace_id)}/artifacts"

    @staticmethod
    def end_user_magickspace_artifacts_presign(magickspace_id: str) -> str:
        """Presign an upload into a magickspace (end-user JWT)."""
        return f"/v1/end-user/magickspaces/{_seg(magickspace_id)}/artifacts/presign"

    @staticmethod
    def end_user_magickspace_artifacts_finalize(magickspace_id: str) -> str:
        """Finalize an upload into a magickspace (end-user JWT)."""
        return f"/v1/end-user/magickspaces/{_seg(magickspace_id)}/artifacts/finalize"

    @staticmethod
    def end_user_magickspace_artifact(magickspace_id: str, artifact_id: str) -> str:
        """One artifact attached to a message in a magickspace (end-user JWT)."""
        return f"/v1/end-user/magickspaces/{_seg(magickspace_id)}/artifacts/{_seg(artifact_id)}"

    @staticmethod
    def end_user_magickspace_artifact_download(
        magickspace_id: str, artifact_id: str
    ) -> str:
        """Presigned download of a magickspace artifact (end-user JWT)."""
        return f"/v1/end-user/magickspaces/{_seg(magickspace_id)}/artifacts/{_seg(artifact_id)}/download"

    @staticmethod
    def end_user_artifact(artifact_id: str) -> str:
        """An artifact owned by the calling end user, regardless of membership."""
        return f"/v1/end-user/artifacts/{_seg(artifact_id)}"

    @staticmethod
    def end_user_artifact_download(artifact_id: str) -> str:
        """Presigned download of an artifact owned by the calling end user."""
        return f"/v1/end-user/artifacts/{_seg(artifact_id)}/download"

    # API Keys endpoints
    KEYS = "/v1/keys"

    # History endpoints (deprecated - use magickspace_messages instead)
    # HISTORY_MESSAGES removed: was "/v1/magickspaces/messages" which doesn't exist in Bifrost.
    # The correct route is /v1/magickspaces/{id}/messages via Routes.magickspace_messages(id).
