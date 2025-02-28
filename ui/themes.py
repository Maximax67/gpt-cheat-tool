import qdarktheme
from enum import Enum

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class Theme(Enum):
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"


class ThemeManager:
    def __init__(self, theme: Theme):
        self._theme = theme
        qdarktheme.setup_theme(theme.value)

    def set_theme(self, theme: Theme) -> bool:
        if self._theme != theme:
            self._theme = theme
            qdarktheme.setup_theme(theme.value)

            return True

        return False

    def get_theme(self) -> Theme:
        return self._theme

    @staticmethod
    def is_white_theme() -> bool:
        app = QApplication.instance()
        palette: QPalette = app.palette()
        color: QColor = palette.color(QPalette.ColorRole.Text)

        # Converting the RGB color values to compute luminance by the following formula:
        # Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
        y = 0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue()

        # If y < 128, white theme as text color is dark
        return y < 128
