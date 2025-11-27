"""
Unit tests for Gallery functionality.
"""

import pytest
import tempfile
import os
import sqlite3
from datetime import datetime

from stegvault.gallery import Gallery, VaultMetadata, GalleryDB
from stegvault.gallery.db import GalleryDBError
from stegvault.gallery.operations import GalleryOperationError


class TestGalleryDB:
    """Tests for GalleryDB class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        yield db_path

        # Cleanup
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_init_creates_schema(self, temp_db):
        """Should create database schema on initialization."""
        db = GalleryDB(temp_db)

        # Check tables exist
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('vaults', 'vault_entries_cache')"
        )
        tables = [row[0] for row in cursor.fetchall()]

        assert "vaults" in tables
        assert "vault_entries_cache" in tables

        db.close()

    def test_add_vault(self, temp_db):
        """Should add a vault to database."""
        db = GalleryDB(temp_db)

        vault_id = db.add_vault(
            "test-vault", "/path/to/vault.png", "Test vault", ["work", "personal"]
        )

        assert isinstance(vault_id, int)
        assert vault_id > 0

        # Verify vault exists
        vault = db.get_vault("test-vault")
        assert vault is not None
        assert vault.name == "test-vault"
        assert vault.image_path == "/path/to/vault.png"
        assert vault.description == "Test vault"
        assert vault.tags == ["work", "personal"]

        db.close()

    def test_add_duplicate_vault_fails(self, temp_db):
        """Should fail when adding duplicate vault name."""
        db = GalleryDB(temp_db)

        db.add_vault("test-vault", "/path/to/vault.png")

        with pytest.raises(GalleryDBError, match="already exists"):
            db.add_vault("test-vault", "/path/to/another.png")

        db.close()

    def test_remove_vault(self, temp_db):
        """Should remove a vault from database."""
        db = GalleryDB(temp_db)

        db.add_vault("test-vault", "/path/to/vault.png")
        result = db.remove_vault("test-vault")

        assert result is True
        assert db.get_vault("test-vault") is None

        db.close()

    def test_remove_nonexistent_vault(self, temp_db):
        """Should return False when removing nonexistent vault."""
        db = GalleryDB(temp_db)

        result = db.remove_vault("nonexistent")

        assert result is False

        db.close()

    def test_list_vaults(self, temp_db):
        """Should list all vaults."""
        db = GalleryDB(temp_db)

        db.add_vault("vault1", "/path/to/vault1.png", tags=["work"])
        db.add_vault("vault2", "/path/to/vault2.png", tags=["personal"])

        vaults = db.list_vaults()

        assert len(vaults) == 2
        assert vaults[0].name == "vault1"
        assert vaults[1].name == "vault2"

        db.close()

    def test_list_vaults_by_tag(self, temp_db):
        """Should list vaults filtered by tag."""
        db = GalleryDB(temp_db)

        db.add_vault("vault1", "/path/to/vault1.png", tags=["work"])
        db.add_vault("vault2", "/path/to/vault2.png", tags=["personal"])

        vaults = db.list_vaults(tag="work")

        assert len(vaults) == 1
        assert vaults[0].name == "vault1"

        db.close()

    def test_update_vault(self, temp_db):
        """Should update vault metadata."""
        db = GalleryDB(temp_db)

        db.add_vault("test-vault", "/path/to/vault.png")
        result = db.update_vault(
            "test-vault", description="Updated", tags=["new-tag"], entry_count=5
        )

        assert result is True

        vault = db.get_vault("test-vault")
        assert vault.description == "Updated"
        assert vault.tags == ["new-tag"]
        assert vault.entry_count == 5

        db.close()

    def test_add_entry_cache(self, temp_db):
        """Should add entry to cache."""
        from stegvault.gallery.core import VaultEntryCache

        db = GalleryDB(temp_db)

        vault_id = db.add_vault("test-vault", "/path/to/vault.png")

        entry = VaultEntryCache(
            vault_id=vault_id,
            entry_key="github",
            username="dev",
            url="https://github.com",
            tags=["work", "code"],
            has_totp=True,
        )

        cache_id = db.add_entry_cache(entry)

        assert isinstance(cache_id, int)
        assert cache_id > 0

        db.close()

    def test_clear_vault_cache(self, temp_db):
        """Should clear all cached entries for a vault."""
        from stegvault.gallery.core import VaultEntryCache

        db = GalleryDB(temp_db)

        vault_id = db.add_vault("test-vault", "/path/to/vault.png")

        # Add entries
        for i in range(3):
            entry = VaultEntryCache(vault_id=vault_id, entry_key=f"entry{i}")
            db.add_entry_cache(entry)

        # Clear cache
        db.clear_vault_cache(vault_id)

        # Verify cleared
        results = db.search_entries("entry", vault_id=vault_id)
        assert len(results) == 0

        db.close()

    def test_search_entries(self, temp_db):
        """Should search cached entries."""
        from stegvault.gallery.core import VaultEntryCache

        db = GalleryDB(temp_db)

        vault_id = db.add_vault("test-vault", "/path/to/vault.png")

        # Add entries
        entries = [
            VaultEntryCache(
                vault_id=vault_id, entry_key="github", username="dev", url="https://github.com"
            ),
            VaultEntryCache(
                vault_id=vault_id,
                entry_key="gmail",
                username="user@gmail.com",
                url="https://gmail.com",
            ),
        ]

        for entry in entries:
            db.add_entry_cache(entry)

        # Search
        results = db.search_entries("github")

        assert len(results) == 1
        assert results[0][0].entry_key == "github"

        db.close()

    def test_db_connect_error(self, monkeypatch):
        """Should raise GalleryDBError when connection fails."""
        import sqlite3

        # Mock sqlite3.connect to raise error
        def mock_connect(*args, **kwargs):
            raise sqlite3.Error("Connection failed")

        monkeypatch.setattr(sqlite3, "connect", mock_connect)

        with pytest.raises(GalleryDBError, match="Failed to connect"):
            GalleryDB("/test/path.db")

    def test_schema_initialization_failure(self, temp_db, monkeypatch):
        """Should handle schema initialization errors."""
        import sqlite3
        from unittest.mock import Mock

        # Create a mock connection that raises error on execute
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Schema creation failed")
        mock_cursor.executescript.side_effect = sqlite3.Error("Schema creation failed")
        mock_conn.cursor.return_value = mock_cursor

        original_connect = sqlite3.connect

        def mock_connect(*args, **kwargs):
            if args[0] == temp_db:
                return mock_conn
            return original_connect(*args, **kwargs)

        monkeypatch.setattr(sqlite3, "connect", mock_connect)

        with pytest.raises(GalleryDBError, match="Failed to initialize schema"):
            GalleryDB(temp_db)

    def test_add_vault_db_error(self, temp_db):
        """Should handle database errors when adding vault."""
        from unittest.mock import Mock, patch
        import sqlite3

        db = GalleryDB(temp_db)

        # Replace conn with a mock that raises error on cursor()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Insert failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to add vault"):
            db.add_vault("test-vault", "/path/to/vault.png")

    def test_get_vault_db_error(self, temp_db):
        """Should handle database errors when getting vault."""
        from unittest.mock import Mock
        import sqlite3

        db = GalleryDB(temp_db)

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Query failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to get vault"):
            db.get_vault("test-vault")

    def test_update_vault_db_error(self, temp_db):
        """Should handle database errors when updating vault."""
        from unittest.mock import Mock
        import sqlite3

        db = GalleryDB(temp_db)

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Update failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to update vault"):
            db.update_vault("test-vault", description="New desc")

    def test_remove_vault_db_error(self, temp_db):
        """Should handle database errors when removing vault."""
        from unittest.mock import Mock
        import sqlite3

        db = GalleryDB(temp_db)

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Delete failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to remove vault"):
            db.remove_vault("test-vault")

    def test_list_vaults_db_error(self, temp_db):
        """Should handle database errors when listing vaults."""
        from unittest.mock import Mock
        import sqlite3

        db = GalleryDB(temp_db)

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("List failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to list vaults"):
            db.list_vaults()

    def test_update_last_accessed_db_error(self, temp_db):
        """Should handle database errors when updating last accessed."""
        from unittest.mock import Mock
        import sqlite3

        db = GalleryDB(temp_db)

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Update failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to update last accessed"):
            db.update_last_accessed("test-vault")

    def test_update_vault_no_fields(self, temp_db):
        """Should return False when no fields to update."""
        db = GalleryDB(temp_db)
        db.add_vault("test-vault", "/path/to/vault.png")

        # Call update with no fields
        result = db.update_vault("test-vault")

        assert result is False
        db.close()

    def test_add_entry_cache_db_error(self, temp_db):
        """Should handle database errors when adding entry cache."""
        from unittest.mock import Mock
        import sqlite3
        from stegvault.gallery.core import VaultEntryCache

        db = GalleryDB(temp_db)
        vault_id = db.add_vault("test-vault", "/path/to/vault.png")

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Insert failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        cache_entry = VaultEntryCache(
            vault_id=vault_id,
            entry_key="test",
            username="user",
            url="https://example.com",
            tags=[],
            has_totp=False,
        )

        with pytest.raises(GalleryDBError, match="Failed to add entry cache"):
            db.add_entry_cache(cache_entry)

    def test_clear_vault_cache_db_error(self, temp_db):
        """Should handle database errors when clearing vault cache."""
        from unittest.mock import Mock
        import sqlite3

        db = GalleryDB(temp_db)
        vault_id = db.add_vault("test-vault", "/path/to/vault.png")

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Delete failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to clear vault cache"):
            db.clear_vault_cache(vault_id)

    def test_search_entries_db_error(self, temp_db):
        """Should handle database errors when searching entries."""
        from unittest.mock import Mock
        import sqlite3

        db = GalleryDB(temp_db)

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Search failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to search entries"):
            db.search_entries("test")

    def test_get_vault_by_id(self, temp_db):
        """Should get vault by ID."""
        db = GalleryDB(temp_db)
        vault_id = db.add_vault("test-vault", "/path/to/vault.png", "Test description")

        # Get by ID
        vault = db.get_vault_by_id(vault_id)

        assert vault is not None
        assert vault.vault_id == vault_id
        assert vault.name == "test-vault"
        assert vault.description == "Test description"

        db.close()

    def test_get_vault_by_id_not_found(self, temp_db):
        """Should return None when vault ID doesn't exist."""
        db = GalleryDB(temp_db)

        vault = db.get_vault_by_id(99999)

        assert vault is None
        db.close()

    def test_get_vault_by_id_db_error(self, temp_db):
        """Should handle database errors when getting vault by ID."""
        from unittest.mock import Mock
        import sqlite3

        db = GalleryDB(temp_db)

        # Replace conn with a mock that raises error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Query failed")
        mock_conn.cursor.return_value = mock_cursor
        db.conn = mock_conn

        with pytest.raises(GalleryDBError, match="Failed to get vault"):
            db.get_vault_by_id(1)


class TestGalleryOperations:
    """Tests for Gallery operations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        db = GalleryDB(db_path)
        yield db

        db.close()

        # Cleanup
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except (PermissionError, FileNotFoundError):
            pass

    @pytest.fixture
    def temp_vault_image(self):
        """Create a temporary vault image."""
        import numpy as np
        from PIL import Image
        from stegvault.vault import create_vault, add_entry, vault_to_json
        from stegvault.crypto import encrypt_data
        from stegvault.stego import embed_payload
        from stegvault.utils import serialize_payload

        # Create cover image
        cover_path = tempfile.mktemp(suffix=".png")
        img_array = np.random.randint(0, 256, (400, 600, 3), dtype=np.uint8)
        test_image = Image.fromarray(img_array, mode="RGB")
        test_image.save(cover_path, format="PNG")

        # Create vault
        vault_path = tempfile.mktemp(suffix=".png")
        passphrase = "TestVault123!Pass"

        vault_obj = create_vault()
        add_entry(
            vault_obj,
            "github",
            "password123",
            username="dev",
            url="https://github.com",
            tags=["work"],
        )
        add_entry(
            vault_obj,
            "gmail",
            "password456",
            username="user@gmail.com",
            url="https://gmail.com",
            tags=["personal"],
        )

        # Encrypt and embed
        vault_json = vault_to_json(vault_obj)
        ciphertext, salt, nonce = encrypt_data(vault_json.encode("utf-8"), passphrase)
        payload = serialize_payload(salt, nonce, ciphertext)
        stego_img = embed_payload(cover_path, payload)
        stego_img.save(vault_path)

        yield vault_path, passphrase

        # Cleanup
        for path in [cover_path, vault_path]:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except (PermissionError, FileNotFoundError):
                pass

    def test_add_vault(self, temp_db, temp_vault_image):
        """Should add a vault to gallery."""
        from stegvault.gallery.operations import add_vault

        vault_path, passphrase = temp_vault_image

        vault = add_vault(temp_db, "test-vault", vault_path, "Test vault", ["work"])

        assert vault is not None
        assert vault.name == "test-vault"
        assert os.path.abspath(vault_path) == vault.image_path
        assert vault.description == "Test vault"
        assert vault.tags == ["work"]

    def test_add_vault_with_passphrase_caches_entries(self, temp_db, temp_vault_image):
        """Should cache entries when passphrase is provided."""
        from stegvault.gallery.operations import add_vault

        vault_path, passphrase = temp_vault_image

        # Add vault with passphrase to trigger entry caching
        vault = add_vault(temp_db, "test-vault", vault_path, "Test vault", ["work"], passphrase)

        assert vault is not None
        assert vault.entry_count == 2  # Should have cached 2 entries

    def test_add_nonexistent_vault_fails(self, temp_db):
        """Should fail when adding nonexistent vault image."""
        from stegvault.gallery.operations import add_vault

        with pytest.raises(GalleryOperationError, match="not found"):
            add_vault(temp_db, "test-vault", "/nonexistent/vault.png")

    def test_remove_vault(self, temp_db, temp_vault_image):
        """Should remove a vault from gallery."""
        from stegvault.gallery.operations import add_vault, remove_vault

        vault_path, _ = temp_vault_image
        add_vault(temp_db, "test-vault", vault_path)

        result = remove_vault(temp_db, "test-vault")

        assert result is True

    def test_list_vaults(self, temp_db, temp_vault_image):
        """Should list all vaults."""
        from stegvault.gallery.operations import add_vault, list_vaults

        vault_path, _ = temp_vault_image
        add_vault(temp_db, "test-vault", vault_path, tags=["work"])

        vaults = list_vaults(temp_db)

        assert len(vaults) >= 1
        assert any(v.name == "test-vault" for v in vaults)

    def test_refresh_vault(self, temp_db, temp_vault_image):
        """Should refresh vault metadata."""
        from stegvault.gallery.operations import add_vault, refresh_vault

        vault_path, passphrase = temp_vault_image
        add_vault(temp_db, "test-vault", vault_path)

        vault = refresh_vault(temp_db, "test-vault", passphrase)

        assert vault.entry_count == 2  # github + gmail

    def test_add_vault_db_error(self, temp_db, temp_vault_image):
        """Should handle database errors when adding vault."""
        from stegvault.gallery.operations import add_vault
        from unittest.mock import patch

        vault_path, _ = temp_vault_image

        # Mock db.add_vault to raise GalleryDBError
        with patch.object(temp_db, "add_vault", side_effect=GalleryDBError("Test error")):
            with pytest.raises(GalleryOperationError, match="Test error"):
                add_vault(temp_db, "test-vault", vault_path)

    def test_remove_vault_db_error(self, temp_db):
        """Should handle database errors when removing vault."""
        from stegvault.gallery.operations import remove_vault
        from unittest.mock import patch

        # Mock db.remove_vault to raise GalleryDBError
        with patch.object(temp_db, "remove_vault", side_effect=GalleryDBError("Test error")):
            with pytest.raises(GalleryOperationError, match="Test error"):
                remove_vault(temp_db, "test-vault")

    def test_list_vaults_db_error(self, temp_db):
        """Should handle database errors when listing vaults."""
        from stegvault.gallery.operations import list_vaults
        from unittest.mock import patch

        # Mock db.list_vaults to raise GalleryDBError
        with patch.object(temp_db, "list_vaults", side_effect=GalleryDBError("Test error")):
            with pytest.raises(GalleryOperationError, match="Test error"):
                list_vaults(temp_db)

    def test_get_vault_db_error(self, temp_db):
        """Should handle database errors when getting vault."""
        from stegvault.gallery.operations import get_vault
        from unittest.mock import patch

        # Mock db.get_vault to raise GalleryDBError
        with patch.object(temp_db, "get_vault", side_effect=GalleryDBError("Test error")):
            with pytest.raises(GalleryOperationError, match="Test error"):
                get_vault(temp_db, "test-vault")

    def test_refresh_vault_not_found(self, temp_db):
        """Should fail when refreshing nonexistent vault."""
        from stegvault.gallery.operations import refresh_vault

        with pytest.raises(GalleryOperationError, match="not found"):
            refresh_vault(temp_db, "nonexistent", "password")

    def test_refresh_vault_image_not_found(self, temp_db, temp_vault_image):
        """Should fail when vault image file doesn't exist."""
        from stegvault.gallery.operations import add_vault, refresh_vault

        vault_path, passphrase = temp_vault_image
        add_vault(temp_db, "test-vault", vault_path)

        # Delete the image file
        os.unlink(vault_path)

        with pytest.raises(GalleryOperationError, match="not found"):
            refresh_vault(temp_db, "test-vault", passphrase)

    def test_refresh_vault_with_no_entries(self, temp_db):
        """Should handle vault with None entries (single-password mode)."""
        from stegvault.gallery.operations import add_vault, refresh_vault
        from stegvault.crypto import encrypt_data
        from stegvault.stego import embed_payload
        from stegvault.utils import serialize_payload
        import numpy as np
        from PIL import Image

        # Create single-password vault (not multi-entry vault)
        cover_path = tempfile.mktemp(suffix=".png")
        vault_path = tempfile.mktemp(suffix=".png")

        try:
            # Create cover image
            img_array = np.random.randint(0, 256, (400, 600, 3), dtype=np.uint8)
            test_image = Image.fromarray(img_array, mode="RGB")
            test_image.save(cover_path, format="PNG")

            # Create single-password vault
            passphrase = "TestPass123!"
            password = "MySecret123"
            ciphertext, salt, nonce = encrypt_data(password.encode("utf-8"), passphrase)
            payload = serialize_payload(salt, nonce, ciphertext)
            stego_img = embed_payload(cover_path, payload)
            stego_img.save(vault_path)

            # Add to gallery (temp_db is already a GalleryDB instance)
            add_vault(temp_db, "single-pass-vault", vault_path)

            # Refresh with passphrase (should handle single-password vault)
            # This triggers the vault_obj.entries is None path (lines 181-182)
            refresh_vault(temp_db, "single-pass-vault", passphrase)

            # Verify entry_count is 0 for single-password vaults
            vault = temp_db.get_vault("single-pass-vault")
            assert vault.entry_count == 0

        finally:
            for path in [cover_path, vault_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except (PermissionError, FileNotFoundError):
                    pass

    def test_refresh_vault_db_error(self, temp_db, temp_vault_image):
        """Should handle database errors during refresh vault."""
        from stegvault.gallery.operations import add_vault, refresh_vault
        from unittest.mock import patch

        vault_path, passphrase = temp_vault_image
        add_vault(temp_db, "test-vault", vault_path)

        # Mock db.update_last_accessed to raise GalleryDBError
        with patch.object(
            temp_db, "update_last_accessed", side_effect=GalleryDBError("Test DB error")
        ):
            with pytest.raises(GalleryOperationError, match="Test DB error"):
                refresh_vault(temp_db, "test-vault", passphrase)

    def test_cache_vault_entries_exception(self, temp_db, temp_vault_image):
        """Should handle exceptions when caching vault entries."""
        from stegvault.gallery.operations import add_vault, refresh_vault
        from unittest.mock import patch

        vault_path, passphrase = temp_vault_image
        add_vault(temp_db, "test-vault", vault_path)

        # Mock db.add_entry_cache inside _cache_vault_entries to raise an exception
        # This will trigger after successful decryption/parsing but during caching
        with patch.object(temp_db, "add_entry_cache", side_effect=Exception("Cache add failed")):
            with pytest.raises(GalleryOperationError, match="Failed to cache entries"):
                refresh_vault(temp_db, "test-vault", passphrase)


class TestGallerySearch:
    """Tests for Gallery search functionality."""

    @pytest.fixture
    def gallery_with_vaults(self):
        """Create a gallery with test vaults."""
        import numpy as np
        from PIL import Image
        from stegvault.vault import create_vault, add_entry, vault_to_json
        from stegvault.crypto import encrypt_data
        from stegvault.stego import embed_payload
        from stegvault.utils import serialize_payload

        # Create temp DB
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        gallery = Gallery(db_path)

        # Create test vault images
        vaults = []
        passphrase = "TestVault123!Pass"

        for i, vault_name in enumerate(["work-vault", "personal-vault"]):
            # Create cover image
            cover_path = tempfile.mktemp(suffix=".png")
            img_array = np.random.randint(0, 256, (400, 600, 3), dtype=np.uint8)
            test_image = Image.fromarray(img_array, mode="RGB")
            test_image.save(cover_path, format="PNG")

            # Create vault
            vault_path = tempfile.mktemp(suffix=".png")

            vault_obj = create_vault()
            if vault_name == "work-vault":
                add_entry(
                    vault_obj,
                    "github",
                    "pass123",
                    username="dev",
                    url="https://github.com",
                    tags=["work"],
                )
                add_entry(
                    vault_obj,
                    "jira",
                    "pass456",
                    username="dev",
                    url="https://jira.com",
                    tags=["work"],
                )
            else:
                add_entry(
                    vault_obj,
                    "gmail",
                    "pass789",
                    username="user@gmail.com",
                    url="https://gmail.com",
                    tags=["email"],
                )

            # Encrypt and embed
            vault_json = vault_to_json(vault_obj)
            ciphertext, salt, nonce = encrypt_data(vault_json.encode("utf-8"), passphrase)
            payload = serialize_payload(salt, nonce, ciphertext)
            stego_img = embed_payload(cover_path, payload)
            stego_img.save(vault_path)

            # Add to gallery
            gallery.add_vault(vault_name, vault_path, tags=[vault_name.split("-")[0]])
            gallery.refresh_vault(vault_name, passphrase)

            vaults.append((cover_path, vault_path))

        yield gallery

        # Cleanup
        gallery.close()
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except (PermissionError, FileNotFoundError):
            pass

        for cover_path, vault_path in vaults:
            for path in [cover_path, vault_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except (PermissionError, FileNotFoundError):
                    pass

    def test_search_all_vaults(self, gallery_with_vaults):
        """Should search across all vaults."""
        results = gallery_with_vaults.search("github")

        assert len(results) >= 1
        assert any(r["entry_key"] == "github" for r in results)

    def test_search_specific_vault(self, gallery_with_vaults):
        """Should search in specific vault only."""
        results = gallery_with_vaults.search("github", vault_name="work-vault")

        assert len(results) >= 1
        assert all(r["vault_name"] == "work-vault" for r in results)

    def test_search_no_results(self, gallery_with_vaults):
        """Should return empty list when no matches."""
        results = gallery_with_vaults.search("nonexistent")

        assert len(results) == 0

    def test_search_by_username(self, gallery_with_vaults):
        """Should search by username field."""
        results = gallery_with_vaults.search("user@gmail.com", fields=["username"])

        assert len(results) >= 1
        assert any(r["entry_key"] == "gmail" for r in results)

    def test_search_nonexistent_vault(self, gallery_with_vaults):
        """Should raise error when searching nonexistent vault."""
        from stegvault.gallery.operations import GalleryOperationError
        from stegvault.gallery.search import search_gallery

        with pytest.raises(GalleryOperationError) as exc_info:
            search_gallery(gallery_with_vaults.db, "test", vault_name="nonexistent")

        assert "not found" in str(exc_info.value)

    def test_search_by_tag(self, gallery_with_vaults):
        """Should search entries by tag."""
        from stegvault.gallery.search import search_by_tag

        results = search_by_tag(gallery_with_vaults.db, "work")

        assert len(results) >= 2  # github and jira
        assert all(r["vault_name"] == "work-vault" for r in results)
        assert any(r["entry_key"] == "github" for r in results)
        assert any(r["entry_key"] == "jira" for r in results)

    def test_search_by_tag_specific_vault(self, gallery_with_vaults):
        """Should search by tag in specific vault only."""
        from stegvault.gallery.search import search_by_tag

        results = search_by_tag(gallery_with_vaults.db, "work", vault_name="work-vault")

        assert len(results) >= 2
        assert all(r["vault_name"] == "work-vault" for r in results)

    def test_search_by_tag_no_results(self, gallery_with_vaults):
        """Should return empty list when tag not found."""
        from stegvault.gallery.search import search_by_tag

        results = search_by_tag(gallery_with_vaults.db, "nonexistent-tag")

        assert len(results) == 0

    def test_search_by_tag_nonexistent_vault(self, gallery_with_vaults):
        """Should raise error when searching nonexistent vault by tag."""
        from stegvault.gallery.operations import GalleryOperationError
        from stegvault.gallery.search import search_by_tag

        with pytest.raises(GalleryOperationError) as exc_info:
            search_by_tag(gallery_with_vaults.db, "work", vault_name="nonexistent")

        assert "not found" in str(exc_info.value)

    def test_search_by_url(self, gallery_with_vaults):
        """Should search entries by URL pattern."""
        from stegvault.gallery.search import search_by_url

        results = search_by_url(gallery_with_vaults.db, "github.com")

        assert len(results) >= 1
        assert any(r["entry_key"] == "github" for r in results)

    def test_search_by_url_specific_vault(self, gallery_with_vaults):
        """Should search by URL in specific vault only."""
        from stegvault.gallery.search import search_by_url

        results = search_by_url(gallery_with_vaults.db, "github.com", vault_name="work-vault")

        assert len(results) >= 1
        assert all(r["vault_name"] == "work-vault" for r in results)

    def test_search_handles_db_error(self, gallery_with_vaults):
        """Should handle database errors gracefully."""
        from stegvault.gallery.operations import GalleryOperationError
        from stegvault.gallery.search import search_gallery
        from stegvault.gallery.db import GalleryDBError
        from unittest.mock import patch

        # Mock db.search_entries to raise GalleryDBError
        with patch.object(
            gallery_with_vaults.db, "search_entries", side_effect=GalleryDBError("Test error")
        ):
            with pytest.raises(GalleryOperationError) as exc_info:
                search_gallery(gallery_with_vaults.db, "test")

            assert "Search failed" in str(exc_info.value)


class TestGallery:
    """Tests for Gallery class."""

    @pytest.fixture
    def temp_gallery(self):
        """Create a temporary gallery."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        gallery = Gallery(db_path)
        yield gallery

        gallery.close()

        # Cleanup
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_context_manager(self):
        """Should work as context manager."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            with Gallery(db_path) as g:
                assert g.db is not None
                assert g.db.conn is not None

            # Connection should be closed after context
            assert g.db.conn is None

        finally:
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
            except (PermissionError, FileNotFoundError):
                pass

    def test_list_empty_gallery(self, temp_gallery):
        """Should return empty list for empty gallery."""
        vaults = temp_gallery.list_vaults()

        assert len(vaults) == 0

    def test_vault_metadata_to_dict(self):
        """Should convert VaultMetadata to dict."""
        from stegvault.gallery.core import VaultMetadata
        from datetime import datetime

        vault = VaultMetadata(
            name="test-vault",
            image_path="/test/vault.png",
            description="Test",
            tags=["work"],
            entry_count=2,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_accessed=None,
            vault_id=1,
        )

        vault_dict = vault.to_dict()

        assert vault_dict["name"] == "test-vault"
        assert vault_dict["image_path"] == "/test/vault.png"
        assert "created_at" in vault_dict
        assert "vault_id" in vault_dict

    def test_vault_metadata_from_dict(self):
        """Should create VaultMetadata from dict."""
        from stegvault.gallery.core import VaultMetadata
        from datetime import datetime

        data = {
            "name": "test",
            "image_path": "/test/path.png",
            "description": "Test",
            "tags": ["work"],
            "entry_count": 5,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_accessed": None,
            "vault_id": 1,
        }

        vault = VaultMetadata.from_dict(data)

        assert vault.name == "test"
        assert vault.image_path == "/test/path.png"
        assert vault.entry_count == 5

    def test_cached_entry_to_dict(self):
        """Should convert VaultEntryCache to dict."""
        from stegvault.gallery.core import VaultEntryCache

        entry = VaultEntryCache(
            vault_id=1,
            entry_key="github",
            username="dev",
            url="https://github.com",
            tags=["work"],
            has_totp=False,
        )

        entry_dict = entry.to_dict()

        assert entry_dict["entry_key"] == "github"
        assert entry_dict["username"] == "dev"
        assert entry_dict["tags"] == ["work"]

    def test_gallery_get_vault(self, temp_gallery):
        """Should get vault by name using Gallery.get_vault method."""
        # Test that Gallery.get_vault returns None for non-existent vault
        vault = temp_gallery.get_vault("non-existent")

        assert vault is None
