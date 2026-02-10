"""
Main application and main window for StegVault Desktop GUI.

Uses the same Application Layer (VaultController, CryptoController, Vault)
as CLI and TUI.

GUI foundation is complete when: Open, View, Save, Save As, Close vault
work end-to-end. Next phase: Add/Edit/Delete entry dialogs and password
visibility/copy.
"""

import os
import tempfile
from typing import Optional, Tuple

from stegvault import __version__
from stegvault.app.controllers.vault_controller import (
    VaultController,
    VaultLoadResult,
    VaultSaveResult,
)
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

    Foundation: Open / View / Save / Close vault cycle.
    - File → Open Vault…, Save, Save As…, Close vault, Exit
    - List of entry keys + read-only entry details
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
        self._update_vault_dependent_actions()

    def _has_vault(self) -> bool:
        """True if a vault is currently loaded."""
        from stegvault.vault.core import Vault

        return isinstance(self._current_vault, Vault)

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

        self._save_action = file_menu.addAction("Save")
        self._save_action.setShortcut("Ctrl+S")
        self._save_action.triggered.connect(self._on_save_vault)  # type: ignore[arg-type]

        self._save_as_action = file_menu.addAction("Save As…")
        self._save_as_action.triggered.connect(self._on_save_vault_as)  # type: ignore[arg-type]

        self._close_vault_action = file_menu.addAction("Close Vault")
        self._close_vault_action.triggered.connect(self._on_close_vault)  # type: ignore[arg-type]

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)  # type: ignore[arg-type]

    def _update_vault_dependent_actions(self) -> None:
        """Enable/disable Save, Save As, Close Vault based on whether a vault is loaded."""
        enabled = self._has_vault()
        self._save_action.setEnabled(enabled)
        self._save_as_action.setEnabled(enabled)
        self._close_vault_action.setEnabled(enabled)
        if enabled and self._current_image_path:
            self.setWindowTitle(f"StegVault - {self._current_image_path}")
        else:
            self.setWindowTitle("StegVault")

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
        self._update_vault_dependent_actions()

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

    def _ask_passphrase(self, title: str = "Vault Passphrase") -> Optional[str]:
        """Ask for passphrase via dialog. Returns None if cancelled or empty."""
        from PySide6.QtWidgets import QInputDialog

        passphrase, ok = QInputDialog.getText(
            self,
            title,
            "Enter vault passphrase:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not passphrase:
            return None
        return passphrase

    def _on_save_vault(self) -> None:
        """Save current vault to the same image path (overwrite)."""
        if not self._has_vault() or not self._current_image_path:
            return
        passphrase = self._ask_passphrase("Save Vault - Passphrase")
        if not passphrase:
            return
        result: VaultSaveResult = self._vault_controller.save_vault(
            vault=self._current_vault,
            output_path=self._current_image_path,
            passphrase=passphrase,
            cover_image=self._current_image_path,
        )
        if result.success:
            QMessageBox.information(
                self,
                "Saved",
                f"Vault saved to:\n{result.output_path}",
            )
        else:
            QMessageBox.critical(
                self,
                "Save Failed",
                result.error or "Failed to save vault.",
            )

    def _get_cover_for_save_as(
        self, current_path: str, output_path: str
    ) -> Tuple[str, Optional[str]]:
        """
        Return (cover_path, temp_path_to_delete).
        Ensures cover image format matches output extension so the stego layer
        writes the correct format (PNG->.png, JPEG->.jpg). When current and
        output extensions differ, converts current image to a temp file in
        the target format; caller must delete the temp file after save.
        Raises on unsupported extension or conversion failure.
        """
        cur_ext = os.path.splitext(current_path)[1].lower()
        out_ext = os.path.splitext(output_path)[1].lower()
        if cur_ext == out_ext:
            return current_path, None

        if out_ext not in (".png", ".jpg", ".jpeg"):
            raise ValueError(
                f"Unsupported output extension '{out_ext}'. Use .png or .jpg / .jpeg."
            )

        from PIL import Image

        img = Image.open(current_path)
        try:
            img.load()
            if out_ext == ".jpg" or out_ext == ".jpeg":
                if img.mode not in ("RGB", "L"):
                    old_img = img
                    img = img.convert("RGB")
                    old_img.close()
                fmt_save = "JPEG"
            else:
                fmt_save = "PNG"
            fd, temp_path = tempfile.mkstemp(suffix=out_ext)
            os.close(fd)
            try:
                if fmt_save == "JPEG":
                    img.save(temp_path, format="JPEG", quality=95)
                else:
                    img.save(temp_path, format="PNG")
            except Exception:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
            return temp_path, temp_path
        finally:
            img.close()

    def _on_save_vault_as(self) -> None:
        """Save current vault to a new image path. Ensures output format matches extension (PNG/JPEG)."""
        if not self._has_vault() or not self._current_image_path:
            return
        new_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Vault As",
            "",
            "Images (*.png *.jpg *.jpeg);;All Files (*)",
        )
        if not new_path:
            return
        passphrase = self._ask_passphrase("Save Vault As - Passphrase")
        if not passphrase:
            return

        try:
            cover_path, temp_to_delete = self._get_cover_for_save_as(
                self._current_image_path, new_path
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save As",
                f"Cannot prepare image for target format: {e}",
            )
            return

        try:
            result: VaultSaveResult = self._vault_controller.save_vault(
                vault=self._current_vault,
                output_path=new_path,
                passphrase=passphrase,
                cover_image=cover_path,
            )
            if result.success:
                self._current_image_path = new_path
                self._update_vault_dependent_actions()
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Vault saved to:\n{result.output_path}",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    result.error or "Failed to save vault.",
                )
        finally:
            if temp_to_delete and os.path.exists(temp_to_delete):
                try:
                    os.unlink(temp_to_delete)
                except OSError:
                    pass

    def _on_close_vault(self) -> None:
        """Clear current vault and reset UI."""
        self._current_vault = None
        self._current_image_path = None
        self._entry_list.clear()
        self._detail_label.setText(
            f"StegVault GUI v{__version__}\n\n"
            "Use File → Open Vault… to load an image-based vault."
        )
        self._update_vault_dependent_actions()


class StegVaultGUI:
    """Entry point for the desktop GUI. Runs the Qt event loop."""

    def run(self) -> None:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        window = MainWindow()
        window.show()
        app.exec()
