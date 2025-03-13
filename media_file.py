#!/usr/bin/env python3
"""
Media File module for Media Organizer application.
Provides a class for handling media files and extracting metadata.
"""

import re
import logging
from pathlib import Path
from datetime import datetime

# Import required libraries for metadata extraction
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
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
            return str(self.file_path.name)  # Return just the filename as a fallback 