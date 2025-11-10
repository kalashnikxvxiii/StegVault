"""
Steganography module for StegVault.

Handles embedding and extraction of encrypted payloads in PNG images using LSB technique.
"""

from stegvault.stego.png_lsb import (
    embed_payload,
    extract_payload,
    calculate_capacity,
    StegoError,
    CapacityError,
    ExtractionError,
)

__all__ = [
    "embed_payload",
    "extract_payload",
    "calculate_capacity",
    "StegoError",
    "CapacityError",
    "ExtractionError",
]
