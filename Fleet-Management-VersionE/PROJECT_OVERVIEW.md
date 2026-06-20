# 📦 單件流水號倉庫系統｜專案完整介紹

> 第五版本 E（最終版）。本文是給新人 / 報告用的整體導覽；
> 完整 schema、ER 圖、所有情境與 API 清單請看 [VERSION_E_ARCHITECTURE.md](./VERSION_E_ARCHITECTURE.md)。

---

## 一、這是什麼系統

模擬一間 **「會員制 ＋ RFID 防盜」的零售門市後台**。核心是「單件追蹤」——每一件實體商品都有自己的流水號，系統能回答三個問題：

1. 這件商品現在是 **庫存中 / 已售出 / 未授權**？
2. 是 **哪位店員** 賣給 **哪位會員** 的？
3. 店員替會員 **查過哪些尺寸**、什麼時候查的、找到幾件？

**操作者只有店員（員工）**；會員是被服務、被結帳的對象，不碰系統；閘門是防盜關卡，自動判定，不歸咎到人。

---

## 二、三個實體 ＋ 三個事件（6 張表）

| 實體 | 說明 |
|---|---|
| `employees` 員工 | 只記姓名（無種類 / 角色） |
| `customers` 會員 | 有單一慣用尺寸 |
| `inventory_items` 商品 | 流水號為主鍵，**尺寸可空**（配件免填） |

| 事件 | 說明 |
|---|---|
| `counter_logs` 櫃檯日記 | 結帳：記店員 ＋ 會員（都必填）＋ 時間 |
| `gate_logs` 閘門日記 | 防盜：authorized / unauthorized ＋ 未讀旗標 ＋ 時間 |
| `search_logs` 查詢紀錄 | 店員替會員查尺寸：記店員 ＋ 會員 ＋ 尺寸 ＋ 件數 ＋ 時間 |

> 「庫存彙總」不是資料表，而是依 `名稱 + 顏色 + 尺寸` 即時 GROUP BY 計算出來的。

### 關係（ER 概念）

```
employees 1 ──< counter_logs    (店員結帳)
employees 1 ──< search_logs     (店員查詢)
customers 1 ──< counter_logs    (會員購買)
customers 1 ──< search_logs     (會員被服務)
inventory_items 1 ──< counter_logs
inventory_items 1 ──< gate_logs
```

---

## 三、狀態機（一件商品的一生）

```
建立 → 0 庫存中 ──櫃檯結帳──→ 1 已售出 ──過閘門──→ 維持 1（正常出貨）
                  │
                  └─（沒結帳就過閘門）──→ 2 未授權（異常出貨，首頁亮 !）
```

- **正常流程**：櫃檯把狀態 0 → 1；閘門看到 1 → 判定 `authorized`，維持 1。
- **異常流程**：商品還是 0 卻直接過閘門 → 改成 2、寫未授權日記、`is_unread = true`、首頁「未授權事件」亮 `!`；店員點進詳情頁後未讀自動清除，`!` 消失。

---

## 四、本版的設計重點

1. **員工**：結帳記「哪位店員」（從自由輸入文字升級成 FK 實體）。
2. **會員 ＋ 尺寸查詢**：選會員自動帶入慣用尺寸 → 查在庫 → 留下查詢紀錄。
3. **尺寸是選填屬性**：配件（鑰匙圈、貼紙）沒有尺寸；查詢指定尺寸時，無尺寸的配件**不會被排除**，留空則回報所有在庫件數。
4. **時間**：結帳 / 閘門 / 查詢每個事件都記錄並顯示時間。
5. **閘門不記人**：未授權是商品本身觸發的，不歸咎到任何員工。

---

## 五、典型操作旅程

1. 開店前：建立員工（小美）、會員（阿明，慣用 M）、商品（馬克杯 / 白色 / M / 數量 2）。
2. 會員阿明來店問「有沒有我的尺寸」→ 店員用「會員尺寸查詢」（選小美 ＋ 阿明，自動帶 M）→ 查到在庫件數，留下查詢紀錄。
3. 阿明決定購買 → 店員在「櫃檯正常出貨」結帳（流水號 ＋ 店員 ＋ 會員）→ 狀態 0 → 1。
4. 阿明帶商品出閘門 → 狀態是 1 → 判定正常出貨。
5. 若有人想把未結帳商品帶出門 → 閘門判定未授權，首頁亮 `!`。

---

## 六、技術與啟動

- **後端**：Flask ＋ SQLAlchemy；**資料庫**：MySQL 8（Docker，port 3307）。
- **API**：全部掛在 `/api/v1.0` 前綴下（例：`/api/v1.0/summary`）。
- **前端**：單頁 Bootstrap 介面 ＋ 各統計卡片的詳情頁。

```bash
docker start warehouse_mysql        # 啟動 MySQL
# 重建資料庫：
mysql -h 127.0.0.1 -P 3307 -u root -proot warehouse_management < warehouse_management.sql
# 啟動網站：
conda activate warehouse-management
FLASK_CONFIG=production CONFIG_FILE=./local_docker_mysql.ini \
  python -c "from app import create_app; create_app('production').run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)"
# 開 http://127.0.0.1:5001
```

完整指令見 [VERSION_E_OPERATION_COMMANDS.md](./VERSION_E_OPERATION_COMMANDS.md)。

---

## 七、文件地圖

| 檔案 | 內容 |
|---|---|
| `PROJECT_OVERVIEW.md` | 本檔，整體導覽 |
| `VERSION_E_ARCHITECTURE.md` | 完整 schema、ER 圖、使用場景、所有情境、API 端點總覽 |
| `VERSION_E_SCHEMA.dbml` | schema 原始碼（可貼到 dbdiagram.io 產生關聯圖） |
| `warehouse_management.sql` | 建表與種子資料 |
| `VERSION_E_OPERATION_COMMANDS.md` | 可直接複製的操作指令與驗證流程 |
| `README.md` | 快速入口 |
