"""
Main application and main window for StegVault Desktop GUI.

Uses the same Application Layer (VaultController, CryptoController, Vault)
as CLI and TUI.

GUI foundation is complete when: Open, View, Save, Save As, Close vault
work end-to-end. Next phase: Add/Edit/Delete entry dialogs and password
visibility/copy.
"""

from typing import Optional

from stegvault import __version__
from stegvault.app.controllers.vault_controller import (
    VaultController,
    VaultLoadResult,
    VaultSaveResult,
)
from stegvault.vault.operations import (
    add_entry as vault_add_entry,
    update_entry as vault_update_entry,
    delete_entry as vault_delete_entry,
    list_entries,
    get_entry,
)
from stegvault.gui.dialogs import AddEntryDialog, EditEntryDialog

try:
    from PySide6.QtWidgets import (
        QApplication,
        QDialog,
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

        edit_menu: QMenu = menubar.addMenu("&Edit")
        self._add_entry_action = edit_menu.addAction("Add Entry…")
        self._add_entry_action.setShortcut("Ctrl+N")
        self._add_entry_action.triggered.connect(self._on_add_entry)  # type: ignore[arg-type]

        self._edit_entry_action = edit_menu.addAction("Edit Entry…")
        self._edit_entry_action.setShortcut("Ctrl+E")
        self._edit_entry_action.triggered.connect(self._on_edit_entry)  # type: ignore[arg-type]

        self._delete_entry_action = edit_menu.addAction("Delete Entry…")
        self._delete_entry_action.setShortcut("Del")
        self._delete_entry_action.triggered.connect(self._on_delete_entry)  # type: ignore[arg-type]

    def _get_selected_key(self) -> Optional[str]:
        """Return the key of the currently selected entry, or None."""
        item = self._entry_list.currentItem()
        return item.text().strip() if item else None

    def _update_vault_dependent_actions(self) -> None:
        """Enable/disable Save, Save As, Close Vault, Add/Edit Entry based on vault and selection."""
        enabled = self._has_vault()
        self._save_action.setEnabled(enabled)
        self._save_as_action.setEnabled(enabled)
        self._close_vault_action.setEnabled(enabled)
        self._add_entry_action.setEnabled(enabled)
        has_selection = self._get_selected_key() is not None
        self._edit_entry_action.setEnabled(enabled and has_selection)
        self._delete_entry_action.setEnabled(enabled and has_selection)
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
        self._update_vault_dependent_actions()

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

    def _on_save_vault_as(self) -> None:
        """Save current vault to a new image path."""
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
        result: VaultSaveResult = self._vault_controller.save_vault(
            vault=self._current_vault,
            output_path=new_path,
            passphrase=passphrase,
            cover_image=self._current_image_path,
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

    def _on_add_entry(self) -> None:
        """Open Add Entry dialog and append new entry to current vault (in-memory; user must Save to persist)."""
        if not self._has_vault():
            return
        dialog = AddEntryDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            vault_add_entry(
                self._current_vault,
                key=dialog.get_key(),
                password=dialog.get_password(),
                username=dialog.get_username(),
                url=dialog.get_url(),
                notes=dialog.get_notes(),
                tags=dialog.get_tags(),
            )
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Add Entry",
                str(e),
            )
            return
        self._populate_entries()
        # Select the new entry in the list
        key = dialog.get_key()
        for i in range(self._entry_list.count()):
            if self._entry_list.item(i).text() == key:
                self._entry_list.setCurrentRow(i)
                break
        QMessageBox.information(
            self,
            "Add Entry",
            f"Entry '{key}' added. Use File → Save to write the vault to the image.",
        )

    def _on_edit_entry(self) -> None:
        """Open Edit Entry dialog for the selected entry and apply changes (in-memory; user must Save to persist)."""
        if not self._has_vault():
            return
        key = self._get_selected_key()
        if not key:
            QMessageBox.information(
                self,
                "Edit Entry",
                "Select an entry from the list to edit.",
            )
            return
        entry = get_entry(self._current_vault, key)
        if not entry:
            QMessageBox.critical(
                self,
                "Edit Entry",
                f"Entry not found: {key}",
            )
            return
        dialog = EditEntryDialog(self, entry=entry)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        kwargs = {
            "username": dialog.get_username(),
            "url": dialog.get_url(),
            "notes": dialog.get_notes(),
            "tags": dialog.get_tags(),
        }
        new_password = dialog.get_password_new_or_unchanged()
        if new_password is not None:
            kwargs["password"] = new_password
        ok = vault_update_entry(self._current_vault, key, **kwargs)
        if not ok:
            QMessageBox.critical(
                self,
                "Edit Entry",
                f"Failed to update entry: {key}",
            )
            return
        self._populate_entries()
        for i in range(self._entry_list.count()):
            if self._entry_list.item(i).text() == key:
                self._entry_list.setCurrentRow(i)
                break
        self._on_entry_selected(
            self._entry_list.currentItem(),
            None,
        )
        QMessageBox.information(
            self,
            "Edit Entry",
            f"Entry '{key}' updated. Use File → Save to write the vault to the image.",
        )

    def _on_delete_entry(self) -> None:
        """Delete the selected entry from the vault (in-memory; user must Save to persist)."""
        if not self._has_vault():
            return
        key = self._get_selected_key()
        if not key:
            QMessageBox.information(
                self,
                "Delete Entry",
                "Select an entry from the list to delete.",
            )
            return
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            f"Delete entry '{key}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok = vault_delete_entry(self._current_vault, key)
        if not ok:
            QMessageBox.critical(
                self,
                "Delete Entry",
                f"Failed to delete entry: {key}",
            )
            return
        self._populate_entries()
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
