"""
Vault Controller - High-level vault management operations.

Provides a clean interface for vault CRUD operations that can be used
by CLI, TUI, and GUI without depending on Click or other UI frameworks.
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path

from stegvault.vault import (
    Vault,
    VaultEntry,
    create_vault,
    add_entry,
    get_entry,
    update_entry,
    delete_entry,
    list_entries,
    vault_to_json,
    parse_payload as parse_vault_payload,
)
from stegvault.stego import embed_payload, extract_payload, calculate_capacity
from stegvault.app.controllers.crypto_controller import CryptoController
from stegvault.config import Config


@dataclass
class VaultLoadResult:
    """Result of loading a vault from an image."""

    vault: Optional[Vault]
    success: bool
    error: Optional[str] = None


@dataclass
class VaultSaveResult:
    """Result of saving a vault to an image."""

    output_path: str
    success: bool
    error: Optional[str] = None


@dataclass
class EntryResult:
    """Result of an entry operation."""

    entry: Optional[VaultEntry]
    success: bool
    error: Optional[str] = None


class VaultController:
    """
    Controller for vault management operations.

    Provides high-level CRUD operations for vaults, handling encryption,
    steganography, and error management. Thread-safe and UI-agnostic.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize VaultController.

        Args:
            config: Configuration object. If None, uses default config.
        """
        self.crypto = CryptoController(config)

    def load_vault(self, image_path: str, passphrase: str) -> VaultLoadResult:
        """
        Load vault from image file.

        Args:
            image_path: Path to image containing vault
            passphrase: Passphrase to decrypt vault

        Returns:
            VaultLoadResult with vault object or error
        """
        try:
            from stegvault.utils import extract_full_payload

            # Extract payload from image
            payload = extract_full_payload(image_path)

            # Decrypt payload
            plaintext, success, error = self.crypto.decrypt_from_payload(payload, passphrase)

            if not success:
                return VaultLoadResult(vault=None, success=False, error=error)

            # Parse vault JSON
            vault = parse_vault_payload(plaintext.decode("utf-8"))

            # Handle single password mode (backward compatibility)
            if isinstance(vault, str):
                return VaultLoadResult(
                    vault=None,
                    success=False,
                    error="Image contains single password, not a vault",
                )

            return VaultLoadResult(vault=vault, success=True)

        except FileNotFoundError:
            return VaultLoadResult(
                vault=None, success=False, error=f"Image not found: {image_path}"
            )
        except Exception as e:
            return VaultLoadResult(vault=None, success=False, error=str(e))

    def save_vault(
        self,
        vault: Vault,
        output_path: str,
        passphrase: str,
        cover_image: Optional[str] = None,
    ) -> VaultSaveResult:
        """
        Save vault to image file.

        Args:
            vault: Vault object to save
            output_path: Path for output image
            passphrase: Passphrase to encrypt vault
            cover_image: Path to cover image. If None, uses output_path as base.

        Returns:
            VaultSaveResult with output path or error
        """
        try:
            # Serialize vault to JSON
            vault_json = vault_to_json(vault)
            vault_bytes = vault_json.encode("utf-8")

            # Check capacity if cover image provided
            if cover_image:
                try:
                    capacity = calculate_capacity(cover_image)
                    # Account for payload overhead (magic + salt + nonce + length + tag)
                    required = len(vault_bytes) + 64
                    if capacity < required:
                        return VaultSaveResult(
                            output_path="",
                            success=False,
                            error=f"Image capacity ({capacity} bytes) insufficient for vault ({required} bytes required)",
                        )
                except Exception:  # nosec B110
                    # If capacity check fails, continue anyway (will fail at embed if truly insufficient)
                    pass

            # Encrypt vault
            payload, success, error = self.crypto.encrypt_with_payload(vault_bytes, passphrase)

            if not success:
                return VaultSaveResult(output_path="", success=False, error=error)

            # Generate seed from salt
            from stegvault.utils import parse_payload

            salt, _, _ = parse_payload(payload)
            seed = int.from_bytes(salt[:4], byteorder="big")

            # Embed payload into image
            input_image = cover_image if cover_image else output_path
            embed_payload(input_image, payload, seed, output_path)

            return VaultSaveResult(output_path=output_path, success=True)

        except Exception as e:
            return VaultSaveResult(output_path="", success=False, error=str(e))

    def create_new_vault(
        self,
        key: str,
        password: str,
        username: Optional[str] = None,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        totp_secret: Optional[str] = None,
    ) -> Tuple[Vault, bool, Optional[str]]:
        """
        Create a new vault with first entry.

        Args:
            key: Entry key
            password: Entry password
            username: Optional username
            url: Optional URL
            notes: Optional notes
            tags: Optional tags list
            totp_secret: Optional TOTP secret

        Returns:
            Tuple of (vault, success, error_message)
        """
        try:
            vault = create_vault()
            add_entry(
                vault,
                key=key,
                password=password,
                username=username,
                url=url,
                notes=notes,
                tags=tags or [],
                totp_secret=totp_secret,
            )
            return vault, True, None
        except Exception as e:
            return None, False, str(e)

    def add_vault_entry(
        self,
        vault: Vault,
        key: str,
        password: str,
        username: Optional[str] = None,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        totp_secret: Optional[str] = None,
    ) -> Tuple[Vault, bool, Optional[str]]:
        """
        Add entry to existing vault.

        Args:
            vault: Existing vault
            key: Entry key
            password: Entry password
            username: Optional username
            url: Optional URL
            notes: Optional notes
            tags: Optional tags list
            totp_secret: Optional TOTP secret

        Returns:
            Tuple of (updated_vault, success, error_message)
        """
        try:
            # Check if key already exists
            if vault.has_entry(key):
                return vault, False, f"Entry with key '{key}' already exists"

            add_entry(
                vault,
                key=key,
                password=password,
                username=username,
                url=url,
                notes=notes,
                tags=tags or [],
                totp_secret=totp_secret,
            )
            return vault, True, None
        except Exception as e:
            return vault, False, str(e)

    def get_vault_entry(self, vault: Vault, key: str) -> EntryResult:
        """
        Get entry from vault by key.

        Args:
            vault: Vault to search
            key: Entry key

        Returns:
            EntryResult with entry or error
        """
        try:
            entry = get_entry(vault, key)
            if entry is None:
                available_keys = ", ".join(list_entries(vault))
                return EntryResult(
                    entry=None,
                    success=False,
                    error=f"Entry '{key}' not found. Available: {available_keys}",
                )
            return EntryResult(entry=entry, success=True)
        except Exception as e:
            return EntryResult(entry=None, success=False, error=str(e))

    def update_vault_entry(
        self,
        vault: Vault,
        key: str,
        password: Optional[str] = None,
        username: Optional[str] = None,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        totp_secret: Optional[str] = None,
    ) -> Tuple[Vault, bool, Optional[str]]:
        """
        Update existing vault entry.

        Args:
            vault: Vault containing entry
            key: Entry key to update
            password: New password (optional)
            username: New username (optional)
            url: New URL (optional)
            notes: New notes (optional)
            tags: New tags (optional)
            totp_secret: New TOTP secret (optional)

        Returns:
            Tuple of (updated_vault, success, error_message)
        """
        try:
            # Check if entry exists
            if not vault.has_entry(key):
                return (
                    vault,
                    False,
                    f"Entry '{key}' not found in vault",
                )

            update_entry(
                vault,
                key=key,
                password=password,
                username=username,
                url=url,
                notes=notes,
                tags=tags,
                totp_secret=totp_secret,
            )
            return vault, True, None
        except Exception as e:
            return vault, False, str(e)

    def delete_vault_entry(self, vault: Vault, key: str) -> Tuple[Vault, bool, Optional[str]]:
        """
        Delete entry from vault.

        Args:
            vault: Vault containing entry
            key: Entry key to delete

        Returns:
            Tuple of (updated_vault, success, error_message)
        """
        try:
            # Check if entry exists
            if not vault.has_entry(key):
                return (
                    vault,
                    False,
                    f"Entry '{key}' not found in vault",
                )

            delete_entry(vault, key)
            return vault, True, None
        except Exception as e:
            return vault, False, str(e)

    def list_vault_entries(self, vault: Vault) -> List[str]:
        """
        List all entry keys in vault.

        Args:
            vault: Vault to list

        Returns:
            List of entry keys
        """
        return list_entries(vault)

    def check_image_capacity(self, image_path: str) -> Tuple[int, bool, Optional[str]]:
        """
        Check image capacity for vault storage.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (capacity_bytes, success, error_message)
        """
        try:
            capacity = calculate_capacity(image_path)
            return capacity, True, None
        except FileNotFoundError:
            return 0, False, f"Image not found: {image_path}"
        except Exception as e:
            return 0, False, str(e)
