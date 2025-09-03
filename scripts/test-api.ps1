#!/usr/bin/env pwsh

# API 功能測試腳本
Write-Host "🌐 Testing API Functionality..." -ForegroundColor Green

Write-Host "`n📋 Checking service health..." -ForegroundColor Yellow
$health = curl -s http://localhost:8000/health | ConvertFrom-Json
Write-Host "Health Status: $($health.status)" -ForegroundColor Green

Write-Host "`n🔧 Testing error handling..." -ForegroundColor Yellow
Write-Host "Testing validation error:"
curl -s http://localhost:8000/api/v1/test-errors/app-exception | ConvertFrom-Json | ConvertTo-Json -Depth 3

Write-Host "`n🔐 Testing JWT middleware..." -ForegroundColor Yellow
Write-Host "Testing middleware chain:"
curl -s http://localhost:8000/api/v1/test-errors/middleware-chain | ConvertFrom-Json | ConvertTo-Json -Depth 3

Write-Host "`n✅ API tests completed!" -ForegroundColor Green