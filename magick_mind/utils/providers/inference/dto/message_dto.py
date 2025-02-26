from dataclasses import dataclass
from magick_mind.utils.providers.inference.constants import MessageRole


@dataclass
class MessageDTO:
    role: MessageRole
    content: str
