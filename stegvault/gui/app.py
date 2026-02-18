"""
Main application and main window for StegVault Desktop GUI.

Uses the same Application Layer (VaultController, CryptoController, Vault)
as CLI and TUI.

Open, View, Save, Save As, Close vault; full CRUD (Add/Edit/Delete entry);
password row in detail panel with Show/Hide and Copy; Generate button in Add/Edit dialogs.
Drag-and-drop an image file onto the window to open it as a vault.
Open-vault decryption runs in a background thread (QThread) to keep the UI responsive.

Debug: set env STEGVAULT_GUI_DEBUG=1 then run:
  set STEGVAULT_GUI_DEBUG=1
  stegvault gui 2>&1 | tee gui_debug.log
(or on Unix: STEGVAULT_GUI_DEBUG=1 stegvault gui 2>&1 | tee gui_debug.log)
Then reproduce the issue (e.g. open Help -> Keyboard Shortcuts). In the log:
- Last line before freeze = where it blocked.
- Many _on_show_shortcuts ENTER without EXIT = dialog open/close loop.
- _update_vault_dependent_actions call# > 50 = signal loop (currentItemChanged re-entrancy).
"""

import os
import sys
import tempfile
import time
from typing import Optional, Tuple

# Debug tracing (enable with STEGVAULT_GUI_DEBUG=1)
_DEBUG_START = time.monotonic()
_DEBUG_ENABLED = os.environ.get("STEGVAULT_GUI_DEBUG", "").strip() in ("1", "true", "yes")


def _dbg(msg: str) -> None:
    if _DEBUG_ENABLED:
        elapsed = (time.monotonic() - _DEBUG_START) * 1000
        print(f"[StegVault GUI] {elapsed:8.1f}ms {msg}", flush=True, file=sys.stderr)


if _DEBUG_ENABLED:
    print(
        "[StegVault GUI] DEBUG TRACE ENABLED (STEGVAULT_GUI_DEBUG=1)", flush=True, file=sys.stderr
    )

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
from stegvault.gui.dialogs import AddEntryDialog, EditEntryDialog, SettingsDialog

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
        QPushButton,
        QHBoxLayout,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import QObject, Qt, QThread, Signal
    from PySide6.QtGui import QDragEnterEvent, QDropEvent, QShowEvent
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

    _debug_update_actions_count = 0  # class-level for debug

    def __init__(self) -> None:
        _dbg("MainWindow.__init__ START")
        super().__init__()
        _dbg("MainWindow.__init__ after super()")
        self.setWindowTitle("StegVault")
        self.setMinimumSize(800, 500)

        # Core state
        _dbg("MainWindow.__init__ creating VaultController")
        self._vault_controller = VaultController()
        _dbg("MainWindow.__init__ VaultController done")
        self._current_vault = None  # type: ignore[assignment]
        self._current_image_path: Optional[str] = None
        self._last_selected_entry_password: Optional[str] = None
        self._pending_open_path: Optional[str] = None
        self._load_thread: Optional[QThread] = None
        self._load_worker: Optional["LoadVaultWorker"] = None
        # Debounce modal dialogs: tiling WMs (e.g. Komorebi) can re-trigger menu actions
        # when focus returns; ignore reopen for 2s; _focus_away_from_menu() reduces re-triggers
        self._last_modal_closed_at: float = 0.0

        self.setAcceptDrops(True)
        _dbg("MainWindow.__init__ calling _setup_ui")
        self._setup_ui()
        _dbg("MainWindow.__init__ _setup_ui done, calling _update_vault_dependent_actions")
        self._update_vault_dependent_actions()
        _dbg("MainWindow.__init__ END")

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        _dbg("MainWindow.showEvent (window just became visible)")

    def _has_vault(self) -> bool:
        """True if a vault is currently loaded."""
        from stegvault.vault.core import Vault

        return isinstance(self._current_vault, Vault)

    # UI setup -------------------------------------------------------------
    def _setup_ui(self) -> None:
        _dbg("_setup_ui START")
        self._create_menu_bar()
        _dbg("_setup_ui menu_bar done")
        self._create_central_layout()
        _dbg("_setup_ui END")

    def _create_menu_bar(self) -> None:
        _dbg("_create_menu_bar START")
        menubar: QMenuBar = self.menuBar()
        file_menu: QMenu = menubar.addMenu("&File")

        open_action = file_menu.addAction("Open Vault…")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_vault)  # type: ignore[arg-type]

        self._save_action = file_menu.addAction("Save")
        self._save_action.setShortcut("Ctrl+S")
        self._save_action.triggered.connect(self._on_save_vault)  # type: ignore[arg-type]

        self._save_as_action = file_menu.addAction("Save As…")
        self._save_as_action.setShortcut("Ctrl+Shift+S")
        self._save_as_action.triggered.connect(self._on_save_vault_as)  # type: ignore[arg-type]

        self._close_vault_action = file_menu.addAction("Close Vault")
        self._close_vault_action.setShortcut("Ctrl+W")
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

        edit_menu.addSeparator()
        settings_action = edit_menu.addAction("Settings…")
        settings_action.triggered.connect(self._on_settings)  # type: ignore[arg-type]

        help_menu: QMenu = menubar.addMenu("&Help")
        shortcuts_action = help_menu.addAction("Keyboard Shortcuts…")
        shortcuts_action.triggered.connect(self._on_show_shortcuts)  # type: ignore[arg-type]
        about_action = help_menu.addAction("About StegVault")
        about_action.triggered.connect(self._on_about)  # type: ignore[arg-type]
        _dbg("_create_menu_bar END")

    def _on_show_shortcuts(self) -> None:
        """Show a dialog listing keyboard shortcuts."""
        text = """File
    Open Vault…     Ctrl+O
    Save            Ctrl+S
    Save As…        Ctrl+Shift+S
    Close Vault     Ctrl+W
    Exit            Ctrl+Q

Edit
    Add Entry…      Ctrl+N
    Edit Entry…     Ctrl+E
    Delete Entry    Del"""
        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            text,
        )

    def _on_about(self) -> None:
        """Show About dialog."""
        QMessageBox.about(
            self,
            "About StegVault",
            f"StegVault v{__version__}\n\n"
            "Password manager using steganography to embed encrypted credentials in images.\n\n"
            "Optional GUI: pip install stegvault[gui]",
        )

    def _on_settings(self) -> None:
        """Show Settings dialog (config path and crypto params, read-only)."""
        if getattr(self, "_modal_debounce", None) and self._modal_debounce("_on_settings"):
            return
        from stegvault.config import get_config_path

        config_path = get_config_path()
        crypto = self._vault_controller.crypto.config.crypto
        dialog = SettingsDialog(
            self,
            config_path=config_path,
            time_cost=crypto.argon2_time_cost,
            memory_cost=crypto.argon2_memory_cost,
            parallelism=crypto.argon2_parallelism,
        )
        dialog.exec()
        if getattr(self, "_modal_closed", None):
            self._modal_closed()

    def _get_selected_key(self) -> Optional[str]:
        """Return the key of the currently selected entry, or None."""
        item = self._entry_list.currentItem()
        return item.text().strip() if item else None

    def _update_vault_dependent_actions(self) -> None:
        """Enable/disable Save, Save As, Close Vault, Add/Edit Entry based on vault and selection."""
        MainWindow._debug_update_actions_count += 1
        n = MainWindow._debug_update_actions_count
        _dbg(f"_update_vault_dependent_actions ENTER call#{n}")
        if n > 50:
            _dbg(f"_update_vault_dependent_actions WARNING call#{n} > 50 (possible loop)")
        self._entry_list.blockSignals(True)
        try:
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
        finally:
            self._entry_list.blockSignals(False)
        _dbg(f"_update_vault_dependent_actions EXIT call#{n}")

    def _create_central_layout(self) -> None:
        _dbg("_create_central_layout START")
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # Left: entry list
        self._entry_list = QListWidget()
        _dbg("_create_central_layout _entry_list created, connecting currentItemChanged")
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

        # Password row: masked by default, Show/Hide toggle and Copy
        password_row = QWidget()
        row_layout = QHBoxLayout(password_row)
        row_layout.addWidget(QLabel("Password:"))
        self._password_line = QLineEdit()
        self._password_line.setReadOnly(True)
        self._password_line.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_line.setText("********")
        self._password_line.setMinimumWidth(120)
        row_layout.addWidget(self._password_line, stretch=1)
        self._btn_show_password = QPushButton("Show")
        self._btn_show_password.clicked.connect(self._on_toggle_password_visibility)  # type: ignore[arg-type]
        self._btn_copy_password = QPushButton("Copy")
        self._btn_copy_password.clicked.connect(self._on_copy_password)  # type: ignore[arg-type]
        row_layout.addWidget(self._btn_show_password)
        row_layout.addWidget(self._btn_copy_password)
        self._password_row_widget = password_row
        self._password_row_widget.setVisible(False)
        detail_layout.addWidget(password_row)

        layout.addWidget(detail_container, stretch=2)
        _dbg("_create_central_layout END")

    # Actions --------------------------------------------------------------
    _IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")

    def _open_vault_from_path(self, image_path: str) -> None:
        """Ask for passphrase and load vault in a background thread. On success updates UI."""
        _dbg("_open_vault_from_path START")
        from PySide6.QtWidgets import QInputDialog

        passphrase, ok = QInputDialog.getText(
            self,
            "Vault Passphrase",
            "Enter vault passphrase:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not passphrase:
            self._modal_closed()
            return
        self._modal_closed()
        self._pending_open_path = image_path
        worker = LoadVaultWorker(image_path=image_path, passphrase=passphrase)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.do_work)  # type: ignore[arg-type]
        worker.finished.connect(self._on_vault_loaded)  # type: ignore[arg-type]
        worker.finished.connect(thread.quit)  # type: ignore[arg-type]
        self._load_thread = thread
        self._load_worker = worker
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.setEnabled(False)
        _dbg("_open_vault_from_path starting worker thread")
        thread.start()

    def _on_vault_loaded(self, success: bool, vault: Optional[object], error_msg: str) -> None:
        """Handle result of background vault load (runs on main thread)."""
        _dbg(f"_on_vault_loaded ENTER success={success}")
        QApplication.restoreOverrideCursor()
        self.setEnabled(True)
        path = self._pending_open_path
        self._pending_open_path = None
        self._load_thread = None
        self._load_worker = None
        if not success or vault is None:
            QMessageBox.critical(
                self,
                "Error",
                error_msg or "Failed to load vault from image.",
            )
            self._modal_closed()
            return
        self._current_vault = vault
        self._current_image_path = path
        self._populate_entries()
        self._update_vault_dependent_actions()
        _dbg("_on_vault_loaded EXIT")

    def _on_open_vault(self) -> None:
        """Open an image containing a vault (file dialog)."""
        if self._modal_debounce("_on_open_vault"):
            return
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Vault Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)",
        )
        if not image_path:
            return
        self._open_vault_from_path(image_path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept drag if at least one dropped item is a local image file."""
        if not event.mimeData().hasUrls():
            return
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if path and os.path.splitext(path)[1].lower() in self._IMAGE_EXTENSIONS:
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent) -> None:
        """Open the first dropped local image file as a vault."""
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = url.toLocalFile()
            if not path or os.path.splitext(path)[1].lower() not in self._IMAGE_EXTENSIONS:
                continue
            if not os.path.isfile(path):
                continue
            self._open_vault_from_path(path)
            event.acceptProposedAction()
            return
        event.ignore()

    def _populate_entries(self) -> None:
        """Populate the entry list with keys from the current vault."""
        from stegvault.vault.core import Vault

        self._entry_list.clear()
        self._last_selected_entry_password = None
        self._password_row_widget.setVisible(False)
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
        key = current.text().strip() if current else None
        _dbg(f"_on_entry_selected ENTER current_key={key!r}")
        if current is None or self._current_vault is None:
            self._last_selected_entry_password = None
            self._password_row_widget.setVisible(False)
            if self._has_vault() and self._current_image_path:
                self._detail_label.setText(
                    f"Vault loaded from:\n{self._current_image_path or ''}\n\n"
                    "Select an entry on the left to view details."
                )
            self._update_vault_dependent_actions()
            _dbg("_on_entry_selected EXIT (no current or no vault)")
            return

        key = current.text()
        entry = get_entry(self._current_vault, key)
        if entry is None:
            self._detail_label.setText(f"Entry not found: {key}")
            self._last_selected_entry_password = None
            self._password_row_widget.setVisible(False)
            self._update_vault_dependent_actions()
            _dbg("_on_entry_selected EXIT (entry not found)")
            return

        self._last_selected_entry_password = entry.password or ""
        self._password_row_widget.setVisible(True)
        self._password_line.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_line.setText("********")
        self._btn_show_password.setText("Show")

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
        _dbg("_on_entry_selected EXIT")

    def _ask_passphrase(self, title: str = "Vault Passphrase") -> Optional[str]:
        """Ask for passphrase via dialog. Returns None if cancelled or empty."""
        from PySide6.QtWidgets import QInputDialog

        passphrase, ok = QInputDialog.getText(
            self,
            title,
            "Enter vault passphrase:",
            QLineEdit.EchoMode.Password,
        )
        self._modal_closed()
        if not ok or not passphrase:
            return None
        return passphrase

    def _on_toggle_password_visibility(self) -> None:
        """Toggle between masked and visible password in the detail panel."""
        if self._last_selected_entry_password is None:
            return
        if self._password_line.echoMode() == QLineEdit.EchoMode.Password:
            self._password_line.setEchoMode(QLineEdit.EchoMode.Normal)
            self._password_line.setText(self._last_selected_entry_password)
            self._btn_show_password.setText("Hide")
        else:
            self._password_line.setEchoMode(QLineEdit.EchoMode.Password)
            self._password_line.setText("********")
            self._btn_show_password.setText("Show")

    def _on_copy_password(self) -> None:
        """Copy the current entry password to the clipboard."""
        if self._last_selected_entry_password is None:
            return
        QApplication.clipboard().setText(self._last_selected_entry_password)

    def _on_save_vault(self) -> None:
        """Save current vault to the same image path (overwrite)."""
        if self._modal_debounce("_on_save_vault"):
            return
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
        self._modal_closed()

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
            raise ValueError(f"Unsupported output extension '{out_ext}'. Use .png or .jpg / .jpeg.")

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
        if self._modal_debounce("_on_save_vault_as"):
            return
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
            self._modal_closed()
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
            self._modal_closed()
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
        self._last_selected_entry_password = None
        self._password_row_widget.setVisible(False)
        self._entry_list.clear()
        self._detail_label.setText(
            f"StegVault GUI v{__version__}\n\n"
            "Use File → Open Vault… to load an image-based vault."
        )
        self._update_vault_dependent_actions()

    def _on_add_entry(self) -> None:
        """Open Add Entry dialog and append new entry to current vault (in-memory; user must Save to persist)."""
        if self._modal_debounce("_on_add_entry"):
            return
        if not self._has_vault():
            return
        dialog = AddEntryDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._modal_closed()
            return
        self._modal_closed()
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
            self._modal_closed()
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
        self._modal_closed()

    def _on_edit_entry(self) -> None:
        """Open Edit Entry dialog for the selected entry and apply changes (in-memory; user must Save to persist)."""
        if self._modal_debounce("_on_edit_entry"):
            return
        if not self._has_vault():
            return
        key = self._get_selected_key()
        if not key:
            QMessageBox.information(
                self,
                "Edit Entry",
                "Select an entry from the list to edit.",
            )
            self._modal_closed()
            return
        entry = get_entry(self._current_vault, key)
        if not entry:
            QMessageBox.critical(
                self,
                "Edit Entry",
                f"Entry not found: {key}",
            )
            self._modal_closed()
            return
        dialog = EditEntryDialog(self, entry=entry)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self._modal_closed()
            return
        self._modal_closed()
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
            self._modal_closed()
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
        self._modal_closed()

    def _on_delete_entry(self) -> None:
        """Delete the selected entry from the vault (in-memory; user must Save to persist)."""
        if self._modal_debounce("_on_delete_entry"):
            return
        if not self._has_vault():
            return
        key = self._get_selected_key()
        if not key:
            QMessageBox.information(
                self,
                "Delete Entry",
                "Select an entry from the list to delete.",
            )
            self._modal_closed()
            return
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            f"Delete entry '{key}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        self._modal_closed()
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok = vault_delete_entry(self._current_vault, key)
        if not ok:
            QMessageBox.critical(
                self,
                "Delete Entry",
                f"Failed to delete entry: {key}",
            )
            self._modal_closed()
            return
        self._populate_entries()
        self._update_vault_dependent_actions()


class LoadVaultWorker(QObject):
    """Runs load_vault in a background thread. Emits finished(success, vault, error_msg)."""

    finished = Signal(bool, object, str)

    def __init__(
        self,
        image_path: str,
        passphrase: str,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._image_path = image_path
        self._passphrase = passphrase

    def do_work(self) -> None:
        _dbg("LoadVaultWorker.do_work START (background thread)")
        controller = VaultController()
        result: VaultLoadResult = controller.load_vault(
            image_path=self._image_path,
            passphrase=self._passphrase,
        )
        self._passphrase = ""
        _dbg("LoadVaultWorker.do_work emitting finished")
        self.finished.emit(
            result.success,
            result.vault,
            result.error or "",
        )
        _dbg("LoadVaultWorker.do_work END")


class StegVaultGUI:
    """Entry point for the desktop GUI. Runs the Qt event loop."""

    def run(self) -> None:
        _dbg("StegVaultGUI.run START")
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        _dbg("StegVaultGUI.run creating MainWindow")
        window = MainWindow()
        _dbg("StegVaultGUI.run MainWindow created, calling show()")
        window.show()
        _dbg("StegVaultGUI.run entering app.exec()")
        app.exec()
        _dbg("StegVaultGUI.run app.exec() returned (event loop ended)")
