# Changelog

All notable changes to StegVault will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.9] - 2025-12-27

### Added - Advanced Settings for Cryptography ⚙️

**Comprehensive Argon2id Parameter Validation System**:
- `stegvault/tui/widgets.py`: Added Advanced Settings section in SettingsScreen
  - Collapsible "Advanced Settings" panel for expert users
  - Three configurable Argon2id KDF parameters:
    - **Time Cost** (iterations): Controls computational cost (default: 3)
    - **Memory Cost** (KB): Controls memory usage (default: 65536 = 64MB)
    - **Parallelism** (threads): Controls thread count (default: 4)
  - Input validation with real-time feedback
  - Security-aware threshold warnings
  - Cross-parameter compatibility checks

**Individual Parameter Validators**:
- `_validate_time_cost()`: Validates time cost parameter
  - Minimum: 1 (CRITICAL security warning)
  - Weak security warning: < 3
  - Performance warning: > 20 (with estimated delay)
  - Recommended range: 3-10 iterations
  - Returns clear, actionable warning messages
- `_validate_memory_cost()`: Validates memory cost parameter
  - Minimum: 8192 KB = 8 MB (CRITICAL security warning)
  - Weak security warning: < 65536 KB (64 MB)
  - High memory warning: > 1048576 KB (1 GB)
  - Recommended: 65536-524288 KB (64-512 MB)
  - Memory impact warnings with MB conversions
- `_validate_parallelism()`: Validates parallelism parameter
  - Minimum: 1 thread
  - Warning: > 8 threads (diminishing returns)
  - Warning: > 16 threads (may reduce performance)
  - Recommended: 1-8 threads based on CPU cores

**Cross-Parameter Compatibility Validation**:
- `_validate_crypto_compatibility()`: Validates parameter combinations
  - Low memory + high parallelism: thread contention warning
  - High time cost + high parallelism: extended delays warning
  - Low time cost + low memory: critical security risk warning
  - Good balance detection: time ≥ 3, memory ≥ 64MB, parallelism ≤ 8
  - Displays yellow warning banner for compatibility issues

**Dynamic UI Feedback System**:
- Inline warning labels below each parameter input
  - Red warnings for critical errors (blocking save)
  - Pink warnings for security risks
  - Informational messages for performance tips
- Dynamic spacing using `\n` prefix pattern
  - Warnings create vertical space only when shown
  - Zero spacing when no warning present
  - Clean, uncluttered interface when all valid
- General warning label above reset button
  - Yellow text with bold italic styling
  - Explains impact of changing parameters

**Reset to Defaults Functionality**:
- `_reset_crypto_params()`: Resets all parameters to secure defaults
  - Time Cost: 3
  - Memory Cost: 65536 (64 MB)
  - Parallelism: 4
  - Clears all warning messages
  - Shows confirmation notification
- Centered "Reset to Defaults" button with warning variant
- One-click restoration of recommended values

**Real-Time Validation**:
- `on_input_changed()`: Triggers validation on every keystroke
  - Immediate feedback for user input
  - Prevents invalid configurations before save
  - Cross-parameter validation on any change
- Save button respects validation state
  - Settings screen stays open on validation errors
  - Shows error notification for invalid configs
  - Allows user to correct values immediately

**UI/UX Improvements**:
- Reduced spacing between parameter options
- Vertical centering of labels with input fields
- Color-coded warnings (red for errors, yellow for compatibility)
- Responsive layout that adapts to warning presence

### Fixed
- Settings screen now stays open when validation fails (no longer returns to home)
- User can immediately correct invalid parameter values

### Testing

**New Tests** (+41 tests, 1035 total):
- `tests/unit/test_tui_widgets.py`: Added `TestSettingsScreenAdvanced` class (42 tests)
  - **Reset Functionality** (2 tests):
    - `test_reset_crypto_params`
    - `test_reset_crypto_params_exception`
  - **Warning Management** (2 tests):
    - `test_clear_all_warnings`
    - `test_clear_all_warnings_exception`
  - **Time Cost Validation** (6 tests):
    - Valid ranges, weak security, performance warnings, critical errors
  - **Memory Cost Validation** (6 tests):
    - Valid ranges, weak security, high memory warnings, critical errors
  - **Parallelism Validation** (5 tests):
    - Valid ranges, high thread count warnings, diminishing returns
  - **Compatibility Validation** (5 tests):
    - Low memory + high parallelism, high time + high parallelism
    - Low time + low memory (critical), good balance detection
  - **Combined Validation** (1 test):
    - `test_validate_all_crypto_params`
  - **Real-Time Validation** (2 tests):
    - `test_on_input_changed_time_cost/memory_cost`
  - **Enhanced Save Logic** (4 tests):
    - Save with invalid time cost, invalid memory cost
    - Save with invalid parallelism, save with valid params
- **Test Coverage**:
  - `stegvault/tui/widgets.py`: Validation logic 100% covered
  - All tests passing: **1030/1035** ✅ (5 skipped)
  - Pass rate: 100%

### Technical Details

**Validation Architecture**:
- Layered validation approach:
  1. Individual parameter validation (range, security, performance)
  2. Cross-parameter compatibility validation
  3. Combined validation before save
- Return pattern: `True` for valid/warning, `False` for blocking error
- Non-blocking warnings allow save with user awareness
- Blocking errors prevent save until corrected

**Dynamic Spacing Pattern**:
```python
# Warning shown: adds \n prefix for spacing
warning_label.update("\n⚠ Warning message")

# Valid state: empty string, no spacing
warning_label.update("")
```

**CSS Implementation**:
```css
.warning-label {
    margin-top: 0;
    margin-bottom: 0;  /* Zero margin - dynamic spacing via \n */
}

.setting-row {
    align: left middle;  /* Vertical center alignment */
}
```

**Security Recommendations**:
- Default values chosen for optimal security/performance balance
- Warnings guide users toward secure configurations
- Critical errors prevent dangerously weak settings
- Compatibility checks prevent misconfigurations

### Configuration

**TOML Updates**:
```toml
[crypto]
time_cost = 3          # Argon2id iterations
memory_cost = 65536    # Argon2id memory (KB)
parallelism = 4        # Argon2id threads
```

### User Impact
- Expert users can now fine-tune security vs performance
- Clear warnings prevent dangerous misconfigurations
- Default values remain optimal for most use cases
- Real-time feedback improves user experience
- Settings screen behavior improved for better UX

## [0.7.8] - 2025-12-25

### Fixed - Auto-Update System Critical Bugs 🔧

**WinError 32 Fix (File In Use)**:
- `stegvault/utils/updater.py`: Added `is_running_from_installed()` function
  - Detects if StegVault is running from installed package (site-packages) vs development
  - Prevents WinError 32 by warning user before attempting update
  - Returns clear instructions for manual update or detached update mechanism
- `stegvault/utils/updater.py`: Modified `_update_pip()` to check for running instance
  - Returns error message instead of attempting update when running from installation
  - Prevents "file is used by another process" errors on Windows
  - Guides user to use "Update Now" button or manual update command

**Detached Update Mechanism**:
- `stegvault/utils/updater.py`: Added `create_detached_update_script()` function
  - Creates Windows batch script that runs after app closure
  - Waits 3 seconds for app to fully close
  - Performs pip update in separate console window
  - Shows success/failure message to user
  - Auto-deletes script after execution
  - Supports both pip and source installations
- `stegvault/utils/updater.py`: Added `launch_detached_update()` function
  - Launches update script with `subprocess.Popen` in detached mode
  - Uses `CREATE_NEW_CONSOLE` and `DETACHED_PROCESS` flags on Windows
  - Returns clear instructions to user about closing application
  - Handles errors gracefully with user-friendly messages
- Cross-platform support for Windows and Linux/Mac

**Cache Version Mismatch Fix**:
- `stegvault/utils/updater.py`: Added `update_cache_version()` function
  - Fixes issue where cache shows old version (0.7.6) after manual reinstall (0.7.7)
  - Updates `current_version` in cache to match running `__version__`
  - Re-evaluates `update_available` flag based on new version
  - Called on TUI app startup to ensure cache accuracy
- `stegvault/tui/app.py`: Modified `on_mount()` to call `update_cache_version()`
  - Fixes cache on every app start
  - Prevents wrong "Update available" banner after reinstall
  - Silent failure if cache doesn't exist

**TUI Update Interface Improvements**:
- `stegvault/tui/widgets.py`: Modified `SettingsScreen` for dynamic update button
  - Shows "Update Now" button when update is available (replaces "Check Updates")
  - Shows "Check Updates" button normally when no update detected
  - Added `_update_available` and `_latest_version` tracking variables
  - Modified `compose()` to render correct button based on state
  - Modified `on_mount()` to check cached update availability
- `stegvault/tui/widgets.py`: Added `_perform_update_now()` async method
  - Calls `launch_detached_update()` to prepare update script
  - Shows notification with clear instructions to close app
  - Handles success/failure cases with appropriate user feedback
  - 2-second delay to ensure user sees message before closing
- Visual feedback during update process:
  - "Preparing update..." notification when button is clicked
  - Success message with instructions to close StegVault
  - Error message if update script creation fails

**Package Distribution**:
- Created `MANIFEST.in` to include `launch_tui.bat` in distribution
  - Users who install via pip will receive the launcher script
  - Enables easy TUI startup for Windows users
  - Includes README.md, CHANGELOG.md, LICENSE in distribution
- `pyproject.toml`: Added `include-package-data = true` for setuptools
  - Ensures MANIFEST.in is respected during build

### Testing

**New Tests** (+26 tests, 994 total):
- `tests/unit/test_updater.py`: Added `TestDetachedUpdate` class (12 tests)
  - `test_is_running_from_installed_true/false/exception`
  - `test_create_detached_update_script_pip/source/portable/exception`
  - `test_launch_detached_update_success_windows/linux`
  - `test_launch_detached_update_script_creation_failed/portable_fallback/popen_exception`
- `tests/unit/test_updater.py`: Added `TestCacheVersionUpdate` class (5 tests)
  - `test_update_cache_version_mismatch/match/no_cache/exception/no_latest_version`
- `tests/unit/test_tui_widgets.py`: Added SettingsScreen update tests (5 tests)
  - `test_on_mount_detects_update_available`
  - `test_on_button_pressed_update_now`
  - `test_perform_update_now_success/failure/exception`
- `tests/unit/test_tui_app.py`: Added app.on_mount tests (2 tests)
  - `test_on_mount_updates_cache_version`
  - `test_on_mount_cache_update_exception`
- All tests passing: **994/994** ✅ (5 skipped)
- `stegvault/utils/updater.py` coverage: 28% → 41% (+13%)

### Technical Details

**Update Flow (New)**:
1. User opens Settings → sees "Update Now" button (if update available)
2. User clicks "Update Now" → detached script is created
3. User sees message: "Update will begin after you close StegVault"
4. User closes StegVault → update script launches in new console window
5. Script waits 3 seconds → runs `pip install --upgrade stegvault`
6. Success: shows confirmation, waits 5 seconds, auto-closes
7. Failure: shows error, waits for user (press any key to close)
8. Script deletes itself after completion

**Files Modified**:
- `stegvault/utils/updater.py`: 4 new functions, 170 lines added
- `stegvault/tui/widgets.py`: SettingsScreen dynamic button, _perform_update_now()
- `stegvault/tui/app.py`: update_cache_version() call in on_mount()
- `pyproject.toml`: include-package-data configuration
- `MANIFEST.in`: new file for package data inclusion
- `tests/unit/test_updater.py`: 17 new tests
- `tests/unit/test_tui_widgets.py`: 5 new tests
- `tests/unit/test_tui_app.py`: 2 new tests

**Known Limitations**:
- Portable package installation still requires manual update (by design)
- Detached update script is Windows-specific (Linux/Mac use shell script)
- User must close StegVault manually to trigger detached update

## [0.7.7] - 2025-12-25

### Added - TOTP/2FA Protection & UI Enhancements 🔐

**TOTP/2FA Application Lock**:
- `stegvault/config/core.py`: New `TOTPConfig` dataclass for TOTP settings
  - `enabled: bool` - Enable/disable TOTP protection for StegVault access
  - `secret: str` - Base32-encoded TOTP secret for authentication
  - `backup_code: str` - 6-digit emergency backup code for reset
- `stegvault/tui/widgets.py`: `TOTPConfigScreen` modal for TOTP setup
  - QR code generation for authenticator apps (Google Authenticator, Authy, etc.)
  - Automatic backup code generation (6-digit random code)
  - Visual setup wizard with step-by-step instructions
  - Copy-to-clipboard for secret and backup code
- `stegvault/tui/widgets.py`: `TOTPAuthScreen` modal for startup authentication
  - Prompts TOTP code on application launch when enabled
  - Backup code support for emergency access
  - Invalid code rejection with retry mechanism
  - Blocks application access without valid authentication
- Settings screen integration: Toggle TOTP protection on/off
- Persistent TOTP configuration saved to `~/.stegvault/config.toml`

**TUI UI/UX Improvements**:
- **Entry Sorting Controls** (`stegvault/tui/screens.py`):
  - New sort toggle buttons in VaultScreen header
  - Sort by: Name (A-Z) / Date (Newest First)
  - Sort direction: Ascending / Descending
  - Visual indicators with up/down arrows (↑↓)
  - Live sorting updates on entry list
  - State persistence during session
- **Notification System Enhancements** (`stegvault/tui/app.py`):
  - Limited to 3 concurrent notifications (FIFO queue)
  - Prevents notification spam and screen clutter
  - Automatic oldest notification removal
  - Improved notification positioning and styling
- **Scrollbar Improvements**:
  - Stable gutter space reservation (prevents layout shifts)
  - Explicit scrollbar width (1 unit) for consistency
  - Applied to welcome screen, content areas, and modals
  - Better visual consistency across all screens

**Configuration Schema Updates**:
- TOTP settings now part of default config structure
- Backward compatible with existing config files
- Automatic migration to include TOTP section

### Fixed - Type Safety & Code Quality 🔧

**Type Annotations & IDE Compatibility**:
- Fixed 70+ type checking errors across all production modules
- Added comprehensive type hints for better IDE support and static analysis
- Improved mypy and Pylance compatibility with strict type checking

**Gallery Module Fixes** (`stegvault/gallery/`):
- `db.py`: Added return type annotations (`-> None`, `-> int`) for all methods
- `db.py`: Fixed `Optional[Connection]` handling with assertion checks
- `db.py`: Fixed `cursor.lastrowid` Optional[int] handling
- `operations.py`: Fixed VaultMetadata return type handling with None checks
- `operations.py`: Fixed `vault.vault_id` Optional[int] type issues
- `core.py`: Changed `dict` to `Dict[str, Any]` for proper type hints
- `core.py`: Added type hints for `__enter__` and `__exit__` methods
- `search.py`: Added connection assertion for database operations

**Stego Module Fixes** (`stegvault/stego/`):
- `dispatcher.py`: Fixed PIL.Image duck typing with proper type narrowing
- `dispatcher.py`: Added type ignore comments for PIL attributes
- `jpeg_dct.py`: Added jpeglib availability assertions before usage

**Vault Module Fixes** (`stegvault/vault/`):
- `core.py`: Migrated `dict` to `Dict[str, Any]` throughout
- `core.py`: Added `__post_init__() -> None` type hint
- `operations.py`: Fixed Python 3.9 compatibility (`list[T]` → `List[T]`)
- `operations.py`: Added proper type hints for all function parameters
- `totp.py`: Added type ignore comments for untyped qrcode library

**TUI Type Fixes** (`stegvault/tui/`):
- `app.py`: Fixed Union syntax for Python 3.9 (`Vault | None` → `Optional[Vault]`)
- `app.py`: Added return type hints for `__init__` and other methods
- `widgets.py`: Added event type hints (`Click`, etc.)
- `screens.py`: Added proper type annotations for new methods

**Code Quality Improvements**:
- All production modules now pass strict type checking
- Improved Python 3.9+ compatibility
- Better IDE autocomplete and error detection
- Enhanced code maintainability and readability

**Testing**:
- All 970 unit tests passing (100% success rate)
- Maintained 79% overall code coverage
- 16 modules at 100% coverage (gallery, stego, vault, crypto, utils)
- Added tests for TOTP configuration and authentication flows

## [0.7.6] - 2025-12-16

### Added - Auto-Update System 🔄

**Core Update Infrastructure**:
- `stegvault/utils/updater.py` - Complete auto-update module (422 lines)
  - `get_install_method()` - Detects installation type (pip/source/portable)
  - `get_latest_version()` - Queries PyPI API for latest release
  - `compare_versions()` - Semantic version comparison (0.7.5 vs 0.7.6)
  - `check_for_updates()` - Main update check with error handling
  - `fetch_changelog()` - Retrieves changelog from GitHub (raw + API fallback)
  - `parse_changelog_section()` - Extracts version-specific changes
  - `perform_update()` - Executes upgrade based on installation method
  - Cache system prevents API rate limiting (24-hour default, configurable)

**CLI Command**:
- `stegvault update` - Full-featured update management
  - `--check-only` - Check without installing
  - `--force` - Bypass cache, fresh check
  - `-y/--yes` - Auto-confirm update
  - Shows changelog preview (first 30 lines)
  - Installation method auto-detection
  - User confirmation before upgrade
  - Portable package instructions (manual update required)

**TUI Integration**:
- Settings screen with cyberpunk magenta theme
  - Toggle "Auto-check for updates on startup"
  - Toggle "Auto-upgrade" (NOT RECOMMENDED - requires restart)
  - "Force Update Check" button (immediate check)
  - "View Changelog" button (shows current version changes)
- Update notification banner (cyberpunk yellow neon)
  - Shows on startup if update available
  - Respects `config.updates.auto_check` setting
  - Silent background check, non-blocking UI
- Changelog viewer modal (cyan theme)
  - Fetches from GitHub on demand
  - Scrollable content for long changelogs
  - Graceful error handling

**Configuration**:
- `UpdatesConfig` dataclass in `config.toml`
  ```toml
  [updates]
  auto_check = true
  auto_upgrade = false
  check_interval_hours = 24
  last_check = ""
  ```
- Settings persist across sessions
- TUI settings menu for easy configuration

**Update Methods Supported**:
- **pip**: `pip install --upgrade stegvault` (automatic)
- **source**: `git pull && pip install -e . --force-reinstall` (automatic)
- **portable**: Manual instructions provided (download + extract)

**User Experience**:
- ASCII output for Windows compatibility (no Unicode encoding errors)
- Cyberpunk-styled UI elements (⚡, ⚙, ◈ symbols)
- Clear error messages and user feedback
- Non-intrusive notifications in TUI

### Changed

**TUI Home Screen**:
- Settings button now uses `━━━` character (2x3 block) instead of gear emoji
  - Resolved Unicode emoji rendering inconsistencies across terminals
  - Better visibility and centering with guaranteed single-width characters
- Settings button positioned in bottom-right corner (transparent background, hover effects)
- 4 action buttons total: Unlock Vault, New Vault, Help, Settings

**Test Suite**:
- Added 20 comprehensive tests for SettingsScreen and UnsavedChangesScreen
- Fixed 4 pre-existing TUI test failures (AsyncMock, query_one, set_timer mocking)
- Total tests: 778 → **798** (+20 tests)
- Test pass rate: 100% ✅

###Fixed

**Settings Screen UX**:
- Added unsaved changes detection when closing Settings
  - Pressing `q` with unsaved changes → shows "Unsaved Changes" dialog
  - Pressing `Escape`/`Cancel` with unsaved changes → shows "Unsaved Changes" dialog
  - User can choose: "Save & Exit", "Don't Save", or "Cancel" (return to settings)
- Pressing `q` without changes → shows "Quit StegVault?" confirmation (not just close settings)
- Pressing `Escape`/`Cancel` without changes → closes settings directly
- Prevents accidental loss of configuration changes

**Config Tests**:
- Updated all Config dataclass instantiations to include UpdatesConfig parameter
- Fixed 4 failing tests in test_config.py (test_config_creation, test_save_config_valid_data, etc.)

### Technical

**Files Modified**:
- `stegvault/utils/updater.py` (NEW - 422 lines)
- `stegvault/config/core.py` (UpdatesConfig dataclass)
- `stegvault/cli.py` (update command, 157 lines)
- `stegvault/tui/app.py` (banner, startup check, settings action)
- `stegvault/tui/widgets.py` (SettingsScreen, ChangelogViewerScreen)
- `stegvault/__init__.py` (version 0.7.5 → 0.7.6)
- `pyproject.toml` (version 0.7.5 → 0.7.6)
- `tests/unit/test_tui_app.py` (settings button test)

**Dependencies**:
- No new dependencies (uses stdlib urllib, json)

## [0.7.5] - 2025-12-15

### Fixed - TUI User Experience Improvements 🎨

**Dynamic Version Display**:
- Version number now dynamically imported from `stegvault.__version__` instead of hardcoded
- Home screen always shows correct version (e.g., "v0.7.5")
- Eliminates manual update errors in TUI welcome screen
- **Affected File**: `stegvault/tui/app.py` (line 14, 287)

**Password Auto-Hide Security Timer**:
- Passwords in VaultScreen now automatically hide after 10 seconds
- Prevents shoulder surfing attacks in public environments
- Timer properly stopped on entry change or panel clear
- Visual feedback maintained (password visibility toggles as expected)
- **Affected File**: `stegvault/tui/widgets.py` (EntryDetailPanel class)
- **Implementation**: `set_timer(10.0, _auto_hide_password)` callback system

**UnsavedChangesScreen Border Alignment**:
- Fixed 2-character misalignment on title border-right
- Title border now perfectly aligns with dialog borders
- CSS margin adjusted from `0 -1 0 -1` to `0 -2 0 -2`
- **Affected File**: `stegvault/tui/widgets.py` (line 2631)

**PasswordHistoryModal Enhancements**:
- Added "Clear History" button with confirmation dialog
- Removed current password display for enhanced security
- New `GenericConfirmationScreen` modal for flexible confirmations
- Confirmation dialog uses cyberpunk styling (yellow border, centered buttons)
- **Affected Files**:
  - `stegvault/tui/widgets.py` (GenericConfirmationScreen class, lines 1454-1550)
  - `stegvault/tui/widgets.py` (PasswordHistoryModal, lines 1654-1703)

**GenericConfirmationScreen Polish**:
- Fixed excessive whitespace below buttons (dialog now adapts to content)
- Buttons properly centered with `align: center middle`
- Applied consistent cyberpunk styling:
  - "Confirm" button: yellow border (`#ffff00`)
  - "Cancel" button: cyan border (`#00ffff`)
  - Hover effects with semi-transparent backgrounds
- **Affected File**: `stegvault/tui/widgets.py` (lines 1457-1527)

### Changed

**PassphraseInputScreen Enhancement** (from previous session):
- Mode parameter: `"unlock"` (simple entry) vs `"set"` (with validation)
- Eye button for password visibility toggle in "set" mode
- Real-time strength validator using zxcvbn (score 0-4)
- Visual feedback bar with dynamic colors (red → orange → yellow → green → bright green)
- Confirmation field with matching validation
- Minimum "Fair" strength (score ≥ 2) enforced for new passphrases

### Internal

**Bug Tracking**:
- Resolved all implementable bugs from user feedback (thank you, dwrpl)


## [0.7.4] - 2025-12-14

### Added - Favorite Folders Feature ⭐

**TUI Enhancements**:
- `FavoriteFoldersManager` - Complete favorite folder management system
  - Save frequently used vault locations for quick access
  - Quick-access dropdown in FileSelectScreen with keyboard navigation
  - Add/remove/rename favorite folders dynamically
  - Automatic cleanup of non-existent paths on load
  - Cross-platform filesystem root detection (`Path.cwd().anchor` instead of hardcoded `C:\`)

**Persistent Storage**:
- Favorite folders saved to `~/.stegvault/favorite_folders.json`
- Restrictive file permissions (0600) for security on multi-user systems
- Prevents unauthorized users from reading vault path information
- JSON format for easy manual editing if needed

**User Experience**:
- Real-time responsive dropdown overlay in TUI
- Keyboard shortcuts: `f` to favorite current folder, `Ctrl+f` for quick access
- Visual indicators for favorited folders
- Seamless integration with existing FileSelectScreen workflow

### Security - File Permissions Enhancement

**Cross-Platform Security**:
- File permissions set to 0600 (owner read/write only) on favorite_folders.json
- Prevents other users on multi-user systems from reading vault paths
- Automatic permission enforcement on file save operations
- Graceful fallback if chmod not available (e.g., FAT32 filesystems)

**Filesystem Compatibility**:
- Cross-platform root directory handling using `Path.cwd().anchor`
- Works correctly on Windows (C:\, D:\), Linux (/), and macOS (/)
- No more hardcoded drive letter assumptions

### Testing

**Comprehensive Test Suite**:
- 16 new tests for FavoriteFoldersManager (100% pass rate)
- Total tests: 740 → **778** (+38 tests)
- Test coverage: 94% on favorite_folders.py
- Tests cover:
  - Add/remove/rename operations
  - Path normalization and validation
  - Persistence across manager instances
  - Corrupted JSON handling
  - Non-existent path cleanup
  - Cross-platform path handling

**Manual Testing**:
- Windows Terminal: ✅ Verified
- PowerShell: ✅ Verified
- Cross-platform root detection: ✅ Working

### Changed

**TUI FileSelectScreen** (integration point):
- Favorite folders dropdown seamlessly integrated
- No breaking changes to existing workflows
- Enhanced with quick-access functionality

### Security Audit

**Crypto-Security-Auditor Approval**: ✅ LOW RISK
- All MEDIUM priority security findings resolved
- File permissions properly enforced
- No sensitive data logged or exposed
- Cross-platform compatibility verified

## [0.7.3] - 2025-12-12

### Fixed - Critical TUI Stability Improvements 🐛

**PasswordGeneratorScreen Terminal Crash** (Critical):
- **Issue**: Pressing 'q' in PasswordGeneratorScreen caused immediate terminal blackout, requiring force-close
- **Root Cause**: Modal's event handlers were completely bypassed by app's global 'q' binding with `priority=True`
- **Debug Discovery**:
  - Modal's `on_key()` was never called (no notification appeared)
  - Modal's BINDINGS were not registered (footer showed parent screen bindings)
  - Event propagation went directly to app, skipping modal entirely
- **Solution**: App-level interception in `action_quit()`
  ```python
  if isinstance(self.screen, PasswordGeneratorScreen):
      self.notify("Press ESC to close this modal first")
      return  # Block quit, keep modal open
  ```
- **Result**: ✅ Notification appears, modal stays open, no crash
- **Affected File**: `stegvault/tui/app.py` (lines 300-310)

**VaultScreen Button Border Overflow**:
- **Issue**:
  - First row: 2-character border overflow (duplicated ASCII chars at line end)
  - Second row: 1-character overflow (duplicated ASCII char at line end)
  - Buttons slightly off-center to the left
- **Root Cause**: Unicode emoji characters (`➕`, `✏️`, `🗑️`, etc.) causing width miscalculations
  - Terminal width calculation inconsistent with emoji rendering
  - `width: 1fr` with emojis exceeded 100% container width
- **Solution**: Removed all emojis from button labels
  - `➕ ADD` → `ADD`
  - `✏️ EDIT` → `EDIT`
  - `🗑️ DEL` → `DELETE`
  - `📋 COPY` → `COPY`
  - `👁️ SHOW` → `SHOW`
  - `🕐 HIST` → `HISTORY`
  - `💾 SAVE` → `SAVE`
  - `◀◀ BACK` → `BACK`
- **CSS Optimization**:
  - Removed `max-width` constraints that caused centering issues
  - `width: 1fr` now distributes buttons evenly (25% each)
  - Full-width button bar with perfect centering
  - Maintains responsiveness on window resize
- **Result**: ✅ No overflow, perfect centering, responsive layout
- **Affected File**: `stegvault/tui/screens.py` (lines 264-272, 151-174)

### Changed
- VaultScreen action buttons: ASCII labels for terminal rendering stability
- Button layout: Full-width responsive distribution without emoji-related width issues
- PasswordGeneratorScreen: Quit action gracefully handled with user notification

### Technical Details
- **Event Handling**: Discovered Textual ModalScreen doesn't process key events when `priority=True` bindings exist at app level
- **Unicode Rendering**: Terminal emulators calculate emoji width inconsistently, causing layout bugs
- **Workaround**: App-level screen type checking + ASCII-only UI elements for stability

### Testing
- 119 TUI tests (100% pass rate) ✅
- Manual testing: Windows Terminal, PowerShell
- Both issues resolved and verified stable

### Fixed - Code Quality ✅

**Bandit Security Scanner Warnings** (Post-release):
- **Issue**: GitHub Actions "Code Quality" workflow failing due to 6 B110 warnings (try-except-pass)
- **Location**:
  - `stegvault/tui/app.py:309` - `action_quit()` exception handler
  - `stegvault/tui/widgets.py` - PasswordGeneratorScreen key event handlers (5 instances)
- **Solution**: Added `# nosec B110` comments to all intentional try-except-pass blocks
  - All blocks are defensive error handlers to prevent TUI crashes
  - Not security issues, but intentional exception suppression
- **Result**: ✅ Bandit reports "No issues identified" (12 suppressed warnings total)
- **Commit**: `c7f10bd`

## [0.7.2] - 2025-12-03

### Changed - Cyberpunk UI Redesign ⚡

**Visual Overhaul**:
- Complete TUI redesign with cyberpunk/dystopian aesthetic
- Neon color palette: cyan (#00ffff), magenta (#ff00ff), yellow (#ffff00), hot pink (#ff0080)
- Dark background (#0a0a0f, #16213e, #1a1a2e) with neon accents
- Heavy borders with glow effects (text-shadow, box-shadow)
- ASCII art STEGVAULT logo on welcome screen
- Cyberpunk-themed labels and iconography throughout

**Welcome Screen**:
- Large ASCII art "STEGVAULT" logo in magenta
- Title: "⚡ STEGVAULT ⚡ Neural Security Terminal"
- Subtitle: "⚡ Steganography-based password vault in a surveillance state ⚡"
- Tagline: "「 Hide in plain sight. Encrypt everything. Trust no one. 」"
- Redesigned buttons with emoji: 🔓 UNLOCK VAULT, ⚡ NEW VAULT, ❓ HELP

**Vault Screen**:
- Header: "🔒 VAULT: [NAME] 🔒" with cyan neon glow
- Entry list: "▸ CREDENTIALS" with magenta border
- Search input: "⚡ NEURAL SEARCH (/) ..." placeholder
- Action buttons with emoji: ➕ ADD, ✏️ EDIT, 🗑️ DEL, 📋 COPY, 👁️ SHOW, 🕐 HIST, 💾 SAVE, ◀ BACK

**Entry Detail Panel**:
- Title: "▸ ENTRY: [KEY]" with cyan glow and magenta border
- Field labels with emoji:
  - 🔑 PASSWORD (magenta masked bullets ●●●●)
  - 👤 USERNAME
  - 🌐 URL
  - 🏷️ TAGS
  - 📝 NOTES
  - ⏱️ TOTP CODE (🔐 code [Xs])
  - 📅 CREATED
  - 📝 MODIFIED
  - 🕐 PASSWORD HISTORY
- All fields with yellow labels, white values, cyan borders

**Theme Elements**:
- Footer: Magenta key bindings, cyan descriptions
- Hover effects: Background glow with border intensification
- Focus states: Double borders with enhanced glow
- Notifications: Colored borders (cyan=info, pink=error, yellow=warning, green=success)
- Button variants: danger (pink), success (green), warning (yellow)

**Thematic Concept**:
- "Privacy as a luxury in a surveillance state"
- Underground hacker terminal aesthetic
- Neural security terminal narrative
- Steganography as digital camouflage
- Trust no one, encrypt everything philosophy

### Fixed
- NoActiveWorker bug: action_new_vault() and action_open_vault() now use run_worker()
- Button press handlers properly execute async actions in worker context

### Testing
- 761 tests total (100% pass rate)
- 87% overall coverage
- Updated test for new title and subtitle

## [0.7.1] - 2025-12-03

### Added - Password History 🕐

**Core Feature**:
- `PasswordHistoryEntry` dataclass for tracking password changes
- Automatic password history tracking with timestamps and reasons
- `max_history` configuration (default: 5 entries per vault entry)
- Methods: `change_password()`, `get_password_history()`, `clear_password_history()`

**CLI Commands**:
- `vault history <key>` - View complete password history for an entry
  - Supports `--json` output for automation
  - Shows current password, timestamps, and change reasons
  - Passphrase from file or environment variable
- `vault history-clear <key>` - Clear password history for an entry
  - Requires `--output` to save updated vault
  - Confirmation prompt for safety (use `--no-confirm` to skip)
  - Preserves current password and other entry data

**TUI Integration**:
- `PasswordHistoryModal` - Full-screen password history viewer
- Inline history preview (first 3 entries) in detail panel
- Key binding `h` for quick access
- "History (h)" button in action bar
- Color-coded display: passwords (warning), timestamps (muted), reasons (accent)

**Vault Operations**:
- `Vault.update_entry()` automatically tracks password changes
- Optional `password_change_reason` parameter for documenting updates
- History persists through vault save/load cycles
- Backward compatible with existing vaults (empty history by default)

### Changed
- `VaultFormat.V2_1_HISTORY = "2.1"` - New vault format version
- `VaultEntry` now includes `password_history` and `max_history` fields
- Vault group help text updated with new history commands

### Testing
- 761 tests total (+0, all existing tests still pass)
- 21 comprehensive password history tests
- 87% overall coverage
- 100% coverage on vault/core.py ✅

## [0.7.0] - 2025-12-03

### Added - TUI Phase 5: Polish & Completion 🎉

**Help System**:
- `HelpScreen` - Comprehensive keyboard shortcuts reference
- Displays all TUI features and security notes
- Accessible via `h` key or Help button
- Scrollable content with full feature documentation

**Search & Filter**:
- Live search input in entry list (`/` to focus)
- Searches across: key, username, URL, notes, tags
- Real-time filtering as you type
- Entry count shows "X/Y" when filtering
- Auto-clears detail panel when selected entry is filtered

**UI Improvements**:
- Search box with visual placeholder
- Entry count badge in header
- Smooth keyboard focus navigation

**Production Ready**:
- 726 tests total (100% pass rate) ✅
- 89% overall code coverage
- All core TUI features implemented
- Complete keyboard-driven workflow

### Changed
- `action_show_help()` now displays HelpScreen (was placeholder)
- Entry list refresh now respects search filter
- Entry count label shows filtered/total when searching

### Testing
- 726 tests total (+4 from alpha.3)
- 100% pass rate ✅
- 89% coverage (maintained)

## [0.7.0-alpha.3] - 2025-12-03

### Added - TUI Phase 4: Advanced Features 🔐

**Phase 4a - Create New Vault Workflow**:
- 6-step guided workflow for vault creation
- Automatic vault opening after creation
- Complete error handling and cancellation support

**Phase 4b - Password Generator Integration**:
- `PasswordGeneratorScreen` with live preview
- Length control (8-64 characters)
- Integration in EntryFormScreen
- Cryptographically secure generation

**Phase 4c - TOTP Display with Auto-Refresh**:
- Live TOTP codes with countdown timer
- Auto-refresh every second
- Invalid secret error handling

### Fixed
- Bandit B105 false positive for password initialization

### Testing
- 722 tests total (+19 from alpha.2)
- 100% pass rate ✅
- 89% coverage maintained

## [0.7.0-alpha.2] - 2025-12-02

### Added - TUI Phase 3: Entry CRUD Operations ✏️

- **Complete Entry Management**
  - `EntryFormScreen` - Modal form for add/edit
  - `DeleteConfirmationScreen` - Safety confirmation
  - Add, Edit, Delete, Save operations in VaultScreen
  - Form validation (required: key, password)
  - Tag parsing from comma-separated strings

- **Keyboard Shortcuts**
  - **a** - Add new entry
  - **e** - Edit selected entry
  - **d** - Delete entry (with confirmation)
  - **s** - Save vault to disk

- **Enhanced VaultScreen**
  - 7-button action bar
  - Entry list auto-refresh after mutations
  - Detail panel updates after edits
  - Passphrase caching for save operations

### Changed
- `EntryFormScreen.on_button_pressed()` changed to async

### Testing
- 703 tests total (+32 from alpha.1)
- 100% pass rate ✅
- 90% overall coverage

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

[0.4.1]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.4.1
[0.4.0]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.4.0
[0.3.3]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.3.3
[0.3.2]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.3.2
[0.3.1]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.3.1
[0.3.0]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.3.0
[0.2.1]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.2.1
[0.2.0]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.2.0
[0.1.0]: https://github.com/kalashnikxvxiii/stegvault/releases/tag/v0.1.0
