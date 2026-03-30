# 测试平台

基于Vue3 + Django + pytest的企业级测试平台

## 功能特性

- 用户管理：用户注册、登录、权限管理
- 测试用例管理：用例CRUD、导入导出、分类管理
- 测试计划管理：计划创建、用例分配、执行跟踪
- 缺陷管理：缺陷跟踪、状态流转、评论功能
- 接口测试：API环境管理、用例执行、结果记录
- 环境管理：多环境配置、变量管理
- 日志管理：操作日志、错误日志、统计分析

## 技术栈

### 后端
- Django 4.2
- Django REST Framework
- MySQL 8.0
- Celery
- Redis
- pytest 7.0+
- allure

### 前端
- Vue 3 (Composition API)
- Element Plus
- axios
- vue-router
- pinia
- echarts

## 快速开始

### 后端启动

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 初始化数据
python scripts/init_db.py

# 启动服务
python manage.py runserver
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 运行测试

```bash
# 运行所有测试
pytest

# 生成allure报告
pytest --alluredir=allure-results
allure serve allure-results
```

## 默认账号

- 管理员: admin / admin123
- 测试用户: tester1 / tester123

## 项目结构

```
Mytest_Platform/
├── Django/                 # Django项目配置
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
├── manage.py
├── requirements.txt
└── README.md
```

## 详细文档

请查看 [DEPLOYMENT.md](DEPLOYMENT.md) 获取详细的部署文档。

## 许可证

MIT License
