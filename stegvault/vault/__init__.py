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
    import_vault_from_file,
    search_entries,
    filter_by_tags,
    filter_by_url,
)
from .generator import (
    PasswordGenerator,
    generate_password,
    generate_passphrase,
    estimate_entropy,
    assess_password_strength,
)
from .totp import (
    generate_totp_secret,
    generate_totp_code,
    verify_totp_code,
    get_totp_provisioning_uri,
    generate_qr_code_ascii,
    get_totp_time_remaining,
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
    "import_vault_from_file",
    "search_entries",
    "filter_by_tags",
    "filter_by_url",
    "PasswordGenerator",
    "generate_password",
    "generate_passphrase",
    "estimate_entropy",
    "assess_password_strength",
    "generate_totp_secret",
    "generate_totp_code",
    "verify_totp_code",
    "get_totp_provisioning_uri",
    "generate_qr_code_ascii",
    "get_totp_time_remaining",
]
