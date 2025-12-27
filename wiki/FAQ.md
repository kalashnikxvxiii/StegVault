# Frequently Asked Questions (FAQ)

Common questions about StegVault.

## General Questions

### What is StegVault?

StegVault is a full-featured password manager that uses steganography to hide encrypted credentials within images. It combines modern cryptography (XChaCha20-Poly1305 + Argon2id) with dual steganography (PNG LSB + JPEG DCT) to create portable, secure password vaults.

**Current version**: 0.7.8 (Auto-Update Critical Bug Fixes)
**Features**: Full vault mode, TOTP/2FA application lock, Gallery management, TUI with favorite folders, Headless mode, Auto-update system with WinError 32 fix

---

### Why would I use StegVault instead of a traditional password manager?

StegVault is designed for **backup** scenarios:
- Create encrypted backups of critical passwords (e.g., password manager master password)
- Store backups as innocent-looking images
- Distribute backups across multiple locations
- Recover passwords without specialized software (just the StegVault CLI)

It's a **complement** to, not a replacement for, password managers.

---

### Is it safe to use?

Yes, with proper usage:
- Uses industry-standard cryptography (XChaCha20-Poly1305, Argon2id)
- Encryption protects your password even if backup image is captured
- **Critical**: You must use a strong passphrase (16+ characters)

See [Security Model](Security-Model.md) for detailed analysis.

---

### Is this open source?

Yes! StegVault is open source under the MIT license:
- Source code: https://github.com/kalashnikxvxiii/StegVault
- Community contributions welcome
- Auditable by security researchers

---

## Security Questions

### Can someone recover my password if they find the backup image?

**Without your passphrase**: No. The password is encrypted with XChaCha20-Poly1305 AEAD. Modern cryptography makes brute-force infeasible with a strong passphrase.

**With your passphrase**: Yes. That's why passphrase protection is critical.

---

### Is the steganography secure?

**Steganography alone**: No. LSB embedding is detectable by experts.

**Combined with encryption**: Yes. Even if detected, the password remains encrypted.

**Key point**: Steganography provides obscurity, NOT security. Encryption is the security layer.

---

### What happens if I forget my passphrase?

**Short answer**: Your password is **permanently unrecoverable**.

**Why**: StegVault is zero-knowledge by design. There's no "password reset" or recovery mechanism.

**Prevention**:
- Store passphrase in a separate password manager
- Memorize strong passphrases
- Consider physical backup in a secure location

---

### Can quantum computers break StegVault?

**Eventually, yes**. XChaCha20 is not post-quantum secure.

**Timeline**: Practical quantum computers are 10-30 years away.

**Mitigation**: Future versions will support post-quantum cryptography.

**For now**: Use strong passphrases to maximize security even against quantum attacks.

---

### Is my backup image suspicious?

**To casual observers**: No. Looks like a normal photo.

**To forensic analysis**: Yes. Statistical analysis can detect LSB steganography.

**Bottom line**: Don't rely on steganography to hide from determined investigators. Rely on encryption.

---

## Usage Questions

### Should I use PNG or JPEG?

**Always use PNG** unless you have a specific reason not to.

**Why PNG**:
- Lossless format preserves data perfectly
- Resaving doesn't corrupt backup
- Reliable for long-term storage

**Why not JPEG**:
- Lossy compression can destroy embedded data
- Editing/resaving changes LSBs
- Unreliable for backups

---

### How many passwords can I store in one image?

**Design**: One backup = one password

**Workaround**: Create separate backups for different passwords

**Why**: Simplicity and security. Each password has its own independent backup.

---

### Can I use the same image for multiple backups?

**Not recommended**. Use a fresh cover image for each backup.

**Why**:
- Prevents statistical analysis across multiple backups
- Each backup is independent
- No pattern correlation

---

### How do I know my backup is working?

**Always test recovery immediately after creation**:

```bash
# Create backup
stegvault backup -i cover.png -o backup.png

# Immediately test
stegvault restore -i backup.png

# Verify password matches
```

Test periodically (monthly recommended) to catch corruption early.

---

### What size image do I need?

**Minimum**: 800×600 pixels (recommended)

**Capacity**: Check with `stegvault check -i image.png`

**Typical password** (8-32 chars) fits easily in 800×600 image.

**Large passwords** (>1000 chars) need larger images.

---

## Technical Questions

### What encryption does StegVault use?

- **Cipher**: XChaCha20-Poly1305 (AEAD)
- **KDF**: Argon2id
- **Library**: libsodium (via PyNaCl)

See [Cryptography Details](Cryptography-Details.md) for complete technical specs.

---

### How is the password embedded in the image?

LSB (Least Significant Bit) steganography with pseudo-random pixel ordering:
1. Encrypt password
2. Serialize encrypted payload
3. Embed payload bits into LSBs of random pixels
4. Result looks visually identical to original

See [Steganography Techniques](Steganography-Techniques.md) for details.

---

### Can I integrate StegVault into my application?

Yes! StegVault provides a Python API:

```python
from stegvault import encrypt_data, embed_payload

# Use in your code
```

See [API Reference](API-Reference.md) for complete documentation.

---

### Does StegVault work on mobile?

**Currently**: No. CLI only, requires Python 3.9+.

**Future**: Mobile apps (iOS/Android) are planned.

**Workaround**: Use Termux (Android) or Python environments on mobile.

---

## Troubleshooting Questions

### "Image capacity insufficient" error

**Cause**: Image too small for payload

**Solution**:
1. Use a larger image (800×600 minimum)
2. Check capacity: `stegvault check -i image.png`
3. Use a different image

---

### "Decryption failed" error

**Causes**:
- Wrong passphrase (most common)
- Image was modified/corrupted
- Not a valid StegVault backup

**Solutions**:
1. Double-check passphrase (watch for typos)
2. Try a different backup copy
3. Verify image hasn't been edited

See [Troubleshooting](Troubleshooting.md) for more.

---

### Backup image looks corrupted

**Visual inspection**: Stego image should look identical to original

**If different**: Something went wrong

**Solutions**:
1. Ensure you're comparing correct files
2. Recreate backup
3. Check for disk errors

---

### Recovery is slow

**Normal**: Argon2id is intentionally slow (~100ms)

**Very slow** (>5 seconds):
- Old hardware
- Low-end device
- System under load

**Not a bug**: Security vs. performance trade-off.

---

## Comparison Questions

### StegVault vs. VeraCrypt?

**VeraCrypt**: Full-disk encryption, encrypted containers
**StegVault**: Password backup in innocent-looking images

**Use together**:
- VeraCrypt for volume encryption
- StegVault for password backup

---

### StegVault vs. Password Managers?

**Password Managers**: Store hundreds of passwords, auto-fill, sync

**StegVault**: Backup critical passwords in portable image format

**Use together**:
- Password manager for daily use
- StegVault to backup manager's master password

---

### StegVault vs. Hardware Security Keys?

**Hardware Keys**: Physical device for authentication

**StegVault**: Software-based password backup

**Different purposes**:
- Use hardware keys for 2FA
- Use StegVault for password backup/recovery

---

## Practical Questions

### Where should I store my backups?

**Multiple locations** (redundancy is critical):
- Cloud storage (Dropbox, Google Drive, etc.)
- External USB drives
- NAS/home server
- Printed QR codes (advanced)

**Never rely on a single copy!**

---

### How often should I create new backups?

**When password changes**: Create new backup immediately

**Periodic backups**: Not necessary if password doesn't change

**Test recovery**: Monthly recommended

---

### Can I share a backup with family/team?

**Not recommended**. Sharing backup = sharing password.

**Better approach**:
- Each person creates their own backup
- Or use secret-sharing schemes (future feature)

---

### What if my backup image is leaked online?

**Good news**: Password is still encrypted

**Actions**:
1. **Don't panic** - encryption protects you
2. Change the actual password (if possible)
3. Create new backup with new passphrase
4. Don't reuse the leaked passphrase

**As long as passphrase is strong, you're safe**.

---

## Future Features

### Will there be a GUI?

**Yes!** Desktop GUI is planned for future releases:

- **v0.7.0**: Terminal UI (TUI) with Textual ✅ COMPLETED
- **v0.8.0**: Desktop GUI with PySide6 🔜 PLANNED

**Current (v0.7.8)**: CLI, TUI (full-featured terminal interface), and headless mode for automation

---

### Will StegVault support multiple passwords?

**Maybe**. Under consideration for future versions.

**Current**: One backup = one password (by design)

---

### Can I contribute?

**Absolutely!** Contributions welcome:
- Code improvements
- Documentation
- Bug reports
- Security reviews

See [Contributing Guidelines](../CONTRIBUTING.md).

---

## Getting Help

### Where can I ask more questions?

- **Documentation**: Read the wiki
- **Issues**: GitHub Issues for bugs
- **Discussions**: GitHub Discussions for questions
- **Security**: See [Vulnerability Disclosure](Vulnerability-Disclosure.md)

### Something not working?

1. Check [Troubleshooting Guide](Troubleshooting.md)
2. Review [Common Errors](Common-Errors.md)
3. Search existing GitHub issues
4. Open a new issue with details

## Next Steps

- Try the [Quick Start Tutorial](Quick-Start-Tutorial.md)
- Read [Security Best Practices](Security-Best-Practices.md)
- Review [Known Limitations](Known-Limitations.md)
- Check [Troubleshooting](Troubleshooting.md) if you have issues
