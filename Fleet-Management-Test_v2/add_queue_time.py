import re
import csv
from datetime import datetime

# 1. 從 gateway_full.log 擷取所有 fetch time
with open('gateway_full.log', 'r', encoding='utf-8') as f:
    log_content = f.read()

pattern = r'fetch time:\s+([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:\.]+)'
fetch_times = re.findall(pattern, log_content)

# 濾掉不合法的時間字串
fetch_times_dt = []
for ft in fetch_times:
    try:
        dt = datetime.fromisoformat(ft)
        fetch_times_dt.append(dt)
    except ValueError:
        print(f'警告：跳過不合法的時間字串 {ft}')

fetch_times_dt.sort()

# 轉換成 datetime 物件並排序
fetch_times_dt = sorted([datetime.fromisoformat(ft) for ft in fetch_times], reverse=True)

print(f'共找到 {len(fetch_times_dt)} 筆 fetch time')

# 2. 讀取 experiment1_2.csv
rows = []
with open('experiment1_2.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader)  # 標題列
    rows = [row for row in reader]

# 3. 對每一列找到符合的最小 fetch time
for row in rows:
    row_time_str = row[0]
    row_time_dt = datetime.fromisoformat(row_time_str)
    
    # 找到最小的 fetch time >= row_time_dt
    matched_ft = ''
    for ft in fetch_times_dt:
        if ft <= row_time_dt:
            matched_ft = ft.isoformat()
            break
    
    row.append(matched_ft)  # 將找到的 fetch time 加到最後

# 4. 輸出新 CSV
new_header = header + ['matched_fetch_time']

with open('experiment1_2_with_fetch.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(new_header)
    writer.writerows(rows)

print(f'已成功輸出到 experiment1_2_with_fetch.csv')