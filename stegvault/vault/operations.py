"""
Vault operations and serialization.
"""

import json
from typing import Optional, Union
from .core import Vault, VaultEntry, VaultFormat


def vault_to_json(vault: Vault, pretty: bool = False) -> str:
    """
    Serialize a vault to JSON string.

    Args:
        vault: The vault to serialize
        pretty: If True, format JSON with indentation

    Returns:
        JSON string representation of the vault
    """
    vault_dict = vault.to_dict()
    if pretty:
        return json.dumps(vault_dict, indent=2, ensure_ascii=False)
    return json.dumps(vault_dict, ensure_ascii=False)


def vault_from_json(json_str: str) -> Vault:
    """
    Deserialize a vault from JSON string.

    Args:
        json_str: JSON string containing vault data

    Returns:
        Vault instance

    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    if not isinstance(data, dict):
        raise ValueError("Vault JSON must be an object")

    # Check if it's a vault format (has 'entries' key)
    if "entries" not in data:
        raise ValueError("Invalid vault format: missing 'entries' field")

    return Vault.from_dict(data)


def detect_format(payload: Union[str, bytes]) -> VaultFormat:
    """
    Detect the format of a payload (single password vs vault).

    Args:
        payload: The decrypted payload (string or bytes)

    Returns:
        VaultFormat indicating the detected format
    """
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            # If it can't be decoded as UTF-8, it's likely corrupted or single password
            return VaultFormat.V1_SINGLE

    payload = payload.strip()

    # Try to parse as JSON
    try:
        data = json.loads(payload)
        if isinstance(data, dict) and "entries" in data:
            return VaultFormat.V2_VAULT
        else:
            # It's JSON but not a vault structure
            return VaultFormat.V1_SINGLE
    except (json.JSONDecodeError, ValueError):
        # Not JSON, must be a single password string
        return VaultFormat.V1_SINGLE


def parse_payload(payload: Union[str, bytes]) -> Union[str, Vault]:
    """
    Parse a payload and return either a single password string or a Vault.

    Args:
        payload: The decrypted payload

    Returns:
        Either a string (single password) or Vault instance

    Raises:
        ValueError: If the payload is invalid
    """
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")

    format_type = detect_format(payload)

    if format_type == VaultFormat.V2_VAULT:
        return vault_from_json(payload)
    else:
        # Single password - return as-is
        return payload.strip()


def create_vault() -> Vault:
    """
    Create a new empty vault.

    Returns:
        New Vault instance
    """
    return Vault()


def add_entry(
    vault: Vault,
    key: str,
    password: str,
    username: Optional[str] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[list] = None,
    totp_secret: Optional[str] = None,
) -> VaultEntry:
    """
    Add a new entry to the vault.

    Args:
        vault: The vault to add to
        key: Unique identifier for the entry
        password: The password
        username: Optional username
        url: Optional URL
        notes: Optional notes
        tags: Optional list of tags
        totp_secret: Optional TOTP secret

    Returns:
        The created VaultEntry

    Raises:
        ValueError: If an entry with the same key already exists
    """
    entry = VaultEntry(
        key=key,
        password=password,
        username=username,
        url=url,
        notes=notes,
        tags=tags or [],
        totp_secret=totp_secret,
    )
    vault.add_entry(entry)
    return entry


def get_entry(vault: Vault, key: str) -> Optional[VaultEntry]:
    """
    Get an entry from the vault by key.

    Args:
        vault: The vault to search
        key: The entry key

    Returns:
        The entry if found, None otherwise
    """
    return vault.get_entry(key)


def list_entries(vault: Vault) -> list[str]:
    """
    List all entry keys in the vault.

    Args:
        vault: The vault to list

    Returns:
        List of entry keys
    """
    return vault.list_keys()


def update_entry(vault: Vault, key: str, **kwargs) -> bool:
    """
    Update an existing entry in the vault.

    Args:
        vault: The vault containing the entry
        key: The entry key to update
        **kwargs: Fields to update

    Returns:
        True if updated, False if entry not found
    """
    return vault.update_entry(key, **kwargs)


def delete_entry(vault: Vault, key: str) -> bool:
    """
    Delete an entry from the vault.

    Args:
        vault: The vault containing the entry
        key: The entry key to delete

    Returns:
        True if deleted, False if entry not found
    """
    return vault.delete_entry(key)


def single_password_to_vault(password: str, key: str = "default") -> Vault:
    """
    Convert a single password to a vault with one entry.

    Args:
        password: The password to convert
        key: The key to use for the entry (default: "default")

    Returns:
        Vault with one entry containing the password
    """
    vault = create_vault()
    add_entry(vault, key=key, password=password)
    return vault


def import_vault_from_file(json_path: str) -> Vault:
    """
    Import a vault from a JSON file.

    Args:
        json_path: Path to the JSON file containing vault data

    Returns:
        Vault instance loaded from the file

    Raises:
        ValueError: If the file doesn't exist, is invalid JSON, or not a vault format
        FileNotFoundError: If the JSON file doesn't exist
    """
    import os

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        json_str = f.read()

    # vault_from_json will raise ValueError if invalid
    return vault_from_json(json_str)


def search_entries(
    vault: Vault,
    query: str,
    case_sensitive: bool = False,
    fields: Optional[list[str]] = None,
) -> list[VaultEntry]:
    """
    Search vault entries by query string.

    Searches across key, username, URL, and notes fields by default.

    Args:
        vault: The vault to search
        query: Search query string
        case_sensitive: If True, perform case-sensitive search
        fields: Optional list of fields to search in. Default: ["key", "username", "url", "notes"]

    Returns:
        List of matching VaultEntry objects
    """
    if not query:
        return []

    search_fields = fields or ["key", "username", "url", "notes"]
    search_query = query if case_sensitive else query.lower()
    results = []

    for entry in vault.entries:
        # Check each field for matches
        for field in search_fields:
            value = getattr(entry, field, None)
            if value:
                check_value = value if case_sensitive else value.lower()
                if search_query in check_value:
                    results.append(entry)
                    break  # Don't add same entry multiple times

    return results


def filter_by_tags(vault: Vault, tags: list[str], match_all: bool = False) -> list[VaultEntry]:
    """
    Filter vault entries by tags.

    Args:
        vault: The vault to filter
        tags: List of tags to filter by
        match_all: If True, entry must have ALL tags. If False, entry must have ANY tag.

    Returns:
        List of matching VaultEntry objects
    """
    if not tags:
        return []

    results = []

    for entry in vault.entries:
        entry_tags = set(entry.tags)
        filter_tags = set(tags)

        if match_all:
            # Entry must have all specified tags
            if filter_tags.issubset(entry_tags):
                results.append(entry)
        else:
            # Entry must have at least one of the specified tags
            if filter_tags.intersection(entry_tags):
                results.append(entry)

    return results


def filter_by_url(vault: Vault, url_pattern: str, exact: bool = False) -> list[VaultEntry]:
    """
    Filter vault entries by URL pattern.

    Args:
        vault: The vault to filter
        url_pattern: URL pattern to match (e.g., "github.com")
        exact: If True, require exact match. If False, use substring match.

    Returns:
        List of matching VaultEntry objects
    """
    if not url_pattern:
        return []

    results = []

    for entry in vault.entries:
        if not entry.url:
            continue

        if exact:
            if entry.url == url_pattern:
                results.append(entry)
        else:
            if url_pattern.lower() in entry.url.lower():
                results.append(entry)

    return results
