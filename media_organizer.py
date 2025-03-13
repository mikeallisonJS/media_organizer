#!/usr/bin/env python3
"""
Media Organizer module - Core functionality for organizing media files.
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
logger = logging.getLogger("MediaOrganizer")

class MediaOrganizer:
    """Class to organize media files based on metadata."""
    
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
        Get the template for the specified media type.

        Args:
            media_type: The media type ('audio', 'video', 'image')

        Returns:
            The template string for the specified media type
        """
        return self.templates.get(media_type, self.template)
    
    def find_media_files(self, supported_extensions=None):
        """
        Find all supported media files in the source directory.
        
        Args:
            supported_extensions: Dictionary of supported file extensions by media type.
                                 If None, uses defaults.
        
        Returns:
            List of Path objects for media files
        """
        if not self.source_dir or not self.source_dir.exists():
            raise ValueError("Source directory does not exist")
        
        if supported_extensions is None:
            supported_extensions = defaults.get_default_extensions()
            
        all_extensions = []
        for extensions_list in supported_extensions.values():
            all_extensions.extend(extensions_list)
        
        media_files = []
        
        # Check if destination is inside source to avoid processing files in the destination
        is_dest_in_source = False
        if self.output_dir and self.source_dir:
            try:
                # Convert to absolute paths for comparison
                abs_source = self.source_dir.resolve()
                abs_output = self.output_dir.resolve()
                # Check if output is a subdirectory of source
                is_dest_in_source = str(abs_output).startswith(str(abs_source))
                if is_dest_in_source:
                    logger.info(f"Destination directory is inside source directory. Will skip files in destination.")
            except Exception as e:
                logger.error(f"Error checking directory relationship: {e}")
        
        # Count total files first
        self.total_files = 0
        for file_path in self.source_dir.rglob("*"):
            if self.stop_requested:
                break
                
            # Skip files in the destination directory if it's inside the source
            if is_dest_in_source and self.output_dir and file_path.is_file():
                try:
                    rel_path = file_path.relative_to(self.source_dir)
                    dest_path = self.output_dir / rel_path
                    if file_path.is_relative_to(self.output_dir) or file_path == dest_path:
                        continue
                except (ValueError, RuntimeError):
                    pass  # Not relative, so continue processing
                    
            if file_path.is_file() and file_path.suffix.lower() in all_extensions:
                self.total_files += 1
        
        # Then collect the files
        for file_path in self.source_dir.rglob("*"):
            if self.stop_requested:
                break

            # Skip files in the destination directory if it's inside the source
            if is_dest_in_source and self.output_dir and file_path.is_file():
                try:
                    rel_path = file_path.relative_to(self.source_dir)
                    dest_path = self.output_dir / rel_path
                    if file_path.is_relative_to(self.output_dir) or file_path == dest_path:
                        continue
                except (ValueError, RuntimeError):
                    pass  # Not relative, so continue processing
                
            if file_path.is_file() and file_path.suffix.lower() in all_extensions:
                self.current_file = str(file_path)
                media_files.append(file_path)
                
        return media_files
    
    def set_operation_mode(self, mode):
        """Set the operation mode (copy or move)."""
        if mode not in ["copy", "move"]:
            raise ValueError("Operation mode must be 'copy' or 'move'")
        self.operation_mode = mode
    
    def organize_files(self, supported_extensions=None, callback=None):
        """
        Organize media files based on their metadata and the template.
        
        Args:
            supported_extensions: Dictionary of supported file extensions by media type.
                                 If None, uses defaults.
            callback: Optional callback function to report progress
        """
        if not self.source_dir or not self.output_dir:
            raise ValueError("Source and output directories must be set")
        
        if supported_extensions is None:
            supported_extensions = defaults.get_default_extensions()
            
        self.is_running = True
        self.stop_requested = False
        self.files_processed = 0
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Find all media files
            media_files = self.find_media_files(supported_extensions)
            
            for file_path in media_files:
                if self.stop_requested:
                    logger.info("Organization stopped by user")
                    break
                
                try:
                    # Update current file being processed
                    self.current_file = str(file_path)
                    
                    # Extract metadata
                    media_file = MediaFile(file_path, supported_extensions)

                    # Get the appropriate template for this file type
                    template = self.get_template(media_file.file_type)
                    
                    # Generate destination path
                    rel_path = media_file.get_formatted_path(template)
                    dest_path = self.output_dir / rel_path
                    
                    # Create destination directory if it doesn't exist
                    os.makedirs(dest_path.parent, exist_ok=True)
                    
                    # Copy or move the file based on operation mode
                    if self.operation_mode == "copy":
                        shutil.copy2(file_path, dest_path)
                        logger.info(f"Copied {file_path} to {dest_path}")
                    else:  # move mode
                        shutil.move(file_path, dest_path)
                        logger.info(f"Moved {file_path} to {dest_path}")
                    
                    # Update progress
                    self.files_processed += 1
                    if callback:
                        callback(self.files_processed, self.total_files, str(file_path))
                        
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
            
            operation_name = "copy" if self.operation_mode == "copy" else "move"
            logger.info(f"{operation_name.capitalize()} operation complete. Processed {self.files_processed} files.")
            
        except Exception as e:
            logger.error(f"Error during organization: {e}")
        
        finally:
            self.is_running = False
            if callback:
                callback(self.files_processed, self.total_files, "Complete")
    
    def stop(self):
        """Stop the organization process."""
        self.stop_requested = True 