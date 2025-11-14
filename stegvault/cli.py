"""
Command-line interface for StegVault.

Provides commands for backup creation and password recovery.
"""

import click
import sys
import os
import threading
import time
from typing import Any, Optional, List

from stegvault import __version__
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
    ConfigError,
)


@click.group()
@click.version_option(version=__version__)
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
        result: List[Any] = [None]
        exception: List[Any] = [None]

        def encrypt_worker() -> None:
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
        if header_bytes[:4] != b"SPW1":
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
        result: List[Any] = [None]
        exception: List[Any] = [None]

        def decrypt_worker() -> None:
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
            click.echo(
                f"  argon2_memory_cost  = {cfg.crypto.argon2_memory_cost} KB ({cfg.crypto.argon2_memory_cost / 1024:.0f} MB)"
            )
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

        def progress_callback(current: int, total: int, label: Optional[str]) -> None:
            click.echo(f"[{current}/{total}] Processing: {label}...", err=True)

        successful, failed, errors = process_batch_backup(
            batch_config, progress_callback=progress_callback, stop_on_error=stop_on_error
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

        def progress_callback(current: int, total: int, label: Optional[str]) -> None:
            click.echo(f"[{current}/{total}] Processing: {label}...", err=True)

        successful, failed, errors, recovered = process_batch_restore(
            batch_config, progress_callback=progress_callback, stop_on_error=stop_on_error
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


@main.group()
def vault() -> None:
    """
    Manage password vaults (multiple passwords in one image).

    The vault commands allow you to store and manage multiple credentials
    within a single image, transforming it into a complete password manager.

    \b
    Subcommands:
      create  - Create a new vault in an image
      add     - Add an entry to an existing vault
      get     - Retrieve a password from the vault
      list    - List all keys in the vault
      show    - Show entry details (without password)
      update  - Update an existing entry
      delete  - Delete an entry from the vault
      export  - Export vault to JSON file
    """
    pass


@vault.command()
@click.option("--image", "-i", required=True, type=click.Path(exists=True), help="Cover image")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output path for vault image")
@click.option("--passphrase", prompt=True, hide_input=True, confirmation_prompt=True, help="Vault encryption passphrase")
@click.option("--key", "-k", required=True, help="Entry key (e.g., 'gmail', 'github')")
@click.option("--password", "-p", help="Password for this entry")
@click.option("--generate", "-g", is_flag=True, help="Generate a secure password")
@click.option("--username", "-u", help="Username or email")
@click.option("--url", help="Website URL")
@click.option("--notes", "-n", help="Additional notes")
def create(image: str, output: str, passphrase: str, key: str, password: Optional[str], generate: bool, username: Optional[str], url: Optional[str], notes: Optional[str]) -> None:
    """
    Create a new vault with the first entry.

    \b
    Example:
        stegvault vault create -i cover.png -o vault.png -k gmail -u user@gmail.com --generate
    """
    try:
        from stegvault.vault import create_vault, add_entry, vault_to_json, generate_password
        from PIL import Image

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config
            config = get_default_config()

        # Handle password generation or prompt
        if generate and password:
            click.echo("Error: Cannot use both --generate and --password", err=True)
            sys.exit(1)

        if generate:
            password = generate_password(length=20)
            click.echo(f"Generated password: {password}")
        elif not password:
            password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

        # Create vault and add first entry
        click.echo(f"Creating vault with entry '{key}'...")
        vault_obj = create_vault()
        add_entry(vault_obj, key=key, password=password, username=username, url=url, notes=notes)

        # Serialize vault to JSON
        vault_json = vault_to_json(vault_obj)
        vault_bytes = vault_json.encode("utf-8")

        # Check image capacity
        img = Image.open(image)
        capacity = calculate_capacity(img)
        img.close()

        click.echo(f"Image capacity: {capacity} bytes")
        click.echo(f"Vault size: {len(vault_bytes)} bytes")

        if not validate_payload_capacity(capacity, len(vault_bytes)):
            click.echo(f"Error: Image too small. Need {len(vault_bytes) + 64} bytes, have {capacity} bytes", err=True)
            sys.exit(1)

        # Encrypt vault
        click.echo("Encrypting vault...")
        result: List[Any] = [None]
        exception: List[Any] = [None]

        def encrypt_worker() -> None:
            try:
                result[0] = encrypt_data(
                    vault_bytes,
                    passphrase,
                    time_cost=config.crypto.argon2_time_cost,
                    memory_cost=config.crypto.argon2_memory_cost,
                    parallelism=config.crypto.argon2_parallelism,
                )
            except Exception as e:
                exception[0] = e

        with click.progressbar(length=100, label="Deriving encryption key", show_eta=False, show_percent=False) as bar:
            thread = threading.Thread(target=encrypt_worker)
            thread.start()
            while thread.is_alive():
                bar.update(10)
                time.sleep(0.1)
            thread.join()
            if exception[0]:
                raise exception[0]
            bar.update(100)

        if result[0] is None:
            click.echo("Error: Encryption failed", err=True)
            sys.exit(1)

        ciphertext, salt, nonce = result[0]
        click.echo("[OK] Encryption complete")

        # Serialize and embed
        payload = serialize_payload(salt, nonce, ciphertext)
        seed = int.from_bytes(salt[:4], byteorder="big")

        click.echo("Embedding vault in image...")
        embed_payload(image, payload, seed, output)

        click.echo(f"[OK] Vault created successfully: {output}")
        click.echo(f"     Entries: 1")
        click.echo(f"     Keys: {key}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--output", "-o", required=True, type=click.Path(), help="Output path for updated vault")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--key", "-k", required=True, help="Entry key")
@click.option("--password", "-p", help="Password for this entry")
@click.option("--generate", "-g", is_flag=True, help="Generate a secure password")
@click.option("--username", "-u", help="Username or email")
@click.option("--url", help="Website URL")
@click.option("--notes", "-n", help="Additional notes")
def add(vault_image: str, output: str, passphrase: str, key: str, password: Optional[str], generate: bool, username: Optional[str], url: Optional[str], notes: Optional[str]) -> None:
    """
    Add a new entry to an existing vault.

    \b
    Example:
        stegvault vault add vault.png -o vault_updated.png -k github --generate
    """
    try:
        from stegvault.vault import add_entry as vault_add, vault_from_json, vault_to_json, generate_password, parse_payload
        from PIL import Image

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config
            config = get_default_config()

        # Handle password
        if generate and password:
            click.echo("Error: Cannot use both --generate and --password", err=True)
            sys.exit(1)

        if generate:
            password = generate_password(length=20)
            click.echo(f"Generated password: {password}")
        elif not password:
            password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

        # Extract and decrypt existing vault
        click.echo("Extracting vault from image...")
        img = Image.open(vault_image)
        seed = 0  # Will be determined from salt
        img.close()

        payload = extract_payload(vault_image, seed)
        salt, nonce, ciphertext = parse_payload(payload)

        # Decrypt
        click.echo("Decrypting vault...")
        decrypted = decrypt_data(ciphertext, passphrase, salt, nonce,
                                 time_cost=config.crypto.argon2_time_cost,
                                 memory_cost=config.crypto.argon2_memory_cost,
                                 parallelism=config.crypto.argon2_parallelism)

        # Parse vault
        parsed = parse_payload(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            click.echo("Use 'stegvault restore' to retrieve it", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Add new entry
        click.echo(f"Adding entry '{key}' to vault...")
        vault_add(vault_obj, key=key, password=password, username=username, url=url, notes=notes)

        # Re-encrypt and embed
        vault_json = vault_to_json(vault_obj)
        vault_bytes = vault_json.encode("utf-8")

        # Check capacity
        img = Image.open(vault_image)
        capacity = calculate_capacity(img)
        img.close()

        if not validate_payload_capacity(capacity, len(vault_bytes)):
            click.echo(f"Error: Vault too large for image", err=True)
            sys.exit(1)

        click.echo("Re-encrypting vault...")
        ciphertext_new, salt_new, nonce_new = encrypt_data(
            vault_bytes, passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

        payload_new = serialize_payload(salt_new, nonce_new, ciphertext_new)
        seed_new = int.from_bytes(salt_new[:4], byteorder="big")

        click.echo("Embedding updated vault...")
        embed_payload(vault_image, payload_new, seed_new, output)

        click.echo(f"[OK] Entry added successfully: {output}")
        click.echo(f"     Total entries: {len(vault_obj.entries)}")

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--key", "-k", required=True, help="Entry key to retrieve")
@click.option("--copy/--no-copy", default=False, help="Copy password to clipboard (if available)")
def get(vault_image: str, passphrase: str, key: str, copy: bool) -> None:
    """
    Retrieve a password from the vault.

    \b
    Example:
        stegvault vault get vault.png -k gmail
    """
    try:
        from stegvault.vault import get_entry, parse_payload

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config
            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload = extract_payload(vault_image, 0)
        salt, nonce, ciphertext = parse_payload(payload)

        decrypted = decrypt_data(ciphertext, passphrase, salt, nonce,
                                 time_cost=config.crypto.argon2_time_cost,
                                 memory_cost=config.crypto.argon2_memory_cost,
                                 parallelism=config.crypto.argon2_parallelism)

        # Parse vault
        parsed = parse_payload(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Get entry
        entry = get_entry(vault_obj, key)
        if not entry:
            click.echo(f"Error: Entry '{key}' not found", err=True)
            click.echo(f"Available keys: {', '.join(vault_obj.list_keys())}", err=True)
            sys.exit(1)

        click.echo(f"\nEntry: {key}")
        if entry.username:
            click.echo(f"Username: {entry.username}")
        if entry.url:
            click.echo(f"URL: {entry.url}")
        click.echo(f"Password: {entry.password}")
        if entry.notes:
            click.echo(f"Notes: {entry.notes}")

        if copy:
            try:
                import pyperclip
                pyperclip.copy(entry.password)
                click.echo("\n[OK] Password copied to clipboard")
            except ImportError:
                click.echo("\nWarning: pyperclip not installed, cannot copy to clipboard", err=True)

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
def list(vault_image: str, passphrase: str) -> None:
    """
    List all entry keys in the vault (without showing passwords).

    \b
    Example:
        stegvault vault list vault.png
    """
    try:
        from stegvault.vault import list_entries, parse_payload

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config
            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload = extract_payload(vault_image, 0)
        salt, nonce, ciphertext = parse_payload(payload)

        decrypted = decrypt_data(ciphertext, passphrase, salt, nonce,
                                 time_cost=config.crypto.argon2_time_cost,
                                 memory_cost=config.crypto.argon2_memory_cost,
                                 parallelism=config.crypto.argon2_parallelism)

        # Parse vault
        parsed = parse_payload(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # List entries
        keys = list_entries(vault_obj)

        click.echo(f"\nVault contains {len(keys)} entries:")
        for i, entry_key in enumerate(keys, 1):
            entry = vault_obj.get_entry(entry_key)
            username_part = f" ({entry.username})" if entry and entry.username else ""
            click.echo(f"  {i}. {entry_key}{username_part}")

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--key", "-k", required=True, help="Entry key to show")
def show(vault_image: str, passphrase: str, key: str) -> None:
    """
    Show entry details without revealing the password.

    \b
    Example:
        stegvault vault show vault.png -k gmail
    """
    try:
        from stegvault.vault import get_entry, parse_payload as vault_parse

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config
            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload = extract_payload(vault_image, 0)
        salt, nonce, ciphertext = parse_payload(payload)

        decrypted = decrypt_data(ciphertext, passphrase, salt, nonce,
                                 time_cost=config.crypto.argon2_time_cost,
                                 memory_cost=config.crypto.argon2_memory_cost,
                                 parallelism=config.crypto.argon2_parallelism)

        # Parse vault
        parsed = vault_parse(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Get entry
        entry = get_entry(vault_obj, key)
        if not entry:
            click.echo(f"Error: Entry '{key}' not found", err=True)
            sys.exit(1)

        click.echo(f"\nEntry: {key}")
        if entry.username:
            click.echo(f"Username: {entry.username}")
        if entry.url:
            click.echo(f"URL: {entry.url}")
        click.echo(f"Password: {'*' * 12} (hidden)")
        if entry.notes:
            click.echo(f"Notes: {entry.notes}")
        if entry.tags:
            click.echo(f"Tags: {', '.join(entry.tags)}")
        click.echo(f"\nCreated: {entry.created}")
        click.echo(f"Modified: {entry.modified}")
        if entry.accessed:
            click.echo(f"Last accessed: {entry.accessed}")

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--output", "-o", required=True, type=click.Path(), help="Output path for updated vault")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--key", "-k", required=True, help="Entry key to update")
@click.option("--password", "-p", help="New password")
@click.option("--username", "-u", help="New username")
@click.option("--url", help="New URL")
@click.option("--notes", "-n", help="New notes")
def update(vault_image: str, output: str, passphrase: str, key: str, password: Optional[str], username: Optional[str], url: Optional[str], notes: Optional[str]) -> None:
    """
    Update an existing entry in the vault.

    \b
    Example:
        stegvault vault update vault.png -o vault_updated.png -k gmail --password newpass123
    """
    try:
        from stegvault.vault import update_entry as vault_update, vault_to_json, parse_payload as vault_parse
        from PIL import Image

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config
            config = get_default_config()

        # Check if at least one field is being updated
        if not any([password, username, url, notes]):
            click.echo("Error: At least one field must be specified for update", err=True)
            sys.exit(1)

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload_data = extract_payload(vault_image, 0)
        salt, nonce, ciphertext = parse_payload(payload_data)

        decrypted = decrypt_data(ciphertext, passphrase, salt, nonce,
                                 time_cost=config.crypto.argon2_time_cost,
                                 memory_cost=config.crypto.argon2_memory_cost,
                                 parallelism=config.crypto.argon2_parallelism)

        # Parse vault
        parsed = vault_parse(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Build update dict
        updates = {}
        if password:
            updates["password"] = password
        if username:
            updates["username"] = username
        if url:
            updates["url"] = url
        if notes:
            updates["notes"] = notes

        # Update entry
        click.echo(f"Updating entry '{key}'...")
        success = vault_update(vault_obj, key, **updates)
        if not success:
            click.echo(f"Error: Entry '{key}' not found", err=True)
            sys.exit(1)

        # Re-encrypt and embed
        vault_json = vault_to_json(vault_obj)
        vault_bytes = vault_json.encode("utf-8")

        # Check capacity
        img = Image.open(vault_image)
        capacity = calculate_capacity(img)
        img.close()

        if not validate_payload_capacity(capacity, len(vault_bytes)):
            click.echo(f"Error: Vault too large for image", err=True)
            sys.exit(1)

        click.echo("Re-encrypting vault...")
        ciphertext_new, salt_new, nonce_new = encrypt_data(
            vault_bytes, passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

        payload_new = serialize_payload(salt_new, nonce_new, ciphertext_new)
        seed_new = int.from_bytes(salt_new[:4], byteorder="big")

        click.echo("Embedding updated vault...")
        embed_payload(vault_image, payload_new, seed_new, output)

        click.echo(f"[OK] Entry updated successfully: {output}")

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--output", "-o", required=True, type=click.Path(), help="Output path for updated vault")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--key", "-k", required=True, help="Entry key to delete")
@click.option("--confirm/--no-confirm", default=True, help="Confirm before deleting")
def delete(vault_image: str, output: str, passphrase: str, key: str, confirm: bool) -> None:
    """
    Delete an entry from the vault.

    \b
    Example:
        stegvault vault delete vault.png -o vault_updated.png -k oldservice
    """
    try:
        from stegvault.vault import delete_entry as vault_delete, vault_to_json, parse_payload as vault_parse
        from PIL import Image

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config
            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload_data = extract_payload(vault_image, 0)
        salt, nonce, ciphertext = parse_payload(payload_data)

        decrypted = decrypt_data(ciphertext, passphrase, salt, nonce,
                                 time_cost=config.crypto.argon2_time_cost,
                                 memory_cost=config.crypto.argon2_memory_cost,
                                 parallelism=config.crypto.argon2_parallelism)

        # Parse vault
        parsed = vault_parse(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Check if entry exists
        if not vault_obj.has_entry(key):
            click.echo(f"Error: Entry '{key}' not found", err=True)
            sys.exit(1)

        # Confirm deletion
        if confirm:
            if not click.confirm(f"Delete entry '{key}'?"):
                click.echo("Deletion cancelled")
                sys.exit(0)

        # Delete entry
        click.echo(f"Deleting entry '{key}'...")
        vault_delete(vault_obj, key)

        # Re-encrypt and embed
        vault_json = vault_to_json(vault_obj)
        vault_bytes = vault_json.encode("utf-8")

        click.echo("Re-encrypting vault...")
        ciphertext_new, salt_new, nonce_new = encrypt_data(
            vault_bytes, passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

        payload_new = serialize_payload(salt_new, nonce_new, ciphertext_new)
        seed_new = int.from_bytes(salt_new[:4], byteorder="big")

        click.echo("Embedding updated vault...")
        embed_payload(vault_image, payload_new, seed_new, output)

        click.echo(f"[OK] Entry deleted successfully: {output}")
        click.echo(f"     Remaining entries: {len(vault_obj.entries)}")

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--output", "-o", required=True, type=click.Path(), help="Output JSON file")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--decrypt/--no-decrypt", default=False, help="Export as plaintext JSON (WARNING: insecure)")
@click.option("--pretty/--no-pretty", default=True, help="Pretty-print JSON")
def export(vault_image: str, output: str, passphrase: str, decrypt: bool, pretty: bool) -> None:
    """
    Export vault to JSON file.

    By default, exports the vault structure without decrypting passwords.
    Use --decrypt to export plaintext (WARNING: insecure!).

    \b
    Example:
        stegvault vault export vault.png -o backup.json --pretty
    """
    try:
        from stegvault.vault import vault_to_json, parse_payload as vault_parse
        import json as json_module

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config
            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload_data = extract_payload(vault_image, 0)
        salt, nonce, ciphertext = parse_payload(payload_data)

        decrypted = decrypt_data(ciphertext, passphrase, salt, nonce,
                                 time_cost=config.crypto.argon2_time_cost,
                                 memory_cost=config.crypto.argon2_memory_cost,
                                 parallelism=config.crypto.argon2_parallelism)

        # Parse vault
        parsed = vault_parse(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Export
        if decrypt:
            click.echo("\nWARNING: Exporting vault with plaintext passwords!", err=True)
            click.echo("This file will contain unencrypted credentials!", err=True)
            if not click.confirm("Continue?"):
                click.echo("Export cancelled")
                sys.exit(0)

            vault_json = vault_to_json(vault_obj, pretty=pretty)
        else:
            # Export without passwords (mask them)
            vault_dict = vault_obj.to_dict()
            for entry in vault_dict["entries"]:
                entry["password"] = "***REDACTED***"

            if pretty:
                vault_json = json_module.dumps(vault_dict, indent=2, ensure_ascii=False)
            else:
                vault_json = json_module.dumps(vault_dict, ensure_ascii=False)

        # Write to file
        with open(output, 'w', encoding='utf-8') as f:
            f.write(vault_json)

        click.echo(f"\n[OK] Vault exported: {output}")
        click.echo(f"     Entries: {len(vault_obj.entries)}")
        if decrypt:
            click.echo(f"     Mode: PLAINTEXT (passwords visible)")
        else:
            click.echo(f"     Mode: REDACTED (passwords masked)")

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
