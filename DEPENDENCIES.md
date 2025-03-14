# Dependencies

This document lists all dependencies used by the Media Organizer application along with their respective licenses.

## License Compatibility Notice

Media Organizer is proprietary software licensed only to the original purchaser. When using third-party libraries, we ensure compliance with their license terms by selecting components with permissive licenses that allow inclusion in proprietary software.

All dependencies used in this application are under permissive licenses (MIT, BSD, Apache) which generally allow inclusion in proprietary software with proper attribution.

Please consult with a legal professional if you have questions about license compliance.

## Required Dependencies

### Python Standard Library

- **tkinter**: Python's standard GUI package (included with Python)
- **pathlib**: Object-oriented filesystem paths (included with Python)
- **json**: JSON encoder and decoder (included with Python)
- **logging**: Logging facility for Python (included with Python)
- **os**: Miscellaneous operating system interfaces (included with Python)
- **shutil**: High-level file operations (included with Python)
- **threading**: Thread-based parallelism (included with Python)
- **datetime**: Basic date and time types (included with Python)
- **re**: Regular expression operations (included with Python)
- **webbrowser**: Convenient web-browser controller (included with Python)
- **zipfile**: Work with ZIP archives (included with Python)
- **xml.etree.ElementTree**: XML processing API (included with Python)

### Third-Party Libraries

#### TinyTag

- **Version**: 2.1.0
- **Description**: A library for reading music meta data of MP3, OGG, FLAC, WAV and MP4 files
- **License**: MIT
- **Website**: https://github.com/devsnd/tinytag
- **Used for**: Extracting metadata from audio files (MP3, FLAC, MP4, OGG, WAV)

#### Pillow (PIL Fork)

- **Version**: 11.0.0+
- **Description**: Python Imaging Library
- **License**: HPND (Historical Permission Notice and Disclaimer)
- **Website**: https://python-pillow.org/
- **Used for**: Image processing and metadata extraction

#### pymediainfo

- **Version**: 6.0.1+
- **Description**: Python wrapper for the MediaInfo library
- **License**: MIT
- **Website**: https://github.com/sbraz/pymediainfo
- **Used for**: Enhanced video metadata extraction
- **Note**: Requires MediaInfo to be installed on the system

#### Black

- **Version**: 24.2.0+
- **Description**: The uncompromising Python code formatter
- **License**: MIT
- **Website**: https://github.com/psf/black
- **Used for**: Development only (code formatting)

## Optional Dependencies

#### PyPDF

- **Description**: PDF toolkit for reading and manipulating PDF files
- **License**: BSD-3-Clause
- **Website**: https://github.com/py-pdf/pypdf
- **Used for**: Extracting metadata from PDF files
- **Note**: If not installed, the application will still work but with limited PDF metadata extraction

#### mobi-python

- **Description**: Python library for working with Kindle MOBI format
- **License**: Apache-2.0
- **Website**: https://github.com/kroo/mobi-python
- **Used for**: Extracting metadata from MOBI/AZW/AZW3 files
- **Note**: If not installed, the application will still work but with limited MOBI/AZW metadata extraction

## System Dependencies

#### MediaInfo

- **Description**: Library for reading metadata from media files
- **License**: BSD-2-Clause
- **Website**: https://mediaarea.net/en/MediaInfo
- **Installation**:
  - macOS: `brew install mediainfo`
  - Windows: Download from [MediaInfo website](https://mediaarea.net/en/MediaInfo/Download/Windows)
- **Used for**: Enhanced video metadata extraction
- **Note**: Optional but recommended for better video metadata extraction

## License Information

### MIT License

A permissive license that allows for reuse with few restrictions. It permits use, modification, and distribution with minimal requirements to preserve copyright and license notices.

### HPND (Historical Permission Notice and Disclaimer)

The Pillow license is derived from the Python Imaging Library (PIL) license, which is a permissive license similar to the BSD license.

### BSD-3-Clause License

A permissive license similar to the MIT License but with an additional clause that prohibits the use of the name of the copyright holder or contributors to promote derived products without specific permission.

### BSD-2-Clause License

A simplified version of the BSD-3-Clause license, removing the non-endorsement clause.

### Apache-2.0 License

A permissive license that allows for free use, modification, and distribution, but requires preservation of copyright and license notices. It also provides an express grant of patent rights from contributors to users.
