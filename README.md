# StegVault

> Secure password manager using steganography to embed encrypted credentials within images

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](https://github.com/kalashnikxvxiii-collab/StegVault/releases/tag/v0.4.0)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-305_passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-79%25-brightgreen.svg)](tests/)

**StegVault** is a full-featured password manager that combines modern cryptography with steganography. It can store either a single password or an entire vault of credentials, all encrypted using battle-tested algorithms (XChaCha20-Poly1305 + Argon2id) and hidden within ordinary PNG images using LSB steganography.

**Latest Features (v0.4.0):** Complete password manager with vault import/export, secure clipboard integration, TOTP/2FA authenticator with QR codes, and realistic password strength validation using zxcvbn!

## Features

### Core Features
- 🔐 **Strong Encryption**: XChaCha20-Poly1305 AEAD with Argon2id KDF
- 🖼️ **Invisible Storage**: LSB steganography with sequential pixel ordering
- 🔒 **Zero-Knowledge**: All operations performed locally, no cloud dependencies
- ✅ **Authenticated**: AEAD tag ensures data integrity
- 🧪 **Well-Tested**: 305 unit tests with 79% overall coverage (all passing)
- ⏱️ **User-Friendly**: Progress indicators for long operations

### Vault Mode
- 🗄️ **Multiple Passwords**: Store entire password vault in one image
- 🎯 **Key-Based Access**: Retrieve specific passwords by key (e.g., "gmail", "github")
- 🔑 **Password Generator**: Cryptographically secure password generation
- 📋 **Rich Metadata**: Username, URL, notes, tags, timestamps for each entry
- 🔄 **Dual-Mode**: Choose single password OR vault mode
- ♻️ **Auto-Detection**: Automatically detects format on restore (backward compatible)
- 📤 **Import/Export**: Backup and restore vaults via JSON
- 📋 **Clipboard Support**: Copy passwords to clipboard with auto-clear
- 🔐 **TOTP/2FA**: Built-in authenticator with QR code support
- 🛡️ **Password Strength**: Realistic validation using zxcvbn with actionable feedback

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

#### Mode 2: Vault (Multiple Passwords) - NEW!

**1. Create Vault with First Entry**
```bash
stegvault vault create -i cover.png -o vault.png -k gmail --generate
# Automatically generates a secure password for Gmail
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

### Steganography Technique

**LSB (Least Significant Bit) Embedding**:

1. **Sequential Pixel Ordering**: All payload bits stored left-to-right, top-to-bottom for reliability and simplicity
2. **Distributed Embedding**: Payload bits spread across R, G, B channels
3. **Minimal Visual Impact**: Only LSB modified (imperceptible to human eye)
4. **Security Philosophy**: Cryptographic strength (XChaCha20-Poly1305 + Argon2id) provides security, not pixel ordering

```python
# Simplified example
for y in range(height):
    for x in range(width):
        for channel in [R, G, B]:
            channel_value = (channel_value & 0xFE) | payload_bit
```

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
- **JPEG Lossy**: Recompressing JPEG images destroys payload (use PNG)
- **Both Required**: Losing either image OR passphrase = permanent data loss
- **Offline Attacks**: Attacker with image can attempt brute-force (mitigated by Argon2id)

### 🔒 Best Practices

1. **Strong Passphrase**: Use 16+ character passphrase with mixed case, numbers, symbols
2. **Multiple Backups**: Store copies in different locations
3. **PNG Format**: Always use PNG (lossless) not JPEG (lossy)
4. **Verify Backups**: Test restore process after creating backup
5. **Secure Storage**: Protect image files as you would protect passwords

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
│   ├── __init__.py
│   └── cli.py           # Command-line interface
├── tests/               # Test suite (275 tests, 80% coverage)
│   ├── unit/
│   │   ├── test_crypto.py              # 26 tests
│   │   ├── test_payload.py             # 22 tests
│   │   ├── test_stego.py               # 16 tests
│   │   ├── test_config.py              # 28 tests
│   │   ├── test_batch.py               # 20 tests
│   │   ├── test_vault.py               # 49 tests (vault module)
│   │   ├── test_cli.py                 # 53 tests (core CLI)
│   │   ├── test_vault_cli.py           # 38 tests (vault CLI)
│   │   ├── test_totp.py                # 19 tests (TOTP/2FA)
│   │   └── test_password_strength.py   # 24 tests (password validation)
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
