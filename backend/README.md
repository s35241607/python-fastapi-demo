# FastAPI Async Demo Application

這是一個乾淨的非同步 FastAPI 應用程式範例，採用現代化的架構設計。

## 專案結構

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── routers.py     # API 路由配置
│   ├── core/
│   │   ├── config.py          # 應用程式配置
│   │   ├── logger.py          # 日誌配置
│   │   └── security.py        # 安全工具
│   ├── db/
│   │   ├── base.py            # 非同步資料庫配置
│   │   └── session.py         # 非同步資料庫 session 管理
│   ├── schemas/               # 空資料夾，準備放置 Pydantic 模型
│   ├── services/              # 空資料夾，準備放置業務邏輯
│   ├── repositories/          # 空資料夾，準備放置資料存取層
│   └── main.py                # FastAPI 應用程式工廠
├── alembic/
│   ├── versions/              # 資料庫遷移檔案
│   └── env.py                 # Alembic 配置
├── tests/
│   ├── api/                   # API 測試
│   │   └── test_items.py      # 基本測試範例
│   ├── services/              # 服務測試
│   └── conftest.py            # 測試配置
├── .env.example               # 環境變數範本
├── alembic.ini                # Alembic 配置
├── main.py                    # 應用程式入口點
└── pyproject.toml             # 專案依賴
```

## 特色

✨ **完全非同步**: 所有資料庫操作和 I/O 都是非同步的
🏗️ **乾淨架構**: 最小化的程式碼結構，易於擴展
🚀 **現代化**: 使用最新的 FastAPI 和 SQLAlchemy 功能
🔧 **開發友善**: 包含完整的開發工具配置

## 快速開始

1. 複製環境變數：

   ```bash
   cp .env.example .env
   ```

2. 安裝依賴：

   ```bash
   pip install -e .
   ```

3. 安裝非同步 SQLite 驅動：

   ```bash
   pip install aiosqlite
   ```

4. 執行應用程式：

   ```bash
   python main.py
   ```

5. 訪問 `http://localhost:8000/docs` 查看 API 文檔

## API 端點

- `/` - 根端點，顯示歡迎訊息
- `/api/v1/health` - 健康檢查端點

## 技術棧

- **FastAPI** - 現代化非同步 Web 框架
- **SQLAlchemy 2.0** - 非同步 ORM
- **aiosqlite** - 非同步 SQLite 驅動
- **Pydantic** - 資料驗證和設定管理
- **Alembic** - 資料庫遷移工具
- **pytest** - 測試框架
- **Loguru** - 現代化日誌庫

## 開發

### 執行測試

```bash
pytest
```

### 程式碼格式化

```bash
ruff format .
```

### 程式碼檢查

```bash
ruff check .
```

### 資料庫遷移

建立新的遷移：

```bash
alembic revision --autogenerate -m "描述變更"
```

套用遷移：

```bash
alembic upgrade head
```

## 擴展指南

這個範例提供了一個乾淨的起點，你可以根據需要添加：

1. **資料模型**: 在 `app/schemas/` 中定義 Pydantic 模型
2. **資料庫模型**: 在 `app/db/` 中定義 SQLAlchemy 模型
3. **業務邏輯**: 在 `app/services/` 中實現服務層
4. **資料存取**: 在 `app/repositories/` 中實現資料存取層
5. **API 端點**: 在 `app/api/v1/endpoints/` 中添加新的端點
