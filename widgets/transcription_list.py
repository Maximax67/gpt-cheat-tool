from enum import Enum
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from services.record_audio.audio_source_type import AudioSourceType
from widgets.transcription_block import TranscriptionBlockWidget


class SelectionStates(Enum):
    ALL_DESELECTED = 0
    SOME_SELECTED = 1
    ALL_SELECTED = 2


class TranscriptionListWidget(QScrollArea):
    selection_changed = Signal(SelectionStates)
    forward_message_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.update_theme_ui()

        self._is_all_selected = False
        self._is_some_selected = False
        self._last_blocks_by_source: Dict[
            AudioSourceType, Optional[TranscriptionBlockWidget]
        ] = {
            AudioSourceType.MIC: None,
            AudioSourceType.SPEAKER: None,
        }

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

    def add_transcription_block(
        self, source: AudioSourceType, text: str
    ) -> TranscriptionBlockWidget:
        block = TranscriptionBlockWidget(text, source)
        block.delete_requested.connect(self.remove_block)
        block.selected_changed_by_click.connect(
            self._handle_block_selected_changed_by_click
        )
        block.forward_signal.connect(self.forward_message_signal.emit)
        self._last_blocks_by_source[source] = block
        self.layout.addWidget(block)

        if self._is_all_selected:
            self._is_all_selected = False
            self.selection_changed.emit(SelectionStates.SOME_SELECTED)

        self.scroll_to_bottom()

        return block

    def update_last_block_text(
        self, source: AudioSourceType, text: str
    ) -> TranscriptionBlockWidget:
        block = self._last_blocks_by_source.get(source)
        if block:
            block.set_text(text)
            return block

        return self.add_transcription_block(source, text)

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
        audio_source = widget.source
        if self._last_blocks_by_source[audio_source] == widget:
            self._last_blocks_by_source[audio_source] = None

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
        items = []
        for i in range(self.layout.count()):
            widget: TranscriptionBlockWidget = self.layout.itemAt(i).widget()
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
            widget: TranscriptionBlockWidget = self.layout.itemAt(i).widget()
            if widget and not getattr(widget, "selected", True):
                return False

        return True

    def _check_is_any_selected(self) -> bool:
        for i in range(self.layout.count()):
            widget: TranscriptionBlockWidget = self.layout.itemAt(i).widget()
            if widget and getattr(widget, "selected", False):
                return True

        return False

    def deselect_all(self):
        if not self._is_some_selected:
            return

        for i in range(self.layout.count()):
            widget: TranscriptionBlockWidget = self.layout.itemAt(i).widget()
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
            widget: TranscriptionBlockWidget = self.layout.itemAt(i).widget()
            if widget and not getattr(widget, "selected", True):
                widget.select()

        self._is_all_selected = True
        self._is_some_selected = True
        self.selection_changed.emit(SelectionStates.ALL_SELECTED)

    def get_is_all_selected(self) -> bool:
        return self._is_all_selected

    def scroll_to_bottom(self):
        QTimer.singleShot(
            50,
            lambda: self.verticalScrollBar().setValue(
                self.verticalScrollBar().maximum()
            ),
        )

    def get_messages(
        self, limit: Optional[int] = None
    ) -> List[Tuple[AudioSourceType, str]]:
        if limit and limit < 1:
            raise ValueError("limit < 1")

        context = []
        count = self.layout.count()
        loop_range = (
            range(count - 1, max(count - limit - 1, -1), -1)
            if limit
            else range(count - 1, -1, -1)
        )
        for i in loop_range:
            widget: TranscriptionBlockWidget = self.layout.itemAt(i).widget()
            context.append((widget.source, widget.text))

        return context

    def update_theme_ui(self):
        for i in range(self.layout.count()):
            widget: TranscriptionBlockWidget = self.layout.itemAt(i).widget()
            if widget:
                widget.update_theme_ui()
