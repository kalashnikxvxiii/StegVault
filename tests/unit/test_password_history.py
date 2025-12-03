"""
Tests for password history functionality.

Tests the PasswordHistoryEntry class and password history methods in VaultEntry.
"""

import pytest
from datetime import datetime

from stegvault.vault import VaultEntry, PasswordHistoryEntry


class TestPasswordHistoryEntry:
    """Tests for PasswordHistoryEntry dataclass."""

    def test_create_history_entry(self):
        """Should create password history entry with defaults."""
        entry = PasswordHistoryEntry(password="old_password")

        assert entry.password == "old_password"
        assert entry.changed_at is not None
        assert entry.reason is None

    def test_create_history_entry_with_reason(self):
        """Should create history entry with reason."""
        entry = PasswordHistoryEntry(password="old_pass", reason="scheduled rotation")

        assert entry.password == "old_pass"
        assert entry.reason == "scheduled rotation"

    def test_history_entry_to_dict(self):
        """Should convert history entry to dictionary."""
        entry = PasswordHistoryEntry(
            password="test_pass", changed_at="2025-01-01T10:00:00Z", reason="test"
        )

        result = entry.to_dict()

        assert result["password"] == "test_pass"
        assert result["changed_at"] == "2025-01-01T10:00:00Z"
        assert result["reason"] == "test"

    def test_history_entry_from_dict(self):
        """Should create history entry from dictionary."""
        data = {
            "password": "test_pass",
            "changed_at": "2025-01-01T10:00:00Z",
            "reason": "test",
        }

        entry = PasswordHistoryEntry.from_dict(data)

        assert entry.password == "test_pass"
        assert entry.changed_at == "2025-01-01T10:00:00Z"
        assert entry.reason == "test"


class TestVaultEntryPasswordHistory:
    """Tests for password history methods in VaultEntry."""

    def test_vault_entry_default_history(self):
        """Should create entry with empty password history by default."""
        entry = VaultEntry(key="test", password="current_pass")

        assert entry.password_history == []
        assert entry.max_history == 5

    def test_change_password_adds_to_history(self):
        """Should add current password to history when changing."""
        entry = VaultEntry(key="test", password="old_password")
        original_modified = entry.modified

        entry.change_password("new_password")

        assert entry.password == "new_password"
        assert len(entry.password_history) == 1
        assert entry.password_history[0]["password"] == "old_password"
        assert entry.modified != original_modified  # Modified timestamp updated

    def test_change_password_with_reason(self):
        """Should store reason when changing password."""
        entry = VaultEntry(key="test", password="old_pass")

        entry.change_password("new_pass", reason="suspected breach")

        assert entry.password_history[0]["password"] == "old_pass"
        assert entry.password_history[0]["reason"] == "suspected breach"

    def test_change_password_multiple_times(self):
        """Should maintain history in order (most recent first)."""
        entry = VaultEntry(key="test", password="pass1")

        entry.change_password("pass2")
        entry.change_password("pass3")
        entry.change_password("pass4")

        assert entry.password == "pass4"
        assert len(entry.password_history) == 3
        assert entry.password_history[0]["password"] == "pass3"  # Most recent
        assert entry.password_history[1]["password"] == "pass2"
        assert entry.password_history[2]["password"] == "pass1"  # Oldest

    def test_change_password_respects_max_history(self):
        """Should trim history to max_history size."""
        entry = VaultEntry(key="test", password="pass1", max_history=3)

        entry.change_password("pass2")
        entry.change_password("pass3")
        entry.change_password("pass4")
        entry.change_password("pass5")
        entry.change_password("pass6")

        assert entry.password == "pass6"
        assert len(entry.password_history) == 3  # Limited to max_history
        assert entry.password_history[0]["password"] == "pass5"  # Most recent
        assert entry.password_history[1]["password"] == "pass4"
        assert entry.password_history[2]["password"] == "pass3"
        # pass1 and pass2 should be trimmed

    def test_change_password_same_as_current(self):
        """Should not add to history if password unchanged."""
        entry = VaultEntry(key="test", password="same_pass")

        entry.change_password("same_pass")

        assert entry.password == "same_pass"
        assert len(entry.password_history) == 0  # No history added

    def test_get_password_history(self):
        """Should return list of PasswordHistoryEntry objects."""
        entry = VaultEntry(key="test", password="current")
        entry.change_password("pass2")
        entry.change_password("pass3")

        history = entry.get_password_history()

        assert len(history) == 2
        assert all(isinstance(h, PasswordHistoryEntry) for h in history)
        assert history[0].password == "pass2"  # Most recent
        assert history[1].password == "current"  # Oldest

    def test_get_password_history_empty(self):
        """Should return empty list if no history."""
        entry = VaultEntry(key="test", password="current")

        history = entry.get_password_history()

        assert history == []

    def test_clear_password_history(self):
        """Should clear all password history."""
        entry = VaultEntry(key="test", password="pass1")
        entry.change_password("pass2")
        entry.change_password("pass3")

        assert len(entry.password_history) == 2

        entry.clear_password_history()

        assert entry.password_history == []
        assert entry.password == "pass3"  # Current password unchanged

    def test_password_history_persistence(self):
        """Should maintain history through to_dict/from_dict cycle."""
        entry = VaultEntry(key="test", password="pass1")
        entry.change_password("pass2", reason="test reason")
        entry.change_password("pass3")

        # Convert to dict and back
        data = entry.to_dict()
        restored = VaultEntry.from_dict(data)

        assert restored.password == "pass3"
        assert len(restored.password_history) == 2
        assert restored.password_history[0]["password"] == "pass2"
        assert restored.password_history[1]["password"] == "pass1"
        assert restored.password_history[1]["reason"] == "test reason"

    def test_custom_max_history(self):
        """Should respect custom max_history value."""
        entry = VaultEntry(key="test", password="pass1", max_history=10)

        for i in range(15):
            entry.change_password(f"pass{i+2}")

        assert len(entry.password_history) == 10  # Limited to custom max

    def test_zero_max_history(self):
        """Should allow disabling history with max_history=0."""
        entry = VaultEntry(key="test", password="pass1", max_history=0)

        entry.change_password("pass2")
        entry.change_password("pass3")

        assert entry.password == "pass3"
        assert len(entry.password_history) == 0  # No history kept

    def test_password_history_timestamps(self):
        """Should include timestamps in history entries."""
        entry = VaultEntry(key="test", password="pass1")

        entry.change_password("pass2")
        entry.change_password("pass3")

        history = entry.get_password_history()

        for hist_entry in history:
            assert hist_entry.changed_at is not None
            # Verify timestamp is valid ISO 8601 format
            datetime.fromisoformat(hist_entry.changed_at.replace("Z", "+00:00"))


class TestVaultUpdatePasswordHistory:
    """Tests for password history integration with Vault.update_entry()."""

    def test_vault_update_entry_tracks_password_changes(self):
        """Should track password history when updating via vault.update_entry()."""
        from stegvault.vault import Vault

        vault = Vault()
        vault.add_entry(VaultEntry(key="test", password="old_pass"))

        # Update password via vault.update_entry
        vault.update_entry("test", password="new_pass")

        entry = vault.get_entry("test")
        assert entry.password == "new_pass"
        assert len(entry.password_history) == 1
        assert entry.password_history[0]["password"] == "old_pass"

    def test_vault_update_entry_with_password_reason(self):
        """Should accept password_change_reason parameter."""
        from stegvault.vault import Vault

        vault = Vault()
        vault.add_entry(VaultEntry(key="test", password="old_pass"))

        # Update password with reason
        vault.update_entry("test", password="new_pass", password_change_reason="scheduled rotation")

        entry = vault.get_entry("test")
        assert entry.password == "new_pass"
        assert entry.password_history[0]["password"] == "old_pass"
        assert entry.password_history[0]["reason"] == "scheduled rotation"

    def test_vault_update_entry_non_password_fields(self):
        """Should not affect password history when updating non-password fields."""
        from stegvault.vault import Vault

        vault = Vault()
        vault.add_entry(VaultEntry(key="test", password="my_pass", username="old_user"))

        # Update non-password field
        vault.update_entry("test", username="new_user", notes="Updated notes")

        entry = vault.get_entry("test")
        assert entry.password == "my_pass"
        assert entry.username == "new_user"
        assert entry.notes == "Updated notes"
        assert len(entry.password_history) == 0  # No password history

    def test_vault_update_entry_mixed_fields_with_password(self):
        """Should handle password and non-password fields together."""
        from stegvault.vault import Vault

        vault = Vault()
        vault.add_entry(VaultEntry(key="test", password="pass1", username="user1"))

        # Update password and other fields
        vault.update_entry(
            "test",
            password="pass2",
            username="user2",
            notes="New notes",
            password_change_reason="security update",
        )

        entry = vault.get_entry("test")
        assert entry.password == "pass2"
        assert entry.username == "user2"
        assert entry.notes == "New notes"
        assert len(entry.password_history) == 1
        assert entry.password_history[0]["password"] == "pass1"
        assert entry.password_history[0]["reason"] == "security update"
