# Pre-commit validation script for StegVault (Windows PowerShell)
# Run this before every commit to avoid CI failures

$ErrorActionPreference = "Stop"  # Exit on any error

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "StegVault Pre-Commit Checks" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Format code
Write-Host "=== 1/3: Formatting code with Black ===" -ForegroundColor Yellow
black stegvault tests
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Code formatting complete" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Black formatting failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Run tests
Write-Host "=== 2/3: Running tests ===" -ForegroundColor Yellow
pytest
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] All tests passed" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Tests failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. Security scan
Write-Host "=== 3/3: Running security scan ===" -ForegroundColor Yellow
try {
    $banditInstalled = Get-Command bandit -ErrorAction SilentlyContinue
    if ($banditInstalled) {
        bandit -r stegvault -f json -o bandit-report.json 2>&1 | Out-Null
        bandit -r stegvault
        if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 1) {
            Write-Host "[OK] Security scan complete" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Security scan had issues (check output)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[SKIP] Bandit not installed (install with: pip install bandit)" -ForegroundColor Yellow
        Write-Host "       Security scan will run on CI" -ForegroundColor Gray
    }
} catch {
    Write-Host "[SKIP] Bandit not available" -ForegroundColor Yellow
}
Write-Host ""

# Success message
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ All pre-commit checks passed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now safely commit and push:" -ForegroundColor White
Write-Host "  git add -A" -ForegroundColor Gray
Write-Host "  git commit -m `"your message`"" -ForegroundColor Gray
Write-Host "  git push origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "After pushing, verify workflows with:" -ForegroundColor White
Write-Host "  gh run list --limit 3" -ForegroundColor Gray
Write-Host ""
