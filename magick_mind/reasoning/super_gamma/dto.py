from dataclasses import dataclass
from typing import Optional


@dataclass
class GetCritiqueDTO:
    question: str
    draft_answer: str
    episodic_memory: Optional[str] = None
    semantic_memory: Optional[str] = None
    role: Optional[str] = None


@dataclass
class ImproveAnswerDTO:
    question: str
    draft_answer: str
    critique: str
    episodic_memory: Optional[str] = None
    semantic_memory: Optional[str] = None
    role: Optional[str] = None


@dataclass
class RateAnswerDTO:
    question: str
    answer: str
    episodic_memory: Optional[str] = None
    semantic_memory: Optional[str] = None
    role: Optional[str] = None
