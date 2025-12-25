"""
Main TUI application for StegVault.

Provides a full-featured terminal interface for vault management.
"""

from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.events import Click
from textual.notifications import SeverityLevel
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button
from textual.widgets._toast import ToastRack, Toast
from textual.binding import Binding

from stegvault import __version__
from stegvault.app.controllers import VaultController, CryptoController
from stegvault.vault import Vault
from stegvault.utils.payload import MAGIC_HEADER, MAGIC_SIZE
from stegvault import stego

from .widgets import (
    FileSelectScreen,
    PassphraseInputScreen,
    HelpScreen,
    QuitConfirmationScreen,
    UnsavedChangesScreen,
    VaultOverwriteWarningScreen,
    SettingsScreen,
    ChangelogViewerScreen,
    TOTPAuthScreen,
)
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
        min-height: 1;
        max-height: 10;
        padding: 0 1;
        width: 100%;
        overflow-x: auto;
        overflow-y: auto;
        scrollbar-gutter: stable;  /* Reserve space for scrollbar to prevent layout shifts */
        scrollbar-size-vertical: 1;  /* Explicit scrollbar width */
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
        overflow-y: auto;  /* Enable vertical scrolling on resize */
        scrollbar-gutter: stable;  /* Reserve space for scrollbar to prevent layout shifts */
        scrollbar-size-vertical: 1;  /* Explicit scrollbar width */
    }

    #content-box {
        width: 90%;
        height: 90%;
        border: double #00ffff;
        background: #0a0a0a;
        padding: 3 2 2 6;  /* top=3, right=2, bottom=2, left=6 */
        align: center middle;
        overflow-y: auto;  /* Enable vertical scrolling on resize */
        scrollbar-gutter: stable;  /* Reserve space for scrollbar to prevent layout shifts */
        scrollbar-size-vertical: 1;  /* Explicit scrollbar width */
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

    /* Settings container - docked to bottom */
    #settings-container {
        dock: bottom;
        width: 100%;
        height: 3;
        align: right middle;
        margin: 0;
        padding: 0;
    }

    /* Settings button - invisible with bold text */
    #btn-settings {
        width: 5;
        height: 3;
        min-width: 5;
        max-width: 5;
        margin: 0;
        padding: 0;
        text-align: center;
        content-align: center middle;
        border: none;
        background: transparent;
        color: #ff0080;
        text-style: bold;
    }

    #btn-settings:hover {
        background: #0a0a0a50;
        color: #00ffff;
        text-style: bold;
    }

    #btn-settings:focus {
        background: transparent;
        color: #00ffff;
        text-style: bold;
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

    /* Update Notification Banner - Cyberpunk Style */
    #update-banner {
        width: 100%;
        height: auto;
        background: #0a0a00;
        border-bottom: heavy #ffff00;
        color: #ffff00;
        padding: 0 2;
        text-align: center;
        text-style: bold;
        dock: top;
        display: none;
    }

    #update-banner Static {
        color: #ffff00;
        text-style: bold;
    }
    """

    TITLE = "⚡⚡ STEGVAULT ⚡⚡ Neural Security Terminal"
    SUB_TITLE = "◈◈ Privacy is a luxury - Your digital safe haven ◈◈"

    BINDINGS = [
        Binding("q", "quit", "Quit"),  # Removed priority=True to allow modals to block quit
        Binding("o", "open_vault", "Open Vault"),
        Binding("n", "new_vault", "New Vault"),
        Binding("h", "show_help", "Help"),
        Binding("s", "show_settings", "Settings"),
    ]

    def __init__(self) -> None:
        """Initialize TUI application."""
        super().__init__()
        self.vault_controller = VaultController()
        self.crypto_controller = CryptoController()
        self.current_vault: Optional[Vault] = None
        self.current_image_path: Optional[str] = None

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header(show_clock=True)
        # Update notification banner (hidden by default)
        yield Static("", id="update-banner")
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
                    f">> NEURAL SECURITY TERMINAL v{__version__} <<",
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
                # Settings container - bottom-right corner
                with Horizontal(id="settings-container"):
                    yield Static("\n━━━\n━━━", id="btn-settings")
        yield Footer()

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: SeverityLevel = "information",
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Override notify to limit notifications to 3 max (FIFO).

        Args:
            message: Notification message
            title: Optional notification title
            severity: Notification severity level
            timeout: Notification timeout in seconds (None uses default)
            **kwargs: Additional keyword arguments passed to parent notify
        """
        # Call parent first to create the notification
        super().notify(message, title=title, severity=severity, timeout=timeout, **kwargs)

        # Then limit to 3 by removing oldest
        try:
            # Access the ToastRack from the screen
            toast_rack = self.screen.query_one(ToastRack)

            # Get all current toasts
            toasts = list(toast_rack.query(Toast))

            # Remove oldest if we have more than 3
            while len(toasts) > 3:
                oldest_toast = toasts.pop(0)
                oldest_toast.remove()

        except Exception:  # nosec B110
            # Fail silently if ToastRack not available
            pass

    def on_mount(self) -> None:
        """Called when app is mounted. Set focus on first button and check for updates."""
        # Fix cache version if it doesn't match running version
        try:
            from stegvault.utils.updater import update_cache_version

            update_cache_version()
        except Exception:  # nosec B110
            pass

        # Check for TOTP authentication requirement
        self.run_worker(self._check_totp_auth(), exclusive=True)

        # Focus on the first button for keyboard navigation
        first_button = self.query_one("#btn-open", Button)
        first_button.focus()

        # Check for updates in background (respects config settings)
        self.run_worker(self._check_for_updates_async(), exclusive=False)

    async def _check_totp_auth(self) -> None:
        """Check if TOTP authentication is required and verify."""
        try:
            from stegvault.config.core import load_config
            from .widgets import TOTPAuthScreen

            # Load config to check if TOTP is enabled
            try:
                config = load_config()
                if not config.totp.enabled or not config.totp.secret:
                    return  # TOTP not enabled or not configured
            except Exception:
                # If config fails to load, continue without TOTP
                return

            # Show TOTP authentication screen
            authenticated = await self.push_screen_wait(
                TOTPAuthScreen(
                    totp_secret=config.totp.secret,
                    backup_code=config.totp.backup_code,
                    max_attempts=3,
                )
            )

            if not authenticated:
                # Authentication failed - exit app
                self.exit()

        except Exception:  # nosec B110
            # If TOTP check fails, continue without authentication
            # (graceful degradation - don't lock users out due to errors)
            pass

    async def _check_for_updates_async(self) -> None:
        """Check for updates in background and show banner if available."""
        try:
            from stegvault.config.core import load_config
            from stegvault.utils.updater import (
                check_for_updates,
                get_cached_check,
                cache_check_result,
            )

            # Load config to check if auto_check is enabled
            try:
                config = load_config()
                if not config.updates.auto_check:
                    return  # Auto-check disabled
            except Exception:
                # If config fails to load, don't check for updates
                return

            # Check cache first
            cached = get_cached_check(config.updates.check_interval_hours)
            if cached:
                update_available = cached["update_available"]
                latest_version = cached["latest_version"]
            else:
                # Perform fresh check
                update_available, latest_version, error = check_for_updates()
                cache_check_result(update_available, latest_version, error)

            # Show banner if update is available
            if update_available and latest_version:
                banner = self.query_one("#update-banner", Static)
                banner.update(
                    f"⚡ UPDATE AVAILABLE: v{latest_version} ⚡ "
                    f"Run 'stegvault update' to upgrade ⚡"
                )
                banner.display = True

        except Exception:  # nosec B110
            # Silently fail if update check fails (don't interrupt user experience)
            pass

    def action_quit(self) -> None:  # type: ignore[override]
        """Quit the application (wrapper for async)."""
        self.run_worker(self._async_quit())

    async def _async_quit(self) -> None:
        """Show quit confirmation and exit if confirmed."""
        # Show confirmation dialog
        result = await self.push_screen_wait(QuitConfirmationScreen())

        if result:  # User confirmed quit
            # Close all modal screens in reverse order (from last to first)
            # QuitConfirmationScreen is already dismissed at this point
            while len(self.screen_stack) > 1:
                self.pop_screen()

            # Schedule exit for next event loop tick to allow final UI cleanup
            # This prevents deadlock when exiting from within a worker
            self.call_later(self.exit)

    def action_open_vault(self) -> None:
        """Open existing vault (wrapper for async)."""
        self.run_worker(self._async_open_vault())

    async def _async_open_vault(self) -> None:
        """Open existing vault."""
        from pathlib import Path

        while True:
            # Step 1: Select vault image file
            file_path = await self.push_screen_wait(
                FileSelectScreen("UNLOCK VAULT - Select Vault Image")
            )

            if not file_path:
                return  # User cancelled from file selection

            # Step 2: Get passphrase
            # Show only filename or last 35 chars of path for better readability
            display_path = Path(file_path).name
            if len(display_path) > 35:
                display_path = "..." + display_path[-32:]

            passphrase = await self.push_screen_wait(
                PassphraseInputScreen(f"Unlock Vault: {display_path}")
            )

            if not passphrase:
                # User cancelled from passphrase - go back to file selection
                continue

            # Step 3: Load vault
            self.notify("Loading vault...", severity="information")

            try:
                result = self.vault_controller.load_vault(file_path, passphrase)

                if not result.success:
                    self.notify(f"Failed to load vault: {result.error}", severity="error")
                    # Loop back to file selection
                    continue

                if not result.vault:
                    self.notify("Vault loaded but contains no data", severity="warning")
                    return

                # Success! Switch to vault screen
                self.current_vault = result.vault
                self.current_image_path = file_path

                vault_screen = VaultScreen(
                    result.vault, file_path, passphrase, self.vault_controller
                )
                self.push_screen(vault_screen)
                return  # Exit loop on success

            except Exception as e:
                self.notify(f"Error loading vault: {e}", severity="error")
                # Loop back to file selection
                continue

    def _check_vault_exists(self, image_path: str) -> bool:
        """Check if an image already contains a vault by reading magic header.

        Args:
            image_path: Path to image file

        Returns:
            True if vault exists, False otherwise
        """
        try:
            # Try to extract first few bytes to check for magic header
            # We only need MAGIC_SIZE bytes to check
            test_payload = stego.extract_payload(image_path, MAGIC_SIZE)

            # Check if magic header matches
            return test_payload[:MAGIC_SIZE] == MAGIC_HEADER
        except Exception:
            # If extraction fails, assume no vault exists
            return False

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

        from .widgets import EntryFormScreen

        while True:
            # Step 1: Select output image file
            file_path = await self.push_screen_wait(
                FileSelectScreen("NEW VAULT - Select Output Image")
            )

            if not file_path:
                return  # User cancelled from file selection

            # Step 1.5: Check if vault already exists and warn user
            if self._check_vault_exists(file_path):
                confirm_overwrite = await self.push_screen_wait(VaultOverwriteWarningScreen())

                if not confirm_overwrite:
                    # User cancelled - go back to file selection
                    self.notify("Vault creation cancelled.", severity="information")
                    continue

            # Step 2: Get passphrase for new vault
            passphrase = await self.push_screen_wait(
                PassphraseInputScreen("Set Passphrase for New Vault", mode="set")
            )

            if not passphrase:
                # User cancelled from passphrase - go back to file selection
                continue

            # Step 3: Get first entry data
            form_data = await self.push_screen_wait(
                EntryFormScreen(mode="add", title="Add First Entry to New Vault")
            )

            if not form_data:
                # User cancelled from entry form - go back to file selection
                continue

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
                    # Loop back to file selection
                    continue

                # Step 5: Save vault to image
                result = self.vault_controller.save_vault(vault, file_path, passphrase)

                if not result.success:
                    self.notify(f"Failed to save vault: {result.error}", severity="error")
                    # Loop back to file selection
                    continue

                # Step 6: Success! Open the new vault
                self.current_vault = vault
                self.current_image_path = file_path

                vault_screen = VaultScreen(vault, file_path, passphrase, self.vault_controller)
                self.push_screen(vault_screen)

                self.notify(
                    f"Vault created successfully with entry '{form_data['key']}'!",
                    severity="information",
                )
                return  # Exit loop on success

            except Exception as e:
                self.notify(f"Error creating vault: {e}", severity="error")
                # Loop back to file selection
                continue

    def action_show_help(self) -> None:
        """Show help screen."""
        self.push_screen(HelpScreen())

    def action_show_settings(self) -> None:
        """Show settings screen."""
        self.push_screen(SettingsScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "btn-open":
            self.action_open_vault()
        elif button_id == "btn-new":
            self.action_new_vault()
        elif button_id == "btn-help":
            self.action_show_help()

    def on_click(self, event: Click) -> None:
        """Handle click events on widgets."""
        # Check if click is on settings Static widget
        if getattr(event.widget, "id", None) == "btn-settings":
            self.action_show_settings()


def run_tui() -> None:
    """Run the StegVault TUI application."""
    app = StegVaultTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
