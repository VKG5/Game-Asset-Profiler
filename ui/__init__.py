from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, QFileDialog, QShortcut
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QKeySequence
from ui.tabs.overview_tab import OverviewTab
from ui.tabs.database_tab import DatabaseTab
from ui.tabs.folder_view_tab import FolderViewTab
from ui.tabs.visualization_tab import VisualizationTab
from db import init_db, set_db_path, export_db
from ui.themes import get_theme

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Game Asset Profiler")
        self.resize(1200, 800)

        # Load theme from settings
        self.settings = QSettings("GameAssetProfiler", "GameAssetProfiler")
        self.current_theme = self.settings.value("theme", "dark")

        init_db()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs as attributes (IMPORTANT)
        self.overview_tab = OverviewTab()
        self.database_tab = DatabaseTab()
        self.visualization_tab = VisualizationTab()

        self.tabs.addTab(self.overview_tab, "Overview")
        self.tabs.addTab(self.database_tab, "Database")
        self.tabs.addTab(self.visualization_tab, "Visualization")

        self.overview_tab.scan_completed_signal.connect(self.database_tab.load_data)
        self.overview_tab.scan_completed_signal.connect(self.visualization_tab.load_data)

        self._create_menu()
        
        # Apply initial theme
        self.apply_theme(self.current_theme)

    def _create_menu(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        load_action = QAction("Load Database...", self)
        load_action.triggered.connect(self.load_database)
        file_menu.addAction(load_action)
        
        save_action = QAction("Save Database As...", self)
        save_action.triggered.connect(self.save_database)
        file_menu.addAction(save_action)

        # View Menu
        view_menu = menubar.addMenu("View")
        
        dark_theme_action = QAction("Dark Theme", self, checkable=True)
        dark_theme_action.setChecked(self.current_theme == "dark")
        dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))
        view_menu.addAction(dark_theme_action)
        
        light_theme_action = QAction("Light Theme", self, checkable=True)
        light_theme_action.setChecked(self.current_theme == "light")
        light_theme_action.triggered.connect(lambda: self.apply_theme("light"))
        view_menu.addAction(light_theme_action)
        
        self.dark_theme_action = dark_theme_action
        self.light_theme_action = light_theme_action

        # ========================= Keyboard Shortcuts =========================
        # Ctrl+R: Refresh all tabs
        QShortcut(QKeySequence.Refresh, self).activated.connect(self.refresh_all_tabs)
        # Ctrl+1: Switch to Overview tab
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(lambda: self.tabs.setCurrentIndex(0))
        # Ctrl+2: Switch to Database tab
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(lambda: self.tabs.setCurrentIndex(1))
        # Ctrl+3: Switch to Visualization tab
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(lambda: self.tabs.setCurrentIndex(2))

    def load_database(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Database", "", "SQLite Databases (*.db);;All Files (*)")
        if file_path:
            set_db_path(file_path)
            self.refresh_all_tabs()
            
    def save_database(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Database As", "", "SQLite Databases (*.db);;All Files (*)")
        if file_path:
            export_db(file_path)

    def refresh_all_tabs(self):
        self.overview_tab.load_logs()
        self.database_tab.load_data()
        self.visualization_tab.load_data()

    def apply_theme(self, theme_name):
        """Apply theme and save preference"""
        self.current_theme = theme_name
        stylesheet = get_theme(theme_name)
        self.setStyleSheet(stylesheet)
        
        # Update menu checkboxes
        self.dark_theme_action.setChecked(theme_name == "dark")
        self.light_theme_action.setChecked(theme_name == "light")
        
        # Save preference
        self.settings.setValue("theme", theme_name)