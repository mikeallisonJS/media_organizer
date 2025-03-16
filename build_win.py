"""
Windows build script for Archimedius.
This script creates a Windows executable using PyInstaller and generates an NSIS installer script.
"""

import os
import sys
import subprocess
import shutil
import requests
import zipfile
import defaults

def download_mediainfo():
    """Download and extract MediaInfo CLI for Windows."""
    print("Downloading MediaInfo...")
    mediainfo_url = "https://mediaarea.net/download/binary/mediainfo/23.11/MediaInfo_CLI_23.11_Windows_x64.zip"
    mediainfo_zip = "mediainfo.zip"
    
    # Download MediaInfo
    response = requests.get(mediainfo_url)
    with open(mediainfo_zip, 'wb') as f:
        f.write(response.content)
    
    # Extract MediaInfo
    with zipfile.ZipFile(mediainfo_zip, 'r') as zip_ref:
        zip_ref.extractall("mediainfo")
    
    # Copy MediaInfo.exe to current directory
    shutil.copy("mediainfo/MediaInfo.exe", ".")
    
    # Clean up
    os.remove(mediainfo_zip)
    print("MediaInfo downloaded and extracted successfully.")

def build_executable():
    """Build the Windows executable using PyInstaller."""
    print("Building Windows executable...")
    
    # Build command
    cmd = [
        "pyinstaller",
        "--name", defaults.APP_NAME,
        "--windowed",
        "--icon=resources/archimedius.ico",
        "--add-data", "MediaInfo.exe;.",
        "main.py"
    ]
    
    # Run PyInstaller
    subprocess.run(cmd, check=True)
    print("Windows executable built successfully.")

def create_nsis_script():
    """Create the NSIS installer script."""
    print("Creating NSIS installer script...")
    
    # Create the NSIS script content
    script_content = """
!include "MUI2.nsh"

; Application information
Name "{0}"
OutFile "{0}-Setup.exe"
InstallDir "$PROGRAMFILES64\\{0}"
InstallDirRegKey HKCU "Software\\{0}" ""
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "resources\\archimedius.ico"
!define MUI_UNICON "resources\\archimedius.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "{0}" SecMain
  SetOutPath "$INSTDIR"
  
  ; Copy all files from the dist directory
  File /r "dist\\{0}\\*.*"
  
  ; Create Start Menu directory first
  SetShellVarContext all
  CreateDirectory "$SMPROGRAMS\\{0}"
  
  ; Create shortcuts
  CreateShortCut "$SMPROGRAMS\\{0}\\{0}.lnk" "$INSTDIR\\{0}.exe"
  CreateShortCut "$DESKTOP\\{0}.lnk" "$INSTDIR\\{0}.exe"
  
  ; Write uninstaller
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  
  ; Write registry keys for uninstall
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{0}" "DisplayName" "{0}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{0}" "UninstallString" "$\\"$INSTDIR\\Uninstall.exe$\\""
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{0}" "QuietUninstallString" "$\\"$INSTDIR\\Uninstall.exe$\" /S"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{0}" "DisplayIcon" "$\\"$INSTDIR\\{0}.exe$\\""
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{0}" "Publisher" "{1}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{0}" "DisplayVersion" "{2}"
SectionEnd

; Uninstaller section
Section "Uninstall"
  SetShellVarContext all
  
  ; Remove installed files
  RMDir /r "$INSTDIR"
  
  ; Remove shortcuts
  Delete "$SMPROGRAMS\\{0}\\{0}.lnk"
  RMDir "$SMPROGRAMS\\{0}"
  Delete "$DESKTOP\\{0}.lnk"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{0}"
  DeleteRegKey HKCU "Software\\{0}"
SectionEnd
""".format(defaults.APP_NAME, defaults.APP_AUTHOR, defaults.APP_VERSION)
    
    # Write NSIS script to file
    with open("installer.nsi", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("NSIS installer script created successfully.")

def build_installer():
    """Build the Windows installer using NSIS."""
    print("Building Windows installer...")
    
    # Check if NSIS is installed
    nsis_path = "C:\\Program Files (x86)\\NSIS\\makensis.exe"
    if not os.path.exists(nsis_path):
        print("NSIS not found. Please install NSIS and try again.")
        print("You can install NSIS using: choco install nsis -y")
        return False
    
    # Build installer
    subprocess.run([nsis_path, "installer.nsi"], check=True)
    print("Windows installer built successfully.")
    return True

def main():
    """Main function to build Windows executable and installer."""
    print(f"Building {defaults.APP_NAME} v{defaults.APP_VERSION} for Windows...")
    
    # Check if running on Windows
    if sys.platform != "win32":
        print("This script should be run on Windows.")
        return
    
    try:
        # Download MediaInfo
        download_mediainfo()
        
        # Build executable
        build_executable()
        
        # Create NSIS installer script
        create_nsis_script()
        
        # Build installer
        if build_installer():
            print(f"Build completed successfully. Installer is at: {defaults.APP_NAME}-Setup.exe")
    except Exception as e:
        print(f"Error during build: {e}")

if __name__ == "__main__":
    main() 