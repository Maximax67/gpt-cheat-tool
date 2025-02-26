import threading
from typing import List, Optional, Callable

from services.generate_text.Message import Message, ChatMessageRole
from services.generate_text.TextGenerator import (
    AbstractTextGenerator,
    ChatMessageDict,
)


class ChatController:

    def __init__(
        self, generator: AbstractTextGenerator, system_message: Optional[str] = None
    ):
        self.generator = generator
        self.system_message = system_message
        self.messages: List[Message] = []
        self.root_messages_ids: List[int] = []

    def get_messages_count(self) -> int:
        return len(self.messages)

    def clear_chat(self) -> None:
        self.messages.clear()
        self.root_messages_ids.clear()

    def _form_messages_list(
        self, message: Message, max_length: Optional[int]
    ) -> List[ChatMessageDict]:
        message_list = []
        current_message = message

        while current_message and (
            max_length is None or len(message_list) < max_length
        ):
            message_list.append(current_message)
            current_message = current_message.parent

        if self.system_message:
            message_list.append(
                {"role": ChatMessageRole.SYSTEM.value, "content": self.system_message}
            )

        message_list.reverse()

        return message_list

    def _add_message(
        self, text: str, role: ChatMessageRole, parent: Optional[Message]
    ) -> Message:
        message_id = len(self.messages)
        message = Message(message_id, text, role, parent)
        self.messages.append(message)

        if parent is None:
            self.root_messages_ids.append(message.id)

        return message

    def _get_assistant_message_by_id(self, assistant_message_id: int) -> Message:
        if assistant_message_id < 0 or assistant_message_id >= len(self.messages):
            raise ValueError("Message with id assistant_message_id not found")

        assistant_message = self.messages[assistant_message_id]
        if assistant_message.role != ChatMessageRole.ASSISTANT:
            raise ValueError(
                "Message with id assistant_message_id is not an assistant message"
            )

        return assistant_message

    def _get_user_message_by_id(self, user_message_id: int) -> Message:
        if user_message_id < 0 or user_message_id >= len(self.messages):
            raise ValueError("Message with id user_message_id not found")

        user_message = self.messages[user_message_id]
        if user_message.role != ChatMessageRole.ASSISTANT:
            raise ValueError("Message with id user_message_id is not an user message")

        return user_message

    def _generate_response_for_message(
        self,
        message: Message,
        callback: Callable[[str], None],
        completed_callback: Callable[[Optional[Exception]], None],
        send_n_messages: Optional[int],
        model: Optional[str],
    ) -> None:
        chat_history = self._form_messages_list(message, send_n_messages)
        response_message = self._add_message("", ChatMessageRole.ASSISTANT, message)
        message.childs.append(response_message)

        def internal_callback(response_text: str):
            response_message.text += response_text
            callback(response_text)

        def internal_completed_callback(exception: Optional[Exception]):
            response_message.error = exception
            completed_callback(exception)

        threading.Thread(
            target=self.generator.generate_text,
            args=(chat_history, internal_callback, internal_completed_callback, model),
        ).start()

    def generate_response(
        self,
        text: str,
        callback: Callable[[str], None],
        completed_callback: Callable[[Optional[Exception]], None],
        assistant_message_id: Optional[int] = None,
        send_n_messages: Optional[int] = None,
        model: Optional[str] = None,
    ) -> None:
        if send_n_messages and send_n_messages < 1:
            raise ValueError("send_n_messages should be >= 1")

        if assistant_message_id:
            assistant_message = self._get_assistant_message_by_id(assistant_message_id)
        else:
            assistant_message = None

        user_message = self._add_message(text, ChatMessageRole.USER, assistant_message)
        if user_message.parent is None:
            self.root_messages_ids.append(user_message.id)

        self._generate_response_for_message(
            user_message, callback, completed_callback, send_n_messages, model
        )

    def regenerate_message(
        self,
        assistant_message_id: int,
        callback: Callable[[str], None],
        completed_callback: Callable[[Optional[Exception]], None],
        send_n_messages: Optional[int] = None,
        model: Optional[str] = None,
    ) -> None:
        if not self.messages:
            raise Exception("No messages to regenerate.")

        if send_n_messages and send_n_messages < 1:
            raise ValueError("send_n_messages should be >= 1")

        assistant_message = self._get_assistant_message_by_id(assistant_message_id)
        user_message = assistant_message.parent
        if user_message is None or user_message.role != ChatMessageRole.USER:
            raise ValueError("Message does not have a parent user message")

        self._generate_response_for_message(
            user_message, callback, completed_callback, send_n_messages, model
        )

    def change_user_message(
        self,
        text: str,
        user_message_id: int,
        callback: Callable[[str], None],
        completed_callback: Callable[[Optional[Exception]], None],
        send_n_messages: Optional[int] = None,
        model: Optional[str] = None,
    ) -> None:
        if not self.messages:
            raise Exception("No messages to change.")

        if send_n_messages and send_n_messages < 1:
            raise ValueError("send_n_messages should be >= 1")

        user_message = self._get_user_message_by_id(user_message_id)
        user_message_parent = user_message.parent
        new_user_message = self._add_message(
            text, ChatMessageRole.USER, user_message_parent
        )

        if user_message_parent is None:
            self.root_messages_ids.append(new_user_message.id)
        else:
            user_message_parent.childs.append(new_user_message)

        self._generate_response_for_message(
            new_user_message, callback, completed_callback, send_n_messages, model
        )
