"""
Batch operations for StegVault.

Handles processing multiple backup/restore operations from configuration files.
"""

from stegvault.batch.core import (
    process_batch_backup,
    process_batch_restore,
    load_batch_config,
    BatchConfig,
    BatchError,
)

__all__ = [
    "process_batch_backup",
    "process_batch_restore",
    "load_batch_config",
    "BatchConfig",
    "BatchError",
]
