import os
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from lightrag import LightRAG, QueryParam
from lightrag.base import EmbeddingFunc
from lightrag.llm.openai import openai_embed, gpt_4o_complete
from magick_mind.memories.semantic_memory.dto.semantic_memory_dto import (
    SemanticMemoryDTO,
)


@dataclass
class SemanticMemory:
    llm_base_url: Optional[str] = field(default=None)
    llm_api_key: Optional[str] = field(default=None)
    root_directory: Optional[str] = field(default="./semantic_working_dir")
    directory: Optional[str] = field(default=None)
    enable_cache: bool = field(default=True)

    def __post_init__(self):
        self.working_directory = self.root_directory

        if not os.path.exists(self.working_directory):
            os.makedirs(self.working_directory)

        if self.directory:
            self.working_directory += "/" + self.directory
            if not os.path.exists(self.working_directory):
                os.makedirs(self.working_directory)

    async def build(self):
        CORE_KNOWLEDGE_DIRECTORY = self.working_directory + "/core_knowledge"
        DOMAIN_SPECIFIC_KNOWLEDGE_DIRECTORY = (
            self.working_directory + "/domain_specific_knowledge"
        )
        COMPANY_KNOWLEDGE_DIRECTORY = self.working_directory + "/company_knowledge"
        PERSONAL_KNOWLEDGE_DIRECTORY = self.working_directory + "/personal_knowledge"

        if not os.path.exists(CORE_KNOWLEDGE_DIRECTORY):
            os.makedirs(CORE_KNOWLEDGE_DIRECTORY)
        if not os.path.exists(DOMAIN_SPECIFIC_KNOWLEDGE_DIRECTORY):
            os.makedirs(DOMAIN_SPECIFIC_KNOWLEDGE_DIRECTORY)
        if not os.path.exists(COMPANY_KNOWLEDGE_DIRECTORY):
            os.makedirs(COMPANY_KNOWLEDGE_DIRECTORY)
        if not os.path.exists(PERSONAL_KNOWLEDGE_DIRECTORY):
            os.makedirs(PERSONAL_KNOWLEDGE_DIRECTORY)

        (
            self.core_knowledge,
            self.domain_specific_knowledge,
            self.company_knowledge,
            self.personal_knowledge,
        ) = await asyncio.gather(
            self.create_rag(CORE_KNOWLEDGE_DIRECTORY),
            self.create_rag(DOMAIN_SPECIFIC_KNOWLEDGE_DIRECTORY),
            self.create_rag(COMPANY_KNOWLEDGE_DIRECTORY),
            self.create_rag(PERSONAL_KNOWLEDGE_DIRECTORY),
        )

    async def create_rag(self, directory: str) -> LightRAG:
        return LightRAG(
            working_dir=directory,
            enable_llm_cache=self.enable_cache,
            llm_model_func=lambda *args, **kwargs: get_mod_open_ai_complete_func(
                *args, base_url=self.llm_base_url, api_key=self.llm_api_key, **kwargs
            ),
            embedding_func=EmbeddingFunc(
                embedding_dim=3072,
                max_token_size=8192,
                func=lambda texts: openai_embed(texts, model="text-embedding-3-large"),
            ),
        )

    async def recall(self, user_query: str) -> SemanticMemoryDTO:
        (
            domain_knowledge,
            core_knowledge,
            company_knowledge,
            personal_knowledge,
        ) = await asyncio.gather(
            self.domain_specific_knowledge.aquery(
                user_query, param=QueryParam(mode="hybrid")
            ),
            self.core_knowledge.aquery(user_query, param=QueryParam(mode="hybrid")),
            self.company_knowledge.aquery(user_query, param=QueryParam(mode="hybrid")),
            self.personal_knowledge.aquery(user_query, param=QueryParam(mode="hybrid")),
        )

        return SemanticMemoryDTO(
            domain_specific_knowledge=domain_knowledge,
            core_knowledge=core_knowledge,
            company_knowledge=company_knowledge,
            personal_knowledge=personal_knowledge,
        )


async def get_mod_open_ai_complete_func(
    *args, base_url: Optional[str] = None, api_key: Optional[str] = None, **kwargs
):
    if not base_url:
        base_url = os.getenv("OPENAI_BASE_URL")

    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    return await gpt_4o_complete(base_url=base_url, api_key=api_key, *args, **kwargs)
