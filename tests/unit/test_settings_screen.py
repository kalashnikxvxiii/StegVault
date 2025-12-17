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
        mock_load_config.return_value = mock_config

        screen = SettingsScreen()

        # Mock query_one to return mock switches
        mock_auto_check_switch = Mock()
        mock_auto_upgrade_switch = Mock()

        def query_one_side_effect(selector, widget_type=None):
            if "auto-check" in selector:
                return mock_auto_check_switch
            elif "auto-upgrade" in selector:
                return mock_auto_upgrade_switch

        screen.query_one = Mock(side_effect=query_one_side_effect)

        # Call on_mount
        screen.on_mount()

        # Verify switches were set
        assert mock_auto_check_switch.value is False
        assert mock_auto_upgrade_switch.value is True

        # Verify initial values were stored
        assert screen._initial_auto_check is False
        assert screen._initial_auto_upgrade is True

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

        # Mock switches with different values
        mock_auto_check_switch = Mock()
        mock_auto_check_switch.value = False  # Changed
        mock_auto_upgrade_switch = Mock()
        mock_auto_upgrade_switch.value = True  # Changed

        def query_one_side_effect(selector, widget_type=None):
            if "auto-check" in selector:
                return mock_auto_check_switch
            elif "auto-upgrade" in selector:
                return mock_auto_upgrade_switch

        screen.query_one = Mock(side_effect=query_one_side_effect)

        assert screen._has_unsaved_changes() is True

    @patch("stegvault.config.core.save_config")
    @patch("stegvault.config.core.load_config")
    def test_save_settings(self, mock_load_config, mock_save_config):
        """Should save settings to config."""
        mock_config = Mock()
        mock_config.updates = Mock()
        mock_load_config.return_value = mock_config

        screen = SettingsScreen()
        mock_app = Mock()

        # Mock switches
        mock_auto_check_switch = Mock()
        mock_auto_check_switch.value = False
        mock_auto_upgrade_switch = Mock()
        mock_auto_upgrade_switch.value = True

        def query_one_side_effect(selector, widget_type=None):
            if "auto-check" in selector:
                return mock_auto_check_switch
            elif "auto-upgrade" in selector:
                return mock_auto_upgrade_switch

        screen.query_one = Mock(side_effect=query_one_side_effect)

        # Patch app property
        with patch.object(type(screen), "app", PropertyMock(return_value=mock_app)):
            # Call save_settings
            screen._save_settings()

            # Verify config was updated and saved
            assert mock_config.updates.auto_check is False
            assert mock_config.updates.auto_upgrade is True
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
        screen._save_settings = Mock()

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
        screen._save_settings = Mock()

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
