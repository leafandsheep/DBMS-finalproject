# 第五版本 E 操作指令

這份是版本 E 的最短操作紀錄，直接照順序貼到終端機就可以。

## 1. 平常啟動

如果 MySQL 已經在跑，平常只要貼這組：

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE
conda activate warehouse-management
/Users/thenights/miniforge3/envs/warehouse-management/bin/python -c "import os; os.chdir('/Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE'); os.environ['FLASK_CONFIG']='production'; os.environ['CONFIG_FILE']='./local_docker_mysql.ini'; from app import create_app; app = create_app('production'); app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)"
```

打開：

```text
http://127.0.0.1:5001
```

---

## 2. 如果 MySQL 沒開

先開資料庫，再開網站：

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE
docker compose up -d mysql
conda activate warehouse-management
/Users/thenights/miniforge3/envs/warehouse-management/bin/python -c "import os; os.chdir('/Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE'); os.environ['FLASK_CONFIG']='production'; os.environ['CONFIG_FILE']='./local_docker_mysql.ini'; from app import create_app; app = create_app('production'); app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)"
```

---

## 3. 如果要整個重建版本 E 資料庫

這組會把資料庫清空後重建：

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE
mysql -h 127.0.0.1 -P 3307 -u root -proot -e "DROP DATABASE IF EXISTS warehouse_management; CREATE DATABASE warehouse_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -P 3307 -u root -proot warehouse_management < warehouse_management.sql
```

重建完後再啟動網站：

```bash
conda activate warehouse-management
/Users/thenights/miniforge3/envs/warehouse-management/bin/python -c "import os; os.chdir('/Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE'); os.environ['FLASK_CONFIG']='production'; os.environ['CONFIG_FILE']='./local_docker_mysql.ini'; from app import create_app; app = create_app('production'); app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)"
```

---

## 4. 停止網站

如果網站正在終端機前景執行，直接按：

```text
Ctrl + C
```

---

## 5. 停止 MySQL

如果你想把 Docker 的 MySQL 關掉：

```bash
cd /Users/thenights/Downloads/大二所有學科/大二資料庫/資料庫專案/Fleet-Management-VersionE
docker compose stop mysql
```

---

## 6. 版本 E 最短驗證流程

種子資料已含員工（小美、阿傑、老闆）與會員（阿明 M、小花 S、大雄 L），以及商品 `SN-000001`～`SN-000007`（其中 SN-000006 鑰匙圈、SN-000007 貼紙為無尺寸配件），可直接驗證：

1. 建立一個物品：
   - 物件名稱：馬克杯、顏色：白色、尺寸：M、數量：2
   - 因為種子已用到 `SN-000007`，新建會從 `SN-000008` 起 → 記下 `SN-000008`、`SN-000009`
2. 用「會員尺寸查詢」：選店員（小美）＋ 會員（阿明，自動帶 M）→ 確認查到對應在庫件數（含無尺寸配件），並留下查詢紀錄。
3. 把 `SN-000008` 送去櫃檯：選結帳店員 ＋ 購買會員 → 狀態 `庫存中 → 已售出`。
4. 把同一個 `SN-000008` 送去閘門 → 維持 `已售出`，記為正常出貨。
5. 把另一個還是 `庫存中` 的 `SN-000009` 直接送去閘門。
6. 確認它變成 `未授權`，首頁「未授權事件」出現 `!`。
7. 點進「未授權事件」詳情頁 → `!` 消失（已讀）。
8. 順手確認櫃檯日記有店員/會員、查詢紀錄有時間、各事件時間都有顯示。
