FROM python:3.9-slim

WORKDIR /app

# 複製並安裝相依套件
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y gcc default-libmysqlclient-dev && \
    pip install --upgrade pip &&\
    pip install -r requirements.txt

# 複製專案程式碼
COPY . .

# 容器啟動指令
CMD ["python", "-u", "manage.py", "runserver", "-h", "0.0.0.0", "-p", "5000"]