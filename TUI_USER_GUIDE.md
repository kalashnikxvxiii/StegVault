# StegVault Terminal UI (TUI) - User Guide

**Version**: v0.7.8
**Last Updated**: 2025-12-26

Welcome to the StegVault Terminal UI! This guide will help you get started with the full-featured terminal interface for managing your password vaults.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Quick Start](#quick-start)
3. [Keyboard Shortcuts](#keyboard-shortcuts)
4. [Features Guide](#features-guide)
5. [Common Tasks](#common-tasks)
6. [Tips & Best Practices](#tips--best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- StegVault installed (`pip install stegvault`)
- A cover image (PNG or JPEG) for creating vaults

### Installation Verification

```bash
# Check StegVault version
stegvault --version

# Launch TUI
stegvault tui
```

If the TUI launches successfully, you're ready to go! 🎉

---

## Quick Start

### Creating Your First Vault

1. **Launch TUI**:
   ```bash
   stegvault tui
   ```

2. **Press `n` (New Vault)**:
   - Browse and select a cover image (PNG/JPEG)
   - Enter a strong passphrase (you'll need this to unlock the vault!)
   - Fill in your first entry details

3. **Save**: Press `s` to save your vault

4. **Done!** Your encrypted vault is now embedded in the image.

### Opening an Existing Vault

1. **Launch TUI**: `stegvault tui`
2. **Press `o` (Open Vault)**:
   - Browse and select your vault image
   - Enter your passphrase
3. **Manage Entries**: Add, edit, delete, or view your passwords

---

## Keyboard Shortcuts

### Main Menu (Welcome Screen)
- `o` - Open an existing vault
- `n` - Create a new vault
- `━━━` button (bottom-right) - Open settings
- `q` - Quit application

### Vault Management Screen
- `a` - Add new entry
- `e` - Edit selected entry
- `d` - Delete selected entry
- `c` - Copy password to clipboard
- `v` - Toggle password visibility (show/hide)
- `h` - View password history (v0.7.1)
- `s` - Save vault changes
- `/` - Focus search box
- `Escape` - Back to main menu
- `q` - Quit application

### Navigation
- `↑` / `↓` - Navigate entry list
- `Tab` - Switch focus between UI elements
- `Enter` - Select/activate focused element

---

## Features Guide

### 1. Entry Management

#### Adding an Entry
1. Press `a` to open the add entry form
2. Fill in the fields:
   - **Key**: Unique identifier (e.g., "gmail", "github")
   - **Password**: Your password (or use generator button)
   - **Username**: Optional username/email
   - **URL**: Optional website URL
   - **Notes**: Optional additional information
   - **Tags**: Optional comma-separated tags
   - **TOTP Secret**: Optional 2FA secret key
3. Press "Save" or `Enter` to add the entry

#### Editing an Entry
1. Select an entry from the list
2. Press `e` to open the edit form
3. Modify any fields
4. Press "Save" to update

#### Deleting an Entry
1. Select an entry from the list
2. Press `d` to delete
3. Confirm deletion when prompted

### 2. Password Generator

When adding or editing an entry:
1. Click the "Generate Password" button
2. Adjust password length (8-64 characters)
3. Toggle character types (lowercase, uppercase, numbers, symbols)
4. Click "Use Password" to fill the entry form

### 3. Search & Filter

**Live Search**:
- Press `/` to focus the search box
- Type your query
- Entries are filtered in real-time
- Searches across: key, username, URL, notes, tags

**Clear Search**:
- Delete all text in the search box
- Or press `Escape` to exit search mode

### 4. TOTP/2FA Codes

If an entry has a TOTP secret:
- The detail panel shows the current 6-digit code
- Code refreshes automatically every second
- Countdown timer shows remaining validity

**Adding TOTP to an Entry**:
1. Edit the entry
2. Paste your TOTP secret in the "TOTP Secret" field
3. Save the entry

### 5. Password History (v0.7.1)

**View History**:
1. Select an entry
2. Press `h` to open the password history modal
3. View all previous passwords with timestamps and reasons

**Inline Preview**:
- The detail panel shows the last 3 password changes
- Full history available in the modal

**Tracking Changes**:
- Password history is automatically tracked when you update passwords
- Each change includes timestamp and optional reason
- Default: keeps last 5 passwords per entry

### 6. Clipboard Operations

**Copy Password**:
1. Select an entry
2. Press `c` to copy password to clipboard
3. Password is copied (not shown on screen for security)

**Security Note**: Clear clipboard manually after use or use CLI with `--clipboard-timeout` for auto-clear.

### 7. Saving Changes

- Press `s` anytime to save your vault
- Changes are encrypted and written to the image
- Original vault is preserved

### 8. Settings (v0.7.6)

**Access Settings**:
1. Click the `━━━` button in the bottom-right corner of the home screen
2. Settings dialog opens with configuration options

**Update Settings**:
- **Auto-Check Updates**: Toggle automatic checking for new versions at startup
- **Auto-Upgrade**: Toggle automatic installation of new versions when available

**Unsaved Changes Protection**:
- When closing Settings with unsaved changes, you'll see a confirmation dialog:
  - "Save & Exit" - Save changes and close
  - "Don't Save" - Discard changes and close
  - "Cancel" - Return to settings
- Pressing `q` without changes shows the quit confirmation for StegVault
- Pressing `Escape` without changes closes settings directly

**Configuration Persistence**:
- All settings are saved to `~/.stegvault/config.toml` (Unix/macOS)
- Or `%APPDATA%\StegVault\config.toml` (Windows)
- Changes take effect immediately

---

## Common Tasks

### Rotate a Password

1. Open your vault (`o`)
2. Select the entry to update
3. Press `e` to edit
4. Update the password field (or use Password Generator)
5. Save the entry
6. Press `s` to save vault
7. Press `h` to view password history

### Add Multiple Entries Quickly

1. Open vault (`o`)
2. For each new service:
   - Press `a`
   - Fill in key and password
   - Press "Save"
3. When done, press `s` to save vault once

### Find an Entry by Tag

1. Open vault (`o`)
2. Press `/` to focus search
3. Type the tag name
4. View filtered results

---

## Tips & Best Practices

### Security Tips

1. **Use Strong Passphrases**: 4+ random words or 16+ character mix
2. **Backup Vault Images**: Keep multiple copies in different locations
3. **Password Visibility**: Use `v` to toggle, ensure no one is watching
4. **Clipboard Security**: Clear clipboard after copying passwords

### Organization Tips

1. **Use Meaningful Keys**: "gmail-work", "github-personal"
2. **Tag Your Entries**: "work", "personal", "finance", "social"
3. **Add Context in Notes**: Security questions, recovery info
4. **Regular Maintenance**: Review and update passwords quarterly

---

## Troubleshooting

### TUI Won't Launch

```bash
# Check if Textual is installed
pip install textual>=0.47.0

# Reinstall StegVault
pip install --upgrade stegvault
```

### Wrong Passphrase Error

- Double-check passphrase (case-sensitive)
- Try entering manually (no copy-paste)
- Restore from backup if available

### Display Issues

- Use a modern terminal (Windows Terminal, iTerm2, Alacritty)
- Increase terminal window size (minimum 80x24)
- Check terminal color support: `tput colors` (should be 256)

---

## Additional Resources

- **CLI Commands**: `stegvault vault --help`
- **API Documentation**: See `wiki/API-Reference.md`
- **Security Details**: See `wiki/Security-Model.md`
- **Full Documentation**: https://github.com/kalashnikxvxiii/StegVault/wiki

---

## Getting Help

- **Check Wiki**: Comprehensive documentation
- **GitHub Issues**: Report bugs or request features
- **FAQ**: `wiki/FAQ.md`

Thank you for using StegVault! 🔐🖼️
