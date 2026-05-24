# 第五版本 E 終端機指令紀錄

這份是目前第五版本 E 可直接複製執行的最短 SOP。

## 第一次建立環境

### 1. 進入專案資料夾

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE
```

### 2. 建立 conda 環境

```bash
conda env create -f environment.yml
```

### 3. 啟用 conda 環境

```bash
conda activate warehouse-management
```

### 4. 重建第五版本 E 資料庫

```bash
mysql -u root -p -e "DROP DATABASE IF EXISTS warehouse_management; CREATE DATABASE warehouse_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p warehouse_management < warehouse_management.sql
```

### 5. 如果還沒建立專案帳號，先建立資料庫使用者

```bash
mysql -u root
```

```sql
CREATE USER 'warehouse_user'@'127.0.0.1' IDENTIFIED BY 'warehouse_pass_123';
GRANT ALL PRIVILEGES ON warehouse_management.* TO 'warehouse_user'@'127.0.0.1';
FLUSH PRIVILEGES;
exit
```

### 6. 啟動 Flask

```bash
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=warehouse_user MYSQL_PASSWORD=warehouse_pass_123 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5001
```

### 7. 開啟頁面

```text
主控台：http://localhost:5001
```

---

## 第五版本 E 最短驗證流程

1. 先建立一組物品，例如：

- 物件名稱：馬克杯
- 顏色：白色
- 數量：2

2. 在物品主表確認：

- 產生兩個不同流水號，例如 `SN-000006`、`SN-000007`
- 狀態都為 `0`

3. 把其中一個流水號送到櫃檯

4. 再把同一個流水號送去閘門

5. 確認：

- 狀態維持 `1`
- 閘門日記記成正常出貨

6. 再把另一個還是 `0` 的流水號直接送去閘門

7. 確認：

- 狀態變成 `2`
- 未授權事件增加
- 主頁未授權卡片出現 `!`

---

## 之後每次要啟動時

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE
conda activate warehouse-management
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=warehouse_user MYSQL_PASSWORD=warehouse_pass_123 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5001
```
