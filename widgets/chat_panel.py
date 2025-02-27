from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
)
from PySide6.QtCore import QMetaObject, Qt, Q_ARG, Slot

from services.generate_text.ChatController import ChatController

from services.generate_text.Message import ChatMessage, ChatMessageRole
from ui.icons import Icon, get_icon
from widgets.chat_messages_list import ChatMessagesListWidget


class ChatPanel(QWidget):

    def __init__(
        self,
        chat_controller: ChatController,
    ):
        super().__init__()
        self.chat_controller = chat_controller
        self.is_generating = False
        self.setup_ui()
        self.update_theme_ui()

    def setup_ui(self):
        # Main vertical layout for the widget
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        self.chat_messages_list = ChatMessagesListWidget()
        self.chat_messages_list.regenerate_requested.connect(self._handle_regenerate)
        self.chat_messages_list.message_switch_signal.connect(
            self._handle_switch_message
        )
        self.layout.addWidget(self.chat_messages_list)

        # Input area with dynamically resizing text edit and send button
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)

        self.input_text = QTextEdit(self)
        self.input_text.setPlaceholderText("Type your message...")
        self.input_text.setFixedHeight(35)
        self.input_text.textChanged.connect(self._adjust_input_height)

        self.send_button = QPushButton()
        self.send_button.setFixedHeight(35)
        self.send_button.setToolTip("Send text")
        self.send_button.clicked.connect(self._handle_send_button_click)

        input_layout.addWidget(self.input_text)
        input_layout.addWidget(self.send_button)
        self.layout.addLayout(input_layout)

    def _adjust_input_height(self):
        doc_height = self.input_text.document().size().height()
        new_height = max(35, min(150, doc_height + 10))
        self.input_text.setFixedHeight(new_height)

    @Slot(int)
    def update_message(self, id: int):
        self.chat_messages_list.update_message_text(id)

    @Slot(int)
    def complete_message(self, id: int):
        self.chat_messages_list.update_message_text(id)
        self.is_generating = False
        self.send_button.setDisabled(False)

    def _handle_update_message(self, id: int):
        QMetaObject.invokeMethod(
            self, "update_message", Qt.QueuedConnection, Q_ARG(int, id)
        )

    def _handle_complete_message(self, id: int):
        QMetaObject.invokeMethod(
            self, "complete_message", Qt.QueuedConnection, Q_ARG(int, id)
        )

    def _handle_send_button_click(self):
        if not self.is_generating:
            self.send_message(self.get_prompt_text())

    def _handle_regenerate(self, message: ChatMessage):
        parent = message.parent
        if parent is None:
            return

        if parent.role == ChatMessageRole.SYSTEM:
            self.chat_messages_list.clear_chat()
        else:
            self.chat_messages_list.delete_message_thread(parent.id)

        self.is_generating = True
        self.send_button.setDisabled(True)
        response_message = self.chat_controller.regenerate_message(
            message.id,
            self._handle_update_message,
            self._handle_complete_message,
        )
        self.chat_messages_list.add_message(response_message)

    def _handle_switch_message(self, message: ChatMessage):
        parent = message.parent
        if parent is None:
            return

        if parent.role == ChatMessageRole.SYSTEM:
            self.chat_messages_list.clear_chat()
        else:
            self.chat_messages_list.delete_message_thread(parent.id)

        self.chat_messages_list.add_message(message)

        current_message = message
        while len(current_message.childs):
            current_message = current_message.childs[-1]
            self.chat_messages_list.add_message(current_message)

    def send_message(self, text: str):
        text = text.strip()
        if text:
            self.add_user_message(text)
            self.clear_prompt()

    def add_user_message(self, text: str):
        last_message = self.chat_messages_list.get_last_message()
        assistant_message_id = last_message.id if last_message else None

        self.is_generating = True
        self.send_button.setDisabled(True)
        user_message, response_message = self.chat_controller.generate_response(
            text,
            self._handle_update_message,
            self._handle_complete_message,
            assistant_message_id,
        )

        self.chat_messages_list.add_message(user_message)
        self.chat_messages_list.add_message(response_message)

    def get_prompt_text(self):
        return self.input_text.toPlainText().strip()

    def clear_prompt(self):
        self.input_text.clear()

    def update_theme_ui(self):
        self.send_button.setIcon(get_icon(Icon.SEND))
        self.chat_messages_list.update_theme_ui()
