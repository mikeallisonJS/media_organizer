"""
Defaults module for Media Organizer.

This module defines all default values used throughout the application.
Centralizing these values makes the application more maintainable and configurable.
"""

# Import the extensions module to access DEFAULT_EXTENSIONS
import extensions
import logging

# Application information
APP_NAME = "Media Organizer"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Mike Allison"
APP_WEBSITE = "https://mikeallisonjs.com"
APP_EMAIL = "support@mikeallisonjs.com"

# Default templates for each media type
DEFAULT_TEMPLATES = {
    "audio": "{creation_year}/{genre}/{filename}",
    "video": "{creation_year}/{filename}",
    "image": "{creation_year}/{filename}",
    "ebook": "{author}/{title}/{filename}",
}

# Default settings
DEFAULT_SETTINGS = {
    "show_full_paths": False,
    "auto_save_enabled": True,
    "auto_preview_enabled": True,
    "logging_level": "INFO",
}

# Logging levels with user-friendly names
LOGGING_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Default window sizes
DEFAULT_WINDOW_SIZES = {
    "main_window": "800x800",
    "preferences_dialog": "600x500",
    "help_window": "600x400",
    "log_window": "600x400",
    "about_dialog": "500x450",
}

# Default operation mode
DEFAULT_OPERATION_MODE = "copy"  # Options: "copy", "move", "simulate"

# Default file paths
DEFAULT_PATHS = {
    "settings_file": "media_organizer_settings.json",
    "log_file": "media_organizer.log",
}

# Function to get default template for a specific media type
def get_default_template(media_type):
    """Get the default template for a specific media type."""
    return DEFAULT_TEMPLATES.get(media_type, DEFAULT_TEMPLATES["audio"])

# Function to get all default extensions
def get_default_extensions():
    """Get a copy of the default extensions dictionary."""
    return extensions.DEFAULT_EXTENSIONS.copy()

# Function to get default setting value
def get_default_setting(setting_name):
    """Get the default value for a specific setting."""
    return DEFAULT_SETTINGS.get(setting_name, None)

# Function to get default window size
def get_default_window_size(window_name):
    """Get the default size for a specific window."""
    return DEFAULT_WINDOW_SIZES.get(window_name, "600x400") 