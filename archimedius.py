#!/usr/bin/env python3
"""
Archimedius - Core module for organizing media files.
This module contains the main logic for finding and organizing media files.
"""

import os
import shutil
import logging
import threading
from pathlib import Path
from datetime import datetime
import json

# Import the MediaFile class
from media_file import MediaFile
# Import the defaults module
import defaults
# Import the extensions module
import extensions

# Configure logging
logger = logging.getLogger("Archimedius")

class Archimedius:
    """Class for organizing media files based on metadata."""
    
    def __init__(self):
        self.source_dir = None
        self.output_dir = None
        # Default templates for each media type from defaults module
        self.templates = defaults.DEFAULT_TEMPLATES.copy()
        # For backward compatibility
        self.template = defaults.DEFAULT_TEMPLATES["audio"]
        self.files_processed = 0
        self.total_files = 0
        self.current_file = ""
        self.is_running = False
        self.stop_requested = False
        self.operation_mode = "copy"  # Default to copy mode
    
    def set_source_dir(self, directory):
        """Set the source directory."""
        self.source_dir = Path(directory)
    
    def set_output_dir(self, directory):
        """Set the output directory."""
        self.output_dir = Path(directory)
    
    def set_template(self, template, media_type=None):
        """
        Set the organization template.

        Args:
            template: The template string
            media_type: Optional media type ('audio', 'video', 'image').
                       If None, sets the default template for backward compatibility.
        """
        if media_type and media_type in self.templates:
            self.templates[media_type] = template
            # Also update the default template if it's audio (for backward compatibility)
            if media_type == "audio":
                self.template = template
        else:
            # For backward compatibility
            self.template = template
            # Also update the audio template
            self.templates["audio"] = template

    def get_template(self, media_type):
        """
        Get the template for a specific media type.
        
        Args:
            media_type: The media type (audio, video, image, ebook)
            
        Returns:
            The template string for the specified media type
        """
        return self.templates.get(media_type, self.templates["audio"])
    
    def set_operation_mode(self, mode):
        """
        Set the operation mode (copy or move).
        
        Args:
            mode: Operation mode ("copy" or "move")
        """
        if mode not in ["copy", "move"]:
            raise ValueError("Operation mode must be 'copy' or 'move'")
        self.operation_mode = mode
    
    def stop(self):
        """Stop the organization process."""
        self.stop_requested = True 