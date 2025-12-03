# StegVault TUI - Manual Testing Guide

**Version**: v0.7.0
**Last Updated**: 2025-12-03
**Tester**: _____________________
**Date Tested**: _____________________

## Prerequisites

### Installation
```bash
# Ensure you have the latest version
cd C:\Users\Administrator\Documents\GitHub\Software\StegVault
pip install -e .

# Verify installation
stegvault --version
# Should show: StegVault version 0.7.0
```

### Test Assets Preparation
```bash
# Create test directory
mkdir test_tui
cd test_tui

# Download or copy a test image (PNG or JPEG)
# You can use any image ~500KB+ for testing
# Example: cover.png or cover.jpg
```

---

## Test Plan Overview

| Test ID | Category | Description | Priority |
|---------|----------|-------------|----------|
| T001 | Launch | TUI launches successfully | P0 |
| T002 | Welcome | Welcome screen displays | P0 |
| T003 | Keyboard | All key bindings work | P0 |
| T004 | File Select | File browser works | P0 |
| T005 | New Vault | Create vault workflow | P1 |
| T006 | Open Vault | Load existing vault | P1 |
| T007 | Entry List | Display all entries | P1 |
| T008 | Entry CRUD | Add/Edit/Delete entries | P1 |
| T009 | Search | Filter entries in real-time | P1 |
| T010 | Password Gen | Generate secure passwords | P1 |
| T011 | TOTP | Display and refresh codes | P2 |
| T012 | Clipboard | Copy passwords | P2 |
| T013 | Save | Persist vault changes | P1 |
| T014 | Help | Display help screen | P2 |
| T015 | Error | Handle errors gracefully | P2 |

---

## Section 1: Launch & Welcome Screen

### T001: Launch TUI Application
**Priority**: P0 (Critical)

**Steps**:
1. Open terminal/command prompt
2. Navigate to test directory: `cd test_tui`
3. Run: `stegvault tui`

**Expected Results**:
- ✅ TUI launches without errors
- ✅ Window displays with title "StegVault TUI"
- ✅ No Python exceptions or stack traces

**Actual Results**: _____________________

---

### T002: Welcome Screen Display
**Priority**: P0 (Critical)

**Steps**:
1. Observe the welcome screen after launch

**Expected Results**:
- ✅ Title: "🔐 Welcome to StegVault TUI"
- ✅ Subtitle: "Secure password management using steganography"
- ✅ Three buttons visible: "Open Vault", "New Vault", "Help"
- ✅ Footer shows key bindings: o=open, n=new, h=help, q=quit

**Actual Results**: _____________________

---

### T003: Keyboard Bindings - Welcome Screen
**Priority**: P0 (Critical)

**Test each key binding**:

| Key | Expected Action | Result (✓/✗) | Notes |
|-----|----------------|--------------|-------|
| `h` | Opens help screen | ☐ | |
| `Escape` | Closes help screen | ☐ | |
| `q` | Quits application | ☐ | Test last! |

**Actual Results**: _____________________

---

## Section 2: Create New Vault Workflow

### T005: Create New Vault - Complete Flow
**Priority**: P1 (High)

**Steps**:
1. From welcome screen, press `n` or click "New Vault"
2. **File Selection Dialog**:
   - Browse to find `cover.png` (or `cover.jpg`)
   - Navigate using arrow keys ↑↓
   - Press Enter to select file
   - Verify path shown in input field
   - Press Enter to confirm
3. **Passphrase Input**:
   - Enter passphrase: `TestPass123!`
   - Verify password is masked (shows *****)
   - Press Enter to continue
4. **First Entry Form**:
   - Title: "Add First Entry to New Vault"
   - Enter key: `gmail`
   - Enter password: `MyPassword123!`
   - Enter username: `test@gmail.com`
   - Enter URL: `https://gmail.com`
   - Enter notes: `Test account for manual testing`
   - Enter tags: `email, personal, test`
   - Press Tab to navigate between fields
   - Click "Save" or press Enter

**Expected Results**:
- ✅ File browser shows directory tree
- ✅ Can navigate with keyboard
- ✅ Passphrase is masked
- ✅ Form accepts all fields
- ✅ Tags are parsed (comma-separated)
- ✅ Success notification appears
- ✅ Vault screen opens with new entry
- ✅ Entry count shows "(1)"
- ✅ Entry appears in list

**Actual Results**: _____________________

---

### T005a: Create New Vault - Cancel Operations
**Priority**: P2 (Medium)

Test cancellation at each step:

| Step | Key | Expected | Result (✓/✗) |
|------|-----|----------|--------------|
| File selection | Escape | Return to welcome | ☐ |
| Passphrase input | Escape | Return to welcome | ☐ |
| Entry form | Escape | Return to welcome | ☐ |

**Actual Results**: _____________________

---

## Section 3: Open Existing Vault

### T006: Open Vault - Success Path
**Priority**: P1 (High)

**Pre-requisite**: Vault created in T005

**Steps**:
1. From welcome screen, press `o` or click "Open Vault"
2. **File Selection**: Navigate to vault image created in T005
3. Press Enter to select
4. **Passphrase Input**: Enter `TestPass123!`
5. Press Enter to unlock

**Expected Results**:
- ✅ Vault screen opens
- ✅ Entry "gmail" visible in list
- ✅ Entry count shows "(1)"
- ✅ Notification: "Loading vault..." appears briefly

**Actual Results**: _____________________

---

### T006a: Open Vault - Wrong Passphrase
**Priority**: P2 (Medium)

**Steps**:
1. Try to open vault with wrong passphrase: `WrongPass123!`

**Expected Results**:
- ✅ Error notification appears
- ✅ Error message mentions decryption failure
- ✅ Returns to welcome screen
- ✅ No crash or exception

**Actual Results**: _____________________

---

### T006b: Open Vault - Invalid File
**Priority**: P2 (Medium)

**Steps**:
1. Try to open a non-vault image (regular PNG/JPEG without embedded data)

**Expected Results**:
- ✅ Error notification appears
- ✅ Error message mentions invalid vault or missing data
- ✅ Returns to welcome screen gracefully

**Actual Results**: _____________________

---

## Section 4: Vault Screen Navigation

### T007: Entry List Display
**Priority**: P1 (High)

**Pre-requisite**: Vault opened with 1 entry

**Steps**:
1. Observe the vault screen layout

**Expected Results**:
- ✅ Screen split: 30% left (list), 70% right (detail)
- ✅ Header shows: "Vault: Unnamed" and file path
- ✅ Entry list shows "gmail" entry
- ✅ Entry count badge shows "(1)"
- ✅ Search box visible with placeholder text
- ✅ Action bar at bottom with 7 buttons
- ✅ Footer shows key bindings

**Key bindings visible**:
- ✅ a=Add, e=Edit, d=Delete, c=Copy, v=Show/Hide, s=Save, /=Search

**Actual Results**: _____________________

---

### T007a: Entry Selection
**Priority**: P1 (High)

**Steps**:
1. Click on "gmail" entry in list (or use arrow keys + Enter)
2. Observe detail panel on right

**Expected Results**:
- ✅ Entry becomes highlighted
- ✅ Detail panel shows all entry fields:
  - Key: gmail
  - Password: ************** (masked)
  - Username: test@gmail.com
  - URL: https://gmail.com
  - Notes: Test account for manual testing
  - Tags: email, personal, test
  - Created: (timestamp)
  - Modified: (timestamp)

**Actual Results**: _____________________

---

## Section 5: Entry CRUD Operations

### T008a: Add New Entry
**Priority**: P1 (High)

**Steps**:
1. Press `a` or click "Add (a)" button
2. **Entry Form**:
   - Key: `github`
   - Password: Click "Generate" button
   - Username: `testuser`
   - URL: `https://github.com`
   - Notes: `Development account`
   - Tags: `dev, work`
3. Click "Save"

**Expected Results**:
- ✅ Form modal appears with title "Add New Entry"
- ✅ "Generate" button visible next to password field
- ✅ All fields editable
- ✅ Success notification appears
- ✅ Entry "github" appears in list
- ✅ Entry count updates to "(2)"
- ✅ List auto-refreshes

**Actual Results**: _____________________

---

### T008b: Edit Existing Entry
**Priority**: P1 (High)

**Steps**:
1. Select "gmail" entry from list
2. Press `e` or click "Edit (e)" button
3. **Entry Form**:
   - Change username to: `newemail@gmail.com`
   - Change notes to: `Updated test account`
   - Add new tag: `, updated`
4. Click "Save"

**Expected Results**:
- ✅ Form modal appears with title "Edit Entry: gmail"
- ✅ All fields pre-populated with current values
- ✅ Changes saved successfully
- ✅ Success notification appears
- ✅ Detail panel updates immediately
- ✅ Modified timestamp updates

**Actual Results**: _____________________

---

### T008c: Delete Entry
**Priority**: P1 (High)

**Steps**:
1. Select "github" entry
2. Press `d` or click "Delete (d)" button
3. **Confirmation Dialog** appears
4. Click "Delete" to confirm (or press Enter)

**Expected Results**:
- ✅ Confirmation dialog shows entry key: "github"
- ✅ Two options: "Delete" and "Cancel"
- ✅ Entry removed from list
- ✅ Entry count updates to "(1)"
- ✅ Detail panel clears (no entry selected)
- ✅ Success notification appears

**Actual Results**: _____________________

---

### T008d: Delete Entry - Cancel
**Priority**: P2 (Medium)

**Steps**:
1. Select "gmail" entry
2. Press `d` to delete
3. In confirmation dialog, click "Cancel" or press Escape

**Expected Results**:
- ✅ Dialog closes
- ✅ Entry NOT deleted
- ✅ Entry still visible in list

**Actual Results**: _____________________

---

## Section 6: Password Generator

### T010: Password Generator - Full Workflow
**Priority**: P1 (High)

**Steps**:
1. Press `a` to add new entry
2. In password field, click "Generate" button
3. **Password Generator Screen**:
   - Observe initial password (16 chars, all types)
   - Click `-` button 3 times (length should decrease)
   - Click `+` button 5 times (length should increase)
   - Press `g` key to generate new password
   - Observe password changes
4. Click "Use This Password" or press Enter

**Expected Results**:
- ✅ Generator modal appears with live preview
- ✅ Initial password: 16 characters
- ✅ Password includes: lowercase, uppercase, digits, symbols
- ✅ `-` button decreases length (min: 8)
- ✅ `+` button increases length (max: 64)
- ✅ Length value updates in UI
- ✅ `g` key generates new password
- ✅ Password changes on each generate
- ✅ "Use This Password" fills password field
- ✅ Generator closes, returns to form

**Actual Results**: _____________________

---

### T010a: Password Generator - Cancel
**Priority**: P2 (Medium)

**Steps**:
1. Open generator
2. Press Escape or click "Cancel"

**Expected Results**:
- ✅ Generator closes
- ✅ Password field remains empty
- ✅ Returns to entry form

**Actual Results**: _____________________

---

### T010b: Password Generator - Edge Cases
**Priority**: P2 (Medium)

| Test | Steps | Expected | Result (✓/✗) |
|------|-------|----------|--------------|
| Min length | Click `-` until 8 | Can't go below 8 | ☐ |
| Max length | Click `+` until 64 | Can't go above 64 | ☐ |
| Rapid generate | Press `g` 10 times quickly | All passwords different | ☐ |

**Actual Results**: _____________________

---

## Section 7: Search & Filter

### T009: Search Functionality
**Priority**: P1 (High)

**Pre-requisite**: Vault with multiple entries (gmail, github, aws, etc.)

**Setup**:
1. Add 3-4 more entries with different keys, usernames, tags

**Steps**:
1. Press `/` to focus search input
2. Type: `gm`
3. Observe entry list
4. Clear search, type: `@gmail.com`
5. Observe entry list
6. Clear search, type: `email`
7. Observe entry list

**Expected Results**:

| Search Term | Matches | Count Display | Result (✓/✗) |
|-------------|---------|---------------|--------------|
| `gm` | gmail | (1/4) | ☐ |
| `@gmail.com` | entries with @gmail.com | (X/4) | ☐ |
| `email` | entries with "email" tag | (X/4) | ☐ |
| `` (empty) | all entries | (4) | ☐ |

**Additional checks**:
- ✅ Search is case-insensitive
- ✅ Search is real-time (updates as you type)
- ✅ Entry count shows "X/Y" when filtering
- ✅ Detail panel clears if selected entry filtered out

**Actual Results**: _____________________

---

### T009a: Search - No Results
**Priority**: P2 (Medium)

**Steps**:
1. Search for: `nonexistent`

**Expected Results**:
- ✅ Entry list becomes empty
- ✅ Count shows "(0/4)"
- ✅ Detail panel is empty
- ✅ No errors or crashes

**Actual Results**: _____________________

---

## Section 8: TOTP Integration

### T011: TOTP Display & Auto-Refresh
**Priority**: P2 (Medium)

**Setup**:
1. Add entry with TOTP secret
2. Use test secret: `JBSWY3DPEHPK3PXP` (standard test secret)

**Steps**:
1. Add new entry:
   - Key: `totp-test`
   - Password: `anypassword`
   - TOTP Secret: `JBSWY3DPEHPK3PXP`
2. Save entry
3. Select "totp-test" from list
4. Observe detail panel
5. Wait 5-10 seconds
6. Observe TOTP code and countdown

**Expected Results**:
- ✅ TOTP section appears in detail panel
- ✅ 6-digit code displayed (e.g., "123456")
- ✅ Countdown timer shown (e.g., "(25s)")
- ✅ Countdown decreases every second
- ✅ Code refreshes when countdown reaches 0
- ✅ New code is different from previous

**Actual Results**: _____________________

---

### T011a: TOTP - Invalid Secret
**Priority**: P2 (Medium)

**Steps**:
1. Add entry with invalid TOTP secret: `INVALID123`
2. Select entry

**Expected Results**:
- ✅ TOTP section shows: "✗ Invalid secret"
- ✅ No countdown or code
- ✅ No errors or crashes

**Actual Results**: _____________________

---

## Section 9: Clipboard Operations

### T012: Copy Password to Clipboard
**Priority**: P2 (Medium)

**Steps**:
1. Select "gmail" entry
2. Press `c` or click "Copy (c)" button
3. Open notepad/text editor
4. Paste (Ctrl+V or Cmd+V)

**Expected Results**:
- ✅ Notification: "Password copied for 'gmail'"
- ✅ Clipboard contains correct password
- ✅ Pasted password matches entry password

**Actual Results**: _____________________

---

### T012a: Copy - No Entry Selected
**Priority**: P2 (Medium)

**Steps**:
1. Deselect any entry (click empty area)
2. Press `c`

**Expected Results**:
- ✅ Warning notification: "No entry selected"
- ✅ Clipboard not modified

**Actual Results**: _____________________

---

### T012b: Toggle Password Visibility
**Priority**: P2 (Medium)

**Steps**:
1. Select any entry
2. Observe password field (should be masked: ************)
3. Press `v` or click "Show/Hide (v)" button
4. Observe password field
5. Press `v` again

**Expected Results**:
- ✅ Initial state: password masked (****)
- ✅ After first `v`: password visible (plaintext)
- ✅ After second `v`: password masked again
- ✅ Toggle works multiple times

**Actual Results**: _____________________

---

## Section 10: Save Vault

### T013: Save Vault Changes
**Priority**: P1 (High)

**Steps**:
1. Make several changes:
   - Add 1 entry
   - Edit 1 entry
   - Delete 1 entry
2. Press `s` or click "Save (s)" button
3. Wait for notification
4. Close TUI (`q`)
5. Reopen TUI and load same vault

**Expected Results**:
- ✅ Notification: "Saving vault..."
- ✅ Notification: "Vault saved successfully!"
- ✅ No errors during save
- ✅ After reopen: all changes persisted
- ✅ New entry exists
- ✅ Edited entry shows updates
- ✅ Deleted entry not present

**Actual Results**: _____________________

---

### T013a: Save - Verify Image File
**Priority**: P2 (Medium)

**Steps**:
1. Note file size before save: `dir vault.png` (Windows) or `ls -lh vault.png` (Linux/Mac)
2. Make changes and save
3. Check file size after save

**Expected Results**:
- ✅ File size changes (increases or stays similar)
- ✅ File modified timestamp updates
- ✅ Image still viewable (can open with image viewer)

**Actual Results**: _____________________

---

## Section 11: Help Screen

### T014: Help Screen Display
**Priority**: P2 (Medium)

**Steps**:
1. From welcome screen, press `h` or click "Help"
2. Scroll through help content
3. Press Escape or click "Close"

**Expected Results**:
- ✅ Help modal appears
- ✅ Title: "🔐 StegVault TUI - Help"
- ✅ Content sections visible:
  - Welcome Screen shortcuts
  - Vault Screen shortcuts
  - Entry Forms shortcuts
  - Password Generator shortcuts
  - Navigation shortcuts
  - About section (version, crypto info)
  - Security Notes
- ✅ Content is scrollable (if long)
- ✅ Escape closes help
- ✅ "Close" button works

**Actual Results**: _____________________

---

## Section 12: Error Handling

### T015a: Handle Full Image (Capacity Exceeded)
**Priority**: P2 (Medium)

**Steps**:
1. Use very small image (<50KB)
2. Try to add many entries (10-20)
3. Observe behavior

**Expected Results**:
- ✅ Error notification when capacity reached
- ✅ Clear message about insufficient space
- ✅ No corruption of existing data
- ✅ Can still save what fits

**Actual Results**: _____________________

---

### T015b: Keyboard Interrupts
**Priority**: P2 (Medium)

**Test graceful handling**:

| Action | Expected | Result (✓/✗) |
|--------|----------|--------------|
| Ctrl+C during load | Graceful exit or error | ☐ |
| Escape in modals | Closes modal, no crash | ☐ |
| Rapid key presses | No lag or crash | ☐ |

**Actual Results**: _____________________

---

### T015c: Edge Cases
**Priority**: P2 (Medium)

| Test Case | Steps | Expected | Result (✓/✗) |
|-----------|-------|----------|--------------|
| Empty key | Try to save entry with no key | Error: "Key required" | ☐ |
| Empty password | Try to save entry with no password | Error: "Password required" | ☐ |
| Duplicate key | Add entry with existing key | Error: "Key already exists" | ☐ |
| Very long key | Key with 500+ characters | Accepts or warns gracefully | ☐ |
| Special chars | Key: `!@#$%^&*()_+{}[]` | Accepts all chars | ☐ |

**Actual Results**: _____________________

---

## Section 13: Performance & Stability

### T016: Performance Tests
**Priority**: P2 (Medium)

| Test | Condition | Expected | Result (✓/✗) | Notes |
|------|-----------|----------|--------------|-------|
| Large vault | 100+ entries | Loads in <2s | ☐ | |
| Search speed | Search with 100+ entries | Results instant | ☐ | |
| Rapid navigation | Select 10 entries quickly | No lag | ☐ | |
| Long session | Use TUI for 10+ minutes | No memory leaks | ☐ | |

**Actual Results**: _____________________

---

### T017: Stability Tests
**Priority**: P2 (Medium)

| Test | Steps | Expected | Result (✓/✗) |
|------|-------|----------|--------------|
| Rapid save | Save vault 10 times quickly | All saves succeed | ☐ |
| Window resize | Resize terminal window | UI adapts gracefully | ☐ |
| Modal stacking | Open modal, try to open another | Prevents or handles | ☐ |
| Memory usage | Monitor RAM during session | Stays under 200MB | ☐ |

**Actual Results**: _____________________

---

## Section 14: Cross-Platform (if applicable)

### T018: Platform-Specific Tests

**Test on each OS** (Windows, macOS, Linux):

| Feature | Windows | macOS | Linux | Notes |
|---------|---------|-------|-------|-------|
| Launch | ☐ | ☐ | ☐ | |
| File browser | ☐ | ☐ | ☐ | Path format |
| Clipboard copy | ☐ | ☐ | ☐ | |
| Keyboard shortcuts | ☐ | ☐ | ☐ | |
| TOTP timer | ☐ | ☐ | ☐ | |
| Colors & themes | ☐ | ☐ | ☐ | Readable? |

**Actual Results**: _____________________

---

## Section 15: Integration Tests

### T019: CLI + TUI Integration
**Priority**: P2 (Medium)

**Steps**:
1. Create vault using CLI:
   ```bash
   stegvault vault create -i cover.png -o cli-vault.png -k testentry -p TestPass123
   ```
2. Open vault in TUI
3. Add/edit entries in TUI
4. Save in TUI
5. Verify with CLI:
   ```bash
   stegvault vault get cli-vault.png -k testentry
   ```

**Expected Results**:
- ✅ TUI can open CLI-created vault
- ✅ TUI changes visible in CLI
- ✅ No compatibility issues

**Actual Results**: _____________________

---

## Test Summary

### Statistics

- **Total Tests Executed**: _____ / 50+
- **Tests Passed**: _____
- **Tests Failed**: _____
- **Tests Skipped**: _____
- **Pass Rate**: _____%

### Critical Issues Found

| Issue ID | Severity | Description | Steps to Reproduce |
|----------|----------|-------------|-------------------|
| | | | |

### Minor Issues Found

| Issue ID | Severity | Description | Steps to Reproduce |
|----------|----------|-------------|-------------------|
| | | | |

### Recommendations

1. _____________________
2. _____________________
3. _____________________

---

## Appendix A: Test Data Templates

### Sample Entries for Testing

```
Entry 1:
- Key: gmail
- Password: Gm@il2024Pass!
- Username: testuser@gmail.com
- URL: https://gmail.com
- Notes: Personal email account
- Tags: email, personal, google

Entry 2:
- Key: github
- Password: Git#Hub2024Secure
- Username: devuser
- URL: https://github.com
- Notes: Development platform
- Tags: dev, coding, git

Entry 3:
- Key: aws
- Password: Aws&Cloud2024
- Username: admin@company.com
- URL: https://aws.amazon.com
- Notes: Cloud infrastructure
- Tags: work, cloud, infrastructure

Entry 4 (with TOTP):
- Key: microsoft
- Password: M$oft2024Pass
- Username: user@microsoft.com
- URL: https://microsoft.com
- TOTP Secret: JBSWY3DPEHPK3PXP
- Tags: work, office, 2fa
```

---

## Appendix B: Known Limitations

1. **Compose methods**: TUI compose() methods have low test coverage (hard to unit test)
2. **Modal stacking**: Opening multiple modals simultaneously not fully tested
3. **Very large vaults**: Performance with 500+ entries not extensively tested
4. **Network disconnects**: N/A (local-only application)

---

## Appendix C: Testing Checklist

### Pre-Test Setup
- [ ] StegVault v0.7.0 installed
- [ ] Test images prepared (PNG and JPEG)
- [ ] Test directory created
- [ ] Notepad/text editor ready (for clipboard test)

### Post-Test Cleanup
- [ ] Delete test vault files
- [ ] Remove test directory
- [ ] Document all findings
- [ ] Create GitHub issues for bugs found

---

**Sign-off**:

Tester: _____________________
Date: _____________________
Result: ☐ PASS ☐ FAIL ☐ PARTIAL

**Notes**: _____________________
