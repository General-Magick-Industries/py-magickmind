import random
import asyncio
from typing import Any, List
from magick_mind.reasoning.interfaces import ReasoningModel
from magick_mind.reasoning.super_gamma.node import Node
from magick_mind.reasoning.super_gamma.constants import MAX_CHILDREN
from magick_mind.reasoning.super_gamma.functions import (
    get_critique,
    improve_answer,
    rate_answer,
)
from magick_mind.reasoning.super_gamma.dto import (
    GetCritiqueDTO,
    ImproveAnswerDTO,
    RateAnswerDTO,
)
from magick_mind.utils.providers.abstraction import InferenceProvider


class SuperGamma(ReasoningModel):
    def __init__(
        self,
        inference_providers: List[InferenceProvider],
        rating_inference_provider: InferenceProvider,
        question: str | None = None,
        seed_answers: List[str] = None,
        episodic_memory: Any | None = None,
        semantic_memory: Any | None = None,
    ):
        self.question = question
        self.seed_answers = seed_answers or [
            "I don't know",
            "I don't have knowledge about this",
            "I don't have information about this",
        ]
        self.inference_providers = inference_providers
        self.rating_inference_provider = rating_inference_provider
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        self.initial_inference_provider = random.choice(inference_providers)
        self.root = Node(
            self.question,
            random.choice(self.seed_answers),
            self.initial_inference_provider,
        )

    async def process(
        self,
        stimulus: str,
        iterations: int,
        role: str | None = None,
        semantic_memory: Any | None = None,
        episodic_memory: Any | None = None,
    ) -> str:
        self.question = stimulus
        self.iterations = iterations
        self.role = role

        self.root = Node(
            self.question,
            random.choice(self.seed_answers),
            self.initial_inference_provider,
        )

        if semantic_memory:
            self.semantic_memory = semantic_memory

        if episodic_memory:
            self.episodic_memory = episodic_memory

        answer = await self.__search()

        return answer

    async def __search(self):
        for _ in range(self.iterations):
            # print(f"\nIteration {i + 1} of {self.iterations}")
            node = self.__select(self.root)
            if not node.is_fully_expanded():
                node = await self.__expand(node)
            reward = await self.__simulate(node)
            self.__backpropagate(node, reward)
        best_answer = self.root.most_visited_child().answer

        # print(f"Best Answer: {best_answer}")

        # match = re.search(r"Final Answer:(.*)\Z", best_answer, re.DOTALL)

        # if match:
        #     best_answer = match.group(1).strip()
        # else:
        #     # If no "Final Answer:" found, return the original answer
        #     best_answer = best_answer.strip()

        return best_answer

    def __select(self, node: Node):
        while node.is_fully_expanded() and node.children:
            node = node.best_child()
        return node

    async def __expand(self, node: Node):
        tasks = []

        if node is self.root:
            for inference in self.inference_providers:
                task = asyncio.create_task(
                    self.__create_and_improve_child_node(node, inference)
                )
                tasks.append(task)
        else:
            for _ in range(MAX_CHILDREN):
                task = asyncio.create_task(
                    self.__create_and_improve_child_node(node, node.inference_provider)
                )
                tasks.append(task)

        await asyncio.gather(*tasks)

        return random.choice(node.children)

    async def __create_and_improve_child_node(self, parent_node, inference_provider):
        """Helper method to create and improve a child node"""
        child_node = Node(
            self.question, parent_node.answer, inference_provider, parent=parent_node
        )
        parent_node.add_child(child_node)

        critique = await get_critique(
            get_critique_dto=GetCritiqueDTO(
                question=self.question,
                draft_answer=child_node.answer,
                episodic_memory=self.episodic_memory,
                semantic_memory=self.semantic_memory,
                role=self.role,
            ),
            inference_provider=child_node.inference_provider,
        )

        improved_answer = await improve_answer(
            improve_answer_dto=ImproveAnswerDTO(
                question=self.question,
                draft_answer=child_node.answer,
                critique=critique,
                episodic_memory=self.episodic_memory,
                semantic_memory=self.semantic_memory,
                role=self.role,
            ),
            inference_provider=child_node.inference_provider,
        )
        child_node.answer = improved_answer
        return child_node

    async def __simulate(self, node: Node):
        rating = await rate_answer(
            rate_answer_dto=RateAnswerDTO(
                question=self.question,
                answer=node.answer,
                episodic_memory=self.episodic_memory,
                semantic_memory=self.semantic_memory,
                role=self.role,
            ),
            inference_provider=self.rating_inference_provider,
        )

        return rating

    def __backpropagate(self, node: Node, reward: float):
        while node is not None:
            node.visits += 1
            node.value += reward
            # print(f"Backpropagating Node: {node.answer}, Visits: {node.visits}, Value: {node.value}")
            node = node.parent
