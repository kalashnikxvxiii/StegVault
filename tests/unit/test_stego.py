"""
Unit tests for steganography module.
"""

import pytest
import tempfile
import os
from PIL import Image
import numpy as np

from stegvault.stego.png_lsb import (
    embed_payload,
    extract_payload,
    calculate_capacity,
    embed_and_extract_roundtrip_test,
    StegoError,
    CapacityError,
    ExtractionError,
)


@pytest.fixture
def test_image_small():
    """Create a small test PNG image (10x10 RGB)."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Create 10x10 RGB image with random colors
        img_array = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode="RGB")
        img.save(tmp.name, format="PNG")
        yield tmp.name
        # Cleanup
        os.unlink(tmp.name)


@pytest.fixture
def test_image_medium():
    """Create a medium test PNG image (100x100 RGB)."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode="RGB")
        img.save(tmp.name, format="PNG")
        yield tmp.name
        os.unlink(tmp.name)


@pytest.fixture
def test_image_large():
    """Create a large test PNG image (500x500 RGB)."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img_array = np.random.randint(0, 256, (500, 500, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode="RGB")
        img.save(tmp.name, format="PNG")
        yield tmp.name
        os.unlink(tmp.name)


class TestCapacityCalculation:
    """Tests for image capacity calculation."""

    def test_capacity_small_image(self, test_image_small):
        """Should calculate correct capacity for 10x10 image."""
        img = Image.open(test_image_small)
        try:
            capacity = calculate_capacity(img)

            # 10x10 pixels * 3 channels / 8 bits = 37.5 bytes → 37 bytes
            expected = (10 * 10 * 3) // 8
            assert capacity == expected
            assert capacity == 37
        finally:
            img.close()

    def test_capacity_medium_image(self, test_image_medium):
        """Should calculate correct capacity for 100x100 image."""
        img = Image.open(test_image_medium)
        capacity = calculate_capacity(img)

        expected = (100 * 100 * 3) // 8
        assert capacity == expected
        assert capacity == 3750

    def test_capacity_large_image(self, test_image_large):
        """Should calculate correct capacity for 500x500 image."""
        img = Image.open(test_image_large)
        capacity = calculate_capacity(img)

        expected = (500 * 500 * 3) // 8
        assert capacity == expected
        assert capacity == 93750


class TestEmbedding:
    """Tests for payload embedding."""

    def test_embed_small_payload(self, test_image_medium):
        """Should successfully embed small payload."""
        payload = b"Hello, StegVault!"
        seed = 12345

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_path = tmp.name

        try:
            stego_img = embed_payload(test_image_medium, payload, seed, output_path)

            assert stego_img is not None
            assert os.path.exists(output_path)

            # Verify it's a valid PNG
            loaded = Image.open(output_path)
            assert loaded.mode == "RGB"
            assert loaded.size == Image.open(test_image_medium).size

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_embed_payload_too_large(self, test_image_small):
        """Should raise CapacityError for oversized payload."""
        # 10x10 image has capacity of 37 bytes
        payload = b"x" * 100  # Way too large

        seed = 12345

        with pytest.raises(CapacityError, match="exceeds image capacity"):
            embed_payload(test_image_small, payload, seed)

    def test_embed_maximum_capacity(self, test_image_medium):
        """Should embed payload at maximum capacity."""
        img = Image.open(test_image_medium)
        capacity = calculate_capacity(img)

        payload = b"x" * capacity  # Maximum size
        seed = 12345

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_path = tmp.name

        try:
            stego_img = embed_payload(test_image_medium, payload, seed, output_path)
            assert stego_img is not None

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_embed_empty_payload(self, test_image_medium):
        """Should handle empty payload."""
        payload = b""
        seed = 12345

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_path = tmp.name

        try:
            stego_img = embed_payload(test_image_medium, payload, seed, output_path)
            assert stego_img is not None

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestExtraction:
    """Tests for payload extraction."""

    def test_extract_embedded_payload(self, test_image_medium):
        """Should correctly extract embedded payload."""
        original_payload = b"Test message for extraction"
        seed = 54321

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            stego_path = tmp.name

        try:
            # Embed
            embed_payload(test_image_medium, original_payload, seed, stego_path)

            # Extract
            extracted = extract_payload(stego_path, len(original_payload), seed)

            assert extracted == original_payload

        finally:
            if os.path.exists(stego_path):
                os.unlink(stego_path)

    def test_extract_with_wrong_seed(self, test_image_medium):
        """Should extract garbage with wrong seed."""
        original_payload = b"Secret data"
        correct_seed = 11111
        wrong_seed = 99999

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            stego_path = tmp.name

        try:
            # Embed with correct seed
            embed_payload(test_image_medium, original_payload, correct_seed, stego_path)

            # Extract with wrong seed
            extracted = extract_payload(stego_path, len(original_payload), wrong_seed)

            # Should get different data
            assert extracted != original_payload

        finally:
            if os.path.exists(stego_path):
                os.unlink(stego_path)

    def test_extract_oversized_payload(self, test_image_small):
        """Should raise ExtractionError for oversized extraction."""
        img = Image.open(test_image_small)
        capacity = calculate_capacity(img)

        with pytest.raises(ExtractionError, match="exceeds image capacity"):
            extract_payload(test_image_small, capacity + 100, 12345)


class TestRoundtrip:
    """End-to-end roundtrip tests."""

    def test_roundtrip_various_payloads(self, test_image_large):
        """Should maintain integrity for various payload types."""
        test_payloads = [
            b"Short",
            b"A" * 100,
            b"Mixed123!@#",
            bytes(range(256)),  # All byte values
            b"\x00" * 50,  # Null bytes
            b"\xff" * 50,  # Max bytes
        ]

        for payload in test_payloads:
            seed = hash(payload) % (2**31)
            assert embed_and_extract_roundtrip_test(
                test_image_large, payload, seed
            ), f"Failed for payload: {payload[:20]}"

    def test_roundtrip_different_seeds(self, test_image_medium):
        """Should work with different random seeds."""
        payload = b"Testing different seeds"

        for seed in [0, 1, 12345, 999999, 2**31 - 1]:
            assert embed_and_extract_roundtrip_test(
                test_image_medium, payload, seed
            ), f"Failed for seed: {seed}"

    def test_roundtrip_binary_data(self, test_image_large):
        """Should handle arbitrary binary data."""
        import os

        payload = os.urandom(1000)
        seed = 42

        assert embed_and_extract_roundtrip_test(test_image_large, payload, seed)


class TestImageFormatHandling:
    """Tests for different image formats and modes."""

    def test_rgba_image_handling(self):
        """Should handle RGBA images by converting to RGB."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            rgba_path = tmp.name

        try:
            # Create RGBA image
            img_array = np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGBA")
            img.save(rgba_path, format="PNG")

            payload = b"Test RGBA"
            seed = 123

            # Should convert and embed successfully
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp2:
                output_path = tmp2.name

            stego_img = embed_payload(rgba_path, payload, seed, output_path)
            assert stego_img.mode == "RGB"

            # Should extract successfully
            extracted = extract_payload(output_path, len(payload), seed)
            assert extracted == payload

            os.unlink(output_path)

        finally:
            if os.path.exists(rgba_path):
                os.unlink(rgba_path)


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_image_path(self):
        """Should raise error for non-existent image."""
        with pytest.raises(Exception):  # FileNotFoundError or similar
            embed_payload("/nonexistent/image.png", b"test", 123)

    def test_extract_from_non_stego_image(self, test_image_medium):
        """Should extract garbage from non-stego image."""
        # Extract from regular image (no embedded payload)
        extracted = extract_payload(test_image_medium, 10, 12345)

        # Should return some data (but it's garbage)
        assert len(extracted) == 10
