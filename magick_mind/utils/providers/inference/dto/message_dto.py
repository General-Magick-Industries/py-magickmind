from pydantic import BaseModel


class MessageDTO(BaseModel):
    role: str
    content: str
