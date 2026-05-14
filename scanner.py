# Threaded scanner with batching + Insight Engine integration

import os
import re
from PyQt5.QtCore import QThread, pyqtSignal

from db import get_connection, upsert_asset_with_insights, set_project_root
from metrics import analyze_image
from insights import analyze_asset_with_sequences

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tga", ".bmp", ".dds")
AUDIO_EXTENSIONS = (".wav", ".ogg", ".mp3")
VIDEO_EXTENSIONS = (".mp4", ".webm", ".ks9")


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
        # Store the project root globally in the database so other tabs can reference it dynamically
        set_project_root(self.root_path)
        
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

    def _parse_import_file(self, filepath, a_type):
        """Reads the .import file associated with the asset and extracts the compression mode."""
        import_path = filepath + ".import"
        
        # Defaults if no import file is found
        if not os.path.exists(import_path):
            if a_type == "image": return "Lossless"
            if a_type == "audio": return "Disabled"
            return "N/A"
            
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if a_type == "image":
                mode_match = re.search(r'compress/mode=(\d+)', content)
                quality_match = re.search(r'compress/lossy_quality=([\d.]+)', content)
                vram_match = re.search(r'"vram_texture":\s*true', content, re.IGNORECASE)
                
                mode = int(mode_match.group(1)) if mode_match else 0
                quality = quality_match.group(1) if quality_match else "0.7"
                
                if vram_match or mode == 2:
                    return f"VRAM Compression (Quality: {quality})"
                elif mode == 0:
                    return "Lossless"
                elif mode == 1:
                    return f"Lossy (Quality: {quality})"
                elif mode == 3:
                    return "Uncompressed"
                return "Lossless"
                
            elif a_type == "audio":
                mode_match = re.search(r'compress/mode=(\d+)', content)
                mode = int(mode_match.group(1)) if mode_match else 0
                
                if mode == 0:
                    return "Disabled"
                elif mode == 1:
                    return "RAM (Ima-ADPCM)"
                return "Disabled"
                
        except Exception as e:
            print(f"Error parsing import file for {filepath}: {e}")
            
        # Fallbacks on exception
        if a_type == "image": return "Lossless"
        if a_type == "audio": return "Disabled"
        return "N/A"

    def _process_file(self, path):
        ext = os.path.splitext(path)[1].lower()

        try:
            size_bytes = os.path.getsize(path)
        except Exception:
            size_bytes = 0

        # Categorize file types
        a_type = "other"
        if ext in IMAGE_EXTENSIONS:
            a_type = "image"
        elif ext in AUDIO_EXTENSIONS:
            a_type = "audio"
        elif ext in VIDEO_EXTENSIONS:
            a_type = "video"
        elif ext == ".tscn":
            a_type = "tscn"
        elif ext == ".tres":
            a_type = "tres"
        elif ext == ".gd":
            a_type = "gd"
        elif ext in (".shader", ".gdshader"):
            a_type = "shader"

        # Extract the compression metadata from Godot's .import file
        compression = self._parse_import_file(path, a_type)

        if a_type == "image":
            result = analyze_image(path)
            if result:
                return (
                    path,
                    a_type,
                    size_bytes,
                    result["width"],
                    result["height"],
                    result["channels"],
                    result["vram_mb"],
                    compression 
                )
        else:
            return (path, a_type, size_bytes, 0, 0, 0, 0, compression) 

        return None