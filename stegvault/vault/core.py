"""
Core vault data structures and types.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional
from enum import Enum


class VaultFormat(str, Enum):
    """Vault format versions."""

    V1_SINGLE = "1.0"  # Single password (backward compatibility)
    V2_VAULT = "2.0"  # Multi-entry vault
    V2_1_HISTORY = "2.1"  # Multi-entry vault with password history


@dataclass
class PasswordHistoryEntry:
    """
    A historical password entry.

    Attributes:
        password: The historical password value
        changed_at: Timestamp when password was changed (ISO 8601)
        reason: Optional reason for change (e.g., "scheduled rotation", "suspected breach")
    """

    password: str
    changed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert history entry to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PasswordHistoryEntry":
        """Create history entry from dictionary."""
        return cls(**data)


@dataclass
class VaultEntry:
    """
    A single entry in a password vault.

    Attributes:
        key: Unique identifier for this entry (e.g., "gmail", "github")
        password: The actual password
        username: Optional username or email
        url: Optional website URL
        notes: Optional additional notes
        tags: Optional list of tags for organization
        totp_secret: Optional TOTP/2FA secret key
        password_history: List of historical passwords (most recent first)
        max_history: Maximum number of historical passwords to keep (default: 5)
        created: Creation timestamp (ISO 8601)
        modified: Last modification timestamp (ISO 8601)
        accessed: Last access timestamp (ISO 8601), None if never accessed
    """

    key: str
    password: str
    username: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    totp_secret: Optional[str] = None
    password_history: List[dict] = field(default_factory=list)  # List of PasswordHistoryEntry dicts
    max_history: int = 5
    created: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    modified: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    accessed: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert entry to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VaultEntry":
        """Create entry from dictionary."""
        return cls(**data)

    def update_modified(self) -> None:
        """Update the modified timestamp to now."""
        self.modified = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def update_accessed(self) -> None:
        """Update the accessed timestamp to now."""
        self.accessed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def change_password(self, new_password: str, reason: Optional[str] = None) -> None:
        """
        Change password and add current password to history.

        Args:
            new_password: The new password to set
            reason: Optional reason for password change
        """
        if self.password != new_password:
            # Create history entry for current password
            history_entry = PasswordHistoryEntry(password=self.password, reason=reason).to_dict()

            # Add to beginning of history list (most recent first)
            self.password_history.insert(0, history_entry)

            # Trim history to max_history size
            if len(self.password_history) > self.max_history:
                self.password_history = self.password_history[: self.max_history]

            # Update password and timestamp
            self.password = new_password
            self.update_modified()

    def get_password_history(self) -> List[PasswordHistoryEntry]:
        """
        Get password history as list of PasswordHistoryEntry objects.

        Returns:
            List of PasswordHistoryEntry objects, most recent first
        """
        return [PasswordHistoryEntry.from_dict(entry) for entry in self.password_history]

    def clear_password_history(self) -> None:
        """Clear all password history."""
        self.password_history = []
        self.update_modified()


@dataclass
class Vault:
    """
    A vault containing multiple password entries.

    Attributes:
        version: Vault format version
        entries: List of vault entries
        created: Vault creation timestamp (ISO 8601)
        modified: Last modification timestamp (ISO 8601)
        metadata: Additional metadata (app version, etc.)
    """

    version: str = VaultFormat.V2_VAULT.value
    entries: List[VaultEntry] = field(default_factory=list)
    created: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    modified: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize metadata with default values."""
        if "total_entries" not in self.metadata:
            self.metadata["total_entries"] = len(self.entries)
        if "app_version" not in self.metadata:
            from .. import __version__

            self.metadata["app_version"] = __version__

    def add_entry(self, entry: VaultEntry) -> None:
        """
        Add an entry to the vault.

        Args:
            entry: The entry to add

        Raises:
            ValueError: If an entry with the same key already exists
        """
        if self.has_entry(entry.key):
            raise ValueError(f"Entry with key '{entry.key}' already exists")

        self.entries.append(entry)
        self.update_modified()

    def get_entry(self, key: str) -> Optional[VaultEntry]:
        """
        Get an entry by key.

        Args:
            key: The entry key to search for

        Returns:
            The entry if found, None otherwise
        """
        for entry in self.entries:
            if entry.key == key:
                entry.update_accessed()
                self.update_modified()
                return entry
        return None

    def update_entry(self, key: str, **kwargs) -> bool:
        """
        Update an existing entry.

        Args:
            key: The entry key to update
            **kwargs: Fields to update (use 'password' to change password with history,
                     or 'password_change_reason' to specify reason for password change)

        Returns:
            True if updated, False if entry not found
        """
        entry = self.get_entry(key)
        if not entry:
            return False

        # Handle password changes specially to preserve history
        if "password" in kwargs:
            new_password = kwargs.pop("password")
            reason = kwargs.pop("password_change_reason", None)
            entry.change_password(new_password, reason=reason)

        # Update other fields normally
        for field_name, value in kwargs.items():
            if hasattr(entry, field_name) and field_name not in ("key", "created"):
                setattr(entry, field_name, value)

        entry.update_modified()
        self.update_modified()
        return True

    def delete_entry(self, key: str) -> bool:
        """
        Delete an entry by key.

        Args:
            key: The entry key to delete

        Returns:
            True if deleted, False if entry not found
        """
        for i, entry in enumerate(self.entries):
            if entry.key == key:
                del self.entries[i]
                self.update_modified()
                return True
        return False

    def has_entry(self, key: str) -> bool:
        """
        Check if an entry with the given key exists.

        Args:
            key: The entry key to check

        Returns:
            True if exists, False otherwise
        """
        return any(entry.key == key for entry in self.entries)

    def list_keys(self) -> List[str]:
        """
        Get a list of all entry keys in the vault.

        Returns:
            List of entry keys
        """
        return [entry.key for entry in self.entries]

    def update_modified(self) -> None:
        """Update the modified timestamp and entry count."""
        self.modified = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.metadata["total_entries"] = len(self.entries)

    def to_dict(self) -> dict:
        """
        Convert vault to dictionary.

        Returns:
            Dictionary representation of the vault
        """
        return {
            "version": self.version,
            "created": self.created,
            "modified": self.modified,
            "entries": [entry.to_dict() for entry in self.entries],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Vault":
        """
        Create vault from dictionary.

        Args:
            data: Dictionary containing vault data

        Returns:
            Vault instance
        """
        entries = [VaultEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(
            version=data.get("version", VaultFormat.V2_VAULT.value),
            entries=entries,
            created=data.get(
                "created", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            ),
            modified=data.get(
                "modified", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            ),
            metadata=data.get("metadata", {}),
        )
