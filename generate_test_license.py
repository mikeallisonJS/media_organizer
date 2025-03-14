#!/usr/bin/env python3
"""
Generate a test license for development purposes.
This script is for testing only and should not be included in the final distribution.
"""

import json
import uuid
import datetime
from pathlib import Path

import defaults

def generate_test_license():
    """Generate a test license file for development purposes."""
    # Generate a random license key
    license_key = str(uuid.uuid4())
    
    # Create license data
    license_data = {
        "product": "Archimedius",
        "license_key": license_key,
        "email": "test@example.com",
        "license_type": "Professional",
        "issue_date": datetime.datetime.now().isoformat(),
        "machines": [],  # Will be filled in by the license manager
        "max_machines": 5
    }
    
    # Save to the license file location
    license_file = Path.home() / defaults.DEFAULT_PATHS.get("license_file", "media_organizer_license.json")
    
    with open(license_file, "w") as f:
        json.dump(license_data, f, indent=2)
    
    print(f"Test license generated and saved to: {license_file}")
    print(f"License key: {license_key}")
    print(f"Email: test@example.com")

if __name__ == "__main__":
    generate_test_license() 