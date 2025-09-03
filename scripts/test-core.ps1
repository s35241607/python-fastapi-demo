#!/usr/bin/env pwsh

# 核心功能測試腳本
Write-Host "🧪 Running Core Functionality Tests..." -ForegroundColor Green

# 檢查 Docker 服務狀態
Write-Host "📋 Checking service status..." -ForegroundColor Yellow
docker-compose ps

Write-Host "`n🔧 Running core middleware tests..." -ForegroundColor Yellow
docker-compose exec backend python -m pytest tests/test_error_handler.py tests/test_logging_middleware.py tests/test_jwt_parser.py tests/test_middleware_integration.py -v --tb=short

Write-Host "`n✅ Core tests completed!" -ForegroundColor Green