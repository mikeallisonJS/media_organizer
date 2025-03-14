#!/usr/bin/env python3
"""
License Manager for Archimedius.
Handles license verification, activation, and trial management.
"""

import os
import json
import uuid
import hashlib
import logging
import platform
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import webbrowser
import time

import defaults

# Configure logging
logger = logging.getLogger("Archimedius")

class LicenseManager:
    """Manages license verification and activation for Archimedius."""
    
    def __init__(self):
        """Initialize the license manager."""
        self.license_file = Path.home() / defaults.DEFAULT_PATHS.get("license_file", "media_organizer_license.json")
        self.license_data = None
        self.is_licensed = False
        self.trial_mode = False
        self.trial_days_left = 0
        self.machine_id = self._get_machine_id()
        
        # Load license data if it exists
        self._load_license()
        
        # Verify the license
        self._verify_license()
    
    def _get_machine_id(self):
        """Generate a unique machine ID based on hardware information."""
        try:
            # Get system information
            system_info = platform.uname()
            
            # Create a unique identifier based on system information
            machine_id = f"{system_info.node}-{system_info.machine}-{system_info.processor}"
            
            # Hash the identifier to create a consistent ID
            return hashlib.sha256(machine_id.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating machine ID: {e}")
            # Fallback to a random UUID if we can't get system info
            return str(uuid.uuid4())
    
    def _load_license(self):
        """Load license data from the license file."""
        try:
            if self.license_file.exists():
                with open(self.license_file, "r") as f:
                    self.license_data = json.load(f)
                logger.info("License data loaded successfully")
            else:
                logger.info("No license file found")
                self.license_data = None
        except Exception as e:
            logger.error(f"Error loading license data: {e}")
            self.license_data = None
    
    def _save_license(self):
        """Save license data to the license file."""
        try:
            with open(self.license_file, "w") as f:
                json.dump(self.license_data, f)
            logger.info("License data saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving license data: {e}")
            return False
    
    def _verify_license(self):
        """Verify the loaded license data."""
        if not self.license_data:
            self._check_trial_eligibility()
            return
        
        try:
            # Check if license is for this product
            if self.license_data.get("product") != "Archimedius":
                logger.warning("Invalid license: wrong product")
                self.is_licensed = False
                self._check_trial_eligibility()
                return
            
            # Check if license is expired
            import datetime
            expiry_date = self.license_data.get("expiry_date")
            if expiry_date:
                expiry = datetime.datetime.fromisoformat(expiry_date)
                if expiry < datetime.datetime.now():
                    logger.warning("License expired")
                    self.is_licensed = False
                    self._check_trial_eligibility()
                    return
            
            # Check if license is for this machine
            registered_machines = self.license_data.get("machines", [])
            if self.machine_id not in registered_machines:
                # If we have fewer than the allowed number of machines, add this one
                max_machines = self.license_data.get("max_machines", 2)
                if len(registered_machines) < max_machines:
                    registered_machines.append(self.machine_id)
                    self.license_data["machines"] = registered_machines
                    self._save_license()
                    logger.info("Added current machine to license")
                else:
                    logger.warning("License already used on maximum number of machines")
                    self.is_licensed = False
                    self._check_trial_eligibility()
                    return
            
            # If we get here, the license is valid
            self.is_licensed = True
            logger.info("License verified successfully")
            
        except Exception as e:
            logger.error(f"Error verifying license: {e}")
            self.is_licensed = False
            self._check_trial_eligibility()
    
    def _check_trial_eligibility(self):
        """Check if the user is eligible for a trial period."""
        try:
            trial_file = Path.home() / defaults.DEFAULT_PATHS.get("trial_file", "media_organizer_trial.json")
            
            if trial_file.exists():
                # Load trial data
                with open(trial_file, "r") as f:
                    trial_data = json.load(f)
                
                # Check if trial is still valid
                import datetime
                start_date = datetime.datetime.fromisoformat(trial_data.get("start_date"))
                trial_length = trial_data.get("trial_length", 30)  # Default 30 days
                end_date = start_date + datetime.timedelta(days=trial_length)
                
                if datetime.datetime.now() < end_date:
                    self.trial_mode = True
                    self.trial_days_left = (end_date - datetime.datetime.now()).days
                    logger.info(f"Trial mode active: {self.trial_days_left} days left")
                else:
                    self.trial_mode = False
                    logger.info("Trial period expired")
            else:
                # Start a new trial
                import datetime
                trial_data = {
                    "start_date": datetime.datetime.now().isoformat(),
                    "trial_length": 30,
                    "machine_id": self.machine_id
                }
                
                with open(trial_file, "w") as f:
                    json.dump(trial_data, f)
                
                self.trial_mode = True
                self.trial_days_left = 30
                logger.info("Started new trial period")
        except Exception as e:
            logger.error(f"Error checking trial eligibility: {e}")
            self.trial_mode = False
    
    def is_valid(self):
        """Check if the software is licensed or in trial mode."""
        return self.is_licensed or self.trial_mode
    
    def get_status_message(self):
        """Get a message describing the current license status."""
        if self.is_licensed:
            license_type = self.license_data.get("license_type", "Standard")
            if "expiry_date" in self.license_data:
                import datetime
                expiry = datetime.datetime.fromisoformat(self.license_data["expiry_date"])
                return f"Licensed: {license_type} (expires {expiry.strftime('%Y-%m-%d')})"
            else:
                return f"Licensed: {license_type}"
        elif self.trial_mode:
            return f"Trial Mode: {self.trial_days_left} days remaining"
        else:
            return "Unlicensed"
    
    def show_activation_dialog(self, parent):
        """Show the license activation dialog."""
        ActivationDialog(parent, self)

    def _verify_license_data(self):
        """Verify the license data is valid."""
        # Check if required fields are present
        required_fields = ["key", "email", "name", "product", "expiration", "signature"]
        if not all(field in self.license_data for field in required_fields):
            logger.warning("License data missing required fields")
            return False
        
        # Check if product name matches
        if self.license_data.get("product") != "Archimedius":
            logger.warning(f"Product name mismatch: {self.license_data.get('product')}")
            return False
        
        return True


class ActivationDialog:
    """Dialog for activating the software license."""
    
    def __init__(self, parent, license_manager):
        """Initialize the activation dialog.
        
        Args:
            parent: The parent window
            license_manager: The LicenseManager instance
        """
        self.license_manager = license_manager
        
        # Create a new top-level window
        self.window = tk.Toplevel(parent)
        self.window.title("Activate Archimedius")
        self.window.geometry("500x400")
        self.window.minsize(500, 400)
        self.window.transient(parent)  # Make it a modal dialog
        self.window.grab_set()  # Make it modal
        
        # Center the window
        self.window.update_idletasks()
        width = 500
        height = 400
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create a frame for the content
        content_frame = ttk.Frame(self.window, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            content_frame, 
            text="Activate Archimedius", 
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Current status
        status_frame = ttk.Frame(content_frame)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(status_frame, text="Current Status:").pack(side=tk.LEFT)
        
        status_text = self.license_manager.get_status_message()
        status_label = ttk.Label(
            status_frame, 
            text=status_text,
            font=("TkDefaultFont", 10, "bold")
        )
        status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # License key entry
        key_frame = ttk.Frame(content_frame)
        key_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(key_frame, text="License Key:").pack(anchor=tk.W)
        
        self.key_var = tk.StringVar()
        key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=40)
        key_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Email entry
        email_frame = ttk.Frame(content_frame)
        email_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(email_frame, text="Email Address:").pack(anchor=tk.W)
        
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(email_frame, textvariable=self.email_var, width=40)
        email_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        activate_button = ttk.Button(
            button_frame, 
            text="Activate", 
            command=self._activate_license
        )
        activate_button.pack(side=tk.LEFT, padx=(0, 10))
        
        purchase_button = ttk.Button(
            button_frame, 
            text="Purchase License", 
            command=self._open_purchase_page
        )
        purchase_button.pack(side=tk.LEFT)
        
        close_button = ttk.Button(
            button_frame, 
            text="Close", 
            command=self.window.destroy
        )
        close_button.pack(side=tk.RIGHT)
        
        # Instructions
        instructions_text = (
            "To activate Archimedius, enter your license key and the email address "
            "associated with your purchase. If you don't have a license key yet, "
            "you can start a free trial or purchase a license."
        )
        
        info_label = ttk.Label(
            content_frame, 
            text=instructions_text,
            wraplength=460,
            justify=tk.LEFT
        )
        info_label.pack(fill=tk.X)
        
        # Set focus to the key entry
        key_entry.focus_set()
        
        # Bind Escape key to close the dialog
        self.window.bind("<Escape>", lambda e: self.window.destroy())
        
        # Make the dialog modal
        parent.wait_window(self.window)
    
    def _activate_license(self):
        """Activate the license with the provided key and email."""
        license_key = self.key_var.get().strip()
        email = self.email_var.get().strip()
        
        if not license_key or not email:
            messagebox.showerror(
                "Activation Error",
                "Please enter both your license key and email address."
            )
            return
        
        # In a real implementation, this would validate the license key with a server
        # For this example, we'll simulate a successful activation
        
        try:
            # Create a license data structure
            import datetime
            license_data = {
                "product": "Archimedius",
                "license_key": license_key,
                "email": email,
                "license_type": "Standard",
                "issue_date": datetime.datetime.now().isoformat(),
                "machines": [self.license_manager.machine_id],
                "max_machines": 2
            }
            
            # Save the license data
            self.license_manager.license_data = license_data
            if self.license_manager._save_license():
                self.license_manager.is_licensed = True
                self.license_manager.trial_mode = False
                
                self._show_activation_success()
            else:
                messagebox.showerror(
                    "Activation Error",
                    "Failed to save license data. Please try again."
                )
        except Exception as e:
            logger.error(f"Error activating license: {e}")
            messagebox.showerror(
                "Activation Error",
                f"An error occurred during activation: {str(e)}"
            )
    
    def _open_purchase_page(self):
        """Open the purchase page in a web browser."""
        webbrowser.open(defaults.APP_WEBSITE + "/purchase")
    
    def _generate_trial_license(self):
        """Generate a trial license."""
        # Create a trial license valid for 30 days
        now = int(time.time())
        expiration = now + (30 * 24 * 60 * 60)  # 30 days in seconds
        
        trial_data = {
            "key": f"TRIAL-{uuid.uuid4()}",
            "email": "trial@user.com",
            "name": "Trial User",
            "product": "Archimedius",
            "purchase_date": now,
            "expiration": expiration,
            "type": "trial"
        }
        
        # Save the trial data
        trial_file = Path.home() / defaults.DEFAULT_PATHS.get("trial_file", "media_organizer_trial.json")
        with open(trial_file, "w") as f:
            json.dump(trial_data, f)
        
        self.license_manager.trial_mode = True
        self.license_manager.trial_days_left = 30
        webbrowser.open(defaults.APP_WEBSITE + "/purchase") 