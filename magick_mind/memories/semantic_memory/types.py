from enum import Enum as PyEnum


class SemanticMemoryType(PyEnum):
    DOMAIN_SPECIFIC_KNOWLEDGE = "domain_specific_knowledge"
    CORE_KNOWLEDGE = "core_knowledge"
    COMPANY_KNOWLEDGE = "company_knowledge"
    PERSONAL_KNOWLEDGE = "personal_knowledge"
