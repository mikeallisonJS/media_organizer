#!/usr/bin/env python3
"""
About Dialog for the Archimedius application.
Displays information about the application, version, and credits.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
import defaults

class AboutDialog:
    """Dialog window showing information about the Archimedius application."""
    
    def __init__(self, parent):
        """Initialize the About dialog.
        
        Args:
            parent: The parent window
        """
        # Create a new top-level window
        self.window = tk.Toplevel(parent)
        self.window.title(f"About {defaults.APP_NAME}")
        self.window.geometry(defaults.DEFAULT_WINDOW_SIZES.get("about_dialog", "500x375"))
        self.window.minsize(500, 375)
        self.window.maxsize(500, 375)
        self.window.resizable(False, False)  # Disable resizing
        self.window.transient(parent)  # Make it a modal dialog
        self.window.grab_set()  # Make it modal
        
        # Center the window
        self.window.update_idletasks()
        width = 500
        height = 375
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create a frame for the content
        content_frame = ttk.Frame(self.window, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Application name
        app_name_label = ttk.Label(
            content_frame, 
            text=defaults.APP_NAME, 
            font=("TkDefaultFont", 16, "bold")
        )
        app_name_label.pack(pady=(0, 5))
        
        # Version
        version_label = ttk.Label(
            content_frame, 
            text=f"Version {defaults.APP_VERSION}",
            font=("TkDefaultFont", 10)
        )
        version_label.pack(pady=(0, 20))
        
        # Description
        description_text = (
            f"{defaults.APP_NAME} is a tool to organize media files based on their metadata. "
            "It can organize audio, video, image, and eBook files into a structured directory "
            "hierarchy using customizable templates."
        )
        description_label = ttk.Label(
            content_frame, 
            text=description_text,
            wraplength=400,
            justify=tk.CENTER
        )
        description_label.pack(pady=(0, 20))
        
        # Credits
        credits_label = ttk.Label(
            content_frame, 
            text=f"Created by {defaults.APP_AUTHOR}",
            font=("TkDefaultFont", 9)
        )
        credits_label.pack(pady=(20, 5))
        
        # Copyright
        copyright_label = ttk.Label(
            content_frame, 
            text="© 2025 All Rights Reserved",
            font=("TkDefaultFont", 9)
        )
        copyright_label.pack(pady=(0, 10))
        
        # Contact information frame
        contact_frame = ttk.Frame(content_frame)
        contact_frame.pack(pady=(0, 20))
        
        # Website link
        website_frame = ttk.Frame(contact_frame)
        website_frame.pack(fill=tk.X, pady=2)
        
        website_label = ttk.Label(
            website_frame, 
            text="Website:",
            font=("TkDefaultFont", 9),
            width=10,
            anchor=tk.E
        )
        website_label.pack(side=tk.LEFT, padx=(0, 5))
        
        website_link = ttk.Label(
            website_frame, 
            text=defaults.APP_WEBSITE,
            font=("TkDefaultFont", 9),
            foreground="#4A9EFF",
            cursor="hand2"
        )
        website_link.pack(side=tk.LEFT)
        website_link.bind("<Button-1>", lambda e: webbrowser.open(defaults.APP_WEBSITE))
        
        # Close button
        close_button = ttk.Button(
            content_frame, 
            text="Close", 
            command=self.window.destroy
        )
        close_button.pack(pady=(10, 0))
        
        # Set focus to the close button
        close_button.focus_set()
        
        # Bind Escape key to close the dialog
        self.window.bind("<Escape>", lambda e: self.window.destroy())
        
        # Make the dialog modal
        parent.wait_window(self.window) 