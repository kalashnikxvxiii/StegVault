"""
Tests for JSON output formatting module.

Tests all JSON output helper functions to achieve 100% coverage.
"""

import json
import pytest

from stegvault.utils.json_output import (
    JSONOutput,
    backup_success,
    restore_success,
    check_success,
    vault_create_success,
    vault_add_success,
    vault_get_success,
    vault_list_success,
    vault_update_success,
    vault_delete_success,
    vault_export_success,
    vault_import_success,
    vault_totp_success,
    vault_search_success,
    batch_success,
    gallery_init_success,
    gallery_add_success,
    gallery_list_success,
    gallery_remove_success,
    gallery_refresh_success,
    gallery_search_success,
)


class TestJSONOutput:
    """Test JSONOutput class methods."""

    def test_success_basic(self):
        """Should format basic success response."""
        result = JSONOutput.success({"key": "value"})
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"] == {"key": "value"}

    def test_success_with_kwargs(self):
        """Should include additional kwargs in output."""
        result = JSONOutput.success({"key": "value"}, extra_field="extra")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"] == {"key": "value"}
        assert data["extra_field"] == "extra"

    def test_error_basic(self):
        """Should format basic error response."""
        result = JSONOutput.error("Something went wrong")
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_type"] == "error"
        assert data["message"] == "Something went wrong"

    def test_error_with_type(self):
        """Should include custom error type."""
        result = JSONOutput.error("Invalid input", error_type="validation")
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_type"] == "validation"
        assert data["message"] == "Invalid input"

    def test_error_with_kwargs(self):
        """Should include additional error context."""
        result = JSONOutput.error("Entry not found", error_type="not_found", entry_id="missing123")
        data = json.loads(result)

        assert data["status"] == "error"
        assert data["error_type"] == "not_found"
        assert data["message"] == "Entry not found"
        assert data["entry_id"] == "missing123"


class TestBackupRestore:
    """Test backup/restore command formatters."""

    def test_backup_success(self):
        """Should format backup success."""
        result = backup_success(
            output_path="/path/to/backup.png",
            image_format="PNG",
            payload_size=1024,
            capacity=5000,
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["output_path"] == "/path/to/backup.png"
        assert data["data"]["image_format"] == "PNG"
        assert data["data"]["payload_size"] == 1024
        assert data["data"]["capacity"] == 5000

    def test_restore_success(self):
        """Should format restore success."""
        result = restore_success(password="secret123", image_path="/path/to/image.png")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["password"] == "secret123"
        assert data["data"]["image_path"] == "/path/to/image.png"


class TestCheckCommand:
    """Test check command formatter."""

    def test_check_success(self):
        """Should format check success."""
        result = check_success(
            image_path="/path/to/image.png",
            image_format="PNG",
            mode="RGB",
            size=(800, 600),
            capacity=10000,
            max_password_size=9936,
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["image_path"] == "/path/to/image.png"
        assert data["data"]["format"] == "PNG"
        assert data["data"]["mode"] == "RGB"
        assert data["data"]["size"] == {"width": 800, "height": 600}
        assert data["data"]["capacity"] == 10000
        assert data["data"]["max_password_size"] == 9936


class TestVaultCommands:
    """Test vault command formatters."""

    def test_vault_create_success(self):
        """Should format vault create success."""
        result = vault_create_success(
            output_path="/path/to/vault.png", entry_count=1, keys=["gmail"]
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["output_path"] == "/path/to/vault.png"
        assert data["data"]["entry_count"] == 1
        assert data["data"]["keys"] == ["gmail"]

    def test_vault_add_success(self):
        """Should format vault add success."""
        result = vault_add_success(
            output_path="/path/to/vault.png", entry_count=2, key_added="github"
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["output_path"] == "/path/to/vault.png"
        assert data["data"]["entry_count"] == 2
        assert data["data"]["key_added"] == "github"

    def test_vault_get_success_minimal(self):
        """Should format vault get success with minimal fields."""
        result = vault_get_success(key="test", password="secret")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["key"] == "test"
        assert data["data"]["password"] == "secret"
        assert data["data"]["has_totp"] is False

    def test_vault_get_success_full(self):
        """Should format vault get success with all fields."""
        result = vault_get_success(
            key="test",
            password="secret",
            username="user@example.com",
            url="https://example.com",
            notes="Test notes",
            has_totp=True,
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["key"] == "test"
        assert data["data"]["password"] == "secret"
        assert data["data"]["username"] == "user@example.com"
        assert data["data"]["url"] == "https://example.com"
        assert data["data"]["notes"] == "Test notes"
        assert data["data"]["has_totp"] is True

    def test_vault_list_success(self):
        """Should format vault list success."""
        entries = [
            {"key": "gmail", "username": "user@gmail.com", "url": None, "has_totp": False},
            {"key": "github", "username": "user", "url": "https://github.com", "has_totp": True},
        ]
        result = vault_list_success(entries=entries, entry_count=2)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["entries"] == entries
        assert data["data"]["entry_count"] == 2

    def test_vault_update_success(self):
        """Should format vault update success."""
        result = vault_update_success(output_path="/path/to/vault.png", key_updated="gmail")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["output_path"] == "/path/to/vault.png"
        assert data["data"]["key_updated"] == "gmail"

    def test_vault_delete_success(self):
        """Should format vault delete success."""
        result = vault_delete_success(
            output_path="/path/to/vault.png", remaining_entries=1, key_deleted="old"
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["output_path"] == "/path/to/vault.png"
        assert data["data"]["remaining_entries"] == 1
        assert data["data"]["key_deleted"] == "old"

    def test_vault_export_success(self):
        """Should format vault export success."""
        result = vault_export_success(
            output_path="/path/to/export.json", entry_count=5, mode="plaintext"
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["output_path"] == "/path/to/export.json"
        assert data["data"]["entry_count"] == 5
        assert data["data"]["mode"] == "plaintext"

    def test_vault_import_success(self):
        """Should format vault import success."""
        result = vault_import_success(output_path="/path/to/vault.png", entry_count=10)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["output_path"] == "/path/to/vault.png"
        assert data["data"]["entry_count"] == 10

    def test_vault_totp_success_minimal(self):
        """Should format TOTP success without secret."""
        result = vault_totp_success(key="gmail", totp_code="123456", time_remaining=25)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["key"] == "gmail"
        assert data["data"]["totp_code"] == "123456"
        assert data["data"]["time_remaining"] == 25
        assert "totp_secret" not in data["data"]

    def test_vault_totp_success_with_secret(self):
        """Should format TOTP success with secret."""
        result = vault_totp_success(
            key="gmail",
            totp_code="123456",
            time_remaining=25,
            totp_secret="BASE32SECRET",
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["key"] == "gmail"
        assert data["data"]["totp_code"] == "123456"
        assert data["data"]["time_remaining"] == 25
        assert data["data"]["totp_secret"] == "BASE32SECRET"

    def test_vault_search_success(self):
        """Should format vault search success."""
        results = [
            {"key": "gmail", "username": "user@gmail.com"},
            {"key": "github", "username": "user"},
        ]
        result = vault_search_success(results=results, query="git", count=2)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["results"] == results
        assert data["data"]["query"] == "git"
        assert data["data"]["count"] == 2


class TestBatchCommands:
    """Test batch command formatters."""

    def test_batch_success_no_errors(self):
        """Should format batch success with no errors."""
        result = batch_success(successful=5, failed=0, errors=[])
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["successful"] == 5
        assert data["data"]["failed"] == 0
        assert data["data"]["errors"] == []

    def test_batch_success_with_errors(self):
        """Should format batch success with errors."""
        errors = ["Error 1", "Error 2"]
        result = batch_success(successful=3, failed=2, errors=errors)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["successful"] == 3
        assert data["data"]["failed"] == 2
        assert data["data"]["errors"] == errors


class TestGalleryCommands:
    """Test gallery command formatters."""

    def test_gallery_init_success(self):
        """Should format gallery init success."""
        result = gallery_init_success(db_path="/path/to/gallery.db")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["db_path"] == "/path/to/gallery.db"

    def test_gallery_add_success_no_tags(self):
        """Should format gallery add without tags."""
        result = gallery_add_success(name="work-vault", path="/path/to/vault.png", entry_count=10)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["name"] == "work-vault"
        assert data["data"]["path"] == "/path/to/vault.png"
        assert data["data"]["entry_count"] == 10
        assert "tags" not in data["data"]

    def test_gallery_add_success_with_tags(self):
        """Should format gallery add with tags."""
        result = gallery_add_success(
            name="work-vault",
            path="/path/to/vault.png",
            entry_count=10,
            tags=["work", "important"],
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["name"] == "work-vault"
        assert data["data"]["path"] == "/path/to/vault.png"
        assert data["data"]["entry_count"] == 10
        assert data["data"]["tags"] == ["work", "important"]

    def test_gallery_list_success(self):
        """Should format gallery list success."""
        vaults = [
            {"name": "work", "entry_count": 10},
            {"name": "personal", "entry_count": 5},
        ]
        result = gallery_list_success(vaults=vaults, count=2)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["vaults"] == vaults
        assert data["data"]["count"] == 2

    def test_gallery_remove_success(self):
        """Should format gallery remove success."""
        result = gallery_remove_success(name="old-vault")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["name"] == "old-vault"

    def test_gallery_refresh_success(self):
        """Should format gallery refresh success."""
        result = gallery_refresh_success(name="work-vault", entry_count=12)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["name"] == "work-vault"
        assert data["data"]["entry_count"] == 12

    def test_gallery_search_success(self):
        """Should format gallery search success."""
        results = [
            {"vault": "work", "key": "github"},
            {"vault": "personal", "key": "gitlab"},
        ]
        result = gallery_search_success(results=results, query="git", count=2)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["results"] == results
        assert data["data"]["query"] == "git"
        assert data["data"]["count"] == 2
