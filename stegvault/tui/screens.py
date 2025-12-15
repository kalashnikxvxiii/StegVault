"""
TUI screens for StegVault.

Provides main application screens for vault management.
"""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, ListView, Button, Label, Input
from textual.screen import Screen
from textual.binding import Binding

from stegvault.vault import Vault, VaultEntry
from stegvault.app.controllers import VaultController

from .widgets import (
    EntryListItem,
    EntryDetailPanel,
    EntryFormScreen,
    DeleteConfirmationScreen,
    UnsavedChangesScreen,
    QuitConfirmationScreen,
)


class VaultScreen(Screen):
    """Main vault management screen."""

    CSS = """
    /* Cyberpunk Vault Screen - Fullscreen responsive */
    VaultScreen {
        background: #000000;
    }

    #vault-container {
        width: 100%;
        height: 100%;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
    }

    #vault-header {
        height: 3;
        background: #0a0a0a;
        border-bottom: heavy #00ffff;
        color: #00ffff;
        padding: 0 2;
        dock: top;
    }

    #vault-title {
        text-style: bold;
        color: #00ffff;
    }

    #vault-path {
        color: #ff00ff;
        margin-left: 2;
        text-style: italic;
    }

    #main-panel {
        width: 100%;
        height: 1fr;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
    }

    /* Entry List - Neon cyan theme */
    #entry-list-container {
        width: 30%;
        border-right: heavy #00ffff;
        background: #0a0a0a;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
    }

    #entry-list-header {
        height: 3;
        background: #0a0a0a;
        border-bottom: solid #ff00ff;
        padding: 0 1;
    }

    #entry-list-header Static {
        color: #ffff00;
        text-style: bold;
    }

    #entry-count {
        color: #ff00ff;
        text-style: bold;
    }

    #search-container {
        height: auto;
        background: #0a0a0a;
        border-bottom: solid #00ffff;
        padding: 0 1;
    }

    #search-input {
        width: 100%;
        height: 3;
        background: #000000;
        border: solid #00ffff;
        color: #00ffff;
    }

    #search-input:focus {
        border: heavy #00ffff;
        background: #0a0a0a;
    }

    #entry-list {
        height: 1fr;
        background: #0a0a0a;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
    }

    /* Detail Panel - Magenta accent */
    #detail-container {
        width: 70%;
        background: #0a0a0a;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
    }

    .entry-item {
        padding: 0 1;
        color: #00ffff;
        border-left: solid transparent;
    }

    .entry-item:hover {
        background: #00ffff20;
        border-left: heavy #00ffff;
    }

    ListItem.--highlight {
        background: #00ffff30;
        border-left: double #00ffff;
        color: #ffffff;
        text-style: bold;
    }

    /* Action Bar - Bottom panel with 2 rows */
    #action-bar-container {
        width: 100%;
        height: auto;
        min-height: 11;
        background: #0a0a0a;
        border-top: solid #ff00ff;
        dock: bottom;
        padding: 0;
    }

    #action-bar-rows {
        width: 100%;
        height: auto;
        align: center middle;
    }

    .action-row {
        width: 100%;
        height: 5;
        align: center middle;
    }

    .action-button {
        margin: 0 2;
        padding: 0 1;
        height: 5;
        width: 1fr;
        border: solid #00ffff;
        background: #000000;
        color: #00ffff;
        text-align: center;
        content-align: center middle;
        text-style: bold;
    }

    .action-button:hover {
        background: #00ffff20;
    }

    .action-button.danger {
        border-left: solid #ff0080;
        border-right: solid #ff0080;
        color: #ff0080;
    }

    .action-button.danger:hover {
        background: #ff008020;
    }

    .action-button.success {
        border-left: solid #00ff9f;
        border-right: solid #00ff9f;
        color: #00ff9f;
    }

    .action-button.success:hover {
        background: #00ff9f20;
    }
    """

    BINDINGS = [
        Binding("escape", "back", "Back to Menu"),
        Binding("a", "add_entry", "Add Entry"),
        Binding("e", "edit_entry", "Edit Entry"),
        Binding("d", "delete_entry", "Delete Entry"),
        Binding("c", "copy_password", "Copy Password"),
        Binding("v", "toggle_password", "Show/Hide Password"),
        Binding("h", "view_history", "Password History"),
        Binding("s", "save_vault", "Save Changes"),
        Binding("/", "focus_search", "Search"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, vault: Vault, image_path: str, passphrase: str, controller: VaultController):
        """Initialize vault screen."""
        super().__init__()
        self.vault = vault
        self.image_path = image_path
        self.passphrase = passphrase
        self.controller = controller
        self.selected_entry: Optional[VaultEntry] = None
        self.search_query: str = ""
        self.has_unsaved_changes: bool = False

    def compose(self) -> ComposeResult:
        """Compose vault screen layout."""
        yield Header()

        with Container(id="vault-container"):
            # Vault header
            with Horizontal(id="vault-header"):
                vault_name = Path(self.image_path).stem.upper() if self.image_path else "UNNAMED"
                yield Label(f"🔒🔒 VAULT: {vault_name} 🔒🔒", id="vault-title")
                yield Label(f">> {self.image_path}", id="vault-path")

            # Main panel with entry list and details
            with Horizontal(id="main-panel"):
                # Entry list
                with Vertical(id="entry-list-container"):
                    with Horizontal(id="entry-list-header"):
                        yield Label(">> CREDENTIALS", id="entry-list-title")
                        yield Label(f"[{len(self.vault.entries)}]", id="entry-count")

                    # Search box
                    with Horizontal(id="search-container"):
                        yield Input(
                            placeholder="⚡⚡ NEURAL SEARCH (/) ...",
                            id="search-input",
                        )

                    # Entry list - populate in on_mount()
                    yield ListView(id="entry-list")

                # Detail panel
                with Container(id="detail-container"):
                    yield EntryDetailPanel()

            # Action bar - 2 rows of 4 buttons each
            with Container(id="action-bar-container"):
                with Vertical(id="action-bar-rows"):
                    with Horizontal(classes="action-row"):
                        yield Button("ADD", id="btn-add", classes="action-button success")
                        yield Button("EDIT", id="btn-edit", classes="action-button")
                        yield Button("DELETE", id="btn-delete", classes="action-button danger")
                        yield Button("COPY", id="btn-copy", classes="action-button")
                    with Horizontal(classes="action-row"):
                        yield Button("SHOW", id="btn-toggle", classes="action-button")
                        yield Button("HISTORY", id="btn-history", classes="action-button")
                        yield Button("SAVE", id="btn-save", classes="action-button success")
                        yield Button("BACK", id="btn-back", classes="action-button")

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted. Populate entry list."""
        # Use call_later to ensure ListView is fully rendered before populating
        self.call_later(self._refresh_entry_list)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle entry selection."""
        if isinstance(event.item, EntryListItem):
            self.selected_entry = event.item.entry
            detail_panel = self.query_one(EntryDetailPanel)
            detail_panel.show_entry(self.selected_entry)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        button_id = event.button.id

        if button_id == "btn-add":
            self.action_add_entry()
        elif button_id == "btn-edit":
            self.action_edit_entry()
        elif button_id == "btn-delete":
            self.action_delete_entry()
        elif button_id == "btn-copy":
            self.action_copy_password()
        elif button_id == "btn-toggle":
            self.action_toggle_password()
        elif button_id == "btn-history":
            self.action_view_history()
        elif button_id == "btn-save":
            self.action_save_vault()
        elif button_id == "btn-back":
            self.action_back()

    def action_copy_password(self) -> None:
        """Copy selected entry password to clipboard."""
        if self.selected_entry:
            try:
                import pyperclip

                pyperclip.copy(self.selected_entry.password)
                self.notify(
                    f"Password copied for '{self.selected_entry.key}'",
                    severity="information",
                )
            except Exception as e:
                self.notify(f"Failed to copy password: {e}", severity="error")
        else:
            self.notify("No entry selected", severity="warning")

    def action_toggle_password(self) -> None:
        """Toggle password visibility."""
        if self.selected_entry:
            detail_panel = self.query_one(EntryDetailPanel)
            detail_panel.toggle_password_visibility()
        else:
            self.notify("No entry selected", severity="warning")

    def action_view_history(self) -> None:
        """View password history (wrapper for async)."""
        self.run_worker(self._async_view_history())

    async def _async_view_history(self) -> None:
        """View password history for selected entry."""
        if self.selected_entry:
            from .widgets import PasswordHistoryModal

            await self.app.push_screen_wait(PasswordHistoryModal(self.selected_entry))
        else:
            self.notify("No entry selected", severity="warning")

    def action_add_entry(self) -> None:
        """Add new entry (wrapper for async)."""
        self.run_worker(self._async_add_entry())

    async def _async_add_entry(self) -> None:
        """Add new entry to vault."""
        # Show add entry form
        form_data = await self.app.push_screen_wait(EntryFormScreen(mode="add"))

        if not form_data:
            return  # User cancelled

        # Add entry using controller
        updated_vault, success, error = self.controller.add_vault_entry(
            self.vault,
            key=form_data["key"],
            password=form_data["password"],
            username=form_data.get("username"),
            url=form_data.get("url"),
            notes=form_data.get("notes"),
            tags=form_data.get("tags"),
        )

        if not success:
            self.notify(f"Failed to add entry: {error}", severity="error")
            return

        # Update vault reference
        self.vault = updated_vault
        self.has_unsaved_changes = True

        # Refresh entry list
        self._refresh_entry_list()
        self.notify(f"Entry '{form_data['key']}' added successfully", severity="information")

    def action_edit_entry(self) -> None:
        """Edit selected entry (wrapper for async)."""
        self.run_worker(self._async_edit_entry())

    async def _async_edit_entry(self) -> None:
        """Edit selected entry."""
        if not self.selected_entry:
            self.notify("No entry selected", severity="warning")
            return

        # Show edit entry form
        form_data = await self.app.push_screen_wait(
            EntryFormScreen(mode="edit", entry=self.selected_entry)
        )

        if not form_data:
            return  # User cancelled

        # Update entry using controller
        updated_vault, success, error = self.controller.update_vault_entry(
            self.vault,
            key=form_data["key"],
            password=form_data.get("password"),
            username=form_data.get("username"),
            url=form_data.get("url"),
            notes=form_data.get("notes"),
            tags=form_data.get("tags"),
        )

        if not success:
            self.notify(f"Failed to update entry: {error}", severity="error")
            return

        # Update vault reference and refresh
        self.vault = updated_vault
        self.has_unsaved_changes = True
        self._refresh_entry_list()

        # Update detail panel if same entry is still selected
        if self.selected_entry and self.selected_entry.key == form_data["key"]:
            updated_entry = next((e for e in self.vault.entries if e.key == form_data["key"]), None)
            if updated_entry:
                self.selected_entry = updated_entry
                detail_panel = self.query_one(EntryDetailPanel)
                detail_panel.show_entry(updated_entry)

        self.notify(f"Entry '{form_data['key']}' updated successfully", severity="information")

    def action_delete_entry(self) -> None:
        """Delete selected entry (wrapper for async)."""
        self.run_worker(self._async_delete_entry())

    async def _async_delete_entry(self) -> None:
        """Delete selected entry."""
        if not self.selected_entry:
            self.notify("No entry selected", severity="warning")
            return

        # Show delete confirmation
        confirmed = await self.app.push_screen_wait(
            DeleteConfirmationScreen(self.selected_entry.key)
        )

        if not confirmed:
            return  # User cancelled

        entry_key = self.selected_entry.key

        # Delete entry using controller
        updated_vault, success, error = self.controller.delete_vault_entry(self.vault, entry_key)

        if not success:
            self.notify(f"Failed to delete entry: {error}", severity="error")
            return

        # Update vault reference and refresh
        self.vault = updated_vault
        self.has_unsaved_changes = True
        self.selected_entry = None

        # Clear detail panel
        detail_panel = self.query_one(EntryDetailPanel)
        detail_panel.clear()

        # Refresh entry list
        self._refresh_entry_list()
        self.notify(f"Entry '{entry_key}' deleted successfully", severity="information")

    def action_save_vault(self) -> None:
        """Save vault changes to disk (wrapper for async)."""
        self.run_worker(self._async_save_vault())

    async def _async_save_vault(self) -> None:
        """Save vault changes to disk."""
        self.notify("Saving vault...", severity="information")

        # Save vault using controller
        result = self.controller.save_vault(self.vault, self.image_path, self.passphrase)

        if not result.success:
            self.notify(f"Failed to save vault: {result.error}", severity="error")
            return

        self.has_unsaved_changes = False
        self.notify("Vault saved successfully!", severity="information")

    def _get_filtered_entries(self) -> list[VaultEntry]:
        """Get entries filtered by search query."""
        if not self.search_query:
            return self.vault.entries

        query = self.search_query.lower()
        filtered = []

        for entry in self.vault.entries:
            # Search in key, username, URL, notes, and tags
            if (
                query in entry.key.lower()
                or (entry.username and query in entry.username.lower())
                or (entry.url and query in entry.url.lower())
                or (entry.notes and query in entry.notes.lower())
                or any(query in tag.lower() for tag in entry.tags)
            ):
                filtered.append(entry)

        return filtered

    def _refresh_entry_list(self) -> None:
        """Refresh the entry list view with current search filter."""
        # Check if screen is mounted before attempting refresh
        if not self.is_mounted:
            return

        # Get entry list and clear it
        entry_list = self.query_one("#entry-list", ListView)
        entry_list.clear()

        # Re-populate with filtered entries
        filtered_entries = self._get_filtered_entries()
        for entry in filtered_entries:
            entry_list.append(EntryListItem(entry))

        # Update entry count
        entry_count_label = self.query_one("#entry-count", Label)
        if self.search_query:
            entry_count_label.update(f"({len(filtered_entries)}/{len(self.vault.entries)})")
        else:
            entry_count_label.update(f"({len(self.vault.entries)})")

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self._refresh_entry_list()

            # Clear detail panel if selected entry is filtered out
            if self.selected_entry and self.selected_entry not in self._get_filtered_entries():
                self.selected_entry = None
                detail_panel = self.query_one(EntryDetailPanel)
                detail_panel.clear()

    def action_refresh(self) -> None:
        """Refresh vault from disk."""
        self.notify("Refresh feature - Coming soon!", severity="information")

    def action_back(self) -> None:
        """Return to welcome screen (wrapper for async)."""
        self.run_worker(self._async_back())

    async def _async_back(self) -> None:
        """Check for unsaved changes before going back."""
        if self.has_unsaved_changes:
            choice = await self.app.push_screen_wait(UnsavedChangesScreen())
            if choice == "save":
                # Save and exit
                await self._async_save_vault()
                self.app.pop_screen()
            elif choice == "dont_save":
                # Exit without saving
                self.app.pop_screen()
            # If "cancel", do nothing
        else:
            # No unsaved changes, just exit
            self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit application (wrapper for async)."""
        self.run_worker(self._async_quit())

    async def _async_quit(self) -> None:
        """Check for unsaved changes before quitting."""
        # Step 1: Handle unsaved changes if any
        if self.has_unsaved_changes:
            choice = await self.app.push_screen_wait(UnsavedChangesScreen())
            if choice == "save":
                # Save vault before proceeding to quit confirmation
                await self._async_save_vault()
            elif choice == "cancel":
                # User cancelled, don't proceed to quit confirmation
                return
            # If "dont_save", continue to quit confirmation

        # Step 2: Show quit confirmation
        confirm_quit = await self.app.push_screen_wait(QuitConfirmationScreen())

        if confirm_quit:
            # User confirmed quit, exit application
            self.app.exit()
