"""
StegVault Auto-Update System

Provides version checking, changelog fetching, and upgrade functionality.
"""

import json
import re
import subprocess  # nosec B404
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from stegvault import __version__


class UpdateError(Exception):
    """Raised when update operations fail."""

    pass


class InstallMethod:
    """Installation method constants."""

    PIP = "pip"
    SOURCE = "source"
    PORTABLE = "portable"
    UNKNOWN = "unknown"


def get_install_method() -> str:
    """
    Detect how StegVault was installed.

    Returns:
        One of: "pip", "source", "portable", "unknown"
    """
    try:
        import stegvault

        install_path = Path(stegvault.__file__).parent.parent

        # Check for portable package indicators
        if (install_path / "setup_portable.bat").exists():
            return InstallMethod.PORTABLE

        # Check for git repository (source install)
        if (install_path / ".git").exists():
            return InstallMethod.SOURCE

        # Check if installed via pip (site-packages or dist-packages)
        if "site-packages" in str(install_path) or "dist-packages" in str(install_path):
            return InstallMethod.PIP

        return InstallMethod.UNKNOWN

    except Exception:
        return InstallMethod.UNKNOWN


def get_latest_version() -> Optional[str]:
    """
    Query PyPI API for the latest StegVault version.

    Returns:
        Latest version string (e.g., "0.7.5") or None if check fails
    """
    try:
        url = "https://pypi.org/pypi/stegvault/json"
        req = Request(url, headers={"User-Agent": f"StegVault/{__version__}"})

        with urlopen(req, timeout=5) as response:  # nosec B310
            data = json.loads(response.read().decode("utf-8"))
            return data["info"]["version"]

    except (URLError, HTTPError, json.JSONDecodeError, KeyError, TimeoutError):
        return None


def compare_versions(current: str, latest: str) -> int:
    """
    Compare two semantic version strings.

    Args:
        current: Current version (e.g., "0.7.5")
        latest: Latest version (e.g., "0.8.0")

    Returns:
        -1 if current < latest (update available)
         0 if current == latest (up to date)
         1 if current > latest (ahead of PyPI)
    """
    try:
        # Parse version strings (e.g., "0.7.5" -> [0, 7, 5])
        current_parts = [int(x) for x in current.split(".")]
        latest_parts = [int(x) for x in latest.split(".")]

        # Pad shorter version with zeros
        max_len = max(len(current_parts), len(latest_parts))
        current_parts += [0] * (max_len - len(current_parts))
        latest_parts += [0] * (max_len - len(latest_parts))

        # Compare part by part
        if current_parts < latest_parts:
            return -1
        elif current_parts > latest_parts:
            return 1
        else:
            return 0

    except (ValueError, AttributeError):
        return 0  # Assume equal if parsing fails


def check_for_updates() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if a new version of StegVault is available.

    Returns:
        Tuple of (update_available, latest_version, error_message)
        - update_available: True if newer version exists
        - latest_version: Version string or None
        - error_message: Error description or None
    """
    try:
        latest = get_latest_version()

        if latest is None:
            return False, None, "Failed to fetch latest version from PyPI"

        comparison = compare_versions(__version__, latest)

        if comparison < 0:
            return True, latest, None
        elif comparison == 0:
            return False, latest, None
        else:
            # Current version ahead of PyPI (development version)
            return False, latest, f"Development version (PyPI: {latest})"

    except Exception as e:
        return False, None, f"Update check failed: {str(e)}"


def fetch_changelog(version: str) -> Optional[str]:
    """
    Fetch changelog from GitHub for a specific version.

    Tries two sources:
    1. Raw CHANGELOG.md from main branch
    2. GitHub Releases API

    Args:
        version: Version string (e.g., "0.7.5")

    Returns:
        Changelog markdown or None if fetch fails
    """
    # Try 1: Raw CHANGELOG.md
    try:
        url = "https://raw.githubusercontent.com/kalashnikxvxiii-collab/StegVault/main/CHANGELOG.md"
        req = Request(url, headers={"User-Agent": f"StegVault/{__version__}"})

        with urlopen(req, timeout=10) as response:  # nosec B310
            content = response.read().decode("utf-8")
            changelog = parse_changelog_section(content, version)
            if changelog:
                return changelog

    except (URLError, HTTPError, TimeoutError):
        pass

    # Try 2: GitHub Releases API
    try:
        url = f"https://api.github.com/repos/kalashnikxvxiii-collab/StegVault/releases/tags/v{version}"
        req = Request(url, headers={"User-Agent": f"StegVault/{__version__}"})

        with urlopen(req, timeout=10) as response:  # nosec B310
            data = json.loads(response.read().decode("utf-8"))
            return data.get("body", None)

    except (URLError, HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def parse_changelog_section(content: str, version: str) -> Optional[str]:
    """
    Extract changelog section for a specific version from CHANGELOG.md.

    Args:
        content: Full CHANGELOG.md content
        version: Version to extract (e.g., "0.7.5")

    Returns:
        Markdown section for that version or None
    """
    try:
        # Pattern: ## [0.7.5] - 2025-12-15
        pattern = rf"## \[{re.escape(version)}\].*?(?=\n## \[|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(0).strip()

        return None

    except Exception:
        return None


def get_cache_file() -> Path:
    """Get path to update check cache file."""
    from stegvault.config.core import get_config_dir

    cache_dir = get_config_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "update_cache.json"


def get_cached_check(max_age_hours: int = 24) -> Optional[dict]:
    """
    Retrieve cached update check result.

    Args:
        max_age_hours: Maximum age of cache in hours

    Returns:
        Cached result dict or None if expired/missing
    """
    try:
        cache_file = get_cache_file()

        if not cache_file.exists():
            return None

        with open(cache_file, "r") as f:
            cache = json.load(f)

        # Check if cache is expired
        cached_time = datetime.fromisoformat(cache["timestamp"])
        age = datetime.now() - cached_time

        if age > timedelta(hours=max_age_hours):
            return None

        return cache

    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return None


def cache_check_result(
    update_available: bool, latest_version: Optional[str], error: Optional[str]
) -> None:
    """
    Cache update check result to disk.

    Args:
        update_available: Whether update is available
        latest_version: Latest version string
        error: Error message if check failed
    """
    try:
        cache_file = get_cache_file()

        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "current_version": __version__,
            "latest_version": latest_version,
            "update_available": update_available,
            "error": error,
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

    except OSError:
        pass  # Silently fail if cache write fails


def perform_update(method: Optional[str] = None) -> Tuple[bool, str]:
    """
    Perform StegVault update based on installation method.

    Args:
        method: Installation method (auto-detected if None)

    Returns:
        Tuple of (success, message)
    """
    if method is None:
        method = get_install_method()

    if method == InstallMethod.PIP:
        return _update_pip()
    elif method == InstallMethod.SOURCE:
        return _update_source()
    elif method == InstallMethod.PORTABLE:
        return _update_portable()
    else:
        return False, "Unknown installation method - cannot auto-update"


def _update_pip() -> Tuple[bool, str]:
    """Update PyPI installation."""
    try:
        # Use same Python interpreter that's running StegVault
        result = subprocess.run(  # nosec B603
            [sys.executable, "-m", "pip", "install", "--upgrade", "stegvault"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return True, "Successfully updated via pip"
        else:
            return False, f"pip upgrade failed: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Update timed out after 2 minutes"
    except Exception as e:
        return False, f"Update failed: {str(e)}"


def _update_source() -> Tuple[bool, str]:
    """Update source installation."""
    try:
        import stegvault

        repo_path = Path(stegvault.__file__).parent.parent

        # Git pull
        result = subprocess.run(  # nosec B603, B607
            ["git", "pull", "origin", "main"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return False, f"git pull failed: {result.stderr}"

        # Reinstall
        result = subprocess.run(  # nosec B603
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-e",
                ".",
                "--force-reinstall",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return True, "Successfully updated from source"
        else:
            return False, f"Reinstall failed: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Update timed out"
    except Exception as e:
        return False, f"Update failed: {str(e)}"


def _update_portable() -> Tuple[bool, str]:
    """Portable package cannot auto-update - return instructions."""
    return (
        False,
        "Portable package requires manual update:\n"
        "1. Download latest release from GitHub\n"
        "2. Extract to StegVault folder (overwrite)\n"
        "3. Run setup_portable.bat\n\n"
        "URL: https://github.com/kalashnikxvxiii-collab/StegVault/releases/latest",
    )
