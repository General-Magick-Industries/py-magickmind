from dataclasses import dataclass
from pydantic import BaseModel
from typing import List


@dataclass
class EpisodicMemoryResponseDTO:
    today_conversation: str
    previous_day_conversation: str
    previous_week_conversation: str
    previous_month_conversation: str
    previous_year_conversation: str
    similar_conversations: str


class MessageDTO(BaseModel):
    role: str
    content: str


class PriorConversation(BaseModel):
    messages: List[MessageDTO] = []
