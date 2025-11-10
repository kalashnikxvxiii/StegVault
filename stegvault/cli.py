"""
Command-line interface for StegVault.

Provides commands for backup creation and password recovery.
"""

import click
import sys
import os
from pathlib import Path

from stegvault.crypto import encrypt_data, decrypt_data, verify_passphrase_strength, CryptoError, DecryptionError
from stegvault.stego import embed_payload, extract_payload, calculate_capacity, StegoError, CapacityError
from stegvault.utils import serialize_payload, parse_payload, validate_payload_capacity, PayloadFormatError


@click.group()
@click.version_option(version="0.1.0")
def main():
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
    help="Master password to encrypt and embed"
)
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Encryption passphrase (keep this secret!)"
)
@click.option(
    "--image",
    "-i",
    required=True,
    type=click.Path(exists=True),
    help="Cover image (PNG format recommended)"
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(),
    help="Output path for stego image"
)
@click.option(
    "--check-strength/--no-check-strength",
    default=True,
    help="Verify passphrase strength"
)
def backup(password, passphrase, image, output, check_strength):
    """
    Create a backup by embedding encrypted password in an image.

    The password is encrypted using XChaCha20-Poly1305 with Argon2id key
    derivation, then embedded in the image using LSB steganography.

    \b
    Example:
        stegvault backup -i cover.png -o backup.png
    """
    try:
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
        password_bytes = password.encode('utf-8')

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
                err=True
            )
            sys.exit(1)

        # Encrypt password
        click.echo("Encrypting password...")
        ciphertext, salt, nonce = encrypt_data(password_bytes, passphrase)

        # Serialize payload
        payload = serialize_payload(salt, nonce, ciphertext)
        click.echo(f"Payload size: {len(payload)} bytes")

        # Derive seed from salt for reproducible pixel ordering
        seed = int.from_bytes(salt[:4], byteorder='big')

        # Embed in image
        click.echo("Embedding payload in image...")
        embed_payload(image, payload, seed, output)

        click.echo(f"✓ Backup created successfully: {output}")
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
    help="Stego image containing encrypted backup"
)
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    help="Encryption passphrase used during backup"
)
@click.option(
    "--output",
    "-o",
    type=click.File('w'),
    default="-",
    help="Output file for recovered password (default: stdout)"
)
def restore(image, passphrase, output):
    """
    Restore password from a stego image backup.

    Extracts and decrypts the password embedded in the image.

    \b
    Example:
        stegvault restore -i backup.png
        stegvault restore -i backup.png -o password.txt
    """
    try:
        click.echo("Restoring password from backup...", err=True)

        # Check if image exists
        if not os.path.exists(image):
            click.echo(f"Error: Image file not found: {image}", err=True)
            sys.exit(1)

        # First, we need to extract the payload header to determine size
        # We'll extract a generous amount first to get the header
        from PIL import Image
        img = Image.open(image)
        capacity = calculate_capacity(img)
        img.close()

        # Extract enough bytes to read the header
        # Header is: 4 (magic) + 16 (salt) + 24 (nonce) + 4 (length) = 48 bytes
        header_size = 48
        seed_temp = 0  # Temporary seed to extract header

        click.echo("Extracting payload header...", err=True)
        header_bytes = extract_payload(image, header_size, seed_temp)

        # Parse header to get ciphertext length
        try:
            # We can't fully parse yet, but we can extract the length field
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
        payload = extract_payload(image, total_payload_size, seed_temp)

        # Parse payload
        click.echo("Parsing payload...", err=True)
        salt, nonce, ciphertext = parse_payload(payload)

        # Derive correct seed from salt
        seed = int.from_bytes(salt[:4], byteorder='big')

        # Re-extract with correct seed
        click.echo("Re-extracting with correct seed...", err=True)
        payload = extract_payload(image, total_payload_size, seed)
        salt, nonce, ciphertext = parse_payload(payload)

        # Decrypt
        click.echo("Decrypting password...", err=True)
        password_bytes = decrypt_data(ciphertext, salt, nonce, passphrase)

        # Convert to string
        password = password_bytes.decode('utf-8')

        # Output
        if output.name == '<stdout>':
            click.echo("\n" + "="*50, err=True)
            click.echo("✓ Password recovered successfully!", err=True)
            click.echo("="*50 + "\n", err=True)

        output.write(password)

        if output.name != '<stdout>':
            output.write('\n')
            click.echo(f"\n✓ Password saved to: {output.name}", err=True)

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
    "--image",
    "-i",
    required=True,
    type=click.Path(exists=True),
    help="Image file to check"
)
def check(image):
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
            click.echo("\n✓ Image has sufficient capacity for password storage.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
