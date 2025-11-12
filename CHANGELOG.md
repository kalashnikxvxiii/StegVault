# Changelog

All notable changes to StegVault will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- CLI coverage improved from 78% to 80%
- Overall coverage improved to 88%
- Total test count: 84 tests (81 passing, 3 flaky on Windows)
- Crypto module functions now accept optional KDF parameters from config
- Dependencies: Added `tomli` and `tomli_w` for TOML support

### Known Issues
- Two tests are flaky on Windows due to rapid file operations:
  - `test_multiple_backups_different_images`: Fails intermittently when creating multiple backups in rapid succession
  - `test_restore_wrong_passphrase`: Occasional timing issues with temporary file cleanup
  - These issues do not affect real-world CLI usage and only occur in test scenarios

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

[0.1.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.1.0
