from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, Signal
from ui.icons import COPY_ICON, DELETE_ICON


class TranscriptionBlockWidget(QWidget):
    # Signal emitted when the delete button is pressed.
    delete_requested = Signal(QWidget)
    selected_changed_by_click = Signal(bool)

    def __init__(self, text: str, source="mic"):
        super().__init__()
        self.text = text
        self.source = source
        self.selected = False
        self.base_style = "margin: 3px; background: " + (
            "#0d0;" if source == "mic" else "#d00;"
        )
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 0, 0, 0)
        self.main_layout.setSpacing(10)

        # Label: takes as much width as possible; selectable text.
        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setContentsMargins(0, 0, 0, 0)
        self.label.setStyleSheet(self.base_style)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.label)

        # Button layout container
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(5)
        self.button_layout.setAlignment(Qt.AlignTop)
        self.button_layout.setContentsMargins(0, 0, 5, 0)

        self.copy_button = QPushButton()
        self.copy_button.setIcon(COPY_ICON)
        self.copy_button.setToolTip("Copy")
        self.copy_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.copy_button.clicked.connect(self.copy_text)
        self.button_layout.addWidget(self.copy_button)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(DELETE_ICON)
        self.delete_button.setToolTip("Delete")
        self.delete_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.delete_button.clicked.connect(self.delete_self)
        self.button_layout.addWidget(self.delete_button)

        self.main_layout.addLayout(self.button_layout)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text)

    def delete_self(self):
        # Emit a signal so that the parent can remove this widget safely.
        self.delete_requested.emit(self)

    def get_text(self) -> str:
        return self.text

    def _update_selection_style(self):
        """Update the style to indicate selection."""
        if self.selected:
            self.label.setStyleSheet(
                self.base_style
                + " margin: 0; border: 3px solid blue; border-radius: 5px;"
            )
        else:
            self.label.setStyleSheet(self.base_style)

    def mousePressEvent(self, event):
        """Toggle selection when the widget is clicked."""
        self.selected = not self.selected
        self._update_selection_style()
        self.selected_changed_by_click.emit(self.selected)
        event.accept()

    def deselect(self):
        self.selected = False
        self._update_selection_style()

    def select(self):
        self.selected = True
        self._update_selection_style()

    def resizeEvent(self, event):
        """Dynamically adjust button layout based on available width."""
        width = self.width()
        if width < 200:
            self.copy_button.setVisible(False)
            self.delete_button.setVisible(False)
            self.main_layout.setContentsMargins(10, 0, 0, 0)

            return

        self.copy_button.setVisible(True)
        self.delete_button.setVisible(True)
        self.main_layout.setContentsMargins(20, 0, 0, 0)

        if width < 300:
            if not isinstance(self.button_layout, QVBoxLayout):
                self.main_layout.removeItem(self.button_layout)
                self.button_layout = QVBoxLayout()
                self.button_layout.setSpacing(5)
                self.button_layout.setAlignment(Qt.AlignTop)
                self.button_layout.setContentsMargins(0, 0, 0, 0)
                self.button_layout.addWidget(self.copy_button)
                self.button_layout.addWidget(self.delete_button)
                self.main_layout.addLayout(self.button_layout)

            return

        if not isinstance(self.button_layout, QHBoxLayout):
            self.main_layout.removeItem(self.button_layout)
            self.button_layout = QHBoxLayout()
            self.button_layout.setSpacing(5)
            self.button_layout.setAlignment(Qt.AlignTop)
            self.button_layout.setContentsMargins(0, 0, 0, 0)
            self.button_layout.addWidget(self.copy_button)
            self.button_layout.addWidget(self.delete_button)
            self.main_layout.addLayout(self.button_layout)

        super().resizeEvent(event)
