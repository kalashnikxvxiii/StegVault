"""
Image format detection and handling utilities.

Determines whether an image is PNG or JPEG and routes to appropriate
steganography module.
"""

import os
from enum import Enum
from typing import Tuple


class ImageFormat(Enum):
    """Supported image formats for steganography."""

    PNG = "png"
    JPEG = "jpeg"
    UNKNOWN = "unknown"


def detect_format_from_path(image_path: str) -> ImageFormat:
    """
    Detect image format from file extension.

    Args:
        image_path: Path to image file

    Returns:
        ImageFormat enum value
    """
    _, ext = os.path.splitext(image_path.lower())

    if ext in (".png",):
        return ImageFormat.PNG
    elif ext in (".jpg", ".jpeg"):
        return ImageFormat.JPEG
    else:
        return ImageFormat.UNKNOWN


def detect_format_from_content(image_path: str) -> ImageFormat:
    """
    Detect image format from file content (magic bytes).

    PNG: starts with b'\\x89PNG\\r\\n\\x1a\\n'
    JPEG: starts with b'\\xff\\xd8\\xff'

    Args:
        image_path: Path to image file

    Returns:
        ImageFormat enum value
    """
    try:
        with open(image_path, "rb") as f:
            magic = f.read(8)

        # PNG magic bytes
        if magic.startswith(b"\x89PNG\r\n\x1a\n"):
            return ImageFormat.PNG

        # JPEG magic bytes
        if magic.startswith(b"\xff\xd8\xff"):
            return ImageFormat.JPEG

        return ImageFormat.UNKNOWN

    except Exception:
        return ImageFormat.UNKNOWN


def detect_format(image_path: str, prefer_content: bool = True) -> ImageFormat:
    """
    Detect image format using both extension and content analysis.

    Args:
        image_path: Path to image file
        prefer_content: If True, prioritize content-based detection over extension

    Returns:
        ImageFormat enum value
    """
    if not os.path.exists(image_path):
        return ImageFormat.UNKNOWN

    if prefer_content:
        # Try content-based detection first
        fmt = detect_format_from_content(image_path)
        if fmt != ImageFormat.UNKNOWN:
            return fmt

        # Fallback to extension
        return detect_format_from_path(image_path)
    else:
        # Try extension first
        fmt = detect_format_from_path(image_path)
        if fmt != ImageFormat.UNKNOWN:
            return fmt

        # Fallback to content
        return detect_format_from_content(image_path)


def get_output_extension(fmt: ImageFormat) -> str:
    """
    Get default file extension for a format.

    Args:
        fmt: ImageFormat enum value

    Returns:
        File extension with dot (e.g., ".png", ".jpg")
    """
    if fmt == ImageFormat.PNG:
        return ".png"
    elif fmt == ImageFormat.JPEG:
        return ".jpg"
    else:
        return ""


def ensure_output_path(input_path: str, output_path: str, fmt: ImageFormat) -> str:
    """
    Ensure output path has correct extension for format.

    Args:
        input_path: Input image path
        output_path: Desired output path
        fmt: Target format

    Returns:
        Output path with correct extension
    """
    ext = get_output_extension(fmt)

    if not ext:
        return output_path

    # If output path doesn't have the right extension, add it
    _, out_ext = os.path.splitext(output_path.lower())
    if out_ext != ext:
        output_path = output_path + ext

    return output_path
