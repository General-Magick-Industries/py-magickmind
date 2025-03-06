from typing import List, Self
from .constants import MAX_CHILDREN
import math
import numpy as np
from magick_mind.utils.providers.abstraction import InferenceProvider


class Node:
    def __init__(
        self,
        question: str,
        answer: str,
        inference_provider: InferenceProvider,
        parent: Self | None = None,
    ):
        self.question = question
        self.answer = answer
        self.inference_provider = inference_provider
        self.parent = parent
        self.children: List[Node] = []
        self.visits = 0
        self.value = 0.0

    def is_fully_expanded(self):
        return len(self.children) >= MAX_CHILDREN

    def best_child(self, exploration_weight: float = 1.41):
        choices_weights = []
        for child in self.children:
            if child.visits == 0:
                weight = float("inf")  # Prioritize unexplored nodes
            else:
                weight = (child.value / child.visits) + exploration_weight * math.sqrt(
                    (2 * math.log(self.visits) / child.visits)
                )
            choices_weights.append(weight)
        return self.children[np.argmax(choices_weights)]

    def most_visited_child(self):
        return max(self.children, key=lambda child: child.visits)

    def add_child(self, child_node):
        self.children.append(child_node)
