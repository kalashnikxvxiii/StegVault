"""
Gallery operations for vault management.
"""

import os
from typing import List, Optional
from datetime import datetime

from stegvault.gallery.core import VaultMetadata, VaultEntryCache
from stegvault.gallery.db import GalleryDB, GalleryDBError


class GalleryOperationError(Exception):
    """Gallery operation error."""

    pass


def add_vault(
    db: GalleryDB,
    name: str,
    image_path: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    passphrase: Optional[str] = None,
) -> VaultMetadata:
    """
    Add a vault to the gallery.

    Args:
        db: GalleryDB instance
        name: Unique vault name
        image_path: Path to vault image file
        description: Optional description
        tags: Optional tags
        passphrase: Optional passphrase to read vault and cache entries

    Returns:
        VaultMetadata

    Raises:
        GalleryOperationError: If vault doesn't exist or operation fails
    """
    # Verify image exists
    if not os.path.exists(image_path):
        raise GalleryOperationError(f"Vault image not found: {image_path}")

    # Convert to absolute path
    image_path = os.path.abspath(image_path)

    try:
        vault_id = db.add_vault(name, image_path, description, tags)
        vault = db.get_vault(name)

        # If passphrase provided, cache entries
        if passphrase and vault:
            _cache_vault_entries(db, vault, passphrase)

        return vault

    except GalleryDBError as e:
        raise GalleryOperationError(str(e))


def remove_vault(db: GalleryDB, name: str) -> bool:
    """
    Remove a vault from the gallery.

    Args:
        db: GalleryDB instance
        name: Vault name

    Returns:
        True if removed, False if not found
    """
    try:
        return db.remove_vault(name)
    except GalleryDBError as e:
        raise GalleryOperationError(str(e))


def list_vaults(db: GalleryDB, tag: Optional[str] = None) -> List[VaultMetadata]:
    """
    List all vaults in the gallery.

    Args:
        db: GalleryDB instance
        tag: Optional tag filter

    Returns:
        List of VaultMetadata
    """
    try:
        return db.list_vaults(tag)
    except GalleryDBError as e:
        raise GalleryOperationError(str(e))


def get_vault(db: GalleryDB, name: str) -> Optional[VaultMetadata]:
    """
    Get vault metadata by name.

    Args:
        db: GalleryDB instance
        name: Vault name

    Returns:
        VaultMetadata or None if not found
    """
    try:
        return db.get_vault(name)
    except GalleryDBError as e:
        raise GalleryOperationError(str(e))


def refresh_vault(db: GalleryDB, name: str, passphrase: str) -> VaultMetadata:
    """
    Refresh vault metadata by reading the vault image.

    Args:
        db: GalleryDB instance
        name: Vault name
        passphrase: Vault passphrase

    Returns:
        Updated VaultMetadata

    Raises:
        GalleryOperationError: If vault not found or decryption fails
    """
    try:
        vault = db.get_vault(name)
        if not vault:
            raise GalleryOperationError(f"Vault '{name}' not found")

        # Verify image still exists
        if not os.path.exists(vault.image_path):
            raise GalleryOperationError(f"Vault image not found: {vault.image_path}")

        # Cache entries
        _cache_vault_entries(db, vault, passphrase)

        # Update last accessed
        db.update_last_accessed(name)

        # Get updated vault
        return db.get_vault(name)

    except GalleryDBError as e:
        raise GalleryOperationError(str(e))


def _cache_vault_entries(db: GalleryDB, vault: VaultMetadata, passphrase: str):
    """
    Cache vault entries for search.

    Args:
        db: GalleryDB instance
        vault: VaultMetadata
        passphrase: Vault passphrase
    """
    from stegvault.utils import extract_full_payload
    from stegvault.crypto import decrypt_data
    from stegvault.utils.payload import parse_payload as parse_binary_payload
    from stegvault.vault import parse_payload as parse_vault_payload

    try:
        # Extract and decrypt
        payload_bytes = extract_full_payload(vault.image_path)
        salt, nonce, ciphertext = parse_binary_payload(payload_bytes)
        decrypted_data = decrypt_data(ciphertext, salt, nonce, passphrase)

        # Parse vault
        vault_obj = parse_vault_payload(decrypted_data.decode("utf-8"))

        # Check if it's a vault (not single password)
        if isinstance(vault_obj, str):
            # Single password mode - no entries to cache
            db.update_vault(vault.name, entry_count=0)
            return

        # Clear existing cache
        db.clear_vault_cache(vault.vault_id)

        # Cache each entry
        entry_count = 0
        for entry in vault_obj.entries:
            cache_entry = VaultEntryCache(
                vault_id=vault.vault_id,
                entry_key=entry.key,
                username=entry.username,
                url=entry.url,
                tags=entry.tags or [],
                has_totp=bool(entry.totp_secret),
                created_at=datetime.fromisoformat(entry.created) if entry.created else None,
                updated_at=datetime.fromisoformat(entry.modified) if entry.modified else None,
            )
            db.add_entry_cache(cache_entry)
            entry_count += 1

        # Update entry count
        db.update_vault(vault.name, entry_count=entry_count)

    except Exception as e:
        raise GalleryOperationError(f"Failed to cache entries: {e}")
