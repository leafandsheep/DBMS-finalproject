# Warehouse Management System

這個專案是以 Flask + MySQL 實作的商品倉儲管理系統第一版，已從原始車隊管理架構整理成目前實際要展示的倉儲版本。

## 目前保留的核心功能

- 商品主表管理
- 入庫 / 出庫操作紀錄
- 門禁授權 / 未授權事件紀錄
- 首頁摘要儀表板
- 主題式列表頁
- MySQL schema 與範例資料初始化

## 資料表

- `products`
  - 商品主檔，包含 `tag_id`、`product_name`、`price`、`status_code`
- `inventory_operations`
  - 入庫與出庫紀錄，包含 `action`、`operator`、`timestamp`
- `gate_records`
  - 門禁事件紀錄，包含 `gate_id`、`result`、`timestamp`

## 專案結構

- `app/`
  - Flask 應用程式、API、頁面模板、資料模型
- `manage.py`
  - 啟動入口
- `warehouse_management.sql`
  - 建表與範例資料
- `default_config.ini`
  - 本機 MySQL 設定
- `docker_config.ini`
  - Docker 內部網路設定
- `local_docker_mysql.ini`
  - 本機 Flask + Docker MySQL 設定
- `TERMINAL_COMMANDS.md`
  - 可直接複製的啟動指令

## 本機啟動

1. 建立環境

```bash
conda env create -f environment.yml
conda activate warehouse-management
```

2. 匯入資料庫

```bash
mysql -u root -p < warehouse_management.sql
```

3. 啟動系統

```bash
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=warehouse_user MYSQL_PASSWORD=warehouse_pass_123 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5001
```

4. 開啟頁面

```text
http://localhost:5001
```

更完整的操作方式請直接看 [TERMINAL_COMMANDS.md](/Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2/TERMINAL_COMMANDS.md)。

## Docker 啟動

```bash
docker compose build
docker compose up -d
```

- Web: `http://localhost:5000`
- MySQL: `localhost:3307`

## 目前狀態

- 已移除舊車隊管理、實驗腳本、快取與 log 類檔案
- 保留目前倉儲系統展示所需的最小核心檔案
- 適合後續以分支和 PR 方式繼續迭代功能
