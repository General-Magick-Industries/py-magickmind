from typing import List
from lightrag import QueryParam
from libs.reasoning.mcts import MCTS
from libs.memories.sematic_memory import get_semantic_memory, SEMANTIC_MEMORY_TYPE

DEFAULT_RATING_MODEL = "anthropic/claude-3-5-sonnet-20240620"


class SuperBrain:
    def __init__(
        self,
        include_semetic_memory: bool = False,
        rating_model: str = DEFAULT_RATING_MODEL,
    ):
        self.include_semetic_memory = include_semetic_memory
        self.rating_model = rating_model

        if include_semetic_memory:
            self.domain_knowledge = get_semantic_memory(
                SEMANTIC_MEMORY_TYPE.DOMAIN_SPECIFIC_KNOWLEDGE)

            self.core_knowledge = get_semantic_memory(
                SEMANTIC_MEMORY_TYPE.CORE_KNOWLEDGE)

            self.company_knowledge = get_semantic_memory(
                SEMANTIC_MEMORY_TYPE.COMPANY_KNOWLEDGE)

            self.personal_knowledge = get_semantic_memory(
                SEMANTIC_MEMORY_TYPE.PERSONAL_KNOWLEDGE)
        else:
            self.domain_knowledge = None
            self.core_knowledge = None
            self.company_knowledge = None
            self.personal_knowledge = None

    def think(
        self,
        question: str,
        small_brains: List[str] = ["openai/gpt-4o-mini",
                                   "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20240620"],
        seed_answers: List[str] = ["I don't know.", "I am not sure."],
        iterations: int = 3,
        max_depth: int = 4,
    ) -> str:
        if self.include_semetic_memory:
            domain_knowledge = self.domain_knowledge.query(
                question, param=QueryParam(mode="hybrid"))

            core_knowledge = self.core_knowledge.query(
                question, param=QueryParam(mode="hybrid"))

            company_knowledge = self.company_knowledge.query(
                question, param=QueryParam(mode="hybrid"))

            personal_knowledge = self.personal_knowledge.query(
                question, param=QueryParam(mode="hybrid"))

            semantic_memory = f"Domain Knowledge: {domain_knowledge}\n" \
                f"Core Knowledge: {core_knowledge}\n" \
                f"Company Knowledge: {company_knowledge}\n" \
                f"Personal Knowledge: {personal_knowledge}\n"

            print(f"Sematic Memory: {semantic_memory}")

            mcts = MCTS(
                question=question,
                seed_answers=seed_answers,
                model_names=small_brains,
                rating_model=self.rating_model,
                iterations=iterations,
                max_depth=max_depth,
                semantic_memory=semantic_memory
            )

            answer = mcts.search()
            return answer

    async def insert(self, file_path: str, type: SEMANTIC_MEMORY_TYPE):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            # Fallback to read as binary and decode with a more permissive encoding
            with open(file_path, "rb") as file:
                content = file.read().decode('utf-8', errors='ignore')

        match type:
            case SEMANTIC_MEMORY_TYPE.DOMAIN_SPECIFIC_KNOWLEDGE:
                await self.domain_knowledge.ainsert(content)
            case SEMANTIC_MEMORY_TYPE.CORE_KNOWLEDGE:
                await self.core_knowledge.ainsert(content)
            case SEMANTIC_MEMORY_TYPE.COMPANY_KNOWLEDGE:
                await self.company_knowledge.ainsert(content)
            case SEMANTIC_MEMORY_TYPE.PERSONAL_KNOWLEDGE:
                await self.personal_knowledge.ainsert(content)
