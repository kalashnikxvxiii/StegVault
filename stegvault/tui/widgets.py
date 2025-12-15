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
    Select,
)
from textual.widgets._directory_tree import DirEntry
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from rich.text import Text

from stegvault.vault import Vault, VaultEntry
from stegvault.utils.favorite_folders import FavoriteFoldersManager


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
        width: 90%;
        max-width: 80;
        height: auto;
        border: heavy #ff00ff;
        background: #0a0a0a;
        padding: 0;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
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
        overflow-y: auto;  /* Enable vertical scrolling on resize */
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

    def action_dismiss(self) -> None:
        """Dismiss help screen."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            event.stop()
            self.app.action_quit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-close":
            self.action_dismiss()


class QuitConfirmationScreen(ModalScreen[bool]):
    """Modal screen for confirming application exit."""

    CSS = """
    /* Cyberpunk Quit Confirmation */
    QuitConfirmationScreen {
        align: center middle;
        background: #00000099;
    }

    #quit-dialog {
        width: 80%;
        max-width: 60;
        height: auto;
        min-height: 12;
        border: heavy #ffff00;
        background: #0a0a0a;
        padding: 1;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
    }

    #quit-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #ffff00;
        margin-bottom: 0;
        border-bottom: solid #ffff00;
        padding-bottom: 0;
    }

    #quit-message {
        width: 100%;
        text-align: center;
        color: #00ffff;
        margin-bottom: 0;
        padding: 1 0;
    }

    #button-row {
        height: auto;
        min-height: 3;
        align: center middle;
        margin: 0;
    }

    .quit-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }

    /* Cyberpunk Button Overrides */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-error {
        border: solid #ff0080;
    }

    Button.-error:hover {
        background: #ff008020;
        border: heavy #ff0080;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self):
        """Initialize quit confirmation screen."""
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose quit confirmation dialog."""
        with Container(id="quit-dialog"):
            yield Label("⚡ Quit StegVault", id="quit-title")
            yield Label("Do you really want to quit StegVault?", id="quit-message")

            with Horizontal(id="button-row"):
                yield Button("YES", variant="error", id="btn-yes", classes="quit-button")
                yield Button("NO", variant="default", id="btn-no", classes="quit-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-yes":
            self.dismiss(True)  # Confirmed - quit app
        elif event.button.id == "btn-no":
            self.dismiss(False)  # Cancelled - stay in app

    def action_cancel(self) -> None:
        """Cancel and close dialog (ESC key)."""
        self.dismiss(False)  # Cancelled - stay in app


class FileSelectScreen(ModalScreen[Optional[str]]):
    """Modal screen for selecting a vault image file with favorite folders."""

    CSS = """
    /* Cyberpunk File Select Dialog */
    FileSelectScreen {
        align: center middle;
        background: #00000099;
    }

    #file-dialog {
        width: 95%;
        max-width: 90;
        height: 48;
        max-height: 95%;
        border: heavy #00ffff;
        background: #0a0a0a;
        padding: 2;
        overflow-y: auto;  /* Enable internal scrolling when content exceeds available space */
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

    #favorites-row {
        height: 3;
        margin-bottom: 1;
        align: left middle;
    }

    #btn-favorites {
        width: 1fr;
        height: 3;
        margin-right: 1;
        border: solid #ffff00;
        background: #000000;
        color: #ffff00;
    }

    #btn-favorites:hover {
        background: #ffff0030;
        border: heavy #ffff00;
    }

    #btn-add-favorite {
        width: 12;
        height: 3;
        margin-right: 1;
        border: solid #ffff00;
        background: #000000;
    }

    #btn-add-favorite:hover {
        background: #ffff0030;
        border: heavy #ffff00;
    }

    #btn-home {
        width: 8;
        height: 3;
        border: solid #00ff00;
        background: #000000;
    }

    #btn-home:hover {
        background: #00ff0030;
        border: heavy #00ff00;
    }

    /* Drive Selector Row */
    #drive-row {
        height: 3;
        margin-bottom: 1;
        align: left middle;
    }

    .drive-button {
        width: auto;
        min-width: 6;
        height: 3;
        margin-right: 1;
        padding: 0 2;
        border: solid #ff00ff;
        background: #000000;
        color: #ff00ff;
        text-style: bold;
    }

    .drive-button:hover {
        background: #ff00ff30;
        border: heavy #ff00ff;
        color: #ffffff;
    }

    .drive-button:focus {
        background: #000000;
        border: double #ff00ff;
    }

    /* Cyberpunk Overlay Favorites Dropdown */
    #favorites-dropdown {
        display: none;  /* Hidden by default */
        layer: overlay;  /* Render as overlay */
        offset-y: 7;  /* Position exactly below favorites-row (padding:2 + title:1 + margin:1 + row:3) */
        /* offset-x and width set dynamically in Python to match Favorites button */
        height: auto;
        max-height: 15;
        border: heavy #ffff00;  /* Cyberpunk yellow border */
        background: #000000;     /* Pure black background */
        padding: 0;
        overflow-y: auto;  /* Enable scrolling for overflow */
    }

    #favorites-dropdown.visible {
        display: block;  /* Show when visible class added */
        border: heavy #00ffff;  /* Cyan border when active */
    }

    #favorites-dropdown > ListItem {
        color: #ffff00;  /* Yellow text */
        padding: 0 2;
        background: #000000;
    }

    #favorites-dropdown > ListItem:hover {
        background: #ffff0030;  /* Yellow glow on hover */
        color: #000000;
        text-style: bold;
    }

    #favorites-dropdown > .list-item--highlight {
        background: #00ffff30;  /* Cyan highlight */
        color: #ffffff;
        text-style: bold;
    }

    #file-tree {
        height: 20;
        min-height: 10;
        border: solid #ff00ff;
        margin-bottom: 1;
        background: #000000;
        overflow-y: auto;
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
        Binding("f", "toggle_favorite", "Add/Remove Favorite", show=True),
    ]

    def __init__(self, title: str = "Select Vault Image"):
        """Initialize file selection screen."""
        super().__init__()
        self.title = title
        self.selected_path: Optional[str] = None
        self.last_selected_path: Optional[str] = None
        self.last_click_time: float = 0
        self.favorites_manager = FavoriteFoldersManager()
        self.current_directory: Optional[str] = None
        self.favorites_button_text: str = "⚡ Favorites"  # Current button text

    def on_resize(self, event) -> None:
        """Handle screen resize - schedule dropdown update for next event loop cycle."""
        # Use call_later to update dropdown after layout has been fully recalculated
        self.call_later(self._update_dropdown_on_resize)

    def _update_dropdown_on_resize(self) -> None:
        """Update dropdown position and width to match Favorites button after resize."""
        try:
            dropdown = self.query_one("#favorites-dropdown", ListView)
            if dropdown.has_class("visible"):
                # Dropdown is visible, update its position and width to match button
                btn = self.query_one("#btn-favorites", Button)
                dialog = self.query_one("#file-dialog")
                if hasattr(btn, "region") and btn.region.width > 0:
                    # Calculate offset-x relative to the dialog container, shift slightly left
                    offset_x = btn.region.x - dialog.region.x - 3
                    dropdown.styles.offset = (offset_x, 7)
                    dropdown.styles.width = btn.region.width
                    # Force dropdown to refresh with new dimensions
                    dropdown.refresh(layout=True)
        except Exception:  # nosec B110
            pass

    def _get_available_drives(self):
        """Get list of available drives on the system.

        Returns:
            List of drive letters (e.g., ['C:\\', 'D:\\', 'E:\\']) on Windows,
            or ['/'] on Unix systems.
        """
        from pathlib import Path
        import platform

        if platform.system() == "Windows":
            # Check common drive letters (A-Z)
            drives = []
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive_path = Path(f"{letter}:\\")
                try:
                    # Check if drive exists by testing if we can list it
                    # This is more reliable than just checking exists()
                    if drive_path.exists():
                        drives.append(f"{letter}:\\")
                except (PermissionError, OSError):
                    # Drive not accessible or doesn't exist
                    continue
            return drives if drives else [str(Path.cwd().anchor)]
        else:
            # Unix systems have single root
            return ["/"]

    def compose(self) -> ComposeResult:
        """Compose file selection dialog with favorite folders."""
        from pathlib import Path
        import time

        with Container(id="file-dialog"):
            yield Label(f">> {self.title.upper()}", id="file-title")

            # Favorite Folders Dropdown Row
            with Horizontal(id="favorites-row"):
                # Custom button to toggle dropdown
                yield Button(
                    self.favorites_button_text,
                    id="btn-favorites",
                    variant="default",
                )
                yield Button("⚡ Add", id="btn-add-favorite")
                yield Button("HOME", id="btn-home", variant="success")

            # Drive Selector Row (Windows only - shows available drives)
            available_drives = self._get_available_drives()
            if len(available_drives) > 1:
                with Horizontal(id="drive-row"):
                    for drive in available_drives:
                        yield Button(
                            drive,
                            id=f"btn-drive-{drive[0]}",
                            variant="primary",
                            classes="drive-button",
                        )

            # Inline Favorites Dropdown (hidden by default)
            with ListView(id="favorites-dropdown"):
                # Populated dynamically when button is clicked
                pass

            # Directory Tree
            # Start from root of current drive (cross-platform)
            # Windows: C:\ (or D:\, E:\, etc. depending on current working directory)
            # Unix: /
            start_path = str(Path.cwd().anchor)
            yield FilteredDirectoryTree(start_path, id="file-tree")

            # Path Input
            yield Input(
                placeholder="Type file path or select from tree above",
                id="file-path-input",
            )

            # Buttons
            with Horizontal(id="button-row"):
                yield Button("SELECT", variant="success", id="btn-select", classes="file-button")
                yield Button("CANCEL", variant="default", id="btn-cancel", classes="file-button")

    def on_mount(self) -> None:
        """Set focus on input field when screen mounts."""
        input_field = self.query_one("#file-path-input", Input)
        input_field.focus()
        # Update favorite button initial state
        self._update_favorite_button()

    def _switch_drive(self, drive_path: str) -> None:
        """Switch DirectoryTree to a different drive.

        Args:
            drive_path: Root path of the drive (e.g., 'C:\\', 'D:\\')
        """
        from pathlib import Path

        try:
            # Get existing tree and change its root path
            tree = self.query_one("#file-tree", FilteredDirectoryTree)
            tree.path = Path(drive_path)
            tree.reload()

            # Update current directory
            self.current_directory = drive_path

            # Hide favorites dropdown if visible
            try:
                dropdown = self.query_one("#favorites-dropdown", ListView)
                dropdown.remove_class("visible")
            except Exception:  # nosec B110
                pass

            # Notify user
            self.app.notify(f"Switched to drive: {drive_path}", severity="information")

        except Exception as e:
            self.app.notify(f"Failed to switch drive: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-select":
            input_widget = self.query_one("#file-path-input", Input)
            path = input_widget.value.strip()

            if not path:
                self.app.notify("Please enter a file path", severity="error")
            elif not Path(path).exists():
                self.app.notify("Path does not exist", severity="error")
            elif Path(path).is_dir():
                self.app.notify("Please select a file, not a directory", severity="error")
            elif Path(path).is_file():
                self.dismiss(path)
            else:
                self.app.notify("Please enter a valid file path", severity="error")
        elif event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-favorites":
            # Toggle inline dropdown
            self._toggle_favorites_dropdown()
        elif event.button.id == "btn-add-favorite":
            self.action_toggle_favorite()
        elif event.button.id == "btn-home":
            # Reset favorites button text, hide dropdown, and navigate to home
            self.favorites_button_text = "⚡ Favorites"
            try:
                btn = self.query_one("#btn-favorites", Button)
                btn.label = self.favorites_button_text
                # Hide dropdown if visible
                dropdown = self.query_one("#favorites-dropdown", ListView)
                dropdown.remove_class("visible")
            except Exception:  # nosec B110
                pass
            self._navigate_to_folder("C:\\")
        elif event.button.id and event.button.id.startswith("btn-drive-"):
            # Drive button clicked - extract drive letter and switch
            drive_letter = event.button.id.split("-")[-1]
            drive_path = f"{drive_letter}:\\"
            self._switch_drive(drive_path)

    def _refresh_favorites_dropdown(self) -> None:
        """Refresh dropdown list with current favorites (if visible)."""
        try:
            dropdown = self.query_one("#favorites-dropdown", ListView)
            if dropdown.has_class("visible"):
                # Dropdown is open, refresh its contents
                favorites = self.favorites_manager.get_favorites()
                dropdown.clear()
                for fav in favorites:
                    dropdown.append(ListItem(Label(f"⚡ {fav['name']}")))
        except Exception:  # nosec B110
            pass

    def _toggle_favorites_dropdown(self) -> None:
        """Toggle visibility of overlay favorites dropdown."""
        favorites = self.favorites_manager.get_favorites()

        if not favorites:
            self.app.notify("No favorites yet. Add some first!", severity="information")
            return

        dropdown = self.query_one("#favorites-dropdown", ListView)

        # If dropdown is visible, hide it
        if dropdown.has_class("visible"):
            dropdown.remove_class("visible")
        else:
            # Populate and show dropdown
            dropdown.clear()
            for fav in favorites:
                dropdown.append(ListItem(Label(f"⚡ {fav['name']}")))

            # Calculate and set dropdown position and width to match Favorites button exactly
            try:
                btn = self.query_one("#btn-favorites", Button)
                dialog = self.query_one("#file-dialog")
                # Force layout refresh to ensure button has rendered size
                self.refresh(layout=True)

                # Get button's actual rendered region (position and size)
                if hasattr(btn, "region") and btn.region.width > 0:
                    # Calculate offset-x relative to the dialog container, shift slightly left
                    offset_x = btn.region.x - dialog.region.x - 3
                    dropdown.styles.offset = (offset_x, 7)
                    # Set dropdown width to match button exactly
                    dropdown.styles.width = btn.region.width
                else:
                    # Fallback to reasonable defaults
                    dropdown.styles.offset = (0, 7)
                    dropdown.styles.width = 50
            except Exception:  # nosec B110
                # Fallback if something fails
                dropdown.styles.offset = (0, 7)
                dropdown.styles.width = 50

            dropdown.add_class("visible")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection from favorites dropdown."""
        # Only handle our favorites dropdown, not other ListViews
        if event.list_view.id != "favorites-dropdown":
            return

        favorites = self.favorites_manager.get_favorites()
        dropdown = self.query_one("#favorites-dropdown", ListView)
        selected_index = dropdown.index

        if 0 <= selected_index < len(favorites):
            selected_fav = favorites[selected_index]
            selected_path = selected_fav["path"]

            # Update button text
            self.favorites_button_text = f"⚡ {selected_fav['name']}"
            try:
                btn = self.query_one("#btn-favorites", Button)
                btn.label = self.favorites_button_text
            except Exception:  # nosec B110
                pass

            # Hide dropdown after selection
            dropdown.remove_class("visible")

            # Navigate to selected folder
            self._navigate_to_folder(selected_path)

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Update button when user navigates to a directory in tree."""
        self._update_favorite_button()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection from tree (update button + double-click logic)."""
        import time

        # Update favorite button for parent directory of selected file
        self._update_favorite_button()

        # Original double-click logic
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

    def _get_folder_display_name(self, folder_path: str) -> str:
        """Get a display-friendly name for a folder path.

        Args:
            folder_path: Absolute path to folder

        Returns:
            Display name (e.g., "Documents" or "C:\" for root)
        """
        path = Path(folder_path)
        folder_name = path.name

        # If name is empty (root directory like C:\), use drive letter
        if not folder_name:
            # For Windows: "C:\" becomes "C:\"
            # For Unix: "/" becomes "/"
            if path.drive:
                return f"{path.drive}\\"
            else:
                return str(path)

        return folder_name

    def _navigate_to_folder(self, folder_path: str) -> None:
        """Navigate DirectoryTree to specified folder.

        Args:
            folder_path: Absolute path to folder
        """
        try:
            tree = self.query_one("#file-tree", FilteredDirectoryTree)
            # Reset tree to new path
            tree.path = Path(folder_path)
            tree.reload()
            self.current_directory = folder_path
            display_name = self._get_folder_display_name(folder_path)
            self.app.notify(f"Navigated to: {display_name}", severity="information")
            # Update button text after navigation
            self._update_favorite_button()
        except Exception as e:  # nosec B110
            self.app.notify(f"Failed to navigate to folder: {str(e)}", severity="error")

    def _get_current_directory(self) -> Optional[str]:
        """Get current directory from tree or input."""
        current_dir = None

        try:
            tree = self.query_one("#file-tree", FilteredDirectoryTree)
            # First try to get the currently selected/highlighted node
            if tree.cursor_node and hasattr(tree.cursor_node, "data"):
                cursor_path = tree.cursor_node.data.path
                # If it's a directory, use it; if file, use parent
                if cursor_path.is_dir():
                    current_dir = str(cursor_path.resolve())
                else:
                    current_dir = str(cursor_path.parent.resolve())
            # Fallback to tree root path
            elif tree.path:
                current_dir = str(tree.path.resolve())
        except Exception:  # nosec B110
            pass

        if not current_dir:
            # Fallback to input field's parent directory
            try:
                input_widget = self.query_one("#file-path-input", Input)
                if input_widget.value:
                    path = Path(input_widget.value.strip())
                    if path.exists():
                        current_dir = str(
                            path.parent.resolve() if path.is_file() else path.resolve()
                        )
            except Exception:  # nosec B110
                pass

        return current_dir

    def _update_favorite_button(self) -> None:
        """Update favorite button text based on current directory."""
        try:
            button = self.query_one("#btn-add-favorite", Button)
            current_dir = self._get_current_directory()

            if current_dir and self.favorites_manager.is_favorite(current_dir):
                button.label = "⚡ Remove"
            else:
                button.label = "⚡ Add"
        except Exception:  # nosec B110
            pass

    def action_toggle_favorite(self) -> None:
        """Add or remove current directory from favorites."""
        current_dir = self._get_current_directory()

        if not current_dir:
            self.app.notify("No folder selected to add to favorites", severity="warning")
            return

        # Check if already a favorite
        if self.favorites_manager.is_favorite(current_dir):
            # Remove from favorites
            if self.favorites_manager.remove_folder(current_dir):
                display_name = self._get_folder_display_name(current_dir)
                self.app.notify(f"Removed from favorites: {display_name}", severity="information")
                self._update_favorite_button()
                # Refresh dropdown if visible
                self._refresh_favorites_dropdown()
            else:
                self.app.notify("Failed to remove favorite", severity="error")
        else:
            # Add to favorites
            if self.favorites_manager.add_folder(current_dir):
                display_name = self._get_folder_display_name(current_dir)
                self.app.notify(f"Added to favorites: {display_name}", severity="information")
                self._update_favorite_button()
                # Refresh dropdown if visible
                self._refresh_favorites_dropdown()
            else:
                self.app.notify("Folder already in favorites", severity="warning")

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            # Check if input field has focus (user is typing)
            try:
                input_field = self.query_one("#file-path-input", Input)
                if input_field.has_focus:
                    # User is typing in input field, let 'q' be typed normally
                    return
            except Exception:  # nosec B110
                pass

            # Input doesn't have focus, trigger app quit confirmation
            event.stop()
            self.app.action_quit()


class PassphraseInputScreen(ModalScreen[Optional[str]]):
    """Modal screen for passphrase input."""

    CSS = """
    /* Cyberpunk Passphrase Dialog */
    PassphraseInputScreen {
        align: center middle;
        background: #00000099;
    }

    #passphrase-dialog {
        width: 80%;
        max-width: 60;
        height: auto;
        max-height: 90%;
        min-height: 15;
        border: heavy #00ffff;
        background: #0a0a0a;
        padding: 2;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
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

    .input-row {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .passphrase-field {
        height: 3;
        width: 1fr;
        background: #000000;
        border: solid #00ffff;
        color: #00ffff;
    }

    .passphrase-field:focus {
        border: heavy #00ffff;
    }

    .toggle-visibility {
        width: 8;
        height: 3;
        margin-left: 1;
        min-width: 8;
        border: solid #ffff00;
        background: #000000;
        color: #ffff00;
    }

    .toggle-visibility:hover {
        background: #ffff0020;
        border: heavy #ffff00;
    }

    #strength-container {
        width: 100%;
        height: auto;
        margin-bottom: 2;
    }

    #strength-label {
        color: #888888;
        margin-bottom: 0;
    }

    #strength-indicator {
        height: 1;
        width: 100%;
        background: #000000;
        border: solid #333333;
    }

    #strength-bar {
        height: 1;
        background: #000000;
    }

    .label-text {
        color: #888888;
        margin-bottom: 0;
    }

    #button-row {
        height: auto;
        min-height: 3;
        align: center middle;
        margin-top: 2;
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

    def __init__(self, title: str = "Enter Passphrase", mode: str = "unlock"):
        """Initialize passphrase input screen.

        Args:
            title: Dialog title
            mode: "unlock" for simple passphrase entry, "set" for new passphrase with validation
        """
        super().__init__()
        self.title = title
        self.mode = mode
        self.password_visible = False
        self.confirm_visible = False
        self.strength_score = 0
        self.strength_label = "Very Weak"

    def compose(self) -> ComposeResult:
        """Compose passphrase dialog."""
        with Container(id="passphrase-dialog"):
            yield Label(self.title, id="passphrase-title")

            # Main passphrase field with eye button
            if self.mode == "set":
                yield Label("Passphrase:", classes="label-text")

            with Horizontal(classes="input-row"):
                yield Input(
                    placeholder=(
                        "Enter vault passphrase"
                        if self.mode == "unlock"
                        else "Enter new passphrase"
                    ),
                    password=True,
                    id="passphrase-input",
                    classes="passphrase-field",
                )
                if self.mode == "set":
                    yield Button("SHOW", id="btn-toggle-pass", classes="toggle-visibility")

            # Strength indicator (only for "set" mode)
            if self.mode == "set":
                with Vertical(id="strength-container"):
                    yield Static("Strength: Very Weak", id="strength-label")
                    yield Static("", id="strength-bar")

                # Confirmation field
                yield Label("Confirm Passphrase:", classes="label-text")
                with Horizontal(classes="input-row"):
                    yield Input(
                        placeholder="Re-enter passphrase",
                        password=True,
                        id="passphrase-confirm",
                        classes="passphrase-field",
                    )
                    yield Button("SHOW", id="btn-toggle-confirm", classes="toggle-visibility")

            # Buttons
            with Horizontal(id="button-row"):
                button_label = "Set Passphrase" if self.mode == "set" else "Unlock"
                yield Button(
                    button_label, variant="primary", id="btn-unlock", classes="pass-button"
                )
                yield Button("Cancel", variant="default", id="btn-cancel", classes="pass-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-unlock":
            input_widget = self.query_one("#passphrase-input", Input)
            passphrase = input_widget.value

            if not passphrase:
                self.app.notify("Passphrase cannot be empty", severity="error")
                return

            # Additional validation for "set" mode
            if self.mode == "set":
                confirm_widget = self.query_one("#passphrase-confirm", Input)
                confirm = confirm_widget.value

                # Check if passphrases match
                if passphrase != confirm:
                    self.app.notify("Passphrases do not match", severity="error")
                    return

                # Check minimum strength (score must be at least 2 = "Fair")
                if self.strength_score < 2:
                    self.app.notify(
                        f"Passphrase too weak ({self.strength_label}). Minimum: Fair",
                        severity="error",
                    )
                    return

            self.dismiss(passphrase)

        elif event.button.id == "btn-cancel":
            self.dismiss(None)

        elif event.button.id == "btn-toggle-pass":
            # Toggle main passphrase visibility
            input_widget = self.query_one("#passphrase-input", Input)
            self.password_visible = not self.password_visible
            input_widget.password = not self.password_visible
            event.button.label = "HIDE" if self.password_visible else "SHOW"

        elif event.button.id == "btn-toggle-confirm":
            # Toggle confirm passphrase visibility
            confirm_widget = self.query_one("#passphrase-confirm", Input)
            self.confirm_visible = not self.confirm_visible
            confirm_widget.password = not self.confirm_visible
            event.button.label = "HIDE" if self.confirm_visible else "SHOW"

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle passphrase input changes to update strength indicator."""
        if event.input.id == "passphrase-input" and self.mode == "set":
            passphrase = event.value

            if passphrase:
                # Import here to avoid circular imports
                from stegvault.vault.generator import assess_password_strength

                self.strength_label, self.strength_score = assess_password_strength(passphrase)

                # Update strength label
                strength_widget = self.query_one("#strength-label", Static)
                strength_widget.update(f"Strength: {self.strength_label}")

                # Update strength bar (visual indicator)
                bar_widget = self.query_one("#strength-bar", Static)

                # Map score to percentage and color
                percentages = {0: 0.20, 1: 0.40, 2: 0.60, 3: 0.80, 4: 1.00}
                colors = {
                    0: "red",  # Very Weak - red
                    1: "#ff6600",  # Weak - orange
                    2: "yellow",  # Fair - yellow
                    3: "green",  # Strong - green
                    4: "#66ff00",  # Very Strong - bright green
                }

                percentage = percentages.get(self.strength_score, 0.20)
                color = colors.get(self.strength_score, "red")

                # Create visual bar with fixed total width (60 blocks to fill container)
                total_blocks = 60
                filled_blocks = int(total_blocks * percentage)

                # Create bar with Rich markup for colored blocks
                if filled_blocks > 0:
                    bar = f"[{color}]{'█' * filled_blocks}[/{color}]"
                else:
                    bar = ""

                bar_widget.update(bar)
            else:
                # Empty passphrase
                strength_widget = self.query_one("#strength-label", Static)
                strength_widget.update("Strength: Very Weak")
                bar_widget = self.query_one("#strength-bar", Static)
                bar_widget.update("")
                self.strength_score = 0
                self.strength_label = "Very Weak"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input."""
        # In "set" mode, pressing Enter in first field should focus confirm field
        if self.mode == "set" and event.input.id == "passphrase-input":
            try:
                confirm_widget = self.query_one("#passphrase-confirm", Input)
                confirm_widget.focus()
            except Exception:  # nosec B110
                pass  # Confirm field might not exist in unlock mode
        elif event.input.id == "passphrase-confirm" or (self.mode == "unlock" and event.value):
            # Trigger validation and dismiss - same logic as unlock button
            input_widget = self.query_one("#passphrase-input", Input)
            passphrase = input_widget.value

            if not passphrase:
                self.app.notify("Passphrase cannot be empty", severity="error")
                return

            if self.mode == "set":
                try:
                    confirm_widget = self.query_one("#passphrase-confirm", Input)
                    confirm = confirm_widget.value

                    if passphrase != confirm:
                        self.app.notify("Passphrases do not match", severity="error")
                        return

                    if self.strength_score < 2:
                        self.app.notify(
                            f"Passphrase too weak ({self.strength_label}). Minimum: Fair",
                            severity="error",
                        )
                        return
                except Exception:  # nosec B110
                    pass  # Confirm field might not exist

            self.dismiss(passphrase)

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            # Check if passphrase input has focus (user is typing)
            try:
                input_field = self.query_one("#passphrase-input", Input)
                if input_field.has_focus:
                    # User is typing, let 'q' be typed normally
                    return
            except Exception:  # nosec B110
                pass

            # Input doesn't have focus, trigger app quit confirmation
            event.stop()
            self.app.action_quit()


class GenericConfirmationScreen(ModalScreen[bool]):
    """Generic confirmation dialog."""

    CSS = """
    /* Cyberpunk Generic Confirmation Dialog */
    GenericConfirmationScreen {
        align: center middle;
        background: #00000099;
    }

    #confirm-dialog {
        width: 80%;
        max-width: 60;
        height: auto;
        border: heavy #ffff00;
        background: #0a0a0a;
        padding: 2;
    }

    #confirm-title {
        text-align: center;
        text-style: bold;
        color: #ffff00;
        margin-bottom: 1;
    }

    #confirm-message {
        text-align: center;
        color: #00ffff;
        margin-bottom: 2;
    }

    #button-row {
        width: 100%;
        height: auto;
        min-height: 3;
        align: center middle;
        margin-top: 1;
    }

    .confirm-button {
        margin: 0 1;
        min-width: 16;
    }

    /* Cyberpunk Button Styles */
    Button {
        border: solid #00ffff;
        background: #000000;
    }

    Button:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }

    Button.-warning {
        border: solid #ffff00;
    }

    Button.-warning:hover {
        background: #ffff0020;
        border: heavy #ffff00;
    }

    Button.-default {
        border: solid #00ffff;
    }

    Button.-default:hover {
        background: #00ffff20;
        border: heavy #00ffff;
    }
    """

    def __init__(self, title: str, message: str):
        """Initialize confirmation dialog."""
        super().__init__()
        self.title_text = title
        self.message_text = message

    def compose(self) -> ComposeResult:
        """Compose confirmation dialog."""
        with Container(id="confirm-dialog"):
            yield Label(self.title_text, id="confirm-title")
            yield Label(self.message_text, id="confirm-message")
            with Horizontal(id="button-row"):
                yield Button(
                    "Confirm", variant="warning", id="btn-confirm", classes="confirm-button"
                )
                yield Button("Cancel", variant="default", id="btn-cancel", classes="confirm-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class PasswordHistoryModal(ModalScreen[None]):
    """Modal screen for viewing full password history."""

    CSS = """
    /* Cyberpunk Password History Modal */
    PasswordHistoryModal {
        align: center middle;
        background: #00000099;
    }

    #history-dialog {
        width: 90%;
        max-width: 80;
        height: auto;
        min-height: 30;
        border: heavy #ff00ff;
        background: #0a0a0a;
        padding: 2;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
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
                # Don't show current password for security
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
                yield Button(
                    "Clear History", variant="error", id="btn-clear", classes="history-button"
                )
                yield Button("Close", variant="primary", id="btn-close", classes="history-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-close":
            self.dismiss(None)
        elif event.button.id == "btn-clear":
            self.run_worker(self._async_clear_history())

    async def _async_clear_history(self) -> None:
        """Clear password history with confirmation."""
        # Show confirmation dialog
        confirm = await self.app.push_screen_wait(
            GenericConfirmationScreen(
                "Clear Password History?",
                f"This will permanently delete all {len(self.entry.get_password_history())} "
                "previous passwords for this entry. This action cannot be undone.",
            )
        )

        if confirm:
            # Clear the password history
            self.entry.password_history.clear()

            # Notify user
            self.app.notify("Password history cleared successfully", severity="information")

            # Refresh the display
            self.refresh(recompose=True)

    def action_close(self) -> None:
        """Close dialog."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            event.stop()
            self.app.action_quit()


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
        self.password_hide_timer = None

    def compose(self) -> ComposeResult:
        """Compose detail panel."""
        yield ScrollableContainer(
            Label("No entry selected", id="no-entry-msg"),
            classes="detail-content",
        )

    def show_entry(self, entry: VaultEntry) -> None:
        """Display entry details."""
        # Stop any existing password hide timer
        if self.password_hide_timer:
            self.password_hide_timer.stop()
            self.password_hide_timer = None

        self.current_entry = entry
        self.password_visible = False
        self._update_display()
        self._start_totp_refresh()

    def toggle_password_visibility(self) -> None:
        """Toggle password visibility with auto-hide timer."""
        if self.current_entry:
            self.password_visible = not self.password_visible
            self._update_display()

            # Cancel existing timer if any
            if self.password_hide_timer:
                self.password_hide_timer.stop()
                self.password_hide_timer = None

            # Start auto-hide timer if password is now visible (10 seconds)
            if self.password_visible:
                self.password_hide_timer = self.set_timer(10.0, self._auto_hide_password)

    def _auto_hide_password(self) -> None:
        """Auto-hide password after timer expires."""
        if self.password_visible:
            self.password_visible = False
            self._update_display()
            self.password_hide_timer = None

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

        # Stop password hide timer
        if self.password_hide_timer:
            self.password_hide_timer.stop()
            self.password_hide_timer = None

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
        width: 90%;
        max-width: 80;
        height: 44;
        border: heavy #00ffff;
        background: #0a0a0a;
        padding: 2;
        overflow-y: auto;  /* Enable internal scrolling when content exceeds available space */
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
        height: auto;
    }

    .field-label {
        color: #888888;
        margin-bottom: 0;
        height: 1;
    }

    Input {
        width: 100%;
        height: auto;
        min-height: 3;
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

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            # Check if any input field has focus (user is typing)
            try:
                input_ids = [
                    "input-key",
                    "input-password",
                    "input-username",
                    "input-url",
                    "input-notes",
                    "input-tags",
                ]
                for input_id in input_ids:
                    try:
                        input_field = self.query_one(f"#{input_id}", Input)
                        if input_field.has_focus:
                            # User is typing, let 'q' be typed normally
                            return
                    except Exception:  # nosec B110
                        pass
            except Exception:  # nosec B110
                pass

            # No input has focus, trigger app quit confirmation
            event.stop()
            self.app.action_quit()


class DeleteConfirmationScreen(ModalScreen[bool]):
    """Modal screen for confirming entry deletion."""

    CSS = """
    /* Cyberpunk Delete Confirmation */
    DeleteConfirmationScreen {
        align: center middle;
        background: #00000099;
    }

    #confirm-dialog {
        width: 80%;
        max-width: 60;
        height: auto;
        min-height: 12;
        border: heavy #ff0000;
        background: #0a0a0a;
        padding: 1;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
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

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(False)

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            event.stop()
            self.app.action_quit()


class VaultOverwriteWarningScreen(ModalScreen[bool]):
    """Modal screen for warning about overwriting existing vault."""

    CSS = """
    /* Cyberpunk Vault Overwrite Warning */
    VaultOverwriteWarningScreen {
        align: center middle;
        background: #00000099;
    }

    #warning-dialog {
        width: 80%;
        max-width: 70;
        height: auto;
        min-height: 16;
        border: heavy #ff8800;
        background: #0a0a0a;
        padding: 1;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
    }

    #warning-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #ff8800;
        margin-bottom: 0;
        border-bottom: solid #ff8800;
        padding-bottom: 0;
    }

    #warning-message {
        width: 100%;
        text-align: center;
        color: #00ffff;
        margin: 1 0 0 0;
    }

    #warning-details {
        width: 100%;
        text-align: center;
        color: #ff0080;
        margin: 0 0 0 0;
        text-style: bold;
    }

    #warning-consequence {
        width: 100%;
        text-align: center;
        color: #ffff00;
        margin: 0 0 0 0;
        text-style: italic;
    }

    #button-row {
        height: auto;
        min-height: 3;
        align: center middle;
        margin: 1 0 0 0;
    }

    .warning-button {
        margin: 0 1;
        min-width: 16;
        height: 3;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose warning dialog."""
        with Container(id="warning-dialog"):
            yield Label("⚠️  Vault Already Exists", id="warning-title")
            yield Label("This image already contains a vault!", id="warning-message")
            yield Label(
                "Creating a new vault will OVERWRITE the existing data.",
                id="warning-details",
            )
            yield Label(
                "This action cannot be undone. ALL existing entries will be lost.",
                id="warning-consequence",
            )

            with Horizontal(id="button-row"):
                yield Button(
                    "Overwrite",
                    variant="error",
                    id="btn-overwrite",
                    classes="warning-button",
                )
                yield Button(
                    "Cancel",
                    variant="default",
                    id="btn-cancel",
                    classes="warning-button",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-overwrite":
            self.dismiss(True)  # User confirms overwrite
        elif event.button.id == "btn-cancel":
            self.dismiss(False)  # User cancels

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(False)

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            event.stop()
            self.app.action_quit()


class UnsavedChangesScreen(ModalScreen[str]):
    """Modal screen for unsaved changes warning."""

    CSS = """
    /* Cyberpunk Unsaved Changes Warning */
    UnsavedChangesScreen {
        align: center middle;
        background: #00000099;
    }

    #unsaved-dialog {
        width: 80%;
        max-width: 60;
        height: auto;
        border: heavy #ff0080;
        background: #0a0a0a;
        padding: 1 1 0 1;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
    }

    #unsaved-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #ff0080;
        margin: 0 -2 0 -2;
        border-bottom: solid #ff0080;
        padding: 0 0 0 0;
    }

    #unsaved-message {
        text-align: center;
        color: #ffff00;
        margin: 1 0 0 0;
    }

    #unsaved-warning {
        text-align: center;
        color: #ff0080;
        text-style: bold;
        margin: 0 0 0 0;
    }

    #button-row {
        width: 100%;
        height: auto;
        align: center middle;
        margin: 1 0 1 0;
    }

    .unsaved-button {
        margin: 0 1;
        min-width: 16;
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

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss("cancel")

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            event.stop()
            self.app.action_quit()


class PasswordGeneratorScreen(ModalScreen[Optional[str]]):
    """Modal screen for generating secure passwords."""

    CSS = """
    /* Cyberpunk Password Generator */
    PasswordGeneratorScreen {
        align: center middle;
        background: #00000099;
    }

    #generator-dialog {
        width: 85%;
        max-width: 70;
        height: auto;
        max-height: 90%;
        border: heavy #00ffff;
        background: #0a0a0a;
        padding: 1;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
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

    def action_cancel(self) -> None:
        """Cancel and close dialog."""
        self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key press - allow 'q' to trigger quit confirmation."""
        if event.key == "q":
            event.stop()
            self.app.action_quit()
