"""
Defaults module for Archimedius.

This module defines all default values used throughout the application.
Centralizing these values makes the application more maintainable and configurable.
"""

# Import the extensions module to access DEFAULT_EXTENSIONS
import extensions
import logging

# Application information
APP_NAME = "Archimedius"
APP_VERSION = "0.1.1"
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

# Default setting for excluding "Unknown" folders from paths
EXCLUDE_UNKNOWN_DEFAULT = True

# Default exclude unknown settings for each media type
DEFAULT_EXCLUDE_UNKNOWN = {
    "audio": EXCLUDE_UNKNOWN_DEFAULT,
    "video": EXCLUDE_UNKNOWN_DEFAULT,
    "image": EXCLUDE_UNKNOWN_DEFAULT,
    "ebook": EXCLUDE_UNKNOWN_DEFAULT,
}

# Default settings
DEFAULT_SETTINGS = {
    "show_full_paths": False,
    "auto_save_enabled": True,
    "auto_preview_enabled": True,
    "logging_level": "INFO",
    "exclude_unknown": DEFAULT_EXCLUDE_UNKNOWN,
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
    "help_window": "600x500",
    "log_window": "600x400",
    "about_dialog": "500x450",
}

# Default file paths
DEFAULT_PATHS = {
    "settings_file": "archimedius_settings.json",
    "log_file": "archimedius.log",
    "license_file": "archimedius_license.json",
    "trial_file": "archimedius_trial.json",
}

# Function to get all default extensions
def get_default_extensions():
    """Get a copy of the default extensions dictionary."""
    return extensions.DEFAULT_EXTENSIONS.copy() 