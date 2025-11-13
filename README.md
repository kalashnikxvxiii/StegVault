# StegVault

> Secure password manager using steganography to embed encrypted credentials within images

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.3.2-blue.svg)](https://github.com/kalashnikxvxiii-collab/StegVault/releases/tag/v0.3.2)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-145_passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen.svg)](tests/)

**StegVault** combines modern cryptography with steganography to create a secure, portable password backup system. Your master password is encrypted using battle-tested algorithms (XChaCha20-Poly1305 + Argon2id) and then hidden within ordinary PNG images using LSB steganography.

## Features

- 🔐 **Strong Encryption**: XChaCha20-Poly1305 AEAD with Argon2id KDF
- 🖼️ **Invisible Storage**: LSB steganography with pseudo-random pixel ordering
- 🔒 **Zero-Knowledge**: All operations performed locally, no cloud dependencies
- ✅ **Authenticated**: AEAD tag ensures data integrity
- 🧪 **Well-Tested**: 145 unit tests with 87% overall coverage (all passing)
- ⏱️ **User-Friendly**: Progress indicators for long operations
- 🚀 **Easy to Use**: Simple CLI interface

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

#### 1. Check Image Capacity

```bash
stegvault check -i myimage.png
```

Output:
```
Image: myimage.png
Format: PNG
Mode: RGB
Size: 500x500 pixels

Capacity: 93750 bytes (91.55 KB)
Max password size: ~93686 bytes (93686 characters)

✓ Image has sufficient capacity for password storage.
```

#### 2. Create Backup

```bash
stegvault backup -i cover.png -o backup.png
```

You'll be prompted for:
- Master password (the password to encrypt and store)
- Encryption passphrase (keep this secret!)

#### 3. Restore Password

```bash
stegvault restore -i backup.png
```

You'll be prompted for your encryption passphrase, then your password is displayed.

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
       • Generate Salt (16B)             • Pseudo-random Order
       • Derive Key (Argon2id)           • Parse Binary Format
       • Encrypt (XChaCha20)
                                      3. Decryption
    3. Payload Format                    • Verify AEAD Tag
       • Magic: "SPW1"                   • Derive Key (Argon2id)
       • Salt + Nonce                    • Decrypt Ciphertext
       • Ciphertext + Tag
                                      4. Recover Password
    4. LSB Embedding                     • Display/Save Password
       • Pseudo-random Pixels
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

1. **Pseudo-random Pixel Ordering**: Seed derived from salt ensures reproducible but unpredictable pixel sequence
2. **Distributed Embedding**: Payload bits spread across R, G, B channels
3. **Minimal Visual Impact**: Only LSB modified (imperceptible to human eye)

```python
# Simplified example
seed = int.from_bytes(salt[:4], 'big')
pixels = shuffle_pixels(image, seed)  # Pseudo-random order

for pixel in pixels:
    for channel in [R, G, B]:
        channel_value = (channel_value & 0xFE) | payload_bit
```

## Security Considerations

### ✅ Strong Security Features

- **Modern Cryptography**: XChaCha20-Poly1305 is a modern AEAD cipher resistant to various attacks
- **Strong KDF**: Argon2id winner of Password Hashing Competition, resistant to GPU/ASIC attacks
- **Authenticated Encryption**: Poly1305 MAC ensures integrity; tampering detected automatically
- **Detection Resistance**: Pseudo-random bit placement resists basic steganographic analysis
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
│   │   └── payload.py
│   ├── __init__.py
│   └── cli.py           # Command-line interface
├── tests/               # Test suite
│   ├── unit/
│   │   ├── test_crypto.py     # 26 tests
│   │   ├── test_payload.py    # 22 tests
│   │   └── test_stego.py      # 15 tests
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
- Multiple password vault support
- Image capacity auto-check
- Compression for large passwords
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
