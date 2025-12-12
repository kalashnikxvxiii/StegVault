"""
Main TUI application for StegVault.

Provides a full-featured terminal interface for vault management.
"""

from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding

from stegvault.app.controllers import VaultController, CryptoController
from stegvault.vault import Vault

from .widgets import FileSelectScreen, PassphraseInputScreen, HelpScreen
from .screens import VaultScreen


class StegVaultTUI(App):
    """StegVault Terminal User Interface application."""

    CSS = """
    /* Cyberpunk Theme - Pure black background with neon accents */
    Screen {
        background: #000000;
    }

    Header {
        background: #0a0a0a;
        color: #00ffff;
        text-style: bold;
        border-bottom: heavy #ff00ff;
        dock: top;
    }

    Footer {
        background: #0a0a0a;
        color: #00ffff;
        border-top: heavy #ff00ff;
        dock: bottom;
        height: auto;
        padding: 0;
        width: 100%;
    }

    Footer .footer--key {
        color: #ffff00;
        text-style: bold;
    }

    Footer .footer--description {
        color: #00ffff;
        text-style: none;
    }

    Footer > .footer--highlight {
        background: transparent;
    }

    Footer > .footer--highlight-key {
        background: transparent;
    }

    /* Welcome Screen - Fullscreen responsive layout */
    #welcome-container {
        width: 100%;
        height: 100%;
        background: #000000;
        align: center middle;
    }

    #content-box {
        width: 90%;
        height: 85%;
        border: double #00ffff;
        background: #0a0a0a;
        padding: 3 6;
        align: center middle;
    }

    #welcome-text {
        content-align: center middle;
        text-style: bold;
        color: #00ffff;
        margin-top: 1;
    }

    #ascii-art {
        content-align: center middle;
        color: #ff00ff;
        text-style: bold;
    }

    #subtitle {
        content-align: center middle;
        color: #ffff00;
        margin-top: 2;
        text-style: italic;
    }

    #tagline {
        content-align: center middle;
        color: #666;
        margin-top: 1;
        text-style: dim italic;
    }

    /* Buttons - Neon glow effect with contained background */
    .action-button {
        margin: 1;
        min-width: 26;
        height: 3;
        padding: 0 1;
        border: solid #00ffff;
        background: #000000;
        color: #00ffff;
        text-style: bold;
    }

    .action-button:hover {
        background: #000000;
        border: heavy #00ffff;
        color: #ffffff;
    }

    .action-button:focus {
        background: #000000;
        border: double #00ffff;
    }

    Button.danger {
        border: solid #ff0080;
        background: #000000;
        color: #ff0080;
        padding: 0 1;
    }

    Button.danger:hover {
        background: #000000;
        border: heavy #ff0080;
    }

    Button.success {
        border: solid #00ff9f;
        background: #000000;
        color: #00ff9f;
        padding: 0 1;
    }

    Button.success:hover {
        background: #000000;
        border: heavy #00ff9f;
    }

    Button.success:focus {
        background: #000000;
        border: double #00ff9f;
    }

    Button.warning {
        border: solid #ffff00;
        background: #000000;
        color: #ffff00;
        padding: 0 1;
    }

    Button.warning:hover {
        background: #000000;
        border: heavy #ffff00;
    }

    Button.warning:focus {
        background: #000000;
        border: double #ffff00;
    }

    Button.info {
        border: solid #ff0080;
        background: #000000;
        color: #ff0080;
        padding: 0 1;
    }

    Button.info:hover {
        background: #000000;
        border: heavy #ff0080;
    }

    Button.info:focus {
        background: #000000;
        border: double #ff0080;
    }

    #button-container {
        align: center middle;
        height: auto;
        margin-top: 2;
    }

    #button-container > Button {
        margin: 0 1;
    }

    #button-container > Button:focus {
        background: #00ffff30;
        border: double #00ffff;
    }

    /* Notifications - Cyberpunk style */
    .notification {
        border: heavy;
        background: #1a1a2e;
    }

    .notification.information {
        border: heavy #00ffff;
        color: #00ffff;
    }

    .notification.error {
        border: heavy #ff0080;
        color: #ff0080;
    }

    .notification.warning {
        border: heavy #ffff00;
        color: #ffff00;
    }

    .notification.success {
        border: heavy #00ff9f;
        color: #00ff9f;
    }
    """

    TITLE = "⚡⚡ STEGVAULT ⚡⚡ Neural Security Terminal"
    SUB_TITLE = "◈◈ Privacy is a luxury - Your digital safe haven ◈◈"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("o", "open_vault", "Open Vault"),
        Binding("n", "new_vault", "New Vault"),
        Binding("h", "show_help", "Help"),
    ]

    def __init__(self):
        """Initialize TUI application."""
        super().__init__()
        self.vault_controller = VaultController()
        self.crypto_controller = CryptoController()
        self.current_vault: Vault | None = None
        self.current_image_path: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header(show_clock=True)
        with Container(id="welcome-container"):
            with Vertical(id="content-box"):
                yield Static(
                    "███████╗████████╗███████╗ ██████╗ ██╗   ██╗ █████╗ ██╗   ██╗██╗  ████████╗\n"
                    "██╔════╝╚══██╔══╝██╔════╝██╔════╝ ██║   ██║██╔══██╗██║   ██║██║  ╚══██╔══╝\n"
                    "███████╗   ██║   █████╗  ██║  ███╗██║   ██║███████║██║   ██║██║     ██║   \n"
                    "╚════██║   ██║   ██╔══╝  ██║   ██║╚██╗ ██╔╝██╔══██║██║   ██║██║     ██║   \n"
                    "███████║   ██║   ███████╗╚██████╔╝ ╚████╔╝ ██║  ██║╚██████╔╝███████╗██║   \n"
                    "╚══════╝   ╚═╝   ╚══════╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝   ",
                    id="ascii-art",
                )
                yield Static(
                    ">> NEURAL SECURITY TERMINAL v0.7.2 <<",
                    id="welcome-text",
                )
                yield Static(
                    "⚡⚡⚡ Steganography-based password vault in a surveillance state ⚡⚡⚡",
                    id="subtitle",
                )
                yield Static(
                    "[ Hide in plain sight. Encrypt everything. Trust no one. ]",
                    id="tagline",
                )
                with Horizontal(id="button-container"):
                    yield Button(
                        "⚡⚡ UNLOCK VAULT ⚡⚡",
                        id="btn-open",
                        classes="action-button success",
                    )
                    yield Button(
                        "✨✨ NEW VAULT ✨✨", id="btn-new", classes="action-button warning"
                    )
                    yield Button("? HELP ?", id="btn-help", classes="action-button info")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted. Set focus on first button."""
        # Focus on the first button for keyboard navigation
        first_button = self.query_one("#btn-open", Button)
        first_button.focus()

    def action_quit(self) -> None:
        """Quit the application."""
        # Check if PasswordGeneratorScreen is open - if so, block quit
        try:
            from .widgets import PasswordGeneratorScreen

            if isinstance(self.screen, PasswordGeneratorScreen):
                self.notify("Press ESC to close this modal first", severity="warning", timeout=2)
                return
        except Exception:
            pass
        self.exit()

    def action_open_vault(self) -> None:
        """Open existing vault (wrapper for async)."""
        self.run_worker(self._async_open_vault())

    async def _async_open_vault(self) -> None:
        """Open existing vault."""
        # Step 1: Select vault image file
        file_path = await self.push_screen_wait(
            FileSelectScreen("UNLOCK VAULT - Select Vault Image")
        )

        if not file_path:
            return  # User cancelled

        # Step 2: Get passphrase
        # Show only filename or last 35 chars of path for better readability
        from pathlib import Path

        display_path = Path(file_path).name
        if len(display_path) > 35:
            display_path = "..." + display_path[-32:]

        passphrase = await self.push_screen_wait(
            PassphraseInputScreen(f"Unlock Vault: {display_path}")
        )

        if not passphrase:
            return  # User cancelled

        # Step 3: Load vault
        self.notify("Loading vault...", severity="information")

        try:
            result = self.vault_controller.load_vault(file_path, passphrase)

            if not result.success:
                self.notify(f"Failed to load vault: {result.error}", severity="error")
                return

            if not result.vault:
                self.notify("Vault loaded but contains no data", severity="warning")
                return

            # Success! Switch to vault screen
            self.current_vault = result.vault
            self.current_image_path = file_path

            vault_screen = VaultScreen(result.vault, file_path, passphrase, self.vault_controller)
            self.push_screen(vault_screen)

        except Exception as e:
            self.notify(f"Error loading vault: {e}", severity="error")

    def action_new_vault(self) -> None:
        """Create new vault (wrapper for async)."""
        self.run_worker(self._async_new_vault())

    async def _async_new_vault(self) -> None:
        """Create new vault."""
        # TODO: Future improvements for New Vault workflow (user feedback):
        # Option A: Add confirmation dialog "⚠️ This will modify the original image. Continue?"
        # Option B: Add "Save As" field in workflow to specify output path
        # Option C: Automatically create backup copy (e.g., image.png.orig)
        # Current behavior: Directly modifies the selected image file

        # Step 1: Select output image file
        file_path = await self.push_screen_wait(FileSelectScreen("NEW VAULT - Select Output Image"))

        if not file_path:
            return  # User cancelled

        # Step 2: Get passphrase for new vault
        passphrase = await self.push_screen_wait(
            PassphraseInputScreen("Set Passphrase for New Vault")
        )

        if not passphrase:
            return  # User cancelled

        # Step 3: Get first entry data
        from .widgets import EntryFormScreen

        form_data = await self.push_screen_wait(
            EntryFormScreen(mode="add", title="Add First Entry to New Vault")
        )

        if not form_data:
            return  # User cancelled

        # Step 4: Create vault with first entry
        self.notify("Creating new vault...", severity="information")

        try:
            vault, success, error = self.vault_controller.create_new_vault(
                key=form_data["key"],
                password=form_data["password"],
                username=form_data.get("username"),
                url=form_data.get("url"),
                notes=form_data.get("notes"),
                tags=form_data.get("tags"),
            )

            if not success:
                self.notify(f"Failed to create vault: {error}", severity="error")
                return

            # Step 5: Save vault to image
            result = self.vault_controller.save_vault(vault, file_path, passphrase)

            if not result.success:
                self.notify(f"Failed to save vault: {result.error}", severity="error")
                return

            # Step 6: Success! Open the new vault
            self.current_vault = vault
            self.current_image_path = file_path

            vault_screen = VaultScreen(vault, file_path, passphrase, self.vault_controller)
            self.push_screen(vault_screen)

            self.notify(
                f"Vault created successfully with entry '{form_data['key']}'!",
                severity="information",
            )

        except Exception as e:
            self.notify(f"Error creating vault: {e}", severity="error")

    def action_show_help(self) -> None:
        """Show help screen."""
        self.push_screen(HelpScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "btn-open":
            self.action_open_vault()
        elif button_id == "btn-new":
            self.action_new_vault()
        elif button_id == "btn-help":
            self.action_show_help()


def run_tui() -> None:
    """Run the StegVault TUI application."""
    app = StegVaultTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
