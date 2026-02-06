# Test Suite Performance Guide

## Overview

StegVault has a comprehensive test suite with **1078 tests** covering 81% of the codebase. Due to the extensive use of Textual UI framework and async testing, the full test suite can consume significant memory (up to 14GB RAM) when run all at once.

This guide provides strategies for memory-efficient test execution.

## Problem Analysis

### Memory Usage Patterns

**High-Memory Modules**:
- `test_tui_widgets.py`: 205 tests (19% of suite), creates 245+ Screen instances
  - **Memory**: <1GB with cleanup (✅ OPTIMIZED)
  - **Duration**: ~9 seconds
- `test_tui_screens.py`: 56 tests with async operations
  - **Memory**: <1GB with cleanup (✅ OPTIMIZED)
  - **Duration**: ~2 seconds
- `test_tui_app.py`: 41 tests with async operations
  - **Memory**: 9-11GB (⚠️ HIGH - creates full App instances)
  - **Duration**: Hangs/slow (2+ minutes)
- **Total TUI tests**: 302 tests (28% of suite)

**Root Causes**:
1. Textual Screen objects hold DOM trees, CSS engines, and event loops
2. Each Screen instance: ~50-100MB memory
3. **Full App instances (StegVaultTUI)**: ~200-300MB each, with worker threads
4. Async event loops accumulate without explicit cleanup
5. Function-scoped fixtures create new instances per test

### Memory Optimizations Implemented

**v0.7.9+ improvements**:
1. **Automatic cleanup fixture** (`conftest.py`):
   - Runs `gc.collect()` after each test
   - Session-level cleanup at start/end

2. **Event loop cleanup**:
   - Explicit event loop closure for async tests
   - Cancels pending tasks before loop close

3. **Garbage collection**:
   - Forces collection of unreferenced Textual objects
   - Releases memory from mock objects

## Running Tests Efficiently

### Option 1: Run Specific Test Modules (Recommended)

Instead of running the full suite, run modules individually:

```bash
# Crypto and core modules (fast, low memory)
pytest tests/unit/test_crypto.py tests/unit/test_vault.py

# TUI modules (one at a time)
pytest tests/unit/test_tui_widgets.py     # 205 tests, 9s, <1GB ✅
pytest tests/unit/test_tui_screens.py      # 56 tests, 2s, <1GB ✅
pytest tests/unit/test_tui_app.py          # 41 tests, 2+ min, 9-11GB ⚠️

# CLI modules
pytest tests/unit/test_cli.py tests/unit/test_vault_cli.py
```

**Memory usage**:
- Most modules: 500MB-1GB (manageable)
- `test_tui_app.py`: **9-11GB** (requires 16GB+ RAM system)

**⚠️ WARNING**: Do NOT run `test_tui_app.py` on systems with <12GB RAM!

### Option 2: Run Tests by Category

```bash
# Non-TUI tests (low memory usage)
pytest tests/unit/ --ignore=tests/unit/test_tui_widgets.py \
                    --ignore=tests/unit/test_tui_screens.py \
                    --ignore=tests/unit/test_tui_app.py \
                    --ignore=tests/unit/test_settings_screen.py

# TUI Screen tests only (optimized, low memory)
pytest tests/unit/test_tui_widgets.py tests/unit/test_tui_screens.py tests/unit/test_settings_screen.py

# TUI App tests (HIGH MEMORY - skip on low-RAM systems)
pytest tests/unit/test_tui_app.py
```

### Option 3: Run Without Coverage (Faster Iteration)

For quick verification during development:

```bash
# Skip coverage to reduce memory overhead
pytest tests/unit/test_tui_widgets.py --no-cov

# Or override addopts
pytest tests/unit/test_tui_widgets.py -o addopts=""
```

**Memory savings**: ~30-40% reduction without coverage tracking

### Option 4: Full Suite (High Memory)

Only run full suite on final validation or CI:

```bash
# Full suite with coverage
pytest

# Expected: 1078 tests, ~10-14GB RAM peak usage
```

**Requirements**:
- 16GB+ RAM recommended
- Close other applications
- Allow 2-3 minutes for completion

## Memory Monitoring

### Check Running Tests

```bash
# Windows (PowerShell)
Get-Process python | Select-Object ProcessName, Id, WorkingSet64 | Format-Table

# Kill runaway pytest process
taskkill /PID <process_id> /F
```

### Signs of Memory Issues

- Test suite hangs without progress
- System becomes unresponsive
- RAM usage exceeds 10GB for single pytest process

**Solution**: Kill process and use Option 1 or 2 above

## CI/CD Recommendations

### GitHub Actions

```yaml
# Split TUI and non-TUI tests into separate jobs
jobs:
  test-core:
    steps:
      - run: pytest tests/unit/ --ignore=tests/unit/test_tui_*.py

  test-tui:
    steps:
      - run: pytest tests/unit/test_tui_*.py
```

**Benefits**:
- Parallel execution
- Isolated memory per job
- Faster overall completion

## Future Improvements

### Potential Optimizations

1. **pytest-xdist** (parallel execution):
   ```bash
   pip install pytest-xdist
   pytest -n auto  # Distributes tests across CPU cores
   ```
   - Isolates memory per worker process
   - Reduces peak RAM usage by ~60%

2. **Textual app mocking**:
   - Replace Screen instantiation with lightweight mocks
   - Test business logic without full UI framework

3. **Test segmentation**:
   - Group related tests to share fixtures
   - Reduce repeated object creation

## Best Practices

1. **During development**:
   - Run only affected test modules
   - Use `--no-cov` for quick iteration
   - Run full suite before commit

2. **Before commit**:
   - Run full suite with coverage
   - Verify 1078 tests passing
   - Check coverage remains ≥81%

3. **On low-memory systems (<8GB RAM)**:
   - NEVER run full suite
   - Use Option 1 (module-by-module)
   - Consider cloud CI for full validation

## Summary

**Default strategy** (recommended for most developers):
```bash
# Run non-TUI tests (fast, low memory)
pytest tests/unit/ --ignore=tests/unit/test_tui_*.py --ignore=tests/unit/test_settings_screen.py

# Run TUI Screen tests (optimized, fast)
pytest tests/unit/test_tui_widgets.py tests/unit/test_tui_screens.py tests/unit/test_settings_screen.py

# Skip test_tui_app.py on systems with <12GB RAM
# Or run on high-RAM system/CI only:
pytest tests/unit/test_tui_app.py
```

**Total time** (without test_tui_app.py): ~2-3 minutes
**Peak memory** (without test_tui_app.py): ~2-3GB
**Reliability**: High (no hangs or crashes)

**With test_tui_app.py**:
**Total time**: ~4-5 minutes
**Peak memory**: ~10-12GB
**Requirements**: 16GB+ RAM system

## Known Test Behavior (Skipped Tests & Warnings)

### Skipped Tests (5 total)

Skipped tests are intentional and do not indicate failures:

| Location | Reason |
|----------|--------|
| `test_tui_app.py` | 2 tests: require full Textual app initialization with screen stack (toast notification, path truncation) |
| `test_tui_app.py` | 1 test: complex async loop with file selection retry, difficult to mock |
| `test_updater.py` | 2 tests: conditional skip when not run from source installation |

Run `pytest -v` and look for "5 skipped" in the summary; all other tests should pass.

### Acceptable Warnings (~33)

When running the full suite you may see:

- **ResourceWarning (unclosed DB/socket)**: Typically in error-path tests where the test intentionally triggers failure before normal cleanup. Test-only impact; production code is not affected. Suppressing would require complex mock teardown for low benefit.
- **RuntimeWarning (unawaited coroutine)**: Emitted by the Textual framework in async tests (e.g. unawaited coroutines in internal code). Framework behavior, not application code. Resolving would require changes in Textual.

These warnings do not affect pass/fail. To reduce noise during development you can run specific modules (see "Option 1" above) or filter warnings in `pytest.ini`/`pyproject.toml` if desired.
