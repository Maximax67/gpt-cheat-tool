import threading
import markdown
from typing import List, Optional, Tuple

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
    QApplication,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from services.generate_text.Message import ChatMessageRole
from services.generate_text.TextGenerator import AbstractTextGenerator
from services.record_audio.AudioSourceType import AudioSourceType

from ui.icons import Icon, get_icon


class QuickAnswerPanel(QWidget):
    forward_signal = Signal(str)
    request_quick_answer_context_signal = Signal()

    def __init__(
        self,
        text_generator: AbstractTextGenerator,
        system_message: Optional[str] = None,
        text: str = "Welcome to ChatGPT cheat tool",
        parent=None,
    ):
        super().__init__(parent)
        self.setup_ui()
        self.update_theme_ui()
        self.set_text(text)

        self.text_generator = text_generator
        self.system_message = system_message
        self.is_generating = False

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setAlignment(Qt.AlignTop)
        self.label.setContentsMargins(10, 10, 10, 10)

        self.scroll_area.setWidget(self.label)
        main_layout.addWidget(self.scroll_area)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.copy_button = QPushButton()
        self.copy_button.setToolTip("Copy")
        self.copy_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.copy_button.clicked.connect(self.copy_text)
        button_layout.addWidget(self.copy_button)

        self.generate_answer_button = QPushButton()
        self.generate_answer_button.setToolTip("Regenerate answer")
        self.generate_answer_button.clicked.connect(self._toggle_generate)
        button_layout.addWidget(self.generate_answer_button)

        self.forward_button = QPushButton()
        self.forward_button.setToolTip("Forward to chat")
        self.forward_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.forward_button.clicked.connect(self.forward_answer)
        button_layout.addWidget(self.forward_button)

        main_layout.addLayout(button_layout)

    def update_label(self):
        html_text = markdown.markdown(self.text)
        self.label.setText(html_text)

    def copy_text(self):
        if self.text:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.text)

    def set_text(self, text: str):
        self.text = text
        self.update_label()

    def clear_text(self):
        self.set_text("")

    def generate_quick_answer(self, messages: List[Tuple[AudioSourceType, str]]):
        if self.is_generating:
            return

        if not len(messages):
            self.text = "No transcribed messages!"
            self.update_label()

            return

        self.clear_text()
        self.generate_answer_button.setDisabled(True)
        self.forward_button.setDisabled(True)
        self.copy_button.setDisabled(True)

        chat_history = []
        if self.system_message:
            chat_history.append(
                {"role": ChatMessageRole.SYSTEM.value, "content": self.system_message}
            )

        messages_formatted = "\n\n".join(
            f"[{source_type.value}]: {text}" for source_type, text in messages
        )

        chat_history.append(
            {
                "role": ChatMessageRole.USER.value,
                "content": messages_formatted,
            }
        )

        skipping_think = False
        write_to_think_buffer = True
        think_buffer = ""

        def callback(text_chunk: str):
            nonlocal skipping_think, think_buffer, write_to_think_buffer

            if write_to_think_buffer:
                think_buffer += text_chunk

                if skipping_think:
                    end_idx = think_buffer.rfind("</think>")
                    if end_idx != -1:
                        skipping_think = False
                        self.text = think_buffer[end_idx + len("</think>") :].lstrip()
                        self.update_label()
                    return

                if think_buffer.strip().startswith("<think>"):
                    skipping_think = True
                    return

            self.text += text_chunk
            think_buffer = ""
            self.update_label()

        def completed_callback(exception: Optional[Exception]):
            self.is_generating = False
            self.generate_answer_button.setDisabled(False)
            self.forward_button.setDisabled(False)
            self.copy_button.setDisabled(False)

            if exception is not None:
                if self.text:
                    self.text += "\n\n"
                self.text += str(exception)
                self.update_label()

            print(self.text)

        threading.Thread(
            target=self.text_generator.generate_text,
            args=(
                chat_history,
                callback,
                completed_callback,
            ),
        ).start()

    def _toggle_generate(self):
        if not self.is_generating:
            self.request_quick_answer_context_signal.emit()

    def forward_answer(self):
        self.forward_signal.emit(self.text)

    def update_theme_ui(self):
        self.copy_button.setIcon(get_icon(Icon.COPY))
        self.generate_answer_button.setIcon(get_icon(Icon.REFRESH))
        self.forward_button.setIcon(get_icon(Icon.SEND))
