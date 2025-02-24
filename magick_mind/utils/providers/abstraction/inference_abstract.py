from abc import ABC, abstractmethod


class InferenceProvider(ABC):
    @abstractmethod
    def infer(self, prompt: str) -> str:
        pass
