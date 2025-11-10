# Security Best Practices

Follow these guidelines to maximize security when using StegVault.

## Passphrase Management

### Creating Strong Passphrases

✅ **DO:**
- Use 16+ characters minimum
- Include uppercase, lowercase, numbers, and symbols
- Use random words combined (e.g., "correct-horse-battery-staple")
- Consider using a passphrase generator
- Make it memorable but not guessable

❌ **DON'T:**
- Use dictionary words alone
- Reuse passphrases from other services
- Use personal information (birthdays, names, etc.)
- Write passphrase in plaintext files
- Share passphrase via insecure channels

### Passphrase Examples

**Weak** ❌:
- `password123`
- `mybirthday1990`
- `P@ssw0rd`

**Strong** ✅:
- `Tr0pic@l-Elephant-29-Surfboard`
- `Quantum$Nebula#7845*Moonlight`
- `correct-HORSE-battery-STAPLE-42!`

### Storing Passphrases

- Use a dedicated password manager (1Password, Bitwarden, KeePass)
- Write on paper and store in secure location (safe, safety deposit box)
- Never store in plain text files
- Consider using a hardware security key (YubiKey) for critical backups

## Image Selection

### Choosing Cover Images

✅ **Good Cover Images:**
- High resolution (500x500 pixels minimum)
- PNG format (lossless compression)
- Complex content (photographs, artwork)
- RGB color mode
- Legitimate personal photos

❌ **Poor Cover Images:**
- Low resolution (<100x100 pixels)
- Simple patterns or solid colors
- Already compressed multiple times
- JPEG format (if possible recompression expected)
- Suspicious or unusual images

### Image Capacity Guidelines

| Image Size | Capacity | Suitable For |
|------------|----------|--------------|
| 100x100 px | ~3.7 KB | Short passwords only |
| 500x500 px | ~93 KB | Most passwords |
| 1000x1000 px | ~375 KB | Multiple passwords/vault |
| 2000x2000 px | ~1.5 MB | Large vaults |

Check capacity before use:
```bash
stegvault check -i myimage.png
```

## Backup Management

### Creating Backups

1. **Test Before Relying**: Always test restore immediately after backup creation
2. **Multiple Copies**: Store at least 3 copies in different locations
3. **Different Media**: Use USB drives, cloud storage, and physical storage
4. **Geographic Distribution**: Store copies in different physical locations
5. **Verify Integrity**: Periodically test restore to ensure backups work

### Backup Storage Locations

✅ **Recommended:**
- Encrypted USB drive in safe
- Cloud storage (Dropbox, Google Drive) - image encrypted locally first
- Password-protected network storage
- Safety deposit box
- Trusted family member's secure storage

❌ **Not Recommended:**
- Public cloud without encryption
- Shared network drives
- Email attachments
- Public USB drives
- Unencrypted external drives

### Backup Rotation

- Create new backups when password changes
- Keep previous backup until new one verified
- Delete old backups securely (overwrite, don't just delete)
- Update all backup locations

## Operational Security

### When Creating Backups

- Use trusted computer (not public/shared computers)
- Ensure no shoulder surfers or cameras
- Use secure environment (not public WiFi)
- Clear clipboard after entering passphrase
- Close StegVault when done

### When Restoring Passwords

- Verify you're on secure device
- Check for keyloggers/malware first
- Use password in secure context only
- Don't display on shared screens
- Clear terminal history if password displayed

### Metadata Concerns

StegVault images contain:
- Embedded encrypted payload
- Image metadata (EXIF data from original)

**Recommendations:**
- Strip EXIF data before creating backup if concerned
- Don't use identifiable original images
- Consider scrubbing metadata from final backup image

```bash
# Strip EXIF data (using exiftool)
exiftool -all= backup.png
```

## Threat Modeling

### What StegVault Protects Against

✅ Protected:
- Casual inspection of image
- Basic file analysis
- Brute-force attacks (with strong passphrase + Argon2id)
- Data extraction without passphrase
- Tampering detection (AEAD tag)

### What StegVault Does NOT Protect Against

❌ Not Protected:
- Advanced steganalysis by experts
- Quantum computer attacks (future threat)
- Rubber-hose cryptanalysis (coercion)
- Compromised device with keylogger
- Social engineering attacks

### Adversary Levels

| Adversary | Risk | Mitigation |
|-----------|------|------------|
| **Casual snooper** | Low | Default settings sufficient |
| **Technical person** | Medium | Strong passphrase, regular updates |
| **Security professional** | High | Consider additional layers, review code |
| **State-level actor** | Very High | StegVault alone insufficient, use additional security measures |

## Advanced Security Measures

### Multi-Layer Security

1. **Encrypt container**: Use VeraCrypt/LUKS for USB drives
2. **Obscure filename**: Don't name file "password_backup.png"
3. **Decoy files**: Mix with other innocent images
4. **Stealth delivery**: If emailing, use end-to-end encryption (ProtonMail)

### Deniability Considerations

If plausible deniability is important:
- Use innocent-looking cover images
- Store among many other similar images
- Don't use obvious filenames
- Consider steganography tools' statistical signatures

**Note**: StegVault has a magic header ("SPW1") making payloads identifiable. True deniability may require modifications.

## Security Updates

### Staying Secure

- Subscribe to StegVault security advisories
- Update to latest version promptly
- Review CHANGELOG for security fixes
- Follow project on GitHub for announcements

### Reporting Vulnerabilities

If you discover a security issue:
- **DO NOT** open public issue
- Email privately to security contact
- Provide detailed description and PoC
- Allow time for patch before disclosure

## Legal & Ethical Considerations

### Legal Compliance

- Steganography laws vary by jurisdiction
- Some countries restrict or ban steganography
- Check local laws before use
- Understand implications of "hidden data"

### Ethical Use

StegVault should be used for:
✅ Legitimate password backup
✅ Personal security
✅ Educational purposes
✅ Security research

❌ NOT for:
- Illegal activities
- Evading lawful investigations
- Malware distribution
- Corporate espionage

## Emergency Procedures

### If Passphrase Compromised

1. **Assume Backup Compromised**: Change master password immediately
2. **Create New Backup**: With new passphrase
3. **Secure Delete Old Backup**: Use secure deletion tools
4. **Audit Access**: Check if any accounts accessed

### If Backup Lost/Corrupted

1. **Don't Panic**: Check all backup locations
2. **Test All Copies**: One may still work
3. **Review Backup Process**: Prevent future issues
4. **Create New Backup**: From current password state

### If Device Compromised

1. **Assume Passphrase Stolen**: Change immediately
2. **Scan for Malware**: Full system scan
3. **Review Logs**: Check for unauthorized access
4. **Rotate All Passwords**: Not just backed-up ones

## Checklist for Maximum Security

Before creating backup:
- [ ] Strong passphrase created (16+ chars)
- [ ] Suitable cover image selected (500x500+ px PNG)
- [ ] Secure environment verified
- [ ] No surveillance concerns
- [ ] Device is trusted and clean

After creating backup:
- [ ] Restore tested successfully
- [ ] Original password verified correct
- [ ] Backup stored in multiple secure locations
- [ ] Original cover image securely deleted
- [ ] Passphrase not written down insecurely
- [ ] Terminal/clipboard cleared

Periodic maintenance:
- [ ] Test restore monthly
- [ ] Verify backup integrity
- [ ] Update StegVault to latest version
- [ ] Review and rotate backups
- [ ] Check backup storage security

## Additional Resources

- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [EFF's Dice-Generated Passphrases](https://www.eff.org/dice)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)

---

**Remember**: Security is a process, not a product. No single tool provides perfect security. StegVault is one layer in a comprehensive security strategy.