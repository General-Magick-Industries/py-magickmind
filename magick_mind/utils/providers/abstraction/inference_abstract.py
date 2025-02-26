from abc import ABC, abstractmethod
from typing import Optional, List
from magick_mind.utils.providers.inference.dto import MessageDTO


class InferenceProvider(ABC):
    @abstractmethod
    def infer(
        self,
        prompt: str,
        messages: Optional[List[MessageDTO]] = None,
        response_format: Optional[dict] = None
    ) -> Optional[str]:
        pass
