# StegVault

> Secure password manager using steganography to embed encrypted credentials within images

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.7.6-blue.svg)](https://github.com/kalashnikxvxiii-collab/StegVault)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-798_passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-74%25-yellow.svg)](tests/)

**StegVault** combines modern cryptography with steganography to create portable, zero-knowledge password backups. Store a single password or entire vault of credentials, all encrypted with XChaCha20-Poly1305 + Argon2id and hidden within ordinary PNG or JPEG images.

**Latest Release (v0.7.6):** Auto-update system with Settings screen - Check and install updates automatically with toggles for auto-check and auto-upgrade!

---

## Features

### Core Features
- 🔐 **Strong Encryption**: XChaCha20-Poly1305 AEAD with Argon2id KDF
- 🖼️ **Dual Steganography**: PNG LSB + JPEG DCT coefficient modification
- 🎯 **Auto-Detection**: Automatically detects image format (PNG/JPEG)
- 🔒 **Zero-Knowledge**: All operations performed locally, no cloud dependencies
- ✅ **Authenticated**: AEAD tag ensures data integrity
- 🧪 **Well-Tested**: 798 unit tests with 74% coverage (all passing)

### Vault Mode
- 🗄️ **Multiple Passwords**: Store entire password vault in one image
- 🎯 **Key-Based Access**: Retrieve specific passwords by key (e.g., "gmail", "github")
- 🔑 **Password Generator**: Cryptographically secure password generation
- 📋 **Rich Metadata**: Username, URL, notes, tags, timestamps for each entry
- 🕐 **Password History**: Track password changes with timestamps and reasons (v0.7.1)
- 🔐 **TOTP/2FA**: Built-in authenticator with QR code support
- 🔍 **Search & Filter**: Find entries by query or filter by tags/URL

### Gallery Mode (v0.5.0)
- 🖼️ **Multi-Vault Management**: Organize multiple vault images
- 🔍 **Cross-Vault Search**: Search across all vaults simultaneously
- 🏷️ **Tagging System**: Organize vaults with custom tags

### Interfaces
- 🖥️ **Terminal UI (TUI)**: Full-featured visual interface with keyboard shortcuts (v0.7.0)
- 🤖 **Command Line (CLI)**: Scriptable commands for automation
- 📊 **Headless Mode**: JSON output for CI/CD pipelines (v0.6.0)

### Auto-Update System (v0.7.6)
- 🔄 **Update Checking**: Check for new versions from PyPI
- ⚡ **Auto-Upgrade**: Optionally install updates automatically
- ⚙️ **Settings Screen**: Configure auto-check and auto-upgrade toggles
- 📝 **Changelog Preview**: View changes before upgrading

---

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

### Updating

```bash
# Standard update
pip install --upgrade stegvault

# Built-in auto-update (v0.7.6)
stegvault updates check     # Check for updates
stegvault updates upgrade   # Install latest version

# Enable auto-updates in TUI Settings
stegvault tui               # Launch TUI
# Click ━━━ button (bottom-right) → Toggle "Auto-Check Updates"
```

See [Installation Guide](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Installation-Guide) for detailed instructions including Windows portable packages.

---

## Usage

StegVault offers **three interfaces** for managing your passwords:

### 1. Terminal UI (TUI) - Recommended

Full-featured visual interface in your terminal.

```bash
# Launch TUI
stegvault tui
```

**Keyboard Shortcuts**:
- `o` - Open vault | `n` - New vault | `h` - View password history
- `a` - Add entry | `e` - Edit | `d` - Delete
- `c` - Copy password | `v` - Toggle visibility
- `/` - Search entries | `f` - Favorite folder | `Ctrl+f` - Quick access

See [TUI User Guide](https://github.com/kalashnikxvxiii-collab/StegVault/blob/main/TUI_USER_GUIDE.md) for complete documentation.

### 2. Command Line (CLI)

Scriptable commands for automation.

**Create Vault**:
```bash
stegvault vault create -i cover.png -o vault.png -k gmail --generate
```

**Add Entry**:
```bash
stegvault vault add vault.png -k github -u myusername --generate
```

**Retrieve Password**:
```bash
stegvault vault get vault.png -k gmail
# Output:
# Key: gmail
# Password: X7k$mP2!qL5@wN
# Username: user@gmail.com
```

**List Entries**:
```bash
stegvault vault list vault.png
# Output: Vault contains 3 entries:
#   1. gmail (user@gmail.com)
#   2. github (myusername)
#   3. aws
```

**Search & Filter**:
```bash
stegvault vault search vault.png -q "github"
stegvault vault filter vault.png --tag work
```

See [CLI Commands Reference](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/CLI-Commands-Reference) for complete command documentation.

### 3. Headless Mode - Automation & CI/CD

Automation-friendly with JSON output and non-interactive authentication.

**JSON Output**:
```bash
stegvault vault get vault.png -k gmail --passphrase-file ~/.vault_pass --json
# {"status":"success","data":{"key":"gmail","password":"...","username":"..."}}
```

**Passphrase Options**:
```bash
# 1. Passphrase file (recommended)
echo "MyPassphrase" > ~/.vault_pass && chmod 600 ~/.vault_pass
stegvault vault get vault.png -k gmail --passphrase-file ~/.vault_pass

# 2. Environment variable
export STEGVAULT_PASSPHRASE="MyPassphrase"
stegvault vault get vault.png -k gmail --json
```

**CI/CD Example** (GitHub Actions):
```yaml
- name: Retrieve database password
  run: |
    PASSWORD=$(stegvault vault get secrets.png \
      -k db_password \
      --passphrase-file <(echo "${{ secrets.VAULT_PASSPHRASE }}") \
      --json | jq -r '.data.password')
    echo "DB_PASSWORD=$PASSWORD" >> $GITHUB_ENV
```

See [Headless Mode Guide](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Headless-Mode-Guide) for automation examples and best practices.

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────┐
│         User Input (CLI/TUI/Headless)           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      1. Encryption (Argon2id + XChaCha20)       │
│         • Generate Salt (16B) & Nonce (24B)     │
│         • Derive Key from Passphrase            │
│         • Encrypt with AEAD Authentication      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      2. Payload Format (Binary Structure)       │
│         Magic: "SPW1" (4B)                      │
│         Salt: 16B | Nonce: 24B                  │
│         Length: 4B | Ciphertext: NB             │
│         AEAD Tag: 16B                           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      3. Steganography (Auto-Detect Format)      │
│         PNG: LSB sequential embedding           │
│         JPEG: DCT coefficient modification      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      Output: Stego Image (vault.png/jpg)        │
└─────────────────────────────────────────────────┘
```

### Cryptographic Stack

| Component | Algorithm | Parameters |
|-----------|-----------|------------|
| **AEAD Cipher** | XChaCha20-Poly1305 | 256-bit key, 192-bit nonce |
| **KDF** | Argon2id | 3 iterations, 64MB memory, 4 threads |
| **Salt/Nonce** | CSPRNG | 128-bit salt, 192-bit nonce |
| **Auth Tag** | Poly1305 | 128 bits (16 bytes) |

### Steganography Techniques

- **PNG LSB**: Sequential pixel embedding (~90KB capacity for 400x600 image)
- **JPEG DCT**: Frequency domain coefficient modification (~18KB capacity for 400x600 Q85)

**Security Philosophy**: Cryptographic strength provides security, not the embedding method.

See [Architecture Overview](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Architecture-Overview) and [Cryptography Details](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Cryptography-Details) for technical details.

---

## Documentation

Complete documentation is available on the [Wiki](https://github.com/kalashnikxvxiii-collab/StegVault/wiki):

### Getting Started
- [Installation Guide](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Installation-Guide)
- [Quick Start Tutorial](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Quick-Start-Tutorial)
- [Basic Usage Examples](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Basic-Usage-Examples) (27 examples)

### User Guides
- [CLI Commands Reference](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/CLI-Commands-Reference) (Complete command reference)
- [TUI User Guide](https://github.com/kalashnikxvxiii-collab/StegVault/blob/main/TUI_USER_GUIDE.md) (Terminal UI)
- [Headless Mode Guide](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Headless-Mode-Guide) (Automation & CI/CD)
- [Security Best Practices](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Security-Best-Practices)

### Technical Documentation
- [Architecture Overview](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Architecture-Overview)
- [Cryptography Details](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Cryptography-Details)
- [Steganography Techniques](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Steganography-Techniques)
- [Security Model](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Security-Model)

### Development
- [Developer Guide](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Developer-Guide)
- [API Reference](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/API-Reference)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## Security Considerations

### ✅ Strong Security Features

- **Modern Cryptography**: XChaCha20-Poly1305 AEAD cipher
- **Strong KDF**: Argon2id resistant to GPU/ASIC attacks
- **Authenticated Encryption**: Poly1305 MAC prevents tampering
- **Fresh Nonces**: New nonce for every encryption

### ⚠️ Limitations & Warnings

- **Not Invisible**: Advanced steganalysis may detect embedded data
- **Format-Specific**: PNG (lossless) vs JPEG (more robust, lower capacity)
- **Both Required**: Losing image OR passphrase = permanent data loss
- **Offline Attacks**: Attacker with image can attempt brute-force (mitigated by Argon2id)

### 🔒 Best Practices

1. **Strong Passphrase**: Use 16+ character passphrase with mixed case, numbers, symbols
2. **Multiple Backups**: Store copies in different locations
3. **Verify Backups**: Test restore process after creating backup
4. **Secure Storage**: Protect image files as you would protect passwords

See [Security Model](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Security-Model) and [Threat Model](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Threat-Model) for comprehensive security information.

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=stegvault --cov-report=html

# Run specific module
pytest tests/unit/test_crypto.py -v
```

### Code Quality

```bash
# Format code
black stegvault tests

# Type checking
mypy stegvault
```

See [Developer Guide](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Developer-Guide) and [Testing Guide](https://github.com/kalashnikxvxiii-collab/StegVault/wiki/Testing-Guide) for complete development documentation.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests
4. Commit (`git commit -m 'feat: add amazing feature'`)
5. Push (`git push origin feature/amazing-feature`)
6. Open Pull Request

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## Disclaimer

StegVault is provided "as-is" for educational and personal use. The authors are not responsible for any data loss or security breaches. Always maintain multiple backups of critical passwords.

**Security Notice**: While StegVault uses strong cryptography, no system is perfect. This tool is best used as a supplementary backup method alongside traditional password managers.

---

## Acknowledgments

- [PyNaCl](https://github.com/pyca/pynacl) - libsodium bindings for Python
- [argon2-cffi](https://github.com/hynek/argon2-cffi) - Argon2 password hashing
- [Pillow](https://github.com/python-pillow/Pillow) - Python Imaging Library
- [Textual](https://github.com/Textualize/textual) - Terminal UI framework
- [jpeglib](https://github.com/martinbenes1996/jpeglib) - JPEG DCT manipulation

---

**Version**: 0.7.6
**Last Updated**: 2025-12-18

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/kalashnikxvxiii-collab">Kalashnikxv</a>
</p>
