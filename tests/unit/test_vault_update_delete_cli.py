"""
Unit tests for vault update and delete CLI commands.
"""

import pytest
import tempfile
import os
from click.testing import CliRunner
from PIL import Image
import numpy as np

from stegvault.cli import vault as vault_cli


@pytest.fixture
def runner():
    """Click CLI runner for testing."""
    return CliRunner()


def get_test_image(width=400, height=300):
    """Create a test image with random pixel data."""
    img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(img_array, mode="RGB")


def cleanup_file(filepath):
    """Safely cleanup a file."""
    try:
        if os.path.exists(filepath):
            os.unlink(filepath)
    except (PermissionError, FileNotFoundError):
        pass


@pytest.fixture
def test_vault_image():
    """Create a test vault with a single entry."""
    from stegvault.vault import create_vault, add_entry, vault_to_json
    from stegvault.crypto import encrypt_data
    from stegvault.stego import embed_payload
    from stegvault.utils import serialize_payload

    cover_path = None
    temp_output = None
    try:
        # Create cover image
        cover_path = tempfile.mktemp(suffix=".png")
        test_image = get_test_image(600, 400)
        test_image.save(cover_path, format="PNG")

        # Create vault with one entry
        temp_output = tempfile.mktemp(suffix=".png")
        passphrase = "TestVault123!Pass"

        vault_obj = create_vault()
        add_entry(
            vault_obj,
            "test_entry",
            "original_password",
            username="testuser",
            url="https://example.com",
            notes="Test notes",
            tags=["test", "example"],
        )

        # Encrypt and embed
        vault_json = vault_to_json(vault_obj)
        ciphertext, salt, nonce = encrypt_data(vault_json.encode("utf-8"), passphrase)
        payload = serialize_payload(salt, nonce, ciphertext)
        embed_payload(cover_path, payload, output_path=temp_output)

        yield temp_output, passphrase, cover_path

    finally:
        if cover_path:
            cleanup_file(cover_path)
        if temp_output:
            cleanup_file(temp_output)


class TestVaultUpdateCLI:
    """Test vault update CLI command."""

    def test_update_password(self, test_vault_image, runner):
        """Test updating password for an entry."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--password",
                    "NewPassword123!",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 0
            assert "Updating entry 'test_entry'" in result.output
            assert os.path.exists(output_path)

        finally:
            cleanup_file(output_path)

    def test_update_username(self, test_vault_image, runner):
        """Test updating username for an entry."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--username",
                    "newuser",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 0
            assert "Updating entry 'test_entry'" in result.output

        finally:
            cleanup_file(output_path)

    def test_update_url_and_notes(self, test_vault_image, runner):
        """Test updating URL and notes for an entry."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--url",
                    "https://newurl.com",
                    "--notes",
                    "Updated notes",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 0

        finally:
            cleanup_file(output_path)

    def test_update_totp_generate(self, test_vault_image, runner):
        """Test generating TOTP secret during update."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--totp-generate",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 0
            assert "Generated TOTP secret:" in result.output
            assert "Scan this QR code" in result.output

        finally:
            cleanup_file(output_path)

    def test_update_totp_secret(self, test_vault_image, runner):
        """Test setting TOTP secret during update."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--totp-secret",
                    "JBSWY3DPEHPK3PXP",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 0

        finally:
            cleanup_file(output_path)

    def test_update_totp_remove(self, test_vault_image, runner):
        """Test removing TOTP secret during update."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--totp-remove",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 0

        finally:
            cleanup_file(output_path)

    def test_update_entry_not_found(self, test_vault_image, runner):
        """Test updating non-existent entry."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "nonexistent",
                    "--password",
                    "NewPass123!",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 1
            assert "Entry 'nonexistent' not found" in result.output

        finally:
            cleanup_file(output_path)

    def test_update_wrong_passphrase(self, test_vault_image, runner):
        """Test update with wrong passphrase."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--password",
                    "NewPass123!",
                    "--passphrase",
                    "wrongpass",
                ],
            )

            assert result.exit_code == 1

        finally:
            cleanup_file(output_path)

    def test_update_multiple_totp_flags(self, test_vault_image, runner):
        """Test update fails with multiple TOTP flags."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--totp-generate",
                    "--totp-remove",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 1
            assert "Only one of --totp-secret, --totp-generate, or --totp-remove" in result.output

        finally:
            cleanup_file(output_path)

    def test_update_no_fields_specified(self, test_vault_image, runner):
        """Test update fails when no fields are specified."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "update",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--passphrase",
                    passphrase,
                ],
            )

            assert result.exit_code == 1
            assert "At least one field must be specified" in result.output

        finally:
            cleanup_file(output_path)


class TestVaultDeleteCLI:
    """Test vault delete CLI command."""

    def test_delete_entry(self, test_vault_image, runner):
        """Test deleting an entry."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "delete",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--passphrase",
                    passphrase,
                ],
                input="y\n",  # Confirm deletion
            )

            assert result.exit_code == 0, f"Delete failed:\n{result.output}"
            assert "Entry deleted successfully" in result.output
            assert os.path.exists(output_path)

        finally:
            cleanup_file(output_path)

    def test_delete_cancelled(self, test_vault_image, runner):
        """Test cancelling deletion."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "delete",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--passphrase",
                    passphrase,
                ],
                input="n\n",  # Cancel deletion
            )

            assert result.exit_code == 0  # Cancellation exits with 0
            assert "Deletion cancelled" in result.output

        finally:
            cleanup_file(output_path)

    def test_delete_entry_not_found(self, test_vault_image, runner):
        """Test deleting non-existent entry."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "delete",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "nonexistent",
                    "--passphrase",
                    passphrase,
                ],
                input="y\n",  # Confirm deletion
            )

            assert result.exit_code == 1
            assert "Entry 'nonexistent' not found" in result.output

        finally:
            cleanup_file(output_path)

    def test_delete_wrong_passphrase(self, test_vault_image, runner):
        """Test delete with wrong passphrase."""
        vault_image, passphrase, cover_path = test_vault_image
        output_path = tempfile.mktemp(suffix=".png")

        try:
            result = runner.invoke(
                vault_cli,
                [
                    "delete",
                    vault_image,
                    "-o",
                    output_path,
                    "-k",
                    "test_entry",
                    "--passphrase",
                    "wrongpass",
                ],
            )

            assert result.exit_code == 1

        finally:
            cleanup_file(output_path)
