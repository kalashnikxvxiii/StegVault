# Changelog

All notable changes to StegVault will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0-alpha.1] - 2025-12-02

### Added - TUI Phase 2: Vault Loading & Entry Display 🎨

- **🖥️ Terminal User Interface Foundation**
  - Full-featured TUI using Textual framework (v6.7.1)
  - Modern, keyboard-driven interface for terminal users
  - Async/await architecture for smooth interactions
  - `stegvault tui` command to launch interface

- **📂 File & Authentication Dialogs**
  - `FileSelectScreen` - Modal file browser with DirectoryTree widget
  - `PassphraseInputScreen` - Secure password-masked input
  - 3-step async vault loading flow (file → passphrase → load)
  - Comprehensive error handling and user feedback

- **📋 Vault Entry Display**
  - `VaultScreen` - Split view main screen (30% list / 70% detail)
  - `EntryListItem` - Entry list with tags display
  - `EntryDetailPanel` - Complete entry details viewer
  - Password visibility toggle (masked/plaintext)
  - All entry fields: password, username, URL, notes, tags, TOTP
  - Timestamps display (created, modified)

- **⌨️ Keyboard Navigation**
  - **c** - Copy password to clipboard
  - **v** - Toggle password visibility
  - **r** - Refresh vault (planned)
  - **escape** - Back to menu
  - **q** - Quit application
  - Mouse support for all interactions

- **📋 Clipboard Integration**
  - Copy passwords with single keypress (c)
  - Secure clipboard integration via pyperclip
  - Copy confirmation notifications

### New Dependencies
- `textual>=0.47.0` - Modern TUI framework
- `pytest-asyncio>=0.21.0` - Async test support (dev)

### New Modules
- `stegvault/tui/__init__.py` - TUI package exports
- `stegvault/tui/app.py` (165 lines) - Main TUI application
- `stegvault/tui/widgets.py` (375 lines) - Custom UI widgets
- `stegvault/tui/screens.py` (214 lines) - Screen layouts

### New Tests
- `tests/unit/test_tui_app.py` - 14 tests (app initialization, async vault loading)
- `tests/unit/test_tui_widgets.py` - 27 tests (all widgets with edge cases)
- `tests/unit/test_tui_screens.py` - 13 tests (screen actions and interactions)
- +54 tests (621 → 675, all passing)

### Coverage
- **TUI app.py**: 88% ✅ (exceeds 85% target)
- **TUI widgets.py**: 88% ✅ (exceeds 85% target)
- **TUI screens.py**: 66% (compose methods untested - acceptable)
- **Overall project**: 91% (maintained)

### Technical Details
- Async/await architecture using Textual's message pump
- VaultController integration for business logic
- DOM-based UI with CSS-like styling
- Comprehensive test mocking for Textual widgets
- Property-based mocking for `app` context

### What's Working
✅ Launch TUI with `stegvault tui`
✅ Open existing vault from image file
✅ Browse and select vault images
✅ Enter passphrase securely
✅ View all vault entries in list
✅ Display complete entry details
✅ Toggle password visibility
✅ Copy passwords to clipboard
✅ Navigate with keyboard shortcuts

### What's Next (Phase 3)
- Add new entry dialog
- Edit existing entry
- Delete entry with confirmation
- Entry search/filter
- Password generator integration
- TOTP code display

### Known Limitations
- No entry creation/editing yet (Phase 3)
- Refresh action not implemented
- Help screen placeholder only
- New vault creation not yet available

## [0.6.1] - 2025-11-28

### Added - Application Layer Architecture

- **🏗️ Application Controllers**
  - New `stegvault/app/` package for UI-agnostic business logic
  - `CryptoController` - High-level encryption/decryption operations
  - `VaultController` - Complete vault CRUD operations (load, save, create, add, update, delete)
  - Thread-safe design suitable for CLI, TUI, and future GUI
  - No UI framework dependencies - pure business logic

- **📊 Result Data Classes**
  - `EncryptionResult` - Structured encryption operation results
  - `DecryptionResult` - Structured decryption operation results
  - `VaultLoadResult` - Vault loading with error handling
  - `VaultSaveResult` - Vault saving with capacity checks
  - `EntryResult` - Entry retrieval with validation
  - Consistent error reporting across all controllers

- **🎯 Benefits**
  - Reusable from any UI layer (CLI/TUI/GUI)
  - Easy to test without mocking UI frameworks
  - Consistent business logic and error handling
  - Dependency injection support (optional Config)
  - Centralized validation and capacity checks

### New Modules
- `stegvault/app/__init__.py` - Application layer entry point
- `stegvault/app/controllers/__init__.py` - Controllers package
- `stegvault/app/controllers/crypto_controller.py` (172 lines) - Encryption controller
- `stegvault/app/controllers/vault_controller.py` (400 lines) - Vault management controller

### New Tests
- `tests/unit/test_crypto_controller.py` - 11 comprehensive tests (86% coverage)
- `tests/unit/test_vault_controller.py` - 18 comprehensive tests (83% coverage)
- +29 tests (585 → 614, all passing)

### Technical Details
- Controller coverage: 83-86% (missing lines are exception handlers)
- All methods return structured results with success/error info
- Thread-safe operations for future GUI implementation
- Full roundtrip testing (encrypt→decrypt, save→load)
- Integration with existing crypto and stego layers

## [0.6.0] - 2025-11-28

### Added - Headless Mode & Automation

- **🤖 JSON Output**
  - Machine-readable JSON output for all critical commands
  - `--json` flag for `check`, `vault get`, `vault list`
  - Structured format: `{"status": "success|error", "data": {...}}`
  - Error responses include `error_type` and `message` fields
  - Perfect for parsing with `jq` or JSON libraries

- **📄 Passphrase from File**
  - `--passphrase-file` option for non-interactive authentication
  - Read passphrase from secure file instead of interactive prompt
  - Supports `~/.vault_pass` and any custom file path
  - Automatic whitespace stripping for clean passphrases
  - Validation: empty files trigger exit code 2

- **🌍 Environment Variable Support**
  - `STEGVAULT_PASSPHRASE` environment variable
  - Completely non-interactive operation for CI/CD
  - Priority system: explicit > file > env > prompt
  - Empty env var triggers validation error (exit code 2)

- **🔢 Standardized Exit Codes**
  - Exit code 0: Success
  - Exit code 1: Runtime error (wrong passphrase, decryption error, file not found)
  - Exit code 2: Validation error (invalid input, empty passphrase)
  - Enables reliable automation and error handling

- **⚙️ Automation Examples**
  - CI/CD pipeline integration (GitHub Actions example)
  - Automated backup scripts
  - Password rotation scripts
  - All examples in README with real-world use cases

### New Modules
- `stegvault/utils/json_output.py` (67 lines) - JSON formatting utilities with 20+ helper functions
- `stegvault/utils/passphrase.py` (36 lines) - Flexible passphrase handling (file/env/prompt)

### New Tests
- `tests/unit/test_headless_mode.py` - 20 integration tests for headless features
- `tests/unit/test_json_output.py` - 29 unit tests for all JSON formatters
- `tests/unit/test_passphrase_utils.py` - 22 unit tests for passphrase handling
- Total: +71 tests (514 → 585, all passing)

### Changed
- Modified `vault get` to support `--json` and `--passphrase-file`
- Modified `vault list` to support `--json` and `--passphrase-file`
- Modified `check` to support `--json` output
- Updated error handling to use standardized exit codes
- Fixed validation error for negative clipboard timeout (exit code 1 → 2)

### Testing & Coverage
- Coverage: 91% → 92% (+1%)
- Total tests: 514 → 585 (+71 tests, 100% pass rate)
- **25 out of 26 modules at 100% coverage** (96%)
  - `json_output.py`: 100% coverage ✅
  - `passphrase.py`: 100% coverage ✅
  - `cli.py`: 84% (expected - not all commands need headless support)

### Documentation
- Comprehensive headless mode section in README
- 3 real-world automation examples (CI/CD, backup, password rotation)
- Passphrase priority system explained
- Exit code documentation
- Updated feature list and badges

### Use Cases Enabled
- ✅ CI/CD pipeline integration (GitHub Actions, GitLab CI)
- ✅ Automated backup scripts (cron jobs, systemd timers)
- ✅ Password rotation automation
- ✅ Server/headless environments
- ✅ Programmatic vault management

## [0.5.1] - 2025-11-27

### Added - JPEG DCT Steganography
- **🖼️ Dual Format Support**
  - JPEG steganography using DCT coefficient modification
  - Automatic format detection (PNG LSB vs JPEG DCT)
  - All vault commands now support both PNG and JPEG images
  - Works with `.png` and `.jpg`/`.jpeg` extensions seamlessly

- **📊 JPEG Implementation Details**
  - DCT coefficient modification in 8x8 blocks across Y, Cb, Cr channels
  - Anti-shrinkage: only modifies coefficients with |value| > 1
  - Robust against JPEG recompression (frequency domain approach)
  - Lower capacity than PNG (~20%) but more resilient
  - Typical capacity: ~18KB for 400x600 Q85 JPEG vs ~90KB for PNG

### New Modules
- `stegvault/stego/jpeg_dct.py` - JPEG DCT steganography implementation (303 lines)
- `stegvault/stego/dispatcher.py` - Automatic PNG/JPEG routing
- `stegvault/utils/image_format.py` - Image format detection utilities

### Dependencies
- Added `jpeglib>=1.0.0` for DCT coefficient access and manipulation

### Changed
- Modified `stegvault/stego/__init__.py` to use dispatcher instead of direct PNG LSB
- Updated all CLI commands to support both PNG and JPEG transparently
- Dispatcher handles both path strings and PIL Image objects

### Testing & Coverage
- Coverage improved: 88% → 91% (+3%)
- Total tests: 429 → 451 (+22 tests)
- All 451 tests passing (100% pass rate)
- 21 out of 22 modules at 100% coverage

### Documentation
- Updated README with JPEG support explanation
- Added PNG vs JPEG comparison with capacity metrics
- Updated security considerations for format-specific warnings
- Added JPEG DCT technique description with code examples

## [0.5.0] - 2025-11-26

### Added - Gallery Foundation
- **🖼️ Gallery Management System**
  - New `gallery` command group for managing multiple vault images
  - SQLite-backed metadata database for vault organization
  - Centralized gallery at `~/.stegvault/gallery.db`
  - 6 new CLI commands: `init`, `add`, `list`, `remove`, `refresh`, `search`

- **🔍 Cross-Vault Search**
  - Search across all vaults simultaneously
  - Cached entry metadata for instant search results
  - Filter search by specific vault or search all
  - Field-specific search (key, username, URL)

- **🗄️ Vault Metadata Management**
  - Track vault entry counts, tags, and descriptions
  - Last accessed timestamps for vault usage tracking
  - Tag-based vault organization and filtering
  - Automatic metadata caching on vault add/refresh

### New Modules
- `stegvault/gallery/` - Complete gallery management system
  - `core.py` - Gallery, VaultMetadata, VaultEntryCache classes
  - `db.py` - SQLite database operations (88% coverage)
  - `operations.py` - High-level gallery operations (72% coverage)
  - `search.py` - Cross-vault search functionality (40% coverage)

### Testing
- 22 new comprehensive gallery tests (100% pass rate)
- Total tests: 324 → 346 (+22 tests)
- Overall coverage: 84% → 78% (new gallery code added)
- Gallery module coverage: 82% average

### Changed
- Moved `extract_full_payload()` to `utils/payload.py` for code reuse
- Updated CLI to import shared `extract_full_payload()` function
- Reorganized documentation with Gallery Mode section

## [0.4.1] - 2025-11-24

### Added
- **🔍 Vault Search and Filter Commands**
  - New `vault search` command: Search entries by query string across multiple fields
  - New `vault filter` command: Filter entries by tags or URL patterns
  - Search supports case-sensitive/insensitive modes and field-specific searches
  - Filter supports tag matching (ANY or ALL) and URL pattern matching (exact or substring)
  - 24 comprehensive tests for search and filter functionality
  - Backend functions: `search_entries()`, `filter_by_tags()`, `filter_by_url()`

### Changed
- Updated vault group documentation to include new search and filter commands
- Improved vault/operations.py coverage from 58% to 94%

## [0.4.0] - 2025-11-24

### Added - Major Features
- **🎉 Vault Import/Export Workflow**
  - New `vault import` command: Restore entire vault from JSON backup
  - Complements existing `vault export` for complete backup/restore workflows
  - Enables vault migration and cross-platform backups
  - Full validation of imported JSON structure
  - 7 comprehensive tests for import functionality

- **🔐 TOTP/2FA Authenticator Support**
  - New `vault totp` command: Generate time-based one-time passwords
  - Built-in authenticator eliminates need for separate 2FA apps
  - QR code display (ASCII art) for easy setup with mobile authenticators
  - Manual entry option with complete setup details (account, secret, type, digits, period)
  - TOTP secret storage in vault entries
  - Integration with `create`, `add`, and `update` commands via `--totp` flag
  - Alias `--totp` for easier use (in addition to `--totp-generate`)
  - Time remaining indicator for code validity
  - New `stegvault.vault.totp` module with 6 functions (100% coverage)
  - 19 comprehensive TOTP tests
  - Dependencies: `pyotp>=2.9.0`, `qrcode>=7.4.0`

- **📋 Secure Clipboard Integration**
  - New `--clipboard` flag for `vault get` command
  - Copy passwords directly to clipboard without screen display
  - Auto-clear functionality with `--clipboard-timeout` option
  - Enhanced security: passwords masked when using clipboard
  - Cross-platform support (Windows, Linux, macOS)
  - 5 comprehensive clipboard tests
  - Dependency: `pyperclip>=1.8.0`

- **🛡️ Realistic Password Strength Validation**
  - Integrated **zxcvbn** library for industry-standard password strength assessment
  - Detects common passwords, patterns, dictionary words, sequences
  - Provides specific, actionable feedback for weak passwords
  - 5-level scoring (0-4: Very Weak, Weak, Fair, Strong, Very Strong)
  - New `get_password_strength_details()` function for comprehensive analysis
  - Returns score, crack time estimate, warnings, and suggestions
  - Updated `assess_password_strength()` to use zxcvbn instead of entropy
  - More accurate than basic character-type validation
  - 24 comprehensive tests for password strength validation
  - Dependency: `zxcvbn>=4.4.28`

### Fixed
- **Critical vault CLI bug fixes** (all 8 vault commands were non-functional in v0.4.0):
  - Fixed `parse_payload` import conflicts between vault and utils.payload modules
  - Fixed `extract_payload` missing parameters (seed, payload_size)
  - Fixed `decrypt_data` parameter order bug (salt/passphrase positions swapped)
  - Created `extract_full_payload()` helper function for proper multi-step extraction
  - All vault commands now fully functional: create, add, get, list, show, update, delete, export, import
- **TOTP UX improvements**:
  - Better QR code parameters for scanning (error correction, inverted colors)
  - Manual entry option always shown (not all authenticators can scan ASCII QR)
  - Flag alias `--totp` added for convenience

### Improved
- **Test suite expansion**:
  - Total test count: 194 → 275 tests (+81 tests, all passing)
  - New test files: `test_vault_cli.py` (38 tests), `test_totp.py` (19 tests), `test_password_strength.py` (24 tests)
  - Vault CLI tests: 26 → 38 tests (import, clipboard, TOTP)
  - 100% coverage for TOTP module
  - Comprehensive real-world password testing
- **Test coverage**:
  - Overall coverage: 67% → 80% (total statements: 1843)
  - CLI module coverage: 44% → 71% (+27 percentage points)
  - Crypto module coverage: 87% → 84% (more code, similar coverage)
  - Vault generator module: 87% → 93% (+6 percentage points)
  - Vault operations module: 91% coverage (import functionality)
- **Code quality**:
  - Fixed test fixture file conflicts with independent temp file creation
  - Improved test reliability across all platforms
  - Better separation of concerns in payload parsing
  - Comprehensive monkeypatching for clipboard and user input testing
  - More realistic password validation than entropy-based methods

### Changed
- **Password strength validation behavior**:
  - Now uses zxcvbn for realistic strength assessment
  - More permissive: Long passphrases accepted even without all character types
  - More strict: Common passwords rejected even with all character types
  - Better feedback: Specific warnings instead of generic "add uppercase" messages
- **Password generator assessment**:
  - `assess_password_strength()` now returns `(label, zxcvbn_score)` instead of `(label, entropy)`
  - Labels updated: "Very Weak", "Weak", "Fair", "Strong", "Very Strong" (5 levels)

### Documentation
- Updated README.md with all new features (import, clipboard, TOTP, password strength)
- Updated version badges and test statistics (275 tests, 80% coverage)
- Updated ROADMAP.md to reflect completed features
- Removed completed items from "Coming Soon" section
- Updated project structure documentation with new modules

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

[0.4.1]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.4.1
[0.4.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.4.0
[0.3.3]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.3.3
[0.3.2]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.3.2
[0.3.1]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.3.1
[0.3.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.3.0
[0.2.1]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.2.1
[0.2.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.2.0
[0.1.0]: https://github.com/kalashnikxvxiii-collab/stegvault/releases/tag/v0.1.0
