"""
Unit tests for CLI commands.
"""

import pytest
import tempfile
import os
from click.testing import CliRunner
from PIL import Image
import numpy as np

from stegvault.cli import main, backup, restore, check


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


class TestBackupCommand:
    """Tests for backup command."""

    def test_backup_success(self, runner, test_image, temp_output):
        """Should successfully create backup."""
        result = runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
                "--password", "MySecretPassword123",
                "--passphrase", "StrongPassphrase!@#456",
                "--no-check-strength"
            ]
        )

        assert result.exit_code == 0
        assert "Backup created successfully" in result.output
        assert os.path.exists(temp_output)

    def test_backup_weak_passphrase_warning(self, runner, test_image, temp_output):
        """Should warn about weak passphrase."""
        result = runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
            ],
            input="MyPassword123\nMyPassword123\nweak\nweak\nn\n"  # Reject weak passphrase
        )

        assert result.exit_code == 0
        assert "Warning:" in result.output
        assert "Backup cancelled" in result.output

    def test_backup_weak_passphrase_accepted(self, runner, test_image, temp_output):
        """Should allow weak passphrase if user confirms."""
        result = runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
            ],
            input="MyPassword123\nMyPassword123\nshort\nshort\ny\n"  # Accept weak passphrase
        )

        assert result.exit_code == 0
        assert "Warning:" in result.output
        assert "Backup created successfully" in result.output

    def test_backup_image_not_found(self, runner, temp_output):
        """Should fail with non-existent image."""
        result = runner.invoke(
            backup,
            [
                "--image", "/nonexistent/image.png",
                "--output", temp_output,
                "--password", "MyPassword123",
                "--passphrase", "StrongPassphrase!@#456",
            ]
        )

        # Click uses exit code 2 for invalid input/file not found
        assert result.exit_code in (1, 2)
        assert ("Error: Image file not found" in result.output or
                "does not exist" in result.output)

    def test_backup_image_too_small(self, runner, temp_output):
        """Should fail if image capacity is insufficient."""
        # Create tiny image (5x5 = 25 pixels, capacity ~9 bytes)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tiny_image = tmp.name
            img_array = np.random.randint(0, 256, (5, 5, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tiny_image, format="PNG")
            img.close()

        try:
            # Long password that won't fit
            long_password = "x" * 100
            result = runner.invoke(
                backup,
                [
                    "--image", tiny_image,
                    "--output", temp_output,
                    "--password", long_password,
                    "--passphrase", "StrongPassphrase!@#456",
                    "--no-check-strength"
                ]
            )

            assert result.exit_code == 1
            assert "Error: Image too small" in result.output

        finally:
            try:
                os.unlink(tiny_image)
            except (PermissionError, FileNotFoundError):
                pass

    def test_backup_displays_important_warnings(self, runner, test_image, temp_output):
        """Should display important security warnings."""
        result = runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
                "--password", "test",
                "--passphrase", "StrongPassphrase!@#456",
                "--no-check-strength"
            ]
        )

        assert result.exit_code == 0
        assert "IMPORTANT:" in result.output
        assert "Keep both the image AND passphrase safe" in result.output
        assert "Losing either means permanent data loss" in result.output


class TestRestoreCommand:
    """Tests for restore command."""

    def test_restore_success(self, runner, test_image, temp_output):
        """Should successfully restore password."""
        # First create a backup
        password = "MySecretPassword123"
        passphrase = "StrongPassphrase!@#456"

        backup_result = runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
                "--password", password,
                "--passphrase", passphrase,
                "--no-check-strength"
            ]
        )
        assert backup_result.exit_code == 0

        # Now restore it
        restore_result = runner.invoke(
            restore,
            [
                "--image", temp_output,
                "--passphrase", passphrase,
            ]
        )

        assert restore_result.exit_code == 0
        assert password in restore_result.output
        assert "Password recovered successfully" in restore_result.output

    def test_restore_wrong_passphrase(self, runner, test_image, temp_output):
        """Should fail with wrong passphrase."""
        # Create backup
        runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
                "--password", "MyPassword",
                "--passphrase", "CorrectPassphrase123!",
                "--no-check-strength"
            ]
        )

        # Try to restore with wrong passphrase
        result = runner.invoke(
            restore,
            [
                "--image", temp_output,
                "--passphrase", "WrongPassphrase456!",
            ]
        )

        assert result.exit_code == 1
        assert "Decryption failed" in result.output
        assert "Wrong passphrase" in result.output

    def test_restore_image_not_found(self, runner):
        """Should fail with non-existent image."""
        result = runner.invoke(
            restore,
            [
                "--image", "/nonexistent/backup.png",
                "--passphrase", "SomePassphrase123",
            ]
        )

        # Click uses exit code 2 for invalid input/file not found
        assert result.exit_code in (1, 2)
        assert ("Error: Image file not found" in result.output or
                "does not exist" in result.output)

    def test_restore_to_file(self, runner, test_image, temp_output):
        """Should save restored password to file."""
        password = "SavedPassword123"
        passphrase = "StrongPassphrase!@#456"

        # Create backup
        runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
                "--password", password,
                "--passphrase", passphrase,
                "--no-check-strength"
            ]
        )

        # Restore to file
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as tmp:
            output_file = tmp.name

        try:
            result = runner.invoke(
                restore,
                [
                    "--image", temp_output,
                    "--passphrase", passphrase,
                    "--output", output_file,
                ]
            )

            assert result.exit_code == 0
            assert os.path.exists(output_file)

            with open(output_file, 'r') as f:
                saved_password = f.read().strip()

            assert saved_password == password

        finally:
            try:
                os.unlink(output_file)
            except (PermissionError, FileNotFoundError):
                pass

    def test_restore_unicode_password(self, runner, test_image, temp_output):
        """Should handle unicode passwords."""
        password = "密码Test🔐"
        passphrase = "StrongPassphrase!@#456"

        # Create backup
        backup_result = runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
                "--password", password,
                "--passphrase", passphrase,
                "--no-check-strength"
            ]
        )
        assert backup_result.exit_code == 0

        # Restore
        restore_result = runner.invoke(
            restore,
            [
                "--image", temp_output,
                "--passphrase", passphrase,
            ]
        )

        assert restore_result.exit_code == 0
        assert password in restore_result.output


class TestCheckCommand:
    """Tests for check command."""

    def test_check_valid_image(self, runner, test_image):
        """Should display image capacity information."""
        result = runner.invoke(check, ["--image", test_image])

        assert result.exit_code == 0
        assert "Image:" in result.output
        assert "Format: PNG" in result.output
        assert "Mode: RGB" in result.output
        assert "Size: 200x200 pixels" in result.output
        assert "Capacity:" in result.output
        assert "bytes" in result.output
        assert "sufficient capacity" in result.output

    def test_check_image_not_found(self, runner):
        """Should fail with non-existent image."""
        result = runner.invoke(check, ["--image", "/nonexistent/image.png"])

        # Click uses exit code 2 for invalid input/file not found
        assert result.exit_code in (1, 2)
        assert ("Error: Image file not found" in result.output or
                "does not exist" in result.output)

    def test_check_small_image_warning(self, runner):
        """Should warn for very small images."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tiny_image = tmp.name
            img_array = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(tiny_image, format="PNG")
            img.close()

        try:
            result = runner.invoke(check, ["--image", tiny_image])

            assert result.exit_code == 0
            # Should show small capacity warning
            assert ("Warning:" in result.output or "Note:" in result.output or
                    "limited" in result.output.lower())

        finally:
            try:
                os.unlink(tiny_image)
            except (PermissionError, FileNotFoundError):
                pass

    def test_check_unsupported_mode(self, runner):
        """Should fail for unsupported image modes."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            gray_image = tmp.name
            # Create grayscale image
            img_array = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="L")
            img.save(gray_image, format="PNG")
            img.close()

        try:
            result = runner.invoke(check, ["--image", gray_image])

            assert result.exit_code == 1
            assert "Unsupported mode" in result.output or "Warning:" in result.output

        finally:
            try:
                os.unlink(gray_image)
            except (PermissionError, FileNotFoundError):
                pass


class TestMainCommand:
    """Tests for main CLI group."""

    def test_main_version(self, runner):
        """Should display version."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_main_help(self, runner):
        """Should display help message."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "StegVault" in result.output
        assert "backup" in result.output
        assert "restore" in result.output
        assert "check" in result.output


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    def test_complete_backup_restore_cycle(self, runner, test_image, temp_output):
        """Should complete full backup and restore workflow."""
        password = "MyCompletePassword!@#123"
        passphrase = "VeryStrongPassphrase!@#456XYZ"

        # Step 1: Check image capacity
        check_result = runner.invoke(check, ["--image", test_image])
        assert check_result.exit_code == 0
        assert "sufficient capacity" in check_result.output

        # Step 2: Create backup
        backup_result = runner.invoke(
            backup,
            [
                "--image", test_image,
                "--output", temp_output,
                "--password", password,
                "--passphrase", passphrase,
                "--no-check-strength"
            ]
        )
        assert backup_result.exit_code == 0
        assert os.path.exists(temp_output)

        # Step 3: Restore password
        restore_result = runner.invoke(
            restore,
            [
                "--image", temp_output,
                "--passphrase", passphrase,
            ]
        )
        assert restore_result.exit_code == 0
        assert password in restore_result.output

    def test_multiple_backups_different_images(self, runner):
        """Should handle multiple backups with different images."""
        passwords = [
            "Password1!@#",
            "Password2!@#",
            "Password3!@#",
        ]
        passphrase = "CommonPassphrase!@#456"

        backups = []

        try:
            for i, pwd in enumerate(passwords):
                # Create test image
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    test_img = tmp.name
                    img_array = np.random.randint(0, 256, (150, 150, 3), dtype=np.uint8)
                    img = Image.fromarray(img_array, mode="RGB")
                    img.save(test_img, format="PNG")
                    img.close()

                # Create backup
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    backup_path = tmp.name

                result = runner.invoke(
                    backup,
                    [
                        "--image", test_img,
                        "--output", backup_path,
                        "--password", pwd,
                        "--passphrase", passphrase,
                        "--no-check-strength"
                    ]
                )
                assert result.exit_code == 0

                backups.append((test_img, backup_path, pwd))

            # Restore all passwords and verify
            for test_img, backup_path, original_pwd in backups:
                restore_result = runner.invoke(
                    restore,
                    [
                        "--image", backup_path,
                        "--passphrase", passphrase,
                    ]
                )
                assert restore_result.exit_code == 0
                assert original_pwd in restore_result.output

        finally:
            # Cleanup
            for test_img, backup_path, _ in backups:
                try:
                    os.unlink(test_img)
                    os.unlink(backup_path)
                except (PermissionError, FileNotFoundError):
                    pass

    def test_backup_restore_edge_cases(self, runner, test_image, temp_output):
        """Should handle edge cases: empty password, special characters."""
        test_cases = [
            ("", "EmptyPassword"),
            ("SingleChar", "Single"),
            ("Special!@#$%^&*()_+-=[]{}|;:',.<>?/~`", "SpecialChars"),
            ("\n\r\t", "Whitespace"),
        ]

        for password, description in test_cases:
            passphrase = f"Passphrase{description}!@#456"

            # Backup
            backup_result = runner.invoke(
                backup,
                [
                    "--image", test_image,
                    "--output", temp_output,
                    "--password", password,
                    "--passphrase", passphrase,
                    "--no-check-strength"
                ]
            )

            if backup_result.exit_code == 0:
                # Restore
                restore_result = runner.invoke(
                    restore,
                    [
                        "--image", temp_output,
                        "--passphrase", passphrase,
                    ]
                )
                assert restore_result.exit_code == 0
                assert password in restore_result.output
