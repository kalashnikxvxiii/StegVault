# StegVault Roadmap

This document outlines the planned development roadmap for StegVault.

## Version History

- **v0.1.0** - Initial Release - CLI MVP (2025-11-10)
- **v0.2.0** - Enhanced CLI & Stability (2025-11-12)
- **v0.2.1** - Critical Bug Fixes & Simplified Embedding (2025-11-13)
- **v0.3.0** - Configuration & Batch Operations (2025-11-13)
- **v0.3.1** - Test Coverage Improvements (2025-11-13)
- **v0.3.2** - Expanded Test Suite (2025-11-13)
- **v0.3.3** - Version Management Fixes (2025-11-13) ✅ **CURRENT**
- **v0.4.0** - Vault Mode & Password Manager (In Progress)

## Completed Milestones

### v0.1.0 - v0.3.3 ✅
- [x] Core CLI with backup/restore/check commands
- [x] XChaCha20-Poly1305 + Argon2id cryptography
- [x] PNG LSB steganography (sequential embedding)
- [x] Progress indicators for long operations
- [x] Batch operations (JSON-based workflows)
- [x] Configuration file support (TOML)
- [x] Fix Pillow file locking issues on Windows
- [x] Comprehensive test suite (145 tests, 87% coverage)
- [x] PyPI publication and CI/CD pipeline
- [x] Performance optimization (sequential embedding)

## Version 0.3.0 - Advanced Steganography (Q1 2026)

### Goals
Add JPEG support and improve detection resistance

### Features
- [ ] JPEG DCT steganography implementation
- [ ] Automatic format selection based on image type
- [ ] Image quality preservation for JPEG
- [ ] Advanced embedding patterns (multiple algorithms)
- [ ] Capacity estimation improvements
- [ ] Support for BMP and TIFF formats

### Security Enhancements
- [ ] Randomized payload padding
- [ ] Optional cover image preprocessing
- [ ] Payload compression (zlib/lz4)
- [ ] Multiple embedding strategies (user selectable)

### Research
- [ ] Benchmark detection resistance vs various steganalysis tools
- [ ] Evaluate F5, nsF5, and other advanced algorithms
- [ ] Study optimal Argon2 parameters for mobile devices

## Version 0.4.0 - Vault Mode & Dual-Mode Architecture (In Progress - Q4 2025)

### Goals
Transform StegVault into flexible password manager with dual-mode operation

### Core Philosophy: User Choice
**Two modes, one tool:**
1. **Single Password Mode** (existing): Quick backup of one password per image
2. **Vault Mode** (new): Multiple passwords organized in one image

Users choose which mode fits their needs. Both use same crypto stack.

### Features - Vault Mode
- [ ] JSON-based vault structure with multiple entries
- [ ] `stegvault vault create` - Initialize new vault in image
- [ ] `stegvault vault add <key>` - Add password entry to vault
- [ ] `stegvault vault get <key>` - Retrieve specific password by key
- [ ] `stegvault vault list` - Show all keys (no passwords)
- [ ] `stegvault vault update <key>` - Modify existing entry
- [ ] `stegvault vault delete <key>` - Remove entry
- [ ] `stegvault vault show <key>` - Display entry details (except password)
- [ ] Auto-detection of format (single vs vault) on restore

### Features - Utilities
- [ ] Integrated password generator (`--generate` flag)
- [ ] Password strength validation
- [ ] Entry metadata (username, URL, tags, timestamps)
- [ ] Export vault to JSON (encrypted/plaintext options)

### Backward Compatibility
- [ ] Existing `backup`/`restore` commands unchanged
- [ ] Auto-detect format during restore operation
- [ ] Migration tool: single password → vault format

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

## Version 0.5.0 - Gallery Foundation (Q1 2026)

### Goals
Enable multi-file vault management - the foundation of the Gallery Vision

### The Gallery Vision 🖼️
**StegVault is not just a password manager - it's a secret multimedia gallery.**

Your photo gallery appears normal, but each file is a secure vault:
```
📁 My_Photos/
  🖼️ vacation_2024.jpg    → 🔐 Social media credentials
  🖼️ family_portrait.png  → 🔐 Banking & finance
  🖼️ sunset_beach.jpg     → 🔐 Work accounts
  🎬 birthday_party.mp4   → 🔐 Personal documents
  🎵 favorite_song.mp3    → 🔐 Backup keys
```

**Benefits:**
- 🎭 Plausible deniability: "Just vacation photos"
- 🛡️ Risk distribution: One compromised file ≠ total loss
- 🎨 Natural camouflage: Hidden in plain sight
- 💾 Natural backup: Photos backup automatically
- 🔄 Flexible organization: Organize by category/service/importance

### Features - Gallery Management
- [ ] Gallery initialization: `stegvault gallery init ./photos`
- [ ] Gallery-wide operations: `stegvault gallery list`
- [ ] Cross-vault search: `stegvault gallery search "gmail"`
- [ ] Smart retrieval: `stegvault gallery get gmail` (auto-finds correct file)
- [ ] Gallery metadata tracking (.stegvault/gallery.db)
- [ ] Integrity checking across all vault files
- [ ] Gallery backup: `stegvault gallery backup ./backup`

### Features - Multi-File Support
- [ ] Index multiple vault-embedded images
- [ ] Quick lookup: key → file mapping
- [ ] Status dashboard: X files, Y passwords, Z total capacity
- [ ] Health monitoring: detect corrupted/missing vaults

## Version 0.6.0 - GUI Gallery Application (Q2 2026)

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

**Last Updated**: 2025-01-14
**Status**: Living document, subject to change based on community feedback and security research

## Quick Reference: Current Focus (v0.4.0)

**NOW IMPLEMENTING:**
1. ✅ Vault mode - multiple passwords in single image
2. ✅ Dual-mode architecture (single password OR vault)
3. ✅ New CLI commands: `vault create/add/get/list/update/delete`
4. ✅ Password generator utility
5. ✅ Auto-detection of format on restore

**NEXT UP (v0.5.0):**
- Gallery foundation - multi-file vault management
- Cross-vault search capabilities
- Gallery metadata tracking

**THE VISION:**
Transform StegVault into a multimedia gallery where each photo/video/audio file can secretly store encrypted vaults. Privacy-first, distributed security, plausible deniability.