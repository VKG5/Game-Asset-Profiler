from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
import os

class FolderViewTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Folder/File", "Size"])

        layout.addWidget(self.tree)
        self.setLayout(layout)

    def load_folder(self, path):
        self.tree.clear()
        root_item = QTreeWidgetItem([path, ""])
        self.tree.addTopLevelItem(root_item)
        self.add_children(root_item, path)

    def add_children(self, parent, path):
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            size = os.path.getsize(full_path) if os.path.isfile(full_path) else 0

            item = QTreeWidgetItem([name, str(size)])
            parent.addChild(item)

            if os.path.isdir(full_path):
                self.add_children(item, full_path)