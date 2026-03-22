#!/bin/bash
# Pre-commit validation script for StegVault
# Replicates ALL GitHub Actions workflows to prevent CI failures
# Run this before every commit to ensure all checks pass

set -e  # Exit on any error

# Auto-activate virtualenv if present
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

echo "=========================================="
echo "StegVault Pre-Commit Validation"
echo "Replicating CI/CD Pipeline Locally"
echo "=========================================="
echo ""

FAILED=0

# Track which checks failed
FAILED_CHECKS=()

# 1. CODE FORMATTING CHECK (Code Quality Workflow)
echo "=== 1/5: Code Formatting (Black) ==="
echo "Checking code formatting..."
if black --check stegvault tests 2>&1; then
    echo "[✓] Code is properly formatted"
else
    echo ""
    echo "[!] Code formatting issues detected"
    echo "    Applying automatic formatting..."
    black stegvault tests
    echo "[✓] Code formatted successfully"
    echo ""
    echo "    ⚠️  WARNING: Files were modified by Black formatter"
    echo "    You need to stage the changes and commit again:"
    echo "    git add -A"
    echo "    git commit --amend --no-edit"
    echo ""
fi
echo ""

# 2. TESTS WITH COVERAGE (CI Workflow)
echo "=== 2/5: Test Suite with Coverage ==="
echo "Running pytest with timeout and coverage (matches CI exactly)..."
if pytest --cov=stegvault --cov-report=xml --cov-report=term --timeout=60 2>&1; then
    echo "[✓] All tests passed with coverage"
else
    echo "[✗] Tests failed"
    FAILED=1
    FAILED_CHECKS+=("pytest")
fi
echo ""

# 3. TYPE CHECKING (Code Quality Workflow)
echo "=== 3/5: Type Checking (mypy) ==="
echo "Running mypy type checker..."
if command -v mypy &> /dev/null; then
    if mypy stegvault 2>&1; then
        echo "[✓] Type checking passed"
    else
        echo "[!] Type checking issues detected (non-blocking in CI)"
        # Don't fail - mypy is continue-on-error in CI
    fi
else
    echo "[SKIP] mypy not installed (install with: pip install mypy)"
fi
echo ""

# 4. SECURITY SCAN (Code Quality Workflow)
echo "=== 4/5: Security Scan (Bandit) ==="
echo "Running bandit security scanner..."
if command -v bandit &> /dev/null; then
    # Run twice: first for JSON report, second for terminal output
    bandit -r stegvault -f json -o bandit-report.json 2>&1 || true
    if bandit -r stegvault 2>&1; then
        echo "[✓] No security issues detected"
    else
        echo "[!] Security issues detected (review output above)"
        # Don't fail - bandit uses || true in CI
    fi
else
    echo "[SKIP] Bandit not installed (install with: pip install bandit)"
fi
echo ""

# 5. DEPENDENCY VULNERABILITIES (Security Workflow)
echo "=== 5/5: Dependency Security Scan (Safety) ==="
echo "Running safety dependency scanner..."
if command -v safety &> /dev/null; then
    # Run twice: first for JSON report, second for terminal output
    safety check --json --output safety-report.json 2>&1 || true
    if safety check 2>&1; then
        echo "[✓] No vulnerable dependencies detected"
    else
        echo "[!] Vulnerable dependencies detected (non-blocking in CI)"
        # Don't fail - safety is continue-on-error in CI
    fi
else
    echo "[SKIP] Safety not installed (install with: pip install safety)"
fi
echo ""

# Final summary
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL PRE-COMMIT CHECKS PASSED!"
    echo "=========================================="
    echo ""
    echo "Ready to commit safely. CI workflows will pass."
    echo ""
    echo "Next steps:"
    echo "  git add -A"
    echo "  git commit -m \"your message\""
    echo "  git push origin main"
    echo ""
    echo "After pushing, verify workflows:"
    echo "  gh run list --limit 3"
    echo ""
    exit 0
else
    echo "❌ PRE-COMMIT VALIDATION FAILED"
    echo "=========================================="
    echo ""
    echo "Failed checks: ${FAILED_CHECKS[*]}"
    echo ""
    echo "⚠️  DO NOT COMMIT - CI will fail!"
    echo ""
    echo "Fix the issues above before committing."
    echo ""
    exit 1
fi
