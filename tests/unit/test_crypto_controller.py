"""
Tests for CryptoController.

Tests all encryption/decryption operations at the controller level.
"""

import pytest

from stegvault.app.controllers.crypto_controller import CryptoController
from stegvault.config import get_default_config


class TestCryptoController:
    """Test CryptoController encryption/decryption."""

    @pytest.fixture
    def controller(self):
        """Create CryptoController instance."""
        return CryptoController()

    @pytest.fixture
    def controller_with_config(self):
        """Create CryptoController with explicit config."""
        config = get_default_config()
        return CryptoController(config=config)

    def test_encrypt_success(self, controller):
        """Should successfully encrypt data."""
        data = b"secret message"
        passphrase = "test_passphrase"

        result = controller.encrypt(data, passphrase)

        assert result.success is True
        assert result.error is None
        assert len(result.ciphertext) > 0
        assert len(result.salt) == 16
        assert len(result.nonce) == 24

    def test_decrypt_success(self, controller):
        """Should successfully decrypt data."""
        data = b"secret message"
        passphrase = "test_passphrase"

        # Encrypt first
        enc_result = controller.encrypt(data, passphrase)
        assert enc_result.success

        # Decrypt
        dec_result = controller.decrypt(
            enc_result.ciphertext, enc_result.salt, enc_result.nonce, passphrase
        )

        assert dec_result.success is True
        assert dec_result.error is None
        assert dec_result.plaintext == data

    def test_decrypt_wrong_passphrase(self, controller):
        """Should fail to decrypt with wrong passphrase."""
        data = b"secret message"
        passphrase = "correct_passphrase"
        wrong_passphrase = "wrong_passphrase"

        # Encrypt
        enc_result = controller.encrypt(data, passphrase)
        assert enc_result.success

        # Try to decrypt with wrong passphrase
        dec_result = controller.decrypt(
            enc_result.ciphertext, enc_result.salt, enc_result.nonce, wrong_passphrase
        )

        assert dec_result.success is False
        assert dec_result.error is not None
        assert "Decryption failed" in dec_result.error
        assert dec_result.plaintext == b""

    def test_encrypt_with_custom_config(self, controller_with_config):
        """Should encrypt with custom config."""
        data = b"test data"
        passphrase = "passphrase"

        result = controller_with_config.encrypt(data, passphrase)

        assert result.success is True
        assert len(result.ciphertext) > 0

    def test_roundtrip_encryption(self, controller):
        """Should successfully roundtrip encrypt and decrypt."""
        data = b"Hello, StegVault!"
        passphrase = "my_secure_passphrase"

        # Encrypt
        enc_result = controller.encrypt(data, passphrase)
        assert enc_result.success

        # Decrypt
        dec_result = controller.decrypt(
            enc_result.ciphertext, enc_result.salt, enc_result.nonce, passphrase
        )

        assert dec_result.success
        assert dec_result.plaintext == data

    def test_encrypt_empty_data(self, controller):
        """Should encrypt empty data."""
        data = b""
        passphrase = "passphrase"

        result = controller.encrypt(data, passphrase)

        assert result.success is True

    def test_encrypt_with_payload_success(self, controller):
        """Should encrypt and serialize to payload."""
        data = b"test message"
        passphrase = "passphrase"

        payload, success, error = controller.encrypt_with_payload(data, passphrase)

        assert success is True
        assert error is None
        assert len(payload) > 0
        # Payload should start with magic header "SPW1"
        assert payload[:4] == b"SPW1"

    def test_decrypt_from_payload_success(self, controller):
        """Should decrypt from payload format."""
        data = b"test message"
        passphrase = "passphrase"

        # Encrypt to payload
        payload, success, error = controller.encrypt_with_payload(data, passphrase)
        assert success

        # Decrypt from payload
        plaintext, success, error = controller.decrypt_from_payload(payload, passphrase)

        assert success is True
        assert error is None
        assert plaintext == data

    def test_decrypt_from_payload_wrong_passphrase(self, controller):
        """Should fail to decrypt payload with wrong passphrase."""
        data = b"secret"
        passphrase = "correct"
        wrong_passphrase = "wrong"

        # Encrypt
        payload, success, error = controller.encrypt_with_payload(data, passphrase)
        assert success

        # Try to decrypt with wrong passphrase
        plaintext, success, error = controller.decrypt_from_payload(payload, wrong_passphrase)

        assert success is False
        assert error is not None
        assert plaintext == b""

    def test_decrypt_from_invalid_payload(self, controller):
        """Should fail to decrypt invalid payload."""
        invalid_payload = b"not a valid payload"
        passphrase = "passphrase"

        plaintext, success, error = controller.decrypt_from_payload(invalid_payload, passphrase)

        assert success is False
        assert error is not None
        assert "Failed to parse payload" in error
        assert plaintext == b""

    def test_roundtrip_with_payload(self, controller):
        """Should successfully roundtrip with payload format."""
        data = b"Full roundtrip test"
        passphrase = "secure_pass"

        # Encrypt to payload
        payload, enc_success, enc_error = controller.encrypt_with_payload(data, passphrase)
        assert enc_success
        assert enc_error is None

        # Decrypt from payload
        plaintext, dec_success, dec_error = controller.decrypt_from_payload(payload, passphrase)
        assert dec_success
        assert dec_error is None
        assert plaintext == data

    def test_encrypt_generic_exception(self, controller, monkeypatch):
        """Should handle generic exceptions during encryption."""

        def mock_derive_key(*args, **kwargs):
            raise RuntimeError("Simulated encryption error")

        monkeypatch.setattr("stegvault.crypto.core.derive_key", mock_derive_key)

        data = b"test"
        passphrase = "pass"

        result = controller.encrypt(data, passphrase)

        assert result.success is False
        assert result.error is not None
        assert "Simulated encryption error" in result.error
        assert result.ciphertext == b""

    def test_decrypt_generic_exception(self, controller, monkeypatch):
        """Should handle generic exceptions during decryption."""

        def mock_derive_key(*args, **kwargs):
            raise RuntimeError("Simulated decryption error")

        monkeypatch.setattr("stegvault.crypto.core.derive_key", mock_derive_key)

        # Use proper salt/nonce sizes
        result = controller.decrypt(b"cipher", b"s" * 16, b"n" * 24, "pass")

        assert result.success is False
        assert result.error is not None
        assert "Simulated decryption error" in result.error
        assert result.plaintext == b""

    def test_encrypt_with_payload_encryption_failure(self, controller, monkeypatch):
        """Should handle encryption failure in encrypt_with_payload."""

        def mock_encrypt(*args, **kwargs):
            from stegvault.app.controllers.crypto_controller import EncryptionResult

            return EncryptionResult(
                ciphertext=b"", salt=b"", nonce=b"", success=False, error="Mock error"
            )

        monkeypatch.setattr(controller, "encrypt", mock_encrypt)

        payload, success, error = controller.encrypt_with_payload(b"data", "pass")

        assert success is False
        assert error == "Mock error"
        assert payload == b""
