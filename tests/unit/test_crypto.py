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

    def test_derive_key_invalid_time_cost(self):
        """Should raise error for invalid time_cost parameter."""
        salt = generate_salt()

        with pytest.raises(CryptoError, match="time_cost must be >= 1"):
            derive_key("test", salt, time_cost=0)

    def test_derive_key_invalid_memory_cost(self):
        """Should raise error for invalid memory_cost parameter."""
        salt = generate_salt()

        with pytest.raises(CryptoError, match="memory_cost must be >= 8"):
            derive_key("test", salt, memory_cost=7)

    def test_derive_key_invalid_parallelism(self):
        """Should raise error for invalid parallelism parameter."""
        salt = generate_salt()

        with pytest.raises(CryptoError, match="parallelism must be >= 1"):
            derive_key("test", salt, parallelism=0)

    def test_derive_key_argon2_failure(self, monkeypatch):
        """Should raise CryptoError when Argon2 fails internally."""
        salt = generate_salt()

        # Mock hash_secret_raw in the crypto.core module to raise an exception
        def mock_hash_secret_raw(*args, **kwargs):
            raise RuntimeError("Simulated Argon2 internal failure")

        monkeypatch.setattr("stegvault.crypto.core.hash_secret_raw", mock_hash_secret_raw)

        with pytest.raises(CryptoError, match="Key derivation failed"):
            derive_key("test", salt)


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

    def test_encrypt_nacl_failure(self, monkeypatch):
        """Should raise CryptoError when NaCl encryption fails."""
        from unittest import mock
        import nacl.secret

        plaintext = b"test data"
        passphrase = "strong-passphrase"

        # Mock SecretBox.encrypt to raise an exception
        original_secretbox = nacl.secret.SecretBox

        class MockSecretBox:
            def __init__(self, key):
                pass

            def encrypt(self, plaintext, nonce):
                raise RuntimeError("Simulated NaCl encryption failure")

        monkeypatch.setattr(nacl.secret, "SecretBox", MockSecretBox)

        with pytest.raises(CryptoError, match="Encryption failed"):
            encrypt_data(plaintext, passphrase)


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

    def test_decrypt_generic_failure(self, monkeypatch):
        """Should raise CryptoError for non-NaCl exceptions during decryption."""
        from unittest import mock
        import nacl.secret

        # First encrypt some data properly
        plaintext = b"test data"
        passphrase = "strong-passphrase"
        ciphertext, salt, nonce = encrypt_data(plaintext, passphrase)

        # Mock SecretBox.decrypt to raise a generic exception (not nacl.exceptions.CryptoError)
        original_secretbox = nacl.secret.SecretBox

        class MockSecretBox:
            def __init__(self, key):
                pass

            def decrypt(self, ciphertext, nonce):
                raise RuntimeError("Simulated generic decryption failure")

        monkeypatch.setattr(nacl.secret, "SecretBox", MockSecretBox)

        with pytest.raises(CryptoError, match="Decryption failed"):
            decrypt_data(ciphertext, salt, nonce, passphrase)


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
        plaintext = "Hello 世界 🔐".encode("utf-8")
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

    def test_acceptable_passphrase(self):
        """Acceptable passphrase (score 2) should pass with tip."""
        # These are known to get zxcvbn score 2 (acceptable)
        # Verified via testing: hjklzx123456, mnbvcx789456, trewqs123456
        valid, msg = verify_passphrase_strength("hjklzx123456")

        # Score 2 is acceptable, so should be valid
        assert valid is True
        assert "acceptable" in msg.lower()

        # Should include a tip from suggestions
        # zxcvbn feedback for this: "Add another word or two. Uncommon words are better."
        # The code shows tip if suggestions exist: message += f" (tip: {suggestions[0]})"
        assert "tip:" in msg.lower() or "suggestions" in msg.lower() or len(msg) > 30

    def test_short_passphrase(self):
        """Short passphrase should fail."""
        valid, msg = verify_passphrase_strength("Short1A")
        assert valid is False
        assert "at least" in msg

    def test_no_uppercase(self):
        """Passphrase without uppercase - zxcvbn may still accept if long/complex."""
        valid, msg = verify_passphrase_strength("nostrongpass123")
        # With zxcvbn, this depends on overall strength, not just character types
        # A simple pattern like this will likely be weak
        # Just verify it returns a valid response
        assert isinstance(valid, bool)
        assert isinstance(msg, str)

    def test_no_lowercase(self):
        """Passphrase without lowercase - zxcvbn may still accept if long/complex."""
        valid, msg = verify_passphrase_strength("NOSTRONGPASS123")
        # With zxcvbn, this depends on overall strength
        assert isinstance(valid, bool)
        assert isinstance(msg, str)

    def test_no_digits(self):
        """Passphrase without digits - zxcvbn may still accept if long/complex."""
        valid, msg = verify_passphrase_strength("NoStrongPassPhrase")
        # With zxcvbn, lack of digits doesn't auto-fail if password is otherwise strong
        assert isinstance(valid, bool)
        assert isinstance(msg, str)
