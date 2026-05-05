import re
import csv

# 讀取 log 檔
with open('gateway_full.log', 'r', encoding='utf-8') as f:
    log_content = f.read()

# 使用正則表達式找出所有 fetch time 與 msg count
# 範例：
# _deal_task: has_task fetch time:  2025-06-30T16:30:54.151652
# msg count:  4

pattern = r'fetch time:\s+([0-9\-:T\.]+)\s+msg count:\s+(\d+)'
matches = re.findall(pattern, log_content)

# 依照規則展開
result_rows = []
for fetch_time, msg_count in matches:
    count = int(msg_count)
    result_rows.extend([fetch_time] * count)

# 輸出到 CSV
with open('queue_time.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['fetch_time'])  # 欄位名稱
    for row in result_rows:
        writer.writerow([row])

print(f'已成功輸出 {len(result_rows)} 筆資料到 queue_time.csv')