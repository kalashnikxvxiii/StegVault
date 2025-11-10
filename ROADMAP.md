# StegVault Roadmap

This document outlines the planned development roadmap for StegVault.

## Version History

- **v0.1.0** (Current) - Initial Release - CLI MVP

## Version 0.2.0 - Enhanced CLI & Stability (Q4 2025)

### Goals
Improve user experience and fix platform-specific issues

### Features
- [ ] Windows Unicode console support fix
- [ ] Progress indicators for long operations
- [ ] Batch backup creation (multiple passwords)
- [ ] Configuration file support (~/.stegvault/config)
- [ ] Verbose/debug output mode (`--verbose`)
- [ ] Dry-run mode for backup operations
- [ ] Automatic image format conversion (JPEG → PNG)
- [ ] Improved error messages with recovery suggestions

### Technical Improvements
- [ ] Fix Pillow file locking issues on Windows
- [ ] Optimize Argon2id parameters based on platform
- [ ] Add performance benchmarks
- [ ] Improve test coverage to 95%+
- [ ] CI/CD pipeline (GitHub Actions)

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

## Version 0.4.0 - Password Vault Support (Q2 2026)

### Goals
Support multiple password storage in single image

### Features
- [ ] Multi-password vault format
- [ ] Vault encryption with master passphrase
- [ ] Add/remove passwords from existing vault
- [ ] List stored passwords (without revealing them)
- [ ] Export vault to JSON (encrypted)
- [ ] Import from popular password managers (LastPass, 1Password, etc.)

### Data Format
- [ ] Vault binary format specification
- [ ] Metadata support (username, URL, tags)
- [ ] Search and filtering capabilities
- [ ] Password strength indicators

## Version 0.5.0 - GUI Application (Q3 2026)

### Goals
User-friendly graphical interface

### Technology Choices
- **Option 1**: Electron + React (cross-platform, web tech)
- **Option 2**: Qt/PySide6 (native look, better performance)
- **Option 3**: Tauri + React (Rust-based, lightweight)

### Features
- [ ] Visual image selection and preview
- [ ] Drag-and-drop image support
- [ ] Password strength meter
- [ ] Visual capacity indicator
- [ ] Side-by-side image comparison (before/after)
- [ ] Built-in image editor (crop, resize)
- [ ] Dark mode support
- [ ] Internationalization (i18n) framework

### User Experience
- [ ] Onboarding tutorial
- [ ] Context-sensitive help
- [ ] Backup/restore wizard
- [ ] Settings panel
- [ ] Recent files history

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

### Version 1.1.0 - Cloud Integration
- [ ] Optional encrypted cloud backup (AWS S3, Google Drive, Dropbox)
- [ ] Synchronization across devices
- [ ] Conflict resolution
- [ ] End-to-end encryption for cloud storage

### Version 1.2.0 - Mobile Apps
- [ ] iOS application (Swift/SwiftUI)
- [ ] Android application (Kotlin)
- [ ] Mobile-optimized UI
- [ ] Biometric authentication support
- [ ] Camera integration for image selection

### Version 1.3.0 - Advanced Features
- [ ] Multi-image sharding (split password across images)
- [ ] Shamir's Secret Sharing integration
- [ ] Time-locked encryption (future decryption date)
- [ ] Dead man's switch functionality
- [ ] QR code backup alternative

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

## Long-term Vision

StegVault aims to become the standard for steganographic password backup, combining:
- **Military-grade security** with accessible user experience
- **Open-source transparency** with professional development
- **Privacy-first design** with optional convenience features
- **Academic rigor** with practical usability

We envision a future where StegVault is:
1. Trusted by security professionals and individuals alike
2. Audited and verified by independent experts
3. Integrated into broader security ecosystems
4. Used for secure backup of sensitive data beyond passwords

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

**Last Updated**: 2025-11-10
**Status**: Living document, subject to change based on community feedback and security research