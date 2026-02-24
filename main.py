#!/usr/bin/env python3
"""
Archimedius - A tool to organize media files based on metadata.
"""

import logging
from pathlib import Path
import json
from ttkbootstrap import Window

# Import application modules
import defaults
from archimedius_gui import ArchimediusGUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("archimedius.log")],
)
logger = logging.getLogger("Archimedius")

# Set PyPDF logger to ERROR level to suppress warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)

def main():
    """Main entry point for the application."""
    # Try to load logging level from settings file
    config_file = Path.home() / defaults.DEFAULT_PATHS["settings_file"]
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                settings = json.load(f)
                logging_level = settings.get("logging_level", defaults.DEFAULT_SETTINGS["logging_level"])
                numeric_level = defaults.LOGGING_LEVELS.get(logging_level, logging.INFO)
                logger.setLevel(numeric_level)
                # Also update the root logger for the file handler
                for handler in logging.root.handlers:
                    if isinstance(handler, logging.FileHandler):
                        handler.setLevel(numeric_level)
                
                # Keep PyPDF logger at ERROR level regardless of user settings
                logging.getLogger("pypdf").setLevel(logging.ERROR)
        except Exception as e:
            logger.error(f"Error loading logging level from settings: {e}")
    
    root = Window(themename="flatly")
    app = ArchimediusGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 
