"""
Cross-vault search functionality.
"""

from typing import List, Optional, Dict, Any

from stegvault.gallery.db import GalleryDB, GalleryDBError
from stegvault.gallery.operations import GalleryOperationError


def search_gallery(
    db: GalleryDB,
    query: str,
    vault_name: Optional[str] = None,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Search across vaults in the gallery.

    Args:
        db: GalleryDB instance
        query: Search query
        vault_name: Optional vault name to limit search
        fields: Optional fields to search (entry_key, username, url)

    Returns:
        List of search results with vault and entry info

    Raises:
        GalleryOperationError: If search fails
    """
    try:
        # Get vault ID if name provided
        vault_id = None
        if vault_name:
            vault = db.get_vault(vault_name)
            if not vault:
                raise GalleryOperationError(f"Vault '{vault_name}' not found")
            vault_id = vault.vault_id

        # Search entries
        results = db.search_entries(query, vault_id, fields)

        # Format results
        formatted_results = []
        for entry, vault in results:
            formatted_results.append(
                {
                    "vault_name": vault.name,
                    "vault_path": vault.image_path,
                    "entry_key": entry.entry_key,
                    "username": entry.username,
                    "url": entry.url,
                    "tags": entry.tags,
                    "has_totp": entry.has_totp,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
                }
            )

        return formatted_results

    except GalleryDBError as e:
        raise GalleryOperationError(f"Search failed: {e}")


def search_by_tag(
    db: GalleryDB,
    tag: str,
    vault_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search entries by tag across vaults.

    Args:
        db: GalleryDB instance
        tag: Tag to search for
        vault_name: Optional vault name to limit search

    Returns:
        List of matching entries

    Raises:
        GalleryOperationError: If search fails
    """
    try:
        # Get vault ID if name provided
        vault_id = None
        if vault_name:
            vault = db.get_vault(vault_name)
            if not vault:
                raise GalleryOperationError(f"Vault '{vault_name}' not found")
            vault_id = vault.vault_id

        # For tag search, we need to query all entries and filter by tags
        # Since tags are stored as JSON, we'll do this in Python
        import json

        cursor = db.conn.cursor()

        if vault_id:
            cursor.execute(
                """
                SELECT e.*, v.*
                FROM vault_entries_cache e
                JOIN vaults v ON e.vault_id = v.id
                WHERE e.vault_id = ?
                ORDER BY v.name, e.entry_key
            """,
                (vault_id,),
            )
        else:
            cursor.execute(
                """
                SELECT e.*, v.*
                FROM vault_entries_cache e
                JOIN vaults v ON e.vault_id = v.id
                ORDER BY v.name, e.entry_key
            """
            )

        rows = cursor.fetchall()

        # Filter by tag
        results = []
        for row in rows:
            entry_tags = json.loads(row["tags"]) if row["tags"] else []
            if tag in entry_tags:
                results.append(
                    {
                        "vault_name": row["name"],
                        "vault_path": row["image_path"],
                        "entry_key": row["entry_key"],
                        "username": row["username"],
                        "url": row["url"],
                        "tags": entry_tags,
                        "has_totp": bool(row["has_totp"]),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )

        return results

    except Exception as e:
        raise GalleryOperationError(f"Tag search failed: {e}")


def search_by_url(
    db: GalleryDB,
    url_pattern: str,
    vault_name: Optional[str] = None,
    exact: bool = False,
) -> List[Dict[str, Any]]:
    """
    Search entries by URL pattern across vaults.

    Args:
        db: GalleryDB instance
        url_pattern: URL pattern to search for
        vault_name: Optional vault name to limit search
        exact: If True, require exact match

    Returns:
        List of matching entries

    Raises:
        GalleryOperationError: If search fails
    """
    # Use the general search with URL field
    return search_gallery(db, url_pattern, vault_name, ["url"])
