from magick_mind.brainoids import AvailableBrainoids
from magick_mind.utils.chat_completion_request import chat_completion_request
from magick_mind.utils.providers.abstraction import InferenceProvider


class LiteLLMInferenceProvider(InferenceProvider):
    def __init__(
        self,
        model: AvailableBrainoids
    ):
        self.model = model

    def infer(
        self,
        prompt: str
    ) -> str:
        return chat_completion_request(prompt, self.model)
