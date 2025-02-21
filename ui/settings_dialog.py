from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QApplication,
)

from ui.icons import update_icon_colors
from ui.switch_theme import switch_theme


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        # Layout for the dialog
        layout = QVBoxLayout(self)

        # Theme selection dropdown
        self.theme_selector = QComboBox(self)
        self.theme_selector.addItem("Light")
        self.theme_selector.addItem("Dark")
        self.theme_selector.addItem("System")
        self.theme_selector.currentTextChanged.connect(self.on_theme_changed)
        layout.addWidget(self.theme_selector)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def on_theme_changed(self, theme: str):
        app = QApplication.instance()
        switch_theme(app, theme.lower())
        update_icon_colors(theme.lower())

