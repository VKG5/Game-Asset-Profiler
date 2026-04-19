# Insight Engine: derives warnings/hints from asset metrics
import os
import re
from collections import defaultdict


def _is_power_of_two(v: int) -> bool:
    return (v & (v - 1) == 0) and v != 0


def detect_numbered_sequences(all_paths):
    """
    Detect numbered image sequences (e.g., texture_001.png, texture_002.png)
    Returns a set of base names that have sequences
    
    Args:
        all_paths: List of all file paths in project
    
    Returns:
        Dictionary: {base_name: [list of sequence numbers]}
    """
    sequence_pattern = re.compile(r'^(.+?)[-_]?(\d{2,})(\.[a-zA-Z0-9]+)$')
    sequences = defaultdict(list)
    
    for path in all_paths:
        filename = os.path.basename(path)
        match = sequence_pattern.match(filename)
        if match:
            base_name = match.group(1)
            seq_num = int(match.group(2))
            sequences[base_name].append((seq_num, path))
    
    # Only return sequences with 3+ consecutive numbers
    valid_sequences = {}
    for base_name, items in sequences.items():
        if len(items) >= 3:
            items.sort(key=lambda x: x[0])
            valid_sequences[base_name] = items
    
    return valid_sequences


def analyze_asset(row):
    """
    row schema:
    (path, type, size_bytes, width, height, channels, vram_mb)
    returns list[str] insights
    """
    path, a_type, size_bytes, w, h, ch, vram = row

    insights = []

    if a_type != "image":
        return insights

    # ---- Size / VRAM thresholds ----
    try:
        vram = float(vram)
    except Exception:
        vram = 0.0

    if vram >= 100:
        insights.append("CRITICAL: >100MB VRAM texture")
    elif vram >= 50:
        insights.append("WARNING: >50MB VRAM texture")

    # ---- Resolution checks ----
    if w >= 4096 or h >= 4096:
        insights.append("CRITICAL: 4K+ texture")
    elif w >= 2048 or h >= 2048:
        insights.append("INFO: 2K texture")

    # ---- Power of two ----
    if w and h and (not _is_power_of_two(w) or not _is_power_of_two(h)):
        insights.append("WARNING: Non power-of-two texture")

    # ---- Channels ----
    if ch == 4:
        # We can't reliably detect alpha usage here, but flag potential waste
        insights.append("INFO: RGBA texture (check alpha usage)")
    elif ch == 1:
        insights.append("INFO: Grayscale texture")

    # ---- File type heuristic ----
    ext = os.path.splitext(path)[1].lower()
    if ext in (".png", ".tga") and vram >= 50:
        insights.append("SUGGESTION: Consider GPU compression (DXT/BC)")

    # ---- Suspicious ratio ----
    if w and h and ch:
        pixel_count = w * h
        if pixel_count > 0:
            density = size_bytes / pixel_count
            # Very rough heuristic
            if density < 0.5:
                insights.append("INFO: Highly compressed on disk")

    return insights


def analyze_asset_with_sequences(row, all_paths=None):
    """
    Enhanced analyze_asset that also checks for numbered sequences.
    
    Args:
        row: Standard asset row (path, type, size_bytes, width, height, channels, vram_mb)
        all_paths: Optional list of all file paths for sequence detection
    
    Returns:
        List of insight strings
    """
    insights = analyze_asset(row)
    
    # Check for texture atlas packing opportunities
    if all_paths and row[1] == "image":
        path = row[0]
        filename = os.path.basename(path)
        
        # Check if this file is part of a sequence
        sequence_pattern = re.compile(r'^(.+?)[-_]?(\d{2,})(\.[a-zA-Z0-9]+)$')
        match = sequence_pattern.match(filename)
        
        if match:
            base_name = match.group(1)
            seq_num = int(match.group(2))
            
            # Count similar files (same base name, different sequence numbers)
            similar_count = sum(
                1 for p in all_paths
                if re.match(
                    r'^' + re.escape(base_name) + r'[-_]?\d{2,}' + re.escape(match.group(3)) + r'$',
                    os.path.basename(p),
                    re.IGNORECASE
                )
            )
            
            if similar_count >= 3:
                insights.append(
                    f"SUGGESTION: Multiple numbered sequences detected ({base_name} x{similar_count}) - "
                    f"consider texture atlas packing with TexturePacker or similar tools"
                )
    
    return insights