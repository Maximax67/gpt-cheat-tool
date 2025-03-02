from typing import Dict, Optional, Tuple
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QTimer

from services.generate_text.message import ChatMessage
from widgets.chat_message import ChatMessageWidget
from utils.logging import logger


class ChatMessagesListWidget(QScrollArea):
    regenerate_requested = Signal(ChatMessage)
    message_switch_signal = Signal(ChatMessage)
    edit_message_signal = Signal(ChatMessage, str)

    def __init__(self):
        super().__init__()
        self._messages: Dict[int, Tuple[ChatMessageWidget, Optional[int]]] = {}
        self.last_message_widget: Optional[ChatMessageWidget] = None
        self._setup_ui()
        self.update_theme_ui()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.container.setLayout(self.layout)
        self.setWidget(self.container)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def add_message(
        self, message: ChatMessage, scroll: bool = True
    ) -> ChatMessageWidget:
        message_widget = ChatMessageWidget(message)
        message_widget.regenerate_requested.connect(self.regenerate_requested.emit)
        message_widget.message_switch_signal.connect(self.message_switch_signal.emit)
        message_widget.edit_message_signal.connect(self.edit_message_signal.emit)

        if self.last_message_widget:
            last_message_id = self.last_message_widget.message.id
            self._messages[last_message_id] = (
                self.last_message_widget,
                message_widget.message.id,
            )

        self.last_message_widget = message_widget

        self._messages[message.id] = (message_widget, None)
        self.layout.addWidget(message_widget)

        logger.debug(f"Chat message added: {message.id}")

        if scroll:
            self.scroll_to_bottom()

        return message_widget

    def update_message_text(self, message_id: int):
        message_widgets = self._messages.get(message_id)
        if message_widgets:
            message_widgets[0].update_text()

    def _remove_widget(self, widget: ChatMessageWidget):
        self.layout.removeWidget(widget)
        widget.deleteLater()
        logger.debug(f"Message deleted: {widget.message.id}")

    def delete_message_thread(self, message_id: int):
        message_data = self._messages.get(message_id)
        if message_data is None:
            return

        message_widget, current_message_id = message_data
        self.last_message_widget = message_widget

        while current_message_id:
            current_message_data = self._messages.pop(current_message_id, None)
            if current_message_data is None:
                return

            current_message, next_message_id = current_message_data
            self._remove_widget(current_message)
            if next_message_id:
                current_message_id = next_message_id

        logger.debug(f"Message thread deleted: {message_id}")

    def clear_chat(self):
        self._messages = {}
        self.last_message_widget = None
        for _ in range(self.layout.count()):
            widget: ChatMessageWidget = self.layout.itemAt(0).widget()
            if widget:
                self._remove_widget(widget)

        logger.debug("Chat cleared")

    def scroll_to_bottom(self):
        QTimer.singleShot(
            50,
            lambda: self.verticalScrollBar().setValue(
                self.verticalScrollBar().maximum()
            ),
        )

    def update_theme_ui(self):
        for i in range(self.layout.count()):
            widget: ChatMessageWidget = self.layout.itemAt(i).widget()
            if widget:
                widget.update_theme_ui()

    def get_last_message(self) -> Optional[ChatMessage]:
        return self.last_message_widget.message if self.last_message_widget else None
