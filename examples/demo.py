#!/usr/bin/env python3
"""
StegVault Demo - Complete Backup and Restore Example

This script demonstrates the full workflow of StegVault:
1. Check image capacity
2. Create encrypted backup
3. Restore password from backup
"""

import sys
import os

# Add parent directory to path to import stegvault
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stegvault.crypto import encrypt_data, decrypt_data
from stegvault.stego import embed_payload, extract_payload, calculate_capacity
from stegvault.utils import serialize_payload, parse_payload
from PIL import Image


def demo_backup_restore():
    """Demonstrate complete backup and restore workflow."""
    print("=" * 70)
    print("              StegVault Demo - Backup & Restore")
    print("=" * 70)
    print()

    # Configuration
    cover_image = "cover_gradient.png"
    backup_image = "backup_demo.png"
    master_password = "MySecretPassword123!"
    passphrase = "StrongPassphrase2024!@#"

    # Step 1: Check image capacity
    print("[Step 1] Checking image capacity...")
    print("-" * 70)

    if not os.path.exists(cover_image):
        print(f"Error: Cover image '{cover_image}' not found.")
        print("Run 'python create_test_images.py' first to create test images.")
        return

    img = Image.open(cover_image)
    img.load()
    capacity = calculate_capacity(img)
    print(f"Cover Image: {cover_image}")
    print(f"Size: {img.width}x{img.height} pixels")
    print(f"Mode: {img.mode}")
    print(f"Capacity: {capacity} bytes ({capacity / 1024:.2f} KB)")
    print(f"Max Password Size: ~{capacity - 64} characters")
    img.close()
    print()

    # Step 2: Create encrypted backup
    print("[Step 2] Creating encrypted backup...")
    print("-" * 70)

    # Encrypt password
    # NOTE: This is a demo file. In production, NEVER log passwords in clear text.
    print(f"Password to hide: {'*' * len(master_password)} ({len(master_password)} chars)")
    print(f"Encryption passphrase: {'*' * len(passphrase)} ({len(passphrase)} chars)")
    print()

    password_bytes = master_password.encode("utf-8")
    print(f"Encrypting {len(password_bytes)} bytes...")

    ciphertext, salt, nonce = encrypt_data(password_bytes, passphrase)
    print(f"[OK] Encryption complete")
    print(f"  - Salt: {len(salt)} bytes")
    print(f"  - Nonce: {len(nonce)} bytes")
    print(f"  - Ciphertext: {len(ciphertext)} bytes")
    print()

    # Serialize payload
    payload = serialize_payload(salt, nonce, ciphertext)
    print(f"[OK] Payload serialized: {len(payload)} bytes total")
    print()

    # Derive seed from salt
    seed = int.from_bytes(salt[:4], byteorder="big")
    print(f"[OK] Seed derived from salt: {seed}")
    print()

    # Embed in image
    print(f"Embedding payload into {cover_image}...")
    stego_img = embed_payload(cover_image, payload, seed, backup_image)
    print(f"[OK] Backup created: {backup_image}")
    print(f"  File size: {os.path.getsize(backup_image)} bytes")
    print()

    # Step 3: Restore password from backup
    print("[Step 3] Restoring password from backup...")
    print("-" * 70)

    print(f"Reading backup image: {backup_image}")
    print()

    # Extract first 20 bytes (magic + salt) - these are stored sequentially
    print("Extracting payload header...")
    header_size = 20
    seed_placeholder = 0  # Doesn't matter for sequential header
    header_bytes = extract_payload(backup_image, header_size, seed_placeholder)

    # Validate magic header
    magic = header_bytes[:4]
    if magic != b"SPW1":
        print(f"[ERROR] Invalid magic header: {magic}")
        return

    print(f"[OK] Magic header validated: {magic}")

    # Extract salt
    extracted_salt = header_bytes[4:20]
    print(f"[OK] Salt extracted: {len(extracted_salt)} bytes")

    # Derive seed
    extracted_seed = int.from_bytes(extracted_salt[:4], byteorder="big")
    print(f"[OK] Seed derived: {extracted_seed}")
    print()

    # Extract full payload
    print("Extracting full payload...")
    full_payload = extract_payload(backup_image, len(payload), extracted_seed)
    print(f"[OK] Extracted {len(full_payload)} bytes")
    print()

    # Parse payload
    print("Parsing payload...")
    parsed_salt, parsed_nonce, parsed_ciphertext = parse_payload(full_payload)
    print(f"[OK] Parsed successfully")
    print(f"  - Salt: {len(parsed_salt)} bytes")
    print(f"  - Nonce: {len(parsed_nonce)} bytes")
    print(f"  - Ciphertext: {len(parsed_ciphertext)} bytes")
    print()

    # Decrypt
    print("Decrypting password...")
    recovered_bytes = decrypt_data(parsed_ciphertext, parsed_salt, parsed_nonce, passphrase)
    recovered_password = recovered_bytes.decode("utf-8")
    print(f"[OK] Decryption successful!")
    print()

    # Verify
    print("[Verification]")
    print("-" * 70)
    print(f"Original Password:  {master_password}")
    print(f"Recovered Password: {recovered_password}")
    print()

    if master_password == recovered_password:
        print("[SUCCESS] Password recovered correctly!")
    else:
        print("[FAILURE] Passwords do not match!")

    print()
    print("=" * 70)
    print("                       Demo Complete")
    print("=" * 70)
    print()
    print("Key takeaways:")
    print("  • Encryption happens BEFORE steganography")
    print("  • Salt and nonce are stored with the ciphertext")
    print("  • First 20 bytes (magic + salt) stored sequentially")
    print("  • Remaining payload uses pseudo-random pixel ordering")
    print("  • Both image AND passphrase required for recovery")
    print()


if __name__ == "__main__":
    try:
        demo_backup_restore()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
