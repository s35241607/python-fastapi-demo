# Python FastAPI Demo

A full-stack application demo with FastAPI backend and modern frontend.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/     # API endpoint handlers
│   │   │       │   ├── health.py
│   │   │       │   └── items.py
│   │   │       └── routers.py     # API router configuration
│   │   ├── core/
│   │   │   ├── config.py          # Application configuration
│   │   │   ├── logger.py          # Logging configuration
│   │   │   └── security.py        # Security utilities
│   │   ├── db/
│   │   │   ├── base.py            # Database base configuration
│   │   │   └── session.py         # Database session management
│   │   ├── schemas/
│   │   │   ├── item.py            # Item Pydantic models
│   │   │   └── user.py            # User Pydantic models
│   │   ├── services/
│   │   │   └── item.py            # Business logic layer
│   │   ├── repositories/
│   │   │   └── item.py            # Data access layer
│   │   └── main.py                # FastAPI application factory
│   ├── alembic/
│   │   ├── versions/              # Database migration files
│   │   └── env.py                 # Alembic configuration
│   ├── tests/
│   │   ├── api/                   # API tests
│   │   ├── services/              # Service tests
│   │   └── conftest.py            # Test configuration
│   ├── .env.example               # Environment variables template
│   ├── alembic.ini                # Alembic configuration
│   ├── main.py                    # Application entry point
│   └── pyproject.toml             # Project dependencies
└── frontend/                      # Frontend application (to be implemented)
```

## Backend Architecture

The backend follows a clean, layered architecture:

- **API Layer** (`api/`): Handles HTTP requests and responses
- **Service Layer** (`services/`): Contains business logic
- **Repository Layer** (`repositories/`): Handles data access
- **Schema Layer** (`schemas/`): Defines data models and validation
- **Core Layer** (`core/`): Contains configuration and utilities

## Getting Started

### Quick Start with Docker (Recommended)

The easiest way to run the application is using Docker Compose:

1. **Prerequisites**: Make sure you have Docker and Docker Compose installed.

2. **Setup environment**:

   ```bash
   # Copy the environment template
   cp .env.example .env

   # Edit .env file with your settings (optional for development)
   ```

3. **Start development environment**:

   ```bash
   # Using PowerShell script (Windows)
   .\scripts\docker-dev.ps1 setup

   # Or using Docker Compose directly
   docker-compose up --build -d
   ```

4. **Access the application**:

   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - pgAdmin (Database UI): http://localhost:5050 (admin@example.com / admin)

5. **Stop the services**:

   ```bash
   # Using PowerShell script
   .\scripts\docker-dev.ps1 stop

   # Or using Docker Compose directly
   docker-compose down
   ```

### Docker Commands

Available PowerShell script commands:

```powershell
# Start development environment
.\scripts\docker-dev.ps1 setup

# Stop all services
.\scripts\docker-dev.ps1 stop

# Restart services
.\scripts\docker-dev.ps1 restart

# View logs
.\scripts\docker-dev.ps1 logs
.\scripts\docker-dev.ps1 logs backend  # specific service

# Run tests
.\scripts\docker-dev.ps1 test

# Check service status
.\scripts\docker-dev.ps1 status

# Clean up Docker resources
.\scripts\docker-dev.ps1 clean
```

### Environment Configurations

The application supports multiple environments:

- **Development** (`.env.development`): Local development with PostgreSQL container
- **Testing** (`.env.testing`): Testing environment with external database
- **Production** (`.env.production`): Production environment with external database

To switch environments, set the `ENVIRONMENT` variable in your `.env` file:

```bash
ENVIRONMENT=development  # or testing, production
```

### Manual Backend Setup (Alternative)

If you prefer to run without Docker:

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Copy environment variables:

   ```bash
   cp .env.example .env
   ```

3. Install dependencies:

   ```bash
   pip install -e .
   ```

4. Run the application:

   ```bash
   fastapi dev main.py
   ```

5. Visit `http://localhost:8000/docs` to see the API documentation.

### API Endpoints

- `/` - Root endpoint
- `/api/v1/health` - Health check endpoint
- `/api/v1/items` - Items management endpoints

## Docker Configuration

### Docker Files

- **`backend/Dockerfile`**: Multi-stage Dockerfile supporting development and production builds
- **`docker-compose.yml`**: Base configuration for all environments
- **`docker-compose.override.yml`**: Development overrides (includes PostgreSQL 16)
- **`docker-compose.prod.yml`**: Production-specific configuration

### Multi-Environment Support

The Docker setup supports different environments:

1. **Development Environment**:

   - Includes PostgreSQL 16 container
   - Hot reload enabled
   - pgAdmin for database management
   - Debug logging enabled

2. **Production Environment**:
   - Optimized Docker image
   - External database connection
   - Resource limits configured
   - Structured logging

### Health Checks

All services include health checks:

- Backend: HTTP health check on `/` endpoint
- PostgreSQL: Database connection check
- Nginx: Service availability check

### Volumes and Data Persistence

- **Development**: Database data persisted in Docker volumes
- **Production**: Logs mounted to host filesystem
- **Configuration**: Environment-specific configs mounted as needed

## Development

### Backend Technologies

- **FastAPI** - Modern, fast web framework for building APIs
- **Pydantic** - Data validation and settings management
- **SQLAlchemy** - SQL toolkit and ORM
- **Alembic** - Database migration tool
- **pytest** - Testing framework
- **Loguru** - Modern logging library

### Testing

Run backend tests:

```bash
cd backend
pytest
```

### Code Quality

The project uses Ruff for linting and formatting:

```bash
cd backend
ruff check .
ruff format .
```

## 中介軟體系統

本專案包含完整的中介軟體系統，提供以下功能：

### 核心中介軟體

- **錯誤處理中介軟體**: 全域異常捕獲和結構化錯誤回應
- **日誌記錄中介軟體**: 結構化 JSON 日誌記錄和請求追蹤
- **JWT 解析中介軟體**: 使用者資訊提取和上下文注入

### 中介軟體特色

- 自動錯誤處理和日誌記錄
- 結構化日誌格式 (JSON)
- JWT token 解析 (錯誤容忍)
- 請求/回應追蹤
- 效能指標記錄

詳細使用說明請參考 [中介軟體使用指南](docs/MIDDLEWARE_GUIDE.md)。

## 文件

### 📚 完整文件指南

查看 **[docs/](docs/)** 目錄獲取完整文件，或參考以下快速連結：

- **[部署指南](docs/DEPLOYMENT_GUIDE.md)** - 環境配置和部署說明
- **[中介軟體指南](docs/MIDDLEWARE_GUIDE.md)** - 中介軟體使用和配置
- **[故障排除指南](docs/TROUBLESHOOTING.md)** - 常見問題和監控指南
- **[文件索引](docs/README.md)** - 完整文件導航和使用場景

### 快速參考

| 文件                                     | 描述                         | 適用對象         |
| ---------------------------------------- | ---------------------------- | ---------------- |
| [部署指南](docs/DEPLOYMENT_GUIDE.md)     | 多環境部署和 Docker 配置     | 開發者、運維人員 |
| [中介軟體指南](docs/MIDDLEWARE_GUIDE.md) | 錯誤處理、日誌記錄、JWT 解析 | 開發者           |
| [故障排除指南](docs/TROUBLESHOOTING.md)  | 診斷、監控和效能調優         | 開發者、運維人員 |

## 監控和日誌

### 日誌查看

```bash
# 查看結構化日誌
docker-compose exec backend tail -f logs/app.log

# 查看特定類型日誌
grep "ERROR" logs/app.log | tail -10
grep "HTTP Request" logs/app.log | tail -10
```

### 健康檢查

```bash
# 檢查服務健康狀態
curl http://localhost:8000/health

# 檢查所有容器狀態
docker-compose ps

# 查看服務日誌
docker-compose logs backend
```

### 效能監控

```bash
# 監控容器資源使用
docker stats

# 查看回應時間
grep "duration_ms" logs/app.log | tail -10
```

## 故障排除

常見問題的快速解決方案：

### 容器啟動問題

```bash
# 重新建構並啟動
docker-compose build --no-cache
docker-compose up -d

# 查看詳細錯誤
docker-compose logs backend
```

### 資料庫連接問題

```bash
# 檢查資料庫狀態
docker-compose ps postgres
docker-compose logs postgres

# 測試資料庫連接
docker-compose exec backend psql $DATABASE_URL -c "SELECT 1;"
```

### 應用程式錯誤

```bash
# 啟用除錯模式
echo "DEBUG=true" >> .env
docker-compose restart backend

# 查看詳細日誌
docker-compose logs -f backend
```

更多故障排除資訊請參考 [故障排除指南](docs/TROUBLESHOOTING.md)。

## License

This project is for demonstration purposes.
