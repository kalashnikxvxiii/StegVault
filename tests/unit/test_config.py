"""
Unit tests for configuration module.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest import mock

from stegvault.config.core import (
    Config,
    CryptoConfig,
    CLIConfig,
    ConfigError,
    get_config_dir,
    get_config_path,
    get_default_config,
    load_config,
    save_config,
    ensure_config_exists,
)


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the config directory to use temp directory
        monkeypatch.setattr(
            "stegvault.config.core.get_config_dir", lambda: Path(tmpdir)
        )
        yield Path(tmpdir)


class TestDataclasses:
    """Tests for configuration dataclasses."""

    def test_crypto_config_defaults(self):
        """Should create CryptoConfig with default values."""
        config = CryptoConfig()
        assert config.argon2_time_cost == 3
        assert config.argon2_memory_cost == 65536
        assert config.argon2_parallelism == 4

    def test_crypto_config_custom_values(self):
        """Should create CryptoConfig with custom values."""
        config = CryptoConfig(
            argon2_time_cost=5, argon2_memory_cost=131072, argon2_parallelism=8
        )
        assert config.argon2_time_cost == 5
        assert config.argon2_memory_cost == 131072
        assert config.argon2_parallelism == 8

    def test_cli_config_defaults(self):
        """Should create CLIConfig with default values."""
        config = CLIConfig()
        assert config.check_strength is True
        assert config.default_image_dir == ""
        assert config.verbose is False

    def test_cli_config_custom_values(self):
        """Should create CLIConfig with custom values."""
        config = CLIConfig(
            check_strength=False, default_image_dir="/tmp/images", verbose=True
        )
        assert config.check_strength is False
        assert config.default_image_dir == "/tmp/images"
        assert config.verbose is True

    def test_config_creation(self):
        """Should create Config with crypto and cli configs."""
        crypto = CryptoConfig(argon2_time_cost=5)
        cli = CLIConfig(verbose=True)
        config = Config(crypto=crypto, cli=cli)

        assert config.crypto.argon2_time_cost == 5
        assert config.cli.verbose is True

    def test_config_to_dict(self):
        """Should convert Config to dictionary."""
        config = Config(
            crypto=CryptoConfig(argon2_time_cost=5),
            cli=CLIConfig(verbose=True),
        )

        data = config.to_dict()

        assert data["crypto"]["argon2_time_cost"] == 5
        assert data["crypto"]["argon2_memory_cost"] == 65536
        assert data["cli"]["verbose"] is True
        assert data["cli"]["check_strength"] is True

    def test_config_from_dict(self):
        """Should create Config from dictionary."""
        data = {
            "crypto": {"argon2_time_cost": 5, "argon2_memory_cost": 131072},
            "cli": {"verbose": True, "default_image_dir": "/tmp"},
        }

        config = Config.from_dict(data)

        assert config.crypto.argon2_time_cost == 5
        assert config.crypto.argon2_memory_cost == 131072
        assert config.cli.verbose is True
        assert config.cli.default_image_dir == "/tmp"

    def test_config_from_dict_missing_sections(self):
        """Should create Config with defaults when sections missing."""
        data = {}
        config = Config.from_dict(data)

        # Should use default values
        assert config.crypto.argon2_time_cost == 3
        assert config.cli.check_strength is True


class TestConfigPaths:
    """Tests for configuration path functions."""

    def test_get_config_dir_windows(self, monkeypatch):
        """Should return correct config dir on Windows."""
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("APPDATA", "C:\\Users\\Test\\AppData\\Roaming")

        config_dir = get_config_dir()
        assert config_dir == Path("C:\\Users\\Test\\AppData\\Roaming\\StegVault")

    def test_get_config_dir_windows_no_appdata(self, monkeypatch):
        """Should fallback to home dir on Windows without APPDATA."""
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.delenv("APPDATA", raising=False)
        monkeypatch.setattr(Path, "home", lambda: Path("/home/test"))

        config_dir = get_config_dir()
        assert config_dir == Path("/home/test/.stegvault")

    def test_get_config_dir_unix_with_xdg(self, monkeypatch):
        """Should use XDG_CONFIG_HOME on Unix when set."""
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setenv("XDG_CONFIG_HOME", "/home/test/.config")

        config_dir = get_config_dir()
        assert config_dir == Path("/home/test/.config/stegvault")

    def test_get_config_dir_unix_without_xdg(self, monkeypatch):
        """Should fallback to ~/.config on Unix without XDG."""
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: Path("/home/test"))

        config_dir = get_config_dir()
        assert config_dir == Path("/home/test/.config/stegvault")

    def test_get_config_path(self, monkeypatch):
        """Should return config.toml in config directory."""
        monkeypatch.setattr(
            "stegvault.config.core.get_config_dir", lambda: Path("/tmp/stegvault")
        )

        config_path = get_config_path()
        assert config_path == Path("/tmp/stegvault/config.toml")


class TestDefaultConfig:
    """Tests for default configuration."""

    def test_get_default_config(self):
        """Should return default configuration."""
        config = get_default_config()

        assert isinstance(config, Config)
        assert isinstance(config.crypto, CryptoConfig)
        assert isinstance(config.cli, CLIConfig)

        # Verify defaults
        assert config.crypto.argon2_time_cost == 3
        assert config.crypto.argon2_memory_cost == 65536
        assert config.cli.check_strength is True


class TestLoadConfig:
    """Tests for loading configuration."""

    def test_load_config_file_not_exists(self, temp_config_dir):
        """Should return default config when file doesn't exist."""
        config = load_config()

        assert isinstance(config, Config)
        assert config.crypto.argon2_time_cost == 3  # Default value

    def test_load_config_valid_file(self, temp_config_dir):
        """Should load valid configuration file."""
        # Create a valid config file
        config_path = temp_config_dir / "config.toml"
        config_content = """
[crypto]
argon2_time_cost = 5
argon2_memory_cost = 131072
argon2_parallelism = 8

[cli]
check_strength = false
verbose = true
default_image_dir = "/tmp/images"
"""
        config_path.write_text(config_content)

        config = load_config()

        assert config.crypto.argon2_time_cost == 5
        assert config.crypto.argon2_memory_cost == 131072
        assert config.crypto.argon2_parallelism == 8
        assert config.cli.check_strength is False
        assert config.cli.verbose is True
        assert config.cli.default_image_dir == "/tmp/images"

    def test_load_config_invalid_time_cost(self, temp_config_dir):
        """Should raise ConfigError for invalid time_cost."""
        config_path = temp_config_dir / "config.toml"
        config_content = """
[crypto]
argon2_time_cost = 0
"""
        config_path.write_text(config_content)

        with pytest.raises(ConfigError, match="argon2_time_cost must be >= 1"):
            load_config()

    def test_load_config_invalid_memory_cost(self, temp_config_dir):
        """Should raise ConfigError for invalid memory_cost."""
        config_path = temp_config_dir / "config.toml"
        config_content = """
[crypto]
argon2_memory_cost = 4
"""
        config_path.write_text(config_content)

        with pytest.raises(ConfigError, match="argon2_memory_cost must be >= 8 KB"):
            load_config()

    def test_load_config_invalid_parallelism(self, temp_config_dir):
        """Should raise ConfigError for invalid parallelism."""
        config_path = temp_config_dir / "config.toml"
        config_content = """
[crypto]
argon2_parallelism = 0
"""
        config_path.write_text(config_content)

        with pytest.raises(ConfigError, match="argon2_parallelism must be >= 1"):
            load_config()

    def test_load_config_invalid_toml(self, temp_config_dir):
        """Should raise ConfigError for invalid TOML syntax."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text("{ invalid toml }")

        with pytest.raises(ConfigError, match="Invalid config file"):
            load_config()

    def test_load_config_partial_file(self, temp_config_dir):
        """Should load partial config and use defaults for missing values."""
        config_path = temp_config_dir / "config.toml"
        config_content = """
[crypto]
argon2_time_cost = 7
"""
        config_path.write_text(config_content)

        config = load_config()

        # Custom value
        assert config.crypto.argon2_time_cost == 7
        # Default values
        assert config.crypto.argon2_memory_cost == 65536
        assert config.cli.check_strength is True


class TestSaveConfig:
    """Tests for saving configuration."""

    def test_save_config_creates_directory(self, temp_config_dir):
        """Should create config directory if it doesn't exist."""
        config = get_default_config()

        # Remove directory if it exists
        if temp_config_dir.exists():
            import shutil

            shutil.rmtree(temp_config_dir)

        save_config(config)

        assert temp_config_dir.exists()
        assert (temp_config_dir / "config.toml").exists()

    def test_save_config_valid_data(self, temp_config_dir):
        """Should save configuration correctly."""
        config = Config(
            crypto=CryptoConfig(argon2_time_cost=5, argon2_memory_cost=131072),
            cli=CLIConfig(verbose=True, default_image_dir="/tmp"),
        )

        save_config(config)

        config_path = temp_config_dir / "config.toml"
        assert config_path.exists()

        # Reload and verify
        loaded_config = load_config()
        assert loaded_config.crypto.argon2_time_cost == 5
        assert loaded_config.crypto.argon2_memory_cost == 131072
        assert loaded_config.cli.verbose is True
        assert loaded_config.cli.default_image_dir == "/tmp"

    def test_save_config_overwrite_existing(self, temp_config_dir):
        """Should overwrite existing configuration."""
        # Save initial config
        config1 = Config(
            crypto=CryptoConfig(argon2_time_cost=3), cli=CLIConfig(verbose=False)
        )
        save_config(config1)

        # Save new config
        config2 = Config(
            crypto=CryptoConfig(argon2_time_cost=7), cli=CLIConfig(verbose=True)
        )
        save_config(config2)

        # Verify new config was saved
        loaded = load_config()
        assert loaded.crypto.argon2_time_cost == 7
        assert loaded.cli.verbose is True


class TestEnsureConfigExists:
    """Tests for ensure_config_exists function."""

    def test_ensure_config_exists_creates_file(self, temp_config_dir):
        """Should create config file if it doesn't exist."""
        config = ensure_config_exists()

        assert isinstance(config, Config)
        assert (temp_config_dir / "config.toml").exists()

    def test_ensure_config_exists_loads_existing(self, temp_config_dir):
        """Should load existing config file."""
        # Create custom config
        custom_config = Config(
            crypto=CryptoConfig(argon2_time_cost=9), cli=CLIConfig(verbose=True)
        )
        save_config(custom_config)

        # Ensure config exists should load it
        config = ensure_config_exists()

        assert config.crypto.argon2_time_cost == 9
        assert config.cli.verbose is True

    def test_ensure_config_exists_graceful_save_failure(
        self, temp_config_dir, monkeypatch
    ):
        """Should return default config if save fails."""
        # Mock save_config to raise error
        def mock_save_config(config):
            raise ConfigError("Cannot save")

        monkeypatch.setattr("stegvault.config.core.save_config", mock_save_config)

        # Should not raise, but return default
        config = ensure_config_exists()

        assert isinstance(config, Config)
        assert config.crypto.argon2_time_cost == 3


class TestConfigRoundtrip:
    """Test save/load roundtrip."""

    def test_save_and_load_roundtrip(self, temp_config_dir):
        """Should preserve all config values through save/load cycle."""
        original = Config(
            crypto=CryptoConfig(
                argon2_time_cost=10, argon2_memory_cost=262144, argon2_parallelism=16
            ),
            cli=CLIConfig(
                check_strength=False, default_image_dir="/custom/path", verbose=True
            ),
        )

        # Save
        save_config(original)

        # Load
        loaded = load_config()

        # Verify all values match
        assert loaded.crypto.argon2_time_cost == original.crypto.argon2_time_cost
        assert loaded.crypto.argon2_memory_cost == original.crypto.argon2_memory_cost
        assert loaded.crypto.argon2_parallelism == original.crypto.argon2_parallelism
        assert loaded.cli.check_strength == original.cli.check_strength
        assert loaded.cli.default_image_dir == original.cli.default_image_dir
        assert loaded.cli.verbose == original.cli.verbose
