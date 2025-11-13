"""
Core batch processing functionality.

Handles multiple backup/restore operations from configuration files.
"""

import json
import os
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass

from stegvault.crypto import encrypt_data, decrypt_data
from stegvault.stego import embed_payload, extract_payload, calculate_capacity
from stegvault.utils import (
    serialize_payload,
    parse_payload,
    validate_payload_capacity,
)
from stegvault.config import load_config, ConfigError, get_default_config
from PIL import Image


class BatchError(Exception):
    """Batch operation errors."""

    pass


@dataclass
class BackupJob:
    """Single backup job configuration."""

    password: str
    image: str
    output: str
    label: Optional[str] = None  # Optional label for identification


@dataclass
class RestoreJob:
    """Single restore job configuration."""

    image: str
    output: Optional[str] = None  # If None, output to stdout
    label: Optional[str] = None


@dataclass
class BatchConfig:
    """Batch operation configuration."""

    passphrase: str
    backup_jobs: List[BackupJob]
    restore_jobs: List[RestoreJob]


def load_batch_config(config_file: str) -> BatchConfig:
    """
    Load batch configuration from JSON file.

    Args:
        config_file: Path to JSON configuration file

    Returns:
        BatchConfig object

    Raises:
        BatchError: If config file is invalid or missing

    Example config format:
    {
        "passphrase": "CommonPassphrase123",
        "backups": [
            {
                "password": "Password1",
                "image": "cover1.png",
                "output": "backup1.png",
                "label": "Gmail backup"
            }
        ],
        "restores": [
            {
                "image": "backup1.png",
                "output": "password1.txt",
                "label": "Gmail restore"
            }
        ]
    }
    """
    if not os.path.exists(config_file):
        raise BatchError(f"Config file not found: {config_file}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        passphrase = data.get("passphrase")
        if not passphrase:
            raise BatchError("Missing required field: passphrase")

        # Parse backup jobs
        backup_jobs: List[BackupJob] = []
        for job_data in data.get("backups", []):
            job = BackupJob(
                password=job_data["password"],
                image=job_data["image"],
                output=job_data["output"],
                label=job_data.get("label"),
            )
            backup_jobs.append(job)

        # Parse restore jobs
        restore_jobs: List[RestoreJob] = []
        for job_data in data.get("restores", []):
            restore_job = RestoreJob(
                image=job_data["image"], output=job_data.get("output"), label=job_data.get("label")
            )
            restore_jobs.append(restore_job)

        return BatchConfig(
            passphrase=passphrase, backup_jobs=backup_jobs, restore_jobs=restore_jobs
        )

    except json.JSONDecodeError as e:
        raise BatchError(f"Invalid JSON format: {e}")
    except KeyError as e:
        raise BatchError(f"Missing required field: {e}")
    except Exception as e:
        raise BatchError(f"Failed to load config: {e}")


def process_batch_backup(
    config: BatchConfig,
    progress_callback: Optional[Callable[[int, int, Optional[str]], None]] = None,
    stop_on_error: bool = False,
) -> Tuple[int, int, List[str]]:
    """
    Process multiple backup operations.

    Args:
        config: Batch configuration
        progress_callback: Optional callback(current, total, job_label)
        stop_on_error: If True, stop on first error; if False, continue

    Returns:
        Tuple of (successful_count, failed_count, error_messages)
    """
    # Load user config for KDF parameters
    try:
        user_config = load_config()
    except ConfigError:
        user_config = get_default_config()

    successful = 0
    failed = 0
    errors = []

    total = len(config.backup_jobs)

    for idx, job in enumerate(config.backup_jobs):
        job_label = job.label or f"Job {idx + 1}"

        if progress_callback:
            progress_callback(idx + 1, total, job_label)

        try:
            # Validate image exists
            if not os.path.exists(job.image):
                raise BatchError(f"Image not found: {job.image}")

            # Check capacity
            img = Image.open(job.image)
            capacity = calculate_capacity(img)
            img.close()

            password_bytes = job.password.encode("utf-8")
            if not validate_payload_capacity(capacity, len(password_bytes)):
                raise BatchError(
                    f"Image too small for password (need {len(password_bytes) + 64} bytes, have {capacity})"
                )

            # Encrypt
            ciphertext, salt, nonce = encrypt_data(
                password_bytes,
                config.passphrase,
                time_cost=user_config.crypto.argon2_time_cost,
                memory_cost=user_config.crypto.argon2_memory_cost,
                parallelism=user_config.crypto.argon2_parallelism,
            )

            # Serialize and embed
            payload = serialize_payload(salt, nonce, ciphertext)
            seed = int.from_bytes(salt[:4], byteorder="big")
            embed_payload(job.image, payload, seed, job.output)

            successful += 1

        except Exception as e:
            failed += 1
            error_msg = f"{job_label}: {str(e)}"
            errors.append(error_msg)

            if stop_on_error:
                break

    return successful, failed, errors


def process_batch_restore(
    config: BatchConfig,
    progress_callback: Optional[Callable[[int, int, Optional[str]], None]] = None,
    stop_on_error: bool = False,
) -> Tuple[int, int, List[str], Dict[str, str]]:
    """
    Process multiple restore operations.

    Args:
        config: Batch configuration
        progress_callback: Optional callback(current, total, job_label)
        stop_on_error: If True, stop on first error; if False, continue

    Returns:
        Tuple of (successful_count, failed_count, error_messages, recovered_passwords)
        recovered_passwords: Dict[label, password]
    """
    # Load user config for KDF parameters
    try:
        user_config = load_config()
    except ConfigError:
        user_config = get_default_config()

    successful = 0
    failed = 0
    errors = []
    recovered = {}

    total = len(config.restore_jobs)

    for idx, job in enumerate(config.restore_jobs):
        job_label = job.label or f"Job {idx + 1}"

        if progress_callback:
            progress_callback(idx + 1, total, job_label)

        try:
            # Validate image exists
            if not os.path.exists(job.image):
                raise BatchError(f"Image not found: {job.image}")

            # Extract header to get salt
            img = Image.open(job.image)
            img.load()
            capacity = calculate_capacity(img)
            img.close()

            # Extract initial header (magic + salt)
            initial_extract_size = 20
            seed_placeholder = 0
            header_bytes = extract_payload(job.image, initial_extract_size, seed_placeholder)

            if header_bytes[:4] != b"SPW1":
                raise BatchError("Invalid or corrupted payload")

            salt = header_bytes[4:20]
            seed = int.from_bytes(salt[:4], byteorder="big")

            # Extract full header
            header_size = 48
            header_bytes = extract_payload(job.image, header_size, seed)

            import struct

            ct_length = struct.unpack(">I", header_bytes[44:48])[0]

            total_payload_size = header_size + ct_length
            if total_payload_size > capacity:
                raise BatchError("Payload size exceeds image capacity")

            # Extract and parse
            payload = extract_payload(job.image, total_payload_size, seed)
            salt, nonce, ciphertext = parse_payload(payload)

            # Decrypt
            password_bytes = decrypt_data(
                ciphertext,
                salt,
                nonce,
                config.passphrase,
                time_cost=user_config.crypto.argon2_time_cost,
                memory_cost=user_config.crypto.argon2_memory_cost,
                parallelism=user_config.crypto.argon2_parallelism,
            )

            password = password_bytes.decode("utf-8")
            recovered[job_label] = password

            # Save to file if specified
            # SECURITY NOTE: This intentionally writes passwords to files as requested by user.
            # The user is responsible for securing these output files appropriately.
            # nosemgrep: python.lang.security.audit.dangerous-system-call.dangerous-system-call
            if job.output:
                with open(job.output, "w", encoding="utf-8") as f:
                    f.write(password)  # nosec B608 - intentional password write

            successful += 1

        except Exception as e:
            failed += 1
            error_msg = f"{job_label}: {str(e)}"
            errors.append(error_msg)

            if stop_on_error:
                break

    return successful, failed, errors, recovered
