# 测试平台部署文档

## 项目简介

基于Vue3 + Django + pytest的企业级测试平台，提供用户管理、测试用例管理、测试计划管理、缺陷管理、接口测试、环境管理、日志管理等完整功能。

## 技术栈

### 后端
- Django 4.2
- Django REST Framework
- MySQL 8.0
- Celery (异步任务)
- Redis (消息队列)
- pytest 7.0+ (测试框架)
- allure (测试报告)

### 前端
- Vue 3 (Composition API)
- Element Plus (UI组件库)
- axios (HTTP客户端)
- vue-router (路由管理)
- pinia (状态管理)
- echarts (数据可视化)

## 环境要求

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Redis 5.0+

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd Mytest_Platform
```

### 2. 后端部署

#### 2.1 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

#### 2.2 安装依赖

```bash
pip install -r requirements.txt
```

#### 2.3 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，配置数据库连接等信息
```

#### 2.4 创建数据库

```bash
mysql -u root -p
CREATE DATABASE test_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

#### 2.5 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 2.6 初始化数据

```bash
python scripts/init_db.py
```

#### 2.7 启动服务

```bash
python manage.py runserver
```

后端服务将运行在 http://localhost:8000

### 3. 前端部署

#### 3.1 安装依赖

```bash
cd frontend
npm install
```

#### 3.2 启动开发服务器

```bash
npm run dev
```

前端服务将运行在 http://localhost:5173

#### 3.3 构建生产版本

```bash
npm run build
```

构建后的文件在 `frontend/dist` 目录

### 4. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_users.py

# 生成allure报告
pytest --alluredir=allure-results
allure serve allure-results
```

## 项目结构

```
Mytest_Platform/
├── Django/                 # Django项目配置
│   ├── settings.py        # Django配置文件
│   ├── urls.py           # URL路由配置
│   └── wsgi.py          # WSGI配置
├── users/                # 用户管理模块
├── test_cases/           # 测试用例管理模块
├── test_plans/           # 测试计划管理模块
├── defects/              # 缺陷管理模块
├── api_test/             # 接口测试模块
├── environments/         # 环境管理模块
├── logs/                 # 日志管理模块
├── utils/                # 工具类
├── tests/                # pytest测试用例
├── scripts/              # 脚本文件
├── frontend/             # Vue3前端项目
│   ├── src/
│   │   ├── api/        # API接口
│   │   ├── views/      # 页面组件
│   │   ├── router/     # 路由配置
│   │   ├── stores/     # 状态管理
│   │   └── utils/      # 工具函数
│   ├── package.json
│   └── vite.config.js
├── manage.py
├── requirements.txt
└── README.md
```

## API文档

### 认证接口

- POST /api/auth/register/ - 用户注册
- POST /api/auth/login/ - 用户登录
- POST /api/auth/logout/ - 用户登出
- GET /api/auth/profile/ - 获取用户信息
- PUT /api/auth/profile/ - 更新用户信息
- POST /api/auth/change-password/ - 修改密码

### 测试用例接口

- GET /api/testcases/ - 获取测试用例列表
- POST /api/testcases/ - 创建测试用例
- GET /api/testcases/{id}/ - 获取测试用例详情
- PATCH /api/testcases/{id}/ - 更新测试用例
- DELETE /api/testcases/{id}/ - 删除测试用例
- POST /api/testcases/import_excel/ - 导入测试用例
- GET /api/testcases/export_excel/ - 导出测试用例

### 测试计划接口

- GET /api/testplans/ - 获取测试计划列表
- POST /api/testplans/ - 创建测试计划
- GET /api/testplans/{id}/ - 获取测试计划详情
- PATCH /api/testplans/{id}/ - 更新测试计划
- DELETE /api/testplans/{id}/ - 删除测试计划
- POST /api/testplans/{id}/add_cases/ - 添加用例到计划
- DELETE /api/testplans/{id}/remove_case/{case_id}/ - 从计划移除用例
- POST /api/testplans/{id}/cases/{case_id}/execute/ - 执行用例

### 缺陷管理接口

- GET /api/defects/ - 获取缺陷列表
- POST /api/defects/ - 创建缺陷
- GET /api/defects/{id}/ - 获取缺陷详情
- PATCH /api/defects/{id}/ - 更新缺陷
- DELETE /api/defects/{id}/ - 删除缺陷
- POST /api/defects/{id}/update_status/ - 更新缺陷状态
- POST /api/defects/{id}/add_comment/ - 添加评论

### 接口测试接口

- GET /api/apitest/environments/ - 获取API环境列表
- POST /api/apitest/environments/ - 创建API环境
- GET /api/apitest/cases/ - 获取API测试用例列表
- POST /api/apitest/cases/ - 创建API测试用例
- POST /api/apitest/cases/execute/ - 执行API测试
- GET /api/apitest/executions/ - 获取执行记录

### 环境管理接口

- GET /api/environments/ - 获取环境列表
- POST /api/environments/ - 创建环境
- GET /api/environments/{id}/ - 获取环境详情
- PATCH /api/environments/{id}/ - 更新环境
- DELETE /api/environments/{id}/ - 删除环境
- POST /api/environments/{id}/add_variable/ - 添加环境变量
- DELETE /api/environments/{id}/variables/{var_id}/ - 删除环境变量

### 日志管理接口

- GET /api/logs/operations/ - 获取操作日志
- GET /api/logs/errors/ - 获取错误日志

## 默认账号

- 管理员: admin / admin123
- 测试用户: tester1 / tester123
- 测试开发: tester_dev1 / testerdev123

## 常见问题

### 1. 数据库连接失败

检查MySQL服务是否启动，以及.env文件中的数据库配置是否正确。

### 2. 前端无法访问后端

检查后端服务是否启动，以及vite.config.js中的代理配置是否正确。

### 3. 测试用例导入失败

确保上传的Excel文件格式正确，包含必要的列：标题、描述、模块、优先级、状态、前置条件、预期结果。

### 4. Redis连接失败

检查Redis服务是否启动，以及.env文件中的Redis配置是否正确。

## 生产环境部署

### 使用Gunicorn部署Django

```bash
pip install gunicorn
gunicorn Django.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/your/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/media/;
    }
}
```

### 使用PM2管理Node.js进程

```bash
npm install -g pm2
cd frontend
pm2 start npm --name "test-platform-frontend" -- run dev
```

## 许可证

MIT License
