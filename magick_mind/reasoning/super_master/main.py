import os
from typing import Any, List, Self

import math
import random
import numpy as np
import re
from litellm import completion
from ..interfaces import ReasoningModel


max_children = 3


def chat_completion_request(prompt, model_name):
    messages = [{"role": "user", "content": prompt}]

    # Create chat completions using LiteLLM's completion function
    chat_response = completion(
        model=model_name,
        messages=messages,
        temperature=0.6,
        max_tokens=1500,
        api_key=os.environ.get("LITELLM_API_KEY"),
        base_url=os.environ.get("LITELLM_BASE_URL"),
    )

    # Extract the completion text from the response
    if chat_response.choices:
        completion_text = chat_response.choices[0].message.content
    else:
        completion_text = None
    return completion_text


# Get Critique
def get_critique(question, draft_answer, model_name, episodic_memory, semantic_memory):
    prompt = (
        f"Episodic Memory: {episodic_memory}\n"
        f"Semantic Memory: {semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {question}\n"
        f"Draft Answer: {draft_answer}\n"
        "Please critique the draft answer. "
        "Do a careful assessment of whether the answer is correct or not, and why."
        "Consider multiple ways of verifying the correctness of the answer."
        "Do point out every flaw and hold the draft answer to a high standard. "
        "Do provide specific recommendations to improve the answer. "
        "Do think step by step. "
        "Do not provide a revised answer."
    )

    # Create the request to the LLM
    return chat_completion_request(prompt, model_name)


def improve_answer(
    question, draft_answer, critique, model_name, episodic_memory, semantic_memory
):
    prompt = (
        f"Episodic Memory: {episodic_memory}\n"
        f"Semantic Memory: {semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {question}\n"
        f"Draft Answer: {draft_answer}\n"
        f"Critique: {critique}\n\n"
        "Please improve the draft answer based on the critique. Follow this format:\n"
        "Reasoning Process: <step-by-step reasoning process>\n"
        "Verification: <verification of the facts>\n"
        "Final Answer: <the improved and verified answer>\n"
    )

    # Create the request to the LLM
    improved_response = chat_completion_request(prompt, model_name)

    # print(f"Improved response: {improved_response}")

    return improved_response


def rate_answer(rating_model, question, answer, episodic_memory, semantic_memory):
    prompt = (
        f"Episodic Memory: {episodic_memory}\n"
        f"Semantic Memory: {semantic_memory}\n"
        "You can use the episodic memory and semantic memory to improve the answer if the user question is related to the episodic memory or semantic memory."
        f"Question: {question}\n"
        f"Answer: {answer}\n\n"
        "As an expert on this topic, please provide a detailed critique of the answer, pointing out every flaw. "
        "Provide only a critique, not a suggested answer. "
        "Then, rate the correctness of the answer on a scale of 0 to 100."
        "Then, provide the confidence score in the correctness rating of the answer on a scale of 0 to 100."
        "The response should be in the following format:\n"
        "Critique: <detailed critique>\n"
        "Rating: <rating>\n"
        "Confidence Score: <confidence score>"
    )

    # Create the request to the LLM
    rating_response = chat_completion_request(prompt, rating_model)

    # Extract the rating
    try:
        rating_match = re.search(r"Rating:\s*(\d+)", rating_response)
        confidence_match = re.search(r"Confidence Score:\s*(\d+)", rating_response)
        if rating_match and confidence_match:
            rating = int(rating_match.group(1))
            confidence = int(confidence_match.group(1))
            if rating > 95:
                rating = 95
            if confidence > 95:
                confidence = 95
            rating = float(rating) / 100
            confidence = float(confidence) / 100
        else:
            raise ValueError("Rating not found in the response")
    except Exception as e:
        print(f"Error extracting rating: {e}")
        rating = 0.0
        confidence = 0.0
    return rating, confidence


class Node:
    def __init__(
        self, question, answer, model_name, parent=None, rating=0.0, confidence=0.0
    ):
        self.question: str = question
        self.answer: str = answer
        self.model_name: str = model_name  # Store the model name instead of instance
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
                exploritation = (self.confidence*self.value)+(1-self.confidence)*(child.value / child.visits)
                exploration = (1/(14.1 * self.confidence)) * math.sqrt(math.log(self.visits) / child.visits)
                weight = exploritation + exploration
            choices_weights.append(weight)
        return self.children[np.argmax(choices_weights)]

    def most_visited_child(self) -> Self:
        return max(self.children, key=lambda child: child.visits)

    def add_child(self, child_node: Self):
        self.children.append(child_node)


class SuperMaster(ReasoningModel):
    def __init__(
        self,
        model_names,
        rating_model,
        episodic_memory: Any | None = None,
        semantic_memory: Any | None = None,
        iterations: int = 2,
        max_depth: int = 3, 
    ):
        self.question: str | None = None
        self.model_names: List[str] = model_names
        self.iterations: int = iterations
        self.max_depth: int = max_depth
        self.rating_model: str = rating_model
        self.episodic_memory: str | None = episodic_memory
        self.semantic_memory: str | None = semantic_memory
        self.root: Node | None = None
        self.current_depth: int = 0

    def think(self, user_question: str) -> str:
        self.question = user_question
        return self.__search()

    def __get_initial_answer(self):
        initial_model = random.choice(self.model_names)
        initial_answer = chat_completion_request(
            self.question,
            initial_model,
        )

        critique = get_critique(
            self.question,
            initial_answer,
            initial_model,
            self.episodic_memory,
            self.semantic_memory,
        )

        improved_answer = improve_answer(
            self.question,
            initial_answer,
            critique,
            initial_model,
            self.episodic_memory,
            self.semantic_memory,
        )
        rating, confidence = rate_answer(
            initial_model,
            self.question,
            improved_answer,
            self.episodic_memory,
            self.semantic_memory,
        )
        return improved_answer, rating, confidence

    def __search(self):
        initial_answer, rating, confidence = self.__get_initial_answer()
        self.root = Node(
            question=self.question,
            answer=initial_answer,
            model_name=random.choice(self.model_names),
            rating=rating,
            confidence=confidence,
        )
        for i in range(self.iterations):
            print(f"\nIteration {i+1}/{self.iterations}")

            self.current_depth = 0  # Reset depth at start of each iteration
            node = self.__select(self.root)
            # print(f"Selected Node: {node.answer}")
            if not node.is_fully_expanded() and self.current_depth < self.max_depth:
                node = self.__expand(node)
                # print(f"\nExpanded Node: {node.answer}")
            self.__backpropagate(node, node.rating)
        # print(f"Visits to most visited child: {self.root.most_visited_child().visits}")
        best_answer = self.root.most_visited_child().answer

        # print(f"Best Answer: {best_answer}")

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

    def __expand(self, node: Node) -> Node:
        for model in self.model_names:
            # Children inherit the parent's model
            child_node = Node(self.question, node.answer, model, parent=node)
            node.add_child(child_node)

            critique = get_critique(
                self.question,
                child_node.answer,
                model,
                self.episodic_memory,
                self.semantic_memory,
            )

            improved_answer = improve_answer(
                self.question,
                child_node.answer,
                critique,
                model,
                self.episodic_memory,
                self.semantic_memory,
            )
            rating, confidence = rate_answer(
                model,
                self.question,
                improved_answer,
                self.episodic_memory,
                self.semantic_memory,
            )

            child_node.answer = improved_answer
            child_node.rating = rating
            child_node.confidence = confidence
        best_child = max(node.children, key=lambda x: x.rating)
        return best_child

    def __backpropagate(self, node: Node, reward: float):
        while node is not None:
            node.visits += 1
            node.value = (node.value * (node.visits - 1) + reward) / node.visits
            node = node.parent
