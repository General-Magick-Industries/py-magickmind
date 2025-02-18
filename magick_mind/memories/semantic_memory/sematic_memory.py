import os
from dataclasses import dataclass, field
from typing import Optional
from lightrag import LightRAG, QueryParam
from lightrag.base import EmbeddingFunc
from lightrag.llm.openai import gpt_4o_complete, openai_embed
from magick_mind.memories.semantic_memory.types import SEMANTIC_MEMORY_TYPE


@dataclass
class SemanticMemory:
    directory: Optional[str] = field(default=None)

    def __post_init__(self):
        self.working_directory = "./semantic_memory"

        if not os.path.exists(self.working_directory):
            os.makedirs(self.working_directory)

        if self.directory:
            self.working_directory += self.directory
            os.makedirs(self.working_directory)

        CORE_KNOWLEDGE_DIRECTORY = self.working_directory + "/core_knowledge"
        DOMAIN_SPECIFIC_KNOWLEDGE_DIRECTORY = self.working_directory + \
            "/domain_specific_knowledge"
        COMPANY_KNOWLEDGE_DIRECTORY = self.working_directory + "/company_knowledge"
        PERSONAL_KNOWLEDGE_DIRECTORY = self.working_directory + "/personal_knowledge"

        os.makedirs(CORE_KNOWLEDGE_DIRECTORY)
        os.makedirs(DOMAIN_SPECIFIC_KNOWLEDGE_DIRECTORY)
        os.makedirs(COMPANY_KNOWLEDGE_DIRECTORY)
        os.makedirs(PERSONAL_KNOWLEDGE_DIRECTORY)

        self.core_knowledge = LightRAG(
            working_dir=CORE_KNOWLEDGE_DIRECTORY,
            enable_llm_cache=False,
            llm_model_func=gpt_4o_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=lambda texts: openai_embed(
                    texts, model="text-embedding-3-small")
            ),
        )

        self.domain_specific_knowledge = LightRAG(
            working_dir=DOMAIN_SPECIFIC_KNOWLEDGE_DIRECTORY,
            enable_llm_cache=False,
            llm_model_func=gpt_4o_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=lambda texts: openai_embed(
                    texts, model="text-embedding-3-small")
            ),
        )

        self.company_knowledge = LightRAG(
            working_dir=COMPANY_KNOWLEDGE_DIRECTORY,
            enable_llm_cache=False,
            llm_model_func=gpt_4o_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=lambda texts: openai_embed(
                    texts, model="text-embedding-3-small")
            ),
        )

        self.personal_knowledge = LightRAG(
            working_dir=PERSONAL_KNOWLEDGE_DIRECTORY,
            enable_llm_cache=False,
            llm_model_func=gpt_4o_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8192,
                func=lambda texts: openai_embed(
                    texts, model="text-embedding-3-small")
            ),
        )

    def query(
        self,
        user_query: str
    ) -> str:
        domain_knowledge = self.domain_specific_knowledge.query(
            user_query, param=QueryParam(mode="hybrid"))

        core_knowledge = self.core_knowledge.query(
            user_query, param=QueryParam(mode="hybrid"))

        company_knowledge = self.company_knowledge.query(
            user_query, param=QueryParam(mode="hybrid"))

        personal_knowledge = self.personal_knowledge.query(
            user_query, param=QueryParam(mode="hybrid"))

        semantic_memory = f"Domain Knowledge: {domain_knowledge}\n" \
            f"Core Knowledge: {core_knowledge}\n" \
            f"Company Knowledge: {company_knowledge}\n" \
            f"Personal Knowledge: {personal_knowledge}\n"

        return semantic_memory


def get_semantic_memory(type: SEMANTIC_MEMORY_TYPE) -> LightRAG:

    WORKING_DIRECTORY = "./semantic_memory"

    if not os.path.exists(WORKING_DIRECTORY):
        os.makedirs(WORKING_DIRECTORY)

    match type:
        case SEMANTIC_MEMORY_TYPE.CORE_KNOWLEDGE:
            WORKING_DIRECTORY = WORKING_DIRECTORY + "/core_knowledge"
        case SEMANTIC_MEMORY_TYPE.COMPANY_KNOWLEDGE:
            WORKING_DIRECTORY = WORKING_DIRECTORY + "/company_knowledge"
        case SEMANTIC_MEMORY_TYPE.PERSONAL_KNOWLEDGE:
            WORKING_DIRECTORY = WORKING_DIRECTORY + "/personal_knowledge"
        case SEMANTIC_MEMORY_TYPE.DOMAIN_SPECIFIC_KNOWLEDGE:
            WORKING_DIRECTORY = WORKING_DIRECTORY + "/domain_specific_knowledge"

    if not os.path.exists(WORKING_DIRECTORY):
        os.makedirs(WORKING_DIRECTORY)

    return LightRAG(
        working_dir=WORKING_DIRECTORY,
        enable_llm_cache=False,
        llm_model_func=gpt_4o_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=8192,
            func=lambda texts: openai_embed(
                texts, model="text-embedding-3-small")
        ),
    )
