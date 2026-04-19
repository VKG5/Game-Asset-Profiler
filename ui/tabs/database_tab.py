# Advanced DB Explorer + Folder Aggregation View (Integrated)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QComboBox, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMenu, QApplication, QFileDialog, QMessageBox,
    QCheckBox
)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QColor, QDesktopServices, QKeySequence, QClipboard
from PyQt5.QtWidgets import QShortcut

from db import filter_assets, search_assets_advanced
import os


class DatabaseTab(QWidget):
    def __init__(self):
        super().__init__()
        self.current_rows = []
        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self.load_data)
        self.recent_searches = []
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Filters
        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by path (live)...")
        # Connect with debounce
        self.search_input.textChanged.connect(self.on_search_text_changed)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "image", "other"])
        # Connect immediately (no debounce for dropdown)
        self.type_filter.currentTextChanged.connect(self.load_data)

        self.vram_filter = QComboBox()
        self.vram_filter.addItems([
            "All", "> 10 MB", "> 50 MB", "> 100 MB"
        ])
        # Connect immediately (no debounce for dropdown)
        self.vram_filter.currentTextChanged.connect(self.load_data)

        # Regex mode toggle
        self.regex_mode_checkbox = QCheckBox("Regex Mode")
        self.regex_mode_checkbox.setStyleSheet("font-size: 11px;")
        self.regex_mode_checkbox.stateChanged.connect(self.on_regex_mode_changed)

        # Clear filters button
        self.clear_filters_btn = QPushButton("Clear Filters")
        self.clear_filters_btn.clicked.connect(self.clear_all_filters)

        self.asset_count_label = QLabel("0 assets")
        self.asset_count_label.setStyleSheet("font-size: 12px; color: #a6adc8;")

        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(self.vram_filter)
        filter_layout.addWidget(self.regex_mode_checkbox)
        filter_layout.addWidget(self.clear_filters_btn)
        filter_layout.addStretch()
        filter_layout.addWidget(self.asset_count_label)

        # Toggle
        toggle_layout = QHBoxLayout()

        self.asset_view_btn = QPushButton("Asset View")
        self.folder_view_btn = QPushButton("Folder View")

        self.asset_view_btn.clicked.connect(self.show_asset_view)
        self.folder_view_btn.clicked.connect(self.show_folder_view)

        toggle_layout.addWidget(self.asset_view_btn)
        toggle_layout.addWidget(self.folder_view_btn)
        toggle_layout.addStretch()

        # Bulk Actions Toolbar (initially hidden)
        bulk_actions_layout = QHBoxLayout()
        bulk_actions_layout.setSpacing(10)
        
        bulk_label = QLabel("Selected Actions:")
        bulk_label.setStyleSheet("font-size: 12px; color: #a6adc8;")
        
        self.bulk_mark_fav_btn = QPushButton("★ Mark Favorite")
        self.bulk_mark_fav_btn.setFixedHeight(28)
        self.bulk_mark_fav_btn.clicked.connect(self.bulk_mark_favorite)
        
        self.bulk_unmark_fav_btn = QPushButton("☆ Unmark Favorite")
        self.bulk_unmark_fav_btn.setFixedHeight(28)
        self.bulk_unmark_fav_btn.clicked.connect(self.bulk_unmark_favorite)
        
        self.bulk_export_btn = QPushButton("📊 Export Selected")
        self.bulk_export_btn.setFixedHeight(28)
        self.bulk_export_btn.clicked.connect(self.shortcut_export_selected)
        
        bulk_actions_layout.addWidget(bulk_label)
        bulk_actions_layout.addWidget(self.bulk_mark_fav_btn)
        bulk_actions_layout.addWidget(self.bulk_unmark_fav_btn)
        bulk_actions_layout.addWidget(self.bulk_export_btn)
        bulk_actions_layout.addStretch()
        
        self.bulk_actions_widget = QWidget()
        self.bulk_actions_widget.setLayout(bulk_actions_layout)
        self.bulk_actions_widget.setVisible(False)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "★", "Path", "Type", "Size", "Width", "Height", "Channels", "VRAM (MB)", "Insights"
        ])
        self.table.setColumnWidth(0, 30)  # Star column width
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)

        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Folder/File", "VRAM (MB)"])
        self.tree.setVisible(False)

        main_layout.addLayout(filter_layout)
        main_layout.addLayout(toggle_layout)
        main_layout.addWidget(self.bulk_actions_widget)
        main_layout.addWidget(self.table)
        main_layout.addWidget(self.tree)

        self.setLayout(main_layout)

        # ========================= Keyboard Shortcuts =========================
        # Ctrl+C: Copy selected asset path
        QShortcut(QKeySequence.Copy, self).activated.connect(self.shortcut_copy_path)
        # Ctrl+E: Export selected assets to CSV
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.shortcut_export_selected)
        # Ctrl+F: Focus search box
        QShortcut(QKeySequence.Find, self).activated.connect(self.search_input.setFocus)
        # Ctrl+R: Refresh data
        QShortcut(QKeySequence.Refresh, self).activated.connect(self.load_data)

    # ========================= Data =========================
    def on_search_text_changed(self):
        """Debounce search input changes (300ms)"""
        self.search_debounce_timer.stop()
        self.search_debounce_timer.start(300)

    def on_regex_mode_changed(self):
        """When regex mode is toggled, reload data"""
        if self.search_input.text():
            self.load_data()

    def clear_all_filters(self):
        """Clear all filter criteria"""
        self.search_input.clear()
        self.type_filter.setCurrentIndex(0)
        self.vram_filter.setCurrentIndex(0)
        self.regex_mode_checkbox.setChecked(False)

    def load_data(self):
        search_text = self.search_input.text()
        selected_type = self.type_filter.currentText()
        vram_option = self.vram_filter.currentText()
        use_regex = self.regex_mode_checkbox.isChecked()

        min_vram = None
        if vram_option == "> 10 MB": min_vram = 10
        elif vram_option == "> 50 MB": min_vram = 50
        elif vram_option == "> 100 MB": min_vram = 100

        asset_type = None if selected_type == "All" else selected_type

        # Use advanced search with regex support
        rows = search_assets_advanced(
            search_query=search_text if search_text else None,
            asset_type=asset_type,
            min_vram=min_vram,
            use_regex=use_regex
        )

        self.current_rows = rows

        self.populate_table(rows)
        self.populate_tree(rows)
        
        # Update asset count label
        count = len(rows)
        self.asset_count_label.setText(f"{count} asset{'s' if count != 1 else ''}")

    # ========================= Asset View =========================
    def populate_table(self, rows):
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            # Column 0: Star (favorite indicator)
            is_favorite = row[8] if len(row) > 8 else 0
            star_text = "★" if is_favorite else "☆"
            star_item = QTableWidgetItem(star_text)
            star_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, star_item)

            # Columns 1-8: Asset data (shifted by 1)
            for j, value in enumerate(row[:8]):  # Only iterate through first 8 values (exclude is_favorite)
                col_index = j + 1  # Shift column index by 1 for the star
                item = QTableWidgetItem(str(value))

                # VRAM column (now at index 7 instead of 6)
                if j == 6:
                    try:
                        vram = float(value)
                        item.setData(Qt.UserRole, vram)
                        
                        if vram > 100:
                            item.setBackground(QColor("#f38ba8"))
                            item.setForeground(QColor("#11111b"))
                        elif vram > 50:
                            item.setBackground(QColor("#f9e2af"))
                            item.setForeground(QColor("#11111b"))
                    except Exception as e:
                        print(f"Exception : {e}")

                # Insights column (now at index 8 instead of 7)
                if j == 7:
                    val_str = str(value)
                    
                    # Sort priority weighting
                    prio = 0
                    if "CRITICAL" in val_str: prio = 4
                    elif "WARNING" in val_str: prio = 3
                    elif "SUGGESTION" in val_str: prio = 2
                    elif "INFO" in val_str: prio = 1
                    item.setData(Qt.UserRole, prio)
                    
                    if "CRITICAL" in val_str:
                        item.setBackground(QColor("#f38ba8"))
                        item.setForeground(QColor("#11111b"))
                    elif "WARNING" in val_str:
                        item.setBackground(QColor("#f9e2af"))
                        item.setForeground(QColor("#11111b"))
                    elif "INFO" in val_str:
                        item.setForeground(QColor("#89b4fa"))
                    elif "SUGGESTION" in val_str:
                        item.setForeground(QColor("#a6e3a1"))

                self.table.setItem(i, col_index, item)

    def on_item_double_clicked(self, item):
        row = item.row()
        path_item = self.table.item(row, 1)  # Path is now at column 1
        if path_item:
            file_path = path_item.text()
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item is not None:
            row = item.row()
            col = item.column()
            
            # If star column clicked, toggle favorite
            if col == 0:
                self.toggle_favorite(row)
                return
            
            menu = QMenu(self)
            open_action = menu.addAction("Open File")
            open_dir_action = menu.addAction("Open Folder Location")
            copy_path_action = menu.addAction("Copy Path")
            toggle_fav_action = menu.addAction("Toggle Favorite")
            
            action = menu.exec_(self.table.viewport().mapToGlobal(pos))
            
            if action:
                path_item = self.table.item(row, 1)  # Path is at column 1
                if path_item:
                    file_path = path_item.text()
                    if action == open_action:
                        if os.path.exists(file_path):
                            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                    elif action == open_dir_action:
                        dir_path = os.path.dirname(file_path)
                        if os.path.exists(dir_path):
                            QDesktopServices.openUrl(QUrl.fromLocalFile(dir_path))
                    elif action == copy_path_action:
                        clipboard = QApplication.clipboard()
                        clipboard.setText(file_path)
                    elif action == toggle_fav_action:
                        self.toggle_favorite(row)

    def show_asset_view(self):
        self.table.setVisible(True)
        self.tree.setVisible(False)

    def show_folder_view(self):
        self.table.setVisible(False)
        self.tree.setVisible(True)

    def populate_tree(self, rows):
        self.tree.clear()

        root = {}

        for row in rows:
            path = row[0]
            vram = float(row[6]) if row[6] else 0

            parts = path.split(os.sep)
            current = root

            for part in parts:
                if part not in current:
                    current[part] = {"__vram__": 0, "__children__": {}}
                current[part]["__vram__"] += vram
                current = current[part]["__children__"]

        for key in root:
            item = self._build_tree_item(key, root[key])
            self.tree.addTopLevelItem(item)

    def _build_tree_item(self, name, data):
        vram = data["__vram__"]
        item = QTreeWidgetItem([name, f"{vram:.2f}"])

        if vram > 1000:
            item.setBackground(1, QColor("#f38ba8"))
            item.setForeground(1, QColor("#11111b"))
        elif vram > 500:
            item.setBackground(1, QColor("#f9e2af"))
            item.setForeground(1, QColor("#11111b"))

        for child_name, child_data in data["__children__"].items():
            child_item = self._build_tree_item(child_name, child_data)
            item.addChild(child_item)

        return item

    # ========================= Keyboard Shortcuts =========================
    def shortcut_copy_path(self):
        """Ctrl+C: Copy selected asset path to clipboard"""
        selected_indexes = self.table.selectedIndexes()
        if selected_indexes:
            row = selected_indexes[0].row()
            path_item = self.table.item(row, 1)  # Path is at column 1
            if path_item:
                clipboard = QApplication.clipboard()
                clipboard.setText(path_item.text())

    def shortcut_export_selected(self):
        """Ctrl+E: Export selected assets to CSV"""
        selected_indexes = self.table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "No Selection", "Please select at least one asset to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Selected Assets", "", "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return

        selected_rows = set()
        for index in selected_indexes:
            selected_rows.add(index.row())

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write("Path,Type,Size (Bytes),Width,Height,Channels,VRAM (MB),Insights,Favorite\n")
                
                # Write selected rows
                for row in sorted(selected_rows):
                    if row < self.table.rowCount():
                        row_data = []
                        for col in range(1, self.table.columnCount()):  # Skip star column (0)
                            item = self.table.item(row, col)
                            if item:
                                # Escape quotes and wrap in quotes if contains comma
                                value = item.text().replace('"', '""')
                                if ',' in value:
                                    value = f'"{value}"'
                                row_data.append(value)
                        # Add favorite status
                        star_item = self.table.item(row, 0)
                        is_favorite = "Yes" if star_item and star_item.text() == "★" else "No"
                        row_data.append(is_favorite)
                        f.write(','.join(row_data) + '\n')
            
            QMessageBox.information(self, "Export Successful", f"Exported {len(selected_rows)} assets to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def toggle_favorite(self, row):
        """Toggle favorite status for the asset in the given row"""
        from db import toggle_favorite
        path_item = self.table.item(row, 1)  # Path is at column 1
        if path_item:
            file_path = path_item.text()
            new_fav_status = toggle_favorite(file_path)
            star_item = self.table.item(row, 0)
            if star_item:
                star_item.setText("★" if new_fav_status else "☆")

    def on_selection_changed(self):
        """Handle selection changes - show/hide bulk actions toolbar"""
        selected_indexes = self.table.selectedIndexes()
        has_selection = len(selected_indexes) > 0
        self.bulk_actions_widget.setVisible(has_selection)

    def bulk_mark_favorite(self):
        """Mark all selected assets as favorite"""
        from db import set_favorite
        selected_rows = set()
        for index in self.table.selectedIndexes():
            selected_rows.add(index.row())
        
        for row in selected_rows:
            path_item = self.table.item(row, 1)
            if path_item:
                file_path = path_item.text()
                set_favorite(file_path, True)
                star_item = self.table.item(row, 0)
                if star_item:
                    star_item.setText("★")

    def bulk_unmark_favorite(self):
        """Unmark all selected assets as favorite"""
        from db import set_favorite
        selected_rows = set()
        for index in self.table.selectedIndexes():
            selected_rows.add(index.row())
        
        for row in selected_rows:
            path_item = self.table.item(row, 1)
            if path_item:
                file_path = path_item.text()
                set_favorite(file_path, False)
                star_item = self.table.item(row, 0)
                if star_item:
                    star_item.setText("☆")
