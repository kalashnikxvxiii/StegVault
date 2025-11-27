"""
Steganography dispatcher - automatically routes to PNG or JPEG implementation.

This module provides a unified interface that automatically detects image format
and routes to the appropriate steganography implementation (PNG LSB or JPEG DCT).
"""

from typing import Optional, Union
from stegvault.utils.image_format import detect_format, ImageFormat
from stegvault.stego import png_lsb, jpeg_dct
from stegvault.stego.png_lsb import StegoError, CapacityError, ExtractionError


def calculate_capacity(image: Union[str, "PIL.Image.Image"]) -> int:  # type: ignore
    """
    Calculate maximum payload capacity of an image.

    Automatically detects format (PNG/JPEG) and uses appropriate method.

    Args:
        image: Path to image file OR PIL Image object

    Returns:
        Maximum payload size in bytes

    Raises:
        StegoError: If image format is unsupported
    """
    # Handle PIL Image object
    if hasattr(image, "save"):  # Duck typing for PIL Image
        from PIL import Image
        import tempfile
        import os

        # Save to temp file to detect format
        suffix = ".png" if image.format == "PNG" else ".jpg"
        temp_path = tempfile.mktemp(suffix=suffix)
        try:
            image.save(temp_path)
            fmt = detect_format(temp_path)

            if fmt == ImageFormat.PNG:
                return png_lsb.calculate_capacity(image)
            elif fmt == ImageFormat.JPEG:
                capacity = jpeg_dct.calculate_capacity(temp_path)
                return capacity
            else:
                raise StegoError(f"Unsupported image format: {image.format}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # Handle path string
    else:
        fmt = detect_format(image)

        if fmt == ImageFormat.PNG:
            from PIL import Image

            img = Image.open(image)
            capacity = png_lsb.calculate_capacity(img)
            img.close()
            return capacity
        elif fmt == ImageFormat.JPEG:
            return jpeg_dct.calculate_capacity(image)
        else:
            raise StegoError(f"Unsupported image format: {image}")


def embed_payload(
    image_path: str,
    payload: bytes,
    seed: int = 0,
    output_path: Optional[str] = None,
) -> str:
    """
    Embed payload in image using appropriate steganography method.

    Automatically detects format (PNG/JPEG) and uses appropriate method.

    Args:
        image_path: Path to cover image
        payload: Binary payload to embed
        output_path: Optional output path (auto-generated if None)
        seed: Deprecated parameter for PNG (ignored)

    Returns:
        Path to output stego image

    Raises:
        CapacityError: If image capacity is insufficient
        StegoError: If embedding fails or format is unsupported
    """
    fmt = detect_format(image_path)

    if fmt == ImageFormat.PNG:
        # PNG LSB returns PIL Image, we need to handle output path
        if output_path is None:
            import os

            base, _ = os.path.splitext(image_path)
            output_path = f"{base}_stego.png"

        stego_img = png_lsb.embed_payload(image_path, payload, seed, output_path)
        stego_img.close()
        return output_path

    elif fmt == ImageFormat.JPEG:
        # JPEG DCT returns output path directly
        return jpeg_dct.embed_payload(image_path, payload, output_path)

    else:
        raise StegoError(f"Unsupported image format: {image_path}")


def extract_payload(image_path: str, payload_size: int, seed: int = 0) -> bytes:
    """
    Extract payload from stego image using appropriate method.

    Automatically detects format (PNG/JPEG) and uses appropriate method.

    Args:
        image_path: Path to stego image
        payload_size: Size of payload in bytes
        seed: Deprecated parameter for PNG (ignored)

    Returns:
        Extracted binary payload

    Raises:
        ExtractionError: If extraction fails
        StegoError: If format is unsupported
    """
    fmt = detect_format(image_path)

    if fmt == ImageFormat.PNG:
        return png_lsb.extract_payload(image_path, payload_size, seed)
    elif fmt == ImageFormat.JPEG:
        return jpeg_dct.extract_payload(image_path, payload_size)
    else:
        raise StegoError(f"Unsupported image format: {image_path}")
