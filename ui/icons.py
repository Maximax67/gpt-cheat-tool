import os
from enum import Enum
from typing import Dict, Tuple
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPalette, QColor
from PySide6.QtWidgets import QApplication


basedir = os.path.dirname(__file__)


class Icon(Enum):
    COPY = os.path.join(basedir, "../assets/icons/copy.svg")
    MIC_OFF = os.path.join(basedir, "../assets/icons/mic-off.svg")
    MIC_ON = os.path.join(basedir, "../assets/icons/mic.svg")
    REFRESH = os.path.join(basedir, "../assets/icons/refresh-cw.svg")
    SEND = os.path.join(basedir, "../assets/icons/send.svg")
    SETTINGS = os.path.join(basedir, "../assets/icons/settings.svg")
    SELECT_ALL = os.path.join(basedir, "../assets/icons/check-square.svg")
    DELETE = os.path.join(basedir, "../assets/icons/trash-2.svg")
    SPEAKER_ON = os.path.join(basedir, "../assets/icons/volume-2.svg")
    SPEAKER_OFF = os.path.join(basedir, "../assets/icons/volume-x.svg")
    ARROW_LEFT = os.path.join(basedir, "../assets/icons/arrow-left.svg")
    ARROW_RIGHT = os.path.join(basedir, "../assets/icons/arrow-right.svg")
    SHEVRONS_RIGHT = os.path.join(basedir, "../assets/icons/chevrons-right.svg")
    EDIT = os.path.join(basedir, "../assets/icons/edit-2.svg")


_cached_icons: Dict[Icon, Tuple[QColor, QIcon]] = {}


def get_icon(icon: Icon) -> QIcon:
    app = QApplication.instance()
    if app is None:
        raise Exception("QApplication not started")

    palette: QPalette = app.palette()
    color: QColor = palette.color(QPalette.ColorRole.Text)

    cached_result = _cached_icons.get(icon)
    if cached_result and cached_result[0] == color:
        return cached_result[1]

    pixmap = QPixmap(icon.value)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()

    painted_icon = QIcon(pixmap)
    _cached_icons[icon] = (color, painted_icon)

    return painted_icon
