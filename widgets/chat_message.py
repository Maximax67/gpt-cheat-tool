import markdown

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QMenu,
    QApplication,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

from services.generate_text.Message import ChatMessage, ChatMessageRole
from ui.icons import Icon, get_icon


class ChatMessageWidget(QWidget):
    message_switch_signal = Signal(ChatMessage)
    regenerate_requested = Signal(ChatMessage)

    def __init__(self, message: ChatMessage):
        if message.role == ChatMessageRole.SYSTEM:
            raise ValueError("System message is not for rendering")

        super().__init__()
        self.message = message
        self._setup_ui()
        self.update_theme_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 0, 10, 0)
        self.main_layout.setSpacing(5)

        # Display the message content
        if self.message.role == ChatMessageRole.USER:
            self.label = QLabel(self.message.text)
        else:
            html_text = markdown.markdown(self.message.text)
            self.label = QLabel(html_text)
            self.label.setTextFormat(Qt.RichText)

        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(self.label)

        # Control box layout
        self.control_layout = QHBoxLayout()

        # Switch Message UI (back and next buttons)
        parent = self.message.parent
        total_siblings_count = len(parent.childs) if parent else 0
        if total_siblings_count > 1:
            current_pos = parent.childs.index(self.message) + 1

            # Back Button (only enabled if it's not the first message)
            self.back_button = QPushButton("<")
            self.back_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.back_button.setEnabled(current_pos > 1)
            self.back_button.clicked.connect(self._on_previous_message)
            self.control_layout.addWidget(self.back_button)

            # Current position / Total messages (e.g., 2/4)
            self.position_label = QLabel(f"{current_pos} / {total_siblings_count}")
            self.position_label.setAlignment(Qt.AlignCenter)
            self.position_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.control_layout.addWidget(self.position_label)

            # Next Button (only enabled if it's not the last message)
            self.next_button = QPushButton(">")
            self.next_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.next_button.setEnabled(current_pos < total_siblings_count)
            self.next_button.clicked.connect(self._on_next_message)
            self.control_layout.addWidget(self.next_button)
        else:
            self.back_button = None
            self.next_button = None

        # Copy button
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_text)
        self.copy_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.control_layout.addWidget(self.copy_button)

        # Add control layout to the main layout
        self.main_layout.addLayout(self.control_layout)

        # Edit or Regenerate Button
        if self.message.role == ChatMessageRole.USER:
            self.edit_button = QPushButton("Edit")
            self.edit_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            # self.edit_button.clicked.connect(self.on_edit_message)
            self.control_layout.addWidget(self.edit_button)
        else:
            self.regenerate_button = QPushButton("Regenerate")
            self.regenerate_button.setSizePolicy(
                QSizePolicy.Minimum, QSizePolicy.Minimum
            )
            self.regenerate_button.clicked.connect(self._handle_regenerate)
            self.control_layout.addWidget(self.regenerate_button)

        # Update the widget layout
        self.setLayout(self.main_layout)

    def _handle_regenerate(self):
        self.regenerate_requested.emit(self.message)

    def _on_previous_message(self):
        current_pos = self.message.parent.childs.index(self.message)
        if current_pos > 0:
            previous_message = self.message.parent.childs[current_pos - 1]
            self.message_switch_signal.emit(previous_message)

    def _on_next_message(self):
        current_pos = self.message.parent.childs.index(self.message)
        if current_pos < len(self.message.parent.childs) - 1:
            next_message = self.message.parent.childs[current_pos + 1]
            self.message_switch_signal.emit(next_message)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.message.text)

    def delete_self(self):
        self.delete_requested.emit(self)

    def update_text(self):
        message_error = self.message.error
        message_text = self.message.text

        text_to_set = (
            markdown.markdown(message_text)
            if ChatMessageRole.ASSISTANT
            else message_text
        )

        if message_error:
            text_to_set += "\n\n" + str(message_error)

        self.label.setText(text_to_set)

    def show_context_menu(self, position):
        menu = QMenu(self)
        copy_action = menu.addAction(get_icon(Icon.COPY), "Copy")
        delete_action = menu.addAction(get_icon(Icon.DELETE), "Delete")

        action = menu.exec(position)
        if action == copy_action:
            self.copy_text()
        elif action == delete_action:
            self.delete_self()

    def update_theme_ui(self):
        app = QApplication.instance()
        palette: QPalette = app.palette()
        color: QColor = palette.color(QPalette.ColorRole.Text)

        # Converting the RGB color values to compute luminance by the following formula:
        # Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
        y = 0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue()

        # Check if the value is nearer to 0 (black) or to 255 (white)
        if y < 128:  # White theme as text color is black
            assistant_message_color = "#BBFFC1"  # Light Green
            user_message_color = "#FEC9C8"  # Light Red
        else:  # Dark theme as text color is white
            assistant_message_color = "#006400"  # Dark Green
            user_message_color = "#8B0000"  # Dark Red

        self.label.setStyleSheet(
            f"background: {assistant_message_color if self.message.role == ChatMessageRole.ASSISTANT else user_message_color};"
        )
