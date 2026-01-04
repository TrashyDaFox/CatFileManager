from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar, QLabel, QVBoxLayout, QWidget, QListView, QFileSystemModel, QLineEdit, QDockWidget, QSplitter, QTreeView, QAbstractItemView, QTableView, QMenu, QStyleFactory, QSizePolicy, QGraphicsOpacityEffect, QMessageBox, QTabWidget, QPushButton, QHBoxLayout, QInputDialog
from PySide6.QtGui import QIcon, QAction, QActionGroup, QPalette, QColor, QFontDatabase, QFont
from PySide6.QtCore import Qt, QSize, QDir, QObject, QEvent, QUrl, QMimeData
from text import TEXT_MD, TEXT_XXXL
from settings import SettingsDialog
from app_config import PRODUCT_NAME, DEBUG
import qdarkstyle
import config_api
import shutil
import sys
import os
from urllib.parse import urlparse, unquote
import subprocess
import platform
from pathlib import Path
def resource_path(relative_path):
    # If running from PyInstaller bundle, _MEIPASS points to temp dir
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)
class PaneClickFilter(QObject):
    def __init__(self, app, panelID):
        super().__init__()
        self.app = app
        self.panelID = panelID

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            print("AA")
            self.app.currentSide = self.panelID
            self.app.update_borders()
        return False  # let the event continue to normal handlers
class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # self.app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        print(QStyleFactory.keys())
        if "Breeze" in QStyleFactory.keys():
            print("Using breeze")
            self.app.setStyle("Breeze")
        self.active_color = "#ff85bc"
        self.inactive_color = "#cf1f6e"
        font_id = QFontDatabase.addApplicationFont(resource_path("assets/MaterialIcons-Regular.ttf"))
        if font_id == -1:
            print("Failed to load font :<")
        else:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            print(f"Loaded font: {font_family}")
        self.window = QMainWindow()
        self.window.show()
        self.config = config_api.Config()
        self.window.setMinimumSize(900, 500)
        self.window.setWindowIcon(QIcon(resource_path("/assets/app_icon")))
        self.window.setWindowTitle(f"{PRODUCT_NAME} - {Path.home()}")
        self.currentSide = "left"
        path_left = self.config.get("path_left")
        if not path_left:
            path_left = str(Path.home())
        self.instances = [{
            "tab_title": "Default",
            "path_left": path_left,
            "path_right": str(Path.home()),
            "panes": {
                "left": {},
                "right": {}
            }
        }]
        self.model = QFileSystemModel()
        self.model.setRootPath("/")
        self.model.setReadOnly(False)
        self.model2 = QFileSystemModel()
        self.model2.setRootPath("/")
        self.model2.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.model2.setReadOnly(False)
        self.currentInstance = 0
        self.appContent = QVBoxLayout()
        self.appContent.setContentsMargins(0, 0, 0, 0)
        self.window.setFont(TEXT_MD)
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.appContent)
        self.window.setCentralWidget(self.centralWidget)
        self.TEXT_ICON = QFont("Material Icons", 19)
        self.TEXT_ICON.setPixelSize(19)
        self.setupToolbars()
        self.setupTabs()
        for i in range(len(self.instances)):
            self.currentInstance = i
            self.setupAppContent()
        self.currentInstance = 0
        self.set_list_layout()
        self.update_borders()
        self.update_browsers()
        self.app.paletteChanged.connect(self.update_overlays)
    def setupTabs(self):
        self.tabs = QTabWidget()
        self.appContent.addWidget(self.tabs, 1)
        self.tabs.currentChanged.connect(self.current_changed)
        self.tabs.setMovable(True)
        add_button = QPushButton("+")
        add_button.setMaximumSize(30, 30)
        add_button.clicked.connect(self.add_tab)
        corner_container = QWidget()
        corner_layout = QHBoxLayout(corner_container)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.addWidget(add_button)
        self.tabs.setCornerWidget(corner_container, Qt.TopRightCorner)
        self.tabs.tabBar().tabMoved.connect(self.on_tab_moved)
        self.tabs.tabBarDoubleClicked.connect(self.on_tab_double_clicked)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.on_tab_close)
    def on_tab_close(self, index):
        self.tabs.removeTab(index)

        del self.instances[index]

        if self.currentInstance >= len(self.instances):
            self.currentInstace = len(self.instances) - 1

        if len(self.instances) == 0:
            self.window.close()
    def on_tab_double_clicked(self, index):
        if index == -1:
            return
        old_name = self.tabs.tabText(index)
        new_name, ok = QInputDialog.getText(self.window, "Rename Tab", "New tab name:", text=old_name)
        if ok and new_name.strip():
            self.tabs.setTabText(index, new_name.strip())
            self.instances[index]["tab_title"] = new_name
    def on_tab_moved(self, from_index, to_index):
        item = self.instances.pop(from_index)
        self.instances.insert(to_index, item)
    def add_tab(self):
        new_name, ok = QInputDialog.getText(self.window, "Create Tab", "New tab name:")
        if ok and new_name.strip():
            self.instances.append({
                "tab_title": new_name,
                "path_left": str(Path.home()),
                "path_right": str(Path.home()),
                "panes": {
                    "left": {},
                    "right": {}
                }
            })
            self.currentInstance = len(self.instances) - 1
            self.setupAppContent()
            self.tabs.setCurrentIndex(self.currentInstance)
    def current_changed(self, index):
        print(f"Changed: {str(index)}")
        self.currentInstance = index
    def update_overlays(self):
        for pane_id, pane in self.instances[self.currentInstance]["panes"].items():
            parent = pane["parentWidget"]

            # Check if overlay already exists
            overlay = getattr(parent, "_dim_overlay", None)
            border = getattr(parent, "_border_overlay", None)
            p = self.app.palette()
            base = p.color(p.ColorRole.Window)
            accent = p.color(p.ColorRole.Highlight)
            stylesheet = f"background-color: rgba({base.red()}, {base.green()}, {base.blue()}, 127);"
            overlay.setStyleSheet(stylesheet)  # semi-transparent black
            stylesheet2 = f"border: 2px solid rgb({accent.red()}, {accent.green()}, {accent.blue()});background-color: rgba(0, 0, 0, 0);"
            border.setStyleSheet(stylesheet2)  # semi-transparent black

    def update_browsers(self):
        for pane2 in self.instances[self.currentInstance]["panes"]:
            pane = self.instances[self.currentInstance]["panes"][pane2]
            path = self.instances[self.currentInstance][f"path_{pane['id']}"]
            pane["listView"].setRootIndex(self.model.index(path))
    def update_borders(self):
        for pane_id, pane in self.instances[self.currentInstance]["panes"].items():
            parent = pane["parentWidget"]

            # Check if overlay already exists
            overlay = getattr(parent, "_dim_overlay", None)
            overlay2 = getattr(parent, "_border_overlay", None)
            if overlay is None:
                overlay = QWidget(parent)
                overlay.setObjectName("dimOverlay")
                p = self.app.palette()
                base = p.color(p.ColorRole.Window)
                stylesheet = f"background-color: rgba({base.red()}, {base.green()}, {base.blue()}, 100);"
                overlay.setStyleSheet(stylesheet)  # semi-transparent black
                overlay.setGeometry(parent.rect())
                overlay.setAttribute(Qt.WA_TransparentForMouseEvents)  # let clicks pass through
                overlay.raise_()
                overlay.show()
                parent._dim_overlay = overlay
            if overlay2 is None:
                overlay2 = QWidget(parent)
                overlay2.setObjectName("borderOverlay")
                p = self.app.palette()
                base = p.color(p.ColorRole.Highlight)
                stylesheet = f"border: 2px solid rgb({base.red()}, {base.green()}, {base.blue()});"
                overlay2.setStyleSheet(stylesheet)  # semi-transparent black
                overlay2.setGeometry(parent.rect())
                overlay2.setAttribute(Qt.WA_TransparentForMouseEvents)  # let clicks pass through
                overlay2.raise_()
                overlay2.show()
                parent._border_overlay = overlay2
            parent.resizeEvent = lambda event, o=overlay, o2=overlay2, p=parent: {(o.setGeometry(p.rect()), o2.setGeometry(p.rect()))}
            # Show only for inactive pane
            if self.currentSide == pane_id:
                overlay.hide()
                overlay2.show()
                overlay2.raise_()
                if "currentView2" in self.instances[self.currentInstance]["panes"][self.currentSide]:
                    if self.instances[self.currentInstance]["panes"][self.currentSide]["currentView2"] == "ICON":
                        self.icon_action.setChecked(True)
                        self.list_action.setChecked(False)
                    else:
                        self.icon_action.setChecked(False)
                        self.list_action.setChecked(True)
            else:
                overlay.show()
                overlay2.hide()
                overlay.raise_()  # ensure it’s on top

    def changeDirectory(self, path):
        if self.currentSide == "left":
            self.config.set("path_left", path)
        self.instances[self.currentInstance][f"path_{self.currentSide}"] = path
        self.instances[self.currentInstance]["panes"][self.currentSide]["listView"].setRootIndex(self.model.index(self.instances[self.currentInstance][f"path_{self.currentSide}"]))
        self.instances[self.currentInstance]["panes"][self.currentSide]["iconView"].setRootIndex(self.model.index(self.instances[self.currentInstance][f"path_{self.currentSide}"]))
        self.window.setWindowTitle(f"{PRODUCT_NAME} - {path}")
        self.path_input.setText(path)
        self.systemTreeView.setCurrentIndex(self.model2.index(self.instances[self.currentInstance][f"path_{self.currentSide}"]))
    def parse_locations(self, argv):
        paths = []
        for arg in argv[1:]:
            if arg.startswith("file://"):
                uri = urlparse(arg)
                paths.append(unqoute(uri.path))
            else:
                paths.append(str(Path(arg).expanduser().resolve()))
    def run(self):
        self.app.exec()
    def setupAppContent(self):
        self.instances[self.currentInstance]["splitter"] = QSplitter(Qt.Horizontal)
        self.leftWidget = QWidget()
        self.rightWidget = QWidget()
        self.leftSide = QVBoxLayout()
        self.rightSide = QVBoxLayout()
        self.leftSide.setContentsMargins(0,0,0,0)
        self.rightSide.setContentsMargins(0,0,0,0)
        self.leftWidget.setLayout(self.leftSide)
        self.rightWidget.setLayout(self.rightSide)
        self.setupFileBrowser(self.leftSide, "left", self.leftWidget)
        self.setupFileBrowser(self.rightSide, "right", self.rightWidget)
        self.currentSide = "left"
        self.instances[self.currentInstance]["splitter"].addWidget(self.leftWidget)
        self.instances[self.currentInstance]["splitter"].addWidget(self.rightWidget)
        self.instances[self.currentInstance]["splitter"].setSizes([1,1])
        self.appContent.addWidget(self.instances[self.currentInstance]["splitter"])
        self.appContent.setStretch(0, 1)
        self.tabs.addTab(self.instances[self.currentInstance]["splitter"], self.instances[self.currentInstance]["tab_title"])
    def setupFileBrowser(self, panel, panelID, parentWidget):
        # Central widget container
        self.instances[self.currentInstance]["panes"][panelID]["widget"] = panel
        self.instances[self.currentInstance]["panes"][panelID]["parentWidget"] = parentWidget
        self.instances[self.currentInstance]["panes"][panelID]["id"] = panelID
        # File views
        self.instances[self.currentInstance]["panes"][panelID]["listView"] = QTableView()   # list mode: multi-column
        self.instances[self.currentInstance]["panes"][panelID]["iconView"] = QListView()    # icon mode: thumbnails/icons
        filter = PaneClickFilter(self, panelID)
        self.instances[self.currentInstance]["panes"][panelID]["filter"] = filter
        # parentWidget.installEventFilter(filter)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].viewport().installEventFilter(filter)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].viewport().installEventFilter(filter)
        # Shared model
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setModel(self.model)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setModel(self.model)

        # List mode setup
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setRootIndex(self.model.index(self.instances[self.currentInstance][f"path_{panelID}"]))
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setSelectionBehavior(QAbstractItemView.SelectRows)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setDragEnabled(True)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setAcceptDrops(True)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setDropIndicatorShown(True)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setDragDropMode(QAbstractItemView.DragDrop)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setShowGrid(False)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].verticalHeader().hide()
        self.instances[self.currentInstance]["panes"][panelID]["listView"].horizontalHeader().setStretchLastSection(True)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setSortingEnabled(True)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.instances[self.currentInstance]["panes"][panelID]["listView"].customContextMenuRequested.connect(self.show_menu)
        # Icon mode setup
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setRootIndex(self.model.index(self.instances[self.currentInstance][f"path_{panelID}"]))
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setSelectionBehavior(QAbstractItemView.SelectItems)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setResizeMode(QListView.Adjust)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setViewMode(QListView.IconMode)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setFlow(QListView.LeftToRight)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setWrapping(True)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setGridSize(QSize(96, 96))
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setSpacing(8)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setDragEnabled(True)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setAcceptDrops(True)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setDropIndicatorShown(True)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setDragDropMode(QAbstractItemView.DragDrop)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].customContextMenuRequested.connect(self.show_menu)
        # Start in list mode
        self.instances[self.currentInstance]["panes"][panelID]["currentView"] = self.instances[self.currentInstance]["panes"][panelID]["listView"]
        panel.addWidget(self.instances[self.currentInstance]["panes"][panelID]["currentView"])

        self.instances[self.currentInstance]["panes"][panelID]["listView"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # Connect double-click
        self.instances[self.currentInstance]["panes"][panelID]["listView"].doubleClicked.connect(self.on_item_double_clicked)
        self.instances[self.currentInstance]["panes"][panelID]["iconView"].doubleClicked.connect(self.on_item_double_clicked)
    def on_item_double_clicked(self, index):
        item_data = index.data()
        path = Path(self.instances[self.currentInstance][f"path_{self.currentSide}"]) / item_data
        if path.is_dir():
            self.changeDirectory(str(path))
        else:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path]) 
    def validate_path(self, text):
        path = Path(text)
        palette = self.path_input.palette()
        if path.exists() and path.is_dir():
            palette.setColor(QPalette.ColorRole.Highlight, QColor("lightgreen"))
        else:
            palette.setColor(QPalette.ColorRole.Highlight, QColor("lightcoral"))
        self.path_input.setPalette(palette)
    def goto(self):
        path = Path(self.path_input.text())
        if path.exists() and path.is_dir():
            self.changeDirectory(str(path))
        elif path.exists() and not path.is_dir():
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        else:
            return
    def on_tree_clicked(self, index):
        path = self.model2.filePath(index)
        self.changeDirectory(str(path))
    def setupToolbars(self):
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(str(Path.home()))
        self.path_input.textChanged.connect(self.validate_path)
        self.path_input.returnPressed.connect(self.goto)
        self.path_input.setText(self.getActivePath())
        self.appContent.addWidget(self.path_input)
        toolbar = QToolBar("Meow")
        toolbar.setMovable(False)
        toolbar2 = QToolBar("Woof")
        toolbar2.setMovable(False)
        toolbar2.setContentsMargins(0, 0, 0, 0)
        toolbar2.setStyleSheet("QToolBar { spacing: 0px; padding: 0px; }")
        # ---- Layout toggle actions ----
        layout_group = QActionGroup(self.window)
        layout_group.setExclusive(True)

        self.list_action = QAction("\ue896", self.window) # LIST
        self.list_action.setFont(self.TEXT_ICON)
        self.list_action.setCheckable(True)
        self.list_action.setChecked(True)

        self.icon_action = QAction("\ue5c3", self.window)
        self.icon_action.setFont(self.TEXT_ICON)
        self.icon_action.setCheckable(True)

        layout_group.addAction(self.list_action)
        layout_group.addAction(self.icon_action)

        self.list_action.triggered.connect(self.set_list_layout)
        self.icon_action.triggered.connect(self.set_icon_layout)

        toolbar2.addAction(self.list_action)
        toolbar2.addAction(self.icon_action)
        toolbar2.addSeparator()

        dock = QDockWidget("Library", self.window)
        dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        dock.setTitleBarWidget(QWidget())
        self.window.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.splitter = QSplitter(Qt.Vertical)
        self.library = QWidget()
        self.system = QWidget()
        self.libraryContent = QVBoxLayout(self.library)
        self.libraryContentText = QLabel("Library")
        self.libraryContent.addWidget(self.libraryContentText)
        self.systemContent = QVBoxLayout(self.system)
        self.systemContentText = QLabel("System")
        self.systemContent.addWidget(self.systemContentText)
        self.systemTreeView = QTreeView()
        self.systemTreeView.setModel(self.model2)
        self.systemTreeView.setCurrentIndex(self.model2.index(self.instances[self.currentInstance][f"path_{self.currentSide}"]))
        self.systemTreeView.clicked.connect(self.on_tree_clicked)
        self.systemTreeView.setHeaderHidden(True)
        self.systemTreeView.setColumnHidden(1, True)
        self.systemTreeView.setColumnHidden(2, True)
        self.systemTreeView.setColumnHidden(3, True)
        self.systemContent.addWidget(self.systemTreeView)
        self.splitter.addWidget(self.library)
        self.splitter.addWidget(self.system)
        dock.setWidget(self.splitter)
        dock.setMinimumWidth(250)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.home_action = QAction("\ue88a", self.window)
        self.home_action.setFont(self.TEXT_ICON)
        self.home_action.triggered.connect(self.home)
        toolbar2.addAction(self.home_action)

        self.up_action = QAction("\ue316", self.window)
        self.up_action.setFont(self.TEXT_ICON)
        self.up_action.triggered.connect(self.up)

        toolbar2.addAction(self.up_action)
        self.back_action = QAction("\ue314", self.window)
        self.back_action.setFont(self.TEXT_ICON)
        self.back_action.triggered.connect(self.back)

        toolbar2.addAction(self.back_action)
        self.forward_action = QAction("\ue315", self.window)
        self.forward_action.setFont(self.TEXT_ICON)
        self.forward_action.triggered.connect(self.forward)

        toolbar2.addAction(self.forward_action)

        settings_action = QAction("\ue8b8", self.window)
        settings_action.setFont(self.TEXT_ICON)
        settings_action.triggered.connect(self.open_settings)
        settings_action.setStatusTip("Open the settings! :3")
        toolbar.addAction(settings_action)
        if DEBUG:
            dev_action = QAction("\ue869", self.window)
            dev_action.setStatusTip("This is a debug menu")
            dev_action.setFont(self.TEXT_ICON)
            dev_action.triggered.connect(self.dev_menu)
            toolbar.addAction(dev_action)

        self.window.addToolBar(toolbar)
        self.appContent.addWidget(toolbar2)
    def open_settings(self):
        settings = SettingsDialog(self.window)
        settings.exec()
    def getActivePath(self):
        return self.instances[self.currentInstance][f"path_{self.currentSide}"]
    def up(self):
        path = Path(self.getActivePath())
        self.changeDirectory(str(path.parent))
    def dev_menu(self):
        pass
    def set_list_layout(self):
        # Switch to QTableView
        self.instances[self.currentInstance]["panes"][self.currentSide]["widget"].removeWidget(self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])
        self.instances[self.currentInstance]["panes"][self.currentSide]["currentView2"] = "LIST"
        self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"].hide()
        self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"] = self.instances[self.currentInstance]["panes"][self.currentSide]["listView"]
        self.instances[self.currentInstance]["panes"][self.currentSide]["widget"].addWidget(self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])
        self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"].show()

    def set_icon_layout(self):
        # Switch to QListView (icons)
        self.instances[self.currentInstance]["panes"][self.currentSide]["widget"].removeWidget(self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])
        self.instances[self.currentInstance]["panes"][self.currentSide]["currentView2"] = "ICON"
        self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"].hide()
        self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"] = self.instances[self.currentInstance]["panes"][self.currentSide]["iconView"]
        self.instances[self.currentInstance]["panes"][self.currentSide]["widget"].addWidget(self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])
        self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"].show()
    def copy_to_clipboard_action(self, index):
        file_path = self.model.filePath(index)

        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(file_path)])
        mime_data.setText(file_path)
        self._clipboard_mime_data = mime_data
        self.app.clipboard().setMimeData(self._clipboard_mime_data)
    def copy(self, src_path, dest_path):
        try:
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dest_path)
            elif os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path)
        except PermissionError:
            msg = QMessageBox()
            msg.setWindowTitle("Permission Denied")
            msg.setText(f"Cannot copy '{os.path.basename(src_path)}'")
            msg.setInformativeText("You don't have permission to access this file or folder.")
            msg.setIcon(QMessageBox.Critical)
            msg.exec()
        except OSError as e:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(f"Cannot copy '{os.path.basename(src_path)}'")
            msg.setInformativeText(str(e))
            msg.setIcon(QMessageBox.Critical)
            msg.exec()
        else:
            print(f"Copied {src_path} → {dest_path} successfully!")

    def paste_from_clipboard_action(self, dest_index):
        dest_folder = self.model.filePath(dest_index)
        if not os.path.isdir(dest_folder):
            dest_folder = os.path.dirname(dest_folder)

        clipboard = self.app.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasUrls():
            print("HAS URLS")
            for url in mime_data.urls():
                src_path = url.toLocalFile()
                if os.path.exists(src_path):
                    filename = os.path.basename(src_path)
                    dest_path = os.path.join(dest_folder, filename)
                    print(src_path, dest_path)
                    if os.path.exists(dest_path):
                        msg = QMessageBox()
                        msg.setWindowTitle("File Conflict")
                        msg.setText(f"The {"folder" if os.path.isdir(src_path) else "file"} already exists here.")
                        msg.setInformativeText("What do you want to do?")
                        overwrite_btn = msg.addButton("Overwrite", QMessageBox.YesRole)
                        skip_btn = msg.addButton("Skip", QMessageBox.NoRole)
                        rename_btn = msg.addButton("Rename", QMessageBox.RejectRole)
                        msg.exec()
                    else:
                        self.copy(src_path, dest_path)

                    print(f"Pasted {src_path} → {dest_path}")
        else:
            print("Clipboard has no files to paste!")
    def show_menu(self, pos):
        index = self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"].indexAt(pos)
        menu = QMenu(self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])

        rename_action = QAction("Rename", self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])
        delete_action = QAction("Delete", self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])
        copy_action = QAction("Copy", self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])
        paste_action = QAction("Paste", self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"])
        if index.isValid():
            menu.addAction(copy_action)
        menu.addAction(paste_action)
        if index.isValid():
            menu.addSeparator()
            menu.addAction(rename_action)
            menu.addSeparator()
            menu.addAction(delete_action)

        rename_action.triggered.connect(lambda: self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"].edit(index))
        delete_action.triggered.connect(lambda: self.model.remove(index))
        copy_action.triggered.connect(lambda: self.copy_to_clipboard_action(index))
        paste_action.triggered.connect(lambda: self.paste_from_clipboard_action(self.getPane()["currentView"].rootIndex()))

        menu.exec(self.instances[self.currentInstance]["panes"][self.currentSide]["currentView"].viewport().mapToGlobal(pos))
    def getPane(self):
        return self.instances[self.currentInstance]["panes"][self.currentSide]
    def home(self):
        self.changeDirectory(str(Path.home()))
    def back(self):
        return
        self.instances[self.currentInstance]["forwardPath"] = self.instances[self.currentInstance]["path"]
        self.changeDirectory(self.instances[self.currentInstance]["backPath"])
        
    def forward(self):
        return
        self.changeDirectory(self.instances[self.currentInstance]["backPath"])