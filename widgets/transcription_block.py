from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QMenu,
    QApplication,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from services.record_audio.AudioSourceTypes import AudioSourceTypes
from ui.icons import COPY_ICON, DELETE_ICON, SEND_ICON


class TranscriptionBlockWidget(QWidget):
    delete_requested = Signal(QWidget)
    selected_changed_by_click = Signal(bool)
    forward_signal = Signal(str)

    def __init__(self, text: str, source: AudioSourceTypes):
        super().__init__()
        self.text = text
        self.source = source
        self.selected = False
        self.base_style = "padding: 3 px; background: " + (
            "#0d0;" if source == AudioSourceTypes.MIC else "#d00;"
        )
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 0, 5, 0)
        self.main_layout.setSpacing(10)

        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setStyleSheet(self.base_style)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.label)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text)

    def delete_self(self):
        self.delete_requested.emit(self)

    def set_text(self, text):
        self.text = text
        self.label.setText(text)

    def _update_selection_style(self):
        """Update the style to indicate selection."""
        if self.selected:
            self.label.setStyleSheet(
                self.base_style
                + " padding: 0; border: 3px solid blue; border-radius: 5px;"
            )
        else:
            self.label.setStyleSheet(self.base_style)

    def mousePressEvent(self, event):
        """Toggle selection when the widget is clicked."""
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

    def show_context_menu(self, position):
        """Create and display the right-click context menu."""
        menu = QMenu(self)
        copy_action = menu.addAction(COPY_ICON, "Copy")
        delete_action = menu.addAction(DELETE_ICON, "Delete")
        forward_action = menu.addAction(SEND_ICON, "Forward to chat")

        action = menu.exec(position)
        if action == copy_action:
            self.copy_text()
        elif action == delete_action:
            self.delete_self()
        elif action == forward_action:
            self.forward_signal.emit(self.text)
