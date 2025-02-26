import math
import numpy as np

from typing import List, Self

from magick_mind.utils.providers.abstraction import InferenceProvider


class Node:
    def __init__(
        self,
        question: str,
        answer: str,
        inference_provider: InferenceProvider,
        parent: Self | None = None,
        rating: float = 0.0,
        confidence: float = 0.0,
    ):
        self.question: str = question
        self.answer: str = answer
        self.inference_provider: InferenceProvider = inference_provider
        self.parent: Node | None = parent
        self.children: List[Node] = []
        self.visits: int = 0
        self.value: float = 0.0
        self.rating: float = rating
        self.confidence: float = confidence

    def is_fully_expanded(self) -> bool:
        return len(self.children) >= 1

    def best_child(self) -> Self:
        choices_weights = []
        for child in self.children:
            if child.visits == 0:
                weight = float("inf")  # Prioritize unexplored nodes
            else:
                exploritation = (self.confidence * self.value) + (
                    1 - self.confidence
                ) * (child.value / child.visits)
                exploration = (1 / (14.1 * self.confidence)) * math.sqrt(
                    math.log(self.visits) / child.visits
                )
                weight = exploritation + exploration
            choices_weights.append(weight)
        return self.children[np.argmax(choices_weights)]

    def most_visited_child(self) -> Self:
        return max(self.children, key=lambda child: child.visits)

    def add_child(self, child_node: Self):
        self.children.append(child_node)
