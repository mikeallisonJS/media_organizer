# Media Organizer

A cross-platform application to organize media files based on their metadata.

## Features

- Recursively scan directories for media files (audio, video, images)
- Extract metadata from media files using the mutagen library
- Organize files based on customizable templates
- User-friendly graphical interface
- Cross-platform compatibility using Python's standard libraries
- Detailed logging of operations

## Supported File Types

- **Audio**: MP3, FLAC, M4A, AAC, OGG, WAV
- **Video**: MP4, MKV, AVI, MOV, WMV
- **Images**: JPG, JPEG, PNG, GIF, BMP, TIFF

## Installation

### Prerequisites

- Python 3.6+ (tested with Python 3.13)
- Tkinter (usually comes with Python, but may need separate installation)

### macOS

1. Make sure you have Python 3 installed
2. Install Tkinter if not already installed:
   ```bash
   brew install python-tk@3.13  # Replace 3.13 with your Python version
   ```
3. Clone or download this repository
4. Run the application using the provided script:
   ```bash
   ./run.sh
   ```

### Windows

1. Make sure you have Python 3 installed
2. Clone or download this repository
3. Run the application using the provided script:
   ```
   run.bat
   ```

### Manual Installation

If the provided scripts don't work, you can set up the environment manually:

1. Create a virtual environment:

   ```bash
   python3 -m venv media_organizer_venv
   ```

2. Activate the virtual environment:

   - On macOS/Linux:
     ```bash
     source media_organizer_venv/bin/activate
     ```
   - On Windows:
     ```
     media_organizer_venv\Scripts\activate
     ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python3 media_organizer.py
   ```

## Usage

1. Launch the application
2. Select the source directory containing your media files
3. Select the output directory where organized files will be placed
4. Configure the organization template (see below)
5. Click "Start Organization" to begin the process

## Organization Templates

The application uses templates with placeholders to determine how files should be organized. Placeholders are enclosed in curly braces `{}` and will be replaced with the corresponding metadata value.

### Available Placeholders

- **Common**: `{filename}`, `{extension}`, `{file_type}`, `{size}`, `{creation_date}`
- **Audio**: `{title}`, `{artist}`, `{album}`, `{year}`, `{genre}`, `{track}`, `{duration}`, `{bitrate}`
- **Image**: `{width}`, `{height}`, `{format}`, `{camera_make}`, `{camera_model}`, `{date_taken}`

### Example Templates

- `{file_type}/{artist}/{album}/{filename}` - Organizes by file type, then artist, then album
- `Music/{year}/{artist} - {title}.{extension}` - Organizes music by year, then artist-title
- `{file_type}/{creation_date}/{filename}` - Organizes by file type, then creation date

## Notes

- If a metadata field is not available for a file, it will be replaced with "Unknown"
- The application will copy files, not move them, so your original files remain intact
- The process can be stopped at any time by clicking the "Stop" button

## Requirements

- Python 3.6+
- mutagen
- Pillow
- Tkinter (usually comes with Python)

## License

This project is open source and available under the MIT License.
