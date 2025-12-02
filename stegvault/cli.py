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
    extract_full_payload,
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
def tui() -> None:
    """Launch the Terminal UI (TUI) interface."""
    try:
        from stegvault.tui import StegVaultTUI

        app = StegVaultTUI()
        app.run()
    except ImportError:
        click.echo(
            "Error: Textual library not installed. Install with: pip install textual",
            err=True,
        )
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error launching TUI: {e}", err=True)
        sys.exit(1)


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
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def check(image: str, json_output: bool) -> None:
    """
    Check image capacity for password storage.

    Displays how much data can be embedded in the given image.

    \b
    Example:
        stegvault check -i myimage.png
        stegvault check -i myimage.png --json
    """
    try:
        from PIL import Image
        from stegvault.utils.json_output import JSONOutput, check_success

        if not os.path.exists(image):
            if json_output:
                click.echo(
                    JSONOutput.error(f"Image file not found: {image}", error_type="file_not_found")
                )
            else:
                click.echo(f"Error: Image file not found: {image}", err=True)
            sys.exit(1)

        img = Image.open(image)

        if img.mode not in ("RGB", "RGBA"):
            if json_output:
                click.echo(
                    JSONOutput.error(
                        f"Unsupported image mode '{img.mode}'. Convert to RGB first.",
                        error_type="unsupported_mode",
                        mode=img.mode,
                    )
                )
            else:
                click.echo(f"\nWarning: Unsupported mode '{img.mode}'. Convert to RGB first.")
            img.close()
            sys.exit(1)

        capacity = calculate_capacity(img)
        max_password = capacity - 64  # Accounting for overhead

        if json_output:
            click.echo(
                check_success(
                    image_path=image,
                    image_format=img.format or "unknown",
                    mode=img.mode,
                    size=(img.width, img.height),
                    capacity=capacity,
                    max_password_size=max_password,
                )
            )
        else:
            click.echo(f"Image: {image}")
            click.echo(f"Format: {img.format}")
            click.echo(f"Mode: {img.mode}")
            click.echo(f"Size: {img.width}x{img.height} pixels")
            click.echo(f"\nCapacity: {capacity} bytes ({capacity / 1024:.2f} KB)")
            click.echo(f"Max password size: ~{max_password} bytes ({max_password} characters)")

            if capacity < 100:
                click.echo("\nWarning: Image is very small. Consider using a larger image.")
            elif capacity < 500:
                click.echo("\nNote: Image capacity is limited. Suitable for short passwords only.")
            else:
                click.echo("\n[OK] Image has sufficient capacity for password storage.")

        img.close()

    except Exception as e:
        if json_output:
            click.echo(JSONOutput.error(str(e), error_type="error"))
        else:
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
      import  - Import vault from JSON file
      totp    - Generate TOTP (2FA) code for an entry
      search  - Search vault entries by query
      filter  - Filter vault entries by tags or URL
    """
    pass


@vault.command()
@click.option("--image", "-i", required=True, type=click.Path(exists=True), help="Cover image")
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output path for vault image"
)
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Vault encryption passphrase",
)
@click.option("--key", "-k", required=True, help="Entry key (e.g., 'gmail', 'github')")
@click.option("--password", "-p", help="Password for this entry")
@click.option("--generate", "-g", is_flag=True, help="Generate a secure password")
@click.option("--username", "-u", help="Username or email")
@click.option("--url", help="Website URL")
@click.option("--notes", "-n", help="Additional notes")
@click.option("--totp-secret", help="TOTP secret (base32) for 2FA")
@click.option("--totp-generate", "--totp", is_flag=True, help="Generate a new TOTP secret for 2FA")
def create(
    image: str,
    output: str,
    passphrase: str,
    key: str,
    password: Optional[str],
    generate: bool,
    username: Optional[str],
    url: Optional[str],
    notes: Optional[str],
    totp_secret: Optional[str],
    totp_generate: bool,
) -> None:
    """
    Create a new vault with the first entry.

    \b
    Examples:
        stegvault vault create -i cover.png -o vault.png -k gmail -u user@gmail.com --generate
        stegvault vault create -i cover.png -o vault.png -k gmail --generate --totp-generate
    """
    try:
        from stegvault.vault import (
            create_vault,
            add_entry,
            vault_to_json,
            generate_password,
            generate_totp_secret,
            get_totp_provisioning_uri,
            generate_qr_code_ascii,
        )
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

        # Handle TOTP
        final_totp_secret = None
        if totp_generate and totp_secret:
            click.echo("Error: Cannot use both --totp-generate and --totp-secret", err=True)
            sys.exit(1)

        if totp_generate:
            final_totp_secret = generate_totp_secret()
            click.echo(f"\n[TOTP Setup]")
            click.echo(f"Generated TOTP secret: {final_totp_secret}")
            click.echo("=" * 60)

            # Display QR code
            account_name = f"{key}@StegVault"
            if username:
                account_name = f"{username} ({key})"
            uri = get_totp_provisioning_uri(final_totp_secret, account_name)

            click.echo("\n📱 Option 1: Scan QR code with your authenticator app")
            click.echo("-" * 60)
            qr_code = generate_qr_code_ascii(uri)
            click.echo(qr_code)

            click.echo("\n🔑 Option 2: Manual entry (if QR scan fails)")
            click.echo("-" * 60)
            click.echo(f"Account: {account_name}")
            click.echo(f"Secret:  {final_totp_secret}")
            click.echo(f"Type:    Time-based (TOTP)")
            click.echo(f"Digits:  6")
            click.echo(f"Period:  30 seconds")
            click.echo("=" * 60)
        elif totp_secret:
            final_totp_secret = totp_secret

        # Create vault and add first entry
        click.echo(f"\nCreating vault with entry '{key}'...")
        vault_obj = create_vault()
        add_entry(
            vault_obj,
            key=key,
            password=password,
            username=username,
            url=url,
            notes=notes,
            totp_secret=final_totp_secret,
        )

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
            click.echo(
                f"Error: Image too small. Need {len(vault_bytes) + 64} bytes, have {capacity} bytes",
                err=True,
            )
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

        with click.progressbar(
            length=100, label="Deriving encryption key", show_eta=False, show_percent=False
        ) as bar:
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
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output path for updated vault"
)
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--key", "-k", required=True, help="Entry key")
@click.option("--password", "-p", help="Password for this entry")
@click.option("--generate", "-g", is_flag=True, help="Generate a secure password")
@click.option("--username", "-u", help="Username or email")
@click.option("--url", help="Website URL")
@click.option("--notes", "-n", help="Additional notes")
@click.option("--totp-secret", help="TOTP secret (base32) for 2FA")
@click.option("--totp-generate", "--totp", is_flag=True, help="Generate a new TOTP secret for 2FA")
def add(
    vault_image: str,
    output: str,
    passphrase: str,
    key: str,
    password: Optional[str],
    generate: bool,
    username: Optional[str],
    url: Optional[str],
    notes: Optional[str],
    totp_secret: Optional[str],
    totp_generate: bool,
) -> None:
    """
    Add a new entry to an existing vault.

    \b
    Example:
        stegvault vault add vault.png -o vault_updated.png -k github --generate
    """
    try:
        from stegvault.vault import (
            add_entry as vault_add,
            vault_from_json,
            vault_to_json,
            generate_password,
            parse_payload as parse_vault_payload,
            generate_totp_secret,
            get_totp_provisioning_uri,
            generate_qr_code_ascii,
        )
        from stegvault.utils.payload import parse_payload as parse_binary_payload
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

        # Handle TOTP
        final_totp_secret = None
        if totp_generate and totp_secret:
            click.echo("Error: Cannot use both --totp-generate and --totp-secret", err=True)
            sys.exit(1)

        if totp_generate:
            final_totp_secret = generate_totp_secret()
            click.echo(f"\n[TOTP Setup]")
            click.echo(f"Generated TOTP secret: {final_totp_secret}")
            click.echo("=" * 60)

            # Display QR code
            account_name = f"{key}@StegVault"
            if username:
                account_name = f"{username} ({key})"
            uri = get_totp_provisioning_uri(final_totp_secret, account_name)

            click.echo("\n📱 Option 1: Scan QR code with your authenticator app")
            click.echo("-" * 60)
            qr_code = generate_qr_code_ascii(uri)
            click.echo(qr_code)

            click.echo("\n🔑 Option 2: Manual entry (if QR scan fails)")
            click.echo("-" * 60)
            click.echo(f"Account: {account_name}")
            click.echo(f"Secret:  {final_totp_secret}")
            click.echo(f"Type:    Time-based (TOTP)")
            click.echo(f"Digits:  6")
            click.echo(f"Period:  30 seconds")
            click.echo("=" * 60)
        elif totp_secret:
            final_totp_secret = totp_secret

        # Extract and decrypt existing vault
        click.echo("Extracting vault from image...")
        payload = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload)

        # Decrypt
        click.echo("Decrypting vault...")
        decrypted = decrypt_data(
            ciphertext,
            salt,
            nonce,
            passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

        # Parse vault
        parsed = parse_vault_payload(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            click.echo("Use 'stegvault restore' to retrieve it", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Add new entry
        click.echo(f"\nAdding entry '{key}' to vault...")
        vault_add(
            vault_obj,
            key=key,
            password=password,
            username=username,
            url=url,
            notes=notes,
            totp_secret=final_totp_secret,
        )

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
            vault_bytes,
            passphrase,
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
@click.option("--passphrase", default=None, help="Vault passphrase (or use --passphrase-file/env)")
@click.option("--passphrase-file", type=click.Path(exists=True), help="Read passphrase from file")
@click.option("--key", "-k", required=True, help="Entry key to retrieve")
@click.option(
    "--clipboard", "-c", is_flag=True, help="Copy password to clipboard instead of displaying"
)
@click.option(
    "--clipboard-timeout",
    type=int,
    default=0,
    help="Auto-clear clipboard after N seconds (0 = no auto-clear)",
)
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def get(
    vault_image: str,
    passphrase: Optional[str],
    passphrase_file: Optional[str],
    key: str,
    clipboard: bool,
    clipboard_timeout: int,
    json_output: bool,
) -> None:
    """
    Retrieve a password from the vault.

    By default, displays the password on screen. Use --clipboard to copy
    to clipboard instead (more secure).

    \b
    Examples:
        stegvault vault get vault.png -k gmail
        stegvault vault get vault.png -k gmail --clipboard
        stegvault vault get vault.png -k gmail --clipboard --clipboard-timeout 30
        stegvault vault get vault.png -k gmail --json
    """
    try:
        from stegvault.vault import get_entry, parse_payload as parse_vault_payload
        from stegvault.utils.payload import parse_payload as parse_binary_payload
        from stegvault.utils.json_output import JSONOutput, vault_get_success
        from stegvault.utils.passphrase import get_passphrase
        import pyperclip

        # Get passphrase from file/env/prompt
        actual_passphrase = get_passphrase(
            passphrase=passphrase,
            passphrase_file=passphrase_file,
            prompt_text="Vault passphrase",
            hide_input=True,
            confirmation_prompt=False,
        )

        # Validate clipboard_timeout
        if clipboard_timeout < 0:
            if json_output:
                click.echo(
                    JSONOutput.error("Clipboard timeout must be >= 0", error_type="validation")
                )
            else:
                click.echo("Error: Clipboard timeout must be >= 0", err=True)
            sys.exit(2)

        if clipboard_timeout > 0 and not clipboard:
            if not json_output:
                click.echo(
                    "Warning: --clipboard-timeout ignored without --clipboard flag", err=True
                )

        # JSON output incompatible with clipboard mode
        if json_output and clipboard:
            click.echo(
                JSONOutput.error("Cannot use --json with --clipboard", error_type="validation")
            )
            sys.exit(2)

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config

            config = get_default_config()

        # Extract and decrypt
        if not json_output:
            click.echo("Decrypting vault...")
        payload = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload)

        decrypted = decrypt_data(
            ciphertext,
            salt,
            nonce,
            actual_passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

        # Parse vault
        parsed = parse_vault_payload(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            if json_output:
                click.echo(
                    JSONOutput.error(
                        "This image contains a single password, not a vault",
                        error_type="wrong_format",
                    )
                )
            else:
                click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Get entry
        entry = get_entry(vault_obj, key)
        if not entry:
            if json_output:
                click.echo(
                    JSONOutput.error(
                        f"Entry '{key}' not found",
                        error_type="entry_not_found",
                        available_keys=vault_obj.list_keys(),
                    )
                )
            else:
                click.echo(f"Error: Entry '{key}' not found", err=True)
                click.echo(f"Available keys: {', '.join(vault_obj.list_keys())}", err=True)
            sys.exit(1)

        # Output
        if json_output:
            click.echo(
                vault_get_success(
                    key=key,
                    password=entry.password,
                    username=entry.username,
                    url=entry.url,
                    notes=entry.notes,
                    has_totp=bool(entry.totp_secret),
                )
            )
        elif clipboard:
            # Copy to clipboard instead of displaying
            try:
                pyperclip.copy(entry.password)
                click.echo(f"\nEntry: {key}")
                if entry.username:
                    click.echo(f"Username: {entry.username}")
                if entry.url:
                    click.echo(f"URL: {entry.url}")
                click.echo(f"Password: ********** (copied to clipboard)")
                click.echo("\n[OK] Password copied to clipboard")

                if clipboard_timeout > 0:
                    click.echo(f"     Clipboard will be cleared in {clipboard_timeout} seconds...")
                    time.sleep(clipboard_timeout)
                    pyperclip.copy("")  # Clear clipboard
                    click.echo(f"     Clipboard cleared")
                else:
                    click.echo("     Remember to clear clipboard manually when done")
            except Exception as e:
                click.echo(f"\nError: Failed to copy to clipboard: {e}", err=True)
                click.echo(f"Password: {entry.password}")  # Fallback to display
        else:
            # Display password on screen
            click.echo(f"\nEntry: {key}")
            if entry.username:
                click.echo(f"Username: {entry.username}")
            if entry.url:
                click.echo(f"URL: {entry.url}")
            click.echo(f"Password: {entry.password}")

        if not json_output and entry.notes:
            click.echo(f"Notes: {entry.notes}")

    except DecryptionError:
        if json_output:
            click.echo(
                JSONOutput.error("Wrong passphrase or corrupted data", error_type="decryption")
            )
        else:
            click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        if json_output:
            click.echo(JSONOutput.error(str(e), error_type="error"))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--passphrase", default=None, help="Vault passphrase (or use --passphrase-file/env)")
@click.option("--passphrase-file", type=click.Path(exists=True), help="Read passphrase from file")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def list(
    vault_image: str, passphrase: Optional[str], passphrase_file: Optional[str], json_output: bool
) -> None:
    """
    List all entry keys in the vault (without showing passwords).

    \b
    Example:
        stegvault vault list vault.png
        stegvault vault list vault.png --json
        stegvault vault list vault.png --passphrase-file ~/.vault_pass
    """
    try:
        from stegvault.vault import list_entries, parse_payload as parse_vault_payload
        from stegvault.utils.payload import parse_payload as parse_binary_payload
        from stegvault.utils.json_output import JSONOutput, vault_list_success
        from stegvault.utils.passphrase import get_passphrase

        # Get passphrase from file/env/prompt
        actual_passphrase = get_passphrase(
            passphrase=passphrase,
            passphrase_file=passphrase_file,
            prompt_text="Vault passphrase",
            hide_input=True,
            confirmation_prompt=False,
        )

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config

            config = get_default_config()

        # Extract and decrypt
        if not json_output:
            click.echo("Decrypting vault...")
        payload = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload)

        decrypted = decrypt_data(
            ciphertext,
            salt,
            nonce,
            actual_passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

        # Parse vault
        parsed = parse_vault_payload(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            if json_output:
                click.echo(
                    JSONOutput.error(
                        "This image contains a single password, not a vault",
                        error_type="wrong_format",
                    )
                )
            else:
                click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # List entries
        keys = list_entries(vault_obj)

        if json_output:
            entries = []
            for entry_key in keys:
                entry = vault_obj.get_entry(entry_key)
                entries.append(
                    {
                        "key": entry_key,
                        "username": entry.username if entry else None,
                        "url": entry.url if entry else None,
                        "has_totp": bool(entry.totp_secret) if entry else False,
                    }
                )
            click.echo(vault_list_success(entries=entries, entry_count=len(keys)))
        else:
            click.echo(f"\nVault contains {len(keys)} entries:")
            for i, entry_key in enumerate(keys, 1):
                entry = vault_obj.get_entry(entry_key)
                username_part = f" ({entry.username})" if entry and entry.username else ""
                click.echo(f"  {i}. {entry_key}{username_part}")

    except DecryptionError:
        if json_output:
            click.echo(
                JSONOutput.error("Wrong passphrase or corrupted data", error_type="decryption")
            )
        else:
            click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        if json_output:
            click.echo(JSONOutput.error(str(e), error_type="error"))
        else:
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
        from stegvault.utils.payload import parse_payload as parse_binary_payload

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config

            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload)

        decrypted = decrypt_data(
            ciphertext,
            salt,
            nonce,
            passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

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
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output path for updated vault"
)
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--key", "-k", required=True, help="Entry key to update")
@click.option("--password", "-p", help="New password")
@click.option("--username", "-u", help="New username")
@click.option("--url", help="New URL")
@click.option("--notes", "-n", help="New notes")
@click.option("--totp-secret", help="New TOTP secret (base32) for 2FA")
@click.option("--totp-generate", "--totp", is_flag=True, help="Generate a new TOTP secret for 2FA")
@click.option("--totp-remove", is_flag=True, help="Remove TOTP from entry")
def update(
    vault_image: str,
    output: str,
    passphrase: str,
    key: str,
    password: Optional[str],
    username: Optional[str],
    url: Optional[str],
    notes: Optional[str],
    totp_secret: Optional[str],
    totp_generate: bool,
    totp_remove: bool,
) -> None:
    """
    Update an existing entry in the vault.

    \b
    Example:
        stegvault vault update vault.png -o vault_updated.png -k gmail --password newpass123
    """
    try:
        from stegvault.vault import (
            update_entry as vault_update,
            vault_to_json,
            parse_payload as vault_parse,
            generate_totp_secret,
            get_totp_provisioning_uri,
            generate_qr_code_ascii,
        )
        from stegvault.utils.payload import parse_payload as parse_binary_payload
        from PIL import Image

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config

            config = get_default_config()

        # Handle TOTP flags validation
        totp_flags_count = sum([bool(totp_secret), totp_generate, totp_remove])
        if totp_flags_count > 1:
            click.echo(
                "Error: Only one of --totp-secret, --totp-generate, or --totp-remove can be used",
                err=True,
            )
            sys.exit(1)

        # Check if at least one field is being updated
        if not any([password, username, url, notes, totp_secret, totp_generate, totp_remove]):
            click.echo("Error: At least one field must be specified for update", err=True)
            sys.exit(1)

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload_data = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload_data)

        decrypted = decrypt_data(
            ciphertext,
            salt,
            nonce,
            passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

        # Parse vault
        parsed = vault_parse(decrypted.decode("utf-8"))
        if isinstance(parsed, str):
            click.echo("Error: This image contains a single password, not a vault", err=True)
            sys.exit(1)

        vault_obj = parsed

        # Handle TOTP updates
        final_totp_update = None
        totp_was_updated = False

        if totp_generate:
            final_totp_update = generate_totp_secret()
            click.echo(f"\nGenerated TOTP secret: {final_totp_update}")
            click.echo("Save this secret in your authenticator app!")

            # Get entry for account name
            from stegvault.vault import get_entry

            entry = get_entry(vault_obj, key)
            if entry:
                account_name = f"{key}@StegVault"
                if entry.username:
                    account_name = f"{entry.username} ({key})"
                uri = get_totp_provisioning_uri(final_totp_update, account_name)
                qr_code = generate_qr_code_ascii(uri)
                click.echo("\nScan this QR code with your authenticator app:\n")
                click.echo(qr_code)
            totp_was_updated = True
        elif totp_secret:
            final_totp_update = totp_secret
            totp_was_updated = True
        elif totp_remove:
            final_totp_update = None
            totp_was_updated = True

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
        if totp_was_updated:
            updates["totp_secret"] = final_totp_update

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
            vault_bytes,
            passphrase,
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
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output path for updated vault"
)
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
        from stegvault.vault import (
            delete_entry as vault_delete,
            vault_to_json,
            parse_payload as vault_parse,
        )
        from stegvault.utils.payload import parse_payload as parse_binary_payload
        from PIL import Image

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config

            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload_data = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload_data)

        decrypted = decrypt_data(
            ciphertext,
            salt,
            nonce,
            passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

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
            vault_bytes,
            passphrase,
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
@click.option(
    "--decrypt/--no-decrypt", default=False, help="Export as plaintext JSON (WARNING: insecure)"
)
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
        from stegvault.utils.payload import parse_payload as parse_binary_payload
        import json as json_module

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config

            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload_data = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload_data)

        decrypted = decrypt_data(
            ciphertext,
            salt,
            nonce,
            passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

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
                entry["password"] = "***REDACTED***"  # nosec B105 - intentional placeholder

            if pretty:
                vault_json = json_module.dumps(vault_dict, indent=2, ensure_ascii=False)
            else:
                vault_json = json_module.dumps(vault_dict, ensure_ascii=False)

        # Write to file
        with open(output, "w", encoding="utf-8") as f:
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


@vault.command(name="import")
@click.argument("json_file", type=click.Path(exists=True))
@click.option("--image", "-i", required=True, type=click.Path(exists=True), help="Cover image")
@click.option(
    "--output", "-o", required=True, type=click.Path(), help="Output path for vault image"
)
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Vault encryption passphrase",
)
@click.option(
    "--check-strength/--no-check-strength", default=True, help="Verify passphrase strength"
)
def import_vault(
    json_file: str, image: str, output: str, passphrase: str, check_strength: bool
) -> None:
    """
    Import vault from JSON file and embed in image.

    Creates a new vault image from a JSON backup file. This is useful for:
    - Restoring from exported backups
    - Migrating vaults to new images
    - Creating vaults from external sources

    \b
    Example:
        stegvault vault import backup.json -i cover.png -o vault.png
    """
    try:
        from stegvault.vault import import_vault_from_file, vault_to_json

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config

            config = get_default_config()

        # Verify passphrase strength
        if check_strength:
            is_strong, message = verify_passphrase_strength(passphrase)
            if not is_strong:
                click.echo(f"Warning: {message}", err=True)
                if not click.confirm("Continue anyway?"):
                    click.echo("Import cancelled")
                    sys.exit(0)

        # Import vault from JSON
        click.echo(f"Loading vault from: {json_file}")
        vault_obj = import_vault_from_file(json_file)
        click.echo(f"[OK] Loaded vault with {len(vault_obj.entries)} entries")

        # Check if any entries have no passwords (could be redacted export)
        redacted_count = sum(
            1 for e in vault_obj.entries if e.password == "***REDACTED***"  # nosec B105
        )
        if redacted_count > 0:
            click.echo(f"\nWarning: {redacted_count} entries have redacted passwords!", err=True)
            click.echo("These entries were likely exported with --no-decrypt flag.", err=True)
            click.echo(
                "The vault will be created, but these passwords will be '***REDACTED***'.", err=True
            )
            if not click.confirm("Continue?"):
                click.echo("Import cancelled")
                sys.exit(0)

        # Serialize vault to JSON
        vault_json = vault_to_json(vault_obj, pretty=False)
        vault_bytes = vault_json.encode("utf-8")

        # Check image capacity
        from PIL import Image

        img = Image.open(image)
        capacity = calculate_capacity(img)
        img.close()

        click.echo(f"Image capacity: {capacity} bytes")
        click.echo(f"Vault size: {len(vault_bytes)} bytes")

        if not validate_payload_capacity(capacity, len(vault_bytes)):
            click.echo(
                f"Error: Image too small for vault. Need at least "
                f"{len(vault_bytes) + 64} bytes, have {capacity} bytes",
                err=True,
            )
            sys.exit(1)

        # Encrypt vault
        click.echo("Encrypting vault...", nl=False)
        click.echo(" (this may take a few seconds)", err=True)

        # Show progress for key derivation
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

        with click.progressbar(
            length=100,
            label="Deriving encryption key",
            show_eta=False,
            show_percent=False,
            bar_template="%(label)s [%(bar)s] %(info)s",
        ) as bar:
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

        # Serialize payload
        payload = serialize_payload(salt, nonce, ciphertext)
        click.echo(f"Payload size: {len(payload)} bytes")

        # Derive seed from salt for reproducible pixel ordering
        seed = int.from_bytes(salt[:4], byteorder="big")

        # Embed in image
        click.echo("Embedding vault in image...")
        embed_payload(image, payload, seed, output)
        click.echo("[OK] Embedding complete")

        click.echo(f"\n[OK] Vault imported successfully: {output}")
        click.echo(f"     Entries: {len(vault_obj.entries)}")
        click.echo("\nIMPORTANT:")
        click.echo("- Keep both the image AND passphrase safe")
        click.echo("- Losing either means permanent data loss")
        click.echo("- Create multiple backup copies")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: Invalid JSON file - {e}", err=True)
        sys.exit(1)
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
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option("--key", "-k", required=True, help="Entry key")
@click.option("--qr", is_flag=True, help="Display QR code for authenticator app setup")
def totp(vault_image: str, passphrase: str, key: str, qr: bool) -> None:
    """
    Generate TOTP (2FA) code for an entry.

    Displays the current 6-digit time-based one-time password code.
    Use --qr to display QR code for setting up in authenticator apps.

    \b
    Examples:
        stegvault vault totp vault.png -k gmail
        stegvault vault totp vault.png -k gmail --qr
    """
    try:
        from stegvault.vault import (
            get_entry,
            parse_payload as parse_vault_payload,
            generate_totp_code,
            get_totp_time_remaining,
            get_totp_provisioning_uri,
            generate_qr_code_ascii,
        )
        from stegvault.utils.payload import parse_payload as parse_binary_payload

        # Load configuration
        try:
            config = load_config()
        except ConfigError:
            from stegvault.config import get_default_config

            config = get_default_config()

        # Extract and decrypt
        click.echo("Decrypting vault...")
        payload = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload)

        decrypted = decrypt_data(
            ciphertext,
            salt,
            nonce,
            passphrase,
            time_cost=config.crypto.argon2_time_cost,
            memory_cost=config.crypto.argon2_memory_cost,
            parallelism=config.crypto.argon2_parallelism,
        )

        # Parse vault
        parsed = parse_vault_payload(decrypted.decode("utf-8"))
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

        # Check if TOTP is configured
        if not entry.totp_secret:
            click.echo(f"Error: Entry '{key}' does not have TOTP configured", err=True)
            click.echo("Use 'vault update' with --totp-generate to add TOTP", err=True)
            sys.exit(1)

        # Generate TOTP code
        try:
            code = generate_totp_code(entry.totp_secret)
            time_remaining = get_totp_time_remaining()

            click.echo(f"\nEntry: {key}")
            click.echo(f"TOTP Code: {code}")
            click.echo(f"Valid for: {time_remaining} seconds")

            if qr:
                # Display QR code
                click.echo("\nScan this QR code with your authenticator app:")
                click.echo("(Google Authenticator, Authy, Microsoft Authenticator, etc.)\n")

                # Generate provisioning URI
                account_name = f"{key}@StegVault"
                if entry.username:
                    account_name = f"{entry.username} ({key})"

                uri = get_totp_provisioning_uri(entry.totp_secret, account_name)
                qr_code = generate_qr_code_ascii(uri)
                click.echo(qr_code)
                click.echo(f"\nSecret (manual entry): {entry.totp_secret}")

        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    confirmation_prompt=False,
    help="Passphrase to decrypt the vault",
)
@click.option(
    "--query",
    "-q",
    required=True,
    help="Search query string",
)
@click.option(
    "--case-sensitive",
    "-c",
    is_flag=True,
    help="Perform case-sensitive search",
)
@click.option(
    "--fields",
    "-f",
    multiple=True,
    type=click.Choice(["key", "username", "url", "notes"]),
    help="Fields to search in (can be specified multiple times)",
)
def search(
    vault_image: str, passphrase: str, query: str, case_sensitive: bool, fields: tuple
) -> None:
    """
    Search vault entries by query string.

    Searches across key, username, URL, and notes fields by default.
    Use --fields to search specific fields only.

    Example:
        stegvault vault search vault.png --query gmail
        stegvault vault search vault.png -q github --fields key --fields username
    """
    from stegvault.vault import search_entries, parse_payload as parse_vault_payload
    from stegvault.utils.payload import parse_payload as parse_binary_payload

    try:
        # Extract and decrypt vault
        payload_bytes = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload_bytes)
        decrypted_data = decrypt_data(ciphertext, salt, nonce, passphrase)
        vault_obj = parse_vault_payload(decrypted_data.decode("utf-8"))

        if isinstance(vault_obj, str):
            click.echo("Error: This is a single-password backup, not a vault", err=True)
            sys.exit(1)

        # Perform search
        search_fields = list(fields) if fields else None
        results = search_entries(
            vault_obj, query, case_sensitive=case_sensitive, fields=search_fields
        )

        if not results:
            click.echo(f"No entries found matching '{query}'")
            return

        click.echo(f"\nFound {len(results)} matching entries:")
        click.echo("=" * 60)

        for entry in results:
            click.echo(f"\nKey: {entry.key}")
            if entry.username:
                click.echo(f"Username: {entry.username}")
            if entry.url:
                click.echo(f"URL: {entry.url}")
            if entry.tags:
                click.echo(f"Tags: {', '.join(entry.tags)}")
            if entry.notes:
                # Truncate long notes
                notes_preview = entry.notes[:100] + "..." if len(entry.notes) > 100 else entry.notes
                click.echo(f"Notes: {notes_preview}")
            click.echo(f"Has TOTP: {'Yes' if entry.totp_secret else 'No'}")

        click.echo("\n" + "=" * 60)
        click.echo(f"Total: {len(results)} entries")

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@vault.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    confirmation_prompt=False,
    help="Passphrase to decrypt the vault",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    help="Tag to filter by (can be specified multiple times)",
)
@click.option(
    "--match-all",
    is_flag=True,
    help="Entry must have ALL tags (default: ANY tag)",
)
@click.option(
    "--url",
    "-u",
    help="URL pattern to filter by",
)
@click.option(
    "--exact-url",
    is_flag=True,
    help="Require exact URL match (default: substring)",
)
def filter(
    vault_image: str, passphrase: str, tag: tuple, match_all: bool, url: str, exact_url: bool
) -> None:
    """
    Filter vault entries by tags or URL.

    Filter by tags, URL patterns, or both.

    Examples:
        stegvault vault filter vault.png --tag work
        stegvault vault filter vault.png --tag work --tag email --match-all
        stegvault vault filter vault.png --url github.com
        stegvault vault filter vault.png --tag work --url corp.com
    """
    from stegvault.vault import filter_by_tags, filter_by_url, parse_payload as parse_vault_payload
    from stegvault.utils.payload import parse_payload as parse_binary_payload

    if not tag and not url:
        click.echo("Error: Must specify at least one filter (--tag or --url)", err=True)
        sys.exit(1)

    try:
        # Extract and decrypt vault
        payload_bytes = extract_full_payload(vault_image)
        salt, nonce, ciphertext = parse_binary_payload(payload_bytes)
        decrypted_data = decrypt_data(ciphertext, salt, nonce, passphrase)
        vault_obj = parse_vault_payload(decrypted_data.decode("utf-8"))

        if isinstance(vault_obj, str):
            click.echo("Error: This is a single-password backup, not a vault", err=True)
            sys.exit(1)

        # Apply filters
        results_list = []

        if tag and url:
            # Both filters: intersection
            tag_results = filter_by_tags(vault_obj, list(tag), match_all=match_all)
            url_results = filter_by_url(vault_obj, url, exact=exact_url)
            # Find intersection by key
            tag_keys = {e.key for e in tag_results}
            url_keys = {e.key for e in url_results}
            intersection_keys = tag_keys.intersection(url_keys)
            results_list = [e for e in tag_results if e.key in intersection_keys]
        elif tag:
            # Only tag filter
            results_list = filter_by_tags(vault_obj, list(tag), match_all=match_all)
        elif url:
            # Only URL filter
            results_list = filter_by_url(vault_obj, url, exact=exact_url)

        results_list = sorted(results_list, key=lambda e: e.key)

        if not results_list:
            click.echo("No entries found matching the specified filters")
            return

        click.echo(f"\nFound {len(results_list)} matching entries:")
        click.echo("=" * 60)

        for entry in results_list:
            click.echo(f"\nKey: {entry.key}")
            if entry.username:
                click.echo(f"Username: {entry.username}")
            if entry.url:
                click.echo(f"URL: {entry.url}")
            if entry.tags:
                click.echo(f"Tags: {', '.join(entry.tags)}")
            if entry.notes:
                # Truncate long notes
                notes_preview = entry.notes[:100] + "..." if len(entry.notes) > 100 else entry.notes
                click.echo(f"Notes: {notes_preview}")
            click.echo(f"Has TOTP: {'Yes' if entry.totp_secret else 'No'}")

        click.echo("\n" + "=" * 60)
        click.echo(f"Total: {len(results_list)} entries")

    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group()
def gallery() -> None:
    """
    Manage multiple vaults in a gallery.

    Gallery provides centralized management of multiple vault images
    with metadata storage and cross-vault search capabilities.
    """
    pass


@gallery.command()
@click.option(
    "--db-path",
    "-d",
    type=click.Path(),
    help="Gallery database path (default: ~/.stegvault/gallery.db)",
)
def init(db_path: Optional[str]) -> None:
    """
    Initialize a new gallery database.

    Creates the SQLite database for storing vault metadata.

    \b
    Example:
        stegvault gallery init
        stegvault gallery init --db-path ./my-gallery.db
    """
    from stegvault.gallery import Gallery
    from pathlib import Path

    try:
        # Default path
        if not db_path:
            db_path = os.path.expanduser("~/.stegvault/gallery.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Check if already exists
        if os.path.exists(db_path):
            click.echo(f"Gallery database already exists: {db_path}")
            if not click.confirm("Overwrite?"):
                sys.exit(0)
            os.remove(db_path)

        # Initialize
        with Gallery(db_path) as g:
            click.echo(f"Gallery initialized: {db_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gallery.command()
@click.argument("vault_image", type=click.Path(exists=True))
@click.option("--name", "-n", required=True, help="Unique name for the vault")
@click.option("--description", "-d", help="Vault description")
@click.option("--tag", "-t", multiple=True, help="Tags (can be specified multiple times)")
@click.option(
    "--passphrase", prompt=True, hide_input=True, help="Vault passphrase to cache entries"
)
@click.option(
    "--db-path",
    type=click.Path(),
    help="Gallery database path (default: ~/.stegvault/gallery.db)",
)
def add(
    vault_image: str,
    name: str,
    description: Optional[str],
    tag: tuple,
    passphrase: str,
    db_path: Optional[str],
) -> None:
    """
    Add a vault to the gallery.

    Adds a vault image to the gallery with metadata and caches
    its entries for fast cross-vault search.

    \b
    Example:
        stegvault gallery add vault.png --name gmail-vault --tag personal
        stegvault gallery add work.png -n work-vault -t work -t important
    """
    from stegvault.gallery import Gallery
    from stegvault.gallery.operations import GalleryOperationError

    try:
        # Default path
        if not db_path:
            db_path = os.path.expanduser("~/.stegvault/gallery.db")

        if not os.path.exists(db_path):
            click.echo(
                "Error: Gallery not initialized. Run 'stegvault gallery init' first.", err=True
            )
            sys.exit(1)

        with Gallery(db_path) as g:
            click.echo(f"Adding vault '{name}'...")
            vault = g.add_vault(name, vault_image, description, list(tag) if tag else None)

            # Cache entries
            click.echo("Caching entries...")
            vault = g.refresh_vault(name, passphrase)

            click.echo(f"\nVault added successfully!")
            click.echo(f"Name: {vault.name}")
            click.echo(f"Path: {vault.image_path}")
            click.echo(f"Entries: {vault.entry_count}")
            if vault.tags:
                click.echo(f"Tags: {', '.join(vault.tags)}")

    except GalleryOperationError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gallery.command()
@click.option(
    "--db-path",
    type=click.Path(),
    help="Gallery database path (default: ~/.stegvault/gallery.db)",
)
@click.option("--tag", "-t", help="Filter by tag")
def list(db_path: Optional[str], tag: Optional[str]) -> None:
    """
    List all vaults in the gallery.

    \b
    Example:
        stegvault gallery list
        stegvault gallery list --tag work
    """
    from stegvault.gallery import Gallery

    try:
        # Default path
        if not db_path:
            db_path = os.path.expanduser("~/.stegvault/gallery.db")

        if not os.path.exists(db_path):
            click.echo(
                "Error: Gallery not initialized. Run 'stegvault gallery init' first.", err=True
            )
            sys.exit(1)

        with Gallery(db_path) as g:
            vaults = g.list_vaults(tag)

            if not vaults:
                click.echo("No vaults in gallery")
                return

            click.echo(f"\n{len(vaults)} vault(s) in gallery:")
            click.echo("=" * 80)

            for vault in vaults:
                click.echo(f"\nName: {vault.name}")
                click.echo(f"Path: {vault.image_path}")
                click.echo(f"Entries: {vault.entry_count}")
                if vault.description:
                    click.echo(f"Description: {vault.description}")
                if vault.tags:
                    click.echo(f"Tags: {', '.join(vault.tags)}")
                if vault.last_accessed:
                    click.echo(
                        f"Last accessed: {vault.last_accessed.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

            click.echo("\n" + "=" * 80)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gallery.command()
@click.argument("name")
@click.option(
    "--db-path",
    type=click.Path(),
    help="Gallery database path (default: ~/.stegvault/gallery.db)",
)
def remove(name: str, db_path: Optional[str]) -> None:
    """
    Remove a vault from the gallery.

    This removes the vault from gallery metadata but does NOT delete
    the actual vault image file.

    \b
    Example:
        stegvault gallery remove gmail-vault
    """
    from stegvault.gallery import Gallery

    try:
        # Default path
        if not db_path:
            db_path = os.path.expanduser("~/.stegvault/gallery.db")

        if not os.path.exists(db_path):
            click.echo(
                "Error: Gallery not initialized. Run 'stegvault gallery init' first.", err=True
            )
            sys.exit(1)

        with Gallery(db_path) as g:
            if not click.confirm(f"Remove vault '{name}' from gallery?"):
                click.echo("Cancelled")
                sys.exit(0)

            if g.remove_vault(name):
                click.echo(f"Vault '{name}' removed from gallery")
            else:
                click.echo(f"Vault '{name}' not found", err=True)
                sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gallery.command()
@click.argument("name")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase")
@click.option(
    "--db-path",
    type=click.Path(),
    help="Gallery database path (default: ~/.stegvault/gallery.db)",
)
def refresh(name: str, passphrase: str, db_path: Optional[str]) -> None:
    """
    Refresh vault metadata by re-reading the vault image.

    Updates cached entry metadata for cross-vault search.

    \b
    Example:
        stegvault gallery refresh gmail-vault
    """
    from stegvault.gallery import Gallery
    from stegvault.gallery.operations import GalleryOperationError

    try:
        # Default path
        if not db_path:
            db_path = os.path.expanduser("~/.stegvault/gallery.db")

        if not os.path.exists(db_path):
            click.echo(
                "Error: Gallery not initialized. Run 'stegvault gallery init' first.", err=True
            )
            sys.exit(1)

        with Gallery(db_path) as g:
            click.echo(f"Refreshing vault '{name}'...")
            vault = g.refresh_vault(name, passphrase)

            click.echo(f"\nVault refreshed successfully!")
            click.echo(f"Entries: {vault.entry_count}")

    except GalleryOperationError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except DecryptionError:
        click.echo("Error: Wrong passphrase", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gallery.command()
@click.argument("query")
@click.option("--vault", "-v", help="Search only in specific vault")
@click.option(
    "--fields",
    "-f",
    multiple=True,
    type=click.Choice(["key", "username", "url"], case_sensitive=False),
    help="Fields to search (default: all)",
)
@click.option(
    "--db-path",
    type=click.Path(),
    help="Gallery database path (default: ~/.stegvault/gallery.db)",
)
def search(
    query: str,
    vault: Optional[str],
    fields: tuple,
    db_path: Optional[str],
) -> None:
    """
    Search for entries across all vaults in the gallery.

    Searches cached entry metadata for fast cross-vault search.
    To update cache, use 'stegvault gallery refresh'.

    \b
    Example:
        stegvault gallery search github
        stegvault gallery search work --vault gmail-vault
        stegvault gallery search user@example.com --fields username
    """
    from stegvault.gallery import Gallery

    try:
        # Default path
        if not db_path:
            db_path = os.path.expanduser("~/.stegvault/gallery.db")

        if not os.path.exists(db_path):
            click.echo(
                "Error: Gallery not initialized. Run 'stegvault gallery init' first.", err=True
            )
            sys.exit(1)

        # Map field names
        field_map = {"key": "entry_key", "username": "username", "url": "url"}
        search_fields = [field_map[f] for f in fields] if fields else None

        with Gallery(db_path) as g:
            results = g.search(query, vault, search_fields)

            if not results:
                click.echo("No entries found")
                return

            click.echo(f"\nFound {len(results)} matching entries:")
            click.echo("=" * 80)

            current_vault = None
            for result in results:
                if result["vault_name"] != current_vault:
                    if current_vault is not None:
                        click.echo("")
                    click.echo(f"\n[{result['vault_name']}]")
                    current_vault = result["vault_name"]

                click.echo(f"\nKey: {result['entry_key']}")
                if result["username"]:
                    click.echo(f"Username: {result['username']}")
                if result["url"]:
                    click.echo(f"URL: {result['url']}")
                if result["tags"]:
                    click.echo(f"Tags: {', '.join(result['tags'])}")
                if result["has_totp"]:
                    click.echo("Has TOTP: Yes")

            click.echo("\n" + "=" * 80)
            click.echo(f"Total: {len(results)} entries")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
