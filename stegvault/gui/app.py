"""
Main application and main window for StegVault Desktop GUI.

Uses the same Application Layer (VaultController, CryptoController, Vault)
as CLI and TUI.
"""

from typing import Optional

from stegvault import __version__
from stegvault.app.controllers.vault_controller import VaultController, VaultLoadResult
from stegvault.vault.operations import list_entries, get_entry

try:
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMenu,
        QMenuBar,
        QMessageBox,
        QHBoxLayout,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except ImportError as e:
    raise ImportError(
        "PySide6 is required for the GUI. Install with: pip install stegvault[gui]"
    ) from e


class MainWindow(QMainWindow):
    """
    Main application window.

    First iteration focuses on a simple, read-only vault viewer:
    - File → Open Vault…
    - List of entry keys on the left
    - Basic entry details on the right (no password editing yet)
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StegVault")
        self.setMinimumSize(800, 500)

        # Core state
        self._vault_controller = VaultController()
        self._current_vault = None  # type: ignore[assignment]
        self._current_image_path: Optional[str] = None

        self._setup_ui()

    # UI setup -------------------------------------------------------------
    def _setup_ui(self) -> None:
        self._create_menu_bar()
        self._create_central_layout()

    def _create_menu_bar(self) -> None:
        menubar: QMenuBar = self.menuBar()

        file_menu: QMenu = menubar.addMenu("&File")

        open_action = file_menu.addAction("Open Vault…")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_vault)  # type: ignore[arg-type]

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)  # type: ignore[arg-type]

    def _create_central_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # Left: entry list
        self._entry_list = QListWidget()
        self._entry_list.currentItemChanged.connect(self._on_entry_selected)  # type: ignore[arg-type]
        layout.addWidget(self._entry_list, stretch=1)

        # Right: entry details
        detail_container = QWidget()
        detail_layout = QVBoxLayout(detail_container)

        self._detail_label = QLabel(
            f"StegVault GUI v{__version__}\n\n"
            "Use File → Open Vault… to load an image-based vault."
        )
        self._detail_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._detail_label.setWordWrap(True)

        detail_layout.addWidget(self._detail_label)
        layout.addWidget(detail_container, stretch=2)

    # Actions --------------------------------------------------------------
    def _on_open_vault(self) -> None:
        """
        Open an image containing a vault and display its entries.
        """
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Vault Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)",
        )
        if not image_path:
            return

        # Ask for passphrase
        from PySide6.QtWidgets import QInputDialog

        passphrase, ok = QInputDialog.getText(
            self,
            "Vault Passphrase",
            "Enter vault passphrase:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not passphrase:
            return

        result: VaultLoadResult = self._vault_controller.load_vault(
            image_path=image_path,
            passphrase=passphrase,
        )

        if not result.success or result.vault is None:
            QMessageBox.critical(
                self,
                "Error",
                result.error or "Failed to load vault from image.",
            )
            return

        self._current_vault = result.vault
        self._current_image_path = image_path
        self._populate_entries()

    def _populate_entries(self) -> None:
        """Populate the entry list with keys from the current vault."""
        from stegvault.vault.core import Vault

        self._entry_list.clear()
        self._detail_label.setText(
            f"Vault loaded from:\n{self._current_image_path or ''}\n\n"
            "Select an entry on the left to view details."
        )

        if not isinstance(self._current_vault, Vault):
            return

        keys = list_entries(self._current_vault)
        for key in keys:
            QListWidgetItem(key, self._entry_list)

    def _on_entry_selected(
        self,
        current: Optional[QListWidgetItem],
        _previous: Optional[QListWidgetItem],
    ) -> None:
        """Update detail panel when a new entry is selected."""
        if current is None or self._current_vault is None:
            return

        key = current.text()
        entry = get_entry(self._current_vault, key)
        if entry is None:
            self._detail_label.setText(f"Entry not found: {key}")
            return

        # Show non-sensitive fields; passwords remain hidden in UI for now.
        tags = ", ".join(entry.tags) if entry.tags else "(none)"
        details = [
            f"Key: {entry.key}",
            f"Username: {entry.username or ''}",
            f"URL: {entry.url or ''}",
            f"Tags: {tags}",
            "",
            f"Created: {entry.created}",
            f"Modified: {entry.modified}",
            f"Last accessed: {entry.accessed or 'never'}",
            "",
            "Notes:",
            entry.notes or "",
        ]
        self._detail_label.setText("\n".join(details))


class StegVaultGUI:
    """Entry point for the desktop GUI. Runs the Qt event loop."""

    def run(self) -> None:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        window = MainWindow()
        window.show()
        app.exec()
