from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from assets.icons.icon import icon
from utils.app_version import APP_VERSION
from utils.platform import CURRENT_PLATFORM, Platform
from utils.logging import logger


def get_app_icon() -> QIcon:
    pixmap = QPixmap()
    pixmap.loadFromData(icon)

    return QIcon(pixmap)


def set_app_icon(app: QApplication):
    app.setWindowIcon(get_app_icon())

    # https://stackoverflow.com/a/1552105
    if CURRENT_PLATFORM == Platform.WINDOWS:
        from ctypes import windll

        myappid = f"gpt-cheat-tool.{APP_VERSION}"
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    logger.debug("App icon set successfully")
