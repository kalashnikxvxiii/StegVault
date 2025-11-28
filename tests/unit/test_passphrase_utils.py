"""
Tests for passphrase handling utilities.

Tests all passphrase functions to achieve 100% coverage.
"""

import os
import tempfile
from pathlib import Path

import pytest
import click

from stegvault.utils.passphrase import get_passphrase, validate_passphrase_sources


class TestGetPassphrase:
    """Test get_passphrase function."""

    def test_explicit_passphrase_priority(self, monkeypatch):
        """Explicit passphrase should have highest priority."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "env_pass")

        result = get_passphrase(
            passphrase="explicit_pass", passphrase_file=None, env_var="STEGVAULT_PASSPHRASE"
        )

        assert result == "explicit_pass"

    def test_file_passphrase_priority(self, tmp_path, monkeypatch):
        """File passphrase should override env var."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "env_pass")

        passphrase_file = tmp_path / "passphrase.txt"
        passphrase_file.write_text("file_pass")

        result = get_passphrase(
            passphrase=None, passphrase_file=str(passphrase_file), env_var="STEGVAULT_PASSPHRASE"
        )

        assert result == "file_pass"

    def test_env_var_passphrase(self, monkeypatch):
        """Environment variable should be used if no file."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "env_pass")

        result = get_passphrase(
            passphrase=None, passphrase_file=None, env_var="STEGVAULT_PASSPHRASE"
        )

        assert result == "env_pass"

    def test_file_not_found_error(self):
        """Should raise ClickException if file not found."""
        with pytest.raises(click.ClickException, match="Passphrase file not found"):
            get_passphrase(passphrase=None, passphrase_file="/nonexistent/file.txt")

    def test_file_is_directory_error(self, tmp_path):
        """Should raise ClickException if path is directory."""
        directory = tmp_path / "test_dir"
        directory.mkdir()

        with pytest.raises(click.ClickException, match="Not a file"):
            get_passphrase(passphrase=None, passphrase_file=str(directory))

    def test_file_empty_error(self, tmp_path):
        """Should exit with code 2 if file is empty."""
        passphrase_file = tmp_path / "empty.txt"
        passphrase_file.write_text("")

        with pytest.raises(SystemExit) as exc_info:
            get_passphrase(passphrase=None, passphrase_file=str(passphrase_file))

        assert exc_info.value.code == 2

    def test_file_whitespace_only_error(self, tmp_path):
        """Should exit with code 2 if file contains only whitespace."""
        passphrase_file = tmp_path / "whitespace.txt"
        passphrase_file.write_text("   \n\t  ")

        with pytest.raises(SystemExit) as exc_info:
            get_passphrase(passphrase=None, passphrase_file=str(passphrase_file))

        assert exc_info.value.code == 2

    def test_file_read_error(self, tmp_path):
        """Should raise ClickException on file read error."""
        passphrase_file = tmp_path / "test.txt"
        passphrase_file.write_text("secret")

        # Make file unreadable (Windows doesn't support chmod the same way)
        # Instead, test with a mock that raises IOError
        from unittest.mock import patch, mock_open

        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = IOError("Permission denied")

            with pytest.raises(click.ClickException, match="Failed to read passphrase file"):
                get_passphrase(passphrase=None, passphrase_file=str(passphrase_file))

    def test_env_var_empty_error(self, monkeypatch):
        """Should exit with code 2 if env var is empty."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "   ")

        with pytest.raises(SystemExit) as exc_info:
            get_passphrase(passphrase=None, passphrase_file=None, env_var="STEGVAULT_PASSPHRASE")

        assert exc_info.value.code == 2

    def test_prompt_fallback(self, monkeypatch):
        """Should prompt if no other source available."""
        # Monkeypatch click.prompt to return a value instead of prompting
        monkeypatch.setattr("click.prompt", lambda *args, **kwargs: "prompted_pass")

        result = get_passphrase(passphrase=None, passphrase_file=None, env_var="NONEXISTENT_VAR")

        assert result == "prompted_pass"

    def test_custom_prompt_text(self, monkeypatch):
        """Should use custom prompt text."""
        prompted = []

        def mock_prompt(text, **kwargs):
            prompted.append(text)
            return "test_pass"

        monkeypatch.setattr("click.prompt", mock_prompt)

        get_passphrase(
            passphrase=None,
            passphrase_file=None,
            env_var="NONEXISTENT_VAR",
            prompt_text="Custom Prompt",
        )

        assert prompted[0] == "Custom Prompt"

    def test_prompt_hide_input(self, monkeypatch):
        """Should hide input when prompting."""
        kwargs_captured = []

        def mock_prompt(text, **kwargs):
            kwargs_captured.append(kwargs)
            return "test_pass"

        monkeypatch.setattr("click.prompt", mock_prompt)

        get_passphrase(
            passphrase=None, passphrase_file=None, env_var="NONEXISTENT_VAR", hide_input=True
        )

        assert kwargs_captured[0]["hide_input"] is True

    def test_prompt_confirmation(self, monkeypatch):
        """Should confirm when confirmation_prompt=True."""
        kwargs_captured = []

        def mock_prompt(text, **kwargs):
            kwargs_captured.append(kwargs)
            return "test_pass"

        monkeypatch.setattr("click.prompt", mock_prompt)

        get_passphrase(
            passphrase=None,
            passphrase_file=None,
            env_var="NONEXISTENT_VAR",
            confirmation_prompt=True,
        )

        assert kwargs_captured[0]["confirmation_prompt"] is True


class TestValidatePassphraseSources:
    """Test validate_passphrase_sources function."""

    def test_no_sources_with_prompt_allowed(self):
        """Should succeed when no sources but prompt is allowed."""
        # Should not raise
        validate_passphrase_sources(passphrase=None, passphrase_file=None, allow_prompt=True)

    def test_no_sources_headless_mode(self, monkeypatch):
        """Should raise error in headless mode with no sources."""
        # Ensure env var is not set
        monkeypatch.delenv("STEGVAULT_PASSPHRASE", raising=False)

        with pytest.raises(click.ClickException, match="No passphrase source specified"):
            validate_passphrase_sources(passphrase=None, passphrase_file=None, allow_prompt=False)

    def test_multiple_sources_passphrase_and_file(self, tmp_path):
        """Should raise error with both passphrase and file."""
        passphrase_file = tmp_path / "pass.txt"
        passphrase_file.write_text("secret")

        with pytest.raises(click.ClickException, match="multiple passphrase sources"):
            validate_passphrase_sources(
                passphrase="explicit", passphrase_file=str(passphrase_file), allow_prompt=True
            )

    def test_multiple_sources_passphrase_and_env(self, monkeypatch):
        """Should raise error with both passphrase and env var."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "env_secret")

        with pytest.raises(click.ClickException, match="multiple passphrase sources"):
            validate_passphrase_sources(
                passphrase="explicit", passphrase_file=None, allow_prompt=True
            )

    def test_multiple_sources_file_and_env(self, tmp_path, monkeypatch):
        """Should raise error with both file and env var."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "env_secret")

        passphrase_file = tmp_path / "pass.txt"
        passphrase_file.write_text("secret")

        with pytest.raises(click.ClickException, match="multiple passphrase sources"):
            validate_passphrase_sources(
                passphrase=None, passphrase_file=str(passphrase_file), allow_prompt=True
            )

    def test_multiple_sources_all_three(self, tmp_path, monkeypatch):
        """Should raise error with all three sources."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "env_secret")

        passphrase_file = tmp_path / "pass.txt"
        passphrase_file.write_text("secret")

        with pytest.raises(click.ClickException, match="multiple passphrase sources"):
            validate_passphrase_sources(
                passphrase="explicit", passphrase_file=str(passphrase_file), allow_prompt=True
            )

    def test_single_source_passphrase(self, monkeypatch):
        """Should succeed with only passphrase."""
        monkeypatch.delenv("STEGVAULT_PASSPHRASE", raising=False)

        # Should not raise
        validate_passphrase_sources(passphrase="explicit", passphrase_file=None, allow_prompt=True)

    def test_single_source_file(self, tmp_path, monkeypatch):
        """Should succeed with only file."""
        monkeypatch.delenv("STEGVAULT_PASSPHRASE", raising=False)

        passphrase_file = tmp_path / "pass.txt"
        passphrase_file.write_text("secret")

        # Should not raise
        validate_passphrase_sources(
            passphrase=None, passphrase_file=str(passphrase_file), allow_prompt=True
        )

    def test_single_source_env(self, monkeypatch):
        """Should succeed with only env var."""
        monkeypatch.setenv("STEGVAULT_PASSPHRASE", "env_secret")

        # Should not raise
        validate_passphrase_sources(passphrase=None, passphrase_file=None, allow_prompt=True)
