# Known Limitations

Known limitations and constraints of StegVault.

## Cryptographic Limitations

### Not Post-Quantum Secure

**Limitation**: XChaCha20-Poly1305 vulnerable to quantum computers

**Impact**: Future quantum computers could decrypt archived backups

**Workaround**: None currently

**Future Plans**: Migrate to post-quantum ciphers (e.g., NIST PQC winners)

**Timeline**: When practical quantum computers emerge (10-30 years)

---

### Argon2id Parameter Trade-offs

**Limitation**: Current parameters balance security vs. usability

**Current Settings**:
- Memory: 64 MB
- Time cost: 3 iterations
- ~100ms per derivation on modern CPU

**Impact**:
- Too low: Vulnerable to GPU attacks
- Too high: Slow on low-end devices

**Workaround**: Parameters may be configurable in future versions

---

## Steganography Limitations

### LSB Embedding is Detectable

**Limitation**: Statistical analysis can detect LSB steganography

**Impact**: Experts can identify backup images contain hidden data

**Reality Check**: Steganography is NOT the security layer

**Mitigation**: Encryption protects password even if detected

**Detection Tools**:
- Chi-square analysis
- RS steganalysis
- Visual LSB plane inspection

---

### JPEG Unreliability

**Limitation**: JPEG compression can destroy embedded data

**Causes**:
- Lossy compression modifies pixel values
- Resaving changes LSBs
- Quality settings affect reliability

**Impact**: Backups may become unrecoverable

**Workaround**: Always use PNG format

**Status**: JPEG support marked experimental

---

### Image Format Support

**Supported**:
- PNG (recommended)
- JPEG (with warnings)

**Not Supported**:
- GIF (limited color palette)
- BMP (rare format)
- TIFF (complex format)
- WebP (lossy by default)
- HEIC/HEIF (patent concerns)

**Workaround**: Convert to PNG before backup

---

## Capacity Limitations

### Maximum Password Length

**Theoretical Limit**: 4 GB (ciphertext length field is 32-bit)

**Practical Limits**:

| Image Size | Max Password Length |
|------------|---------------------|
| 800×600 | ~180,000 chars |
| 1920×1080 | ~777,000 chars |
| 3840×2160 | ~3,110,000 chars |

**Impact**: None for typical use (passwords <1000 chars)

---

### Minimum Image Size

**Requirement**: Image must hold payload + overhead (64 bytes)

**Minimum Dimensions**:
- For 8-char password: ~200×200 pixels
- Recommended: 800×600 or larger

**Impact**: Cannot use very small images

---

## Usability Limitations

### Passphrase Recovery Impossible

**Limitation**: No "forgot passphrase" recovery mechanism

**Impact**: Lost passphrase = permanently lost password

**Design Choice**: Zero-knowledge by design

**Workaround**: None (fundamental design decision)

**Mitigation**: Users must protect passphrases carefully

---

### No Multi-User Support

**Limitation**: Cannot create backups with multiple passphrases

**Impact**: Cannot share backup with team (without sharing passphrase)

**Workaround**: Create separate backups for each user

**Future**: Secret-sharing schemes (Shamir) may be added

---

### No Desktop GUI Yet (v0.7.3)

**Limitation**: No graphical desktop application yet

**Impact**: May be less accessible to some non-technical users

**Current Interfaces** (v0.7.3):
- ✅ **CLI**: Full-featured command-line interface
- ✅ **TUI**: Terminal UI with full keyboard navigation (v0.7.0+)
  - Live TOTP codes with auto-refresh
  - Password generator with live preview
  - Full CRUD operations
  - Search/filter functionality
  - Password history tracking
- ✅ **Headless**: JSON output for automation (v0.6.0+)
- ✅ **Application Layer**: Ready for GUI integration (v0.6.1+)

**Workaround**: TUI provides full interactive experience in terminal

**Status**: TUI is stable and production-ready (v0.7.3 bug fixes)

**Future**: Desktop GUI (PySide6) planned for v0.8.0

---

## Platform Limitations

### Memory Requirements

**Requirement**: ~100 MB RAM for typical operation

**Impact**: May not run on extremely constrained devices

**Breakdown**:
- Argon2id memory: 64 MB
- Image loading: 10-50 MB (depends on size)
- Python overhead: 20-30 MB

---

### Performance on Low-End Devices

**Limitation**: Argon2id is intentionally slow

**Impact**: Backup/restore takes longer on slow CPUs

**Examples**:
- Modern desktop: ~100ms
- Raspberry Pi 3: ~500ms
- Very old hardware: ~2-5 seconds

**Workaround**: None (security vs. performance trade-off)

---

## Security Limitations

### No Protection Against Keyloggers

**Limitation**: Malware can capture passphrase during entry

**Impact**: Compromised system = compromised passphrase

**Scope**: Out of scope for StegVault

**Mitigation**: User must maintain system security

---

### No Memory Wiping

**Limitation**: Plaintext password may linger in RAM

**Impact**: Memory dump after recovery may reveal password

**Status**: Not yet implemented

**Future**: Explicit memory clearing planned

---

### No Secure Input Method

**Limitation**: Passphrase visible in process memory

**Impact**: Privileged attacker can read passphrase from RAM

**Mitigation**: Limited (OS-level protection needed)

---

## Operational Limitations

### No Cloud Sync

**Limitation**: No built-in cloud backup/sync

**Impact**: Users must manually copy backups to multiple locations

**Workaround**: Use cloud storage providers manually

**Future**: Optional cloud integration may be added

---

### No Backup Versioning

**Limitation**: No automatic backup history/versioning

**Impact**: User must manually manage multiple backup versions

**Workaround**: Use dated filenames (e.g., `backup_2024-01-15.png`)

---

### No Metadata Embedding

**Limitation**: Cannot embed metadata (creation date, notes, etc.)

**Impact**: Must track backup information separately

**Design Choice**: Minimize payload complexity

---

## Compatibility Limitations

### Python Version Requirement

**Requirement**: Python 3.9+

**Impact**: Cannot run on older systems with Python 3.8 or earlier

**Reason**: Modern type hints and library dependencies

**Workaround**: Upgrade Python or use Docker

---

### Dependency Requirements

**Required Libraries**:
- PyNaCl (requires libsodium)
- Pillow (requires image libraries)
- argon2-cffi (requires C compiler for some platforms)

**Impact**: Installation may require build tools on some systems

---

## Design Limitations

### Single Password Storage

**Limitation**: One backup = one password

**Impact**: Managing many passwords requires many backups

**Design Philosophy**: Simplicity over feature richness

**Use Case**: Backup critical master passwords, not entire vaults

---

### No Compression

**Limitation**: Payload not compressed before embedding

**Impact**: Slightly larger payloads for long passwords

**Reason**: Compression may reveal information about plaintext

**Impact**: Negligible for typical password lengths

---

### Sequential Processing

**Limitation**: No parallel processing for large images

**Impact**: Large images take longer to process

**Status**: Not optimized yet

**Future**: Parallelization may be added

---

## Documentation Limitations

### No Formal Security Audit

**Status**: v0.6.1 has not undergone external security audit

**Impact**: Undiscovered vulnerabilities may exist

**Mitigation**: Code is open source for community review

**Future**: Professional audit planned

---

### Limited Language Support

**Current**: English only

**Impact**: Non-English speakers may face barriers

**Future**: Internationalization planned

---

## Mitigations and Workarounds

### General Guidance

1. **Use PNG exclusively** (avoid JPEG)
2. **Choose strong passphrases** (16+ characters)
3. **Create multiple backups** (redundancy)
4. **Test recovery regularly** (verify backups work)
5. **Keep system secure** (no keyloggers)

### Accepting Limitations

Some limitations are by design:
- **No passphrase recovery**: Inherent to zero-knowledge design
- **LSB detectability**: Steganography is obscurity, not security
- **No post-quantum**: Migrate when practical quantum computers exist

## Future Improvements

See [ROADMAP.md](../ROADMAP.md) for planned enhancements:

- GUI application
- Post-quantum cryptography
- Advanced steganography techniques
- Multi-password support
- Mobile applications

## Reporting Limitations

Found a new limitation not listed here?

1. Check if it's a bug or intended behavior
2. Search existing issues
3. Open a GitHub issue with "Limitation:" prefix
4. Provide use case and impact assessment

## Next Steps

- Review [Security Model](Security-Model.md)
- Read [Threat Model](Threat-Model.md)
- Check [Security Best Practices](Security-Best-Practices.md)
- See [FAQ](FAQ.md) for common questions
