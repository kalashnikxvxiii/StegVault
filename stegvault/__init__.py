"""
StegVault - Password Manager with Steganography

A secure password manager that embeds encrypted credentials within images
using steganographic techniques.
"""

__version__ = "0.7.5"
__author__ = "Kalashnikxv"

from stegvault.crypto import encrypt_data, decrypt_data
from stegvault.stego import embed_payload, extract_payload, calculate_capacity
from stegvault.utils import serialize_payload, parse_payload

__all__ = [
    "encrypt_data",
    "decrypt_data",
    "embed_payload",
    "extract_payload",
    "calculate_capacity",
    "serialize_payload",
    "parse_payload",
]
