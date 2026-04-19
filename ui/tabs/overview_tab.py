# Polished Overview Tab with QThread integration, progress bar, and controls

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel,
    QProgressBar, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QMenu, QShortcut, QApplication, QMessageBox,
    QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QColor, QDesktopServices, QKeySequence, QClipboard
from scanner import ScanWorker
from db import fetch_flagged_assets, get_database_statistics
import os


class OverviewTab(QWidget):
    scan_completed_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.worker = None
        self.selected_folder = None
        self.all_logs = []  # Store fetched logs

        self._build_ui()
        self.load_logs()  # Load any existing logs on startup
        self.refresh_statistics()  # Load statistics on startup

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ===== Folder Selection =====
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-size: 14px;")
        self.folder_label.setWordWrap(True)

        self.browse_btn = QPushButton("Browse Project")
        self.browse_btn.setFixedHeight(36)
        self.browse_btn.setMinimumWidth(140)
        self.browse_btn.clicked.connect(self.select_folder)

        folder_layout.addWidget(self.folder_label)
        folder_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding))
        folder_layout.addWidget(self.browse_btn)

        # ===== Controls =====
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)

        self.start_btn = QPushButton("Start Scan")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setMinimumWidth(140)
        self.start_btn.clicked.connect(self.start_scan)

        self.stop_btn = QPushButton("Stop Scan")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setMinimumWidth(140)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding))

        # ===== Statistics Panel =====
        stats_group = QGroupBox("Database Statistics")
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        self.stats_total_assets = QLabel("Total Assets: 0")
        self.stats_total_assets.setStyleSheet("font-size: 12px;")
        
        self.stats_total_vram = QLabel("Total VRAM: 0 MB")
        self.stats_total_vram.setStyleSheet("font-size: 12px;")
        
        self.stats_avg_vram = QLabel("Average VRAM: 0 MB")
        self.stats_avg_vram.setStyleSheet("font-size: 12px;")
        
        self.stats_type_breakdown = QLabel("Assets: 0 images, 0 other")
        self.stats_type_breakdown.setStyleSheet("font-size: 12px;")
        
        stats_layout.addWidget(self.stats_total_assets, 0, 0)
        stats_layout.addWidget(self.stats_total_vram, 0, 1)
        stats_layout.addWidget(self.stats_avg_vram, 1, 0)
        stats_layout.addWidget(self.stats_type_breakdown, 1, 1)
        
        stats_group.setLayout(stats_layout)
        stats_group.setStyleSheet(
            "QGroupBox { border: 1px solid #45475a; border-radius: 5px; margin-top: 10px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }"
        )

        # ===== Progress =====
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("font-size: 12px; color: gray;")

        # ===== Logs Section =====
        logs_layout = QVBoxLayout()
        logs_layout.setSpacing(10)
        
        logs_header_layout = QHBoxLayout()
        logs_label = QLabel("Generated Insights & Logs")
        logs_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.log_filter = QComboBox()
        self.log_filter.addItems(["All", "CRITICAL", "WARNING", "INFO", "SUGGESTION"])
        self.log_filter.currentTextChanged.connect(self.filter_logs)
        
        self.export_btn = QPushButton("Export Logs")
        self.export_btn.clicked.connect(self.export_logs)
        
        self.log_count_label = QLabel("0 insights")
        self.log_count_label.setStyleSheet("font-size: 12px; color: #a6adc8;")
        
        logs_header_layout.addWidget(logs_label)
        logs_header_layout.addStretch()
        logs_header_layout.addWidget(self.log_count_label)
        logs_header_layout.addWidget(QLabel("Filter:"))
        logs_header_layout.addWidget(self.log_filter)
        logs_header_layout.addWidget(self.export_btn)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Path", "Severity", "Message"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.log_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.log_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.log_table.customContextMenuRequested.connect(self.show_context_menu)
        
        logs_layout.addLayout(logs_header_layout)
        logs_layout.addWidget(self.log_table)

        # ===== Assemble Layout =====
        main_layout.addLayout(folder_layout)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(stats_group)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(logs_layout) # Replaced stretch with logs
        
        self.setLayout(main_layout)

        # ========================= Keyboard Shortcuts =========================
        # Ctrl+N: Start new scan
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.start_scan)
        # Ctrl+E: Export logs
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.export_logs)
        # Ctrl+C: Copy selected log path
        QShortcut(QKeySequence.Copy, self).activated.connect(self.shortcut_copy_log_path)

    # ========================= Actions =========================

    def on_item_double_clicked(self, item):
        row = item.row()
        path_item = self.log_table.item(row, 0)
        if path_item:
            file_path = path_item.text()
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def show_context_menu(self, pos):
        item = self.log_table.itemAt(pos)
        if item is not None:
            menu = QMenu(self)
            open_action = menu.addAction("Open File")
            open_dir_action = menu.addAction("Open Folder Location")
            copy_path_action = menu.addAction("Copy Path")
            
            action = menu.exec_(self.log_table.viewport().mapToGlobal(pos))
            
            if action:
                row = item.row()
                path_item = self.log_table.item(row, 0)
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

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(folder)

    def start_scan(self):
        if not self.selected_folder:
            self.status_label.setText("Please select a folder first")
            return

        self.worker = ScanWorker(self.selected_folder)

        # Connect signals
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_processed.connect(self.update_status)
        self.worker.scan_complete.connect(self.scan_finished)

        # UI state
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Scanning started...")

        self.worker.start()

    def stop_scan(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("Stopping scan...")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, path):
        self.status_label.setText(f"Scanning: {path}")

    def scan_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Scan complete")
        self.progress_bar.setValue(100)

        # Updating UI upon signal emission
        tab_widget = self.parent()
        db_tab = tab_widget.widget(1)
        db_tab.load_data()
        
        self.load_logs()
        self.refresh_statistics()

        # Emit signal instead of hacking UI hierarchy
        self.scan_completed_signal.emit()

    def refresh_statistics(self):
        """Refresh the statistics panel with current database data"""
        try:
            stats = get_database_statistics()
            
            # Update labels
            self.stats_total_assets.setText(f"Total Assets: {stats['total_assets']}")
            self.stats_total_vram.setText(f"Total VRAM: {stats['total_vram_mb']:.2f} MB")
            self.stats_avg_vram.setText(f"Average VRAM: {stats['avg_vram_mb']:.2f} MB")
            
            # Format type breakdown
            type_parts = []
            for asset_type in sorted(stats['asset_type_counts'].keys()):
                count = stats['asset_type_counts'][asset_type]
                type_parts.append(f"{count} {asset_type}s")
            type_str = ", ".join(type_parts) if type_parts else "No assets"
            self.stats_type_breakdown.setText(f"Assets: {type_str}")
        except Exception as e:
            print(f"Error refreshing statistics: {e}")

    def load_logs(self):
        try:
            flagged = fetch_flagged_assets()
        except Exception:
            flagged = []
            
        self.all_logs = []
        for path, insights_str in flagged:
            for insight in insights_str.split(" | "):
                insight = insight.strip()
                if not insight:
                    continue
                
                parts = insight.split(":", 1)
                severity = parts[0].strip() if len(parts) > 1 else "UNKNOWN"
                message = parts[1].strip() if len(parts) > 1 else insight
                
                self.all_logs.append((path, severity, message))
                
        self.filter_logs()
        
    def filter_logs(self):
        selected_filter = self.log_filter.currentText()
        filtered_logs = []
        
        for path, severity, message in self.all_logs:
            if selected_filter == "All" or severity == selected_filter:
                filtered_logs.append((path, severity, message))
                
        self.log_table.setRowCount(len(filtered_logs))
        for i, (path, severity, message) in enumerate(filtered_logs):
            path_item = QTableWidgetItem(path)
            severity_item = QTableWidgetItem(severity)
            message_item = QTableWidgetItem(message)
            
            if severity == "CRITICAL":
                severity_item.setBackground(QColor("#f38ba8"))
                severity_item.setForeground(QColor("#11111b"))
            elif severity == "WARNING":
                severity_item.setBackground(QColor("#f9e2af"))
                severity_item.setForeground(QColor("#11111b"))
            elif severity == "INFO":
                severity_item.setForeground(QColor("#89b4fa"))
            elif severity == "SUGGESTION":
                severity_item.setForeground(QColor("#a6e3a1"))
                
            self.log_table.setItem(i, 0, path_item)
            self.log_table.setItem(i, 1, severity_item)
            self.log_table.setItem(i, 2, message_item)
        
        # Update insight count label
        count = len(filtered_logs)
        self.log_count_label.setText(f"{count} insight{'s' if count != 1 else ''}")
            
    def export_logs(self):
        if self.log_table.rowCount() == 0:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Logs", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
            
        from collections import defaultdict
        categorized_logs = defaultdict(list)
        
        for row in range(self.log_table.rowCount()):
            path = self.log_table.item(row, 0).text()
            severity = self.log_table.item(row, 1).text()
            msg = self.log_table.item(row, 2).text()
            categorized_logs[severity].append((path, msg))
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Game Asset Profiler - Insights Log\n")
                f.write("=" * 50 + "\n\n")
                
                # Sort order for output sections
                order = ["CRITICAL", "WARNING", "SUGGESTION", "INFO", "UNKNOWN"]
                all_severities = order + [s for s in categorized_logs.keys() if s not in order]
                
                for severity in all_severities:
                    if severity in categorized_logs:
                        f.write(f"### {severity} ###\n")
                        for path, msg in categorized_logs[severity]:
                            f.write(f"File: {path}\nMessage: {msg}\n")
                            f.write("-" * 30 + "\n")
                        f.write("\n")
        except Exception as e:
            print(f"Error exporting logs: {e}")

    def shortcut_copy_log_path(self):
        """Ctrl+C: Copy selected log path to clipboard"""
        selected_indexes = self.log_table.selectedIndexes()
        if selected_indexes:
            row = selected_indexes[0].row()
            path_item = self.log_table.item(row, 0)
            if path_item:
                clipboard = QApplication.clipboard()
                clipboard.setText(path_item.text())