# Common Errors

Quick reference for common StegVault errors and solutions.

## Error Messages

### CryptoError: Decryption failed

```
Error: Decryption failed
Cause: AEAD authentication tag verification failed
```

**Meaning**: Authentication failed during decryption

**Common Causes**:
1. Wrong passphrase (most common)
2. Image was modified after backup creation
3. Corrupted backup file

**Quick Fix**:
```bash
# Try again with correct passphrase
# Ensure no typos, check Caps Lock
```

**See**: [Restoring Passwords](Restoring-Passwords.md#error-1-incorrect-passphrase)

---

### CapacityError: Image capacity insufficient

```
Error: Image capacity insufficient
Required: 120 bytes
Available: 75 bytes
```

**Meaning**: Image too small for payload

**Common Causes**:
- Image resolution too low
- Trying to embed very long password

**Quick Fix**:
```bash
# Use larger image (800x600 recommended minimum)
stegvault check -i your_image.png  # Check capacity first
```

**See**: [Choosing Cover Images](Choosing-Cover-Images.md#minimum-requirements)

---

### PayloadFormatError: Invalid magic header

```
Error: Payload extraction failed
Cause: Invalid magic header
Expected: 'SPW1'
Found: [random bytes]
```

**Meaning**: Not a valid StegVault backup

**Common Causes**:
1. Wrong image file
2. JPEG recompression destroyed payload
3. Image heavily modified/corrupted

**Quick Fix**:
```bash
# Verify you're using correct backup image
# Try backup from different storage location
```

**See**: [Troubleshooting](Troubleshooting.md#invalid-magic-header)

---

### StegoError: Extraction failed

```
Error: Failed to extract payload from image
```

**Meaning**: Could not read payload from image

**Common Causes**:
- Image format changed (JPEG resaved)
- Image edited or filtered
- File corruption

**Quick Fix**:
```bash
# Use original unmodified backup
# Check file format: file backup.png
```

---

### ValueError: Invalid passphrase length

```
ValueError: Passphrase must be at least 1 character
```

**Meaning**: Empty passphrase provided

**Quick Fix**:
```bash
# Enter passphrase when prompted
# Don't press Enter without typing
```

---

### FileNotFoundError: Image not found

```
FileNotFoundError: [Errno 2] No such file or directory: 'cover.png'
```

**Meaning**: Image file doesn't exist at specified path

**Common Causes**:
- Typo in filename
- Wrong directory
- File moved or deleted

**Quick Fix**:
```bash
# Check file exists
ls -la cover.png

# Use absolute path
stegvault backup -i /full/path/to/cover.png -o backup.png
```

---

### PermissionError: Permission denied

```
PermissionError: [Errno 13] Permission denied: 'backup.png'
```

**Meaning**: Cannot write to output location

**Common Causes**:
- No write permission in directory
- File is read-only
- File in use by another program

**Quick Fix**:
```bash
# Check permissions
ls -l backup.png

# Use writable directory
cd ~/Documents
stegvault backup -i cover.png -o backup.png
```

---

### ImportError: No module named 'nacl'

```
ImportError: No module named 'nacl'
```

**Meaning**: PyNaCl not installed

**Quick Fix**:
```bash
pip install PyNaCl
# Or reinstall StegVault
pip install -e .
```

**See**: [Installation Guide](Installation-Guide.md#dependency-information)

---

### ModuleNotFoundError: No module named 'stegvault'

```
ModuleNotFoundError: No module named 'stegvault'
```

**Meaning**: StegVault not installed

**Quick Fix**:
```bash
# Install from source
cd StegVault
pip install -e .

# Verify
stegvault --version
```

**See**: [Installation Guide](Installation-Guide.md)

---

### UnsupportedImageFormatError

```
Error: Unsupported image format
Supported formats: PNG, JPEG
```

**Meaning**: Image format not supported

**Common Formats**:
- GIF, BMP, WebP, TIFF not supported

**Quick Fix**:
```bash
# Convert to PNG
convert image.gif image.png
```

---

### MemoryError: Unable to allocate

```
MemoryError: Unable to allocate memory for Argon2
```

**Meaning**: Insufficient RAM

**Common Causes**:
- System has <512MB RAM
- Many other programs running
- Very large image

**Quick Fix**:
```bash
# Close other applications
# Use smaller image
# Restart system to free memory
```

---

## Warning Messages

### Warning: Passphrase is too weak

```
Warning: Passphrase is too weak (only digits)
Continue anyway? [y/N]:
```

**Meaning**: Passphrase doesn't meet strength criteria

**Recommendations**:
- Use 16+ characters
- Mix character types
- Avoid dictionary words

**Quick Fix**:
```bash
# Use stronger passphrase
# Example: "Correct-Horse-Battery-Staple-92!"
```

**See**: [Security Best Practices](Security-Best-Practices.md#passphrase-guidelines)

---

### Warning: JPEG format detected

```
Warning: JPEG format detected
Avoid resaving or editing this image
Consider using PNG for better reliability
```

**Meaning**: JPEG is risky for backups

**Recommendation**: Use PNG instead

**Quick Fix**:
```bash
# Convert to PNG first
convert photo.jpg photo.png
stegvault backup -i photo.png -o backup.png
```

**See**: [Choosing Cover Images](Choosing-Cover-Images.md#format-selection)

---

### Warning: Image capacity is low

```
Warning: Image capacity (85 bytes) is barely sufficient
Recommend using larger image (800x600+)
```

**Meaning**: Image is small, consider larger one

**Quick Fix**:
```bash
# Use 800x600 or larger image
stegvault check -i larger_image.png
```

---

## Exit Codes

### Exit Code 0

**Meaning**: Success

---

### Exit Code 1

**Meaning**: General error

**Causes**:
- Invalid arguments
- File not found
- Operation failed

**Action**: Check error message

---

### Exit Code 2

**Meaning**: CLI argument error

**Causes**:
- Missing required argument
- Invalid option

**Quick Fix**:
```bash
stegvault backup --help
```

---

## Python Tracebacks

### AttributeError: 'NoneType' object has no attribute

```
AttributeError: 'NoneType' object has no attribute 'size'
```

**Meaning**: Image failed to load

**Common Causes**:
- Corrupted image file
- Unsupported format
- File is not an image

**Quick Fix**:
```bash
# Verify image is valid
file image.png
# Should say "PNG image data"

# Try opening in image viewer
```

---

### TypeError: argument must be bytes

```
TypeError: a bytes-like object is required, not 'str'
```

**Meaning**: Internal encoding issue

**Action**: Report as bug (should not happen in normal usage)

---

### KeyError: 'ciphertext'

```
KeyError: 'ciphertext'
```

**Meaning**: Payload parsing failed

**Causes**:
- Corrupted backup
- Wrong image
- Payload format issue

**Quick Fix**:
- Use correct backup image
- Try alternate backup copy

---

## Network Errors (Future)

### ConnectionError

Not applicable to v0.7.10 (no cloud features yet)

The auto-update system (v0.7.6+) checks PyPI for updates but does not sync data. Cloud sync features may be added in future versions.

---

## Debugging Unknown Errors

### Steps to Debug

1. **Enable verbose mode** (if available):
   ```bash
   stegvault backup -i cover.png -o backup.png -v
   ```

2. **Check Python version**:
   ```bash
   python --version  # Should be 3.9+
   ```

3. **Verify installation**:
   ```bash
   pip show stegvault
   pip list | grep -E "(PyNaCl|argon2|Pillow)"
   ```

4. **Test with minimal example**:
   ```bash
   # Create test image
   python -c "from PIL import Image; Image.new('RGB', (100,100)).save('test.png')"

   # Test backup
   stegvault backup -i test.png -o test_backup.png
   ```

5. **Check file integrity**:
   ```bash
   # Verify images are valid
   file *.png
   ```

6. **Reinstall clean**:
   ```bash
   pip uninstall stegvault
   pip install -e .
   ```

---

## Reporting Errors

### When Reporting

Include:
1. **Full error message** (copy-paste entire traceback)
2. **Command used** (exact command)
3. **System info**:
   - OS and version
   - Python version
   - StegVault version
4. **Steps to reproduce**

### Where to Report

- **Bugs**: GitHub Issues
- **Security**: See [Vulnerability Disclosure](Vulnerability-Disclosure.md)
- **Questions**: GitHub Discussions or [FAQ](FAQ.md)

### Issue Template

```markdown
**Error**: [Error message]

**Command**:
```bash
stegvault backup -i cover.png -o backup.png
```

**System**:
- OS: Ubuntu 22.04
- Python: 3.11.0
- StegVault: 0.6.1

**Steps**:
1. Created cover image
2. Ran backup command
3. Got error

**Full Traceback**:
[Paste full error output]
```

---

## Quick Reference Table

| Error | Cause | Solution |
|-------|-------|----------|
| Decryption failed | Wrong passphrase | Check passphrase, try again |
| Capacity insufficient | Image too small | Use larger image (800x600+) |
| Invalid magic header | Wrong/corrupted image | Use correct backup image |
| File not found | Wrong path | Check filename and path |
| Permission denied | No write access | Use writable directory |
| No module 'nacl' | PyNaCl not installed | `pip install PyNaCl` |
| No module 'stegvault' | Not installed | `pip install -e .` |
| Unsupported format | Wrong image type | Convert to PNG |
| Memory error | Insufficient RAM | Close apps, use smaller image |

## Next Steps

- Full solutions: [Troubleshooting Guide](Troubleshooting.md)
- Common questions: [FAQ](FAQ.md)
- Installation help: [Installation Guide](Installation-Guide.md)
- Usage help: [Quick Start Tutorial](Quick-Start-Tutorial.md)
