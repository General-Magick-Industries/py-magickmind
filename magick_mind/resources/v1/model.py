from typing import Optional, List

from magick_mind.resources.base import BaseResource
from magick_mind.models.v1.model import ModelsListResponse
from magick_mind.routes import Routes


class ModelsResourceV1(BaseResource):
    """Resource to interact with the models API."""

    def list(self) -> ModelsListResponse:
        """
        List all available models.

        Returns:
            ModelsListResponse: A list of available models.
        """
        return ModelsListResponse(**self._http.get(Routes.MODELS))
