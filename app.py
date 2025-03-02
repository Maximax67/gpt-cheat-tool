from dotenv import load_dotenv


load_dotenv()

import sys
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from utils.app_icon import set_app_icon

if __name__ == "__main__":
    app = QApplication(sys.argv)

    set_app_icon(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
