SQL檔有更新時須先將data資料夾內資料清空
若在linux上執行須注意port不能與本機已安裝服務相衝
目前使用綁定掛載直接使用本機的目錄，可能需要調整權限。日後若有需要可改為產生volume
防火牆問題用sudo ufw allow 3306
新增新gateway時需要於mqtt_gateway資料表中註冊，快速插入1~n語法如下：
docker exec -it iot_mysql_server mysql -uroot -proot
INSERT INTO fleet_server.mqtt_gateway (gateway_mac_address, gateway_name, gateway_status)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 10
)
SELECT CONCAT('gw-', LPAD(n, 3, '0')), "test", 2
FROM seq;
INSERT INTO fleet_gateway.mqtt_gateway (gateway_mac_address, gateway_name, gateway_status)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 10
)
SELECT CONCAT('gw-', LPAD(n, 3, '0')), "test", 2
FROM seq;
本機測試多個gateway用python gen_compose_and_configs_with_sql.py 2 --start-mysql-port 3400 --start-redis-port 6500 --expose-ports
多個測試時以docker rm -f $(docker ps -aq)和docker compose down -v停止


筆記：
會改到msg_log的函式：
deal_message：接到ack訊息時把原need_ack訊息改為已完成，原is_need_ack訊息timestamp改為接到ack的時間
_send_message：撈mqtt_msg待傳訊息時，根據待傳訊息is_need_ack更新mqtt_msg_log對應訊息status，需要ack改為等待ack，不需要ack改為done，將message_timestamp改為傳送訊息的時間，(已新增可選：不需要ack的message_timestamp不更新)
_resend_message：撈mqtt_msg待回傳訊息時，將resend_times改為這一次傳出的重傳次數，(已註解：將message_timestamp改為重新傳送訊息的時間)

實驗一：
發送端為gateway
message_timestamp是發送時間，timestamp是接收時間，兩者相減是延遲時間
發送端更改generate_position中的total_message，點擊網頁上的持續發送後到發送端 (1+2+3+4) 資料庫看資料
開啟update_payload_and_timestamp_in_message_log把ack時間改為原訊息時間
_send_message中傳ack訊息將update_message_log改為update_message_log_without_payload_timestamp
_send_message傳ack訊息後更新message_log前把payload改回來
雙向往返時間：
為確保時鐘沒有誤差，收發在同一台機器上
發送頻率要降低，不然高機率寫不進資料表
接收端_mqtt_on_message中開啟立即回傳機制
發送端deal_message中開啟update_done_message_in_message_log_only_timestamp與立即return記錄回傳時間
發送端deal_message中更改為update_done_message_in_message_log_no_timestamp讓ack訊息不更改回傳時間
發送端執行experiment1-2.py可產生1+2延遲表
延遲表時間除以2就是單向傳輸時間

docker logs iot_gateway > gateway_full.log 2>&1
python manage.py runserver -h 0.0.0.0 -p 5000 2>&1 | tee gateway_full.log

實驗二：
發送端為gateway
發送端更改generate_position中的迴圈time.sleep控制寫入頻率
以實驗一作法得到結果

實驗三：
設定drop_rate模擬封包遺失率
開啟_mqtt_on_message的封包遺失模擬
發送端執行experiment2.py取得總花費時間及重傳次數
關閉_send_message的print("fetch time")

雙Deamon：
開啟resend_message_scheduler的resume和start
開啟_resend_message的print("fetch time")

單Deamon：
關閉resend_message_scheduler的resume和start
開啟_send_message中resend機制

Docker指令：
docker compose build
docker compose up -d server mysql redis
docker compose down
docker compose down -v

docker compose ps
docker compose ps -a
docker compose logs -f server

docker stop iot_server
docker kill iot_server

docker exec -it iot_mysql mysql -uroot -proot
docker exec -it iot_mysql bash
mysql -uroot -proot
USE fleet_server;
USE fleet_gateway;

SELECT * FROM mqtt_message_log LIMIT 10;
SELECT count(*) FROM mqtt_message_log;
TRUNCATE TABLE mqtt_message;
TRUNCATE TABLE mqtt_message_log;
TRUNCATE TABLE mqtt_task;
TRUNCATE TABLE mqtt_task_log;

exit

docker exec -it iot_mysql mysql -uroot -proot
USE fleet_server;
TRUNCATE TABLE mqtt_message;
TRUNCATE TABLE mqtt_message_log;
TRUNCATE TABLE mqtt_task;
TRUNCATE TABLE mqtt_task_log;
exit

docker exec -it iot_mysql mysql -uroot -proot
USE fleet_gateway;
TRUNCATE TABLE mqtt_message;
TRUNCATE TABLE mqtt_message_log;
TRUNCATE TABLE mqtt_task;
TRUNCATE TABLE mqtt_task_log;
exit

待解決：
等待資料庫可連線再啟動gw程式

linux架設流程：
sudo apt update && sudo apt upgrade -y
sudo apt install git -y
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker version
docker run hello-world
sudo apt install docker-compose-plugin -y
<!-- sudo apt install ntp -y
sudo systemctl enable ntp
sudo systemctl start ntp -->
git clone https://github.com/A21941205/GW.git
cd GW/Fleet-Management-Test_v2
docker compose build
sudo rm -rf ./data
docker compose up -d gateway mysql redis
docker compose down -v

linux安裝python及套件流程：
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
cd /usr/src
sudo wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz
sudo tar xzf Python-3.9.18.tgz
cd Python-3.9.18
sudo ./configure --enable-optimizations
sudo make -j$(nproc)
sudo make altinstall
python3.9 --version
python3.9 -m ensurepip
python3.9 -m pip install --upgrade pip
sudo apt install default-libmysqlclient-dev -y
python3.9 -m pip install -r /home/pi5-a/GW/Fleet-Management-Test_v2/requirements.txt

docker exec -it iot_gateway python -c "from datetime import datetime; print(datetime.now())"

linux安裝MySQL與Redis流程：
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo mysql_secure_installation
密碼設root，全選Yes
mysql -u root -p < fleet_server.sql
mysql -u root -p < fleet_gateway.sql

sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
redis-cli ping

部分作業系統無法安裝MySQL：
sudo apt update
sudo apt install mariadb-server mariadb-client
sudo systemctl start mariadb
sudo systemctl enable mariadb
sudo mysql_secure_installation
grep -n utf8mb4_0900_ai_ci fleet_server.sql
sed -i 's/utf8mb4_0900_ai_ci/utf8mb4_general_ci/g' fleet_server.sql
grep -n utf8mb4_0900_ai_ci fleet_gateway.sql
sed -i 's/utf8mb4_0900_ai_ci/utf8mb4_general_ci/g' fleet_gateway.sql
mysql -u root -p < fleet_server.sql
mysql -u root -p < fleet_gateway.sql

原始架構：
調整server_config.ini和gateway_config.ini中MYSQL_HOST=localhost
若Redis有密碼則新增redis_password = os.getenv('REDIS_PASSWORD', None)和redis.Redis(host=redis_host, port=redis_port, password=redis_password)
執行方式：
Windows：
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:REDIS_PASSWORD = ""
$env:CONFIG_FILE = "./server_config.ini"

python manage.py runserver -h 0.0.0.0 -p 5000

Linux:
REDIS_HOST=localhost REDIS_PORT=6379 CONFIG_FILE=./gateway_config.ini python manage.py runserver -h 0.0.0.0 -p 5000