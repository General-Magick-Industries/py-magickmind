from dataclasses import dataclass


@dataclass
class SemanticMemoryDTO:
    core_knowledge: str
    domain_specific_knowledge: str
    company_knowledge: str
    personal_knowledge: str
