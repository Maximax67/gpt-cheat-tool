from enum import Enum
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from services.record_audio.AudioSourceTypes import AudioSourceTypes
from widgets.transcription_block import TranscriptionBlockWidget


class SelectionStates(Enum):
    ALL_DESELECTED = 0
    SOME_SELECTED = 1
    ALL_SELECTED = 2


class TranscriptionListWidget(QScrollArea):
    selection_changed = Signal(SelectionStates)

    def __init__(self):
        super().__init__()

        self.setWidgetResizable(True)
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.container.setLayout(self.layout)
        self.setWidget(self.container)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._is_all_selected = False
        self._is_some_selected = False

    def add_transcription_block(self, text: str, source: AudioSourceTypes):
        block = TranscriptionBlockWidget(text, source)
        block.delete_requested.connect(self.remove_block)
        block.selected_changed_by_click.connect(
            self._handle_block_selected_changed_by_click
        )
        self.layout.addWidget(block)

        if self._is_all_selected:
            self._is_all_selected = False
            self.selection_changed.emit(SelectionStates.SOME_SELECTED)

        self.scroll_to_bottom()

    def _handle_block_selected_changed_by_click(self, selected: bool):
        if not selected:
            if self.layout.count() < 2:
                self._is_all_selected = False
                self._is_some_selected = False
                self.selection_changed.emit(SelectionStates.ALL_DESELECTED)
                return

            if self._is_all_selected:
                self._is_all_selected = False
                self.selection_changed.emit(SelectionStates.SOME_SELECTED)
                return

            if self._check_is_any_selected():
                return

            self._is_some_selected = False
            self.selection_changed.emit(SelectionStates.ALL_DESELECTED)

            return

        if self._check_is_all_selected():
            self._is_all_selected = True
            self._is_some_selected = True
            self.selection_changed.emit(SelectionStates.ALL_SELECTED)
        elif not self._is_some_selected:
            self._is_some_selected = True
            self.selection_changed.emit(SelectionStates.SOME_SELECTED)

    def _remove_widget(self, widget: TranscriptionBlockWidget):
        self.layout.removeWidget(widget)
        widget.deleteLater()

    def remove_block(self, widget: TranscriptionBlockWidget):
        self._remove_widget(widget)

        if self._is_all_selected or not self._is_some_selected:
            return

        if not self._check_is_any_selected():
            self._is_some_selected = False
            self.selection_changed.emit(SelectionStates.ALL_DESELECTED)

    def selected_items(self) -> list[TranscriptionBlockWidget]:
        """Return a list of all blocks that are currently selected."""
        items = []
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget and getattr(widget, "selected", False):
                items.append(widget)

        return items

    def remove_selected(self):
        selected_items = self.selected_items()
        for item in selected_items:
            self._remove_widget(item)

        self._is_all_selected = False
        self._is_some_selected = False
        self.selection_changed.emit(SelectionStates.ALL_DESELECTED)

    def _check_is_all_selected(self) -> bool:
        count = self.layout.count()
        if not count:
            return False

        for i in range(count):
            widget = self.layout.itemAt(i).widget()
            if widget and not getattr(widget, "selected", True):
                return False

        return True

    def _check_is_any_selected(self) -> bool:
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget and getattr(widget, "selected", False):
                return True

        return False

    def deselect_all(self):
        if not self._is_some_selected:
            return

        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget and getattr(widget, "selected", False):
                widget.deselect()

        if self._is_all_selected or self._is_some_selected:
            self._is_all_selected = False
            self._is_some_selected = False
            self.selection_changed.emit(SelectionStates.ALL_DESELECTED)

    def select_all(self):
        if self._is_all_selected:
            return

        count = self.layout.count()
        if not count:
            return

        for i in range(count):
            widget = self.layout.itemAt(i).widget()
            if widget and not getattr(widget, "selected", True):
                widget.select()

        self._is_all_selected = True
        self._is_some_selected = True
        self.selection_changed.emit(SelectionStates.ALL_SELECTED)

    def get_is_all_selected(self) -> bool:
        return self._is_all_selected

    def scroll_to_bottom(self):
        """Ensure the latest message is visible."""
        QTimer.singleShot(
            50,
            lambda: self.verticalScrollBar().setValue(
                self.verticalScrollBar().maximum()
            ),
        )
