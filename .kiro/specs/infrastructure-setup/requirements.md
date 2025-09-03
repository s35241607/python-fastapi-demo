# Requirements Document

## Introduction

此功能旨在建立完整的基礎建設配置，包含 Docker 容器化、環境變數管理、資料庫配置以及核心中介軟體（錯誤處理、日誌記錄、JWT 使用者資訊解析）。系統需要支援本地開發、測試和正式環境的不同配置需求。

## Requirements

### Requirement 1

**User Story:** 作為開發者，我希望能使用 Docker 和 Docker Compose 來容器化應用程式，以便在不同環境中保持一致的部署體驗。

#### Acceptance Criteria

1. WHEN 開發者執行 docker-compose up THEN 系統 SHALL 啟動所有必要的服務容器
2. WHEN 在本地環境運行 THEN 系統 SHALL 自動啟動 PostgreSQL 16 資料庫容器
3. WHEN 在測試或正式環境運行 THEN 系統 SHALL 連接到外部既有的資料庫而不啟動本地資料庫容器

### Requirement 2

**User Story:** 作為開發者，我希望能透過不同的環境變數檔案來管理各環境的配置，以便輕鬆切換開發、測試和正式環境。

#### Acceptance Criteria

1. WHEN 系統啟動 THEN 系統 SHALL 根據環境載入對應的 .env 檔案（.env.development, .env.testing, .env.production）
2. WHEN 切換環境 THEN 系統 SHALL 自動使用正確的資料庫連接設定
3. WHEN 載入環境變數 THEN 系統 SHALL 不包含 JWT key 配置（因為透過 Kong API 驗證）

### Requirement 3

**User Story:** 作為開發者，我希望系統具備完整的錯誤處理機制，以便能夠優雅地處理各種異常情況並提供有意義的錯誤回應。

#### Acceptance Criteria

1. WHEN 應用程式發生未處理的異常 THEN 系統 SHALL 捕獲異常並返回適當的 HTTP 狀態碼
2. WHEN 發生錯誤 THEN 系統 SHALL 記錄詳細的錯誤資訊到日誌中
3. WHEN 回應錯誤給客戶端 THEN 系統 SHALL 提供結構化的錯誤訊息格式

### Requirement 4

**User Story:** 作為開發者，我希望系統具備結構化的日誌記錄功能，以便能夠有效地監控和除錯應用程式。

#### Acceptance Criteria

1. WHEN 應用程式運行 THEN 系統 SHALL 將日誌以結構化格式（JSON）記錄到檔案中
2. WHEN 記錄日誌 THEN 系統 SHALL 包含時間戳、日誌等級、訊息和相關上下文資訊
3. WHEN 處理請求 THEN 系統 SHALL 記錄請求和回應的相關資訊
4. WHEN 發生錯誤 THEN 系統 SHALL 記錄完整的錯誤堆疊追蹤

### Requirement 5

**User Story:** 作為開發者，我希望系統能夠解析 JWT token 並提取使用者資訊，以便在應用程式中使用使用者身份資訊。

#### Acceptance Criteria

1. WHEN 收到包含 JWT token 的請求 THEN 系統 SHALL 解析 token 並提取使用者資訊
2. WHEN JWT token 有效 THEN 系統 SHALL 將使用者資訊注入到請求上下文中
3. WHEN JWT token 無效或過期 THEN 系統 SHALL 記錄錯誤但不阻止請求（因為驗證由 Kong 處理）
4. WHEN 沒有 JWT token THEN 系統 SHALL 繼續處理請求但不提供使用者資訊
