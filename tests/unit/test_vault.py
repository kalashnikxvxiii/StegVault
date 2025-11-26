"""
Unit tests for vault module.
"""

import pytest
import json
from datetime import datetime
from stegvault.vault import (
    Vault,
    VaultEntry,
    VaultFormat,
    create_vault,
    add_entry,
    get_entry,
    list_entries,
    update_entry,
    delete_entry,
    vault_to_json,
    vault_from_json,
    detect_format,
    parse_payload,
    single_password_to_vault,
    generate_password,
    generate_passphrase,
    estimate_entropy,
    assess_password_strength,
    PasswordGenerator,
)


class TestVaultEntry:
    """Tests for VaultEntry dataclass."""

    def test_create_entry_minimal(self):
        """Create entry with minimal required fields."""
        entry = VaultEntry(key="test", password="secret123")
        assert entry.key == "test"
        assert entry.password == "secret123"
        assert entry.username is None
        assert entry.url is None
        assert entry.notes is None
        assert entry.tags == []
        assert entry.totp_secret is None

    def test_create_entry_full(self):
        """Create entry with all fields."""
        entry = VaultEntry(
            key="gmail",
            password="SuperSecret123!",
            username="user@gmail.com",
            url="https://gmail.com",
            notes="Personal email",
            tags=["email", "personal"],
            totp_secret="BASE32SECRET",
        )
        assert entry.key == "gmail"
        assert entry.password == "SuperSecret123!"
        assert entry.username == "user@gmail.com"
        assert entry.url == "https://gmail.com"
        assert entry.notes == "Personal email"
        assert entry.tags == ["email", "personal"]
        assert entry.totp_secret == "BASE32SECRET"

    def test_entry_has_timestamps(self):
        """Entry should have created and modified timestamps."""
        entry = VaultEntry(key="test", password="secret")
        assert entry.created is not None
        assert entry.modified is not None
        assert entry.accessed is None  # Not accessed yet

    def test_entry_to_dict(self):
        """Entry should convert to dictionary."""
        entry = VaultEntry(
            key="test",
            password="secret",
            username="user",
            url="https://example.com",
        )
        data = entry.to_dict()
        assert isinstance(data, dict)
        assert data["key"] == "test"
        assert data["password"] == "secret"
        assert data["username"] == "user"
        assert data["url"] == "https://example.com"

    def test_entry_from_dict(self):
        """Entry should create from dictionary."""
        data = {
            "key": "test",
            "password": "secret",
            "username": "user",
            "url": "https://example.com",
            "notes": None,
            "tags": [],
            "totp_secret": None,
            "created": "2025-01-14T12:00:00Z",
            "modified": "2025-01-14T12:00:00Z",
            "accessed": None,
        }
        entry = VaultEntry.from_dict(data)
        assert entry.key == "test"
        assert entry.password == "secret"
        assert entry.username == "user"

    def test_update_modified(self):
        """update_modified should update timestamp."""
        entry = VaultEntry(key="test", password="secret")
        original_modified = entry.modified
        import time

        time.sleep(0.01)  # Ensure time passes
        entry.update_modified()
        assert entry.modified != original_modified

    def test_update_accessed(self):
        """update_accessed should set accessed timestamp."""
        entry = VaultEntry(key="test", password="secret")
        assert entry.accessed is None
        entry.update_accessed()
        assert entry.accessed is not None


class TestVault:
    """Tests for Vault container."""

    def test_create_empty_vault(self):
        """Create empty vault."""
        vault = Vault()
        assert vault.version == VaultFormat.V2_VAULT.value
        assert vault.entries == []
        assert vault.created is not None
        assert vault.modified is not None
        assert "total_entries" in vault.metadata
        assert vault.metadata["total_entries"] == 0

    def test_add_entry_to_vault(self):
        """Add entry to vault."""
        vault = Vault()
        entry = VaultEntry(key="test", password="secret")
        vault.add_entry(entry)
        assert len(vault.entries) == 1
        assert vault.entries[0].key == "test"
        assert vault.metadata["total_entries"] == 1

    def test_add_duplicate_key_raises_error(self):
        """Adding duplicate key should raise ValueError."""
        vault = Vault()
        entry1 = VaultEntry(key="test", password="secret1")
        entry2 = VaultEntry(key="test", password="secret2")
        vault.add_entry(entry1)
        with pytest.raises(ValueError, match="already exists"):
            vault.add_entry(entry2)

    def test_get_entry(self):
        """Get entry by key."""
        vault = Vault()
        entry = VaultEntry(key="test", password="secret")
        vault.add_entry(entry)

        retrieved = vault.get_entry("test")
        assert retrieved is not None
        assert retrieved.key == "test"
        assert retrieved.password == "secret"

    def test_get_nonexistent_entry(self):
        """Get nonexistent entry returns None."""
        vault = Vault()
        retrieved = vault.get_entry("nonexistent")
        assert retrieved is None

    def test_get_entry_updates_accessed(self):
        """Getting entry should update accessed timestamp."""
        vault = Vault()
        entry = VaultEntry(key="test", password="secret")
        vault.add_entry(entry)

        assert entry.accessed is None
        vault.get_entry("test")
        assert entry.accessed is not None

    def test_has_entry(self):
        """has_entry should check if key exists."""
        vault = Vault()
        entry = VaultEntry(key="test", password="secret")
        vault.add_entry(entry)

        assert vault.has_entry("test") is True
        assert vault.has_entry("nonexistent") is False

    def test_list_keys(self):
        """list_keys should return all entry keys."""
        vault = Vault()
        vault.add_entry(VaultEntry(key="gmail", password="pass1"))
        vault.add_entry(VaultEntry(key="github", password="pass2"))
        vault.add_entry(VaultEntry(key="twitter", password="pass3"))

        keys = vault.list_keys()
        assert len(keys) == 3
        assert "gmail" in keys
        assert "github" in keys
        assert "twitter" in keys

    def test_update_entry(self):
        """Update existing entry."""
        vault = Vault()
        entry = VaultEntry(key="test", password="old", username="olduser")
        vault.add_entry(entry)

        success = vault.update_entry("test", password="new", username="newuser")
        assert success is True

        updated = vault.get_entry("test")
        assert updated.password == "new"
        assert updated.username == "newuser"

    def test_update_nonexistent_entry(self):
        """Update nonexistent entry returns False."""
        vault = Vault()
        success = vault.update_entry("nonexistent", password="new")
        assert success is False

    def test_update_entry_updates_modified(self):
        """Updating entry should update modified timestamp."""
        vault = Vault()
        entry = VaultEntry(key="test", password="old")
        vault.add_entry(entry)

        original_modified = entry.modified
        import time

        time.sleep(0.01)
        vault.update_entry("test", password="new")

        updated = vault.get_entry("test")
        assert updated.modified != original_modified

    def test_delete_entry(self):
        """Delete entry from vault."""
        vault = Vault()
        vault.add_entry(VaultEntry(key="test", password="secret"))

        assert len(vault.entries) == 1
        success = vault.delete_entry("test")
        assert success is True
        assert len(vault.entries) == 0
        assert vault.metadata["total_entries"] == 0

    def test_delete_nonexistent_entry(self):
        """Delete nonexistent entry returns False."""
        vault = Vault()
        success = vault.delete_entry("nonexistent")
        assert success is False

    def test_vault_to_dict(self):
        """Vault should convert to dictionary."""
        vault = Vault()
        vault.add_entry(VaultEntry(key="test", password="secret"))

        data = vault.to_dict()
        assert isinstance(data, dict)
        assert data["version"] == VaultFormat.V2_VAULT.value
        assert len(data["entries"]) == 1
        assert data["entries"][0]["key"] == "test"

    def test_vault_from_dict(self):
        """Vault should create from dictionary."""
        data = {
            "version": "2.0",
            "created": "2025-01-14T12:00:00Z",
            "modified": "2025-01-14T12:00:00Z",
            "entries": [
                {
                    "key": "test",
                    "password": "secret",
                    "username": None,
                    "url": None,
                    "notes": None,
                    "tags": [],
                    "totp_secret": None,
                    "created": "2025-01-14T12:00:00Z",
                    "modified": "2025-01-14T12:00:00Z",
                    "accessed": None,
                }
            ],
            "metadata": {"total_entries": 1},
        }

        vault = Vault.from_dict(data)
        assert vault.version == "2.0"
        assert len(vault.entries) == 1
        assert vault.entries[0].key == "test"


class TestVaultOperations:
    """Tests for vault operation functions."""

    def test_create_vault(self):
        """create_vault should return empty vault."""
        vault = create_vault()
        assert isinstance(vault, Vault)
        assert len(vault.entries) == 0

    def test_add_entry_function(self):
        """add_entry function should add entry to vault."""
        vault = create_vault()
        entry = add_entry(
            vault,
            key="gmail",
            password="secret",
            username="user@gmail.com",
            url="https://gmail.com",
        )

        assert isinstance(entry, VaultEntry)
        assert len(vault.entries) == 1
        assert vault.entries[0].key == "gmail"

    def test_get_entry_function(self):
        """get_entry function should retrieve entry."""
        vault = create_vault()
        add_entry(vault, key="test", password="secret")

        entry = get_entry(vault, "test")
        assert entry is not None
        assert entry.key == "test"

    def test_list_entries_function(self):
        """list_entries function should return keys."""
        vault = create_vault()
        add_entry(vault, key="gmail", password="pass1")
        add_entry(vault, key="github", password="pass2")

        keys = list_entries(vault)
        assert len(keys) == 2
        assert "gmail" in keys
        assert "github" in keys

    def test_update_entry_function(self):
        """update_entry function should update entry."""
        vault = create_vault()
        add_entry(vault, key="test", password="old")

        success = update_entry(vault, "test", password="new")
        assert success is True

        entry = get_entry(vault, "test")
        assert entry.password == "new"

    def test_delete_entry_function(self):
        """delete_entry function should delete entry."""
        vault = create_vault()
        add_entry(vault, key="test", password="secret")

        success = delete_entry(vault, "test")
        assert success is True
        assert len(vault.entries) == 0


class TestVaultSerialization:
    """Tests for vault JSON serialization."""

    def test_vault_to_json(self):
        """vault_to_json should serialize to JSON string."""
        vault = create_vault()
        add_entry(vault, key="test", password="secret")

        json_str = vault_to_json(vault)
        assert isinstance(json_str, str)

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["version"] == "2.0"
        assert len(data["entries"]) == 1

    def test_vault_to_json_pretty(self):
        """vault_to_json with pretty=True should indent."""
        vault = create_vault()
        add_entry(vault, key="test", password="secret")

        json_str = vault_to_json(vault, pretty=True)
        assert "\n" in json_str  # Has newlines
        assert "  " in json_str  # Has indentation

    def test_vault_from_json(self):
        """vault_from_json should deserialize from JSON string."""
        json_str = """
        {
            "version": "2.0",
            "created": "2025-01-14T12:00:00Z",
            "modified": "2025-01-14T12:00:00Z",
            "entries": [
                {
                    "key": "test",
                    "password": "secret",
                    "username": null,
                    "url": null,
                    "notes": null,
                    "tags": [],
                    "totp_secret": null,
                    "created": "2025-01-14T12:00:00Z",
                    "modified": "2025-01-14T12:00:00Z",
                    "accessed": null
                }
            ],
            "metadata": {"total_entries": 1}
        }
        """

        vault = vault_from_json(json_str)
        assert isinstance(vault, Vault)
        assert len(vault.entries) == 1
        assert vault.entries[0].key == "test"

    def test_vault_from_json_invalid(self):
        """vault_from_json should raise on invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            vault_from_json("not valid json")

    def test_vault_from_json_missing_entries(self):
        """vault_from_json should raise if missing entries field."""
        json_str = '{"version": "2.0"}'
        with pytest.raises(ValueError, match="missing 'entries'"):
            vault_from_json(json_str)

    def test_roundtrip_serialization(self):
        """Vault should survive serialization roundtrip."""
        vault1 = create_vault()
        add_entry(vault1, key="gmail", password="pass1", username="user@gmail.com")
        add_entry(vault1, key="github", password="pass2", url="https://github.com")

        json_str = vault_to_json(vault1)
        vault2 = vault_from_json(json_str)

        assert len(vault2.entries) == 2
        assert vault2.get_entry("gmail").password == "pass1"
        assert vault2.get_entry("github").password == "pass2"


class TestFormatDetection:
    """Tests for format auto-detection."""

    def test_detect_vault_format(self):
        """detect_format should recognize vault JSON."""
        vault = create_vault()
        add_entry(vault, key="test", password="secret")
        json_str = vault_to_json(vault)

        format_type = detect_format(json_str)
        assert format_type == VaultFormat.V2_VAULT

    def test_detect_single_password_format(self):
        """detect_format should recognize single password."""
        password = "MySinglePassword123!"
        format_type = detect_format(password)
        assert format_type == VaultFormat.V1_SINGLE

    def test_detect_format_bytes(self):
        """detect_format should handle bytes input."""
        vault = create_vault()
        add_entry(vault, key="test", password="secret")
        json_bytes = vault_to_json(vault).encode("utf-8")

        format_type = detect_format(json_bytes)
        assert format_type == VaultFormat.V2_VAULT

    def test_parse_payload_vault(self):
        """parse_payload should return Vault for vault format."""
        vault = create_vault()
        add_entry(vault, key="test", password="secret")
        json_str = vault_to_json(vault)

        parsed = parse_payload(json_str)
        assert isinstance(parsed, Vault)
        assert len(parsed.entries) == 1

    def test_parse_payload_single(self):
        """parse_payload should return string for single password."""
        password = "MySinglePassword123!"
        parsed = parse_payload(password)
        assert isinstance(parsed, str)
        assert parsed == password

    def test_single_password_to_vault(self):
        """single_password_to_vault should convert password to vault."""
        password = "MySinglePassword123!"
        vault = single_password_to_vault(password)

        assert isinstance(vault, Vault)
        assert len(vault.entries) == 1
        assert vault.entries[0].key == "default"
        assert vault.entries[0].password == password


class TestPasswordGenerator:
    """Tests for password generator."""

    def test_generate_password_default(self):
        """Generate password with default settings."""
        password = generate_password()
        assert len(password) == 16
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)

    def test_generate_password_custom_length(self):
        """Generate password with custom length."""
        password = generate_password(length=32)
        assert len(password) == 32

    def test_generate_password_no_symbols(self):
        """Generate password without symbols."""
        password = generate_password(use_symbols=False)
        assert not any(c in "!@#$%^&*()" for c in password)

    def test_generate_password_only_digits(self):
        """Generate password with only digits."""
        password = generate_password(
            length=10,
            use_lowercase=False,
            use_uppercase=False,
            use_digits=True,
            use_symbols=False,
        )
        assert len(password) == 10
        assert password.isdigit()

    def test_password_generator_class(self):
        """PasswordGenerator class should work."""
        gen = PasswordGenerator(length=20, use_symbols=False)
        password = gen.generate()
        assert len(password) == 20
        assert not any(c in "!@#$%^&*()" for c in password)

    def test_password_generator_multiple(self):
        """Generate multiple passwords."""
        gen = PasswordGenerator()
        passwords = gen.generate_multiple(count=5)
        assert len(passwords) == 5
        assert len(set(passwords)) == 5  # All unique

    def test_generate_passphrase(self):
        """Generate memorable passphrase."""
        passphrase = generate_passphrase(word_count=4)
        words = passphrase.split("-")
        assert len(words) == 4

    def test_estimate_entropy(self):
        """Estimate password entropy."""
        # Weak password
        weak_entropy = estimate_entropy("password")
        assert weak_entropy < 40

        # Strong password
        strong = "Xk9$mP2!qL5@wN8#"
        strong_entropy = estimate_entropy(strong)
        assert strong_entropy > 80

    def test_assess_password_strength(self):
        """Assess password strength using zxcvbn."""
        # Now returns (label, score) instead of (label, entropy)
        weak_label, weak_score = assess_password_strength("pass")
        assert weak_label in ["Very Weak", "Weak"]  # zxcvbn might rate "pass" as 0 or 1
        assert weak_score <= 1  # Score 0-1 for weak passwords

        strong_label, strong_score = assess_password_strength("Xk9$mP2!qL5@wN8#vR3^")
        assert strong_label in ["Strong", "Very Strong"]
        assert strong_score >= 3  # Score 3-4 for strong passwords

    def test_password_generator_no_charsets_raises_error(self):
        """Should raise ValueError when all charsets are disabled."""
        import pytest

        with pytest.raises(ValueError, match="At least one character set must be enabled"):
            PasswordGenerator(
                use_lowercase=False,
                use_uppercase=False,
                use_digits=False,
                use_symbols=False,
            )

    def test_password_generator_exclude_ambiguous(self):
        """Should exclude ambiguous characters when requested."""
        gen = PasswordGenerator(length=100, exclude_ambiguous=True)
        password = gen.generate()

        # Check that ambiguous characters are not present
        ambiguous = "il1Lo0O"
        assert not any(c in ambiguous for c in password)

    def test_password_meets_requirements_lowercase(self):
        """Generated password should meet lowercase requirement."""
        gen = PasswordGenerator(
            length=20, use_lowercase=True, use_uppercase=False, use_digits=False, use_symbols=False
        )
        password = gen.generate()

        # Should contain at least one lowercase letter
        assert any(c.islower() for c in password)

    def test_password_meets_requirements_uppercase(self):
        """Generated password should meet uppercase requirement."""
        gen = PasswordGenerator(
            length=20, use_lowercase=False, use_uppercase=True, use_digits=False, use_symbols=False
        )
        password = gen.generate()

        # Should contain at least one uppercase letter
        assert any(c.isupper() for c in password)

    def test_password_meets_requirements_symbols(self):
        """Generated password should meet symbols requirement."""
        gen = PasswordGenerator(
            length=20, use_lowercase=False, use_uppercase=False, use_digits=False, use_symbols=True
        )
        password = gen.generate()

        # Should contain at least one symbol
        symbols = "!@#$%^&*()-_=+[]{}|;:,.<>?"
        assert any(c in symbols for c in password)

    def test_estimate_entropy_empty_charset(self):
        """Should return 0.0 for passwords with no recognizable characters."""
        # Test with empty string or only whitespace
        entropy = estimate_entropy("")
        assert entropy == 0.0
