# 测试平台部署与启动指南

## 1. 环境配置

### 1.1 配置文件
- **文件**: `.env`
- **位置**: 项目根目录
- **用途**: 存储环境变量配置

### 1.2 Redis资源隔离配置

测试平台使用Redis进行资源隔离，通过不同的数据库编号实现：

| 数据库编号 | 用途 | 配置项 |
|---------|------|--------|
| 0 | Django缓存 (Cache) | `CACHES` 配置 |
| 1 | Celery消息代理 (Broker) | `CELERY_BROKER_URL` 配置 |
| 2 | Celery结果后端 (Result Backend) | `CELERY_RESULT_BACKEND` 配置 |

### 1.3 配置示例

```env
# Redis 配置
REDIS_HOST=192.168.3.100
REDIS_PORT=6379
REDIS_PASSWORD=

# Celery 配置 (使用上面的Redis配置)
CELERY_BROKER_URL=redis://192.168.3.100:6379/1
CELERY_RESULT_BACKEND=redis://192.168.3.100:6379/2
```

## 2. 服务启动

### 2.1 后端服务启动

#### 2.1.1 激活虚拟环境
```powershell
.venv\Scripts\Activate.ps1
```

#### 2.1.2 启动Django服务
```powershell
python manage.py runserver
```
- **默认地址**: http://127.0.0.1:8000

#### 2.1.3 启动Celery Worker
```powershell
celery -A Django worker -l info
```
- **注意**: Celery worker会自动读取Django配置中的`CELERY_BROKER_URL`和`CELERY_RESULT_BACKEND`设置
- **验证**: 启动时应显示连接到正确的Redis数据库

### 2.2 前端服务启动

#### 2.2.1 进入前端目录
```powershell
cd frontend
```

#### 2.2.2 启动前端服务
```powershell
npm run dev
```
- **默认地址**: http://localhost:5173

## 3. 验证方法

### 3.1 检查Redis连接
```powershell
python -c "import redis; r = redis.Redis(host='192.168.3.100', port=6379, db=1); print('Redis Broker connection:', r.ping())"
python -c "import redis; r = redis.Redis(host='192.168.3.100', port=6379, db=2); print('Redis Result Backend connection:', r.ping())"
```

### 3.2 检查Celery Worker状态
- 启动Celery worker后，查看日志输出，确认：
  - 连接到正确的Redis地址和数据库
  - 成功注册了自动化任务
  - 没有错误信息

### 3.3 测试任务执行
1. 通过前端界面或API创建并执行自动化测试任务
2. 检查Celery worker日志，确认任务被接收和执行
3. 检查执行历史，确认任务执行记录被创建

## 4. 故障排除

### 4.1 常见问题

#### 4.1.1 Celery Worker无法接收到任务
- **原因**: Redis连接问题或数据库编号配置错误
- **解决**: 
  - 检查Redis服务是否正常运行
  - 验证`CELERY_BROKER_URL`配置是否正确
  - 重启Celery worker

#### 4.1.2 任务执行失败
- **原因**: 测试文件不存在或导入错误
- **解决**: 
  - 检查测试文件路径是否正确
  - 确保测试文件语法正确
  - 检查依赖是否安装

#### 4.1.3 Redis权限错误
- **原因**: Windows系统权限限制
- **解决**: 
  - 以管理员身份运行终端
  - 检查Redis服务权限设置

### 4.2 日志查看

#### 4.2.1 Django日志
- **位置**: 终端输出
- **内容**: API请求、错误信息

#### 4.2.2 Celery Worker日志
- **位置**: 终端输出
- **内容**: 任务接收、执行过程、错误信息

#### 4.2.3 执行历史日志
- **路径**: 通过API访问 `/api/automation/executions/{id}/logs/`
- **内容**: 任务执行详细日志

## 5. 部署注意事项

### 5.1 生产环境配置
- 更改`DEBUG=False`
- 生成新的`SECRET_KEY`
- 使用正式的Redis服务
- 配置合适的数据库连接

### 5.2 服务管理
- 使用进程管理工具（如Supervisor）管理服务
- 配置日志轮转
- 设置监控和告警

### 5.3 性能优化
- 调整Celery worker数量
- 配置合适的任务超时时间
- 优化Redis内存使用

## 6. 命令速查

### 6.1 启动服务
```powershell
# 后端服务
.venv\Scripts\Activate.ps1
python manage.py runserver

# Celery Worker
.venv\Scripts\Activate.ps1
celery -A Django worker -l info

# 前端服务
cd frontend
npm run dev
```

### 6.2 检查状态
```powershell
# 检查Redis连接
python -c "import redis; r = redis.Redis(host='192.168.3.100', port=6379, db=1); print('Redis Broker connection:', r.ping())"

# 检查任务列表
python -c "import requests; data = {'username': 'admin', 'password': 'admin123'}; login_response = requests.post('http://localhost:8000/api/auth/users/login/', json=data); if login_response.status_code == 200: token = login_response.json()['data']['token']; headers = {'Authorization': 'Token ' + token}; tasks_response = requests.get('http://localhost:8000/api/automation/tasks/', headers=headers); print('Tasks:', tasks_response.json())"
```

## 7. 技术支持

如果遇到问题，请检查以下内容：
1. 环境配置是否正确
2. Redis服务是否正常运行
3. 服务启动命令是否正确
4. 查看日志输出获取详细错误信息

如需进一步帮助，请提供详细的错误信息和操作步骤。