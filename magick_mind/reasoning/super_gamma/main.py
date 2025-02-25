import random
import re
from typing import Any, List
from magick_mind.reasoning.interfaces import ReasoningModel
from magick_mind.reasoning.super_gamma.node import Node
from magick_mind.reasoning.super_gamma.constants import MAX_CHILDREN
from magick_mind.reasoning.super_gamma.functions import get_critique, improve_answer, rate_answer
from magick_mind.utils.providers.abstraction import InferenceProvider
import asyncio


class SuperGamma(ReasoningModel):
    def __init__(
        self,
        inference_providers: List[InferenceProvider],
        rating_inference_provider: InferenceProvider,
        question: str | None = None,
        seed_answers: List[str] = [
            "I don't know",
            "I don't have knowledge about this",
            "I don't have information about this",
        ],
        episodic_memory: Any | None = None,
        semantic_memory: Any | None = None,
        iterations: int = 3,
    ):
        self.question = question
        self.seed_answers = seed_answers
        self.inference_providers = inference_providers
        self.iterations = iterations
        self.rating_inference_provider = rating_inference_provider
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        initial_inference_provider = random.choice(inference_providers)
        self.root = Node(
            question,
            random.choice(seed_answers),
            initial_inference_provider
        )

    async def process(
        self,
        stimulus: str,
        semantic_memory: Any | None = None,
        episodic_memory: Any | None = None,
        iterations: int | None = None,
    ) -> str:
        self.question = stimulus

        if semantic_memory:
            self.semantic_memory = semantic_memory

        if episodic_memory:
            self.episodic_memory = episodic_memory

        if iterations:
            self.iterations = iterations

        answer = await self.__search()

        return answer

    async def __search(self):
        for i in range(self.iterations):
            print(f"\nIteration {i+1}/{self.iterations}")
            node = self.__select(self.root)
            if not node.is_fully_expanded():
                node = await self.__expand(node)
            reward = self.__simulate(node)
            self.__backpropagate(node, reward)
        best_answer = self.root.most_visited_child().answer

        # print(f"Best Answer: {best_answer}")

        match = re.search(r'Final Answer:(.*?)(?=\Z)', best_answer, re.DOTALL)

        if match:
            best_answer = match.group(1).strip()
        else:
            # If no "Final Answer:" found, return the original answer
            best_answer = best_answer.strip()

        return best_answer

    def __select(self, node: Node):
        while node.is_fully_expanded() and node.children:
            node = node.best_child()
        return node

    async def __expand(self, node: Node):
        tasks = []

        if node is self.root:
            # Create tasks for root node expansion
            for inference in self.inference_providers:
                task = asyncio.create_task(
                    self.__create_and_improve_child_node(node, inference)
                )
                tasks.append(task)
        else:
            # Create tasks for regular node expansion
            remaining_children = MAX_CHILDREN - len(node.children)
            for _ in range(remaining_children):
                task = asyncio.create_task(
                    self.__create_and_improve_child_node(
                        node, node.inference_provider)
                )
                tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        return random.choice(node.children)

    async def __create_and_improve_child_node(self, parent_node, inference_provider):
        """Helper method to create and improve a child node"""
        child_node = Node(
            self.question,
            parent_node.answer,
            inference_provider,
            parent=parent_node
        )
        parent_node.add_child(child_node)

        critique = await get_critique(
            self.question,
            child_node.answer,
            self.episodic_memory,
            self.semantic_memory,
            child_node.inference_provider,
        )

        improved_answer = await improve_answer(
            self.question,
            child_node.answer,
            critique,
            self.episodic_memory,
            self.semantic_memory,
            child_node.inference_provider,
        )
        child_node.answer = improved_answer
        return child_node

    def __simulate(self, node: Node):
        rating = rate_answer(
            self.question,
            node.answer,
            self.episodic_memory,
            self.semantic_memory,
            self.rating_inference_provider,
        )

        return rating

    def __backpropagate(self, node: Node, reward: float):
        while node is not None:
            node.visits += 1
            node.value += reward
            # print(f"Backpropagating Node: {node.answer}, Visits: {node.visits}, Value: {node.value}")
            node = node.parent
