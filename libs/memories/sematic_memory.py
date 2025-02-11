import os
from lightrag import LightRAG
from lightrag.base import EmbeddingFunc
from lightrag.llm.openai import gpt_4o_complete, openai_embed
from enum import Enum as PyEnum


class SEMANTIC_MEMORY_TYPE(PyEnum):
    DOMAIN_SPECIFIC_KNOWLEDGE = "domain_specific_knowledge"
    CORE_KNOWLEDGE = "core_knowledge"
    COMPANY_KNOWLEDGE = "company_knowledge"
    PERSONAL_KNOWLEDGE = "personal_knowledge"


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
