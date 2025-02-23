from PySide6.QtGui import Qt, QIcon, QColor, QPainter, QImage, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize


COPY_ICON = QIcon("./assets/icons/copy.svg")
MIC_OFF_ICON = QIcon("./assets/icons/mic-off.svg")
MIC_ON_ICON = QIcon("./assets/icons/mic.svg")
REFRESH_ICON = QIcon("./assets/icons/refresh-cw.svg")
SEND_ICON = QIcon("./assets/icons/send.svg")
SETTINGS_ICON = QIcon("./assets/icons/settings.svg")
SELECT_ALL_ICON = QIcon("./assets/icons/check-square.svg")
DELETE_ICON = QIcon("./assets/icons/trash-2.svg")
SPEAKER_ON_ICON = QIcon("./assets/icons/volume-2.svg")
SPEAKER_OFF_ICON = QIcon("./assets/icons/volume-x.svg")


def recolor_svg_icon(icon_path: str, color: QColor) -> QIcon:
    renderer = QSvgRenderer(icon_path)

    size = renderer.defaultSize()
    if not size.isValid() or size.isEmpty():
        size = QSize(256, 256)

    image = QImage(size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    recolored = image.copy()
    painter = QPainter(recolored)

    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(recolored.rect(), color)
    painter.end()

    return QIcon(QPixmap.fromImage(recolored))


def update_icon_colors(theme: str):
    icon_color = QColor(Qt.white) if theme == "dark" else QColor(Qt.black)

    global COPY_ICON, MIC_OFF_ICON, MIC_ON_ICON, REFRESH_ICON, SEND_ICON, SETTINGS_ICON, SELECT_ALL_ICON, DELETE_ICON, SPEAKER_ON_ICON, SPEAKER_OFF_ICON

    COPY_ICON = recolor_svg_icon("./assets/icons/copy.svg", icon_color)
    MIC_OFF_ICON = recolor_svg_icon("./assets/icons/mic-off.svg", icon_color)
    MIC_ON_ICON = recolor_svg_icon("./assets/icons/mic.svg", icon_color)
    REFRESH_ICON = recolor_svg_icon("./assets/icons/refresh-cw.svg", icon_color)
    SEND_ICON = recolor_svg_icon("./assets/icons/send.svg", icon_color)
    SETTINGS_ICON = recolor_svg_icon("./assets/icons/settings.svg", icon_color)
    SELECT_ALL_ICON = recolor_svg_icon("./assets/icons/check-square.svg", icon_color)
    DELETE_ICON = recolor_svg_icon("./assets/icons/trash-2.svg", icon_color)
    SPEAKER_ON_ICON = recolor_svg_icon("./assets/icons/volume-2.svg", icon_color)
    SPEAKER_OFF_ICON = recolor_svg_icon("./assets/icons/volume-x.svg", icon_color)
