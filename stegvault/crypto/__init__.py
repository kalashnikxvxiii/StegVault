"""
Cryptography module for StegVault.

Handles key derivation (Argon2id) and authenticated encryption (XChaCha20-Poly1305).
"""

from stegvault.crypto.core import (
    encrypt_data,
    decrypt_data,
    derive_key,
    verify_passphrase_strength,
    CryptoError,
    DecryptionError,
)

__all__ = [
    "encrypt_data",
    "decrypt_data",
    "derive_key",
    "verify_passphrase_strength",
    "CryptoError",
    "DecryptionError",
]
