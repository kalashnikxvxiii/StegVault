# StegVault Wiki

Welcome to the StegVault documentation wiki!

## What is StegVault?

StegVault is a secure password manager that uses steganography to hide encrypted passwords within ordinary images. It combines modern cryptography (XChaCha20-Poly1305 + Argon2id) with dual steganography (PNG LSB + JPEG DCT) to create a portable, zero-knowledge backup system.

## Quick Links

### Getting Started
- [Installation Guide](Installation-Guide.md)
- [Quick Start Tutorial](Quick-Start-Tutorial.md)
- [Basic Usage Examples](Basic-Usage-Examples.md)

### User Guides
- [CLI Commands Reference](CLI-Commands-Reference.md) - Complete command reference ✨ NEW
- [TUI User Guide](TUI_USER_GUIDE.md) - Terminal UI keyboard shortcuts
- [Headless Mode Guide](Headless-Mode-Guide.md) - Automation & CI/CD ✨ NEW
- [Creating Backups](Creating-Backups.md)
- [Restoring Passwords](Restoring-Passwords.md)
- [Choosing Cover Images](Choosing-Cover-Images.md)
- [Security Best Practices](Security-Best-Practices.md)

### Technical Documentation
- [Architecture Overview](Architecture-Overview.md)
- [Cryptography Details](Cryptography-Details.md)
- [Steganography Techniques](Steganography-Techniques.md)
- [Payload Format Specification](Payload-Format-Specification.md)

### Development
- [Developer Guide](Developer-Guide.md)
- [API Reference](API-Reference.md)
- [Testing Guide](Testing-Guide.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

### Security
- [Security Model](Security-Model.md)
- [Threat Model](Threat-Model.md)
- [Known Limitations](Known-Limitations.md)
- [Vulnerability Disclosure](Vulnerability-Disclosure.md)

### FAQ & Troubleshooting
- [Frequently Asked Questions](FAQ.md)
- [Troubleshooting Guide](Troubleshooting.md)
- [Common Errors](Common-Errors.md)

## Project Status

- **Version**: 0.7.10 (Critical Bug Fixes & Test Quality)
- **Status**: Stable - Production-ready
- **License**: MIT
- **Language**: Python 3.9+
- **Tests**: 1078 passing (81% coverage)

## Key Features

- ✅ XChaCha20-Poly1305 AEAD encryption
- ✅ Argon2id key derivation (configurable parameters)
- ✅ Advanced Settings with real-time validation (v0.7.9)
- ✅ Argon2id parameter tuning (time cost, memory cost, parallelism)
- ✅ Smart warnings (security, performance, compatibility)
- ✅ Dual steganography (PNG LSB + JPEG DCT)
- ✅ Full vault mode with CRUD operations
- ✅ Password history tracking (v0.7.1)
- ✅ TOTP/2FA application lock (v0.7.7)
- ✅ Auto-update system with critical bug fixes (v0.7.6+)
- ✅ Detached update mechanism (fixes WinError 32)
- ✅ Dynamic "Update Now" button in Settings
- ✅ TOTP/2FA authenticator
- ✅ Gallery multi-vault management
- ✅ Terminal UI (TUI) with full keyboard navigation
- ✅ Headless mode (JSON output, automation)
- ✅ Application layer (UI-agnostic controllers)
- ✅ CLI interface
- ✅ 1078 unit tests with 81% coverage
- ✅ Zero-knowledge architecture

## Coming Soon

See [ROADMAP.md](../ROADMAP.md) for planned features.

## Need Help?

- 💬 [Discussions](https://github.com/kalashnikxvxiii/stegvault/discussions)
- 🐛 [Issue Tracker](https://github.com/kalashnikxvxiii/stegvault/issues)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.