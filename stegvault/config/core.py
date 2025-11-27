"""
Core configuration management functionality.

Handles loading, saving, and validating StegVault configuration files.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict

# Python 3.11+ has tomllib in stdlib, earlier versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

# For writing TOML, we need tomli_w regardless of Python version
try:
    import tomli_w
except ImportError:  # pragma: no cover
    tomli_w = None  # type: ignore


class ConfigError(Exception):
    """Configuration-related errors."""

    pass


@dataclass
class CryptoConfig:
    """Cryptography configuration parameters."""

    argon2_time_cost: int = 3  # Iterations
    argon2_memory_cost: int = 65536  # 64MB in KB
    argon2_parallelism: int = 4  # Thread count


@dataclass
class CLIConfig:
    """CLI behavior configuration."""

    check_strength: bool = True  # Check passphrase strength by default
    default_image_dir: str = ""  # Default directory for images
    verbose: bool = False  # Verbose output


@dataclass
class Config:
    """Complete StegVault configuration."""

    crypto: CryptoConfig
    cli: CLIConfig

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            "crypto": asdict(self.crypto),
            "cli": asdict(self.cli),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        crypto = CryptoConfig(**data.get("crypto", {}))
        cli = CLIConfig(**data.get("cli", {}))
        return cls(crypto=crypto, cli=cli)


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    if sys.platform == "win32":
        # Windows: use APPDATA
        appdata = os.environ.get("APPDATA")
        if appdata:
            config_dir = Path(appdata) / "StegVault"
        else:
            config_dir = Path.home() / ".stegvault"
    else:
        # Unix-like: use XDG_CONFIG_HOME or ~/.config
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / "stegvault"
        else:
            config_dir = Path.home() / ".config" / "stegvault"

    return config_dir


def get_config_path() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.toml"


def get_default_config() -> Config:
    """Get default configuration."""
    return Config(
        crypto=CryptoConfig(),
        cli=CLIConfig(),
    )


def load_config() -> Config:
    """
    Load configuration from file.

    Returns default configuration if file doesn't exist.
    Raises ConfigError if file exists but is invalid.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return get_default_config()

    if tomllib is None:
        raise ConfigError("TOML support not available. Install tomli: pip install tomli")

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        # Validate and create config
        config = Config.from_dict(data)

        # Validate crypto parameters
        if config.crypto.argon2_time_cost < 1:
            raise ConfigError("argon2_time_cost must be >= 1")
        if config.crypto.argon2_memory_cost < 8:
            raise ConfigError("argon2_memory_cost must be >= 8 KB")
        if config.crypto.argon2_parallelism < 1:
            raise ConfigError("argon2_parallelism must be >= 1")

        return config

    except (OSError, IOError) as e:
        raise ConfigError(f"Failed to read config file: {e}")
    except Exception as e:
        raise ConfigError(f"Invalid config file: {e}")


def save_config(config: Config) -> None:
    """
    Save configuration to file.

    Creates config directory if it doesn't exist.
    Raises ConfigError on failure.
    """
    if tomli_w is None:
        raise ConfigError("TOML write support not available. Install tomli_w: pip install tomli_w")

    config_dir = get_config_dir()
    config_path = get_config_path()

    try:
        # Create directory if needed
        config_dir.mkdir(parents=True, exist_ok=True)

        # Write config
        with open(config_path, "wb") as f:
            tomli_w.dump(config.to_dict(), f)

    except (OSError, IOError) as e:
        raise ConfigError(f"Failed to write config file: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to serialize config: {e}")


def ensure_config_exists() -> Config:
    """
    Ensure configuration file exists.

    Creates default config if it doesn't exist.
    Returns the loaded configuration.
    """
    config_path = get_config_path()

    if not config_path.exists():
        config = get_default_config()
        try:
            save_config(config)
        except ConfigError:
            # If we can't save, just return default
            pass
        return config

    return load_config()
