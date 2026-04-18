# Insight Engine: derives warnings/hints from asset metrics
import os


def _is_power_of_two(v: int) -> bool:
    return (v & (v - 1) == 0) and v != 0


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