# Accurate-ish VRAM estimation logic for images

from PIL import Image
import math
import os

# Bytes per channel (usually 1 byte = 8 bits)
BYTES_PER_CHANNEL = 1

# Common GPU block compression formats (future extension)
COMPRESSION_FACTORS = {
    "DXT1": 0.5,   # ~4 bits per pixel
    "DXT5": 1.0,   # ~8 bits per pixel
    "BC7": 1.0,    # ~8 bits per pixel (uncompressed equivalent for profiling)
}

# Mapping PIL modes to bytes per pixel
MODE_TO_BPP = {
    "1": 1/8,
    "L": 1,
    "P": 1,
    "RGB": 3,
    "RGBA": 4,
    "CMYK": 4,
    "YCbCr": 3,
    "I": 4,
    "F": 4,
    "I;16": 2,
    "I;16L": 2,
    "I;16B": 2,
}


def get_image_info(path, load_pixels=True):
    """
    Extracts width, height, and channels safely, optionally loading pixels for true size
    """
    try:
        with Image.open(path) as img:
            width, height = img.size
            channels = len(img.getbands())
            mode = img.mode
            
            # True memory size calculation
            if load_pixels:
                # Triggers pixel loading if not already loaded
                img.load()
                # Use tobytes() length for authoritative uncompressed size
                # This accounts for bit-depth and padding better than manual calculations
                try:
                    true_bytes = len(img.tobytes())
                except Exception:
                    # Fallback for complex/partially supported modes
                    bpp = MODE_TO_BPP.get(mode, channels)
                    true_bytes = width * height * bpp
            else:
                bpp = MODE_TO_BPP.get(mode, channels)
                true_bytes = width * height * bpp

            return {
                "width": width,
                "height": height,
                "channels": channels,
                "mode": mode,
                "true_bytes": true_bytes
            }
    except Exception as e:
        print(f"Error reading image {path}: {e}")
        return None


def is_power_of_two(value):
    return (value & (value - 1) == 0) and value != 0


def calculate_mipmap_levels(width, height):
    """
    Number of mip levels until 1x1
    """
    return int(math.floor(math.log2(max(width, height)))) + 1


def estimate_vram(width, height, channels, compression=None, base_bytes=None):
    """
    Estimate VRAM usage in MB (Aligned with IrfanView: uncompressed in-memory size)
    """
    # Use actual loaded bytes if available, otherwise fallback to estimate
    base_size = base_bytes if base_bytes is not None else (width * height * channels)

    # Apply compression if specified
    if compression in COMPRESSION_FACTORS:
        base_size *= COMPRESSION_FACTORS[compression]

    return base_size / (1024 * 1024)


def analyze_image(path, deep_scan=True):
    """
    Full image analysis pipeline
    """
    ext = os.path.splitext(path)[1].lower()

    # Special logic for DDS: VRAM size = Disk size
    if ext == ".dds":
        info = get_image_info(path, load_pixels=False) # Dim only
        if not info:
            return None
            
        try:
            vram_mb = os.path.getsize(path) / (1024 * 1024)
        except Exception:
            vram_mb = 0
            
        return {
            "width": info["width"],
            "height": info["height"],
            "channels": info["channels"],
            "vram_mb": round(vram_mb, 2),
            "is_pot": is_power_of_two(info["width"]) and is_power_of_two(info["height"]),
            "mip_levels": calculate_mipmap_levels(info["width"], info["height"])
        }

    # Standard formats
    info = get_image_info(path, load_pixels=deep_scan)
    if not info:
        return None

    width = info["width"]
    height = info["height"]
    channels = info["channels"]
    true_bytes = info.get("true_bytes")

    vram_mb = estimate_vram(width, height, channels, base_bytes=true_bytes)

    return {
        "width": width,
        "height": height,
        "channels": channels,
        "vram_mb": round(vram_mb, 2),
        "is_pot": is_power_of_two(width) and is_power_of_two(height),
        "mip_levels": calculate_mipmap_levels(width, height)
    }
