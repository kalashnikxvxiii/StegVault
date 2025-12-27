# Installation Guide

This guide covers installing StegVault on various platforms.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (for cloning repository)

## Installation Methods

### Method 1: Install from Source (Recommended)

**Current Version**: v0.7.8

This is currently the primary installation method.

#### Windows

```powershell
# Install Python (if not already installed)
# Download from https://www.python.org/downloads/

# Clone repository
git clone https://github.com/kalashnikxvxiii/stegvault.git
cd stegvault

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install StegVault
pip install -e .

# Verify installation
stegvault --version
```

#### macOS

```bash
# Install Python (if not already installed)
brew install python@3.9

# Clone repository
git clone https://github.com/kalashnikxvxiii/stegvault.git
cd stegvault

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install StegVault
pip install -e .

# Verify installation
stegvault --version
```

#### Linux (Ubuntu/Debian)

```bash
# Install Python and dependencies
sudo apt update
sudo apt install python3.9 python3-pip python3-venv git

# Clone repository
git clone https://github.com/kalashnikxvxiii/stegvault.git
cd stegvault

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install StegVault
pip install -e .

# Verify installation
stegvault --version
```

### Method 2: Install from PyPI (Coming Soon)

```bash
pip install stegvault
```

## Dependency Information

StegVault requires the following Python packages:

| Package | Version | Purpose |
|---------|---------|---------|
| PyNaCl | ≥1.5.0 | Cryptography (libsodium bindings) |
| argon2-cffi | ≥23.1.0 | Argon2id key derivation |
| Pillow | ≥10.0.0 | Image processing |
| click | ≥8.1.0 | CLI framework |
| numpy | ≥1.20.0 | Array operations for steganography |
| jpeglib | ≥1.0.0 | JPEG DCT steganography |
| pyotp | ≥2.9.0 | TOTP/2FA code generation |
| qrcode | ≥7.4.0 | QR code scanning |
| pyperclip | ≥1.8.0 | Clipboard operations |
| pyzbar | - | QR code reading (optional) |

Development dependencies:
- pytest ≥7.4.0
- pytest-cov ≥4.1.0
- black ≥23.0.0
- mypy ≥1.5.0

## Verifying Installation

After installation, verify everything works:

```bash
# Check version
stegvault --version

# View help
stegvault --help

# List available commands (v0.6.1)
stegvault backup --help          # Single password mode
stegvault restore --help         # Single password restore
stegvault vault --help           # Vault mode (multi-password manager)
stegvault gallery --help         # Multi-vault management
stegvault check --help           # Image capacity check
```

Expected output:
```
Usage: stegvault [OPTIONS] COMMAND [ARGS]...

  StegVault - Password Manager with Steganography
  ...
```

## Troubleshooting

### Python Version Issues

If you encounter `Python 3.9+ required` errors:

```bash
# Check Python version
python --version

# Use specific Python version
python3.9 -m venv venv
```

### Permission Errors

On Unix/macOS, if you get permission errors:

```bash
# Don't use sudo with pip in virtual environment
# Instead, ensure virtual environment is activated
source venv/bin/activate
```

### Windows Execution Policy

If PowerShell blocks script execution:

```powershell
# Set execution policy for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Missing Dependencies

If imports fail:

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Virtual Environment Issues

If virtual environment doesn't activate:

```bash
# Remove and recreate
rm -rf venv
python -m venv venv
```

## Platform-Specific Notes

### Windows
- Ensure Windows Terminal or PowerShell is used for best Unicode support
- Some emoji characters may not display correctly (doesn't affect functionality)

### macOS
- Xcode Command Line Tools may be required: `xcode-select --install`
- Use Homebrew for easier Python management

### Linux
- May need to install `python3-dev` for compilation: `sudo apt install python3-dev`
- Some distros require `python3-venv` separately: `sudo apt install python3-venv`

## Updating StegVault

To update to the latest version:

### Method 1: Auto-Update (v0.7.8+)

StegVault includes built-in update commands with critical bug fixes:

```bash
# Check for updates
stegvault updates check

# Install latest version from PyPI
stegvault updates upgrade
```

Or use the TUI "Update Now" button (NEW in v0.7.8):
1. Launch TUI: `stegvault tui`
2. Click `━━━` button (bottom-right) → Settings
3. If update available, click **Update Now** (replaces "Check Updates")
4. Close StegVault → detached update runs automatically (fixes WinError 32)

Or enable auto-updates:
1. Launch TUI: `stegvault tui`
2. Click `━━━` button (bottom-right)
3. Toggle **Auto-Check Updates** and **Auto-Upgrade**

### Method 2: Manual Update from Source

```bash
cd stegvault
git pull origin main
pip install --upgrade -r requirements.txt
pip install -e .
```

## Uninstalling

To remove StegVault:

```bash
# Deactivate virtual environment
deactivate

# Remove installation
pip uninstall stegvault

# Remove repository (optional)
cd ..
rm -rf stegvault
```

## Next Steps

After installation:
1. Read the [Quick Start Tutorial](Quick-Start-Tutorial.md)
2. Review [Security Best Practices](Security-Best-Practices.md)
3. Try the [Basic Usage Examples](Basic-Usage-Examples.md)

## Getting Help

If you encounter issues:
- Check [Troubleshooting Guide](Troubleshooting.md)
- Review [Common Errors](Common-Errors.md)
- Open an [issue](https://github.com/yourusername/stegvault/issues)