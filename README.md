# 测试平台

基于Vue3 + Django + pytest的企业级测试平台

## 功能特性

- **用户管理**：用户注册、登录、权限管理
- **测试用例管理**：用例CRUD、导入导出、分类管理、时间格式化
- **测试计划管理**：计划创建、用例分配、执行跟踪、时间格式化
- **缺陷管理**：缺陷跟踪、状态流转、评论功能、时间格式化
- **接口测试**：API环境管理、用例执行、结果记录、响应时间格式化
- **自动化测试**：任务管理、远程执行、Docker容器、Allure报告
- **环境管理**：多环境配置、变量管理
- **日志管理**：操作日志、错误日志、统计分析

## 技术栈

### 后端
- Django 4.2+
- Django REST Framework
- Celery 5.3+ (任务队列)
- Redis 5.0+ (消息代理和缓存)
- pytest 9.0+ (测试框架)
- allure-pytest 2.15+ (测试报告)
- scp 0.15+ (远程文件传输)

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
# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 启动Django服务
python manage.py runserver 0.0.0.0:8000

# 启动Celery Worker (使用solo pool避免Windows权限问题)
.venv\Scripts\python.exe -m celery -A Django worker --loglevel=info --pool=solo
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
pytest --alluredir=allure-results --clean-alluredir
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
├── automation/           # 自动化测试模块
├── environments/         # 环境管理模块
├── logs/                 # 日志管理模块
├── utils/                # 工具类
├── tests/                # pytest测试用例
├── scripts/              # 脚本文件
├── frontend/             # Vue3前端项目
├── manage.py
├── requirements.txt
├── README.md
├── DEPLOYMENT.md
└── DEPLOYMENT_GUIDE.md
```

## 详细文档

请查看以下文档获取详细信息：
- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署与启动指南
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 详细部署指导

## 许可证

MIT License
