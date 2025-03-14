# Media Organizer

A cross-platform application to organize media files based on their metadata.

## Features

- Recursively scan directories for media files (audio, video, images)
- Extract metadata from media files using the TinyTag library
- Organize files based on customizable templates
- User-friendly graphical interface
- Cross-platform compatibility using Python's standard libraries
- Detailed logging of operations

## Purchasing

Media Organizer is proprietary software available for purchase. For pricing information, licensing details, and how to buy, please see the [PURCHASING.md](PURCHASING.md) file.

## Supported File Types

- **Audio**: MP3, FLAC, M4A, AAC, OGG, WAV
- **Video**: MP4, MKV, AVI, MOV, WMV
- **Images**: JPG, JPEG, PNG, GIF, BMP, TIFF
- **eBooks**: PDF, EPUB, MOBI, AZW

## Dependencies

Media Organizer relies on several Python libraries to function properly. For a complete list of dependencies and their licenses, please see the [DEPENDENCIES.md](DEPENDENCIES.md) file.

## Installation

### Prerequisites

- Python 3.6+ (tested with Python 3.13)
- Tkinter (usually comes with Python, but may need separate installation)
- MediaInfo (optional, for enhanced video metadata extraction)

### macOS

1. Make sure you have Python 3 installed
2. Install Tkinter if not already installed:
   ```bash
   brew install python-tk@3.13  # Replace 3.13 with your Python version
   ```
3. Install MediaInfo for enhanced video metadata extraction (optional but recommended):
   ```bash
   brew install mediainfo
   ```
4. Clone or download this repository
5. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Run the application using the provided script:
   ```bash
   ./run.sh
   ```

### Windows

1. Make sure you have Python 3 installed
2. Install MediaInfo for enhanced video metadata extraction (optional but recommended):
   - Download and install from [MediaInfo website](https://mediaarea.net/en/MediaInfo/Download/Windows)
3. Clone or download this repository
4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the application using the provided script:
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
   python3 main.py
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

- **Common**: `{filename}`, `{extension}`, `{file_type}`, `{size}`, `{creation_date}`, `{creation_year}`, `{creation_month}`, `{creation_month_name}`
- **Audio**: `{title}`, `{artist}`, `{album}`, `{year}`, `{genre}`, `{track}`, `{duration}`, `{bitrate}`
- **Image**: `{width}`, `{height}`, `{format}`, `{camera_make}`, `{camera_model}`, `{date_taken}`

### Example Templates

- `{file_type}/{artist}/{album}/{filename}` - Organizes by file type, then artist, then album
- `Music/{year}/{artist} - {title}.{extension}` - Organizes music by year, then artist-title
- `{file_type}/{creation_year}/{creation_month_name}/{filename}` - Organizes by file type, year, and month name
- `Photos/{creation_year}/{creation_month}/{filename}` - Organizes photos by year and month number

## Notes

- If a metadata field is not available for a file, it will be replaced with "Unknown"
- The application will copy files, not move them, so your original files remain intact
- The process can be stopped at any time by clicking the "Stop" button

## Requirements

- Python 3.6+
- TinyTag
- Pillow
- Tkinter (usually comes with Python)

## Development

### Code Style and Linting

This project uses [Black](https://black.readthedocs.io/) for code formatting and [Flake8](https://flake8.pycqa.org/) for linting. To set up the development environment:

1. Install the development dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the linter and formatter manually:

   ```bash
   python -m black .
   ```

   Or to check without modifying files:

   ```bash
   python -m black --check .
   ```

### VSCode Setup

This project includes VSCode configuration for automatic formatting with Black:

1. Install the [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) extension in VSCode
2. The `.vscode/settings.json` file is already configured to:
   - Use Black as the default formatter for Python files
   - Format Python files automatically on save
   - Use the line length specified in `pyproject.toml` (100 characters)

## License

This software is proprietary and is licensed only to the original purchaser. See the [LICENSE](LICENSE) file for the complete terms and conditions.
