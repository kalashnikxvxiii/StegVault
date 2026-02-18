"""
GUI tests for StegVault Desktop (PySide6).

Collected only when PySide6 is installed (see conftest pytest_ignore_collect).
Requires pytest-qt (install with: pip install stegvault[gui]).
"""

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import QLineEdit, QPushButton

from stegvault.gui.app import MainWindow, LoadVaultWorker, StegVaultGUI
from stegvault.gui.dialogs import AddEntryDialog, EditEntryDialog, SettingsDialog
from stegvault.vault.core import VaultEntry


class TestMainWindow:
    """MainWindow creation and basic state."""

    def test_main_window_opens_with_title(self, qtbot):
        win = MainWindow()
        qtbot.addWidget(win)
        with qtbot.waitExposed(win, timeout=2000):
            win.show()
        assert win.windowTitle() == "StegVault"

    def test_main_window_has_menu_bar(self, qtbot):
        win = MainWindow()
        qtbot.addWidget(win)
        menubar = win.menuBar()
        assert menubar is not None
        actions = menubar.actions()
        assert len(actions) >= 3  # File, Edit, Help


class TestSettingsDialog:
    """Settings dialog shows config path and Argon2 params."""

    def test_settings_dialog_shows_config_and_crypto(self, qtbot):
        dialog = SettingsDialog(
            parent=None,
            config_path="/tmp/test_config.toml",
            time_cost=2,
            memory_cost=8192,
            parallelism=1,
        )
        qtbot.addWidget(dialog)
        edits = dialog.findChildren(QLineEdit)
        assert len(edits) >= 4
        assert edits[0].text() == "/tmp/test_config.toml"
        assert edits[1].text() == "2"
        assert edits[2].text() == "8192 KB"
        assert edits[3].text() == "1"


class TestAddEntryDialog:
    """Add Entry dialog getters and Generate button."""

    def test_add_entry_dialog_getters(self, qtbot):
        dialog = AddEntryDialog(parent=None)
        qtbot.addWidget(dialog)
        dialog._key_edit.setText("mykey")
        dialog._password_edit.setText("mypass")
        dialog._username_edit.setText("user")
        dialog._url_edit.setText("https://example.com")
        dialog._notes_edit.setPlainText("some notes")
        dialog._tags_edit.setText("a, b, c")
        assert dialog.get_key() == "mykey"
        assert dialog.get_password() == "mypass"
        assert dialog.get_username() == "user"
        assert dialog.get_url() == "https://example.com"
        assert dialog.get_notes() == "some notes"
        assert dialog.get_tags() == ["a", "b", "c"]

    def test_add_entry_dialog_generate_fills_password(self, qtbot):
        dialog = AddEntryDialog(parent=None)
        qtbot.addWidget(dialog)
        assert len(dialog._password_edit.text()) == 0
        gen_buttons = dialog.findChildren(QPushButton)
        gen_btn = next((b for b in gen_buttons if b.text() == "Generate"), None)
        assert gen_btn is not None
        qtbot.mouseClick(gen_btn, Qt.MouseButton.LeftButton)
        text = dialog._password_edit.text()
        assert len(text) == 20
        assert text.isprintable()


class TestEditEntryDialog:
    """Edit Entry dialog fill from entry and getters."""

    def test_edit_entry_dialog_fill_and_get(self, qtbot):
        entry = VaultEntry(
            key="entry_key",
            password="secret",
            username="u",
            url="https://u.com",
            notes="n",
            tags=["x", "y"],
        )
        dialog = EditEntryDialog(parent=None, entry=entry)
        qtbot.addWidget(dialog)
        assert dialog.get_key() == "entry_key"
        assert dialog.get_username() == "u"
        assert dialog.get_url() == "https://u.com"
        assert dialog.get_notes() == "n"
        assert dialog.get_tags() == ["x", "y"]
        assert dialog.get_password_new_or_unchanged() is None
        dialog._password_edit.setText("newpass")
        assert dialog.get_password_new_or_unchanged() == "newpass"


class TestLoadVaultWorker:
    """Background worker emits finished on load failure."""

    def test_load_vault_worker_emits_finished_on_failure(self, qtbot):
        worker = LoadVaultWorker(
            image_path="/nonexistent/image.png",
            passphrase="test",
        )
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.do_work)
        worker.finished.connect(thread.quit)
        with qtbot.waitSignal(worker.finished, timeout=10000) as blocker:
            thread.start()
        success, vault, error_msg = blocker.args
        assert success is False
        assert vault is None
        assert isinstance(error_msg, str) and len(error_msg) > 0


class TestStegVaultGUI:
    """Application entry point."""

    def test_stegvault_gui_instantiates(self):
        app = StegVaultGUI()
        assert hasattr(app, "run")
        assert callable(app.run)
