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
    QPlainTextEdit,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPalette, QColor

from services.generate_text.Message import ChatMessage, ChatMessageRole
from ui.icons import Icon, get_icon


class ChatMessageWidget(QWidget):
    message_switch_signal = Signal(ChatMessage)
    regenerate_requested = Signal(ChatMessage)
    edit_message_signal = Signal(ChatMessage, str)

    def __init__(self, message: ChatMessage):
        if message.role == ChatMessageRole.SYSTEM:
            raise ValueError("System message is not for rendering")

        super().__init__()
        self.message = message
        self.error_label_color_applied = False
        self._setup_ui()
        self.update_theme_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 0, 10, 0)
        self.main_layout.setSpacing(5)

        # Display the message content
        error = str(self.message.error) if self.message.error else None
        if self.message.role == ChatMessageRole.USER:
            text = self.message.text
            if error:
                self.error_label_color_applied = True
                text += "\n\n" + error

            self.label = QLabel(text)
        else:
            html_text = markdown.markdown(self.message.text)
            if error:
                self.error_label_color_applied = True
                html_text += "\n\n" + error

            self.label = QLabel(html_text)
            self.label.setTextFormat(Qt.RichText)

        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(self.label)

        # Control box layout
        self.control_layout = QHBoxLayout()
        self.control_layout.setContentsMargins(5, 0, 0, 5)
        self.control_layout.setAlignment(Qt.AlignLeft)
        self.control_layout.setSpacing(5)

        # Switch Message UI (back and next buttons)
        parent = self.message.parent
        total_siblings_count = len(parent.childs) if parent else 0
        if total_siblings_count > 1:
            current_pos = parent.childs.index(self.message) + 1

            # Back Button (only enabled if it's not the first message)
            self.back_button = QPushButton()
            self.back_button.setFixedWidth(20)
            self.back_button.setFixedHeight(20)
            self.back_button.setIconSize(QSize(12, 12))
            self.back_button.setEnabled(current_pos > 1)
            self.back_button.clicked.connect(self._on_previous_message)
            self.control_layout.addWidget(self.back_button)

            # Current position / Total messages (e.g., 2/4)
            self.position_label = QLabel(f"{current_pos} / {total_siblings_count}")
            self.position_label.setFixedWidth(35)
            self.position_label.setFixedHeight(20)
            self.position_label.setAlignment(Qt.AlignCenter)
            self.control_layout.addWidget(self.position_label)

            # Next Button (only enabled if it's not the last message)
            self.next_button = QPushButton()
            self.next_button.setFixedWidth(20)
            self.next_button.setFixedHeight(20)
            self.next_button.setIconSize(QSize(12, 12))
            self.next_button.setEnabled(current_pos < total_siblings_count)
            self.next_button.clicked.connect(self._on_next_message)
            self.control_layout.addWidget(self.next_button)
        else:
            self.back_button = None
            self.next_button = None

        # Copy button
        self.copy_button = QPushButton()
        self.copy_button.setFixedWidth(20)
        self.copy_button.setFixedHeight(20)
        self.copy_button.setIconSize(QSize(12, 12))
        self.copy_button.clicked.connect(self.copy_text)
        self.control_layout.addWidget(self.copy_button)

        # Edit or Regenerate Button
        if self.message.role == ChatMessageRole.USER:
            self.edit_button = QPushButton()
            self.edit_button.setFixedWidth(20)
            self.edit_button.setFixedHeight(20)
            self.edit_button.setIconSize(QSize(12, 12))
            self.edit_button.clicked.connect(self._on_edit_message)
            self.control_layout.addWidget(self.edit_button)
            self.regenerate_button = None
        else:
            self.regenerate_button = QPushButton()
            self.regenerate_button.setFixedWidth(20)
            self.regenerate_button.setFixedHeight(20)
            self.regenerate_button.setIconSize(QSize(12, 12))
            self.regenerate_button.clicked.connect(self._handle_regenerate)
            self.control_layout.addWidget(self.regenerate_button)
            self.edit_button = None

        self.main_layout.addLayout(self.control_layout)
        self.setLayout(self.main_layout)

    def _on_edit_message(self):
        self._original_text = self.message.text

        self.label.hide()

        for i in range(self.control_layout.count()):
            widget: QWidget = self.control_layout.itemAt(i).widget()
            if widget:
                widget.hide()

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(self._original_text)
        self.main_layout.insertWidget(0, self.text_edit)

        self.edit_buttons_layout = QHBoxLayout()
        self.edit_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.edit_buttons_layout.setAlignment(Qt.AlignRight)

        self.cancel_button = QPushButton("Cancel")
        self.apply_button = QPushButton("Apply")
        self.apply_button.setEnabled(False)

        self.edit_buttons_layout.addWidget(self.cancel_button)
        self.edit_buttons_layout.addWidget(self.apply_button)

        self.main_layout.insertLayout(1, self.edit_buttons_layout)

        self.cancel_button.clicked.connect(self._cancel_edit)
        self.apply_button.clicked.connect(self._apply_edit)
        self.text_edit.textChanged.connect(self._on_text_edit_changed)

    def _on_text_edit_changed(self):
        current_text = self.text_edit.toPlainText().strip()
        enable_apply = bool(current_text and current_text != self._original_text)
        self.apply_button.setEnabled(enable_apply)

    def _cancel_edit(self):
        self.main_layout.removeWidget(self.text_edit)
        self.text_edit.deleteLater()
        self.text_edit = None

        while self.edit_buttons_layout.count():
            item = self.edit_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.edit_buttons_layout = None
        self.label.show()

        for i in range(self.control_layout.count()):
            widget: QWidget = self.control_layout.itemAt(i).widget()
            if widget:
                widget.show()

    def _apply_edit(self):
        new_text = self.text_edit.toPlainText().strip()
        if new_text and new_text != self._original_text:
            self._cancel_edit()
            self.edit_message_signal.emit(self.message, new_text)

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
            if not self.error_label_color_applied:
                self.error_label_color_applied = True
                self._update_label_background()

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

    def _update_label_background(self):
        app = QApplication.instance()
        palette: QPalette = app.palette()
        color: QColor = palette.color(QPalette.ColorRole.Text)

        # Converting the RGB color values to compute luminance by the following formula:
        # Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
        y = 0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue()

        if self.message.error:
            self.label.setStyleSheet(
                f"background: {'#FEC9C8' if y < 128 else '#8B0000'};"
            )
        elif self.message.role == ChatMessageRole.USER:
            self.label.setStyleSheet(
                f"background: {'#E8E8E8' if y < 128 else '#2E2E2E'};"
            )

    def update_theme_ui(self):
        self._update_label_background()
        self.copy_button.setIcon(get_icon(Icon.COPY))

        if self.back_button:
            self.back_button.setIcon(get_icon(Icon.ARROW_LEFT))

        if self.next_button:
            self.next_button.setIcon(get_icon(Icon.ARROW_RIGHT))

        if self.edit_button:
            self.edit_button.setIcon(get_icon(Icon.EDIT))

        if self.regenerate_button:
            self.regenerate_button.setIcon(get_icon(Icon.REFRESH))
