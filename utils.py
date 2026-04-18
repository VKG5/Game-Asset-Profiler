import os

def format_size(bytes_size):
    for unit in ['B','KB','MB','GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024