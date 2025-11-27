"""
Steganography module for StegVault.

Handles embedding and extraction of encrypted payloads in images.
Automatically detects format (PNG/JPEG) and uses appropriate method.
"""

from stegvault.stego.dispatcher import (
    embed_payload,
    extract_payload,
    calculate_capacity,
)
from stegvault.stego.png_lsb import (
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
