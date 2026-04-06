# 测试平台部署指导文档

## 1. 环境要求

- Python 3.11+
- Node.js 16+
- Redis 5.0+ (远程服务器)
- MySQL 8.0+ (可选，默认使用 SQLite)
- Docker (用于运行自动化测试)

## 2. 项目结构

```
Mytest_Platform/
├── .venv/               # Python 虚拟环境
├── Django/              # Django 后端
├── frontend/            # Vue3 前端
├── automation/          # 自动化测试模块
├── test_cases/          # 测试用例管理
├── test_plans/          # 测试计划管理
├── defects/             # 缺陷管理
├── api_test/            # API 测试
├── environments/        # 环境管理
├── logs/                # 日志管理
├── users/               # 用户管理
├── utils/               # 工具类
├── manage.py            # Django 管理脚本
├── requirements.txt     # Python 依赖
├── frontend/package.json # 前端依赖
├── .env                 # 环境配置文件
├── README.md            # 项目说明
├── DEPLOYMENT.md        # 部署与启动指南
└── DEPLOYMENT_GUIDE.md  # 详细部署指导
```

## 3. 环境配置

### 3.1 配置 .env 文件

复制 `.env` 文件并修改配置：

```env
# ============================================
# Django 数据库配置 (MySQL)
# ============================================
DB_ENGINE=django.db.backends.mysql
DB_NAME=test_platform
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=192.168.3.100
DB_PORT=3306

# ============================================
# Redis 配置 (用于Celery和缓存)
# ============================================
# 资源隔离配置：
# DB 0: Django 缓存 (Cache)
# DB 1: Celery 消息代理 (Broker)
# DB 2: Celery 结果后端 (Result Backend)
REDIS_HOST=192.168.3.100
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery 配置 (使用上面的Redis配置)
CELERY_BROKER_URL=redis://192.168.3.100:6379/1
CELERY_RESULT_BACKEND=redis://192.168.3.100:6379/2

# ============================================
# Django 安全密钥 (生产环境请修改)
# ============================================
SECRET_KEY=django-insecure-8!67b^9z#^4=ps5yd-aq2!j03h)47kvxvrbqm0h*!v66&p9(pf

# ============================================
# Django 调试模式 (生产环境请设置为False)
# ============================================
DEBUG=True

# ============================================
# 允许访问的主机 (多个用逗号分隔)
# ============================================
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.3.100

# ============================================
# 管理员账号配置 (首次初始化时使用)
# ============================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
```

### 3.2 Redis 资源隔离说明

| Redis 数据库 | 用途 | 配置文件位置 |
|------------|------|------------|
| DB 0 | Django 缓存 (Cache) | `.env` 中的 `REDIS_DB` |
| DB 1 | Celery 消息代理 (Broker) | `.env` 中的 `CELERY_BROKER_URL` |
| DB 2 | Celery 结果后端 (Result Backend) | `.env` 中的 `CELERY_RESULT_BACKEND` |

## 4. 安装依赖

### 4.1 后端依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4.2 前端依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

## 5. 数据库初始化

```bash
# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 执行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

## 6. 服务启动

### 6.1 启动 Django 服务

```bash
# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 启动 Django 服务
python manage.py runserver 0.0.0.0:8000
```

### 6.2 启动 Celery 服务

```bash
# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 启动 Celery 工人 (使用 solo pool 避免 Windows 权限问题)
.venv\Scripts\python.exe -m celery -A Django worker --loglevel=info --pool=solo

# 可选：启动 Celery Beat (用于定时任务)
.venv\Scripts\python.exe -m celery -A Django beat --loglevel=info
```

### 6.3 启动前端服务

```bash
# 进入前端目录
cd frontend

# 启动前端开发服务器
npm run dev
```

## 7. 访问地址

- Django 后端：http://localhost:8000
- 前端应用：http://localhost:5173
- Django 管理后台：http://localhost:8000/admin

## 8. 常见问题

### 8.1 Redis 连接问题

- 确保远程 Redis 服务器可访问
- 检查 Redis 配置中的主机、端口和密码
- 确保 Redis 服务正在运行

### 8.2 Celery 启动问题

- 在 Windows 上使用 `--pool=solo` 参数避免权限问题
- 检查 Redis 连接配置
- 查看 Celery 日志了解具体错误

### 8.3 前端代理问题

- 确保 Django 服务正在运行
- 检查 `vite.config.js` 中的代理配置
- 确保 `ALLOWED_HOSTS` 包含前端地址

### 8.4 测试文件导入错误

- 确保测试文件中的依赖项已安装
- 检查测试文件的导入路径是否正确
- 查看 Celery 日志中的详细错误信息

### 8.5 Allure报告统计错误

- **原因**: 宿主机上的result目录包含历史执行结果
- **解决**: 系统已自动修复，现在在Docker容器中执行zip命令

## 9. 生产环境部署

### 9.1 使用 Gunicorn 运行 Django

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动 Gunicorn
gunicorn Django.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 9.2 使用 Supervisor 管理服务

```ini
# /etc/supervisor/conf.d/test_platform.conf
[program:django]
command=/path/to/venv/bin/gunicorn Django.wsgi:application --bind 0.0.0.0:8000 --workers 4
directory=/path/to/Mytest_Platform
autostart=true
autorestart=true
stderr_logfile=/var/log/django_error.log
stdout_logfile=/var/log/django.log

[program:celery_worker]
command=/path/to/venv/bin/celery -A Django worker --loglevel=info
directory=/path/to/Mytest_Platform
autostart=true
autorestart=true
stderr_logfile=/var/log/celery_worker_error.log
stdout_logfile=/var/log/celery_worker.log

[program:celery_beat]
command=/path/to/venv/bin/celery -A Django beat --loglevel=info
directory=/path/to/Mytest_Platform
autostart=true
autorestart=true
stderr_logfile=/var/log/celery_beat_error.log
stdout_logfile=/var/log/celery_beat.log
```

### 9.3 前端构建

```bash
# 进入前端目录
cd frontend

# 构建生产版本
npm run build

# 将构建结果部署到静态文件服务器
```

## 10. 服务状态检查

### 10.1 检查 Django 服务

```bash
# 检查服务是否运行
curl http://localhost:8000/api/health

# 查看日志
tail -f django.log
```

### 10.2 检查 Celery 服务

```bash
# 检查 Celery 状态
celery -A Django status

# 查看 Celery 日志
tail -f celery.log
```

### 10.3 检查前端服务

```bash
# 检查前端是否可访问
curl http://localhost:5173

# 查看前端日志
npm run dev
```

## 11. 自动化任务执行

1. 登录前端应用
2. 进入「自动化任务」页面
3. 创建或选择现有任务
4. 点击「执行」按钮
5. 查看执行历史和日志
6. 查看Allure报告

## 12. 功能说明

### 12.1 核心功能

- **用户管理**: 用户注册、登录、权限管理
- **测试用例管理**: 用例CRUD、导入导出、分类管理、时间格式化
- **测试计划管理**: 计划创建、用例分配、执行跟踪、时间格式化
- **缺陷管理**: 缺陷跟踪、状态流转、评论功能、时间格式化
- **接口测试**: API环境管理、用例执行、结果记录、响应时间格式化
- **自动化测试**: 任务管理、远程执行、Docker容器、Allure报告
- **环境管理**: 多环境配置、变量管理
- **日志管理**: 操作日志、错误日志、统计分析

### 12.2 技术特性

- **Redis资源隔离**: 使用不同的Redis数据库编号进行资源隔离
- **Docker容器**: 自动化测试在Docker容器中执行，确保环境一致性
- **Allure报告**: 生成详细的测试报告，支持图表和趋势分析
- **时间格式化**: 所有时间字段都进行了格式化，提高可读性
- **权限控制**: 基于角色的权限管理，确保数据安全

## 13. 技术栈

- **后端**: Django 4.2+, REST Framework, Celery 5.3+, scp 0.15+
- **前端**: Vue 3, Element Plus, Axios, vue-router, pinia, echarts
- **数据库**: SQLite (默认), MySQL (可选)
- **消息队列**: Redis 5.0+
- **测试框架**: Pytest 9.0+, Allure 2.15+
- **容器化**: Docker

## 14. 注意事项

- 生产环境请修改 `SECRET_KEY`
- 生产环境请设置 `DEBUG=False`
- 定期备份数据库和 Redis 数据
- 监控服务运行状态和日志
- 确保服务器安全，配置防火墙规则
- 确保远程执行机上的Docker服务正常运行
