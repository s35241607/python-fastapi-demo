# 專案文件索引

本目錄包含完整的專案文件，涵蓋部署、使用和維護的各個方面。

## 文件結構

### 核心指南

| 文件                                | 描述                 | 適用對象         |
| ----------------------------------- | -------------------- | ---------------- |
| [部署指南](DEPLOYMENT_GUIDE.md)     | 環境配置和部署說明   | 開發者、運維人員 |
| [中介軟體指南](MIDDLEWARE_GUIDE.md) | 中介軟體使用和配置   | 開發者           |
| [故障排除指南](TROUBLESHOOTING.md)  | 診斷、監控和效能調優 | 開發者、運維人員 |

### 技術文件

| 文件                                                         | 描述             |
| ------------------------------------------------------------ | ---------------- |
| [配置說明](../backend/docs/configuration.md)                 | 詳細配置選項說明 |
| [整合測試說明](../backend/tests/README_INTEGRATION_TESTS.md) | 測試執行和驗證   |

## 快速導航

### 新手入門

1. **環境設定**: 參考 [部署指南 - 開發環境部署](DEPLOYMENT_GUIDE.md#開發環境部署)
2. **Docker 使用**: 參考 [主要 README](../README.md#quick-start-with-docker-recommended)
3. **API 測試**: 訪問 http://localhost:8000/docs

### 開發者指南

1. **中介軟體使用**: 參考 [中介軟體指南](MIDDLEWARE_GUIDE.md)
2. **錯誤處理**: 參考 [中介軟體指南 - 錯誤處理](MIDDLEWARE_GUIDE.md#錯誤處理中介軟體)
3. **日誌記錄**: 參考 [中介軟體指南 - 日誌記錄](MIDDLEWARE_GUIDE.md#日誌記錄中介軟體)

### 運維指南

1. **生產部署**: 參考 [部署指南 - 生產環境部署](DEPLOYMENT_GUIDE.md#生產環境部署)
2. **監控設定**: 參考 [故障排除指南 - 監控和告警](TROUBLESHOOTING.md#監控和告警)
3. **備份恢復**: 參考 [故障排除指南 - 備份和災難恢復](TROUBLESHOOTING.md#備份和災難恢復)

## 常見使用場景

### 場景 1: 本地開發環境設定

```bash
# 1. 複製專案
git clone <repository>
cd <project>

# 2. 設定環境變數
cp .env.example .env

# 3. 啟動開發環境
.\scripts\docker-dev.ps1 setup

# 4. 驗證服務
curl http://localhost:8000/health
```

詳細說明: [部署指南 - 開發環境部署](DEPLOYMENT_GUIDE.md#開發環境部署)

### 場景 2: 生產環境部署

```bash
# 1. 準備生產配置
cp backend/.env.example backend/.env.production
# 編輯 .env.production 設定生產參數

# 2. 建構生產映像
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# 3. 啟動生產服務
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. 驗證部署
curl http://localhost:8000/health
```

詳細說明: [部署指南 - 生產環境部署](DEPLOYMENT_GUIDE.md#生產環境部署)

### 場景 3: 問題診斷

```bash
# 1. 檢查服務狀態
docker-compose ps

# 2. 查看日誌
docker-compose logs backend

# 3. 檢查健康狀態
curl http://localhost:8000/health

# 4. 查看結構化日誌
docker-compose exec backend tail -f logs/app.log
```

詳細說明: [故障排除指南](TROUBLESHOOTING.md)

### 場景 4: 中介軟體自訂

```python
# 1. 建立自訂中介軟體
from app.middleware.base import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    async def dispatch(self, request, call_next):
        # 自訂邏輯
        response = await call_next(request)
        return response

# 2. 註冊中介軟體
app.add_middleware(CustomMiddleware)
```

詳細說明: [中介軟體指南](MIDDLEWARE_GUIDE.md)

## 支援和貢獻

### 回報問題

如果遇到問題，請按以下步驟：

1. 查看 [故障排除指南](TROUBLESHOOTING.md) 中的常見問題
2. 收集相關日誌和錯誤資訊
3. 提供系統環境資訊
4. 建立 Issue 並附上詳細資訊

### 文件貢獻

歡迎改善文件品質：

1. 發現錯誤或不清楚的地方
2. 建議新增內容或範例
3. 提供翻譯或本地化改善
4. 分享使用經驗和最佳實務

## 版本資訊

| 版本  | 日期    | 主要變更                             |
| ----- | ------- | ------------------------------------ |
| 1.0.0 | 2024-01 | 初始版本，包含基礎架構和中介軟體系統 |

## 相關資源

### 外部文件

- [FastAPI 官方文件](https://fastapi.tiangolo.com/)
- [Docker 官方文件](https://docs.docker.com/)
- [PostgreSQL 文件](https://www.postgresql.org/docs/)

### 工具和框架

- [Pydantic](https://pydantic-docs.helpmanual.io/) - 資料驗證
- [SQLAlchemy](https://docs.sqlalchemy.org/) - ORM
- [Alembic](https://alembic.sqlalchemy.org/) - 資料庫遷移
- [Loguru](https://loguru.readthedocs.io/) - 日誌記錄
