"""
Unit tests for batch operations module.
"""

import pytest
import tempfile
import json
import os
from PIL import Image
import numpy as np

from stegvault.batch.core import (
    load_batch_config,
    process_batch_backup,
    process_batch_restore,
    BatchError,
    BackupJob,
    RestoreJob,
    BatchConfig,
)


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
def test_image_small():
    """Create a small test PNG image (10x10 RGB) - insufficient capacity."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img_array = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode="RGB")
        img.save(tmp.name, format="PNG")
        img.close()
        yield tmp.name
        try:
            os.unlink(tmp.name)
        except (PermissionError, FileNotFoundError):
            pass


@pytest.fixture
def valid_batch_config(test_image):
    """Create a valid batch configuration JSON file."""
    config_data = {
        "passphrase": "TestPassphrase123!",
        "backups": [
            {
                "password": "Password1",
                "image": test_image,
                "output": tempfile.mktemp(suffix=".png"),
                "label": "Test Backup 1",
            },
            {
                "password": "Password2",
                "image": test_image,
                "output": tempfile.mktemp(suffix=".png"),
                "label": "Test Backup 2",
            },
        ],
        "restores": [],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(config_data, tmp)
        config_path = tmp.name

    yield config_path, config_data

    # Cleanup
    try:
        os.unlink(config_path)
        for job in config_data["backups"]:
            if os.path.exists(job["output"]):
                os.unlink(job["output"])
    except (PermissionError, FileNotFoundError):
        pass


class TestBatchConfigLoading:
    """Tests for batch configuration loading."""

    def test_load_valid_config(self, valid_batch_config):
        """Should successfully load valid configuration."""
        config_path, config_data = valid_batch_config

        batch_config = load_batch_config(config_path)

        assert batch_config.passphrase == config_data["passphrase"]
        assert len(batch_config.backup_jobs) == 2
        assert batch_config.backup_jobs[0].password == "Password1"
        assert batch_config.backup_jobs[0].label == "Test Backup 1"

    def test_load_nonexistent_file(self):
        """Should raise BatchError for nonexistent file."""
        with pytest.raises(BatchError, match="Config file not found"):
            load_batch_config("/nonexistent/config.json")

    def test_load_invalid_json(self):
        """Should raise BatchError for invalid JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write("{ invalid json }")
            config_path = tmp.name

        try:
            with pytest.raises(BatchError, match="Invalid JSON format"):
                load_batch_config(config_path)
        finally:
            try:
                os.unlink(config_path)
            except OSError:
                pass

    def test_load_missing_passphrase(self, test_image):
        """Should raise BatchError when passphrase is missing."""
        config_data = {
            "backups": [
                {
                    "password": "Password1",
                    "image": test_image,
                    "output": "output.png",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(config_data, tmp)
            config_path = tmp.name

        try:
            with pytest.raises(BatchError, match="Missing required field: passphrase"):
                load_batch_config(config_path)
        finally:
            try:
                os.unlink(config_path)
            except OSError:
                pass

    def test_load_missing_backup_field(self, test_image):
        """Should raise BatchError when backup job has missing field."""
        config_data = {
            "passphrase": "TestPass123",
            "backups": [
                {
                    "password": "Password1",
                    # Missing 'image' field
                    "output": "output.png",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(config_data, tmp)
            config_path = tmp.name

        try:
            with pytest.raises(BatchError, match="Missing required field"):
                load_batch_config(config_path)
        finally:
            try:
                os.unlink(config_path)
            except OSError:
                pass

    def test_load_empty_backup_and_restore(self):
        """Should successfully load config with no jobs."""
        config_data = {"passphrase": "TestPass123", "backups": [], "restores": []}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(config_data, tmp)
            config_path = tmp.name

        try:
            batch_config = load_batch_config(config_path)
            assert len(batch_config.backup_jobs) == 0
            assert len(batch_config.restore_jobs) == 0
        finally:
            try:
                os.unlink(config_path)
            except OSError:
                pass

    def test_load_config_with_restore_jobs(self, test_image):
        """Should successfully load config with restore jobs."""
        config_data = {
            "passphrase": "TestPass123",
            "backups": [],
            "restores": [
                {
                    "image": test_image,
                    "output": "restored1.txt",
                    "label": "Restore Job 1",
                },
                {
                    "image": test_image,
                    "label": "Restore Job 2",
                    # No output specified
                },
            ],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(config_data, tmp)
            config_path = tmp.name

        try:
            batch_config = load_batch_config(config_path)
            assert len(batch_config.restore_jobs) == 2
            assert batch_config.restore_jobs[0].image == test_image
            assert batch_config.restore_jobs[0].output == "restored1.txt"
            assert batch_config.restore_jobs[0].label == "Restore Job 1"
            assert batch_config.restore_jobs[1].output is None
        finally:
            try:
                os.unlink(config_path)
            except OSError:
                pass


class TestBatchBackup:
    """Tests for batch backup operations."""

    def test_batch_backup_success(self, test_image):
        """Should successfully process multiple backups."""
        output1 = tempfile.mktemp(suffix=".png")
        output2 = tempfile.mktemp(suffix=".png")

        config = BatchConfig(
            passphrase="TestPass123!",
            backup_jobs=[
                BackupJob("Password1", test_image, output1, "Job 1"),
                BackupJob("Password2", test_image, output2, "Job 2"),
            ],
            restore_jobs=[],
        )

        try:
            successful, failed, errors = process_batch_backup(config, stop_on_error=False)

            assert successful == 2
            assert failed == 0
            assert len(errors) == 0
            assert os.path.exists(output1)
            assert os.path.exists(output2)

        finally:
            for path in [output1, output2]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_backup_with_progress_callback(self, test_image):
        """Should call progress callback during backup."""
        output = tempfile.mktemp(suffix=".png")
        progress_calls = []

        def progress_callback(current, total, label):
            progress_calls.append((current, total, label))

        config = BatchConfig(
            passphrase="TestPass123!",
            backup_jobs=[BackupJob("Password1", test_image, output, "Test Job")],
            restore_jobs=[],
        )

        try:
            process_batch_backup(config, progress_callback=progress_callback, stop_on_error=False)

            assert len(progress_calls) == 1
            assert progress_calls[0] == (1, 1, "Test Job")

        finally:
            try:
                if os.path.exists(output):
                    os.unlink(output)
            except OSError:
                pass

    def test_batch_backup_continue_on_error(self, test_image):
        """Should continue processing after error when stop_on_error=False."""
        output1 = tempfile.mktemp(suffix=".png")
        output2 = tempfile.mktemp(suffix=".png")

        config = BatchConfig(
            passphrase="TestPass123!",
            backup_jobs=[
                BackupJob("Password1", test_image, output1, "Job 1"),
                BackupJob("Password2", "/nonexistent/image.png", output2, "Job 2"),
                BackupJob("Password3", test_image, output1, "Job 3"),  # Reuse output1
            ],
            restore_jobs=[],
        )

        try:
            successful, failed, errors = process_batch_backup(config, stop_on_error=False)

            # Job 1 succeeds, Job 2 fails (missing image), Job 3 succeeds
            assert successful == 2
            assert failed == 1
            assert len(errors) == 1
            assert "Job 2" in errors[0]

        finally:
            try:
                if os.path.exists(output1):
                    os.unlink(output1)
            except OSError:
                pass

    def test_batch_backup_stop_on_error(self, test_image):
        """Should stop processing after first error when stop_on_error=True."""
        output1 = tempfile.mktemp(suffix=".png")
        output2 = tempfile.mktemp(suffix=".png")
        output3 = tempfile.mktemp(suffix=".png")

        config = BatchConfig(
            passphrase="TestPass123!",
            backup_jobs=[
                BackupJob("Password1", test_image, output1, "Job 1"),
                BackupJob("Password2", "/nonexistent/image.png", output2, "Job 2"),
                BackupJob("Password3", test_image, output3, "Job 3"),
            ],
            restore_jobs=[],
        )

        try:
            successful, failed, errors = process_batch_backup(config, stop_on_error=True)

            # Job 1 succeeds, Job 2 fails and stops, Job 3 never runs
            assert successful == 1
            assert failed == 1
            assert len(errors) == 1
            assert not os.path.exists(output3)  # Job 3 didn't run

        finally:
            for path in [output1, output2, output3]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_backup_insufficient_capacity(self, test_image_small):
        """Should fail when image capacity is insufficient."""
        output = tempfile.mktemp(suffix=".png")

        config = BatchConfig(
            passphrase="TestPass123!",
            backup_jobs=[
                BackupJob(
                    "VeryLongPasswordThatWontFitInSmallImage" * 10,
                    test_image_small,
                    output,
                    "Job 1",
                )
            ],
            restore_jobs=[],
        )

        try:
            successful, failed, errors = process_batch_backup(config, stop_on_error=False)

            assert successful == 0
            assert failed == 1
            assert len(errors) == 1
            assert "too small" in errors[0].lower()

        finally:
            try:
                if os.path.exists(output):
                    os.unlink(output)
            except OSError:
                pass

    def test_batch_backup_with_invalid_config(self, test_image, monkeypatch):
        """Should use default config when config file is invalid."""
        from stegvault.config import ConfigError

        output = tempfile.mktemp(suffix=".png")

        # Mock load_config to raise ConfigError
        def mock_load_config():
            raise ConfigError("Invalid config file")

        monkeypatch.setattr("stegvault.batch.core.load_config", mock_load_config)

        config = BatchConfig(
            passphrase="TestPass123!",
            backup_jobs=[BackupJob("Password1", test_image, output, "Job 1")],
            restore_jobs=[],
        )

        try:
            # Should use default config and succeed
            successful, failed, errors = process_batch_backup(config, stop_on_error=False)

            assert successful == 1
            assert failed == 0
            assert os.path.exists(output)

        finally:
            try:
                if os.path.exists(output):
                    os.unlink(output)
            except OSError:
                pass


class TestBatchRestore:
    """Tests for batch restore operations."""

    def test_batch_restore_success(self, test_image):
        """Should successfully process multiple restores."""
        # First create backups
        backup1 = tempfile.mktemp(suffix=".png")
        backup2 = tempfile.mktemp(suffix=".png")
        output1 = tempfile.mktemp(suffix=".txt")
        output2 = tempfile.mktemp(suffix=".txt")

        passphrase = "TestPass123!"
        password1 = "Password1"
        password2 = "Password2"

        # Create backups
        backup_config = BatchConfig(
            passphrase=passphrase,
            backup_jobs=[
                BackupJob(password1, test_image, backup1, "Backup 1"),
                BackupJob(password2, test_image, backup2, "Backup 2"),
            ],
            restore_jobs=[],
        )

        process_batch_backup(backup_config, stop_on_error=False)

        try:
            # Now restore
            restore_config = BatchConfig(
                passphrase=passphrase,
                backup_jobs=[],
                restore_jobs=[
                    RestoreJob(backup1, output1, "Restore 1"),
                    RestoreJob(backup2, output2, "Restore 2"),
                ],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, stop_on_error=False
            )

            assert successful == 2
            assert failed == 0
            assert len(errors) == 0
            assert recovered["Restore 1"] == password1
            assert recovered["Restore 2"] == password2

            # Verify files were created
            assert os.path.exists(output1)
            assert os.path.exists(output2)

            with open(output1, "r", encoding="utf-8") as f:
                assert f.read() == password1

        finally:
            for path in [backup1, backup2, output1, output2]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_restore_wrong_passphrase(self, test_image):
        """Should fail restore with wrong passphrase."""
        backup = tempfile.mktemp(suffix=".png")
        output = tempfile.mktemp(suffix=".txt")

        # Create backup
        backup_config = BatchConfig(
            passphrase="CorrectPass123!",
            backup_jobs=[BackupJob("Password1", test_image, backup, "Backup 1")],
            restore_jobs=[],
        )

        process_batch_backup(backup_config, stop_on_error=False)

        try:
            # Try to restore with wrong passphrase
            restore_config = BatchConfig(
                passphrase="WrongPass123!",
                backup_jobs=[],
                restore_jobs=[RestoreJob(backup, output, "Restore 1")],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, stop_on_error=False
            )

            assert successful == 0
            assert failed == 1
            assert len(errors) == 1
            assert len(recovered) == 0

        finally:
            for path in [backup, output]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_restore_continue_on_error(self, test_image):
        """Should continue processing after error when stop_on_error=False."""
        backup1 = tempfile.mktemp(suffix=".png")
        output1 = tempfile.mktemp(suffix=".txt")
        output2 = tempfile.mktemp(suffix=".txt")

        passphrase = "TestPass123!"

        # Create one valid backup
        backup_config = BatchConfig(
            passphrase=passphrase,
            backup_jobs=[BackupJob("Password1", test_image, backup1, "Backup 1")],
            restore_jobs=[],
        )

        process_batch_backup(backup_config, stop_on_error=False)

        try:
            # Try to restore: one valid, one invalid image
            restore_config = BatchConfig(
                passphrase=passphrase,
                backup_jobs=[],
                restore_jobs=[
                    RestoreJob(backup1, output1, "Restore 1"),
                    RestoreJob("/nonexistent/backup.png", output2, "Restore 2"),
                ],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, stop_on_error=False
            )

            assert successful == 1
            assert failed == 1
            assert len(errors) == 1
            assert "Restore 2" in errors[0]
            assert len(recovered) == 1

        finally:
            for path in [backup1, output1, output2]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_restore_without_output_file(self, test_image):
        """Should restore successfully without creating output file."""
        backup = tempfile.mktemp(suffix=".png")
        passphrase = "TestPass123!"
        password = "Password1"

        # Create backup
        backup_config = BatchConfig(
            passphrase=passphrase,
            backup_jobs=[BackupJob(password, test_image, backup, "Backup 1")],
            restore_jobs=[],
        )

        process_batch_backup(backup_config, stop_on_error=False)

        try:
            # Restore without output file (output=None)
            restore_config = BatchConfig(
                passphrase=passphrase,
                backup_jobs=[],
                restore_jobs=[RestoreJob(backup, output=None, label="Restore 1")],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, stop_on_error=False
            )

            assert successful == 1
            assert failed == 0
            assert recovered["Restore 1"] == password

        finally:
            try:
                if os.path.exists(backup):
                    os.unlink(backup)
            except OSError:
                pass

    def test_batch_restore_corrupted_payload(self, test_image):
        """Should fail restore with corrupted payload."""
        from stegvault.stego import embed_payload

        backup = tempfile.mktemp(suffix=".png")
        output = tempfile.mktemp(suffix=".txt")

        try:
            # Create image with corrupted payload (invalid magic header)
            bad_payload = b"XXXX" + b"\x00" * 44  # Invalid magic
            stego_img = embed_payload(test_image, bad_payload, seed=0)
            stego_img.save(backup)

            # Try to restore
            restore_config = BatchConfig(
                passphrase="TestPass123!",
                backup_jobs=[],
                restore_jobs=[RestoreJob(backup, output, "Restore 1")],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, stop_on_error=False
            )

            assert successful == 0
            assert failed == 1
            assert len(errors) == 1

        finally:
            for path in [backup, output]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_restore_with_invalid_config(self, test_image, monkeypatch):
        """Should use default config when config file is invalid."""
        from stegvault.config import ConfigError

        backup = tempfile.mktemp(suffix=".png")
        output = tempfile.mktemp(suffix=".txt")
        passphrase = "TestPass123!"
        password = "Password1"

        # Create backup
        backup_config = BatchConfig(
            passphrase=passphrase,
            backup_jobs=[BackupJob(password, test_image, backup, "Backup 1")],
            restore_jobs=[],
        )

        process_batch_backup(backup_config, stop_on_error=False)

        try:
            # Mock load_config to raise ConfigError
            def mock_load_config():
                raise ConfigError("Invalid config file")

            monkeypatch.setattr("stegvault.batch.core.load_config", mock_load_config)

            # Restore with mocked config (should use default)
            restore_config = BatchConfig(
                passphrase=passphrase,
                backup_jobs=[],
                restore_jobs=[RestoreJob(backup, output, "Restore 1")],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, stop_on_error=False
            )

            assert successful == 1
            assert failed == 0
            assert recovered["Restore 1"] == password

        finally:
            for path in [backup, output]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_restore_with_progress_callback(self, test_image):
        """Should call progress callback during restore."""
        from stegvault.batch.core import BackupJob

        backup = tempfile.mktemp(suffix=".png")
        output = tempfile.mktemp(suffix=".txt")
        passphrase = "TestPass123!"
        password = "Password1"
        progress_calls = []

        def progress_callback(current, total, label):
            progress_calls.append((current, total, label))

        # Create backup first
        backup_config = BatchConfig(
            passphrase=passphrase,
            backup_jobs=[BackupJob(password, test_image, backup, "Backup 1")],
            restore_jobs=[],
        )
        process_batch_backup(backup_config, stop_on_error=False)

        try:
            # Restore with progress callback
            restore_config = BatchConfig(
                passphrase=passphrase,
                backup_jobs=[],
                restore_jobs=[RestoreJob(backup, output, "Restore 1")],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, progress_callback=progress_callback, stop_on_error=False
            )

            assert successful == 1
            assert len(progress_calls) == 1
            assert progress_calls[0] == (1, 1, "Restore 1")

        finally:
            for path in [backup, output]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_restore_stop_on_error_with_break(self, test_image):
        """Should stop and break when stop_on_error=True."""
        from stegvault.batch.core import BackupJob

        backup1 = tempfile.mktemp(suffix=".png")
        backup2 = tempfile.mktemp(suffix=".png")
        output1 = tempfile.mktemp(suffix=".txt")
        output2 = tempfile.mktemp(suffix=".txt")
        passphrase = "TestPass123!"

        # Create one valid backup
        backup_config = BatchConfig(
            passphrase=passphrase,
            backup_jobs=[BackupJob("Password1", test_image, backup1, "Backup 1")],
            restore_jobs=[],
        )
        process_batch_backup(backup_config, stop_on_error=False)

        try:
            # Try to restore: one non-existent, one valid (should not run)
            restore_config = BatchConfig(
                passphrase=passphrase,
                backup_jobs=[],
                restore_jobs=[
                    RestoreJob("/nonexistent/image.png", output1, "Restore 1"),
                    RestoreJob(backup1, output2, "Restore 2"),  # Won't run
                ],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, stop_on_error=True  # Stop on first error
            )

            assert successful == 0
            assert failed == 1
            assert len(errors) == 1
            assert "Restore 1" in errors[0]
            # Second restore should not run (break triggered)
            assert "Restore 2" not in " ".join(errors)

        finally:
            for path in [backup1, backup2, output1, output2]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass

    def test_batch_restore_payload_exceeds_capacity(self, test_image):
        """Should fail restore when payload size exceeds image capacity."""
        from stegvault.stego import embed_payload
        from stegvault.crypto.core import generate_salt, generate_nonce
        import struct

        backup = tempfile.mktemp(suffix=".png")
        output = tempfile.mktemp(suffix=".txt")
        passphrase = "TestPass123!"

        try:
            # Create a malicious payload with fake oversized ct_length
            # Header format: [Magic:4][Salt:16][Nonce:24][Length:4][Ciphertext][Tag:16]
            magic = b"SPW1"
            salt = generate_salt()  # 16 bytes
            nonce = generate_nonce()  # 24 bytes

            # Set ct_length to a huge value (will exceed capacity)
            fake_ct_length = 999999999  # Ridiculously large
            ct_length_bytes = struct.pack(">I", fake_ct_length)

            # Create minimal ciphertext + tag (just to have valid structure initially)
            fake_ciphertext = b"A" * 32  # 32 bytes fake data

            # Build malicious payload
            malicious_payload = magic + salt + nonce + ct_length_bytes + fake_ciphertext

            # Embed into image
            stego_img = embed_payload(test_image, malicious_payload, seed=0)
            stego_img.save(backup)

            # Try to restore - should fail with capacity error
            restore_config = BatchConfig(
                passphrase=passphrase,
                backup_jobs=[],
                restore_jobs=[RestoreJob(backup, output, "Restore 1")],
            )

            successful, failed, errors, recovered = process_batch_restore(
                restore_config, stop_on_error=False
            )

            assert successful == 0
            assert failed == 1
            assert len(errors) == 1
            assert (
                "exceeds image capacity" in errors[0].lower() or "payload size" in errors[0].lower()
            )

        finally:
            for path in [backup, output]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass


class TestDataclasses:
    """Tests for dataclass structures."""

    def test_backup_job_creation(self):
        """Should create BackupJob with all fields."""
        job = BackupJob("password", "input.png", "output.png", "Test Label")
        assert job.password == "password"
        assert job.image == "input.png"
        assert job.output == "output.png"
        assert job.label == "Test Label"

    def test_backup_job_without_label(self):
        """Should create BackupJob without label."""
        job = BackupJob("password", "input.png", "output.png")
        assert job.label is None

    def test_restore_job_creation(self):
        """Should create RestoreJob with all fields."""
        job = RestoreJob("input.png", "output.txt", "Test Label")
        assert job.image == "input.png"
        assert job.output == "output.txt"
        assert job.label == "Test Label"

    def test_restore_job_without_output(self):
        """Should create RestoreJob without output file."""
        job = RestoreJob("input.png")
        assert job.output is None
        assert job.label is None

    def test_batch_config_creation(self):
        """Should create BatchConfig with jobs."""
        backup_jobs = [BackupJob("pass", "in.png", "out.png")]
        restore_jobs = [RestoreJob("backup.png", "output.txt")]

        config = BatchConfig("TestPass123", backup_jobs, restore_jobs)
        assert config.passphrase == "TestPass123"
        assert len(config.backup_jobs) == 1
        assert len(config.restore_jobs) == 1
