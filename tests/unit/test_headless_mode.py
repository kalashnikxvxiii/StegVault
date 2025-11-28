"""
Tests for headless mode features (JSON output, passphrase file, env vars).

Tests v0.6.0 headless mode functionality:
- JSON output for critical commands
- Passphrase from file
- Passphrase from environment variable
- Exit codes (0=success, 1=error, 2=validation)
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from stegvault.cli import main
from stegvault.vault import create_vault, add_entry, vault_to_json
from stegvault.crypto import encrypt_data
from stegvault.stego import embed_payload
from stegvault.utils import serialize_payload


class TestCheckCommandJSON:
    """Test 'check' command with JSON output."""

    def test_check_json_success(self, png_image):
        """Should output JSON for successful check."""
        runner = CliRunner()
        result = runner.invoke(main, ["check", "-i", png_image, "--json"])

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["image_path"] == png_image
        assert "capacity" in data["data"]
        assert "max_password_size" in data["data"]

    def test_check_json_nonexistent_file(self):
        """Should exit with error for nonexistent file (Click validation)."""
        runner = CliRunner()
        result = runner.invoke(main, ["check", "-i", "nonexistent.png", "--json"])

        # Click validates path before our code runs
        assert result.exit_code != 0
        assert "does not exist" in result.output.lower()


class TestVaultGetCommandJSON:
    """Test 'vault get' command with JSON output."""

    def test_vault_get_json_success(self, vault_image, vault_passphrase):
        """Should output JSON for successful vault get."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase",
                vault_passphrase,
                "--json",
            ],
        )

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["key"] == "test_key"
        assert "password" in data["data"]

    def test_vault_get_json_wrong_passphrase(self, vault_image):
        """Should output JSON error for wrong passphrase."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["vault", "get", vault_image, "-k", "test_key", "--passphrase", "wrongpass", "--json"],
        )

        assert result.exit_code == 1

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "error"
        assert data["error_type"] == "decryption"

    def test_vault_get_json_entry_not_found(self, vault_image, vault_passphrase):
        """Should output JSON error for missing entry."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "nonexistent",
                "--passphrase",
                vault_passphrase,
                "--json",
            ],
        )

        assert result.exit_code == 1

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "error"
        assert data["error_type"] == "entry_not_found"
        assert "available_keys" in data

    def test_vault_get_json_invalid_clipboard_timeout(self, vault_image, vault_passphrase):
        """Should output JSON validation error for invalid timeout."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase",
                vault_passphrase,
                "--clipboard-timeout",
                "-1",
                "--json",
            ],
        )

        assert result.exit_code == 2  # Validation error

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "error"
        assert data["error_type"] == "validation"

    def test_vault_get_json_incompatible_with_clipboard(self, vault_image, vault_passphrase):
        """Should reject --json with --clipboard."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase",
                vault_passphrase,
                "--clipboard",
                "--json",
            ],
        )

        assert result.exit_code == 2  # Validation error

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "error"
        assert data["error_type"] == "validation"


class TestVaultListCommandJSON:
    """Test 'vault list' command with JSON output."""

    def test_vault_list_json_success(self, vault_image, vault_passphrase):
        """Should output JSON for successful vault list."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["vault", "list", vault_image, "--passphrase", vault_passphrase, "--json"]
        )

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert "entries" in data["data"]
        assert data["data"]["entry_count"] > 0

    def test_vault_list_json_wrong_passphrase(self, vault_image):
        """Should output JSON error for wrong passphrase."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["vault", "list", vault_image, "--passphrase", "wrongpass", "--json"]
        )

        assert result.exit_code == 1

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "error"
        assert data["error_type"] == "decryption"


class TestPassphraseFile:
    """Test --passphrase-file support."""

    def test_vault_get_passphrase_from_file(self, vault_image, vault_passphrase, tmp_path):
        """Should read passphrase from file successfully."""
        # Create passphrase file
        passphrase_file = tmp_path / "passphrase.txt"
        passphrase_file.write_text(vault_passphrase)

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase-file",
                str(passphrase_file),
                "--json",
            ],
        )

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["key"] == "test_key"

    def test_vault_get_passphrase_file_with_whitespace(
        self, vault_image, vault_passphrase, tmp_path
    ):
        """Should strip whitespace from passphrase file."""
        # Create passphrase file with newlines and spaces
        passphrase_file = tmp_path / "passphrase.txt"
        passphrase_file.write_text(f"  {vault_passphrase}  \n")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase-file",
                str(passphrase_file),
                "--json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"

    def test_vault_get_passphrase_file_empty(self, vault_image, tmp_path):
        """Should reject empty passphrase file."""
        passphrase_file = tmp_path / "empty.txt"
        passphrase_file.write_text("")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase-file",
                str(passphrase_file),
            ],
        )

        assert result.exit_code == 2  # Validation error
        assert "empty" in result.output.lower()


class TestPassphraseEnvironmentVariable:
    """Test STEGVAULT_PASSPHRASE environment variable."""

    def test_vault_get_passphrase_from_env(self, vault_image, vault_passphrase, monkeypatch):
        """Should read passphrase from environment variable."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", vault_passphrase)

        runner = CliRunner()
        result = runner.invoke(main, ["vault", "get", vault_image, "-k", "test_key", "--json"])

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["key"] == "test_key"

    def test_vault_get_env_passphrase_with_whitespace(
        self, vault_image, vault_passphrase, monkeypatch
    ):
        """Should strip whitespace from env var passphrase."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", f"  {vault_passphrase}  ")

        runner = CliRunner()
        result = runner.invoke(main, ["vault", "get", vault_image, "-k", "test_key", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"

    def test_vault_get_env_passphrase_empty(self, vault_image, monkeypatch):
        """Should reject empty env var passphrase."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "   ")

        runner = CliRunner()
        result = runner.invoke(main, ["vault", "get", vault_image, "-k", "test_key"])

        assert result.exit_code == 2  # Validation error
        assert "empty" in result.output.lower()


class TestPassphrasePriority:
    """Test passphrase source priority (explicit > file > env > prompt)."""

    def test_explicit_passphrase_overrides_file(self, vault_image, vault_passphrase, tmp_path):
        """Explicit --passphrase should override --passphrase-file."""
        wrong_file = tmp_path / "wrong.txt"
        wrong_file.write_text("wrongpassphrase")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase",
                vault_passphrase,
                "--passphrase-file",
                str(wrong_file),
                "--json",
            ],
        )

        # Should succeed because explicit passphrase is correct
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"

    def test_file_overrides_env(self, vault_image, vault_passphrase, tmp_path, monkeypatch):
        """--passphrase-file should override STEGVAULT_PASSPHRASE."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "wrongpassphrase")

        passphrase_file = tmp_path / "passphrase.txt"
        passphrase_file.write_text(vault_passphrase)

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase-file",
                str(passphrase_file),
                "--json",
            ],
        )

        # Should succeed because file passphrase is correct
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"


class TestExitCodes:
    """Test exit code standardization (0=success, 1=error, 2=validation)."""

    def test_check_success_exit_0(self, png_image):
        """Successful check should exit 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["check", "-i", png_image])
        assert result.exit_code == 0

    def test_vault_get_decryption_error_exit_1(self, vault_image):
        """Decryption error should exit 1."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["vault", "get", vault_image, "-k", "test_key", "--passphrase", "wrongpass", "--json"],
        )
        assert result.exit_code == 1

    def test_vault_get_validation_error_exit_2(self, vault_image, vault_passphrase):
        """Validation error should exit 2."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "vault",
                "get",
                vault_image,
                "-k",
                "test_key",
                "--passphrase",
                vault_passphrase,
                "--clipboard-timeout",
                "-1",
                "--json",
            ],
        )
        assert result.exit_code == 2


# Fixtures
@pytest.fixture
def png_image(tmp_path):
    """Create a test PNG image."""
    from PIL import Image
    import numpy as np

    img_path = tmp_path / "test.png"
    img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, mode="RGB")
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def vault_passphrase():
    """Test vault passphrase."""
    return "TestPassphrase123!@#"


@pytest.fixture
def vault_image(png_image, vault_passphrase):
    """Create a test vault image with one entry."""
    from stegvault.vault import create_vault, add_entry, vault_to_json

    # Create vault
    vault = create_vault()
    add_entry(
        vault,
        key="test_key",
        password="test_password",
        username="testuser",
        url="https://example.com",
    )

    # Serialize
    vault_json = vault_to_json(vault)
    vault_bytes = vault_json.encode("utf-8")

    # Encrypt
    ciphertext, salt, nonce = encrypt_data(vault_bytes, vault_passphrase)
    payload = serialize_payload(salt, nonce, ciphertext)

    # Embed
    seed = int.from_bytes(salt[:4], byteorder="big")
    output_path = png_image.replace(".png", "_vault.png")
    embed_payload(png_image, payload, seed, output_path)

    return output_path
