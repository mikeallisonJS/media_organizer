from setuptools import setup
import defaults  # Import the defaults module to get version information

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['tkinter', 'PIL', 'tinytag', 'pymediainfo', 'pypdf', 'TKinterModernThemes'],
    'includes': ['PIL', 'tkinter', 'tinytag', 'pymediainfo', 'pypdf', 'TKinterModernThemes', 'PIL._tkinter_finder'],
    'iconfile': 'resources/archimedius.icns',
    'plist': {
        'CFBundleName': defaults.APP_NAME,
        'CFBundleDisplayName': defaults.APP_NAME,
        'CFBundleGetInfoString': 'Media file organizer',
        'CFBundleIdentifier': f'com.{defaults.APP_AUTHOR.lower().replace(" ", "")}.{defaults.APP_NAME.lower()}',
        'CFBundleVersion': defaults.APP_VERSION,
        'CFBundleShortVersionString': defaults.APP_VERSION,
        'NSHumanReadableCopyright': f'© 2025 {defaults.APP_AUTHOR}',
        'LSUIElement': False,  # Show in Dock
        'LSBackgroundOnly': False,  # Not a background-only app
        'CFBundleDocumentTypes': [],  # No document types
        'NSHighResolutionCapable': True,  # Enable Retina display support
        'NSRequiresAquaSystemAppearance': False  # Support Dark Mode
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'Pillow',
        'tinytag',
        'pymediainfo',
        'pypdf',
        'TKinterModernThemes'
    ],
    name=defaults.APP_NAME,
    version=defaults.APP_VERSION,
    author=defaults.APP_AUTHOR,
    author_email=defaults.APP_EMAIL,
    url=defaults.APP_WEBSITE,
    description='Media file organizer',
) 