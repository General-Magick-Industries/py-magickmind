from abc import ABC, abstractmethod
from typing import Any


class ReasoningModel(ABC):
    """Abstract base class defining the interface for reasoning models.

    All reasoning model implementations must inherit from this class and
    implement the `think` method.
    """

    @abstractmethod
    async def process(
        self,
        stimulus: str,
        iterations: int,
        role: str | None = None,
        semantic_memory: Any | None = None,
        episodic_memory: Any | None = None,
    ) -> str:
        """Execute the reasoning process and return the result.

        Returns:
            str: The output of the reasoning process.
        """
        pass
