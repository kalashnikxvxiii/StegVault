"""
Crypto Controller - High-level encryption/decryption operations.

Provides a clean interface for encryption operations that can be used
by CLI, TUI, and GUI without depending on Click or other UI frameworks.
"""

from typing import Tuple, Optional
from dataclasses import dataclass

from stegvault.crypto import encrypt_data, decrypt_data, DecryptionError
from stegvault.config import Config, get_default_config


@dataclass
class EncryptionResult:
    """Result of an encryption operation."""

    ciphertext: bytes
    salt: bytes
    nonce: bytes
    success: bool = True
    error: Optional[str] = None


@dataclass
class DecryptionResult:
    """Result of a decryption operation."""

    plaintext: bytearray  # Mutable so caller can secure_wipe() after use
    success: bool = True
    error: Optional[str] = None


class CryptoController:
    """
    Controller for cryptographic operations.

    Handles encryption and decryption with configuration management.
    Thread-safe and UI-agnostic.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize CryptoController.

        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or get_default_config()

    def encrypt(self, data: bytes, passphrase: str) -> EncryptionResult:
        """
        Encrypt data with passphrase.

        Args:
            data: Plaintext data to encrypt
            passphrase: User passphrase for encryption

        Returns:
            EncryptionResult with ciphertext, salt, and nonce
        """
        try:
            ciphertext, salt, nonce = encrypt_data(
                data,
                passphrase,
                time_cost=self.config.crypto.argon2_time_cost,
                memory_cost=self.config.crypto.argon2_memory_cost,
                parallelism=self.config.crypto.argon2_parallelism,
            )

            return EncryptionResult(ciphertext=ciphertext, salt=salt, nonce=nonce, success=True)

        except Exception as e:
            return EncryptionResult(
                ciphertext=b"", salt=b"", nonce=b"", success=False, error=str(e)
            )

    def decrypt(
        self, ciphertext: bytes, salt: bytes, nonce: bytes, passphrase: str
    ) -> DecryptionResult:
        """
        Decrypt data with passphrase.

        Args:
            ciphertext: Encrypted data
            salt: Salt used for key derivation
            nonce: Nonce used for encryption
            passphrase: User passphrase for decryption

        Returns:
            DecryptionResult with plaintext or error
        """
        try:
            plaintext = decrypt_data(
                ciphertext,
                salt,
                nonce,
                passphrase,
                time_cost=self.config.crypto.argon2_time_cost,
                memory_cost=self.config.crypto.argon2_memory_cost,
                parallelism=self.config.crypto.argon2_parallelism,
            )

            return DecryptionResult(plaintext=plaintext, success=True)

        except DecryptionError as e:
            return DecryptionResult(plaintext=bytearray(), success=False, error=f"Decryption failed: {e}")
        except Exception as e:
            return DecryptionResult(plaintext=bytearray(), success=False, error=str(e))

    def encrypt_with_payload(
        self, data: bytes, passphrase: str
    ) -> Tuple[bytes, bool, Optional[str]]:
        """
        Encrypt data and serialize into payload format.

        Args:
            data: Plaintext data to encrypt
            passphrase: User passphrase

        Returns:
            Tuple of (payload_bytes, success, error_message)
        """
        from stegvault.utils import serialize_payload

        result = self.encrypt(data, passphrase)

        if not result.success:
            return b"", False, result.error

        try:
            payload = serialize_payload(result.salt, result.nonce, result.ciphertext)
            return payload, True, None
        except Exception as e:
            return b"", False, f"Failed to serialize payload: {e}"

    def decrypt_from_payload(
        self, payload: bytes, passphrase: str
    ) -> Tuple[bytes, bool, Optional[str]]:
        """
        Parse payload and decrypt data.

        Args:
            payload: Serialized payload bytes
            passphrase: User passphrase

        Returns:
            Tuple of (plaintext_bytes, success, error_message)
        """
        from stegvault.utils import parse_payload

        try:
            salt, nonce, ciphertext = parse_payload(payload)
        except Exception as e:
            return bytearray(), False, f"Failed to parse payload: {e}"

        result = self.decrypt(ciphertext, salt, nonce, passphrase)

        if not result.success:
            return bytearray(), False, result.error

        return result.plaintext, True, None
