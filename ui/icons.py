from PySide6.QtCore import QFile, QIODevice
from PySide6.QtGui import Qt, QIcon, QPainter, QColor, QPixmap
from PySide6.QtSvg import QSvgRenderer


COPY_ICON = QIcon("./assets/icons/copy.svg")
MIC_OFF_ICON = QIcon("./assets/icons/mic-off.svg")
MIC_ON_ICON = QIcon("./assets/icons/mic.svg")
PAUSE_ICON = QIcon("./assets/icons/pause.svg")
PLAY_ICON = QIcon("./assets/icons/play.svg")
SEND_ICON = QIcon("./assets/icons/send.svg")
SETTINGS_ICON = QIcon("./assets/icons/settings.svg")
DELETE_ICON = QIcon("./assets/icons/trash-2.svg")
SPEAKER_ON_ICON = QIcon("./assets/icons/volume-2.svg")
SPEAKER_OFF_ICON = QIcon("./assets/icons/volume-x.svg")


def recolor_svg_icon(icon_path: str, color: QColor) -> QIcon:
    file = QFile(icon_path)
    if not file.open(QIODevice.ReadOnly):
        return QIcon()  # Return an empty icon if the file can't be read

    # Create an SVG renderer
    renderer = QSvgRenderer(file)

    # Create a QPixmap with the size of the SVG
    pixmap = QPixmap(renderer.defaultSize())
    pixmap.fill(Qt.transparent)  # Fill the pixmap with transparency

    # Create a painter to draw on the pixmap
    painter = QPainter(pixmap)
    renderer.render(painter)  # Render the SVG to the pixmap
    painter.end()

    # Recolor the rendered pixmap using the desired color
    pixmap = pixmap.copy()  # Make a copy of the pixmap for further manipulation
    painter.begin(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()

    return QIcon(pixmap)


def update_icon_colors(theme: str):
    icon_color = QColor(Qt.white) if theme == "dark" else QColor(Qt.black)

    global COPY_ICON, MIC_OFF_ICON, MIC_ON_ICON, PAUSE_ICON, PLAY_ICON, SEND_ICON, SETTINGS_ICON, DELETE_ICON, SPEAKER_ON_ICON, SPEAKER_OFF_ICON

    COPY_ICON = recolor_svg_icon("./assets/icons/copy.svg", icon_color)
    MIC_OFF_ICON = recolor_svg_icon("./assets/icons/mic-off.svg", icon_color)
    MIC_ON_ICON = recolor_svg_icon("./assets/icons/mic.svg", icon_color)
    PAUSE_ICON = recolor_svg_icon("./assets/icons/pause.svg", icon_color)
    PLAY_ICON = recolor_svg_icon("./assets/icons/play.svg", icon_color)
    SEND_ICON = recolor_svg_icon("./assets/icons/send.svg", icon_color)
    SETTINGS_ICON = recolor_svg_icon("./assets/icons/settings.svg", icon_color)
    DELETE_ICON = recolor_svg_icon("./assets/icons/trash-2.svg", icon_color)
    SPEAKER_ON_ICON = recolor_svg_icon("./assets/icons/volume-2.svg", icon_color)
    SPEAKER_OFF_ICON = recolor_svg_icon("./assets/icons/volume-x.svg", icon_color)
