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
from textual.widgets._directory_tree import DirEntry
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from rich.text import Text

from stegvault.vault import Vault, VaultEntry


class FilteredDirectoryTree(DirectoryTree):
    """DirectoryTree that filters to show only compatible image files."""

    COMPATIBLE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """Filter paths to show only directories and compatible image files."""
        filtered = []
        for path in paths:
            if path.is_dir():
                filtered.append(path)
            elif path.suffix.lower() in self.COMPATIBLE_EXTENSIONS:
                filtered.append(path)
        return filtered

    def render_label(self, node: DirEntry, base_style: str, style: str) -> Text:
        """Render label with color coding for file types."""
        label = super().render_label(node, base_style, style)

        # Add file coloring based on extension
        # node.data contains the DirEntry, which has .path attribute
        if hasattr(node, "data") and node.data is not None:
            path = node.data.path
            if not path.is_dir():
                ext = path.suffix.lower()
                if ext == ".png":
                    label.stylize("yellow")
                elif ext in {".jpg", ".jpeg"}:
                    label.stylize("magenta")

        return label


class HelpScreen(ModalScreen[None]):
    """Modal screen displaying help and keyboard shortcuts."""

    CSS = """
    /* Cyberpunk Help Screen */
    HelpScreen {
        align: center middle;
        background: #00000099;
    }

    #help-dialog {
        width: 80;
        height: auto;
        border: heavy #ff00ff;
        background: #0a0a0a;
        padding: 0;
    }

    #help-title {
        text-style: bold;
        text-align: center;
        color: #00ffff;
        margin-bottom: 0;
        border-bottom: solid #ff00ff;
        padding-bottom: 0;
    }

    #help-content {
        height: auto;
        border: solid #00ffff;
        padding: 0 1;
        margin-bottom: 1;
        background: #000000;
    }

    .help-section {
        margin: 0;
        padding: 0;
        color: #00ff00;
    }

    .help-section-title {
        text-style: bold;
        color: #ff00ff;
    }

    .help-item {
        margin-left: 2;
        color: #00ffff;
    }

    .help-key {
        text-style: bold;
        color: #ffff00;
    }

    #help-footer {
        text-align: center;
        color: #888888;
        margin: 0 0 1 0;
        padding: 0;
    }

    #button-row {
        width: 100%;
        height: 3;
        align: center middle;
        margin: 0 0 1 0;
        padding: 0;
    }

    .help-button {
        margin: 0;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides - Preserve Native Text Rendering */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-primary {
        border: solid #00ff9f;
    }

    Button.-primary:hover {
        background: #00ff9f20;
        border: heavy #00ff9f;
    }

    Button.-success {
        border: solid #00ff00;
    }

    Button.-success:hover {
        background: #00ff0020;
        border: heavy #00ff00;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    def __init__(self):
        """Initialize help screen."""
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose help screen layout."""
        with Container(id="help-dialog"):
            yield Static("🔐 StegVault TUI - Help", id="help-title")

            with ScrollableContainer(id="help-content"):
                yield Static(
                    "[bold cyan]Welcome Screen[/bold cyan]\n"
                    "  [bold yellow]o[/bold yellow] / [bold yellow]Ctrl+O[/bold yellow] - Open existing vault\n"
                    "  [bold yellow]n[/bold yellow] / [bold yellow]Ctrl+N[/bold yellow] - Create new vault\n"
                    "  [bold yellow]h[/bold yellow] / [bold yellow]F1[/bold yellow] - Show this help\n"
                    "  [bold yellow]q[/bold yellow] / [bold yellow]Ctrl+Q[/bold yellow] - Quit application\n\n"
                    "[bold cyan]Vault Screen[/bold cyan]\n"
                    "  [bold yellow]a[/bold yellow] - Add new entry\n"
                    "  [bold yellow]e[/bold yellow] - Edit selected entry\n"
                    "  [bold yellow]d[/bold yellow] - Delete selected entry\n"
                    "  [bold yellow]c[/bold yellow] - Copy password to clipboard\n"
                    "  [bold yellow]v[/bold yellow] - Toggle password visibility\n"
                    "  [bold yellow]s[/bold yellow] - Save vault to disk\n"
                    "  [bold yellow]Escape[/bold yellow] - Back to welcome screen\n"
                    "  [bold yellow]q[/bold yellow] - Quit application\n\n"
                    "[bold cyan]Entry Forms[/bold cyan]\n"
                    "  [bold yellow]Tab[/bold yellow] / [bold yellow]Shift+Tab[/bold yellow] - Navigate fields\n"
                    "  [bold yellow]Enter[/bold yellow] - Submit form\n"
                    "  [bold yellow]Escape[/bold yellow] - Cancel and close\n\n"
                    "[bold cyan]Password Generator[/bold cyan]\n"
                    "  [bold yellow]g[/bold yellow] - Generate new password\n"
                    "  [bold yellow]+[/bold yellow] / [bold yellow]-[/bold yellow] - Adjust password length\n"
                    "  [bold yellow]Enter[/bold yellow] - Use generated password\n"
                    "  [bold yellow]Escape[/bold yellow] - Cancel\n\n"
                    "[bold cyan]Navigation[/bold cyan]\n"
                    "  [bold yellow]↑[/bold yellow] / [bold yellow]↓[/bold yellow] - Navigate entry list\n"
                    "  [bold yellow]Enter[/bold yellow] - Select entry\n"
                    "  [bold yellow]Mouse[/bold yellow] - Click to interact\n\n"
                    "[bold cyan]About[/bold cyan]\n"
                    "  StegVault v0.7.0 - Password Manager with Steganography\n"
                    "  Embeds encrypted credentials in images (PNG/JPEG)\n"
                    "  Uses XChaCha20-Poly1305 encryption + Argon2id KDF\n\n"
                    "[bold cyan]Security Notes[/bold cyan]\n"
                    "  • Strong passphrase is critical for security\n"
                    "  • Keep multiple backup copies of vault images\n"
                    "  • Losing image OR passphrase = permanent data loss\n"
                    "  • JPEG: Robust but smaller capacity (~18KB)\n"
                    "  • PNG: Larger capacity (~90KB) but requires lossless format",
                    markup=True,
                    classes="help-section",
                )

            yield Static("Press [bold]Escape[/bold] or click Close to return", id="help-footer")
            with Horizontal(id="button-row"):
                yield Button("Close", variant="primary", id="btn-close", classes="help-button")

    def on_key(self, event) -> None:
        """Handle key press - prevent 'q' from propagating to parent."""
        if event.key == "q":
            event.stop()
            self.dismiss(None)

    def action_dismiss(self) -> None:
        """Dismiss help screen."""
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-close":
            self.action_dismiss()


class FileSelectScreen(ModalScreen[Optional[str]]):
    """Modal screen for selecting a vault image file."""

    CSS = """
    /* Cyberpunk File Select Dialog */
    FileSelectScreen {
        align: center middle;
        background: #00000099;
    }

    #file-dialog {
        width: 90;
        height: auto;
        min-height: 38;
        border: heavy #00ffff;
        background: #0a0a0a;
        padding: 2;
    }

    #file-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #00ffff;
        margin-bottom: 1;
        border-bottom: solid #ff00ff;
        padding-bottom: 1;
    }

    #file-tree {
        height: 20;
        border: solid #ff00ff;
        margin-bottom: 1;
        background: #000000;
    }

    #file-tree TreeNode {
        color: #00ffff;
    }

    #file-tree TreeNode:hover {
        background: #00ffff30;
        color: #000000;
    }

    #file-tree TreeNode.-selected {
        background: #00ffff30;
        color: #ffffff;
        text-style: bold;
    }

    #file-tree TreeNode.-selected:hover {
        background: #00ffff50;
        color: #000000;
    }

    #file-tree > .tree--cursor {
        background: #00ffff30;
    }

    #file-path-input {
        height: 3;
        margin-bottom: 2;
        background: #000000;
        border: solid #00ffff;
        color: #00ffff;
    }

    #file-path-input:focus {
        border: heavy #00ffff;
    }

    #file-path-input > .input--cursor {
        background: #00ffff;
    }

    #button-row {
        height: auto;
        min-height: 3;
        align: center middle;
    }

    .file-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides - Preserve Native Text Rendering */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-primary {
        border: solid #00ff9f;
    }

    Button.-primary:hover {
        background: #00ff9f20;
        border: heavy #00ff9f;
    }

    Button.-success {
        border: solid #00ff00;
    }

    Button.-success:hover {
        background: #00ff0020;
        border: heavy #00ff00;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
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
        self.last_selected_path: Optional[str] = None
        self.last_click_time: float = 0

    def compose(self) -> ComposeResult:
        """Compose file selection dialog."""
        from pathlib import Path
        import time

        with Container(id="file-dialog"):
            yield Label(f">> {self.title.upper()}", id="file-title")
            # Start from C:\ root on Windows
            start_path = "C:\\"
            yield FilteredDirectoryTree(start_path, id="file-tree")
            yield Input(
                placeholder="Type file path or select from tree above",
                id="file-path-input",
            )
            with Horizontal(id="button-row"):
                yield Button("SELECT", variant="success", id="btn-select", classes="file-button")
                yield Button("CANCEL", variant="default", id="btn-cancel", classes="file-button")

    def on_mount(self) -> None:
        """Set focus on input field when screen mounts."""
        input_field = self.query_one("#file-path-input", Input)
        input_field.focus()

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
        """Handle file selection from tree (single and double-click)."""
        import time

        input_widget = self.query_one("#file-path-input", Input)
        file_path_str = str(event.path)
        input_widget.value = file_path_str

        # Check for double-click (within 500ms)
        current_time = time.time()
        if self.last_selected_path == file_path_str and (current_time - self.last_click_time) < 0.5:
            # Double-click detected - auto-select file
            if Path(file_path_str).is_file():
                self.selected_path = file_path_str
                self.dismiss(self.selected_path)
        else:
            # First click - remember this path
            self.last_selected_path = file_path_str
            self.last_click_time = current_time

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key press - prevent 'q' from propagating to parent."""
        if event.key == "q":
            event.stop()
            self.dismiss(None)


class PassphraseInputScreen(ModalScreen[Optional[str]]):
    """Modal screen for passphrase input."""

    CSS = """
    /* Cyberpunk Passphrase Dialog */
    PassphraseInputScreen {
        align: center middle;
        background: #00000099;
    }

    #passphrase-dialog {
        width: 60;
        height: auto;
        min-height: 15;
        border: heavy #00ffff;
        background: #0a0a0a;
        padding: 2;
    }

    #passphrase-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #00ffff;
        margin-bottom: 1;
        border-bottom: solid #ff00ff;
        padding-bottom: 1;
    }

    #passphrase-input {
        height: 3;
        margin-bottom: 2;
        background: #000000;
        border: solid #00ffff;
        color: #00ffff;
    }

    #passphrase-input:focus {
        border: heavy #00ffff;
    }

    #button-row {
        height: auto;
        min-height: 3;
        align: center middle;
    }

    .pass-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides - Preserve Native Text Rendering */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-primary {
        border: solid #00ff9f;
    }

    Button.-primary:hover {
        background: #00ff9f20;
        border: heavy #00ff9f;
    }

    Button.-success {
        border: solid #00ff00;
    }

    Button.-success:hover {
        background: #00ff0020;
        border: heavy #00ff00;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
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

    def on_key(self, event) -> None:
        """Handle key press - prevent 'q' from propagating to parent."""
        if event.key == "q":
            event.stop()
            self.dismiss(None)


class PasswordHistoryModal(ModalScreen[None]):
    """Modal screen for viewing full password history."""

    CSS = """
    /* Cyberpunk Password History Modal */
    PasswordHistoryModal {
        align: center middle;
        background: #00000099;
    }

    #history-dialog {
        width: 80;
        height: auto;
        min-height: 30;
        border: heavy #ff00ff;
        background: #0a0a0a;
        padding: 2;
    }

    #history-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #00ffff;
        margin-bottom: 1;
        border-bottom: solid #ff00ff;
        padding-bottom: 1;
    }

    #history-content {
        height: auto;
        min-height: 22;
        border: solid #00ffff;
        margin-bottom: 1;
        background: #000000;
        padding: 1;
    }

    .history-entry {
        margin-bottom: 1;
        padding: 1;
        background: #1a1a1a;
        border: solid #333333;
    }

    .history-password {
        color: #ffff00;
        text-style: bold;
    }

    .history-timestamp {
        color: #888888;
    }

    .history-reason {
        color: #ff00ff;
        text-style: italic;
    }

    #button-row {
        height: auto;
        min-height: 3;
        align: center middle;
        width: 100%;
    }

    .history-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides - Preserve Native Text Rendering */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-primary {
        border: solid #00ff9f;
    }

    Button.-primary:hover {
        background: #00ff9f20;
        border: heavy #00ff9f;
    }

    Button.-success {
        border: solid #00ff00;
    }

    Button.-success:hover {
        background: #00ff0020;
        border: heavy #00ff00;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def __init__(self, entry: VaultEntry):
        """Initialize password history modal."""
        super().__init__()
        self.entry = entry

    def compose(self) -> ComposeResult:
        """Compose history dialog."""
        with Container(id="history-dialog"):
            yield Label(f"Password History: {self.entry.key}", id="history-title")

            password_history = self.entry.get_password_history()

            if not password_history:
                yield ScrollableContainer(
                    Label("No password history available.", classes="history-timestamp"),
                    id="history-content",
                )
            else:
                history_widgets = []
                history_widgets.append(
                    Label(f"Current Password: {self.entry.password}", classes="history-password")
                )
                history_widgets.append(
                    Label(f"Modified: {self.entry.modified}", classes="history-timestamp")
                )
                history_widgets.append(Label(""))  # Blank line
                history_widgets.append(Label(f"Previous Passwords ({len(password_history)}):"))
                history_widgets.append(Label(""))

                for i, hist_entry in enumerate(password_history, 1):
                    history_widgets.append(
                        Label(f"{i}. Password: {hist_entry.password}", classes="history-password")
                    )
                    history_widgets.append(
                        Label(f"   Changed: {hist_entry.changed_at}", classes="history-timestamp")
                    )
                    if hist_entry.reason:
                        history_widgets.append(
                            Label(f"   Reason: {hist_entry.reason}", classes="history-reason")
                        )
                    history_widgets.append(Label(""))  # Blank line between entries

                yield ScrollableContainer(*history_widgets, id="history-content")

            with Horizontal(id="button-row"):
                yield Button("Close", variant="primary", id="btn-close", classes="history-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-close":
            self.dismiss(None)

    def action_close(self) -> None:
        """Close dialog."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key press - prevent 'q' from propagating to parent."""
        if event.key == "q":
            event.stop()
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
        self.totp_refresh_timer = None

    def compose(self) -> ComposeResult:
        """Compose detail panel."""
        yield ScrollableContainer(
            Label("No entry selected", id="no-entry-msg"),
            classes="detail-content",
        )

    def show_entry(self, entry: VaultEntry) -> None:
        """Display entry details."""
        self.current_entry = entry
        self.password_visible = False
        self._update_display()
        self._start_totp_refresh()

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
                classes="detail-content",
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
                from stegvault.vault.totp import generate_totp_code, get_totp_time_remaining

                try:
                    totp_code = generate_totp_code(entry.totp_secret)
                    time_remaining = get_totp_time_remaining()
                    widgets.append(
                        Vertical(
                            Label("TOTP Code:", classes="field-label"),
                            Label(
                                f"{totp_code}  ({time_remaining}s)",
                                classes="field-value",
                                id="totp-code-display",
                            ),
                            classes="detail-field",
                        )
                    )
                except Exception:
                    # Invalid TOTP secret
                    widgets.append(
                        Vertical(
                            Label("TOTP:", classes="field-label"),
                            Label("✗ Invalid secret", classes="field-value"),
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

            # Password History
            password_history = entry.get_password_history()
            if password_history:
                history_lines = [f"Password History ({len(password_history)} entries):"]
                for i, hist_entry in enumerate(password_history[:3], 1):  # Show first 3
                    reason_str = f" - {hist_entry.reason}" if hist_entry.reason else ""
                    history_lines.append(f"  {i}. {hist_entry.changed_at}{reason_str}")
                if len(password_history) > 3:
                    history_lines.append(f"  ... and {len(password_history) - 3} more")

                widgets.append(
                    Vertical(
                        Label("Password History:", classes="field-label"),
                        Label("\n".join(history_lines), classes="field-value"),
                        classes="detail-field",
                    )
                )

            content = ScrollableContainer(*widgets, classes="detail-content")

        # Replace content - use query to find and replace
        existing = self.query(".detail-content")
        if existing:
            for widget in existing:
                widget.remove()
        self.mount(content)

    def clear(self) -> None:
        """Clear the detail panel."""
        self._stop_totp_refresh()
        self.current_entry = None
        self.password_visible = False
        self._update_display()

    def _start_totp_refresh(self) -> None:
        """Start TOTP auto-refresh timer if entry has TOTP secret."""
        self._stop_totp_refresh()  # Stop any existing timer
        if self.current_entry and self.current_entry.totp_secret:
            # Refresh every second
            self.totp_refresh_timer = self.set_interval(1.0, self._refresh_totp_display)

    def _stop_totp_refresh(self) -> None:
        """Stop TOTP auto-refresh timer."""
        if self.totp_refresh_timer:
            self.totp_refresh_timer.stop()
            self.totp_refresh_timer = None

    def _refresh_totp_display(self) -> None:
        """Refresh only the TOTP code display (called every second)."""
        if not self.current_entry or not self.current_entry.totp_secret:
            self._stop_totp_refresh()
            return

        try:
            # Query the TOTP display label
            totp_label = self.query_one("#totp-code-display", Label)

            from stegvault.vault.totp import generate_totp_code, get_totp_time_remaining

            totp_code = generate_totp_code(self.current_entry.totp_secret)
            time_remaining = get_totp_time_remaining()

            # Update label text
            totp_label.update(f"{totp_code}  ({time_remaining}s)")
        except Exception:
            # TOTP label not found or invalid secret, stop refreshing
            self._stop_totp_refresh()


class EntryFormScreen(ModalScreen[Optional[dict]]):
    """Modal screen for adding/editing vault entries."""

    CSS = """
    /* Cyberpunk Entry Form */
    EntryFormScreen {
        align: center middle;
        background: #00000099;
    }

    #form-dialog {
        width: 80;
        height: auto;
        min-height: 30;
        border: heavy #00ffff;
        background: #0a0a0a;
        padding: 2;
    }

    #form-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #00ffff;
        margin-bottom: 1;
        border-bottom: solid #ff00ff;
        padding-bottom: 1;
    }

    .form-field {
        margin-bottom: 1;
    }

    .field-label {
        color: #888888;
        margin-bottom: 0;
    }

    Input {
        width: 100%;
        background: #000000;
        border: solid #00ffff;
        color: #00ffff;
    }

    Input:focus {
        border: heavy #00ffff;
    }

    .password-row {
        height: auto;
        width: 100%;
    }

    .password-row Input {
        width: 1fr;
    }

    .gen-btn {
        min-width: 10;
        width: auto;
        margin-left: 1;
    }

    #button-row {
        height: auto;
        min-height: 3;
        align: center middle;
        margin-top: 1;
    }

    .form-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides - Preserve Native Text Rendering */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-primary {
        border: solid #00ff9f;
    }

    Button.-primary:hover {
        background: #00ff9f20;
        border: heavy #00ff9f;
    }

    Button.-success {
        border: solid #00ff00;
    }

    Button.-success:hover {
        background: #00ff0020;
        border: heavy #00ff00;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
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
                with Horizontal(classes="password-row"):
                    password_input = Input(
                        placeholder="Enter password",
                        password=True,
                        id="input-password",
                    )
                    if self.entry:
                        password_input.value = self.entry.password
                    yield password_input
                    yield Button(
                        "GEN",
                        variant="warning",
                        id="btn-generate-password",
                        classes="gen-btn",
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

    def on_key(self, event) -> None:
        """Handle key press - prevent 'q' from propagating to parent."""
        if event.key == "q":
            event.stop()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)


class DeleteConfirmationScreen(ModalScreen[bool]):
    """Modal screen for confirming entry deletion."""

    CSS = """
    /* Cyberpunk Delete Confirmation */
    DeleteConfirmationScreen {
        align: center middle;
        background: #00000099;
    }

    #confirm-dialog {
        width: 60;
        height: auto;
        min-height: 12;
        border: heavy #ff0000;
        background: #0a0a0a;
        padding: 1;
    }

    #confirm-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #ff0000;
        margin-bottom: 0;
        border-bottom: solid #ff0000;
        padding-bottom: 0;
    }

    #confirm-message {
        width: 100%;
        text-align: center;
        color: #00ffff;
        margin-bottom: 0;
    }

    #confirm-warning {
        width: 100%;
        text-align: center;
        color: #ff0080;
        margin-bottom: 0;
        text-style: italic;
    }

    #entry-key {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #ffff00;
        margin-bottom: 0;
    }

    #button-row {
        height: auto;
        min-height: 3;
        align: center middle;
        margin: 0;
    }

    .confirm-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides - Preserve Native Text Rendering */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-primary {
        border: solid #00ff9f;
    }

    Button.-primary:hover {
        background: #00ff9f20;
        border: heavy #00ff9f;
    }

    Button.-success {
        border: solid #00ff00;
    }

    Button.-success:hover {
        background: #00ff0020;
        border: heavy #00ff00;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
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
            yield Label("This action cannot be undone.", id="confirm-warning")

            with Horizontal(id="button-row"):
                yield Button("Delete", variant="error", id="btn-delete", classes="confirm-button")
                yield Button("Cancel", variant="default", id="btn-cancel", classes="confirm-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-delete":
            self.dismiss(True)  # Confirmed
        elif event.button.id == "btn-cancel":
            self.dismiss(False)  # Cancelled

    def on_key(self, event) -> None:
        """Handle key press - prevent 'q' from propagating to parent."""
        if event.key == "q":
            event.stop()
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(False)


class UnsavedChangesScreen(ModalScreen[str]):
    """Modal screen for unsaved changes warning."""

    CSS = """
    /* Cyberpunk Unsaved Changes Warning */
    UnsavedChangesScreen {
        align: center middle;
        background: #00000099;
    }

    #unsaved-dialog {
        width: 60;
        height: auto;
        min-height: 10;
        border: heavy #ff0080;
        background: #0a0a0a;
        padding: 0;
    }

    #unsaved-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #ff0080;
        margin-bottom: 1;
        border-bottom: solid #ff0080;
        padding-bottom: 1;
    }

    #unsaved-message {
        text-align: center;
        color: #ffff00;
        margin-bottom: 0;
    }

    #unsaved-warning {
        text-align: center;
        color: #ff0080;
        text-style: bold;
        margin-bottom: 0;
    }

    #button-row {
        width: 100%;
        align: center middle;
        margin-top: 0;
    }

    .unsaved-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides - Preserve Native Text Rendering */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-primary {
        border: solid #00ff9f;
    }

    Button.-primary:hover {
        background: #00ff9f20;
        border: heavy #00ff9f;
    }

    Button.-success {
        border: solid #00ff00;
    }

    Button.-success:hover {
        background: #00ff0020;
        border: heavy #00ff00;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose unsaved changes dialog."""
        with Container(id="unsaved-dialog"):
            yield Label("⚠️ UNSAVED CHANGES ⚠️", id="unsaved-title")
            yield Label(
                "You have unsaved changes in the vault.",
                id="unsaved-message",
            )
            yield Label(
                "What do you want to do?",
                id="unsaved-warning",
            )

            with Horizontal(id="button-row"):
                yield Button(
                    "Save & Exit",
                    variant="success",
                    id="btn-save-exit",
                    classes="unsaved-button",
                )
                yield Button(
                    "Don't Save",
                    variant="error",
                    id="btn-dont-save",
                    classes="unsaved-button",
                )
                yield Button(
                    "Cancel",
                    variant="default",
                    id="btn-cancel",
                    classes="unsaved-button",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-save-exit":
            self.dismiss("save")
        elif event.button.id == "btn-dont-save":
            self.dismiss("dont_save")
        elif event.button.id == "btn-cancel":
            self.dismiss("cancel")

    def on_key(self, event) -> None:
        """Handle key press - prevent 'q' from propagating to parent."""
        if event.key == "q":
            event.stop()
            self.dismiss("cancel")

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss("cancel")


class PasswordGeneratorScreen(ModalScreen[Optional[str]]):
    """Modal screen for generating secure passwords."""

    CSS = """
    /* Cyberpunk Password Generator */
    PasswordGeneratorScreen {
        align: center middle;
        background: #00000099;
    }

    #generator-dialog {
        width: 70;
        height: auto;
        border: heavy #00ffff;
        background: #0a0a0a;
        padding: 1;
    }

    #generator-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #00ffff;
        margin-bottom: 1;
        border-bottom: solid #ff00ff;
        padding-bottom: 1;
    }

    .generator-section {
        width: 100%;
        margin-bottom: 1;
        padding: 0;
        height: auto;
    }

    .section-label {
        width: 100%;
        text-align: center;
        color: #888888;
        margin-bottom: 0;
        padding: 0;
    }

    #password-preview {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #00ff00;
        background: #000000;
        border: solid #00ffff;
        padding: 1;
        min-height: 3;
        content-align: center middle;
    }

    #password-preview-container {
        width: 100%;
        height: auto;
        align: center middle;
    }

    #length-value {
        width: 100%;
        text-align: center;
        color: #ff00ff;
        margin: 0;
    }

    #length-value-container {
        width: 100%;
        height: auto;
    }

    #length-controls {
        width: 100%;
        height: auto;
        margin-top: 0;
        padding: 0;
        align: center middle;
    }

    #charset-info {
        color: #00ffff;
        text-align: center;
        margin: 0;
        padding: 0;
    }

    .options-grid {
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0;
        align: center middle;
    }

    .option-button {
        margin: 0 1;
        min-width: 20;
        height: 3;
    }

    #button-row {
        width: 100%;
        height: auto;
        margin-top: 1;
        padding: 0;
        align: center middle;
    }

    .gen-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides - Preserve Native Text Rendering */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-primary {
        border: solid #00ff9f;
    }

    Button.-primary:hover {
        background: #00ff9f20;
        border: heavy #00ff9f;
    }

    Button.-success {
        border: solid #00ff00;
    }

    Button.-success:hover {
        background: #00ff0020;
        border: heavy #00ff00;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("g", "generate", "Generate"),
        Binding("q", "ignore_quit", "Close Modal (ESC)", show=True, priority=True),
    ]

    def __init__(self):
        """Initialize password generator screen."""
        super().__init__()
        self.length = 16
        self.use_lowercase = True
        self.use_uppercase = True
        self.use_digits = True
        self.use_symbols = True
        # Flag to track if we should block quit
        self._block_quit = True
        self.exclude_ambiguous = False
        self.current_password = ""  # nosec B105 - not a hardcoded password, just initialization

    def compose(self) -> ComposeResult:
        """Compose password generator dialog."""
        with Container(id="generator-dialog"):
            yield Label("🔐 Password Generator", id="generator-title")

            # Password preview
            with Vertical(classes="generator-section"):
                yield Label("Generated Password:", classes="section-label")
                with Horizontal(id="password-preview-container"):
                    yield Label(self._generate_password(), id="password-preview")

            # Length control
            with Vertical(classes="generator-section"):
                yield Label("Password Length:", classes="section-label")
                with Horizontal(id="length-value-container"):
                    yield Label(f"{self.length} characters", id="length-value")
                with Horizontal(id="length-controls"):
                    yield Button("-", id="btn-length-dec", classes="gen-button")
                    yield Button("+", id="btn-length-inc", classes="gen-button")

            # Character options
            with Vertical(classes="generator-section"):
                yield Label("Character Options:", classes="section-label")
                with Horizontal(classes="options-grid"):
                    yield Button(
                        "✓ Lowercase (a-z)",
                        variant="success",
                        id="btn-opt-lowercase",
                        classes="option-button",
                    )
                    yield Button(
                        "✓ Uppercase (A-Z)",
                        variant="success",
                        id="btn-opt-uppercase",
                        classes="option-button",
                    )
                with Horizontal(classes="options-grid"):
                    yield Button(
                        "✓ Digits (0-9)",
                        variant="success",
                        id="btn-opt-digits",
                        classes="option-button",
                    )
                    yield Button(
                        "✓ Symbols (!@#$)",
                        variant="success",
                        id="btn-opt-symbols",
                        classes="option-button",
                    )

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

        elif event.button.id == "btn-opt-lowercase":
            # Toggle lowercase (but keep at least one option enabled)
            new_value = not self.use_lowercase
            if not new_value and not (self.use_uppercase or self.use_digits or self.use_symbols):
                self.app.notify("At least one character type must be enabled", severity="warning")
                return
            self.use_lowercase = new_value
            self._update_option_button(event.button, self.use_lowercase)

        elif event.button.id == "btn-opt-uppercase":
            # Toggle uppercase (but keep at least one option enabled)
            new_value = not self.use_uppercase
            if not new_value and not (self.use_lowercase or self.use_digits or self.use_symbols):
                self.app.notify("At least one character type must be enabled", severity="warning")
                return
            self.use_uppercase = new_value
            self._update_option_button(event.button, self.use_uppercase)

        elif event.button.id == "btn-opt-digits":
            # Toggle digits (but keep at least one option enabled)
            new_value = not self.use_digits
            if not new_value and not (self.use_lowercase or self.use_uppercase or self.use_symbols):
                self.app.notify("At least one character type must be enabled", severity="warning")
                return
            self.use_digits = new_value
            self._update_option_button(event.button, self.use_digits)

        elif event.button.id == "btn-opt-symbols":
            # Toggle symbols (but keep at least one option enabled)
            new_value = not self.use_symbols
            if not new_value and not (self.use_lowercase or self.use_uppercase or self.use_digits):
                self.app.notify("At least one character type must be enabled", severity="warning")
                return
            self.use_symbols = new_value
            self._update_option_button(event.button, self.use_symbols)

        elif event.button.id == "btn-use":
            # Return current password
            if self.current_password:
                self.dismiss(self.current_password)
            else:
                self.app.notify("Please generate a password first", severity="warning")

        elif event.button.id == "btn-cancel":
            self.dismiss(None)

    def _update_option_button(self, button: Button, enabled: bool) -> None:
        """Update option button appearance based on state."""
        label_map = {
            "btn-opt-lowercase": ("✓ Lowercase (a-z)", "✗ Lowercase (a-z)"),
            "btn-opt-uppercase": ("✓ Uppercase (A-Z)", "✗ Uppercase (A-Z)"),
            "btn-opt-digits": ("✓ Digits (0-9)", "✗ Digits (0-9)"),
            "btn-opt-symbols": ("✓ Symbols (!@#$)", "✗ Symbols (!@#$)"),
        }

        enabled_label, disabled_label = label_map.get(button.id, ("", ""))
        button.label = enabled_label if enabled else disabled_label
        button.variant = "success" if enabled else "error"

    def action_generate(self) -> None:
        """Generate new password (keyboard shortcut)."""
        new_password = self._generate_password()
        preview = self.query_one("#password-preview", Label)
        preview.update(new_password)

    async def key(self, event) -> None:
        """Override key method - intercept 'q' at lowest level."""
        try:
            if event.key == "q":
                # Block 'q' completely
                event.stop()
                event.prevent_default()
                # Show notification
                try:
                    self.app.notify("Press ESC to close this modal", severity="warning", timeout=2)
                except Exception:
                    pass
                # Don't call parent - completely stop processing
                return
        except Exception:
            pass
        # For other keys, call parent
        await super().key(event)

    def on_key(self, event) -> None:
        """Handle key press - block 'q' to prevent terminal crash."""
        try:
            if event.key == "q":
                # Completely block 'q' key - do nothing at all
                event.stop()
                event.prevent_default()
                # Show notification
                try:
                    self.app.notify(
                        "'q' disabled in this modal. Use ESC to close.",
                        severity="warning",
                        timeout=3,
                    )
                except Exception:
                    pass
                return
        except Exception:
            # Catch any exception to prevent crash
            pass

    def action_ignore_quit(self) -> None:
        """Override quit action - do absolutely nothing."""
        # Don't exit, don't dismiss, don't do anything
        try:
            self.app.notify("Use ESC to close this modal", severity="warning", timeout=2)
        except Exception:
            pass

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)
