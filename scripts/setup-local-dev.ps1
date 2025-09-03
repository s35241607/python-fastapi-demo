#!/usr/bin/env pwsh

# 本地開發環境設定腳本
Write-Host "🔧 Setting up local development environment..." -ForegroundColor Green

# 檢查 Python 版本
Write-Host "`n📋 Checking Python version..." -ForegroundColor Yellow
python --version

# 進入 backend 目錄
Set-Location backend

# 建立虛擬環境（如果不存在）
if (-not (Test-Path ".venv")) {
    Write-Host "`n🐍 Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# 啟動虛擬環境
Write-Host "`n⚡ Activating virtual environment..." -ForegroundColor Yellow
if ($IsWindows) {
    & .\.venv\Scripts\Activate.ps1
} else {
    & ./.venv/bin/activate
}

# 安裝依賴項
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -e .
pip install pytest pytest-asyncio httpx requests

# 建立日誌目錄
Write-Host "`n📁 Creating logs directory..." -ForegroundColor Yellow
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs"
}

# 回到根目錄
Set-Location ..

Write-Host "`n✅ Local development environment setup completed!" -ForegroundColor Green
Write-Host "📝 You can now use F5 in VS Code to start the application or run tests." -ForegroundColor Cyan
Write-Host "🚀 Available launch configurations:" -ForegroundColor Cyan
Write-Host "   - 🚀 Start FastAPI Server" -ForegroundColor White
Write-Host "   - 🧪 Run Core Tests" -ForegroundColor White
Write-Host "   - 🐛 Debug FastAPI Server" -ForegroundColor White
Write-Host "   - 🧪 Debug Current Test" -ForegroundColor White