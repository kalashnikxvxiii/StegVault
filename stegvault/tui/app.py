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

from .widgets import FileSelectScreen, PassphraseInputScreen
from .screens import VaultScreen


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

    async def action_open_vault(self) -> None:
        """Open existing vault."""
        # Step 1: Select vault image file
        file_path = await self.push_screen_wait(FileSelectScreen("Select Vault Image"))

        if not file_path:
            return  # User cancelled

        # Step 2: Get passphrase
        passphrase = await self.push_screen_wait(
            PassphraseInputScreen(f"Unlock Vault: {file_path}")
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

    async def action_new_vault(self) -> None:
        """Create new vault."""
        # Step 1: Select output image file
        file_path = await self.push_screen_wait(
            FileSelectScreen("Select Output Image for New Vault")
        )

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
        self.notify("Help screen - Coming in Phase 3!", severity="information")

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
