"""
Tests for SettingsScreen and unsaved changes handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, PropertyMock

from stegvault.tui.widgets import SettingsScreen, UnsavedChangesScreen


class TestSettingsScreen:
    """Tests for SettingsScreen widget."""

    def test_settings_screen_creation(self):
        """Should create settings screen with initial values."""
        screen = SettingsScreen()

        assert screen._initial_auto_check is True
        assert screen._initial_auto_upgrade is False

    @patch("stegvault.config.core.load_config")
    def test_settings_screen_on_mount(self, mock_load_config):
        """Should load config values on mount."""
        # Mock config
        mock_config = Mock()
        mock_config.updates.auto_check = False
        mock_config.updates.auto_upgrade = True
        mock_config.totp.enabled = True
        mock_config.crypto.argon2_time_cost = 5
        mock_config.crypto.argon2_memory_cost = 131072
        mock_config.crypto.argon2_parallelism = 8
        mock_load_config.return_value = mock_config

        screen = SettingsScreen()

        # Mock query_one to return mock switches and inputs
        mock_auto_check_switch = Mock()
        mock_auto_upgrade_switch = Mock()
        mock_totp_enabled_switch = Mock()
        mock_time_cost_input = Mock()
        mock_memory_cost_input = Mock()
        mock_parallelism_input = Mock()

        def query_one_side_effect(selector, widget_type=None):
            if "auto-check" in selector:
                return mock_auto_check_switch
            elif "auto-upgrade" in selector:
                return mock_auto_upgrade_switch
            elif "totp-enabled" in selector:
                return mock_totp_enabled_switch
            elif "time-cost" in selector:
                return mock_time_cost_input
            elif "memory-cost" in selector:
                return mock_memory_cost_input
            elif "parallelism" in selector:
                return mock_parallelism_input

        screen.query_one = Mock(side_effect=query_one_side_effect)

        # Call on_mount
        screen.on_mount()

        # Verify switches were set
        assert mock_auto_check_switch.value is False
        assert mock_auto_upgrade_switch.value is True
        assert mock_totp_enabled_switch.value is True

        # Verify crypto inputs were set
        assert mock_time_cost_input.value == "5"
        assert mock_memory_cost_input.value == "131072"
        assert mock_parallelism_input.value == "8"

        # Verify initial values were stored
        assert screen._initial_auto_check is False
        assert screen._initial_auto_upgrade is True
        assert screen._initial_totp_enabled is True
        assert screen._initial_time_cost == 5
        assert screen._initial_memory_cost == 131072
        assert screen._initial_parallelism == 8

    def test_has_unsaved_changes_no_changes(self):
        """Should return False when no changes."""
        screen = SettingsScreen()
        screen._initial_auto_check = True
        screen._initial_auto_upgrade = False

        # Mock switches with same values as initial
        mock_auto_check_switch = Mock()
        mock_auto_check_switch.value = True
        mock_auto_upgrade_switch = Mock()
        mock_auto_upgrade_switch.value = False

        def query_one_side_effect(selector, widget_type=None):
            if "auto-check" in selector:
                return mock_auto_check_switch
            elif "auto-upgrade" in selector:
                return mock_auto_upgrade_switch

        screen.query_one = Mock(side_effect=query_one_side_effect)

        assert screen._has_unsaved_changes() is False

    def test_has_unsaved_changes_with_changes(self):
        """Should return True when there are changes."""
        screen = SettingsScreen()
        screen._initial_auto_check = True
        screen._initial_auto_upgrade = False
        screen._initial_totp_enabled = False
        screen._initial_time_cost = 3
        screen._initial_memory_cost = 65536
        screen._initial_parallelism = 4

        # Mock switches with different values
        mock_auto_check_switch = Mock()
        mock_auto_check_switch.value = False  # Changed
        mock_auto_upgrade_switch = Mock()
        mock_auto_upgrade_switch.value = True  # Changed
        mock_totp_enabled_switch = Mock()
        mock_totp_enabled_switch.value = False  # Not changed

        # Mock crypto inputs with unchanged values
        mock_time_cost_input = Mock(value="3")
        mock_memory_cost_input = Mock(value="65536")
        mock_parallelism_input = Mock(value="4")

        def query_one_side_effect(selector, widget_type=None):
            if "auto-check" in selector:
                return mock_auto_check_switch
            elif "auto-upgrade" in selector:
                return mock_auto_upgrade_switch
            elif "totp-enabled" in selector:
                return mock_totp_enabled_switch
            elif "time-cost" in selector:
                return mock_time_cost_input
            elif "memory-cost" in selector:
                return mock_memory_cost_input
            elif "parallelism" in selector:
                return mock_parallelism_input

        screen.query_one = Mock(side_effect=query_one_side_effect)

        assert screen._has_unsaved_changes() is True

    @patch("stegvault.config.core.save_config")
    @patch("stegvault.config.core.load_config")
    def test_save_settings(self, mock_load_config, mock_save_config):
        """Should save settings to config."""
        mock_config = Mock()
        mock_config.updates = Mock()
        mock_config.totp = Mock()
        mock_config.crypto = Mock()
        mock_load_config.return_value = mock_config

        screen = SettingsScreen()
        mock_app = Mock()

        # Mock switches
        mock_auto_check_switch = Mock()
        mock_auto_check_switch.value = False
        mock_auto_upgrade_switch = Mock()
        mock_auto_upgrade_switch.value = True
        mock_totp_enabled_switch = Mock()
        mock_totp_enabled_switch.value = True

        # Mock crypto inputs with valid values
        mock_time_cost_input = Mock(value="3")
        mock_memory_cost_input = Mock(value="65536")
        mock_parallelism_input = Mock(value="4")

        def query_one_side_effect(selector, widget_type=None):
            if "auto-check" in selector:
                return mock_auto_check_switch
            elif "auto-upgrade" in selector:
                return mock_auto_upgrade_switch
            elif "totp-enabled" in selector:
                return mock_totp_enabled_switch
            elif "time-cost" in selector:
                return mock_time_cost_input
            elif "memory-cost" in selector:
                return mock_memory_cost_input
            elif "parallelism" in selector:
                return mock_parallelism_input

        screen.query_one = Mock(side_effect=query_one_side_effect)

        # Mock validation methods to return True (all valid)
        screen._validate_time_cost = Mock(return_value=True)
        screen._validate_memory_cost = Mock(return_value=True)
        screen._validate_parallelism = Mock(return_value=True)
        screen._validate_crypto_compatibility = Mock(return_value=True)

        # Patch app property
        with patch.object(type(screen), "app", PropertyMock(return_value=mock_app)):
            # Call save_settings
            result = screen._save_settings()

            # Verify it returned True
            assert result is True

            # Verify config was updated and saved
            assert mock_config.updates.auto_check is False
            assert mock_config.updates.auto_upgrade is True
            assert mock_config.totp.enabled is True
            assert mock_config.crypto.argon2_time_cost == 3
            assert mock_config.crypto.argon2_memory_cost == 65536
            assert mock_config.crypto.argon2_parallelism == 4
            mock_save_config.assert_called_once_with(mock_config)
            mock_app.notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_close_with_check_no_changes_quit(self):
        """Should show quit confirmation when no changes and quit_on_no_changes=True."""
        screen = SettingsScreen()
        mock_app = Mock()
        screen._has_unsaved_changes = Mock(return_value=False)

        # Patch app property
        with patch.object(type(screen), "app", PropertyMock(return_value=mock_app)):
            # Call with quit_on_no_changes=True
            await screen._handle_close_with_check(quit_on_no_changes=True)

            # Should call app.action_quit()
            mock_app.action_quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_close_with_check_no_changes_close(self):
        """Should dismiss when no changes and quit_on_no_changes=False."""
        screen = SettingsScreen()
        screen.dismiss = Mock()
        screen._has_unsaved_changes = Mock(return_value=False)

        # Call with quit_on_no_changes=False
        await screen._handle_close_with_check(quit_on_no_changes=False)

        # Should dismiss
        screen.dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_handle_close_with_check_with_changes_save(self):
        """Should save and exit when user chooses 'save'."""
        screen = SettingsScreen()
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value="save")
        screen.dismiss = Mock()
        screen._has_unsaved_changes = Mock(return_value=True)
        screen._save_settings = Mock(return_value=True)  # Successful save

        # Patch app property
        with patch.object(type(screen), "app", PropertyMock(return_value=mock_app)):
            await screen._handle_close_with_check()

            # Should save and dismiss
            screen._save_settings.assert_called_once()
            screen.dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_handle_close_with_check_with_changes_dont_save(self):
        """Should exit without saving when user chooses 'dont_save'."""
        screen = SettingsScreen()
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value="dont_save")
        screen.dismiss = Mock()
        screen._has_unsaved_changes = Mock(return_value=True)
        screen._save_settings = Mock()

        # Patch app property
        with patch.object(type(screen), "app", PropertyMock(return_value=mock_app)):
            await screen._handle_close_with_check()

            # Should dismiss without saving
            screen._save_settings.assert_not_called()
            screen.dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_handle_close_with_check_with_changes_cancel(self):
        """Should stay in settings when user chooses 'cancel'."""
        screen = SettingsScreen()
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value="cancel")
        screen.dismiss = Mock()
        screen._has_unsaved_changes = Mock(return_value=True)
        screen._save_settings = Mock()

        # Patch app property
        with patch.object(type(screen), "app", PropertyMock(return_value=mock_app)):
            await screen._handle_close_with_check()

            # Should not save or dismiss
            screen._save_settings.assert_not_called()
            screen.dismiss.assert_not_called()

    def test_on_button_pressed_save(self):
        """Should save settings and dismiss on Save button."""
        screen = SettingsScreen()
        screen.dismiss = Mock()
        screen._save_settings = Mock(return_value=True)  # Successful save

        button = Mock()
        button.id = "btn-save"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen._save_settings.assert_called_once()
        screen.dismiss.assert_called_once_with(None)

    def test_on_button_pressed_cancel(self):
        """Should check for unsaved changes on Cancel button."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        # Should call run_worker with _handle_close_with_check
        screen.run_worker.assert_called_once()

    def test_action_close(self):
        """Should check for unsaved changes on Escape."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        screen.action_close()

        # Should call run_worker with _handle_close_with_check
        screen.run_worker.assert_called_once()

    def test_on_key_q(self):
        """Should check for unsaved changes with quit on 'q' press."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        event = Mock()
        event.key = "q"
        event.stop = Mock()

        screen.on_key(event)

        # Should stop event and call run_worker
        event.stop.assert_called_once()
        screen.run_worker.assert_called_once()


class TestUnsavedChangesScreen:
    """Tests for UnsavedChangesScreen widget."""

    def test_unsaved_changes_screen_creation(self):
        """Should create unsaved changes screen."""
        screen = UnsavedChangesScreen()

        assert screen is not None

    def test_on_button_pressed_save_exit(self):
        """Should dismiss with 'save' on Save & Exit button."""
        screen = UnsavedChangesScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-save-exit"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("save")

    def test_on_button_pressed_dont_save(self):
        """Should dismiss with 'dont_save' on Don't Save button."""
        screen = UnsavedChangesScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-dont-save"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("dont_save")

    def test_on_button_pressed_cancel(self):
        """Should dismiss with 'cancel' on Cancel button."""
        screen = UnsavedChangesScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("cancel")

    def test_action_cancel(self):
        """Should dismiss with 'cancel' on Escape."""
        screen = UnsavedChangesScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with("cancel")
