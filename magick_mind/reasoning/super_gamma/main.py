import os
from typing import Any, List

import math
import random
import numpy as np
import re
from litellm import completion
from ..interfaces import ReasoningModel


max_children = 3


def chat_completion_request(prompt, model_name):
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    # Create chat completions using LiteLLM's completion function
    chat_response = completion(
        model=model_name,
        messages=messages,
        temperature=1.0,
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


def improve_answer(question, draft_answer, critique, model_name, episodic_memory, semantic_memory):
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
        "Then, rate the answer on a scale of 0 to 100. "
        "The response should be in the following format:\n"
        "Critique: <detailed critique>\n"
        "Rating: <rating>"
    )

    # Create the request to the LLM
    rating_response = chat_completion_request(
        prompt, rating_model)

    # Extract the rating
    try:
        match = re.search(r'Rating:\s*(\d+)', rating_response)
        if match:
            rating = int(match.group(1))
            if rating > 95:
                rating = 95
            rating = float(rating) / 100
        else:
            raise ValueError("Rating not found in the response")
    except Exception as e:
        print(f"Error extracting rating: {e}")
        # print(f"Rating response was: {rating_response}")
        rating = 0.0

    # print(f"\nRating: {rating}")
    # print(rating_response)
    return rating


class Node:
    def __init__(self, question, answer, model_name, parent=None):
        self.question = question
        self.answer = answer
        self.model_name = model_name  # Store the model name instead of instance
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0.0

    def is_fully_expanded(self):
        return len(self.children) >= max_children

    def best_child(self, exploration_weight=1.41):
        choices_weights = []
        for child in self.children:
            if child.visits == 0:
                weight = float('inf')  # Prioritize unexplored nodes
            else:
                weight = (child.value / child.visits) + exploration_weight * \
                    math.sqrt((2 * math.log(self.visits) / child.visits))
            choices_weights.append(weight)
        return self.children[np.argmax(choices_weights)]

    def most_visited_child(self):
        return max(self.children, key=lambda child: child.visits)

    def add_child(self, child_node):
        self.children.append(child_node)


class SuperGamma(ReasoningModel):
    def __init__(
        self,
        question: str | None,
        model_names,
        rating_model,
        seed_answers: List[str] = [
            "I don't know",
            "I don't have knowledge about this",
            "I don't have information about this",
        ],
        episodic_memory: Any | None = None,
        semantic_memory: Any | None = None,
        iterations=2,
        max_depth=3
    ):
        self.question = question
        self.seed_answers = seed_answers
        self.model_names = model_names
        self.iterations = iterations
        self.max_depth = max_depth
        self.rating_model = rating_model
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        initial_model = random.choice(model_names)
        self.root = Node(question, random.choice(seed_answers), initial_model)
        self.current_depth = 0

    def think(
        self,
        user_question: str
    ) -> str:
        self.question = user_question
        return self.__search()

    def __search(self):
        for i in range(self.iterations):
            print(f"\nIteration {i+1}/{self.iterations}")

            self.current_depth = 0  # Reset depth at start of each iteration
            node = self.__select(self.root)
            # print(f"Selected Node: {node.answer}")
            if not node.is_fully_expanded() and self.current_depth < self.max_depth:
                node = self.__expand(node)
                # print(f"\nExpanded Node: {node.answer}")
            reward = self.__simulate(node)
            # print(f"\nSimulated Reward: {reward}")
            self.__backpropagate(node, reward)
        # print(f"Visits to most visited child: {self.root.most_visited_child().visits}")
        best_answer = self.root.most_visited_child().answer

        # print(f"Best Answer: {best_answer}")

        match = re.search(r'Final Answer:(.*?)(?=\Z)', best_answer, re.DOTALL)

        if match:
            best_answer = match.group(1).strip()
        else:
            # If no "Final Answer:" found, return the original answer
            best_answer = best_answer.strip()

        return best_answer

    def __select(self, node):
        while node.is_fully_expanded() and node.children:
            self.current_depth += 1
            if self.current_depth >= self.max_depth:
                break
            node = node.best_child()
        return node

    def __expand(self, node):
        for j in range(max_children - len(node.children)):
            # Children inherit the parent's model
            child_node = Node(self.question, node.answer,
                              node.model_name, parent=node)
            node.add_child(child_node)

            critique = get_critique(
                self.question, child_node.answer, child_node.model_name, self.episodic_memory, self.semantic_memory)
            # print(f"\n--Critique {j}--\n{critique}")

            improved_answer = improve_answer(
                self.question,
                child_node.answer,
                critique,
                child_node.model_name,
                self.episodic_memory,
                self.semantic_memory
            )
            # print(f"\n--Improved answer {j}--\n{improved_answer}")

            child_node.answer = improved_answer
        return random.choice(node.children)

    def __simulate(self, node):
        rating = rate_answer(
            self.rating_model, self.question, node.answer, self.episodic_memory, self.semantic_memory)
        return rating

    def __backpropagate(self, node, reward):
        while node is not None:
            node.visits += 1
            node.value += reward
            # print(f"Backpropagating Node: {node.answer}, Visits: {node.visits}, Value: {node.value}")
            node = node.parent
