"""
Main TUI application for StegVault.

Provides a full-featured terminal interface for vault management.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding

from stegvault.app.controllers import VaultController, CryptoController
from stegvault.vault import Vault


class StegVaultTUI(App):
    """StegVault Terminal User Interface application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #welcome-container {
        width: 60;
        height: 15;
        border: solid $primary;
        background: $panel;
        padding: 2;
    }

    #welcome-text {
        content-align: center middle;
        text-style: bold;
    }

    #subtitle {
        content-align: center middle;
        color: $text-muted;
        margin-top: 1;
    }

    .action-button {
        margin: 1;
        width: 30;
    }

    #button-container {
        align: center middle;
        height: auto;
    }
    """

    TITLE = "StegVault TUI"
    SUB_TITLE = "Secure Password Manager with Steganography"

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
        yield Header()
        yield Container(
            Vertical(
                Static(
                    "🔐 Welcome to StegVault TUI",
                    id="welcome-text",
                ),
                Static(
                    "Secure password management using steganography",
                    id="subtitle",
                ),
                Horizontal(
                    Button("Open Vault", variant="primary", id="btn-open"),
                    Button("New Vault", variant="success", id="btn-new"),
                    Button("Help", variant="default", id="btn-help"),
                    id="button-container",
                ),
                id="welcome-container",
            ),
        )
        yield Footer()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_open_vault(self) -> None:
        """Open existing vault."""
        self.notify("Open Vault feature - Coming soon!", severity="information")

    def action_new_vault(self) -> None:
        """Create new vault."""
        self.notify("New Vault feature - Coming soon!", severity="information")

    def action_show_help(self) -> None:
        """Show help screen."""
        self.notify("Help screen - Coming soon!", severity="information")

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
