from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def switch_theme(app: QApplication, theme: str):
    """
    Switch the theme of the application.

    :param app: QApplication instance
    :param theme: "dark", "light", or "system"
    """
    palette = app.palette()

    if theme == "dark":
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)

    elif theme == "light":
        palette.setColor(QPalette.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, Qt.black)

    elif theme == "system":
        app.setStyle(
            "Fusion"
        )
        return  # If system theme is selected, let system settings decide.

    app.setPalette(palette)
