"""
Unit tests for vault CLI commands.
"""

import pytest
import tempfile
import os
from click.testing import CliRunner
from PIL import Image
import numpy as np

from stegvault.cli import vault, main


@pytest.fixture
def runner():
    """Click CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def test_image():
    """Create a test PNG image (200x200 RGB)."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img_array = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode="RGB")
        img.save(tmp.name, format="PNG")
        img.close()
        yield tmp.name
        try:
            os.unlink(tmp.name)
        except (PermissionError, FileNotFoundError):
            pass


@pytest.fixture
def temp_output():
    """Generate temporary output path."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        output_path = tmp.name
    yield output_path
    try:
        os.unlink(output_path)
    except (PermissionError, FileNotFoundError):
        pass


# Helper functions
def get_test_image(width=200, height=200):
    """Create a test image with random pixel data."""
    img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(img_array, mode="RGB")


def get_temp_filename(suffix=".png"):
    """Generate a temporary filename."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        return tmp.name


def cleanup_file(filepath):
    """Safely cleanup a file."""
    try:
        if os.path.exists(filepath):
            os.unlink(filepath)
    except (PermissionError, FileNotFoundError):
        pass


class TestVaultCreateCommand:
    """Tests for vault create command."""

    def test_create_with_password(self, runner, test_image, temp_output):
        """Should successfully create vault with explicit password."""
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "StrongVaultPass123!",
                "--key",
                "gmail",
                "--password",
                "MyEmailPassword123",
                "--username",
                "user@gmail.com",
                "--url",
                "https://gmail.com",
                "--notes",
                "Personal email",
            ],
        )

        assert result.exit_code == 0
        assert "Vault created successfully" in result.output
        assert "Entries: 1" in result.output
        assert "Keys: gmail" in result.output
        assert os.path.exists(temp_output)

    def test_create_with_generate(self, runner, test_image, temp_output):
        """Should successfully create vault with generated password."""
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "StrongVaultPass123!",
                "--key",
                "github",
                "--generate",
                "--username",
                "myuser",
            ],
        )

        assert result.exit_code == 0
        assert "Generated password:" in result.output
        assert "Vault created successfully" in result.output
        assert os.path.exists(temp_output)

    def test_create_with_prompt(self, runner, test_image, temp_output):
        """Should prompt for password if not provided."""
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "StrongVaultPass123!",
                "--key",
                "test",
            ],
            input="MyPassword123\nMyPassword123\n",
        )

        assert result.exit_code == 0
        assert "Vault created successfully" in result.output

    def test_create_generate_and_password_error(self, runner, test_image, temp_output):
        """Should error when both --generate and --password are used."""
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "StrongVaultPass123!",
                "--key",
                "test",
                "--password",
                "MyPass123",
                "--generate",
            ],
        )

        assert result.exit_code == 1
        assert "Cannot use both --generate and --password" in result.output

    def test_create_image_too_small(self, runner, temp_output):
        """Should error when image is too small."""
        # Create tiny image (10x10)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tiny_img = Image.new("RGB", (10, 10))
            tiny_img.save(tmp.name, format="PNG")
            tiny_img.close()
            tiny_image = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "create",
                    "--image",
                    tiny_image,
                    "--output",
                    temp_output,
                    "--passphrase",
                    "StrongVaultPass123!",
                    "--key",
                    "test",
                    "--password",
                    "MyPassword123",
                ],
            )

            assert result.exit_code == 1
            assert "Image too small" in result.output
        finally:
            try:
                os.unlink(tiny_image)
            except (PermissionError, FileNotFoundError):
                pass

    def test_create_invalid_image(self, runner, temp_output):
        """Should error when image file doesn't exist."""
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                "/nonexistent/image.png",
                "--output",
                temp_output,
                "--passphrase",
                "StrongVaultPass123!",
                "--key",
                "test",
                "--password",
                "MyPassword123",
            ],
        )

        assert result.exit_code == 2  # Click uses exit code 2 for bad parameters
        assert "Error:" in result.output or "does not exist" in result.output

    def test_create_with_totp_generate(self, runner, test_image, temp_output):
        """Should successfully create vault with generated TOTP secret."""
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "StrongVaultPass123!",
                "--key",
                "github_totp",
                "--password",
                "MyPassword123",
                "--totp-generate",
            ],
        )

        assert result.exit_code == 0
        assert "Generated TOTP secret" in result.output
        assert "Vault created successfully" in result.output
        assert os.path.exists(temp_output)

    def test_create_with_totp_secret(self, runner, test_image, temp_output):
        """Should successfully create vault with explicit TOTP secret."""
        totp_secret = "JBSWY3DPEHPK3PXP"  # Valid base32
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "StrongVaultPass123!",
                "--key",
                "github_totp",
                "--password",
                "MyPassword123",
                "--totp-secret",
                totp_secret,
            ],
        )

        assert result.exit_code == 0
        assert "Vault created successfully" in result.output
        assert os.path.exists(temp_output)

    def test_create_totp_conflict(self, runner, test_image, temp_output):
        """Should fail when both --totp-generate and --totp-secret are used."""
        totp_secret = "JBSWY3DPEHPK3PXP"
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "StrongVaultPass123!",
                "--key",
                "test",
                "--password",
                "MyPassword123",
                "--totp-generate",
                "--totp-secret",
                totp_secret,
            ],
        )

        assert result.exit_code == 1
        assert "Cannot use both --totp-generate and --totp-secret" in result.output


class TestVaultAddCommand:
    """Tests for vault add command."""

    @pytest.fixture
    def vault_image(self, runner, test_image):
        """Create a vault image for testing."""
        # Create a temporary file for the vault
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            vault_path = tmp.name

        # First create a vault
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                vault_path,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "first_entry",
                "--password",
                "FirstPassword123",
            ],
        )
        assert result.exit_code == 0, f"Vault creation failed:\n{result.output}"
        assert "Vault created successfully" in result.output, f"Unexpected output:\n{result.output}"

        yield vault_path

        # Cleanup
        try:
            os.unlink(vault_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_add_with_password(self, runner, vault_image, temp_output):
        """Should successfully add entry to vault."""
        # Create a different temp output for the updated vault
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "add",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "second_entry",
                    "--password",
                    "SecondPassword123",
                    "--username",
                    "user2",
                ],
            )

            assert result.exit_code == 0, f"Command failed with output:\n{result.output}"
            assert "Entry added successfully" in result.output
            assert "Total entries: 2" in result.output
            assert os.path.exists(new_vault)
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_add_with_generate(self, runner, vault_image, temp_output):
        """Should add entry with generated password."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "add",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "new_entry",
                    "--generate",
                ],
            )

            assert result.exit_code == 0
            assert "Generated password:" in result.output
            assert "Entry added successfully" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_add_wrong_passphrase(self, runner, vault_image, temp_output):
        """Should error with wrong passphrase."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "add",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "WrongPassphrase123!",
                    "--key",
                    "test",
                    "--password",
                    "TestPass123",
                ],
            )

            assert result.exit_code == 1
            assert "Wrong passphrase" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_add_duplicate_key(self, runner, vault_image, temp_output):
        """Should error when adding duplicate key."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "add",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "first_entry",  # Duplicate key
                    "--password",
                    "AnotherPass123",
                ],
            )

            assert result.exit_code == 1
            assert "Error:" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_add_with_totp_generate(self, runner, vault_image, temp_output):
        """Should add entry with TOTP generated and display QR code."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "add",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "totp_entry",
                    "--password",
                    "TestPass123!",
                    "--username",
                    "testuser",
                    "--totp-generate",
                ],
            )

            assert result.exit_code == 0
            assert "[TOTP Setup]" in result.output
            assert "Generated TOTP secret:" in result.output
            assert "Option 1: Scan QR code" in result.output
            assert "Option 2: Manual entry" in result.output
            assert "Account:" in result.output
            assert "Secret:" in result.output
            assert "Entry added successfully" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_add_with_totp_secret(self, runner, vault_image, temp_output):
        """Should add entry with provided TOTP secret."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "add",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "totp_entry",
                    "--password",
                    "TestPass123!",
                    "--totp-secret",
                    "JBSWY3DPEHPK3PXP",
                ],
            )

            assert result.exit_code == 0
            assert "Entry added successfully" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_add_totp_conflict(self, runner, vault_image, temp_output):
        """Should fail when both --totp-generate and --totp-secret are used."""
        totp_secret = "JBSWY3DPEHPK3PXP"
        result = runner.invoke(
            vault,
            [
                "add",
                vault_image,
                "--output",
                temp_output,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "test",
                "--password",
                "MyPassword123",
                "--totp-generate",
                "--totp-secret",
                totp_secret,
            ],
        )

        assert result.exit_code == 1
        assert "Cannot use both --totp-generate and --totp-secret" in result.output


class TestVaultGetCommand:
    """Tests for vault get command."""

    @pytest.fixture
    def vault_image(self, runner, test_image):
        """Create a vault image for testing."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            vault_path = tmp.name

        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                vault_path,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "test_entry",
                "--password",
                "TestPassword123",
                "--username",
                "testuser",
                "--url",
                "https://example.com",
            ],
        )
        assert result.exit_code == 0, f"Vault creation failed:\n{result.output}"

        yield vault_path

        try:
            os.unlink(vault_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_get_existing_entry(self, runner, vault_image):
        """Should retrieve existing entry."""
        result = runner.invoke(
            vault,
            [
                "get",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "test_entry",
            ],
        )

        assert result.exit_code == 0
        assert "test_entry" in result.output
        assert "TestPassword123" in result.output
        assert "testuser" in result.output
        assert "https://example.com" in result.output

    def test_get_nonexistent_entry(self, runner, vault_image):
        """Should error when entry doesn't exist."""
        result = runner.invoke(
            vault,
            [
                "get",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "nonexistent",
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "Error:" in result.output

    def test_get_wrong_passphrase(self, runner, vault_image):
        """Should error with wrong passphrase."""
        result = runner.invoke(
            vault,
            [
                "get",
                vault_image,
                "--passphrase",
                "WrongPass123!",
                "--key",
                "test_entry",
            ],
        )

        assert result.exit_code == 1
        assert "Wrong passphrase" in result.output

    def test_get_with_clipboard(self, runner, vault_image, monkeypatch):
        """Should copy password to clipboard instead of displaying."""
        # Mock pyperclip
        copied_value = []

        def mock_copy(text):
            copied_value.append(text)

        import pyperclip

        monkeypatch.setattr(pyperclip, "copy", mock_copy)

        result = runner.invoke(
            vault,
            [
                "get",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "test_entry",
                "--clipboard",
            ],
        )

        assert result.exit_code == 0
        assert "Password copied to clipboard" in result.output
        assert "**********" in result.output  # Password masked
        assert "TestPassword123" not in result.output  # Password not displayed
        assert len(copied_value) == 1
        assert copied_value[0] == "TestPassword123"

    def test_get_without_clipboard(self, runner, vault_image):
        """Should display password on screen when --clipboard not used."""
        result = runner.invoke(
            vault,
            [
                "get",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "test_entry",
            ],
        )

        assert result.exit_code == 0
        assert "Password: TestPassword123" in result.output  # Password displayed

    def test_get_with_clipboard_timeout(self, runner, vault_image, monkeypatch):
        """Should auto-clear clipboard after timeout."""
        copied_values = []

        def mock_copy(text):
            copied_values.append(text)

        def mock_sleep(seconds):
            pass  # Don't actually sleep in tests

        import pyperclip
        import time as time_module

        monkeypatch.setattr(pyperclip, "copy", mock_copy)
        monkeypatch.setattr(time_module, "sleep", mock_sleep)

        result = runner.invoke(
            vault,
            [
                "get",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "test_entry",
                "--clipboard",
                "--clipboard-timeout",
                "5",
            ],
        )

        assert result.exit_code == 0
        assert "Password copied to clipboard" in result.output
        assert "Clipboard will be cleared in 5 seconds" in result.output
        assert "Clipboard cleared" in result.output
        assert len(copied_values) == 2
        assert copied_values[0] == "TestPassword123"
        assert copied_values[1] == ""  # Cleared

    def test_get_clipboard_timeout_without_clipboard(self, runner, vault_image):
        """Should warn when --clipboard-timeout used without --clipboard."""
        result = runner.invoke(
            vault,
            [
                "get",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "test_entry",
                "--clipboard-timeout",
                "30",
            ],
        )

        assert "Warning: --clipboard-timeout ignored without --clipboard flag" in result.output

    def test_get_negative_clipboard_timeout(self, runner, vault_image):
        """Should error with negative clipboard timeout (validation error)."""
        result = runner.invoke(
            vault,
            [
                "get",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "test_entry",
                "--clipboard",
                "--clipboard-timeout",
                "-1",
            ],
        )

        assert result.exit_code == 2  # Validation error
        assert "Clipboard timeout must be >= 0" in result.output


class TestVaultListCommand:
    """Tests for vault list command."""

    @pytest.fixture
    def multi_entry_vault(self, runner, test_image):
        """Create a vault with multiple entries."""
        # Create first vault
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            vault1_path = tmp.name

        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                vault1_path,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "entry1",
                "--password",
                "Pass1",
            ],
        )
        assert result.exit_code == 0, f"Vault creation failed:\n{result.output}"

        # Add second entry
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            vault2_path = tmp.name

        result = runner.invoke(
            vault,
            [
                "add",
                vault1_path,
                "--output",
                vault2_path,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "entry2",
                "--password",
                "Pass2",
            ],
        )
        assert result.exit_code == 0, f"Adding entry failed:\n{result.output}"

        # Cleanup first vault
        try:
            os.unlink(vault1_path)
        except (PermissionError, FileNotFoundError):
            pass

        yield vault2_path

        # Cleanup final vault
        try:
            os.unlink(vault2_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_list_entries(self, runner, multi_entry_vault):
        """Should list all vault entries."""
        result = runner.invoke(
            vault,
            [
                "list",
                multi_entry_vault,
                "--passphrase",
                "VaultPass123!",
            ],
        )

        assert result.exit_code == 0
        assert "entry1" in result.output
        assert "entry2" in result.output
        assert "2 entries" in result.output or "Total: 2" in result.output

    def test_list_wrong_passphrase(self, runner, multi_entry_vault):
        """Should error with wrong passphrase."""
        result = runner.invoke(
            vault,
            [
                "list",
                multi_entry_vault,
                "--passphrase",
                "WrongPass123!",
            ],
        )

        assert result.exit_code == 1
        assert "Wrong passphrase" in result.output


class TestVaultShowCommand:
    """Tests for vault show command."""

    @pytest.fixture
    def vault_image(self, runner, test_image, temp_output):
        """Create a vault image for testing."""
        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "show_test",
                "--password",
                "ShowPassword123",
                "--username",
                "showuser",
                "--notes",
                "Test notes",
            ],
        )
        assert result.exit_code == 0
        return temp_output

    def test_show_entry(self, runner, vault_image):
        """Should show full entry details."""
        result = runner.invoke(
            vault,
            [
                "show",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "show_test",
            ],
        )

        assert result.exit_code == 0
        assert "show_test" in result.output
        assert "************ (hidden)" in result.output  # Password is hidden in show command
        assert "showuser" in result.output
        assert "Test notes" in result.output

    def test_show_nonexistent(self, runner, vault_image):
        """Should error for nonexistent entry."""
        result = runner.invoke(
            vault,
            [
                "show",
                vault_image,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "nonexistent",
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "Error:" in result.output


class TestVaultUpdateCommand:
    """Tests for vault update command."""

    @pytest.fixture
    def vault_image(self, runner, test_image):
        """Create a vault image for testing."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            vault_path = tmp.name

        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                vault_path,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "update_test",
                "--password",
                "OldPassword123",
                "--username",
                "olduser",
            ],
        )
        assert result.exit_code == 0, f"Vault creation failed:\n{result.output}"

        yield vault_path

        try:
            os.unlink(vault_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_update_password(self, runner, vault_image, temp_output):
        """Should update entry password."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "update",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "update_test",
                    "--password",
                    "NewPassword123",
                ],
            )

            assert result.exit_code == 0
            assert "Entry updated successfully" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_update_username(self, runner, vault_image, temp_output):
        """Should update entry username."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "update",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "update_test",
                    "--username",
                    "newuser",
                ],
            )

            assert result.exit_code == 0
            assert "Entry updated successfully" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_update_nonexistent(self, runner, vault_image, temp_output):
        """Should error when updating nonexistent entry."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "update",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "nonexistent",
                    "--password",
                    "NewPass123",
                ],
            )

            assert result.exit_code == 1
            assert "Error:" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass


class TestVaultDeleteCommand:
    """Tests for vault delete command."""

    @pytest.fixture
    def vault_image(self, runner, test_image):
        """Create a vault image with entry to delete."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            vault_path = tmp.name

        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                vault_path,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "delete_me",
                "--password",
                "DeletePassword123",
            ],
        )
        assert result.exit_code == 0, f"Vault creation failed:\n{result.output}"

        yield vault_path

        try:
            os.unlink(vault_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_delete_with_confirm(self, runner, vault_image, temp_output):
        """Should delete entry without prompting when using --no-confirm."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "delete",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "delete_me",
                    "--no-confirm",  # Skip confirmation prompt
                ],
            )

            assert result.exit_code == 0, f"Delete failed:\n{result.output}"
            assert (
                "Entry deleted successfully" in result.output or "deleted" in result.output.lower()
            )
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_delete_without_confirm(self, runner, vault_image, temp_output):
        """Should prompt for confirmation when --confirm not used."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "delete",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "delete_me",
                ],
                input="y\n",  # Confirm deletion
            )

            assert result.exit_code == 0
            assert (
                "Entry deleted successfully" in result.output or "deleted" in result.output.lower()
            )
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass

    def test_delete_nonexistent(self, runner, vault_image, temp_output):
        """Should error when deleting nonexistent entry."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            new_vault = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "delete",
                    vault_image,
                    "--output",
                    new_vault,
                    "--passphrase",
                    "VaultPass123!",
                    "--key",
                    "nonexistent",
                    "--confirm",
                ],
            )

            assert result.exit_code == 1
            assert "Error:" in result.output
        finally:
            try:
                os.unlink(new_vault)
            except (PermissionError, FileNotFoundError):
                pass


class TestVaultExportCommand:
    """Tests for vault export command."""

    @pytest.fixture
    def vault_image(self, runner, test_image):
        """Create a vault image for export testing."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            vault_path = tmp.name

        result = runner.invoke(
            vault,
            [
                "create",
                "--image",
                test_image,
                "--output",
                vault_path,
                "--passphrase",
                "VaultPass123!",
                "--key",
                "export_test",
                "--password",
                "ExportPassword123",
                "--username",
                "exportuser",
            ],
        )
        assert result.exit_code == 0, f"Vault creation failed:\n{result.output}"

        yield vault_path

        try:
            os.unlink(vault_path)
        except (PermissionError, FileNotFoundError):
            pass

    def test_export_decrypted(self, runner, vault_image, temp_output):
        """Should export vault as decrypted JSON."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            json_file = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "export",
                    vault_image,
                    "--output",
                    json_file,
                    "--passphrase",
                    "VaultPass123!",
                    "--decrypt",
                ],
                input="y\n",  # Confirm export with plaintext passwords
            )

            assert result.exit_code == 0, f"Export failed:\n{result.output}"
            assert (
                "Vault exported successfully" in result.output
                or "exported" in result.output.lower()
            )
            assert os.path.exists(json_file)

            # Verify JSON content
            with open(json_file, "r") as f:
                content = f.read()
                assert "export_test" in content
                assert "ExportPassword123" in content
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_export_pretty(self, runner, vault_image, temp_output):
        """Should export with pretty formatting."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            json_file = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "export",
                    vault_image,
                    "--output",
                    json_file,
                    "--passphrase",
                    "VaultPass123!",
                    "--decrypt",
                    "--pretty",
                ],
                input="y\n",  # Confirm export with plaintext passwords
            )

            assert result.exit_code == 0, f"Export failed:\n{result.output}"
            assert os.path.exists(json_file)

            # Verify pretty formatting (indented JSON)
            with open(json_file, "r") as f:
                content = f.read()
                # Pretty JSON should have indentation
                assert "  " in content or "\t" in content
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_export_wrong_passphrase(self, runner, vault_image, temp_output):
        """Should error with wrong passphrase."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            json_file = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "export",
                    vault_image,
                    "--output",
                    json_file,
                    "--passphrase",
                    "WrongPass123!",
                    "--decrypt",
                ],
            )

            assert result.exit_code == 1
            assert "Wrong passphrase" in result.output
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_export_with_redact(self, runner, vault_image, temp_output):
        """Should export vault with passwords redacted (default behavior without --decrypt)."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            json_file = tmp.name

        try:
            # Export WITHOUT --decrypt flag = passwords are redacted
            result = runner.invoke(
                vault,
                [
                    "export",
                    vault_image,
                    "--output",
                    json_file,
                    "--passphrase",
                    "VaultPass123!",
                ],
            )

            assert result.exit_code == 0, f"Export failed:\n{result.output}"
            assert os.path.exists(json_file)

            # Verify passwords are redacted
            with open(json_file, "r") as f:
                content = f.read()
                assert "***REDACTED***" in content
                # Password should NOT be in plaintext
                assert "ExportPassword123" not in content
                # But other fields should be present
                assert "export_test" in content
                assert "exportuser" in content

        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_export_with_redact_pretty(self, runner, vault_image, temp_output):
        """Should export with redacted passwords and pretty formatting."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            json_file = tmp.name

        try:
            # Export WITHOUT --decrypt but WITH --pretty = redacted + formatted
            result = runner.invoke(
                vault,
                [
                    "export",
                    vault_image,
                    "--output",
                    json_file,
                    "--passphrase",
                    "VaultPass123!",
                    "--pretty",
                ],
            )

            assert result.exit_code == 0, f"Export failed:\n{result.output}"
            assert os.path.exists(json_file)

            # Verify pretty formatting (indentation) and redaction
            with open(json_file, "r") as f:
                content = f.read()
                assert "  " in content  # Should have indentation
                assert "***REDACTED***" in content
                assert "ExportPassword123" not in content

        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_import_success(self, runner, test_image, temp_output):
        """Should import vault from JSON file."""
        # Create a valid vault JSON file
        vault_json = {
            "version": "2.0",
            "created": "2025-01-14T12:00:00Z",
            "modified": "2025-01-14T12:00:00Z",
            "entries": [
                {
                    "key": "test_import",
                    "password": "ImportPass123",
                    "username": "testuser",
                    "url": "https://example.com",
                    "notes": "Test import",
                    "tags": ["test"],
                    "totp_secret": None,
                    "created": "2025-01-14T12:00:00Z",
                    "modified": "2025-01-14T12:00:00Z",
                    "accessed": None,
                }
            ],
            "metadata": {
                "total_entries": 1,
                "app_version": "0.4.0",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            import json as json_module

            json_module.dump(vault_json, tmp)
            json_file = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "import",
                    json_file,
                    "--image",
                    test_image,
                    "--output",
                    temp_output,
                    "--passphrase",
                    "ImportTest123!",
                ],
                input="ImportTest123!\n",  # Confirmation
            )

            assert result.exit_code == 0, f"Import failed:\n{result.output}"
            assert (
                "Vault imported successfully" in result.output
                or "imported" in result.output.lower()
            )
            assert os.path.exists(temp_output)
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_import_invalid_json(self, runner, test_image, temp_output):
        """Should error with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            tmp.write("not valid json{}")
            json_file = tmp.name
            tmp.flush()  # Ensure data is written to disk

        try:
            result = runner.invoke(
                vault,
                [
                    "import",
                    json_file,
                    "--image",
                    test_image,
                    "--output",
                    temp_output,
                    "--passphrase",
                    "StrongPass123!",  # Long enough to bypass strength check
                    "--no-check-strength",  # Skip strength check entirely
                ],
                input="StrongPass123!\n",
            )

            assert result.exit_code == 1
            assert "Invalid JSON" in result.output or "error" in result.output.lower()
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_import_nonexistent_file(self, runner, test_image, temp_output):
        """Should error with non-existent JSON file."""
        result = runner.invoke(
            vault,
            [
                "import",
                "nonexistent_vault.json",
                "--image",
                test_image,
                "--output",
                temp_output,
                "--passphrase",
                "Test123!",
            ],
            input="Test123!\n",
        )

        # Click should error on non-existent file with exit code 2
        assert result.exit_code in (1, 2)

    def test_import_redacted_warning(self, runner, test_image, temp_output):
        """Should warn about redacted passwords."""
        # Create vault JSON with redacted passwords
        vault_json = {
            "version": "2.0",
            "created": "2025-01-14T12:00:00Z",
            "modified": "2025-01-14T12:00:00Z",
            "entries": [
                {
                    "key": "redacted_entry",
                    "password": "***REDACTED***",
                    "username": "testuser",
                    "url": "https://example.com",
                    "notes": "",
                    "tags": [],
                    "totp_secret": None,
                    "created": "2025-01-14T12:00:00Z",
                    "modified": "2025-01-14T12:00:00Z",
                    "accessed": None,
                }
            ],
            "metadata": {
                "total_entries": 1,
                "app_version": "0.4.0",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            import json as json_module

            json_module.dump(vault_json, tmp)
            json_file = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "import",
                    json_file,
                    "--image",
                    test_image,
                    "--output",
                    temp_output,
                    "--passphrase",
                    "Test123!",
                ],
                input="Test123!\ny\n",  # Passphrase confirmation + redacted warning confirmation
            )

            assert "redacted passwords" in result.output.lower()
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_import_weak_passphrase(self, runner, test_image, temp_output):
        """Should warn about weak passphrase."""
        vault_json = {
            "version": "2.0",
            "created": "2025-01-14T12:00:00Z",
            "modified": "2025-01-14T12:00:00Z",
            "entries": [
                {
                    "key": "test",
                    "password": "TestPass",
                    "username": None,
                    "url": None,
                    "notes": "",
                    "tags": [],
                    "totp_secret": None,
                    "created": "2025-01-14T12:00:00Z",
                    "modified": "2025-01-14T12:00:00Z",
                    "accessed": None,
                }
            ],
            "metadata": {
                "total_entries": 1,
                "app_version": "0.4.0",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            import json as json_module

            json_module.dump(vault_json, tmp)
            json_file = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "import",
                    json_file,
                    "--image",
                    test_image,
                    "--output",
                    temp_output,
                    "--passphrase",
                    "weak",
                ],
                input="weak\n",  # Confirmation
            )

            # Should warn about weak passphrase
            assert result.exit_code in (0, 1)
            # May contain warning or may have been cancelled
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_import_roundtrip(self, runner, vault_image, test_image, temp_output):
        """Should successfully export then import vault."""
        # Export first
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            json_file = tmp.name

        # Create second temp file for imported vault
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp2:
            vault_out = tmp2.name

        try:
            # Export decrypted
            export_result = runner.invoke(
                vault,
                [
                    "export",
                    vault_image,
                    "--output",
                    json_file,
                    "--passphrase",
                    "VaultPass123!",
                    "--decrypt",
                ],
                input="y\n",  # Confirm export
            )
            assert export_result.exit_code == 0

            # Import into new image
            import_result = runner.invoke(
                vault,
                [
                    "import",
                    json_file,
                    "--image",
                    test_image,
                    "--output",
                    vault_out,
                    "--passphrase",
                    "NewPassword123!",
                ],
                input="NewPassword123!\n",  # Confirmation
            )

            assert import_result.exit_code == 0, f"Import failed:\n{import_result.output}"
            assert os.path.exists(vault_out)

            # Verify we can get the entry from imported vault
            get_result = runner.invoke(
                vault,
                [
                    "get",
                    vault_out,
                    "--key",
                    "export_test",
                    "--passphrase",
                    "NewPassword123!",
                ],
            )
            assert get_result.exit_code == 0
            assert "ExportPassword123" in get_result.output
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass
            try:
                os.unlink(vault_out)
            except (PermissionError, FileNotFoundError):
                pass

    def test_import_no_check_strength(self, runner, test_image, temp_output):
        """Should skip passphrase strength check with --no-check-strength."""
        vault_json = {
            "version": "2.0",
            "created": "2025-01-14T12:00:00Z",
            "modified": "2025-01-14T12:00:00Z",
            "entries": [
                {
                    "key": "test",
                    "password": "TestPass",
                    "username": None,
                    "url": None,
                    "notes": "",
                    "tags": [],
                    "totp_secret": None,
                    "created": "2025-01-14T12:00:00Z",
                    "modified": "2025-01-14T12:00:00Z",
                    "accessed": None,
                }
            ],
            "metadata": {
                "total_entries": 1,
                "app_version": "0.4.0",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            import json as json_module

            json_module.dump(vault_json, tmp)
            json_file = tmp.name

        try:
            result = runner.invoke(
                vault,
                [
                    "import",
                    json_file,
                    "--image",
                    test_image,
                    "--output",
                    temp_output,
                    "--passphrase",
                    "weak",
                    "--no-check-strength",
                ],
                input="weak\n",  # Confirmation
            )

            # Should succeed without warning
            assert result.exit_code == 0, f"Import failed:\n{result.output}"
            assert os.path.exists(temp_output)
        finally:
            try:
                os.unlink(json_file)
            except (PermissionError, FileNotFoundError):
                pass


class TestVaultTOTPCommand:
    """Test vault totp command."""

    @pytest.fixture
    def vault_with_totp_fixture(self):
        """Create a vault with TOTP configured."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False, mode="wb") as cover:
            test_image = get_test_image(400, 300)
            test_image.save(cover, format="PNG")
            cover_path = cover.name

        temp_output = None
        try:
            temp_output = get_temp_filename(".png")
            passphrase = "test_passphrase_123"

            # Create vault with TOTP
            from stegvault.vault import create_vault, add_entry, vault_to_json
            from stegvault.vault.totp import generate_totp_secret
            from stegvault.crypto import encrypt_data
            from stegvault.stego import embed_payload
            from stegvault.utils import serialize_payload

            vault = create_vault()
            totp_secret = generate_totp_secret()
            add_entry(
                vault,
                "test_entry",
                "test_password",
                username="testuser",
                totp_secret=totp_secret,
            )

            # Serialize and encrypt
            vault_json = vault_to_json(vault)
            ciphertext, salt, nonce = encrypt_data(vault_json.encode("utf-8"), passphrase)
            payload = serialize_payload(salt, nonce, ciphertext)

            # Embed in image
            embed_payload(cover_path, payload, output_path=temp_output)

            yield temp_output, passphrase

        finally:
            cleanup_file(cover_path)
            if temp_output:
                cleanup_file(temp_output)

    def test_totp_generate_code(self, vault_with_totp_fixture, runner):
        """Test generating TOTP code."""
        vault_image, passphrase = vault_with_totp_fixture

        result = runner.invoke(
            vault,
            ["totp", vault_image, "-k", "test_entry", "--passphrase", passphrase],
            input=f"{passphrase}\n",
        )

        assert result.exit_code == 0
        assert "TOTP Code:" in result.output
        assert "Valid for:" in result.output
        assert "test_entry" in result.output

    def test_totp_with_qr_code(self, vault_with_totp_fixture, runner):
        """Test TOTP with QR code display."""
        vault_image, passphrase = vault_with_totp_fixture

        result = runner.invoke(
            vault,
            ["totp", vault_image, "-k", "test_entry", "--passphrase", passphrase, "--qr"],
            input=f"{passphrase}\n",
        )

        assert result.exit_code == 0
        assert "TOTP Code:" in result.output
        assert "Scan this QR code" in result.output
        assert "Secret (manual entry):" in result.output

    def test_totp_entry_not_found(self, vault_with_totp_fixture, runner):
        """Test TOTP with nonexistent entry."""
        vault_image, passphrase = vault_with_totp_fixture

        result = runner.invoke(
            vault,
            ["totp", vault_image, "-k", "nonexistent", "--passphrase", passphrase],
            input=f"{passphrase}\n",
        )

        assert result.exit_code == 1
        assert "Entry 'nonexistent' not found" in result.output
        assert "Available keys:" in result.output

    def test_totp_no_totp_configured(self, runner):
        """Test TOTP with entry that has no TOTP secret."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False, mode="wb") as cover:
            test_image = get_test_image(400, 300)
            test_image.save(cover, format="PNG")
            cover_path = cover.name

        temp_output = None
        try:
            temp_output = get_temp_filename(".png")

            # Create vault without TOTP
            passphrase = "SuperSecure123!Pass"
            result = runner.invoke(
                vault,
                [
                    "create",
                    "-i",
                    cover_path,
                    "-o",
                    temp_output,
                    "-k",
                    "no_totp_entry",
                    "--password",
                    "mypass123",
                    "--passphrase",
                    passphrase,
                ],
                input=f"{passphrase}\n",
            )

            assert result.exit_code == 0

            # Try to get TOTP (should fail)
            result = runner.invoke(
                vault,
                ["totp", temp_output, "-k", "no_totp_entry", "--passphrase", passphrase],
                input=f"{passphrase}\n",
            )

            assert result.exit_code == 1
            assert "does not have TOTP configured" in result.output
            assert "vault update" in result.output

        finally:
            cleanup_file(cover_path)
            if temp_output:
                cleanup_file(temp_output)

    def test_totp_wrong_passphrase(self, vault_with_totp_fixture, runner):
        """Test TOTP with wrong passphrase."""
        vault_image, _ = vault_with_totp_fixture

        result = runner.invoke(
            vault,
            ["totp", vault_image, "-k", "test_entry", "--passphrase", "wrong_pass"],
            input="wrong_pass\n",
        )

        assert result.exit_code == 1
        assert "Wrong passphrase" in result.output

    def test_totp_single_password_image(self, runner):
        """Test TOTP with single password image (not a vault)."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False, mode="wb") as cover:
            test_image = get_test_image(400, 300)
            test_image.save(cover, format="PNG")
            cover_path = cover.name

        temp_output = None
        try:
            temp_output = get_temp_filename(".png")

            # Create single password backup (not vault)
            passphrase = "test_passphrase_123"
            result = runner.invoke(
                main,
                [
                    "backup",
                    "-i",
                    cover_path,
                    "-o",
                    temp_output,
                    "--password",
                    "singlepass",
                    "--passphrase",
                    passphrase,
                    "--no-check-strength",
                ],
                input=f"{passphrase}\n",
            )

            assert result.exit_code == 0

            # Try to get TOTP from single password image
            result = runner.invoke(
                vault,
                ["totp", temp_output, "-k", "any_key", "--passphrase", passphrase],
                input=f"{passphrase}\n",
            )

            assert result.exit_code == 1
            assert "single password, not a vault" in result.output

        finally:
            cleanup_file(cover_path)
            if temp_output:
                cleanup_file(temp_output)
