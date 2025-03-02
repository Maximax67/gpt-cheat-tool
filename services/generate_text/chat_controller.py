import threading
from typing import List, Optional, Callable, Tuple

from services.generate_text.message import ChatMessage, ChatMessageRole
from services.generate_text.text_generator import (
    AbstractTextGenerator,
    ChatMessageDict,
)

from utils.prompts import CHAT_PROMPT


class ChatController:

    def __init__(
        self,
        text_generator: AbstractTextGenerator,
        system_message: Optional[str] = None,
        default_message_context: Optional[int] = None,
    ):
        self.text_generator = text_generator
        self.default_message_context = default_message_context

        if system_message is None:
            system_message = CHAT_PROMPT

        system_message = ChatMessage(0, system_message, ChatMessageRole.SYSTEM, None)
        self.messages: List[ChatMessage] = [system_message]

    def get_message(self, message_id: int) -> ChatMessage:
        if message_id < 0:
            raise ValueError("message_id < 0")

        if message_id >= len(self.messages):
            raise ValueError("message with message_id not found")

        return self.messages[message_id]

    def clear_chat(self) -> None:
        system_message = self.messages[0]
        self.messages = [system_message]

    def _form_messages_list(
        self, message: ChatMessage, max_length: Optional[int]
    ) -> List[ChatMessageDict]:
        message_list: List[ChatMessageDict] = []
        current_message = message

        while (
            current_message
            and current_message.role != ChatMessageRole.SYSTEM
            and (max_length is None or len(message_list) < max_length)
        ):
            message_list.append(
                {
                    "role": current_message.role.value,
                    "content": current_message.text,
                }
            )
            current_message = current_message.parent

        system_message_text = self.messages[0].text
        if system_message_text:
            message_list.append(
                {
                    "role": ChatMessageRole.SYSTEM.value,
                    "content": system_message_text,
                }
            )

        message_list.reverse()

        return message_list

    def _add_message(
        self, text: str, role: ChatMessageRole, parent: Optional[ChatMessage]
    ) -> ChatMessage:
        message_id = len(self.messages)
        if not parent:
            parent = self.messages[0]

        message = ChatMessage(message_id, text, role, parent)
        parent.childs.append(message)
        self.messages.append(message)

        return message

    def _get_assistant_message_by_id(self, assistant_message_id: int) -> ChatMessage:
        if assistant_message_id < 0 or assistant_message_id >= len(self.messages):
            raise ValueError("Message with id assistant_message_id not found")

        assistant_message = self.messages[assistant_message_id]
        if assistant_message.role != ChatMessageRole.ASSISTANT:
            raise ValueError(
                "Message with id assistant_message_id is not an assistant message"
            )

        return assistant_message

    def _get_user_message_by_id(self, user_message_id: int) -> ChatMessage:
        if user_message_id < 0 or user_message_id >= len(self.messages):
            raise ValueError("Message with id user_message_id not found")

        user_message = self.messages[user_message_id]
        if user_message.role != ChatMessageRole.USER:
            raise ValueError("Message with id user_message_id is not an user message")

        return user_message

    def _generate_response_for_message(
        self,
        message: ChatMessage,
        callback: Callable[[int], None],
        completed_callback: Callable[[int], None],
        message_context: Optional[int],
        model: Optional[str],
    ) -> ChatMessage:
        if message_context is None:
            message_context = self.default_message_context

        chat_history = self._form_messages_list(message, message_context)
        response_message = self._add_message("", ChatMessageRole.ASSISTANT, message)

        def internal_callback(text_chunk: str):
            response_message.text += text_chunk
            callback(response_message.id)

        def internal_completed_callback(exception: Optional[Exception]):
            response_message.error = exception
            completed_callback(response_message.id)

        threading.Thread(
            target=self.text_generator.generate_text,
            args=(chat_history, internal_callback, internal_completed_callback, model),
        ).start()

        return response_message

    def generate_response(
        self,
        text: str,
        callback: Callable[[int], None],
        completed_callback: Callable[[int], None],
        assistant_message_id: Optional[int] = None,
        message_context: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Tuple[ChatMessage, ChatMessage]:
        if message_context and message_context < 1:
            raise ValueError("message_context should be >= 1")

        if assistant_message_id:
            assistant_message = self._get_assistant_message_by_id(assistant_message_id)
        else:
            assistant_message = None

        user_message = self._add_message(text, ChatMessageRole.USER, assistant_message)
        response_message = self._generate_response_for_message(
            user_message, callback, completed_callback, message_context, model
        )

        return user_message, response_message

    def regenerate_message(
        self,
        assistant_message_id: int,
        callback: Callable[[int], None],
        completed_callback: Callable[[int], None],
        message_context: Optional[int] = None,
        model: Optional[str] = None,
    ) -> ChatMessage:
        if not self.messages:
            raise Exception("No messages to regenerate.")

        if message_context and message_context < 1:
            raise ValueError("message_context should be >= 1")

        assistant_message = self._get_assistant_message_by_id(assistant_message_id)
        user_message = assistant_message.parent
        if user_message is None or user_message.role != ChatMessageRole.USER:
            raise ValueError("Message does not have a parent user message")

        return self._generate_response_for_message(
            user_message, callback, completed_callback, message_context, model
        )

    def change_user_message(
        self,
        text: str,
        user_message_id: int,
        callback: Callable[[int], None],
        completed_callback: Callable[[int], None],
        message_context: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Tuple[ChatMessage, ChatMessage]:
        if not self.messages:
            raise Exception("No messages to change.")

        if message_context and message_context < 1:
            raise ValueError("message_context should be >= 1")

        user_message = self._get_user_message_by_id(user_message_id)
        user_message_parent = user_message.parent
        new_user_message = self._add_message(
            text, ChatMessageRole.USER, user_message_parent
        )

        response_message = self._generate_response_for_message(
            new_user_message, callback, completed_callback, message_context, model
        )

        return new_user_message, response_message
