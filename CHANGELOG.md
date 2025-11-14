# Changelog

All notable changes to StegVault will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2025-01-14

### Added
- **🎉 Vault Mode - Full Password Manager Functionality**
  - Store multiple passwords in a single image (vault mode)
  - New `stegvault vault` command group with 8 subcommands
  - Dual-mode architecture: single password OR vault (user choice)
  - Auto-detection of format on restore (backward compatible)

- **Vault Commands**
  - `vault create` - Create new vault with first entry
  - `vault add` - Add entry to existing vault
  - `vault get` - Retrieve specific password by key
  - `vault list` - List all keys (passwords hidden)
  - `vault show` - Show entry details (password masked)
  - `vault update` - Update existing entry
  - `vault delete` - Delete entry from vault
  - `vault export` - Export vault to JSON (plaintext or redacted)

- **Password Generator**
  - Cryptographically secure password generation using `secrets` module
  - Customizable length, character sets (uppercase, lowercase, digits, symbols)
  - Option to exclude ambiguous characters (i, l, 1, L, o, 0, O)
  - Memorable passphrase generation
  - Password strength assessment with entropy calculation
  - `--generate` flag for all vault commands

- **Vault Metadata**
  - Full entry metadata: username, URL, notes, tags
  - Timestamps: created, modified, accessed
  - TOTP/2FA secret storage (prepared for future)
  - Version tracking (v1.0 single, v2.0 vault)

### Changed
- CLI now supports both single-password and vault workflows
- `backup` and `restore` commands remain unchanged (backward compatible)
- Vault data encrypted with same crypto stack (XChaCha20-Poly1305 + Argon2id)

### Technical
- **New Module**: `stegvault.vault` with 3 submodules
  - `vault.core` - VaultEntry and Vault dataclasses (100% coverage)
  - `vault.operations` - CRUD operations and serialization (91% coverage)
  - `vault.generator` - Password generation utilities (87% coverage)
- **49 new unit tests** for vault functionality (all passing)
- **Total test count**: 145 → 194 tests
- **Project coverage**: Maintained at 67% overall
- Fixed Python 3.14 deprecation warnings for `datetime.utcnow()`

### Documentation
- Updated ROADMAP.md with complete Gallery Vision
- Added vault architecture to development plan
- Comprehensive docstrings for all vault functions

## [0.3.3] - 2025-11-13

### Fixed

- CLI `--version` command now correctly displays the current version from `__version__`
- Previously showed hardcoded "0.2.0" instead of actual package version

### Changed

- Version test now dynamically checks against `__version__` instead of hardcoded value

## [0.3.2] - 2025-11-13

### Added

- **Expanded test suite**: 61 additional CLI tests
  - Total test count increased from 84 to 145 tests
  - CLI module now has 113 comprehensive tests covering all commands
  - New tests for config, batch, and end-to-end workflows
  - Improved edge case coverage and error handling scenarios

### Changed

- **Improved test coverage**: Overall coverage increased from 75% to 87%
  - CLI module: 78% → 81% coverage
  - Batch operations: 93% → 95% coverage
  - All core modules maintain high coverage (85%+)
- Code formatting: Applied Black formatter to test_cli.py for consistency

### Quality

- All 145 tests pass reliably across Python 3.9-3.14
- Better test organization and readability
- Enhanced CI/CD reliability with comprehensive test coverage

## [0.3.1] - 2025-11-13

### Added

- Comprehensive test coverage improvements:
  - Added 48 new tests for batch operations (20 tests) and configuration management (28 tests)
  - Overall test coverage increased from 57% to 75%
  - Batch operations module coverage: 0% → 93%
  - Configuration module coverage: 55% → 87%

### Fixed

- Security: Masked password logging in demo.py (GitHub CodeQL alert #41)
- Security: Added documentation for intentional password file writes in batch operations (GitHub CodeQL alert #32)
- Code quality: Removed 11 unused imports across multiple modules
- CI: Fixed cross-platform path comparison issues in configuration tests
  - Tests now properly handle Windows paths on Linux CI runners
  - Added platform-specific test skipping where appropriate

## [0.3.0] - 2025-11-13

### Added

- **Batch Operations**: Process multiple backups/restores from JSON configuration files
  - New `stegvault batch-backup` command: Create multiple backups in one operation
  - New `stegvault batch-restore` command: Restore multiple passwords in one operation
  - JSON-based configuration format with support for:
    - Multiple backup jobs with custom labels
    - Multiple restore jobs with optional file output
    - Shared passphrase across all operations
  - Features:
    - Progress tracking for each job
    - Continue-on-error mode (default) or stop-on-error
    - Success/failure summary with error details
    - Optional password display for restore operations
  - Example configuration file included in `examples/batch_example.json`
- **Configuration File Support**: Users can now customize StegVault settings via TOML config file
  - Config location: `~/.config/stegvault/config.toml` (Linux/Mac) or `%APPDATA%\StegVault\config.toml` (Windows)
  - Configurable Argon2id KDF parameters (time_cost, memory_cost, parallelism)
  - CLI behavior settings (check_strength, verbose mode)
  - New `stegvault config` command group with subcommands:
    - `stegvault config show`: Display current configuration
    - `stegvault config init`: Create default configuration file
    - `stegvault config path`: Show config file location
- Progress indicators for key derivation operations
  - Visual progress bar during Argon2id KDF (can take 1-3 seconds)
  - Progress feedback for encryption and decryption
  - User-friendly feedback for long-running operations
- Improved CLI output with operation status indicators

### Changed

- Crypto module functions now accept optional KDF parameters from config
- Dependencies: Added `tomli` and `tomli_w` for TOML support

## [0.2.1] - 2025-11-13

### Fixed

- **Critical bug fix**: Eliminated pixel overlap issue in LSB embedding
  - Previous hybrid approach (sequential header + pseudo-random payload) could cause pixel overlap
  - This resulted in rare data corruption (observed in CI tests on Python 3.9 and 3.11)
  - Now uses fully sequential embedding for 100% reliability

### Changed

- **Simplified steganography implementation**: Switched to sequential-only pixel ordering
  - Removed pseudo-random pixel shuffling logic (~60 lines of code)
  - All payload bits now embedded left-to-right, top-to-bottom
  - Simpler, faster, and more maintainable codebase
  - **Security model clarified**: Cryptographic strength comes from XChaCha20-Poly1305 + Argon2id, not pixel ordering
  - `seed` parameter now deprecated (kept for backward compatibility)

### Improved

- **Test reliability**: All 84 tests now pass consistently on all platforms
  - Fixed all Windows file locking issues
  - No more flaky tests on any Python version (3.9-3.14)
  - Test coverage: 57% overall, 88% stego module
- Code quality: Cleaner, more maintainable steganography module

## [0.2.0] - 2025-11-12

### Added

- Comprehensive CLI test suite with 20 new tests covering all commands
- End-to-end integration tests for complete backup/restore workflows
- Examples directory with working demonstrations:
  - Test image generation script (create_test_images.py)
  - Complete demo.py showing full workflow
  - Comprehensive examples/README.md with usage guides
- Support for edge cases in CLI (empty passwords, special characters, etc.)

### Changed

- **BREAKING CHANGE**: Modified LSB embedding strategy to fix critical design flaw
  - Header (magic + salt) now stored in sequential pixel order (first 20 bytes)
  - Remaining payload uses pseudo-random pixel ordering for security
  - Resolves circular dependency where seed derivation required salt extraction
  - Existing v0.1.0 backups are NOT compatible with v0.2.0
- Improved test coverage from 58% to 88% overall
- CLI coverage increased from 0% to 78%
- Better error messages and user feedback

### Fixed

- Critical bug in restore command that prevented password recovery
- Windows file locking issues in test suite (14 test errors resolved)
- Unicode display issues in Windows console (replaced with ASCII symbols)
- Proper PIL Image resource cleanup to prevent PermissionError
- Test fixtures now handle Windows-specific file locking correctly
- Fixed test_extract_with_wrong_seed to work with new sequential header

### Improved

- Test suite reliability: 82 of 84 tests passing (2 flaky on Windows)
- All core modules now properly close file handles
- Better separation of sequential and random pixel ordering
- More robust temp file cleanup in tests

### Documentation

- Added comprehensive examples with real working code
- Improved inline code documentation

### Security

- No security vulnerabilities introduced
- Core cryptography unchanged and secure
- New sequential header storage does not weaken security
  (header was already public, and contains no secrets except salt which is needed for KDF)

## [0.1.0] - 2025-11-10

### Added

- Initial release of StegVault
- Core cryptography module with XChaCha20-Poly1305 AEAD encryption
- Argon2id key derivation function with secure parameters
- PNG LSB steganography implementation with pseudo-random pixel ordering
- Versioned binary payload format with magic header
- Command-line interface with three main commands:
  - `backup`: Create encrypted backups embedded in images
  - `restore`: Recover passwords from stego images
  - `check`: Verify image capacity for password storage
- Comprehensive test suite with 63+ unit tests
- Support for RGB and RGBA PNG images
- Passphrase strength validation
- Automatic AEAD authentication tag verification
- CSPRNG-based salt and nonce generation

### Security Features

- Modern cryptography: XChaCha20-Poly1305 with 256-bit keys
- Strong KDF: Argon2id (3 iterations, 64MB memory, 4 threads)
- Detection resistance: Pseudo-random bit placement using seed derived from salt
- Integrity verification: AEAD tag ensures data hasn't been tampered with
- Zero-knowledge: All operations performed locally, no external dependencies

### Documentation

- Comprehensive README with usage examples
- Contributing guidelines (CONTRIBUTING.md)
- Development roadmap (ROADMAP.md)
- MIT License

### Testing

- 26 unit tests for cryptography module (90% coverage)
- 22 unit tests for payload format (100% coverage)
- 15 unit tests for steganography module
- Roundtrip tests for encryption → embedding → extraction → decryption

### Known Issues

- Windows console Unicode character display issues (does not affect functionality)
- Temporary file cleanup warnings in Windows during tests (Pillow file locking)

[0.4.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.4.0
[0.3.3]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.3.3
[0.3.2]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.3.2
[0.3.1]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.3.1
[0.3.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.3.0
[0.2.1]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.2.1
[0.2.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.2.0
[0.1.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.1.0
