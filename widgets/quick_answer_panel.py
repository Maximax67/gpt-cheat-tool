import lorem
import markdown
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
from ui.icons import COPY_ICON, REFRESH_ICON, SEND_ICON


class QuickAnswerPanel(QWidget):
    forward_signal = Signal(str)

    def __init__(self, text: str = "Welcome to chatGPT cheat tool", parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.set_text(text)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Scrollable label container
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
        self.copy_button.setIcon(COPY_ICON)
        self.copy_button.setToolTip("Copy")
        self.copy_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.copy_button.clicked.connect(self.copy_text)
        button_layout.addWidget(self.copy_button)

        self.generate_answer_button = QPushButton()
        self.generate_answer_button.setIcon(REFRESH_ICON)
        self.generate_answer_button.setToolTip("Pause Transcription")
        self.generate_answer_button.clicked.connect(self._toggle_generate)
        button_layout.addWidget(self.generate_answer_button)

        self.forward_button = QPushButton()
        self.forward_button.setIcon(SEND_ICON)
        self.forward_button.setToolTip("Forward to chat")
        self.forward_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.forward_button.clicked.connect(self.forward_answer)
        button_layout.addWidget(self.forward_button)

        main_layout.addLayout(button_layout)

    def copy_text(self):
        if self.text:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.text)

    def set_text(self, text: str):
        self.text = text
        html_text = markdown.markdown(text)
        self.label.setText(html_text)

    def clear_text(self):
        self.set_text("")

    def get_text(self) -> str:
        return self.text

    def _toggle_generate(self):
        self.set_text(lorem.text())
        self.scroll_area.verticalScrollBar().setValue(0)

    def forward_answer(self):
        self.forward_signal.emit(self.text)
