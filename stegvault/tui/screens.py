"""
TUI screens for StegVault.

Provides main application screens for vault management.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, ListView, Button, Label, Input
from textual.screen import Screen
from textual.binding import Binding

from stegvault.vault import Vault, VaultEntry
from stegvault.app.controllers import VaultController

from .widgets import EntryListItem, EntryDetailPanel, EntryFormScreen, DeleteConfirmationScreen


class VaultScreen(Screen):
    """Main vault management screen."""

    CSS = """
    VaultScreen {
        background: $surface;
    }

    #vault-container {
        height: 100%;
    }

    #vault-header {
        height: 3;
        background: $primary;
        color: $text;
        padding: 0 2;
        dock: top;
    }

    #vault-title {
        text-style: bold;
    }

    #vault-path {
        color: $text-muted;
        margin-left: 2;
    }

    #main-panel {
        height: 1fr;
    }

    #entry-list-container {
        width: 30%;
        border-right: solid $accent;
    }

    #entry-list-header {
        height: 3;
        background: $panel;
        padding: 0 1;
    }

    #entry-count {
        color: $text-muted;
    }

    #search-container {
        height: 3;
        background: $panel;
        padding: 0 1;
    }

    #search-input {
        width: 100%;
    }

    #entry-list {
        height: 1fr;
    }

    #detail-container {
        width: 70%;
    }

    .entry-item {
        padding: 0 1;
    }

    .entry-item:hover {
        background: $primary 20%;
    }

    ListItem.--highlight {
        background: $primary;
    }

    #action-bar {
        height: 3;
        background: $panel;
        dock: bottom;
        padding: 0 2;
    }

    .action-button {
        margin: 0 1;
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

    def compose(self) -> ComposeResult:
        """Compose vault screen layout."""
        yield Header()

        with Container(id="vault-container"):
            # Vault header
            with Horizontal(id="vault-header"):
                yield Label(f"Vault: {self.vault.name or 'Unnamed'}", id="vault-title")
                yield Label(f"📁 {self.image_path}", id="vault-path")

            # Main panel with entry list and details
            with Horizontal(id="main-panel"):
                # Entry list
                with Vertical(id="entry-list-container"):
                    with Horizontal(id="entry-list-header"):
                        yield Label("Entries", id="entry-list-title")
                        yield Label(f"({len(self.vault.entries)})", id="entry-count")

                    # Search box
                    with Horizontal(id="search-container"):
                        yield Input(
                            placeholder="🔍 Search entries... (press / to focus)",
                            id="search-input",
                        )

                    entry_list = ListView(id="entry-list")
                    for entry in self.vault.entries:
                        entry_list.append(EntryListItem(entry))
                    yield entry_list

                # Detail panel
                with Container(id="detail-container"):
                    yield EntryDetailPanel()

            # Action bar
            with Horizontal(id="action-bar"):
                yield Button("Add (a)", variant="success", id="btn-add", classes="action-button")
                yield Button("Edit (e)", variant="warning", id="btn-edit", classes="action-button")
                yield Button(
                    "Delete (d)", variant="error", id="btn-delete", classes="action-button"
                )
                yield Button("Copy (c)", variant="primary", id="btn-copy", classes="action-button")
                yield Button(
                    "Show/Hide (v)", variant="default", id="btn-toggle", classes="action-button"
                )
                yield Button(
                    "History (h)", variant="default", id="btn-history", classes="action-button"
                )
                yield Button("Save (s)", variant="primary", id="btn-save", classes="action-button")
                yield Button("Back", variant="default", id="btn-back", classes="action-button")

        yield Footer()

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

    async def action_view_history(self) -> None:
        """View password history for selected entry."""
        if self.selected_entry:
            from .widgets import PasswordHistoryModal

            await self.app.push_screen_wait(PasswordHistoryModal(self.selected_entry))
        else:
            self.notify("No entry selected", severity="warning")

    async def action_add_entry(self) -> None:
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

        # Refresh entry list
        self._refresh_entry_list()
        self.notify(f"Entry '{form_data['key']}' added successfully", severity="information")

    async def action_edit_entry(self) -> None:
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
        self._refresh_entry_list()

        # Update detail panel if same entry is still selected
        if self.selected_entry and self.selected_entry.key == form_data["key"]:
            updated_entry = next((e for e in self.vault.entries if e.key == form_data["key"]), None)
            if updated_entry:
                self.selected_entry = updated_entry
                detail_panel = self.query_one(EntryDetailPanel)
                detail_panel.show_entry(updated_entry)

        self.notify(f"Entry '{form_data['key']}' updated successfully", severity="information")

    async def action_delete_entry(self) -> None:
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
        self.selected_entry = None

        # Clear detail panel
        detail_panel = self.query_one(EntryDetailPanel)
        detail_panel.clear()

        # Refresh entry list
        self._refresh_entry_list()
        self.notify(f"Entry '{entry_key}' deleted successfully", severity="information")

    async def action_save_vault(self) -> None:
        """Save vault changes to disk."""
        self.notify("Saving vault...", severity="information")

        # Save vault using controller
        result = self.controller.save_vault(self.vault, self.image_path, self.passphrase)

        if not result.success:
            self.notify(f"Failed to save vault: {result.error}", severity="error")
            return

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
        """Return to welcome screen."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit application."""
        self.app.exit()
