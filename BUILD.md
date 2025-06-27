# Building 24fire CLI

This document explains how to build the 24fire CLI tool into standalone executables.

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Quick Build

### Windows
```batch
build.bat
```

### Linux/macOS
```bash
chmod +x build.sh
./build.sh
```

## Manual Build

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install pyinstaller
```

2. Build executable:

**Windows:**
```bash
pyinstaller --onefile --name=24fire-cli --add-data ".env;." --hidden-import=dotenv main.py
```

**Linux/macOS:**
```bash
pyinstaller --onefile --name=24fire-cli --add-data ".env:." --hidden-import=dotenv main.py
```

3. The executable will be created in the `dist/` folder.

## GitHub Actions

The repository includes automated builds via GitHub Actions:

- **Trigger**: Push to main/master branch or create a tag
- **Platforms**: Windows, Linux, macOS
- **Artifacts**: Available for download from the Actions tab
- **Releases**: Automatically created when you push a version tag (e.g., `v1.0.0`)

### Creating a Release

1. Tag your commit:
```bash
git tag v1.0.0
git push origin v1.0.0
```

2. GitHub Actions will automatically build and create a release with executables for all platforms.

## Build Options

### Optimization
- `--optimize=2`: Enable Python bytecode optimization
- `--upx`: Compress executable (requires UPX)

### Debugging
- `--debug`: Enable debug mode
- `--console`: Keep console window (Windows)

### Icon
- `--icon=icon.ico`: Add custom icon (Windows)

## Troubleshooting

### Missing Modules
If you get import errors, add hidden imports:
```bash
--hidden-import=module_name
```

### Large File Size
- Use `--exclude-module` to remove unused modules
- Use UPX compression with `--upx`
- Consider using `--onedir` instead of `--onefile`

### Antivirus False Positives
- Some antivirus software may flag PyInstaller executables
- Add exclusions or use code signing certificates for distribution