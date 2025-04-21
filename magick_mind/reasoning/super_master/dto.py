from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel


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
    response_format: Optional[BaseModel] = None


@dataclass
class RateAnswerDTO:
    question: str
    answer: str
    episodic_memory: Optional[str] = None
    semantic_memory: Optional[str] = None
    role: Optional[str] = None


class AgentAnswerDTO(BaseModel):
    reasoning_process: str
    verification: str
    final_answer: str | dict
