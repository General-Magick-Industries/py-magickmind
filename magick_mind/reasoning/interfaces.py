from abc import ABC, abstractmethod


class ReasoningModel(ABC):
    """Abstract base class defining the interface for reasoning models.

    All reasoning model implementations must inherit from this class and
    implement the `think` method.
    """

    @abstractmethod
    def think(self) -> str:
        """Execute the reasoning process and return the result.

        Returns:
            str: The output of the reasoning process.
        """
        pass
