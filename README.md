# StegVault

> Secure password manager using steganography to embed encrypted credentials within images

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.7.4-blue.svg)](https://github.com/kalashnikxvxiii-collab/StegVault)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-778_passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen.svg)](tests/)

**StegVault** is a full-featured password manager that combines modern cryptography with steganography. It can store either a single password or an entire vault of credentials, all encrypted using battle-tested algorithms (XChaCha20-Poly1305 + Argon2id) and hidden within ordinary **PNG or JPEG** images.

**Latest Release (v0.7.4):** Favorite Folders feature for TUI - Quick access to frequently used vault locations with cross-platform filesystem support!

## Features

### Core Features
- 🔐 **Strong Encryption**: XChaCha20-Poly1305 AEAD with Argon2id KDF
- 🖼️ **Dual Steganography**: PNG LSB + JPEG DCT coefficient modification
- 🎯 **Auto-Detection**: Automatically detects image format (PNG/JPEG)
- 🔒 **Zero-Knowledge**: All operations performed locally, no cloud dependencies
- ✅ **Authenticated**: AEAD tag ensures data integrity
- 🧪 **Well-Tested**: 778 unit tests with 89% overall coverage (all passing)
- ⏱️ **User-Friendly**: Progress indicators for long operations

### Vault Mode
- 🗄️ **Multiple Passwords**: Store entire password vault in one image
- 🎯 **Key-Based Access**: Retrieve specific passwords by key (e.g., "gmail", "github")
- 🔑 **Password Generator**: Cryptographically secure password generation
- 📋 **Rich Metadata**: Username, URL, notes, tags, timestamps for each entry
- 🕐 **Password History**: Track password changes with timestamps and reasons (v0.7.1)
- 🔄 **Dual-Mode**: Choose single password OR vault mode
- ♻️ **Auto-Detection**: Automatically detects format on restore (backward compatible)
- 📤 **Import/Export**: Backup and restore vaults via JSON
- 📋 **Clipboard Support**: Copy passwords to clipboard with auto-clear
- 🔐 **TOTP/2FA**: Built-in authenticator with QR code support
- 🛡️ **Password Strength**: Realistic validation using zxcvbn with actionable feedback
- 🔍 **Search & Filter**: Find entries by query or filter by tags/URL

### Gallery Mode (v0.5.0)
- 🖼️ **Multi-Vault Management**: Organize multiple vault images in one gallery
- 🗄️ **SQLite Metadata**: Centralized database for vault information and entry cache
- 🔍 **Cross-Vault Search**: Search across all vaults simultaneously
- 🏷️ **Tagging System**: Organize vaults with custom tags
- ⚡ **Fast Search**: Cached entry metadata for instant results
- 📊 **Vault Statistics**: Track entry counts, last accessed times
- 🔄 **Auto-Refresh**: Update cache when vault contents change

### Headless Mode (v0.6.0)
- 🤖 **JSON Output**: Machine-readable output for all critical commands
- 📄 **Passphrase File**: Non-interactive authentication via `--passphrase-file`
- 🌍 **Environment Variables**: `STEGVAULT_PASSPHRASE` for CI/CD pipelines
- 🔢 **Exit Codes**: Standardized codes (0=success, 1=error, 2=validation)
- ⚙️ **Automation-Ready**: Perfect for scripts, backups, and deployments
- 🔗 **Priority System**: Explicit > File > Env > Prompt fallback

### Application Layer (v0.6.1)
- 🏗️ **Clean Architecture**: Separation of business logic from UI layers
- 🎯 **Multi-Interface**: Controllers work with CLI, TUI, and future GUI
- 📦 **Structured Results**: All operations return typed result objects
- 🧪 **Easy Testing**: No UI framework dependencies in business logic
- 🔄 **Thread-Safe**: Designed for concurrent access in GUI applications
- 🎨 **Consistent Logic**: Same business rules across all interfaces

## Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install stegvault

# Or install from source
git clone https://github.com/kalashnikxvxiii-collab/stegvault.git
cd stegvault
pip install -e .
```

### Usage

StegVault offers **three interfaces** for managing your passwords:
1. **Terminal UI (TUI)** - Full-featured visual interface in your terminal 🎨
2. **Command Line (CLI)** - Scriptable commands for automation 🤖
3. **Headless Mode** - JSON output for CI/CD and scripts 📊

#### Terminal UI (TUI) - Recommended for Interactive Use

Launch the full-featured terminal interface:
```bash
stegvault tui
```

**Features**:
- 🖥️ Modern visual interface with keyboard shortcuts
- 📂 File browser for selecting vaults
- 📋 Entry list with live search/filter
- 🔐 TOTP codes with auto-refresh countdown
- 🎲 Built-in password generator
- 📝 Full CRUD operations (Create, Read, Update, Delete)
- ⌨️ Complete keyboard navigation

**Keyboard Shortcuts**:
- `o` - Open vault | `n` - New vault | `h` - View password history
- `a` - Add entry | `e` - Edit | `d` - Delete
- `c` - Copy password | `v` - Toggle visibility
- `s` - Save changes | `/` - Search entries
- `f` - Favorite current folder | `Ctrl+f` - Quick access to favorites

**Favorite Folders** (v0.7.4):
- Save frequently used vault locations for quick access
- Quick dropdown menu with cross-platform support
- Persistent storage in `~/.stegvault/favorite_folders.json` with restrictive permissions (0600)
- Automatic cleanup of non-existent paths
- Toggle favorites on/off with a single keypress

#### Mode 1: Single Password (Simple Backup)

**1. Check Image Capacity**
```bash
stegvault check -i myimage.png
```

**2. Create Backup**
```bash
stegvault backup -i cover.png -o backup.png
```

**3. Restore Password**
```bash
stegvault restore backup.png
```

#### Mode 2: Vault (Multiple Passwords)

> **Note**: All commands work with both PNG and JPEG! Simply use `.jpg` extension:
> ```bash
> stegvault vault create -i cover.jpg -o vault.jpg -k gmail --generate
> ```

**1. Create Vault with First Entry**
```bash
stegvault vault create -i cover.png -o vault.png -k gmail --generate
# Automatically generates a secure password for Gmail
# Works with JPEG too: -i cover.jpg -o vault.jpg
```

**2. Add More Passwords**
```bash
stegvault vault add vault.png -o vault_v2.png -k github -u myusername --generate
stegvault vault add vault_v2.png -o vault_v3.png -k aws
```

**3. Retrieve Specific Password**
```bash
stegvault vault get vault_v3.png -k gmail
# Output:
# Entry: gmail
# Username: user@gmail.com
# URL: https://gmail.com
# Password: X7k$mP2!qL5@wN
```

**4. List All Keys**
```bash
stegvault vault list vault_v3.png
# Output:
# Vault contains 3 entries:
#   1. gmail (user@gmail.com)
#   2. github (myusername)
#   3. aws
```

**5. Update Entry**
```bash
stegvault vault update vault_v3.png -o vault_v4.png -k gmail --password newpass123
```

**6. Export Vault**
```bash
stegvault vault export vault_v4.png -o backup.json --pretty
```

**7. Import Vault**
```bash
stegvault vault import backup.json -i cover.png -o restored_vault.png
```

**8. Delete Entry**
```bash
stegvault vault delete vault_v4.png -o vault_v5.png -k oldservice
```

**9. Copy Password to Clipboard**
```bash
stegvault vault get vault.png -k gmail --clipboard
# Password copied to clipboard (not displayed on screen)

# Auto-clear clipboard after 30 seconds
stegvault vault get vault.png -k gmail --clipboard --clipboard-timeout 30
```

**10. Setup TOTP/2FA**
```bash
# Add TOTP secret to entry
stegvault vault add vault.png -o vault_v2.png -k github -u myuser --totp

# Generate TOTP code
stegvault vault totp vault_v2.png -k github
# Output: Current TOTP code for 'github': 123456 (valid for 25 seconds)

# Show QR code for authenticator app
stegvault vault totp vault_v2.png -k github --qr

# Search vault entries
stegvault vault search vault.png --query "github"
# Search specific fields only
stegvault vault search vault.png -q "work" --fields key --fields notes

# Filter entries by tags
stegvault vault filter vault.png --tag work
stegvault vault filter vault.png --tag work --tag email --match-all

# Filter by URL pattern
stegvault vault filter vault.png --url github.com
```

### Password History (v0.7.1)

**Track and view password changes over time:**

```bash
# View password history for an entry
stegvault vault history vault.png gmail
# Output:
# ============================================================
# Password History for: gmail
# ============================================================
# Current password: MyNewSecureP@ss2024
# Modified: 2025-12-03T17:45:23.456789Z
#
# History (2 entries):
# ------------------------------------------------------------
#
# 1. Password: OldPassword123
#    Changed at: 2025-12-02T10:30:15.123456Z
#    Reason: scheduled rotation
#
# 2. Password: VeryOldPass456
#    Changed at: 2025-11-15T08:20:00.000000Z
# ============================================================

# View history with JSON output (for automation)
stegvault vault history vault.png gmail --json
# Output: {"status":"success","data":{"key":"gmail","current_password":"...","history_count":2,...}}

# Clear password history for an entry
stegvault vault history-clear vault.png gmail -o vault_updated.png
# Confirmation: This will clear 2 historical password(s) for 'gmail'.
# Are you sure? [y/N]: y
# Output: Password history cleared for 'gmail'.
#         Updated vault saved to: vault_updated.png

# Clear history without confirmation (for scripts)
stegvault vault history-clear vault.png gmail -o vault_updated.png --no-confirm

# Update password with reason for tracking
stegvault vault update vault.png -o vault_v2.png -k gmail \
    --password "NewSecurePass123" \
    --password-change-reason "suspected breach"
# History automatically tracks: old password + timestamp + reason
```

**TUI Password History** (Terminal UI):
- Press `h` with an entry selected to view full password history
- See inline preview of last 3 changes in detail panel
- Color-coded display: passwords (yellow), timestamps (gray), reasons (cyan)

### Gallery Management (v0.5.0)

**Manage multiple vaults in one place:**

```bash
# Initialize gallery database
stegvault gallery init
# Creates ~/.stegvault/gallery.db

# Add vaults to gallery
stegvault gallery add work_vault.png --name work-vault --tag work
stegvault gallery add personal_vault.png --name personal-vault --tag personal

# List all vaults
stegvault gallery list
# Output:
# 2 vault(s) in gallery:
#
# Name: personal-vault
# Path: /path/to/personal_vault.png
# Entries: 5
# Tags: personal
#
# Name: work-vault
# Path: /path/to/work_vault.png
# Entries: 12
# Tags: work

# Search across ALL vaults
stegvault gallery search "github"
# Output:
# Found 2 matching entries:
#
# [work-vault]
# Key: github-work
# Username: work@company.com
# URL: https://github.com
#
# [personal-vault]
# Key: github-personal
# Username: myusername
# URL: https://github.com

# Search in specific vault only
stegvault gallery search "email" --vault work-vault

# Refresh vault metadata after changes
stegvault gallery refresh work-vault

# Remove vault from gallery (doesn't delete the image)
stegvault gallery remove old-vault
```

### Headless Mode (v0.6.0) - Automation & CI/CD

**Automation-friendly features for scripts, CI/CD pipelines, and server environments.**

#### JSON Output

All critical commands support `--json` for machine-readable output:

```bash
# Check image capacity with JSON output
stegvault check -i image.png --json
```
```json
{
  "status": "success",
  "data": {
    "image_path": "image.png",
    "format": "PNG",
    "mode": "RGB",
    "size": {"width": 800, "height": 600},
    "capacity": 18750,
    "max_password_size": 18686
  }
}
```

```bash
# Retrieve password in JSON format
stegvault vault get vault.png -k gmail --passphrase mypass --json
```
```json
{
  "status": "success",
  "data": {
    "key": "gmail",
    "password": "secret123",
    "username": "user@gmail.com",
    "url": "https://gmail.com",
    "notes": "Personal email",
    "has_totp": true
  }
}
```

```bash
# List vault entries as JSON
stegvault vault list vault.png --passphrase mypass --json
```
```json
{
  "status": "success",
  "data": {
    "entries": [
      {"key": "gmail", "username": "user@gmail.com", "url": "https://gmail.com", "has_totp": true},
      {"key": "github", "username": "myuser", "url": "https://github.com", "has_totp": false}
    ],
    "entry_count": 2
  }
}
```

#### Passphrase from File

Avoid interactive prompts by providing passphrase via file:

```bash
# Store passphrase in a secure file
echo "MySecretPassphrase" > ~/.vault_pass
chmod 600 ~/.vault_pass

# Use --passphrase-file to read from file
stegvault vault get vault.png -k gmail --passphrase-file ~/.vault_pass --json

# Works with all vault commands
stegvault vault list vault.png --passphrase-file ~/.vault_pass
```

#### Environment Variable

Set `STEGVAULT_PASSPHRASE` for completely non-interactive operation:

```bash
# Export passphrase as environment variable
export STEGVAULT_PASSPHRASE="MySecretPassphrase"

# No passphrase prompt - automatically uses env var
stegvault vault get vault.png -k gmail --json
stegvault vault list vault.png --json
```

#### Passphrase Priority

StegVault uses this priority order for passphrases:

1. **Explicit `--passphrase`** (highest priority)
2. **`--passphrase-file`**
3. **`STEGVAULT_PASSPHRASE` environment variable**
4. **Interactive prompt** (fallback)

```bash
# Explicit passphrase overrides file and env var
stegvault vault get vault.png -k gmail --passphrase "explicit" --json

# File overrides env var
stegvault vault get vault.png -k gmail --passphrase-file ~/.pass --json

# Env var used if no explicit or file
export STEGVAULT_PASSPHRASE="fallback"
stegvault vault get vault.png -k gmail --json
```

#### Exit Codes

Standardized exit codes for automation:

- **0** = Success
- **1** = Runtime error (wrong passphrase, file not found, decryption error)
- **2** = Validation error (invalid input, empty passphrase file)

```bash
# Check exit code in scripts
stegvault vault get vault.png -k gmail --passphrase-file ~/.pass --json
if [ $? -eq 0 ]; then
    echo "Success"
elif [ $? -eq 1 ]; then
    echo "Runtime error"
elif [ $? -eq 2 ]; then
    echo "Validation error"
fi
```

#### Example: CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- name: Retrieve database password
  run: |
    PASSWORD=$(stegvault vault get secrets.png \
      -k db_password \
      --passphrase-file ${{ secrets.VAULT_PASSPHRASE_FILE }} \
      --json | jq -r '.data.password')
    echo "::add-mask::$PASSWORD"
    echo "DB_PASSWORD=$PASSWORD" >> $GITHUB_ENV

- name: Deploy application
  run: ./deploy.sh
  env:
    DB_PASSWORD: ${{ env.DB_PASSWORD }}
```

#### Example: Backup Script

```bash
#!/bin/bash
# backup_passwords.sh - Automated password backup

set -e  # Exit on error

VAULT_PASS_FILE="$HOME/.vault_pass"
BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d)

# Verify passphrase file exists
if [ ! -f "$VAULT_PASS_FILE" ]; then
    echo "Error: Passphrase file not found"
    exit 1
fi

# Export vault to JSON
stegvault vault export vault.png \
    -o "$BACKUP_DIR/vault_$DATE.json" \
    --passphrase-file "$VAULT_PASS_FILE" \
    --pretty

# Check exit code
if [ $? -eq 0 ]; then
    echo "Backup created: $BACKUP_DIR/vault_$DATE.json"

    # Get vault statistics
    STATS=$(stegvault vault list vault.png \
        --passphrase-file "$VAULT_PASS_FILE" \
        --json)

    ENTRY_COUNT=$(echo "$STATS" | jq -r '.data.entry_count')
    echo "Backed up $ENTRY_COUNT entries"
else
    echo "Backup failed"
    exit 1
fi
```

#### Example: Password Rotation

```bash
#!/bin/bash
# rotate_password.sh - Programmatic password rotation

VAULT_FILE="vault.png"
SERVICE="github"
NEW_PASSWORD=$(openssl rand -base64 32)

# Retrieve current password info as JSON
INFO=$(stegvault vault get "$VAULT_FILE" \
    -k "$SERVICE" \
    --passphrase-file ~/.vault_pass \
    --json)

if [ $? -eq 0 ]; then
    USERNAME=$(echo "$INFO" | jq -r '.data.username')

    # Update password via external API (example)
    curl -X POST "https://api.github.com/user/password" \
        -u "$USERNAME:$NEW_PASSWORD"

    # Update vault with new password
    stegvault vault update "$VAULT_FILE" \
        -o "${VAULT_FILE}.new" \
        -k "$SERVICE" \
        --password "$NEW_PASSWORD" \
        --passphrase-file ~/.vault_pass

    mv "${VAULT_FILE}.new" "$VAULT_FILE"
    echo "Password rotated successfully"
fi
```

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    StegVault Workflow                    │
└─────────────────────────────────────────────────────────┘

        BACKUP CREATION                 PASSWORD RECOVERY
               ↓                                ↓
    1. User Input                    1. Load Stego Image
       • Master Password                 • backup.png
       • Passphrase                      • Enter Passphrase
       • Cover Image
                                      2. Extract Payload
    2. Encryption                        • LSB Extraction
       • Generate Salt (16B)             • Sequential Order
       • Derive Key (Argon2id)           • Parse Binary Format
       • Encrypt (XChaCha20)
                                      3. Decryption
    3. Payload Format                    • Verify AEAD Tag
       • Magic: "SPW1"                   • Derive Key (Argon2id)
       • Salt + Nonce                    • Decrypt Ciphertext
       • Ciphertext + Tag
                                      4. Recover Password
    4. LSB Embedding                     • Display/Save Password
       • Sequential Pixels
       • Modify LSB of R,G,B
       • Save Stego Image

    5. Output: backup.png
```

### Cryptographic Stack

| Component | Algorithm | Parameters |
|-----------|-----------|------------|
| **AEAD Cipher** | XChaCha20-Poly1305 | 256-bit key, 192-bit nonce |
| **KDF** | Argon2id | 3 iterations, 64MB memory, 4 threads |
| **Salt** | CSPRNG | 128 bits (16 bytes) |
| **Nonce** | CSPRNG | 192 bits (24 bytes) |
| **Tag** | Poly1305 | 128 bits (16 bytes) |

### Payload Format

Binary structure embedded in images:

```
┌────────────────────────────────────────────────────┐
│  Offset  │  Size  │  Field         │  Description  │
├──────────┼────────┼────────────────┼───────────────┤
│  0       │  4B    │  Magic Header  │  "SPW1"       │
│  4       │  16B   │  Salt          │  For Argon2id │
│  20      │  24B   │  Nonce         │  For XChaCha20│
│  44      │  4B    │  CT Length     │  Big-endian   │
│  48      │  N     │  Ciphertext    │  Variable     │
│  48+N    │  16B   │  AEAD Tag      │  (appended)   │
└────────────────────────────────────────────────────┘
```

### Steganography Techniques

StegVault automatically detects image format and uses the appropriate method:

#### **PNG: LSB (Least Significant Bit) Embedding**

1. **Sequential Pixel Ordering**: All payload bits stored left-to-right, top-to-bottom for reliability and simplicity
2. **Distributed Embedding**: Payload bits spread across R, G, B channels
3. **Minimal Visual Impact**: Only LSB modified (imperceptible to human eye)
4. **High Capacity**: ~3 bits per pixel (~90KB for 400x600 image)

```python
# Simplified PNG LSB example
for y in range(height):
    for x in range(width):
        for channel in [R, G, B]:
            channel_value = (channel_value & 0xFE) | payload_bit
```

#### **JPEG: DCT Coefficient Modification**

1. **Frequency Domain**: Modifies DCT (Discrete Cosine Transform) coefficients in 8x8 blocks
2. **Anti-Shrinkage**: Only uses coefficients with |value| > 1 to prevent artifacts
3. **Multi-Channel**: Embeds across Y, Cb, Cr channels
4. **Robust**: More resistant to JPEG recompression than spatial methods
5. **Lower Capacity**: ~1 bit per suitable coefficient (~18KB for 400x600 Q85 image)

```python
# Simplified JPEG DCT example
for block in [Y_blocks, Cb_blocks, Cr_blocks]:
    for coef in block.AC_coefficients:  # Skip DC
        if abs(coef) > 1:  # Anti-shrinkage
            coef_lsb = abs(coef) % 2
            if coef_lsb != payload_bit:
                coef += 1 if coef > 0 else -1
```

**Security Philosophy**: Cryptographic strength (XChaCha20-Poly1305 + Argon2id) provides security, not the embedding method

## Security Considerations

### ✅ Strong Security Features

- **Modern Cryptography**: XChaCha20-Poly1305 is a modern AEAD cipher resistant to various attacks
- **Strong KDF**: Argon2id winner of Password Hashing Competition, resistant to GPU/ASIC attacks
- **Authenticated Encryption**: Poly1305 MAC ensures integrity; tampering detected automatically
- **Cryptographic Security**: Security provided by strong cryptography, not by hiding embedding pattern
- **No Key Reuse**: Fresh nonce generated for each encryption

### ⚠️ Limitations & Warnings

- **Not Invisible**: Advanced steganalysis may detect embedded data
- **No Deniability**: Payload has identifiable magic header
- **Format-Specific**:
  - **PNG**: Use lossless formats only; JPEG recompression destroys LSB data
  - **JPEG**: More robust against recompression but lower capacity (~20% of PNG)
- **Both Required**: Losing either image OR passphrase = permanent data loss
- **Offline Attacks**: Attacker with image can attempt brute-force (mitigated by Argon2id)

### 🔒 Best Practices

1. **Strong Passphrase**: Use 16+ character passphrase with mixed case, numbers, symbols
2. **Multiple Backups**: Store copies in different locations
3. **PNG Format**: Always use PNG (lossless) not JPEG (lossy)
4. **Verify Backups**: Test restore process after creating backup
5. **Secure Storage**: Protect image files as you would protect passwords

## Application Layer (v0.6.1)

StegVault now includes a clean **Application Layer** that separates business logic from UI concerns. This architecture enables multiple user interfaces (CLI, TUI, GUI) to share the same underlying operations.

### Architecture

```
┌─────────────────────────────────────────────┐
│          User Interfaces (UI)               │
│  CLI (Click)  │  TUI (Textual)  │  GUI (Qt) │
└──────────────┬──────────────────┬───────────┘
               │                  │
          ┌────▼──────────────────▼────┐
          │   Application Controllers  │
          │  • CryptoController        │
          │  • VaultController         │
          └────┬──────────────────┬────┘
               │                  │
          ┌────▼──────────────────▼────┐
          │    Core Modules            │
          │  • crypto  • vault  • stego│
          └────────────────────────────┘
```

### Controllers

#### CryptoController

High-level encryption operations with structured results:

```python
from stegvault.app.controllers import CryptoController

controller = CryptoController()

# Encrypt data
result = controller.encrypt(b"secret data", "passphrase")
if result.success:
    print(f"Salt: {result.salt.hex()}")
    print(f"Nonce: {result.nonce.hex()}")
else:
    print(f"Error: {result.error}")

# Decrypt data
result = controller.decrypt(
    ciphertext, salt, nonce, "passphrase"
)
if result.success:
    print(f"Plaintext: {result.plaintext}")
```

#### VaultController

Complete vault CRUD operations:

```python
from stegvault.app.controllers import VaultController

controller = VaultController()

# Create new vault
vault, success, error = controller.create_new_vault(
    key="gmail",
    password="secret123",
    username="user@gmail.com",
    url="https://gmail.com",
    tags=["email", "personal"]
)

# Save to image
result = controller.save_vault(
    vault, "vault.png", "passphrase",
    cover_image="cover.png"
)

# Load from image
result = controller.load_vault("vault.png", "passphrase")
if result.success:
    vault = result.vault

# Get entry
entry_result = controller.get_vault_entry(vault, "gmail")
if entry_result.success:
    print(f"Password: {entry_result.entry.password}")
```

### Benefits

- **UI-Agnostic**: Controllers work with any interface (CLI/TUI/GUI)
- **Easy Testing**: No need to mock UI frameworks
- **Consistent Logic**: Same business rules across all interfaces
- **Thread-Safe**: Designed for concurrent access (future GUI)
- **Structured Results**: All operations return typed result objects

### Result Data Classes

All controller methods return structured results with success/error info:

- `EncryptionResult` - Encryption operations (ciphertext, salt, nonce)
- `DecryptionResult` - Decryption operations (plaintext)
- `VaultLoadResult` - Vault loading (vault object, error)
- `VaultSaveResult` - Vault saving (output path, error)
- `EntryResult` - Entry retrieval (entry object, error)

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=stegvault --cov-report=html

# Run specific module tests
pytest tests/unit/test_crypto.py -v
```

### Code Quality

```bash
# Format code
black stegvault tests

# Type checking
mypy stegvault
```

### Project Structure

```
stegvault/
├── stegvault/           # Source code
│   ├── crypto/          # Cryptography (Argon2id + XChaCha20)
│   │   ├── __init__.py
│   │   └── core.py
│   ├── stego/           # Steganography (PNG LSB)
│   │   ├── __init__.py
│   │   └── png_lsb.py
│   ├── utils/           # Payload format handling
│   │   ├── __init__.py
│   │   ├── payload.py
│   │   └── config.py
│   ├── vault/           # Password vault management (NEW in v0.4.0)
│   │   ├── __init__.py
│   │   ├── core.py       # Vault and VaultEntry classes
│   │   ├── operations.py # Vault CRUD operations + import
│   │   ├── generator.py  # Password generator
│   │   └── totp.py       # TOTP/2FA support
│   ├── batch/           # Batch operations
│   │   ├── __init__.py
│   │   └── processor.py
│   ├── gallery/         # Multi-vault management (v0.5.0)
│   │   ├── __init__.py
│   │   ├── core.py      # Gallery and metadata classes
│   │   ├── db.py        # SQLite database operations
│   │   ├── operations.py # Gallery CRUD operations
│   │   └── search.py    # Cross-vault search
│   ├── __init__.py
│   └── cli.py           # Command-line interface
├── tests/               # Test suite (346 tests, 78% coverage)
│   ├── unit/
│   │   ├── test_crypto.py              # 26 tests
│   │   ├── test_payload.py             # 22 tests
│   │   ├── test_stego.py               # 16 tests
│   │   ├── test_config.py              # 28 tests
│   │   ├── test_batch.py               # 20 tests
│   │   ├── test_vault.py                  # 49 tests (vault module)
│   │   ├── test_cli.py                    # 53 tests (core CLI)
│   │   ├── test_vault_cli.py              # 46 tests (vault CLI + TOTP)
│   │   ├── test_totp.py                   # 19 tests (TOTP/2FA)
│   │   ├── test_password_strength.py      # 24 tests (password validation)
│   │   ├── test_vault_search.py           # 24 tests (search/filter backend)
│   │   ├── test_vault_search_filter_cli.py # 5 tests (search/filter CLI)
│   │   ├── test_vault_update_delete_cli.py # 12 tests (update/delete CLI)
│   │   └── test_gallery.py                # 22 tests (gallery management)
│   └── __init__.py
├── docs/                # Documentation
├── examples/            # Example images
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE              # MIT License
├── README.md            # This file
├── ROADMAP.md
├── pyproject.toml
└── requirements.txt
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and development timeline.

### Coming Soon

- GUI application (Electron or Qt)
- JPEG DCT steganography (more robust)
- Multi-vault operations and search
- Gallery foundation for multi-file vault management
- Optional cloud storage integration

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests
4. Commit (`git commit -m 'feat: add amazing feature'`)
5. Push (`git push origin feature/amazing-feature`)
6. Open Pull Request

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

StegVault is provided "as-is" for educational and personal use. The authors are not responsible for any data loss or security breaches. Always maintain multiple backups of critical passwords.

**Security Notice**: While StegVault uses strong cryptography, no system is perfect. This tool is best used as a supplementary backup method alongside traditional password managers.

## Acknowledgments

- [PyNaCl](https://github.com/pyca/pynacl) - libsodium bindings for Python
- [argon2-cffi](https://github.com/hynek/argon2-cffi) - Argon2 password hashing
- [Pillow](https://github.com/python-pillow/Pillow) - Python Imaging Library
