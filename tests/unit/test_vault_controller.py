"""
Tests for VaultController.

Tests all vault CRUD operations at the controller level.
"""

import tempfile
from pathlib import Path

import pytest
import numpy as np
from PIL import Image

from stegvault.app.controllers.vault_controller import VaultController
from stegvault.vault import create_vault, add_entry


class TestVaultController:
    """Test VaultController CRUD operations."""

    @pytest.fixture
    def controller(self):
        """Create VaultController instance."""
        return VaultController()

    @pytest.fixture
    def test_image(self, tmp_path):
        """Create a test PNG image."""
        img_path = tmp_path / "test.png"
        img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode="RGB")
        img.save(img_path)
        return str(img_path)

    @pytest.fixture
    def vault_with_entries(self):
        """Create vault with test entries."""
        vault = create_vault()
        add_entry(vault, "gmail", "password1", username="user@gmail.com")
        add_entry(vault, "github", "password2", username="githubuser")
        return vault

    def test_create_new_vault(self, controller):
        """Should create new vault with first entry."""
        vault, success, error = controller.create_new_vault(
            key="test",
            password="secret",
            username="testuser",
            url="https://example.com",
        )

        assert success is True
        assert error is None
        assert vault is not None
        assert vault.has_entry("test")
        entry = vault.get_entry("test")
        assert entry.password == "secret"
        assert entry.username == "testuser"

    def test_create_new_vault_minimal(self, controller):
        """Should create vault with minimal fields."""
        vault, success, error = controller.create_new_vault(key="simple", password="pass")

        assert success is True
        assert vault is not None
        assert vault.has_entry("simple")

    def test_add_vault_entry(self, controller):
        """Should add entry to existing vault."""
        # Create initial vault
        vault, _, _ = controller.create_new_vault(key="first", password="pass1")

        # Add another entry
        vault, success, error = controller.add_vault_entry(
            vault, key="second", password="pass2", username="user2"
        )

        assert success is True
        assert error is None
        assert vault.has_entry("second")
        assert len(vault.entries) == 2

    def test_add_duplicate_key(self, controller):
        """Should fail to add entry with duplicate key."""
        vault, _, _ = controller.create_new_vault(key="test", password="pass")

        # Try to add with same key
        vault, success, error = controller.add_vault_entry(vault, key="test", password="newpass")

        assert success is False
        assert error is not None
        assert "already exists" in error

    def test_get_vault_entry(self, controller, vault_with_entries):
        """Should retrieve entry by key."""
        result = controller.get_vault_entry(vault_with_entries, "gmail")

        assert result.success is True
        assert result.error is None
        assert result.entry is not None
        assert result.entry.password == "password1"
        assert result.entry.username == "user@gmail.com"

    def test_get_nonexistent_entry(self, controller, vault_with_entries):
        """Should fail to get nonexistent entry."""
        result = controller.get_vault_entry(vault_with_entries, "nonexistent")

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error
        assert result.entry is None

    def test_update_vault_entry(self, controller, vault_with_entries):
        """Should update existing entry."""
        vault, success, error = controller.update_vault_entry(
            vault_with_entries, key="gmail", password="new_password", username="newuser"
        )

        assert success is True
        assert error is None
        entry = vault.get_entry("gmail")
        assert entry.password == "new_password"
        assert entry.username == "newuser"

    def test_update_nonexistent_entry(self, controller, vault_with_entries):
        """Should fail to update nonexistent entry."""
        vault, success, error = controller.update_vault_entry(
            vault_with_entries, key="nonexistent", password="newpass"
        )

        assert success is False
        assert error is not None
        assert "not found" in error

    def test_delete_vault_entry(self, controller, vault_with_entries):
        """Should delete entry from vault."""
        initial_count = len(vault_with_entries.entries)

        vault, success, error = controller.delete_vault_entry(vault_with_entries, "gmail")

        assert success is True
        assert error is None
        assert not vault.has_entry("gmail")
        assert len(vault.entries) == initial_count - 1

    def test_delete_nonexistent_entry(self, controller, vault_with_entries):
        """Should fail to delete nonexistent entry."""
        vault, success, error = controller.delete_vault_entry(vault_with_entries, "nonexistent")

        assert success is False
        assert error is not None
        assert "not found" in error

    def test_list_vault_entries(self, controller, vault_with_entries):
        """Should list all entry keys."""
        keys = controller.list_vault_entries(vault_with_entries)

        assert len(keys) == 2
        assert "gmail" in keys
        assert "github" in keys

    def test_save_and_load_vault(self, controller, test_image, tmp_path):
        """Should save and load vault from image."""
        # Create vault
        vault, _, _ = controller.create_new_vault(
            key="test", password="secret", username="testuser"
        )

        # Save to image
        output_path = str(tmp_path / "vault.png")
        save_result = controller.save_vault(
            vault, output_path, "passphrase", cover_image=test_image
        )

        assert save_result.success is True
        assert save_result.error is None

        # Load from image
        load_result = controller.load_vault(output_path, "passphrase")

        assert load_result.success is True
        assert load_result.error is None
        assert load_result.vault is not None
        assert load_result.vault.has_entry("test")

    def test_load_vault_wrong_passphrase(self, controller, test_image, tmp_path):
        """Should fail to load vault with wrong passphrase."""
        # Create and save vault
        vault, _, _ = controller.create_new_vault(key="test", password="secret")
        output_path = str(tmp_path / "vault.png")
        controller.save_vault(vault, output_path, "correct_pass", cover_image=test_image)

        # Try to load with wrong passphrase
        load_result = controller.load_vault(output_path, "wrong_pass")

        assert load_result.success is False
        assert load_result.error is not None
        assert load_result.vault is None

    def test_load_nonexistent_image(self, controller):
        """Should fail to load from nonexistent image."""
        result = controller.load_vault("/nonexistent/image.png", "passphrase")

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error or "Unsupported" in result.error

    def test_check_image_capacity(self, controller, test_image):
        """Should check image capacity."""
        capacity, success, error = controller.check_image_capacity(test_image)

        assert success is True
        assert error is None
        assert capacity > 0

    def test_check_nonexistent_image_capacity(self, controller):
        """Should fail to check capacity of nonexistent image."""
        capacity, success, error = controller.check_image_capacity("/nonexistent/image.png")

        assert success is False
        assert error is not None
        assert "not found" in error or "Unsupported" in error
        assert capacity == 0

    def test_get_vault_entry_not_found(self, controller):
        """Should return error when entry not found."""
        vault, _, _ = controller.create_new_vault(key="test", password="pass")

        result = controller.get_vault_entry(vault, "nonexistent")

        assert result.success is False
        assert "not found" in result.error.lower()
        assert result.entry is None

    def test_update_vault_entry_not_found(self, controller):
        """Should fail to update nonexistent entry."""
        vault, _, _ = controller.create_new_vault(key="test", password="pass")

        vault, success, error = controller.update_vault_entry(vault, "nonexistent", password="new")

        assert success is False
        assert "not found" in error.lower()

    def test_delete_vault_entry_not_found(self, controller):
        """Should fail to delete nonexistent entry."""
        vault, _, _ = controller.create_new_vault(key="test", password="pass")

        vault, success, error = controller.delete_vault_entry(vault, "nonexistent")

        assert success is False
        assert "not found" in error.lower()

    def test_save_vault_insufficient_capacity(self, controller, tmp_path):
        """Should fail to save vault if image too small."""
        # Create very small image (insufficient capacity)
        small_img_path = tmp_path / "small.png"
        img_array = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode="RGB")
        img.save(small_img_path)

        # Create vault with large entry
        vault, _, _ = controller.create_new_vault(key="test", password="x" * 1000, notes="y" * 1000)

        # Try to save
        output_path = str(tmp_path / "output.png")
        result = controller.save_vault(
            vault, output_path, "passphrase", cover_image=str(small_img_path)
        )

        # Should fail due to insufficient capacity
        assert result.success is False
        assert "insufficient" in result.error.lower() or "capacity" in result.error.lower()

    def test_roundtrip_with_all_fields(self, controller, test_image, tmp_path):
        """Should preserve all entry fields in roundtrip."""
        # Create vault with all fields
        vault, _, _ = controller.create_new_vault(
            key="complete",
            password="secret",
            username="user@example.com",
            url="https://example.com",
            notes="Test notes",
            tags=["work", "important"],
            totp_secret="BASE32SECRET",
        )

        # Save and load
        output_path = str(tmp_path / "vault.png")
        controller.save_vault(vault, output_path, "pass", cover_image=test_image)
        load_result = controller.load_vault(output_path, "pass")

        assert load_result.success
        entry = load_result.vault.get_entry("complete")
        assert entry.password == "secret"
        assert entry.username == "user@example.com"
        assert entry.url == "https://example.com"
        assert entry.notes == "Test notes"
        assert entry.tags == ["work", "important"]
        assert entry.totp_secret == "BASE32SECRET"
