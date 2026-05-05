# Warehouse Management System

這個版本已將原本的車隊管理展示架構，改造成「商品倉儲管理系統」第一版，對應簡報中的三個核心資料表：

- 商品主表 `products`
- 操作紀錄表 `inventory_operations`
- 門禁紀錄表 `gate_records`

## 目前已完成的功能

- 商品新增、編輯、查詢
- 商品狀態追蹤：`庫存中 / 已結帳 / 未授權離場`
- 入庫與出庫紀錄
- 門禁授權與未授權事件紀錄
- 首頁摘要儀表板
- Docker 初始化 MySQL schema 與範例資料

## 資料表對應

### products

- `tag_id`: 商品標籤 ID，主鍵
- `product_name`: 商品名稱
- `price`: 商品價格
- `status_code`: 商品狀態碼
- `last_action`: 最後操作類型
- `update_time`: 最後更新時間

### inventory_operations

- `operation_id`: 流水號，主鍵
- `tag_id`: 商品標籤 ID，外鍵
- `action`: 入庫或出庫
- `operator`: 操作者
- `timestamp`: 操作時間

### gate_records

- `gate_record_id`: 流水號，主鍵
- `tag_id`: 商品標籤 ID，外鍵
- `gate_id`: 出口閘道
- `result`: 已授權或未授權
- `timestamp`: 操作時間

## 本機執行

1. 安裝套件

```bash
pip install -r requirements.txt
```

2. 設定 MySQL 並建立資料庫

```bash
mysql -u root -p < warehouse_management.sql
```

若你的 MySQL 不在本機 `127.0.0.1:3306`，請先調整 [default_config.ini](/Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2/default_config.ini)。

你也可以直接在啟動時覆蓋連線設定，例如：

```bash
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=root MYSQL_PASSWORD=你的密碼 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5000
```

3. 啟動應用程式

```bash
CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5000
```

4. 開啟瀏覽器

```text
http://localhost:5000
```

## Docker 執行

若之前已用舊 schema 跑過，請先清空 `data/mysql` 再重新建立容器。

```bash
docker compose build
docker compose up -d
```

頁面預設在：

```text
http://localhost:5000
```

MySQL 預設對外埠：

```text
localhost:3307
```

如果 Flask 在本機虛擬環境執行、MySQL 在 Docker 裡執行，請用：

```bash
CONFIG_FILE=./local_docker_mysql.ini python manage.py runserver -h 0.0.0.0 -p 5000
```

## 後續可擴充方向

- 使用者登入與角色權限
- 商品分類、供應商、倉位管理
- 圖表報表與異常告警
- RFID/條碼硬體串接
- 交易流程與授權審核
