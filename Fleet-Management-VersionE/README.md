# Warehouse Management System｜第五版本 E（最終版）

單件流水號倉庫系統，加入**員工、會員、尺寸與查詢紀錄**的零售門市 + RFID 防盜情境。

> 想快速了解整個專案，先看 **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)**。

## 核心特色

- 每件商品都有獨立流水號（`SN-000001`…）與尺寸
- 狀態碼：`0` 庫存中 → `1` 已售出 → `2` 未授權
- 店員（員工）替會員查「有沒有他尺寸的商品」，留下查詢紀錄
- 結帳記錄「哪位店員賣給哪位會員」
- 閘門自動判定正常 / 未授權，未授權維持不歸屬到人
- 每個事件（結帳 / 閘門 / 查詢）都有時間
- 庫存彙總依「名稱＋顏色＋尺寸」即時分組計算

## 6 張資料表

`employees`、`customers`、`inventory_items`、`counter_logs`、`gate_logs`、`search_logs`

完整設計（所有 schema、ER 圖、使用場景、所有可能情境）請看：
👉 **[VERSION_E_ARCHITECTURE.md](./VERSION_E_ARCHITECTURE.md)**

## 快速啟動（本機 Docker MySQL，port 3307）

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE

# 1. 啟動 MySQL（Docker）
docker compose up -d mysql        # 第一次；之後用 docker start warehouse_mysql

# 2. 重建資料庫
mysql -h 127.0.0.1 -P 3307 -u root -proot -e "DROP DATABASE IF EXISTS warehouse_management; CREATE DATABASE warehouse_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -P 3307 -u root -proot warehouse_management < warehouse_management.sql

# 3. 啟動 Flask
conda activate warehouse-management
FLASK_CONFIG=production CONFIG_FILE=./local_docker_mysql.ini \
  python -c "from app import create_app; create_app('production').run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)"
```

開啟 http://127.0.0.1:5001

> 註：API 都掛在 `/api/v1.0` 前綴下（例如 `/api/v1.0/summary`）。完整端點清單見 [VERSION_E_ARCHITECTURE.md](./VERSION_E_ARCHITECTURE.md) 第七節。

更詳細、可直接複製的指令請看 [VERSION_E_OPERATION_COMMANDS.md](./VERSION_E_OPERATION_COMMANDS.md)。
