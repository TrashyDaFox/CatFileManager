from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog, QVBoxLayout, QLabel, QTabWidget, QWidget, QHBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from app.text import TEXT_LG
import app.app_config as app_config
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedSize(600, 500)
        self.setupAbout()
        self.setup()
    def setupAbout(self):
        self.aboutWidget = QWidget()
        self.aboutLayout = QVBoxLayout()
        label = QLabel()
        pixmap = QPixmap("./assets/app_icon.png")
        label.setPixmap(pixmap)
        label.setScaledContents(True)
        label.setFixedSize(128, 128)
        label2 = QLabel(f"<a href=\"https://github.com/TrashyDaFox/CatFileManager\">{app_config.PRODUCT_NAME} {app_config.VERSION}</a>")
        label2.setFont(TEXT_LG)
        label2.setAlignment(Qt.AlignCenter)
        label.setAlignment(Qt.AlignCenter)
        label2.setTextFormat(Qt.RichText)
        label2.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label2.setOpenExternalLinks(True)
        self.aboutLayout.setAlignment(Qt.AlignHCenter)
        self.aboutLayout.addWidget(label, alignment=Qt.AlignHCenter)
        # self.aboutLayout.addWidget(label)
        self.aboutLayout.addWidget(label2, alignment=Qt.AlignHCenter)
        # self.aboutLayout.addWidget(label2)
        self.aboutLayout.addStretch(0)
        self.aboutWidget.setLayout(self.aboutLayout)
    def setup(self):
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.aboutWidget, "About")
        self.tabs.addTab(QWidget(), "Tags")
        self.tabs.addTab(QWidget(), "Galleries")
        self.tabs.addTab(QWidget(), "Startup")
        self.tabs.addTab(QWidget(), "Other")
        self.layout.addWidget(self.tabs)