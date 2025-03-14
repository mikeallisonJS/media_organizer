# Archimedius GitHub Actions

This directory contains GitHub Actions workflows for automating various tasks in the Archimedius project.

## Build Installers Workflow

The `build-installers.yml` workflow automatically builds installers for macOS and Windows when a new release is created on GitHub.

### How it works

1. When you create a new release on GitHub, the workflow is triggered automatically.
2. It builds a macOS .dmg installer and a Windows .exe installer.
3. The installers are automatically attached to the GitHub release.

### Requirements

For the workflow to function properly:

1. **Icons**:

   - Place your macOS icon file at `resources/archimedius.icns`
   - Place your Windows icon file at `resources/archimedius.ico`

2. **LICENSE file**:

   - Ensure the LICENSE file is in the root of the repository (used in the Windows installer)

3. **Dependencies**:
   - Make sure all required dependencies are listed in `requirements.txt`

### Creating a Release

To create a new release and trigger the workflow:

1. Go to the "Releases" section of your GitHub repository
2. Click "Draft a new release"
3. Enter a tag version (e.g., `v0.1.0`)
4. Enter a release title and description
5. Click "Publish release"

The workflow will start automatically, and the installers will be attached to the release when they're ready.

### Customizing the Installers

To customize the installers:

- **macOS**: Edit the `setup.py` section in the workflow file to change app metadata
- **Windows**: Edit the NSIS script section to customize the installer behavior

### Troubleshooting

If the workflow fails:

1. Check the workflow run logs on GitHub
2. Ensure all required files are present in the repository
3. Verify that the repository has the necessary permissions to upload release assets
