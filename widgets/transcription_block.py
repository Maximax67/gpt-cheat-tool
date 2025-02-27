from typing import List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QMenu,
    QApplication,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor

from services.record_audio.AudioSourceType import AudioSourceType
from ui.icons import Icon, get_icon


class TranscriptionBlockWidget(QWidget):
    delete_requested = Signal(QWidget)
    selected_changed_by_click = Signal(bool)
    forward_signal = Signal(str)

    def __init__(self, text: str, source: AudioSourceType):
        super().__init__()
        self.text = text
        self.text_history: List[str] = [text]
        self.text_history_index = 0
        self.source = source
        self.selected = False
        self._setup_ui()
        self.update_theme_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 0, 10, 0)

        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(self.label)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text)

    def delete_self(self):
        self.delete_requested.emit(self)

    def set_text(self, text):
        if text != self.text_history[-1]:
            self.text = text
            self.label.setText(text)
            self.text_history_index = len(self.text_history)
            self.text_history.append(text)

    def _update_selection_style(self):
        if self.selected:
            self.label.setStyleSheet(
                self.label_style
                + " margin: 0; border: 3px solid blue; border-radius: 5px;"
            )
        else:
            self.label.setStyleSheet(self.label_style)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected = not self.selected
            self._update_selection_style()
            self.selected_changed_by_click.emit(self.selected)
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
            event.accept()
        else:
            super().mousePressEvent(event)

    def deselect(self):
        self.selected = False
        self._update_selection_style()

    def select(self):
        self.selected = True
        self._update_selection_style()

    def _set_text_from_history(self):
        self.text = self.text_history[self.text_history_index]
        self.label.setText(self.text)

    def show_context_menu(self, position):
        menu = QMenu(self)
        copy_action = menu.addAction(get_icon(Icon.COPY), "Copy")
        delete_action = menu.addAction(get_icon(Icon.DELETE), "Delete")
        forward_action = menu.addAction(get_icon(Icon.SEND), "Forward to chat")

        if len(self.text_history) > 1:
            menu.addSeparator()

        back_action = None
        next_action = None
        to_last_action = None

        if self.text_history_index:
            back_action = menu.addAction(get_icon(Icon.ARROW_LEFT), "Back")

        if self.text_history_index < len(self.text_history) - 1:
            next_action = menu.addAction(get_icon(Icon.ARROW_RIGHT), "Forward")

            if self.text_history_index < len(self.text_history) - 2:
                to_last_action = menu.addAction(
                    get_icon(Icon.SHEVRONS_RIGHT), "To last message"
                )

        action = menu.exec(position)
        if action == copy_action:
            self.copy_text()
        elif action == delete_action:
            self.delete_self()
        elif action == forward_action:
            self.forward_signal.emit(self.text)
        elif back_action and action == back_action:
            self.text_history_index -= 1
            self._set_text_from_history()
        elif next_action and action == next_action:
            self.text_history_index += 1
            self._set_text_from_history()
        elif to_last_action and action == to_last_action:
            self.text_history_index = len(self.text_history) - 1
            self._set_text_from_history()

    def update_theme_ui(self):
        app = QApplication.instance()
        palette: QPalette = app.palette()
        color: QColor = palette.color(QPalette.ColorRole.Text)

        # Converting the RGB color values to compute luminance by the following formula:
        # Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
        y = 0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue()

        # Check if the value is nearer to 0 (black) or to 255 (white)
        if y < 128:  # White theme as text color is black
            mic_color = "#BBFFC1"  # Light Green
            file_color = "#FEC9C8"  # Light Red
        else:  # Dark theme as text color is white
            mic_color = "#006400"  # Dark Green
            file_color = "#8B0000"  # Dark Red

        self.label_style = f"margin: 3px; border: 0; background: {mic_color if self.source == AudioSourceType.MIC else file_color};"
        self.label.setStyleSheet(self.label_style)
