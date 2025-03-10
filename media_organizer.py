#!/usr/bin/env python3
"""
Media Organizer - A tool to organize media files based on metadata.
"""

import os
import sys
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
from PIL import Image, ImageTk
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('media_organizer.log')
    ]
)
logger = logging.getLogger('MediaOrganizer')

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    'audio': ['.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wav'],
    'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv'],
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
}

class MediaFile:
    """Class to represent a media file with its metadata."""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.metadata = {}
        self.file_type = self._get_file_type()
        self.extract_metadata()
        
    def _get_file_type(self):
        """Determine the type of media file."""
        ext = self.file_path.suffix.lower()
        for file_type, extensions in SUPPORTED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return 'unknown'
    
    def extract_metadata(self):
        """Extract metadata from the media file."""
        try:
            if self.file_type == 'audio':
                self._extract_audio_metadata()
            elif self.file_type == 'video':
                self._extract_video_metadata()
            elif self.file_type == 'image':
                self._extract_image_metadata()
            
            # Add file information
            self.metadata['filename'] = self.file_path.name
            self.metadata['extension'] = self.file_path.suffix.lower()[1:]  # Remove the dot
            self.metadata['size'] = self.file_path.stat().st_size
            self.metadata['creation_date'] = datetime.fromtimestamp(
                self.file_path.stat().st_ctime
            ).strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {self.file_path}: {e}")
    
    def _extract_audio_metadata(self):
        """Extract metadata from audio files."""
        ext = self.file_path.suffix.lower()
        
        try:
            if ext == '.mp3':
                audio = MP3(self.file_path)
                if audio.tags:
                    id3 = ID3(self.file_path)
                    self.metadata['title'] = str(id3.get('TIT2', ''))
                    self.metadata['artist'] = str(id3.get('TPE1', ''))
                    self.metadata['album'] = str(id3.get('TALB', ''))
                    self.metadata['year'] = str(id3.get('TDRC', ''))
                    self.metadata['genre'] = str(id3.get('TCON', ''))
                    self.metadata['track'] = str(id3.get('TRCK', ''))
            
            elif ext == '.flac':
                audio = FLAC(self.file_path)
                self.metadata['title'] = ', '.join(audio.get('title', ['']))
                self.metadata['artist'] = ', '.join(audio.get('artist', ['']))
                self.metadata['album'] = ', '.join(audio.get('album', ['']))
                self.metadata['year'] = ', '.join(audio.get('date', ['']))
                self.metadata['genre'] = ', '.join(audio.get('genre', ['']))
                self.metadata['track'] = ', '.join(audio.get('tracknumber', ['']))
            
            elif ext in ['.m4a', '.aac']:
                audio = MP4(self.file_path)
                self.metadata['title'] = ', '.join(audio.get('\xa9nam', ['']))
                self.metadata['artist'] = ', '.join(audio.get('\xa9ART', ['']))
                self.metadata['album'] = ', '.join(audio.get('\xa9alb', ['']))
                self.metadata['year'] = ', '.join(audio.get('\xa9day', ['']))
                self.metadata['genre'] = ', '.join(audio.get('\xa9gen', ['']))
                
            # Add audio-specific information
            if hasattr(audio, 'info'):
                self.metadata['duration'] = audio.info.length
                self.metadata['bitrate'] = getattr(audio.info, 'bitrate', 0)
                self.metadata['sample_rate'] = getattr(audio.info, 'sample_rate', 0)
                
        except Exception as e:
            logger.error(f"Error extracting audio metadata from {self.file_path}: {e}")
            
    def _extract_video_metadata(self):
        """Extract metadata from video files."""
        # Basic file information for videos
        # For more detailed video metadata, additional libraries like ffmpeg would be needed
        self.metadata['title'] = self.file_path.stem
        
    def _extract_image_metadata(self):
        """Extract metadata from image files."""
        try:
            with Image.open(self.file_path) as img:
                self.metadata['width'] = img.width
                self.metadata['height'] = img.height
                self.metadata['format'] = img.format
                self.metadata['mode'] = img.mode
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        # Map EXIF tags to readable names
                        exif_tags = {
                            271: 'camera_make',
                            272: 'camera_model',
                            306: 'date_time',
                            36867: 'date_taken',
                            33432: 'copyright'
                        }
                        
                        for tag, value in exif.items():
                            if tag in exif_tags:
                                self.metadata[exif_tags[tag]] = value
        
        except Exception as e:
            logger.error(f"Error extracting image metadata from {self.file_path}: {e}")

    def get_formatted_path(self, template):
        """
        Generate a formatted path based on the template and metadata.
        
        Template can include placeholders like {artist}, {album}, {year}, etc.
        """
        try:
            # Create a dictionary with lowercase keys for case-insensitive matching
            metadata_lower = {k.lower(): v for k, v in self.metadata.items()}
            
            # Replace placeholders in the template
            formatted = template
            
            # Find all placeholders in the template
            placeholders = re.findall(r'\{([^{}]+)\}', template)
            
            for placeholder in placeholders:
                # Check if the placeholder exists in metadata (case-insensitive)
                placeholder_lower = placeholder.lower()
                if placeholder_lower in metadata_lower:
                    value = metadata_lower[placeholder_lower]
                    # Convert to string and sanitize for filesystem
                    value_str = str(value)
                    # Replace invalid characters with underscore
                    value_str = re.sub(r'[<>:"/\\|?*]', '_', value_str)
                    # Replace placeholder in the template
                    formatted = formatted.replace(f'{{{placeholder}}}', value_str)
                else:
                    # If placeholder not found, replace with 'Unknown'
                    formatted = formatted.replace(f'{{{placeholder}}}', 'Unknown')
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting path with template {template}: {e}")
            return str(self.file_path.name)  # Return just the filename as fallback


class MediaOrganizer:
    """Class to organize media files based on metadata."""
    
    def __init__(self):
        self.source_dir = None
        self.output_dir = None
        self.template = "{file_type}/{artist}/{album}/{filename}"
        self.files_processed = 0
        self.total_files = 0
        self.current_file = ""
        self.is_running = False
        self.stop_requested = False
    
    def set_source_dir(self, directory):
        """Set the source directory."""
        self.source_dir = Path(directory)
    
    def set_output_dir(self, directory):
        """Set the output directory."""
        self.output_dir = Path(directory)
    
    def set_template(self, template):
        """Set the organization template."""
        self.template = template
    
    def find_media_files(self):
        """Find all supported media files in the source directory."""
        if not self.source_dir or not self.source_dir.exists():
            raise ValueError("Source directory does not exist")
        
        all_extensions = []
        for extensions in SUPPORTED_EXTENSIONS.values():
            all_extensions.extend(extensions)
        
        media_files = []
        
        # Count total files first
        self.total_files = sum(1 for _ in self.source_dir.rglob('*') 
                              if _.is_file() and _.suffix.lower() in all_extensions)
        
        # Then collect the files
        for file_path in self.source_dir.rglob('*'):
            if self.stop_requested:
                break
                
            if file_path.is_file() and file_path.suffix.lower() in all_extensions:
                self.current_file = str(file_path)
                media_files.append(file_path)
                
        return media_files
    
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
                    media_file = MediaFile(file_path)
                    
                    # Generate destination path
                    rel_path = media_file.get_formatted_path(self.template)
                    dest_path = self.output_dir / rel_path
                    
                    # Create destination directory if it doesn't exist
                    os.makedirs(dest_path.parent, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(file_path, dest_path)
                    logger.info(f"Copied {file_path} to {dest_path}")
                    
                    # Update progress
                    self.files_processed += 1
                    if callback:
                        callback(self.files_processed, self.total_files, str(file_path))
                        
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
            
            logger.info(f"Organization complete. Processed {self.files_processed} files.")
            
        except Exception as e:
            logger.error(f"Error during organization: {e}")
        
        finally:
            self.is_running = False
            if callback:
                callback(self.files_processed, self.total_files, "Complete")
    
    def stop(self):
        """Stop the organization process."""
        self.stop_requested = True


class MediaOrganizerGUI:
    """GUI for the Media Organizer application."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Media Organizer")
        self.root.geometry("800x700")  # Increased height to accommodate extension checkboxes
        self.root.minsize(800, 700)
        
        # Set up the organizer
        self.organizer = MediaOrganizer()
        
        # Create variables for extension filters
        self.extension_vars = {
            'audio': {},
            'video': {},
            'image': {}
        }
        
        # Config file path
        self.config_file = Path.home() / '.media_organizer_config.json'
        
        # Always enable auto-preview
        self.auto_preview_enabled = True
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the widgets
        self._create_widgets()
        
        # Load saved settings
        self._load_settings()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Initialize Git repository for the project
        self._init_git_repo()
        
        # Log startup
        logger.info("Media Organizer started")
    
    def _create_widgets(self):
        """Create the GUI widgets."""
        # Source directory selection
        source_frame = ttk.LabelFrame(self.main_frame, text="Source Directory", padding=10)
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_entry = ttk.Entry(source_frame)
        self.source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        source_button = ttk.Button(source_frame, text="Browse...", command=self._browse_source)
        source_button.pack(side=tk.RIGHT)
        
        # Extension filters
        extensions_frame = ttk.LabelFrame(self.main_frame, text="File Type Filters", padding=10)
        extensions_frame.pack(fill=tk.X, pady=5)
        
        # Create a frame for each file type category
        file_types_frame = ttk.Frame(extensions_frame)
        file_types_frame.pack(fill=tk.X, pady=5)
        
        # Audio extensions
        audio_frame = ttk.LabelFrame(file_types_frame, text="Audio")
        audio_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create "Select All" checkbox for audio
        self.audio_all_var = tk.BooleanVar(value=True)
        audio_all_cb = ttk.Checkbutton(
            audio_frame, 
            text="All Audio", 
            variable=self.audio_all_var,
            command=lambda: self._toggle_all_extensions('audio')
        )
        audio_all_cb.pack(anchor=tk.W)
        
        # Create individual checkboxes for audio extensions
        audio_extensions_frame = ttk.Frame(audio_frame)
        audio_extensions_frame.pack(fill=tk.X, padx=10)
        
        for i, ext in enumerate(SUPPORTED_EXTENSIONS['audio']):
            ext_name = ext.lstrip('.')
            var = tk.BooleanVar(value=True)
            self.extension_vars['audio'][ext] = var
            cb = ttk.Checkbutton(
                audio_extensions_frame, 
                text=ext_name, 
                variable=var,
                command=self._update_extension_selection
            )
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=5)
        
        # Video extensions
        video_frame = ttk.LabelFrame(file_types_frame, text="Video")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create "Select All" checkbox for video
        self.video_all_var = tk.BooleanVar(value=True)
        video_all_cb = ttk.Checkbutton(
            video_frame, 
            text="All Video", 
            variable=self.video_all_var,
            command=lambda: self._toggle_all_extensions('video')
        )
        video_all_cb.pack(anchor=tk.W)
        
        # Create individual checkboxes for video extensions
        video_extensions_frame = ttk.Frame(video_frame)
        video_extensions_frame.pack(fill=tk.X, padx=10)
        
        for i, ext in enumerate(SUPPORTED_EXTENSIONS['video']):
            ext_name = ext.lstrip('.')
            var = tk.BooleanVar(value=True)
            self.extension_vars['video'][ext] = var
            cb = ttk.Checkbutton(
                video_extensions_frame, 
                text=ext_name, 
                variable=var,
                command=self._update_extension_selection
            )
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=5)
        
        # Image extensions
        image_frame = ttk.LabelFrame(file_types_frame, text="Image")
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create "Select All" checkbox for image
        self.image_all_var = tk.BooleanVar(value=True)
        image_all_cb = ttk.Checkbutton(
            image_frame, 
            text="All Images", 
            variable=self.image_all_var,
            command=lambda: self._toggle_all_extensions('image')
        )
        image_all_cb.pack(anchor=tk.W)
        
        # Create individual checkboxes for image extensions
        image_extensions_frame = ttk.Frame(image_frame)
        image_extensions_frame.pack(fill=tk.X, padx=10)
        
        for i, ext in enumerate(SUPPORTED_EXTENSIONS['image']):
            ext_name = ext.lstrip('.')
            var = tk.BooleanVar(value=True)
            self.extension_vars['image'][ext] = var
            cb = ttk.Checkbutton(
                image_extensions_frame, 
                text=ext_name, 
                variable=var,
                command=self._update_extension_selection
            )
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=5)
        
        # Output directory selection
        output_frame = ttk.LabelFrame(self.main_frame, text="Output Directory", padding=10)
        output_frame.pack(fill=tk.X, pady=5)
        
        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        output_button = ttk.Button(output_frame, text="Browse...", command=self._browse_output)
        output_button.pack(side=tk.RIGHT)
        
        # Template configuration
        template_frame = ttk.LabelFrame(self.main_frame, text="Organization Template", padding=10)
        template_frame.pack(fill=tk.X, pady=5)
        
        template_header_frame = ttk.Frame(template_frame)
        template_header_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(template_header_frame, text="Use {placeholders} for metadata fields:").pack(side=tk.LEFT)
        
        # Help button for placeholders
        help_button = ttk.Button(template_header_frame, text="Placeholders Help", command=self._show_placeholders_help)
        help_button.pack(side=tk.RIGHT)
        
        self.template_var = tk.StringVar(value=self.organizer.template)
        self.template_var.trace_add("write", self._on_template_change)
        
        self.template_entry = ttk.Entry(template_frame, textvariable=self.template_var)
        self.template_entry.pack(fill=tk.X, pady=5)
        
        template_help = ttk.Label(template_frame, text="Examples: {file_type}/{artist}/{album}/{filename}, Music/{year}/{artist} - {title}")
        template_help.pack(anchor=tk.W)
        
        # Template buttons
        template_buttons = ttk.Frame(template_frame)
        template_buttons.pack(fill=tk.X, pady=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(self.main_frame, text="Preview (Original → New Path)", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Preview list with scrollbar
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)
        
        # Use a monospace font for better readability of paths
        preview_font = ('Courier', 10)
        self.preview_list = tk.Text(preview_container, height=8, wrap=tk.NONE, font=preview_font)
        self.preview_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        preview_scrollbar_y = ttk.Scrollbar(preview_container, orient="vertical", command=self.preview_list.yview)
        preview_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        preview_scrollbar_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview_list.xview)
        preview_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.preview_list.config(yscrollcommand=preview_scrollbar_y.set, xscrollcommand=preview_scrollbar_x.set)
        self.preview_list.configure(state='disabled')
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.main_frame, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W)
        
        self.file_var = tk.StringVar(value="")
        file_label = ttk.Label(progress_frame, textvariable=self.file_var)
        file_label.pack(anchor=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(buttons_frame, text="Start Organization", command=self._start_organization)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="Stop", command=self._stop_organization, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Add reset settings button
        reset_button = ttk.Button(buttons_frame, text="Reset Settings", command=self._reset_settings)
        reset_button.pack(side=tk.RIGHT, padx=5)
        
        # Add save settings button
        save_button = ttk.Button(buttons_frame, text="Save Settings", command=self._save_settings_manual)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(self.main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Configure logging to text widget
        self._setup_text_logging()
    
    def _setup_text_logging(self):
        """Set up logging to the text widget."""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                
                def append():
                    self.text_widget.configure(state='normal')
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.configure(state='disabled')
                
                # Schedule the append operation on the GUI thread
                self.text_widget.after(0, append)
        
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(text_handler)
        
        # Disable editing
        self.log_text.configure(state='disabled')
    
    def _browse_source(self):
        """Browse for source directory."""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, directory)
            # Clear preview when source changes
            self._clear_preview()
            # Auto-save settings
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
            # Auto-save settings
            self._save_settings()
            # Auto-generate preview
            self._auto_generate_preview()
            
    def _clear_preview(self):
        """Clear the preview list."""
        self.preview_list.configure(state='normal')
        self.preview_list.delete(1.0, tk.END)
        self.preview_list.configure(state='disabled')
    
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
        # Auto-save settings
        self._save_settings()
        # Auto-generate preview
        self._auto_generate_preview()
    
    def _update_extension_selection(self):
        """Update the 'All' checkboxes based on individual selections."""
        for file_type in ['audio', 'video', 'image']:
            all_selected = all(var.get() for var in self.extension_vars[file_type].values())
            getattr(self, f"{file_type}_all_var").set(all_selected)
        # Auto-save settings
        self._save_settings()
        # Auto-generate preview
        self._auto_generate_preview()
    
    def _get_selected_extensions(self):
        """Get a list of all selected file extensions."""
        selected_extensions = []
        for file_type, extensions in self.extension_vars.items():
            for ext, var in extensions.items():
                if var.get():
                    selected_extensions.append(ext)
        return selected_extensions
    
    def _generate_preview(self):
        """Generate a preview of how files will be organized."""
        source_dir = self.source_entry.get().strip()
        output_dir = self.output_entry.get().strip()
        template = self.template_var.get().strip()
        
        if not source_dir:
            messagebox.showerror("Error", "Please select a source directory.")
            return
            
        if not template:
            messagebox.showerror("Error", "Please provide an organization template.")
            return
            
        # Clear previous preview
        self._clear_preview()
        
        try:
            # Configure organizer for preview
            self.organizer.set_source_dir(source_dir)
            if output_dir:
                self.organizer.set_output_dir(output_dir)
            self.organizer.set_template(template)
            
            # Find media files (limit to 100 for preview)
            self.status_var.set("Generating preview...")
            self.root.update_idletasks()
            
            # Get selected extensions
            selected_extensions = self._get_selected_extensions()
            if not selected_extensions:
                messagebox.showinfo("Info", "No file types selected. Please select at least one file type.")
                self.status_var.set("Ready")
                return
                
            # Find up to 100 files for preview
            source_path = Path(source_dir)
            preview_files = []
            count = 0
            
            for file_path in source_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in selected_extensions:
                    preview_files.append(file_path)
                    count += 1
                    if count >= 100:  # Limit to 100 files for preview
                        break
            
            # Generate preview for each file
            self.preview_list.configure(state='normal')
            
            # Add header
            self.preview_list.insert(tk.END, "Original File (relative to source) → New Path (relative to output)\n")
            self.preview_list.insert(tk.END, "-" * 80 + "\n\n")
            
            for file_path in preview_files:
                try:
                    # Extract metadata
                    media_file = MediaFile(file_path)
                    
                    # Generate destination path
                    rel_path = media_file.get_formatted_path(template)
                    
                    # Get relative paths for display
                    try:
                        # Get relative path from source directory
                        original_rel_path = file_path.relative_to(source_path)
                        
                        # Format for display
                        self.preview_list.insert(tk.END, f"{original_rel_path} → {rel_path}\n")
                    except ValueError:
                        # If file is not relative to source (shouldn't happen), show full path
                        self.preview_list.insert(tk.END, f"{file_path} → {rel_path}\n")
                    
                except Exception as e:
                    logger.error(f"Error generating preview for {file_path}: {e}")
            
            self.preview_list.configure(state='disabled')
            
            if count == 0:
                self.status_var.set("No media files found in the source directory.")
            else:
                self.status_var.set(f"Preview generated for {count} files.")
                
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")
            self.status_var.set("Preview generation failed.")
    
    def _start_organization(self):
        """Start the organization process."""
        # Validate inputs
        source_dir = self.source_entry.get().strip()
        output_dir = self.output_entry.get().strip()
        template = self.template_var.get().strip()
        
        if not source_dir or not output_dir:
            messagebox.showerror("Error", "Please select both source and output directories.")
            return
        
        if not template:
            messagebox.showerror("Error", "Please provide an organization template.")
            return
        
        if not os.path.exists(source_dir):
            messagebox.showerror("Error", "Source directory does not exist.")
            return
        
        # Get selected extensions
        selected_extensions = self._get_selected_extensions()
        if not selected_extensions:
            messagebox.showinfo("Info", "No file types selected. Please select at least one file type.")
            return
        
        # Configure organizer
        self.organizer.set_source_dir(source_dir)
        self.organizer.set_output_dir(output_dir)
        self.organizer.set_template(template)
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.status_var.set("Starting...")
        self.file_var.set("")
        
        # Clear preview
        self._clear_preview()
        
        # Start organization in a separate thread
        threading.Thread(
            target=self._run_organization_with_filters, 
            args=(selected_extensions,), 
            daemon=True
        ).start()
        
        logger.info(f"Starting organization from {source_dir} to {output_dir}")
        logger.info(f"Using template: {template}")
        logger.info(f"Selected extensions: {', '.join(selected_extensions)}")
    
    def _run_organization_with_filters(self, selected_extensions):
        """Run the organization process with the selected file extensions."""
        try:
            # Find all media files
            source_path = Path(self.organizer.source_dir)
            output_path = Path(self.organizer.output_dir)
            template = self.organizer.template
            
            # Count total files first
            total_files = sum(1 for _ in source_path.rglob('*') 
                             if _.is_file() and _.suffix.lower() in selected_extensions)
            
            # Process files
            processed = 0
            
            for file_path in source_path.rglob('*'):
                if self.organizer.stop_requested:
                    logger.info("Organization stopped by user")
                    break
                    
                if file_path.is_file() and file_path.suffix.lower() in selected_extensions:
                    try:
                        # Extract metadata
                        media_file = MediaFile(file_path)
                        
                        # Generate destination path
                        rel_path = media_file.get_formatted_path(template)
                        dest_path = output_path / rel_path
                        
                        # Create destination directory if it doesn't exist
                        os.makedirs(dest_path.parent, exist_ok=True)
                        
                        # Copy the file
                        shutil.copy2(file_path, dest_path)
                        logger.info(f"Copied {file_path} to {dest_path}")
                        
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
                    
                    # Update progress
                    processed += 1
                    self._update_progress(processed, total_files, str(file_path))
            
            # Complete
            self._update_progress(processed, total_files, "Complete")
            logger.info(f"Organization complete. Processed {processed} files.")
            
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
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Show completion message
        messagebox.showinfo("Complete", f"Organization complete!\n\nProcessed {self.organizer.files_processed} files.")

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
                'source_dir': self.source_entry.get().strip(),
                'output_dir': self.output_entry.get().strip(),
                'template': self.template_var.get().strip(),
                'extensions': {
                    'audio': {ext: var.get() for ext, var in self.extension_vars['audio'].items()},
                    'video': {ext: var.get() for ext, var in self.extension_vars['video'].items()},
                    'image': {ext: var.get() for ext, var in self.extension_vars['image'].items()}
                }
            }
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(settings, f)
                
            logger.info(f"Settings saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def _load_settings(self):
        """Load user settings from the configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                
                # Apply settings
                if 'source_dir' in settings and settings['source_dir']:
                    self.source_entry.delete(0, tk.END)
                    self.source_entry.insert(0, settings['source_dir'])
                
                if 'output_dir' in settings and settings['output_dir']:
                    self.output_entry.delete(0, tk.END)
                    self.output_entry.insert(0, settings['output_dir'])
                
                if 'template' in settings and settings['template']:
                    self.template_var.set(settings['template'])
                
                # Apply extension selections
                if 'extensions' in settings:
                    for file_type in ['audio', 'video', 'image']:
                        if file_type in settings['extensions']:
                            for ext, value in settings['extensions'][file_type].items():
                                if ext in self.extension_vars[file_type]:
                                    self.extension_vars[file_type][ext].set(value)
                
                # Update "All" checkboxes
                self._update_extension_selection()
                
                logger.info(f"Settings loaded from {self.config_file}")
                
                # Generate initial preview if auto-preview is enabled
                self._auto_generate_preview()
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def _reset_settings(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            try:
                # Clear entries
                self.source_entry.delete(0, tk.END)
                self.output_entry.delete(0, tk.END)
                self.template_var.set("{file_type}/{artist}/{album}/{filename}")
                
                # Reset extension checkboxes to checked
                for file_type in ['audio', 'video', 'image']:
                    getattr(self, f"{file_type}_all_var").set(True)
                    self._toggle_all_extensions(file_type)
                
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
        messagebox.showinfo("Settings Saved", f"Your settings have been saved to:\n{self.config_file}")

    def _on_template_change(self, *args):
        """Handle template change event."""
        # Auto-save settings after a short delay
        # This prevents saving on every keystroke
        if hasattr(self, '_template_timer'):
            self.root.after_cancel(self._template_timer)
        self._template_timer = self.root.after(1000, self._save_settings)
        
        # Auto-generate preview after a short delay
        # This prevents generating preview on every keystroke
        if hasattr(self, '_preview_timer'):
            self.root.after_cancel(self._preview_timer)
        self._preview_timer = self.root.after(1500, self._auto_generate_preview)

    def _auto_generate_preview(self):
        """Automatically generate preview if enabled and source directory exists."""
        if self.auto_preview_enabled:
            source_dir = self.source_entry.get().strip()
            if source_dir and os.path.exists(source_dir):
                # Cancel any pending preview generation
                if hasattr(self, '_preview_timer'):
                    self.root.after_cancel(self._preview_timer)
                # Schedule preview generation after a short delay
                self._preview_timer = self.root.after(500, self._generate_preview)

    def _show_placeholders_help(self):
        """Show a modal dialog with information about available placeholders."""
        # Create a new top-level window
        help_window = tk.Toplevel(self.root)
        help_window.title("Available Placeholders")
        help_window.geometry("600x400")
        help_window.minsize(600, 400)
        help_window.transient(self.root)  # Make it a modal dialog
        help_window.grab_set()  # Make it modal
        
        # Center the window
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Create a frame for the content
        content_frame = ttk.Frame(help_window, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(content_frame, text="Available Placeholders", font=("TkDefaultFont", 14, "bold"))
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
            ("{file_type}", "Type of file (audio, video, image)"),
            ("{size}", "File size in bytes"),
            ("{creation_date}", "File creation date (YYYY-MM-DD)")
        ]
        
        for i, (placeholder, description) in enumerate(common_placeholders):
            ttk.Label(common_frame, text=placeholder, width=15, anchor=tk.W).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(common_frame, text=description, anchor=tk.W).grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
        
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
            ("{bitrate}", "Audio bitrate")
        ]
        
        for i, (placeholder, description) in enumerate(audio_placeholders):
            ttk.Label(audio_frame, text=placeholder, width=15, anchor=tk.W).grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=5, pady=2)
            ttk.Label(audio_frame, text=description, anchor=tk.W).grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=2)
        
        # Image placeholders
        image_frame = ttk.LabelFrame(categories_frame, text="Image", padding=10)
        image_frame.pack(fill=tk.X, pady=5)
        
        image_placeholders = [
            ("{width}", "Image width in pixels"),
            ("{height}", "Image height in pixels"),
            ("{format}", "Image format (e.g., JPEG, PNG)"),
            ("{camera_make}", "Camera manufacturer"),
            ("{camera_model}", "Camera model"),
            ("{date_taken}", "Date when the photo was taken")
        ]
        
        for i, (placeholder, description) in enumerate(image_placeholders):
            ttk.Label(image_frame, text=placeholder, width=15, anchor=tk.W).grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=5, pady=2)
            ttk.Label(image_frame, text=description, anchor=tk.W).grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=2)
        
        # Example usage
        example_frame = ttk.LabelFrame(content_frame, text="Example Templates", padding=10)
        example_frame.pack(fill=tk.X, pady=5)
        
        examples = [
            ("{file_type}/{artist}/{album}/{filename}", "Organizes by file type, then artist, then album"),
            ("Music/{year}/{artist} - {title}.{extension}", "Organizes music by year, then artist-title"),
            ("{file_type}/{creation_date}/{filename}", "Organizes by file type, then creation date")
        ]
        
        for i, (template, description) in enumerate(examples):
            ttk.Label(example_frame, text=template, wraplength=250, anchor=tk.W).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(example_frame, text=description, wraplength=300, anchor=tk.W).grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Close button
        close_button = ttk.Button(content_frame, text="Close", command=help_window.destroy)
        close_button.pack(pady=20)

    def _init_git_repo(self):
        """Initialize Git repository for the project if it doesn't exist."""
        try:
            # Check if we're in a Git repository
            project_dir = Path(__file__).parent.absolute()
            git_dir = project_dir / '.git'
            
            if not git_dir.exists():
                # Initialize Git repository
                result = self._run_git_command(['init'], cwd=str(project_dir))
                if result and result.returncode == 0:
                    logger.info(f"Git repository initialized for the project at {project_dir}")
                    
                    # Create initial .gitignore file
                    gitignore_path = project_dir / '.gitignore'
                    if not gitignore_path.exists():
                        with open(gitignore_path, 'w') as f:
                            f.write("# Python\n")
                            f.write("__pycache__/\n*.py[cod]\n*$py.class\n")
                            f.write("*.so\n.Python\nenv/\nbuild/\ndevelop-eggs/\ndist/\n")
                            f.write("downloads/\neggs/\n.eggs/\nlib/\nlib64/\nparts/\nsdist/\n")
                            f.write("var/\n*.egg-info/\n.installed.cfg\n*.egg\n")
                            f.write("\n# Virtual environments\nvenv/\nENV/\n.env\n")
                            f.write("\n# Logs\n*.log\n")
                            f.write("\n# User settings\n.media_organizer_config.json\n")
                            f.write("\n# System files\n.DS_Store\nThumbs.db\n")
                    
                    # Add files to Git
                    self._run_git_command(['add', '.'], cwd=str(project_dir))
                    
                    # Try to set user config if not already set
                    try:
                        # Check if user config exists
                        user_name = self._run_git_command(['config', 'user.name'], cwd=str(project_dir))
                        user_email = self._run_git_command(['config', 'user.email'], cwd=str(project_dir))
                        
                        if not (user_name and user_name.stdout.strip()) or not (user_email and user_email.stdout.strip()):
                            # Try to get system username
                            import getpass
                            username = getpass.getuser()
                            
                            # Set default Git config
                            self._run_git_command(['config', 'user.email', f'{username}@example.com'], cwd=str(project_dir))
                            self._run_git_command(['config', 'user.name', f'{username.capitalize()}'], cwd=str(project_dir))
                    except Exception as e:
                        logger.warning(f"Could not set Git user config: {e}")
                    
                    # Initial commit
                    self._run_git_command(['commit', '-m', 'Initial commit: Media Organizer project'], cwd=str(project_dir))
                    
                    logger.info("Project initialized with Git")
                else:
                    logger.error(f"Failed to initialize Git repository: {result.stderr if result else 'Unknown error'}")
            else:
                logger.info(f"Using existing Git repository at {project_dir}")
        except Exception as e:
            logger.error(f"Error initializing Git repository: {e}")
    
    def _run_git_command(self, args, cwd=None):
        """Run a Git command and return the result."""
        try:
            result = subprocess.run(['git'] + args, cwd=cwd, capture_output=True, text=True)
            return result
        except Exception as e:
            logger.error(f"Error running Git command: {e}")
            return None


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = MediaOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 