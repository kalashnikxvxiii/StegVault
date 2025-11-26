"""
Core data structures for Gallery management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json


@dataclass
class VaultMetadata:
    """Metadata for a vault image in the gallery."""

    name: str
    image_path: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    entry_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    vault_id: Optional[int] = None  # Database ID

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "image_path": self.image_path,
            "description": self.description,
            "tags": self.tags,
            "entry_count": self.entry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "vault_id": self.vault_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VaultMetadata":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            image_path=data["image_path"],
            description=data.get("description"),
            tags=data.get("tags", []),
            entry_count=data.get("entry_count", 0),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
            ),
            last_accessed=(
                datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
            ),
            vault_id=data.get("vault_id"),
        )


@dataclass
class VaultEntryCache:
    """Cached entry metadata for cross-vault search."""

    vault_id: int
    entry_key: str
    username: Optional[str] = None
    url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    has_totp: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cache_id: Optional[int] = None  # Database ID

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "vault_id": self.vault_id,
            "entry_key": self.entry_key,
            "username": self.username,
            "url": self.url,
            "tags": self.tags,
            "has_totp": self.has_totp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cache_id": self.cache_id,
        }


class Gallery:
    """
    Gallery manager for multiple vault images.

    Provides centralized management of vault metadata and cross-vault search.
    """

    def __init__(self, db_path: str):
        """
        Initialize gallery with database path.

        Args:
            db_path: Path to SQLite database file
        """
        from stegvault.gallery.db import GalleryDB

        self.db = GalleryDB(db_path)

    def add_vault(
        self,
        name: str,
        image_path: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> VaultMetadata:
        """
        Add a vault to the gallery.

        Args:
            name: Unique name for the vault
            image_path: Path to vault image file
            description: Optional description
            tags: Optional list of tags

        Returns:
            VaultMetadata object
        """
        from stegvault.gallery.operations import add_vault

        return add_vault(self.db, name, image_path, description, tags)

    def remove_vault(self, name: str) -> bool:
        """
        Remove a vault from the gallery.

        Args:
            name: Name of vault to remove

        Returns:
            True if removed, False if not found
        """
        from stegvault.gallery.operations import remove_vault

        return remove_vault(self.db, name)

    def list_vaults(self, tag: Optional[str] = None) -> List[VaultMetadata]:
        """
        List all vaults in the gallery.

        Args:
            tag: Optional tag filter

        Returns:
            List of VaultMetadata objects
        """
        from stegvault.gallery.operations import list_vaults

        return list_vaults(self.db, tag)

    def get_vault(self, name: str) -> Optional[VaultMetadata]:
        """
        Get vault metadata by name.

        Args:
            name: Vault name

        Returns:
            VaultMetadata or None if not found
        """
        from stegvault.gallery.operations import get_vault

        return get_vault(self.db, name)

    def refresh_vault(self, name: str, passphrase: str) -> VaultMetadata:
        """
        Refresh vault metadata by reading the vault image.

        Args:
            name: Vault name
            passphrase: Vault passphrase for decryption

        Returns:
            Updated VaultMetadata
        """
        from stegvault.gallery.operations import refresh_vault

        return refresh_vault(self.db, name, passphrase)

    def search(
        self,
        query: str,
        vault_name: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Search across vaults.

        Args:
            query: Search query
            vault_name: Optional vault name to limit search
            fields: Optional list of fields to search

        Returns:
            List of matching entries with vault info
        """
        from stegvault.gallery.search import search_gallery

        return search_gallery(self.db, query, vault_name, fields)

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
