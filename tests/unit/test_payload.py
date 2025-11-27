"""
Unit tests for payload format module.
"""

import pytest
import struct
from stegvault.utils.payload import (
    serialize_payload,
    parse_payload,
    calculate_payload_size,
    get_max_message_size,
    validate_payload_capacity,
    PayloadFormat,
    PayloadError,
    PayloadFormatError,
    MAGIC_HEADER,
    MAGIC_SIZE,
    SALT_SIZE,
    NONCE_SIZE,
    LENGTH_SIZE,
)


class TestPayloadSerialization:
    """Tests for payload serialization."""

    def test_serialize_valid_payload(self):
        """Should serialize payload with correct structure."""
        salt = b"a" * 16
        nonce = b"b" * 24
        ciphertext = b"c" * 32

        payload = serialize_payload(salt, nonce, ciphertext)

        # Check total size
        expected_size = MAGIC_SIZE + SALT_SIZE + NONCE_SIZE + LENGTH_SIZE + 32
        assert len(payload) == expected_size

        # Check magic header
        assert payload[:4] == MAGIC_HEADER

        # Check salt
        assert payload[4:20] == salt

        # Check nonce
        assert payload[20:44] == nonce

        # Check ciphertext length (big-endian)
        ct_length = struct.unpack(">I", payload[44:48])[0]
        assert ct_length == 32

        # Check ciphertext
        assert payload[48:] == ciphertext

    def test_serialize_minimum_ciphertext(self):
        """Should accept minimum valid ciphertext (16 bytes for AEAD tag)."""
        salt = b"a" * 16
        nonce = b"b" * 24
        ciphertext = b"c" * 16  # Minimum: just the tag

        payload = serialize_payload(salt, nonce, ciphertext)
        assert len(payload) == MAGIC_SIZE + SALT_SIZE + NONCE_SIZE + LENGTH_SIZE + 16

    def test_serialize_invalid_salt_size(self):
        """Should raise error for invalid salt size."""
        with pytest.raises(PayloadError, match="Salt must be exactly"):
            serialize_payload(b"short", b"n" * 24, b"c" * 32)

    def test_serialize_invalid_nonce_size(self):
        """Should raise error for invalid nonce size."""
        with pytest.raises(PayloadError, match="Nonce must be exactly"):
            serialize_payload(b"s" * 16, b"short", b"c" * 32)

    def test_serialize_ciphertext_too_short(self):
        """Should raise error for ciphertext shorter than AEAD tag."""
        with pytest.raises(PayloadError, match="too short"):
            serialize_payload(b"s" * 16, b"n" * 24, b"short")


class TestPayloadParsing:
    """Tests for payload parsing."""

    def test_parse_valid_payload(self):
        """Should correctly parse valid payload."""
        salt = b"a" * 16
        nonce = b"b" * 24
        ciphertext = b"c" * 32

        payload = serialize_payload(salt, nonce, ciphertext)
        parsed_salt, parsed_nonce, parsed_ct = parse_payload(payload)

        assert parsed_salt == salt
        assert parsed_nonce == nonce
        assert parsed_ct == ciphertext

    def test_parse_payload_too_short(self):
        """Should raise error for truncated payload."""
        short_payload = b"SPW1" + b"x" * 20

        with pytest.raises(PayloadFormatError, match="too short"):
            parse_payload(short_payload)

    def test_parse_invalid_magic(self):
        """Should raise error for invalid magic header."""
        invalid_payload = b"XXXX" + b"a" * 16 + b"b" * 24
        invalid_payload += struct.pack(">I", 32) + b"c" * 32

        with pytest.raises(PayloadFormatError, match="Invalid magic header"):
            parse_payload(invalid_payload)

    def test_parse_truncated_ciphertext(self):
        """Should raise error when ciphertext is truncated."""
        salt = b"a" * 16
        nonce = b"b" * 24
        ciphertext = b"c" * 32

        # Create payload but truncate the ciphertext
        payload = MAGIC_HEADER + salt + nonce + struct.pack(">I", 32)
        payload += ciphertext[:20]  # Only partial ciphertext

        with pytest.raises(PayloadFormatError, match="Truncated ciphertext"):
            parse_payload(payload)

    def test_parse_invalid_ciphertext_length(self):
        """Should raise error for invalid ciphertext length."""
        payload = MAGIC_HEADER + b"a" * 16 + b"b" * 24
        payload += struct.pack(">I", 10)  # Length < 16 (AEAD tag size)
        payload += b"c" * 16  # Add enough data to pass length check

        with pytest.raises(PayloadFormatError, match="Invalid ciphertext length"):
            parse_payload(payload)

    def test_parse_extra_data(self):
        """Should parse successfully even with extra trailing data."""
        salt = b"a" * 16
        nonce = b"b" * 24
        ciphertext = b"c" * 32

        payload = serialize_payload(salt, nonce, ciphertext)
        payload += b"extra_data"  # Add trailing garbage

        # Should still parse correctly, ignoring extra data
        parsed_salt, parsed_nonce, parsed_ct = parse_payload(payload)

        assert parsed_salt == salt
        assert parsed_nonce == nonce
        assert parsed_ct == ciphertext


class TestPayloadRoundtrip:
    """Test serialization and parsing roundtrip."""

    def test_roundtrip_various_sizes(self):
        """Should maintain data integrity for various payload sizes."""
        test_cases = [
            (b"s" * 16, b"n" * 24, b"c" * 16),  # Minimum
            (b"s" * 16, b"n" * 24, b"c" * 100),  # Medium
            (b"s" * 16, b"n" * 24, b"c" * 1000),  # Large
            (b"s" * 16, b"n" * 24, b"c" * 10000),  # Very large
        ]

        for salt, nonce, ciphertext in test_cases:
            payload = serialize_payload(salt, nonce, ciphertext)
            parsed_salt, parsed_nonce, parsed_ct = parse_payload(payload)

            assert parsed_salt == salt
            assert parsed_nonce == nonce
            assert parsed_ct == ciphertext

    def test_roundtrip_random_data(self):
        """Should handle arbitrary binary data."""
        import os

        salt = os.urandom(16)
        nonce = os.urandom(24)
        ciphertext = os.urandom(256)

        payload = serialize_payload(salt, nonce, ciphertext)
        parsed_salt, parsed_nonce, parsed_ct = parse_payload(payload)

        assert parsed_salt == salt
        assert parsed_nonce == nonce
        assert parsed_ct == ciphertext


class TestPayloadDataclass:
    """Tests for PayloadFormat dataclass."""

    def test_valid_payload_format(self):
        """Should create valid PayloadFormat instance."""
        pf = PayloadFormat(
            magic=MAGIC_HEADER, salt=b"s" * 16, nonce=b"n" * 24, ciphertext=b"c" * 32
        )

        assert pf.magic == MAGIC_HEADER
        assert len(pf.salt) == 16
        assert len(pf.nonce) == 24
        assert len(pf.ciphertext) == 32

    def test_invalid_magic_size(self):
        """Should raise error for invalid magic size."""
        with pytest.raises(ValueError, match="Magic must be"):
            PayloadFormat(
                magic=b"XX", salt=b"s" * 16, nonce=b"n" * 24, ciphertext=b"c" * 32  # Too short
            )

    def test_invalid_salt_size(self):
        """Should raise error for invalid salt size."""
        with pytest.raises(ValueError, match="Salt must be"):
            PayloadFormat(magic=MAGIC_HEADER, salt=b"short", nonce=b"n" * 24, ciphertext=b"c" * 32)

    def test_invalid_nonce_size(self):
        """Should raise error for invalid nonce size."""
        with pytest.raises(ValueError, match="Nonce must be"):
            PayloadFormat(magic=MAGIC_HEADER, salt=b"s" * 16, nonce=b"short", ciphertext=b"c" * 32)

    def test_ciphertext_too_short(self):
        """Should raise error for ciphertext without AEAD tag."""
        with pytest.raises(ValueError, match="too short"):
            PayloadFormat(magic=MAGIC_HEADER, salt=b"s" * 16, nonce=b"n" * 24, ciphertext=b"short")


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_calculate_payload_size(self):
        """Should correctly calculate payload size."""
        ct_length = 100
        expected = MAGIC_SIZE + SALT_SIZE + NONCE_SIZE + LENGTH_SIZE + ct_length
        assert calculate_payload_size(ct_length) == expected

    def test_get_max_message_size(self):
        """Should calculate maximum message size."""
        overhead = MAGIC_SIZE + SALT_SIZE + NONCE_SIZE + LENGTH_SIZE + 16

        # Exact overhead capacity should return 0
        assert get_max_message_size(overhead) == 0

        # Additional capacity should be available for message
        assert get_max_message_size(overhead + 100) == 100

        # Insufficient capacity should return 0
        assert get_max_message_size(overhead - 1) == 0

    def test_validate_payload_capacity_sufficient(self):
        """Should validate sufficient capacity."""
        plaintext_size = 100
        required = calculate_payload_size(plaintext_size + 16)

        assert validate_payload_capacity(required, plaintext_size) is True
        assert validate_payload_capacity(required + 100, plaintext_size) is True

    def test_validate_payload_capacity_insufficient(self):
        """Should detect insufficient capacity."""
        plaintext_size = 100
        required = calculate_payload_size(plaintext_size + 16)

        assert validate_payload_capacity(required - 1, plaintext_size) is False
        assert validate_payload_capacity(0, plaintext_size) is False


class TestExtractFullPayload:
    """Tests for extract_full_payload utility function."""

    def test_extract_full_payload_invalid_magic(self, tmp_path):
        """Should raise ValueError when magic header is invalid."""
        import pytest
        import numpy as np
        from PIL import Image
        from stegvault.stego import embed_payload
        from stegvault.utils import extract_full_payload

        # Create test image
        img_path = tmp_path / "test.png"
        img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        test_image = Image.fromarray(img_array, mode="RGB")
        test_image.save(img_path, format="PNG")

        # Embed payload with wrong magic header (not "SPW1")
        bad_payload = b"XXXX" + b"\x00" * 44  # Wrong magic header
        embed_payload(str(img_path), bad_payload, seed=0, output_path=str(img_path))

        # Should raise ValueError for bad magic header
        with pytest.raises(ValueError, match="Invalid or corrupted payload"):
            extract_full_payload(str(img_path))
