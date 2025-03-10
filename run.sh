#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 to run this application."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "media_organizer_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv media_organizer_venv
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source media_organizer_venv/bin/activate
pip install -r requirements.txt

# Check if Tkinter is installed
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "Tkinter is not installed. Please install it using: brew install python-tk@3.13"
    exit 1
fi

# Run the application
python3 media_organizer.py

# Deactivate virtual environment
deactivate 