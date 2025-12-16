"""Resource clients for API endpoints."""

from typing import TYPE_CHECKING

from magick_mind.resources.base import BaseResource

if TYPE_CHECKING:
    from magick_mind.http import HTTPClient


class V1Resources:
    """Container for all v1 API resources."""

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize V1 resources.

        Args:
            http_client: HTTP client for making API requests
        """
        from magick_mind.resources.v1.artifact import ArtifactResourceV1
        from magick_mind.resources.v1.api_keys import ApiKeysResourceV1
        from magick_mind.resources.v1.chat import ChatResourceV1
        from magick_mind.resources.v1.corpus import CorpusResourceV1
        from magick_mind.resources.v1.end_user import EndUserResourceV1
        from magick_mind.resources.v1.history import HistoryResourceV1
        from magick_mind.resources.v1.mindspace import MindspaceResourceV1
        from magick_mind.resources.v1.project import ProjectResourceV1

        self.artifact = ArtifactResourceV1(http_client)
        self.api_keys = ApiKeysResourceV1(http_client)
        self.chat = ChatResourceV1(http_client)
        self.corpus = CorpusResourceV1(http_client)
        self.end_user = EndUserResourceV1(http_client)
        self.history = HistoryResourceV1(http_client)
        self.mindspace = MindspaceResourceV1(http_client)
        self.project = ProjectResourceV1(http_client)


__all__ = ["BaseResource", "V1Resources"]
