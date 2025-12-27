# Developer Guide

Complete guide for developers contributing to StegVault or integrating it into other projects.

**Version**: 0.6.1 (Application Layer)

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Guidelines](#coding-guidelines)
- [Testing](#testing)
- [Contributing](#contributing)

## Getting Started

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/kalashnikxvxiii/StegVault.git
cd StegVault

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e .[dev]

# Verify installation
python -m pytest --cov=stegvault
```

### Prerequisites

- **Python**: 3.9+ (tested on 3.9-3.14)
- **Git**: For version control
- **Development Tools**:
  - Black (code formatting)
  - mypy (type checking)
  - pytest (testing)
  - pytest-cov (coverage)

### First-Time Setup

```bash
# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Run full test suite
pytest --cov=stegvault --cov-report=html

# Check code formatting
black --check stegvault tests

# Run type checker
mypy stegvault
```

## Project Structure

```
StegVault/
├── stegvault/                      # Main package
│   ├── __init__.py                 # Package exports (version: 0.7.8)
│   ├── cli.py                      # CLI interface (Click, 1389 lines)
│   │
│   ├── app/                        # Application layer (v0.6.1)
│   │   ├── __init__.py
│   │   └── controllers/            # UI-agnostic business logic
│   │       ├── __init__.py
│   │       ├── crypto_controller.py  # Encryption controller (172 lines)
│   │       └── vault_controller.py   # Vault CRUD controller (400 lines)
│   │
│   ├── crypto/                     # Cryptography module
│   │   ├── __init__.py
│   │   └── core.py                 # XChaCha20-Poly1305 + Argon2id (89 lines)
│   │
│   ├── vault/                      # Vault management
│   │   ├── __init__.py
│   │   ├── core.py                 # Vault/VaultEntry dataclasses (81 lines)
│   │   ├── operations.py           # CRUD operations (105 lines)
│   │   ├── generator.py            # Password generator (81 lines)
│   │   └── totp.py                 # TOTP/2FA authenticator (31 lines)
│   │
│   ├── stego/                      # Steganography module
│   │   ├── __init__.py
│   │   ├── png_lsb.py              # PNG LSB steganography (120 lines)
│   │   ├── jpeg_dct.py             # JPEG DCT steganography (132 lines) **v0.5.1**
│   │   └── dispatcher.py           # Format auto-detection (53 lines) **v0.5.1**
│   │
│   ├── gallery/                    # Multi-vault management
│   │   ├── __init__.py
│   │   ├── core.py                 # Gallery dataclass (57 lines)
│   │   ├── db.py                   # SQLite database (173 lines)
│   │   ├── operations.py           # Gallery CRUD (77 lines)
│   │   └── search.py               # Cross-vault search (42 lines)
│   │
│   ├── batch/                      # Batch processing
│   │   ├── __init__.py
│   │   └── core.py                 # Batch operations (129 lines)
│   │
│   ├── config/                     # Configuration system
│   │   ├── __init__.py
│   │   └── core.py                 # TOML config (89 lines)
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── payload.py              # Payload format (83 lines)
│       ├── image_format.py         # Magic byte detection (50 lines) **v0.5.1**
│       ├── json_output.py          # JSON formatting (67 lines) **v0.6.0**
│       └── passphrase.py           # Passphrase handling (36 lines) **v0.6.0**
│
├── tests/unit/                     # Unit tests (994 tests, 79% coverage)
│   ├── test_crypto.py              # Crypto module (26 tests, 100% coverage)
│   ├── test_crypto_controller.py   # CryptoController (14 tests, 96%) **v0.6.1**
│   ├── test_vault.py               # Vault core (55 tests, 100% coverage)
│   ├── test_vault_controller.py    # VaultController (21 tests, 83%) **v0.6.1**
│   ├── test_vault_cli.py           # Vault CLI (44 tests)
│   ├── test_stego.py               # PNG LSB (16 tests, 100% coverage)
│   ├── test_jpeg_stego.py          # JPEG DCT (48 tests, 98% coverage)
│   ├── test_gallery.py             # Gallery (52 tests, 100% coverage)
│   ├── test_json_output.py         # JSON output (29 tests, 100%) **v0.6.0**
│   ├── test_passphrase_utils.py    # Passphrase (22 tests, 100%) **v0.6.0**
│   ├── test_totp.py                # TOTP/2FA (19 tests)
│   ├── test_batch.py               # Batch ops (27 tests, 100% coverage)
│   ├── test_config.py              # Config (33 tests, 100% coverage)
│   ├── test_payload.py             # Payload (22 tests, 100% coverage)
│   ├── test_tui_app.py             # TUI app (18 tests, 88%) **v0.7.0**
│   ├── test_tui_widgets.py         # TUI widgets (126 tests, 88%) **v0.7.0**
│   ├── test_tui_screens.py         # TUI screens (27 tests, 66%) **v0.7.0**
│   ├── test_updater.py             # Auto-update (87 tests, 91%) **v0.7.6-v0.7.8**
│   └── ...                         # Total: 994 tests
│
├── wiki/                           # GitHub wiki documentation
│   ├── Home.md
│   ├── Architecture-Overview.md
│   ├── API-Reference.md
│   └── ...
│
├── pyproject.toml                  # Project metadata & dependencies
├── CHANGELOG.md                    # Version history
├── CONTRIBUTING.md                 # Contribution guidelines
└── README.md                       # Main documentation
```

### Key Architectural Components

#### Application Layer (v0.6.1)

The **Application Layer** provides UI-agnostic business logic:

- **Controllers**: High-level operations with structured results
- **Result Types**: `@dataclass` objects (`EncryptionResult`, `VaultLoadResult`, etc.)
- **Benefits**: Reusable from CLI/TUI/GUI, easy testing, thread-safe

**Example**:
```python
from stegvault.app.controllers import VaultController

controller = VaultController()
result = controller.load_vault("vault.png", "passphrase")
if result.success:
    vault = result.vault
```

#### Core Modules

- **crypto/**: XChaCha20-Poly1305 AEAD + Argon2id KDF
- **vault/**: Password vault data structures and operations
- **stego/**: Dual steganography (PNG LSB + JPEG DCT with auto-detection)
- **gallery/**: Multi-vault management with SQLite
- **utils/**: Shared utilities (payload, JSON, passphrase handling)

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make your changes**
   - Write code following [Coding Guidelines](#coding-guidelines)
   - Add/update tests (maintain 80%+ coverage)
   - Update documentation (docstrings, README, wiki)

3. **Format code with Black**
   ```bash
   black stegvault tests
   ```

4. **Run tests**
   ```bash
   pytest --cov=stegvault --cov-report=term
   ```

5. **Verify formatting** (CI check)
   ```bash
   black --check stegvault tests
   ```

6. **Commit changes** (conventional commits)
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   # Create PR on GitHub
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

**Examples**:
```bash
git commit -m "feat: add JPEG DCT steganography support"
git commit -m "fix: handle empty passphrase in CLI"
git commit -m "test: add VaultController CRUD tests"
git commit -m "docs: update API reference for v0.6.1"
```

### Pre-Commit Checklist

**CRITICAL**: Always run before committing:

```bash
# 1. Format code
black stegvault tests

# 2. Run full test suite
pytest --cov=stegvault --cov-report=term

# 3. Verify formatting (CI will check this)
black --check stegvault tests
```

**CI will fail** if code is not formatted with Black.

## Coding Guidelines

### Python Style

- **PEP 8**: Follow Python style guide
- **Formatter**: Black (line length: 88)
- **Type Hints**: Required for public APIs
- **Docstrings**: Google style for all modules/classes/functions

### Code Quality Rules

1. **Simplicity Over Cleverness**
   - Write clear, readable code
   - Avoid premature optimization
   - Prefer explicit over implicit

2. **Error Handling**
   - Controllers return structured results (no exceptions)
   - Core modules raise specific exceptions
   - Validate inputs at boundaries

3. **Testing**
   - Write tests BEFORE or WITH code
   - Aim for 80%+ coverage
   - Test edge cases and error paths

4. **Documentation**
   - Add docstrings to all public APIs
   - Update README for user-facing changes
   - Update wiki for architectural changes

### Type Hints

All public APIs must have type hints:

```python
from typing import Optional, Tuple, List

def encrypt_data(
    plaintext: bytes,
    passphrase: str,
    time_cost: int = 3
) -> Tuple[bytes, bytes, bytes]:
    """Encrypt data with passphrase.

    Args:
        plaintext: Data to encrypt
        passphrase: Encryption passphrase
        time_cost: Argon2id time cost

    Returns:
        Tuple of (ciphertext, salt, nonce)
    """
    ...
```

### Docstring Format

Use Google-style docstrings:

```python
def load_vault(image_path: str, passphrase: str) -> VaultLoadResult:
    """Load vault from image file.

    This function extracts the encrypted vault from a stego image,
    decrypts it, and parses the JSON structure.

    Args:
        image_path: Path to stego image containing vault
        passphrase: Vault encryption passphrase

    Returns:
        VaultLoadResult with vault object and success status

    Raises:
        ValueError: If image format is unsupported
        PayloadFormatError: If vault data is corrupted

    Example:
        >>> controller = VaultController()
        >>> result = controller.load_vault("vault.png", "pass")
        >>> if result.success:
        ...     vault = result.vault
    """
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=stegvault --cov-report=term

# Run specific test file
pytest tests/unit/test_crypto_controller.py

# Run specific test
pytest tests/unit/test_vault.py::TestVault::test_add_entry

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=stegvault --cov-report=html
# Open htmlcov/index.html
```

### Test Structure

Tests are organized by module:

```python
# tests/unit/test_vault_controller.py
import pytest
from stegvault.app.controllers import VaultController
from stegvault.vault import Vault

class TestVaultController:
    """Tests for VaultController."""

    @pytest.fixture
    def controller(self):
        """Create VaultController instance."""
        return VaultController()

    def test_create_new_vault(self, controller):
        """Should create new vault with first entry."""
        vault, success, error = controller.create_new_vault(
            key="test", password="secret"
        )

        assert success is True
        assert vault.has_entry("test")
```

### Writing Good Tests

1. **Use Fixtures**
   ```python
   @pytest.fixture
   def test_image(tmp_path):
       """Create test image."""
       from PIL import Image
       img = Image.new("RGB", (100, 100))
       path = tmp_path / "test.png"
       img.save(path)
       return str(path)
   ```

2. **Test One Thing**
   ```python
   def test_encrypt_success(self, controller):
       """Should successfully encrypt data."""
       result = controller.encrypt(b"data", "pass")
       assert result.success is True
   ```

3. **Use Descriptive Names**
   ```python
   def test_load_vault_wrong_passphrase(self):
       """Should fail with wrong passphrase."""
   ```

4. **Test Error Cases**
   ```python
   def test_add_duplicate_key(self, controller):
       """Should fail when adding duplicate key."""
       vault, _, _ = controller.create_new_vault(key="test", password="p")
       vault, success, error = controller.add_vault_entry(
           vault, key="test", password="p"
       )
       assert success is False
       assert "already exists" in error
   ```

### Coverage Goals

- **Overall**: 80%+ (current: 92%)
- **Critical Modules**: 100%
  - crypto/core.py ✅
  - vault/core.py ✅
  - stego/png_lsb.py ✅
  - stego/jpeg_dct.py ✅ (98%)
  - gallery/db.py ✅
- **Controllers**: 85%+
  - CryptoController: 86% ✅
  - VaultController: 83% ✅

## Working with Controllers (v0.6.1)

### Adding New Controllers

1. **Create controller file**
   ```python
   # stegvault/app/controllers/my_controller.py
   from dataclasses import dataclass
   from typing import Optional

   @dataclass
   class MyResult:
       """Result of my operation."""
       data: Optional[dict]
       success: bool
       error: Optional[str] = None

   class MyController:
       """Controller for my operations."""

       def do_something(self, param: str) -> MyResult:
           """Do something with param."""
           try:
               # Business logic here
               return MyResult(data={"result": "ok"}, success=True)
           except Exception as e:
               return MyResult(data=None, success=False, error=str(e))
   ```

2. **Add to __init__.py**
   ```python
   # stegvault/app/controllers/__init__.py
   from stegvault.app.controllers.my_controller import MyController, MyResult

   __all__ = ["CryptoController", "VaultController", "MyController"]
   ```

3. **Write comprehensive tests**
   ```python
   # tests/unit/test_my_controller.py
   class TestMyController:
       @pytest.fixture
       def controller(self):
           return MyController()

       def test_do_something(self, controller):
           result = controller.do_something("param")
           assert result.success is True
   ```

### Controller Design Patterns

1. **Structured Results**
   - Use `@dataclass` for return types
   - Always include `success: bool` and `error: Optional[str]`
   - Return actual data in dedicated fields

2. **No Exceptions**
   - Controllers catch exceptions and return error results
   - UI layer handles success/error display

3. **Thread-Safe**
   - No shared mutable state
   - Use immutable data structures
   - Safe for concurrent access (future GUI)

## Contributing

### Pull Request Process

1. **Fork the repository**
2. **Create feature branch** from `main`
3. **Make changes** following guidelines
4. **Run pre-commit checks** (Black, tests)
5. **Push to your fork**
6. **Create Pull Request** with:
   - Clear description of changes
   - Link to related issues
   - Test results
   - Screenshots (if UI changes)

### PR Review Criteria

- ✅ Code formatted with Black
- ✅ All tests passing
- ✅ Coverage maintained/improved
- ✅ Documentation updated
- ✅ No breaking changes (or clearly marked)
- ✅ Follows architectural patterns

### Code Review Guidelines

**For Reviewers**:
- Check architectural fit
- Verify test coverage
- Look for edge cases
- Suggest improvements (not demands)
- Be respectful and constructive

**For Contributors**:
- Respond to all comments
- Make requested changes
- Ask questions if unclear
- Update PR description with changes

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 0.6.1)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Creating a Release

1. **Update version**
   ```python
   # stegvault/__init__.py
   __version__ = "0.7.0"
   ```
   ```toml
   # pyproject.toml
   version = "0.7.0"
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [0.7.0] - 2025-XX-XX

   ### Added
   - Feature description

   ### Changed
   - Change description

   ### Fixed
   - Fix description
   ```

3. **Update README.md** (badges, features list)

4. **Run pre-commit checks**
   ```bash
   black stegvault tests
   pytest --cov=stegvault
   black --check stegvault tests
   ```

5. **Commit and tag**
   ```bash
   git add -A
   git commit -m "chore: release v0.7.0"
   git push origin main
   git tag v0.7.0
   git push origin v0.7.0
   ```

6. **Create GitHub release** (triggers PyPI publish)
   ```bash
   gh release create v0.7.0 --title "v0.7.0 - TUI Mode" --notes "..."
   ```

## Resources

### Documentation

- [Architecture Overview](Architecture-Overview.md) - System architecture
- [API Reference](API-Reference.md) - Complete API documentation
- [Testing Guide](Testing-Guide.md) - Comprehensive testing guide
- [Security Model](Security-Model.md) - Security assumptions

### External Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

### Tools

- [Black](https://black.readthedocs.io/) - Code formatter
- [pytest](https://docs.pytest.org/) - Testing framework
- [mypy](https://mypy.readthedocs.io/) - Type checker
- [coverage.py](https://coverage.readthedocs.io/) - Coverage measurement

## Getting Help

- **Discussions**: [GitHub Discussions](https://github.com/kalashnikxvxiii/stegvault/discussions)
- **Issues**: [Issue Tracker](https://github.com/kalashnikxvxiii/stegvault/issues)
- **Wiki**: [GitHub Wiki](https://github.com/kalashnikxvxiii/stegvault/wiki)

## License

StegVault is released under the MIT License. See [LICENSE](../LICENSE) for details.
