from enum import Enum as PyEnum


class MessageRole(PyEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
