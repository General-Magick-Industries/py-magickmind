import os
from typing import Optional, List
from litellm import completion
from dataclasses import dataclass, field
from magick_mind.brainoids import AvailableBrainoids
from magick_mind.utils.providers.abstraction import InferenceProvider
from magick_mind.utils.providers.inference.constants import MessageRole
from magick_mind.utils.providers.inference.dto.message_dto import MessageDTO


@dataclass
class LiteLLMInferenceProvider(InferenceProvider):
    model: AvailableBrainoids
    api_key: str = field(default=os.environ.get("LITELLM_API_KEY"))
    base_url: str = field(default=os.environ.get("LITELLM_BASE_URL"))

    def infer(
        self,
        prompt: str,
        # messages: Optional[List[MessageDTO]] = None,
        response_format: Optional[dict] = None
    ) -> Optional[str]:
        messages = [
            {
                "role": MessageRole.USER.value,
                "content": prompt
            }
        ]

        # if messages:
        #     messages.append(MessageDTO(role=MessageRole.USER, content=prompt))

        chat_response = completion(
            model=self.model.value,
            messages=messages,
            temperature=0.6,
            max_tokens=1500,
            api_key=self.api_key,
            base_url=self.base_url,
            response_format=response_format if "gpt" in self.model.value else None
        )

        return chat_response.choices[0].message.content if chat_response.choices else None
