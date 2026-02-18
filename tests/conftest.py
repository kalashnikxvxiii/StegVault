"""
Pytest configuration and fixtures for memory-efficient testing.

Provides cleanup hooks to reduce RAM usage during test execution.
Skips TUI test modules when the 'textual' package is not installed (e.g. Python 3.14).
Skips GUI test modules when 'PySide6' is not installed (optional [gui] extra).
"""

from pathlib import Path

import gc
import asyncio
import pytest


def pytest_ignore_collect(collection_path: Path, path=None, config=None) -> bool:
    """
    Skip TUI-related test modules when 'textual' is not installed.
    Skip GUI-related test modules when 'PySide6' is not installed.

    Allows the rest of the test suite to run on environments where textual
    has no wheel (e.g. Python 3.14) or GUI is not installed, so pre-commit and CI can pass.

    Signature matches pytest hook: (collection_path, path, config).
    path is legacy/deprecated; we only use collection_path.
    """
    path_str = str(collection_path)
    if "test_tui" in path_str or "test_settings_screen" in path_str:
        try:
            import textual  # noqa: F401
        except ImportError:
            return True
    if "test_gui" in path_str:
        try:
            import PySide6  # noqa: F401
        except ImportError:
            return True
    return False


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Automatically cleanup after each test.

    Runs garbage collection to release memory from:
    - Textual Screen instances
    - Async event loops
    - Mock objects
    """
    yield
    # Force garbage collection to release unreferenced objects
    gc.collect()


@pytest.fixture(autouse=True, scope="session")
def session_cleanup():
    """
    Cleanup at session start and end.

    Ensures clean state for entire test suite.
    """
    # Initial cleanup before tests
    gc.collect()
    yield
    # Final cleanup after all tests
    gc.collect()


@pytest.fixture
def event_loop():
    """
    Create and cleanup event loop for async tests.

    Explicitly closes event loop after each test to prevent memory leaks.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Cleanup: close all pending tasks
    try:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass
    finally:
        loop.close()
        gc.collect()
