"""
StegVault Vault Module

This module provides password vault functionality for storing multiple
credentials in a single encrypted payload.
"""

from .core import Vault, VaultEntry, VaultFormat
from .operations import (
    create_vault,
    add_entry,
    get_entry,
    list_entries,
    update_entry,
    delete_entry,
    vault_to_json,
    vault_from_json,
    detect_format,
    parse_payload,
    single_password_to_vault,
)
from .generator import (
    PasswordGenerator,
    generate_password,
    generate_passphrase,
    estimate_entropy,
    assess_password_strength,
)

__all__ = [
    "Vault",
    "VaultEntry",
    "VaultFormat",
    "create_vault",
    "add_entry",
    "get_entry",
    "list_entries",
    "update_entry",
    "delete_entry",
    "vault_to_json",
    "vault_from_json",
    "detect_format",
    "parse_payload",
    "single_password_to_vault",
    "PasswordGenerator",
    "generate_password",
    "generate_passphrase",
    "estimate_entropy",
    "assess_password_strength",
]
