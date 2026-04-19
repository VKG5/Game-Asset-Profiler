# Folder View Tab - Database-based hierarchical folder browser

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from db import fetch_all_assets


class FolderViewTab(QWidget):
    """Tab that shows assets organized by folder hierarchy loaded from database"""
    
    def __init__(self):
        super().__init__()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Folder/File", "VRAM (MB)", "Files"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 80)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Top controls
        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Folder View")
        refresh_btn.clicked.connect(self.load_from_database)
        controls_layout.addWidget(refresh_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def load_from_database(self):
        """Load all assets from database and organize by folder hierarchy"""
        self.tree.clear()
        
        try:
            # Fetch all assets from database
            assets = fetch_all_assets()
            
            if not assets:
                self.tree.clear()
                item = QTreeWidgetItem(["(No assets in database)", "", ""])
                self.tree.addTopLevelItem(item)
                return
            
            # Build folder hierarchy
            folder_tree = {}
            
            for asset in assets:
                path = asset[0]  # path is first column
                vram = float(asset[6]) if len(asset) > 6 and asset[6] else 0
                
                # Split path into folder parts
                parts = path.replace("\\\\", "/").split("/")
                
                # Navigate/create folder structure
                current = folder_tree
                for i, part in enumerate(parts[:-1]):  # All parts except filename
                    if part not in current:
                        current[part] = {"type": "folder", "vram": 0, "count": 0, "children": {}}
                    current[part]["vram"] += vram
                    current[part]["count"] += 1
                    current = current[part]["children"]
                
                # Add file as leaf node
                if parts:
                    filename = parts[-1]
                    current[filename] = {"type": "file", "vram": vram, "count": 1}
            
            # Build tree items
            for name, data in sorted(folder_tree.items()):
                item = self._build_tree_item(name, data)
                self.tree.addTopLevelItem(item)
        
        except Exception as e:
            print(f"Error loading folder view: {e}")
            self.tree.clear()
            error_item = QTreeWidgetItem([f"Error: {str(e)}", "", ""])
            self.tree.addTopLevelItem(error_item)

    def _build_tree_item(self, name, data):
        """Recursively build tree items from folder hierarchy"""
        is_folder = data.get("type") == "folder"
        vram = data.get("vram", 0)
        count = data.get("count", 0)
        
        # Format display text with icons
        if is_folder:
            display_name = f"📁 {name}"
        else:
            display_name = f"📄 {name}"
        
        item = QTreeWidgetItem([display_name, f"{vram:.2f}", str(count)])
        
        # Color code by VRAM (column 1)
        if vram > 1000:
            item.setBackground(1, QColor("#f38ba8"))
            item.setForeground(1, QColor("#11111b"))
        elif vram > 500:
            item.setBackground(1, QColor("#f9e2af"))
            item.setForeground(1, QColor("#11111b"))
        
        # Add children (subfolders and files)
        if is_folder:
            children = data.get("children", {})
            for child_name, child_data in sorted(children.items()):
                child_item = self._build_tree_item(child_name, child_data)
                item.addChild(child_item)
        
        return item
    
    def show(self):
        """Called when tab is shown - load data"""
        super().show()
        if self.tree.topLevelItemCount() == 0:
            self.load_from_database()