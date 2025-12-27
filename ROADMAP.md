# StegVault Roadmap

This document outlines the planned development roadmap for StegVault.

## Version History

- **v0.1.0** - Initial Release - CLI MVP (2025-11-10)
- **v0.2.0** - Enhanced CLI & Stability (2025-11-12)
- **v0.2.1** - Critical Bug Fixes & Simplified Embedding (2025-11-13)
- **v0.3.0** - Configuration & Batch Operations (2025-11-13)
- **v0.3.1** - Test Coverage Improvements (2025-11-13)
- **v0.3.2** - Expanded Test Suite (2025-11-13)
- **v0.3.3** - Version Management Fixes (2025-11-13)
- **v0.4.0** - Complete Password Manager (2025-11-24)
- **v0.4.1** - Vault Search & Filter Commands (2025-11-24)
- **v0.5.0** - Gallery Foundation (2025-11-26)
- **v0.5.1** - JPEG DCT Steganography (2025-11-27)
- **v0.6.0** - Headless Mode (2025-11-28)
- **v0.6.1** - Application Layer (2025-11-28)
- **v0.7.0** - Terminal UI (TUI) (2025-12-03)
- **v0.7.1-v0.7.4** - TUI Improvements & Bug Fixes (2025-12-12 to 2025-12-14)
- **v0.7.5-v0.7.6** - Auto-Update System (2025-12-14 to 2025-12-24)
- **v0.7.7** - TOTP/2FA Protection & UI Enhancements (2025-12-25)
- **v0.7.8** - Auto-Update System Critical Bug Fixes (2025-12-25) ✅ **CURRENT**

## Completed Milestones

### v0.1.0 - v0.3.3 ✅
- [x] Core CLI with backup/restore/check commands
- [x] XChaCha20-Poly1305 + Argon2id cryptography
- [x] PNG LSB steganography (sequential embedding)
- [x] Progress indicators for long operations
- [x] Batch operations (JSON-based workflows)
- [x] Configuration file support (TOML)
- [x] Fix Pillow file locking issues on Windows
- [x] Comprehensive test suite (145 tests, 87% coverage → 220 tests, 85% coverage in v0.4.0)
- [x] PyPI publication and CI/CD pipeline
- [x] Performance optimization (sequential embedding)

### v0.4.0 ✅ (Released 2025-11-24)
- [x] Vault import command for backup/restore workflows
- [x] Clipboard integration with auto-clear functionality
- [x] TOTP/2FA authenticator support with QR codes and manual entry
- [x] Realistic password strength validation using zxcvbn
- [x] Critical bug fixes for all vault CLI commands
- [x] Test suite expansion (194 → 275 tests, 80% coverage)
- [x] New vault.totp module (100% coverage)
- [x] Password strength meter with detailed feedback

### v0.4.1 ✅ (Released 2025-11-24)
- [x] `vault search` command - search vault entries by query
- [x] `vault filter` command - filter entries by tags/URL
- [x] 24 new tests for search/filter functionality
- [x] Total: 299 tests passing

### v0.5.0 ✅ (Released 2025-11-26)
- [x] Gallery Foundation - multi-vault management system
- [x] Gallery database (SQLite) with metadata and entry caching
- [x] 6 new CLI commands: init, add, list, remove, refresh, search
- [x] Cross-vault search functionality
- [x] 22 comprehensive gallery tests (100% pass rate)
- [x] Total: 346 tests, 78% coverage

### v0.5.1 ✅ (Released 2025-11-27)
- [x] JPEG DCT Steganography implementation
- [x] jpeglib library integration
- [x] Image format auto-detection (magic bytes)
- [x] Dispatcher for PNG/JPEG routing
- [x] CLI integration with both formats
- [x] Comprehensive CLI tests
- [x] Documentation updates

### v0.6.0 ✅ (Released 2025-11-28)
- [x] Headless Mode - JSON output for automation
- [x] `--json` flag for check, vault get, vault list
- [x] `--passphrase-file` support
- [x] `STEGVAULT_PASSPHRASE` environment variable
- [x] Standardized exit codes (0=success, 1=error, 2=validation)
- [x] 20 comprehensive headless mode tests
- [x] Total: 585 tests, 92% coverage

### v0.6.1 ✅ (Released 2025-11-28)
- [x] Application Layer - shared business logic
- [x] CryptoController for encryption operations
- [x] VaultController for vault CRUD operations
- [x] UI-agnostic controller architecture
- [x] 29 controller tests
- [x] Total: 614 tests

### v0.7.0 ✅ (Released 2025-12-03)
- [x] Terminal UI (TUI) with Textual framework
- [x] Full-featured visual interface with keyboard shortcuts
- [x] Entry list with split view (30%/70%)
- [x] Add/Edit/Delete dialogs
- [x] Password generator integration
- [x] TOTP display with auto-refresh
- [x] Search/filter with live results
- [x] Help screen with comprehensive shortcuts
- [x] Create new vault workflow
- [x] Total: 740 tests, 89% coverage

### v0.7.1-v0.7.4 ✅ (Released 2025-12-12 to 2025-12-14)
- [x] Critical TUI bug fixes (PasswordGeneratorScreen crash)
- [x] Button border overflow fixes
- [x] Bandit B110 warnings suppression
- [x] Favorite Folders feature for quick vault access
- [x] Security audit approved (LOW RISK rating)
- [x] Total: 778 tests

### v0.7.5-v0.7.6 ✅ (Released 2025-12-14 to 2025-12-24)
- [x] Auto-update system with Settings screen
- [x] Check for updates from PyPI
- [x] Auto-upgrade toggle
- [x] Changelog preview
- [x] Settings screen integration

### v0.7.7 ✅ (Released 2025-12-25)
- [x] TOTP/2FA Application Lock with QR codes
- [x] Entry sorting controls (A-Z, Date)
- [x] Notification system enhancements (3 max FIFO)
- [x] Scrollbar improvements
- [x] 70+ type checking error fixes
- [x] Total: 970 tests, 79% coverage

### v0.7.8 ✅ (Released 2025-12-25) **CURRENT**
- [x] Auto-update system critical bug fixes
- [x] WinError 32 fix (file in use)
- [x] Detached update mechanism
- [x] Cache version mismatch fix
- [x] Dynamic "Update Now" button in Settings
- [x] MANIFEST.in for package distribution
- [x] 26 new tests
- [x] Total: 994 tests, 79% coverage
- [x] updater.py coverage: 28% → 91% (+63%)

## Version 0.8.0 - Desktop GUI (Q1 2026)

### Goals
Native desktop application with visual vault management

### Technology Choice
**PySide6 (Qt for Python)** - Selected for:
- Native performance (~20MB vs 100MB+ Electron)
- 100% Python integration
- LGPL license (commercial-friendly)
- Cross-platform (Windows/macOS/Linux)
- pytest-qt testing framework
- Qt Designer for rapid UI development

### Features
- [ ] Native desktop application with Qt/PySide6
- [ ] Visual vault entry editor
- [ ] Password strength meter and generator UI
- [ ] Search across all vaults
- [ ] Tag-based organization
- [ ] Dark mode support
- [ ] Settings dialog
- [ ] Keyboard shortcuts
- [ ] Drag-and-drop image support

### Testing
- [ ] 170+ GUI tests with pytest-qt
- [ ] 85%+ coverage target

## Version 0.4.0 - Vault Mode & Dual-Mode Architecture ✅ (Released 2025-11-24)

### Goals
Transform StegVault into flexible password manager with dual-mode operation

### Core Philosophy: User Choice
**Two modes, one tool:**
1. **Single Password Mode** (existing): Quick backup of one password per image
2. **Vault Mode** (new): Multiple passwords organized in one image

Users choose which mode fits their needs. Both use same crypto stack.

### Features - Vault Mode ✅
- [x] JSON-based vault structure with multiple entries
- [x] `stegvault vault create` - Initialize new vault in image
- [x] `stegvault vault add <key>` - Add password entry to vault
- [x] `stegvault vault get <key>` - Retrieve specific password by key (with --clipboard support)
- [x] `stegvault vault list` - Show all keys (no passwords)
- [x] `stegvault vault update <key>` - Modify existing entry
- [x] `stegvault vault delete <key>` - Remove entry
- [x] `stegvault vault show <key>` - Display entry details (except password)
- [x] `stegvault vault totp <key>` - Generate TOTP/2FA codes
- [x] Auto-detection of format (single vs vault) on restore
- [x] `stegvault vault export` - Export vault to JSON
- [x] `stegvault vault import` - Import vault from JSON backup

### Features - Utilities ✅
- [x] Integrated password generator (`--generate` flag)
- [x] Password strength validation and entropy calculation
- [x] Entry metadata (username, URL, tags, timestamps)
- [x] Export vault to JSON (encrypted/plaintext options)
- [x] Import vault from JSON (complete backup/restore workflow)
- [x] Memorable passphrase generation
- [x] Clipboard integration with auto-clear timeout
- [x] TOTP/2FA authenticator with QR code generation

### Backward Compatibility ✅
- [x] Existing `backup`/`restore` commands unchanged
- [x] Auto-detect format during restore operation
- [ ] Migration tool: single password → vault format (planned for future release)

### Testing & Quality ✅
- [x] 49 comprehensive unit tests for vault module
- [x] 38 comprehensive CLI tests for vault commands (import, clipboard, TOTP)
- [x] 19 comprehensive TOTP tests (100% coverage)
- [x] Critical bug fixes: all vault commands fully functional
- [x] Coverage: 93% vault module, 79% CLI, 81% overall
- [x] Total test count: 251 tests (all passing)

### Data Format
```json
{
  "version": "2.0",
  "entries": [
    {
      "key": "gmail",
      "username": "user@example.com",
      "password": "encrypted_password",
      "url": "https://gmail.com",
      "notes": "Personal email",
      "tags": ["email", "personal"],
      "created": "2025-01-14T12:00:00Z",
      "modified": "2025-01-14T12:00:00Z"
    }
  ]
}
```

## Version 0.9.0 - Advanced Features (Q2 2026)

### Goals
Advanced security features and quality of life improvements

### Features
- [ ] Saved paths feature (TUI/GUI) - recently opened vaults
- [ ] Auto-save configuration with visual indicators
- [ ] Export formats (CSV, KeePass XML, 1Password 1PIF)
- [ ] Advanced search with regex support
- [ ] Vault templates (Social Media, Banking, etc.)
- [ ] Session timeout with auto-lock
- [ ] Passphrase strength requirements

## Version 1.0.0 - Production Ready (Q3 2026)

### Goals
Visual gallery interface - the complete StegVault experience

### Technology Choices
- **Option 1**: Electron + React (cross-platform, web tech)
- **Option 2**: Qt/PySide6 (native look, better performance)
- **Option 3**: Tauri + React (Rust-based, lightweight)

### Features - Gallery View
- [ ] **Photo gallery interface** - thumbnails of all vault files
- [ ] Visual indicators: 🔐 badge showing number of passwords per file
- [ ] Drag-and-drop support for adding new vault files
- [ ] Double-click to unlock and view vault contents
- [ ] Image preview with vault statistics
- [ ] Grid/list view toggle
- [ ] Sort and filter (by date, size, password count)

### Features - Vault Management
- [ ] Visual password entry editor
- [ ] Password strength meter and generator
- [ ] Search across all vaults in gallery
- [ ] Tag-based organization
- [ ] Bulk operations (export, backup, verify)

### Features - User Experience
- [ ] Onboarding tutorial explaining gallery concept
- [ ] Dark mode support
- [ ] Context-sensitive help
- [ ] Settings panel with gallery preferences
- [ ] Recent vaults history
- [ ] Visual capacity indicators
- [ ] Side-by-side comparison (before/after embedding)

## Version 1.0.0 - Production Ready (Q4 2026)

### Goals
Stable, secure, production-ready release

### Requirements
- [ ] Complete security audit by external firm
- [ ] Penetration testing
- [ ] Code review by cryptography experts
- [ ] Performance optimization
- [ ] Comprehensive documentation
- [ ] User manual and video tutorials
- [ ] Cross-platform testing (Windows, macOS, Linux, iOS, Android)

### Distribution
- [ ] PyPI package publication
- [ ] Homebrew formula (macOS)
- [ ] Chocolatey package (Windows)
- [ ] Snap package (Linux)
- [ ] DMG installer (macOS)
- [ ] MSI installer (Windows)
- [ ] AppImage (Linux)

## Future Versions (Post 1.0)

### Version 1.1.0 - Multimedia Steganography
**Expanding beyond images - the complete multimedia gallery**

#### JPEG Support
- [ ] JPEG DCT-based steganography
- [ ] F5/nsF5 algorithm implementation
- [ ] Resistance to recompression
- [ ] Quality-preserving embedding

#### Video Steganography
- [ ] MP4/AVI support
- [ ] Frame-based embedding
- [ ] Motion vector manipulation
- [ ] Huge capacity (MBs of data per video)

#### Audio Steganography
- [ ] MP3/WAV/FLAC support
- [ ] LSB audio embedding
- [ ] Phase coding techniques
- [ ] Echo hiding

#### Format Auto-Detection
- [ ] Automatic format detection
- [ ] Best format recommendation based on file type
- [ ] Capacity optimization per format

### Version 1.2.0 - Cloud Integration (Optional Plugin)
**Privacy-first cloud sync as optional plugin**
- [ ] Plugin architecture for cloud providers
- [ ] AWS S3 plugin
- [ ] Google Drive plugin
- [ ] Dropbox plugin
- [ ] Self-hosted backend plugin
- [ ] End-to-end encryption (client-side only)
- [ ] Selective sync (choose which vaults to sync)
- [ ] Conflict resolution
- [ ] Zero-knowledge architecture: server never sees passphrases

### Version 1.3.0 - Mobile Apps
- [ ] iOS application (Swift/SwiftUI)
- [ ] Android application (Kotlin)
- [ ] Mobile gallery interface
- [ ] Biometric authentication support
- [ ] Camera integration for vault creation (take photo → embed vault)
- [ ] Mobile-optimized vault management

### Version 1.4.0 - Advanced Features
- [ ] Multi-image sharding (split vault across multiple images)
- [ ] Shamir's Secret Sharing integration
- [ ] Time-locked encryption (future decryption date)
- [ ] Dead man's switch functionality
- [ ] QR code backup alternative
- [ ] Duress password (reveals decoy vault under coercion)

### Version 2.0.0 - Next Generation
- [ ] Hardware security module (HSM) support
- [ ] Post-quantum cryptography (CRYSTALS-Kyber/Dilithium)
- [ ] Blockchain-based timestamp proofs
- [ ] Decentralized identity integration
- [ ] Zero-knowledge proof authentication

## Research & Experimentation

### Ongoing Research Topics
- Audio steganography (WAV, FLAC)
- Video steganography (MP4, AVI)
- Network steganography (covert channels)
- Steganography in AI-generated images
- Plausible deniability techniques

### Security Research
- Quantum-resistant algorithms
- Side-channel attack resistance
- Memory-hard function optimization
- Constant-time implementations
- Formal verification of cryptographic primitives

## Community & Ecosystem

### Documentation
- [ ] API documentation (Sphinx)
- [ ] Developer guide
- [ ] Security best practices guide
- [ ] FAQ and troubleshooting
- [ ] Video tutorials
- [ ] Blog posts on cryptography and steganography

### Community Building
- [ ] Discord/Slack community
- [ ] Bug bounty program
- [ ] Regular security audits
- [ ] Academic paper publication

### Integrations
- [ ] Browser extensions (Chrome, Firefox)
- [ ] Password manager plugins
- [ ] CLI tool integrations (pass, gopass)
- [ ] API for third-party applications

## Long-term Vision: The Secret Gallery

### What is StegVault?
**StegVault transforms your multimedia collection into a secure, distributed password vault.**

Your photos, videos, and music files appear completely normal to anyone who sees them. But to you, they're a sophisticated security system where each file can hide encrypted credentials, documents, or sensitive data.

### Core Principles
1. **Plausible Deniability**: Your vault looks like an ordinary media gallery
2. **Distributed Security**: Risk spread across multiple files, not one master database
3. **Privacy-First**: Everything encrypted locally, cloud is optional plugin
4. **User Choice**: Use as simple backup tool OR full password manager
5. **Trust Through Transparency**: Open source, audited, verifiable

### The Complete Vision
```
User's Experience:
  📱 Phone Gallery          🖥️ Desktop Gallery        ☁️ Cloud Photos
  ├── vacation.jpg         ├── vacation.jpg          ├── vacation.jpg
  ├── family.png      ←→   ├── family.png       ←→   ├── family.png
  └── video.mp4            └── video.mp4             └── video.mp4

  What Others See: "Normal photos and videos"
  What You Know: "Each file = encrypted vault with credentials"

  Access Anywhere:
  - Desktop: Full GUI gallery with management
  - Mobile: Camera → instant vault creation
  - CLI: Power user scripting and automation
```

### Why StegVault Will Succeed
1. **Unique Approach**: No other password manager uses multimedia steganography
2. **Natural Backups**: People already backup photos (Google Photos, iCloud, etc.)
3. **Low Suspicion**: Encrypted databases attract attention, vacation photos don't
4. **Flexible Security**: Choose your own tradeoff (convenience vs paranoia)
5. **Future-Proof**: Supports image, video, audio - multi-format resilience

### Target Users
- **Privacy Advocates**: Want maximum security without cloud dependence
- **Security Professionals**: Need plausible deniability and distributed storage
- **Regular Users**: Want simple password backup without complexity
- **Journalists/Activists**: Need to hide sensitive data in plain sight
- **Travelers**: Can't rely on cloud access, need offline vault

### Success Metrics (v1.0)
- ✅ Trusted by security community
- ✅ External security audit passed
- ✅ 10,000+ active users
- ✅ Zero critical vulnerabilities
- ✅ Used in academic security research
- ✅ Integration with major password managers (import/export)

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for how you can help shape this roadmap.

Priority areas for community contribution:
- Testing on various platforms and configurations
- Security research and vulnerability disclosure
- Documentation improvements
- Feature requests and use case feedback
- Code contributions following our guidelines

## Versioning Strategy

StegVault follows [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0): Breaking changes to file format or API
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes, no new features

## Support & Maintenance

- **v0.x**: Active development, breaking changes possible
- **v1.x**: LTS (Long-Term Support), 2 years of security updates
- **v2.x+**: Future major versions

---

**Last Updated**: 2025-12-25
**Status**: Living document, subject to change based on community feedback and security research

## Quick Reference: Current Status (v0.7.8)

**CURRENT VERSION (v0.7.8):**
- ✅ 994 tests passing (79% coverage)
- ✅ Auto-update system with bug fixes (WinError 32, cache sync)
- ✅ Terminal UI (TUI) with full vault management
- ✅ TOTP/2FA application lock
- ✅ Gallery Foundation with cross-vault search
- ✅ JPEG DCT + PNG LSB steganography
- ✅ Headless mode for automation
- ✅ Application layer architecture

**RECENTLY COMPLETED (v0.7.0-v0.7.8):**
1. ✅ Full-featured Terminal UI with Textual
2. ✅ Auto-update system with Settings integration
3. ✅ TOTP/2FA application lock for enhanced security
4. ✅ Critical auto-update bug fixes (WinError 32, cache sync)
5. ✅ Dynamic "Update Now" button
6. ✅ Favorite folders for quick vault access

**NEXT UP (v0.8.0 / Desktop GUI):**
- Native desktop application with PySide6
- Visual vault management interface
- Password generator UI
- Settings dialog
- Dark mode support

**THE VISION:**
Privacy-first password manager using steganography. Hide encrypted vaults in ordinary images. Three interfaces (CLI, TUI, GUI) for all use cases. Zero-knowledge, local-first, open source.