from abc import ABC, abstractmethod
from typing import Optional, List
from magick_mind.utils.providers.inference.dto import MessageDTO


class InferenceProvider(ABC):
    @abstractmethod
    def infer(
        self,
        messages: Optional[List[MessageDTO]],
        response_format: Optional[dict] = None,
        temperature: float = 0.6,
        max_tokens: int = 1500,
    ) -> Optional[str]:
        pass
