"""
Tests for TUI screens.

Tests the VaultScreen for StegVault TUI.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from stegvault.tui.screens import VaultScreen
from stegvault.vault import Vault, VaultEntry
from stegvault.app.controllers import VaultController, VaultSaveResult


class TestVaultScreen:
    """Tests for VaultScreen."""

    def test_vault_screen_creation(self):
        """Should create vault screen."""
        vault = Vault(entries=[])
        controller = VaultController()

        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        assert screen.vault == vault
        assert screen.image_path == "test.png"
        assert screen.passphrase == "passphrase"
        assert screen.controller == controller
        assert screen.selected_entry is None

    def test_vault_screen_bindings(self):
        """Should have key bindings defined."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        binding_keys = [b.key for b in screen.BINDINGS]

        assert "escape" in binding_keys  # back
        assert "a" in binding_keys  # add entry
        assert "e" in binding_keys  # edit entry
        assert "d" in binding_keys  # delete entry
        assert "c" in binding_keys  # copy password
        assert "v" in binding_keys  # toggle password
        assert "s" in binding_keys  # save vault
        assert "q" in binding_keys  # quit

    def test_action_back(self):
        """Should call app.pop_screen."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        # Create a mock parent with app
        mock_app = Mock()
        mock_app.pop_screen = Mock()
        screen._parent = Mock()
        screen._parent.app = mock_app

        # Patch the app property to return mock_app
        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.action_back()
            mock_app.pop_screen.assert_called_once()

    def test_action_quit(self):
        """Should call app.exit."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        # Create a mock parent with app
        mock_app = Mock()
        mock_app.exit = Mock()
        screen._parent = Mock()
        screen._parent.app = mock_app

        # Patch the app property to return mock_app
        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            screen.action_quit()
            mock_app.exit.assert_called_once()

    def test_action_refresh(self):
        """Should notify refresh feature."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()

        screen.action_refresh()

        screen.notify.assert_called_once()
        call_args = screen.notify.call_args
        assert "Coming soon" in call_args[0][0]

    def test_action_copy_password_no_entry(self):
        """Should warn when no entry selected."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()

        screen.action_copy_password()

        screen.notify.assert_called_once()
        call_args = screen.notify.call_args
        assert "No entry selected" in call_args[0][0]
        assert call_args[1]["severity"] == "warning"

    def test_action_copy_password_success(self):
        """Should copy password to clipboard."""
        entry = VaultEntry(key="test", password="secret123")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry
        screen.notify = Mock()

        # Mock pyperclip at import level
        with patch("pyperclip.copy") as mock_copy:
            screen.action_copy_password()

            mock_copy.assert_called_once_with("secret123")
            screen.notify.assert_called_once()
            call_args = screen.notify.call_args
            assert "Password copied" in call_args[0][0]
            assert "test" in call_args[0][0]

    def test_action_copy_password_failure(self):
        """Should handle clipboard copy failure."""
        entry = VaultEntry(key="test", password="secret")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry
        screen.notify = Mock()

        # Mock pyperclip to raise exception
        with patch("pyperclip.copy", side_effect=Exception("Clipboard error")):
            screen.action_copy_password()

            screen.notify.assert_called_once()
            call_args = screen.notify.call_args
            assert "Failed to copy password" in call_args[0][0]
            assert call_args[1]["severity"] == "error"

    def test_action_toggle_password_no_entry(self):
        """Should warn when no entry selected."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()

        screen.action_toggle_password()

        screen.notify.assert_called_once()
        call_args = screen.notify.call_args
        assert "No entry selected" in call_args[0][0]
        assert call_args[1]["severity"] == "warning"

    def test_action_toggle_password_success(self):
        """Should toggle password visibility."""
        entry = VaultEntry(key="test", password="secret")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry

        # Mock detail panel
        mock_panel = Mock()
        mock_panel.toggle_password_visibility = Mock()
        screen.query_one = Mock(return_value=mock_panel)

        screen.action_toggle_password()

        mock_panel.toggle_password_visibility.assert_called_once()

    def test_on_button_pressed_copy(self):
        """Should handle copy button press."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.action_copy_password = Mock()

        button = Mock()
        button.id = "btn-copy"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.action_copy_password.assert_called_once()

    def test_on_button_pressed_toggle(self):
        """Should handle toggle button press."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.action_toggle_password = Mock()

        button = Mock()
        button.id = "btn-toggle"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.action_toggle_password.assert_called_once()

    def test_on_button_pressed_back(self):
        """Should handle back button press."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.action_back = Mock()

        button = Mock()
        button.id = "btn-back"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.action_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_add_entry_success(self):
        """Should add new entry successfully."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()
        screen._refresh_entry_list = Mock()

        # Mock push_screen_wait to return form data
        form_data = {
            "key": "gmail",
            "password": "secret123",
            "username": "user@gmail.com",
            "url": "https://gmail.com",
            "notes": "Personal email",
            "tags": ["email", "personal"],
        }

        # Mock controller to return success
        updated_vault = Vault(entries=[VaultEntry(key="gmail", password="secret123")])
        controller.add_vault_entry = Mock(return_value=(updated_vault, True, None))

        # Mock app.push_screen_wait
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=form_data)

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_add_entry()

            controller.add_vault_entry.assert_called_once()
            screen._refresh_entry_list.assert_called_once()
            screen.notify.assert_called_once()
            assert "added successfully" in screen.notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_action_add_entry_cancel(self):
        """Should handle add entry cancellation."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()
        screen._refresh_entry_list = Mock()

        # Mock app.push_screen_wait to return None (cancelled)
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=None)

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_add_entry()

            screen._refresh_entry_list.assert_not_called()
            screen.notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_action_add_entry_failure(self):
        """Should handle add entry failure."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()

        # Mock form data
        form_data = {"key": "test", "password": "secret"}

        # Mock controller to return failure
        controller.add_vault_entry = Mock(return_value=(vault, False, "Entry already exists"))

        # Mock app
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=form_data)

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_add_entry()

            screen.notify.assert_called_once()
            assert "Failed to add entry" in screen.notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_action_edit_entry_no_selection(self):
        """Should warn when no entry selected for edit."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()

        await screen.action_edit_entry()

        screen.notify.assert_called_once()
        assert "No entry selected" in screen.notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_action_edit_entry_success(self):
        """Should edit entry successfully."""
        entry = VaultEntry(key="test", password="old_password")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry
        screen.notify = Mock()
        screen._refresh_entry_list = Mock()

        # Mock form data
        form_data = {"key": "test", "password": "new_password"}

        # Mock controller
        updated_entry = VaultEntry(key="test", password="new_password")
        updated_vault = Vault(entries=[updated_entry])
        controller.update_vault_entry = Mock(return_value=(updated_vault, True, None))

        # Mock app
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=form_data)

        # Mock detail panel
        mock_panel = Mock()
        screen.query_one = Mock(return_value=mock_panel)

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_edit_entry()

            controller.update_vault_entry.assert_called_once()
            screen._refresh_entry_list.assert_called_once()
            assert "updated successfully" in screen.notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_action_delete_entry_no_selection(self):
        """Should warn when no entry selected for delete."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()

        await screen.action_delete_entry()

        screen.notify.assert_called_once()
        assert "No entry selected" in screen.notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_action_delete_entry_cancel(self):
        """Should handle delete cancellation."""
        entry = VaultEntry(key="test", password="secret")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry
        screen.notify = Mock()
        screen._refresh_entry_list = Mock()

        # Mock app to return False (cancelled)
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=False)

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_delete_entry()

            screen._refresh_entry_list.assert_not_called()
            screen.notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_action_delete_entry_success(self):
        """Should delete entry successfully."""
        entry = VaultEntry(key="test", password="secret")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry
        screen.notify = Mock()
        screen._refresh_entry_list = Mock()

        # Mock controller
        updated_vault = Vault(entries=[])
        controller.delete_vault_entry = Mock(return_value=(updated_vault, True, None))

        # Mock app
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=True)

        # Mock detail panel
        mock_panel = Mock()
        screen.query_one = Mock(return_value=mock_panel)

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_delete_entry()

            controller.delete_vault_entry.assert_called_once()
            screen._refresh_entry_list.assert_called_once()
            assert "deleted successfully" in screen.notify.call_args[0][0]
            assert screen.selected_entry is None

    @pytest.mark.asyncio
    async def test_action_save_vault_success(self):
        """Should save vault successfully."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()

        # Mock controller
        from stegvault.app.controllers.vault_controller import VaultSaveResult

        result = VaultSaveResult(output_path="test.png", success=True)
        controller.save_vault = Mock(return_value=result)

        await screen.action_save_vault()

        controller.save_vault.assert_called_once_with(vault, "test.png", "passphrase")
        screen.notify.assert_called()
        assert "saved successfully" in screen.notify.call_args[0][0]

    @pytest.mark.asyncio
    async def test_action_save_vault_failure(self):
        """Should handle save vault failure."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.notify = Mock()

        # Mock controller
        from stegvault.app.controllers.vault_controller import VaultSaveResult

        result = VaultSaveResult(output_path="test.png", success=False, error="Disk full")
        controller.save_vault = Mock(return_value=result)

        await screen.action_save_vault()

        screen.notify.assert_called()
        assert "Failed to save vault" in screen.notify.call_args[0][0]

    def test_refresh_entry_list(self):
        """Should refresh entry list."""
        entry1 = VaultEntry(key="test1", password="pass1")
        entry2 = VaultEntry(key="test2", password="pass2")
        vault = Vault(entries=[entry1, entry2])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        # Mock entry list
        mock_list = Mock()
        mock_list.clear = Mock()
        mock_list.append = Mock()

        # Mock entry count label
        mock_label = Mock()

        def mock_query_one(selector, widget_type=None):
            if selector == "#entry-list":
                return mock_list
            elif selector == "#entry-count":
                return mock_label
            return Mock()

        screen.query_one = mock_query_one

        screen._refresh_entry_list()

        mock_list.clear.assert_called_once()
        assert mock_list.append.call_count == 2
        mock_label.update.assert_called_once_with("(2)")

    def test_on_button_pressed_add(self):
        """Should handle add button press."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.action_add_entry = Mock()

        button = Mock()
        button.id = "btn-add"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.action_add_entry.assert_called_once()

    def test_on_button_pressed_edit(self):
        """Should handle edit button press."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.action_edit_entry = Mock()

        button = Mock()
        button.id = "btn-edit"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.action_edit_entry.assert_called_once()

    def test_on_button_pressed_delete(self):
        """Should handle delete button press."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.action_delete_entry = Mock()

        button = Mock()
        button.id = "btn-delete"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.action_delete_entry.assert_called_once()

    def test_on_button_pressed_save(self):
        """Should handle save button press."""
        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.action_save_vault = Mock()

        button = Mock()
        button.id = "btn-save"
        event = Mock()
        event.button = button

        screen.on_button_pressed(event)

        screen.action_save_vault.assert_called_once()

    def test_on_list_view_selected(self):
        """Should handle entry selection from list view."""
        from textual.widgets import ListView
        from stegvault.tui.widgets import EntryListItem, EntryDetailPanel

        entry = VaultEntry(key="test", password="pass")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        # Mock query_one to return EntryDetailPanel
        mock_panel = Mock(spec=EntryDetailPanel)
        screen.query_one = Mock(return_value=mock_panel)

        # Create mock event
        mock_item = Mock(spec=EntryListItem)
        mock_item.entry = entry
        event = Mock(spec=ListView.Selected)
        event.item = mock_item

        screen.on_list_view_selected(event)

        assert screen.selected_entry == entry
        mock_panel.show_entry.assert_called_once_with(entry)

    def test_on_list_view_selected_not_entry_item(self):
        """Should ignore non-EntryListItem selections."""
        from textual.widgets import ListView

        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        # Create mock event with non-EntryListItem
        mock_item = Mock()  # Not an EntryListItem
        event = Mock(spec=ListView.Selected)
        event.item = mock_item

        screen.on_list_view_selected(event)

        # Should not set selected_entry
        assert screen.selected_entry is None

    def test_get_filtered_entries_no_query(self):
        """Should return all entries when no search query."""
        entry1 = VaultEntry(key="gmail", password="pass1")
        entry2 = VaultEntry(key="github", password="pass2")
        vault = Vault(entries=[entry1, entry2])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        filtered = screen._get_filtered_entries()

        assert len(filtered) == 2
        assert entry1 in filtered
        assert entry2 in filtered

    def test_get_filtered_entries_by_key(self):
        """Should filter entries by key."""
        entry1 = VaultEntry(key="gmail", password="pass1")
        entry2 = VaultEntry(key="github", password="pass2")
        entry3 = VaultEntry(key="aws", password="pass3")
        vault = Vault(entries=[entry1, entry2, entry3])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        screen.search_query = "git"  # Matches github
        filtered = screen._get_filtered_entries()

        assert len(filtered) == 1
        assert entry2 in filtered
        assert entry1 not in filtered
        assert entry3 not in filtered

    def test_get_filtered_entries_by_username(self):
        """Should filter entries by username."""
        entry1 = VaultEntry(key="site1", password="pass1", username="john@gmail.com")
        entry2 = VaultEntry(key="site2", password="pass2", username="jane@github.com")
        vault = Vault(entries=[entry1, entry2])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        screen.search_query = "john"
        filtered = screen._get_filtered_entries()

        assert len(filtered) == 1
        assert entry1 in filtered

    def test_get_filtered_entries_by_url(self):
        """Should filter entries by URL."""
        entry1 = VaultEntry(key="site1", password="pass1", url="https://gmail.com")
        entry2 = VaultEntry(key="site2", password="pass2", url="https://github.com")
        vault = Vault(entries=[entry1, entry2])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        screen.search_query = "gmail"
        filtered = screen._get_filtered_entries()

        assert len(filtered) == 1
        assert entry1 in filtered

    def test_get_filtered_entries_by_notes(self):
        """Should filter entries by notes."""
        entry1 = VaultEntry(key="site1", password="pass1", notes="Work email")
        entry2 = VaultEntry(key="site2", password="pass2", notes="Personal project")
        vault = Vault(entries=[entry1, entry2])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        screen.search_query = "work"
        filtered = screen._get_filtered_entries()

        assert len(filtered) == 1
        assert entry1 in filtered

    def test_get_filtered_entries_by_tags(self):
        """Should filter entries by tags."""
        entry1 = VaultEntry(key="site1", password="pass1", tags=["work", "email"])
        entry2 = VaultEntry(key="site2", password="pass2", tags=["personal", "dev"])
        vault = Vault(entries=[entry1, entry2])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        screen.search_query = "work"
        filtered = screen._get_filtered_entries()

        assert len(filtered) == 1
        assert entry1 in filtered

    def test_action_focus_search(self):
        """Should focus search input."""
        from textual.widgets import Input

        vault = Vault(entries=[])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        # Mock query_one and focus
        mock_input = Mock(spec=Input)
        screen.query_one = Mock(return_value=mock_input)

        screen.action_focus_search()

        screen.query_one.assert_called_once_with("#search-input", Input)
        mock_input.focus.assert_called_once()

    def test_on_input_changed_search(self):
        """Should handle search input changes."""
        from textual.widgets import Input

        entry1 = VaultEntry(key="gmail", password="pass1")
        entry2 = VaultEntry(key="github", password="pass2")
        vault = Vault(entries=[entry1, entry2])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)

        # Mock _refresh_entry_list
        screen._refresh_entry_list = Mock()

        # Create mock event
        mock_input = Mock(spec=Input)
        mock_input.id = "search-input"
        event = Mock(spec=Input.Changed)
        event.input = mock_input
        event.value = "gm"

        screen.on_input_changed(event)

        assert screen.search_query == "gm"
        screen._refresh_entry_list.assert_called_once()

    def test_on_input_changed_clears_filtered_selection(self):
        """Should clear detail panel if selected entry is filtered out."""
        from textual.widgets import Input
        from stegvault.tui.widgets import EntryDetailPanel

        entry1 = VaultEntry(key="gmail", password="pass1")
        entry2 = VaultEntry(key="github", password="pass2")
        vault = Vault(entries=[entry1, entry2])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry2  # Select github

        # Mock methods
        screen._refresh_entry_list = Mock()
        mock_panel = Mock(spec=EntryDetailPanel)
        screen.query_one = Mock(return_value=mock_panel)

        # Create mock event that filters to only gmail
        mock_input = Mock(spec=Input)
        mock_input.id = "search-input"
        event = Mock(spec=Input.Changed)
        event.input = mock_input
        event.value = "gmail"  # This filters out github

        screen.on_input_changed(event)

        # Selected entry (github) should be cleared because it's filtered out
        assert screen.selected_entry is None
        mock_panel.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_edit_entry_user_cancels(self):
        """Should handle user cancellation in edit form."""
        entry = VaultEntry(key="test", password="pass")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry

        # Mock app using patch.object
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=None)

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_edit_entry()

        # Vault should not be modified
        assert len(vault.entries) == 1

    @pytest.mark.asyncio
    async def test_action_edit_entry_failure(self):
        """Should handle edit entry failure."""
        entry = VaultEntry(key="test", password="pass")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry
        screen.notify = Mock()

        # Mock app using patch.object
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value={"key": "test", "password": "newpass"})

        # Mock controller to return failure
        screen.controller.update_vault_entry = Mock(return_value=(vault, False, "Update failed"))

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_edit_entry()

        screen.notify.assert_called_with("Failed to update entry: Update failed", severity="error")

    @pytest.mark.asyncio
    async def test_action_delete_entry_failure(self):
        """Should handle delete entry failure."""
        entry = VaultEntry(key="test", password="pass")
        vault = Vault(entries=[entry])
        controller = VaultController()
        screen = VaultScreen(vault, "test.png", "passphrase", controller)
        screen.selected_entry = entry
        screen.notify = Mock()

        # Mock app using patch.object
        mock_app = Mock()
        mock_app.push_screen_wait = AsyncMock(return_value=True)

        # Mock controller to return failure
        screen.controller.delete_vault_entry = Mock(return_value=(vault, False, "Delete failed"))

        with patch.object(type(screen), "app", property(lambda self: mock_app)):
            await screen.action_delete_entry()

        screen.notify.assert_called_with("Failed to delete entry: Delete failed", severity="error")
