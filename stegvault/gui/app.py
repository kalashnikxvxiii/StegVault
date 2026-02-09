"""
Main application and main window for StegVault Desktop GUI.

Uses the same Application Layer (VaultController, CryptoController) as CLI and TUI.
"""

from stegvault import __version__

try:
    from PySide6.QtWidgets import (
        QApplication,
        QLabel,
        QMainWindow,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtCore import Qt
except ImportError as e:
    raise ImportError(
        "PySide6 is required for the GUI. Install with: pip install stegvault[gui]"
    ) from e


class MainWindow(QMainWindow):
    """Main application window (minimal shell for v0.8.0 foundation)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StegVault")
        self.setMinimumSize(400, 300)
        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        label = QLabel(f"StegVault GUI v{__version__}\n\nDesktop interface (preview).")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


class StegVaultGUI:
    """Entry point for the desktop GUI. Runs the Qt event loop."""

    def run(self) -> None:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        window = MainWindow()
        window.show()
        app.exec()
