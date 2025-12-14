"""Tests for favorite folders manager."""

import json
import tempfile
from pathlib import Path

import pytest

from stegvault.utils.favorite_folders import FavoriteFoldersManager


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Create temporary config directory for testing."""
    config_dir = tmp_path / ".stegvault"
    config_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return config_dir


@pytest.fixture
def manager(temp_config_dir):
    """Create FavoriteFoldersManager instance with temp config."""
    return FavoriteFoldersManager()


@pytest.fixture
def test_folders(tmp_path):
    """Create test folders."""
    folder1 = tmp_path / "folder1"
    folder2 = tmp_path / "folder2"
    folder3 = tmp_path / "folder3"
    folder1.mkdir()
    folder2.mkdir()
    folder3.mkdir()
    return {
        "folder1": str(folder1),
        "folder2": str(folder2),
        "folder3": str(folder3),
    }


def test_add_folder(manager, test_folders):
    """Test adding a folder to favorites."""
    result = manager.add_folder(test_folders["folder1"], name="Test Folder")
    assert result is True

    favorites = manager.get_favorites()
    assert len(favorites) == 1
    assert favorites[0]["path"] == test_folders["folder1"]
    assert favorites[0]["name"] == "Test Folder"


def test_add_folder_default_name(manager, test_folders):
    """Test adding folder with default name (folder name)."""
    result = manager.add_folder(test_folders["folder1"])
    assert result is True

    favorites = manager.get_favorites()
    assert len(favorites) == 1
    assert favorites[0]["name"] == "folder1"


def test_add_folder_duplicate(manager, test_folders):
    """Test adding duplicate folder returns False."""
    manager.add_folder(test_folders["folder1"])
    result = manager.add_folder(test_folders["folder1"])
    assert result is False

    favorites = manager.get_favorites()
    assert len(favorites) == 1


def test_add_folder_invalid_path(manager):
    """Test adding non-existent path returns False."""
    result = manager.add_folder("/nonexistent/path")
    assert result is False


def test_remove_folder(manager, test_folders):
    """Test removing a folder from favorites."""
    manager.add_folder(test_folders["folder1"])
    manager.add_folder(test_folders["folder2"])

    result = manager.remove_folder(test_folders["folder1"])
    assert result is True

    favorites = manager.get_favorites()
    assert len(favorites) == 1
    assert favorites[0]["path"] == test_folders["folder2"]


def test_remove_folder_not_found(manager, test_folders):
    """Test removing non-existent folder returns False."""
    result = manager.remove_folder(test_folders["folder1"])
    assert result is False


def test_get_favorites_empty(manager):
    """Test getting favorites when list is empty."""
    favorites = manager.get_favorites()
    assert favorites == []


def test_get_favorites_filters_invalid_paths(manager, test_folders, tmp_path):
    """Test that get_favorites() filters out non-existent paths."""
    # Add valid folder
    manager.add_folder(test_folders["folder1"])

    # Manually add invalid folder to JSON
    favorites_file = manager.favorites_file
    with open(favorites_file, "r") as f:
        data = json.load(f)

    data["favorite_folders"].append(
        {"path": str(tmp_path / "nonexistent"), "name": "Deleted Folder"}
    )

    with open(favorites_file, "w") as f:
        json.dump(data, f)

    # Should only return valid folders
    favorites = manager.get_favorites()
    assert len(favorites) == 1
    assert favorites[0]["path"] == test_folders["folder1"]


def test_get_folder_paths(manager, test_folders):
    """Test getting just the folder paths."""
    manager.add_folder(test_folders["folder1"])
    manager.add_folder(test_folders["folder2"])

    paths = manager.get_folder_paths()
    assert len(paths) == 2
    assert test_folders["folder1"] in paths
    assert test_folders["folder2"] in paths


def test_is_favorite(manager, test_folders):
    """Test checking if folder is a favorite."""
    manager.add_folder(test_folders["folder1"])

    assert manager.is_favorite(test_folders["folder1"]) is True
    assert manager.is_favorite(test_folders["folder2"]) is False


def test_clear(manager, test_folders):
    """Test clearing all favorites."""
    manager.add_folder(test_folders["folder1"])
    manager.add_folder(test_folders["folder2"])

    manager.clear()

    favorites = manager.get_favorites()
    assert favorites == []


def test_rename_favorite(manager, test_folders):
    """Test renaming a favorite folder's display name."""
    manager.add_folder(test_folders["folder1"], name="Old Name")

    result = manager.rename_favorite(test_folders["folder1"], "New Name")
    assert result is True

    favorites = manager.get_favorites()
    assert len(favorites) == 1
    assert favorites[0]["name"] == "New Name"


def test_rename_favorite_not_found(manager, test_folders):
    """Test renaming non-existent favorite returns False."""
    result = manager.rename_favorite(test_folders["folder1"], "New Name")
    assert result is False


def test_persistence(manager, test_folders):
    """Test that favorites persist across manager instances."""
    # Add folders with first manager
    manager.add_folder(test_folders["folder1"])
    manager.add_folder(test_folders["folder2"])

    # Create new manager instance
    new_manager = FavoriteFoldersManager()
    favorites = new_manager.get_favorites()

    assert len(favorites) == 2
    paths = [f["path"] for f in favorites]
    assert test_folders["folder1"] in paths
    assert test_folders["folder2"] in paths


def test_corrupted_json_file(manager, tmp_path):
    """Test handling of corrupted JSON file."""
    # Create corrupted JSON file
    manager._ensure_config_dir()
    with open(manager.favorites_file, "w") as f:
        f.write("invalid json {{{")

    # Should return empty list instead of crashing
    favorites = manager.get_favorites()
    assert favorites == []


def test_add_folder_normalizes_path(manager, test_folders):
    """Test that paths are normalized (resolved to absolute)."""
    # Add folder with relative path notation
    folder_path = Path(test_folders["folder1"])
    relative_ish = str(folder_path / ".." / folder_path.name)

    result = manager.add_folder(relative_ish)
    assert result is True

    favorites = manager.get_favorites()
    # Path should be normalized to absolute
    assert favorites[0]["path"] == test_folders["folder1"]
