# CLI Commands Reference

Complete command-line reference for StegVault (v0.7.6).

## Table of Contents

- [Global Options](#global-options)
- [Image Capacity](#image-capacity)
- [Single Password Mode](#single-password-mode)
- [Vault Mode](#vault-mode)
- [Gallery Mode](#gallery-mode)
- [Password Generator](#password-generator)
- [Updates](#updates)
- [Terminal UI](#terminal-ui)
- [Exit Codes](#exit-codes)

---

## Global Options

Options available for all commands:

```bash
stegvault --version    # Show version and exit
stegvault --help       # Show help message
```

### Command Help

Get help for any specific command:

```bash
stegvault <command> --help
stegvault vault <subcommand> --help
stegvault gallery <subcommand> --help
```

---

## Image Capacity

Check how much data can be embedded in an image.

### `stegvault check`

**Synopsis**:
```bash
stegvault check -i <image> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Image file to check (PNG or JPEG)

**Options**:
- `--json` - Output results in JSON format (headless mode)

**Output**:
- Image format (PNG/JPEG)
- Dimensions (width x height)
- Color mode (RGB, RGBA, etc.)
- Capacity in bytes
- Maximum password size

**Example**:
```bash
stegvault check -i cover.png
# Output:
# Image: cover.png
# Format: PNG
# Dimensions: 800x600
# Capacity: 18750 bytes
```

**JSON Example**:
```bash
stegvault check -i cover.png --json
# {"status":"success","data":{"image_path":"cover.png","format":"PNG",...}}
```

---

## Single Password Mode

Quick backup and restore of a single master password.

### `stegvault backup`

Create encrypted backup of a single password.

**Synopsis**:
```bash
stegvault backup -i <cover_image> -o <output> [options]
```

**Required Arguments**:
- `-i, --input PATH` - Cover image (PNG or JPEG)
- `-o, --output PATH` - Output backup image

**Options**:
- `--password TEXT` - Master password (will prompt if not provided)
- `--passphrase TEXT` - Encryption passphrase (will prompt if not provided)
- `--passphrase-file PATH` - Read passphrase from file (headless mode)

**Environment Variables**:
- `STEGVAULT_PASSPHRASE` - Fallback passphrase if not provided via flag/file

**Example**:
```bash
stegvault backup -i cover.png -o backup.png
# Prompts for master password and passphrase

stegvault backup -i cover.png -o backup.png --passphrase-file ~/.vault_pass
# Non-interactive with passphrase from file
```

### `stegvault restore`

Restore password from backup image.

**Synopsis**:
```bash
stegvault restore -i <backup_image> [options]
```

**Required Arguments**:
- `-i, --input PATH` - Backup image containing password

**Options**:
- `--passphrase TEXT` - Decryption passphrase (will prompt if not provided)
- `--passphrase-file PATH` - Read passphrase from file (headless mode)

**Environment Variables**:
- `STEGVAULT_PASSPHRASE` - Fallback passphrase if not provided via flag/file

**Example**:
```bash
stegvault restore -i backup.png
# Prompts for passphrase, displays password

stegvault restore -i backup.png --passphrase-file ~/.vault_pass
# Non-interactive restore
```

---

## Vault Mode

Full password manager with multiple credentials.

### `stegvault vault create`

Create new vault with first entry.

**Synopsis**:
```bash
stegvault vault create -i <cover> -o <output> -k <key> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Cover image (PNG or JPEG)
- `-o, --output PATH` - Output vault image
- `-k, --key TEXT` - Entry key/identifier (e.g., "gmail")

**Password Options** (at least one required):
- `-p, --password TEXT` - Password for this entry
- `--generate` - Generate secure random password
- `--prompt` - Prompt for password input (default if no password option)

**Metadata Options**:
- `-u, --username TEXT` - Username or email
- `--url TEXT` - Website URL
- `--notes TEXT` - Free-form notes
- `--tags TEXT` - Comma-separated tags (e.g., "work,email")

**TOTP/2FA Options**:
- `--totp-secret TEXT` - TOTP secret key (base32)
- `--totp-qr PATH` - Scan TOTP QR code from image

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase (will prompt if not provided)
- `--passphrase-file PATH` - Read passphrase from file

**Example**:
```bash
# Create with manual password
stegvault vault create -i cover.png -o vault.png \
  -k gmail -p MyPassword123 -u user@gmail.com \
  --url https://gmail.com --tags email,personal

# Create with generated password
stegvault vault create -i cover.png -o vault.png \
  -k github --generate -u githubuser --tags work

# Create with TOTP
stegvault vault create -i cover.png -o vault.png \
  -k aws --generate --totp-secret "JBSWY3DPEHPK3PXP"
```

### `stegvault vault add`

Add new entry to existing vault.

**Synopsis**:
```bash
stegvault vault add -i <vault> -k <key> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Existing vault image
- `-k, --key TEXT` - Entry key/identifier

**Password Options** (at least one required):
- `-p, --password TEXT` - Password for this entry
- `--generate` - Generate secure random password
- `--prompt` - Prompt for password input (default)

**Metadata Options**:
- `-u, --username TEXT` - Username or email
- `--url TEXT` - Website URL
- `--notes TEXT` - Free-form notes
- `--tags TEXT` - Comma-separated tags

**TOTP/2FA Options**:
- `--totp-secret TEXT` - TOTP secret key (base32)
- `--totp-qr PATH` - Scan TOTP QR code from image

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `-o, --output PATH` - Save to new file (default: overwrites input)

**Example**:
```bash
# Add entry (overwrites vault.png)
stegvault vault add -i vault.png -k github \
  -p GitHubToken123 -u myuser

# Add entry (save to new file)
stegvault vault add -i vault.png -o vault_v2.png \
  -k aws --generate --tags work,cloud

# Non-interactive add
stegvault vault add -i vault.png -k gitlab \
  --password "secret" --passphrase-file ~/.vault_pass
```

### `stegvault vault get`

Retrieve entry from vault.

**Synopsis**:
```bash
stegvault vault get -i <vault> -k <key> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image
- `-k, --key TEXT` - Entry key to retrieve

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `--json` - Output in JSON format (headless mode)
- `--clipboard` - Copy password to clipboard (not printed to stdout)
- `--clipboard-timeout SECONDS` - Auto-clear clipboard after N seconds (default: 30)

**Example**:
```bash
# Display entry
stegvault vault get -i vault.png -k gmail
# Output: Key: gmail, Password: ..., Username: ..., etc.

# Copy to clipboard
stegvault vault get -i vault.png -k gmail --clipboard
# Password copied (clears after 30s)

# JSON output for automation
stegvault vault get -i vault.png -k gmail --json --passphrase-file ~/.pass
# {"status":"success","data":{"key":"gmail","password":"...","username":"..."}}
```

### `stegvault vault list`

List all entries in vault.

**Synopsis**:
```bash
stegvault vault list -i <vault> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `--json` - Output in JSON format (headless mode)
- `--verbose, -v` - Show full details for each entry

**Example**:
```bash
# List entry keys
stegvault vault list -i vault.png
# Output: Vault contains 3 entries: 1. gmail 2. github 3. aws

# Verbose output (shows usernames, URLs, tags)
stegvault vault list -i vault.png --verbose

# JSON output
stegvault vault list -i vault.png --json --passphrase-file ~/.pass
# {"status":"success","data":{"entries":[...],"entry_count":3}}
```

### `stegvault vault update`

Update existing entry in vault.

**Synopsis**:
```bash
stegvault vault update -i <vault> -k <key> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image
- `-k, --key TEXT` - Entry key to update

**Update Fields** (at least one required):
- `-p, --password TEXT` - New password
- `--generate` - Generate new random password
- `-u, --username TEXT` - New username
- `--url TEXT` - New URL
- `--notes TEXT` - New notes
- `--tags TEXT` - New tags (replaces existing)
- `--totp-secret TEXT` - New TOTP secret
- `--clear-totp` - Remove TOTP secret

**Password History Options**:
- `--password-change-reason TEXT` - Reason for password change (tracked in history)

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `-o, --output PATH` - Save to new file (default: overwrites input)

**Example**:
```bash
# Update password
stegvault vault update -i vault.png -k gmail --password NewPassword123

# Update with history tracking
stegvault vault update -i vault.png -k gmail \
  --generate --password-change-reason "scheduled rotation"

# Update multiple fields
stegvault vault update -i vault.png -k github \
  --username newuser --url https://github.com/newuser \
  --tags work,dev,active

# Remove TOTP
stegvault vault update -i vault.png -k oldservice --clear-totp
```

### `stegvault vault delete`

Delete entry from vault.

**Synopsis**:
```bash
stegvault vault delete -i <vault> -k <key> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image
- `-k, --key TEXT` - Entry key to delete

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `-o, --output PATH` - Save to new file (default: overwrites input)
- `--no-confirm` - Skip confirmation prompt (for scripts)

**Example**:
```bash
# Delete with confirmation
stegvault vault delete -i vault.png -k oldservice
# Prompts: Are you sure? [y/N]

# Delete without confirmation (automation)
stegvault vault delete -i vault.png -k oldservice --no-confirm --passphrase-file ~/.pass
```

### `stegvault vault export`

Export vault to JSON file.

**Synopsis**:
```bash
stegvault vault export -i <vault> -o <json_file> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image
- `-o, --output PATH` - Output JSON file

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `--pretty` - Pretty-print JSON with indentation
- `--redact` - Redact passwords (safe for version control)

**Security Warning**:
Exported JSON contains plaintext passwords unless `--redact` is used!

**Example**:
```bash
# Export with readable formatting
stegvault vault export -i vault.png -o backup.json --pretty

# Export with passwords redacted
stegvault vault export -i vault.png -o safe-backup.json --redact

# Automated export
stegvault vault export -i vault.png -o backup.json --passphrase-file ~/.pass
```

### `stegvault vault import`

Import vault from JSON file.

**Synopsis**:
```bash
stegvault vault import -i <cover> -o <output> --json-file <json> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Cover image (PNG or JPEG)
- `-o, --output PATH` - Output vault image
- `--json-file PATH` - JSON file to import

**Passphrase Options**:
- `--passphrase TEXT` - Passphrase for new vault
- `--passphrase-file PATH` - Read passphrase from file

**Example**:
```bash
# Import JSON to new vault
stegvault vault import -i cover.png -o restored.png --json-file backup.json

# Import with passphrase file
stegvault vault import -i cover.png -o restored.png \
  --json-file backup.json --passphrase-file ~/.pass
```

### `stegvault vault totp`

Generate TOTP/2FA code for entry.

**Synopsis**:
```bash
stegvault vault totp -i <vault> -k <key> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image
- `-k, --key TEXT` - Entry key with TOTP secret

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `--qr` - Display QR code (for authenticator app setup)
- `--json` - Output in JSON format

**Example**:
```bash
# Generate TOTP code
stegvault vault totp -i vault.png -k github
# Output: Current TOTP code: 123456 (valid for 25 seconds)

# Show QR code
stegvault vault totp -i vault.png -k github --qr
# Displays ASCII QR code for scanning

# JSON output
stegvault vault totp -i vault.png -k github --json
# {"status":"success","data":{"code":"123456","valid_for":25}}
```

### `stegvault vault search`

Search vault entries by keyword.

**Synopsis**:
```bash
stegvault vault search -i <vault> -q <query> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image
- `-q, --query TEXT` - Search query

**Search Options**:
- `--fields FIELD` - Search specific fields only (multiple allowed)
  - Valid fields: `key`, `username`, `url`, `notes`, `tags`
  - Example: `--fields key --fields username`

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `--json` - Output in JSON format

**Example**:
```bash
# Search all fields
stegvault vault search -i vault.png -q "github"
# Output: Found 2 entries: github, github-work

# Search specific fields
stegvault vault search -i vault.png -q "email" --fields notes --fields tags

# JSON output
stegvault vault search -i vault.png -q "work" --json
# {"status":"success","data":{"matches":["github","aws"],"match_count":2}}
```

### `stegvault vault filter`

Filter vault entries by tags or URL.

**Synopsis**:
```bash
stegvault vault filter -i <vault> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image

**Filter Options** (at least one required):
- `--tag TEXT` - Filter by tag (multiple allowed)
- `--url TEXT` - Filter by URL pattern
- `--match-all` - Require ALL tags (default: ANY tag)

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `--json` - Output in JSON format

**Example**:
```bash
# Filter by single tag
stegvault vault filter -i vault.png --tag work
# Output: Entries with tag 'work': github, aws, slack

# Filter by multiple tags (OR logic)
stegvault vault filter -i vault.png --tag email --tag personal

# Filter by multiple tags (AND logic)
stegvault vault filter -i vault.png --tag work --tag email --match-all

# Filter by URL pattern
stegvault vault filter -i vault.png --url github.com
# Matches: github, github-work
```

### `stegvault vault history`

View password history for an entry.

**Synopsis**:
```bash
stegvault vault history -i <vault> <key> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image
- `<key>` - Entry key to view history for

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `--json` - Output in JSON format

**Example**:
```bash
# View password history
stegvault vault history -i vault.png gmail
# Output:
# Current password: MyNewSecureP@ss2024
# History (2 entries):
#   1. OldPassword123 (2025-12-02, reason: scheduled rotation)
#   2. VeryOldPass456 (2025-11-15)

# JSON output
stegvault vault history -i vault.png gmail --json
# {"status":"success","data":{"current_password":"...","history":[...]}}
```

### `stegvault vault history-clear`

Clear password history for an entry.

**Synopsis**:
```bash
stegvault vault history-clear -i <vault> <key> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image
- `<key>` - Entry key to clear history for

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Output Options**:
- `-o, --output PATH` - Save to new file (default: overwrites input)
- `--no-confirm` - Skip confirmation prompt

**Example**:
```bash
# Clear history with confirmation
stegvault vault history-clear -i vault.png gmail
# Prompts: This will clear 2 historical password(s) for 'gmail'. Are you sure? [y/N]

# Clear history without confirmation
stegvault vault history-clear -i vault.png gmail --no-confirm --passphrase-file ~/.pass
```

---

## Gallery Mode

Manage multiple vaults in one gallery database.

### `stegvault gallery init`

Initialize new gallery database.

**Synopsis**:
```bash
stegvault gallery init [options]
```

**Options**:
- `-d, --database PATH` - Gallery database path (default: `~/.stegvault/gallery.db`)
- `--name TEXT` - Gallery name
- `--description TEXT` - Gallery description

**Example**:
```bash
# Create default gallery
stegvault gallery init

# Create custom gallery
stegvault gallery init -d ~/my-gallery.db \
  --name "Work Vaults" \
  --description "Corporate password vaults"
```

### `stegvault gallery add`

Add vault to gallery.

**Synopsis**:
```bash
stegvault gallery add -i <vault> [options]
```

**Required Arguments**:
- `-i, --image PATH` - Vault image to add

**Gallery Options**:
- `-d, --database PATH` - Gallery database (default: `~/.stegvault/gallery.db`)
- `--name TEXT` - Vault alias/name in gallery
- `--tags TEXT` - Comma-separated tags

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase (for caching entries)
- `--passphrase-file PATH` - Read passphrase from file

**Example**:
```bash
# Add vault with defaults
stegvault gallery add -i vault.png

# Add vault with alias and tags
stegvault gallery add -i work-vault.png \
  --name "Work Passwords" \
  --tags work,corporate
```

### `stegvault gallery list`

List all vaults in gallery.

**Synopsis**:
```bash
stegvault gallery list [options]
```

**Gallery Options**:
- `-d, --database PATH` - Gallery database (default: `~/.stegvault/gallery.db`)

**Output Options**:
- `--json` - Output in JSON format
- `--verbose, -v` - Show detailed information

**Example**:
```bash
# List vaults
stegvault gallery list
# Output:
# 2 vault(s) in gallery:
# 1. Personal (3 entries, tags: personal)
# 2. Work (5 entries, tags: work)

# Verbose listing
stegvault gallery list --verbose
# Shows full paths, last accessed times, etc.
```

### `stegvault gallery remove`

Remove vault from gallery.

**Synopsis**:
```bash
stegvault gallery remove <name> [options]
```

**Required Arguments**:
- `<name>` - Vault name/alias to remove

**Gallery Options**:
- `-d, --database PATH` - Gallery database (default: `~/.stegvault/gallery.db`)
- `--no-confirm` - Skip confirmation prompt

**Note**: This removes the vault from gallery metadata only. The vault image file is NOT deleted.

**Example**:
```bash
# Remove with confirmation
stegvault gallery remove "Old Vault"
# Prompts: Remove vault 'Old Vault' from gallery? [y/N]

# Remove without confirmation
stegvault gallery remove "Old Vault" --no-confirm
```

### `stegvault gallery refresh`

Refresh vault metadata in gallery.

**Synopsis**:
```bash
stegvault gallery refresh <name> [options]
```

**Required Arguments**:
- `<name>` - Vault name/alias to refresh

**Gallery Options**:
- `-d, --database PATH` - Gallery database (default: `~/.stegvault/gallery.db`)

**Passphrase Options**:
- `--passphrase TEXT` - Vault passphrase
- `--passphrase-file PATH` - Read passphrase from file

**Use Case**: Run this after modifying a vault to update the cached entry list.

**Example**:
```bash
# Refresh vault metadata
stegvault gallery refresh "Work Passwords"
# Prompts for passphrase, updates cached entries
```

### `stegvault gallery search`

Search across all vaults in gallery.

**Synopsis**:
```bash
stegvault gallery search -q <query> [options]
```

**Required Arguments**:
- `-q, --query TEXT` - Search query

**Gallery Options**:
- `-d, --database PATH` - Gallery database (default: `~/.stegvault/gallery.db`)
- `--vault TEXT` - Search in specific vault only

**Search Options**:
- `--tag TEXT` - Filter by tag
- `--url TEXT` - Filter by URL pattern

**Output Options**:
- `--json` - Output in JSON format

**Example**:
```bash
# Search all vaults
stegvault gallery search -q "github"
# Output:
# Found 2 entries:
# [Personal] github
# [Work] github-corp

# Search in specific vault
stegvault gallery search -q "email" --vault "Personal"

# Search by tag
stegvault gallery search --tag work --tag email
```

---

## Password Generator

Generate cryptographically secure passwords.

### `stegvault generate`

Generate random password.

**Synopsis**:
```bash
stegvault generate [options]
```

**Options**:
- `-l, --length INTEGER` - Password length (default: 16, range: 8-128)
- `--no-uppercase` - Exclude uppercase letters
- `--no-lowercase` - Exclude lowercase letters
- `--no-numbers` - Exclude numbers
- `--no-symbols` - Exclude symbols
- `--no-ambiguous` - Exclude ambiguous characters (0, O, 1, l, I)
- `--custom-charset TEXT` - Use custom character set

**Example**:
```bash
# Generate default 16-char password
stegvault generate
# Output: Kp9@mX4nQ!rT2vB#

# Generate 32-char password
stegvault generate -l 32

# Alphanumeric only (no symbols)
stegvault generate -l 24 --no-symbols

# Numbers and symbols only
stegvault generate -l 20 --no-uppercase --no-lowercase

# Custom character set
stegvault generate -l 16 --custom-charset "ABCDEF0123456789"
```

---

## Updates

Check and install StegVault updates (v0.7.6).

### `stegvault updates check`

Check for new versions on PyPI.

**Synopsis**:
```bash
stegvault updates check [options]
```

**Options**:
- `--check-only` - Only check, don't prompt to upgrade
- `--force` - Bypass cache, force fresh check

**Output**:
- Current installed version
- Latest available version on PyPI
- Update status (up-to-date or available)
- Changelog preview

**Example**:
```bash
# Check for updates
stegvault updates check
# Output:
# Current version: 0.7.5
# Latest version: 0.7.6
# Update available!
# Upgrade? [y/N]

# Check only (no prompt)
stegvault updates check --check-only
```

### `stegvault updates upgrade`

Install latest version from PyPI.

**Synopsis**:
```bash
stegvault updates upgrade [options]
```

**Options**:
- `-y, --yes` - Auto-confirm upgrade (no prompt)
- `--force` - Bypass cache, force fresh check

**Requirements**:
- Requires `pip` installation method (not source/portable)

**Example**:
```bash
# Upgrade with confirmation
stegvault updates upgrade
# Prompts: Upgrade from 0.7.5 to 0.7.6? [y/N]

# Auto-upgrade (no prompt)
stegvault updates upgrade -y
```

---

## Terminal UI

Launch the Terminal User Interface (v0.7.0).

### `stegvault tui`

Launch interactive TUI.

**Synopsis**:
```bash
stegvault tui
```

**Features**:
- Visual interface in terminal
- Full keyboard navigation
- Entry list with live search/filter
- TOTP codes with auto-refresh countdown
- Built-in password generator
- Full CRUD operations
- Password history viewer

**Keyboard Shortcuts**:
- `o` - Open vault
- `n` - New vault
- `h` - View password history
- `a` - Add entry
- `e` - Edit entry
- `d` - Delete entry
- `c` - Copy password to clipboard
- `v` - Toggle password visibility
- `s` - Save vault
- `/` - Search entries
- `f` - Favorite current folder
- `Ctrl+f` - Quick access favorites
- `Escape` - Back/Cancel
- `q` - Quit

**Example**:
```bash
# Launch TUI
stegvault tui
```

See [TUI Guide](https://github.com/kalashnikxvxiii/StegVault/blob/main/TUI_USER_GUIDE.md) for detailed usage.

---

## Exit Codes

StegVault uses standardized exit codes for automation:

| Code | Meaning | Examples |
|------|---------|----------|
| **0** | Success | Command completed successfully |
| **1** | Runtime Error | Wrong passphrase, file not found, decryption failed |
| **2** | Validation Error | Invalid input, empty passphrase file, missing arguments |

**Usage in Scripts**:

```bash
stegvault vault get vault.png -k gmail --json --passphrase-file ~/.pass
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Success"
elif [ $EXIT_CODE -eq 1 ]; then
    echo "Runtime error (wrong passphrase?)"
elif [ $EXIT_CODE -eq 2 ]; then
    echo "Validation error (bad arguments?)"
fi
```

---

## See Also

- [Quick Start Tutorial](https://github.com/kalashnikxvxiii/StegVault/wiki/Quick-Start-Tutorial) - Get started in 5 minutes
- [Basic Usage Examples](https://github.com/kalashnikxvxiii/StegVault/wiki/Basic-Usage-Examples) - 27 practical examples
- [Headless Mode Guide](https://github.com/kalashnikxvxiii/StegVault/wiki/Headless-Mode-Guide) - Automation and CI/CD
- [TUI Guide](https://github.com/kalashnikxvxiii/StegVault/blob/main/TUI_USER_GUIDE.md) - Terminal UI reference
- [Security Best Practices](https://github.com/kalashnikxvxiii/StegVault/wiki/Security-Best-Practices) - Usage guidelines
- [Troubleshooting](https://github.com/kalashnikxvxiii/StegVault/wiki/Troubleshooting) - Common issues

---

**Version**: 0.7.6
**Last Updated**: 2025-12-18
