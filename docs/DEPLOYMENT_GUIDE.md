# 部署指南

本文件提供完整的環境配置和部署指南，涵蓋開發、測試和生產環境的設定。

## 環境配置

### 支援的環境

系統支援三種環境配置：

1. **Development (開發環境)** - 本地開發使用
2. **Testing (測試環境)** - 自動化測試和 CI/CD
3. **Production (生產環境)** - 正式環境部署

### 環境變數檔案

每個環境都有對應的配置檔案：

```
backend/
├── .env.development    # 開發環境配置
├── .env.testing       # 測試環境配置
├── .env.production    # 生產環境配置
└── .env.example       # 範例檔案
```

### 環境切換

透過設定 `ENVIRONMENT` 環境變數來切換環境：

```bash
# 在 .env 檔案中設定
ENVIRONMENT=development

# 或透過命令列設定
export ENVIRONMENT=production
```

## 開發環境部署

### 快速啟動

1. **複製環境變數檔案**：

   ```bash
   cp .env.example .env
   ```

2. **啟動開發環境**：

   ```bash
   # 使用 PowerShell 腳本 (推薦)
   .\scripts\docker-dev.ps1 setup

   # 或直接使用 Docker Compose
   docker-compose up --build -d
   ```

3. **驗證服務**：
   - Backend API: http://localhost:8000
   - API 文件: http://localhost:8000/docs
   - pgAdmin: http://localhost:5050

### 開發環境特色

- **自動重載**: 程式碼變更時自動重新載入
- **本地資料庫**: 包含 PostgreSQL 16 容器
- **除錯模式**: 啟用詳細日誌記錄
- **開發工具**: 包含 pgAdmin 資料庫管理介面

## 測試環境部署

### 配置要求

測試環境需要外部資料庫連接：

```bash
# .env.testing 範例
ENVIRONMENT=testing
DATABASE_URL=postgresql://user:password@test-db:5432/testdb
DEBUG=false
LOG_LEVEL=INFO
```

### 部署步驟

1. **準備測試資料庫**：

   ```bash
   # 確保測試資料庫可用
   psql -h test-db -U user -d testdb -c "SELECT 1;"
   ```

2. **啟動測試環境**：

   ```bash
   ENVIRONMENT=testing docker-compose -f docker-compose.yml up -d
   ```

3. **執行測試**：
   ```bash
   .\scripts\docker-dev.ps1 test
   ```

## 生產環境部署

### 前置準備

1. **準備生產資料庫**
2. **設定環境變數**
3. **準備 SSL 憑證** (如需要)
4. **配置反向代理** (Nginx)

### 生產環境配置

```bash
# .env.production 範例
ENVIRONMENT=production
DATABASE_URL=postgresql://prod_user:secure_password@prod-db:5432/proddb
DEBUG=false
LOG_LEVEL=WARNING
LOG_FILE_PATH=/app/logs/app.log

# CORS 設定
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]

# 應用程式設定
APP_NAME="Production API"
VERSION="1.0.0"
```

### 部署步驟

1. **建立生產映像**：

   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
   ```

2. **啟動生產服務**：

   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **驗證部署**：

   ```bash
   # 檢查服務狀態
   docker-compose ps

   # 檢查健康狀態
   curl http://localhost:8000/health
   ```

### 生產環境最佳實務

#### 安全性

- 使用強密碼和安全的資料庫連接
- 啟用 HTTPS
- 限制 CORS 來源
- 定期更新依賴套件

#### 效能優化

- 設定適當的資源限制
- 使用連接池
- 啟用快取機制
- 監控資源使用情況

#### 監控和日誌

- 設定結構化日誌記錄
- 配置日誌輪轉
- 設定監控告警
- 定期備份日誌

## Docker 配置詳解

### Dockerfile 特色

- **多階段建構**: 優化映像大小
- **安全性**: 使用非 root 使用者
- **快取優化**: 分層建構提升建構速度

### Docker Compose 檔案

#### docker-compose.yml (基礎配置)

```yaml
version: "3.8"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### docker-compose.override.yml (開發覆蓋)

- 包含 PostgreSQL 16 容器
- 啟用程式碼熱重載
- 包含 pgAdmin 管理介面

#### docker-compose.prod.yml (生產配置)

- 資源限制設定
- 日誌配置
- 安全性強化

### 健康檢查

所有服務都包含健康檢查：

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 資料庫管理

### 遷移管理

使用 Alembic 進行資料庫遷移：

```bash
# 建立新遷移
docker-compose exec backend alembic revision --autogenerate -m "描述"

# 執行遷移
docker-compose exec backend alembic upgrade head

# 回滾遷移
docker-compose exec backend alembic downgrade -1
```

### 備份和還原

```bash
# 備份資料庫
docker-compose exec postgres pg_dump -U postgres -d mydb > backup.sql

# 還原資料庫
docker-compose exec -T postgres psql -U postgres -d mydb < backup.sql
```

## 擴展和維護

### 水平擴展

```bash
# 擴展後端服務
docker-compose up --scale backend=3 -d
```

### 更新部署

```bash
# 滾動更新
docker-compose pull
docker-compose up -d --no-deps backend
```

### 清理和維護

```bash
# 清理未使用的映像
docker system prune -f

# 清理未使用的卷
docker volume prune -f
```

## 故障排除

常見問題請參考 [故障排除指南](TROUBLESHOOTING.md)。

## 安全性檢查清單

- [ ] 資料庫密碼安全
- [ ] CORS 設定正確
- [ ] HTTPS 已啟用
- [ ] 日誌不包含敏感資訊
- [ ] 容器以非 root 使用者執行
- [ ] 定期更新基礎映像
- [ ] 網路隔離設定
- [ ] 資源限制配置
