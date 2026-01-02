from PySide6.QtWidgets import QApplication, QMainWindow, QSizePolicy
from PySide6.QtGui import QIcon
from app_config import PRODUCT_NAME
import sys
from pathlib import Path

class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.window = QMainWindow()
        self.window.show()
        self.window.setMinimumSize(900, 500)
        self.window.setWindowIcon()
        self.window.setWindowTitle(f"{PRODUCT_NAME} - {Path.home()}")
        self.instances = [{
            "path": Path.home()
        }]
        self.currentInstance = 0
    def changeDirectory(self, path):
        self.window.setWindowTitle(f"{PRODUCT_NAME} - {path}")
    def run(self):
        self.app.exec()