"""
Configuration management for StegVault.

Handles loading and saving user configuration from ~/.stegvault/config.toml
"""

from stegvault.config.core import (
    load_config,
    save_config,
    get_default_config,
    get_config_path,
    get_config_dir,
    Config,
    ConfigError,
)

__all__ = [
    "load_config",
    "save_config",
    "get_default_config",
    "get_config_path",
    "get_config_dir",
    "Config",
    "ConfigError",
]
