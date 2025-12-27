# Troubleshooting Guide

Solutions to common StegVault problems.

## Installation Issues

### "pip install fails" or "No module named 'stegvault'"

**Symptoms**:
```bash
pip install stegvault
ERROR: Could not find a version that satisfies the requirement stegvault
```

**Cause**: Package not yet on PyPI (v0.6.1 is source-only)

**Solution**:
```bash
# Clone and install from source
git clone https://github.com/kalashnikxvxiii/StegVault.git
cd StegVault
pip install -e .
```

---

### "Python version too old"

**Symptoms**:
```
ERROR: Python 3.9 or higher required
```

**Cause**: Using Python 3.8 or earlier

**Solution**:
```bash
# Check version
python --version

# Upgrade Python
# - Windows: Download from python.org
# - macOS: brew install python@3.11
# - Linux: sudo apt install python3.11
```

---

### "C compiler required" on installation

**Symptoms**:
```
error: Microsoft Visual C++ 14.0 is required
```

**Cause**: argon2-cffi needs compilation on some platforms

**Solution**:

**Windows**:
```bash
# Install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

**Linux**:
```bash
sudo apt install build-essential python3-dev
```

**macOS**:
```bash
xcode-select --install
```

---

### "Failed to import PyNaCl"

**Symptoms**:
```
ImportError: No module named 'nacl'
```

**Cause**: PyNaCl not installed or libsodium missing

**Solution**:
```bash
# Reinstall PyNaCl
pip install --upgrade PyNaCl

# If fails, install libsodium
# - Windows: Usually works automatically
# - Linux: sudo apt install libsodium-dev
# - macOS: brew install libsodium
```

---

## Backup Creation Issues

### "Image capacity insufficient"

**Symptoms**:
```
Error: Image capacity insufficient
Required: 92 bytes
Available: 48 bytes
```

**Cause**: Image too small for payload

**Solution**:
```bash
# Check image capacity first
stegvault check -i your_image.png

# Use a larger image (800x600 minimum recommended)
convert small.png -resize 800x600 larger.png
stegvault backup -i larger.png -o backup.png
```

---

### "Passphrase too weak" warning

**Symptoms**:
```
Warning: Passphrase is too weak (only lowercase letters)
Continue anyway? [y/N]:
```

**Cause**: Passphrase doesn't meet strength criteria

**Solution**:
- Use 16+ characters
- Mix uppercase, lowercase, numbers, symbols
- Avoid dictionary words

**Example strong passphrase**:
```
Correct-Horse-Battery-Staple-92!
MyD0g@teMyH0m3w0rk#2024
```

---

### "File exists" error

**Symptoms**:
```
Error: Output file already exists: backup.png
```

**Cause**: Output file already exists (safety check)

**Solution**:
```bash
# Use different output name
stegvault backup -i cover.png -o backup_new.png

# Or remove existing file first
rm backup.png
stegvault backup -i cover.png -o backup.png
```

---

### "Unsupported image format"

**Symptoms**:
```
Error: Unsupported image format
Supported formats: PNG, JPEG
```

**Cause**: Using GIF, BMP, WebP, etc.

**Solution**:
```bash
# Convert to PNG
convert image.gif image.png
stegvault backup -i image.png -o backup.png
```

---

## Restoration Issues

### "Decryption failed"

**Symptoms**:
```
Error: Decryption failed
Cause: AEAD authentication tag verification failed
```

**Common Causes & Solutions**:

#### Wrong Passphrase
```bash
# Double-check passphrase
# Watch for:
# - Typos
# - Caps Lock
# - Extra spaces
```

#### Image Modified
```bash
# Try a backup copy
stegvault restore -i backup_copy.png

# Check if image was edited
# - Resaved as JPEG
# - Cropped or resized
# - Filters applied
```

#### Corrupted File
```bash
# Verify file integrity
sha256sum backup.png

# Try different storage location
# USB, cloud, etc.
```

#### Not a StegVault Backup
```bash
# Verify it's a backup you created
# Check filename, location, date
```

---

### "Invalid magic header"

**Symptoms**:
```
Error: Payload extraction failed
Cause: Invalid magic header
```

**Causes**:
- Not a StegVault backup
- Image heavily corrupted
- JPEG recompression destroyed payload

**Solution**:
```bash
# Verify this is the correct backup image
# Try alternate backup copies
# If JPEG, use original before recompression
```

---

### "Payload too short"

**Symptoms**:
```
Error: Payload format error
Cause: Payload too short (expected 64+ bytes)
```

**Cause**: Image corruption or wrong image

**Solution**:
- Use correct backup image
- Try backup from different storage location
- Check disk health

---

## Runtime Issues

### Backup/restore very slow

**Symptoms**: Takes >5 seconds

**Normal on**:
- Raspberry Pi
- Old computers
- Low-end hardware

**Cause**: Argon2id is intentionally slow (security feature)

**Solutions**:
```bash
# Upgrade hardware (if possible)
# Or accept slower performance as security trade-off

# Not recommended: Reduce security (requires code modification)
```

---

### High memory usage

**Symptoms**: System slows down during operation

**Cause**: Argon2id uses 64 MB + image loading

**Solution**:
```bash
# Close other applications
# Use smaller images if possible
# Upgrade RAM (if system has <1GB)
```

---

### "Out of memory" error

**Symptoms**:
```
MemoryError: Unable to allocate memory
```

**Cause**: Very large image or constrained system

**Solution**:
```bash
# Use smaller image
convert large.png -resize 1920x1080 smaller.png

# Or increase available memory
# - Close other applications
# - Restart system
```

---

## CLI Issues

### "Command not found: stegvault"

**Symptoms**:
```bash
stegvault --version
bash: stegvault: command not found
```

**Cause**: Not installed or not in PATH

**Solution**:
```bash
# Reinstall in editable mode
pip install -e .

# Or use python -m
python -m stegvault.cli --version

# Check installation
pip show stegvault
```

---

### "Permission denied" errors

**Symptoms**:
```
Permission denied: /path/to/backup.png
```

**Cause**: File permissions or directory access

**Solution**:
```bash
# Check file permissions
ls -l backup.png

# Fix permissions
chmod 644 backup.png

# Or save to writable directory
cd ~/Documents
stegvault backup -i cover.png -o backup.png
```

---

### Input prompts not working

**Symptoms**: Prompts don't appear or accept input

**Cause**: Non-interactive terminal or redirection issues

**Solution**:
```bash
# Use explicit parameters
stegvault backup \
  -i cover.png \
  -o backup.png \
  --password "mypassword" \
  --passphrase "mypassphrase"

# Or ensure interactive terminal
# Don't pipe through other commands
```

---

## Image Issues

### JPEG backup fails recovery

**Symptoms**: Backup works, but restore fails later

**Cause**: JPEG recompression destroyed LSBs

**Solution**:
```bash
# Always use PNG for production backups
stegvault backup -i cover.png -o backup.png

# Convert existing JPEG covers to PNG first
convert photo.jpg photo.png
```

---

### "Image file not found"

**Symptoms**:
```
Error: Image file not found: cover.png
```

**Cause**: Wrong path or filename

**Solution**:
```bash
# List files
ls -la

# Use absolute path
stegvault backup -i /full/path/to/cover.png -o backup.png

# Or cd to directory first
cd /path/to/images
stegvault backup -i cover.png -o backup.png
```

---

### Image appears corrupted after backup

**Symptoms**: Stego image looks wrong

**Cause**: Should NOT be visible! LSB changes are imperceptible.

**If visible**:
- File corruption during save
- Wrong image format
- Disk errors

**Solution**:
```bash
# Recreate backup
# Check disk health
# Use PNG format
```

---

## Platform-Specific Issues

### Windows: PowerShell execution policy

**Symptoms**:
```
cannot be loaded because running scripts is disabled
```

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### macOS: "Developer cannot be verified"

**Symptoms**: Security warning on first run

**Solution**:
```bash
# Allow in System Preferences > Security & Privacy
# Or install libsodium via Homebrew first
brew install libsodium
```

---

### Linux: Missing dependencies

**Symptoms**: Import errors for Pillow

**Solution**:
```bash
# Install image libraries
sudo apt install libjpeg-dev zlib1g-dev libpng-dev

# Reinstall Pillow
pip install --upgrade --force-reinstall Pillow
```

---

## Debugging Steps

### General Debugging Process

1. **Check versions**:
   ```bash
   python --version
   pip show stegvault PyNaCl Pillow argon2-cffi
   ```

2. **Run with verbose output**:
   ```bash
   stegvault backup -i cover.png -o backup.png -v
   ```

3. **Test with minimal example**:
   ```bash
   # Create simple test image
   python -c "from PIL import Image; Image.new('RGB', (100,100)).save('test.png')"

   # Try backup
   stegvault backup -i test.png -o test_backup.png
   ```

4. **Check file integrity**:
   ```bash
   # Verify image is valid
   file cover.png
   identify cover.png  # If ImageMagick installed
   ```

5. **Test in clean environment**:
   ```bash
   # Create fresh venv
   python -m venv clean_test
   source clean_test/bin/activate
   pip install stegvault
   ```

---

## Getting More Help

### Before Asking for Help

Collect this information:
- StegVault version (`stegvault --version`)
- Python version (`python --version`)
- Operating system
- Full error message
- Steps to reproduce

### Where to Ask

1. **Check documentation**:
   - [FAQ](FAQ.md)
   - [Common Errors](Common-Errors.md)
   - [Installation Guide](Installation-Guide.md)

2. **Search existing issues**:
   - GitHub Issues
   - Closed issues (may already be solved)

3. **Open new issue**:
   - Provide system info
   - Include error messages
   - Describe steps to reproduce

## Next Steps

- Review [Common Errors](Common-Errors.md)
- Check [FAQ](FAQ.md)
- Read [Installation Guide](Installation-Guide.md)
- See [Security Best Practices](Security-Best-Practices.md)
