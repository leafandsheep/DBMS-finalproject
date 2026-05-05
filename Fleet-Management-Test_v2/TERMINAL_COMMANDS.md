# 終端機指令紀錄

這份是給你之後直接複製執行用的。
目前已驗證可用的情境：

- 你要用 `conda`
- Flask 在本機虛擬環境跑
- MySQL 也是本機跑
- 使用資料庫帳號 `warehouse_user`
- Flask 跑在 `5001`

## 第一次建立環境

### 1. 進入專案資料夾

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2
```

### 2. 建立 conda 環境

```bash
conda env create -f environment.yml
```

### 3. 啟用 conda 環境

```bash
conda activate warehouse-management
```

### 4. 建立資料庫

```bash
mysql -u root -p < warehouse_management.sql
```

### 5. 如果還沒建立專案帳號，先建立資料庫使用者

先進入 MySQL：

```bash
mysql -u root
```

再貼上：

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

### 7. 開瀏覽器

```text
http://localhost:5001
```

---

## 目前最常用的啟動方式

這組是你現在已經驗證成功的版本：

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2
conda activate warehouse-management
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=warehouse_user MYSQL_PASSWORD=warehouse_pass_123 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5001
```

---

## 之後每次要啟動時

### 1. 進入專案資料夾

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2
```

### 2. 啟用 conda 環境

```bash
conda activate warehouse-management
```

### 3. 啟動 Flask

```bash
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=warehouse_user MYSQL_PASSWORD=warehouse_pass_123 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5001
```

### 4. 開瀏覽器

```text
http://localhost:5001
```

---

## 如果你想用 Docker 跑 MySQL

### 1. 進入專案資料夾

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2
```

### 2. 啟動 MySQL 容器

```bash
docker compose up -d mysql
```

### 3. 啟用 conda 環境

```bash
conda activate warehouse-management
```

### 4. 啟動 Flask

```bash
MYSQL_USER=root MYSQL_PASSWORD=root CONFIG_FILE=./local_docker_mysql.ini python manage.py runserver -h 0.0.0.0 -p 5001
```

---

## 如果 conda env create 失敗

可以改成這組：

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2
conda create -n warehouse-management python=3.9 -y
conda activate warehouse-management
pip install -r requirements.txt
```

---

## 如果看到 Access denied for user 'root'@'localhost'

代表你本機 MySQL 的密碼不是 `root`。

先測試登入：

```bash
mysql -u root -p
```

如果你輸入的密碼不是 `root`，那就用你自己的密碼啟動 Flask：

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2
conda activate warehouse-management
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=root MYSQL_PASSWORD=你的密碼 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5001
```

---

## 如果看到 Port 5000 is in use

目前已知你的環境可以直接改用 `5001`：

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-Test_v2
conda activate warehouse-management
MYSQL_HOST=127.0.0.1 MYSQL_PORT=3306 MYSQL_USER=warehouse_user MYSQL_PASSWORD=warehouse_pass_123 DB_NAME=warehouse_management CONFIG_FILE=./default_config.ini python manage.py runserver -h 0.0.0.0 -p 5001
```
