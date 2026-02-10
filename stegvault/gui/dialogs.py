"""
Dialogs for StegVault Desktop GUI.

Add Entry, Edit Entry (future), Delete confirmation (future).
"""

from typing import Optional, List

try:
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLineEdit,
        QPlainTextEdit,
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
        form.addRow("Password (required):", self._password_edit)

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
