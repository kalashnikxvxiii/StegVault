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
        url = "https://raw.githubusercontent.com/kalashnikxvxiii/StegVault/main/CHANGELOG.md"
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
        url = f"https://api.github.com/repos/kalashnikxvxiii/StegVault/releases/tags/v{version}"
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


def update_cache_version() -> None:
    """
    Update cached current_version if it doesn't match running version.

    This fixes the issue where cache shows old version after manual
    reinstall/update (e.g., cache shows 0.7.6 but running 0.7.7).
    """
    try:
        cache_file = get_cache_file()

        if not cache_file.exists():
            return

        # Read current cache
        with open(cache_file, "r") as f:
            cache = json.load(f)

        # Check if current_version in cache matches running version
        cached_version = cache.get("current_version")
        if cached_version != __version__:
            # Version mismatch - update cache
            cache["current_version"] = __version__
            cache["timestamp"] = datetime.now().isoformat()

            # Re-evaluate update_available based on new version
            latest = cache.get("latest_version")
            if latest:
                comparison = compare_versions(__version__, latest)
                cache["update_available"] = comparison < 0
            else:
                cache["update_available"] = False

            # Write updated cache
            with open(cache_file, "w") as f:
                json.dump(cache, f, indent=2)

    except (json.JSONDecodeError, OSError, KeyError):
        pass  # Silently fail


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


def is_running_from_installed() -> bool:
    """Check if currently running from installed package (not dev mode)."""
    try:
        import stegvault

        install_path = Path(stegvault.__file__).parent.parent
        # Check if running from site-packages (installed) vs source directory
        return "site-packages" in str(install_path) or "dist-packages" in str(install_path)
    except Exception:
        return False


def create_detached_update_script(method: Optional[str] = None) -> Optional[Path]:
    """
    Create a batch script for detached update (runs after app closure).

    This script will:
    1. Wait for StegVault to close
    2. Perform the update
    3. Clean up the script

    Args:
        method: Installation method (auto-detected if None)

    Returns:
        Path to the update script, or None if creation failed
    """
    if method is None:
        method = get_install_method()

    try:
        from stegvault.config.core import get_config_dir

        config_dir = get_config_dir()
        script_path = config_dir / "perform_update.bat"

        # Create Windows batch script
        if method == InstallMethod.PIP:
            script_content = f"""@echo off
title StegVault Auto-Update
echo ========================================
echo    StegVault Auto-Update
echo ========================================
echo.
echo Waiting for StegVault to close...
timeout /t 3 /nobreak >nul

echo.
echo Updating StegVault via pip...
echo This may take a minute...
echo.

"{sys.executable}" -m pip install --upgrade stegvault

if errorlevel 1 (
    echo.
    echo ========================================
    echo    Update Failed
    echo ========================================
    echo.
    echo Please check your internet connection
    echo and try again manually:
    echo.
    echo   pip install --upgrade stegvault
    echo.
    pause
) else (
    echo.
    echo ========================================
    echo    Update Successful!
    echo ========================================
    echo.
    echo StegVault has been updated successfully.
    echo You can now close this window and
    echo restart StegVault.
    echo.
    timeout /t 5
)

del "%~f0"
"""
        elif method == InstallMethod.SOURCE:
            import stegvault

            repo_path = Path(stegvault.__file__).parent.parent

            script_content = f"""@echo off
title StegVault Auto-Update (Source)
echo ========================================
echo    StegVault Auto-Update (Source)
echo ========================================
echo.
echo Waiting for StegVault to close...
timeout /t 3 /nobreak >nul

echo.
echo Pulling latest changes from GitHub...
cd /d "{repo_path}"
git pull origin main

echo.
echo Reinstalling StegVault...
"{sys.executable}" -m pip install -e . --force-reinstall

if errorlevel 1 (
    echo.
    echo ========================================
    echo    Update Failed
    echo ========================================
    pause
) else (
    echo.
    echo ========================================
    echo    Update Successful!
    echo ========================================
    timeout /t 5
)

del "%~f0"
"""
        else:
            return None  # Portable/unknown methods not supported

        # Write script
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        return script_path

    except Exception:
        return None


def launch_detached_update(method: Optional[str] = None) -> Tuple[bool, str]:
    """
    Launch detached update process that runs after app closure.

    Args:
        method: Installation method (auto-detected if None)

    Returns:
        Tuple of (success, message)
    """
    script_path = create_detached_update_script(method)

    if script_path is None:
        method = method or get_install_method()
        if method == InstallMethod.PORTABLE:
            return _update_portable()  # Return manual instructions
        return False, "Could not create update script"

    try:
        # Launch script in detached mode (new window, no wait)
        if sys.platform == "win32":
            subprocess.Popen(  # nosec B603, B607
                ["cmd", "/c", "start", "", str(script_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS,
            )
        else:
            # Linux/Mac: run in background
            subprocess.Popen(  # nosec B603, B607
                ["sh", str(script_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        return (
            True,
            "Update will begin after you close StegVault.\n"
            "A window will open showing the update progress.\n\n"
            "Please close StegVault now to proceed with the update.",
        )

    except Exception as e:
        return False, f"Failed to launch update: {str(e)}"


def _update_pip() -> Tuple[bool, str]:
    """Update PyPI installation."""
    try:
        # WARNING: Cannot update while StegVault is running from installed package
        # This will cause WinError 32 (file in use) on Windows
        if is_running_from_installed():
            return (
                False,
                "Cannot update while StegVault is running.\n"
                "Please close StegVault and run:\n"
                "  pip install --upgrade stegvault\n\n"
                "Or use the TUI 'Update Now' button which will\n"
                "close StegVault and perform the update automatically.",
            )

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
            error_msg = result.stderr
            # Check for common errors
            if "WinError 32" in error_msg or "file is used by another process" in error_msg:
                return (
                    False,
                    "Update failed: StegVault files are in use.\n"
                    "Please close all StegVault instances and try again.",
                )
            return False, f"pip upgrade failed: {error_msg}"

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
        "URL: https://github.com/kalashnikxvxiii/StegVault/releases/latest",
    )
