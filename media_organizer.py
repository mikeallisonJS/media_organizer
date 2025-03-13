#!/usr/bin/env python3
"""
Media Organizer - A tool to organize media files based on metadata.
"""

import os
import shutil
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
import re
import json
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
from PIL import Image

# Import the extensions module
import extensions
# Import the defaults module
import defaults
# Import the LogWindow class
from log_window import LogWindow
# Import the PreferencesDialog class
from preferences_dialog import PreferencesDialog
# Import the MediaFile class
from media_file import MediaFile

try:
    from pymediainfo import MediaInfo

    MEDIAINFO_AVAILABLE = True
except (ImportError, OSError):
    MEDIAINFO_AVAILABLE = False
    logging.warning(
        "pymediainfo or MediaInfo not available. Video metadata extraction will be limited."
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("media_organizer.log")],
)
logger = logging.getLogger("MediaOrganizer")

# Initialize SUPPORTED_EXTENSIONS from the defaults module
SUPPORTED_EXTENSIONS = defaults.get_default_extensions()


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
    
    def find_media_files(self):
        """Find all supported media files in the source directory."""
        if not self.source_dir or not self.source_dir.exists():
            raise ValueError("Source directory does not exist")
        
        all_extensions = []
        for extensions_list in SUPPORTED_EXTENSIONS.values():
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
    
    def organize_files(self, callback=None):
        """
        Organize media files based on their metadata and the template.
        
        Args:
            callback: Optional callback function to report progress
        """
        if not self.source_dir or not self.output_dir:
            raise ValueError("Source and output directories must be set")
        
        self.is_running = True
        self.stop_requested = False
        self.files_processed = 0
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Find all media files
            media_files = self.find_media_files()
            
            for file_path in media_files:
                if self.stop_requested:
                    logger.info("Organization stopped by user")
                    break
                
                try:
                    # Update current file being processed
                    self.current_file = str(file_path)
                    
                    # Extract metadata
                    media_file = MediaFile(file_path, SUPPORTED_EXTENSIONS)

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

    def _organization_complete(self):
        """Handle organization completion."""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        operation_name = "copied" if self.operation_mode == "copy" else "moved"
        
        # Show completion message
        messagebox.showinfo(
            "Complete",
            f"Organization complete!\n\n{operation_name.capitalize()} {self.files_processed} files.",
        )

    def _on_close(self):
        """Handle window close event."""
        # Save settings before closing
        self._save_settings()
        # Close the window
        self.root.destroy()

    def _save_settings(self):
        """Save user settings to a configuration file."""
        try:
            # Collect settings
            settings = {
                "source_dir": self.source_entry.get().strip(),
                "output_dir": self.output_entry.get().strip(),
                "templates": {
                    "audio": self.template_vars["audio"].get().strip(),
                    "video": self.template_vars["video"].get().strip(),
                    "image": self.template_vars["image"].get().strip(),
                    "ebook": self.template_vars["ebook"].get().strip(),
                },
                # For backward compatibility
                "template": self.template_vars["audio"].get().strip(),
                "extensions": {
                    "audio": {ext: var.get() for ext, var in self.extension_vars["audio"].items()},
                    "video": {ext: var.get() for ext, var in self.extension_vars["video"].items()},
                    "image": {ext: var.get() for ext, var in self.extension_vars["image"].items()},
                    "ebook": {ext: var.get() for ext, var in self.extension_vars["ebook"].items()},
                },
                # Save custom extensions
                "custom_extensions": SUPPORTED_EXTENSIONS,
                "show_full_paths": getattr(self, "show_full_paths", False),
                "auto_save_enabled": getattr(self, "auto_save_enabled", True),
                "auto_preview_enabled": getattr(self, "auto_preview_enabled", True),
                "logging_level": getattr(self, "logging_level", defaults.DEFAULT_SETTINGS["logging_level"]),
                "operation_mode": getattr(self, "operation_mode", "copy"),
            }

            # Save to file
            with open(self.config_file, "w") as f:
                json.dump(settings, f)

            logger.info(f"Settings saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def _load_settings(self):
        """Load user settings from the configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    settings = json.load(f)

                # Apply settings
                if "source_dir" in settings and settings["source_dir"]:
                    self.source_entry.delete(0, tk.END)
                    self.source_entry.insert(0, settings["source_dir"])

                if "output_dir" in settings and settings["output_dir"]:
                    self.output_entry.delete(0, tk.END)
                    self.output_entry.insert(0, settings["output_dir"])

                # Load templates
                if "templates" in settings:
                    for media_type in ["audio", "video", "image", "ebook"]:
                        if (
                            media_type in settings["templates"]
                            and settings["templates"][media_type]
                        ):
                            self.template_vars[media_type].set(settings["templates"][media_type])
                # For backward compatibility
                elif "template" in settings and settings["template"]:
                    self.template_vars["audio"].set(settings["template"])
                    # Also update the default template variable for backward compatibility
                    self.template_var.set(settings["template"])

                # Load custom extensions if available
                if "custom_extensions" in settings:
                    global SUPPORTED_EXTENSIONS
                    # Start with default extensions
                    custom_extensions = extensions.DEFAULT_EXTENSIONS.copy()
                    # Update with custom extensions
                    for media_type, exts in settings["custom_extensions"].items():
                        if media_type in custom_extensions and exts:
                            custom_extensions[media_type] = exts
                    # Update global extensions
                    SUPPORTED_EXTENSIONS = custom_extensions

                # Apply extension selections
                if "extensions" in settings:
                    for file_type in ["audio", "video", "image", "ebook"]:
                        if file_type in settings["extensions"]:
                            for ext, value in settings["extensions"][file_type].items():
                                if ext in self.extension_vars[file_type]:
                                    self.extension_vars[file_type][ext].set(value)

                # Load full paths setting
                self.show_full_paths = settings.get("show_full_paths", False)

                # Load auto-save setting (defaults to True)
                self.auto_save_enabled = settings.get("auto_save_enabled", True)

                # Load auto-preview setting (defaults to True)
                self.auto_preview_enabled = settings.get("auto_preview_enabled", True)

                # Load logging level setting
                self.logging_level = settings.get("logging_level", defaults.DEFAULT_SETTINGS["logging_level"])

                # Update "All" checkboxes
                self._update_extension_selection()

                logger.info(f"Settings loaded from {self.config_file}")

                # Generate initial preview if auto-preview is enabled
                self._auto_generate_preview()

                # Load operation mode
                self.operation_mode = settings.get("operation_mode", "copy")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def _reset_settings(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno(
            "Reset Settings", "Are you sure you want to reset all settings to defaults?"
        ):
            try:
                # Clear entries
                self.source_entry.delete(0, tk.END)
                self.output_entry.delete(0, tk.END)

                # Reset templates to defaults
                for media_type in ["audio", "video", "image", "ebook"]:
                    self.template_vars[media_type].set(defaults.DEFAULT_TEMPLATES[media_type])

                # For backward compatibility
                self.template_var.set(defaults.DEFAULT_TEMPLATES["audio"])
                
                # Reset extension checkboxes to checked
                for file_type in ["audio", "video", "image", "ebook"]:
                    getattr(self, f"{file_type}_all_var").set(True)
                    self._toggle_all_extensions(file_type)
                
                # Reset settings to defaults
                self.show_full_paths = defaults.DEFAULT_SETTINGS["show_full_paths"]
                self.auto_save_enabled = defaults.DEFAULT_SETTINGS["auto_save_enabled"]
                self.auto_preview_enabled = defaults.DEFAULT_SETTINGS["auto_preview_enabled"]
                self.logging_level = defaults.DEFAULT_SETTINGS["logging_level"]
                
                # Clear preview
                self._clear_preview()
                
                # Delete config file if it exists
                if self.config_file.exists():
                    self.config_file.unlink()
                    logger.info(f"Settings file deleted: {self.config_file}")
                
                self.status_var.set("Settings reset to defaults")
                
            except Exception as e:
                logger.error(f"Error resetting settings: {e}")
                messagebox.showerror("Error", f"Failed to reset settings: {str(e)}")

    def _save_settings_manual(self):
        """Manually save settings and show confirmation."""
        self._save_settings()
        self.status_var.set(f"Settings saved to {self.config_file}")
        messagebox.showinfo(
            "Settings Saved", f"Your settings have been saved to:\n{self.config_file}"
        )

    def _on_template_change(self, *args, media_type=None):
        """
        Handle template change event.

        Args:
            *args: Variable arguments passed by tkinter trace
            media_type: The media type whose template changed ('audio', 'video', 'image', 'ebook')
        """
        # Auto-save settings after a short delay if enabled
        if getattr(self, "auto_save_enabled", True):
            if hasattr(self, "_template_timer"):
                self.root.after_cancel(self._template_timer)
            self._template_timer = self.root.after(1000, self._save_settings)

        # Auto-generate preview after a short delay
        if hasattr(self, "_preview_timer"):
            self.root.after_cancel(self._preview_timer)
        self._preview_timer = self.root.after(1500, self._auto_generate_preview)

    def _auto_generate_preview(self):
        """Automatically generate preview if enabled and source directory exists."""
        if self.auto_preview_enabled:
            source_dir = self.source_entry.get().strip()
            if source_dir and os.path.exists(source_dir):
                # Cancel any pending preview generation
                if hasattr(self, "_preview_timer"):
                    self.root.after_cancel(self._preview_timer)
                # Schedule preview generation after a short delay
                self._preview_timer = self.root.after(500, self._generate_preview)

    def _show_placeholders_help(self):
        """Show a modal dialog with information about available placeholders."""
        # Create a new top-level window
        help_window = tk.Toplevel(self.root)
        help_window.title("Available Placeholders")
        help_window.geometry(defaults.DEFAULT_WINDOW_SIZES["help_window"])
        help_window.minsize(600, 400)
        help_window.transient(self.root)  # Make it a modal dialog
        help_window.grab_set()  # Make it modal
        
        # Center the window
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create a frame for the content
        content_frame = ttk.Frame(help_window, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            content_frame, text="Available Placeholders", font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create a frame for each category
        categories_frame = ttk.Frame(content_frame)
        categories_frame.pack(fill=tk.BOTH, expand=True)
        
        # Common placeholders
        common_frame = ttk.LabelFrame(categories_frame, text="Common", padding=10)
        common_frame.pack(fill=tk.X, pady=5)
        
        common_placeholders = [
            ("{filename}", "Original filename without extension"),
            ("{extension}", "File extension (e.g., mp3, jpg)"),
            ("{file_type}", "Type of file (audio, video, image, ebook)"),
            ("{size}", "File size in bytes"),
            ("{creation_date}", "File creation date (YYYY-MM-DD)"),
            ("{creation_year}", "Year of file creation (YYYY)"),
            ("{creation_month}", "Month of file creation (01-12)"),
            ("{creation_month_name}", "Month name of file creation (January, February, etc.)"),
        ]
        
        for i, (placeholder, description) in enumerate(common_placeholders):
            ttk.Label(common_frame, text=placeholder, width=15, anchor=tk.W).grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(common_frame, text=description, anchor=tk.W).grid(
                row=i, column=1, sticky=tk.W, padx=5, pady=2
            )
        
        # Audio placeholders
        audio_frame = ttk.LabelFrame(categories_frame, text="Audio", padding=10)
        audio_frame.pack(fill=tk.X, pady=5)
        
        audio_placeholders = [
            ("{title}", "Song title"),
            ("{artist}", "Artist name"),
            ("{album}", "Album name"),
            ("{year}", "Release year"),
            ("{genre}", "Music genre"),
            ("{track}", "Track number"),
            ("{duration}", "Song duration"),
            ("{bitrate}", "Audio bitrate"),
        ]
        
        for i, (placeholder, description) in enumerate(audio_placeholders):
            ttk.Label(audio_frame, text=placeholder, width=15, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(audio_frame, text=description, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, padx=5, pady=2
            )
        
        # Image placeholders
        image_frame = ttk.LabelFrame(categories_frame, text="Image", padding=10)
        image_frame.pack(fill=tk.X, pady=5)
        
        image_placeholders = [
            ("{width}", "Image width in pixels"),
            ("{height}", "Image height in pixels"),
            ("{format}", "Image format (e.g., JPEG, PNG)"),
            ("{camera_make}", "Camera manufacturer"),
            ("{camera_model}", "Camera model"),
            ("{date_taken}", "Date when the photo was taken"),
        ]
        
        for i, (placeholder, description) in enumerate(image_placeholders):
            ttk.Label(image_frame, text=placeholder, width=15, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(image_frame, text=description, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, padx=5, pady=2
            )

        # eBook placeholders
        ebook_frame = ttk.LabelFrame(categories_frame, text="eBook", padding=10)
        ebook_frame.pack(fill=tk.X, pady=5)

        ebook_placeholders = [
            ("{title}", "Book title"),
            ("{author}", "Author name"),
            ("{year}", "Publication year"),
            ("{genre}", "Book genre"),
        ]

        for i, (placeholder, description) in enumerate(ebook_placeholders):
            ttk.Label(ebook_frame, text=placeholder, width=15, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(ebook_frame, text=description, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, padx=5, pady=2
            )
        
        # Example usage
        example_frame = ttk.LabelFrame(content_frame, text="Example Templates", padding=10)
        example_frame.pack(fill=tk.X, pady=5)
        
        examples = [
            (
                "{file_type}/{artist}/{album}/{filename}",
                "Organizes by file type, then artist, then album",
            ),
            (
                "Music/{year}/{artist} - {title}.{extension}",
                "Organizes music by year, then artist-title",
            ),
            (
                "{file_type}/{creation_year}/{creation_month_name}/{filename}",
                "Organizes by file type, year, and month",
            ),
            (
                "Photos/{creation_year}/{creation_month}/{filename}",
                "Organizes photos by year and month number",
            ),
        ]
        
        for i, (template, description) in enumerate(examples):
            ttk.Label(example_frame, text=template, wraplength=250, anchor=tk.W).grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(example_frame, text=description, wraplength=300, anchor=tk.W).grid(
                row=i, column=1, sticky=tk.W, padx=5, pady=2
            )
        
        # Close button
        close_button = ttk.Button(content_frame, text="Close", command=help_window.destroy)
        close_button.pack(pady=20)

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, justify=tk.LEFT,
                             background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                             wraplength=250)
            label.pack(padx=3, pady=3)
            
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)


class MediaOrganizerGUI:
    """GUI for the Media Organizer application."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Media Organizer")
        self.root.geometry(defaults.DEFAULT_WINDOW_SIZES["main_window"])  # Increase default height
        self.root.minsize(800, 800)    # Ensure minimum size
        
        # Create a media organizer instance
        self.organizer = MediaOrganizer()
        
        # Initialize settings
        self.show_full_paths = defaults.DEFAULT_SETTINGS["show_full_paths"]
        self.auto_save_enabled = defaults.DEFAULT_SETTINGS["auto_save_enabled"]
        self.auto_preview_enabled = defaults.DEFAULT_SETTINGS["auto_preview_enabled"]
        self.logging_level = defaults.DEFAULT_SETTINGS["logging_level"]
        
        # Create variables for extension filters
        self.extension_vars = {"audio": {}, "video": {}, "image": {}, "ebook": {}}
        
        # Config file path
        self.config_file = Path.home() / defaults.DEFAULT_PATHS["settings_file"]
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the menubar
        self._create_menubar()
        
        # Create the widgets
        self._create_widgets()
        
        # Create log window
        self.log_window = LogWindow(self.root, logger)
        
        # Load saved settings
        self._load_settings()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Log startup
        logger.info("Media Organizer started")
    
    def _create_menubar(self):
        """Create the menubar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Logs", command=self._toggle_logs)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences...", command=self._show_preferences)
        settings_menu.add_separator()
        settings_menu.add_command(label="Reset to Defaults", command=self._reset_settings)
        settings_menu.add_command(label="Save Settings", command=self._save_settings_manual)

    def _toggle_logs(self):
        """Toggle the visibility of the log window."""
        if self.log_window.window.winfo_viewable():
            self.log_window.hide()
        else:
            self.log_window.show()

    def _show_preferences(self):
        """Show the preferences dialog."""
        global SUPPORTED_EXTENSIONS
        
        # Create a callback function to handle the result from the preferences dialog
        def on_save(result):
            if result and 'extensions' in result:
                # Update the global SUPPORTED_EXTENSIONS
                global SUPPORTED_EXTENSIONS
                SUPPORTED_EXTENSIONS = result['extensions']
                # Save settings to file
                self._save_settings()
        
        # Create the preferences dialog with the callback
        PreferencesDialog(self.root, self, SUPPORTED_EXTENSIONS, callback=on_save)
        
    def _create_widgets(self):
        """Create the GUI widgets."""
        # Create a main container frame with three sections
        # 1. Bottom section for progress and buttons (fixed height, packed first)
        # 2. Top section for inputs (fixed height)
        # 3. Middle section for preview (expandable)
        
        # Bottom section - fixed height for progress and buttons
        # Pack this FIRST to ensure it's always at the bottom and visible
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        # Set a minimum height for the bottom frame to ensure it's always visible
        bottom_frame.pack_propagate(False)  # Prevent the frame from shrinking
        bottom_frame.configure(height=150)  # Set minimum height
        
        # Progress frame
        progress_frame = ttk.LabelFrame(bottom_frame, text="Progress", padding=5)
        progress_frame.pack(fill=tk.X, pady=2)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=2)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W)

        self.file_var = tk.StringVar(value="")
        file_label = ttk.Label(progress_frame, textvariable=self.file_var)
        file_label.pack(anchor=tk.W)

        # Buttons frame
        buttons_frame = ttk.Frame(bottom_frame)
        buttons_frame.pack(fill=tk.X, pady=3)

        # Replace single button with Copy and Move buttons
        self.copy_button = ttk.Button(
            buttons_frame, text="Copy Files", command=lambda: self._start_organization("copy")
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)

        self.move_button = ttk.Button(
            buttons_frame, text="Move Files", command=lambda: self._start_organization("move")
        )
        self.move_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            buttons_frame, text="Stop", command=self._stop_organization, state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Top section frame - fixed height
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, pady=2, side=tk.TOP)
        
        # Create a frame to hold both directory selection frames
        directories_frame = ttk.Frame(top_frame)
        directories_frame.pack(fill=tk.X, pady=2)

        # Source directory selection
        source_frame = ttk.LabelFrame(directories_frame, text="Source Directory", padding=5)
        source_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.source_entry = ttk.Entry(source_frame)
        self.source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        source_button = ttk.Button(source_frame, text="Browse...", command=self._browse_source)
        source_button.pack(side=tk.RIGHT)

        # Output directory selection
        output_frame = ttk.LabelFrame(directories_frame, text="Output Directory", padding=5)
        output_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        output_button = ttk.Button(output_frame, text="Browse...", command=self._browse_output)
        output_button.pack(side=tk.RIGHT)
        
        # Extension filters
        extensions_frame = ttk.LabelFrame(top_frame, text="File Type Filters", padding=5)
        extensions_frame.pack(fill=tk.X, pady=2)
        
        # Create a frame for each file type category
        file_types_frame = ttk.Frame(extensions_frame)
        file_types_frame.pack(fill=tk.X, pady=2)
        
        # Audio extensions
        audio_frame = ttk.LabelFrame(file_types_frame, text="Audio")
        audio_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create "Select All" checkbox for audio
        self.audio_all_var = tk.BooleanVar(value=True)
        audio_all_cb = ttk.Checkbutton(
            audio_frame, 
            text="All Audio", 
            variable=self.audio_all_var,
            command=lambda: self._toggle_all_extensions("audio"),
        )
        audio_all_cb.pack(anchor=tk.W)
        
        # Create individual checkboxes for audio extensions
        audio_extensions_frame = ttk.Frame(audio_frame)
        audio_extensions_frame.pack(fill=tk.X, padx=10)
        
        for i, ext in enumerate(SUPPORTED_EXTENSIONS["audio"]):
            ext_name = ext.lstrip(".")
            var = tk.BooleanVar(value=True)
            self.extension_vars["audio"][ext] = var
            cb = ttk.Checkbutton(
                audio_extensions_frame, 
                text=ext_name, 
                variable=var,
                command=self._update_extension_selection,
            )
            cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=5)
        
        # Video extensions
        video_frame = ttk.LabelFrame(file_types_frame, text="Video")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create "Select All" checkbox for video
        self.video_all_var = tk.BooleanVar(value=True)
        video_all_cb = ttk.Checkbutton(
            video_frame, 
            text="All Video", 
            variable=self.video_all_var,
            command=lambda: self._toggle_all_extensions("video"),
        )
        video_all_cb.pack(anchor=tk.W)
        
        # Create individual checkboxes for video extensions
        video_extensions_frame = ttk.Frame(video_frame)
        video_extensions_frame.pack(fill=tk.X, padx=10)
        
        for i, ext in enumerate(SUPPORTED_EXTENSIONS["video"]):
            ext_name = ext.lstrip(".")
            var = tk.BooleanVar(value=True)
            self.extension_vars["video"][ext] = var
            cb = ttk.Checkbutton(
                video_extensions_frame, 
                text=ext_name, 
                variable=var,
                command=self._update_extension_selection,
            )
            cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=5)
        
        # Image extensions
        image_frame = ttk.LabelFrame(file_types_frame, text="Image")
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create "Select All" checkbox for image
        self.image_all_var = tk.BooleanVar(value=True)
        image_all_cb = ttk.Checkbutton(
            image_frame, 
            text="All Images", 
            variable=self.image_all_var,
            command=lambda: self._toggle_all_extensions("image"),
        )
        image_all_cb.pack(anchor=tk.W)
        
        # Create individual checkboxes for image extensions
        image_extensions_frame = ttk.Frame(image_frame)
        image_extensions_frame.pack(fill=tk.X, padx=10)
        
        for i, ext in enumerate(SUPPORTED_EXTENSIONS["image"]):
            ext_name = ext.lstrip(".")
            var = tk.BooleanVar(value=True)
            self.extension_vars["image"][ext] = var
            cb = ttk.Checkbutton(
                image_extensions_frame, 
                text=ext_name, 
                variable=var,
                command=self._update_extension_selection,
            )
            cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=5)

        # eBook extensions
        ebook_frame = ttk.LabelFrame(file_types_frame, text="eBook")
        ebook_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Create "Select All" checkbox for eBook
        self.ebook_all_var = tk.BooleanVar(value=True)
        ebook_all_cb = ttk.Checkbutton(
            ebook_frame,
            text="All eBooks",
            variable=self.ebook_all_var,
            command=lambda: self._toggle_all_extensions("ebook"),
        )
        ebook_all_cb.pack(anchor=tk.W)

        # Create individual checkboxes for eBook extensions
        ebook_extensions_frame = ttk.Frame(ebook_frame)
        ebook_extensions_frame.pack(fill=tk.X, padx=10)

        for i, ext in enumerate(SUPPORTED_EXTENSIONS["ebook"]):
            ext_name = ext.lstrip(".")
            var = tk.BooleanVar(value=True)
            self.extension_vars["ebook"][ext] = var
            cb = ttk.Checkbutton(
                ebook_extensions_frame,
                text=ext_name,
                variable=var,
                command=self._update_extension_selection,
            )
            cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=5)
        
        # Template configuration
        template_frame = ttk.LabelFrame(top_frame, text="Organization Templates", padding=5)
        template_frame.pack(fill=tk.X, pady=2)
        
        template_header_frame = ttk.Frame(template_frame)
        template_header_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(template_header_frame, text="Use {placeholders} for metadata fields:").pack(
            side=tk.LEFT
        )
        
        # Help button for placeholders
        help_button = ttk.Button(
            template_header_frame, text="Placeholders Help", command=self._show_placeholders_help
        )
        help_button.pack(side=tk.RIGHT)
        
        # Create a notebook for different media type templates
        template_notebook = ttk.Notebook(template_frame)
        template_notebook.pack(fill=tk.X, pady=2)

        # Audio template tab
        audio_template_frame = ttk.Frame(template_notebook, padding=2)
        template_notebook.add(audio_template_frame, text="Audio")

        # Video template tab
        video_template_frame = ttk.Frame(template_notebook, padding=2)
        template_notebook.add(video_template_frame, text="Video")

        # Image template tab
        image_template_frame = ttk.Frame(template_notebook, padding=2)
        template_notebook.add(image_template_frame, text="Image")

        # eBook template tab
        ebook_template_frame = ttk.Frame(template_notebook, padding=2)
        template_notebook.add(ebook_template_frame, text="eBook")

        # Create template variables and entries for each media type
        self.template_vars = {}
        self.template_entries = {}

        # Audio template
        self.template_vars["audio"] = tk.StringVar(value=self.organizer.templates["audio"])
        self.template_vars["audio"].trace_add(
            "write", lambda *args: self._on_template_change("audio")
        )
        ttk.Label(audio_template_frame, text="Audio Template:").pack(anchor=tk.W)
        self.template_entries["audio"] = ttk.Entry(
            audio_template_frame, textvariable=self.template_vars["audio"]
        )
        self.template_entries["audio"].pack(fill=tk.X, pady=1)
        ttk.Label(
            audio_template_frame, text="Example: {file_type}/{artist}/{album}/{filename}"
        ).pack(anchor=tk.W)

        # Video template
        self.template_vars["video"] = tk.StringVar(value=self.organizer.templates["video"])
        self.template_vars["video"].trace_add(
            "write", lambda *args: self._on_template_change("video")
        )
        ttk.Label(video_template_frame, text="Video Template:").pack(anchor=tk.W)
        self.template_entries["video"] = ttk.Entry(
            video_template_frame, textvariable=self.template_vars["video"]
        )
        self.template_entries["video"].pack(fill=tk.X, pady=1)
        ttk.Label(video_template_frame, text="Example: {file_type}/{year}/{filename}").pack(
            anchor=tk.W
        )

        # Image template
        self.template_vars["image"] = tk.StringVar(value=self.organizer.templates["image"])
        self.template_vars["image"].trace_add(
            "write", lambda *args: self._on_template_change("image")
        )
        ttk.Label(image_template_frame, text="Image Template:").pack(anchor=tk.W)
        self.template_entries["image"] = ttk.Entry(
            image_template_frame, textvariable=self.template_vars["image"]
        )
        self.template_entries["image"].pack(fill=tk.X, pady=1)
        ttk.Label(
            image_template_frame,
            text="Example: {file_type}/{creation_year}/{creation_month_name}/{filename}",
        ).pack(anchor=tk.W)

        # eBook template
        self.template_vars["ebook"] = tk.StringVar(value=self.organizer.templates["ebook"])
        self.template_vars["ebook"].trace_add(
            "write", lambda *args: self._on_template_change("ebook")
        )
        ttk.Label(ebook_template_frame, text="eBook Template:").pack(anchor=tk.W)
        self.template_entries["ebook"] = ttk.Entry(
            ebook_template_frame, textvariable=self.template_vars["ebook"]
        )
        self.template_entries["ebook"].pack(fill=tk.X, pady=1)
        ttk.Label(
            ebook_template_frame,
            text="Example: {file_type}/{author}/{title}/{filename}",
        ).pack(anchor=tk.W)

        # For backward compatibility
        self.template_var = self.template_vars["audio"]
        self.template_entry = self.template_entries["audio"]

        # Middle section - expandable preview
        middle_frame = ttk.Frame(self.main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=2, side=tk.TOP)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(
            middle_frame, text="Preview", padding=5
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        # Add a button frame at the top of the preview
        preview_button_frame = ttk.Frame(preview_frame)
        preview_button_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Add Analyze button
        analyze_button = ttk.Button(
            preview_button_frame, text="Analyze", command=self._generate_preview
        )
        analyze_button.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(analyze_button, "Refresh the preview based on current settings")
        
        # Preview table with scrollbars
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)

        # Create the treeview
        self.preview_tree = ttk.Treeview(
            preview_container,
            columns=("source", "destination"),
            show="headings",
            selectmode="browse"
        )
        
        # Define the columns
        self.preview_tree.heading("source", text="Source Path")
        self.preview_tree.heading("destination", text="Destination Path")
        
        # Configure column widths (both columns get equal width)
        preview_container.update_idletasks()  # Ensure container has been drawn
        width = preview_container.winfo_width()
        self.preview_tree.column("source", width=width//2, stretch=True)
        self.preview_tree.column("destination", width=width//2, stretch=True)

        # Add scrollbars
        preview_scrollbar_y = ttk.Scrollbar(
            preview_container, orient="vertical", command=self.preview_tree.yview
        )
        preview_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        preview_scrollbar_x = ttk.Scrollbar(
            preview_container, orient="horizontal", command=self.preview_tree.xview
        )
        preview_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.preview_tree.configure(
            yscrollcommand=preview_scrollbar_y.set,
            xscrollcommand=preview_scrollbar_x.set
        )
    
    def _browse_source(self):
        """Browse for source directory."""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, directory)
            # Clear preview when source changes
            self._clear_preview()
            # Auto-save settings if enabled
            if getattr(self, "auto_save_enabled", True):
                self._save_settings()
            # Auto-generate preview
            self._auto_generate_preview()
    
    def _browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
            # Clear preview when output changes
            self._clear_preview()
            # Auto-save settings if enabled
            if getattr(self, "auto_save_enabled", True):
                self._save_settings()
            # Auto-generate preview
            self._auto_generate_preview()
            
    def _clear_preview(self):
        """Clear the preview list."""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
    
    def _update_progress(self, processed, total, current_file):
        """Update the progress display."""
        if total > 0:
            progress = (processed / total) * 100
            self.progress_var.set(progress)
            
            self.status_var.set(f"Processed: {processed}/{total} files ({progress:.1f}%)")
            
            if current_file == "Complete":
                self.file_var.set("Organization complete!")
                self._organization_complete()
            else:
                # Truncate long paths for display
                if len(current_file) > 70:
                    display_file = "..." + current_file[-67:]
                else:
                    display_file = current_file
                self.file_var.set(f"Current: {display_file}")
    
    def _toggle_all_extensions(self, file_type):
        """Toggle all extensions for a file type."""
        value = getattr(self, f"{file_type}_all_var").get()
        for var in self.extension_vars[file_type].values():
            var.set(value)
        # Auto-save settings if enabled
        if getattr(self, "auto_save_enabled", True):
            self._save_settings()
        # Auto-generate preview
        self._auto_generate_preview()
    
    def _update_extension_selection(self):
        """Update the 'All' checkboxes based on individual selections."""
        for file_type in ["audio", "video", "image", "ebook"]:
            all_selected = all(var.get() for var in self.extension_vars[file_type].values())
            getattr(self, f"{file_type}_all_var").set(all_selected)
        # Auto-save settings if enabled
        if getattr(self, "auto_save_enabled", True):
            self._save_settings()
        # Auto-generate preview
        self._auto_generate_preview()
    
    def _get_selected_extensions(self):
        """Get a list of all selected file extensions."""
        selected_extensions = []
        for file_type, extensions_list in self.extension_vars.items():
            for ext, var in extensions_list.items():
                if var.get():
                    selected_extensions.append(ext)
        return selected_extensions
    
    def _generate_preview(self):
        """Generate a preview of the organization."""
        # Validate inputs
        source_dir = self.source_entry.get().strip()
        output_dir = self.output_entry.get().strip()

        # Get templates for each media type
        templates = {
            "audio": self.template_vars["audio"].get().strip(),
            "video": self.template_vars["video"].get().strip(),
            "image": self.template_vars["image"].get().strip(),
            "ebook": self.template_vars["ebook"].get().strip(),
        }
        
        if not source_dir:
            messagebox.showerror("Error", "Please select a source directory.")
            return
            
        if not all(templates.values()):
            messagebox.showerror("Error", "Please provide templates for all media types.")
            return
            
        # Clear previous preview
        self._clear_preview()
        
        # Update status to show preview is generating
        self.status_var.set("Analyzing files and generating preview...")
        self.file_var.set("Please wait while files are being analyzed...")
        self.root.update_idletasks()
        
        # Start preview generation in a separate thread
        threading.Thread(
            target=self._generate_preview_thread,
            args=(source_dir, output_dir, templates),
            daemon=True
        ).start()

    def _generate_preview_thread(self, source_dir, output_dir, templates):
        """Generate preview in a separate thread to keep UI responsive."""
        try:
            # Configure organizer for preview
            self.organizer.set_source_dir(source_dir)
            if output_dir:
                self.organizer.set_output_dir(output_dir)

            # Set templates for each media type
            for media_type, template in templates.items():
                self.organizer.set_template(template, media_type)
            
            # Get selected extensions
            selected_extensions = self._get_selected_extensions()
            if not selected_extensions:
                # Update UI in the main thread
                self.root.after(0, lambda: self._update_preview_status("No file types selected. Please select at least one file type."))
                return
                
            # Check if destination is inside source to avoid processing files in the destination
            source_path = Path(source_dir)
            is_dest_in_source = False
            if output_dir:
                output_path = Path(output_dir)
                try:
                    # Convert to absolute paths for comparison
                    abs_source = source_path.resolve()
                    abs_output = output_path.resolve()
                    # Check if output is a subdirectory of source
                    is_dest_in_source = str(abs_output).startswith(str(abs_source))
                    if is_dest_in_source:
                        logger.info(f"Destination directory is inside source directory. Will skip files in destination for preview.")
                except Exception as e:
                    logger.error(f"Error checking directory relationship: {e}")

            # Find up to 100 files for preview
            preview_files = []
            count = 0
            
            for file_path in source_path.rglob("*"):
                # Skip files in the destination directory if it's inside the source
                if is_dest_in_source and output_dir and file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(source_path)
                        dest_path = Path(output_dir) / rel_path
                        if file_path.is_relative_to(Path(output_dir)) or file_path == dest_path:
                            continue
                    except (ValueError, RuntimeError):
                        pass  # Not relative, so continue processing
                        
                if file_path.is_file() and file_path.suffix.lower() in selected_extensions:
                    preview_files.append(file_path)
                    count += 1
                    if count >= 100:  # Limit to 100 files for preview
                        break
            
            # Prepare preview data
            preview_data = []
            
            # Generate preview for each file
            for file_path in preview_files:
                try:
                    # Extract metadata
                    media_file = MediaFile(file_path, SUPPORTED_EXTENSIONS)

                    # Get the appropriate template for this file type
                    template = self.organizer.get_template(media_file.file_type)
                    
                    # Generate destination path
                    rel_path = media_file.get_formatted_path(template)
                    
                    # Get source path for display
                    if getattr(self, "show_full_paths", False):
                        display_source = str(file_path)
                        display_dest = str(self.organizer.output_dir / rel_path)
                    else:
                        try:
                            display_source = str(file_path.relative_to(source_path))
                            display_dest = rel_path
                        except ValueError:
                            display_source = str(file_path)
                            display_dest = str(self.organizer.output_dir / rel_path)
                    
                    # Add to preview data
                    preview_data.append((display_source, display_dest))
                    
                except Exception as e:
                    logger.error(f"Error generating preview for {file_path}: {e}")
            
            # Update UI in the main thread
            self.root.after(0, lambda: self._update_preview_results(preview_data, count))

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            # Update UI in the main thread
            self.root.after(0, lambda: self._update_preview_status(f"Preview generation failed: {str(e)}", error=True))

    def _update_preview_results(self, preview_data, count):
        """Update the preview treeview with results from the preview thread."""
        # Insert preview data into treeview
        for display_source, display_dest in preview_data:
            self.preview_tree.insert("", "end", values=(display_source, display_dest))

        # Update status
            if count == 0:
                self.status_var.set("No media files found in the source directory.")
                self.file_var.set("")
            else:
            # Count files by media type
                media_types = {}
            for file_path, _ in preview_data:
                # Get file extension
                ext = os.path.splitext(file_path)[1].lower()
                # Determine media type
                media_type = None
                for type_name, extensions in SUPPORTED_EXTENSIONS.items():
                    if ext in extensions:
                        media_type = type_name
                        break
                
                if media_type:
                    media_types[media_type] = media_types.get(media_type, 0) + 1
            
                # Create detailed message
                type_counts = ", ".join([f"{count} {media_type}" for media_type, count in media_types.items()])
                self.status_var.set(f"Preview generated for {count} files.")
            self.file_var.set(f"Found: {type_counts}")
    
    def _update_preview_status(self, message, error=False):
        """Update the preview status with a message."""
        self.status_var.set(message)
        if error:
            messagebox.showerror("Error", message)
    
    def _start_organization(self, mode="copy"):
        """Start the organization process with the specified mode (copy or move)."""
        # Validate inputs
        source_dir = self.source_entry.get().strip()
        output_dir = self.output_entry.get().strip()

        # Get templates for each media type
        templates = {
            "audio": self.template_vars["audio"].get().strip(),
            "video": self.template_vars["video"].get().strip(),
            "image": self.template_vars["image"].get().strip(),
            "ebook": self.template_vars["ebook"].get().strip(),
        }
        
        if not source_dir or not output_dir:
            messagebox.showerror("Error", "Please select both source and output directories.")
            return
        
        if not all(templates.values()):
            messagebox.showerror("Error", "Please provide templates for all media types.")
            return
        
        if not os.path.exists(source_dir):
            messagebox.showerror("Error", "Source directory does not exist.")
            return
        
        # Confirm move operation
        if mode == "move" and not messagebox.askyesno(
            "Confirm Move Operation",
            "Moving files will remove them from the source directory. Continue?",
        ):
            return

        # Create output directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create output directory: {str(e)}")
            return
        
        # Get selected extensions
        selected_extensions = self._get_selected_extensions()
        if not selected_extensions:
            messagebox.showinfo(
                "Info", "No file types selected. Please select at least one file type."
            )
            return
        
        # Configure organizer
        self.organizer.set_source_dir(source_dir)
        self.organizer.set_output_dir(output_dir)
        self.organizer.set_operation_mode(mode)

        # Set templates for each media type
        for media_type, template in templates.items():
            self.organizer.set_template(template, media_type)

        # Save settings
        self._save_settings()

        # Log settings
        logger.info(f"Source directory: {source_dir}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Operation mode: {mode}")
        for media_type, template in templates.items():
            logger.info(f"Using {media_type} template: {template}")
        logger.info(f"Selected extensions: {', '.join(selected_extensions)}")

        # Start organization in a separate thread
        self._run_organization_with_filters(selected_extensions)

    def _run_organization_with_filters(self, selected_extensions):
        """Run the organization process with the selected file extensions."""
        # Update UI
        self.copy_button.config(state=tk.DISABLED)
        self.move_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.status_var.set("Starting...")
        self.file_var.set("")
        
        # Clear preview
        self._clear_preview()
        
        # Start organization in a separate thread
        threading.Thread(
            target=self._run_organization_process, args=(selected_extensions,), daemon=True
        ).start()
        
    def _run_organization_process(self, selected_extensions):
        """Run the actual organization process in a separate thread."""
        try:
            # Find all media files
            source_path = Path(self.organizer.source_dir)
            output_path = Path(self.organizer.output_dir)

            # Check if destination is inside source to avoid processing files in the destination
            is_dest_in_source = False
            try:
                # Convert to absolute paths for comparison
                abs_source = source_path.resolve()
                abs_output = output_path.resolve()
                # Check if output is a subdirectory of source
                is_dest_in_source = str(abs_output).startswith(str(abs_source))
                if is_dest_in_source:
                    logger.info(f"Destination directory is inside source directory. Will skip files in destination.")
            except Exception as e:
                logger.error(f"Error checking directory relationship: {e}")

            # Count total files first (excluding files in destination if it's inside source)
            total_files = 0
            for file_path in source_path.rglob("*"):
                if self.organizer.stop_requested:
                    break
                    
                # Skip files in the destination directory if it's inside the source
                if is_dest_in_source and file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(source_path)
                        dest_path = output_path / rel_path
                        if file_path.is_relative_to(output_path) or file_path == dest_path:
                            continue
                    except (ValueError, RuntimeError):
                        pass  # Not relative, so continue processing
                        
                if file_path.is_file() and file_path.suffix.lower() in selected_extensions:
                    total_files += 1
            
            # Process files
            processed = 0
            
            for file_path in source_path.rglob("*"):
                if self.organizer.stop_requested:
                    logger.info("Organization stopped by user")
                    break
                    
                # Skip files in the destination directory if it's inside the source
                if is_dest_in_source and file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(source_path)
                        dest_path = output_path / rel_path
                        if file_path.is_relative_to(output_path) or file_path == dest_path:
                            continue
                    except (ValueError, RuntimeError):
                        pass  # Not relative, so continue processing
                    
                if file_path.is_file() and file_path.suffix.lower() in selected_extensions:
                    try:
                        # Extract metadata
                        media_file = MediaFile(file_path, SUPPORTED_EXTENSIONS)

                        # Get the appropriate template for this file type
                        template = self.organizer.get_template(media_file.file_type)
                        
                        # Generate destination path
                        rel_path = media_file.get_formatted_path(template)
                        dest_path = output_path / rel_path
                        
                        # Create destination directory if it doesn't exist
                        os.makedirs(dest_path.parent, exist_ok=True)
                        
                        # Copy or move the file based on operation mode
                        if self.organizer.operation_mode == "copy":
                            shutil.copy2(file_path, dest_path)
                            logger.info(f"Copied {file_path} to {dest_path}")
                        else:  # move mode
                            shutil.move(file_path, dest_path)
                            logger.info(f"Moved {file_path} to {dest_path}")
                        
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
                    
                    # Update progress
                    processed += 1
                    self._update_progress(processed, total_files, str(file_path))
            
            # Complete
            self._update_progress(processed, total_files, "Complete")
            operation_name = "copy" if self.organizer.operation_mode == "copy" else "move"
            logger.info(f"{operation_name.capitalize()} operation complete. Processed {processed} files.")
            
        except Exception as e:
            logger.error(f"Error during organization: {e}")
            messagebox.showerror("Error", f"An error occurred during organization: {str(e)}")
    
    def _stop_organization(self):
        """Stop the organization process."""
        if self.organizer.is_running:
            self.organizer.stop()
            self.status_var.set("Stopping...")
            logger.info("Stopping organization process...")
    
    def _organization_complete(self):
        """Handle organization completion."""
        self.copy_button.config(state=tk.NORMAL)
        self.move_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        operation_name = "copied" if self.organizer.operation_mode == "copy" else "moved"
        
        # Show completion message
        messagebox.showinfo(
            "Complete",
            f"Organization complete!\n\n{operation_name.capitalize()} {self.organizer.files_processed} files.",
        )

    def _on_close(self):
        """Handle window close event."""
        # Save settings before closing
        self._save_settings()
        # Close the window
        self.root.destroy()
    
    def _save_settings(self):
        """Save user settings to a configuration file."""
        try:
            # Collect settings
            settings = {
                "source_dir": self.source_entry.get().strip(),
                "output_dir": self.output_entry.get().strip(),
                "templates": {
                    "audio": self.template_vars["audio"].get().strip(),
                    "video": self.template_vars["video"].get().strip(),
                    "image": self.template_vars["image"].get().strip(),
                    "ebook": self.template_vars["ebook"].get().strip(),
                },
                # For backward compatibility
                "template": self.template_vars["audio"].get().strip(),
                "extensions": {
                    "audio": {ext: var.get() for ext, var in self.extension_vars["audio"].items()},
                    "video": {ext: var.get() for ext, var in self.extension_vars["video"].items()},
                    "image": {ext: var.get() for ext, var in self.extension_vars["image"].items()},
                    "ebook": {ext: var.get() for ext, var in self.extension_vars["ebook"].items()},
                },
                # Save custom extensions
                "custom_extensions": SUPPORTED_EXTENSIONS,
                "show_full_paths": getattr(self, "show_full_paths", False),
                "auto_save_enabled": getattr(self, "auto_save_enabled", True),
                "auto_preview_enabled": getattr(self, "auto_preview_enabled", True),
                "logging_level": getattr(self, "logging_level", defaults.DEFAULT_SETTINGS["logging_level"]),
                "operation_mode": getattr(self, "operation_mode", "copy"),
            }
            
            # Save to file
            with open(self.config_file, "w") as f:
                json.dump(settings, f)
                
            logger.info(f"Settings saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def _load_settings(self):
        """Load user settings from the configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    settings = json.load(f)
                
                # Apply settings
                if "source_dir" in settings and settings["source_dir"]:
                    self.source_entry.delete(0, tk.END)
                    self.source_entry.insert(0, settings["source_dir"])
                
                if "output_dir" in settings and settings["output_dir"]:
                    self.output_entry.delete(0, tk.END)
                    self.output_entry.insert(0, settings["output_dir"])

                # Load templates
                if "templates" in settings:
                    for media_type in ["audio", "video", "image", "ebook"]:
                        if (
                            media_type in settings["templates"]
                            and settings["templates"][media_type]
                        ):
                            self.template_vars[media_type].set(settings["templates"][media_type])
                # For backward compatibility
                elif "template" in settings and settings["template"]:
                    self.template_vars["audio"].set(settings["template"])
                    # Also update the default template variable for backward compatibility
                    self.template_var.set(settings["template"])

                # Load custom extensions if available
                if "custom_extensions" in settings:
                    global SUPPORTED_EXTENSIONS
                    # Start with default extensions
                    custom_extensions = extensions.DEFAULT_EXTENSIONS.copy()
                    # Update with custom extensions
                    for media_type, exts in settings["custom_extensions"].items():
                        if media_type in custom_extensions and exts:
                            custom_extensions[media_type] = exts
                    # Update global extensions
                    SUPPORTED_EXTENSIONS = custom_extensions
                
                # Apply extension selections
                if "extensions" in settings:
                    for file_type in ["audio", "video", "image", "ebook"]:
                        if file_type in settings["extensions"]:
                            for ext, value in settings["extensions"][file_type].items():
                                if ext in self.extension_vars[file_type]:
                                    self.extension_vars[file_type][ext].set(value)
                
                # Load full paths setting
                self.show_full_paths = settings.get("show_full_paths", False)

                # Load auto-save setting (defaults to True)
                self.auto_save_enabled = settings.get("auto_save_enabled", True)

                # Load auto-preview setting (defaults to True)
                self.auto_preview_enabled = settings.get("auto_preview_enabled", True)

                # Load logging level setting
                self.logging_level = settings.get("logging_level", defaults.DEFAULT_SETTINGS["logging_level"])

                # Update "All" checkboxes
                self._update_extension_selection()
                
                logger.info(f"Settings loaded from {self.config_file}")
                
                # Generate initial preview if auto-preview is enabled
                self._auto_generate_preview()

                # Load operation mode
                self.operation_mode = settings.get("operation_mode", "copy")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def _reset_settings(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno(
            "Reset Settings", "Are you sure you want to reset all settings to defaults?"
        ):
            try:
                # Clear entries
                self.source_entry.delete(0, tk.END)
                self.output_entry.delete(0, tk.END)

                # Reset templates to defaults
                for media_type in ["audio", "video", "image", "ebook"]:
                    self.template_vars[media_type].set(defaults.DEFAULT_TEMPLATES[media_type])

                # For backward compatibility
                self.template_var.set(defaults.DEFAULT_TEMPLATES["audio"])
                
                # Reset extension checkboxes to checked
                for file_type in ["audio", "video", "image", "ebook"]:
                    getattr(self, f"{file_type}_all_var").set(True)
                    self._toggle_all_extensions(file_type)
                
                # Reset settings to defaults
                self.show_full_paths = defaults.DEFAULT_SETTINGS["show_full_paths"]
                self.auto_save_enabled = defaults.DEFAULT_SETTINGS["auto_save_enabled"]
                self.auto_preview_enabled = defaults.DEFAULT_SETTINGS["auto_preview_enabled"]
                self.logging_level = defaults.DEFAULT_SETTINGS["logging_level"]
                
                # Clear preview
                self._clear_preview()
                
                # Delete config file if it exists
                if self.config_file.exists():
                    self.config_file.unlink()
                    logger.info(f"Settings file deleted: {self.config_file}")
                
                self.status_var.set("Settings reset to defaults")
                
            except Exception as e:
                logger.error(f"Error resetting settings: {e}")
                messagebox.showerror("Error", f"Failed to reset settings: {str(e)}")

    def _save_settings_manual(self):
        """Manually save settings and show confirmation."""
        self._save_settings()
        self.status_var.set(f"Settings saved to {self.config_file}")
        messagebox.showinfo(
            "Settings Saved", f"Your settings have been saved to:\n{self.config_file}"
        )

    def _on_template_change(self, *args, media_type=None):
        """
        Handle template change event.

        Args:
            *args: Variable arguments passed by tkinter trace
            media_type: The media type whose template changed ('audio', 'video', 'image', 'ebook')
        """
        # Auto-save settings after a short delay if enabled
        if getattr(self, "auto_save_enabled", True):
            if hasattr(self, "_template_timer"):
                self.root.after_cancel(self._template_timer)
            self._template_timer = self.root.after(1000, self._save_settings)
        
        # Auto-generate preview after a short delay
        if hasattr(self, "_preview_timer"):
            self.root.after_cancel(self._preview_timer)
            self._preview_timer = self.root.after(1500, self._auto_generate_preview)

    def _auto_generate_preview(self):
        """Automatically generate preview if enabled and source directory exists."""
        if self.auto_preview_enabled:
            source_dir = self.source_entry.get().strip()
            if source_dir and os.path.exists(source_dir):
                # Cancel any pending preview generation
                if hasattr(self, "_preview_timer"):
                    self.root.after_cancel(self._preview_timer)
                # Schedule preview generation after a short delay
                self._preview_timer = self.root.after(500, self._generate_preview)

    def _show_placeholders_help(self):
        """Show a modal dialog with information about available placeholders."""
        # Create a new top-level window
        help_window = tk.Toplevel(self.root)
        help_window.title("Available Placeholders")
        help_window.geometry(defaults.DEFAULT_WINDOW_SIZES["help_window"])
        help_window.minsize(600, 400)
        help_window.transient(self.root)  # Make it a modal dialog
        help_window.grab_set()  # Make it modal
        
        # Center the window
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create a frame for the content
        content_frame = ttk.Frame(help_window, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            content_frame, text="Available Placeholders", font=("TkDefaultFont", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create a frame for each category
        categories_frame = ttk.Frame(content_frame)
        categories_frame.pack(fill=tk.BOTH, expand=True)
        
        # Common placeholders
        common_frame = ttk.LabelFrame(categories_frame, text="Common", padding=10)
        common_frame.pack(fill=tk.X, pady=5)
        
        common_placeholders = [
            ("{filename}", "Original filename without extension"),
            ("{extension}", "File extension (e.g., mp3, jpg)"),
            ("{file_type}", "Type of file (audio, video, image, ebook)"),
            ("{size}", "File size in bytes"),
            ("{creation_date}", "File creation date (YYYY-MM-DD)"),
            ("{creation_year}", "Year of file creation (YYYY)"),
            ("{creation_month}", "Month of file creation (01-12)"),
            ("{creation_month_name}", "Month name of file creation (January, February, etc.)"),
        ]
        
        for i, (placeholder, description) in enumerate(common_placeholders):
            ttk.Label(common_frame, text=placeholder, width=15, anchor=tk.W).grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(common_frame, text=description, anchor=tk.W).grid(
                row=i, column=1, sticky=tk.W, padx=5, pady=2
            )
        
        # Audio placeholders
        audio_frame = ttk.LabelFrame(categories_frame, text="Audio", padding=10)
        audio_frame.pack(fill=tk.X, pady=5)
        
        audio_placeholders = [
            ("{title}", "Song title"),
            ("{artist}", "Artist name"),
            ("{album}", "Album name"),
            ("{year}", "Release year"),
            ("{genre}", "Music genre"),
            ("{track}", "Track number"),
            ("{duration}", "Song duration"),
            ("{bitrate}", "Audio bitrate"),
        ]
        
        for i, (placeholder, description) in enumerate(audio_placeholders):
            ttk.Label(audio_frame, text=placeholder, width=15, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(audio_frame, text=description, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, padx=5, pady=2
            )
        
        # Image placeholders
        image_frame = ttk.LabelFrame(categories_frame, text="Image", padding=10)
        image_frame.pack(fill=tk.X, pady=5)
        
        image_placeholders = [
            ("{width}", "Image width in pixels"),
            ("{height}", "Image height in pixels"),
            ("{format}", "Image format (e.g., JPEG, PNG)"),
            ("{camera_make}", "Camera manufacturer"),
            ("{camera_model}", "Camera model"),
            ("{date_taken}", "Date when the photo was taken"),
        ]
        
        for i, (placeholder, description) in enumerate(image_placeholders):
            ttk.Label(image_frame, text=placeholder, width=15, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(image_frame, text=description, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, padx=5, pady=2
            )

        # eBook placeholders
        ebook_frame = ttk.LabelFrame(categories_frame, text="eBook", padding=10)
        ebook_frame.pack(fill=tk.X, pady=5)

        ebook_placeholders = [
            ("{title}", "Book title"),
            ("{author}", "Author name"),
            ("{year}", "Publication year"),
            ("{genre}", "Book genre"),
        ]

        for i, (placeholder, description) in enumerate(ebook_placeholders):
            ttk.Label(ebook_frame, text=placeholder, width=15, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(ebook_frame, text=description, anchor=tk.W).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, padx=5, pady=2
            )
        
        # Example usage
        example_frame = ttk.LabelFrame(content_frame, text="Example Templates", padding=10)
        example_frame.pack(fill=tk.X, pady=5)
        
        examples = [
            (
                "{file_type}/{artist}/{album}/{filename}",
                "Organizes by file type, then artist, then album",
            ),
            (
                "Music/{year}/{artist} - {title}.{extension}",
                "Organizes music by year, then artist-title",
            ),
            (
                "{file_type}/{creation_year}/{creation_month_name}/{filename}",
                "Organizes by file type, year, and month",
            ),
            (
                "Photos/{creation_year}/{creation_month}/{filename}",
                "Organizes photos by year and month number",
            ),
        ]
        
        for i, (template, description) in enumerate(examples):
            ttk.Label(example_frame, text=template, wraplength=250, anchor=tk.W).grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(example_frame, text=description, wraplength=300, anchor=tk.W).grid(
                row=i, column=1, sticky=tk.W, padx=5, pady=2
            )
        
        # Close button
        close_button = ttk.Button(content_frame, text="Close", command=help_window.destroy)
        close_button.pack(pady=20)

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, justify=tk.LEFT,
                             background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                             wraplength=250)
            label.pack(padx=3, pady=3)
            
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)


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
        except Exception as e:
            logger.error(f"Error loading logging level from settings: {e}")
    
    root = tk.Tk()
    app = MediaOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 
