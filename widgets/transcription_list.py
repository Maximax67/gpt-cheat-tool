from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from widgets.transcription_block import TranscriptionBlockWidget


class TranscriptionListWidget(QScrollArea):
    select_all_changed = Signal(bool)

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

    def add_transcription_block(self, text: str, source="mic"):
        block = TranscriptionBlockWidget(text, source)
        block.delete_requested.connect(self.remove_block)
        block.selected_changed_by_click.connect(
            self._handle_block_selected_changed_by_click
        )
        self.layout.addWidget(block)

        if self._is_all_selected:
            self._is_all_selected = False
            self.select_all_changed.emit(False)

        self.scroll_to_bottom()

    def _handle_block_selected_changed_by_click(self, selected: bool):
        if self._is_all_selected:
            if not selected:
                self._is_all_selected = False
                self.select_all_changed.emit(False)

            return

        if selected and self._check_is_all_selected():
            self._is_all_selected = True
            self.select_all_changed.emit(True)

    def remove_block(self, widget: TranscriptionBlockWidget):
        self.layout.removeWidget(widget)
        widget.deleteLater()

        check_result = self._check_is_all_selected()
        if self._is_all_selected != check_result:
            self._is_all_selected = check_result
            self.select_all_changed.emit(check_result)

    def selected_items(self) -> list[TranscriptionBlockWidget]:
        """Return a list of all blocks that are currently selected."""
        items = []
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget and getattr(widget, "selected", False):
                items.append(widget)

        return items

    def _check_is_all_selected(self) -> bool:
        count = self.layout.count()
        if not count:
            return False

        for i in range(count):
            widget = self.layout.itemAt(i).widget()
            if widget and not getattr(widget, "selected", True):
                return False

        return True

    def deselect_all(self):
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget and getattr(widget, "selected", False):
                widget.deselect()

        if self._is_all_selected:
            self._is_all_selected = False
            self.select_all_changed.emit(False)

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
        self.select_all_changed.emit(True)

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
