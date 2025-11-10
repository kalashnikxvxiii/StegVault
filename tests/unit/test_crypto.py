"""
Unit tests for cryptography module.
"""

import pytest
from stegvault.crypto.core import (
    derive_key,
    encrypt_data,
    decrypt_data,
    generate_salt,
    generate_nonce,
    verify_passphrase_strength,
    CryptoError,
    DecryptionError,
    SALT_SIZE,
    NONCE_SIZE,
)


class TestKeyDerivation:
    """Tests for Argon2id key derivation."""

    def test_derive_key_returns_32_bytes(self):
        """Key derivation should return 32-byte key."""
        salt = generate_salt()
        key = derive_key("test-passphrase", salt)
        assert len(key) == 32

    def test_derive_key_deterministic(self):
        """Same passphrase and salt should produce same key."""
        salt = generate_salt()
        passphrase = "test-passphrase"

        key1 = derive_key(passphrase, salt)
        key2 = derive_key(passphrase, salt)

        assert key1 == key2

    def test_derive_key_different_salts(self):
        """Different salts should produce different keys."""
        passphrase = "test-passphrase"
        salt1 = generate_salt()
        salt2 = generate_salt()

        key1 = derive_key(passphrase, salt1)
        key2 = derive_key(passphrase, salt2)

        assert key1 != key2

    def test_derive_key_different_passphrases(self):
        """Different passphrases should produce different keys."""
        salt = generate_salt()

        key1 = derive_key("passphrase1", salt)
        key2 = derive_key("passphrase2", salt)

        assert key1 != key2

    def test_derive_key_invalid_salt_size(self):
        """Should raise error for invalid salt size."""
        with pytest.raises(CryptoError, match="Salt must be exactly"):
            derive_key("passphrase", b"short")


class TestRandomGeneration:
    """Tests for random salt and nonce generation."""

    def test_generate_salt_size(self):
        """Salt should be 16 bytes."""
        salt = generate_salt()
        assert len(salt) == SALT_SIZE

    def test_generate_salt_unique(self):
        """Generated salts should be unique."""
        salts = [generate_salt() for _ in range(100)]
        assert len(set(salts)) == 100

    def test_generate_nonce_size(self):
        """Nonce should be 24 bytes."""
        nonce = generate_nonce()
        assert len(nonce) == NONCE_SIZE

    def test_generate_nonce_unique(self):
        """Generated nonces should be unique."""
        nonces = [generate_nonce() for _ in range(100)]
        assert len(set(nonces)) == 100


class TestEncryption:
    """Tests for AEAD encryption."""

    def test_encrypt_returns_tuple(self):
        """Encryption should return (ciphertext, salt, nonce)."""
        plaintext = b"secret message"
        passphrase = "strong-passphrase"

        result = encrypt_data(plaintext, passphrase)

        assert isinstance(result, tuple)
        assert len(result) == 3

        ciphertext, salt, nonce = result
        assert len(salt) == SALT_SIZE
        assert len(nonce) == NONCE_SIZE
        assert len(ciphertext) > len(plaintext)  # Includes tag

    def test_encrypt_different_each_time(self):
        """Encrypting same data should produce different ciphertext."""
        plaintext = b"secret message"
        passphrase = "strong-passphrase"

        ct1, salt1, nonce1 = encrypt_data(plaintext, passphrase)
        ct2, salt2, nonce2 = encrypt_data(plaintext, passphrase)

        # Different random values
        assert salt1 != salt2
        assert nonce1 != nonce2
        assert ct1 != ct2

    def test_encrypt_empty_data(self):
        """Should be able to encrypt empty data."""
        plaintext = b""
        passphrase = "strong-passphrase"

        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)

        assert len(ciphertext) == 16  # Just the Poly1305 tag


class TestDecryption:
    """Tests for AEAD decryption."""

    def test_decrypt_correct_passphrase(self):
        """Decryption with correct passphrase should recover plaintext."""
        plaintext = b"secret message"
        passphrase = "strong-passphrase"

        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)
        decrypted = decrypt_data(ciphertext, salt, nonce, passphrase)

        assert decrypted == plaintext

    def test_decrypt_wrong_passphrase(self):
        """Decryption with wrong passphrase should fail."""
        plaintext = b"secret message"
        passphrase = "strong-passphrase"

        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)

        with pytest.raises(DecryptionError, match="wrong passphrase"):
            decrypt_data(ciphertext, salt, nonce, "wrong-passphrase")

    def test_decrypt_corrupted_ciphertext(self):
        """Decryption with corrupted ciphertext should fail."""
        plaintext = b"secret message"
        passphrase = "strong-passphrase"

        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)

        # Corrupt the ciphertext
        corrupted = bytearray(ciphertext)
        corrupted[0] ^= 0xFF

        with pytest.raises(DecryptionError, match="wrong passphrase"):
            decrypt_data(bytes(corrupted), salt, nonce, passphrase)

    def test_decrypt_wrong_salt(self):
        """Decryption with wrong salt should fail."""
        plaintext = b"secret message"
        passphrase = "strong-passphrase"

        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)
        wrong_salt = generate_salt()

        with pytest.raises(DecryptionError):
            decrypt_data(ciphertext, wrong_salt, nonce, passphrase)

    def test_decrypt_wrong_nonce(self):
        """Decryption with wrong nonce should fail."""
        plaintext = b"secret message"
        passphrase = "strong-passphrase"

        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)
        wrong_nonce = generate_nonce()

        with pytest.raises(DecryptionError):
            decrypt_data(ciphertext, salt, wrong_nonce, passphrase)

    def test_decrypt_invalid_salt_size(self):
        """Should raise error for invalid salt size."""
        with pytest.raises(CryptoError, match="Salt must be exactly"):
            decrypt_data(b"data", b"short", generate_nonce(), "passphrase")

    def test_decrypt_invalid_nonce_size(self):
        """Should raise error for invalid nonce size."""
        with pytest.raises(CryptoError, match="Nonce must be exactly"):
            decrypt_data(b"data", generate_salt(), b"short", "passphrase")


class TestRoundtrip:
    """End-to-end encryption/decryption tests."""

    def test_roundtrip_various_sizes(self):
        """Test encryption/decryption for various data sizes."""
        passphrase = "strong-passphrase"

        test_cases = [
            b"",
            b"short",
            b"a" * 100,
            b"a" * 1000,
            b"a" * 10000,
            bytes(range(256)),  # All byte values
        ]

        for plaintext in test_cases:
            ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)
            decrypted = decrypt_data(ciphertext, salt, nonce, passphrase)
            assert decrypted == plaintext, f"Failed for size {len(plaintext)}"

    def test_roundtrip_unicode(self):
        """Test with unicode characters."""
        plaintext = "Hello 世界 🔐".encode('utf-8')
        passphrase = "strong-passphrase"

        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)
        decrypted = decrypt_data(ciphertext, salt, nonce, passphrase)

        assert decrypted == plaintext


class TestPassphraseStrength:
    """Tests for passphrase strength verification."""

    def test_strong_passphrase(self):
        """Strong passphrase should pass."""
        valid, msg = verify_passphrase_strength("MyStrong123Pass")
        assert valid is True

    def test_short_passphrase(self):
        """Short passphrase should fail."""
        valid, msg = verify_passphrase_strength("Short1A")
        assert valid is False
        assert "at least" in msg

    def test_no_uppercase(self):
        """Passphrase without uppercase should fail."""
        valid, msg = verify_passphrase_strength("nostrongpass123")
        assert valid is False
        assert "uppercase" in msg.lower()

    def test_no_lowercase(self):
        """Passphrase without lowercase should fail."""
        valid, msg = verify_passphrase_strength("NOSTRONGPASS123")
        assert valid is False
        assert "lowercase" in msg.lower()

    def test_no_digits(self):
        """Passphrase without digits should fail."""
        valid, msg = verify_passphrase_strength("NoStrongPass")
        assert valid is False
        assert "digit" in msg.lower()
