import lorem
import markdown

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, QTimer

from ui.icons import SEND_ICON


class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Main vertical layout for the widget
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # Scroll area to hold messages
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.messages_widget)
        self.layout.addWidget(self.scroll_area)

        # Input area with dynamically resizing text edit and send button
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)

        self.input_text = QTextEdit(self)
        self.input_text.setPlaceholderText("Type your message...")
        self.input_text.setFixedHeight(32)
        self.input_text.textChanged.connect(self._adjust_input_height)

        self.send_button = QPushButton()
        self.send_button.setFixedHeight(32)
        self.send_button.setIcon(SEND_ICON)
        self.send_button.setToolTip("Send text")
        self.send_button.clicked.connect(self._handle_send)

        input_layout.addWidget(self.input_text)
        input_layout.addWidget(self.send_button)
        self.layout.addLayout(input_layout)

    def _adjust_input_height(self):
        """Adjust the height of the input box based on its content."""
        doc_height = self.input_text.document().size().height()
        new_height = max(35, min(150, doc_height + 10))
        self.input_text.setFixedHeight(new_height)

    def _handle_send(self):
        """Handle sending a message: add user message and simulate bot response."""
        text = self.input_text.toPlainText().strip()
        if text:
            self.add_user_message(text)
            self.clear_prompt()
            # Simulate an API response after a short delay
            QTimer.singleShot(500, self.simulate_response)

    def send_message(self, text):
        """Handle sending a message: add user message and simulate bot response."""
        text = text.strip()
        if text:
            self.add_user_message(text)
            self.clear_prompt()
            # Simulate an API response after a short delay
            QTimer.singleShot(500, self.simulate_response)

    def add_user_message(self, text):
        """Display a user message aligned to the right."""
        msg_widget = QLabel(text, self)
        msg_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg_widget.setWordWrap(True)
        container = QFrame(self)
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(msg_widget)
        container_layout.setAlignment(Qt.AlignRight)
        self.messages_layout.addWidget(container)
        self.scroll_to_bottom()

    def add_bot_message(self, text):
        """Display a bot message with markdown support and action buttons."""
        # Convert markdown text to HTML for rich text display
        html_text = markdown.markdown(text)
        msg_widget = QLabel(html_text, self)
        msg_widget.setWordWrap(True)
        msg_widget.setTextFormat(Qt.RichText)
        msg_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Create buttons for regenerating and copying the message
        regenerate_btn = QPushButton("Regenerate", self)
        copy_btn = QPushButton("Copy", self)
        regenerate_btn.setFixedWidth(80)
        copy_btn.setFixedWidth(80)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(regenerate_btn)
        btn_layout.addWidget(copy_btn)
        btn_layout.addStretch()

        # Container for the bot message and its buttons
        container = QFrame(self)
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(msg_widget)
        container_layout.addLayout(btn_layout)
        container_layout.setAlignment(Qt.AlignLeft)

        # Connect button actions; regenerate updates the message, copy sends text to clipboard
        regenerate_btn.clicked.connect(lambda: self.handle_regenerate(msg_widget))
        copy_btn.clicked.connect(lambda: self.handle_copy(text))

        self.messages_layout.addWidget(container)
        self.scroll_to_bottom()

    def handle_regenerate(self, msg_widget):
        """Simulate regenerating the bot response with new dummy text."""
        new_text = lorem.paragraph()
        new_text += " \n\n**bold**\n\n1. Something\n\n2. Another\n\n3. FDFDF\n\n[asdf](https://google.com)"
        html_text = markdown.markdown(new_text)
        msg_widget.setText(html_text)

    def handle_copy(self, text):
        """Copy the message text to the system clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def simulate_response(self):
        """Simulate an API response using the lorem library."""
        dummy_text = lorem.paragraph()
        self.add_bot_message(dummy_text)

    def scroll_to_bottom(self):
        """Ensure the latest message is visible."""
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def get_prompt_text(self):
        return self.input_text.toPlainText().strip()

    def clear_prompt(self):
        self.input_text.clear()
