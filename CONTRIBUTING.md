# Contributing to StegVault

Thank you for your interest in contributing to StegVault! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Security Considerations](#security-considerations)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive criticism
- Prioritize security and user safety
- Report security vulnerabilities responsibly

## Getting Started

Before contributing, please:

1. Read the [README.md](README.md) to understand the project
2. Review the [WIKI](https://github.com/kalashnikxvxiii/StegVault/wiki) for technical architecture details
3. Check existing [issues](https://github.com/kalashnikxvxiii/stegvault/issues) and [pull requests](https://github.com/kalashnikxvxiii/stegvault/pulls)
4. Join discussions to understand ongoing work

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv)

### Setup Instructions

```bash
# Clone the repository
git clone https://github.com/kalashnikxvxiii/stegvault.git
cd stegvault

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify setup
pytest
```

## How to Contribute

### Reporting Bugs

When reporting bugs, please include:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: OS, Python version, StegVault version
- **Logs/Screenshots**: Any relevant error messages or screenshots

### Suggesting Enhancements

For feature requests, please provide:

- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives Considered**: Other approaches you've thought about
- **Impact**: How will this affect existing functionality?

### Security Vulnerabilities

**DO NOT** open public issues for security vulnerabilities. Instead:

1. Email security concerns privately
2. Include detailed description and proof of concept
3. Wait for acknowledgment before public disclosure
4. Follow responsible disclosure practices

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting (line length: 100)
- Use type hints for function signatures
- Write docstrings for all public functions and classes

### Code Formatting

```bash
# Format code with Black
black stegvault tests

# Check types with mypy
mypy stegvault
```

### Documentation

- Use Google-style docstrings
- Include parameter types and return types
- Provide usage examples for complex functions
- Keep the WIKI folder updated with architectural changes

### Example Function

```python
def encrypt_data(plaintext: bytes, passphrase: str) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypt data using XChaCha20-Poly1305 AEAD with Argon2id key derivation.

    Args:
        plaintext: Data to encrypt
        passphrase: User-provided passphrase

    Returns:
        Tuple of (ciphertext, salt, nonce)

    Raises:
        CryptoError: If encryption fails

    Example:
        >>> ciphertext, salt, nonce = encrypt_data(b"secret", "passphrase")
        >>> len(ciphertext) > len(b"secret")
        True
    """
    # Implementation
```

## Testing Guidelines

### Test Requirements

- **Coverage**: Aim for 90%+ test coverage
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **Roundtrip Tests**: Verify encrypt → embed → extract → decrypt cycles

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=stegvault --cov-report=html

# Run specific test file
pytest tests/unit/test_crypto.py

# Run specific test
pytest tests/unit/test_crypto.py::TestEncryption::test_encrypt_returns_tuple
```

### Writing Tests

```python
import pytest
from stegvault.crypto import encrypt_data, decrypt_data

class TestCrypto:
    """Test suite for cryptography module."""

    def test_encryption_roundtrip(self):
        """Should encrypt and decrypt data successfully."""
        plaintext = b"test data"
        passphrase = "TestPass123"

        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)
        decrypted = decrypt_data(ciphertext, salt, nonce, passphrase)

        assert decrypted == plaintext

    def test_wrong_passphrase_fails(self):
        """Should raise DecryptionError with wrong passphrase."""
        plaintext = b"test data"
        ciphertext, salt, nonce = encrypt_data(plaintext, "correct")

        with pytest.raises(DecryptionError):
            decrypt_data(ciphertext, salt, nonce, "wrong")
```

## Security Considerations

### Cryptographic Code

When working with cryptographic code:

- **Never roll your own crypto**: Use established libraries (PyNaCl, argon2-cffi)
- **Use secure defaults**: Strong parameters for Argon2id, proper key sizes
- **Verify AEAD tags**: Always check authentication before decrypting
- **Use CSPRNG**: Use `os.urandom()` or `nacl.utils.random()` for randomness
- **Clear sensitive data**: Overwrite secrets in memory when done (where possible in Python)

### Code Review Requirements

Security-critical changes require:

- Detailed explanation of cryptographic choices
- References to academic papers or standards
- Review by multiple contributors
- Extensive testing including edge cases

### What NOT to Do

- ❌ Store passphrases or plaintext passwords
- ❌ Use predictable seeds or IVs
- ❌ Skip AEAD tag verification
- ❌ Use weak KDF parameters
- ❌ Implement custom cryptographic primitives
- ❌ Log sensitive information

## Pull Request Process

### Before Submitting

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Write tests**: Ensure new code is tested
3. **Run test suite**: `pytest` should pass
4. **Format code**: Run `black stegvault tests`
5. **Update documentation**: Update README, WIKI if needed
6. **Update CHANGELOG**: Add entry under "Unreleased" section

### Pull Request Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes Made
- Change 1
- Change 2

## Testing
How was this tested?

## Checklist
- [ ] Tests pass locally
- [ ] Code formatted with Black
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No security concerns
```

### Review Process

1. Submit pull request with clear description
2. Address automated CI/CD checks
3. Respond to reviewer feedback
4. Make requested changes
5. Wait for approval from maintainers
6. Squash commits if requested
7. Merge after approval

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add JPEG DCT steganography support

- Implement DCT coefficient modification
- Add JPEG quality preservation
- Include roundtrip tests

Closes #123
```

**Commit types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

## Development Workflow

### Typical Contribution Flow

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create branch** from `main`
4. **Make changes** with tests
5. **Commit** with clear messages
6. **Push** to your fork
7. **Open PR** against `main`
8. **Address feedback**
9. **Merge** after approval

### Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. Build distribution packages
5. Publish to PyPI (future)
6. Update documentation

## Questions?

If you have questions about contributing:

- Open a [discussion](https://github.com/kalashnikxvxiii/stegvault/discussions)
- Check existing [issues](https://github.com/kalashnikxvxiii/stegvault/issues)
- Review [WIKI](https://github.com/kalashnikxvxiii/StegVault/wiki) for technical details

Thank you for contributing to StegVault!
