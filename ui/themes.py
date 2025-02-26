import qdarktheme
from enum import Enum


class Theme(Enum):
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"


class ThemeManager:
    def __init__(self, theme: Theme):
        self._theme = theme
        self.set_theme(theme)

    def set_theme(self, theme: Theme) -> bool:
        if self._theme != theme:
            self._theme = theme
            qdarktheme.setup_theme(theme.value)

            return True

        return False

    def get_theme(self) -> Theme:
        return self._theme
