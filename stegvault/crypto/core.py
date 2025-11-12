"""
Core cryptography functions for StegVault.

Implements:
- Argon2id key derivation
- XChaCha20-Poly1305 AEAD encryption/decryption
"""

import os
from typing import Tuple
from argon2 import PasswordHasher
from argon2.low_level import Type, hash_secret_raw
import nacl.secret
import nacl.utils


# Argon2id parameters (balanced security/performance)
ARGON2_TIME_COST = 3  # Number of iterations
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 4  # Number of parallel threads
ARGON2_HASH_LENGTH = 32  # 256-bit key for XChaCha20-Poly1305

# Standard sizes
SALT_SIZE = 16  # 128 bits
NONCE_SIZE = 24  # 192 bits for XChaCha20


class CryptoError(Exception):
    """Base exception for cryptography errors."""

    pass


class DecryptionError(CryptoError):
    """Raised when decryption or authentication fails."""

    pass


def generate_salt() -> bytes:
    """
    Generate a cryptographically secure random salt.

    Returns:
        16 bytes of random data from CSPRNG
    """
    return os.urandom(SALT_SIZE)


def generate_nonce() -> bytes:
    """
    Generate a cryptographically secure random nonce for XChaCha20.

    Returns:
        24 bytes of random data from CSPRNG
    """
    return nacl.utils.random(NONCE_SIZE)


def derive_key(
    passphrase: str,
    salt: bytes,
    time_cost: int = ARGON2_TIME_COST,
    memory_cost: int = ARGON2_MEMORY_COST,
    parallelism: int = ARGON2_PARALLELISM,
) -> bytes:
    """
    Derive a 256-bit encryption key from a passphrase using Argon2id.

    Args:
        passphrase: User-provided passphrase
        salt: 16-byte salt (must be stored with ciphertext)
        time_cost: Number of iterations (default: 3)
        memory_cost: Memory usage in KB (default: 65536 = 64MB)
        parallelism: Number of parallel threads (default: 4)

    Returns:
        32-byte derived key suitable for XChaCha20-Poly1305

    Raises:
        CryptoError: If key derivation fails or parameters are invalid
    """
    if len(salt) != SALT_SIZE:
        raise CryptoError(f"Salt must be exactly {SALT_SIZE} bytes, got {len(salt)}")

    if time_cost < 1:
        raise CryptoError(f"time_cost must be >= 1, got {time_cost}")
    if memory_cost < 8:
        raise CryptoError(f"memory_cost must be >= 8 KB, got {memory_cost}")
    if parallelism < 1:
        raise CryptoError(f"parallelism must be >= 1, got {parallelism}")

    try:
        # Use Argon2id (hybrid mode: resistant to both side-channel and GPU attacks)
        key = hash_secret_raw(
            secret=passphrase.encode("utf-8"),
            salt=salt,
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=ARGON2_HASH_LENGTH,
            type=Type.ID,  # Argon2id
        )
        return key
    except Exception as e:
        raise CryptoError(f"Key derivation failed: {e}")


def encrypt_data(
    plaintext: bytes,
    passphrase: str,
    time_cost: int = ARGON2_TIME_COST,
    memory_cost: int = ARGON2_MEMORY_COST,
    parallelism: int = ARGON2_PARALLELISM,
) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypt data using XChaCha20-Poly1305 AEAD with Argon2id key derivation.

    Args:
        plaintext: Data to encrypt
        passphrase: User-provided passphrase
        time_cost: Argon2id iterations (default: 3)
        memory_cost: Argon2id memory in KB (default: 65536 = 64MB)
        parallelism: Argon2id thread count (default: 4)

    Returns:
        Tuple of (ciphertext, salt, nonce)
        - ciphertext includes the 16-byte Poly1305 authentication tag appended
        - salt: 16 bytes (for key derivation)
        - nonce: 24 bytes (for XChaCha20)

    Raises:
        CryptoError: If encryption fails
    """
    try:
        # Generate random salt and nonce
        salt = generate_salt()
        nonce = generate_nonce()

        # Derive encryption key from passphrase
        key = derive_key(passphrase, salt, time_cost, memory_cost, parallelism)

        # Create XChaCha20-Poly1305 cipher
        box = nacl.secret.SecretBox(key)

        # Encrypt (returns nonce + ciphertext + tag, but we manage nonce separately)
        # Use encrypt() which automatically handles the tag
        ciphertext = box.encrypt(plaintext, nonce)

        # Extract just the ciphertext+tag (remove the prepended nonce from PyNaCl)
        # PyNaCl prepends the nonce, but we want to manage it separately
        ciphertext_with_tag = ciphertext[NONCE_SIZE:]

        return ciphertext_with_tag, salt, nonce

    except Exception as e:
        raise CryptoError(f"Encryption failed: {e}")


def decrypt_data(
    ciphertext: bytes,
    salt: bytes,
    nonce: bytes,
    passphrase: str,
    time_cost: int = ARGON2_TIME_COST,
    memory_cost: int = ARGON2_MEMORY_COST,
    parallelism: int = ARGON2_PARALLELISM,
) -> bytes:
    """
    Decrypt data using XChaCha20-Poly1305 AEAD with Argon2id key derivation.

    Args:
        ciphertext: Encrypted data (includes 16-byte Poly1305 tag appended)
        salt: 16-byte salt used for key derivation
        nonce: 24-byte nonce used for encryption
        passphrase: User-provided passphrase
        time_cost: Argon2id iterations (default: 3)
        memory_cost: Argon2id memory in KB (default: 65536 = 64MB)
        parallelism: Argon2id thread count (default: 4)

    Returns:
        Decrypted plaintext

    Raises:
        DecryptionError: If decryption or authentication fails
        CryptoError: If other crypto operations fail
    """
    if len(salt) != SALT_SIZE:
        raise CryptoError(f"Salt must be exactly {SALT_SIZE} bytes, got {len(salt)}")

    if len(nonce) != NONCE_SIZE:
        raise CryptoError(f"Nonce must be exactly {NONCE_SIZE} bytes, got {len(nonce)}")

    try:
        # Derive the same encryption key from passphrase
        key = derive_key(passphrase, salt, time_cost, memory_cost, parallelism)

        # Create XChaCha20-Poly1305 cipher
        box = nacl.secret.SecretBox(key)

        # PyNaCl's decrypt expects: nonce + ciphertext + tag
        # We store them separately, so reconstruct the format
        encrypted_message = nonce + ciphertext

        # Decrypt and verify authentication tag
        plaintext = box.decrypt(encrypted_message)

        return plaintext

    except nacl.exceptions.CryptoError as e:
        # This is raised when authentication fails (wrong passphrase or corrupted data)
        raise DecryptionError("Decryption failed: wrong passphrase or corrupted data")

    except Exception as e:
        raise CryptoError(f"Decryption failed: {e}")


def verify_passphrase_strength(passphrase: str, min_length: int = 12) -> Tuple[bool, str]:
    """
    Basic passphrase strength verification.

    Args:
        passphrase: Passphrase to verify
        min_length: Minimum acceptable length

    Returns:
        Tuple of (is_valid, message)
    """
    if len(passphrase) < min_length:
        return False, f"Passphrase must be at least {min_length} characters"

    # Check for basic complexity
    has_upper = any(c.isupper() for c in passphrase)
    has_lower = any(c.islower() for c in passphrase)
    has_digit = any(c.isdigit() for c in passphrase)

    if not (has_upper and has_lower and has_digit):
        return False, "Passphrase should contain uppercase, lowercase, and digits"

    return True, "Passphrase strength is acceptable"
