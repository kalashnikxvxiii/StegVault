# StegVault Examples

This directory contains example code and test images for StegVault.

## Quick Start

### 1. Create Test Images

```bash
cd examples
python create_test_images.py
```

This generates three test PNG images:
- `cover_gradient.png` - Gradient background (500x500)
- `cover_pattern.png` - Geometric pattern (500x500)
- `cover_nature.png` - Nature-inspired texture (500x500)

### 2. Run Demo Script

```bash
python demo.py
```

This demonstrates the complete backup and restore workflow:
1. Check image capacity
2. Create encrypted backup
3. Restore password from backup

### 3. Try CLI Commands

#### Check Image Capacity

```bash
stegvault check -i cover_gradient.png
```

**Expected Output:**
```
Image: cover_gradient.png
Format: PNG
Mode: RGB
Size: 500x500 pixels

Capacity: 93750 bytes (91.55 KB)
Max password size: ~93686 bytes (93686 characters)

✓ Image has sufficient capacity for password storage.
```

#### Create Backup

```bash
stegvault backup -i cover_gradient.png -o my_backup.png
```

You'll be prompted for:
- **Master password**: The password you want to encrypt and hide
- **Encryption passphrase**: Secret passphrase for encryption (keep this safe!)

#### Restore Password

```bash
stegvault restore -i my_backup.png
```

You'll be prompted for your encryption passphrase, then your password is displayed.

## Example: Securing Database Password

```bash
# 1. Check image capacity
$ stegvault check -i cover_nature.png
Capacity: 93750 bytes (91.55 KB)
✓ Image has sufficient capacity for password storage.

# 2. Create backup with database password
$ stegvault backup -i cover_nature.png -o db_backup.png
Master password: myDatabasePassword123!@#
Encryption passphrase: MyStrongPassphrase2024!
Encryption passphrase (again): MyStrongPassphrase2024!

Creating encrypted backup...
Image capacity: 93750 bytes
Encrypting password...
Payload size: 97 bytes
Embedding payload in image...
✓ Backup created successfully: db_backup.png

IMPORTANT:
- Keep both the image AND passphrase safe
- Losing either means permanent data loss
- Do not recompress JPEG images (use PNG)
- Create multiple backup copies

# 3. Later, restore the password
$ stegvault restore -i db_backup.png
Encryption passphrase: MyStrongPassphrase2024!

Restoring password from backup...
Extracting payload header...
Payload size: 97 bytes
Extracting full payload...
Parsing payload...
Decrypting password...

==================================================
✓ Password recovered successfully!
==================================================

myDatabasePassword123!@#
```

## Security Best Practices

### ✅ DO:
- Use PNG images (lossless format)
- Use strong passphrases (16+ characters)
- Store backup images in multiple secure locations
- Test restore process after creating backup
- Use different passphrases for different backups

### ❌ DON'T:
- Use JPEG images (lossy compression destroys payload)
- Reuse passphrases across services
- Edit or resize images after embedding
- Share images without understanding the risks
- Forget either the image OR the passphrase

## File Structure

```
examples/
├── README.md                 # This file
├── create_test_images.py    # Generate test images
├── demo.py                   # Complete workflow demonstration
├── cover_gradient.png        # Test image (generated)
├── cover_pattern.png         # Test image (generated)
├── cover_nature.png          # Test image (generated)
└── backup_demo.png           # Example backup (created by demo.py)
```

## Advanced Usage

### Python API

```python
from stegvault.crypto import encrypt_data, decrypt_data
from stegvault.stego import embed_payload, extract_payload
from stegvault.utils import serialize_payload, parse_payload

# Encrypt
password_bytes = "MyPassword123".encode('utf-8')
ciphertext, salt, nonce = encrypt_data(password_bytes, "passphrase")

# Serialize
payload = serialize_payload(salt, nonce, ciphertext)

# Embed
seed = int.from_bytes(salt[:4], byteorder="big")
embed_payload("cover.png", payload, seed, "backup.png")

# Extract
payload_extracted = extract_payload("backup.png", len(payload), seed)

# Parse
salt, nonce, ciphertext = parse_payload(payload_extracted)

# Decrypt
recovered = decrypt_data(ciphertext, salt, nonce, "passphrase")
print(recovered.decode('utf-8'))
```

### Capacity Calculation

Image capacity depends on dimensions and mode:

| Image Size | Mode | Capacity | Max Password |
|------------|------|----------|--------------|
| 100x100    | RGB  | 3,750 B  | ~3,686 chars |
| 500x500    | RGB  | 93,750 B | ~93,686 chars|
| 1000x1000  | RGB  | 375,000 B| ~374,936 chars|
| 2000x2000  | RGB  | 1,500,000 B| ~1,499,936 chars|

Formula: `capacity = (width * height * 3) / 8`

## Troubleshooting

### "Image too small for password"
**Solution**: Use a larger image or shorter password. Check capacity with `stegvault check -i image.png`.

### "Decryption failed"
**Solution**: Verify you're using the correct passphrase. Passphrases are case-sensitive.

### "Invalid or corrupted payload"
**Solution**: Ensure the image wasn't edited, recompressed, or converted to JPEG after backup creation.

## Learn More

- [Main README](https://github.com/kalashnikxvxiii-collab/StegVault/blob/main/README.md) - Full project documentation
- [Contributing Guide](https://github.com/kalashnikxvxiii-collab/StegVault/blob/main/CONTRIBUTING.md) - How to contribute
- [Security Policy](https://github.com/kalashnikxvxiii-collab/StegVault/blob/main/SECURITY.md) - Security information
- [Roadmap](https://github.com/kalashnikxvxiii-collab/StegVault/blob/main/ROADMAP.md) - Future features

## License

See [LICENSE](https://github.com/kalashnikxvxiii-collab/StegVault/blob/main/LICENSE) file for details.
