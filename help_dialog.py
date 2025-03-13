#!/usr/bin/env python3
"""
Help Dialog for the Media Organizer application.
Provides comprehensive help information about using the application.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
import defaults

class HelpDialog:
    """Dialog window showing help information for the Media Organizer application."""
    
    def __init__(self, parent):
        """Initialize the Help dialog.
        
        Args:
            parent: The parent window
        """
        # Create a new top-level window
        self.window = tk.Toplevel(parent)
        self.window.title(f"{defaults.APP_NAME} Help")
        self.window.geometry(defaults.DEFAULT_WINDOW_SIZES.get("help_window", "600x500"))
        self.window.minsize(600, 500)
        self.window.transient(parent)  # Make it a modal dialog
        self.window.grab_set()  # Make it modal
        
        # Center the window
        self.window.update_idletasks()
        width = 600
        height = 500
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create a frame for the content
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a notebook for different help sections
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs for different help sections
        self._create_getting_started_tab()
        self._create_templates_tab()
        self._create_file_types_tab()
        self._create_tips_tab()
        self._create_troubleshooting_tab()
        
        # Create a frame for the buttons at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Add a link to online documentation
        docs_link = ttk.Label(
            button_frame,
            text="Online Documentation",
            foreground="blue",
            cursor="hand2"
        )
        docs_link.pack(side=tk.LEFT, padx=5)
        docs_link.bind("<Button-1>", lambda e: webbrowser.open(defaults.APP_WEBSITE))
        
        # Add close button
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy
        )
        close_button.pack(side=tk.RIGHT, padx=5)
        
        # Set focus to the close button
        close_button.focus_set()
        
        # Bind Escape key to close the dialog
        self.window.bind("<Escape>", lambda e: self.window.destroy())
        
        # Make the dialog modal
        parent.wait_window(self.window)
    
    def _create_getting_started_tab(self):
        """Create the Getting Started tab with basic usage instructions."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Getting Started")
        
        # Create a scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = ttk.Label(
            scrollable_frame,
            text="Getting Started with Media Organizer",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(0, 10), anchor="w")
        
        # Introduction
        intro_text = (
            f"{defaults.APP_NAME} helps you organize your media files (audio, video, images, and eBooks) "
            "based on their metadata. This guide will help you get started with the basic features."
        )
        intro_label = ttk.Label(
            scrollable_frame,
            text=intro_text,
            wraplength=550,
            justify="left"
        )
        intro_label.pack(pady=(0, 15), anchor="w")
        
        # Basic steps
        steps_frame = ttk.LabelFrame(scrollable_frame, text="Basic Steps", padding=10)
        steps_frame.pack(fill="x", pady=(0, 15))
        
        steps = [
            ("1. Select Source Directory", 
             "Click the 'Browse...' button next to 'Source Directory' to select the folder containing your media files."),
            ("2. Select Output Directory", 
             "Click the 'Browse...' button next to 'Output Directory' to select where you want your organized files to be placed."),
            ("3. Choose File Types", 
             "Select which types of media files you want to organize by checking the appropriate boxes in the 'File Type Filters' section."),
            ("4. Configure Templates", 
             "Set up organization templates for each media type using the tabs in the 'Organization Templates' section."),
            ("5. Generate Preview", 
             "Click the 'Analyze' button to see a preview of how your files will be organized."),
            ("6. Start Organization", 
             "Click 'Copy Files' to copy files to the new structure, or 'Move Files' to move them.")
        ]
        
        for i, (title, description) in enumerate(steps):
            step_frame = ttk.Frame(steps_frame)
            step_frame.pack(fill="x", pady=(0 if i == 0 else 5, 0))
            
            step_title = ttk.Label(
                step_frame,
                text=title,
                font=("TkDefaultFont", 10, "bold")
            )
            step_title.pack(anchor="w")
            
            step_desc = ttk.Label(
                step_frame,
                text=description,
                wraplength=520,
                justify="left"
            )
            step_desc.pack(anchor="w", padx=(15, 0))
        
        # Interface overview
        interface_frame = ttk.LabelFrame(scrollable_frame, text="Interface Overview", padding=10)
        interface_frame.pack(fill="x", pady=(0, 15))
        
        interface_sections = [
            ("Source and Output Directories", 
             "At the top of the window, you can select the source directory (where your files are located) and the output directory (where organized files will be placed)."),
            ("File Type Filters", 
             "This section allows you to select which types of files to include in the organization process. You can select all files of a type or individual extensions."),
            ("Organization Templates", 
             "This section lets you define how files should be organized using placeholders for metadata. Different tabs allow you to set templates for each media type."),
            ("Preview", 
             "The central area shows a preview of how your files will be organized, with source and destination paths."),
            ("Progress", 
             "The bottom section shows progress information during the organization process.")
        ]
        
        for i, (title, description) in enumerate(interface_sections):
            section_frame = ttk.Frame(interface_frame)
            section_frame.pack(fill="x", pady=(0 if i == 0 else 5, 0))
            
            section_title = ttk.Label(
                section_frame,
                text=title,
                font=("TkDefaultFont", 10, "bold")
            )
            section_title.pack(anchor="w")
            
            section_desc = ttk.Label(
                section_frame,
                text=description,
                wraplength=520,
                justify="left"
            )
            section_desc.pack(anchor="w", padx=(15, 0))
    
    def _create_templates_tab(self):
        """Create the Templates tab with information about organization templates."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Templates")
        
        # Create a scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = ttk.Label(
            scrollable_frame,
            text="Organization Templates",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(0, 10), anchor="w")
        
        # Introduction
        intro_text = (
            "Templates determine how your files will be organized. They use placeholders (enclosed in curly braces) "
            "that will be replaced with actual metadata from your files. For example, {artist}/{album}/{filename} "
            "would organize music files by artist, then by album."
        )
        intro_label = ttk.Label(
            scrollable_frame,
            text=intro_text,
            wraplength=550,
            justify="left"
        )
        intro_label.pack(pady=(0, 15), anchor="w")
        
        # Common placeholders
        common_frame = ttk.LabelFrame(scrollable_frame, text="Common Placeholders", padding=10)
        common_frame.pack(fill="x", pady=(0, 15))
        
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
            placeholder_frame = ttk.Frame(common_frame)
            placeholder_frame.pack(fill="x", pady=(0 if i == 0 else 2, 0))
            
            placeholder_label = ttk.Label(
                placeholder_frame,
                text=placeholder,
                width=20,
                font=("TkDefaultFont", 9, "bold")
            )
            placeholder_label.pack(side="left")
            
            description_label = ttk.Label(
                placeholder_frame,
                text=description,
                wraplength=400,
                justify="left"
            )
            description_label.pack(side="left", padx=(5, 0))
        
        # Audio placeholders
        audio_frame = ttk.LabelFrame(scrollable_frame, text="Audio Placeholders", padding=10)
        audio_frame.pack(fill="x", pady=(0, 15))
        
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
            placeholder_frame = ttk.Frame(audio_frame)
            placeholder_frame.pack(fill="x", pady=(0 if i == 0 else 2, 0))
            
            placeholder_label = ttk.Label(
                placeholder_frame,
                text=placeholder,
                width=20,
                font=("TkDefaultFont", 9, "bold")
            )
            placeholder_label.pack(side="left")
            
            description_label = ttk.Label(
                placeholder_frame,
                text=description,
                wraplength=400,
                justify="left"
            )
            description_label.pack(side="left", padx=(5, 0))
        
        # Image placeholders
        image_frame = ttk.LabelFrame(scrollable_frame, text="Image Placeholders", padding=10)
        image_frame.pack(fill="x", pady=(0, 15))
        
        image_placeholders = [
            ("{width}", "Image width in pixels"),
            ("{height}", "Image height in pixels"),
            ("{format}", "Image format (e.g., JPEG, PNG)"),
            ("{camera_make}", "Camera manufacturer"),
            ("{camera_model}", "Camera model"),
            ("{date_taken}", "Date when the photo was taken"),
        ]
        
        for i, (placeholder, description) in enumerate(image_placeholders):
            placeholder_frame = ttk.Frame(image_frame)
            placeholder_frame.pack(fill="x", pady=(0 if i == 0 else 2, 0))
            
            placeholder_label = ttk.Label(
                placeholder_frame,
                text=placeholder,
                width=20,
                font=("TkDefaultFont", 9, "bold")
            )
            placeholder_label.pack(side="left")
            
            description_label = ttk.Label(
                placeholder_frame,
                text=description,
                wraplength=400,
                justify="left"
            )
            description_label.pack(side="left", padx=(5, 0))
        
        # eBook placeholders
        ebook_frame = ttk.LabelFrame(scrollable_frame, text="eBook Placeholders", padding=10)
        ebook_frame.pack(fill="x", pady=(0, 15))
        
        ebook_placeholders = [
            ("{title}", "Book title"),
            ("{author}", "Author name"),
            ("{year}", "Publication year"),
            ("{genre}", "Book genre"),
        ]
        
        for i, (placeholder, description) in enumerate(ebook_placeholders):
            placeholder_frame = ttk.Frame(ebook_frame)
            placeholder_frame.pack(fill="x", pady=(0 if i == 0 else 2, 0))
            
            placeholder_label = ttk.Label(
                placeholder_frame,
                text=placeholder,
                width=20,
                font=("TkDefaultFont", 9, "bold")
            )
            placeholder_label.pack(side="left")
            
            description_label = ttk.Label(
                placeholder_frame,
                text=description,
                wraplength=400,
                justify="left"
            )
            description_label.pack(side="left", padx=(5, 0))
        
        # Example templates
        example_frame = ttk.LabelFrame(scrollable_frame, text="Example Templates", padding=10)
        example_frame.pack(fill="x", pady=(0, 15))
        
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
            (
                "{author}/{title}/{filename}",
                "Organizes eBooks by author and title",
            ),
        ]
        
        for i, (template, description) in enumerate(examples):
            example_frame = ttk.Frame(example_frame)
            example_frame.pack(fill="x", pady=(0 if i == 0 else 5, 0))
            
            template_label = ttk.Label(
                example_frame,
                text=template,
                font=("TkDefaultFont", 9, "bold"),
                wraplength=250
            )
            template_label.pack(side="left", padx=(0, 10))
            
            description_label = ttk.Label(
                example_frame,
                text=description,
                wraplength=300,
                justify="left"
            )
            description_label.pack(side="left")
    
    def _create_file_types_tab(self):
        """Create the File Types tab with information about supported file types."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="File Types")
        
        # Title
        title_label = ttk.Label(
            tab,
            text="Supported File Types",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(0, 10), anchor="w")
        
        # Introduction
        intro_text = (
            f"{defaults.APP_NAME} supports various file types across different media categories. "
            "You can select which file types to include in the organization process using the checkboxes in the 'File Type Filters' section."
        )
        intro_label = ttk.Label(
            tab,
            text=intro_text,
            wraplength=550,
            justify="left"
        )
        intro_label.pack(pady=(0, 15), anchor="w")
        
        # File types by category
        categories = [
            ("Audio Files", 
             "Audio files contain music or other sound recordings. The application can extract metadata such as artist, album, title, and genre.",
             ["MP3", "FLAC", "M4A", "AAC", "OGG", "WAV"]),
            ("Video Files", 
             "Video files contain moving images and usually audio. The application can extract metadata such as title, duration, and creation date.",
             ["MP4", "MKV", "AVI", "MOV", "WMV"]),
            ("Image Files", 
             "Image files contain still pictures. The application can extract metadata such as dimensions, camera information, and date taken.",
             ["JPG/JPEG", "PNG", "GIF", "BMP", "TIFF"]),
            ("eBook Files", 
             "eBook files contain digital books. The application can extract metadata such as title, author, and publication date.",
             ["PDF", "EPUB", "MOBI", "AZW"])
        ]
        
        for category, description, formats in categories:
            category_frame = ttk.LabelFrame(tab, text=category, padding=10)
            category_frame.pack(fill="x", pady=(0, 15))
            
            # Description
            desc_label = ttk.Label(
                category_frame,
                text=description,
                wraplength=550,
                justify="left"
            )
            desc_label.pack(anchor="w", pady=(0, 10))
            
            # Formats
            formats_text = "Supported formats: " + ", ".join(formats)
            formats_label = ttk.Label(
                category_frame,
                text=formats_text,
                font=("TkDefaultFont", 9, "italic")
            )
            formats_label.pack(anchor="w")
    
    def _create_tips_tab(self):
        """Create the Tips & Tricks tab with helpful information."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Tips & Tricks")
        
        # Title
        title_label = ttk.Label(
            tab,
            text="Tips & Tricks",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(0, 10), anchor="w")
        
        # Introduction
        intro_text = (
            "Here are some helpful tips to get the most out of Media Organizer."
        )
        intro_label = ttk.Label(
            tab,
            text=intro_text,
            wraplength=550,
            justify="left"
        )
        intro_label.pack(pady=(0, 15), anchor="w")
        
        # Tips
        tips = [
            ("Preview Before Organizing", 
             "Always use the 'Analyze' button to preview how your files will be organized before starting the actual organization process."),
            ("Use Copy Instead of Move Initially", 
             "When first using the application, use the 'Copy Files' option instead of 'Move Files' to ensure your original files remain intact until you're confident with the results."),
            ("Customize Templates for Each Media Type", 
             "Different media types have different metadata. Use the tabs in the 'Organization Templates' section to set appropriate templates for each type."),
            ("Use the Placeholders Help", 
             "Click the 'Placeholders Help' button in the templates section to see all available placeholders and examples."),
            ("Save Your Settings", 
             "Your settings are automatically saved, but you can manually save them using Settings > Save Settings if you've made changes you want to keep."),
            ("Check the Logs", 
             "If something doesn't work as expected, check the logs (View > Show Logs) for more detailed information about what happened."),
            ("Auto-Preview", 
             "Enable auto-preview in the preferences to automatically see how your files will be organized whenever you change settings."),
            ("Organize by Date", 
             "For photos and videos, organizing by creation date (e.g., {creation_year}/{creation_month_name}) is often a good approach."),
            ("Organize Music by Metadata", 
             "For music files, organizing by artist and album (e.g., {artist}/{album}) helps keep your collection well-structured."),
            ("Use Full Paths", 
             "Enable 'Show Full Paths' in the preferences to see the complete file paths in the preview.")
        ]
        
        for i, (title, description) in enumerate(tips):
            tip_frame = ttk.Frame(tab)
            tip_frame.pack(fill="x", pady=(0 if i == 0 else 10, 0))
            
            tip_title = ttk.Label(
                tip_frame,
                text=title,
                font=("TkDefaultFont", 10, "bold")
            )
            tip_title.pack(anchor="w")
            
            tip_desc = ttk.Label(
                tip_frame,
                text=description,
                wraplength=550,
                justify="left"
            )
            tip_desc.pack(anchor="w", padx=(15, 0))
    
    def _create_troubleshooting_tab(self):
        """Create the Troubleshooting tab with solutions to common problems."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Troubleshooting")
        
        # Title
        title_label = ttk.Label(
            tab,
            text="Troubleshooting",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(0, 10), anchor="w")
        
        # Introduction
        intro_text = (
            "If you encounter issues while using Media Organizer, here are solutions to some common problems."
        )
        intro_label = ttk.Label(
            tab,
            text=intro_text,
            wraplength=550,
            justify="left"
        )
        intro_label.pack(pady=(0, 15), anchor="w")
        
        # Common problems
        problems = [
            ("No Files Found", 
             "If no files are found in the source directory, check that you've selected the correct directory and that you've enabled the appropriate file types in the 'File Type Filters' section."),
            ("Missing Metadata", 
             "If metadata is missing (shown as 'Unknown' in the organized path), the file may not contain that metadata. Try using different placeholders in your template."),
            ("Organization Process is Slow", 
             "Processing large numbers of files, especially video files, can take time. Be patient, and check the progress indicator at the bottom of the window."),
            ("Application Freezes", 
             "If the application appears to freeze during organization, it may be processing a large file. Check the logs (View > Show Logs) for more information."),
            ("Destination Path Already Exists", 
             "If a file with the same name already exists at the destination, the application will append a number to the filename to avoid overwriting."),
            ("Permission Errors", 
             "If you encounter permission errors, make sure you have the necessary permissions to read from the source directory and write to the output directory."),
            ("Metadata Not Extracted Correctly", 
             "Some files may have incomplete or incorrect metadata. You can use tools like MP3Tag (for audio) or ExifTool (for images) to fix the metadata before organizing."),
            ("Application Crashes", 
             "If the application crashes, check the log file (media_organizer.log) for error messages. You may need to install additional dependencies for certain file types."),
            ("Templates Not Working", 
             "Make sure your templates use valid placeholders enclosed in curly braces {}. Check the 'Templates' tab in this help dialog for a list of valid placeholders.")
        ]
        
        for i, (title, description) in enumerate(problems):
            problem_frame = ttk.Frame(tab)
            problem_frame.pack(fill="x", pady=(0 if i == 0 else 10, 0))
            
            problem_title = ttk.Label(
                problem_frame,
                text=title,
                font=("TkDefaultFont", 10, "bold")
            )
            problem_title.pack(anchor="w")
            
            problem_desc = ttk.Label(
                problem_frame,
                text=description,
                wraplength=550,
                justify="left"
            )
            problem_desc.pack(anchor="w", padx=(15, 0)) 