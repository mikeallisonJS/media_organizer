#!/usr/bin/env python3
"""
ArchimediusGUI - GUI module for the Archimedius application.
Provides the main application window and user interface components.
"""

import os
import logging
import threading
import copy
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from ttkbootstrap import Style

# Import application modules
import defaults
from settings import (
    MEDIA_TYPES,
    collect_settings_from_gui,
    default_settings,
    load_settings,
    save_settings,
    settings_path,
    sync_gui_from_settings,
)
from log_window import LogWindow
from run_state import RunState
from organize_plan import (
    CollisionAction,
    scan_source,
)
from organize_run import (
    OrganizeRequest,
    OrganizeRunError,
    OrganizeRunNotice,
    prepare_destination_root,
    run_organize,
    validate_request,
)
from about_dialog import AboutDialog
from collision_dialog import CollisionPromptDialog
from gui.extension_filter_panel import ExtensionFilterPanel
from gui.preferences_panel import PreferencesPanel
from gui.preview_panel import PreviewPanel
from gui.template_panel import TemplatePanel
from help_dialog import HelpDialog

# Configure logging
logger = logging.getLogger("Archimedius")


class ArchimediusGUI:
    """GUI for the Archimedius application."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title(defaults.APP_NAME)
        self.root.geometry(defaults.DEFAULT_WINDOW_SIZES["main_window"])  # Increase default height
        self.root.minsize(800, 800)    # Ensure minimum size
        
        # Run-only state for the current organize/preview run
        self.run_state = RunState()

        # Settings model (extensions and persisted prefs)
        self.settings = default_settings()
        sync_gui_from_settings(self, self.settings)
        self.style = Style()
        
        # Config file path
        self.config_file = settings_path()
        
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

    @property
    def _full_preview_data(self):
        return self.preview_panel.full_preview_data

    @_full_preview_data.setter
    def _full_preview_data(self, value):
        self.preview_panel.full_preview_data = value

    @property
    def _full_preview_count(self):
        return self.preview_panel.full_preview_count

    @_full_preview_count.setter
    def _full_preview_count(self, value):
        self.preview_panel.full_preview_count = value

    def apply_theme(self, dark_mode):
        """Apply ttkbootstrap theme based on dark mode."""
        self.dark_mode = bool(dark_mode)
        theme_name = "darkly" if self.dark_mode else "litera"

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
        self.status_var.set("Ready")
        
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

        self.extension_filter_panel = ExtensionFilterPanel(self)
        self.extension_filter_panel.build(file_types_tab)

        self.template_panel = TemplatePanel(self)
        self.template_panel.build(templates_tab)

        self.preview_panel = PreviewPanel(self)
        self.preview_panel.build(preview_tab)

        self.preferences_panel = PreferencesPanel(self)
        self.preferences_panel.build(preferences_tab)

    def _toggle_logs(self):
        """Toggle the visibility of the log window."""
        if self.log_window.window.winfo_viewable():
            self.log_window.hide()
        else:
            self.log_window.show()

    def _create_collision_resolver(self):
        """Build a thread-safe collision resolver for prompt policy during a run."""
        run_state = {"action": None, "apply_all": False}
        state_lock = threading.Lock()

        def resolver(plan, destination_path) -> CollisionAction:
            with state_lock:
                if run_state["apply_all"] and run_state["action"] is not None:
                    return run_state["action"]

            result: dict[str, CollisionAction | None] = {"action": None}
            done = threading.Event()

            def show_dialog() -> None:
                action, apply_all = CollisionPromptDialog(
                    self.root,
                    source_path=plan.source_path,
                    destination_path=destination_path,
                ).show()
                result["action"] = action
                if apply_all:
                    with state_lock:
                        run_state["action"] = action
                        run_state["apply_all"] = True
                done.set()

            self.root.after(0, show_dialog)
            done.wait()
            return result["action"] or defaults.COLLISION_POLICY_SKIP

        return resolver

    def _collision_resolver_for_policy(self, collision_policy):
        """A prompt resolver when the policy asks, otherwise None."""
        if collision_policy == defaults.COLLISION_POLICY_PROMPT:
            return self._create_collision_resolver()
        return None

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
        """Clear the preview list and stored preview data."""
        self.preview_panel.clear()

    def _update_progress(self, processed, total, current_file):
        """Update the progress display."""
        if total > 0:
            progress = (processed / total) * 100
            self.progress_var.set(progress)
            
            self.status_var.set(f"Processed: {processed}/{total} files ({progress:.1f}%)")
            
            if current_file == "Complete":
                self.file_var.set("Organization complete!")
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
    
    def _generate_preview(self):
        """Generate a preview of the organization."""
        # Validate inputs
        source_dir = self.source_entry.get().strip()
        output_dir = self.output_entry.get().strip()

        # Get templates for each media type
        templates = self._get_template_settings()

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
            output_root = Path(output_dir) if output_dir else None

            # Get selected extensions
            selected_extensions = self._get_selected_extensions()
            if not selected_extensions:
                # Update UI in the main thread
                self.root.after(0, lambda: self._update_preview_status("No file types selected. Please select at least one file type."))
                return

            source_path = Path(source_dir)
            exclude_unknown = self._get_exclude_unknown_settings()

            self.root.after(0, lambda: self.status_var.set("Counting files..."))

            scan_result = scan_source(
                source_path,
                output_dir or None,
                templates,
                self.settings.supported_extensions,
                selected_extensions,
                exclude_unknown,
                max_files=100,
            )
            total_files = scan_result.total_count
            processed = len(scan_result.plans)

            if total_files > 0:
                progress = (processed / total_files) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(
                    0,
                    lambda p=processed, t=total_files: self.file_var.set(f"Found {p} of {t} files..."),
                )

            self.root.after(0, lambda: self.status_var.set("Finding file details..."))

            preview_data = []
            for plan in scan_result.plans:
                try:
                    file_path = plan.source_path
                    rel_path = plan.destination_path

                    if getattr(self, "show_full_paths", False):
                        display_source = str(file_path)
                        if output_root:
                            display_dest = str(output_root / rel_path)
                        else:
                            display_dest = rel_path
                    else:
                        try:
                            display_source = str(file_path.relative_to(source_path))
                            display_dest = rel_path
                        except ValueError:
                            display_source = str(file_path)
                            if output_root:
                                display_dest = str(output_root / rel_path)
                            else:
                                display_dest = rel_path

                    preview_data.append((display_source, display_dest, str(file_path)))
                except Exception as e:
                    logger.error(f"Error generating preview for {plan.source_path}: {e}")

            self.root.after(0, lambda: self._update_preview_results(preview_data, processed))

        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            # Update UI in the main thread
            self.root.after(
                0,
                lambda err=e: self._update_preview_status(
                    f"Preview generation failed: {str(err)}",
                    error=True,
                ),
            )
        finally:
            # Reset progress bar
            self.root.after(0, lambda: self.progress_var.set(0))

    def _update_preview_results(self, preview_data, count):
        """Update the preview treeview with results from the preview thread."""
        self.preview_panel.update_results(preview_data, count)

    def _display_preview_data(self, preview_data, count):
        """Populate the preview treeview with the given data and update status."""
        self.preview_panel.display(preview_data, count)

    def _filter_preview(self):
        """Re-filter stored preview data by currently selected extensions and refresh the tree."""
        self.preview_panel.filter_by_selected_extensions()

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
        self.extension_filter_panel.toggle_all(file_type)

    def _update_extension_selection(self):
        """Update the 'All' checkboxes based on individual selections."""
        self.extension_filter_panel.update_selection()

    def _get_selected_extensions(self):
        """Get a list of all selected file extensions."""
        return self.extension_filter_panel.get_selected_extensions()

    def _get_exclude_unknown_settings(self):
        """Return per-media-type exclude-unknown flags from the GUI."""
        return self.template_panel.get_exclude_unknown_settings()

    def _get_template_settings(self):
        """Return current path templates for all media types."""
        return self.template_panel.get_template_settings()

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
        """Start an Organize run over a full source scan."""
        request = self._prepare_organize_run(mode)
        if request is None:
            return

        # Operation mode for this run (also persisted via settings below)
        self.operation_mode = mode
        self._save_settings()
        self._log_organize_request(request)

        self._begin_organize_run(request)

    def _build_organize_request(self, mode, selected_paths=None):
        """Build an OrganizeRequest from the current GUI state."""
        return OrganizeRequest(
            source_dir=self.source_entry.get().strip(),
            destination_dir=self.output_entry.get().strip(),
            operation_mode=mode,
            templates=self._get_template_settings(),
            supported_extensions=self.settings.supported_extensions,
            selected_extensions=self._get_selected_extensions(),
            exclude_unknown=self._get_exclude_unknown_settings(),
            selected_paths=selected_paths,
            collision_policy=getattr(
                self,
                "collision_policy",
                defaults.DEFAULT_SETTINGS["collision_policy"],
            ),
        )

    def _prepare_organize_run(self, mode, selected_paths=None):
        """
        Validate the run and confirm it with the user.

        Returns the request to run, or None when the run should not start.
        """
        request = self._build_organize_request(mode, selected_paths)

        try:
            validate_request(request)
        except OrganizeRunNotice as notice:
            messagebox.showinfo("Info", str(notice))
            return None
        except OrganizeRunError as error:
            messagebox.showerror("Error", str(error))
            return None

        # Confirm before creating anything, so declining leaves no empty destination.
        if not self._confirm_move(request):
            return None

        try:
            prepare_destination_root(request)
        except OrganizeRunError as error:
            messagebox.showerror("Error", str(error))
            return None

        return request

    def _confirm_move(self, request):
        """Ask the user to confirm a move run. Copy runs need no confirmation."""
        if request.operation_mode != "move":
            return True

        if request.is_selection_run:
            message = (
                f"Moving {len(request.selected_paths)} files will remove them "
                "from the source directory. Continue?"
            )
        else:
            message = "Moving files will remove them from the source directory. Continue?"

        return messagebox.askyesno("Confirm Move Operation", message)

    def _log_organize_request(self, request):
        """Log the settings this Organize run will use."""
        logger.info(f"Source directory: {request.source_dir}")
        logger.info(f"Output directory: {request.destination_dir}")
        logger.info(f"Operation mode: {request.operation_mode}")
        for media_type, template in request.templates.items():
            logger.info(f"Using {media_type} template: {template}")
        logger.info(f"Selected extensions: {', '.join(request.selected_extensions)}")

    def _begin_organize_run(self, request):
        """Start an Organize run on a background thread."""
        self.run_state.begin()
        self._update_ui_for_processing(True)

        # A source scan run replaces whatever the preview last showed.
        if not request.is_selection_run:
            self._clear_preview()

        threading.Thread(
            target=self._organize_run_thread,
            args=(request,),
            daemon=True,
        ).start()

    def _organize_run_thread(self, request):
        """Run the Organize run off the UI thread and report back to it."""
        try:
            result = run_organize(
                request,
                collision_resolver=self._collision_resolver_for_policy(request.collision_policy),
                should_stop=lambda: self.run_state.stop_requested,
                on_progress=self._report_organize_progress,
            )
            self.run_state.files_processed = result.successful
            self.root.after(0, lambda r=result: self._organize_run_complete(request, r))
        except OrganizeRunError as error:
            logger.error(f"Cannot run organization: {error}")
            self.root.after(0, lambda msg=str(error): self._organize_run_failed(msg))
        except Exception as e:
            logger.error(f"Error during organization: {e}")
            message = str(e) or "Unknown error"
            self.root.after(
                0,
                lambda msg=message: self._organize_run_failed(
                    f"An error occurred during organization: {msg}"
                ),
            )
        finally:
            self.run_state.is_running = False

    def _report_organize_progress(self, processed, total, current_file):
        """Marshal progress from the run thread onto the UI thread."""
        self.root.after(
            0,
            lambda p=processed, t=total, f=current_file: self._update_progress(p, t, f),
        )

    def _organize_run_complete(self, request, result):
        """Handle Organize run completion on the UI thread."""
        self._update_ui_for_processing(False)
        self._update_progress(result.attempted, result.total_count, "Complete")

        operation_past = "copied" if request.operation_mode == "copy" else "moved"
        messagebox.showinfo(
            "Complete",
            f"Organization complete!\n\n{operation_past.capitalize()} {result.successful} files.",
        )

        # Moved files are gone from the source, so the preview list is stale.
        if request.is_selection_run and request.operation_mode == "move" and result.successful:
            self.root.after(500, self._generate_preview)

    def _organize_run_failed(self, message):
        """Handle a failed Organize run on the UI thread."""
        self._update_ui_for_processing(False)
        self.status_var.set("Organization failed")
        messagebox.showerror("Error", message)

    def _stop_organization(self):
        """Stop the organization process."""
        if self.run_state.is_running:
            self.run_state.stop()
            self.status_var.set("Stopping...")
            logger.info("Stopping organization process...")

    def _save_settings(self):
        """Save user settings to a configuration file."""
        try:
            self.settings = collect_settings_from_gui(self)
            save_settings(self.settings, self.config_file)
            sync_gui_from_settings(self, self.settings)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def _apply_settings_to_widgets(self, settings):
        """Apply a Settings instance to GUI widgets."""
        if settings.window_geometry:
            try:
                self.root.geometry(settings.window_geometry)
            except Exception as e:
                logger.warning(f"Could not restore saved window size: {e}")

        if settings.source_dir:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, settings.source_dir)

        if settings.output_dir:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, settings.output_dir)

        self.template_panel.apply_settings(settings)
        self._refresh_extension_filters()
        self.extension_filter_panel.apply_settings(settings)

        self.apply_theme(settings.dark_mode)
        self.preferences_panel.apply_settings(settings)

    def _load_settings(self):
        """Load user settings from the configuration file."""
        try:
            self.settings = load_settings(self.config_file)
            sync_gui_from_settings(self, self.settings)
            if self.config_file.exists():
                self._apply_settings_to_widgets(self.settings)
                logger.info(f"Settings loaded from {self.config_file}")
                self._auto_generate_preview()
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

                self.template_panel.reset_to_defaults()
                self.extension_filter_panel.reset_all_selected()

                self.settings = default_settings()
                sync_gui_from_settings(self, self.settings)
                self.settings.supported_extensions = copy.deepcopy(defaults.DEFAULT_EXTENSIONS)
                self._refresh_extension_filters()
                self.apply_theme(self.dark_mode)
                self.preferences_panel.apply_settings(self.settings)
                
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

    def _toggle_selection(self, event):
        """Toggle selection of a file in the preview treeview when clicked."""
        self.preview_panel.toggle_selection(event)

    def _select_all_files(self):
        """Select all files in the preview treeview."""
        self.preview_panel.select_all_files()

    def _deselect_all_files(self):
        """Deselect all files in the preview treeview."""
        self.preview_panel.deselect_all_files()

    def _process_selected_files(self, mode):
        """Start an Organize run over the files selected in the preview."""
        selected_paths = [
            data["full_path"]
            for data in self.preview_panel.preview_files.values()
            if data["selected"]
        ]

        request = self._prepare_organize_run(mode, selected_paths=selected_paths)
        if request is None:
            return

        # Operation mode for this run
        self.operation_mode = mode

        self._begin_organize_run(request)

    def _update_ui_for_processing(self, is_processing):
        """Update the UI elements for processing state."""
        if is_processing:
            self.copy_button.config(state=tk.DISABLED)
            self.move_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            self.source_entry.config(state=tk.DISABLED)
            self.output_entry.config(state=tk.DISABLED)
            for button in self.source_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    button.config(state=tk.DISABLED)
            for button in self.output_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    button.config(state=tk.DISABLED)

            self.extension_filter_panel.set_enabled(False)
            self.template_panel.set_enabled(False)
            self.preview_panel.set_processing_state(True)

            self.progress_var.set(0)
            self.status_var.set("Processing files...")
            self.file_var.set("")
        else:
            self.copy_button.config(state=tk.NORMAL)
            self.move_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

            self.source_entry.config(state=tk.NORMAL)
            self.output_entry.config(state=tk.NORMAL)
            for button in self.source_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    button.config(state=tk.NORMAL)
            for button in self.output_frame.winfo_children():
                if isinstance(button, ttk.Button):
                    button.config(state=tk.NORMAL)

            self.extension_filter_panel.set_enabled(True)
            self.template_panel.set_enabled(True)
            self.preview_panel.set_processing_state(False)

    def _refresh_extension_filters(self):
        """Refresh the extension filter checkboxes based on current supported extensions."""
        self.extension_filter_panel.refresh()
