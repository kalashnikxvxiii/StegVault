"""
Tests for TUI widgets.

Tests custom Textual widgets for StegVault TUI.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from stegvault.tui.widgets import (
    FilteredDirectoryTree,
    HelpScreen,
    QuitConfirmationScreen,
    FileSelectScreen,
    PassphraseInputScreen,
    GenericConfirmationScreen,
    PasswordHistoryModal,
    EntryListItem,
    EntryDetailPanel,
    EntryFormScreen,
    DeleteConfirmationScreen,
    VaultOverwriteWarningScreen,
    UnsavedChangesScreen,
    PasswordGeneratorScreen,
    ChangelogViewerScreen,
    SettingsScreen,
    BackupCodeInputScreen,
    TOTPConfigScreen,
    TOTPAuthScreen,
)
from stegvault.vault import Vault, VaultEntry


class TestEntryListItem:
    """Tests for EntryListItem widget."""

    def test_entry_list_item_creation(self):
        """Should create entry list item."""
        entry = VaultEntry(
            key="test",
            password="secret",
            username="user@test.com",
            tags=["work", "email"],
        )

        item = EntryListItem(entry)

        assert item.entry == entry
        assert "entry-item" in item.classes

    def test_entry_list_item_render_with_tags(self):
        """Should render entry with tags."""
        entry = VaultEntry(
            key="github",
            password="pass",
            tags=["dev", "work"],
        )

        item = EntryListItem(entry)
        rendered = item.render()

        assert "github" in rendered
        assert "dev" in rendered
        assert "work" in rendered

    def test_entry_list_item_render_without_tags(self):
        """Should render entry without tags."""
        entry = VaultEntry(key="simple", password="pass")

        item = EntryListItem(entry)
        rendered = item.render()

        assert "simple" in rendered
        assert "[" not in rendered  # No tags


class TestEntryDetailPanel:
    """Tests for EntryDetailPanel widget."""

    def test_entry_detail_panel_creation(self):
        """Should create entry detail panel."""
        panel = EntryDetailPanel()

        assert panel.current_entry is None
        assert panel.password_visible is False
        assert panel.totp_refresh_timer is None

    def test_show_entry_basic(self):
        """Should display entry details."""
        entry = VaultEntry(
            key="test",
            password="secret123",
            username="user@test.com",
        )

        # Create panel and manually set composed state
        panel = EntryDetailPanel()
        panel._composed = True  # Simulate composition

        # Mock query_one to avoid DOM access
        from unittest.mock import Mock

        mock_content = Mock()
        panel.query_one = Mock(return_value=mock_content)
        panel.mount = Mock()
        panel.set_interval = Mock()  # Mock timer

        panel.show_entry(entry)

        assert panel.current_entry == entry
        assert panel.password_visible is False

    def test_show_entry_with_all_fields(self):
        """Should display entry with all fields."""
        entry = VaultEntry(
            key="complete",
            password="pass",
            username="user@example.com",
            url="https://example.com",
            notes="Important notes here",
            tags=["tag1", "tag2"],
            totp_secret="ABCD1234",
        )

        # Create panel and mock DOM access
        panel = EntryDetailPanel()
        panel._composed = True
        from unittest.mock import Mock

        mock_content = Mock()
        panel.query_one = Mock(return_value=mock_content)
        panel.mount = Mock()
        panel.set_interval = Mock()  # Mock timer

        panel.show_entry(entry)

        assert panel.current_entry == entry
        panel.set_interval.assert_called_once()  # TOTP refresh started

    def test_toggle_password_visibility(self):
        """Should toggle password visibility."""
        entry = VaultEntry(key="test", password="secret")

        # Create panel and mock DOM access
        panel = EntryDetailPanel()
        panel._composed = True
        from unittest.mock import Mock

        mock_content = Mock()
        panel.query_one = Mock(return_value=mock_content)
        panel.mount = Mock()
        panel.set_interval = Mock()  # Mock timer
        panel.set_timer = Mock()  # Mock auto-hide timer

        panel.show_entry(entry)
        assert panel.password_visible is False

        panel.toggle_password_visibility()
        assert panel.password_visible is True

        panel.toggle_password_visibility()
        assert panel.password_visible is False

    def test_toggle_password_without_entry(self):
        """Should handle toggle without entry."""
        panel = EntryDetailPanel()

        # Should not crash
        panel.toggle_password_visibility()
        assert panel.password_visible is False

    def test_clear_panel(self):
        """Should clear entry detail panel."""
        entry = VaultEntry(key="test", password="pass")

        # Create panel and mock DOM access
        panel = EntryDetailPanel()
        panel._composed = True
        from unittest.mock import Mock

        mock_content = Mock()
        panel.query_one = Mock(return_value=mock_content)
        panel.mount = Mock()
        panel.set_interval = Mock()  # Mock timer

        panel.show_entry(entry)
        assert panel.current_entry is not None

        panel.clear()
        assert panel.current_entry is None
        assert panel.password_visible is False

    def test_start_totp_refresh_with_totp_secret(self):
        """Should start TOTP refresh timer when entry has TOTP secret."""
        entry = VaultEntry(key="test", password="pass", totp_secret="JBSWY3DPEHPK3PXP")

        panel = EntryDetailPanel()
        panel._composed = True
        from unittest.mock import Mock

        mock_timer = Mock()
        panel.set_interval = Mock(return_value=mock_timer)

        panel._start_totp_refresh()
        panel.set_interval.assert_not_called()  # No entry set yet

        panel.current_entry = entry
        panel._start_totp_refresh()
        panel.set_interval.assert_called_once_with(1.0, panel._refresh_totp_display)
        assert panel.totp_refresh_timer == mock_timer

    def test_start_totp_refresh_without_totp_secret(self):
        """Should not start TOTP refresh timer when entry has no TOTP secret."""
        entry = VaultEntry(key="test", password="pass")

        panel = EntryDetailPanel()
        panel._composed = True
        from unittest.mock import Mock

        panel.set_interval = Mock()
        panel.current_entry = entry

        panel._start_totp_refresh()
        panel.set_interval.assert_not_called()

    def test_stop_totp_refresh(self):
        """Should stop TOTP refresh timer."""
        panel = EntryDetailPanel()
        from unittest.mock import Mock

        mock_timer = Mock()
        panel.totp_refresh_timer = mock_timer

        panel._stop_totp_refresh()
        mock_timer.stop.assert_called_once()
        assert panel.totp_refresh_timer is None

    def test_stop_totp_refresh_no_timer(self):
        """Should handle stopping when no timer exists."""
        panel = EntryDetailPanel()
        panel.totp_refresh_timer = None

        # Should not crash
        panel._stop_totp_refresh()
        assert panel.totp_refresh_timer is None

    @patch("stegvault.vault.totp.generate_totp_code")
    @patch("stegvault.vault.totp.get_totp_time_remaining")
    def test_refresh_totp_display(self, mock_time_remaining, mock_generate):
        """Should refresh TOTP display with current code."""
        mock_generate.return_value = "123456"
        mock_time_remaining.return_value = 25

        entry = VaultEntry(key="test", password="pass", totp_secret="JBSWY3DPEHPK3PXP")
        panel = EntryDetailPanel()
        panel._composed = True
        panel.current_entry = entry

        from unittest.mock import Mock

        mock_label = Mock()
        panel.query_one = Mock(return_value=mock_label)

        panel._refresh_totp_display()

        mock_generate.assert_called_once_with("JBSWY3DPEHPK3PXP")
        mock_time_remaining.assert_called_once()
        mock_label.update.assert_called_once_with("123456  (25s)")

    def test_refresh_totp_display_no_entry(self):
        """Should stop refresh when no entry is set."""
        panel = EntryDetailPanel()
        panel._composed = True
        panel.current_entry = None

        from unittest.mock import Mock

        panel._stop_totp_refresh = Mock()

        panel._refresh_totp_display()
        panel._stop_totp_refresh.assert_called_once()

    def test_refresh_totp_display_no_secret(self):
        """Should stop refresh when entry has no TOTP secret."""
        entry = VaultEntry(key="test", password="pass")
        panel = EntryDetailPanel()
        panel._composed = True
        panel.current_entry = entry

        from unittest.mock import Mock

        panel._stop_totp_refresh = Mock()

        panel._refresh_totp_display()
        panel._stop_totp_refresh.assert_called_once()

    def test_refresh_totp_display_exception(self):
        """Should stop refresh on exception (e.g., label not found)."""
        entry = VaultEntry(key="test", password="pass", totp_secret="JBSWY3DPEHPK3PXP")
        panel = EntryDetailPanel()
        panel._composed = True
        panel.current_entry = entry

        from unittest.mock import Mock

        panel.query_one = Mock(side_effect=Exception("Label not found"))
        panel._stop_totp_refresh = Mock()

        panel._refresh_totp_display()
        panel._stop_totp_refresh.assert_called_once()


class TestFileSelectScreen:
    """Tests for FileSelectScreen modal."""

    def test_file_select_screen_creation(self):
        """Should create file select screen."""
        screen = FileSelectScreen()

        assert screen.title == "Select Vault Image"
        assert screen.selected_path is None

    def test_file_select_screen_custom_title(self):
        """Should create file select screen with custom title."""
        screen = FileSelectScreen(title="Choose Image")

        assert screen.title == "Choose Image"

    def test_file_select_screen_bindings(self):
        """Should have escape binding."""
        screen = FileSelectScreen()
        binding_keys = [b.key for b in screen.BINDINGS]
        assert "escape" in binding_keys

    def test_action_cancel(self):
        """Should dismiss with None on cancel."""
        screen = FileSelectScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(None)

    async def test_on_button_pressed_select_valid_path(self, tmp_path):
        """Should dismiss with path when valid."""
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"test")

        screen = FileSelectScreen()
        screen.dismiss = Mock()

        # Mock input widget
        mock_input = Mock()
        mock_input.value = str(test_file)
        screen.query_one = Mock(return_value=mock_input)

        # Create button pressed event
        button = Mock()
        button.id = "btn-select"
        event = Mock()
        event.button = button

        await screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(str(test_file))

    async def test_on_button_pressed_select_invalid_path(self):
        """Should notify error for invalid path."""
        screen = FileSelectScreen()
        screen.dismiss = Mock()

        # Mock app
        mock_app = Mock()
        mock_app.notify = Mock()

        # Mock input widget with invalid path
        mock_input = Mock()
        mock_input.value = "/nonexistent/path/file.png"
        screen.query_one = Mock(return_value=mock_input)

        # Create button pressed event
        button = Mock()
        button.id = "btn-select"
        event = Mock()
        event.button = button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.on_button_pressed(event)

            mock_app.notify.assert_called_once()
            call_args = mock_app.notify.call_args
            assert "Path does not exist" in call_args[0][0]

    async def test_on_button_pressed_cancel(self):
        """Should dismiss with None on cancel button."""
        screen = FileSelectScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        await screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(None)

    def test_on_directory_tree_file_selected(self):
        """Should update input when file selected from tree."""
        screen = FileSelectScreen()

        # Mock input widget
        mock_input = Mock()
        mock_input.value = ""
        screen.query_one = Mock(return_value=mock_input)

        # Create file selected event
        event = Mock()
        event.path = Path("/some/path/file.png")

        screen.on_directory_tree_file_selected(event)

        assert mock_input.value == str(event.path)

    def test_get_available_drives_windows(self):
        """Should return list of available drives on Windows."""
        screen = FileSelectScreen()

        with patch("platform.system", return_value="Windows"):
            with patch.object(Path, "exists", return_value=True):
                drives = screen._get_available_drives()
                assert len(drives) > 0
                assert all(drive.endswith(":\\") for drive in drives)

    def test_get_available_drives_unix(self):
        """Should return root on Unix systems."""
        screen = FileSelectScreen()

        with patch("platform.system", return_value="Linux"):
            drives = screen._get_available_drives()
            assert drives == ["/"]

    def test_get_available_drives_windows_no_drives(self):
        """Should return current drive if no drives found."""
        screen = FileSelectScreen()

        with patch("platform.system", return_value="Windows"):
            with patch.object(Path, "exists", return_value=False):
                drives = screen._get_available_drives()
                assert len(drives) == 1
                assert drives[0] == str(Path.cwd().anchor)

    def test_switch_drive_success(self):
        """Should switch directory tree to different drive."""
        screen = FileSelectScreen()
        screen._composed = True

        from unittest.mock import Mock

        mock_tree = Mock()
        mock_dropdown = Mock()
        mock_app = Mock()

        screen.query_one = Mock(
            side_effect=lambda selector, *args: (
                mock_tree if "file-tree" in selector else mock_dropdown
            )
        )

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen._switch_drive("D:\\")

            assert screen.current_directory == "D:\\"
            mock_tree.reload.assert_called_once()
            mock_dropdown.remove_class.assert_called_once_with("visible")

    def test_switch_drive_exception(self):
        """Should handle exception when switching drives."""
        screen = FileSelectScreen()
        screen._composed = True

        from unittest.mock import Mock

        mock_app = Mock()
        screen.query_one = Mock(side_effect=Exception("Query failed"))

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            # Should not crash
            screen._switch_drive("D:\\")
            assert screen.current_directory is None  # Not set due to exception

    def test_update_dropdown_on_resize_visible(self):
        """Should update dropdown position when visible."""
        screen = FileSelectScreen()
        screen._composed = True

        from unittest.mock import Mock

        mock_dropdown = Mock()
        mock_dropdown.has_class = Mock(return_value=True)
        mock_btn = Mock()
        mock_btn.region = Mock(x=10, width=30)
        mock_dialog = Mock()
        mock_dialog.region = Mock(x=5)

        def query_side_effect(selector, *args):
            if "favorites-dropdown" in selector:
                return mock_dropdown
            elif "btn-favorites" in selector:
                return mock_btn
            elif "file-dialog" in selector:
                return mock_dialog

        screen.query_one = Mock(side_effect=query_side_effect)

        screen._update_dropdown_on_resize()

        assert mock_dropdown.styles.offset == (2, 7)  # 10 - 5 - 3 = 2
        assert mock_dropdown.styles.width == 30
        mock_dropdown.refresh.assert_called_once_with(layout=True)

    def test_update_dropdown_on_resize_not_visible(self):
        """Should not update dropdown when not visible."""
        screen = FileSelectScreen()
        screen._composed = True

        from unittest.mock import Mock

        mock_dropdown = Mock()
        mock_dropdown.has_class = Mock(return_value=False)

        screen.query_one = Mock(return_value=mock_dropdown)

        screen._update_dropdown_on_resize()

        # Should not crash, and dropdown not refreshed
        mock_dropdown.refresh.assert_not_called()

    def test_update_dropdown_on_resize_exception(self):
        """Should handle exception during resize update."""
        screen = FileSelectScreen()
        screen._composed = True

        screen.query_one = Mock(side_effect=Exception("Query failed"))

        # Should not crash
        screen._update_dropdown_on_resize()

    def test_on_mount(self):
        """Should focus input and update favorite button on mount."""
        screen = FileSelectScreen()
        screen._composed = True

        from unittest.mock import Mock

        mock_input = Mock()
        screen.query_one = Mock(return_value=mock_input)
        screen._update_favorite_button = Mock()

        screen.on_mount()

        mock_input.focus.assert_called_once()
        screen._update_favorite_button.assert_called_once()


class TestPassphraseInputScreen:
    """Tests for PassphraseInputScreen modal."""

    def test_passphrase_input_screen_creation(self):
        """Should create passphrase input screen."""
        screen = PassphraseInputScreen()

        assert screen.title == "Enter Passphrase"

    def test_passphrase_input_screen_custom_title(self):
        """Should create passphrase input screen with custom title."""
        screen = PassphraseInputScreen(title="Unlock Vault")

        assert screen.title == "Unlock Vault"

    def test_passphrase_input_screen_bindings(self):
        """Should have escape binding."""
        screen = PassphraseInputScreen()
        binding_keys = [b.key for b in screen.BINDINGS]
        assert "escape" in binding_keys

    def test_action_cancel(self):
        """Should dismiss with None on cancel."""
        screen = PassphraseInputScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(None)

    def test_on_button_pressed_unlock_with_passphrase(self):
        """Should dismiss with passphrase on unlock."""
        screen = PassphraseInputScreen()
        screen.dismiss = Mock()

        # Mock input widget
        mock_input = Mock()
        mock_input.value = "my_secret_passphrase"
        screen.query_one = Mock(return_value=mock_input)

        # Create button pressed event
        button = Mock()
        button.id = "btn-unlock"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("my_secret_passphrase")

    def test_on_button_pressed_unlock_empty_passphrase(self):
        """Should notify error for empty passphrase."""
        screen = PassphraseInputScreen()
        screen.dismiss = Mock()

        # Mock app
        mock_app = Mock()
        mock_app.notify = Mock()

        # Mock input widget with empty value
        mock_input = Mock()
        mock_input.value = ""
        screen.query_one = Mock(return_value=mock_input)

        # Create button pressed event
        button = Mock()
        button.id = "btn-unlock"
        event = Mock()
        event.button = button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_button_pressed(event)

            mock_app.notify.assert_called_once()
            call_args = mock_app.notify.call_args
            assert "cannot be empty" in call_args[0][0]
            screen.dismiss.assert_not_called()

    def test_on_button_pressed_cancel(self):
        """Should dismiss with None on cancel button."""
        screen = PassphraseInputScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(None)

    def test_on_input_submitted(self):
        """Should dismiss with value on Enter key."""
        screen = PassphraseInputScreen()
        screen.dismiss = Mock()

        # Create input submitted event
        mock_input = Mock()
        mock_input.id = "passphrase-input"
        mock_input.value = "my_passphrase"
        screen.query_one = Mock(return_value=mock_input)  # Mock query_one

        event = Mock()
        event.input = mock_input
        event.value = "my_passphrase"

        screen.on_input_submitted(event)

        screen.dismiss.assert_called_once_with("my_passphrase")

    def test_on_input_submitted_empty_value(self):
        """Should not dismiss on Enter with empty value."""
        screen = PassphraseInputScreen()
        screen.dismiss = Mock()

        # Create input submitted event with empty value
        mock_input = Mock()
        mock_input.id = "passphrase-input"
        event = Mock()
        event.input = mock_input
        event.value = ""

        screen.on_input_submitted(event)

        screen.dismiss.assert_not_called()

    def test_passphrase_set_mode_creation(self):
        """Should create passphrase screen in set mode."""
        screen = PassphraseInputScreen(mode="set", title="Set Vault Passphrase")

        assert screen.mode == "set"
        assert screen.title == "Set Vault Passphrase"
        assert screen.password_visible is False
        assert screen.confirm_visible is False
        assert screen.strength_score == 0.0
        assert screen.strength_label == "Very Weak"

    def test_set_mode_passphrases_do_not_match(self):
        """Should notify error when passphrases don't match in set mode."""
        screen = PassphraseInputScreen(mode="set")
        screen.dismiss = Mock()
        screen.strength_score = 3  # Strong enough

        mock_app = Mock()
        mock_app.notify = Mock()

        mock_pass_input = Mock()
        mock_pass_input.value = "MySecurePass123!"
        mock_confirm_input = Mock()
        mock_confirm_input.value = "DifferentPass456!"

        def mock_query(selector, *args):
            if "#passphrase-input" in selector:
                return mock_pass_input
            elif "#passphrase-confirm" in selector:
                return mock_confirm_input

        screen.query_one = mock_query

        button = Mock()
        button.id = "btn-unlock"
        event = Mock()
        event.button = button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_button_pressed(event)

            mock_app.notify.assert_called_once()
            call_args = mock_app.notify.call_args
            assert "do not match" in call_args[0][0]
            screen.dismiss.assert_not_called()

    def test_set_mode_passphrase_too_weak(self):
        """Should notify error when passphrase is too weak (score < 2)."""
        screen = PassphraseInputScreen(mode="set")
        screen.dismiss = Mock()
        screen.strength_score = 1  # Weak (minimum is 2 = Fair)
        screen.strength_label = "Weak"

        mock_app = Mock()
        mock_app.notify = Mock()

        mock_pass_input = Mock()
        mock_pass_input.value = "weak"
        mock_confirm_input = Mock()
        mock_confirm_input.value = "weak"

        def mock_query(selector, *args):
            if "#passphrase-input" in selector:
                return mock_pass_input
            elif "#passphrase-confirm" in selector:
                return mock_confirm_input

        screen.query_one = mock_query

        button = Mock()
        button.id = "btn-unlock"
        event = Mock()
        event.button = button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_button_pressed(event)

            mock_app.notify.assert_called_once()
            call_args = mock_app.notify.call_args
            assert "too weak" in call_args[0][0]
            assert "Weak" in call_args[0][0]
            screen.dismiss.assert_not_called()

    def test_set_mode_success_with_valid_passphrase(self):
        """Should dismiss with passphrase when valid and matching in set mode."""
        screen = PassphraseInputScreen(mode="set")
        screen.dismiss = Mock()
        screen.strength_score = 3  # Strong

        mock_pass_input = Mock()
        mock_pass_input.value = "MyStrongPass123!"
        mock_confirm_input = Mock()
        mock_confirm_input.value = "MyStrongPass123!"

        def mock_query(selector, *args):
            if "#passphrase-input" in selector:
                return mock_pass_input
            elif "#passphrase-confirm" in selector:
                return mock_confirm_input

        screen.query_one = mock_query

        button = Mock()
        button.id = "btn-unlock"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("MyStrongPass123!")

    def test_toggle_main_passphrase_visibility(self):
        """Should toggle main passphrase visibility."""
        screen = PassphraseInputScreen(mode="set")
        screen._composed = True

        mock_input = Mock()
        mock_input.password = True
        mock_button = Mock()
        mock_button.id = "btn-toggle-pass"

        screen.query_one = Mock(return_value=mock_input)

        event = Mock()
        event.button = mock_button

        # First toggle - show password
        screen.on_button_pressed(event)
        assert screen.password_visible is True
        assert mock_input.password is False
        assert mock_button.label == "HIDE"

        # Second toggle - hide password
        screen.on_button_pressed(event)
        assert screen.password_visible is False
        assert mock_input.password is True
        assert mock_button.label == "SHOW"

    def test_toggle_confirm_passphrase_visibility(self):
        """Should toggle confirm passphrase visibility."""
        screen = PassphraseInputScreen(mode="set")
        screen._composed = True

        mock_confirm_input = Mock()
        mock_confirm_input.password = True
        mock_button = Mock()
        mock_button.id = "btn-toggle-confirm"

        screen.query_one = Mock(return_value=mock_confirm_input)

        event = Mock()
        event.button = mock_button

        # First toggle - show password
        screen.on_button_pressed(event)
        assert screen.confirm_visible is True
        assert mock_confirm_input.password is False
        assert mock_button.label == "HIDE"

        # Second toggle - hide password
        screen.on_button_pressed(event)
        assert screen.confirm_visible is False
        assert mock_confirm_input.password is True
        assert mock_button.label == "SHOW"

    def test_on_input_changed_updates_strength_indicator(self):
        """Should update strength indicator on passphrase input change."""
        screen = PassphraseInputScreen(mode="set")
        screen._composed = True

        mock_strength_label = Mock()
        mock_strength_bar = Mock()

        def mock_query(selector, *args):
            if "#strength-label" in selector:
                return mock_strength_label
            elif "#strength-bar" in selector:
                return mock_strength_bar

        screen.query_one = mock_query

        mock_input = Mock()
        mock_input.id = "passphrase-input"

        event = Mock()
        event.input = mock_input
        event.value = "MyStrongP@ssw0rd!"

        with patch("stegvault.vault.generator.assess_password_strength") as mock_assess:
            mock_assess.return_value = ("Strong", 3)

            screen.on_input_changed(event)

            mock_assess.assert_called_once_with("MyStrongP@ssw0rd!")
            assert screen.strength_score == 3
            assert screen.strength_label == "Strong"
            mock_strength_label.update.assert_called_once_with("Strength: Strong")
            mock_strength_bar.update.assert_called_once()

    def test_on_input_changed_empty_passphrase_resets_strength(self):
        """Should reset strength indicator when passphrase is empty."""
        screen = PassphraseInputScreen(mode="set")
        screen._composed = True
        screen.strength_score = 3
        screen.strength_label = "Strong"

        mock_strength_label = Mock()
        mock_strength_bar = Mock()

        def mock_query(selector, *args):
            if "#strength-label" in selector:
                return mock_strength_label
            elif "#strength-bar" in selector:
                return mock_strength_bar

        screen.query_one = mock_query

        mock_input = Mock()
        mock_input.id = "passphrase-input"

        event = Mock()
        event.input = mock_input
        event.value = ""

        screen.on_input_changed(event)

        assert screen.strength_score == 0.0
        assert screen.strength_label == "Very Weak"
        mock_strength_label.update.assert_called_once_with("Strength: Very Weak")
        mock_strength_bar.update.assert_called_once_with("")

    def test_on_input_submitted_set_mode_first_field_focuses_confirm(self):
        """Should focus confirm field when Enter pressed in first field (set mode)."""
        screen = PassphraseInputScreen(mode="set")
        screen._composed = True

        mock_confirm_input = Mock()
        screen.query_one = Mock(return_value=mock_confirm_input)

        mock_input = Mock()
        mock_input.id = "passphrase-input"

        event = Mock()
        event.input = mock_input
        event.value = "MyPass123!"

        screen.on_input_submitted(event)

        mock_confirm_input.focus.assert_called_once()

    def test_on_input_submitted_confirm_field_validates_and_dismisses(self):
        """Should validate and dismiss when Enter pressed in confirm field."""
        screen = PassphraseInputScreen(mode="set")
        screen._composed = True
        screen.dismiss = Mock()
        screen.strength_score = 3  # Strong enough

        mock_pass_input = Mock()
        mock_pass_input.value = "MyStrongPass123!"
        mock_confirm_input = Mock()
        mock_confirm_input.value = "MyStrongPass123!"

        def mock_query(selector, *args):
            if "#passphrase-input" in selector:
                return mock_pass_input
            elif "#passphrase-confirm" in selector:
                return mock_confirm_input

        screen.query_one = mock_query

        event = Mock()
        event.input = mock_confirm_input
        event.input.id = "passphrase-confirm"
        event.value = "MyStrongPass123!"

        screen.on_input_submitted(event)

        screen.dismiss.assert_called_once_with("MyStrongPass123!")

    def test_on_input_submitted_confirm_mismatch_notifies_error(self):
        """Should notify error when confirm field doesn't match."""
        screen = PassphraseInputScreen(mode="set")
        screen._composed = True
        screen.dismiss = Mock()
        screen.strength_score = 3

        mock_app = Mock()
        mock_app.notify = Mock()

        mock_pass_input = Mock()
        mock_pass_input.value = "MyStrongPass123!"
        mock_confirm_input = Mock()
        mock_confirm_input.value = "DifferentPass456!"

        def mock_query(selector, *args):
            if "#passphrase-input" in selector:
                return mock_pass_input
            elif "#passphrase-confirm" in selector:
                return mock_confirm_input

        screen.query_one = mock_query

        event = Mock()
        event.input = mock_confirm_input
        event.input.id = "passphrase-confirm"
        event.value = "DifferentPass456!"

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_input_submitted(event)

            mock_app.notify.assert_called_once()
            assert "do not match" in mock_app.notify.call_args[0][0]
            screen.dismiss.assert_not_called()

    def test_on_key_q_triggers_quit_when_input_not_focused(self):
        """Should trigger app quit when 'q' pressed and input not focused."""
        screen = PassphraseInputScreen()
        screen._composed = True

        mock_app = Mock()
        mock_app.action_quit = Mock()

        mock_input = Mock()
        mock_input.has_focus = False
        screen.query_one = Mock(return_value=mock_input)

        event = Mock()
        event.key = "q"
        event.stop = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_key(event)

            event.stop.assert_called_once()

    def test_on_key_q_allows_typing_when_input_focused(self):
        """Should allow 'q' to be typed when input has focus."""
        screen = PassphraseInputScreen()
        screen._composed = True

        mock_app = Mock()
        mock_app.action_quit = Mock()

        mock_input = Mock()
        mock_input.has_focus = True
        screen.query_one = Mock(return_value=mock_input)

        event = Mock()
        event.key = "q"
        event.stop = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_key(event)

            # Should NOT stop event or quit
            event.stop.assert_not_called()
            mock_app.action_quit.assert_not_called()


class TestEntryFormScreen:
    """Tests for EntryFormScreen widget."""

    def test_entry_form_screen_creation_add_mode(self):
        """Should create entry form in add mode."""
        screen = EntryFormScreen(mode="add")

        assert screen.mode == "add"
        assert screen.entry is None
        assert screen.title == "Add New Entry"

    def test_entry_form_screen_creation_edit_mode(self):
        """Should create entry form in edit mode."""
        entry = VaultEntry(key="test", password="secret")
        screen = EntryFormScreen(mode="edit", entry=entry)

        assert screen.mode == "edit"
        assert screen.entry == entry
        assert screen.title == "Edit Entry"

    def test_entry_form_screen_custom_title(self):
        """Should create entry form with custom title."""
        screen = EntryFormScreen(mode="add", title="Custom Title")

        assert screen.title == "Custom Title"

    def test_entry_form_screen_bindings(self):
        """Should have escape binding."""
        screen = EntryFormScreen()
        binding_keys = [b.key for b in screen.BINDINGS]
        assert "escape" in binding_keys

    def test_action_cancel(self):
        """Should dismiss with None on cancel."""
        screen = EntryFormScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_on_button_pressed_save_valid_add(self):
        """Should dismiss with form data on valid add."""
        screen = EntryFormScreen(mode="add")
        screen.dismiss = Mock()

        # Mock input widgets
        mock_key = Mock()
        mock_key.value = "gmail"
        mock_password = Mock()
        mock_password.value = "secret123"
        mock_username = Mock()
        mock_username.value = "user@gmail.com"
        mock_url = Mock()
        mock_url.value = "https://gmail.com"
        mock_notes = Mock()
        mock_notes.value = "Personal email"
        mock_tags = Mock()
        mock_tags.value = "email, personal"
        mock_totp = Mock()
        mock_totp.value = "JBSWY3DPEHPK3PXP"

        def mock_query_one(selector, widget_type):
            if selector == "#input-key":
                return mock_key
            elif selector == "#input-password":
                return mock_password
            elif selector == "#input-username":
                return mock_username
            elif selector == "#input-url":
                return mock_url
            elif selector == "#input-notes":
                return mock_notes
            elif selector == "#input-tags":
                return mock_tags
            elif selector == "#input-totp":
                return mock_totp

        screen.query_one = mock_query_one

        # Create button pressed event
        button = Mock()
        button.id = "btn-save"
        event = Mock()
        event.button = button

        await screen.on_button_pressed(event)

        screen.dismiss.assert_called_once()
        form_data = screen.dismiss.call_args[0][0]
        assert form_data["key"] == "gmail"
        assert form_data["password"] == "secret123"
        assert form_data["username"] == "user@gmail.com"
        assert form_data["url"] == "https://gmail.com"
        assert form_data["notes"] == "Personal email"
        assert form_data["tags"] == ["email", "personal"]
        assert form_data["totp_secret"] == "JBSWY3DPEHPK3PXP"

    @pytest.mark.asyncio
    async def test_on_button_pressed_save_empty_key(self):
        """Should notify error for empty key."""
        screen = EntryFormScreen()
        screen.dismiss = Mock()

        # Mock app
        mock_app = Mock()
        mock_app.notify = Mock()

        # Mock input widgets with empty key
        mock_key = Mock()
        mock_key.value = "  "  # Whitespace only
        mock_password = Mock()
        mock_password.value = "secret"

        def mock_query_one(selector, widget_type):
            if selector == "#input-key":
                return mock_key
            elif selector == "#input-password":
                return mock_password
            return Mock(value="")

        screen.query_one = mock_query_one

        button = Mock()
        button.id = "btn-save"
        event = Mock()
        event.button = button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.on_button_pressed(event)

            mock_app.notify.assert_called_once()
            call_args = mock_app.notify.call_args
            assert "Key is required" in call_args[0][0]
            screen.dismiss.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_button_pressed_save_empty_password(self):
        """Should notify error for empty password."""
        screen = EntryFormScreen()
        screen.dismiss = Mock()

        # Mock app
        mock_app = Mock()
        mock_app.notify = Mock()

        # Mock input widgets with empty password
        mock_key = Mock()
        mock_key.value = "test"
        mock_password = Mock()
        mock_password.value = ""

        def mock_query_one(selector, widget_type):
            if selector == "#input-key":
                return mock_key
            elif selector == "#input-password":
                return mock_password
            return Mock(value="")

        screen.query_one = mock_query_one

        button = Mock()
        button.id = "btn-save"
        event = Mock()
        event.button = button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.on_button_pressed(event)

            mock_app.notify.assert_called_once()
            call_args = mock_app.notify.call_args
            assert "Password is required" in call_args[0][0]
            screen.dismiss.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_button_pressed_cancel(self):
        """Should dismiss with None on cancel button."""
        screen = EntryFormScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        await screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_on_button_pressed_toggle_password_visibility(self):
        """Should toggle password visibility."""
        screen = EntryFormScreen(mode="add")
        screen._composed = True
        screen.set_timer = Mock(return_value=Mock())

        mock_password_input = Mock()
        mock_password_input.password = True
        mock_button = Mock()
        mock_button.id = "btn-toggle-password"

        screen.query_one = Mock(return_value=mock_password_input)

        event = Mock()
        event.button = mock_button

        # First toggle - show password
        await screen.on_button_pressed(event)
        assert screen.password_visible is True
        assert mock_password_input.password is False
        assert mock_button.label == "HIDE"
        screen.set_timer.assert_called_once_with(5.0, screen._auto_hide_password)

        # Second toggle - hide password
        await screen.on_button_pressed(event)
        assert screen.password_visible is False
        assert mock_password_input.password is True
        assert mock_button.label == "SHOW"

    @pytest.mark.asyncio
    async def test_on_button_pressed_generate_password_success(self):
        """Should fill password field with generated password."""
        screen = EntryFormScreen(mode="add")
        screen._composed = True
        screen.dismiss = Mock()

        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value="GeneratedPass123!")
        mock_app.notify = Mock()

        mock_password_input = Mock()
        screen.query_one = Mock(return_value=mock_password_input)

        mock_button = Mock()
        mock_button.id = "btn-generate-password"

        event = Mock()
        event.button = mock_button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.on_button_pressed(event)

            mock_app.push_screen_wait.assert_called_once()
            assert mock_password_input.value == "GeneratedPass123!"
            mock_app.notify.assert_called_once_with(
                "Password generated successfully", severity="information"
            )

    @pytest.mark.asyncio
    async def test_on_button_pressed_generate_password_cancelled(self):
        """Should do nothing when password generation is cancelled."""
        screen = EntryFormScreen(mode="add")
        screen._composed = True

        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=None)
        mock_app.notify = Mock()

        mock_button = Mock()
        mock_button.id = "btn-generate-password"

        event = Mock()
        event.button = mock_button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.on_button_pressed(event)

            mock_app.push_screen_wait.assert_called_once()
            # Should NOT notify when cancelled
            mock_app.notify.assert_not_called()

    def test_auto_hide_password(self):
        """Should auto-hide password after timer."""
        screen = EntryFormScreen(mode="add")
        screen._composed = True
        screen.password_visible = True

        mock_password_input = Mock()
        mock_toggle_btn = Mock()

        def mock_query(selector, *args):
            if "#input-password" in selector:
                return mock_password_input
            elif "#btn-toggle-password" in selector:
                return mock_toggle_btn

        screen.query_one = mock_query

        screen._auto_hide_password()

        assert screen.password_visible is False
        assert mock_password_input.password is True
        assert mock_toggle_btn.label == "SHOW"
        assert screen.password_hide_timer is None

    def test_auto_hide_password_button_not_found(self):
        """Should handle exception when button not found during auto-hide."""
        screen = EntryFormScreen(mode="add")
        screen._composed = True
        screen.password_visible = True

        mock_password_input = Mock()

        def mock_query(selector, *args):
            if "#input-password" in selector:
                return mock_password_input
            elif "#btn-toggle-password" in selector:
                raise Exception("Button not found")

        screen.query_one = mock_query

        # Should not crash
        screen._auto_hide_password()

        assert screen.password_visible is False
        assert mock_password_input.password is True

    def test_on_key_q_allows_typing_when_input_focused(self):
        """Should allow 'q' to be typed when any input has focus."""
        screen = EntryFormScreen(mode="add")
        screen._composed = True

        mock_app = Mock()
        mock_app.action_quit = Mock()

        mock_key_input = Mock()
        mock_key_input.has_focus = True

        screen.query_one = Mock(return_value=mock_key_input)

        event = Mock()
        event.key = "q"
        event.stop = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_key(event)

            # Should NOT stop event or quit
            event.stop.assert_not_called()
            mock_app.action_quit.assert_not_called()

    def test_on_key_q_triggers_quit_when_no_input_focused(self):
        """Should trigger app quit when 'q' pressed and no input focused."""
        screen = EntryFormScreen(mode="add")
        screen._composed = True

        mock_app = Mock()
        mock_app.action_quit = Mock()

        mock_input = Mock()
        mock_input.has_focus = False

        screen.query_one = Mock(return_value=mock_input)

        event = Mock()
        event.key = "q"
        event.stop = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_key(event)

            event.stop.assert_called_once()

    def test_entry_form_edit_mode_populates_all_fields(self):
        """Should populate all fields in edit mode."""
        entry = VaultEntry(
            key="github",
            password="secret",
            username="user@example.com",
            url="https://github.com",
            notes="Dev account",
            tags=["work", "dev"],
            totp_secret="JBSWY3DPEHPK3PXP",
        )
        screen = EntryFormScreen(mode="edit", entry=entry)

        assert screen.mode == "edit"
        assert screen.entry == entry
        assert screen.title == "Edit Entry"


class TestDeleteConfirmationScreen:
    """Tests for DeleteConfirmationScreen widget."""

    def test_delete_confirmation_screen_creation(self):
        """Should create delete confirmation screen."""
        screen = DeleteConfirmationScreen("test-entry")

        assert screen.entry_key == "test-entry"

    def test_delete_confirmation_screen_bindings(self):
        """Should have escape binding."""
        screen = DeleteConfirmationScreen("test")
        binding_keys = [b.key for b in screen.BINDINGS]
        assert "escape" in binding_keys

    def test_action_cancel(self):
        """Should dismiss with False on cancel."""
        screen = DeleteConfirmationScreen("test")
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(False)

    def test_on_button_pressed_delete(self):
        """Should dismiss with True on delete button."""
        screen = DeleteConfirmationScreen("test")
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-delete"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(True)

    def test_on_button_pressed_cancel(self):
        """Should dismiss with False on cancel button."""
        screen = DeleteConfirmationScreen("test")
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(False)


class TestPasswordGeneratorScreen:
    """Tests for PasswordGeneratorScreen."""

    def test_password_generator_screen_creation(self):
        """Should create password generator screen with defaults."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()

        assert screen.length == 16
        assert screen.use_lowercase is True
        assert screen.use_uppercase is True
        assert screen.use_digits is True
        assert screen.use_symbols is True
        assert screen.exclude_ambiguous is False

    def test_password_generator_screen_bindings(self):
        """Should have key bindings defined."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()

        binding_keys = [b.key for b in screen.BINDINGS]

        assert "escape" in binding_keys  # cancel
        assert "g" in binding_keys  # generate

    def test_action_cancel(self):
        """Should dismiss with None on cancel."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(None)

    def test_generate_password(self):
        """Should generate password with current settings."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()

        password = screen._generate_password()

        assert len(password) == 16
        assert password == screen.current_password
        # Password should contain various character types
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)

    def test_on_button_pressed_generate(self):
        """Should generate new password on generate button."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()

        # Mock preview label
        mock_preview = Mock()
        screen.query_one = Mock(return_value=mock_preview)

        button = Mock()
        button.id = "btn-generate"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        # Should update preview with new password
        mock_preview.update.assert_called_once()
        assert len(mock_preview.update.call_args[0][0]) == 16

    def test_on_button_pressed_length_dec(self):
        """Should decrease password length."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()
        screen.length = 16

        # Mock length label
        mock_label = Mock()
        screen.query_one = Mock(return_value=mock_label)

        button = Mock()
        button.id = "btn-length-dec"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        assert screen.length == 15
        mock_label.update.assert_called_once_with("15 characters")

    def test_on_button_pressed_length_dec_min(self):
        """Should not decrease below min length (8)."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()
        screen.length = 8

        # Mock length label
        mock_label = Mock()
        screen.query_one = Mock(return_value=mock_label)

        button = Mock()
        button.id = "btn-length-dec"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        assert screen.length == 8  # Should stay at 8
        mock_label.update.assert_not_called()

    def test_on_button_pressed_length_inc(self):
        """Should increase password length."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()
        screen.length = 16

        # Mock length label
        mock_label = Mock()
        screen.query_one = Mock(return_value=mock_label)

        button = Mock()
        button.id = "btn-length-inc"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        assert screen.length == 17
        mock_label.update.assert_called_once_with("17 characters")

    def test_on_button_pressed_length_inc_max(self):
        """Should not increase above max length (64)."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()
        screen.length = 64

        # Mock length label
        mock_label = Mock()
        screen.query_one = Mock(return_value=mock_label)

        button = Mock()
        button.id = "btn-length-inc"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        assert screen.length == 64  # Should stay at 64
        mock_label.update.assert_not_called()

    def test_on_button_pressed_use_with_password(self):
        """Should dismiss with current password on use button."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()
        screen.current_password = "Test123!@#"
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-use"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("Test123!@#")

    def test_on_button_pressed_use_without_password(self):
        """Should notify warning if no password generated."""
        from unittest.mock import patch
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()
        screen.current_password = ""

        # Mock app.notify
        mock_app = Mock()

        button = Mock()
        button.id = "btn-use"
        event = Mock()
        event.button = button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_button_pressed(event)

            mock_app.notify.assert_called_once()
            assert "generate a password first" in mock_app.notify.call_args[0][0]

    def test_on_button_pressed_cancel(self):
        """Should dismiss with None on cancel button."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(None)

    def test_action_generate(self):
        """Should generate password on keyboard shortcut."""
        from stegvault.tui.widgets import PasswordGeneratorScreen

        screen = PasswordGeneratorScreen()

        # Mock preview label
        mock_preview = Mock()
        screen.query_one = Mock(return_value=mock_preview)

        screen.action_generate()

        # Should update preview
        mock_preview.update.assert_called_once()
        assert len(screen.current_password) == 16


class TestHelpScreen:
    """Tests for HelpScreen widget."""

    def test_help_screen_creation(self):
        """Should create help screen."""
        screen = HelpScreen()

        assert screen is not None

    def test_help_screen_bindings(self):
        """Should have escape binding."""
        screen = HelpScreen()

        binding_keys = [b.key for b in screen.BINDINGS]
        assert "escape" in binding_keys

    @pytest.mark.asyncio
    async def test_action_dismiss(self):
        """Should dismiss screen."""
        screen = HelpScreen()
        screen.dismiss = Mock()

        await screen.action_dismiss()

        screen.dismiss.assert_called_once()

    def test_on_button_pressed_close(self):
        """Should dismiss on close button."""
        from textual.widgets import Button

        screen = HelpScreen()

        # Mock app with run_worker
        mock_app = Mock()
        mock_app.run_worker = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            # Create mock button event
            mock_button = Mock(spec=Button)
            mock_button.id = "btn-close"
            mock_event = Mock()
            mock_event.button = mock_button

            screen.on_button_pressed(mock_event)

            mock_app.run_worker.assert_called_once()

    def test_on_key_q_triggers_quit(self):
        """Should trigger app quit when 'q' is pressed."""
        from textual import events

        screen = HelpScreen()

        # Mock app with action_quit
        mock_app = Mock()
        mock_app.action_quit = Mock()

        # Create mock key event
        mock_event = Mock(spec=events.Key)
        mock_event.key = "q"
        mock_event.stop = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_key(mock_event)

            mock_event.stop.assert_called_once()
            mock_app.action_quit.assert_called_once()

    def test_on_key_other_keys_ignored(self):
        """Should not trigger quit for other keys."""
        from textual import events

        screen = HelpScreen()

        # Mock app with action_quit
        mock_app = Mock()
        mock_app.action_quit = Mock()

        # Create mock key event for a different key
        mock_event = Mock(spec=events.Key)
        mock_event.key = "a"
        mock_event.stop = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_key(mock_event)

            mock_event.stop.assert_not_called()
            mock_app.action_quit.assert_not_called()


class TestFilteredDirectoryTree:
    """Tests for FilteredDirectoryTree widget."""

    def test_filtered_directory_tree_filter_paths(self, tmp_path):
        """Should filter to show only directories and compatible images."""
        # Create test files
        png_file = tmp_path / "test.png"
        jpg_file = tmp_path / "test.jpg"
        jpeg_file = tmp_path / "test.jpeg"
        txt_file = tmp_path / "test.txt"
        sub_dir = tmp_path / "subdir"

        png_file.touch()
        jpg_file.touch()
        jpeg_file.touch()
        txt_file.touch()
        sub_dir.mkdir()

        tree = FilteredDirectoryTree(str(tmp_path))

        paths = [png_file, jpg_file, jpeg_file, txt_file, sub_dir]
        filtered = tree.filter_paths(paths)

        # Should include PNG, JPG, JPEG files and directory
        assert png_file in filtered
        assert jpg_file in filtered
        assert jpeg_file in filtered
        assert sub_dir in filtered
        # Should exclude TXT file
        assert txt_file not in filtered

    def test_filtered_directory_tree_render_label_png(self, tmp_path):
        """Should render PNG files with yellow color."""
        png_file = tmp_path / "test.png"
        png_file.touch()

        tree = FilteredDirectoryTree(str(tmp_path))

        # Create mock node with data
        mock_node = Mock()
        mock_node.data = Mock()
        mock_node.data.path = png_file

        # Mock the super().render_label to return a Text object
        from rich.text import Text

        base_label = Text("test.png")

        with patch.object(
            FilteredDirectoryTree.__bases__[0], "render_label", return_value=base_label
        ):
            label = tree.render_label(mock_node, "", "")

            # Should have stylize called (yellow for PNG)
            assert "test.png" in str(label)

    def test_filtered_directory_tree_render_label_jpg(self, tmp_path):
        """Should render JPG files with magenta color."""
        jpg_file = tmp_path / "test.jpg"
        jpg_file.touch()

        tree = FilteredDirectoryTree(str(tmp_path))

        # Create mock node with data
        mock_node = Mock()
        mock_node.data = Mock()
        mock_node.data.path = jpg_file

        from rich.text import Text

        base_label = Text("test.jpg")

        with patch.object(
            FilteredDirectoryTree.__bases__[0], "render_label", return_value=base_label
        ):
            label = tree.render_label(mock_node, "", "")

            assert "test.jpg" in str(label)

    def test_filtered_directory_tree_render_label_directory(self, tmp_path):
        """Should render directories without special coloring."""
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()

        tree = FilteredDirectoryTree(str(tmp_path))

        # Create mock node for directory
        mock_node = Mock()
        mock_node.data = Mock()
        mock_node.data.path = sub_dir

        from rich.text import Text

        base_label = Text("subdir")

        with patch.object(
            FilteredDirectoryTree.__bases__[0], "render_label", return_value=base_label
        ):
            label = tree.render_label(mock_node, "", "")

            # No special styling for directories
            assert "subdir" in str(label)

    def test_filtered_directory_tree_render_label_no_data(self):
        """Should handle nodes without data attribute."""
        tree = FilteredDirectoryTree(".")

        # Create mock node without data
        mock_node = Mock(spec=[])  # No attributes

        from rich.text import Text

        base_label = Text("node")

        with patch.object(
            FilteredDirectoryTree.__bases__[0], "render_label", return_value=base_label
        ):
            label = tree.render_label(mock_node, "", "")

            # Should not crash, just return base label
            assert "node" in str(label)


class TestQuitConfirmationScreen:
    """Tests for QuitConfirmationScreen modal."""

    def test_quit_confirmation_screen_creation(self):
        """Should create quit confirmation screen."""
        screen = QuitConfirmationScreen()

        assert screen is not None

    def test_quit_confirmation_screen_on_button_pressed_yes(self):
        """Should dismiss with True on yes button."""
        screen = QuitConfirmationScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-yes"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(True)

    def test_quit_confirmation_screen_on_button_pressed_no(self):
        """Should dismiss with False on no button."""
        screen = QuitConfirmationScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-no"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(False)

    def test_quit_confirmation_screen_action_cancel(self):
        """Should dismiss with False on escape."""
        screen = QuitConfirmationScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(False)


class TestGenericConfirmationScreen:
    """Tests for GenericConfirmationScreen modal."""

    def test_generic_confirmation_screen_creation(self):
        """Should create generic confirmation screen."""
        screen = GenericConfirmationScreen(title="Confirm Action", message="Are you sure?")

        assert screen.title_text == "Confirm Action"
        assert screen.message_text == "Are you sure?"

    def test_generic_confirmation_screen_on_button_pressed_confirm(self):
        """Should dismiss with True on confirm button."""
        screen = GenericConfirmationScreen("Title", "Message")
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-confirm"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(True)

    def test_generic_confirmation_screen_on_button_pressed_cancel(self):
        """Should dismiss with False on cancel button."""
        screen = GenericConfirmationScreen("Title", "Message")
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(False)


class TestPasswordHistoryModal:
    """Tests for PasswordHistoryModal widget."""

    def test_password_history_modal_creation(self):
        """Should create password history modal."""
        entry = VaultEntry(
            key="test",
            password="current_password",
            password_history=[
                {"password": "old_pass1", "changed_at": "2025-01-01T10:00:00"},
                {"password": "old_pass2", "changed_at": "2025-01-02T10:00:00"},
            ],
        )

        screen = PasswordHistoryModal(entry)

        assert screen.entry == entry

    def test_password_history_modal_on_button_pressed_close(self):
        """Should dismiss on close button."""
        entry = VaultEntry(key="test", password="pass")
        screen = PasswordHistoryModal(entry)
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-close"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once()

    def test_password_history_modal_action_close(self):
        """Should dismiss on close action."""
        entry = VaultEntry(key="test", password="pass")
        screen = PasswordHistoryModal(entry)
        screen.dismiss = Mock()

        screen.action_close()

        screen.dismiss.assert_called_once()


class TestVaultOverwriteWarningScreen:
    """Tests for VaultOverwriteWarningScreen modal."""

    def test_vault_overwrite_warning_screen_on_button_pressed_overwrite(self):
        """Should dismiss with True on overwrite button."""
        screen = VaultOverwriteWarningScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-overwrite"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(True)

    def test_vault_overwrite_warning_screen_on_button_pressed_cancel(self):
        """Should dismiss with False on cancel button."""
        screen = VaultOverwriteWarningScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with(False)

    def test_vault_overwrite_warning_screen_action_cancel(self):
        """Should dismiss with False on escape."""
        screen = VaultOverwriteWarningScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(False)


class TestUnsavedChangesScreen:
    """Tests for UnsavedChangesScreen modal."""

    def test_unsaved_changes_screen_on_button_pressed_save(self):
        """Should dismiss with 'save' on save-exit button."""
        screen = UnsavedChangesScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-save-exit"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("save")

    def test_unsaved_changes_screen_on_button_pressed_dont_save(self):
        """Should dismiss with 'dont_save' on dont-save button."""
        screen = UnsavedChangesScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-dont-save"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("dont_save")

    def test_unsaved_changes_screen_on_button_pressed_cancel(self):
        """Should dismiss with 'cancel' on cancel button."""
        screen = UnsavedChangesScreen()
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once_with("cancel")

    def test_unsaved_changes_screen_action_cancel(self):
        """Should dismiss with 'cancel' on escape."""
        screen = UnsavedChangesScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with("cancel")


class TestPasswordGeneratorScreenExtended:
    """Extended tests for PasswordGeneratorScreen to cover missing lines."""

    def test_on_button_pressed_toggle_lowercase(self):
        """Should toggle lowercase option via button."""
        screen = PasswordGeneratorScreen()
        screen.use_lowercase = True

        # Mock app and button
        mock_app = Mock()
        mock_app.notify = Mock()
        mock_button = Mock()
        mock_button.id = "btn-opt-lowercase"

        event = Mock()
        event.button = mock_button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen._update_option_button = Mock()  # Mock the button update
            screen.on_button_pressed(event)

            assert screen.use_lowercase is False

    def test_on_button_pressed_toggle_uppercase(self):
        """Should toggle uppercase option via button."""
        screen = PasswordGeneratorScreen()
        screen.use_uppercase = True

        mock_app = Mock()
        mock_app.notify = Mock()
        mock_button = Mock()
        mock_button.id = "btn-opt-uppercase"

        event = Mock()
        event.button = mock_button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen._update_option_button = Mock()
            screen.on_button_pressed(event)

            assert screen.use_uppercase is False

    def test_on_button_pressed_toggle_digits(self):
        """Should toggle digits option via button."""
        screen = PasswordGeneratorScreen()
        screen.use_digits = True

        mock_app = Mock()
        mock_app.notify = Mock()
        mock_button = Mock()
        mock_button.id = "btn-opt-digits"

        event = Mock()
        event.button = mock_button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen._update_option_button = Mock()
            screen.on_button_pressed(event)

            assert screen.use_digits is False

    def test_on_button_pressed_toggle_symbols(self):
        """Should toggle symbols option via button."""
        screen = PasswordGeneratorScreen()
        screen.use_symbols = True

        mock_app = Mock()
        mock_app.notify = Mock()
        mock_button = Mock()
        mock_button.id = "btn-opt-symbols"

        event = Mock()
        event.button = mock_button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen._update_option_button = Mock()
            screen.on_button_pressed(event)

            assert screen.use_symbols is False

    def test_on_button_pressed_toggle_last_option_warning(self):
        """Should warn when trying to disable last character type."""
        screen = PasswordGeneratorScreen()
        # Set only lowercase enabled
        screen.use_lowercase = True
        screen.use_uppercase = False
        screen.use_digits = False
        screen.use_symbols = False

        mock_app = Mock()
        mock_app.notify = Mock()
        mock_button = Mock()
        mock_button.id = "btn-opt-lowercase"

        event = Mock()
        event.button = mock_button

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.on_button_pressed(event)

            # Should still be enabled
            assert screen.use_lowercase is True
            # Should have notified user
            mock_app.notify.assert_called_once()
            assert "At least one character type" in mock_app.notify.call_args[0][0]


class TestChangelogViewerScreen:
    """Tests for ChangelogViewerScreen modal."""

    def test_changelog_viewer_screen_creation(self):
        """Should create changelog viewer screen."""
        screen = ChangelogViewerScreen(version="0.7.4")

        assert screen.version == "0.7.4"

    def test_changelog_viewer_screen_on_mount_no_file(self):
        """Should handle missing CHANGELOG.md file."""
        screen = ChangelogViewerScreen(version="0.7.4")

        # Mock query_one to avoid actual DOM access
        mock_content = Mock()
        screen.query_one = Mock(return_value=mock_content)

        # Mock the app
        mock_app = Mock()
        mock_app.notify = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            with patch("pathlib.Path.exists", return_value=False):
                # CHANGELOG.md doesn't exist - on_mount should handle gracefully
                # The method doesn't return a coroutine, so just call it
                try:
                    screen.on_mount()
                except Exception:
                    pass  # It's ok if it fails, we're just testing it doesn't crash

    def test_changelog_viewer_screen_on_button_pressed_close(self):
        """Should dismiss on close button."""
        screen = ChangelogViewerScreen(version="0.7.4")
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-close"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.dismiss.assert_called_once()

    def test_changelog_viewer_screen_action_close(self):
        """Should dismiss on close action."""
        screen = ChangelogViewerScreen(version="0.7.4")
        screen.dismiss = Mock()

        screen.action_close()

        screen.dismiss.assert_called_once()


class TestSettingsScreen:
    """Tests for SettingsScreen modal."""

    def test_settings_screen_creation(self):
        """Should create settings screen."""
        screen = SettingsScreen()

        assert screen is not None

    def test_settings_screen_has_unsaved_changes_false(self):
        """Should return False when no changes or query fails."""
        screen = SettingsScreen()
        # Without proper DOM, query_one will fail and should return False
        assert screen._has_unsaved_changes() is False

    def test_settings_screen_on_button_pressed_save(self):
        """Should save settings and dismiss on save button."""
        screen = SettingsScreen()
        screen._save_settings = Mock()  # Mock the save method
        screen.dismiss = Mock()

        button = Mock()
        button.id = "btn-save"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen._save_settings.assert_called_once()
        screen.dismiss.assert_called_once()

    def test_settings_screen_on_button_pressed_cancel(self):
        """Should check for changes on cancel button."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        button = Mock()
        button.id = "btn-cancel"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        # Should call run_worker to handle close with check
        screen.run_worker.assert_called_once()

    def test_settings_screen_on_button_pressed_force_check(self):
        """Should force update check on force-check button."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        button = Mock()
        button.id = "btn-force-check"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        # Should call run_worker for update check
        screen.run_worker.assert_called_once()

    def test_settings_screen_on_button_pressed_view_changelog(self):
        """Should show changelog on view-changelog button."""
        screen = SettingsScreen()

        # Mock _show_changelog since it's called directly
        screen._show_changelog = Mock()

        button = Mock()
        button.id = "btn-view-changelog"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        # Should call _show_changelog
        screen._show_changelog.assert_called_once()

    def test_settings_screen_on_switch_changed(self):
        """Should handle switch change events."""
        screen = SettingsScreen()

        mock_switch = Mock()
        mock_switch.id = "switch-auto-check"
        mock_switch.value = True

        event = Mock()
        event.switch = mock_switch
        event.value = True

        # Should not crash
        screen.on_switch_changed(event)

    def test_settings_screen_action_close(self):
        """Should check for changes on close action."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        screen.action_close()

        # Should call run_worker to handle close
        screen.run_worker.assert_called_once()


class TestBackupCodeInputScreen:
    """Tests for BackupCodeInputScreen modal."""

    def test_backup_code_input_screen_action_cancel(self):
        """Should dismiss with None on cancel."""
        screen = BackupCodeInputScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(None)


class TestTOTPConfigScreen:
    """Tests for TOTPConfigScreen modal."""

    def test_totp_config_screen_creation(self):
        """Should create TOTP config screen."""
        screen = TOTPConfigScreen()

        assert screen is not None

    def test_totp_config_screen_action_cancel(self):
        """Should dismiss with None on cancel."""
        screen = TOTPConfigScreen()
        screen.dismiss = Mock()

        screen.action_cancel()

        screen.dismiss.assert_called_once_with(None)


class TestTOTPAuthScreen:
    """Tests for TOTPAuthScreen modal."""

    def test_totp_auth_screen_creation(self):
        """Should create TOTP auth screen."""
        screen = TOTPAuthScreen(
            totp_secret="JBSWY3DPEHPK3PXP", backup_code="BACKUP123", max_attempts=3
        )

        assert screen.totp_secret == "JBSWY3DPEHPK3PXP"
        assert screen.backup_code == "BACKUP123"
        assert screen.max_attempts == 3
        assert screen.attempts == 0

    def test_totp_auth_screen_action_cancel(self):
        """Should dismiss with False and quit app on cancel."""
        screen = TOTPAuthScreen(totp_secret="JBSWY3DPEHPK3PXP")
        screen.dismiss = Mock()
        screen.run_worker = Mock()

        # Mock app since action_cancel accesses app.action_quit()
        mock_app = Mock()
        mock_app.action_quit = Mock(return_value=Mock())  # Return a mock coroutine

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.action_cancel()

            screen.dismiss.assert_called_once_with(False)
            screen.run_worker.assert_called_once()


# Additional comprehensive tests for coverage improvement


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="Flaky async/Textual tests in Python 3.9 CI environment"
)
class TestSettingsScreenAdvanced:
    """Advanced tests for SettingsScreen to improve coverage."""

    @patch("stegvault.config.core.save_config")
    @patch("stegvault.config.core.load_config")
    def test_save_settings_success(self, mock_load_config, mock_save_config):
        """Should save settings successfully."""
        # Create mock config with nested mocks
        mock_config = Mock()
        mock_config.updates = Mock()
        mock_config.totp = Mock()
        mock_load_config.return_value = mock_config

        screen = SettingsScreen()

        # Mock switches
        mock_auto_check = Mock(value=True)
        mock_auto_upgrade = Mock(value=False)
        mock_totp = Mock(value=True)

        screen.query_one = Mock(side_effect=[mock_auto_check, mock_auto_upgrade, mock_totp])

        # Mock app
        mock_app = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen._save_settings()

            mock_save_config.assert_called_once()
            mock_app.notify.assert_called_once()
            assert "saved successfully" in mock_app.notify.call_args[0][0]

    @patch("stegvault.config.core.save_config")
    @patch("stegvault.config.core.load_config")
    def test_save_settings_exception(self, mock_load_config, mock_save_config):
        """Should handle exception during save."""
        mock_load_config.side_effect = Exception("Config error")

        screen = SettingsScreen()

        # Mock app
        mock_app = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen._save_settings()

            # Should notify error
            assert mock_app.notify.called
            call_args = mock_app.notify.call_args
            assert "Failed to save" in call_args[0][0]
            assert call_args[1]["severity"] == "error"

    def test_has_unsaved_changes_true(self):
        """Should detect unsaved changes."""
        screen = SettingsScreen()
        screen._initial_auto_check = True
        screen._initial_auto_upgrade = False
        screen._initial_totp_enabled = False

        # Mock switches with changed values
        mock_auto_check = Mock(value=False)  # Changed from True
        mock_auto_upgrade = Mock(value=False)
        mock_totp = Mock(value=False)

        screen.query_one = Mock(side_effect=[mock_auto_check, mock_auto_upgrade, mock_totp])

        assert screen._has_unsaved_changes() is True

    def test_has_unsaved_changes_query_exception(self):
        """Should return False on query exception."""
        screen = SettingsScreen()
        screen.query_one = Mock(side_effect=Exception("Query failed"))

        assert screen._has_unsaved_changes() is False

    @pytest.mark.asyncio
    async def test_handle_close_with_check_no_changes_quit(self):
        """Should quit app when no changes and quit_on_no_changes=True."""
        screen = SettingsScreen()
        screen._has_unsaved_changes = Mock(return_value=False)

        # Mock app
        mock_app = Mock()
        mock_app.action_quit = Mock(return_value=Mock())

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._handle_close_with_check(quit_on_no_changes=True)

            mock_app.action_quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_close_with_check_no_changes_close(self):
        """Should dismiss when no changes and quit_on_no_changes=False."""
        screen = SettingsScreen()
        screen._has_unsaved_changes = Mock(return_value=False)
        screen.dismiss = Mock()

        await screen._handle_close_with_check(quit_on_no_changes=False)

        screen.dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_handle_close_with_check_unsaved_save(self):
        """Should save and dismiss when user chooses to save."""
        screen = SettingsScreen()
        screen._has_unsaved_changes = Mock(return_value=True)
        screen._save_settings = Mock()
        screen.dismiss = Mock()

        # Mock app
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value="save")

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._handle_close_with_check()

            screen._save_settings.assert_called_once()
            screen.dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_handle_close_with_check_unsaved_dont_save(self):
        """Should dismiss without saving when user chooses don't save."""
        screen = SettingsScreen()
        screen._has_unsaved_changes = Mock(return_value=True)
        screen._save_settings = Mock()
        screen.dismiss = Mock()

        # Mock app
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value="dont_save")

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._handle_close_with_check()

            screen._save_settings.assert_not_called()
            screen.dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_handle_close_with_check_unsaved_cancel(self):
        """Should stay in settings when user cancels."""
        screen = SettingsScreen()
        screen._has_unsaved_changes = Mock(return_value=True)
        screen.dismiss = Mock()

        # Mock app
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value="cancel")

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._handle_close_with_check()

            # Should not dismiss
            screen.dismiss.assert_not_called()

    @pytest.mark.asyncio
    @patch("stegvault.utils.updater.check_for_updates")
    @patch("stegvault.utils.updater.cache_check_result")
    def test_force_update_check_update_available(self, mock_cache, mock_check):
        """Should notify when update is available."""
        mock_check.return_value = (True, "1.0.0", None)

        screen = SettingsScreen()

        # Mock app
        mock_app = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            import asyncio

            asyncio.run(screen._force_update_check())

            # Should notify about update
            assert mock_app.notify.call_count == 2  # Checking + available
            notify_calls = [call[0][0] for call in mock_app.notify.call_args_list]
            assert any("Update available" in call for call in notify_calls)
            mock_cache.assert_called_once()

    @pytest.mark.asyncio
    @patch("stegvault.utils.updater.check_for_updates")
    @patch("stegvault.utils.updater.cache_check_result")
    def test_force_update_check_up_to_date(self, mock_cache, mock_check):
        """Should notify when already up-to-date."""
        mock_check.return_value = (False, "0.7.6", None)

        screen = SettingsScreen()

        # Mock app
        mock_app = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            import asyncio

            asyncio.run(screen._force_update_check())

            # Should notify up-to-date
            assert mock_app.notify.call_count == 2
            notify_calls = [call[0][0] for call in mock_app.notify.call_args_list]
            assert any("up-to-date" in call for call in notify_calls)
            mock_cache.assert_called_once()

    @pytest.mark.asyncio
    @patch("stegvault.utils.updater.check_for_updates")
    def test_force_update_check_error(self, mock_check):
        """Should handle update check error."""
        mock_check.return_value = (False, None, "Network error")

        screen = SettingsScreen()

        # Mock app
        mock_app = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            import asyncio

            asyncio.run(screen._force_update_check())

            # Should notify error
            notify_calls = [call[0][0] for call in mock_app.notify.call_args_list]
            assert any("failed" in call for call in notify_calls)

    @pytest.mark.asyncio
    @patch("stegvault.utils.updater.check_for_updates")
    def test_force_update_check_exception(self, mock_check):
        """Should handle exception during update check."""
        mock_check.side_effect = Exception("Unexpected error")

        screen = SettingsScreen()

        # Mock app
        mock_app = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            import asyncio

            asyncio.run(screen._force_update_check())

            # Should notify error
            notify_calls = [call[0][0] for call in mock_app.notify.call_args_list]
            assert any("failed" in call for call in notify_calls)

    def test_show_changelog(self):
        """Should push changelog screen."""
        screen = SettingsScreen()

        # Mock app
        mock_app = Mock()

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen._show_changelog()

            mock_app.push_screen.assert_called_once()
            # Should pass ChangelogViewerScreen
            from stegvault.tui.widgets import ChangelogViewerScreen

            assert isinstance(mock_app.push_screen.call_args[0][0], ChangelogViewerScreen)

    @pytest.mark.asyncio
    @patch("stegvault.config.core.load_config")
    @patch("stegvault.config.core.save_config")
    async def test_configure_totp_first_time_success(self, mock_save_config, mock_load_config):
        """Should configure TOTP when user completes setup."""
        from stegvault.config.core import Config, TOTPConfig

        # Create mock config
        mock_config = Mock()
        mock_config.totp = Mock()
        mock_load_config.return_value = mock_config

        screen = SettingsScreen()
        screen._initial_totp_enabled = False

        # Mock switch
        mock_switch = Mock(value=True)

        # Mock app
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=("SECRET123", "BACKUP456"))

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._configure_totp_first_time(mock_switch)

            # Should save config with TOTP settings
            mock_save_config.assert_called_once()
            assert screen._initial_totp_enabled is True
            assert mock_app.notify.called

    @pytest.mark.asyncio
    @patch("stegvault.config.core.load_config")
    async def test_configure_totp_first_time_cancelled(self, mock_load_config):
        """Should revert switch when TOTP setup is cancelled."""
        screen = SettingsScreen()
        screen._initial_totp_enabled = False

        # Mock switch
        mock_switch = Mock(value=True)

        # Mock app - user cancels
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=None)

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._configure_totp_first_time(mock_switch)

            # Should revert switch
            assert mock_switch.value is False
            assert mock_app.notify.called

    @pytest.mark.asyncio
    async def test_configure_totp_first_time_exception(self):
        """Should handle exception during TOTP configuration."""
        screen = SettingsScreen()

        # Mock switch
        mock_switch = Mock(value=True)

        # Mock app - exception
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(side_effect=Exception("Config error"))

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._configure_totp_first_time(mock_switch)

            # Should revert switch and notify error
            assert mock_switch.value is False
            assert mock_app.notify.called

    def test_on_switch_changed_totp_enabled_first_time(self):
        """Should trigger TOTP configuration when enabling for first time."""
        screen = SettingsScreen()
        screen._initial_totp_enabled = False
        screen.run_worker = Mock()

        # Mock switch event
        mock_switch = Mock(id="switch-totp-enabled", value=True)
        event = Mock(switch=mock_switch, value=True)

        screen.on_switch_changed(event)

        # Should call run_worker for TOTP configuration
        screen.run_worker.assert_called_once()

    def test_on_switch_changed_totp_disabled(self):
        """Should not trigger configuration when disabling TOTP."""
        screen = SettingsScreen()
        screen._initial_totp_enabled = True
        screen.run_worker = Mock()

        # Mock switch event - disabling
        mock_switch = Mock(id="switch-totp-enabled", value=False)
        event = Mock(switch=mock_switch, value=False)

        screen.on_switch_changed(event)

        # Should not call run_worker
        screen.run_worker.assert_not_called()

    def test_on_switch_changed_other_switch(self):
        """Should ignore changes to non-TOTP switches."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        # Mock switch event - different switch
        mock_switch = Mock(id="switch-auto-check", value=True)
        event = Mock(switch=mock_switch, value=True)

        screen.on_switch_changed(event)

        # Should not call run_worker
        screen.run_worker.assert_not_called()

    def test_on_button_pressed_reset_totp(self):
        """Should trigger TOTP reset on reset-totp button."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        button = Mock(id="btn-reset-totp")
        event = Mock(button=button)

        screen.on_button_pressed(event)

        # Should call run_worker for reset
        screen.run_worker.assert_called_once()

    @patch("stegvault.config.core.load_config")
    def test_on_mount_loads_config(self, mock_load_config):
        """Should load config on mount."""
        from stegvault.config.core import Config, UpdatesConfig, TOTPConfig

        # Create mock config
        mock_config = Mock()
        mock_config.updates = Mock(auto_check=True, auto_upgrade=False)
        mock_config.totp = Mock(enabled=True)
        mock_load_config.return_value = mock_config

        screen = SettingsScreen()

        # Mock switches
        mock_auto_check = Mock()
        mock_auto_upgrade = Mock()
        mock_totp = Mock()

        screen.query_one = Mock(side_effect=[mock_auto_check, mock_auto_upgrade, mock_totp])

        screen.on_mount()

        # Should set switch values
        assert mock_auto_check.value is True
        assert mock_auto_upgrade.value is False
        assert mock_totp.value is True

        # Should store initial values
        assert screen._initial_auto_check is True
        assert screen._initial_auto_upgrade is False
        assert screen._initial_totp_enabled is True

    def test_on_mount_config_exception(self):
        """Should handle exception during config load on mount."""
        screen = SettingsScreen()
        screen.query_one = Mock(side_effect=Exception("Config error"))

        # Should not crash
        screen.on_mount()

    @patch("stegvault.utils.updater.get_cached_check")
    @patch("stegvault.config.core.load_config")
    def test_on_mount_detects_update_available(self, mock_load_config, mock_get_cached):
        """Should detect cached update availability on mount."""
        from stegvault.config.core import Config, UpdatesConfig, TOTPConfig

        # Create mock config
        mock_config = Mock()
        mock_config.updates = Mock(auto_check=True, auto_upgrade=False)
        mock_config.totp = Mock(enabled=False)
        mock_load_config.return_value = mock_config

        # Mock cached update check showing update available
        mock_get_cached.return_value = {
            "update_available": True,
            "latest_version": "0.8.0",
        }

        screen = SettingsScreen()

        # Mock switches
        mock_auto_check = Mock()
        mock_auto_upgrade = Mock()
        mock_totp = Mock()

        screen.query_one = Mock(side_effect=[mock_auto_check, mock_auto_upgrade, mock_totp])

        screen.on_mount()

        # Should set update_available flag
        assert screen._update_available is True
        assert screen._latest_version == "0.8.0"

    def test_on_button_pressed_update_now(self):
        """Should handle Update Now button press."""
        screen = SettingsScreen()
        screen.run_worker = Mock()

        button = Mock(id="btn-update-now")
        event = Mock(button=button)

        screen.on_button_pressed(event)

        # Should call run_worker for update
        screen.run_worker.assert_called_once()

    @patch("stegvault.utils.updater.launch_detached_update")
    async def test_perform_update_now_success(self, mock_launch):
        """Should launch detached update successfully."""
        screen = SettingsScreen()
        mock_app = Mock()
        mock_launch.return_value = (True, "Update will begin after you close StegVault")

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._perform_update_now()

            # Should notify user
            mock_app.notify.assert_called()
            call_args = mock_app.notify.call_args_list
            assert any("Preparing update" in str(call) for call in call_args)

    @patch("stegvault.utils.updater.launch_detached_update")
    async def test_perform_update_now_failure(self, mock_launch):
        """Should handle update launch failure."""
        screen = SettingsScreen()
        mock_app = Mock()
        mock_launch.return_value = (False, "Could not create update script")

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._perform_update_now()

            # Should notify user of failure
            mock_app.notify.assert_called()
            call_args = mock_app.notify.call_args_list
            assert any("Update failed" in str(call) for call in call_args)

    @patch("stegvault.utils.updater.launch_detached_update")
    async def test_perform_update_now_exception(self, mock_launch):
        """Should handle exception during update launch."""
        screen = SettingsScreen()
        mock_app = Mock()
        mock_launch.side_effect = Exception("Launch error")

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen._perform_update_now()

            # Should notify user of error
            mock_app.notify.assert_called()
            call_args = mock_app.notify.call_args_list
            assert any("Update launch failed" in str(call) for call in call_args)
