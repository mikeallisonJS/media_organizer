#!/usr/bin/env python3
"""
Log Window module for Media Organizer application.
Provides a separate window for displaying and managing application logs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

class LogWindow:
    """Separate window for displaying logs."""
    
    def __init__(self, parent, logger):
        """
        Initialize the log window.
        
        Args:
            parent: The parent window
            logger: The logger instance to use
        """
        self.parent = parent
        self.logger = logger
        self.window = tk.Toplevel(parent)
        self.window.title("Media Organizer Logs")
        self.window.geometry("600x400")
        self.window.minsize(400, 300)
        
        # Configure the window to be hidden instead of destroyed when closed
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        
        # Create main container frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the log text widget
        self.log_text = tk.Text(main_frame, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Add button frame at the bottom
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Add shortcut label
        shortcut_label = ttk.Label(button_frame, text="Shortcut: Ctrl+L")
        shortcut_label.pack(side=tk.LEFT, padx=5)
        
        # Add Clear Logs button
        clear_button = ttk.Button(
            button_frame, text="Clear Logs", command=self.clear_logs
        )
        clear_button.pack(side=tk.RIGHT)
        
        # Add tooltip to the Clear Logs button
        self._create_tooltip(clear_button, "Clear all log entries (this cannot be undone)")
        
        # Add keyboard shortcut (Ctrl+L) to clear logs
        self.window.bind("<Control-l>", lambda event: self.clear_logs())
        
        # Configure logging to text widget
        self._setup_text_logging()
        
        # Initially hide the window
        self.hide()
    
    def _setup_text_logging(self):
        """Set up logging to the text widget."""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)

                def append():
                    self.text_widget.configure(state="normal")
                    self.text_widget.insert(tk.END, msg + "\n")
                    self.text_widget.see(tk.END)
                    self.text_widget.configure(state="disabled")

                # Schedule the append operation on the GUI thread
                self.text_widget.after(0, append)

        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(text_handler)

        # Disable editing
        self.log_text.configure(state="disabled")
    
    def clear_logs(self):
        """Clear the log text widget."""
        # Show confirmation dialog
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all logs?"):
            self.log_text.configure(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.configure(state="disabled")
            self.logger.info("Log window cleared")
    
    def show(self):
        """Show the log window."""
        self.window.deiconify()
        self.window.lift()
    
    def hide(self):
        """Hide the log window."""
        self.window.withdraw()

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, justify=tk.LEFT,
                             background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                             wraplength=250)
            label.pack(padx=3, pady=3)
            
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave) 