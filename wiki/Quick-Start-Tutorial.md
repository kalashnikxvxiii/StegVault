# Quick Start Tutorial

Get started with StegVault in 5 minutes! This tutorial walks you through using StegVault's password management features.

**Version**: 0.7.3 (TUI Stable)

## What You'll Learn

This tutorial covers **three interfaces**:
1. **TUI Mode** (recommended) - Interactive terminal UI with full keyboard navigation
2. **CLI Vault Mode** - Command-line for scripting and automation
3. **Single Password Mode** - Quick backup of one master password

## Prerequisites

- StegVault installed (see [Installation Guide](Installation-Guide.md))
- A PNG or JPEG image file
- Basic terminal/command-line familiarity

## Choose Your Interface

### TUI Mode (Recommended for v0.7.0+)

Use TUI mode if you want:
- Visual, interactive experience in your terminal
- Full keyboard navigation (no mouse needed)
- Live TOTP codes with countdown timer
- Password generator with live preview
- Real-time search and filtering

**Launch TUI**:
```bash
$ stegvault tui
```

Then use keyboard shortcuts to navigate (press `h` for help).

### CLI Vault Mode (Recommended for v0.6.1+)

Use vault mode if you want to:
- Store multiple passwords in one image
- Manage credentials like a password manager
- Add TOTP/2FA codes
- Search and filter entries

[Skip to Vault Mode Tutorial](#vault-mode-tutorial)

### Single Password Mode

Use single password mode if you want to:
- Quick backup of one critical password (e.g., master password)
- Simplest possible workflow

[Continue with Single Password Mode](#single-password-mode-tutorial)

---

# Vault Mode Tutorial

## Step 1: Create Your First Vault

Create a new vault with your first password entry:

```bash
$ stegvault vault create -i cover.png -o myvault.png \
  -k gmail \
  -p MyGmailPassword2024 \
  -u user@gmail.com \
  --url https://gmail.com \
  --tags email,personal

Enter vault passphrase: ****************
Confirm passphrase: ****************

✓ Created vault with 1 entry
✓ Saved to: myvault.png
```

## Step 2: Add More Passwords

Add additional entries to your vault:

```bash
$ stegvault vault add -i myvault.png \
  -k github \
  -p GitHubToken123 \
  -u githubuser

Enter passphrase: ****************
✓ Added entry: github
✓ Vault now has 2 entries
```

## Step 3: Retrieve a Password

Get a password from your vault:

```bash
$ stegvault vault get -i myvault.png -k gmail
Enter passphrase: ****************

Key: gmail
Password: MyGmailPassword2024
Username: user@gmail.com
URL: https://gmail.com
Tags: email, personal
```

## Step 4: List All Entries

View all passwords in your vault:

```bash
$ stegvault vault list -i myvault.png
Enter passphrase: ****************

Vault entries (2):
1. gmail (email, personal)
2. github
```

**Next Steps for Vault Mode**:
- Try [Basic Usage Examples](Basic-Usage-Examples.md) for TOTP/2FA
- Learn about [Gallery Mode](Basic-Usage-Examples.md#gallery-mode) for multi-vault management
- See [Headless Mode](Basic-Usage-Examples.md#headless-mode) for automation

---

# Single Password Mode Tutorial

## Step 1: Prepare Your Cover Image

Find or download an image to use as a cover. Requirements:
- **Format**: PNG (recommended) or JPEG
- **Size**: At least 100KB for adequate capacity
- **Resolution**: 800x600 pixels or larger recommended

Example: Download a sample image or use your own photo.

```bash
# Check your image size
ls -lh cover.png
```

## Step 2: Create Your First Backup

Use the `backup` command to encrypt and embed a password:

```bash
stegvault backup -i cover.png -o backup.png
```

You'll be prompted for:
1. **Master Password**: The sensitive password you want to protect (e.g., your vault master password)
2. **Encryption Passphrase**: The key used to encrypt the master password (memorize this!)

### Example Session

```
$ stegvault backup -i cover.png -o backup.png
Master password: ****************
Repeat for confirmation: ****************
Encryption passphrase: ********************
Repeat for confirmation: ********************

Creating encrypted backup...
Image capacity: 76800 bytes
Payload size: 92 bytes (0.12% of capacity)
✓ Encrypted password embedded successfully
Backup saved to: backup.png

⚠ IMPORTANT: Store your passphrase securely!
   Without it, the password cannot be recovered.
```

## Step 3: Verify the Backup

Check that the backup image looks identical to the original:

```bash
# View the backup image - it should look unchanged
# (Use any image viewer)

# Check file size (should be nearly identical to original)
ls -lh cover.png backup.png
```

The backup image contains your encrypted password but is visually indistinguishable from the original.

## Step 4: Test Password Recovery

Recover your password from the backup image:

```bash
stegvault restore -i backup.png
```

Enter your encryption passphrase when prompted:

```
$ stegvault restore -i backup.png
Encryption passphrase: ********************

Extracting encrypted password...
✓ Password recovered successfully

Your password: MySecretPassword123

⚠ Make sure no one is looking at your screen!
```

## Step 5: Secure Storage

Now that you've verified the backup works:

1. **Keep the backup image safe**: Store it on USB drives, cloud storage, or multiple locations
2. **Memorize your passphrase**: Without it, recovery is impossible
3. **Delete the original cover.png** if desired (optional)
4. **Test recovery periodically** to ensure backups remain intact

## Common First-Time Questions

### Can I see the password without special tools?

No. The password is encrypted with modern cryptography (XChaCha20-Poly1305) before embedding. Without the passphrase, it's computationally infeasible to recover.

### Will image compression destroy my backup?

- **PNG**: Safe for any storage (lossless format)
- **JPEG**: Risky - resaving/editing may corrupt the embedded data

Always use PNG for production backups.

### Can I use the same image multiple times?

Each backup should use a fresh cover image. Reusing images may create detectable patterns.

### What happens if I forget my passphrase?

The password is permanently unrecoverable. There is no "password reset" by design - this is zero-knowledge security.

## Next Steps

Now that you've mastered the basics:

**For Vault Mode Users**:
- Explore [Basic Usage Examples](Basic-Usage-Examples.md) (27 examples)
- Learn about TOTP/2FA, Gallery mode, and Headless mode
- See [API Reference](API-Reference.md) for Application Layer controllers

**For All Users**:
- Read [Security Best Practices](Security-Best-Practices.md)
- Learn about [Choosing Cover Images](Choosing-Cover-Images.md)
- Understand the [Security Model](Security-Model.md)
- Review [Architecture Overview](Architecture-Overview.md) for v0.6.1 features

## Quick Reference

### Vault Mode Commands (v0.6.1)
```bash
# Create vault with first entry
stegvault vault create -i cover.png -o vault.png -k mykey -p mypass

# Add entry to vault
stegvault vault add -i vault.png -k newkey -p newpass

# Get password from vault
stegvault vault get -i vault.png -k mykey

# List all entries
stegvault vault list -i vault.png

# TOTP/2FA codes
stegvault vault totp -i vault.png -k mykey
```

### Single Password Mode Commands
```bash
# Create backup
stegvault backup -i cover.png -o backup.png

# Restore password
stegvault restore -i backup.png

# Check image capacity
stegvault check -i cover.png
```

### Help Commands
```bash
stegvault --help
stegvault vault --help
stegvault gallery --help
```

## Troubleshooting

If something goes wrong, see:
- [Troubleshooting Guide](Troubleshooting.md)
- [Common Errors](Common-Errors.md)
- [FAQ](FAQ.md)
