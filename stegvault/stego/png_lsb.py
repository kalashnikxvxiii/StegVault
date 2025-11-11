"""
PNG LSB Steganography for StegVault.

Embeds and extracts encrypted payloads in PNG images using Least Significant Bit
modification with pseudo-random pixel ordering for detection resistance.
"""

import random
from typing import Tuple, Optional
from PIL import Image
import numpy as np


class StegoError(Exception):
    """Base exception for steganography errors."""

    pass


class CapacityError(StegoError):
    """Raised when image capacity is insufficient for payload."""

    pass


class ExtractionError(StegoError):
    """Raised when payload extraction fails."""

    pass


def calculate_capacity(image: Image.Image) -> int:
    """
    Calculate maximum payload capacity of an image in bytes.

    Uses LSB of each RGB channel, so capacity = (width * height * 3) / 8

    Args:
        image: PIL Image object

    Returns:
        Maximum payload size in bytes
    """
    if image.mode not in ("RGB", "RGBA"):
        raise StegoError(f"Unsupported image mode: {image.mode}. Use RGB or RGBA.")

    width, height = image.size
    # 3 bits per pixel (R, G, B), divide by 8 to get bytes
    return (width * height * 3) // 8


def _generate_pixel_sequence(width: int, height: int, seed: int) -> list:
    """
    Generate pseudo-random sequence of pixel coordinates.

    Args:
        width: Image width
        height: Image height
        seed: Random seed (derived from salt for reproducibility)

    Returns:
        List of (x, y) tuples in pseudo-random order
    """
    # Create all pixel coordinates
    pixels = [(x, y) for y in range(height) for x in range(width)]

    # Shuffle deterministically based on seed (using seed derived from cryptographic salt)
    # nosec B311: random.Random() is used here for deterministic pixel ordering,
    # not for cryptographic purposes. The seed itself is derived from crypto-grade randomness.
    rng = random.Random(seed)  # nosec B311
    rng.shuffle(pixels)

    return pixels


def _bytes_to_bits(data: bytes) -> list:
    """
    Convert bytes to list of bits.

    Args:
        data: Binary data

    Returns:
        List of bits (0 or 1)
    """
    bits = []
    for byte in data:
        for i in range(7, -1, -1):  # MSB first
            bits.append((byte >> i) & 1)
    return bits


def _bits_to_bytes(bits: list) -> bytes:
    """
    Convert list of bits to bytes.

    Args:
        bits: List of bits (0 or 1)

    Returns:
        Binary data
    """
    # Pad to multiple of 8
    while len(bits) % 8 != 0:
        bits.append(0)

    bytes_list = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        bytes_list.append(byte)

    return bytes(bytes_list)


def embed_payload(
    image_path: str, payload: bytes, seed: int, output_path: Optional[str] = None
) -> Image.Image:
    """
    Embed payload in PNG image using LSB steganography.

    Args:
        image_path: Path to cover image (PNG)
        payload: Binary payload to embed
        seed: Random seed for pixel ordering (derive from salt)
        output_path: Optional path to save stego image

    Returns:
        PIL Image object with embedded payload

    Raises:
        CapacityError: If image is too small for payload
        StegoError: If embedding fails
    """
    try:
        # Load image
        image = Image.open(image_path)

        # Convert to RGB if needed
        if image.mode == "RGBA":
            # Convert RGBA to RGB by compositing on white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = background  # type: ignore[assignment]
        elif image.mode != "RGB":
            raise StegoError(f"Unsupported image mode: {image.mode}")

        # Check capacity
        capacity = calculate_capacity(image)
        if len(payload) > capacity:
            raise CapacityError(
                f"Payload size ({len(payload)} bytes) exceeds image capacity ({capacity} bytes)"
            )

        # Convert image to numpy array for efficient manipulation
        pixels = np.array(image)
        height, width = pixels.shape[:2]

        # Generate pseudo-random pixel sequence
        pixel_sequence = _generate_pixel_sequence(width, height, seed)

        # Convert payload to bits
        payload_bits = _bytes_to_bits(payload)

        # Embed bits in LSB of pixel channels
        bit_index = 0
        for x, y in pixel_sequence:
            if bit_index >= len(payload_bits):
                break

            # Modify LSB of R, G, B channels
            for channel in range(3):  # R=0, G=1, B=2
                if bit_index >= len(payload_bits):
                    break

                # Clear LSB and set to payload bit
                pixels[y, x, channel] = (pixels[y, x, channel] & 0xFE) | payload_bits[bit_index]
                bit_index += 1

        # Convert back to PIL Image
        stego_image = Image.fromarray(pixels, mode="RGB")

        # Save if output path provided
        if output_path:
            stego_image.save(output_path, format="PNG")

        return stego_image

    except CapacityError:
        raise
    except Exception as e:
        raise StegoError(f"Embedding failed: {e}")


def extract_payload(image_path: str, payload_size: int, seed: int) -> bytes:
    """
    Extract payload from PNG image using LSB steganography.

    Args:
        image_path: Path to stego image
        payload_size: Size of payload in bytes
        seed: Random seed used during embedding (same as embed)

    Returns:
        Extracted binary payload

    Raises:
        ExtractionError: If extraction fails
        StegoError: If image format is invalid
    """
    try:
        # Load image
        image = Image.open(image_path)

        # Convert to RGB if needed
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background  # type: ignore[assignment]
        elif image.mode != "RGB":
            raise StegoError(f"Unsupported image mode: {image.mode}")

        # Check capacity
        capacity = calculate_capacity(image)
        if payload_size > capacity:
            raise ExtractionError(
                f"Requested payload size ({payload_size} bytes) exceeds image capacity ({capacity} bytes)"
            )

        # Convert image to numpy array
        pixels = np.array(image)
        height, width = pixels.shape[:2]

        # Generate same pseudo-random pixel sequence
        pixel_sequence = _generate_pixel_sequence(width, height, seed)

        # Extract bits from LSB of pixel channels
        extracted_bits: list[int] = []
        bits_needed = payload_size * 8

        for x, y in pixel_sequence:
            if len(extracted_bits) >= bits_needed:
                break

            # Extract LSB from R, G, B channels
            for channel in range(3):  # R=0, G=1, B=2
                if len(extracted_bits) >= bits_needed:
                    break

                bit = pixels[y, x, channel] & 1
                extracted_bits.append(bit)

        # Convert bits to bytes
        payload = _bits_to_bytes(extracted_bits[:bits_needed])

        return payload

    except ExtractionError:
        raise
    except Exception as e:
        raise StegoError(f"Extraction failed: {e}")


def embed_and_extract_roundtrip_test(image_path: str, payload: bytes, seed: int) -> bool:
    """
    Test embedding and extraction roundtrip (for testing purposes).

    Args:
        image_path: Path to test image
        payload: Test payload
        seed: Random seed

    Returns:
        True if roundtrip successful, False otherwise
    """
    try:
        import tempfile
        import os

        # Embed
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_path = tmp.name

        stego_image = embed_payload(image_path, payload, seed, temp_path)

        # Extract
        extracted = extract_payload(temp_path, len(payload), seed)

        # Cleanup
        os.unlink(temp_path)

        return extracted == payload

    except Exception:
        return False
