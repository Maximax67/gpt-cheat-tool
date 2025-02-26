from enum import Enum
from typing import Optional, List


class ChatMessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message:
    def __init__(
        self,
        id: int,
        text: str,
        role: ChatMessageRole,
        parent: Optional["Message"] = None,
    ):
        self.id = id
        self.text = text
        self.role = role
        self.parent = parent
        self.error: Optional[Exception] = None
        self.childs: List["Message"] = []
