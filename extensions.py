"""
Extensions module for Media Organizer.

This module defines the default supported file extensions for different media types.
"""

# Default supported file extensions
DEFAULT_EXTENSIONS = {
    "audio": [".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav"],
    "video": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
    "ebook": [".epub", ".pdf", ".mobi", ".azw", ".azw3", ".fb2"],
}

def get_all_extensions():
    """Get a flat list of all supported extensions."""
    all_extensions = []
    for extensions in DEFAULT_EXTENSIONS.values():
        all_extensions.extend(extensions)
    return all_extensions

def get_extensions_by_type(media_type):
    """Get extensions for a specific media type."""
    return DEFAULT_EXTENSIONS.get(media_type, [])

def is_supported_extension(extension):
    """Check if an extension is supported."""
    return extension.lower() in get_all_extensions()

def get_media_type(extension):
    """Get the media type for an extension."""
    extension = extension.lower()
    for media_type, extensions in DEFAULT_EXTENSIONS.items():
        if extension in extensions:
            return media_type
    return None 