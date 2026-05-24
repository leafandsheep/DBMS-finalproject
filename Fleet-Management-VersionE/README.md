# Warehouse Management System - Version E

這個版本是第五版本 E，核心回到單件追蹤。

## 版本 E 核心規則

- 每一件物品都有獨立流水號 `serial_number`
- 主表一定包含：
  - 物件名稱 `item_name`
  - 顏色 `color`
  - 流水號 `serial_number`
  - 狀態碼 `status_code`
- 狀態碼定義：
  - `0` = 庫存中
  - `1` = 已售出
  - `2` = 未授權
- 建立物品時狀態預設為 `0`

## 流程

### 正常流程

1. 物品先經過櫃檯
2. 櫃檯把該流水號狀態從 `0` 設成 `1`
3. 之後物品經過閘門
4. 閘門查這個流水號是否為 `1`
5. 如果是 `1`，就維持 `1` 並記錄正常出貨日記

### 異常流程

1. 物品沒有先經過櫃檯
2. 直接經過閘門
3. 閘門查到這個流水號目前是 `0`
4. 系統把狀態改成 `2`
5. 在未授權按鈕內可以查看對應的閘門日記
6. 主頁會顯示未讀驚嘆號 `!`

## 主要資料表

### `inventory_items`

物品主表。

重要欄位：

- `serial_number`
- `item_name`
- `color`
- `status_code`

### `counter_logs`

櫃檯日記，代表正常出貨前的櫃檯處理。

重要欄位：

- `counter_log_id`
- `serial_number`
- `previous_status`
- `new_status`
- `operator`
- `note`

### `gate_logs`

閘門日記，代表物品經過閘門的檢查結果。

重要欄位：

- `gate_log_id`
- `serial_number`
- `result`
- `previous_status`
- `new_status`
- `note`
- `is_unread`

## 庫存彙總

除了主表以外，版本 E 還提供一個彙總視角：

- 依據 `item_name + color` 分組
- 回報：
  - 總數
  - 庫存中數量
  - 已售出數量
  - 未授權數量

這個彙總不是獨立資料表，而是由主表 group 後即時計算。

## 啟動方式

1. 建立環境

```bash
conda env create -f environment.yml
conda activate warehouse-management
```

2. 重建資料庫

```bash
mysql -u root -p -e "DROP DATABASE IF EXISTS warehouse_management; CREATE DATABASE warehouse_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p warehouse_management < warehouse_management.sql
```

3. 啟動 Flask

```bash
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=warehouse_user MYSQL_PASSWORD=warehouse_pass_123 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5001
```

4. 開啟頁面

- 主控台：
  - `http://localhost:5001`

更完整的第五版本 E 設計說明請看：
[VERSION_E_ARCHITECTURE.md](/Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE/VERSION_E_ARCHITECTURE.md)

如果你要看 schema 圖原始碼，或貼到 `dbdiagram.io` 產生圖，請看：
[VERSION_E_SCHEMA.dbml](/Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE/VERSION_E_SCHEMA.dbml)
