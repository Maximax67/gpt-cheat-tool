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
    deleteRequested = Signal(QWidget)

    def __init__(self, text, source="mic"):
        super().__init__()
        self.text = text
        self.source = source  # Either "mic" or "speaker"
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 0, 5, 0)
        main_layout.setSpacing(10)

        # Label: takes as much width as possible; selectable text.
        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.label)

        # Vertical layout for buttons.
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.copy_button = QPushButton()
        self.copy_button.setIcon(COPY_ICON)
        self.copy_button.setToolTip("Copy")
        self.copy_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.copy_button.clicked.connect(self.copy_text)
        button_layout.addWidget(self.copy_button)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(DELETE_ICON)
        self.delete_button.setToolTip("Delete")
        self.delete_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.delete_button.clicked.connect(self.delete_self)
        button_layout.addWidget(self.delete_button)

        main_layout.addLayout(button_layout)

        # Allow the widget to size itself based on content.
        self.setMinimumHeight(40)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text)

    def delete_self(self):
        # Emit a signal so that the parent can remove this widget safely.
        self.deleteRequested.emit(self)

    def get_text(self):
        return self.text
