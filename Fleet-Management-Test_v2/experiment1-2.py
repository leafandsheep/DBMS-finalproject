import pymysql
import pandas as pd

# 連線設定（若 MySQL 在 Docker 容器內，host 可設為 '127.0.0.1' 並設定 port 對應）
connection = pymysql.connect(
    host='127.0.0.1',     
    # port=3307,
    port=3410,
    user='root',
    password='root',
    database='fleet_gateway',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# SQL 查詢
query = """
SELECT 
  JSON_UNQUOTE(JSON_EXTRACT(payload, '$.header.message_timestamp')) AS message_timestamp,
  DATE_FORMAT(`timestamp`, '%Y-%m-%dT%H:%i:%s.%f') AS timestamp_iso,
  TIMESTAMPDIFF(MICROSECOND, 
    CAST(JSON_UNQUOTE(JSON_EXTRACT(payload, '$.header.message_timestamp')) AS DATETIME(6)),
    `timestamp`) AS diff_microseconds
FROM mqtt_message_log;
"""

try:
    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    df = pd.DataFrame(result, dtype=str)
    # df.to_csv(r'.\experiment1_2.csv', index=False, encoding='utf-8')
    df.to_csv(r'.\experiment_addi_10.csv', index=False, encoding='utf-8')
    print("資料已正確匯出到 experiment_addi_1.csv")
    # print(df)

finally:
    connection.close()