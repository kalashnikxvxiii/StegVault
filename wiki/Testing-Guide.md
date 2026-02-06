# Testing Guide

Comprehensive guide to testing in StegVault.

**Version**: 0.7.10
**Test Suite**: 1078 tests, 81% coverage

## Table of Contents

- [Overview](#overview)
- [Running Tests](#running-tests)
- [Test Organization](#test-organization)
- [Writing Tests](#writing-tests)
- [Coverage Analysis](#coverage-analysis)
- [CI/CD Integration](#cicd-integration)

## Overview

### Test Statistics (v0.7.10)

```
Total Tests:     1078
Pass Rate:       100% (1073 passing, 5 skipped)
Overall Coverage: 81%
Modules at 100%:  20/37 (54%)
Test Duration:    ~2 minutes (full suite: ~4-5 min with test_tui_app.py)
```

### Test Framework

- **Framework**: pytest
- **Coverage**: pytest-cov
- **Fixtures**: pytest fixtures for setup/teardown
- **Mocking**: unittest.mock for external dependencies
- **Temp Files**: pytest tmp_path for file operations

### Coverage Goals

- **Overall Target**: 80%+ ✅ (achieved: 81%)
- **Critical Modules**: 100%
- **Controllers**: 85%+
- **CLI**: 80%+

### Skipped Tests and Warnings

- **5 tests are skipped by design** (TUI/updater edge cases; see [TEST_PERFORMANCE.md](../docs/dev/TEST_PERFORMANCE.md#known-test-behavior-skipped-tests--warnings)).
- **~33 warnings** (ResourceWarning, RuntimeWarning) may appear; they are acceptable and documented in the same guide. They do not affect the pass count.

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=stegvault

# Run with detailed coverage report
pytest --cov=stegvault --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=stegvault --cov-report=html
# Open htmlcov/index.html in browser
```

### Selective Testing

```bash
# Run specific test file
pytest tests/unit/test_crypto_controller.py

# Run specific test class
pytest tests/unit/test_vault.py::TestVault

# Run specific test method
pytest tests/unit/test_vault.py::TestVault::test_add_entry

# Run tests matching pattern
pytest -k "test_vault"

# Run tests with verbose output
pytest -v

# Run tests with extra verbose output
pytest -vv
```

## Test Organization

### Directory Structure

```
tests/
└── unit/                           # Unit tests (614 tests)
    ├── test_crypto.py              # Cryptography (26 tests, 100%)
    ├── test_crypto_controller.py   # CryptoController (11 tests, 86%) **NEW**
    ├── test_vault.py               # Vault core (55 tests, 100%)
    ├── test_vault_controller.py    # VaultController (18 tests, 83%) **NEW**
    ├── test_vault_cli.py           # Vault CLI (44 tests)
    ├── test_stego.py               # PNG LSB (16 tests, 100%)
    ├── test_jpeg_stego.py          # JPEG DCT (48 tests, 98%)
    ├── test_gallery.py             # Gallery (52 tests, 100%)
    ├── test_json_output.py         # JSON formatting (29 tests, 100%) **NEW**
    ├── test_passphrase_utils.py    # Passphrase handling (22 tests, 100%) **NEW**
    └── ...                         # 614 total tests
```

## Writing Tests

### Test Structure

```python
# tests/unit/test_vault_controller.py
import pytest
from stegvault.app.controllers import VaultController

class TestVaultController:
    """Tests for VaultController."""

    @pytest.fixture
    def controller(self):
        """Create VaultController instance."""
        return VaultController()

    def test_create_new_vault(self, controller):
        """Should create new vault with first entry."""
        # Arrange
        key = "gmail"
        password = "secret123"

        # Act
        vault, success, error = controller.create_new_vault(
            key=key, password=password
        )

        # Assert
        assert success is True
        assert vault.has_entry(key)
```

### Testing Controllers (v0.6.1)

Controllers return structured results:

```python
def test_load_vault_success(self, controller, test_image):
    """Should successfully load vault."""
    result = controller.load_vault(test_image, "pass")

    assert result.success is True
    assert result.vault is not None

def test_load_vault_wrong_passphrase(self, controller, test_image):
    """Should fail with wrong passphrase."""
    result = controller.load_vault(test_image, "wrong_pass")

    assert result.success is False
    assert result.error is not None
```

## Coverage Analysis

### Current Coverage (v0.6.1)

```
Module                              Coverage
----------------------------------------
crypto/core.py                      100% ✅
vault/core.py                       100% ✅
stego/png_lsb.py                    100% ✅
stego/jpeg_dct.py                    98% ✅
gallery/db.py                       100% ✅
utils/json_output.py                100% ✅
utils/passphrase.py                 100% ✅
app/controllers/crypto_controller.py  86%
app/controllers/vault_controller.py   83%
cli.py                               84%
----------------------------------------
Overall                              81% ✅
```

## CI/CD Integration

### GitHub Actions

StegVault uses 4 CI workflows:

1. **CI**: Tests on Python 3.9-3.14
2. **Code Quality**: Black formatting, mypy, Bandit
3. **Security**: CodeQL analysis
4. **Release**: Auto-publish to PyPI

### Pre-Commit Checklist

```bash
# 1. Format code
black stegvault tests

# 2. Run tests
pytest --cov=stegvault

# 3. Verify formatting
black --check stegvault tests
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Developer Guide](Developer-Guide.md)
- [API Reference](API-Reference.md)
