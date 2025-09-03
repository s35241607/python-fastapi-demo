# 故障排除和監控指南

本文件提供常見問題的診斷和解決方案，以及系統監控的最佳實務。

## 快速診斷

### 系統健康檢查

```bash
# 檢查所有服務狀態
docker-compose ps

# 檢查應用程式健康狀態
curl http://localhost:8000/health

# 檢查 API 文件是否可用
curl http://localhost:8000/docs
```

### 日誌快速查看

```bash
# 查看所有服務日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs backend
docker-compose logs postgres

# 即時追蹤日誌
docker-compose logs -f backend
```

## 常見問題和解決方案

### 1. 容器啟動問題

#### 問題：容器無法啟動

**症狀**：

```bash
$ docker-compose up
ERROR: Service 'backend' failed to build
```

**可能原因和解決方案**：

1. **Docker 映像建構失敗**

   ```bash
   # 清理 Docker 快取並重新建構
   docker-compose build --no-cache backend

   # 檢查 Dockerfile 語法
   docker build -t test-build ./backend
   ```

2. **依賴套件安裝失敗**

   ```bash
   # 檢查 requirements.txt 或 pyproject.toml
   cd backend
   pip install -r requirements.txt
   ```

3. **權限問題**

   ```bash
   # 確保 Docker 有適當權限
   sudo docker-compose up

   # 或將使用者加入 docker 群組
   sudo usermod -aG docker $USER
   ```

#### 問題：容器啟動後立即退出

**症狀**：

```bash
$ docker-compose ps
Name    Command    State    Ports
backend   ...      Exit 1
```

**診斷步驟**：

```bash
# 查看容器退出原因
docker-compose logs backend

# 檢查容器內部狀態
docker-compose run --rm backend bash

# 手動執行啟動命令
docker-compose run --rm backend python main.py
```

### 2. 資料庫連接問題

#### 問題：無法連接到資料庫

**症狀**：

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**解決步驟**：

1. **檢查資料庫容器狀態**

   ```bash
   docker-compose ps postgres
   docker-compose logs postgres
   ```

2. **驗證資料庫連接設定**

   ```bash
   # 檢查環境變數
   docker-compose exec backend env | grep DATABASE

   # 測試資料庫連接
   docker-compose exec backend python -c "
   from app.core.config import settings
   print(settings.DATABASE_URL)
   "
   ```

3. **手動測試連接**

   ```bash
   # 從容器內測試
   docker-compose exec backend psql $DATABASE_URL -c "SELECT 1;"

   # 從主機測試
   psql -h localhost -p 5432 -U postgres -d mydb -c "SELECT 1;"
   ```

#### 問題：資料庫遷移失敗

**症狀**：

```
alembic.util.exc.CommandError: Target database is not up to date
```

**解決步驟**：

```bash
# 檢查遷移狀態
docker-compose exec backend alembic current

# 查看待執行的遷移
docker-compose exec backend alembic heads

# 強制執行遷移
docker-compose exec backend alembic upgrade head

# 如果需要重置資料庫
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
```

### 3. 應用程式錯誤

#### 問題：500 內部伺服器錯誤

**診斷步驟**：

1. **檢查應用程式日誌**

   ```bash
   # 查看結構化日誌
   docker-compose exec backend tail -f logs/app.log

   # 查看容器日誌
   docker-compose logs -f backend
   ```

2. **檢查錯誤詳情**

   ```bash
   # 啟用除錯模式
   echo "DEBUG=true" >> .env
   docker-compose restart backend
   ```

3. **測試特定端點**

   ```bash
   # 測試健康檢查
   curl -v http://localhost:8000/health

   # 測試 API 端點
   curl -v -X POST http://localhost:8000/api/v1/items \
     -H "Content-Type: application/json" \
     -d '{"name": "test"}'
   ```

#### 問題：JWT 解析錯誤

**症狀**：

```json
{
  "error": "JWTError",
  "message": "Invalid token format"
}
```

**解決步驟**：

1. **檢查 JWT token 格式**

   ```bash
   # 解碼 JWT token (不驗證簽名)
   echo "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | base64 -d
   ```

2. **檢查中介軟體日誌**

   ```bash
   grep "JWTParser" logs/app.log | tail -10
   ```

3. **測試不同的 token**

   ```bash
   # 測試有效 token
   curl -H "Authorization: Bearer valid_token" http://localhost:8000/api/v1/items

   # 測試無效 token
   curl -H "Authorization: Bearer invalid_token" http://localhost:8000/api/v1/items
   ```

### 4. 效能問題

#### 問題：回應時間過長

**診斷步驟**：

1. **檢查回應時間日誌**

   ```bash
   # 查看慢請求
   grep "duration_ms" logs/app.log | awk '$NF > 1000' | tail -10
   ```

2. **監控資源使用**

   ```bash
   # 檢查容器資源使用
   docker stats

   # 檢查系統資源
   htop
   ```

3. **資料庫效能分析**
   ```bash
   # 檢查慢查詢
   docker-compose exec postgres psql -U postgres -d mydb -c "
   SELECT query, mean_time, calls
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   "
   ```

#### 問題：記憶體使用過高

**解決步驟**：

1. **檢查記憶體洩漏**

   ```bash
   # 監控容器記憶體使用
   docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"
   ```

2. **調整容器資源限制**
   ```yaml
   # 在 docker-compose.yml 中設定
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 512M
           reservations:
             memory: 256M
   ```

### 5. 網路問題

#### 問題：服務間無法通信

**診斷步驟**：

1. **檢查網路配置**

   ```bash
   # 查看 Docker 網路
   docker network ls
   docker network inspect $(docker-compose ps -q | head -1 | xargs docker inspect --format='{{.NetworkSettings.Networks}}')
   ```

2. **測試服務連通性**

   ```bash
   # 從一個容器 ping 另一個
   docker-compose exec backend ping postgres

   # 測試端口連通性
   docker-compose exec backend nc -zv postgres 5432
   ```

#### 問題：外部無法訪問服務

**解決步驟**：

1. **檢查端口映射**

   ```bash
   # 查看端口映射
   docker-compose ps
   netstat -tlnp | grep :8000
   ```

2. **檢查防火牆設定**

   ```bash
   # Ubuntu/Debian
   sudo ufw status

   # CentOS/RHEL
   sudo firewall-cmd --list-all
   ```

## 監控和告警

### 系統監控

#### 基本監控指標

1. **服務可用性**

   ```bash
   # 健康檢查腳本
   #!/bin/bash
   if curl -f http://localhost:8000/health > /dev/null 2>&1; then
     echo "Service is healthy"
   else
     echo "Service is down" >&2
     exit 1
   fi
   ```

2. **回應時間監控**

   ```bash
   # 測量回應時間
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

   # curl-format.txt 內容：
   # time_total: %{time_total}s
   # time_connect: %{time_connect}s
   # time_starttransfer: %{time_starttransfer}s
   ```

3. **資源使用監控**
   ```bash
   # CPU 和記憶體使用
   docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
   ```

#### 日誌監控

1. **錯誤日誌監控**

   ```bash
   # 監控錯誤日誌
   tail -f logs/app.log | grep -E "(ERROR|CRITICAL)"
   ```

2. **日誌分析腳本**
   ```bash
   #!/bin/bash
   # 分析最近一小時的錯誤
   since=$(date -d '1 hour ago' --iso-8601=seconds)
   grep -E "(ERROR|CRITICAL)" logs/app.log | \
   jq -r "select(.timestamp > \"$since\") | .message" | \
   sort | uniq -c | sort -nr
   ```

### 告警設定

#### 基本告警規則

1. **服務不可用告警**

   ```bash
   # 檢查腳本 (check_service.sh)
   #!/bin/bash
   if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
     echo "CRITICAL: Service is down"
     # 發送告警通知
     # curl -X POST webhook_url -d "Service is down"
     exit 2
   fi
   ```

2. **高錯誤率告警**
   ```bash
   # 檢查錯誤率腳本
   #!/bin/bash
   error_count=$(grep -c "ERROR" logs/app.log | tail -100)
   if [ $error_count -gt 10 ]; then
     echo "WARNING: High error rate detected"
     exit 1
   fi
   ```

#### Cron 任務設定

```bash
# 編輯 crontab
crontab -e

# 每分鐘檢查服務健康狀態
* * * * * /path/to/check_service.sh

# 每 5 分鐘檢查錯誤率
*/5 * * * * /path/to/check_error_rate.sh

# 每小時清理舊日誌
0 * * * * find /path/to/logs -name "*.log" -mtime +7 -delete
```

## 效能調優

### 應用程式調優

1. **資料庫連接池**

   ```python
   # 在 config.py 中調整
   DATABASE_POOL_SIZE = 20
   DATABASE_MAX_OVERFLOW = 30
   DATABASE_POOL_TIMEOUT = 30
   ```

2. **非同步處理**
   ```python
   # 使用非同步資料庫操作
   async def get_items():
       async with get_db_session() as session:
           result = await session.execute(select(Item))
           return result.scalars().all()
   ```

### 容器調優

1. **資源限制**

   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: "1.0"
             memory: 1G
           reservations:
             cpus: "0.5"
             memory: 512M
   ```

2. **健康檢查調優**
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 60s
   ```

## 備份和災難恢復

### 資料備份

1. **資料庫備份**

   ```bash
   # 自動備份腳本
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   docker-compose exec postgres pg_dump -U postgres mydb > backup_$DATE.sql

   # 壓縮備份
   gzip backup_$DATE.sql

   # 清理舊備份 (保留 7 天)
   find . -name "backup_*.sql.gz" -mtime +7 -delete
   ```

2. **應用程式資料備份**

   ```bash
   # 備份日誌檔案
   tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

   # 備份配置檔案
   tar -czf config_backup_$(date +%Y%m%d).tar.gz .env* docker-compose*
   ```

### 災難恢復

1. **快速恢復步驟**

   ```bash
   # 1. 停止所有服務
   docker-compose down

   # 2. 恢復資料庫
   docker-compose up -d postgres
   docker-compose exec -T postgres psql -U postgres -d mydb < backup.sql

   # 3. 重新啟動應用程式
   docker-compose up -d
   ```

2. **驗證恢復**

   ```bash
   # 檢查服務狀態
   docker-compose ps

   # 測試 API 功能
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v1/items
   ```

## 安全性監控

### 安全檢查

1. **容器安全掃描**

   ```bash
   # 使用 Docker Scout 掃描
   docker scout cves backend:latest

   # 使用 Trivy 掃描
   trivy image backend:latest
   ```

2. **日誌安全分析**

   ```bash
   # 檢查可疑活動
   grep -E "(401|403|404)" logs/app.log | tail -20

   # 檢查異常請求
   grep -E "POST|PUT|DELETE" logs/app.log | grep -v "200\|201\|204"
   ```

### 安全告警

```bash
# 檢查異常登入嘗試
#!/bin/bash
failed_attempts=$(grep "401" logs/app.log | wc -l)
if [ $failed_attempts -gt 50 ]; then
  echo "SECURITY ALERT: High number of failed authentication attempts"
  # 發送安全告警
fi
```

## 聯絡支援

如果問題仍無法解決，請提供以下資訊：

1. **系統資訊**

   ```bash
   # 收集系統資訊
   docker --version
   docker-compose --version
   uname -a
   ```

2. **服務狀態**

   ```bash
   docker-compose ps
   docker-compose logs --tail=50
   ```

3. **配置資訊**

   ```bash
   # 移除敏感資訊後提供
   cat .env | sed 's/PASSWORD=.*/PASSWORD=***/'
   ```

4. **錯誤日誌**
   ```bash
   # 最近的錯誤日誌
   grep -E "(ERROR|CRITICAL)" logs/app.log | tail -20
   ```
