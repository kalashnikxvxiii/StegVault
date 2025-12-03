"""
Custom widgets for StegVault TUI.

Provides reusable UI components for the terminal interface.
"""

from pathlib import Path
from typing import Optional, Callable

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Static,
    Input,
    Button,
    Label,
    ListView,
    ListItem,
    DirectoryTree,
)
from textual.screen import Screen, ModalScreen
from textual.binding import Binding

from stegvault.vault import Vault, VaultEntry


class FileSelectScreen(ModalScreen[Optional[str]]):
    """Modal screen for selecting a vault image file."""

    CSS = """
    FileSelectScreen {
        align: center middle;
    }

    #file-dialog {
        width: 80;
        height: 30;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #file-tree {
        height: 20;
        border: solid $accent;
        margin-bottom: 1;
    }

    #file-path-input {
        margin-bottom: 1;
    }

    #button-row {
        height: 3;
        align: center middle;
    }

    .file-button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, title: str = "Select Vault Image"):
        """Initialize file selection screen."""
        super().__init__()
        self.title = title
        self.selected_path: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Compose file selection dialog."""
        with Container(id="file-dialog"):
            yield Label(self.title)
            yield DirectoryTree(".", id="file-tree")
            yield Input(
                placeholder="Enter file path or select from tree",
                id="file-path-input",
            )
            with Horizontal(id="button-row"):
                yield Button("Select", variant="primary", id="btn-select", classes="file-button")
                yield Button("Cancel", variant="default", id="btn-cancel", classes="file-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-select":
            input_widget = self.query_one("#file-path-input", Input)
            path = input_widget.value.strip()

            if path and Path(path).exists():
                self.dismiss(path)
            else:
                self.app.notify("Please enter a valid file path", severity="error")
        elif event.button.id == "btn-cancel":
            self.dismiss(None)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection from tree."""
        input_widget = self.query_one("#file-path-input", Input)
        input_widget.value = str(event.path)

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)


class PassphraseInputScreen(ModalScreen[Optional[str]]):
    """Modal screen for passphrase input."""

    CSS = """
    PassphraseInputScreen {
        align: center middle;
    }

    #passphrase-dialog {
        width: 60;
        height: 15;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    #passphrase-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #passphrase-input {
        margin-bottom: 2;
    }

    #button-row {
        height: 3;
        align: center middle;
    }

    .pass-button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, title: str = "Enter Passphrase"):
        """Initialize passphrase input screen."""
        super().__init__()
        self.title = title

    def compose(self) -> ComposeResult:
        """Compose passphrase dialog."""
        with Container(id="passphrase-dialog"):
            yield Label(self.title, id="passphrase-title")
            yield Input(
                placeholder="Enter vault passphrase",
                password=True,
                id="passphrase-input",
            )
            with Horizontal(id="button-row"):
                yield Button("Unlock", variant="primary", id="btn-unlock", classes="pass-button")
                yield Button("Cancel", variant="default", id="btn-cancel", classes="pass-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-unlock":
            input_widget = self.query_one("#passphrase-input", Input)
            passphrase = input_widget.value

            if passphrase:
                self.dismiss(passphrase)
            else:
                self.app.notify("Passphrase cannot be empty", severity="error")
        elif event.button.id == "btn-cancel":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input."""
        if event.input.id == "passphrase-input" and event.value:
            self.dismiss(event.value)

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)


class EntryListItem(ListItem):
    """List item for a vault entry."""

    def __init__(self, entry: VaultEntry):
        """Initialize entry list item."""
        super().__init__()
        self.entry = entry
        self.add_class("entry-item")

    def render(self) -> str:
        """Render entry list item."""
        tags_str = f" [{', '.join(self.entry.tags)}]" if self.entry.tags else ""
        return f"{self.entry.key}{tags_str}"


class EntryDetailPanel(Container):
    """Panel displaying details of a vault entry."""

    CSS = """
    EntryDetailPanel {
        height: 100%;
        border: solid $accent;
        padding: 1;
    }

    .detail-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .detail-field {
        margin-bottom: 1;
    }

    .field-label {
        color: $text-muted;
        text-style: italic;
    }

    .field-value {
        margin-left: 2;
    }

    .password-masked {
        color: $warning;
    }

    #no-entry-msg {
        color: $text-muted;
        text-align: center;
        margin-top: 5;
    }
    """

    def __init__(self):
        """Initialize entry detail panel."""
        super().__init__()
        self.current_entry: Optional[VaultEntry] = None
        self.password_visible = False

    def compose(self) -> ComposeResult:
        """Compose detail panel."""
        yield ScrollableContainer(
            Label("No entry selected", id="no-entry-msg"),
            id="detail-content",
        )

    def show_entry(self, entry: VaultEntry) -> None:
        """Display entry details."""
        self.current_entry = entry
        self.password_visible = False
        self._update_display()

    def toggle_password_visibility(self) -> None:
        """Toggle password visibility."""
        if self.current_entry:
            self.password_visible = not self.password_visible
            self._update_display()

    def _update_display(self) -> None:
        """Update the display with current entry details."""
        if not self.current_entry:
            content = ScrollableContainer(
                Label("No entry selected", id="no-entry-msg"),
                id="detail-content",
            )
        else:
            entry = self.current_entry
            widgets = [
                Label(f"Entry: {entry.key}", classes="detail-title"),
            ]

            # Password field
            password_display = (
                entry.password if self.password_visible else "*" * len(entry.password)
            )
            widgets.append(
                Vertical(
                    Label("Password:", classes="field-label"),
                    Label(password_display, classes="field-value password-masked"),
                    classes="detail-field",
                )
            )

            # Username
            if entry.username:
                widgets.append(
                    Vertical(
                        Label("Username:", classes="field-label"),
                        Label(entry.username, classes="field-value"),
                        classes="detail-field",
                    )
                )

            # URL
            if entry.url:
                widgets.append(
                    Vertical(
                        Label("URL:", classes="field-label"),
                        Label(entry.url, classes="field-value"),
                        classes="detail-field",
                    )
                )

            # Tags
            if entry.tags:
                widgets.append(
                    Vertical(
                        Label("Tags:", classes="field-label"),
                        Label(", ".join(entry.tags), classes="field-value"),
                        classes="detail-field",
                    )
                )

            # Notes
            if entry.notes:
                widgets.append(
                    Vertical(
                        Label("Notes:", classes="field-label"),
                        Label(entry.notes, classes="field-value"),
                        classes="detail-field",
                    )
                )

            # TOTP
            if entry.totp_secret:
                widgets.append(
                    Vertical(
                        Label("TOTP:", classes="field-label"),
                        Label("✓ Configured", classes="field-value"),
                        classes="detail-field",
                    )
                )

            # Timestamps
            widgets.append(
                Vertical(
                    Label("Created:", classes="field-label"),
                    Label(entry.created, classes="field-value"),
                    classes="detail-field",
                )
            )

            if entry.modified != entry.created:
                widgets.append(
                    Vertical(
                        Label("Modified:", classes="field-label"),
                        Label(entry.modified, classes="field-value"),
                        classes="detail-field",
                    )
                )

            content = ScrollableContainer(*widgets, id="detail-content")

        # Replace content
        old_content = self.query_one("#detail-content")
        old_content.remove()
        self.mount(content)

    def clear(self) -> None:
        """Clear the detail panel."""
        self.current_entry = None
        self.password_visible = False
        self._update_display()


class EntryFormScreen(ModalScreen[Optional[dict]]):
    """Modal screen for adding/editing vault entries."""

    CSS = """
    EntryFormScreen {
        align: center middle;
    }

    #form-dialog {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    #form-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .form-field {
        margin-bottom: 1;
    }

    .field-label {
        color: $text-muted;
        margin-bottom: 0;
    }

    Input {
        width: 100%;
    }

    #button-row {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    .form-button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        mode: str = "add",
        entry: Optional[VaultEntry] = None,
        title: Optional[str] = None,
    ):
        """
        Initialize entry form screen.

        Args:
            mode: "add" or "edit"
            entry: Entry to edit (only for edit mode)
            title: Optional custom title
        """
        super().__init__()
        self.mode = mode
        self.entry = entry
        self.title = title or ("Edit Entry" if mode == "edit" else "Add New Entry")

    def compose(self) -> ComposeResult:
        """Compose entry form dialog."""
        with Container(id="form-dialog"):
            yield Label(self.title, id="form-title")

            # Key field
            with Vertical(classes="form-field"):
                yield Label("Key (identifier):", classes="field-label")
                key_input = Input(
                    placeholder="e.g., gmail, github, aws",
                    id="input-key",
                )
                if self.entry and self.mode == "edit":
                    key_input.value = self.entry.key
                    key_input.disabled = True  # Can't change key in edit mode
                yield key_input

            # Password field with generate button
            with Vertical(classes="form-field"):
                yield Label("Password:", classes="field-label")
                with Horizontal():
                    password_input = Input(
                        placeholder="Enter password",
                        password=True,
                        id="input-password",
                    )
                    if self.entry:
                        password_input.value = self.entry.password
                    yield password_input
                    yield Button(
                        "Generate",
                        variant="success",
                        id="btn-generate-password",
                        classes="form-button",
                    )

            # Username field
            with Vertical(classes="form-field"):
                yield Label("Username (optional):", classes="field-label")
                username_input = Input(
                    placeholder="e.g., user@example.com",
                    id="input-username",
                )
                if self.entry and self.entry.username:
                    username_input.value = self.entry.username
                yield username_input

            # URL field
            with Vertical(classes="form-field"):
                yield Label("URL (optional):", classes="field-label")
                url_input = Input(
                    placeholder="e.g., https://example.com",
                    id="input-url",
                )
                if self.entry and self.entry.url:
                    url_input.value = self.entry.url
                yield url_input

            # Notes field
            with Vertical(classes="form-field"):
                yield Label("Notes (optional):", classes="field-label")
                notes_input = Input(
                    placeholder="Any additional notes",
                    id="input-notes",
                )
                if self.entry and self.entry.notes:
                    notes_input.value = self.entry.notes
                yield notes_input

            # Tags field
            with Vertical(classes="form-field"):
                yield Label("Tags (optional, comma-separated):", classes="field-label")
                tags_input = Input(
                    placeholder="e.g., work, email, important",
                    id="input-tags",
                )
                if self.entry and self.entry.tags:
                    tags_input.value = ", ".join(self.entry.tags)
                yield tags_input

            # Buttons
            with Horizontal(id="button-row"):
                yield Button(
                    "Save" if self.mode == "edit" else "Add",
                    variant="primary",
                    id="btn-save",
                    classes="form-button",
                )
                yield Button("Cancel", variant="default", id="btn-cancel", classes="form-button")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-generate-password":
            # Show password generator dialog
            generated_password = await self.app.push_screen_wait(PasswordGeneratorScreen())

            if generated_password:
                # Fill password field with generated password
                password_input = self.query_one("#input-password", Input)
                password_input.value = generated_password
                self.app.notify("Password generated successfully", severity="information")
            return

        if event.button.id == "btn-save":
            # Gather form data
            key = self.query_one("#input-key", Input).value.strip()
            password = self.query_one("#input-password", Input).value
            username = self.query_one("#input-username", Input).value.strip() or None
            url = self.query_one("#input-url", Input).value.strip() or None
            notes = self.query_one("#input-notes", Input).value.strip() or None
            tags_str = self.query_one("#input-tags", Input).value.strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

            # Validate required fields
            if not key:
                self.app.notify("Key is required", severity="error")
                return
            if not password:
                self.app.notify("Password is required", severity="error")
                return

            # Return form data
            form_data = {
                "key": key,
                "password": password,
                "username": username,
                "url": url,
                "notes": notes,
                "tags": tags,
            }
            self.dismiss(form_data)

        elif event.button.id == "btn-cancel":
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)


class DeleteConfirmationScreen(ModalScreen[bool]):
    """Modal screen for confirming entry deletion."""

    CSS = """
    DeleteConfirmationScreen {
        align: center middle;
    }

    #confirm-dialog {
        width: 60;
        height: 15;
        border: thick $error;
        background: $surface;
        padding: 2;
    }

    #confirm-title {
        text-align: center;
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }

    #confirm-message {
        text-align: center;
        margin-bottom: 2;
    }

    #entry-key {
        text-align: center;
        text-style: bold;
        color: $warning;
        margin-bottom: 2;
    }

    #button-row {
        height: 3;
        align: center middle;
    }

    .confirm-button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, entry_key: str):
        """
        Initialize delete confirmation screen.

        Args:
            entry_key: Key of entry to delete
        """
        super().__init__()
        self.entry_key = entry_key

    def compose(self) -> ComposeResult:
        """Compose confirmation dialog."""
        with Container(id="confirm-dialog"):
            yield Label("⚠️  Confirm Deletion", id="confirm-title")
            yield Label("Are you sure you want to delete this entry?", id="confirm-message")
            yield Label(f'"{self.entry_key}"', id="entry-key")
            yield Label("This action cannot be undone.", id="confirm-message")

            with Horizontal(id="button-row"):
                yield Button("Delete", variant="error", id="btn-delete", classes="confirm-button")
                yield Button("Cancel", variant="default", id="btn-cancel", classes="confirm-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-delete":
            self.dismiss(True)  # Confirmed
        elif event.button.id == "btn-cancel":
            self.dismiss(False)  # Cancelled

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(False)


class PasswordGeneratorScreen(ModalScreen[Optional[str]]):
    """Modal screen for generating secure passwords."""

    CSS = """
    PasswordGeneratorScreen {
        align: center middle;
    }

    #generator-dialog {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    #generator-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .generator-section {
        margin-bottom: 1;
    }

    .section-label {
        color: $text-muted;
        margin-bottom: 0;
    }

    #password-preview {
        text-align: center;
        text-style: bold;
        color: $success;
        background: $panel;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }

    #length-value {
        text-align: center;
        color: $primary;
        margin-bottom: 1;
    }

    #button-row {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    .gen-button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("g", "generate", "Generate"),
    ]

    def __init__(self):
        """Initialize password generator screen."""
        super().__init__()
        self.length = 16
        self.use_lowercase = True
        self.use_uppercase = True
        self.use_digits = True
        self.use_symbols = True
        self.exclude_ambiguous = False
        self.current_password = ""

    def compose(self) -> ComposeResult:
        """Compose password generator dialog."""
        with Container(id="generator-dialog"):
            yield Label("🔐 Password Generator", id="generator-title")

            # Password preview
            with Vertical(classes="generator-section"):
                yield Label("Generated Password:", classes="section-label")
                yield Label(self._generate_password(), id="password-preview")

            # Length control
            with Vertical(classes="generator-section"):
                yield Label("Password Length:", classes="section-label")
                yield Label(f"{self.length} characters", id="length-value")
                with Horizontal():
                    yield Button("-", id="btn-length-dec", classes="gen-button")
                    yield Button("+", id="btn-length-inc", classes="gen-button")

            # Character options (simplified - checkboxes would require custom widgets)
            with Vertical(classes="generator-section"):
                yield Label("Options: All character types enabled", classes="section-label")
                yield Label("(a-z, A-Z, 0-9, symbols)", id="charset-info")

            # Action buttons
            with Horizontal(id="button-row"):
                yield Button(
                    "Generate New", variant="primary", id="btn-generate", classes="gen-button"
                )
                yield Button(
                    "Use This Password", variant="success", id="btn-use", classes="gen-button"
                )
                yield Button("Cancel", variant="default", id="btn-cancel", classes="gen-button")

    def _generate_password(self) -> str:
        """Generate a new password with current settings."""
        from stegvault.vault.generator import PasswordGenerator

        generator = PasswordGenerator(
            length=self.length,
            use_lowercase=self.use_lowercase,
            use_uppercase=self.use_uppercase,
            use_digits=self.use_digits,
            use_symbols=self.use_symbols,
            exclude_ambiguous=self.exclude_ambiguous,
        )
        self.current_password = generator.generate()
        return self.current_password

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-generate":
            # Generate new password and update preview
            new_password = self._generate_password()
            preview = self.query_one("#password-preview", Label)
            preview.update(new_password)

        elif event.button.id == "btn-length-dec":
            # Decrease length (min 8)
            if self.length > 8:
                self.length -= 1
                length_label = self.query_one("#length-value", Label)
                length_label.update(f"{self.length} characters")

        elif event.button.id == "btn-length-inc":
            # Increase length (max 64)
            if self.length < 64:
                self.length += 1
                length_label = self.query_one("#length-value", Label)
                length_label.update(f"{self.length} characters")

        elif event.button.id == "btn-use":
            # Return current password
            if self.current_password:
                self.dismiss(self.current_password)
            else:
                self.app.notify("Please generate a password first", severity="warning")

        elif event.button.id == "btn-cancel":
            self.dismiss(None)

    def action_generate(self) -> None:
        """Generate new password (keyboard shortcut)."""
        new_password = self._generate_password()
        preview = self.query_one("#password-preview", Label)
        preview.update(new_password)

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)
