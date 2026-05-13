import os
import re
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QLabel,
    QFileDialog, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

from db import get_project_root


class DepScannerWorker(QThread):
    progress_updated = pyqtSignal(int)
    scan_complete = pyqtSignal(dict, str)

    def __init__(self, root_dir):
        super().__init__()
        self.root_dir = root_dir
        self._is_running = True
        self.graph = {}

    def stop(self):
        self._is_running = False

    def run(self):
        files_to_scan = []
        # Target Godot specific extensions
        valid_exts = ('.tscn', '.tres', '.gd', '.material', '.anim', '.shader', '.gdshader')
        
        for root, _, files in os.walk(self.root_dir):
            for f in files:
                if f.endswith(valid_exts):
                    files_to_scan.append(os.path.join(root, f))

        total_files = len(files_to_scan)
        if total_files == 0:
            self.scan_complete.emit({}, self.root_dir)
            return

        # Regex for Godot resources, and GDScript preloads
        pattern_ext = re.compile(r'path="res://([^"]+)"')
        pattern_gd = re.compile(r'preload\("res://([^"]+)"\)')

        for i, filepath in enumerate(files_to_scan):
            if not self._is_running:
                break

            # Convert to Godot res:// format
            rel_path = os.path.relpath(filepath, self.root_dir).replace("\\", "/")
            res_path = f"res://{rel_path}"

            if res_path not in self.graph:
                self.graph[res_path] = []

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = pattern_ext.findall(content) + pattern_gd.findall(content)
                    
                    for match in matches:
                        dep_res_path = f"res://{match}"
                        if dep_res_path not in self.graph[res_path]:
                            self.graph[res_path].append(dep_res_path)
                            
                        # Ensure the dependency also exists as a node in the graph
                        if dep_res_path not in self.graph:
                            self.graph[dep_res_path] = []
            except Exception:
                pass

            # Update progress
            progress = int((i + 1) / total_files * 100)
            self.progress_updated.emit(progress)

        self.scan_complete.emit(self.graph, self.root_dir)


class ReferencesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.project_root = ""
        self.graph = {}
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- Top Controls ---
        controls_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("Refresh References")
        self.btn_refresh.clicked.connect(self.load_from_db)
        
        self.btn_migrate = QPushButton("Migrate Selected File & Dependencies")
        self.btn_migrate.clicked.connect(self.migrate_selected)
        self.btn_migrate.setEnabled(False)
        self.btn_migrate.setStyleSheet("background-color: #313244;")

        self.status_label = QLabel("No project loaded.")
        self.status_label.setStyleSheet("color: #a6adc8;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        controls_layout.addWidget(self.btn_refresh)
        controls_layout.addWidget(self.btn_migrate)
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()

        # --- Main Splitter ---
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Folder View
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_label = QLabel("Project Files (Folder View)")
        left_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(["Folder / File"])
        self.folder_tree.itemSelectionChanged.connect(self.on_file_selected)
        
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.folder_tree)

        # Right side: Dependency Hierarchy
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_label = QLabel("Dependency Hierarchy")
        right_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree.setHeaderLabels(["Reference Tree"])
        
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.hierarchy_tree)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600]) # Default ratio

        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def load_from_db(self):
        """Dynamically load the references graph by pulling the root project directory from settings."""
        root_dir = get_project_root()
        if not root_dir or not os.path.exists(root_dir):
            self.status_label.setText("No project loaded. Please scan a project in the Overview tab.")
            return

        self.status_label.setText(f"Scanning: {root_dir}")
        self.progress_bar.setValue(0)
        self.btn_refresh.setEnabled(False)
        
        self.worker = DepScannerWorker(root_dir)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.scan_complete.connect(self.on_scan_complete)
        self.worker.start()

    def on_scan_complete(self, graph, root_dir):
        self.graph = graph
        self.project_root = root_dir
        self.status_label.setText(f"Scan complete. Found {len(self.graph)} unique references.")
        self.btn_refresh.setEnabled(True)
        self.build_folder_tree()

    def build_folder_tree(self):
        self.folder_tree.clear()
        folder_structure = {}

        # Build dict hierarchy
        for res_path in self.graph.keys():
            clean_path = res_path.replace("res://", "")
            parts = clean_path.split("/")

            current = folder_structure
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {"_type": "folder", "children": {}}
                current = current[part]["children"]

            if parts:
                filename = parts[-1]
                current[filename] = {"_type": "file", "res_path": res_path}

        # Recursively build QTreeWidgetItems
        for name, data in sorted(folder_structure.items()):
            item = self._build_tree_node(name, data)
            self.folder_tree.addTopLevelItem(item)

    def _build_tree_node(self, name, data):
        is_folder = data.get("_type") == "folder"
        display_text = f"📁 {name}" if is_folder else f"📄 {name}"
        item = QTreeWidgetItem([display_text])

        if not is_folder:
            item.setData(0, Qt.UserRole, data["res_path"])
        else:
            children = data.get("children", {})
            for child_name, child_data in sorted(children.items()):
                child_item = self._build_tree_node(child_name, child_data)
                item.addChild(child_item)
                
        return item

    def on_file_selected(self):
        selected_items = self.folder_tree.selectedItems()
        self.hierarchy_tree.clear()
        
        if not selected_items:
            self.btn_migrate.setEnabled(False)
            return

        item = selected_items[0]
        res_path = item.data(0, Qt.UserRole)
        
        # If it's a folder, res_path is None
        if not res_path:
            self.btn_migrate.setEnabled(False)
            return

        self.btn_migrate.setEnabled(True)
        self.btn_migrate.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold;")
        
        # Populate the right-side tree
        root_item = QTreeWidgetItem(self.hierarchy_tree, [f"🎯 {res_path}"])
        root_item.setExpanded(True)
        self._populate_hierarchy(res_path, root_item, set())

    def _populate_hierarchy(self, current_res, parent_item, visited):
        """Recursively visualizes dependencies, stopping at circular loops"""
        if current_res in visited:
            child = QTreeWidgetItem(parent_item, [f"🔄 [Circular/Already listed] {current_res}"])
            child.setForeground(0, QColor("#f38ba8")) # Red warning
            return

        visited.add(current_res)
        dependencies = self.graph.get(current_res, [])
        
        for dep in dependencies:
            child = QTreeWidgetItem(parent_item, [f"🔗 {dep}"])
            child.setExpanded(True)
            self._populate_hierarchy(dep, child, visited.copy())

    def get_all_descendants(self, root_res, visited=None):
        if visited is None:
            visited = set()
            
        if root_res in visited:
            return visited
            
        visited.add(root_res)
        for dep in self.graph.get(root_res, []):
            self.get_all_descendants(dep, visited)
            
        return visited

    def migrate_selected(self):
        selected_items = self.folder_tree.selectedItems()
        if not selected_items: 
            return
        
        res_path = selected_items[0].data(0, Qt.UserRole)
        if not res_path: 
            return

        target_dir = QFileDialog.getExistingDirectory(self, "Select Empty Target Folder for Migration")
        if not target_dir: 
            return

        # 1. Gather all files needed
        all_required_files = self.get_all_descendants(res_path)
        
        success_count = 0
        missing_count = 0
        
        # 2. Replicate directory structure and copy
        for required_res in all_required_files:
            rel_path = required_res.replace("res://", "")
            src_abs = os.path.join(self.project_root, rel_path)
            dst_abs = os.path.join(target_dir, rel_path)
            
            if os.path.exists(src_abs):
                os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
                shutil.copy2(src_abs, dst_abs)
                success_count += 1
            else:
                missing_count += 1

        msg = f"Migration complete!\nSuccessfully copied {success_count} files."
        if missing_count > 0:
            msg += f"\nWarning: {missing_count} linked files could not be found on disk."
            
        QMessageBox.information(self, "Migration Status", msg)