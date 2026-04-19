import os
import re
from PIL import Image


def format_size(bytes_size):
    for unit in ['B','KB','MB','GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024


def generate_thumbnail(image_path, size=(80, 80)):
    """
    Generate a thumbnail for an image file.
    
    Args:
        image_path: Path to the image file
        size: Tuple of (width, height) for thumbnail size
    
    Returns:
        PIL Image object or None if failed
    """
    try:
        img = Image.open(image_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        # Create new image with padding to maintain aspect ratio
        thumbnail = Image.new('RGBA', size, (30, 30, 46, 255))  # Catppuccin bg color
        offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
        thumbnail.paste(img, offset, img if img.mode == 'RGBA' else None)
        return thumbnail
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return None


def apply_regex_search(pattern, text):
    """
    Apply regex search with fallback to literal matching on error.
    
    Args:
        pattern: Regex pattern string
        text: Text to search in
    
    Returns:
        True if match found, False otherwise
    """
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        # Fallback to literal matching
        return pattern.lower() in text.lower()