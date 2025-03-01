from enum import Enum
from typing import Optional, List


class ChatMessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage:

    def __init__(
        self,
        id: int,
        text: str,
        role: ChatMessageRole,
        parent: Optional["ChatMessage"] = None,
        is_completed: bool = True,
    ):
        self.id = id
        self.text = text
        self.role = role
        self.parent = parent
        self.is_completed = is_completed
        self.error: Optional[Exception] = None
        self.childs: List["ChatMessage"] = []
