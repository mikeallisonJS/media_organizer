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

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    "audio": [".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav"],
    "video": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
    "ebook": [".epub", ".pdf", ".mobi", ".azw", ".azw3", ".fb2"],
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
        return "unknown"
    
    def extract_metadata(self):
        """Extract metadata from the media file."""
        try:
            if self.file_type == "audio":
                self._extract_audio_metadata()
            elif self.file_type == "video":
                self._extract_video_metadata()
            elif self.file_type == "image":
                self._extract_image_metadata()
            elif self.file_type == "ebook":
                self._extract_ebook_metadata()
            
            # Add file information
            self.metadata["filename"] = self.file_path.name
            self.metadata["extension"] = self.file_path.suffix.lower()[1:]  # Remove the dot
            self.metadata["size"] = self.file_path.stat().st_size

            # Extract creation date information
            creation_time = datetime.fromtimestamp(self.file_path.stat().st_ctime)
            self.metadata["creation_date"] = creation_time.strftime("%Y-%m-%d")
            self.metadata["creation_year"] = creation_time.strftime("%Y")
            self.metadata["creation_month"] = creation_time.strftime("%m")  # Numeric month (01-12)
            self.metadata["creation_month_name"] = creation_time.strftime("%B")  # Full month name
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {self.file_path}: {e}")
    
    def _extract_audio_metadata(self):
        """Extract metadata from audio files."""
        ext = self.file_path.suffix.lower()

        # Initialize default metadata values
        self.metadata.update(
            {
                "title": self.file_path.stem,
                "artist": "Unknown",
                "album": "Unknown",
                "year": "Unknown",
                "genre": "Unknown",
                "track": "Unknown",
                "duration": "Unknown",
                "bitrate": "Unknown",
                "sample_rate": "Unknown",
            }
        )

        try:
            # MP3 files
            if ext == ".mp3":
                try:
                    audio = MP3(self.file_path)
                    if audio.tags:
                        id3 = ID3(self.file_path)
                        if "TIT2" in id3:
                            self.metadata["title"] = str(id3["TIT2"])
                        if "TPE1" in id3:
                            self.metadata["artist"] = str(id3["TPE1"])
                        if "TALB" in id3:
                            self.metadata["album"] = str(id3["TALB"])
                        if "TDRC" in id3:
                            self.metadata["year"] = str(id3["TDRC"])[:4]  # Extract just the year
                        if "TCON" in id3:
                            self.metadata["genre"] = str(id3["TCON"])
                        if "TRCK" in id3:
                            self.metadata["track"] = str(id3["TRCK"])

                        # Add audio-specific information
                        if hasattr(audio, "info"):
                            duration_seconds = int(audio.info.length)
                            minutes = duration_seconds // 60
                            seconds = duration_seconds % 60
                            self.metadata["duration"] = f"{minutes}:{seconds:02d}"

                            if hasattr(audio.info, "bitrate"):
                                self.metadata["bitrate"] = f"{audio.info.bitrate // 1000} kbps"
                            if hasattr(audio.info, "sample_rate"):
                                self.metadata["sample_rate"] = f"{audio.info.sample_rate // 1000} kHz"
                except Exception as e:
                    logger.error(f"Error extracting MP3 metadata from {self.file_path}: {e}")

            # FLAC files
            elif ext == ".flac":
                try:
                    audio = FLAC(self.file_path)
                    if "title" in audio:
                        self.metadata["title"] = ", ".join(audio["title"])
                    if "artist" in audio:
                        self.metadata["artist"] = ", ".join(audio["artist"])
                    if "album" in audio:
                        self.metadata["album"] = ", ".join(audio["album"])
                    if "date" in audio:
                        date_value = ", ".join(audio["date"])
                        # Try to extract just the year
                        year_match = re.search(r"\d{4}", date_value)
                        if year_match:
                            self.metadata["year"] = year_match.group(0)
                        else:
                            self.metadata["year"] = date_value
                    if "genre" in audio:
                        self.metadata["genre"] = ", ".join(audio["genre"])
                    if "tracknumber" in audio:
                        self.metadata["track"] = ", ".join(audio["tracknumber"])

                    # Add audio-specific information
                    if hasattr(audio, "info"):
                        duration_seconds = int(audio.info.length)
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        self.metadata["duration"] = f"{minutes}:{seconds:02d}"

                        if hasattr(audio.info, "bitrate"):
                            self.metadata["bitrate"] = f"{audio.info.bitrate // 1000} kbps"
                        if hasattr(audio.info, "sample_rate"):
                            self.metadata["sample_rate"] = f"{audio.info.sample_rate // 1000} kHz"
                except Exception as e:
                    logger.error(f"Error extracting FLAC metadata from {self.file_path}: {e}")

            # M4A/AAC files
            elif ext in [".m4a", ".aac"]:
                try:
                    audio = MP4(self.file_path)
                    if "\xa9nam" in audio:
                        self.metadata["title"] = ", ".join(audio["\xa9nam"])
                    if "\xa9ART" in audio:
                        self.metadata["artist"] = ", ".join(audio["\xa9ART"])
                    if "\xa9alb" in audio:
                        self.metadata["album"] = ", ".join(audio["\xa9alb"])
                    if "\xa9day" in audio:
                        date_value = ", ".join(audio["\xa9day"])
                        # Try to extract just the year
                        year_match = re.search(r"\d{4}", date_value)
                        if year_match:
                            self.metadata["year"] = year_match.group(0)
                        else:
                            self.metadata["year"] = date_value
                    if "\xa9gen" in audio:
                        self.metadata["genre"] = ", ".join(audio["\xa9gen"])
                    if "trkn" in audio:
                        track_tuple = audio["trkn"][0]
                        self.metadata["track"] = (
                            f"{track_tuple[0]}/{track_tuple[1]}"
                            if len(track_tuple) > 1
                            else str(track_tuple[0])
                        )
                
                    # Add audio-specific information
                    if hasattr(audio, "info"):
                        duration_seconds = int(audio.info.length)
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        self.metadata["duration"] = f"{minutes}:{seconds:02d}"

                        if hasattr(audio.info, "bitrate"):
                            self.metadata["bitrate"] = f"{audio.info.bitrate // 1000} kbps"
                        if hasattr(audio.info, "sample_rate"):
                            self.metadata["sample_rate"] = f"{audio.info.sample_rate // 1000} kHz"
                except Exception as e:
                    logger.error(f"Error extracting M4A/AAC metadata from {self.file_path}: {e}")

            # OGG files
            elif ext == ".ogg":
                try:
                    from mutagen.oggvorbis import OggVorbis

                    audio = OggVorbis(self.file_path)

                    if "title" in audio:
                        self.metadata["title"] = ", ".join(audio["title"])
                    if "artist" in audio:
                        self.metadata["artist"] = ", ".join(audio["artist"])
                    if "album" in audio:
                        self.metadata["album"] = ", ".join(audio["album"])
                    if "date" in audio:
                        date_value = ", ".join(audio["date"])
                        # Try to extract just the year
                        year_match = re.search(r"\d{4}", date_value)
                        if year_match:
                            self.metadata["year"] = year_match.group(0)
                        else:
                            self.metadata["year"] = date_value
                    if "genre" in audio:
                        self.metadata["genre"] = ", ".join(audio["genre"])
                    if "tracknumber" in audio:
                        self.metadata["track"] = ", ".join(audio["tracknumber"])

                    # Add audio-specific information
                    if hasattr(audio, "info"):
                        duration_seconds = int(audio.info.length)
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        self.metadata["duration"] = f"{minutes}:{seconds:02d}"

                        if hasattr(audio.info, "bitrate"):
                            self.metadata["bitrate"] = f"{audio.info.bitrate // 1000} kbps"
                        if hasattr(audio.info, "sample_rate"):
                            self.metadata["sample_rate"] = f"{audio.info.sample_rate // 1000} kHz"
                except Exception as e:
                    logger.error(f"Error extracting OGG metadata from {self.file_path}: {e}")

            # WAV files
            elif ext == ".wav":
                try:
                    from mutagen.wave import WAVE

                    audio = WAVE(self.file_path)

                    # WAV files typically have limited metadata
                    # Add audio-specific information
                    if hasattr(audio, "info"):
                        duration_seconds = int(audio.info.length)
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        self.metadata["duration"] = f"{minutes}:{seconds:02d}"

                        if hasattr(audio.info, "bitrate"):
                            self.metadata["bitrate"] = f"{audio.info.bitrate // 1000} kbps"
                        if hasattr(audio.info, "sample_rate"):
                            self.metadata["sample_rate"] = f"{audio.info.sample_rate // 1000} kHz"
                except Exception as e:
                    logger.error(f"Error extracting WAV metadata from {self.file_path}: {e}")

            # Generic fallback for other audio formats
            else:
                try:
                    audio = mutagen.File(self.file_path)
                    if audio is not None:
                        # Try to extract common metadata fields
                        for key in audio:
                            lower_key = key.lower()
                            if "title" in lower_key:
                                self.metadata["title"] = str(audio[key][0])
                            elif "artist" in lower_key:
                                self.metadata["artist"] = str(audio[key][0])
                            elif "album" in lower_key:
                                self.metadata["album"] = str(audio[key][0])
                            elif "date" in lower_key or "year" in lower_key:
                                date_value = str(audio[key][0])
                                # Try to extract just the year
                                year_match = re.search(r"\d{4}", date_value)
                                if year_match:
                                    self.metadata["year"] = year_match.group(0)
                                else:
                                    self.metadata["year"] = date_value
                            elif "genre" in lower_key:
                                self.metadata["genre"] = str(audio[key][0])
                            elif "track" in lower_key:
                                self.metadata["track"] = str(audio[key][0])

                        # Add audio-specific information
                        if hasattr(audio, "info"):
                            duration_seconds = int(audio.info.length)
                            minutes = duration_seconds // 60
                            seconds = duration_seconds % 60
                            self.metadata["duration"] = f"{minutes}:{seconds:02d}"

                            if hasattr(audio.info, "bitrate"):
                                self.metadata["bitrate"] = f"{audio.info.bitrate // 1000} kbps"
                            if hasattr(audio.info, "sample_rate"):
                                self.metadata["sample_rate"] = (
                                    f"{audio.info.sample_rate // 1000} kHz"
                                )
                except Exception as e:
                    logger.error(
                        f"Error extracting generic audio metadata from {self.file_path}: {e}"
                    )

            logger.info(f"Extracted audio metadata for {self.file_path}")

        except Exception as e:
            logger.error(f"Error in audio metadata extraction for {self.file_path}: {e}")
            # Ensure we have at least basic metadata
            if "title" not in self.metadata:
                self.metadata["title"] = self.file_path.stem
            
    def _extract_video_metadata(self):
        """Extract metadata from video files."""
        # Basic file information for videos
        self.metadata["title"] = self.file_path.stem

        if MEDIAINFO_AVAILABLE:
            try:
                media_info = MediaInfo.parse(self.file_path)

                # Get general track info
                for track in media_info.tracks:
                    if track.track_type == "General":
                        # Extract common metadata
                        if hasattr(track, "title") and track.title:
                            self.metadata["title"] = track.title
                        if hasattr(track, "movie_name") and track.movie_name:
                            self.metadata["title"] = track.movie_name
                        if hasattr(track, "album") and track.album:
                            self.metadata["album"] = track.album
                        if hasattr(track, "performer") and track.performer:
                            self.metadata["artist"] = track.performer
                        if hasattr(track, "director") and track.director:
                            self.metadata["director"] = track.director
                        if hasattr(track, "recorded_date") and track.recorded_date:
                            self.metadata["year"] = track.recorded_date[
                                :4
                            ]  # Extract year from date
                        if hasattr(track, "genre") and track.genre:
                            self.metadata["genre"] = track.genre
                        if hasattr(track, "duration") and track.duration:
                            # Convert milliseconds to minutes:seconds
                            duration_ms = float(track.duration)
                            minutes = int(duration_ms / 60000)
                            seconds = int((duration_ms % 60000) / 1000)
                        self.metadata["duration"] = f"{minutes}:{seconds:02d}"

                    # Get video track info
                    elif track.track_type == "Video":
                        if hasattr(track, "width") and track.width:
                            self.metadata["width"] = track.width
                        if hasattr(track, "height") and track.height:
                            self.metadata["height"] = track.height
                        if hasattr(track, "frame_rate") and track.frame_rate:
                            self.metadata["frame_rate"] = track.frame_rate
                        if hasattr(track, "codec") and track.codec:
                            self.metadata["codec"] = track.codec
                        if hasattr(track, "bit_depth") and track.bit_depth:
                            self.metadata["bit_depth"] = track.bit_depth

                logger.info(f"Extracted video metadata for {self.file_path}")
            except Exception as e:
                logger.error(f"Error extracting video metadata: {e}")
        else:
            logger.warning(f"MediaInfo not available. Limited metadata for {self.file_path}")
            # Set some basic metadata based on file properties
            self.metadata["year"] = datetime.fromtimestamp(self.file_path.stat().st_mtime).strftime(
                "%Y"
            )
        
    def _extract_image_metadata(self):
        """Extract metadata from image files."""
        try:
            with Image.open(self.file_path) as img:
                self.metadata["width"] = img.width
                self.metadata["height"] = img.height
                self.metadata["format"] = img.format
                self.metadata["mode"] = img.mode
                
                # Extract EXIF data if available
                if hasattr(img, "_getexif") and img._getexif():
                    exif = img._getexif()
                    if exif:
                        # Map EXIF tags to readable names
                        exif_tags = {
                            271: "camera_make",
                            272: "camera_model",
                            306: "date_time",
                            36867: "date_taken",
                            33432: "copyright",
                        }
                        
                        for tag, value in exif.items():
                            if tag in exif_tags:
                                self.metadata[exif_tags[tag]] = value
        
        except Exception as e:
            logger.error(f"Error extracting image metadata from {self.file_path}: {e}")

    def _extract_ebook_metadata(self):
        """Extract metadata from ebook files."""
        # Initialize default metadata values
        self.metadata.update({
            "title": self.file_path.stem,
            "author": "Unknown",
            "year": "Unknown",
            "genre": "Unknown",
            "publisher": "Unknown",
            "isbn": "Unknown",
            "language": "Unknown",
        })

        ext = self.file_path.suffix.lower()

        try:
            # PDF files
            if ext == ".pdf":
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(self.file_path)
                    info = reader.metadata
                    if info:
                        if info.get("/Title"):
                            self.metadata["title"] = info["/Title"]
                        if info.get("/Author"):
                            self.metadata["author"] = info["/Author"]
                        if info.get("/Producer"):
                            self.metadata["publisher"] = info["/Producer"]
                        if info.get("/CreationDate"):
                            # Try to extract year from PDF creation date
                            date_str = info["/CreationDate"]
                            year_match = re.search(r"D:(\d{4})", date_str)
                            if year_match:
                                self.metadata["year"] = year_match.group(1)
                except ImportError:
                    logger.warning("PyPDF2 not available. Limited PDF metadata extraction.")
                except Exception as e:
                    logger.error(f"Error extracting PDF metadata from {self.file_path}: {e}")

            # EPUB files
            elif ext == ".epub":
                try:
                    import zipfile
                    from xml.etree import ElementTree as ET
                    
                    with zipfile.ZipFile(self.file_path) as epub:
                        # Try to find and parse the OPF file
                        for name in epub.namelist():
                            if name.endswith(".opf"):
                                with epub.open(name) as opf:
                                    tree = ET.parse(opf)
                                    root = tree.getroot()
                                    
                                    # Define XML namespaces
                                    ns = {
                                        'dc': 'http://purl.org/dc/elements/1.1/',
                                        'opf': 'http://www.idpf.org/2007/opf'
                                    }
                                    
                                    # Extract metadata
                                    metadata = root.find('.//{http://www.idpf.org/2007/opf}metadata')
                                    if metadata is not None:
                                        title = metadata.find('.//dc:title', ns)
                                        if title is not None and title.text:
                                            self.metadata["title"] = title.text
                                            
                                        creator = metadata.find('.//dc:creator', ns)
                                        if creator is not None and creator.text:
                                            self.metadata["author"] = creator.text
                                            
                                        date = metadata.find('.//dc:date', ns)
                                        if date is not None and date.text:
                                            # Try to extract year from date
                                            year_match = re.search(r"\d{4}", date.text)
                                            if year_match:
                                                self.metadata["year"] = year_match.group(0)
                                                
                                        publisher = metadata.find('.//dc:publisher', ns)
                                        if publisher is not None and publisher.text:
                                            self.metadata["publisher"] = publisher.text
                                            
                                        language = metadata.find('.//dc:language', ns)
                                        if language is not None and language.text:
                                            self.metadata["language"] = language.text
                                            
                                        identifier = metadata.find('.//dc:identifier', ns)
                                        if identifier is not None and identifier.text:
                                            # Try to extract ISBN
                                            if "isbn" in identifier.text.lower():
                                                self.metadata["isbn"] = identifier.text
                                break
                except Exception as e:
                    logger.error(f"Error extracting EPUB metadata from {self.file_path}: {e}")

            # MOBI/AZW/AZW3 files
            elif ext in [".mobi", ".azw", ".azw3"]:
                try:
                    import mobi
                    book = mobi.Mobi(self.file_path)
                    book.parse()
                    
                    if book.title:
                        self.metadata["title"] = book.title
                    if book.author:
                        self.metadata["author"] = book.author
                    if book.publisher:
                        self.metadata["publisher"] = book.publisher
                    if book.publication_date:
                        # Try to extract year from publication date
                        year_match = re.search(r"\d{4}", book.publication_date)
                        if year_match:
                            self.metadata["year"] = year_match.group(0)
                    if book.language:
                        self.metadata["language"] = book.language
                except ImportError:
                    logger.warning("mobi-python not available. Limited MOBI/AZW metadata extraction.")
                except Exception as e:
                    logger.error(f"Error extracting MOBI/AZW metadata from {self.file_path}: {e}")

            # FB2 files
            elif ext == ".fb2":
                try:
                    from xml.etree import ElementTree as ET
                    
                    tree = ET.parse(self.file_path)
                    root = tree.getroot()
                    
                    # Find title info section
                    title_info = root.find(".//title-info")
                    if title_info is not None:
                        book_title = title_info.find(".//book-title")
                        if book_title is not None and book_title.text:
                            self.metadata["title"] = book_title.text
                            
                        author = title_info.find(".//author")
                        if author is not None:
                            first_name = author.find(".//first-name")
                            last_name = author.find(".//last-name")
                            author_name = []
                            if first_name is not None and first_name.text:
                                author_name.append(first_name.text)
                            if last_name is not None and last_name.text:
                                author_name.append(last_name.text)
                            if author_name:
                                self.metadata["author"] = " ".join(author_name)
                                
                        genre = title_info.find(".//genre")
                        if genre is not None and genre.text:
                            self.metadata["genre"] = genre.text
                            
                        lang = title_info.find(".//lang")
                        if lang is not None and lang.text:
                            self.metadata["language"] = lang.text
                            
                        date = title_info.find(".//date")
                        if date is not None and date.text:
                            # Try to extract year from date
                            year_match = re.search(r"\d{4}", date.text)
                            if year_match:
                                self.metadata["year"] = year_match.group(0)
                except Exception as e:
                    logger.error(f"Error extracting FB2 metadata from {self.file_path}: {e}")

            logger.info(f"Extracted ebook metadata for {self.file_path}")

        except Exception as e:
            logger.error(f"Error in ebook metadata extraction for {self.file_path}: {e}")
            # Ensure we have at least basic metadata
            if "title" not in self.metadata:
                self.metadata["title"] = self.file_path.stem

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
            placeholders = re.findall(r"\{([^{}]+)\}", template)
            
            for placeholder in placeholders:
                # Check if the placeholder exists in metadata (case-insensitive)
                placeholder_lower = placeholder.lower()
                if placeholder_lower in metadata_lower:
                    value = metadata_lower[placeholder_lower]
                    # Check if the value is empty or None
                    if value is None or str(value).strip() == "" or str(value).strip() == "Unknown":
                        # If empty, replace with 'Unknown'
                        formatted = formatted.replace(f"{{{placeholder}}}", "Unknown")
                    else:
                        # Convert to string and sanitize for filesystem
                        value_str = str(value)
                        # Replace invalid characters with underscore
                        value_str = re.sub(r'[<>:"/\\|?*]', "_", value_str)
                        # Replace placeholder in the template
                        formatted = formatted.replace(f"{{{placeholder}}}", value_str)
                else:
                    # If placeholder not found, replace with 'Unknown'
                    formatted = formatted.replace(f"{{{placeholder}}}", "Unknown")

            # Clean up any double slashes that might have been created
            formatted = re.sub(r"//+", "/", formatted)

            # Ensure the path doesn't end with a period (Windows issue)
            formatted = re.sub(r"\.$", "_", formatted)
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting path with template {template}: {e}")
            return str(self.file_path.name)  # Return just the filename as fallback


class MediaOrganizer:
    """Class to organize media files based on metadata."""
    
    def __init__(self):
        self.source_dir = None
        self.output_dir = None
        # Default templates for each media type
        self.templates = {
            "audio": "{file_type}/{artist}/{album}/{filename}",
            "video": "{file_type}/{year}/{filename}",
            "image": "{file_type}/{creation_year}/{creation_month_name}/{filename}",
            "ebook": "{file_type}/{author}/{title}/{filename}",
        }
        # For backward compatibility
        self.template = "{file_type}/{artist}/{album}/{filename}"
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
        for extensions in SUPPORTED_EXTENSIONS.values():
            all_extensions.extend(extensions)
        
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
                    media_file = MediaFile(file_path)

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
                "show_full_paths": getattr(self, "show_full_paths", False),
                "auto_save_enabled": getattr(self, "auto_save_enabled", True),
                "auto_preview_enabled": getattr(self, "auto_preview_enabled", True),
                "operation_mode": self.operation_mode,
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
                self.template_vars["audio"].set("{file_type}/{artist}/{album}/{filename}")
                self.template_vars["video"].set("{file_type}/{year}/{filename}")
                self.template_vars["image"].set(
                    "{file_type}/{creation_year}/{creation_month_name}/{filename}"
                )
                self.template_vars["ebook"].set("{file_type}/{author}/{title}/{filename}")

                # For backward compatibility
                self.template_var.set("{file_type}/{artist}/{album}/{filename}")

                # Reset extension checkboxes to checked
                for file_type in ["audio", "video", "image", "ebook"]:
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


class MediaOrganizerGUI:
    """GUI for the Media Organizer application."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Media Organizer")
        self.root.geometry("800x800")  # Increase default height
        self.root.minsize(800, 800)    # Increase minimum height

        # Create menubar
        self._create_menubar()
        
        # Set up the organizer
        self.organizer = MediaOrganizer()
        
        # Create variables for extension filters
        self.extension_vars = {"audio": {}, "video": {}, "image": {}, "ebook": {}}
        
        # Config file path
        self.config_file = Path.home() / ".media_organizer_config.json"
        
        # Always enable auto-preview
        self.auto_preview_enabled = True
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the widgets
        self._create_widgets()

        # Create log window
        self.log_window = LogWindow(self.root)
        
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
        PreferencesDialog(self.root, self)

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
            preview_frame, orient="horizontal", command=self.preview_tree.xview
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
        for file_type, extensions in self.extension_vars.items():
            for ext, var in extensions.items():
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
        self.status_var.set("Generating preview...")
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
                    media_file = MediaFile(file_path)

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
        else:
            self.status_var.set(f"Preview generated for {count} files.")

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
                        media_file = MediaFile(file_path)

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
                "show_full_paths": getattr(self, "show_full_paths", False),
                "auto_save_enabled": getattr(self, "auto_save_enabled", True),
                "auto_preview_enabled": getattr(self, "auto_preview_enabled", True),
                "operation_mode": self.operation_mode,
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
                self.template_vars["audio"].set("{file_type}/{artist}/{album}/{filename}")
                self.template_vars["video"].set("{file_type}/{year}/{filename}")
                self.template_vars["image"].set(
                    "{file_type}/{creation_year}/{creation_month_name}/{filename}"
                )
                self.template_vars["ebook"].set("{file_type}/{author}/{title}/{filename}")

                # For backward compatibility
                self.template_var.set("{file_type}/{artist}/{album}/{filename}")

                # Reset extension checkboxes to checked
                for file_type in ["audio", "video", "image", "ebook"]:
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


class LogWindow:
    """Separate window for displaying logs."""
    
    def __init__(self, parent):
        """Initialize the log window."""
        self.window = tk.Toplevel(parent)
        self.window.title("Media Organizer Logs")
        self.window.geometry("600x400")
        self.window.minsize(400, 300)
        
        # Configure the window to be hidden instead of destroyed when closed
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        
        # Create the log text widget
        self.log_text = tk.Text(self.window, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.window, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Configure logging to text widget
        self._setup_text_logging()
        
        # Initially hide the window
        self.hide()
    
    def _setup_text_logging(self):
        """Set up logging to the text widget."""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)

                def append():
                    self.text_widget.configure(state="normal")
                    self.text_widget.insert(tk.END, msg + "\n")
                    self.text_widget.see(tk.END)
                    self.text_widget.configure(state="disabled")

                # Schedule the append operation on the GUI thread
                self.text_widget.after(0, append)

        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(text_handler)

        # Disable editing
        self.log_text.configure(state="disabled")
    
    def show(self):
        """Show the log window."""
        self.window.deiconify()
        self.window.lift()
    
    def hide(self):
        """Hide the log window."""
        self.window.withdraw()


class PreferencesDialog:
    """Dialog for managing application preferences."""
    
    def __init__(self, parent, app):
        """Initialize the preferences dialog."""
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Preferences")
        self.dialog.geometry("600x500")
        self.dialog.minsize(600, 500)
        self.dialog.transient(parent)  # Make it a modal dialog
        self.dialog.grab_set()  # Make it modal
        
        # Store reference to main app
        self.app = app
        
        # Center the window
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create the main content frame
        self.content_frame = ttk.Frame(self.dialog, padding=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create General tab
        self.general_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.general_frame, text="General")
        
        # Auto-preview option
        self.auto_preview_var = tk.BooleanVar(value=self.app.auto_preview_enabled)
        auto_preview_cb = ttk.Checkbutton(
            self.general_frame,
            text="Automatically generate preview when settings change",
            variable=self.auto_preview_var
        )
        auto_preview_cb.pack(anchor=tk.W, pady=5)
        
        # Auto-save option
        self.auto_save_var = tk.BooleanVar(value=getattr(self.app, 'auto_save_enabled', True))
        auto_save_cb = ttk.Checkbutton(
            self.general_frame,
            text="Automatically save settings when inputs change",
            variable=self.auto_save_var
        )
        auto_save_cb.pack(anchor=tk.W, pady=5)
        
        # Full path display option
        self.show_full_paths_var = tk.BooleanVar(value=getattr(self.app, 'show_full_paths', False))
        full_paths_cb = ttk.Checkbutton(
            self.general_frame,
            text="Show full file paths in preview",
            variable=self.show_full_paths_var
        )
        full_paths_cb.pack(anchor=tk.W, pady=5)
        
        # Create File Types tab
        self.file_types_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.file_types_frame, text="File Types")
        
        # Create sub-notebook for file type tabs
        self.file_types_notebook = ttk.Notebook(self.file_types_frame)
        self.file_types_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create text variables for extensions
        self.extension_texts = {}
        
        # Create sub-tabs for each media type
        for media_type in ["audio", "video", "image", "ebook"]:
            frame = ttk.Frame(self.file_types_notebook, padding=10)
            self.file_types_notebook.add(frame, text=media_type.title())
            
            # Add description label
            ttk.Label(
                frame,
                text=f"Enter file extensions for {media_type} files (one per line, with or without dot):",
                wraplength=400
            ).pack(anchor=tk.W, pady=(0, 5))
            
            # Create text widget with scrollbar for extensions
            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            text_widget = tk.Text(text_frame, height=10, width=40)
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Get current extensions and format them
            current_extensions = [ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS[media_type]]
            text_widget.insert("1.0", "\n".join(current_extensions))
            
            self.extension_texts[media_type] = text_widget
        
        # Create buttons frame
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add Save and Cancel buttons
        save_button = ttk.Button(buttons_frame, text="Save", command=self._save_preferences)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(buttons_frame, text="Cancel", command=self.dialog.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _save_preferences(self):
        """Save preferences and update the main application."""
        # Update auto-preview setting
        self.app.auto_preview_enabled = self.auto_preview_var.get()
        
        # Update auto-save setting
        self.app.auto_save_enabled = self.auto_save_var.get()
        
        # Update full paths setting
        self.app.show_full_paths = self.show_full_paths_var.get()
        
        # Update extensions
        new_extensions = {}
        for media_type, text_widget in self.extension_texts.items():
            # Get extensions from text widget
            extensions = text_widget.get("1.0", "end-1c").split("\n")
            # Clean up extensions (remove empty lines, add dot if missing)
            extensions = [ext.strip() for ext in extensions if ext.strip()]
            extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]
            new_extensions[media_type] = extensions
        
        # Update SUPPORTED_EXTENSIONS
        global SUPPORTED_EXTENSIONS
        SUPPORTED_EXTENSIONS = new_extensions
        
        # Update the main window's extension checkboxes
        self.app._update_extension_checkboxes()
        
        # Save settings to file
        self.app._save_settings()
        
        # Generate preview if auto-preview is enabled
        self.app._auto_generate_preview()
        
        # Close the dialog
        self.dialog.destroy()

    def _update_extension_checkboxes(self):
        """Update the extension checkboxes in the main window based on SUPPORTED_EXTENSIONS."""
        # Clear existing extension frames
        for frame in self.main_frame.winfo_children():
            if isinstance(frame, ttk.LabelFrame) and frame.winfo_text() == "File Type Filters":
                frame.destroy()

        # Recreate extension filters frame
        extensions_frame = ttk.LabelFrame(self.main_frame, text="File Type Filters", padding=5)
        extensions_frame.pack(fill=tk.X, pady=2)

        # Create a frame for each file type category
        file_types_frame = ttk.Frame(extensions_frame)
        file_types_frame.pack(fill=tk.X, pady=2)

        # Clear existing extension variables
        self.extension_vars = {"audio": {}, "video": {}, "image": {}, "ebook": {}}

        # Recreate frames for each media type
        for media_type, title in [("audio", "Audio"), ("video", "Video"), 
                                ("image", "Image"), ("ebook", "eBook")]:
            type_frame = ttk.LabelFrame(file_types_frame, text=title)
            type_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            # Create "Select All" checkbox
            all_var = tk.BooleanVar(value=True)
            setattr(self, f"{media_type}_all_var", all_var)
            all_cb = ttk.Checkbutton(
                type_frame,
                text=f"All {title}",
                variable=all_var,
                command=lambda t=media_type: self._toggle_all_extensions(t),
            )
            all_cb.pack(anchor=tk.W)

            # Create individual checkboxes for extensions
            extensions_frame = ttk.Frame(type_frame)
            extensions_frame.pack(fill=tk.X, padx=10)

            for i, ext in enumerate(SUPPORTED_EXTENSIONS[media_type]):
                ext_name = ext.lstrip(".")
                var = tk.BooleanVar(value=True)
                self.extension_vars[media_type][ext] = var
                cb = ttk.Checkbutton(
                    extensions_frame,
                    text=ext_name,
                    variable=var,
                    command=self._update_extension_selection,
                )
                cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=5)

        # Update the layout
        self.main_frame.update_idletasks()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = MediaOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 
