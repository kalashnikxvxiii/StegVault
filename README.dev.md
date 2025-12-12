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

### Security scan
```bash
bandit -r stegvault
```

## AI-Assisted Development

StegVault leverages AI assistance (Claude by Anthropic) for enhanced development workflows:

### Testing & Quality Assurance
- **Test Generation**: AI assists in creating comprehensive test suites
  - Edge case identification and coverage improvement
  - Mock object creation and test fixture design
  - Async test patterns for TUI components (pytest-asyncio)
  - Achieved 89% overall coverage with 740+ tests

### Bug Identification & Debugging
- **Root Cause Analysis**: Deep investigation of complex issues
  - Terminal rendering bugs (emoji width calculations, border overflows)
  - Event propagation in Textual framework (ModalScreen bypassing)
  - Async/await patterns and worker context issues
- **Debugging Strategies**: Systematic approaches using:
  - `git diff` analysis for change tracking
  - `mypy` and `pylint` for static analysis
  - Manual testing protocols for TUI components

### Technical Decision Support
- **Architecture Decisions**:
  - Multi-interface design (CLI, TUI, GUI roadmap)
  - Application layer controllers for code reuse
  - Stegano format selection (PNG LSB vs JPEG DCT)
- **Library Selection**:
  - Textual framework evaluation for TUI
  - jpeglib vs jpegio comparison
  - pytest-asyncio integration
- **Performance Optimization**:
  - Parallel tool execution strategies
  - Test execution efficiency
  - Coverage improvement techniques

### Code Review & Best Practices
- **Security Review**: Identifying potential vulnerabilities
- **Code Quality**: Following PEP 8, type hints, docstrings
- **Testing Standards**: Maintaining 80%+ coverage target
- **Documentation**: Comprehensive CHANGELOG and technical docs

### Limitations & Human Oversight
- All AI suggestions reviewed by maintainer before implementation
- Critical decisions (security, architecture) require human judgment
- AI assists but doesn't replace human expertise and domain knowledge
- Code formatting (Black) and linting (mypy) enforce consistency

## Pre-Commit Checklist

**IMPORTANT**: Run these checks before every `git commit` and `git push` to avoid CI failures.

### 1. Format Code with Black
```bash
black stegvault tests
```
**Why**: CI fails if code is not formatted. Black ensures consistent style.

### 2. Run All Tests Locally
```bash
pytest
```
**Why**: Catch test failures early. All 324 tests must pass.
**Expected**: `324 passed` (or current test count)

### 3. Run Bandit Security Scan
```bash
bandit -r stegvault
```
**Why**: Detect security issues before CI. Fix or suppress with `# nosec` if false positive.
**Expected**: No high/medium severity issues in production code

### 4. Check Type Hints (Optional but Recommended)
```bash
mypy stegvault
```
**Why**: Catch type errors early (mypy in CI is informational only)

### 5. Verify Git Status
```bash
git status
```
**Why**: Ensure all intended files are staged, no accidental commits of temp files

### 6. Check Recent Workflow Status (After Push)
```bash
gh run list --limit 3
```
**Why**: Verify CI, Code Quality, and Security Scan workflows pass
**Expected**: All workflows show `success` status

### Quick Pre-Commit Script

**Linux/Mac** (`pre-commit.sh`):
```bash
#!/bin/bash
set -e

echo "=== Formatting code with Black ==="
black stegvault tests

echo ""
echo "=== Running tests ==="
pytest

echo ""
echo "=== Running security scan ==="
bandit -r stegvault

echo ""
echo "=== All checks passed! ==="
echo "Ready to commit and push."
```

Make it executable: `chmod +x pre-commit.sh`

Run before commit: `./pre-commit.sh`

**Windows** (`pre-commit.ps1`):
```powershell
# Run with: .\pre-commit.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Formatting code with Black ==="
black stegvault tests

Write-Host "`n=== Running tests ==="
pytest

Write-Host "`n=== Running security scan ==="
bandit -r stegvault

Write-Host "`n=== All checks passed! ==="
Write-Host "Ready to commit and push."
```

Run before commit: `.\pre-commit.ps1`

**Note**: Both scripts are included in the repository root.

### Common CI Failure Fixes

**Problem**: Black formatting failure
**Fix**: Run `black stegvault tests` locally before commit

**Problem**: Test failure on CI but passes locally
**Fix**:
- Check if test relies on local files/state
- Ensure proper file cleanup in test teardown
- Use `--no-check-strength` flags in CLI tests to avoid prompt issues

**Problem**: Bandit security warnings
**Fix**:
- Review if it's a real issue or false positive
- Add `# nosec B###` comment if false positive (e.g., `# nosec B105` for intentional password strings)
- Include reason: `# nosec B105 - intentional placeholder`

**Problem**: Different behavior on Windows vs Linux CI
**Fix**:
- Use `tempfile.NamedTemporaryFile` with explicit `flush()`
- Close file handles explicitly before reading
- Use `Path` from `pathlib` for cross-platform paths

## Project Structure

```
stegvault/
├── crypto/          # Cryptography: Argon2id + XChaCha20-Poly1305
├── stego/           # Steganography: PNG LSB embedding
├── utils/           # Payload format, config handling
├── vault/           # Password vault management (v0.4.0+)
│   ├── core.py       # Vault and VaultEntry classes
│   ├── operations.py # Vault CRUD operations + import
│   ├── generator.py  # Password generator
│   └── totp.py       # TOTP/2FA support (v0.5.0+)
├── batch/           # Batch operations processor
└── cli.py           # Command-line interface

tests/
├── unit/            # Unit tests (324 tests, 84% coverage)
│   ├── test_crypto.py                    # 26 tests
│   ├── test_payload.py                   # 22 tests
│   ├── test_stego.py                     # 16 tests
│   ├── test_config.py                    # 28 tests
│   ├── test_batch.py                     # 20 tests
│   ├── test_vault.py                     # 49 tests
│   ├── test_cli.py                       # 53 tests
│   ├── test_vault_cli.py                 # 46 tests (vault CLI + TOTP)
│   ├── test_totp.py                      # 19 tests (TOTP/2FA)
│   ├── test_password_strength.py         # 24 tests (password validation)
│   ├── test_vault_search.py              # 24 tests (search/filter backend)
│   ├── test_vault_search_filter_cli.py   # 5 tests (search/filter CLI)
│   └── test_vault_update_delete_cli.py   # 12 tests (update/delete CLI)

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
