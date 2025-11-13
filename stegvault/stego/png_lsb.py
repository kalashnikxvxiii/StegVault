"""
PNG LSB Steganography for StegVault.

Embeds and extracts encrypted payloads in PNG images using Least Significant Bit
modification with sequential pixel ordering for reliability and simplicity.

The payload begins with a "SPW1" magic header for validation.
Security is provided by strong cryptography (XChaCha20-Poly1305 + Argon2id),
not by pixel ordering.
"""

from typing import Optional, List
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
    image_path: str, payload: bytes, seed: int = 0, output_path: Optional[str] = None
) -> Image.Image:
    """
    Embed payload in PNG image using LSB steganography with sequential ordering.

    The payload is embedded left-to-right, top-to-bottom in the RGB channels.
    Security is provided by strong cryptography (XChaCha20-Poly1305 + Argon2id),
    not by pixel ordering.

    Args:
        image_path: Path to cover image (PNG)
        payload: Binary payload to embed (should start with "SPW1" magic header)
        seed: Deprecated parameter kept for backward compatibility (ignored)
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
        # Force load pixel data and close file descriptor (fixes Windows file locking)
        image.load()

        # Convert to RGB if needed
        if image.mode == "RGBA":
            # Convert RGBA to RGB by compositing on white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image.close()  # Close original RGBA image
            image = background  # type: ignore[assignment]
        elif image.mode != "RGB":
            image.close()
            raise StegoError(f"Unsupported image mode: {image.mode}")

        # Check capacity
        capacity = calculate_capacity(image)
        if len(payload) > capacity:
            image.close()
            raise CapacityError(
                f"Payload size ({len(payload)} bytes) exceeds image capacity ({capacity} bytes)"
            )

        # Convert image to numpy array for efficient manipulation
        pixels = np.array(image)
        height, width = pixels.shape[:2]

        # Close the original image now that we have the pixel data
        image.close()

        # Convert payload to bits
        payload_bits = _bytes_to_bits(payload)

        # Embed all bits sequentially (left-to-right, top-to-bottom)
        # This is simple, reliable, and avoids any pixel overlap issues
        bit_index = 0
        for y in range(height):
            for x in range(width):
                if bit_index >= len(payload_bits):
                    break

                for channel in range(3):  # R=0, G=1, B=2
                    if bit_index >= len(payload_bits):
                        break

                    # Clear LSB and set to payload bit
                    pixels[y, x, channel] = (pixels[y, x, channel] & 0xFE) | payload_bits[bit_index]
                    bit_index += 1

            if bit_index >= len(payload_bits):
                break

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


def extract_payload(image_path: str, payload_size: int, seed: int = 0) -> bytes:
    """
    Extract payload from PNG image using LSB steganography with sequential ordering.

    Args:
        image_path: Path to stego image
        payload_size: Size of payload in bytes
        seed: Deprecated parameter kept for backward compatibility (ignored)

    Returns:
        Extracted binary payload

    Raises:
        ExtractionError: If extraction fails
        StegoError: If image format is invalid
    """
    try:
        # Load image
        image = Image.open(image_path)
        # Force load pixel data and close file descriptor (fixes Windows file locking)
        image.load()

        # Convert to RGB if needed
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image.close()  # Close original RGBA image
            image = background  # type: ignore[assignment]
        elif image.mode != "RGB":
            image.close()
            raise StegoError(f"Unsupported image mode: {image.mode}")

        # Check capacity
        capacity = calculate_capacity(image)
        if payload_size > capacity:
            image.close()
            raise ExtractionError(
                f"Requested payload size ({payload_size} bytes) exceeds image capacity ({capacity} bytes)"
            )

        # Convert image to numpy array
        pixels = np.array(image)
        height, width = pixels.shape[:2]

        # Close the original image now that we have the pixel data
        image.close()

        # Extract all bits sequentially (left-to-right, top-to-bottom)
        extracted_bits: List[int] = []
        bits_needed = payload_size * 8

        for y in range(height):
            for x in range(width):
                if len(extracted_bits) >= bits_needed:
                    break

                for channel in range(3):  # R=0, G=1, B=2
                    if len(extracted_bits) >= bits_needed:
                        break

                    bit = pixels[y, x, channel] & 1
                    extracted_bits.append(bit)

            if len(extracted_bits) >= bits_needed:
                break

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
