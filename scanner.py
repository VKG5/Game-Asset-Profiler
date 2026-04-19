# Threaded scanner with batching + Insight Engine integration

import os
from PyQt5.QtCore import QThread, pyqtSignal

from db import get_connection, upsert_asset_with_insights
from metrics import analyze_image
from insights import analyze_asset_with_sequences

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tga", ".bmp", ".dds")


class ScanWorker(QThread):
    progress_updated = pyqtSignal(int)
    file_processed = pyqtSignal(str)
    scan_complete = pyqtSignal()

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        all_files = self._collect_files(self.root_path)
        total_files = len(all_files)

        if total_files == 0:
            self.scan_complete.emit()
            return

        with get_connection() as conn:
            for index, path in enumerate(all_files):
                if not self._is_running:
                    break

                try:
                    row = self._process_file(path)
                    if row:
                        # Use sequence-aware insight analysis
                        insights = analyze_asset_with_sequences(row, all_files)
                        insights_str = " | ".join(insights)

                        upsert_asset_with_insights(conn, row + (insights_str,))
                except Exception as e:
                    print(f"Error processing {path}: {e}")
                    continue

                progress = int((index + 1) / total_files * 100)
                self.progress_updated.emit(progress)
                self.file_processed.emit(path)

            conn.commit()

        self.scan_complete.emit()

    def _collect_files(self, root_path):
        file_list = []
        for root, _, files in os.walk(root_path):
            for f in files:
                file_list.append(os.path.join(root, f))
        return file_list

    def _process_file(self, path):
        ext = os.path.splitext(path)[1].lower()

        try:
            size_bytes = os.path.getsize(path)
        except Exception:
            size_bytes = 0

        if ext in IMAGE_EXTENSIONS:
            result = analyze_image(path)

            if result:
                return (
                    path,
                    "image",
                    size_bytes,
                    result["width"],
                    result["height"],
                    result["channels"],
                    result["vram_mb"]
                )
        else:
            return (path, "other", size_bytes, 0, 0, 0, 0)

        return None
