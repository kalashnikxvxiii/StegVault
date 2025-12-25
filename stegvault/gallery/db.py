"""
SQLite database operations for Gallery.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Any
from stegvault.gallery.core import VaultMetadata, VaultEntryCache


class GalleryDBError(Exception):
    """Gallery database error."""

    pass


class GalleryDB:
    """SQLite database manager for Gallery."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._initialize_schema()

    def _connect(self) -> None:
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to connect to database: {e}")

    def _initialize_schema(self) -> None:
        """Create database schema if not exists."""
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()

            # Vaults table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vaults (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    image_path TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    entry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            """
            )

            # Vault entries cache table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vault_entries_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vault_id INTEGER NOT NULL,
                    entry_key TEXT NOT NULL,
                    username TEXT,
                    url TEXT,
                    tags TEXT,
                    has_totp BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (vault_id) REFERENCES vaults(id) ON DELETE CASCADE,
                    UNIQUE(vault_id, entry_key)
                )
            """
            )

            # Create indexes for better search performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_vault_entries_vault_id
                ON vault_entries_cache(vault_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_vault_entries_key
                ON vault_entries_cache(entry_key)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_vault_entries_url
                ON vault_entries_cache(url)
            """
            )

            self.conn.commit()

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to initialize schema: {e}")

    def add_vault(
        self,
        name: str,
        image_path: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Add a vault to the database.

        Args:
            name: Unique vault name
            image_path: Path to vault image
            description: Optional description
            tags: Optional tags list

        Returns:
            Vault ID

        Raises:
            GalleryDBError: If vault already exists or database error
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            tags_json = json.dumps(tags or [])
            now = datetime.now()

            cursor.execute(
                """
                INSERT INTO vaults (name, image_path, description, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (name, image_path, description, tags_json, now, now),
            )

            self.conn.commit()
            return cursor.lastrowid or 0

        except sqlite3.IntegrityError:
            raise GalleryDBError(f"Vault '{name}' already exists")
        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to add vault: {e}")

    def remove_vault(self, name: str) -> bool:
        """
        Remove a vault from the database.

        Args:
            name: Vault name

        Returns:
            True if removed, False if not found
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM vaults WHERE name = ?", (name,))
            self.conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to remove vault: {e}")

    def get_vault(self, name: str) -> Optional[VaultMetadata]:
        """
        Get vault metadata by name.

        Args:
            name: Vault name

        Returns:
            VaultMetadata or None if not found
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM vaults WHERE name = ?", (name,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_vault_metadata(row)

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to get vault: {e}")

    def get_vault_by_id(self, vault_id: int) -> Optional[VaultMetadata]:
        """
        Get vault metadata by ID.

        Args:
            vault_id: Vault ID

        Returns:
            VaultMetadata or None if not found
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM vaults WHERE id = ?", (vault_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_vault_metadata(row)

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to get vault: {e}")

    def list_vaults(self, tag: Optional[str] = None) -> List[VaultMetadata]:
        """
        List all vaults, optionally filtered by tag.

        Args:
            tag: Optional tag filter

        Returns:
            List of VaultMetadata
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()

            if tag:
                cursor.execute("SELECT * FROM vaults ORDER BY name")
                rows = cursor.fetchall()
                # Filter by tag in Python (SQLite JSON support is limited)
                filtered_rows = []
                for row in rows:
                    tags = json.loads(row["tags"]) if row["tags"] else []
                    if tag in tags:
                        filtered_rows.append(row)
                rows = filtered_rows
            else:
                cursor.execute("SELECT * FROM vaults ORDER BY name")
                rows = cursor.fetchall()

            return [self._row_to_vault_metadata(row) for row in rows]

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to list vaults: {e}")

    def update_vault(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        entry_count: Optional[int] = None,
    ) -> bool:
        """
        Update vault metadata.

        Args:
            name: Vault name
            description: New description
            tags: New tags list
            entry_count: New entry count

        Returns:
            True if updated, False if not found
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            updates: List[str] = []
            params: List[Any] = []

            if description is not None:
                updates.append("description = ?")
                params.append(description)

            if tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(tags))

            if entry_count is not None:
                updates.append("entry_count = ?")
                params.append(entry_count)

            if not updates:
                return False

            updates.append("updated_at = ?")
            params.append(datetime.now())
            params.append(name)

            # Safe: updates list contains only validated column names, all values are parameterized
            query = f"UPDATE vaults SET {', '.join(updates)} WHERE name = ?"  # nosec B608
            cursor.execute(query, params)
            self.conn.commit()

            return cursor.rowcount > 0

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to update vault: {e}")

    def update_last_accessed(self, name: str) -> None:
        """
        Update vault's last accessed timestamp.

        Args:
            name: Vault name
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE vaults SET last_accessed = ? WHERE name = ?",
                (datetime.now(), name),
            )
            self.conn.commit()

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to update last accessed: {e}")

    def add_entry_cache(self, entry: VaultEntryCache) -> int:
        """
        Add entry to cache.

        Args:
            entry: VaultEntryCache object

        Returns:
            Cache entry ID
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            tags_json = json.dumps(entry.tags)

            cursor.execute(
                """
                INSERT OR REPLACE INTO vault_entries_cache
                (vault_id, entry_key, username, url, tags, has_totp, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry.vault_id,
                    entry.entry_key,
                    entry.username,
                    entry.url,
                    tags_json,
                    entry.has_totp,
                    entry.created_at,
                    entry.updated_at,
                ),
            )

            self.conn.commit()
            return cursor.lastrowid or 0

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to add entry cache: {e}")

    def clear_vault_cache(self, vault_id: int) -> None:
        """
        Clear all cached entries for a vault.

        Args:
            vault_id: Vault ID
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM vault_entries_cache WHERE vault_id = ?", (vault_id,))
            self.conn.commit()

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to clear vault cache: {e}")

    def search_entries(
        self,
        query: str,
        vault_id: Optional[int] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Tuple[VaultEntryCache, VaultMetadata]]:
        """
        Search cached entries.

        Args:
            query: Search query
            vault_id: Optional vault ID to limit search
            fields: Optional fields to search

        Returns:
            List of (VaultEntryCache, VaultMetadata) tuples
        """
        try:
            assert self.conn is not None  # nosec B101
            cursor = self.conn.cursor()
            query_lower = query.lower()

            # Build WHERE clause
            conditions = []
            params = []

            if vault_id:
                conditions.append("e.vault_id = ?")
                params.append(vault_id)

            # Search conditions
            search_fields = fields or ["entry_key", "username", "url"]
            field_conditions = []

            for field in search_fields:
                if field in ["entry_key", "username", "url"]:
                    field_conditions.append(f"LOWER(e.{field}) LIKE ?")
                    params.append(f"%{query_lower}%")

            if field_conditions:
                conditions.append(f"({' OR '.join(field_conditions)})")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Safe: where_clause built from validated field names, all values are parameterized
            sql = f"""
                SELECT e.*, v.*
                FROM vault_entries_cache e
                JOIN vaults v ON e.vault_id = v.id
                WHERE {where_clause}
                ORDER BY v.name, e.entry_key
            """  # nosec B608

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                entry = VaultEntryCache(
                    vault_id=row["vault_id"],
                    entry_key=row["entry_key"],
                    username=row["username"],
                    url=row["url"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    has_totp=bool(row["has_totp"]),
                    created_at=(
                        datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
                    ),
                    updated_at=(
                        datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                    ),
                    cache_id=row["id"],
                )

                vault = VaultMetadata(
                    vault_id=row["id"],
                    name=row["name"],
                    image_path=row["image_path"],
                    description=row["description"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    entry_count=row["entry_count"],
                )

                results.append((entry, vault))

            return results

        except sqlite3.Error as e:
            raise GalleryDBError(f"Failed to search entries: {e}")

    def _row_to_vault_metadata(self, row: sqlite3.Row) -> VaultMetadata:
        """Convert database row to VaultMetadata."""
        return VaultMetadata(
            vault_id=row["id"],
            name=row["name"],
            image_path=row["image_path"],
            description=row["description"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            entry_count=row["entry_count"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            last_accessed=(
                datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None
            ),
        )

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
