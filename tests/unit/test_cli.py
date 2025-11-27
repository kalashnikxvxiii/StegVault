"""
Unit tests for CLI commands.
"""

import pytest
import tempfile
import os
from click.testing import CliRunner
from PIL import Image
import numpy as np

from stegvault.cli import main, backup, restore, check, config, batch_backup, batch_restore


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
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                "MySecretPassword123",
                "--passphrase",
                "StrongPassphrase!@#456",
                "--no-check-strength",
            ],
        )

        assert result.exit_code == 0
        assert "Backup created successfully" in result.output
        assert os.path.exists(temp_output)

    def test_backup_weak_passphrase_warning(self, runner, test_image, temp_output):
        """Should warn about weak passphrase."""
        result = runner.invoke(
            backup,
            [
                "--image",
                test_image,
                "--output",
                temp_output,
            ],
            input="MyPassword123\nMyPassword123\nweak\nweak\nn\n",  # Reject weak passphrase
        )

        assert result.exit_code == 0
        assert "Warning:" in result.output
        assert "Backup cancelled" in result.output

    def test_backup_weak_passphrase_accepted(self, runner, test_image, temp_output):
        """Should allow weak passphrase if user confirms."""
        result = runner.invoke(
            backup,
            [
                "--image",
                test_image,
                "--output",
                temp_output,
            ],
            input="MyPassword123\nMyPassword123\nshort\nshort\ny\n",  # Accept weak passphrase
        )

        assert result.exit_code == 0
        assert "Warning:" in result.output
        assert "Backup created successfully" in result.output

    def test_backup_image_not_found(self, runner, temp_output):
        """Should fail with non-existent image."""
        result = runner.invoke(
            backup,
            [
                "--image",
                "/nonexistent/image.png",
                "--output",
                temp_output,
                "--password",
                "MyPassword123",
                "--passphrase",
                "StrongPassphrase!@#456",
            ],
        )

        # Click uses exit code 2 for invalid input/file not found
        assert result.exit_code in (1, 2)
        assert "Error: Image file not found" in result.output or "does not exist" in result.output

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
                    "--image",
                    tiny_image,
                    "--output",
                    temp_output,
                    "--password",
                    long_password,
                    "--passphrase",
                    "StrongPassphrase!@#456",
                    "--no-check-strength",
                ],
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
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                "test",
                "--passphrase",
                "StrongPassphrase!@#456",
                "--no-check-strength",
            ],
        )

        assert result.exit_code == 0
        assert "IMPORTANT:" in result.output
        assert "Keep both the image AND passphrase safe" in result.output
        assert "Losing either means permanent data loss" in result.output

    def test_backup_with_invalid_config(self, runner, test_image, temp_output, monkeypatch):
        """Should fallback to default config when config file is invalid."""
        from stegvault.config import ConfigError

        # Mock load_config to raise ConfigError
        def mock_load_config():
            raise ConfigError("Invalid config file")

        monkeypatch.setattr("stegvault.cli.load_config", mock_load_config)

        # Should use default config and succeed
        result = runner.invoke(
            backup,
            [
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                "TestPassword123",
                "--passphrase",
                "StrongPassphrase!@#456",
                "--no-check-strength",
            ],
        )

        assert "Warning: Failed to load config" in result.output
        assert "Using default settings" in result.output
        assert result.exit_code == 0


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
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                password,
                "--passphrase",
                passphrase,
                "--no-check-strength",
            ],
        )
        assert backup_result.exit_code == 0

        # Now restore it
        restore_result = runner.invoke(
            restore,
            [
                "--image",
                temp_output,
                "--passphrase",
                passphrase,
            ],
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
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                "MyPassword",
                "--passphrase",
                "CorrectPassphrase123!",
                "--no-check-strength",
            ],
        )

        # Try to restore with wrong passphrase
        result = runner.invoke(
            restore,
            [
                "--image",
                temp_output,
                "--passphrase",
                "WrongPassphrase456!",
            ],
        )

        assert result.exit_code == 1
        assert "Decryption failed" in result.output
        assert "Wrong passphrase" in result.output

    def test_restore_image_not_found(self, runner):
        """Should fail with non-existent image."""
        result = runner.invoke(
            restore,
            [
                "--image",
                "/nonexistent/backup.png",
                "--passphrase",
                "SomePassphrase123",
            ],
        )

        # Click uses exit code 2 for invalid input/file not found
        assert result.exit_code in (1, 2)
        assert "Error: Image file not found" in result.output or "does not exist" in result.output

    def test_restore_to_file(self, runner, test_image, temp_output):
        """Should save restored password to file."""
        password = "SavedPassword123"
        passphrase = "StrongPassphrase!@#456"

        # Create backup
        runner.invoke(
            backup,
            [
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                password,
                "--passphrase",
                passphrase,
                "--no-check-strength",
            ],
        )

        # Restore to file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            output_file = tmp.name

        try:
            result = runner.invoke(
                restore,
                [
                    "--image",
                    temp_output,
                    "--passphrase",
                    passphrase,
                    "--output",
                    output_file,
                ],
            )

            assert result.exit_code == 0
            assert os.path.exists(output_file)

            with open(output_file, "r") as f:
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
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                password,
                "--passphrase",
                passphrase,
                "--no-check-strength",
            ],
        )
        assert backup_result.exit_code == 0

        # Restore
        restore_result = runner.invoke(
            restore,
            [
                "--image",
                temp_output,
                "--passphrase",
                passphrase,
            ],
        )

        assert restore_result.exit_code == 0
        assert password in restore_result.output

    def test_restore_corrupted_payload(self, runner, test_image, temp_output):
        """Should fail with corrupted payload format."""
        from stegvault.stego import embed_payload

        # Create a stego image with invalid payload format (wrong magic header)
        bad_payload = b"XXXX" + b"\x00" * 44  # Invalid magic header (not "SPW1")
        stego_img = embed_payload(test_image, bad_payload, seed=0)
        stego_img.save(temp_output)

        result = runner.invoke(
            restore,
            [
                "--image",
                temp_output,
                "--passphrase",
                "AnyPassphrase123!",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid or corrupted payload" in result.output

    def test_restore_extraction_error(self, runner, test_image):
        """Should fail with extraction error for non-stego image."""
        # Try to restore from plain image (no embedded data)
        result = runner.invoke(
            restore,
            [
                "--image",
                test_image,
                "--passphrase",
                "AnyPassphrase123!",
            ],
        )

        # Should fail during extraction
        assert result.exit_code == 1
        assert (
            "Invalid or corrupted payload" in result.output or "bad magic header" in result.output
        )

    def test_restore_parse_error(self, runner, test_image, temp_output):
        """Should fail when parse_payload fails."""
        from stegvault.stego import embed_payload
        from stegvault.utils import serialize_payload

        # Create a payload with invalid salt/nonce sizes (will fail parsing)
        bad_payload = b"SPW1" + b"\x00" * 10  # Too short for salt+nonce+length
        stego_img = embed_payload(test_image, bad_payload, seed=0)
        stego_img.save(temp_output)

        result = runner.invoke(
            restore,
            [
                "--image",
                temp_output,
                "--passphrase",
                "AnyPassphrase123!",
            ],
        )

        # Should fail during parsing
        assert result.exit_code == 1

    def test_restore_with_invalid_config(self, runner, test_image, temp_output, monkeypatch):
        """Should fallback to default config when config file is invalid."""
        from stegvault.config import ConfigError

        # Create a valid backup first
        password = "TestPassword123"
        passphrase = "TestPassphrase!@#456"
        runner.invoke(
            backup,
            [
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                password,
                "--passphrase",
                passphrase,
                "--no-check-strength",
            ],
        )

        # Mock load_config to raise ConfigError
        def mock_load_config():
            raise ConfigError("Invalid config file")

        monkeypatch.setattr("stegvault.cli.load_config", mock_load_config)

        # Should use default config and succeed
        result = runner.invoke(
            restore,
            [
                "--image",
                temp_output,
                "--passphrase",
                passphrase,
            ],
        )

        assert "Warning: Failed to load config" in result.output
        assert "Using default settings" in result.output
        assert result.exit_code == 0


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
        assert "Error: Image file not found" in result.output or "does not exist" in result.output

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
            assert (
                "Warning:" in result.output
                or "Note:" in result.output
                or "limited" in result.output.lower()
            )

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

    def test_check_medium_capacity_note(self, runner):
        """Should show note for medium-capacity images (100-500 bytes)."""
        # Create image with ~200 bytes capacity (26x26 RGB = 676 pixels * 3 / 8 = 253 bytes)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            medium_image = tmp.name
            img_array = np.random.randint(0, 256, (26, 26, 3), dtype=np.uint8)
            img = Image.fromarray(img_array, mode="RGB")
            img.save(medium_image, format="PNG")
            img.close()

        try:
            result = runner.invoke(check, ["--image", medium_image])

            assert result.exit_code == 0
            # Should show limited capacity note (100-500 bytes range)
            assert "Note:" in result.output or "limited" in result.output.lower()

        finally:
            try:
                os.unlink(medium_image)
            except (PermissionError, FileNotFoundError):
                pass


class TestMainCommand:
    """Tests for main CLI group."""

    def test_main_version(self, runner):
        """Should display version."""
        from stegvault import __version__

        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output

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
                "--image",
                test_image,
                "--output",
                temp_output,
                "--password",
                password,
                "--passphrase",
                passphrase,
                "--no-check-strength",
            ],
        )
        assert backup_result.exit_code == 0
        assert os.path.exists(temp_output)

        # Step 3: Restore password
        restore_result = runner.invoke(
            restore,
            [
                "--image",
                temp_output,
                "--passphrase",
                passphrase,
            ],
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
                        "--image",
                        test_img,
                        "--output",
                        backup_path,
                        "--password",
                        pwd,
                        "--passphrase",
                        passphrase,
                        "--no-check-strength",
                    ],
                )
                assert result.exit_code == 0

                backups.append((test_img, backup_path, pwd))

            # Restore all passwords and verify
            for test_img, backup_path, original_pwd in backups:
                restore_result = runner.invoke(
                    restore,
                    [
                        "--image",
                        backup_path,
                        "--passphrase",
                        passphrase,
                    ],
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
                    "--image",
                    test_image,
                    "--output",
                    temp_output,
                    "--password",
                    password,
                    "--passphrase",
                    passphrase,
                    "--no-check-strength",
                ],
            )

            if backup_result.exit_code == 0:
                # Restore
                restore_result = runner.invoke(
                    restore,
                    [
                        "--image",
                        temp_output,
                        "--passphrase",
                        passphrase,
                    ],
                )
                assert restore_result.exit_code == 0
                assert password in restore_result.output


class TestConfigCommand:
    """Tests for config commands."""

    def test_config_show_no_file(self, runner, monkeypatch, tmp_path):
        """Should show default settings when no config file exists."""
        # Mock config path to temp directory
        config_dir = tmp_path / "stegvault"
        config_path = config_dir / "config.toml"

        monkeypatch.setattr("stegvault.config.core.get_config_path", lambda: config_path)
        monkeypatch.setattr("stegvault.config.core.get_config_dir", lambda: config_dir)

        result = runner.invoke(config, ["show"])

        assert result.exit_code == 0
        assert "No configuration file found" in result.output
        assert "Using default settings" in result.output
        assert "[crypto]" in result.output
        assert "argon2_time_cost" in result.output

    def test_config_show_with_file(self, runner, monkeypatch, tmp_path):
        """Should display existing configuration."""
        from stegvault.config import save_config, get_default_config

        # Create config in temp directory
        config_dir = tmp_path / "stegvault"
        config_dir.mkdir()
        config_path = config_dir / "config.toml"

        monkeypatch.setattr("stegvault.config.core.get_config_path", lambda: config_path)
        monkeypatch.setattr("stegvault.config.core.get_config_dir", lambda: config_dir)

        cfg = get_default_config()
        save_config(cfg)

        result = runner.invoke(config, ["show"])

        assert result.exit_code == 0
        assert str(config_path) in result.output
        assert "[crypto]" in result.output
        assert "[cli]" in result.output

    def test_config_init_new_file(self, runner, monkeypatch, tmp_path):
        """Should create new configuration file."""
        config_dir = tmp_path / "stegvault"
        config_path = config_dir / "config.toml"

        monkeypatch.setattr("stegvault.config.core.get_config_path", lambda: config_path)
        monkeypatch.setattr("stegvault.config.core.get_config_dir", lambda: config_dir)

        result = runner.invoke(config, ["init"])

        assert result.exit_code == 0
        assert "Created configuration file" in result.output
        assert config_path.exists()

    def test_config_init_overwrite_existing(self, runner, monkeypatch, tmp_path):
        """Should prompt before overwriting existing config."""
        from stegvault.config import save_config, get_default_config

        config_dir = tmp_path / "stegvault"
        config_dir.mkdir()
        config_path = config_dir / "config.toml"

        monkeypatch.setattr("stegvault.config.core.get_config_path", lambda: config_path)
        monkeypatch.setattr("stegvault.config.core.get_config_dir", lambda: config_dir)

        # Create existing config
        cfg = get_default_config()
        save_config(cfg)

        # Cancel overwrite
        result = runner.invoke(config, ["init"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Confirm overwrite
        result = runner.invoke(config, ["init"], input="y\n")
        assert result.exit_code == 0
        assert "Created configuration file" in result.output

    def test_config_path_file_exists(self, runner, monkeypatch, tmp_path):
        """Should show config path when file exists."""
        from stegvault.config import save_config, get_default_config

        config_dir = tmp_path / "stegvault"
        config_dir.mkdir()
        config_path = config_dir / "config.toml"

        monkeypatch.setattr("stegvault.config.core.get_config_path", lambda: config_path)
        monkeypatch.setattr("stegvault.config.core.get_config_dir", lambda: config_dir)

        cfg = get_default_config()
        save_config(cfg)

        result = runner.invoke(config, ["path"])

        assert result.exit_code == 0
        assert str(config_dir) in result.output
        assert str(config_path) in result.output
        assert "File exists" in result.output

    def test_config_path_file_not_found(self, runner, monkeypatch, tmp_path):
        """Should show config path when file doesn't exist."""
        config_dir = tmp_path / "stegvault"
        config_path = config_dir / "config.toml"

        monkeypatch.setattr("stegvault.config.core.get_config_path", lambda: config_path)
        monkeypatch.setattr("stegvault.config.core.get_config_dir", lambda: config_dir)

        result = runner.invoke(config, ["path"])

        assert result.exit_code == 0
        assert str(config_dir) in result.output
        assert str(config_path) in result.output
        assert "File not found" in result.output
        assert "using defaults" in result.output.lower()


class TestBatchCommands:
    """Tests for batch commands."""

    def test_batch_backup_success(self, runner, test_image, tmp_path):
        """Should process multiple backups successfully."""
        import json

        # Create batch config
        output1 = tmp_path / "backup1.png"
        output2 = tmp_path / "backup2.png"

        config_data = {
            "passphrase": "TestPassphrase123!",
            "backups": [
                {
                    "password": "Password1",
                    "image": test_image,
                    "output": str(output1),
                    "label": "Backup 1",
                },
                {
                    "password": "Password2",
                    "image": test_image,
                    "output": str(output2),
                    "label": "Backup 2",
                },
            ],
        }

        config_file = tmp_path / "batch_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(batch_backup, ["--config", str(config_file)])

        assert result.exit_code == 0
        assert "2 backup job(s)" in result.output
        assert "Successful: 2" in result.output
        assert output1.exists()
        assert output2.exists()

    def test_batch_backup_no_jobs(self, runner, tmp_path):
        """Should error when no backup jobs in config."""
        import json

        config_data = {"passphrase": "TestPassphrase123!", "backups": []}

        config_file = tmp_path / "batch_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(batch_backup, ["--config", str(config_file)])

        assert result.exit_code == 1
        assert "No backup jobs found" in result.output

    def test_batch_backup_continue_on_error(self, runner, test_image, tmp_path):
        """Should continue processing after error by default."""
        import json

        output1 = tmp_path / "backup1.png"
        output2 = tmp_path / "backup2.png"

        config_data = {
            "passphrase": "TestPassphrase123!",
            "backups": [
                {
                    "password": "Password1",
                    "image": test_image,
                    "output": str(output1),
                    "label": "Backup 1",
                },
                {
                    "password": "Password2",
                    "image": "nonexistent.png",
                    "output": str(output2),
                    "label": "Backup 2",
                },
            ],
        }

        config_file = tmp_path / "batch_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(batch_backup, ["--config", str(config_file)])

        assert result.exit_code == 1  # Exit 1 when there are failures
        assert "Successful: 1" in result.output
        assert "Failed:" in result.output and "1" in result.output
        assert output1.exists()

    def test_batch_backup_stop_on_error(self, runner, test_image, tmp_path):
        """Should stop on first error when --stop-on-error flag used."""
        import json

        output1 = tmp_path / "backup1.png"
        output2 = tmp_path / "backup2.png"

        config_data = {
            "passphrase": "TestPassphrase123!",
            "backups": [
                {
                    "password": "Password1",
                    "image": "nonexistent.png",
                    "output": str(output1),
                    "label": "Backup 1",
                },
                {
                    "password": "Password2",
                    "image": test_image,
                    "output": str(output2),
                    "label": "Backup 2",
                },
            ],
        }

        config_file = tmp_path / "batch_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(batch_backup, ["--config", str(config_file), "--stop-on-error"])

        assert result.exit_code == 1  # Exit 1 when there are failures
        assert "Failed:" in result.output and "1" in result.output

    def test_batch_restore_success(self, runner, test_image, tmp_path):
        """Should restore multiple passwords successfully."""
        import json

        # First create backups
        from stegvault.crypto import encrypt_data
        from stegvault.stego import embed_payload
        from stegvault.utils import serialize_payload

        passphrase = "TestPassphrase123!"
        password1 = "Password1"
        password2 = "Password2"

        backup1 = tmp_path / "backup1.png"
        backup2 = tmp_path / "backup2.png"

        # Create backup 1
        ciphertext1, salt1, nonce1 = encrypt_data(password1.encode(), passphrase)
        payload1 = serialize_payload(salt1, nonce1, ciphertext1)
        seed1 = int.from_bytes(salt1[:4], byteorder="big")
        embed_payload(test_image, payload1, seed1, str(backup1))

        # Create backup 2
        ciphertext2, salt2, nonce2 = encrypt_data(password2.encode(), passphrase)
        payload2 = serialize_payload(salt2, nonce2, ciphertext2)
        seed2 = int.from_bytes(salt2[:4], byteorder="big")
        embed_payload(test_image, payload2, seed2, str(backup2))

        # Create restore config
        config_data = {
            "passphrase": passphrase,
            "restores": [
                {"image": str(backup1), "label": "Restore 1"},
                {"image": str(backup2), "label": "Restore 2"},
            ],
        }

        config_file = tmp_path / "restore_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(batch_restore, ["--config", str(config_file), "--show-passwords"])

        assert result.exit_code == 0
        assert "2 restore job(s)" in result.output
        assert "Successful: 2" in result.output
        assert password1 in result.output
        assert password2 in result.output

    def test_batch_restore_no_jobs(self, runner, tmp_path):
        """Should error when no restore jobs in config."""
        import json

        config_data = {"passphrase": "TestPassphrase123!", "restores": []}

        config_file = tmp_path / "restore_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(batch_restore, ["--config", str(config_file)])

        assert result.exit_code == 1
        assert "No restore jobs found" in result.output

    def test_batch_restore_wrong_passphrase(self, runner, test_image, tmp_path):
        """Should fail with wrong passphrase."""
        import json
        from stegvault.crypto import encrypt_data
        from stegvault.stego import embed_payload
        from stegvault.utils import serialize_payload

        # Create backup with one passphrase
        password = "Password1"
        passphrase = "CorrectPassphrase123!"
        backup = tmp_path / "backup.png"

        ciphertext, salt, nonce = encrypt_data(password.encode(), passphrase)
        payload = serialize_payload(salt, nonce, ciphertext)
        seed = int.from_bytes(salt[:4], byteorder="big")
        embed_payload(test_image, payload, seed, str(backup))

        # Try to restore with wrong passphrase
        config_data = {
            "passphrase": "WrongPassphrase123!",
            "restores": [{"image": str(backup), "label": "Restore 1"}],
        }

        config_file = tmp_path / "restore_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(batch_restore, ["--config", str(config_file)])

        assert result.exit_code == 1  # Exit 1 when there are failures
        assert "Failed:" in result.output and "1" in result.output
