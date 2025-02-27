import asyncio
import random
import re
from typing import Any, List, Tuple

from magick_mind.reasoning.interfaces import ReasoningModel
from magick_mind.reasoning.super_master.functions import (
    get_critique,
    improve_answer,
    rate_answer,
)
from magick_mind.reasoning.super_master.node import Node
from magick_mind.utils.providers.abstraction import InferenceProvider


class SuperMaster(ReasoningModel):
    def __init__(
        self,
        inference_providers: List[InferenceProvider],
        question: str | None = None,
        episodic_memory: Any | None = None,
        semantic_memory: Any | None = None,
        iterations: int = 2,
        max_depth: int = 3,
    ):
        self.question: str | None = question
        self.inference_providers: List[InferenceProvider] = inference_providers
        self.iterations: int = iterations
        self.max_depth: int = max_depth
        self.episodic_memory: str | None = episodic_memory
        self.semantic_memory: str | None = semantic_memory
        self.root: Node | None = None
        self.current_depth: int = 0

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

    async def __get_initial_answer(self) -> Tuple[str, float, float, InferenceProvider]:
        initial_inference_provider = random.choice(self.inference_providers)
        initial_answer = initial_inference_provider.infer(
            self.question,
        )

        critique = await get_critique(
            question=self.question,
            draft_answer=initial_answer,
            episodic_memory=self.episodic_memory,
            semantic_memory=self.semantic_memory,
            inference_provider=initial_inference_provider,
        )

        improved_answer = await improve_answer(
            question=self.question,
            draft_answer=initial_answer,
            critique=critique,
            episodic_memory=self.episodic_memory,
            semantic_memory=self.semantic_memory,
            inference_provider=initial_inference_provider,
        )
        rating, confidence = await rate_answer(
            question=self.question,
            answer=improved_answer,
            episodic_memory=self.episodic_memory,
            semantic_memory=self.semantic_memory,
            inference_provider=initial_inference_provider,
        )
        return improved_answer, rating, confidence, initial_inference_provider

    async def __search(self) -> str:
        initial_answer, rating, confidence, inference_provider = await self.__get_initial_answer()
        self.root = Node(
            question=self.question,
            answer=initial_answer,
            inference_provider=inference_provider,
            rating=rating,
            confidence=confidence,
        )
        for i in range(self.iterations):
            print(f"\nIteration {i+1}/{self.iterations}")

            self.current_depth = 0  # Reset depth at start of each iteration
            node = self.__select(self.root)
            if not node.is_fully_expanded() and self.current_depth < self.max_depth:
                node = await self.__expand(node)
            self.__backpropagate(node, node.rating)
            if node.rating > 0.93:
                break
        best_answer = self.root.most_visited_child().answer


        match = re.search(r"Final Answer:(.*?)(?=\Z)", best_answer, re.DOTALL)

        if match:
            best_answer = match.group(1).strip()
        else:
            # If no "Final Answer:" found, return the original answer
            best_answer = best_answer.strip()

        return best_answer

    def __select(self, node: Node) -> Node:
        while node.is_fully_expanded() and node.children:
            self.current_depth += 1
            if self.current_depth >= self.max_depth:
                break
            node = node.best_child()
        return node

    async def __expand(self, node: Node) -> Node:
        tasks = []

        async def process_child_node(inference_provider):
            # Children inherit the parent's model
            child_node = Node(
                self.question, node.answer, inference_provider, parent=node
            )
            node.add_child(child_node)

            critique = await get_critique(
                question=self.question,
                draft_answer=child_node.answer,
                episodic_memory=self.episodic_memory,
                semantic_memory=self.semantic_memory,
                inference_provider=inference_provider,
            )

            improved_answer = await improve_answer(
                question=self.question,
                draft_answer=child_node.answer,
                critique=critique,
                episodic_memory=self.episodic_memory,
                semantic_memory=self.semantic_memory,
                inference_provider=inference_provider,
            )
            rating, confidence = await rate_answer(
                question=self.question,
                answer=improved_answer,
                episodic_memory=self.episodic_memory,
                semantic_memory=self.semantic_memory,
                inference_provider=inference_provider,
            )

            child_node.answer = improved_answer
            child_node.rating = rating
            child_node.confidence = confidence

        # Create tasks for all inference providers
        tasks = [
            asyncio.create_task(process_child_node(inference_provider))
            for inference_provider in self.inference_providers
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        best_child = max(node.children, key=lambda x: x.rating)
        return best_child

    def __backpropagate(self, node: Node, reward: float) -> None:
        while node is not None:
            node.visits += 1
            node.value = (node.value * (node.visits - 1) + reward) / node.visits
            node = node.parent
