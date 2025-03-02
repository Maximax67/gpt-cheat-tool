from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from assets.icons.icon import icon
from utils.app_version import APP_VERSION
from utils.platform import CURRENT_PLATFORM, Platform


def get_icon() -> QIcon:
    pixmap = QPixmap()
    pixmap.loadFromData(icon)

    return QIcon(pixmap)


def set_icon(app: QApplication):
    app.setWindowIcon(get_icon())

    # https://stackoverflow.com/a/1552105
    if CURRENT_PLATFORM == Platform.WINDOWS:
        import ctypes

        myappid = f"gpt-cheat-tool.{APP_VERSION}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
