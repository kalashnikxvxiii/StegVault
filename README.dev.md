# StegVault - Development Guide

## Setup Development Environment

### 1. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Install in development mode
```bash
pip install -e ".[dev]"
```

## Development Commands

### Run tests
```bash
pytest
```

### Run tests with coverage
```bash
pytest --cov=stegvault --cov-report=html
```

### Format code
```bash
black stegvault tests
```

### Type checking
```bash
mypy stegvault
```

## Project Structure

```
stegvault/
├── crypto/          # Cryptography: Argon2id + XChaCha20-Poly1305
├── stego/           # Steganography: PNG LSB embedding
├── utils/           # Payload format and utilities
└── cli.py           # Command-line interface

tests/
├── unit/            # Unit tests for individual modules
└── integration/     # End-to-end roundtrip tests

examples/            # Example cover images and usage demos
docs/                # Additional documentation
```

## CLI Usage (once implemented)

### Create backup
```bash
stegvault backup \
  --password "my-master-password" \
  --passphrase "encryption-passphrase" \
  --image cover.png \
  --output backup.png
```

### Restore backup
```bash
stegvault restore \
  --image backup.png \
  --passphrase "encryption-passphrase"
```
