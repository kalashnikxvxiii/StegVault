"""
Comprehensive tests for JPEG DCT steganography modules.

Tests cover:
- jpeg_dct.py: JPEG steganography implementation
- dispatcher.py: Format auto-detection and routing
- image_format.py: Image format detection utilities
"""

import os
import tempfile
import pytest
import numpy as np
from PIL import Image

from stegvault.stego import jpeg_dct, dispatcher
from stegvault.utils import image_format
from stegvault.stego.jpeg_dct import StegoError, CapacityError


class TestJPEGDCT:
    """Tests for JPEG DCT steganography module."""

    @pytest.fixture
    def jpeg_image(self):
        """Create a temporary JPEG test image."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            # Create 400x300 RGB image
            img_array = np.random.randint(0, 256, (300, 400, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tmp.name, format="JPEG", quality=85)
            tmp_path = tmp.name

        yield tmp_path

        # Cleanup
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_calculate_capacity_jpeg(self, jpeg_image):
        """Should calculate capacity for JPEG image."""
        capacity = jpeg_dct.calculate_capacity(jpeg_image)

        # JPEG capacity should be positive
        assert capacity > 0
        # Typical capacity for 400x300 JPEG ~10-20KB
        assert 5000 < capacity < 30000

    def test_calculate_capacity_nonexistent_file(self):
        """Should raise StegoError for nonexistent file."""
        with pytest.raises(StegoError, match="Capacity calculation failed"):
            jpeg_dct.calculate_capacity("nonexistent.jpg")

    def test_embed_and_extract_roundtrip(self, jpeg_image):
        """Should embed and extract payload successfully."""
        payload = b"Test payload data" * 50  # ~850 bytes
        output = tempfile.mktemp(suffix=".jpg")

        try:
            # Embed payload
            stego_path = jpeg_dct.embed_payload(jpeg_image, payload, output_path=output)
            assert os.path.exists(stego_path)
            assert stego_path == output

            # Extract payload
            extracted = jpeg_dct.extract_payload(stego_path, len(payload))
            assert extracted == payload

        finally:
            if os.path.exists(output):
                os.unlink(output)

    def test_embed_without_output_path(self, jpeg_image):
        """Should auto-generate output path if not provided."""
        payload = b"Short test"

        stego_path = jpeg_dct.embed_payload(jpeg_image, payload)

        try:
            # Should have "_stego.jpg" suffix
            assert stego_path.endswith("_stego.jpg")
            assert os.path.exists(stego_path)

            # Should be extractable
            extracted = jpeg_dct.extract_payload(stego_path, len(payload))
            assert extracted == payload

        finally:
            if os.path.exists(stego_path):
                os.unlink(stego_path)

    def test_embed_payload_too_large(self, jpeg_image):
        """Should raise CapacityError for oversized payload."""
        # Create payload larger than JPEG capacity
        capacity = jpeg_dct.calculate_capacity(jpeg_image)
        oversized_payload = b"X" * (capacity + 1000)

        with pytest.raises(CapacityError, match="exceeds image capacity"):
            jpeg_dct.embed_payload(jpeg_image, oversized_payload)

    def test_extract_invalid_size(self, jpeg_image):
        """Should handle extraction of different size than embedded."""
        # Create small stego image
        payload = b"Small"
        stego_path = jpeg_dct.embed_payload(jpeg_image, payload)

        try:
            # Try to extract more than embedded - JPEG doesn't validate size
            # It will return whatever data is available (may be truncated or padded)
            extracted = jpeg_dct.extract_payload(stego_path, len(payload) * 10)
            # Just verify it returns bytes
            assert isinstance(extracted, bytes)

        finally:
            if os.path.exists(stego_path):
                os.unlink(stego_path)

    def test_embed_empty_payload(self, jpeg_image):
        """Should handle empty payload gracefully."""
        payload = b""
        output = tempfile.mktemp(suffix=".jpg")

        try:
            stego_path = jpeg_dct.embed_payload(jpeg_image, payload, output_path=output)
            assert os.path.exists(stego_path)

            # Extract should return empty
            extracted = jpeg_dct.extract_payload(stego_path, 0)
            assert extracted == b""

        finally:
            if os.path.exists(output):
                os.unlink(output)

    def test_various_payload_sizes(self, jpeg_image):
        """Should handle various payload sizes correctly."""
        capacity = jpeg_dct.calculate_capacity(jpeg_image)

        test_sizes = [
            10,  # Very small
            100,  # Small
            1000,  # Medium
            capacity // 2,  # Half capacity
            capacity - 100,  # Near capacity
        ]

        for size in test_sizes:
            payload = os.urandom(size)
            output = tempfile.mktemp(suffix=".jpg")

            try:
                stego_path = jpeg_dct.embed_payload(jpeg_image, payload, output_path=output)
                extracted = jpeg_dct.extract_payload(stego_path, size)
                assert extracted == payload, f"Failed for payload size {size}"

            finally:
                if os.path.exists(output):
                    os.unlink(output)

    def test_jpeglib_not_available_calculate_capacity(self, jpeg_image, monkeypatch):
        """Should raise JPEGNotAvailableError when jpeglib is not available (calculate_capacity)."""
        # Mock jpeglib as None to simulate import failure
        import stegvault.stego.jpeg_dct as jpeg_dct_module

        monkeypatch.setattr(jpeg_dct_module, "jpeglib", None)

        from stegvault.stego.jpeg_dct import JPEGNotAvailableError

        with pytest.raises(JPEGNotAvailableError, match="jpeglib library is not installed"):
            jpeg_dct.calculate_capacity(jpeg_image)

    def test_jpeglib_not_available_embed(self, jpeg_image, monkeypatch):
        """Should raise JPEGNotAvailableError when jpeglib is not available (embed_payload)."""
        import stegvault.stego.jpeg_dct as jpeg_dct_module

        monkeypatch.setattr(jpeg_dct_module, "jpeglib", None)

        from stegvault.stego.jpeg_dct import JPEGNotAvailableError

        with pytest.raises(JPEGNotAvailableError, match="jpeglib library is not installed"):
            jpeg_dct.embed_payload(jpeg_image, b"test")

    def test_jpeglib_not_available_extract(self, jpeg_image, monkeypatch):
        """Should raise JPEGNotAvailableError when jpeglib is not available (extract_payload)."""
        import stegvault.stego.jpeg_dct as jpeg_dct_module

        monkeypatch.setattr(jpeg_dct_module, "jpeglib", None)

        from stegvault.stego.jpeg_dct import JPEGNotAvailableError

        with pytest.raises(JPEGNotAvailableError, match="jpeglib library is not installed"):
            jpeg_dct.extract_payload(jpeg_image, 100)

    def test_bits_to_bytes_padding(self):
        """Should pad bits to multiple of 8 when converting to bytes."""
        # Test the internal _bits_to_bytes function with non-multiple-of-8 bits
        # This covers line 128 (padding logic)
        bits = [1, 0, 1, 0, 1]  # 5 bits (not multiple of 8)

        result = jpeg_dct._bits_to_bytes(bits)

        # Should pad with 3 zeros to make 8 bits: [1,0,1,0,1,0,0,0]
        # This equals byte value: 10101000 = 168
        assert result == bytes([168])

    def test_embed_generic_error(self, jpeg_image, monkeypatch):
        """Should raise StegoError for generic errors during embedding."""
        # This tests lines 245-246: generic exception handler
        import stegvault.stego.jpeg_dct as jpeg_dct_module

        def mock_read_dct_error(path):
            raise RuntimeError("Unexpected JPEG read error")

        monkeypatch.setattr(jpeg_dct_module.jpeglib, "read_dct", mock_read_dct_error)

        with pytest.raises(StegoError, match="Embedding failed: Unexpected JPEG read error"):
            jpeg_dct.embed_payload(jpeg_image, b"test")

    def test_extract_insufficient_bits_error(self, jpeg_image, monkeypatch):
        """Should raise ExtractionError when cannot extract enough bits."""
        # This tests line 316: insufficient bits during extraction
        import stegvault.stego.jpeg_dct as jpeg_dct_module

        def mock_read_dct_small(path):
            """Mock jpeglib.read_dct to return JPEG with very few usable coefficients."""

            class MockChannel:
                def __init__(self):
                    # Create tiny array with very few usable coefficients
                    self.shape = (1, 1, 8, 8)
                    # Only one coefficient > 1
                    self._data = np.ones((1, 1, 8, 8), dtype=np.int16)
                    self._data[0, 0, 1, 1] = 5  # One usable coefficient

                def __getitem__(self, key):
                    return self._data[key]

            class MockJPEG:
                def __init__(self):
                    self.Y = MockChannel()
                    self.Cb = None
                    self.Cr = None

            return MockJPEG()

        monkeypatch.setattr(jpeg_dct_module.jpeglib, "read_dct", mock_read_dct_small)

        from stegvault.stego.jpeg_dct import ExtractionError

        # Request more bytes than available
        with pytest.raises(ExtractionError, match="Could not extract all payload bits"):
            jpeg_dct.extract_payload(jpeg_image, 100)

    def test_extract_generic_error(self, jpeg_image, monkeypatch):
        """Should raise StegoError for generic errors during extraction."""
        # This tests lines 325-328: generic exception handler
        import stegvault.stego.jpeg_dct as jpeg_dct_module

        def mock_read_dct_error(path):
            raise RuntimeError("Unexpected extraction error")

        monkeypatch.setattr(jpeg_dct_module.jpeglib, "read_dct", mock_read_dct_error)

        with pytest.raises(StegoError, match="Extraction failed: Unexpected extraction error"):
            jpeg_dct.extract_payload(jpeg_image, 10)


class TestDispatcher:
    """Tests for format dispatcher module."""

    @pytest.fixture
    def png_image(self):
        """Create a temporary PNG test image."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img_array = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tmp.name, format="PNG")
            tmp_path = tmp.name

        yield tmp_path

        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except (PermissionError, FileNotFoundError):
            pass

    @pytest.fixture
    def jpeg_image(self):
        """Create a temporary JPEG test image."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            img_array = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tmp.name, format="JPEG", quality=85)
            tmp_path = tmp.name

        yield tmp_path

        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_calculate_capacity_png_path(self, png_image):
        """Should calculate capacity for PNG file path."""
        capacity = dispatcher.calculate_capacity(png_image)
        assert capacity > 0

    def test_calculate_capacity_jpeg_path(self, jpeg_image):
        """Should calculate capacity for JPEG file path."""
        capacity = dispatcher.calculate_capacity(jpeg_image)
        assert capacity > 0

    def test_calculate_capacity_pil_image_png(self, png_image):
        """Should calculate capacity for PIL PNG Image object."""
        img = Image.open(png_image)
        try:
            capacity = dispatcher.calculate_capacity(img)
            assert capacity > 0
        finally:
            img.close()

    def test_calculate_capacity_pil_image_jpeg(self, jpeg_image):
        """Should calculate capacity for PIL JPEG Image object."""
        img = Image.open(jpeg_image)
        try:
            capacity = dispatcher.calculate_capacity(img)
            assert capacity > 0
        finally:
            img.close()

    def test_embed_extract_png_roundtrip(self, png_image):
        """Should handle PNG embed/extract via dispatcher."""
        payload = b"PNG test payload"
        output = tempfile.mktemp(suffix=".png")

        try:
            stego_path = dispatcher.embed_payload(png_image, payload, output_path=output)
            assert os.path.exists(stego_path)

            extracted = dispatcher.extract_payload(stego_path, len(payload))
            assert extracted == payload

        finally:
            if os.path.exists(output):
                os.unlink(output)

    def test_embed_extract_jpeg_roundtrip(self, jpeg_image):
        """Should handle JPEG embed/extract via dispatcher."""
        payload = b"JPEG test payload"
        output = tempfile.mktemp(suffix=".jpg")

        try:
            stego_path = dispatcher.embed_payload(jpeg_image, payload, output_path=output)
            assert os.path.exists(stego_path)

            extracted = dispatcher.extract_payload(stego_path, len(payload))
            assert extracted == payload

        finally:
            if os.path.exists(output):
                os.unlink(output)

    def test_dispatcher_unsupported_format(self):
        """Should raise StegoError for unsupported format."""
        # Import from png_lsb since dispatcher re-uses that exception
        from stegvault.stego.png_lsb import StegoError as PNGStegoError

        # Create a BMP file (unsupported)
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp:
            img_array = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tmp.name, format="BMP")
            bmp_path = tmp.name

        try:
            with pytest.raises(PNGStegoError, match="Unsupported image format"):
                dispatcher.calculate_capacity(bmp_path)

        finally:
            if os.path.exists(bmp_path):
                os.unlink(bmp_path)

    def test_dispatcher_embed_png_no_output_path(self, png_image):
        """Should auto-generate output path for PNG without output_path."""
        payload = b"Test PNG"

        # Embed without output_path
        stego_path = dispatcher.embed_payload(png_image, payload)

        try:
            # Should have "_stego.png" suffix
            assert stego_path.endswith("_stego.png")
            assert os.path.exists(stego_path)

            # Verify extraction works
            extracted = dispatcher.extract_payload(stego_path, len(payload))
            assert extracted == payload

        finally:
            if os.path.exists(stego_path):
                os.unlink(stego_path)

    def test_dispatcher_embed_unsupported_format(self):
        """Should raise StegoError when embedding in unsupported format."""
        from stegvault.stego.png_lsb import StegoError as PNGStegoError

        # Create BMP file
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp:
            img_array = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tmp.name, format="BMP")
            bmp_path = tmp.name

        try:
            with pytest.raises(PNGStegoError, match="Unsupported image format"):
                dispatcher.embed_payload(bmp_path, b"test")

        finally:
            if os.path.exists(bmp_path):
                os.unlink(bmp_path)

    def test_dispatcher_extract_unsupported_format(self):
        """Should raise StegoError when extracting from unsupported format."""
        from stegvault.stego.png_lsb import StegoError as PNGStegoError

        # Create BMP file
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp:
            img_array = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tmp.name, format="BMP")
            bmp_path = tmp.name

        try:
            with pytest.raises(PNGStegoError, match="Unsupported image format"):
                dispatcher.extract_payload(bmp_path, 100)

        finally:
            if os.path.exists(bmp_path):
                os.unlink(bmp_path)


class TestImageFormat:
    """Tests for image format detection module."""

    @pytest.fixture
    def png_file(self):
        """Create a temporary PNG file."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img_array = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tmp.name, format="PNG")
            tmp_path = tmp.name

        yield tmp_path

        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except (PermissionError, FileNotFoundError):
            pass

    @pytest.fixture
    def jpeg_file(self):
        """Create a temporary JPEG file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            img_array = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tmp.name, format="JPEG")
            tmp_path = tmp.name

        yield tmp_path

        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_detect_png_from_content(self, png_file):
        """Should detect PNG from magic bytes."""
        fmt = image_format.detect_format_from_content(png_file)
        assert fmt == image_format.ImageFormat.PNG

    def test_detect_jpeg_from_content(self, jpeg_file):
        """Should detect JPEG from magic bytes."""
        fmt = image_format.detect_format_from_content(jpeg_file)
        assert fmt == image_format.ImageFormat.JPEG

    def test_detect_png_from_extension(self):
        """Should detect PNG from file extension."""
        fmt = image_format.detect_format_from_path("test.png")
        assert fmt == image_format.ImageFormat.PNG

        fmt = image_format.detect_format_from_path("TEST.PNG")
        assert fmt == image_format.ImageFormat.PNG

    def test_detect_jpeg_from_extension(self):
        """Should detect JPEG from file extension."""
        fmt = image_format.detect_format_from_path("test.jpg")
        assert fmt == image_format.ImageFormat.JPEG

        fmt = image_format.detect_format_from_path("test.jpeg")
        assert fmt == image_format.ImageFormat.JPEG

        fmt = image_format.detect_format_from_path("TEST.JPG")
        assert fmt == image_format.ImageFormat.JPEG

    def test_detect_unknown_extension(self):
        """Should return UNKNOWN for unsupported extension."""
        fmt = image_format.detect_format_from_path("test.bmp")
        assert fmt == image_format.ImageFormat.UNKNOWN

        fmt = image_format.detect_format_from_path("test.gif")
        assert fmt == image_format.ImageFormat.UNKNOWN

    def test_detect_format_png(self, png_file):
        """Should detect PNG format (content + extension)."""
        fmt = image_format.detect_format(png_file)
        assert fmt == image_format.ImageFormat.PNG

    def test_detect_format_jpeg(self, jpeg_file):
        """Should detect JPEG format (content + extension)."""
        fmt = image_format.detect_format(jpeg_file)
        assert fmt == image_format.ImageFormat.JPEG

    def test_detect_format_nonexistent_file(self):
        """Should return UNKNOWN for nonexistent file."""
        fmt = image_format.detect_format("nonexistent.png")
        assert fmt == image_format.ImageFormat.UNKNOWN

    def test_detect_unknown_content(self):
        """Should return UNKNOWN for unknown magic bytes."""
        # Create file with invalid magic bytes
        with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as tmp:
            tmp.write(b"INVALID_MAGIC_BYTES")
            tmp_path = tmp.name

        try:
            fmt = image_format.detect_format_from_content(tmp_path)
            assert fmt == image_format.ImageFormat.UNKNOWN

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_image_format_enum_values(self):
        """Should have correct enum values."""
        assert image_format.ImageFormat.PNG.value == "png"
        assert image_format.ImageFormat.JPEG.value == "jpeg"
        assert image_format.ImageFormat.UNKNOWN.value == "unknown"

    def test_detect_format_prefer_extension(self, png_file):
        """Should detect format with prefer_content=False."""
        # Test extension-first detection
        fmt = image_format.detect_format(png_file, prefer_content=False)
        assert fmt == image_format.ImageFormat.PNG

    def test_detect_format_prefer_extension_fallback(self):
        """Should fallback to content when extension fails (prefer_content=False)."""
        # Create file with wrong extension but valid content
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            # Write PNG magic bytes
            tmp.write(b"\x89PNG\r\n\x1a\n")
            tmp.write(b"fake png content")
            tmp_path = tmp.name

        try:
            # Should fallback to content detection
            fmt = image_format.detect_format(tmp_path, prefer_content=False)
            assert fmt == image_format.ImageFormat.PNG

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_detect_format_from_content_exception(self):
        """Should handle exceptions gracefully in detect_format_from_content."""
        # Create directory (not a file) to trigger exception
        with tempfile.TemporaryDirectory() as tmpdir:
            # Trying to read a directory as file should trigger exception
            fmt = image_format.detect_format_from_content(tmpdir)
            assert fmt == image_format.ImageFormat.UNKNOWN

    def test_get_output_extension_jpeg(self):
        """Should return .jpg for JPEG format."""
        ext = image_format.get_output_extension(image_format.ImageFormat.JPEG)
        assert ext == ".jpg"

    def test_get_output_extension_png(self):
        """Should return .png for PNG format."""
        ext = image_format.get_output_extension(image_format.ImageFormat.PNG)
        assert ext == ".png"

    def test_get_output_extension_unknown(self):
        """Should return empty string for UNKNOWN format."""
        ext = image_format.get_output_extension(image_format.ImageFormat.UNKNOWN)
        assert ext == ""

    def test_ensure_output_path_png(self):
        """Should ensure PNG output path has .png extension."""
        output = image_format.ensure_output_path(
            "input.png", "output", image_format.ImageFormat.PNG
        )
        assert output == "output.png"

    def test_ensure_output_path_jpeg(self):
        """Should ensure JPEG output path has .jpg extension."""
        output = image_format.ensure_output_path(
            "input.jpg", "output", image_format.ImageFormat.JPEG
        )
        assert output == "output.jpg"

    def test_ensure_output_path_already_correct(self):
        """Should not modify output path if extension is already correct."""
        output = image_format.ensure_output_path(
            "input.png", "output.png", image_format.ImageFormat.PNG
        )
        assert output == "output.png"

    def test_ensure_output_path_unknown_format(self):
        """Should return output path unchanged for UNKNOWN format."""
        output = image_format.ensure_output_path(
            "input.bmp", "output", image_format.ImageFormat.UNKNOWN
        )
        assert output == "output"
