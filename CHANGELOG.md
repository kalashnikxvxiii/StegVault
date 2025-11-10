# Changelog

All notable changes to StegVault will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-10

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
