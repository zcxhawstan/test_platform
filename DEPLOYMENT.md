# 测试平台部署指南

本文档覆盖三种部署形态，按推荐程度排序：

| 部署方式 | 适用场景 | 前置依赖 |
|---------|---------|---------|
| [Docker Compose](#方式一docker-compose-部署推荐) | 快速部署、生产环境 | Docker Engine 24+ |
| [WSL 裸机部署](#方式二wsl-裸机部署) | Windows 开发机上的长期运行 | WSL2 Ubuntu + Python 3.11 |
| [开发模式](#方式三开发模式) | 本地开发调试 | Python 3.11+ / Node 18+ |

---

## 方式一：Docker Compose 部署（推荐）

### 1.1 准备配置

```bash
cp .env.docker.example .env.docker
```

编辑 `.env.docker`，**必须**修改以下两项（占位值会导致无法启动或数据不安全）：

```bash
# 生成 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"

# 生成 ENCRYPTION_KEY（Fernet，用于执行机密码加密存储）
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

其他可调整项：`MYSQL_PASSWORD`、`ADMIN_USERNAME/PASSWORD`（初始管理员）、`WEB_PORT`（对外端口，默认 8000）。

### 1.2 启动

```bash
docker compose up -d --build
```

首次构建约 5-10 分钟（前端 npm 构建 + Python 依赖 + Allure 命令行）。容器自动完成：等数据库就绪 → `migrate` → 创建初始管理员 → 启动服务。

### 1.3 验证

```bash
docker compose ps          # 五个服务全部 Up（mysql/redis 显示 healthy）
curl -X POST http://localhost:8000/api/auth/users/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin@2026"}'   # 返回 200 + token
```

浏览器访问 `http://localhost:8000` 直接进入前端（Django 托管构建产物，无需单独起前端）。

### 1.4 服务架构

| 服务 | 说明 |
|------|------|
| web | gunicorn × 3 workers，对外 8000 |
| worker | celery worker（异步任务执行） |
| beat | celery beat（定时任务调度） |
| mysql | MySQL 8.4，数据持久化于 `mysql_data` 卷 |
| redis | Redis 7，缓存/分布式锁/消息队列 |

### 1.5 常用运维命令

```bash
docker compose logs -f web        # 看服务日志
docker compose restart web        # 重启单个服务
docker compose down               # 停止（保留数据）
docker compose down -v            # 停止并清空数据（危险）
```

### 1.6 注意事项

- **`.env.docker` 不入库**（已 gitignore），密钥丢失 = 已存的执行机密码无法解密
- 远程执行机场景：SSH 出口在 worker 容器内，执行机需允许来自容器网络的连接
- 端口冲突：宿主机 8000 被占用时改 `.env.docker` 的 `WEB_PORT`

---

## 方式二：WSL 裸机部署

适用于 Windows 开发机，用 `scripts/wsl_deploy.sh` 固化运维（实测环境：WSL2 Ubuntu 26.04）。

### 2.1 一次性初始化

```bash
# WSL 内：装系统依赖（需要 sudo）
sudo apt install -y mysql-server redis-server default-libmysqlclient-dev pkg-config openjdk-21-jre-headless

# 建库
sudo mysql -uroot -e "CREATE DATABASE test_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; \
  CREATE USER 'tpuser'@'localhost' IDENTIFIED BY 'TpUser@2026'; \
  GRANT ALL PRIVILEGES ON test_platform.* TO 'tpuser'@'localhost'; FLUSH PRIVILEGES;"

# Python 虚拟环境 + 依赖
python3.11 -m venv ~/test_platform_venv
~/test_platform_venv/bin/pip install -r requirements.txt

# 项目代码与 .env（DB_HOST=127.0.0.1，参考 .example）
# migrate + 前端构建（npm ci && npm run build，dist 由 Django 自动托管）
```

### 2.2 日常启停

```bash
# Windows 侧直接调用
wsl -d Ubuntu -- bash ~/test_platform_deploy/deploy.sh start    # 全量启动
wsl -d Ubuntu -- bash ~/test_platform_deploy/deploy.sh status   # 状态 + API 健康检查
wsl -d Ubuntu -- bash ~/test_platform_deploy/deploy.sh restart
wsl -d Ubuntu -- bash ~/test_platform_deploy/deploy.sh stop
```

WSL 完全重启后 MySQL 需要手动 `sudo` 启动一次，其余服务脚本自动拉起。

### 2.3 已知限制

WSL 无 systemd：MySQL 用 `mysqld --daemonize` 直启，Redis 用 `service` 命令。

---

## 方式三：开发模式

```bash
# 后端（Windows 本地）
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# Celery（Windows 需 --pool=solo）
python -m celery -A Django worker --loglevel=info --pool=solo

# 前端 dev server（API 自动代理到 8000）
cd frontend && npm install && npm run dev   # http://localhost:5173
```

开发模式默认 sqlite（`db.sqlite3`），无需 MySQL/Redis 即可起 Web（异步任务除外）。

---

## 环境变量说明

### 核心配置（.env / .env.docker 通用）

| 变量 | 必填 | 说明 |
|------|------|------|
| `SECRET_KEY` | 生产必填 | Django 密钥，生产（DEBUG=False）缺失直接拒绝启动 |
| `DEBUG` | 建议 False | 生产必须 False |
| `ALLOWED_HOSTS` | 生产必填 | 域名/IP 列表，禁止 `*` |
| `CORS_ALLOWED_ORIGINS` | 生产必填 | 前端来源白名单，逗号分隔 |
| `ENCRYPTION_KEY` | 必填 | Fernet 密钥，加密执行机密码等敏感字段 |
| `ADMIN_USERNAME/PASSWORD/EMAIL` | 可选 | 初始管理员（幂等创建） |

### 数据库与 Redis

| 变量 | 说明 |
|------|------|
| `DB_ENGINE` | `django.db.backends.mysql` 启用 MySQL；不设则用 sqlite |
| `DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT` | MySQL 连接信息 |
| `REDIS_HOST/PORT/PASSWORD` | Redis 连接（容器内 compose 自动注入主机名） |

### Redis 库分配（资源隔离）

| 库编号 | 用途 |
|--------|------|
| 0 | Django 缓存 + 任务分布式锁（`automation:task_lock:*`） |
| 1 | Celery 消息代理（Broker） |
| 2 | Celery 结果后端（Result Backend） |

---

## 故障排查

| 现象 | 排查 |
|------|------|
| web 容器反复重启 | `docker compose logs web` 看初始化报错；多为数据库未就绪或 SECRET_KEY 缺失 |
| 登录 401/400 | ADMIN_PASSWORD 未按 .env.docker 设置的值；或重新 up 后管理员已存在但密码变了 |
| 任务一直排队不执行 | worker 未就绪；`docker compose logs worker` 确认 celery ready；Redis 不可达时任务拒绝执行（fail-closed 设计） |
| 前端空白页 | 确认镜像构建包含 frontend/dist（多阶段构建产物）；Ctrl+F5 强刷 |
| 端口冲突 | 改 `WEB_PORT`；WSL 裸机部署与容器部署共用 8000，二选一 |
| mysqlclient 编译失败 | 缺 `default-libmysqlclient-dev pkg-config gcc`（镜像内已处理，裸机部署需自装） |
