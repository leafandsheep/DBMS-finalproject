#!/usr/bin/env python3
"""
Generate docker-compose.generated.yml and per-gateway config files,
and ensure each MySQL container has fleet_server.sql and fleet_gateway.sql mounted.

Usage:
    python gen_compose_and_configs_with_sql.py N [--expose-ports] [--start-mysql-port START] [--start-redis-port START]

Example:
    python gen_compose_and_configs_with_sql.py 10
"""
import os
import sys
import argparse
from pathlib import Path

TEMPLATE_GATEWAY_INI = """[default]
ROLE=Gateway
SERVER_ID={SERVER_ID}
GATEWAY_ID={GATEWAY_ID}
GATEWAY_SN={GATEWAY_SN}
BROKER_HOST={BROKER_HOST}
RUN_ENV=flask
DELIVER_WAY=Ethernet
MYSQL_HOST={MYSQL_HOST}
MYSQL_PORT={MYSQL_PORT}
MYSQL_USER={MYSQL_USER}
MYSQL_PASSWORD={MYSQL_PASSWORD}
DB_NAME={DB_NAME}
"""

TEMPLATE_SERVER_INI = """[default]
ROLE=Server
SERVER_ID={SERVER_ID}
GATEWAY_ID={GATEWAY_ID}
GATEWAY_SN={GATEWAY_SN}
BROKER_HOST={BROKER_HOST}
RUN_ENV=flask
DELIVER_WAY=Ethernet
MYSQL_HOST={MYSQL_HOST}
MYSQL_PORT={MYSQL_PORT}
MYSQL_USER={MYSQL_USER}
MYSQL_PASSWORD={MYSQL_PASSWORD}
DB_NAME={DB_NAME}
"""

PLACEHOLDER_SQL = """-- placeholder SQL for {name}
-- Please replace this file with your actual SQL (fleet_server.sql or fleet_gateway.sql)
"""

def mkdir_p(p):
    os.makedirs(p, exist_ok=True)

def copy_or_create_sql(base_name, dest_path):
    """
    If root/base_name exists (e.g., fleet_server.sql), copy it to dest_path.
    Otherwise create a placeholder file at dest_path.
    """
    src = Path(base_name)
    if src.exists():
        with open(src, "rb") as fr, open(dest_path, "wb") as fw:
            fw.write(fr.read())
    else:
        # create placeholder
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(PLACEHOLDER_SQL.format(name=base_name))

def generate_compose(n, expose_ports=False, start_mysql_port=3307, start_redis_port=6380, start_gateway_port=5001):
    services = []

    # Shared server block + its mysql/redis (server keeps its own mysql/redis)
    server_block = f"""  server:
    build: .
    container_name: iot_server
    ports:
      - "5000:5000"
    environment:
      - CONFIG_FILE=/app/server_config.ini
      - REDIS_HOST=iot_redis_server
      - REDIS_PORT=6379
    depends_on:
      - iot_mysql_server
      - iot_redis_server
    volumes:
      - ./configs/server_config.ini:/app/server_config.ini:ro
"""
    services.append(server_block)

    mysql_server_block = f"""  iot_mysql_server:
    image: mysql:8.0
    container_name: iot_mysql_server
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: fleet_server
    volumes:
      - ./data/mysql_server:/var/lib/mysql
      - ./init_sql/fleet_server_server.sql:/docker-entrypoint-initdb.d/fleet_server.sql:ro
      - ./init_sql/fleet_gateway_server.sql:/docker-entrypoint-initdb.d/fleet_gateway.sql:ro
    ports:
      - "{start_mysql_port}:3306"
"""
    redis_server_block = f"""  iot_redis_server:
    image: redis:7
    container_name: iot_redis_server
    restart: always
    volumes:
      - ./data/redis_server:/data
    ports:
      - "{start_redis_port}:6379"
"""
    services.append(mysql_server_block)
    services.append(redis_server_block)

    for i in range(1, n+1):
        idx = str(i)
        # mysql: mount two init sql files (fleet_server + fleet_gateway) per mysql container
        mysql_service = f"""  iot_mysql_{idx}:
    image: mysql:8.0
    container_name: iot_mysql_{idx}
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: fleet_gateway
    volumes:
      - ./data/mysql_{idx}:/var/lib/mysql
      - ./init_sql/fleet_server_{idx}.sql:/docker-entrypoint-initdb.d/fleet_server.sql:ro
      - ./init_sql/fleet_gateway_{idx}.sql:/docker-entrypoint-initdb.d/fleet_gateway.sql:ro
"""
        if expose_ports:
            host_mysql_port = start_mysql_port + i
            mysql_service += f'    ports:\n      - "{host_mysql_port}:3306"\n'

        redis_service = f"""  iot_redis_{idx}:
    image: redis:7
    container_name: iot_redis_{idx}
    restart: always
    volumes:
      - ./data/redis_{idx}:/data
"""
        if expose_ports:
            host_redis_port = start_redis_port + i
            redis_service += f'    ports:\n      - "{host_redis_port}:6379"\n'

        host_gateway_port = start_gateway_port + (i - 1)
        gateway_service = f"""  iot_gateway_{idx}:
    build: .
    container_name: iot_gateway_{idx}
    environment:
      - CONFIG_FILE=/app/gateway_config.ini
      - REDIS_HOST=iot_redis_{idx}
      - REDIS_PORT=6379
      - MYSQL_HOST=iot_mysql_{idx}
      - MYSQL_PORT=3306
      - MYSQL_USER=root
      - MYSQL_PASSWORD=root
      - DB_NAME=fleet_gateway
      - GATEWAY_ID=gw-{idx.zfill(3)}
      - GATEWAY_SN={idx}
    depends_on:
      - iot_mysql_{idx}
      - iot_redis_{idx}
    volumes:
      - ./configs/gateway_config_{idx}.ini:/app/gateway_config.ini:ro
    ports:
      - "{host_gateway_port}:5000"
"""
        services.append(mysql_service)
        services.append(redis_service)
        services.append(gateway_service)

    header = "services:\n"
    compose_content = header + "\n".join(services)
    return compose_content

def generate_configs_and_sql(n, server_info=None):
    mkdir_p("configs")
    mkdir_p("data")
    mkdir_p("init_sql")
    mkdir_p("data/mysql_server")
    mkdir_p("data/redis_server")

    # server config
    server_cfg = TEMPLATE_SERVER_INI.format(
        SERVER_ID=server_info.get('SERVER_ID','140.116.39.174'),
        GATEWAY_ID=server_info.get('GATEWAY_ID','.'),
        GATEWAY_SN=server_info.get('GATEWAY_SN','1'),
        BROKER_HOST=server_info.get('BROKER_HOST','140.116.39.171'),
        MYSQL_HOST='iot_mysql_server',
        MYSQL_PORT='3306',
        MYSQL_USER='root',
        MYSQL_PASSWORD='root',
        DB_NAME='fleet_server'
    )
    with open("configs/server_config.ini","w",encoding="utf-8") as f:
        f.write(server_cfg)

    # prepare base SQL files in project root (optional)
    # If user has fleet_server.sql / fleet_gateway.sql in project root, use them as template.
    base_server_sql = Path("fleet_server.sql")
    base_gateway_sql = Path("fleet_gateway.sql")

    # create per-gateway config and per-mysql init_sql + data dirs
    for i in range(1, n+1):
        idx = str(i)
        cfg = TEMPLATE_GATEWAY_INI.format(
            SERVER_ID=server_info.get('SERVER_ID','140.116.39.174'),
            GATEWAY_ID=f"gw-{idx.zfill(3)}",
            GATEWAY_SN=idx,
            BROKER_HOST=server_info.get('BROKER_HOST','140.116.39.171'),
            MYSQL_HOST=f"iot_mysql_{idx}",
            MYSQL_PORT='3306',
            MYSQL_USER='root',
            MYSQL_PASSWORD='root',
            DB_NAME=f"fleet_gateway"
        )
        cfg_path = Path("configs") / f"gateway_config_{idx}.ini"
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(cfg)

        # init sql files: for each mysql, create fleet_server_{i}.sql and fleet_gateway_{i}.sql
        dest_server_sql = Path("init_sql") / f"fleet_server_{idx}.sql"
        dest_gateway_sql = Path("init_sql") / f"fleet_gateway_{idx}.sql"

        # copy from root if exists, else create placeholder
        copy_or_create_sql("fleet_server.sql", dest_server_sql)
        copy_or_create_sql("fleet_gateway.sql", dest_gateway_sql)

        # create data dirs
        mkdir_p(os.path.join("data", f"mysql_{idx}"))
        mkdir_p(os.path.join("data", f"redis_{idx}"))

    # For server's mysql init sql, also prepare copies (server specific names)
    copy_or_create_sql("fleet_server.sql", Path("init_sql") / "fleet_server_server.sql")
    copy_or_create_sql("fleet_gateway.sql", Path("init_sql") / "fleet_gateway_server.sql")

    print(f"Generated {n} gateway config files in ./configs and init_sql for each mysql under ./init_sql")

def main():
    parser = argparse.ArgumentParser(description="Generate docker-compose and configs for multiple gateways (each with independent MySQL/Redis). Each MySQL will receive fleet_server.sql and fleet_gateway.sql.")
    parser.add_argument("n", type=int, help="Number of gateways to generate")
    parser.add_argument("--expose-ports", action="store_true", help="Expose each mysql/redis to host (be careful with port conflicts)")
    parser.add_argument("--start-mysql-port", type=int, default=3307, help="Start port for server mysql (default 3307) and used as base for gateways")
    parser.add_argument("--start-redis-port", type=int, default=6380, help="Start port for server redis (default 6380) and used as base for gateways")
    parser.add_argument("--start-gateway-port", type=int, default=5001, help="Start host port for gateways (gateway1 -> start-gateway-port:5000). Default=5001")
    args = parser.parse_args()

    n = args.n
    expose_ports = args.expose_ports
    start_mysql_port = args.start_mysql_port
    start_redis_port = args.start_redis_port
    start_gateway_port = args.start_gateway_port

    print(f"Generating docker-compose with {n} gateways (gateway ports start at {start_gateway_port}, expose_ports={expose_ports}) ...")
    compose_content = generate_compose(n, expose_ports=expose_ports, start_mysql_port=start_mysql_port, start_redis_port=start_redis_port, start_gateway_port=start_gateway_port)
    with open("docker-compose.generated.yml","w",encoding="utf-8") as f:
        f.write(compose_content)
    print("Wrote docker-compose.generated.yml")

    server_info = {
        'SERVER_ID':'140.116.39.174',
        'BROKER_HOST':'140.116.39.171',
        'GATEWAY_ID':'.',
        'GATEWAY_SN':'1'
    }
    generate_configs_and_sql(n, server_info=server_info)
    print("Done. You can now run:")
    print("  docker compose -f docker-compose.generated.yml up -d")
    print("")
    print("Notes:")
    print("- Each MySQL container will have two init SQL files mounted: fleet_server.sql and fleet_gateway.sql (unique copies per container).")
    print("- Ensure your fleet_server.sql and fleet_gateway.sql (if you have real ones) are located in project root before running this script so they are copied into each init_sql/* file.")
    print("- If you don't have the real SQL files, placeholder files were created; replace them with your actual SQL before starting containers.")
    print("- If exposing many host ports, watch for collisions and port range limits.")
    print("- MySQL will execute any .sql in /docker-entrypoint-initdb.d only on first initialisation of an empty data dir. If data dir already contains DB files, init SQL won't run again.")
    
if __name__ == "__main__":
    main()