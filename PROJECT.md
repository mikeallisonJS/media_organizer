# Media Organizer Project Documentation

## Project Overview

Media Organizer is a cross-platform desktop application built with Python and Tkinter that helps users organize their media files (audio, video, images, and ebooks) based on metadata. The application extracts metadata from various file formats and organizes them into a structured directory hierarchy according to user-defined templates.

## Architecture

The application follows a modular architecture with clear separation of concerns:

1. **Core Logic**: Handles file operations, metadata extraction, and organization logic
2. **GUI Layer**: Provides the user interface for interacting with the core functionality
3. **Utility Modules**: Contains helper functions, constants, and shared resources

### Design Patterns

- **Model-View-Controller (MVC)**: The application loosely follows the MVC pattern:

  - **Model**: `MediaFile` and `MediaOrganizer` classes handle data and business logic
  - **View**: Tkinter UI components in `MediaOrganizerGUI` and dialog classes
  - **Controller**: Event handlers and callbacks in the GUI classes

- **Observer Pattern**: Used for updating the UI when background operations complete (via callbacks)

- **Template Method**: Used in the metadata extraction process, with specialized methods for different file types

## Module Structure

### Core Modules

- **`media_file.py`**: Handles metadata extraction from different file types
- **`media_organizer.py`**: Core logic for organizing files based on templates
- **`main.py`**: Entry point and GUI implementation

### Support Modules

- **`defaults.py`**: Default settings, templates, and constants
- **`extensions.py`**: Supported file extensions for different media types
- **`log_window.py`**: Logging interface for the application
- **`preferences_dialog.py`**: Dialog for managing application preferences

## Key Classes

### MediaFile

The `MediaFile` class is responsible for:

- Determining the file type (audio, video, image, ebook)
- Extracting metadata from files using appropriate libraries
- Generating formatted paths based on templates and metadata

```python
# Key methods:
extract_metadata()  # Main method that calls type-specific extractors
_extract_audio_metadata()  # Extracts metadata from audio files
_extract_video_metadata()  # Extracts metadata from video files
_extract_image_metadata()  # Extracts metadata from image files
_extract_ebook_metadata()  # Extracts metadata from ebook files
get_formatted_path()  # Generates path based on template and metadata
```

### MediaOrganizer

The `MediaOrganizer` class handles:

- Finding media files in the source directory
- Organizing files (copy/move) according to templates
- Managing the organization process (start/stop)

```python
# Key methods:
find_media_files()  # Finds all supported media files in source directory
organize_files()    # Organizes files based on templates
set_template()      # Sets the organization template for a media type
get_template()      # Gets the template for a specific media type
```

### MediaOrganizerGUI

The `MediaOrganizerGUI` class provides:

- The main application window and UI components
- User interaction handling
- Settings management
- Preview generation
- Progress reporting

## Data Flow

1. User selects source and destination directories
2. User configures templates for each media type
3. User selects file types to process
4. Application scans source directory for matching files
5. For each file:
   - Metadata is extracted
   - Destination path is generated based on template
   - File is copied/moved to destination
6. Progress is reported to the user

## Configuration Management

The application stores user settings in a JSON file located at:

- `~/media_organizer_settings.json`

Settings include:

- Source and destination directories
- Templates for each media type
- Selected file extensions
- UI preferences
- Custom file extensions

## Threading Model

The application uses threading to keep the UI responsive:

- Long-running operations (preview generation, file organization) run in background threads
- Progress updates are sent to the main thread via callbacks
- Thread synchronization is handled through the Tkinter event loop

## Error Handling

- Comprehensive logging using Python's `logging` module
- Try-except blocks for handling file operations and metadata extraction
- User-friendly error messages via message boxes
- Graceful degradation when optional dependencies are missing

## Dependencies

- **Tkinter**: GUI framework
- **Mutagen**: Audio metadata extraction
- **Pillow (PIL)**: Image processing and metadata extraction
- **PyPDF2**: PDF metadata extraction
- **MediaInfo** (optional): Enhanced video metadata extraction

## Cross-Platform Considerations

- Uses `pathlib.Path` for cross-platform path handling
- Avoids platform-specific APIs
- Uses Tkinter for cross-platform UI
- Handles file system differences (case sensitivity, path separators)

## Future Development

Planned features and improvements:

- Extension editor for media types
- Separate modules for media type editors
- Help and About dialogs
- Mac & Windows executables
- Improved logging configuration
- Custom application name and icon
- Purchase functionality

## Development Methodology

The project follows an iterative development approach with:

- Modular design for maintainability
- Progressive enhancement of features
- Refactoring for improved code organization
- Comprehensive error handling and logging
