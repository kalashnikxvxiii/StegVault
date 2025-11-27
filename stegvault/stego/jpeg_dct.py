"""
JPEG DCT Steganography for StegVault.

Embeds and extracts encrypted payloads in JPEG images using DCT coefficient
modification. This approach is more robust against JPEG recompression compared
to LSB methods on spatial domain.

Implementation uses simple ±1 modification of AC DCT coefficients, avoiding
coefficients with small absolute values to prevent "shrinkage" artifacts.

The payload begins with a "SPW1" magic header for validation (same as PNG).
Security is provided by strong cryptography (XChaCha20-Poly1305 + Argon2id),
not by the steganographic method itself.
"""

from typing import Optional, List
import numpy as np

try:
    import jpeglib  # type: ignore
except ImportError:
    jpeglib = None  # type: ignore


class StegoError(Exception):
    """Base exception for steganography errors."""

    pass


class CapacityError(StegoError):
    """Raised when image capacity is insufficient for payload."""

    pass


class ExtractionError(StegoError):
    """Raised when payload extraction fails."""

    pass


class JPEGNotAvailableError(StegoError):
    """Raised when jpeglib library is not available."""

    pass


def _ensure_jpeglib() -> None:
    """Ensure jpeglib library is available."""
    if jpeglib is None:
        raise JPEGNotAvailableError(
            "jpeglib library is not installed. Install with: pip install jpeglib"
        )


def calculate_capacity(image_path: str) -> int:
    """
    Calculate maximum payload capacity of a JPEG image in bytes.

    Uses non-zero AC DCT coefficients with |value| > 1 for embedding.
    Capacity depends on image complexity and JPEG quality.

    Args:
        image_path: Path to JPEG image

    Returns:
        Maximum payload size in bytes (conservative estimate)

    Raises:
        JPEGNotAvailableError: If jpeglib is not installed
        StegoError: If capacity calculation fails
    """
    _ensure_jpeglib()

    try:
        # Read JPEG DCT coefficients
        jpeg = jpeglib.read_dct(image_path)

        # Count usable DCT coefficients across all channels (Y, Cb, Cr)
        total_coefficients = 0

        for channel in [jpeg.Y, jpeg.Cb, jpeg.Cr]:
            if channel is not None:
                # Count coefficients with |value| > 1 (avoid shrinkage)
                usable = np.count_nonzero(np.abs(channel) > 1)
                total_coefficients += usable

        # 1 bit per coefficient, account for overhead (~10%)
        usable_bits = int(total_coefficients * 0.9)
        capacity_bytes = usable_bits // 8

        return capacity_bytes

    except Exception as e:
        raise StegoError(f"Capacity calculation failed: {e}")


def _bytes_to_bits(data: bytes) -> List[int]:
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


def _bits_to_bytes(bits: List[int]) -> bytes:
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


def embed_payload(image_path: str, payload: bytes, output_path: Optional[str] = None) -> str:
    """
    Embed payload in JPEG image using DCT coefficient modification.

    Uses ±1 modification of AC DCT coefficients to embed data.
    Avoids coefficients with |value| ≤ 1 to prevent shrinkage artifacts.

    Args:
        image_path: Path to cover JPEG image
        payload: Binary payload to embed (should start with "SPW1" magic header)
        output_path: Optional path to save stego image (auto-generated if None)

    Returns:
        Path to output stego image

    Raises:
        CapacityError: If image capacity is insufficient
        JPEGNotAvailableError: If jpeglib is not installed
        StegoError: If embedding fails
    """
    _ensure_jpeglib()

    try:
        # Read JPEG DCT coefficients
        jpeg = jpeglib.read_dct(image_path)

        # Check capacity
        capacity = calculate_capacity(image_path)
        if len(payload) > capacity:
            raise CapacityError(
                f"Payload size ({len(payload)} bytes) exceeds image capacity ({capacity} bytes)"
            )

        # Convert payload to bits
        payload_bits = _bytes_to_bits(payload)

        # Embed bits into DCT coefficients
        bit_idx = 0

        for channel in [jpeg.Y, jpeg.Cb, jpeg.Cr]:
            if channel is None or bit_idx >= len(payload_bits):
                break

            # Channel shape is (num_blocks_v, num_blocks_h, 8, 8)
            num_blocks_v, num_blocks_h = channel.shape[:2]

            for block_v in range(num_blocks_v):
                for block_h in range(num_blocks_h):
                    if bit_idx >= len(payload_bits):
                        break

                    # Iterate through 8x8 DCT coefficients in this block
                    for i in range(8):
                        for j in range(8):
                            if bit_idx >= len(payload_bits):
                                break

                            # Skip DC coefficient (0,0)
                            if i == 0 and j == 0:
                                continue

                            coef_value = channel[block_v, block_h, i, j]

                            # Only use coefficients with |value| > 1
                            if abs(coef_value) <= 1:
                                continue

                            # Extract current LSB
                            current_lsb = abs(coef_value) % 2

                            # If LSB doesn't match desired bit, modify coefficient
                            if current_lsb != payload_bits[bit_idx]:
                                if coef_value > 0:
                                    channel[block_v, block_h, i, j] = coef_value + 1
                                else:
                                    channel[block_v, block_h, i, j] = coef_value - 1

                            bit_idx += 1

                        if bit_idx >= len(payload_bits):
                            break

                if bit_idx >= len(payload_bits):
                    break

        # Check if we embedded all bits
        if bit_idx < len(payload_bits):
            raise CapacityError(
                f"Could not embed all payload bits (embedded {bit_idx}/{len(payload_bits)})"
            )

        # Determine output path
        if output_path is None:
            import os

            base, _ = os.path.splitext(image_path)
            output_path = f"{base}_stego.jpg"

        # Write modified JPEG
        jpeg.write_dct(output_path)

        return output_path

    except CapacityError:
        raise
    except Exception as e:
        raise StegoError(f"Embedding failed: {e}")


def extract_payload(image_path: str, payload_size: int) -> bytes:
    """
    Extract payload from JPEG image using DCT coefficient analysis.

    Args:
        image_path: Path to stego JPEG image
        payload_size: Size of payload in bytes

    Returns:
        Extracted binary payload

    Raises:
        JPEGNotAvailableError: If jpeglib is not installed
        ExtractionError: If extraction fails
        StegoError: If extraction fails for other reasons
    """
    _ensure_jpeglib()

    try:
        # Read JPEG DCT coefficients
        jpeg = jpeglib.read_dct(image_path)

        # Extract bits from DCT coefficients
        extracted_bits: List[int] = []
        bits_needed = payload_size * 8

        for channel in [jpeg.Y, jpeg.Cb, jpeg.Cr]:
            if channel is None or len(extracted_bits) >= bits_needed:
                break

            # Channel shape is (num_blocks_v, num_blocks_h, 8, 8)
            num_blocks_v, num_blocks_h = channel.shape[:2]

            for block_v in range(num_blocks_v):
                for block_h in range(num_blocks_h):
                    if len(extracted_bits) >= bits_needed:
                        break

                    # Iterate through 8x8 DCT coefficients in this block
                    for i in range(8):
                        for j in range(8):
                            if len(extracted_bits) >= bits_needed:
                                break

                            # Skip DC coefficient (0,0)
                            if i == 0 and j == 0:
                                continue

                            coef_value = channel[block_v, block_h, i, j]

                            # Only extract from coefficients with |value| > 1
                            # (same selection as embedding)
                            if abs(coef_value) <= 1:
                                continue

                            # Extract LSB
                            bit = abs(coef_value) % 2
                            extracted_bits.append(bit)

                        if len(extracted_bits) >= bits_needed:
                            break

                if len(extracted_bits) >= bits_needed:
                    break

        # Check if we extracted enough bits
        if len(extracted_bits) < bits_needed:
            raise ExtractionError(
                f"Could not extract all payload bits (extracted {len(extracted_bits)}/{bits_needed})"
            )

        # Convert bits to bytes
        payload = _bits_to_bytes(extracted_bits[:bits_needed])

        return payload

    except ExtractionError:
        raise
    except Exception as e:
        raise StegoError(f"Extraction failed: {e}")
