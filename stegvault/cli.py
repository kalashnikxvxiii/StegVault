"""
Command-line interface for StegVault.

Provides commands for backup creation and password recovery.
"""

import click
import sys
import os
import threading
import time
from pathlib import Path
from typing import Any

from stegvault.crypto import (
    encrypt_data,
    decrypt_data,
    verify_passphrase_strength,
    CryptoError,
    DecryptionError,
)
from stegvault.stego import (
    embed_payload,
    extract_payload,
    calculate_capacity,
    StegoError,
    CapacityError,
)
from stegvault.utils import (
    serialize_payload,
    parse_payload,
    validate_payload_capacity,
    PayloadFormatError,
)
from stegvault.config import (
    load_config,
    Config,
    ConfigError,
)


@click.group()
@click.version_option(version="0.2.0")
def main() -> None:
    """
    StegVault - Password Manager with Steganography

    Securely embed encrypted credentials within images using steganographic techniques.
    """
    pass


@main.command()
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Master password to encrypt and embed",
)
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Encryption passphrase (keep this secret!)",
)
@click.option(
    "--image",
    "-i",
    required=True,
    type=click.Path(exists=True),
    help="Cover image (PNG format recommended)",
)
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output path for stego image"
)
@click.option(
    "--check-strength/--no-check-strength", default=True, help="Verify passphrase strength"
)
def backup(password: str, passphrase: str, image: str, output: str, check_strength: bool) -> None:
    """
    Create a backup by embedding encrypted password in an image.

    The password is encrypted using XChaCha20-Poly1305 with Argon2id key
    derivation, then embedded in the image using LSB steganography.

    \b
    Example:
        stegvault backup -i cover.png -o backup.png
    """
    try:
        # Load configuration
        try:
            config = load_config()
        except ConfigError as e:
            click.echo(f"Warning: Failed to load config: {e}", err=True)
            click.echo("Using default settings...", err=True)
            from stegvault.config import get_default_config
            config = get_default_config()

        click.echo("Creating encrypted backup...")

        # Verify passphrase strength
        if check_strength:
            is_strong, message = verify_passphrase_strength(passphrase)
            if not is_strong:
                click.echo(f"Warning: {message}", err=True)
                if not click.confirm("Continue anyway?"):
                    click.echo("Backup cancelled.")
                    sys.exit(0)

        # Check if image file exists
        if not os.path.exists(image):
            click.echo(f"Error: Image file not found: {image}", err=True)
            sys.exit(1)

        # Convert password to bytes
        password_bytes = password.encode("utf-8")

        # Check image capacity
        from PIL import Image

        img = Image.open(image)
        capacity = calculate_capacity(img)
        img.close()

        click.echo(f"Image capacity: {capacity} bytes")

        if not validate_payload_capacity(capacity, len(password_bytes)):
            click.echo(
                f"Error: Image too small for password. Need at least "
                f"{len(password_bytes) + 64} bytes, have {capacity} bytes",
                err=True,
            )
            sys.exit(1)

        # Encrypt password
        click.echo("Encrypting password...", nl=False)
        click.echo(" (this may take a few seconds)", err=True)

        # Show progress for key derivation (Argon2id is intentionally slow)
        result = [None]
        exception = [None]

        def encrypt_worker():
            try:
                result[0] = encrypt_data(
                    password_bytes,
                    passphrase,
                    time_cost=config.crypto.argon2_time_cost,
                    memory_cost=config.crypto.argon2_memory_cost,
                    parallelism=config.crypto.argon2_parallelism,
                )
            except Exception as e:
                exception[0] = e

        with click.progressbar(
            length=100,
            label="Deriving encryption key",
            show_eta=False,
            show_percent=False,
            bar_template="%(label)s [%(bar)s] %(info)s",
        ) as bar:
            # Simulate progress during KDF (it's not truly measurable)
            thread = threading.Thread(target=encrypt_worker)
            thread.start()

            # Update progress bar while KDF is running
            while thread.is_alive():
                bar.update(10)
                time.sleep(0.1)

            thread.join()

            if exception[0]:
                raise exception[0]

            bar.update(100)  # Complete the bar

        if result[0] is None:
            click.echo("Error: Encryption failed", err=True)
            sys.exit(1)

        ciphertext, salt, nonce = result[0]
        click.echo("[OK] Encryption complete")

        # Serialize payload
        payload = serialize_payload(salt, nonce, ciphertext)
        click.echo(f"Payload size: {len(payload)} bytes")

        # Derive seed from salt for reproducible pixel ordering
        seed = int.from_bytes(salt[:4], byteorder="big")

        # Embed in image
        click.echo("Embedding payload in image...")
        embed_payload(image, payload, seed, output)
        click.echo("[OK] Embedding complete")

        click.echo(f"[OK] Backup created successfully: {output}")
        click.echo("\nIMPORTANT:")
        click.echo("- Keep both the image AND passphrase safe")
        click.echo("- Losing either means permanent data loss")
        click.echo("- Do not recompress JPEG images (use PNG)")
        click.echo("- Create multiple backup copies")

    except CapacityError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except CryptoError as e:
        click.echo(f"Encryption error: {e}", err=True)
        sys.exit(1)
    except StegoError as e:
        click.echo(f"Steganography error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--image",
    "-i",
    required=True,
    type=click.Path(exists=True),
    help="Stego image containing encrypted backup",
)
@click.option(
    "--passphrase", prompt=True, hide_input=True, help="Encryption passphrase used during backup"
)
@click.option(
    "--output",
    "-o",
    type=click.File("w"),
    default="-",
    help="Output file for recovered password (default: stdout)",
)
def restore(image: str, passphrase: str, output: Any) -> None:
    """
    Restore password from a stego image backup.

    Extracts and decrypts the password embedded in the image.

    \b
    Example:
        stegvault restore -i backup.png
        stegvault restore -i backup.png -o password.txt
    """
    try:
        # Load configuration
        try:
            config = load_config()
        except ConfigError as e:
            click.echo(f"Warning: Failed to load config: {e}", err=True)
            click.echo("Using default settings...", err=True)
            from stegvault.config import get_default_config
            config = get_default_config()

        click.echo("Restoring password from backup...", err=True)

        # Check if image exists
        if not os.path.exists(image):
            click.echo(f"Error: Image file not found: {image}", err=True)
            sys.exit(1)

        # Extract payload from image
        # NOTE: The first 20 bytes (magic + salt) are stored sequentially
        # This allows us to extract them without knowing the seed
        from PIL import Image

        img = Image.open(image)
        img.load()
        capacity = calculate_capacity(img)
        img.close()

        click.echo("Extracting payload header...", err=True)

        # Extract just enough to get magic + salt (first 20 bytes)
        # These are stored sequentially, so seed doesn't matter for this part
        initial_extract_size = 20
        seed_placeholder = 0  # Seed doesn't matter for sequential extraction
        header_bytes = extract_payload(image, initial_extract_size, seed_placeholder)

        # Validate magic header
        if header_bytes[:4] != b'SPW1':
            click.echo("Error: Invalid or corrupted payload (bad magic header)", err=True)
            sys.exit(1)

        # Extract salt from header
        salt = header_bytes[4:20]

        # Derive correct seed from salt for the remaining payload
        seed = int.from_bytes(salt[:4], byteorder="big")

        # Now extract the full header to get payload size
        header_size = 48  # 4 (magic) + 16 (salt) + 24 (nonce) + 4 (length)
        header_bytes = extract_payload(image, header_size, seed)

        # Parse header to get ciphertext length
        try:
            import struct
            ct_length = struct.unpack(">I", header_bytes[44:48])[0]
        except:
            click.echo("Error: Invalid or corrupted payload", err=True)
            sys.exit(1)

        total_payload_size = header_size + ct_length
        click.echo(f"Payload size: {total_payload_size} bytes", err=True)

        if total_payload_size > capacity:
            click.echo("Error: Payload size exceeds image capacity", err=True)
            sys.exit(1)

        # Extract full payload
        click.echo("Extracting full payload...", err=True)
        payload = extract_payload(image, total_payload_size, seed)

        # Parse payload
        click.echo("Parsing payload...", err=True)
        salt, nonce, ciphertext = parse_payload(payload)

        # Decrypt
        click.echo("Decrypting password...", nl=False, err=True)
        click.echo(" (deriving key, this may take a few seconds)", err=True)

        # Show progress for key derivation (Argon2id is intentionally slow)
        result = [None]
        exception = [None]

        def decrypt_worker():
            try:
                result[0] = decrypt_data(
                    ciphertext,
                    salt,
                    nonce,
                    passphrase,
                    time_cost=config.crypto.argon2_time_cost,
                    memory_cost=config.crypto.argon2_memory_cost,
                    parallelism=config.crypto.argon2_parallelism,
                )
            except Exception as e:
                exception[0] = e

        with click.progressbar(
            length=100,
            label="Deriving decryption key",
            show_eta=False,
            show_percent=False,
            bar_template="%(label)s [%(bar)s] %(info)s",
            file=sys.stderr,
        ) as bar:
            thread = threading.Thread(target=decrypt_worker)
            thread.start()

            # Update progress bar while KDF is running
            while thread.is_alive():
                bar.update(10)
                time.sleep(0.1)

            thread.join()

            if exception[0]:
                raise exception[0]

            bar.update(100)  # Complete the bar

        if result[0] is None:
            click.echo("\nError: Decryption failed", err=True)
            sys.exit(1)

        password_bytes = result[0]
        click.echo("[OK] Decryption complete", err=True)

        # Convert to string
        password = password_bytes.decode("utf-8")

        # Output
        if output.name == "<stdout>":
            click.echo("\n" + "=" * 50, err=True)
            click.echo("[OK] Password recovered successfully!", err=True)
            click.echo("=" * 50 + "\n", err=True)

        output.write(password)

        if output.name != "<stdout>":
            output.write("\n")
            click.echo(f"\n[OK] Password saved to: {output.name}", err=True)

    except DecryptionError:
        click.echo("\nError: Decryption failed. Wrong passphrase or corrupted data.", err=True)
        sys.exit(1)
    except PayloadFormatError as e:
        click.echo(f"\nError: Invalid payload format: {e}", err=True)
        sys.exit(1)
    except StegoError as e:
        click.echo(f"\nError: Extraction failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nUnexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--image", "-i", required=True, type=click.Path(exists=True), help="Image file to check"
)
def check(image: str) -> None:
    """
    Check image capacity for password storage.

    Displays how much data can be embedded in the given image.

    \b
    Example:
        stegvault check -i myimage.png
    """
    try:
        from PIL import Image

        if not os.path.exists(image):
            click.echo(f"Error: Image file not found: {image}", err=True)
            sys.exit(1)

        img = Image.open(image)

        click.echo(f"Image: {image}")
        click.echo(f"Format: {img.format}")
        click.echo(f"Mode: {img.mode}")
        click.echo(f"Size: {img.width}x{img.height} pixels")

        if img.mode not in ("RGB", "RGBA"):
            click.echo(f"\nWarning: Unsupported mode '{img.mode}'. Convert to RGB first.")
            img.close()
            sys.exit(1)

        capacity = calculate_capacity(img)
        img.close()

        click.echo(f"\nCapacity: {capacity} bytes ({capacity / 1024:.2f} KB)")

        # Calculate max password sizes
        max_password = capacity - 64  # Accounting for overhead
        click.echo(f"Max password size: ~{max_password} bytes ({max_password} characters)")

        if capacity < 100:
            click.echo("\nWarning: Image is very small. Consider using a larger image.")
        elif capacity < 500:
            click.echo("\nNote: Image capacity is limited. Suitable for short passwords only.")
        else:
            click.echo("\n[OK] Image has sufficient capacity for password storage.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group()
def config() -> None:
    """
    Manage StegVault configuration.

    Subcommands: show, init, path
    """
    pass


@config.command()
def show() -> None:
    """Display current configuration."""
    try:
        from stegvault.config import load_config, get_config_path

        config_path = get_config_path()

        if not config_path.exists():
            click.echo("No configuration file found.")
            click.echo(f"Expected location: {config_path}")
            click.echo("\nUsing default settings:")
        else:
            click.echo(f"Configuration file: {config_path}\n")

        try:
            cfg = load_config()

            click.echo("[crypto]")
            click.echo(f"  argon2_time_cost    = {cfg.crypto.argon2_time_cost}")
            click.echo(f"  argon2_memory_cost  = {cfg.crypto.argon2_memory_cost} KB ({cfg.crypto.argon2_memory_cost / 1024:.0f} MB)")
            click.echo(f"  argon2_parallelism  = {cfg.crypto.argon2_parallelism}")
            click.echo()
            click.echo("[cli]")
            click.echo(f"  check_strength      = {cfg.cli.check_strength}")
            click.echo(f"  default_image_dir   = {cfg.cli.default_image_dir or '(not set)'}")
            click.echo(f"  verbose             = {cfg.cli.verbose}")

        except ConfigError as e:
            click.echo(f"Error loading config: {e}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command()
def init() -> None:
    """Create default configuration file."""
    try:
        from stegvault.config import save_config, get_default_config, get_config_path

        config_path = get_config_path()

        if config_path.exists():
            click.echo(f"Configuration file already exists: {config_path}")
            if not click.confirm("Overwrite with default settings?"):
                click.echo("Cancelled.")
                sys.exit(0)

        cfg = get_default_config()
        save_config(cfg)

        click.echo(f"Created configuration file: {config_path}")
        click.echo("\nDefault settings:")
        click.echo(f"  Argon2 time cost:    {cfg.crypto.argon2_time_cost} iterations")
        click.echo(f"  Argon2 memory cost:  {cfg.crypto.argon2_memory_cost / 1024:.0f} MB")
        click.echo(f"  Argon2 parallelism:  {cfg.crypto.argon2_parallelism} threads")

    except ConfigError as e:
        click.echo(f"Error creating config: {e}", err=True)
        sys.exit(1)


@config.command()
def path() -> None:
    """Show configuration file path."""
    from stegvault.config import get_config_path, get_config_dir

    config_path = get_config_path()
    config_dir = get_config_dir()

    click.echo(f"Config directory: {config_dir}")
    click.echo(f"Config file:      {config_path}")
    click.echo()

    if config_path.exists():
        click.echo(f"Status: File exists")
    else:
        click.echo(f"Status: File not found (using defaults)")
        click.echo(f"\nRun 'stegvault config init' to create it.")


@main.command()
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True),
    help="Batch configuration file (JSON format)",
)
@click.option(
    "--stop-on-error/--continue-on-error",
    default=False,
    help="Stop processing on first error (default: continue)",
)
def batch_backup(config: str, stop_on_error: bool) -> None:
    """
    Create multiple backups from a configuration file.

    The config file should be in JSON format with the following structure:
    {
        "passphrase": "CommonPassphrase123",
        "backups": [
            {
                "password": "Password1",
                "image": "cover1.png",
                "output": "backup1.png",
                "label": "Gmail backup"
            }
        ]
    }

    \b
    Example:
        stegvault batch-backup -c batch_config.json
    """
    try:
        from stegvault.batch import load_batch_config, process_batch_backup, BatchError

        click.echo("Loading batch configuration...")
        batch_config = load_batch_config(config)

        total_jobs = len(batch_config.backup_jobs)
        if total_jobs == 0:
            click.echo("No backup jobs found in configuration.", err=True)
            sys.exit(1)

        click.echo(f"Processing {total_jobs} backup job(s)...\n")

        def progress_callback(current, total, label):
            click.echo(f"[{current}/{total}] Processing: {label}...", err=True)

        successful, failed, errors = process_batch_backup(
            batch_config,
            progress_callback=progress_callback,
            stop_on_error=stop_on_error
        )

        # Summary
        click.echo(f"\n{'='*50}")
        click.echo(f"Batch Backup Complete")
        click.echo(f"{'='*50}")
        click.echo(f"Successful: {successful}")
        click.echo(f"Failed:     {failed}")

        if errors:
            click.echo(f"\nErrors:")
            for error in errors:
                click.echo(f"  - {error}", err=True)

        sys.exit(0 if failed == 0 else 1)

    except BatchError as e:
        click.echo(f"Batch error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True),
    help="Batch configuration file (JSON format)",
)
@click.option(
    "--stop-on-error/--continue-on-error",
    default=False,
    help="Stop processing on first error (default: continue)",
)
@click.option(
    "--show-passwords/--no-show-passwords",
    default=False,
    help="Display recovered passwords (default: hide)",
)
def batch_restore(config: str, stop_on_error: bool, show_passwords: bool) -> None:
    """
    Restore multiple passwords from a configuration file.

    The config file should be in JSON format with the following structure:
    {
        "passphrase": "CommonPassphrase123",
        "restores": [
            {
                "image": "backup1.png",
                "output": "password1.txt",
                "label": "Gmail restore"
            }
        ]
    }

    \b
    Example:
        stegvault batch-restore -c batch_config.json
        stegvault batch-restore -c batch_config.json --show-passwords
    """
    try:
        from stegvault.batch import load_batch_config, process_batch_restore, BatchError

        click.echo("Loading batch configuration...")
        batch_config = load_batch_config(config)

        total_jobs = len(batch_config.restore_jobs)
        if total_jobs == 0:
            click.echo("No restore jobs found in configuration.", err=True)
            sys.exit(1)

        click.echo(f"Processing {total_jobs} restore job(s)...\n")

        def progress_callback(current, total, label):
            click.echo(f"[{current}/{total}] Processing: {label}...", err=True)

        successful, failed, errors, recovered = process_batch_restore(
            batch_config,
            progress_callback=progress_callback,
            stop_on_error=stop_on_error
        )

        # Summary
        click.echo(f"\n{'='*50}")
        click.echo(f"Batch Restore Complete")
        click.echo(f"{'='*50}")
        click.echo(f"Successful: {successful}")
        click.echo(f"Failed:     {failed}")

        if errors:
            click.echo(f"\nErrors:")
            for error in errors:
                click.echo(f"  - {error}", err=True)

        if show_passwords and recovered:
            click.echo(f"\nRecovered Passwords:")
            for label, password in recovered.items():
                click.echo(f"  {label}: {password}")

        sys.exit(0 if failed == 0 else 1)

    except BatchError as e:
        click.echo(f"Batch error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
