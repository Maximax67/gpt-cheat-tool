from dotenv import load_dotenv

load_dotenv()

import sys
import qdarktheme
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
