from typing import Optional, List

from magick_mind.resources.base import BaseResource
from magick_mind.models.v1.model import ModelsListResponse, Model
from magick_mind.routes import Routes


class ModelsResourceV1(BaseResource):
    """Resource to interact with the models API."""

    def list(self) -> List[Model]:
        """
        List all available models.

        Returns:
            List[Model]: A list of available models.
        """
        response = ModelsListResponse(**self._http.get(Routes.MODELS))
        return response.data
