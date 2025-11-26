"""
Payload format handling for StegVault.

Defines the binary structure for encrypted payloads embedded in images.
"""

import struct
from typing import Tuple
from dataclasses import dataclass


# Magic header for payload identification and versioning
MAGIC_HEADER = b"SPW1"  # StegVault Password Wallet v1
MAGIC_SIZE = 4

# Component sizes (in bytes)
SALT_SIZE = 16  # 128 bits
NONCE_SIZE = 24  # 192 bits for XChaCha20
LENGTH_SIZE = 4  # 32-bit unsigned int for ciphertext length


@dataclass
class PayloadFormat:
    """
    Structure for serialized payload format.

    Binary layout:
    [Magic: 4B] [Salt: 16B] [Nonce: 24B] [CT Length: 4B] [Ciphertext: variable]

    Note: AEAD tag (16B) is included at the end of ciphertext by PyNaCl
    """

    magic: bytes
    salt: bytes
    nonce: bytes
    ciphertext: bytes

    def __post_init__(self) -> None:
        """Validate payload components."""
        if len(self.magic) != MAGIC_SIZE:
            raise ValueError(f"Magic must be {MAGIC_SIZE} bytes")
        if len(self.salt) != SALT_SIZE:
            raise ValueError(f"Salt must be {SALT_SIZE} bytes")
        if len(self.nonce) != NONCE_SIZE:
            raise ValueError(f"Nonce must be {NONCE_SIZE} bytes")
        if len(self.ciphertext) < 16:
            raise ValueError("Ciphertext too short (must include AEAD tag)")


class PayloadError(Exception):
    """Base exception for payload-related errors."""

    pass


class PayloadFormatError(PayloadError):
    """Raised when payload format is invalid."""

    pass


def serialize_payload(salt: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """
    Serialize payload components into binary format.

    Args:
        salt: 16-byte salt for KDF
        nonce: 24-byte nonce for XChaCha20
        ciphertext: Encrypted data (includes 16-byte AEAD tag)

    Returns:
        Serialized binary payload

    Raises:
        PayloadError: If component sizes are invalid
    """
    if len(salt) != SALT_SIZE:
        raise PayloadError(f"Salt must be exactly {SALT_SIZE} bytes, got {len(salt)}")

    if len(nonce) != NONCE_SIZE:
        raise PayloadError(f"Nonce must be exactly {NONCE_SIZE} bytes, got {len(nonce)}")

    if len(ciphertext) < 16:
        raise PayloadError("Ciphertext too short (must include AEAD tag)")

    # Encode ciphertext length as 4-byte big-endian unsigned int
    ciphertext_length = struct.pack(">I", len(ciphertext))

    # Concatenate all components
    payload = MAGIC_HEADER + salt + nonce + ciphertext_length + ciphertext

    return payload


def parse_payload(payload: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Parse binary payload into components.

    Args:
        payload: Serialized binary payload

    Returns:
        Tuple of (salt, nonce, ciphertext)

    Raises:
        PayloadFormatError: If payload format is invalid or corrupted
    """
    # Calculate minimum payload size
    min_size = MAGIC_SIZE + SALT_SIZE + NONCE_SIZE + LENGTH_SIZE + 16

    if len(payload) < min_size:
        raise PayloadFormatError(f"Payload too short: {len(payload)} bytes (minimum {min_size})")

    # Parse magic header
    offset = 0
    magic = payload[offset : offset + MAGIC_SIZE]
    offset += MAGIC_SIZE

    if magic != MAGIC_HEADER:
        raise PayloadFormatError(
            f"Invalid magic header: {magic.hex()} (expected {MAGIC_HEADER.hex()})"
        )

    # Parse salt
    salt = payload[offset : offset + SALT_SIZE]
    offset += SALT_SIZE

    # Parse nonce
    nonce = payload[offset : offset + NONCE_SIZE]
    offset += NONCE_SIZE

    # Parse ciphertext length
    ciphertext_length_bytes = payload[offset : offset + LENGTH_SIZE]
    offset += LENGTH_SIZE

    ciphertext_length = struct.unpack(">I", ciphertext_length_bytes)[0]

    # Validate ciphertext length
    if ciphertext_length < 16:
        raise PayloadFormatError(f"Invalid ciphertext length: {ciphertext_length} (minimum 16)")

    # Check if enough data remains
    if len(payload) < offset + ciphertext_length:
        raise PayloadFormatError(
            f"Truncated ciphertext: expected {ciphertext_length} bytes, "
            f"got {len(payload) - offset}"
        )

    # Parse ciphertext (includes AEAD tag)
    ciphertext = payload[offset : offset + ciphertext_length]
    offset += ciphertext_length

    # Warn if there's extra data (not an error, but unusual)
    if offset < len(payload):
        extra_bytes = len(payload) - offset
        # Could log a warning here in production
        pass

    return salt, nonce, ciphertext


def calculate_payload_size(ciphertext_length: int) -> int:
    """
    Calculate total payload size for a given ciphertext length.

    Args:
        ciphertext_length: Length of ciphertext (including AEAD tag)

    Returns:
        Total payload size in bytes
    """
    return MAGIC_SIZE + SALT_SIZE + NONCE_SIZE + LENGTH_SIZE + ciphertext_length


def get_max_message_size(payload_capacity: int) -> int:
    """
    Calculate maximum plaintext message size for given payload capacity.

    Args:
        payload_capacity: Total bytes available for payload

    Returns:
        Maximum plaintext size (accounting for overhead and AEAD tag)
    """
    overhead = MAGIC_SIZE + SALT_SIZE + NONCE_SIZE + LENGTH_SIZE + 16  # 16 = AEAD tag

    if payload_capacity < overhead:
        return 0

    return payload_capacity - overhead


def validate_payload_capacity(image_capacity: int, plaintext_size: int) -> bool:
    """
    Check if image has sufficient capacity for plaintext.

    Args:
        image_capacity: Available bytes in image for payload
        plaintext_size: Size of plaintext to encrypt and embed

    Returns:
        True if capacity is sufficient, False otherwise
    """
    required = calculate_payload_size(plaintext_size + 16)  # +16 for AEAD tag
    return image_capacity >= required


def extract_full_payload(image_path: str) -> bytes:
    """
    Extract full payload from image following the standard pattern.

    This handles the multi-step extraction process:
    1. Extract header to determine payload size
    2. Derive seed from salt
    3. Extract full payload with correct seed

    Args:
        image_path: Path to image file

    Returns:
        Complete payload bytes

    Raises:
        ValueError: If magic header is invalid
        PayloadFormatError: If payload format is corrupted
    """
    from stegvault.stego import extract_payload

    # Extract just enough to get magic + salt (first 20 bytes)
    initial_extract_size = 20
    header_bytes = extract_payload(image_path, initial_extract_size, seed=0)

    # Validate magic header
    if header_bytes[:4] != b"SPW1":
        raise ValueError("Invalid or corrupted payload (bad magic header)")

    # Extract salt and derive seed
    salt = header_bytes[4:20]
    seed = int.from_bytes(salt[:4], byteorder="big")

    # Extract full header to get payload size
    header_size = 48  # 4 (magic) + 16 (salt) + 24 (nonce) + 4 (length)
    header_bytes = extract_payload(image_path, header_size, seed)

    # Parse ciphertext length from header
    ct_length = struct.unpack(">I", header_bytes[44:48])[0]
    total_payload_size = header_size + ct_length

    # Extract full payload
    payload = extract_payload(image_path, total_payload_size, seed)
    return payload
