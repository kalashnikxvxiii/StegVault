"""
Dialogs for StegVault Desktop GUI.

Add Entry, Edit Entry, Settings (read-only), Delete confirmation (via QMessageBox in app).
"""

from pathlib import Path
from typing import Optional, List, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from stegvault.vault.core import VaultEntry

try:
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except ImportError as e:
    raise ImportError(
        "PySide6 is required for the GUI. Install with: pip install stegvault[gui]"
    ) from e


class AddEntryDialog(QDialog):
    """
    Dialog to add a new vault entry.

    Fields: key (required), password (required), username, url, notes, tags (comma-separated).
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Entry")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText("e.g. gmail, github")
        self._key_edit.setMaxLength(200)
        form.addRow("Key (required):", self._key_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_edit.setPlaceholderText("Password")
        btn_generate = QPushButton("Generate")
        btn_generate.clicked.connect(self._on_generate_password)  # type: ignore[arg-type]
        password_row = QWidget()
        password_row_layout = QHBoxLayout(password_row)
        password_row_layout.setContentsMargins(0, 0, 0, 0)
        password_row_layout.addWidget(self._password_edit, stretch=1)
        password_row_layout.addWidget(btn_generate)
        form.addRow("Password (required):", password_row)

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("Username or email")
        form.addRow("Username:", self._username_edit)

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://...")
        form.addRow("URL:", self._url_edit)

        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setPlaceholderText("Notes")
        self._notes_edit.setMaximumHeight(80)
        form.addRow("Notes:", self._notes_edit)

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("tag1, tag2, tag3")
        form.addRow("Tags (comma-separated):", self._tags_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_generate_password(self) -> None:
        from stegvault.vault.generator import generate_password

        self._password_edit.setText(generate_password(length=20))

    def _on_accept(self) -> None:
        key = self._key_edit.text().strip()
        password = self._password_edit.text()
        if not key:
            self._key_edit.setFocus()
            return
        if not password:
            self._password_edit.setFocus()
            return
        self.accept()

    def get_key(self) -> str:
        return self._key_edit.text().strip()

    def get_password(self) -> str:
        return self._password_edit.text()

    def get_username(self) -> Optional[str]:
        t = self._username_edit.text().strip()
        return t if t else None

    def get_url(self) -> Optional[str]:
        t = self._url_edit.text().strip()
        return t if t else None

    def get_notes(self) -> Optional[str]:
        t = self._notes_edit.toPlainText().strip()
        return t if t else None

    def get_tags(self) -> List[str]:
        t = self._tags_edit.text().strip()
        if not t:
            return []
        return [tag.strip() for tag in t.split(",") if tag.strip()]


class EditEntryDialog(QDialog):
    """
    Dialog to edit an existing vault entry.

    Key is read-only. Password: leave blank to keep current; otherwise updated.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        entry: Optional["VaultEntry"] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Entry")
        self.setMinimumWidth(400)
        self._entry = entry
        self._setup_ui()
        if entry:
            self._fill_from_entry()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._key_edit = QLineEdit()
        self._key_edit.setReadOnly(True)
        self._key_edit.setPlaceholderText("(key)")
        form.addRow("Key:", self._key_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_edit.setPlaceholderText("Leave blank to keep current password")
        btn_generate = QPushButton("Generate")
        btn_generate.clicked.connect(self._on_generate_password)  # type: ignore[arg-type]
        password_row = QWidget()
        password_row_layout = QHBoxLayout(password_row)
        password_row_layout.setContentsMargins(0, 0, 0, 0)
        password_row_layout.addWidget(self._password_edit, stretch=1)
        password_row_layout.addWidget(btn_generate)
        form.addRow("Password:", password_row)

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("Username or email")
        form.addRow("Username:", self._username_edit)

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://...")
        form.addRow("URL:", self._url_edit)

        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setMaximumHeight(80)
        form.addRow("Notes:", self._notes_edit)

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("tag1, tag2, tag3")
        form.addRow("Tags (comma-separated):", self._tags_edit)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_generate_password(self) -> None:
        from stegvault.vault.generator import generate_password

        self._password_edit.setText(generate_password(length=20))

    def _fill_from_entry(self) -> None:
        if not self._entry:
            return
        e = self._entry
        self._key_edit.setText(e.key)
        self._username_edit.setText(e.username or "")
        self._url_edit.setText(e.url or "")
        self._notes_edit.setPlainText(e.notes or "")
        self._tags_edit.setText(", ".join(e.tags) if e.tags else "")

    def get_key(self) -> str:
        return self._key_edit.text().strip()

    def get_password_new_or_unchanged(self) -> Optional[str]:
        """Return new password if user entered one, else None (do not update password)."""
        p = self._password_edit.text().strip()
        return p if p else None

    def get_username(self) -> Optional[str]:
        t = self._username_edit.text().strip()
        return t if t else None

    def get_url(self) -> Optional[str]:
        t = self._url_edit.text().strip()
        return t if t else None

    def get_notes(self) -> Optional[str]:
        t = self._notes_edit.toPlainText().strip()
        return t if t else None

    def get_tags(self) -> List[str]:
        t = self._tags_edit.text().strip()
        if not t:
            return []
        return [tag.strip() for tag in t.split(",") if tag.strip()]


class SettingsDialog(QDialog):
    """
    Read-only settings dialog: config file path and current crypto parameters (Argon2).
    Advanced editing remains in config file or TUI.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        config_path: Union[str, Path, None] = None,
        time_cost: int = 3,
        memory_cost: int = 65536,
        parallelism: int = 4,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        path_str = str(config_path) if config_path else "(default)"
        self._setup_ui(path_str, time_cost, memory_cost, parallelism)

    def _setup_ui(
        self, config_path_str: str, time_cost: int, memory_cost: int, parallelism: int
    ) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        path_edit = QLineEdit()
        path_edit.setReadOnly(True)
        path_edit.setText(config_path_str)
        form.addRow("Config file:", path_edit)

        layout.addLayout(form)
        layout.addWidget(QLabel("Cryptography (Argon2) — read-only; edit via config file or TUI:"))

        crypto_form = QFormLayout()
        time_edit = QLineEdit()
        time_edit.setReadOnly(True)
        time_edit.setText(str(time_cost))
        crypto_form.addRow("Time cost:", time_edit)

        mem_edit = QLineEdit()
        mem_edit.setReadOnly(True)
        mem_edit.setText(f"{memory_cost} KB")
        crypto_form.addRow("Memory cost:", mem_edit)

        par_edit = QLineEdit()
        par_edit.setReadOnly(True)
        par_edit.setText(str(parallelism))
        crypto_form.addRow("Parallelism:", par_edit)

        layout.addLayout(crypto_form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
