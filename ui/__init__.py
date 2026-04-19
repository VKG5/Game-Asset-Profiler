from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, QFileDialog, QShortcut, QMessageBox, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QKeySequence
from ui.tabs.overview_tab import OverviewTab
from ui.tabs.database_tab import DatabaseTab
from ui.tabs.folder_view_tab import FolderViewTab
from ui.tabs.visualization_tab import VisualizationTab
from db import init_db, set_db_path, export_db, clear_database
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
        load_action.setShortcut(QKeySequence.Open)  # Ctrl+O
        load_action.triggered.connect(self.load_database)
        file_menu.addAction(load_action)
        
        save_action = QAction("Save Database As...", self)
        save_action.setShortcut(QKeySequence.SaveAs)  # Ctrl+Shift+S
        save_action.triggered.connect(self.save_database)
        file_menu.addAction(save_action)
        
        export_action = QAction("Export Database...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))  # Ctrl+E
        export_action.triggered.connect(self.export_database)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        clear_action = QAction("Clear Database...", self)
        clear_action.triggered.connect(self.clear_database_action)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)  # Ctrl+R
        refresh_action.triggered.connect(self.refresh_all_tabs)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)  # Ctrl+Q
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("View")
        
        overview_action = QAction("Overview Tab", self)
        overview_action.setShortcut(QKeySequence("Ctrl+1"))
        overview_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        view_menu.addAction(overview_action)
        
        database_action = QAction("Database Tab", self)
        database_action.setShortcut(QKeySequence("Ctrl+2"))
        database_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        view_menu.addAction(database_action)
        
        visualization_action = QAction("Visualization Tab", self)
        visualization_action.setShortcut(QKeySequence("Ctrl+3"))
        visualization_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        view_menu.addAction(visualization_action)
        
        view_menu.addSeparator()
        
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
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        
        shortcuts_action = QAction("Keyboard Shortcuts", self)
        shortcuts_action.setShortcut(QKeySequence("Ctrl+?"))
        shortcuts_action.triggered.connect(self.show_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        # ========================= Keyboard Shortcuts =========================
        # Ctrl+R: Refresh all tabs
        QShortcut(QKeySequence.Refresh, self).activated.connect(self.refresh_all_tabs)
        # Ctrl+1: Switch to Overview tab
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(lambda: self.tabs.setCurrentIndex(0))
        # Ctrl+2: Switch to Database tab
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(lambda: self.tabs.setCurrentIndex(1))
        # Ctrl+3: Switch to Visualization tab
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(lambda: self.tabs.setCurrentIndex(2))
        # Ctrl+?: Show keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+?"), self).activated.connect(self.show_shortcuts_dialog)

    def load_database(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Database", "", "SQLite Databases (*.db);;All Files (*)")
        if file_path:
            set_db_path(file_path)
            self.refresh_all_tabs()
            
    def save_database(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Database As", "", "SQLite Databases (*.db);;All Files (*)")
        if file_path:
            export_db(file_path)
    
    def export_database(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Database", "", "SQLite Databases (*.db);;All Files (*)")
        if file_path:
            export_db(file_path)

    def clear_database_action(self):
        """Clear database with confirmation dialog"""
        from db import get_database_statistics
        try:
            stats = get_database_statistics()
            count = stats['total_assets']
        except:
            count = 0
        
        reply = QMessageBox.question(
            self, 
            "Clear Database", 
            f"This will delete all {count} assets from the database. This action cannot be undone.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                clear_database()
                self.refresh_all_tabs()
                QMessageBox.information(self, "Success", "Database cleared successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear database: {e}")

    def show_shortcuts_dialog(self):
        """Show keyboard shortcuts reference dialog"""
        dialog = KeyboardShortcutsDialog(self)
        dialog.exec_()

    def show_about_dialog(self):
        """Show about dialog"""
        about_text = (
            "Game Asset Profiler v1.0\n\n"
            "A PyQt5-based desktop application for analyzing and profiling game assets.\n\n"
            "Features:\n"
            "• Multi-threaded asset scanning\n"
            "• VRAM estimation and analysis\n"
            "• Advanced insights and recommendations\n"
            "• Interactive visualization and filtering\n\n"
            "Built with Python, PyQt5, PIL, and Matplotlib"
        )
        QMessageBox.information(self, "About Game Asset Profiler", about_text)

    def refresh_all_tabs(self):
        """Refresh all tabs with current database data"""
        self.overview_tab.load_logs()
        self.overview_tab.refresh_statistics()
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


class KeyboardShortcutsDialog(QDialog):
    """Dialog showing all keyboard shortcuts"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QTableWidget { gridline-color: #45475a; }
            QHeaderView::section { background-color: #313244; color: #cdd6f4; border: none; }
            QTableWidget::item { color: #cdd6f4; }
        """)
        
        layout = QVBoxLayout()
        
        title = QTableWidgetItem("Keyboard Shortcuts Reference")
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 180)
        
        shortcuts = [
            ("GLOBAL", ""),
            ("Ctrl+?", "Show keyboard shortcuts"),
            ("Ctrl+1", "Switch to Overview tab"),
            ("Ctrl+2", "Switch to Database tab"),
            ("Ctrl+3", "Switch to Visualization tab"),
            ("Ctrl+R", "Refresh all tabs"),
            ("Ctrl+O", "Load database"),
            ("Ctrl+Shift+S", "Save database as"),
            ("Ctrl+Q", "Exit application"),
            ("", ""),
            ("OVERVIEW TAB", ""),
            ("Ctrl+N", "Start new scan"),
            ("Ctrl+E", "Export logs"),
            ("Ctrl+C", "Copy selected log path"),
            ("", ""),
            ("DATABASE TAB", ""),
            ("Ctrl+F", "Focus search box"),
            ("Ctrl+C", "Copy selected asset path"),
            ("Ctrl+E", "Export selected assets"),
            ("Ctrl+R", "Refresh data"),
            ("", ""),
            ("VISUALIZATION TAB", ""),
            ("Ctrl+R", "Refresh visualization"),
        ]
        
        row = 0
        for shortcut, action in shortcuts:
            self.table.insertRow(row)
            
            shortcut_item = QTableWidgetItem(shortcut)
            action_item = QTableWidgetItem(action)
            
            if shortcut in ["GLOBAL", "OVERVIEW TAB", "DATABASE TAB", "VISUALIZATION TAB"]:
                shortcut_item.setForeground(QTableWidgetItem("test").foreground())
                shortcut_item.setData(12, True)  # User role for bold styling
                action_item.setData(12, True)
                # Simulate bold with styling
                font = shortcut_item.font()
                font.setBold(True)
                shortcut_item.setFont(font)
                action_item.setFont(font)
                shortcut_item.setForeground(QTableWidgetItem("test").foreground())
            
            self.table.setItem(row, 0, shortcut_item)
            self.table.setItem(row, 1, action_item)
            row += 1
        
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.table)
        self.setLayout(layout)