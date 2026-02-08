"""Tests for stegvault.utils.secure_memory."""

import pytest

from stegvault.utils.secure_memory import secure_wipe


class TestSecureWipe:
    """Tests for secure_wipe."""

    def test_wipe_bytearray_zeros(self):
        """Wiped bytearray should be all zeros."""
        buf = bytearray(b"secret")
        secure_wipe(buf)
        assert buf == bytearray(len(buf))

    def test_wipe_empty_bytearray(self):
        """Empty bytearray is a no-op."""
        buf = bytearray()
        secure_wipe(buf)
        assert buf == bytearray()

    def test_wipe_none_no_op(self):
        """None is a no-op."""
        secure_wipe(None)  # no raise

    def test_wipe_bytes_ignored(self):
        """Immutable bytes are ignored (no exception)."""
        secure_wipe(b"immutable")  # no raise

    def test_wipe_memoryview_writable(self):
        """Writable memoryview (from bytearray) is wiped."""
        buf = bytearray(b"data")
        mv = memoryview(buf)
        secure_wipe(mv)
        assert buf == bytearray(len(buf))
