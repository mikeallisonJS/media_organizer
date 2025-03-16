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
    
    # Verify the executable was created
    dist_dir = os.path.join("dist", defaults.APP_NAME)
    exe_path = os.path.join(dist_dir, f"{defaults.APP_NAME}.exe")
    
    if os.path.exists(exe_path):
        print(f"Windows executable built successfully at: {exe_path}")
        # List contents of dist directory
        print("Contents of dist directory:")
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                print(f"  {os.path.join(root, file)}")
        return True
    else:
        print(f"Error: Executable not found at {exe_path}")
        if os.path.exists("dist"):
            print("Contents of dist directory:")
            for root, dirs, files in os.walk("dist"):
                for file in files:
                    print(f"  {os.path.join(root, file)}")
        else:
            print("dist directory not found")
        return False

def create_nsis_script():
    """Create the NSIS installer script."""
    print("Creating NSIS installer script...")
    
    # Get current directory for absolute paths
    current_dir = os.path.abspath('.')
    installer_path = os.path.join(current_dir, f"{defaults.APP_NAME}-Setup.exe")
    dist_dir = os.path.join(current_dir, "dist", defaults.APP_NAME)
    
    # Verify dist directory exists
    if not os.path.exists(dist_dir):
        print(f"Error: Dist directory not found at {dist_dir}")
        print("Available directories in dist:")
        if os.path.exists("dist"):
            for item in os.listdir("dist"):
                print(f"  {item}")
        else:
            print("  dist directory does not exist")
        raise FileNotFoundError(f"Dist directory not found: {dist_dir}")
    
    # Create the NSIS script content
    script_content = """
!include "MUI2.nsh"

; Application information
Name "{0}"
OutFile "{3}"
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
  File /r "{4}\\*.*"
  
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
""".format(defaults.APP_NAME, defaults.APP_AUTHOR, defaults.APP_VERSION, 
           installer_path.replace('\\', '\\\\'), dist_dir.replace('\\', '\\\\'))
    
    # Write NSIS script to file
    with open("installer.nsi", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print(f"NSIS installer script created successfully. Installer will be created at: {installer_path}")
    return installer_path

def build_installer(installer_path):
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
    
    # Verify installer was created
    if os.path.exists(installer_path):
        print(f"Windows installer built successfully at: {installer_path}")
        return True
    else:
        print(f"Error: Installer file not found at {installer_path}")
        return False

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
        if build_executable():
            # Create NSIS installer script
            installer_path = create_nsis_script()
            
            # Build installer
            if build_installer(installer_path):
                # Verify the installer exists
                if os.path.exists(installer_path):
                    print(f"Build completed successfully. Installer is at: {installer_path}")
                    
                    # Copy to root directory with standard name if needed
                    root_installer = f"{defaults.APP_NAME}-Setup.exe"
                    if os.path.abspath(installer_path) != os.path.abspath(root_installer):
                        shutil.copy(installer_path, root_installer)
                        print(f"Copied installer to: {os.path.abspath(root_installer)}")
                else:
                    # Search for the installer file
                    print("Installer not found at expected path. Searching...")
                    found = False
                    for root, dirs, files in os.walk('.'):
                        for file in files:
                            if file.endswith('-Setup.exe'):
                                found_path = os.path.join(root, file)
                                print(f"Found installer at: {found_path}")
                                # Copy to root directory
                                root_installer = f"{defaults.APP_NAME}-Setup.exe"
                                shutil.copy(found_path, root_installer)
                                print(f"Copied installer to: {os.path.abspath(root_installer)}")
                                found = True
                                break
                        if found:
                            break
                    
                    if not found:
                        print("ERROR: Could not find installer file anywhere!")
                        sys.exit(1)
        else:
            print("ERROR: Failed to build executable")
            sys.exit(1)
    except Exception as e:
        print(f"Error during build: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 