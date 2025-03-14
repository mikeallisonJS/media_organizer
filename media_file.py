#!/usr/bin/env python3
"""
Media File module for Media Organizer application.
Provides a class for handling media files and extracting metadata.
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime

# Import required libraries for metadata extraction
from tinytag import TinyTag
from PIL import Image

# Import the defaults module
import defaults

# Configure logging
logger = logging.getLogger("MediaOrganizer")

# Check if MediaInfo is available
try:
    from pymediainfo import MediaInfo
    MEDIAINFO_AVAILABLE = True
except (ImportError, OSError):
    MEDIAINFO_AVAILABLE = False
    logging.warning(
        "pymediainfo or MediaInfo not available. Video metadata extraction will be limited."
    )

class MediaFile:
    """Class to represent a media file with its metadata."""
    
    def __init__(self, file_path, supported_extensions):
        """
        Initialize a MediaFile object.
        
        Args:
            file_path: Path to the media file
            supported_extensions: Dictionary of supported file extensions by media type
        """
        self.file_path = Path(file_path)
        self.metadata = {}
        self.supported_extensions = supported_extensions
        self.file_type = self._get_file_type()
        self.extract_metadata()
        
    def _get_file_type(self):
        """Determine the type of media file."""
        ext = self.file_path.suffix.lower()
        for file_type, extensions_list in self.supported_extensions.items():
            if ext in extensions_list:
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
        """Extract metadata from audio files using TinyTag."""
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
            # TinyTag supports MP3, OGG, OPUS, FLAC, WMA, MP4/M4A/AAC, and WAV
            tag = TinyTag.get(self.file_path)
            
            # Extract common metadata
            if tag.title:
                self.metadata["title"] = tag.title
            if tag.artist:
                self.metadata["artist"] = tag.artist
            if tag.album:
                self.metadata["album"] = tag.album
            if tag.year:
                self.metadata["year"] = str(tag.year)
            if tag.genre:
                self.metadata["genre"] = tag.genre
            if tag.track:
                self.metadata["track"] = str(tag.track)
            
            # Audio-specific information
            if tag.duration:
                minutes = int(tag.duration // 60)
                seconds = int(tag.duration % 60)
                self.metadata["duration"] = f"{minutes}:{seconds:02d}"
            if tag.bitrate:
                self.metadata["bitrate"] = f"{int(tag.bitrate)} kbps"
            if tag.samplerate:
                self.metadata["sample_rate"] = f"{int(tag.samplerate / 1000)} kHz"
            
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
                            self.metadata["year"] = track.recorded_date[:4]  # Extract year from date
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
            
            # Try to use TinyTag for basic video metadata if possible
            try:
                # TinyTag has limited support for some video formats
                tag = TinyTag.get(self.file_path)
                
                if tag.title:
                    self.metadata["title"] = tag.title
                if tag.artist:
                    self.metadata["artist"] = tag.artist
                if tag.year:
                    self.metadata["year"] = str(tag.year)
                if tag.duration:
                    minutes = int(tag.duration // 60)
                    seconds = int(tag.duration % 60)
                    self.metadata["duration"] = f"{minutes}:{seconds:02d}"
            except:
                # Silently fail if TinyTag can't handle the video format
                pass
        
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
                    from pypdf import PdfReader
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
                    logger.warning("PyPDF not available. Limited PDF metadata extraction.")
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
                                            # Check if it's an ISBN
                                            if "isbn" in identifier.get("{http://www.idpf.org/2007/opf}scheme", "").lower() or re.search(r"isbn", identifier.text, re.I):
                                                self.metadata["isbn"] = identifier.text
                                break
                except Exception as e:
                    logger.error(f"Error extracting EPUB metadata from {self.file_path}: {e}")

            # MOBI files
            elif ext in [".mobi", ".azw", ".azw3"]:
                try:
                    # Try to use mobi-python if available
                    import mobi
                    book = mobi.Mobi(self.file_path)
                    book.parse()
                    
                    if book.title:
                        self.metadata["title"] = book.title
                    if book.author:
                        self.metadata["author"] = book.author
                    if book.publisher:
                        self.metadata["publisher"] = book.publisher
                    
                    # Try to extract year from publication date if available
                    if hasattr(book, "publication_date") and book.publication_date:
                        year_match = re.search(r"\d{4}", book.publication_date)
                        if year_match:
                            self.metadata["year"] = year_match.group(0)
                            
                except ImportError:
                    logger.warning("mobi-python not available. Limited MOBI metadata extraction.")
                except Exception as e:
                    logger.error(f"Error extracting MOBI metadata from {self.file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in ebook metadata extraction for {self.file_path}: {e}")
            
    def get_formatted_path(self, template):
        """
        Format the destination path using the template and metadata.
        
        Args:
            template: String template with placeholders for metadata fields
            
        Returns:
            Formatted path string
        """
        try:
            # Replace placeholders with metadata values
            formatted_path = template
            
            # Add file_type to metadata for template use
            self.metadata["file_type"] = self.file_type
            
            # Replace each placeholder with its corresponding metadata value
            for key, value in self.metadata.items():
                placeholder = "{" + key + "}"
                if placeholder in formatted_path:
                    # Convert value to string and sanitize for use in filenames
                    str_value = str(value)
                    # Replace characters that are problematic in file paths
                    sanitized = re.sub(r'[<>:"/\\|?*]', '_', str_value)
                    formatted_path = formatted_path.replace(placeholder, sanitized)
            
            # Replace any remaining placeholders with "Unknown"
            formatted_path = re.sub(r'{[^{}]+}', 'Unknown', formatted_path)
            
            # Ensure the path ends with the original filename if not already included
            if "{filename}" not in template and "{filename}.{extension}" not in template:
                if formatted_path.endswith(".{extension}"):
                    # Replace just the extension placeholder
                    formatted_path = formatted_path.replace(".{extension}", f".{self.metadata['extension']}")
                else:
                    # Add the full filename with extension
                    formatted_path = os.path.join(formatted_path, f"{self.metadata['filename']}")
            elif "{filename}" in template and "{extension}" not in template:
                # If filename is included but extension isn't, add the extension
                formatted_path = formatted_path.replace("{filename}", f"{self.metadata['filename']}")
            
            # Clean up any double slashes or other path issues
            formatted_path = os.path.normpath(formatted_path)
            
            return formatted_path
            
        except Exception as e:
            logger.error(f"Error formatting path: {e}")
            # Fallback to a safe default
            return os.path.join(self.file_type, self.metadata["filename"]) 