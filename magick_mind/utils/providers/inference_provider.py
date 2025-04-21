import os
import litellm
from typing import Optional, List
from litellm import completion
from dataclasses import dataclass, field
from magick_mind.brainoids import AvailableBrainoids
from magick_mind.utils.providers.abstraction import InferenceProvider
from magick_mind.utils.providers.inference.dto.message_dto import MessageDTO
from pydantic import BaseModel


@dataclass
class LiteLLMInferenceProvider(InferenceProvider):
    model: AvailableBrainoids
    api_key: str = field(default=os.environ.get("LITELLM_API_KEY"))
    base_url: str = field(default=os.environ.get("LITELLM_BASE_URL"))

    def __post_init__(self):
        litellm.enable_json_schema_validation = True

    def infer(
        self,
        messages: List[MessageDTO],
        response_format: BaseModel | None = None,
        temperature: float = 0.6,
        max_tokens: int = 1500,
    ) -> Optional[str]:
        chat_response = completion(
            model=self.model.value,
            messages=[message.model_dump() for message in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key,
            base_url=self.base_url,
            response_format=response_format,
        )

        answers = (
            chat_response.choices[0].message.content if chat_response.choices else None
        )

        return answers
