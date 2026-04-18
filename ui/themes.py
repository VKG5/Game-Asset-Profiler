# Theme manager for Dark/Light mode switching

DARK_THEME = """
/* Global Application Style - Dark Theme */
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 15px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #313244;
    background-color: #1e1e2e;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid transparent;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-bottom: 1px solid #1e1e2e;
}

QTabBar::tab:hover {
    background-color: #313244;
}

/* Buttons */
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #45475a;
    border: 1px solid #585b70;
}

QPushButton:pressed {
    background-color: #181825;
}

QPushButton:disabled {
    background-color: #181825;
    color: #6c7086;
    border: 1px solid #313244;
}

/* Combo Box */
QComboBox {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 4px;
    padding: 6px 10px;
    color: #cdd6f4;
}

QComboBox::drop-down {
    border: none;
}

QComboBox:hover {
    border: 1px solid #45475a;
}

/* Line Edit */
QLineEdit {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 4px;
    padding: 6px 10px;
    color: #cdd6f4;
}

QLineEdit:focus {
    border: 1px solid #89b4fa;
}

/* Progress Bar */
QProgressBar {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    text-align: center;
    color: #cdd6f4;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 4px;
}

/* Table Widget */
QTableWidget {
    background-color: #1e1e2e;
    alternate-background-color: #181825;
    gridline-color: #313244;
    border: 1px solid #313244;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #45475a;
}

QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    padding: 4px;
    border: none;
    border-right: 1px solid #181825;
}

/* Tree Widget */
QTreeWidget {
    background-color: #1e1e2e;
    alternate-background-color: #181825;
    gridline-color: #313244;
    border: 1px solid #313244;
}

QTreeWidget::item:selected {
    background-color: #45475a;
}

/* Menu */
QMenuBar {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}

QMenuBar::item:selected {
    background-color: #313244;
}

QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
}

QMenu::item:selected {
    background-color: #313244;
}

/* Scroll Bar */
QScrollBar:vertical {
    background-color: #181825;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}

QScrollBar:horizontal {
    background-color: #181825;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #585b70;
}

QScrollBar::up-arrow, QScrollBar::down-arrow, QScrollBar::left-arrow, QScrollBar::right-arrow {
    border: none;
    background: none;
}

QScrollBar::sub-line, QScrollBar::add-line {
    background: none;
}
"""

LIGHT_THEME = """
/* Global Application Style - Light Theme */
QWidget {
    background-color: #f5f5f5;
    color: #333333;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 15px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #d0d0d0;
    background-color: #ffffff;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #e8e8e8;
    color: #666666;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid transparent;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #d0d0d0;
    border-bottom: 1px solid #ffffff;
}

QTabBar::tab:hover {
    background-color: #f0f0f0;
}

/* Buttons */
QPushButton {
    background-color: #e0e0e0;
    color: #333333;
    border: 1px solid #c0c0c0;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #d0d0d0;
    border: 1px solid #a0a0a0;
}

QPushButton:pressed {
    background-color: #c0c0c0;
}

QPushButton:disabled {
    background-color: #f5f5f5;
    color: #999999;
    border: 1px solid #d0d0d0;
}

/* Combo Box */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px 10px;
    color: #333333;
}

QComboBox::drop-down {
    border: none;
}

QComboBox:hover {
    border: 1px solid #a0a0a0;
}

/* Line Edit */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px 10px;
    color: #333333;
}

QLineEdit:focus {
    border: 1px solid #4a90e2;
}

/* Progress Bar */
QProgressBar {
    background-color: #e8e8e8;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    text-align: center;
    color: #333333;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #4a90e2;
    border-radius: 4px;
}

/* Table Widget */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f8f8;
    gridline-color: #e0e0e0;
    border: 1px solid #d0d0d0;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #cce5ff;
}

QHeaderView::section {
    background-color: #e8e8e8;
    color: #333333;
    padding: 4px;
    border: none;
    border-right: 1px solid #d0d0d0;
}

/* Tree Widget */
QTreeWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f8f8;
    gridline-color: #e0e0e0;
    border: 1px solid #d0d0d0;
}

QTreeWidget::item:selected {
    background-color: #cce5ff;
}

/* Menu */
QMenuBar {
    background-color: #f5f5f5;
    color: #333333;
    border-bottom: 1px solid #d0d0d0;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
}

QMenu {
    background-color: #f5f5f5;
    color: #333333;
    border: 1px solid #d0d0d0;
}

QMenu::item:selected {
    background-color: #e0e0e0;
}

/* Scroll Bar */
QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #d0d0d0;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #c0c0c0;
}

QScrollBar:horizontal {
    background-color: #f5f5f5;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #d0d0d0;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #c0c0c0;
}

QScrollBar::up-arrow, QScrollBar::down-arrow, QScrollBar::left-arrow, QScrollBar::right-arrow {
    border: none;
    background: none;
}

QScrollBar::sub-line, QScrollBar::add-line {
    background: none;
}
"""

def get_theme(theme_name="dark"):
    """Return theme stylesheet by name"""
    if theme_name.lower() == "light":
        return LIGHT_THEME
    return DARK_THEME
