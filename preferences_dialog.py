#!/usr/bin/env python3
"""
Preferences Dialog module for Media Organizer application.
Provides a dialog for managing application preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox

# Import the extensions module
import extensions

class PreferencesDialog:
    """Dialog for managing application preferences."""
    
    def __init__(self, parent, app, supported_extensions):
        """
        Initialize the preferences dialog.
        
        Args:
            parent: The parent window
            app: The main application instance
            supported_extensions: The dictionary of supported file extensions
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Preferences")
        self.dialog.geometry("600x500")
        self.dialog.minsize(600, 500)
        self.dialog.transient(parent)  # Make it a modal dialog
        self.dialog.grab_set()  # Make it modal
        
        # Store reference to main app and extensions
        self.app = app
        self.supported_extensions = supported_extensions
        
        # Center the window
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create the main content frame
        self.content_frame = ttk.Frame(self.dialog, padding=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create General tab
        self.general_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.general_frame, text="General")
        
        # Auto-preview option
        self.auto_preview_var = tk.BooleanVar(value=self.app.auto_preview_enabled)
        auto_preview_cb = ttk.Checkbutton(
            self.general_frame,
            text="Automatically generate preview when settings change",
            variable=self.auto_preview_var
        )
        auto_preview_cb.pack(anchor=tk.W, pady=5)
        
        # Auto-save option
        self.auto_save_var = tk.BooleanVar(value=getattr(self.app, 'auto_save_enabled', True))
        auto_save_cb = ttk.Checkbutton(
            self.general_frame,
            text="Automatically save settings when inputs change",
            variable=self.auto_save_var
        )
        auto_save_cb.pack(anchor=tk.W, pady=5)
        
        # Full path display option
        self.show_full_paths_var = tk.BooleanVar(value=getattr(self.app, 'show_full_paths', False))
        full_paths_cb = ttk.Checkbutton(
            self.general_frame,
            text="Show full file paths in preview",
            variable=self.show_full_paths_var
        )
        full_paths_cb.pack(anchor=tk.W, pady=5)
        
        # Create File Types tab
        self.file_types_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.file_types_frame, text="File Types")
        
        # Create sub-notebook for file type tabs
        self.file_types_notebook = ttk.Notebook(self.file_types_frame)
        self.file_types_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create text variables for extensions
        self.extension_texts = {}
        
        # Create sub-tabs for each media type
        for media_type in ["audio", "video", "image", "ebook"]:
            frame = ttk.Frame(self.file_types_notebook, padding=10)
            self.file_types_notebook.add(frame, text=media_type.title())
            
            # Add description label
            ttk.Label(
                frame,
                text=f"Enter file extensions for {media_type} files (one per line, with or without dot):",
                wraplength=400
            ).pack(anchor=tk.W, pady=(0, 5))
            
            # Create text widget with scrollbar for extensions
            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            text_widget = tk.Text(text_frame, height=10, width=40)
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Get current extensions and format them
            current_extensions = [ext.lstrip(".") for ext in self.supported_extensions[media_type]]
            text_widget.insert("1.0", "\n".join(current_extensions))
            
            self.extension_texts[media_type] = text_widget
            
            # Add a "Reset to Default" button
            reset_button = ttk.Button(
                frame, 
                text="Reset to Default", 
                command=lambda m=media_type: self._reset_extensions_to_default(m)
            )
            reset_button.pack(anchor=tk.E, pady=5)
        
        # Create buttons frame
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Add Save and Cancel buttons
        save_button = ttk.Button(buttons_frame, text="Save", command=self._save_preferences)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(buttons_frame, text="Cancel", command=self.dialog.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
    def _reset_extensions_to_default(self, media_type):
        """Reset extensions for a media type to default values."""
        # Get default extensions from the extensions module
        default_extensions = [ext.lstrip(".") for ext in extensions.DEFAULT_EXTENSIONS[media_type]]
        
        # Clear the text widget
        self.extension_texts[media_type].delete("1.0", tk.END)
        
        # Insert default extensions
        self.extension_texts[media_type].insert("1.0", "\n".join(default_extensions))
    
    def _save_preferences(self):
        """Save preferences and update the main application."""
        # Update app settings
        self.app.auto_preview_enabled = self.auto_preview_var.get()
        self.app.auto_save_enabled = self.auto_save_var.get()
        self.app.show_full_paths = self.show_full_paths_var.get()
        
        # Update extensions
        new_extensions = {}
        for media_type, text_widget in self.extension_texts.items():
            # Get extensions from text widget
            extensions_text = text_widget.get("1.0", "end-1c").split("\n")
            # Clean up extensions (remove empty lines, add dot if missing)
            extensions_list = [ext.strip() for ext in extensions_text if ext.strip()]
            extensions_list = [ext if ext.startswith(".") else f".{ext}" for ext in extensions_list]
            new_extensions[media_type] = extensions_list
        
        # Return the result as a dictionary
        return {
            'extensions': new_extensions
        } 