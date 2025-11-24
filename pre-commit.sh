#!/bin/bash
# Pre-commit validation script for StegVault
# Run this before every commit to avoid CI failures

set -e  # Exit on any error

echo "=========================================="
echo "StegVault Pre-Commit Checks"
echo "=========================================="
echo ""

# 1. Format code
echo "=== 1/3: Formatting code with Black ==="
black stegvault tests
echo "[OK] Code formatting complete"
echo ""

# 2. Run tests
echo "=== 2/3: Running tests ==="
pytest
echo "[OK] All tests passed"
echo ""

# 3. Security scan
echo "=== 3/3: Running security scan ==="
if command -v bandit &> /dev/null; then
    bandit -r stegvault -f json -o bandit-report.json || true
    bandit -r stegvault
    echo "[OK] Security scan complete"
else
    echo "[SKIP] Bandit not installed (install with: pip install bandit)"
    echo "       Security scan will run on CI"
fi
echo ""

# Success message
echo "=========================================="
echo "✅ All pre-commit checks passed!"
echo "=========================================="
echo ""
echo "You can now safely commit and push:"
echo "  git add -A"
echo "  git commit -m \"your message\""
echo "  git push origin main"
echo ""
echo "After pushing, verify workflows with:"
echo "  gh run list --limit 3"
echo ""
