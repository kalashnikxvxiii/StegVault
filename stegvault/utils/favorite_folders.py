"""Utility for managing favorite vault folders for quick access."""

import json
import os
import stat
from pathlib import Path
from typing import List, Optional


class FavoriteFoldersManager:
    """Manages favorite folder paths for quick vault access."""

    def __init__(self):
        """Initialize favorite folders manager."""
        self.config_dir = Path.home() / ".stegvault"
        self.favorites_file = self.config_dir / "favorite_folders.json"

    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_favorites(self) -> List[dict]:
        """Load favorite folders from JSON file.

        Returns:
            List of favorite folder entries with metadata
        """
        if not self.favorites_file.exists():
            return []

        try:
            with open(self.favorites_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("favorite_folders", [])
        except (json.JSONDecodeError, OSError):
            return []

    def _save_favorites(self, favorites: List[dict]) -> None:
        """Save favorite folders to JSON file with restrictive permissions.

        Args:
            favorites: List of favorite folder entries
        """
        self._ensure_config_dir()

        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump({"favorite_folders": favorites}, f, indent=2)

            # Set restrictive permissions (owner read/write only - 0600)
            # This prevents other users on multi-user systems from reading vault paths
            if hasattr(os, "chmod"):
                os.chmod(self.favorites_file, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass  # Fail silently if can't save

    def _get_display_name(self, folder_path: str) -> str:
        """Get a display-friendly name for a folder path.

        Args:
            folder_path: Absolute path to folder

        Returns:
            Display name (e.g., "Documents" or "C:\\" for root)
        """
        path = Path(folder_path)
        folder_name = path.name

        # If name is empty (root directory like C:\), use drive letter
        if not folder_name:
            # For Windows: "C:\" becomes "C:\"
            # For Unix: "/" becomes "/"
            if path.drive:
                return f"{path.drive}\\"
            else:
                return str(path)

        return folder_name

    def add_folder(self, folder_path: str, name: Optional[str] = None) -> bool:
        """Add a folder to favorites.

        Args:
            folder_path: Absolute path to folder
            name: Optional custom name for the folder (defaults to folder name)

        Returns:
            True if added successfully, False if already exists
        """
        # Normalize path
        normalized_path = str(Path(folder_path).resolve())

        # Check if path is a directory
        if not Path(normalized_path).is_dir():
            return False

        # Load existing favorites
        favorites = self._load_favorites()

        # Check if already exists
        if any(f.get("path") == normalized_path for f in favorites):
            return False

        # Add new favorite
        new_favorite = {
            "path": normalized_path,
            "name": name or self._get_display_name(normalized_path),
        }
        favorites.append(new_favorite)

        # Save
        self._save_favorites(favorites)
        return True

    def remove_folder(self, folder_path: str) -> bool:
        """Remove a folder from favorites.

        Args:
            folder_path: Path to remove

        Returns:
            True if removed, False if not found
        """
        normalized_path = str(Path(folder_path).resolve())
        favorites = self._load_favorites()

        # Filter out the path
        new_favorites = [f for f in favorites if f.get("path") != normalized_path]

        if len(new_favorites) == len(favorites):
            return False  # Not found

        # Save
        self._save_favorites(new_favorites)
        return True

    def get_favorites(self) -> List[dict]:
        """Get list of favorite folders with metadata.

        Returns:
            List of dicts with 'path' and 'name' keys
        """
        favorites = self._load_favorites()

        # Filter out paths that no longer exist
        valid_favorites = [f for f in favorites if Path(f["path"]).is_dir()]

        # Update if any invalid paths were removed
        if len(valid_favorites) < len(favorites):
            self._save_favorites(valid_favorites)

        return valid_favorites

    def get_folder_paths(self) -> List[str]:
        """Get list of favorite folder paths.

        Returns:
            List of absolute folder paths
        """
        return [f["path"] for f in self.get_favorites()]

    def is_favorite(self, folder_path: str) -> bool:
        """Check if a folder is in favorites.

        Args:
            folder_path: Path to check

        Returns:
            True if folder is in favorites
        """
        normalized_path = str(Path(folder_path).resolve())
        return normalized_path in self.get_folder_paths()

    def clear(self) -> None:
        """Clear all favorite folders."""
        self._save_favorites([])

    def rename_favorite(self, folder_path: str, new_name: str) -> bool:
        """Rename a favorite folder's display name.

        Args:
            folder_path: Path of the favorite to rename
            new_name: New display name

        Returns:
            True if renamed successfully, False if not found
        """
        normalized_path = str(Path(folder_path).resolve())
        favorites = self._load_favorites()

        # Find and update the favorite
        found = False
        for favorite in favorites:
            if favorite.get("path") == normalized_path:
                favorite["name"] = new_name
                found = True
                break

        if not found:
            return False

        # Save
        self._save_favorites(favorites)
        return True
