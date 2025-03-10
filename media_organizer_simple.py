#!/usr/bin/env python3
"""
Media Organizer - A tool to organize media files based on metadata.
Simplified version for testing.
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
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
from PIL import Image, ImageTk

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
        """Determine the file type based on extension."""
        ext = self.file_path.suffix.lower()
        for file_type, extensions in SUPPORTED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return "unknown"
    
    def extract_metadata(self):
        """Extract metadata from the file."""
        # Basic file metadata
        self.metadata['filename'] = self.file_path.stem
        self.metadata['extension'] = self.file_path.suffix.lstrip('.')
        self.metadata['file_type'] = self.file_type
        self.metadata['size'] = os.path.getsize(self.file_path)
        self.metadata['creation_date'] = datetime.fromtimestamp(
            os.path.getctime(self.file_path)
        ).strftime('%Y-%m-%d')
        
        # Extract specific metadata based on file type
        try:
            if self.file_type == 'audio':
                self._extract_audio_metadata()
            elif self.file_type == 'image':
                self._extract_image_metadata()
            elif self.file_type == 'video':
                self._extract_video_metadata()
        except Exception as e:
            logger.error(f"Error extracting metadata from {self.file_path}: {e}")
    
    def _extract_audio_metadata(self):
        """Extract metadata from audio files."""
        # Default values
        self.metadata.update({
            'title': 'Unknown',
            'artist': 'Unknown',
            'album': 'Unknown',
            'year': 'Unknown',
            'genre': 'Unknown',
            'track': 'Unknown',
            'duration': 'Unknown',
            'bitrate': 'Unknown'
        })
        
        try:
            ext = self.file_path.suffix.lower()
            
            if ext == '.mp3':
                audio = MP3(self.file_path)
                if audio.tags:
                    if 'TIT2' in audio.tags:
                        self.metadata['title'] = str(audio.tags['TIT2'])
                    if 'TPE1' in audio.tags:
                        self.metadata['artist'] = str(audio.tags['TPE1'])
                    if 'TALB' in audio.tags:
                        self.metadata['album'] = str(audio.tags['TALB'])
                    if 'TDRC' in audio.tags:
                        self.metadata['year'] = str(audio.tags['TDRC'])
                    if 'TCON' in audio.tags:
                        self.metadata['genre'] = str(audio.tags['TCON'])
                    if 'TRCK' in audio.tags:
                        self.metadata['track'] = str(audio.tags['TRCK'])
                
                if audio.info:
                    self.metadata['duration'] = str(int(audio.info.length // 60)) + ':' + str(int(audio.info.length % 60)).zfill(2)
                    self.metadata['bitrate'] = str(audio.info.bitrate // 1000) + ' kbps'
            
            elif ext == '.flac':
                audio = FLAC(self.file_path)
                if 'title' in audio:
                    self.metadata['title'] = audio['title'][0]
                if 'artist' in audio:
                    self.metadata['artist'] = audio['artist'][0]
                if 'album' in audio:
                    self.metadata['album'] = audio['album'][0]
                if 'date' in audio:
                    self.metadata['year'] = audio['date'][0]
                if 'genre' in audio:
                    self.metadata['genre'] = audio['genre'][0]
                if 'tracknumber' in audio:
                    self.metadata['track'] = audio['tracknumber'][0]
                
                if audio.info:
                    self.metadata['duration'] = str(int(audio.info.length // 60)) + ':' + str(int(audio.info.length % 60)).zfill(2)
                    self.metadata['bitrate'] = str(audio.info.bits_per_sample) + ' bit'
            
            elif ext == '.m4a':
                audio = MP4(self.file_path)
                if '\xa9nam' in audio:
                    self.metadata['title'] = audio['\xa9nam'][0]
                if '\xa9ART' in audio:
                    self.metadata['artist'] = audio['\xa9ART'][0]
                if '\xa9alb' in audio:
                    self.metadata['album'] = audio['\xa9alb'][0]
                if '\xa9day' in audio:
                    self.metadata['year'] = audio['\xa9day'][0]
                if '\xa9gen' in audio:
                    self.metadata['genre'] = audio['\xa9gen'][0]
                if 'trkn' in audio:
                    self.metadata['track'] = str(audio['trkn'][0][0])
                
                if audio.info:
                    self.metadata['duration'] = str(int(audio.info.length // 60)) + ':' + str(int(audio.info.length % 60)).zfill(2)
                    self.metadata['bitrate'] = str(audio.info.bitrate // 1000) + ' kbps'
        
        except Exception as e:
            logger.error(f"Error extracting audio metadata from {self.file_path}: {e}")
    
    def _extract_image_metadata(self):
        """Extract metadata from image files."""
        # Default values
        self.metadata.update({
            'width': 'Unknown',
            'height': 'Unknown',
            'format': 'Unknown',
            'camera_make': 'Unknown',
            'camera_model': 'Unknown',
            'date_taken': 'Unknown'
        })
        
        try:
            with Image.open(self.file_path) as img:
                self.metadata['width'], self.metadata['height'] = img.size
                self.metadata['format'] = img.format
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        # EXIF tags
                        if 271 in exif:  # Make
                            self.metadata['camera_make'] = exif[271]
                        if 272 in exif:  # Model
                            self.metadata['camera_model'] = exif[272]
                        if 36867 in exif:  # DateTimeOriginal
                            self.metadata['date_taken'] = exif[36867]
        
        except Exception as e:
            logger.error(f"Error extracting image metadata from {self.file_path}: {e}")
    
    def _extract_video_metadata(self):
        """Extract metadata from video files."""
        # For now, we'll just use basic file metadata
        # In a real implementation, you might want to use a library like ffmpeg-python
        pass
    
    def get_formatted_path(self, template):
        """
        Format the destination path based on the template and metadata.
        
        Args:
            template: A string template with placeholders in curly braces
            
        Returns:
            A formatted path string
        """
        # Replace placeholders with metadata values
        formatted = template
        
        # Find all placeholders in the template
        placeholders = re.findall(r'\{([^}]+)\}', template)
        
        for placeholder in placeholders:
            value = self.metadata.get(placeholder, 'Unknown')
            
            # Clean the value for use in a file path
            if isinstance(value, str):
                # Replace characters that are problematic in file paths
                value = value.replace('/', '-').replace('\\', '-')
                value = value.replace(':', '-').replace('*', '-')
                value = value.replace('?', '-').replace('"', '-')
                value = value.replace('<', '-').replace('>', '-')
                value = value.replace('|', '-')
            
            formatted = formatted.replace('{' + placeholder + '}', str(value))
        
        # Add the original extension
        if not formatted.endswith(self.file_path.suffix):
            if '{extension}' not in template:
                formatted += self.file_path.suffix
        
        return formatted


class MediaOrganizer:
    """Class to organize media files based on metadata."""
    
    def __init__(self):
        """Initialize the organizer."""
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
            # Call callback one last time to update UI
            if callback:
                callback(self.files_processed, self.total_files, "")
    
    def stop(self):
        """Stop the organization process."""
        self.stop_requested = True


class MediaOrganizerGUI:
    """GUI for the Media Organizer application."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Media Organizer")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Set up the organizer
        self.organizer = MediaOrganizer()
        
        # Create variables
        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.template_var = tk.StringVar(value="{file_type}/{artist}/{album}/{filename}")
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.file_var = tk.StringVar()
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the form frame
        self.form_frame = ttk.LabelFrame(self.main_frame, text="Configuration", padding=10)
        self.form_frame.pack(fill=tk.X, pady=5)
        
        # Source directory
        ttk.Label(self.form_frame, text="Source Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.form_frame, textvariable=self.source_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5)
        ttk.Button(self.form_frame, text="Browse...", command=self._browse_source).grid(row=0, column=2, padx=5, pady=5)
        
        # Output directory
        ttk.Label(self.form_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.form_frame, textvariable=self.output_var, width=50).grid(row=1, column=1, sticky=tk.EW, pady=5)
        ttk.Button(self.form_frame, text="Browse...", command=self._browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        # Template
        ttk.Label(self.form_frame, text="Organization Template:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.form_frame, textvariable=self.template_var, width=50).grid(row=2, column=1, sticky=tk.EW, pady=5)
        ttk.Button(self.form_frame, text="Help", command=self._show_template_help).grid(row=2, column=2, padx=5, pady=5)
        
        # Configure grid
        self.form_frame.columnconfigure(1, weight=1)
        
        # Create the button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Start and stop buttons
        self.start_button = ttk.Button(self.button_frame, text="Start Organization", command=self._start_organization)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="Stop", command=self._stop_organization, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Create the progress frame
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="Progress", padding=10)
        self.progress_frame.pack(fill=tk.X, pady=5)
        
        # Status
        ttk.Label(self.progress_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(self.progress_frame, textvariable=self.status_var).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Progress bar
        ttk.Label(self.progress_frame, text="Progress:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # Current file
        ttk.Label(self.progress_frame, text="Current File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(self.progress_frame, textvariable=self.file_var, wraplength=600).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Configure grid
        self.progress_frame.columnconfigure(1, weight=1)
        
        # Create the log frame
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Log", padding=10)
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Log text
        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for log
        self.log_scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)
        
        # Redirect logging to the text widget
        self._setup_logging()
        
        logger.info("Media Organizer started")
    
    def _setup_logging(self):
        """Set up logging to the text widget."""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record) + '\n'
                self.text_widget.insert(tk.END, msg)
                self.text_widget.see(tk.END)
        
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(text_handler)
    
    def _browse_source(self):
        """Browse for source directory."""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_var.set(directory)
    
    def _browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_var.set(directory)
    
    def _show_template_help(self):
        """Show help for the organization template."""
        help_text = """
        Organization Templates:
        
        The application uses templates with placeholders to determine how files should be organized.
        Placeholders are enclosed in curly braces {} and will be replaced with the corresponding metadata value.
        
        Available Placeholders:
        
        Common: {filename}, {extension}, {file_type}, {size}, {creation_date}
        Audio: {title}, {artist}, {album}, {year}, {genre}, {track}, {duration}, {bitrate}
        Image: {width}, {height}, {format}, {camera_make}, {camera_model}, {date_taken}
        
        Example Templates:
        
        {file_type}/{artist}/{album}/{filename} - Organizes by file type, then artist, then album
        Music/{year}/{artist} - {title}.{extension} - Organizes music by year, then artist-title
        {file_type}/{creation_date}/{filename} - Organizes by file type, then creation date
        """
        messagebox.showinfo("Template Help", help_text)
    
    def _update_progress(self, files_processed, total_files, current_file):
        """Update the progress display."""
        if total_files > 0:
            progress = (files_processed / total_files) * 100
            self.progress_var.set(progress)
            self.status_var.set(f"Processing file {files_processed} of {total_files}")
            self.file_var.set(current_file)
        
        # If processing is complete
        if files_processed == total_files and not self.organizer.is_running:
            self._organization_complete()
        
        # Update the UI
        self.root.update_idletasks()
    
    def _start_organization(self):
        """Start the organization process."""
        source_dir = self.source_var.get()
        output_dir = self.output_var.get()
        template = self.template_var.get()
        
        if not source_dir or not output_dir:
            messagebox.showerror("Error", "Please select source and output directories.")
            return
        
        if not template:
            messagebox.showerror("Error", "Please provide an organization template.")
            return
        
        if not os.path.exists(source_dir):
            messagebox.showerror("Error", "Source directory does not exist.")
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
        
        # Start organization in a separate thread
        threading.Thread(target=self.organizer.organize_files, 
                         args=(self._update_progress,), 
                         daemon=True).start()
        
        logger.info(f"Starting organization from {source_dir} to {output_dir}")
        logger.info(f"Using template: {template}")
    
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


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = MediaOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 