"""
Gallery management for StegVault.

This module provides functionality for managing multiple vault images
in a centralized gallery with metadata storage and cross-vault search.
"""

from stegvault.gallery.core import Gallery, VaultMetadata
from stegvault.gallery.db import GalleryDB
from stegvault.gallery.operations import (
    add_vault,
    remove_vault,
    list_vaults,
    refresh_vault,
    get_vault,
)

__all__ = [
    "Gallery",
    "VaultMetadata",
    "GalleryDB",
    "add_vault",
    "remove_vault",
    "list_vaults",
    "refresh_vault",
    "get_vault",
]
