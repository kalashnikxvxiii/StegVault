# Headless Mode Guide

Complete guide to automation-friendly features in StegVault (v0.6.0+).

## Table of Contents

- [Overview](#overview)
- [JSON Output](#json-output)
- [Passphrase Handling](#passphrase-handling)
- [Exit Codes](#exit-codes)
- [CI/CD Integration](#cicd-integration)
- [Automation Examples](#automation-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Headless Mode** enables non-interactive, automation-friendly usage of StegVault:

- 🤖 **JSON Output** - Machine-readable structured data
- 📄 **Passphrase Files** - Non-interactive authentication
- 🌍 **Environment Variables** - Zero-interaction operation
- 🔢 **Exit Codes** - Standard codes for error handling
- ⚙️ **Priority System** - Flexible passphrase sources

### Use Cases

- **CI/CD Pipelines** - Inject secrets into deployment workflows
- **Backup Scripts** - Automated vault backups and migrations
- **Server Management** - Retrieve credentials for automation
- **Monitoring** - Automated checks and alerting
- **Integration Testing** - Programmatic vault operations

### Requirements

- StegVault v0.6.0 or later
- `jq` (recommended) for JSON parsing in scripts

---

## JSON Output

All critical commands support `--json` flag for machine-readable output.

### Supported Commands

| Command | JSON Support |
|---------|--------------|
| `stegvault check` | ✅ Yes |
| `stegvault vault get` | ✅ Yes |
| `stegvault vault list` | ✅ Yes |
| `stegvault vault totp` | ✅ Yes |
| `stegvault vault search` | ✅ Yes |
| `stegvault vault filter` | ✅ Yes |
| `stegvault vault history` | ✅ Yes |
| `stegvault gallery list` | ✅ Yes |
| `stegvault gallery search` | ✅ Yes |

### JSON Structure

All JSON responses follow this structure:

#### Success Response

```json
{
  "status": "success",
  "data": {
    ... command-specific data ...
  }
}
```

#### Error Response

```json
{
  "status": "error",
  "error": "Human-readable error message",
  "error_type": "ValidationError|RuntimeError"
}
```

### Example: Check Image Capacity

**Command**:
```bash
stegvault check -i cover.png --json
```

**Output**:
```json
{
  "status": "success",
  "data": {
    "image_path": "cover.png",
    "format": "PNG",
    "mode": "RGB",
    "size": {
      "width": 800,
      "height": 600
    },
    "capacity": 18750,
    "max_password_size": 18686
  }
}
```

### Example: Get Vault Entry

**Command**:
```bash
stegvault vault get vault.png -k gmail --passphrase mypass --json
```

**Output**:
```json
{
  "status": "success",
  "data": {
    "key": "gmail",
    "password": "MyGmailPass2024",
    "username": "user@gmail.com",
    "url": "https://gmail.com",
    "notes": "Personal email",
    "tags": ["email", "personal"],
    "has_totp": true,
    "created": "2025-01-10T14:30:00Z",
    "modified": "2025-01-15T10:15:00Z",
    "accessed": "2025-01-18T09:45:00Z"
  }
}
```

### Example: List Vault Entries

**Command**:
```bash
stegvault vault list vault.png --passphrase mypass --json
```

**Output**:
```json
{
  "status": "success",
  "data": {
    "entries": [
      {
        "key": "gmail",
        "username": "user@gmail.com",
        "url": "https://gmail.com",
        "tags": ["email", "personal"],
        "has_totp": true
      },
      {
        "key": "github",
        "username": "myuser",
        "url": "https://github.com",
        "tags": ["work", "dev"],
        "has_totp": false
      }
    ],
    "entry_count": 2
  }
}
```

### Parsing JSON with `jq`

**Extract specific field**:
```bash
# Get password only
PASSWORD=$(stegvault vault get vault.png -k gmail --passphrase-file ~/.pass --json | jq -r '.data.password')
echo "Password: $PASSWORD"
```

**Check status**:
```bash
# Check if command succeeded
STATUS=$(stegvault vault get vault.png -k gmail --json | jq -r '.status')
if [ "$STATUS" == "success" ]; then
    echo "Success!"
fi
```

**Extract array elements**:
```bash
# List all entry keys
KEYS=$(stegvault vault list vault.png --passphrase-file ~/.pass --json | jq -r '.data.entries[].key')
echo "$KEYS"
```

---

## Passphrase Handling

Headless mode provides three non-interactive passphrase options.

### Priority System

StegVault uses this priority order for passphrases (highest to lowest):

1. **`--passphrase` flag** (explicit command-line argument)
2. **`--passphrase-file` flag** (read from secure file)
3. **`STEGVAULT_PASSPHRASE` environment variable** (fallback)
4. **Interactive prompt** (if none of above)

### Method 1: Explicit Passphrase (Least Secure)

Pass passphrase directly via command-line argument.

**⚠️ WARNING**: Passphrase visible in shell history and process list!

```bash
stegvault vault get vault.png -k gmail --passphrase "MySecretPass"
```

**Use Case**: Quick testing only (never use in production).

### Method 2: Passphrase File (Recommended)

Store passphrase in a secure file with restrictive permissions.

**Setup**:
```bash
# Create passphrase file
echo "MySecretPassphrase" > ~/.vault_pass

# Set restrictive permissions (owner read-only)
chmod 600 ~/.vault_pass

# Verify permissions
ls -la ~/.vault_pass
# Output: -rw------- 1 user user 19 Dec 18 10:00 .vault_pass
```

**Usage**:
```bash
stegvault vault get vault.png -k gmail --passphrase-file ~/.vault_pass --json
```

**Security Benefits**:
- Not visible in shell history
- Not visible in process list (`ps aux`)
- File permissions prevent unauthorized access
- Can be stored in encrypted filesystems

**Best Practices**:
- Use `600` (owner-only) permissions
- Store in user home directory (`~/.vault_pass`)
- Never commit to version control
- Use encrypted disk/filesystem
- Rotate passphrases regularly

### Method 3: Environment Variable

Set `STEGVAULT_PASSPHRASE` for zero-interaction operation.

**Setup**:
```bash
# Export passphrase as environment variable
export STEGVAULT_PASSPHRASE="MySecretPassphrase"

# Verify (for testing only)
echo $STEGVAULT_PASSPHRASE
```

**Usage**:
```bash
# No passphrase prompt - automatically uses env var
stegvault vault get vault.png -k gmail --json
stegvault vault list vault.png --json
```

**Persistence** (add to shell profile):
```bash
# ~/.bashrc or ~/.zshrc
export STEGVAULT_PASSPHRASE="MySecretPassphrase"
```

**Security Considerations**:
- ✅ Not visible in shell history
- ✅ Not visible in process list
- ⚠️ Visible in environment variables (`env`, `printenv`)
- ⚠️ Inherited by child processes
- ⚠️ May leak in crash dumps/logs

**Best Practices**:
- Use for personal workstations only
- Clear after use: `unset STEGVAULT_PASSPHRASE`
- Prefer passphrase files for production
- Never hardcode in scripts (read from secure file instead)

### Priority Override Example

```bash
# Explicit passphrase overrides everything
stegvault vault get vault.png -k gmail --passphrase "explicit" --json

# File overrides environment variable
export STEGVAULT_PASSPHRASE="env-pass"
stegvault vault get vault.png -k gmail --passphrase-file ~/.pass --json
# Uses ~/.pass, not $STEGVAULT_PASSPHRASE

# Environment variable used if no explicit/file
export STEGVAULT_PASSPHRASE="fallback"
stegvault vault get vault.png -k gmail --json
# Uses $STEGVAULT_PASSPHRASE
```

---

## Exit Codes

StegVault uses standardized exit codes for automation error handling.

### Exit Code Values

| Code | Status | Description | Examples |
|------|--------|-------------|----------|
| **0** | Success | Command completed successfully | Password retrieved, vault created |
| **1** | Runtime Error | Execution failed | Wrong passphrase, file not found, decryption error |
| **2** | Validation Error | Invalid input | Empty passphrase file, missing arguments |

### Checking Exit Codes

**Bash/Shell**:
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

**Python**:
```python
import subprocess
import json

result = subprocess.run(
    ["stegvault", "vault", "get", "vault.png", "-k", "gmail", "--json", "--passphrase-file", "~/.pass"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    data = json.loads(result.stdout)
    print(f"Password: {data['data']['password']}")
elif result.returncode == 1:
    print("Runtime error:", result.stderr)
elif result.returncode == 2:
    print("Validation error:", result.stderr)
```

### Common Exit Code Scenarios

#### Exit Code 0 (Success)

```bash
$ stegvault vault get vault.png -k gmail --passphrase-file ~/.pass --json
{"status":"success","data":{...}}
$ echo $?
0
```

#### Exit Code 1 (Runtime Error)

```bash
# Wrong passphrase
$ stegvault vault get vault.png -k gmail --passphrase "wrong" --json
{"status":"error","error":"Decryption failed: Invalid passphrase","error_type":"RuntimeError"}
$ echo $?
1

# File not found
$ stegvault vault get nonexistent.png -k gmail --json
{"status":"error","error":"File not found: nonexistent.png","error_type":"RuntimeError"}
$ echo $?
1
```

#### Exit Code 2 (Validation Error)

```bash
# Empty passphrase file
$ touch empty.txt
$ stegvault vault get vault.png -k gmail --passphrase-file empty.txt --json
{"status":"error","error":"Passphrase file is empty","error_type":"ValidationError"}
$ echo $?
2

# Missing required argument
$ stegvault vault get vault.png --json
Error: Missing option '-k' / '--key'
$ echo $?
2
```

---

## CI/CD Integration

Integrate StegVault into automated deployment pipelines.

### GitHub Actions

#### Example 1: Retrieve Database Password

```yaml
# .github/workflows/deploy.yml
name: Deploy Application

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Install StegVault
        run: pip install stegvault

      - name: Download vault image
        run: |
          # Retrieve vault from secure storage
          aws s3 cp s3://my-secrets/vault.png vault.png

      - name: Retrieve database password
        run: |
          # Extract password using headless mode
          PASSWORD=$(stegvault vault get vault.png \
            -k db_password \
            --passphrase-file <(echo "${{ secrets.VAULT_PASSPHRASE }}") \
            --json | jq -r '.data.password')

          # Mask password in logs
          echo "::add-mask::$PASSWORD"

          # Export to environment
          echo "DB_PASSWORD=$PASSWORD" >> $GITHUB_ENV

      - name: Deploy application
        run: ./deploy.sh
        env:
          DB_PASSWORD: ${{ env.DB_PASSWORD }}
```

#### Example 2: Rotate Secrets

```yaml
# .github/workflows/rotate-secrets.yml
name: Rotate Secrets

on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly

jobs:
  rotate:
    runs-on: ubuntu-latest
    steps:
      - name: Install StegVault
        run: pip install stegvault

      - name: Download vault
        run: aws s3 cp s3://my-secrets/vault.png vault.png

      - name: Generate new password
        run: |
          NEW_PASS=$(stegvault generate -l 32 --no-ambiguous)
          echo "NEW_PASSWORD=$NEW_PASS" >> $GITHUB_ENV

      - name: Update vault
        run: |
          stegvault vault update vault.png \
            -k api_key \
            --password "${{ env.NEW_PASSWORD }}" \
            --password-change-reason "scheduled rotation" \
            --passphrase-file <(echo "${{ secrets.VAULT_PASSPHRASE }}")

      - name: Upload updated vault
        run: aws s3 cp vault.png s3://my-secrets/vault.png
```

### GitLab CI

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  image: python:3.11
  before_script:
    - pip install stegvault jq
  script:
    - echo "$VAULT_PASSPHRASE" > /tmp/vault_pass
    - chmod 600 /tmp/vault_pass

    # Retrieve credentials
    - |
      DB_HOST=$(stegvault vault get vault.png -k db_host \
        --passphrase-file /tmp/vault_pass --json | jq -r '.data.password')
      DB_USER=$(stegvault vault get vault.png -k db_user \
        --passphrase-file /tmp/vault_pass --json | jq -r '.data.username')
      DB_PASS=$(stegvault vault get vault.png -k db_pass \
        --passphrase-file /tmp/vault_pass --json | jq -r '.data.password')

    # Deploy
    - ./deploy.sh "$DB_HOST" "$DB_USER" "$DB_PASS"
  after_script:
    - rm -f /tmp/vault_pass
  only:
    - main
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    stages {
        stage('Deploy') {
            steps {
                script {
                    // Install StegVault
                    sh 'pip install stegvault'

                    // Create passphrase file from Jenkins secret
                    withCredentials([string(credentialsId: 'vault-passphrase', variable: 'VAULT_PASS')]) {
                        writeFile file: '/tmp/vault_pass', text: env.VAULT_PASS
                        sh 'chmod 600 /tmp/vault_pass'
                    }

                    // Retrieve password
                    def password = sh(
                        script: """
                            stegvault vault get vault.png -k db_password \
                                --passphrase-file /tmp/vault_pass \
                                --json | jq -r '.data.password'
                        """,
                        returnStdout: true
                    ).trim()

                    // Use password
                    sh "./deploy.sh '${password}'"

                    // Cleanup
                    sh 'rm -f /tmp/vault_pass'
                }
            }
        }
    }
}
```

---

## Automation Examples

### Example 1: Automated Backup Script

```bash
#!/bin/bash
# backup_passwords.sh - Automated vault backup

set -e  # Exit on error

# Configuration
VAULT_FILE="vault.png"
VAULT_PASS_FILE="$HOME/.vault_pass"
BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Verify passphrase file exists
if [ ! -f "$VAULT_PASS_FILE" ]; then
    echo "Error: Passphrase file not found: $VAULT_PASS_FILE"
    exit 1
fi

# Export vault to JSON
echo "Exporting vault to JSON..."
stegvault vault export "$VAULT_FILE" \
    -o "$BACKUP_DIR/vault_$DATE.json" \
    --passphrase-file "$VAULT_PASS_FILE" \
    --pretty

if [ $? -eq 0 ]; then
    echo "Backup created: $BACKUP_DIR/vault_$DATE.json"

    # Get vault statistics
    STATS=$(stegvault vault list "$VAULT_FILE" \
        --passphrase-file "$VAULT_PASS_FILE" \
        --json)

    ENTRY_COUNT=$(echo "$STATS" | jq -r '.data.entry_count')
    echo "Backed up $ENTRY_COUNT entries"

    # Compress backup
    gzip "$BACKUP_DIR/vault_$DATE.json"
    echo "Compressed: $BACKUP_DIR/vault_$DATE.json.gz"

    # Delete backups older than 30 days
    find "$BACKUP_DIR" -name "vault_*.json.gz" -mtime +30 -delete
    echo "Cleanup: Deleted backups older than 30 days"
else
    echo "Backup failed"
    exit 1
fi
```

### Example 2: Password Rotation Script

```bash
#!/bin/bash
# rotate_password.sh - Programmatic password rotation

set -e

VAULT_FILE="vault.png"
SERVICE="$1"
VAULT_PASS_FILE="$HOME/.vault_pass"

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service_key>"
    exit 2
fi

# Generate new password
echo "Generating new password..."
NEW_PASSWORD=$(stegvault generate -l 32 --no-ambiguous)

# Retrieve current entry info
echo "Retrieving current entry info..."
INFO=$(stegvault vault get "$VAULT_FILE" \
    -k "$SERVICE" \
    --passphrase-file "$VAULT_PASS_FILE" \
    --json)

if [ $? -ne 0 ]; then
    echo "Error: Failed to retrieve entry '$SERVICE'"
    exit 1
fi

USERNAME=$(echo "$INFO" | jq -r '.data.username')
URL=$(echo "$INFO" | jq -r '.data.url')

echo "Service: $SERVICE"
echo "Username: $USERNAME"
echo "URL: $URL"

# Update password via external API (example)
echo "Updating password on remote service..."
curl -s -X POST "$URL/api/update-password" \
    -u "$USERNAME:$NEW_PASSWORD" \
    -H "Content-Type: application/json" \
    -d '{"new_password":"'"$NEW_PASSWORD"'"}'

if [ $? -eq 0 ]; then
    echo "Remote password updated successfully"

    # Update vault
    echo "Updating vault..."
    stegvault vault update "$VAULT_FILE" \
        -k "$SERVICE" \
        --password "$NEW_PASSWORD" \
        --password-change-reason "automated rotation $(date +%Y-%m-%d)" \
        --passphrase-file "$VAULT_PASS_FILE"

    if [ $? -eq 0 ]; then
        echo "Vault updated successfully"
        echo "Password rotation complete for '$SERVICE'"
    else
        echo "Error: Failed to update vault"
        exit 1
    fi
else
    echo "Error: Failed to update remote password"
    exit 1
fi
```

### Example 3: Monitoring Script

```bash
#!/bin/bash
# check_vault.sh - Monitor vault integrity

set -e

VAULT_FILE="vault.png"
VAULT_PASS_FILE="$HOME/.vault_pass"
ALERT_EMAIL="admin@example.com"

# Check vault integrity
echo "Checking vault integrity..."
RESULT=$(stegvault vault list "$VAULT_FILE" \
    --passphrase-file "$VAULT_PASS_FILE" \
    --json 2>&1)

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    ENTRY_COUNT=$(echo "$RESULT" | jq -r '.data.entry_count')
    echo "Vault OK: $ENTRY_COUNT entries"
    exit 0
elif [ $EXIT_CODE -eq 1 ]; then
    # Runtime error - vault corrupted or wrong passphrase
    ERROR_MSG=$(echo "$RESULT" | jq -r '.error')
    echo "ERROR: $ERROR_MSG"

    # Send alert
    echo "Vault integrity check failed: $ERROR_MSG" | \
        mail -s "ALERT: StegVault Integrity Failure" "$ALERT_EMAIL"

    exit 1
elif [ $EXIT_CODE -eq 2 ]; then
    # Validation error - configuration issue
    ERROR_MSG=$(echo "$RESULT" | jq -r '.error')
    echo "VALIDATION ERROR: $ERROR_MSG"

    # Send alert
    echo "Vault configuration error: $ERROR_MSG" | \
        mail -s "ALERT: StegVault Configuration Issue" "$ALERT_EMAIL"

    exit 2
fi
```

### Example 4: Multi-Vault Sync

```bash
#!/bin/bash
# sync_vaults.sh - Sync vaults across devices

set -e

VAULT_PASS_FILE="$HOME/.vault_pass"
SYNC_DIR="$HOME/Dropbox/vault-sync"
DATE=$(date +%Y%m%d)

# Export local vault
echo "Exporting local vault..."
stegvault vault export local-vault.png \
    -o "$SYNC_DIR/sync_$DATE.json" \
    --passphrase-file "$VAULT_PASS_FILE" \
    --pretty

if [ $? -eq 0 ]; then
    echo "Local vault exported to: $SYNC_DIR/sync_$DATE.json"

    # Verify Dropbox sync completed
    sleep 5

    # On remote device: import synced vault
    # (This part runs on Device 2)
    # stegvault vault import remote-vault.png \
    #     --json-file "$SYNC_DIR/sync_$DATE.json" \
    #     --passphrase-file "$VAULT_PASS_FILE"

    echo "Sync complete"
else
    echo "Export failed"
    exit 1
fi
```

---

## Best Practices

### Security

1. **Use Passphrase Files**:
   - Prefer `--passphrase-file` over environment variables
   - Set `chmod 600` permissions (owner read-only)
   - Never commit to version control
   - Store in encrypted filesystems

2. **Protect JSON Output**:
   - JSON contains plaintext passwords
   - Never log JSON responses
   - Immediately parse and extract needed fields
   - Clear variables after use

3. **Mask Sensitive Data**:
   ```bash
   # GitHub Actions
   echo "::add-mask::$PASSWORD"

   # GitLab CI
   echo "PASSWORD=[MASKED]" >> $CI_JOB_LOG
   ```

4. **Use Exit Codes**:
   - Always check exit codes
   - Handle errors gracefully
   - Send alerts on failures

5. **Rotate Passphrases**:
   - Change vault passphrases periodically
   - Use password manager for passphrase storage
   - Document passphrase rotation procedures

### Performance

1. **Cache Considerations**:
   - Vault decryption is CPU-intensive (Argon2id KDF)
   - Cache extracted passwords temporarily
   - Avoid repeated decryption in loops

2. **Parallel Operations**:
   ```bash
   # Retrieve multiple passwords in parallel
   stegvault vault get vault.png -k gmail --json --passphrase-file ~/.pass & P1=$!
   stegvault vault get vault.png -k github --json --passphrase-file ~/.pass & P2=$!
   wait $P1 $P2
   ```

3. **Batch Operations**:
   - Use `vault export` for bulk extraction
   - Parse JSON once instead of multiple `get` commands

### Error Handling

```bash
#!/bin/bash
# Robust error handling example

VAULT_FILE="vault.png"
KEY="gmail"
PASS_FILE="$HOME/.vault_pass"

# Function to handle errors
handle_error() {
    local exit_code=$1
    local error_msg=$2

    case $exit_code in
        0)
            return 0
            ;;
        1)
            echo "Runtime Error: $error_msg"
            # Log error, send alert, etc.
            return 1
            ;;
        2)
            echo "Validation Error: $error_msg"
            # Fix configuration, retry, etc.
            return 2
            ;;
        *)
            echo "Unknown Error: $error_msg"
            return 99
            ;;
    esac
}

# Execute command
RESULT=$(stegvault vault get "$VAULT_FILE" -k "$KEY" \
    --passphrase-file "$PASS_FILE" --json 2>&1)
EXIT_CODE=$?

# Handle result
if [ $EXIT_CODE -eq 0 ]; then
    PASSWORD=$(echo "$RESULT" | jq -r '.data.password')
    echo "Password retrieved: $PASSWORD"
else
    ERROR_MSG=$(echo "$RESULT" | jq -r '.error' 2>/dev/null || echo "$RESULT")
    handle_error $EXIT_CODE "$ERROR_MSG"
fi
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Passphrase File Not Found

**Error**:
```
{"status":"error","error":"Passphrase file not found: ~/.vault_pass","error_type":"RuntimeError"}
```

**Solution**:
- Use absolute path: `--passphrase-file /home/user/.vault_pass`
- Check file permissions: `ls -la ~/.vault_pass`
- Verify file exists: `cat ~/.vault_pass`

#### Issue 2: Empty Passphrase File

**Error**:
```
{"status":"error","error":"Passphrase file is empty","error_type":"ValidationError"}
```

**Solution**:
- Verify file has content: `cat ~/.vault_pass`
- Check for trailing newline: `wc -l ~/.vault_pass`
- Re-create file: `echo "passphrase" > ~/.vault_pass`

#### Issue 3: JSON Parsing Fails

**Error**:
```bash
$ PASSWORD=$(... | jq -r '.data.password')
jq: error: Invalid JSON
```

**Solution**:
- Check command exit code first
- Verify `--json` flag is present
- Inspect raw output: `stegvault ... --json | tee /tmp/output.json`
- Check for error response: `jq -r '.status' /tmp/output.json`

#### Issue 4: Exit Code Always 0

**Problem**: Script not detecting errors.

**Solution**:
- Use `set -e` in scripts (exit on error)
- Check `$?` immediately after command
- Don't pipe commands before checking exit code:
  ```bash
  # WRONG - can't check exit code
  PASSWORD=$(stegvault vault get ... | jq -r '.data.password')

  # CORRECT - check exit code
  RESULT=$(stegvault vault get ... --json)
  if [ $? -eq 0 ]; then
      PASSWORD=$(echo "$RESULT" | jq -r '.data.password')
  fi
  ```

---

## See Also

- [CLI Commands Reference](https://github.com/kalashnikxvxiii/StegVault/wiki/CLI-Commands-Reference) - Complete command reference
- [Security Best Practices](https://github.com/kalashnikxvxiii/StegVault/wiki/Security-Best-Practices) - Security guidelines
- [Basic Usage Examples](https://github.com/kalashnikxvxiii/StegVault/wiki/Basic-Usage-Examples) - Practical examples
- [Troubleshooting](https://github.com/kalashnikxvxiii/StegVault/wiki/Troubleshooting) - Common issues and solutions

---

**Version**: 0.7.8
**Last Updated**: 2025-12-26
