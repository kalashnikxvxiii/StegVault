"""
Tests for TUI main application.

Tests StegVaultTUI app initialization and basic functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from stegvault.tui.app import StegVaultTUI
from stegvault.vault import Vault, VaultEntry
from stegvault.app.controllers import VaultController


class TestStegVaultTUI:
    """Tests for StegVaultTUI application."""

    def test_tui_app_creation(self):
        """Should create TUI application."""
        app = StegVaultTUI()

        assert app.vault_controller is not None
        assert app.crypto_controller is not None
        assert app.current_vault is None
        assert app.current_image_path is None

    def test_tui_app_title(self):
        """Should have correct title."""
        app = StegVaultTUI()

        assert app.TITLE == "StegVault TUI"
        assert "Password Manager" in app.SUB_TITLE

    def test_tui_app_bindings(self):
        """Should have key bindings defined."""
        app = StegVaultTUI()

        binding_keys = [b.key for b in app.BINDINGS]

        assert "q" in binding_keys  # quit
        assert "o" in binding_keys  # open vault
        assert "n" in binding_keys  # new vault
        assert "h" in binding_keys  # help

    def test_action_quit(self):
        """Should exit application."""
        app = StegVaultTUI()
        app.exit = Mock()

        app.action_quit()

        app.exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_new_vault_cancel_file(self):
        """Should handle cancelled file selection for new vault."""
        app = StegVaultTUI()
        app.push_screen_wait = AsyncMock(return_value=None)

        await app.action_new_vault()

        # Should return early without error
        app.push_screen_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_new_vault_cancel_passphrase(self):
        """Should handle cancelled passphrase input for new vault."""
        app = StegVaultTUI()
        app.push_screen_wait = AsyncMock(side_effect=["output.png", None])

        await app.action_new_vault()

        # Should call push_screen_wait twice (file, then passphrase)
        assert app.push_screen_wait.call_count == 2

    @pytest.mark.asyncio
    async def test_action_new_vault_cancel_first_entry(self):
        """Should handle cancelled first entry form."""
        app = StegVaultTUI()
        app.push_screen_wait = AsyncMock(side_effect=["output.png", "passphrase", None])

        await app.action_new_vault()

        # Should call push_screen_wait three times (file, passphrase, entry form)
        assert app.push_screen_wait.call_count == 3

    @pytest.mark.asyncio
    async def test_action_new_vault_create_failure(self):
        """Should handle vault creation failure."""
        app = StegVaultTUI()
        form_data = {"key": "test", "password": "secret"}
        app.push_screen_wait = AsyncMock(side_effect=["output.png", "passphrase", form_data])
        app.notify = Mock()

        # Mock controller to return failure
        app.vault_controller.create_new_vault = Mock(return_value=(None, False, "Test error"))

        await app.action_new_vault()

        # Should notify error
        app.notify.assert_called()
        error_calls = [call for call in app.notify.call_args_list if "Failed" in str(call)]
        assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_action_new_vault_save_failure(self):
        """Should handle vault save failure."""
        app = StegVaultTUI()
        form_data = {"key": "test", "password": "secret"}
        app.push_screen_wait = AsyncMock(side_effect=["output.png", "passphrase", form_data])
        app.notify = Mock()

        # Mock create success, save failure
        mock_vault = Vault(entries=[])
        app.vault_controller.create_new_vault = Mock(return_value=(mock_vault, True, None))

        from stegvault.app.controllers import VaultSaveResult

        save_result = VaultSaveResult(output_path="", success=False, error="Disk full")
        app.vault_controller.save_vault = Mock(return_value=save_result)

        await app.action_new_vault()

        # Should notify error
        app.notify.assert_called()
        error_calls = [call for call in app.notify.call_args_list if "Failed to save" in str(call)]
        assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_action_new_vault_success(self):
        """Should successfully create and open new vault."""
        app = StegVaultTUI()
        form_data = {
            "key": "gmail",
            "password": "secret123",
            "username": "user@gmail.com",
            "url": "https://gmail.com",
            "notes": "Personal",
            "tags": ["email"],
        }
        app.push_screen_wait = AsyncMock(side_effect=["output.png", "passphrase", form_data])
        app.push_screen = Mock()
        app.notify = Mock()

        # Mock successful vault creation and save
        mock_entry = VaultEntry(key="gmail", password="secret123")
        mock_vault = Vault(entries=[mock_entry])
        app.vault_controller.create_new_vault = Mock(return_value=(mock_vault, True, None))

        from stegvault.app.controllers import VaultSaveResult

        save_result = VaultSaveResult(output_path="output.png", success=True)
        app.vault_controller.save_vault = Mock(return_value=save_result)

        await app.action_new_vault()

        # Should create vault with correct parameters
        app.vault_controller.create_new_vault.assert_called_once_with(
            key="gmail",
            password="secret123",
            username="user@gmail.com",
            url="https://gmail.com",
            notes="Personal",
            tags=["email"],
        )

        # Should save vault
        app.vault_controller.save_vault.assert_called_once_with(
            mock_vault, "output.png", "passphrase"
        )

        # Should push vault screen
        app.push_screen.assert_called_once()
        assert app.current_vault == mock_vault
        assert app.current_image_path == "output.png"

        # Should notify success
        success_calls = [
            call for call in app.notify.call_args_list if "created successfully" in str(call)
        ]
        assert len(success_calls) > 0

    @pytest.mark.asyncio
    async def test_action_new_vault_exception(self):
        """Should handle exceptions during vault creation."""
        app = StegVaultTUI()
        form_data = {"key": "test", "password": "secret"}
        app.push_screen_wait = AsyncMock(side_effect=["output.png", "passphrase", form_data])
        app.notify = Mock()

        # Mock controller to raise exception
        app.vault_controller.create_new_vault = Mock(side_effect=Exception("Test error"))

        await app.action_new_vault()

        # Should notify error
        app.notify.assert_called()
        error_calls = [call for call in app.notify.call_args_list if "Error creating" in str(call)]
        assert len(error_calls) > 0

    def test_action_show_help(self):
        """Should notify help screen feature."""
        app = StegVaultTUI()
        app.notify = Mock()

        app.action_show_help()

        app.notify.assert_called_once()
        call_args = app.notify.call_args
        assert "Phase 3" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_action_open_vault_cancel_file(self):
        """Should handle cancelled file selection."""
        app = StegVaultTUI()
        app.push_screen_wait = AsyncMock(return_value=None)

        await app.action_open_vault()

        # Should return early without error
        app.push_screen_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_open_vault_cancel_passphrase(self):
        """Should handle cancelled passphrase input."""
        app = StegVaultTUI()
        app.push_screen_wait = AsyncMock(side_effect=["test.png", None])

        await app.action_open_vault()

        # Should call push_screen_wait twice (file, then passphrase)
        assert app.push_screen_wait.call_count == 2

    @pytest.mark.asyncio
    async def test_action_open_vault_load_failure(self):
        """Should handle vault loading failure."""
        app = StegVaultTUI()
        app.push_screen_wait = AsyncMock(side_effect=["test.png", "passphrase"])
        app.notify = Mock()

        # Mock controller to return failure
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "Invalid passphrase"
        app.vault_controller.load_vault = Mock(return_value=mock_result)

        await app.action_open_vault()

        # Should notify error
        app.notify.assert_called()
        error_calls = [call for call in app.notify.call_args_list if "Failed" in str(call)]
        assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_action_open_vault_success(self):
        """Should successfully load vault."""
        app = StegVaultTUI()
        app.push_screen_wait = AsyncMock(side_effect=["test.png", "passphrase"])
        app.push_screen = Mock()
        app.notify = Mock()

        # Mock successful vault load
        mock_vault = Vault(entries=[])
        mock_result = Mock()
        mock_result.success = True
        mock_result.vault = mock_vault
        app.vault_controller.load_vault = Mock(return_value=mock_result)

        await app.action_open_vault()

        # Should push vault screen
        app.push_screen.assert_called_once()
        assert app.current_vault == mock_vault
        assert app.current_image_path == "test.png"

    @pytest.mark.asyncio
    async def test_action_open_vault_exception(self):
        """Should handle exceptions during vault loading."""
        app = StegVaultTUI()
        app.push_screen_wait = AsyncMock(side_effect=["test.png", "passphrase"])
        app.notify = Mock()

        # Mock controller to raise exception
        app.vault_controller.load_vault = Mock(side_effect=Exception("Test error"))

        await app.action_open_vault()

        # Should notify error
        app.notify.assert_called()
        error_calls = [call for call in app.notify.call_args_list if "Error" in str(call)]
        assert len(error_calls) > 0

    def test_on_button_pressed_open(self):
        """Should handle open button press."""
        app = StegVaultTUI()
        app.action_open_vault = AsyncMock()

        button = Mock()
        button.id = "btn-open"
        event = Mock()
        event.button = button

        app.on_button_pressed(event)

        # Should call action (note: won't await in sync context)
        app.action_open_vault.assert_called_once()

    def test_on_button_pressed_new(self):
        """Should handle new button press."""
        app = StegVaultTUI()
        app.action_new_vault = Mock()

        button = Mock()
        button.id = "btn-new"
        event = Mock()
        event.button = button

        app.on_button_pressed(event)

        app.action_new_vault.assert_called_once()

    def test_on_button_pressed_help(self):
        """Should handle help button press."""
        app = StegVaultTUI()
        app.action_show_help = Mock()

        button = Mock()
        button.id = "btn-help"
        event = Mock()
        event.button = button

        app.on_button_pressed(event)

        app.action_show_help.assert_called_once()
