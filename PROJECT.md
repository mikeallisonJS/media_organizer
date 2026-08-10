# Archimedius Project Documentation

## Project Overview

Archimedius is a cross-platform desktop application built with Python and Tkinter that helps users organize their media files (audio, video, images, and ebooks) based on metadata. The application extracts metadata from various file formats and organizes them into a structured directory hierarchy according to user-defined templates.

## Architecture

The application follows a modular architecture with clear separation of concerns:

1. **Core Logic**: Handles file operations, metadata extraction, and organization logic
2. **GUI Layer**: Provides the user interface for interacting with the core functionality
3. **Utility Modules**: Contains helper functions, constants, and shared resources

### Design Patterns

- **Model-View-Controller (MVC)**: The application loosely follows the MVC pattern:

  - **Model**: `Settings`, `organize_plan`, and `RunState` handle data and business logic
  - **View**: Tkinter UI components in `ArchimediusGUI` and dialog classes
  - **Controller**: Event handlers and callbacks in the GUI classes

- **Observer Pattern**: Used for updating the UI when background operations complete (via callbacks)

- **Template Method**: Used in the metadata extraction process, with specialized methods for different file types

## Module Structure

### Core Modules

- **`metadata_extract/`**: Per-media-type metadata extraction and media type detection
- **`destination_path.py`**: Template-based destination path resolution
- **`organize_plan.py`**: Source scan, file planning, and organize execution
- **`organize_run.py`**: Organize run orchestration — validate, plan, execute, report progress
- **`run_state.py`**: Run-only flags (stop request, in-progress, processed count) for an active run
- **`archimedius_gui.py`**: Entry point and GUI implementation

### Support Modules

- **`defaults.py`**: Default settings, templates, supported extensions, and constants
- **`log_window.py`**: Logging interface for the application
- **`settings.py`**: Settings model and persistence for user preferences

## Key Classes

### organize_plan

The `organize_plan` module is the shared pipeline for Preview and Organize run:

- `iter_matching_files` / `scan_source` — recursive source scan with extension and destination rules
- `build_file_plan` — metadata extraction plus destination path via `resolve_destination_path`
- `execute_plans` — copy/move planned files with collision handling

### organize_run

The `organize_run` module owns a whole Organize run, so both GUI entry points
("Copy/Move All" and "Copy/Move Selected") share one code path:

- `OrganizeRequest` — the run's inputs, independent of the GUI. `selected_paths`
  is `None` for a full source scan and a list of paths for a preview selection.
- `validate_request` / `prepare_destination_root` — user-facing validation, raising
  `OrganizeRunError` (or `OrganizeRunNotice` when nothing was selected)
- `build_plans` — file plans from a source scan or from explicit paths
- `run_organize` — validate, plan, execute under the run's collision policy, and
  report progress; the collision resolver, stop predicate, and progress callback
  are all injected, so the module is testable without launching the window

### Settings

The `Settings` dataclass (in `settings.py`) is the single source of truth for run
configuration, persisted to JSON:

- Source and destination directories
- Per-media-type templates and operation mode (copy/move)
- Selected extensions, exclude-unknown flags, collision policy, and UI preferences

Preview and organize runs read paths, templates, and operation mode from `Settings`
(and the bound GUI widgets) and pass them into `organize_plan`.

### RunState

The `RunState` dataclass (in `run_state.py`) holds only the mutable flags an
active run needs:

- `stop_requested` — set when the user clicks Stop
- `is_running` — whether a run is in progress
- `files_processed` — count of files transferred in the current run

### ArchimediusGUI

The GUI layer provides:

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

- `~/archimedius_settings.json`

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
- **tinytag**: Audio (and video fallback) metadata extraction
- **Pillow (PIL)**: Image processing and metadata extraction
- **pypdf**: PDF metadata extraction
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
