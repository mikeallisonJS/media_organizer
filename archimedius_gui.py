#!/usr/bin/env python3
"""
ArchimediusGUI - GUI module for the Archimedius application.
Provides the main application window and user interface components.
"""

import os
import shutil
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import json
from ttkbootstrap import Style

# Import application modules
import extensions
import defaults
from log_window import LogWindow
from preferences_dialog import PreferencesDialog
from media_file import MediaFile
from archimedius import Archimedius
from about_dialog import AboutDialog
from help_dialog import HelpDialog
from license_manager import LicenseManager

# Configure logging
logger = logging.getLogger("Archimedius")

# Initialize SUPPORTED_EXTENSIONS from the defaults module
SUPPORTED_EXTENSIONS = defaults.get_default_extensions()

class ArchimediusGUI:
    """GUI for the Archimedius application."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title(defaults.APP_NAME)
        self.root.geometry(defaults.DEFAULT_WINDOW_SIZES["main_window"])  # Increase default height
        self.root.minsize(800, 800)    # Ensure minimum size
        
        # Initialize license manager
        self.license_manager = LicenseManager()
        
        # Check license status
        if not self.license_manager.is_valid():
            # Show activation dialog if not licensed or in trial mode
            self.license_manager.show_activation_dialog(self.root)
            # If still not valid after dialog, exit
            if not self.license_manager.is_valid():
                messagebox.showerror(
                    "License Required",
                    f"{defaults.APP_NAME} requires a valid license or active trial to run."
                )
                self.root.destroy()
                return
        
        # Initialize the media organizer
        self.organizer = Archimedius()
        
        # Initialize settings
        self.show_full_paths = defaults.DEFAULT_SETTINGS["show_full_paths"]
        self.auto_save_enabled = defaults.DEFAULT_SETTINGS["auto_save_enabled"]
        self.auto_preview_enabled = defaults.DEFAULT_SETTINGS["auto_preview_enabled"]
        self.logging_level = defaults.DEFAULT_SETTINGS["logging_level"]
        self.dark_mode = defaults.DEFAULT_SETTINGS["dark_mode"]
        self.style = Style()
        
        # Create variables for extension filters
        self.extension_vars = {"audio": {}, "video": {}, "image": {}, "ebook": {}}
        
        # Config file path
        self.config_file = Path.home() / defaults.DEFAULT_PATHS["settings_file"]
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the menubar
        self._create_menu()
        
        # Create the widgets
        self._create_widgets()
        self.apply_theme(self.dark_mode)
        
        # Create log window
        self.log_window = LogWindow(self.root, logger)
        
        # Load saved settings
        self._load_settings()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Log startup
        logger.info("Archimedius started")

    def apply_theme(self, dark_mode):
        """Apply ttkbootstrap theme based on dark mode."""
        self.dark_mode = bool(dark_mode)
        theme_name = "darkly" if self.dark_mode else "flatly"

        try:
            self.style.theme_use(theme_name)

            # tk.Menu is not a ttk widget; keep it consistently light.
            menu_colors = {
                "bg": "#f5f5f5",
                "fg": "#1a1a1a",
                "active_bg": "#e6e6e6",
                "active_fg": "#111111",
            }

            if hasattr(self, "menubar"):
                self.menubar.configure(
                    background=menu_colors["bg"],
                    foreground=menu_colors["fg"],
                    activebackground=menu_colors["active_bg"],
                    activeforeground=menu_colors["active_fg"],
                    borderwidth=0,
                )
                for menu in [self.file_menu, self.tools_menu, self.help_menu]:
                    menu.configure(
                        background=menu_colors["bg"],
                        foreground=menu_colors["fg"],
                        activebackground=menu_colors["active_bg"],
                        activeforeground=menu_colors["active_fg"],
                        borderwidth=0,
                    )
        except Exception as e:
            logger.warning("Failed to apply Sun-Valley theme: %s", e)

    def _create_menu(self):
        """Create the application menu."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Source Directory...", command=self._browse_source)
        self.file_menu.add_command(label="Open Output Directory...", command=self._browse_output)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save Settings", command=self._save_settings_manual)
        self.file_menu.add_command(label="Reset Settings", command=self._reset_settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self._on_close)
        
        # Tools menu
        self.tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=self.tools_menu)
        self.tools_menu.add_command(label="View Logs", command=self._toggle_logs)
        
        # Help menu
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Help Contents", command=self._show_help)
        self.help_menu.add_command(label="Placeholders Help", command=self._show_placeholders_help)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="License Activation", command=self._show_license_activation)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="About", command=self._show_about)

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
        
        # Status bar
        status_frame = ttk.Frame(bottom_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        self.status_var = tk.StringVar()
        status_message = self.license_manager.get_status_message()
        self.status_var.set(f"License: {status_message}")
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, padx=5)

        self.file_var = tk.StringVar(value="")
        file_label = ttk.Label(progress_frame, textvariable=self.file_var)
        file_label.pack(anchor=tk.W)

        # Buttons frame
        buttons_frame = ttk.Frame(bottom_frame)
        buttons_frame.pack(fill=tk.X, pady=3)

        # Replace single button with Copy and Move buttons
        self.copy_button = ttk.Button(
            buttons_frame, text="Copy All", command=lambda: self._start_organization("copy")
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)

        self.move_button = ttk.Button(
            buttons_frame, text="Move All", command=lambda: self._start_organization("move")
        )
        self.move_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            buttons_frame, text="Stop", command=self._stop_organization, state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Top section frame - directories + tabbed content
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=2, side=tk.TOP)
        
        # Create a frame to hold both directory selection frames
        directories_frame = ttk.Frame(top_frame)
        directories_frame.pack(fill=tk.X, pady=2)

        # Source directory selection
        self.source_frame = ttk.LabelFrame(directories_frame, text="Source Directory", padding=5)
        self.source_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.source_entry = ttk.Entry(self.source_frame)
        self.source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        source_button = ttk.Button(self.source_frame, text="Browse...", command=self._browse_source)
        source_button.pack(side=tk.RIGHT)

        # Output directory selection
        self.output_frame = ttk.LabelFrame(directories_frame, text="Output Directory", padding=5)
        self.output_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        self.output_entry = ttk.Entry(self.output_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        output_button = ttk.Button(self.output_frame, text="Browse...", command=self._browse_output)
        output_button.pack(side=tk.RIGHT)
        
        # Tabbed content area for filters/templates/preview
        content_tabs = ttk.Notebook(top_frame)
        content_tabs.pack(fill=tk.BOTH, expand=True, pady=2)

        file_types_tab = ttk.Frame(content_tabs, padding=5)
        templates_tab = ttk.Frame(content_tabs, padding=5)
        preview_tab = ttk.Frame(content_tabs, padding=5)
        preferences_tab = ttk.Frame(content_tabs, padding=10)

        content_tabs.add(preview_tab, text="Preview")
        content_tabs.add(templates_tab, text="Organization Templates")
        content_tabs.add(file_types_tab, text="File Type Filters")
        content_tabs.add(preferences_tab, text="Preferences")
        content_tabs.select(preview_tab)
        self._create_preferences_tab(preferences_tab)

        # Create a frame for each file type category
        self.file_types_frame = ttk.Frame(file_types_tab)
        self.file_types_frame.pack(fill=tk.X, pady=2)
        
        # Audio extensions
        audio_frame = ttk.LabelFrame(self.file_types_frame, text="Audio")
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
        video_frame = ttk.LabelFrame(self.file_types_frame, text="Video")
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
        image_frame = ttk.LabelFrame(self.file_types_frame, text="Image")
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
        ebook_frame = ttk.LabelFrame(self.file_types_frame, text="eBook")
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
        template_frame = ttk.LabelFrame(templates_tab, text="Organization Templates", padding=5)
        template_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
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
        # Variables for exclude unknown options
        self.exclude_unknown_vars = {}

        # Initialize exclude unknown variables with default values from defaults.py
        for media_type in ["audio", "video", "image", "ebook"]:
            self.exclude_unknown_vars[media_type] = tk.BooleanVar(value=defaults.DEFAULT_EXCLUDE_UNKNOWN[media_type])

        # Audio template
        self.template_vars["audio"] = tk.StringVar(value=self.organizer.templates["audio"])
        self.template_vars["audio"].trace_add(
            "write", lambda *_: self._on_template_change("audio")
        )
        ttk.Label(audio_template_frame, text="Audio Template:").pack(anchor=tk.W)
        self.template_entries["audio"] = ttk.Entry(
            audio_template_frame, textvariable=self.template_vars["audio"]
        )
        self.template_entries["audio"].pack(fill=tk.X, pady=1)
        ttk.Label(
            audio_template_frame, text="Example: {file_type}/{artist}/{album}/{filename}"
        ).pack(anchor=tk.W)
        # Add exclude unknown checkbox
        self.exclude_unknown_vars["audio"].trace_add(
            "write", lambda *_: self._on_template_change("audio")
        )
        ttk.Checkbutton(
            audio_template_frame, 
            text="Exclude 'Unknown' folders from path", 
            variable=self.exclude_unknown_vars["audio"]
        ).pack(anchor=tk.W, pady=(5, 0))

        # Video template
        self.template_vars["video"] = tk.StringVar(value=self.organizer.templates["video"])
        self.template_vars["video"].trace_add(
            "write", lambda *_: self._on_template_change("video")
        )
        ttk.Label(video_template_frame, text="Video Template:").pack(anchor=tk.W)
        self.template_entries["video"] = ttk.Entry(
            video_template_frame, textvariable=self.template_vars["video"]
        )
        self.template_entries["video"].pack(fill=tk.X, pady=1)
        ttk.Label(video_template_frame, text="Example: {file_type}/{year}/{filename}").pack(
            anchor=tk.W
        )
        # Add exclude unknown checkbox
        self.exclude_unknown_vars["video"].trace_add(
            "write", lambda *_: self._on_template_change("video")
        )
        ttk.Checkbutton(
            video_template_frame, 
            text="Exclude 'Unknown' folders from path", 
            variable=self.exclude_unknown_vars["video"]
        ).pack(anchor=tk.W, pady=(5, 0))

        # Image template
        self.template_vars["image"] = tk.StringVar(value=self.organizer.templates["image"])
        self.template_vars["image"].trace_add(
            "write", lambda *_: self._on_template_change("image")
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
        # Add exclude unknown checkbox
        self.exclude_unknown_vars["image"].trace_add(
            "write", lambda *_: self._on_template_change("image")
        )
        ttk.Checkbutton(
            image_template_frame, 
            text="Exclude 'Unknown' folders from path", 
            variable=self.exclude_unknown_vars["image"]
        ).pack(anchor=tk.W, pady=(5, 0))

        # eBook template
        self.template_vars["ebook"] = tk.StringVar(value=self.organizer.templates["ebook"])
        self.template_vars["ebook"].trace_add(
            "write", lambda *_: self._on_template_change("ebook")
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
        # Add exclude unknown checkbox
        self.exclude_unknown_vars["ebook"].trace_add(
            "write", lambda *_: self._on_template_change("ebook")
        )
        ttk.Checkbutton(
            ebook_template_frame, 
            text="Exclude 'Unknown' folders from path", 
            variable=self.exclude_unknown_vars["ebook"]
        ).pack(anchor=tk.W, pady=(5, 0))

        # For backward compatibility
        self.template_var = self.template_vars["audio"]

        # Preview tab content
        preview_frame = ttk.LabelFrame(
            preview_tab, text="Preview", padding=5
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        # Add a button frame at the top of the preview
        self.preview_button_frame = ttk.Frame(preview_frame)
        self.preview_button_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Add Analyze button
        analyze_button = ttk.Button(
            self.preview_button_frame, text="Analyze", command=self._generate_preview
        )
        analyze_button.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(analyze_button, "Refresh the preview based on current settings")
        
        # Add Copy Selected button
        copy_selected_button = ttk.Button(
            self.preview_button_frame, text="Copy Selected", command=lambda: self._process_selected_files("copy")
        )
        copy_selected_button.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(copy_selected_button, "Copy only the selected files to the destination")
        
        # Add Move Selected button
        move_selected_button = ttk.Button(
            self.preview_button_frame, text="Move Selected", command=lambda: self._process_selected_files("move")
        )
        move_selected_button.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(move_selected_button, "Move only the selected files to the destination")
        
        # Add Select All button
        select_all_button = ttk.Button(
            self.preview_button_frame, text="Select All", command=self._select_all_files
        )
        select_all_button.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(select_all_button, "Select all files in the preview")
        
        # Add Deselect All button
        deselect_all_button = ttk.Button(
            self.preview_button_frame, text="Deselect All", command=self._deselect_all_files
        )
        deselect_all_button.pack(side=tk.LEFT, padx=5)
        self._create_tooltip(deselect_all_button, "Deselect all files in the preview")
        
        # Preview table with scrollbars
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)

        # Create the treeview
        self.preview_tree = ttk.Treeview(
            preview_container,
            columns=("selected", "source", "destination"),
            show="headings",
            selectmode="extended"  # Allow multiple selections
        )
        
        # Define the columns
        self.preview_tree.heading("selected", text="Select ☑")
        self.preview_tree.heading("source", text="Source Path")
        self.preview_tree.heading("destination", text="Destination Path")
        
        # Configure column widths
        preview_container.update_idletasks()  # Ensure container has been drawn
        width = preview_container.winfo_width()
        self.preview_tree.column("selected", width=60, stretch=False)  # Fixed width for checkbox column
        self.preview_tree.column("source", width=(width-60)//2, stretch=True)
        self.preview_tree.column("destination", width=(width-60)//2, stretch=True)

        # Add click event to toggle selection
        self.preview_tree.bind("<ButtonRelease-1>", self._toggle_selection)
        # Keep double-click event as a backup
        self.preview_tree.bind("<Double-1>", self._toggle_selection)

        # Add scrollbars
        preview_scrollbar_y = ttk.Scrollbar(
            preview_container, orient="vertical", command=self.preview_tree.yview
        )
        preview_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        preview_scrollbar_x = ttk.Scrollbar(
            preview_container, orient="horizontal", command=self.preview_tree.xview
        )
        preview_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.preview_tree.configure(
            yscrollcommand=preview_scrollbar_y.set,
            xscrollcommand=preview_scrollbar_x.set
        )

    def _toggle_logs(self):
        """Toggle the visibility of the log window."""
        if self.log_window.window.winfo_viewable():
            self.log_window.hide()
        else:
            self.log_window.show()

    def _show_preferences(self):
        """Show the preferences dialog."""
        # Create a callback function to handle the result from the preferences dialog
        def on_save(result):
            if result:
                if 'extensions' in result:
                    # Update the global SUPPORTED_EXTENSIONS
                    global SUPPORTED_EXTENSIONS
                    SUPPORTED_EXTENSIONS = result['extensions']
                    # Save settings to file
                    self._save_settings()
                    # Refresh extension filters if needed
                    if result.get('refresh_extensions', False):
                        self._refresh_extension_filters()
                        # Auto-generate preview if enabled
                        self._auto_generate_preview()
        
        # Create the preferences dialog with the callback
        PreferencesDialog(self.root, self, SUPPORTED_EXTENSIONS, callback=on_save)

    def _create_preferences_tab(self, parent):
        """Create inline preferences controls in the Preferences tab."""
        preferences_frame = ttk.Frame(parent)
        preferences_frame.pack(fill=tk.BOTH, expand=True)

        prefs_notebook = ttk.Notebook(preferences_frame)
        prefs_notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        general_tab = ttk.Frame(prefs_notebook, padding=10)
        file_types_tab = ttk.Frame(prefs_notebook, padding=10)
        prefs_notebook.add(general_tab, text="General")
        prefs_notebook.add(file_types_tab, text="File Types")

        # General settings
        self.pref_auto_preview_var = tk.BooleanVar(value=self.auto_preview_enabled)
        self.pref_auto_save_var = tk.BooleanVar(value=self.auto_save_enabled)
        self.pref_show_full_paths_var = tk.BooleanVar(value=self.show_full_paths)
        self.pref_dark_mode_var = tk.BooleanVar(value=self.dark_mode)
        self.pref_logging_level_var = tk.StringVar(value=self.logging_level)

        ttk.Checkbutton(
            general_tab,
            text="Automatically generate preview when settings change",
            variable=self.pref_auto_preview_var,
        ).pack(anchor=tk.W, pady=4)
        ttk.Checkbutton(
            general_tab,
            text="Automatically save settings when inputs change",
            variable=self.pref_auto_save_var,
        ).pack(anchor=tk.W, pady=4)
        ttk.Checkbutton(
            general_tab,
            text="Show full file paths in preview",
            variable=self.pref_show_full_paths_var,
        ).pack(anchor=tk.W, pady=4)
        ttk.Checkbutton(
            general_tab,
            text="Enable dark mode",
            variable=self.pref_dark_mode_var,
        ).pack(anchor=tk.W, pady=4)

        logging_row = ttk.Frame(general_tab)
        logging_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(logging_row, text="Logging Level:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Combobox(
            logging_row,
            textvariable=self.pref_logging_level_var,
            values=list(defaults.LOGGING_LEVELS.keys()),
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT)

        # File type extension settings
        self.pref_extension_texts = {}
        filetype_notebook = ttk.Notebook(file_types_tab)
        filetype_notebook.pack(fill=tk.BOTH, expand=True)

        for media_type in ["audio", "video", "image", "ebook"]:
            frame = ttk.Frame(filetype_notebook, padding=10)
            filetype_notebook.add(frame, text=media_type.title())
            ttk.Label(
                frame,
                text=f"Extensions for {media_type} files (one per line):",
                wraplength=500,
            ).pack(anchor=tk.W, pady=(0, 5))

            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            text_widget = tk.Text(text_frame, height=10)
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.insert(
                "1.0",
                "\n".join(ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS[media_type]),
            )
            self.pref_extension_texts[media_type] = text_widget

            ttk.Button(
                frame,
                text="Reset to Default",
                command=lambda m=media_type: self._reset_inline_extensions_to_default(m),
            ).pack(anchor=tk.E, pady=5)

        # Action buttons
        buttons_frame = ttk.Frame(preferences_frame)
        buttons_frame.pack(fill=tk.X)
        ttk.Button(
            buttons_frame,
            text="Save Preferences",
            command=self._save_inline_preferences,
        ).pack(side=tk.RIGHT, padx=5)
        ttk.Button(
            buttons_frame,
            text="Reload From Saved Settings",
            command=self._load_settings,
        ).pack(side=tk.RIGHT, padx=5)

    def _reset_inline_extensions_to_default(self, media_type):
        """Reset inline extension editor for one media type."""
        default_extensions = [ext.lstrip(".") for ext in defaults.get_default_extensions()[media_type]]
        if media_type in getattr(self, "pref_extension_texts", {}):
            self.pref_extension_texts[media_type].delete("1.0", tk.END)
            self.pref_extension_texts[media_type].insert("1.0", "\n".join(default_extensions))

    def _save_inline_preferences(self):
        """Save inline preferences tab settings."""
        try:
            self.auto_preview_enabled = self.pref_auto_preview_var.get()
            self.auto_save_enabled = self.pref_auto_save_var.get()
            self.show_full_paths = self.pref_show_full_paths_var.get()
            self.logging_level = self.pref_logging_level_var.get()
            self.dark_mode = self.pref_dark_mode_var.get()
            self.apply_theme(self.dark_mode)

            new_extensions = {}
            for media_type, text_widget in self.pref_extension_texts.items():
                extensions_text = text_widget.get("1.0", "end-1c").split("\n")
                extensions_list = [ext.strip() for ext in extensions_text if ext.strip()]
                extensions_list = [ext if ext.startswith(".") else f".{ext}" for ext in extensions_list]
                if not extensions_list:
                    messagebox.showerror(
                        "Error",
                        f"Please provide at least one extension for {media_type}.",
                    )
                    return
                new_extensions[media_type] = extensions_list

            global SUPPORTED_EXTENSIONS
            SUPPORTED_EXTENSIONS = new_extensions
            self._refresh_extension_filters()
            self._save_settings()
            self._auto_generate_preview()
            self.status_var.set("Preferences saved.")
        except Exception as e:
            logger.error(f"Error saving inline preferences: {e}")
            messagebox.showerror("Error", f"Failed to save preferences: {str(e)}")

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
                # Only call _organization_complete for the main organization process, not for selected files
                if not hasattr(self, 'processing_selected_files') or not self.processing_selected_files:
                    self._organization_complete()
            else:
                # Truncate long paths for display
                if len(current_file) > 70:
                    display_file = "..." + current_file[-67:]
                else:
                    display_file = current_file
                self.file_var.set(f"Current: {display_file}")
        elif current_file == "Complete":
            self.progress_var.set(0)
            self.status_var.set("No matching files found.")
            self.file_var.set("")
            if not hasattr(self, "processing_selected_files") or not self.processing_selected_files:
                self._organization_complete()
    
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
        self.status_var.set("Finding files...")
        self.file_var.set("Scanning for media files...")
        self.progress_var.set(0)
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
                    # Check if output is a true subdirectory of source (not the same directory)
                    is_dest_in_source = False
                    if abs_output != abs_source:
                        try:
                            abs_output.relative_to(abs_source)
                            is_dest_in_source = True
                        except ValueError:
                            is_dest_in_source = False
                    if is_dest_in_source:
                        logger.info(f"Destination directory is inside source directory. Will skip files in destination for preview.")
                except Exception as e:
                    logger.error(f"Error checking directory relationship: {e}")

            # First pass: Count total files for progress tracking
            self.root.after(0, lambda: self.status_var.set("Counting files..."))
            total_files = 0
            for file_path in source_path.rglob("*"):
                # Skip files in the destination directory if it's inside the source
                if is_dest_in_source and file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(source_path)
                        dest_path = Path(output_dir) / rel_path
                        if file_path.is_relative_to(Path(output_dir)) or file_path == dest_path:
                            continue
                    except (ValueError, RuntimeError):
                        pass  # Not relative, so continue processing
                        
                if file_path.is_file() and file_path.suffix.lower() in selected_extensions:
                    total_files += 1
                    if total_files % 100 == 0:  # Update status periodically
                        self.root.after(0, lambda count=total_files: self.file_var.set(f"Found {count} files..."))

            # Second pass: Process files for preview
            self.root.after(0, lambda: self.status_var.set("Finding file details..."))
            preview_files = []
            processed = 0
            
            for file_path in source_path.rglob("*"):
                # Skip files in the destination directory if it's inside the source
                if is_dest_in_source and file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(source_path)
                        dest_path = Path(output_dir) / rel_path
                        if file_path.is_relative_to(Path(output_dir)) or file_path == dest_path:
                            continue
                    except (ValueError, RuntimeError):
                        pass  # Not relative, so continue processing
                        
                if file_path.is_file() and file_path.suffix.lower() in selected_extensions:
                    preview_files.append(file_path)
                    processed += 1
                    # Update progress every 10 files or for the last file
                    if processed % 10 == 0 or processed == total_files:
                        progress = (processed / total_files) * 100 if total_files > 0 else 0
                        self.root.after(0, lambda p=progress: self.progress_var.set(p))
                        self.root.after(0, lambda p=processed, t=total_files: 
                            self.file_var.set(f"Found {p} of {t} files..."))
                    
                    if processed >= 100:  # Limit to 100 files for preview
                        break
            
            # Prepare preview data
            preview_data = []
            
            # Generate preview for each file
            for i, file_path in enumerate(preview_files):
                try:
                    # Extract metadata
                    media_file = MediaFile(file_path, SUPPORTED_EXTENSIONS)

                    # Get the appropriate template for this file type
                    template = self.organizer.get_template(media_file.file_type)
                    
                    # Get exclude_unknown setting for this file type
                    exclude_unknown = self.exclude_unknown_vars.get(media_file.file_type, tk.BooleanVar(value=False)).get()
                    
                    # Generate destination path
                    rel_path = media_file.get_formatted_path(template, exclude_unknown=exclude_unknown)
                    
                    # Get source path for display
                    if getattr(self, "show_full_paths", False):
                        display_source = str(file_path)
                        if self.organizer.output_dir:
                            display_dest = str(self.organizer.output_dir / rel_path)
                        else:
                            display_dest = rel_path
                    else:
                        try:
                            display_source = str(file_path.relative_to(source_path))
                            display_dest = rel_path
                        except ValueError:
                            display_source = str(file_path)
                            if self.organizer.output_dir:
                                display_dest = str(self.organizer.output_dir / rel_path)
                            else:
                                display_dest = rel_path
                    
                    # Add to preview data with the full file path
                    preview_data.append((display_source, display_dest, str(file_path)))
                    
                except Exception as e:
                    logger.error(f"Error generating preview for {file_path}: {e}")
            
            # Update UI in the main thread
            self.root.after(0, lambda: self._update_preview_results(preview_data, processed))

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            # Update UI in the main thread
            self.root.after(0, lambda: self._update_preview_status(f"Preview generation failed: {str(e)}", error=True))
        finally:
            # Reset progress bar
            self.root.after(0, lambda: self.progress_var.set(0))

    def _update_preview_results(self, preview_data, count):
        """Update the preview treeview with results from the preview thread."""
        # Clear existing items
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
            
        # Store the full file paths for later processing
        self.preview_files = {}
        
        # Insert preview data into treeview
        for i, (display_source, display_dest, full_path) in enumerate(preview_data):
            # Use a checkbox for selection (initially unchecked)
            item_id = self.preview_tree.insert("", "end", values=("☐", display_source, display_dest))
            
            # Store the full file path for later processing
            self.preview_files[item_id] = {
                "source_path": display_source,
                "dest_path": display_dest,
                "selected": False,
                "full_path": full_path
            }

        # Update status
        if count == 0:
            self.status_var.set("No media files found in the source directory.")
            self.file_var.set("")
        else:
            # Count files by media type
            media_types = {}
            for display_source, _, full_path in preview_data:
                # Get file extension
                ext = os.path.splitext(full_path)[1].lower()
                # Determine media type
                media_type = None
                for type_name, extensions in SUPPORTED_EXTENSIONS.items():
                    if ext in extensions:
                        media_type = type_name
                        break
                
                if media_type:
                    media_types[media_type] = media_types.get(media_type, 0) + 1
            
            # Create detailed message
            type_counts = ", ".join([f"{count} {media_type}" for media_type, count in media_types.items()])
            self.status_var.set(f"Preview generated for {count} files.")
            self.file_var.set(f"Found: {type_counts}")
    
    def _update_preview_status(self, message, error=False):
        """Update the preview status with a message."""
        self.status_var.set(message)
        if error:
            messagebox.showerror("Error", message)
    
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
        for file_type, extensions_list in self.extension_vars.items():
            for ext, var in extensions_list.items():
                if var.get():
                    selected_extensions.append(ext)
        return selected_extensions

    def _on_template_change(self, *_, media_type=None):
        """
        Handle template change event.

        Args:
            *_: Variable arguments passed by tkinter trace (unused)
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

    def _show_placeholders_help(self):
        """Show a modal dialog with information about available placeholders."""
        # Create a new top-level window
        help_window = tk.Toplevel(self.root)
        help_window.title("Available Placeholders")
        help_window.geometry(defaults.DEFAULT_WINDOW_SIZES["help_window"])
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
        
        # Create a scrollable content area so all placeholders are accessible.
        scroll_container = ttk.Frame(help_window)
        scroll_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_container, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(
            scroll_container, orient="vertical", command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        content_frame = ttk.Frame(canvas, padding=20)
        content_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def _sync_scroll_region(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _sync_content_width(event):
            canvas.itemconfigure(content_window, width=event.width)

        content_frame.bind("<Configure>", _sync_scroll_region)
        canvas.bind("<Configure>", _sync_content_width)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        help_window.bind(
            "<Destroy>",
            lambda _event: canvas.unbind_all("<MouseWheel>"),
        )
        
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

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def enter(_):
            try:
                x, y, _, _ = widget.bbox("insert")
            except Exception:
                x, y = 0, 0
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")

            # Tooltips use tk widgets so colors stay readable in both themes.
            if self.dark_mode:
                tooltip_bg = "#2b2b2b"
                tooltip_fg = "#e6e6e6"
                tooltip_border = "#4a4a4a"
            else:
                tooltip_bg = "#fff8d6"
                tooltip_fg = "#1a1a1a"
                tooltip_border = "#c7c7c7"

            label = tk.Label(
                self.tooltip,
                text=text,
                justify=tk.LEFT,
                bg=tooltip_bg,
                fg=tooltip_fg,
                relief=tk.SOLID,
                borderwidth=1,
                highlightthickness=1,
                highlightbackground=tooltip_border,
                padx=6,
                pady=4,
                wraplength=250,
            )
            label.pack(padx=3, pady=3)
            
        def leave(_):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

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
        self.organizer.stop_requested = False
        self.organizer.is_running = True
        self.organizer.files_processed = 0

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
                # Check if output is a true subdirectory of source (not the same directory)
                is_dest_in_source = False
                if abs_output != abs_source:
                    try:
                        abs_output.relative_to(abs_source)
                        is_dest_in_source = True
                    except ValueError:
                        is_dest_in_source = False
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
                        # Create a custom supported_extensions dictionary with only selected extensions
                        custom_extensions = {}
                        for media_type, extensions_list in SUPPORTED_EXTENSIONS.items():
                            custom_extensions[media_type] = [ext for ext in extensions_list if ext in selected_extensions]
                        
                        # Extract metadata
                        media_file = MediaFile(file_path, custom_extensions)

                        # Get the appropriate template for this file type
                        template = self.organizer.get_template(media_file.file_type)
                        
                        # Get exclude_unknown setting for this file type
                        exclude_unknown = self.exclude_unknown_vars.get(media_file.file_type, tk.BooleanVar(value=False)).get()
                        
                        # Generate destination path
                        rel_path = media_file.get_formatted_path(template, exclude_unknown=exclude_unknown)
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
                    self.root.after(
                        0, lambda p=processed, t=total_files, f=str(file_path): self._update_progress(p, t, f)
                    )
            
            # Complete
            self.organizer.files_processed = processed
            self.root.after(0, lambda p=processed, t=total_files: self._update_progress(p, t, "Complete"))
            operation_name = "copy" if self.organizer.operation_mode == "copy" else "move"
            logger.info(f"{operation_name.capitalize()} operation complete. Processed {processed} files.")
            
        except Exception as e:
            logger.error(f"Error during organization: {e}")
            self.root.after(
                0,
                lambda msg=str(e): messagebox.showerror(
                    "Error", f"An error occurred during organization: {msg}"
                ),
            )
        finally:
            self.organizer.is_running = False
    
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
                # Save exclude unknown settings
                "exclude_unknown": {
                    "audio": self.exclude_unknown_vars["audio"].get(),
                    "video": self.exclude_unknown_vars["video"].get(),
                    "image": self.exclude_unknown_vars["image"].get(),
                    "ebook": self.exclude_unknown_vars["ebook"].get(),
                },
                # Save custom extensions
                "custom_extensions": SUPPORTED_EXTENSIONS,
                "show_full_paths": getattr(self, "show_full_paths", False),
                "auto_save_enabled": getattr(self, "auto_save_enabled", True),
                "auto_preview_enabled": getattr(self, "auto_preview_enabled", True),
                "logging_level": getattr(self, "logging_level", defaults.DEFAULT_SETTINGS["logging_level"]),
                "dark_mode": getattr(self, "dark_mode", defaults.DEFAULT_SETTINGS["dark_mode"]),
                "window_geometry": self.root.geometry(),
                "operation_mode": getattr(self, "operation_mode", "copy"),
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
                if "window_geometry" in settings and settings["window_geometry"]:
                    try:
                        self.root.geometry(settings["window_geometry"])
                    except Exception as e:
                        logger.warning(f"Could not restore saved window size: {e}")

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

                # Load custom extensions if available
                if "custom_extensions" in settings:
                    global SUPPORTED_EXTENSIONS
                    # Start with default extensions
                    custom_extensions = extensions.DEFAULT_EXTENSIONS.copy()
                    # Update with custom extensions
                    for media_type, exts in settings["custom_extensions"].items():
                        if media_type in custom_extensions and exts:
                            custom_extensions[media_type] = exts
                    # Update global extensions
                    SUPPORTED_EXTENSIONS = custom_extensions
                    # Refresh the extension filters to show the updated extensions
                    self._refresh_extension_filters()
                
                # Apply extension selections after refreshing filters
                if "extensions" in settings:
                    for file_type in ["audio", "video", "image", "ebook"]:
                        if file_type in settings["extensions"]:
                            # First update individual extensions
                            for ext, value in settings["extensions"][file_type].items():
                                if ext in self.extension_vars[file_type]:
                                    self.extension_vars[file_type][ext].set(value)
                            
                            # Then update the "All" checkbox based on individual selections
                            all_selected = all(var.get() for var in self.extension_vars[file_type].values())
                            getattr(self, f"{file_type}_all_var").set(all_selected)
                
                # Load full paths setting
                self.show_full_paths = settings.get("show_full_paths", False)

                # Load auto-save setting (defaults to True)
                self.auto_save_enabled = settings.get("auto_save_enabled", True)

                # Load auto-preview setting (defaults to True)
                self.auto_preview_enabled = settings.get("auto_preview_enabled", True)

                # Load exclude unknown settings
                if "exclude_unknown" in settings:
                    for media_type in ["audio", "video", "image", "ebook"]:
                        if media_type in settings["exclude_unknown"]:
                            self.exclude_unknown_vars[media_type].set(settings["exclude_unknown"][media_type])
                        else:
                            # Use default for this media type if not in settings
                            self.exclude_unknown_vars[media_type].set(defaults.DEFAULT_EXCLUDE_UNKNOWN[media_type])
                else:
                    # Use defaults for all media types if exclude_unknown not in settings
                    for media_type in ["audio", "video", "image", "ebook"]:
                        self.exclude_unknown_vars[media_type].set(defaults.DEFAULT_EXCLUDE_UNKNOWN[media_type])

                # Load logging level setting
                self.logging_level = settings.get("logging_level", defaults.DEFAULT_SETTINGS["logging_level"])
                self.dark_mode = settings.get("dark_mode", defaults.DEFAULT_SETTINGS["dark_mode"])
                self.apply_theme(self.dark_mode)
                
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
                for media_type in ["audio", "video", "image", "ebook"]:
                    self.template_vars[media_type].set(defaults.DEFAULT_TEMPLATES[media_type])

                # For backward compatibility
                self.template_var.set(defaults.DEFAULT_TEMPLATES["audio"])
                
                # Reset extension checkboxes to checked
                for file_type in ["audio", "video", "image", "ebook"]:
                    getattr(self, f"{file_type}_all_var").set(True)
                    self._toggle_all_extensions(file_type)
                
                # Reset settings to defaults
                self.show_full_paths = defaults.DEFAULT_SETTINGS["show_full_paths"]
                self.auto_save_enabled = defaults.DEFAULT_SETTINGS["auto_save_enabled"]
                self.auto_preview_enabled = defaults.DEFAULT_SETTINGS["auto_preview_enabled"]
                self.logging_level = defaults.DEFAULT_SETTINGS["logging_level"]
                self.dark_mode = defaults.DEFAULT_SETTINGS["dark_mode"]
                self.apply_theme(self.dark_mode)
                
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

    def _on_close(self):
        """Handle window close event."""
        # Save settings before closing
        self._save_settings()
        # Close the window
        self.root.destroy()

    def _show_about(self):
        """Show the About dialog."""
        AboutDialog(self.root)

    def _show_help(self):
        """Show the Help dialog."""
        HelpDialog(self.root)

    def _show_license_activation(self):
        """Show the license activation dialog."""
        self.license_manager.show_activation_dialog(self.root)
        
        # Update status bar with license status
        status_message = self.license_manager.get_status_message()
        self.status_var.set(f"License: {status_message}")

    def _toggle_selection(self, event):
        """Toggle selection of a file in the preview treeview when clicked."""
        # Get the item that was clicked
        region = self.preview_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        item = self.preview_tree.identify_row(event.y)
        if not item:
            return
            
        # Get the column that was clicked
        column = self.preview_tree.identify_column(event.x)
        column_index = int(column.replace('#', '')) - 1
        
        # Only toggle if the checkbox column was clicked
        if column_index == 0:
            # Toggle the checkbox
            values = list(self.preview_tree.item(item, "values"))
            if values[0] == "☐":
                values[0] = "☑"
                self.preview_files[item]["selected"] = True
            else:
                values[0] = "☐"
                self.preview_files[item]["selected"] = False
                
            # Update the item
            self.preview_tree.item(item, values=values)
            
    def _select_all_files(self):
        """Select all files in the preview treeview."""
        for item in self.preview_tree.get_children():
            values = list(self.preview_tree.item(item, "values"))
            values[0] = "☑"
            self.preview_tree.item(item, values=values)
            self.preview_files[item]["selected"] = True
            
    def _deselect_all_files(self):
        """Deselect all files in the preview treeview."""
        for item in self.preview_tree.get_children():
            values = list(self.preview_tree.item(item, "values"))
            values[0] = "☐"
            self.preview_tree.item(item, values=values)
            self.preview_files[item]["selected"] = False
            
    def _process_selected_files(self, mode):
        """Process only the selected files in the preview treeview."""
        # Get the source and output directories
        source_dir = self.source_entry.get().strip()
        output_dir = self.output_entry.get().strip()
        
        if not source_dir or not output_dir:
            messagebox.showerror("Error", "Please select both source and output directories.")
            return
            
        if not os.path.exists(source_dir):
            messagebox.showerror("Error", "Source directory does not exist.")
            return
            
        # Create output directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create output directory: {str(e)}")
            return
            
        # Get selected files
        selected_files = []
        for item, data in self.preview_files.items():
            if data["selected"]:
                # Use the full_path for source and dest_path for destination
                selected_files.append((data["full_path"], data["dest_path"]))
                
        if not selected_files:
            messagebox.showinfo("Info", "No files selected for processing.")
            return
            
        # Confirm move operation
        if mode == "move" and not messagebox.askyesno(
            "Confirm Move Operation",
            f"Moving {len(selected_files)} files will remove them from the source directory. Continue?",
        ):
            return
            
        # Configure organizer
        self.organizer.set_source_dir(source_dir)
        self.organizer.set_output_dir(output_dir)
        self.organizer.set_operation_mode(mode)
        self.organizer.stop_requested = False
        self.organizer.is_running = True
        self.organizer.files_processed = 0
        
        # Set flag to indicate we're processing selected files
        self.processing_selected_files = True
        
        # Start processing in a separate thread
        threading.Thread(
            target=self._process_selected_files_thread,
            args=(selected_files, mode),
            daemon=True
        ).start()
        
    def _process_selected_files_thread(self, selected_files, mode):
        """Process the selected files in a separate thread."""
        try:
            # Update UI
            self.root.after(0, lambda: self._update_ui_for_processing(True))
            
            # Get the output path
            output_path = Path(self.organizer.output_dir)
            
            # Process each selected file
            total_files = len(selected_files)
            processed = 0
            successful = 0  # Track successfully processed files
            
            for source_path, dest_rel in selected_files:
                if self.organizer.stop_requested:
                    logger.info("Processing stopped by user")
                    break
                    
                try:
                    # Convert paths
                    source_file = Path(source_path)
                    
                    # Skip if the source file doesn't exist
                    if not source_file.exists():
                        logger.warning(f"Skipping file {source_file} as it no longer exists")
                        processed += 1
                        continue
                    
                    # For destination, check if it's a relative or absolute path
                    if os.path.isabs(dest_rel):
                        dest_file = Path(dest_rel)
                    else:
                        dest_file = output_path / dest_rel
                    
                    # Create destination directory if it doesn't exist
                    os.makedirs(dest_file.parent, exist_ok=True)
                    
                    # Copy or move the file
                    if mode == "copy":
                        shutil.copy2(source_file, dest_file)
                        logger.info(f"Copied {source_file} to {dest_file}")
                    else:  # move mode
                        shutil.move(source_file, dest_file)
                        logger.info(f"Moved {source_file} to {dest_file}")
                    
                    # Increment successful count
                    successful += 1
                        
                except Exception as e:
                    logger.error(f"Error processing file {source_path}: {e}")
                    
                # Update progress
                processed += 1
                self.root.after(0, lambda p=processed, t=total_files, f=source_path: 
                               self._update_progress(p, t, f))
                
            # Update the organizer's files_processed attribute
            self.organizer.files_processed = successful
            
            # Complete
            self.root.after(0, lambda: self._update_progress(processed, total_files, "Complete"))
            operation_name = "copy" if mode == "copy" else "move"
            logger.info(f"{operation_name.capitalize()} operation complete. Processed {successful} files successfully out of {processed} attempted.")
            
            # Show custom completion message
            operation_past = "copied" if mode == "copy" else "moved"
            self.root.after(0, lambda: messagebox.showinfo(
                "Complete",
                f"Operation complete!\n\n{operation_past.capitalize()} {successful} files successfully."
            ))
            
            # Refresh the preview if files were moved to show current state
            if mode == "move" and successful > 0:
                self.root.after(500, self._generate_preview)
            
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            error_msg = str(e) if str(e) else "Unknown error"
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", f"An error occurred during processing: {msg}"))
        finally:
            self.organizer.is_running = False
            # Update UI
            self.root.after(0, lambda: self._update_ui_for_processing(False))
            
    def _update_ui_for_processing(self, is_processing):
        """Update the UI elements for processing state."""
        if is_processing:
            # Disable all interactive elements during processing
            # Disable main action buttons
            self.copy_button.config(state=tk.DISABLED)
            self.move_button.config(state=tk.DISABLED)
            # Enable stop button
            self.stop_button.config(state=tk.NORMAL)
            
            # Disable directory selection
            self.source_entry.config(state=tk.DISABLED)
            self.output_entry.config(state=tk.DISABLED)
            for button in self.source_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    button.config(state=tk.DISABLED)
            for button in self.output_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    button.config(state=tk.DISABLED)
            
            # Disable extension filters
            for frame in self.file_types_frame.winfo_children():
                for widget in frame.winfo_children():
                    if isinstance(widget, (ttk.Checkbutton, ttk.Frame)):
                        if isinstance(widget, ttk.Frame):
                            for cb in widget.winfo_children():
                                if isinstance(cb, ttk.Checkbutton):
                                    cb.config(state=tk.DISABLED)
                        else:
                            widget.config(state=tk.DISABLED)
            
            # Disable template entries and exclude unknown checkboxes
            for media_type in ["audio", "video", "image", "ebook"]:
                self.template_entries[media_type].config(state=tk.DISABLED)
                
            # Disable preview controls
            for widget in self.preview_button_frame.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.config(state=tk.DISABLED)
            
            # Disable preview tree
            self.preview_tree.config(selectmode="none")
            
            # Reset progress indicators
            self.progress_var.set(0)
            self.status_var.set("Processing files...")
            self.file_var.set("")
        else:
            # Re-enable all interactive elements after processing
            # Enable main action buttons
            self.copy_button.config(state=tk.NORMAL)
            self.move_button.config(state=tk.NORMAL)
            # Disable stop button
            self.stop_button.config(state=tk.DISABLED)
            
            # Enable directory selection
            self.source_entry.config(state=tk.NORMAL)
            self.output_entry.config(state=tk.NORMAL)
            for button in self.source_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    button.config(state=tk.NORMAL)
            for button in self.output_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    button.config(state=tk.NORMAL)
            
            # Enable extension filters
            for frame in self.file_types_frame.winfo_children():
                for widget in frame.winfo_children():
                    if isinstance(widget, (ttk.Checkbutton, ttk.Frame)):
                        if isinstance(widget, ttk.Frame):
                            for cb in widget.winfo_children():
                                if isinstance(cb, ttk.Checkbutton):
                                    cb.config(state=tk.NORMAL)
                        else:
                            widget.config(state=tk.NORMAL)
            
            # Enable template entries and exclude unknown checkboxes
            for media_type in ["audio", "video", "image", "ebook"]:
                self.template_entries[media_type].config(state=tk.NORMAL)
                
            # Enable preview controls
            for widget in self.preview_button_frame.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.config(state=tk.NORMAL)
            
            # Enable preview tree
            self.preview_tree.config(selectmode="extended")
            
            # Reset the processing_selected_files flag
            self.processing_selected_files = False

    def _refresh_extension_filters(self):
        """Refresh the extension filter checkboxes based on current SUPPORTED_EXTENSIONS."""
        # Store current selections before clearing frames
        current_selections = {}
        current_all_selections = {}
        for file_type in ["audio", "video", "image", "ebook"]:
            current_selections[file_type] = {ext: var.get() for ext, var in self.extension_vars[file_type].items()}
            current_all_selections[file_type] = getattr(self, f"{file_type}_all_var").get()

        # Clear existing extension frames
        for frame in self.file_types_frame.winfo_children():
            frame.destroy()
        
        # Recreate extension frames for each file type
        for file_type, frame_title in [
            ("audio", "Audio"), ("video", "Video"), 
            ("image", "Image"), ("ebook", "eBook")
        ]:
            # Create frame
            type_frame = ttk.LabelFrame(self.file_types_frame, text=frame_title)
            type_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            # Create "Select All" checkbox
            # If parent was selected, keep new extensions selected
            all_selected = current_all_selections.get(file_type, True)
            all_var = tk.BooleanVar(value=all_selected)
            setattr(self, f"{file_type}_all_var", all_var)
            all_cb = ttk.Checkbutton(
                type_frame,
                text=f"All {frame_title}",
                variable=all_var,
                command=lambda ft=file_type: self._toggle_all_extensions(ft)
            )
            all_cb.pack(anchor=tk.W)
            
            # Create frame for extension checkboxes
            extensions_frame = ttk.Frame(type_frame)
            extensions_frame.pack(fill=tk.X, padx=10)
            
            # Clear existing extension vars for this type
            self.extension_vars[file_type] = {}
            
            # Create checkboxes for each extension
            for i, ext in enumerate(SUPPORTED_EXTENSIONS[file_type]):
                ext_name = ext.lstrip(".")
                # If parent was selected or extension existed and was selected, keep it selected
                selected = all_selected or current_selections.get(file_type, {}).get(ext, True)
                var = tk.BooleanVar(value=selected)
                self.extension_vars[file_type][ext] = var
                cb = ttk.Checkbutton(
                    extensions_frame,
                    text=ext_name,
                    variable=var,
                    command=self._update_extension_selection
                )
                cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=5)

    # Copy all methods from the original MediaOrganizerGUI class
    # ... existing code ... 