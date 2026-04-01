# 测试平台运行详细步骤

## 一、MySQL虚拟机对接配置

### 1.1 获取虚拟机MySQL连接信息

首先需要在VMware虚拟机中获取MySQL的连接信息：

```bash
# 在虚拟机中执行以下命令
# 1. 查看MySQL服务状态
sudo systemctl status mysql

# 2. 获取MySQL监听地址
sudo netstat -tlnp | grep mysql

# 3. 查看MySQL配置文件
sudo cat /etc/mysql/mysql.conf.d/mysqld.cnf
```

### 1.2 配置MySQL允许远程连接

在虚拟机中执行：

```bash
# 登录MySQL
sudo mysql -u root -p

# 执行以下SQL命令（替换密码）
CREATE USER 'root'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

# 创建测试平台数据库
CREATE DATABASE test_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 1.3 修改MySQL配置文件

```bash
# 编辑MySQL配置文件
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# 找到bind-address，修改为：
bind-address = 0.0.0.0

# 重启MySQL服务
sudo systemctl restart mysql
```

### 1.4 获取虚拟机IP地址

```bash
# 在虚拟机中执行
ip addr show
# 或
ifconfig
```

记录虚拟机的IP地址，例如：192.168.1.100

### 1.5 配置Windows本地项目的.env文件

在项目根目录创建`.env`文件：

```bash
# 复制示例文件
copy .env.example .env
```

编辑`.env`文件，修改数据库连接信息：

```env
# 数据库配置（使用虚拟机IP）
DB_NAME=test_platform
DB_USER=root
DB_PASSWORD=your_password  # 替换为实际密码
DB_HOST=192.168.1.100     # 替换为虚拟机IP
DB_PORT=3306

# Django配置
SECRET_KEY=django-insecure-8!67b^9z#^4=ps5yd-aq2!j03h)47kvxvrbqm0h*!v66&p9(pf)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Celery配置（暂时使用本地Redis）
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 管理员账号
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
```

## 二、Redis安装配置

### 2.1 下载Redis for Windows

由于Redis官方不支持Windows，我们使用Windows版本：

```bash
# 下载Redis for Windows
# 访问：https://github.com/microsoftarchive/redis/releases
# 下载最新的Redis-x64-3.2.100.msi

# 或者使用Memurai（Redis的Windows替代品）
# 访问：https://www.memurai.com/get-memurai
```

### 2.2 安装Redis

```bash
# 运行下载的MSI安装包，按默认设置安装
# 安装完成后，Redis会自动作为Windows服务运行
```

### 2.3 验证Redis安装

```bash
# 打开命令行，测试Redis连接
redis-cli ping
# 应该返回：PONG

# 或者使用PowerShell
redis-cli.exe ping
```

### 2.4 配置Redis（可选）

如果需要修改Redis配置：

```bash
# Redis配置文件位置
# C:\Program Files\Redis\redis.windows.conf

# 主要配置项：
# port 6379
# bind 127.0.0.1
# requirepass your_password  # 如果需要密码
```

## 三、后端启动步骤

### 3.1 创建Python虚拟环境

```bash
# 在项目根目录执行
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 验证虚拟环境激活成功（命令行前面有(venv)标识）
```

### 3.2 安装Python依赖

```bash
# 升级pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 如果遇到mysqlclient安装失败，可以尝试：
pip install mysqlclient --binary-only
# 或者使用pymysql替代
pip install pymysql
```

### 3.3 测试数据库连接

```bash
# 测试能否连接到虚拟机的MySQL
python -c "import pymysql; conn = pymysql.connect(host='192.168.1.100', user='root', password='your_password', database='test_platform'); print('连接成功!')"
```

如果连接失败，检查：
- 虚拟机防火墙是否开放3306端口
- 虚拟机网络连接是否正常
- MySQL用户权限是否正确

### 3.4 数据库迁移

```bash
# 生成迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 如果遇到错误，可以尝试：
python manage.py makemigrations --empty
python manage.py migrate --fake-initial
```

### 3.5 初始化数据

```bash
# 运行初始化脚本
python scripts/init_db.py

# 这会创建：
# - 超级管理员账号：admin / admin123
# - 测试用户账号：tester1 / tester123
# - 测试开发账号：tester_dev1 / testerdev123
```

### 3.6 创建超级管理员（可选）

如果初始化脚本失败，可以手动创建：

```bash
python manage.py createsuperuser
# 按提示输入用户名、邮箱、密码
```

### 3.7 收集静态文件（生产环境需要）

```bash
python manage.py collectstatic
```

### 3.8 启动Django开发服务器

```bash
# 方式1：使用manage.py
python manage.py runserver

# 方式2：指定IP和端口
python manage.py runserver 0.0.0.0:8000

# 方式3：使用不同端口
python manage.py runserver 127.0.0.1:8080
```

启动成功后，访问 http://localhost:8000 应该能看到Django的默认页面。

### 3.9 测试API接口

```bash
# 测试用户注册接口
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123","email":"test@example.com","role":"tester"}'

# 测试用户登录接口
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 四、前端启动步骤

### 4.1 安装Node.js

```bash
# 检查Node.js版本
node --version
# 如果没有安装，访问 https://nodejs.org/ 下载安装

# 检查npm版本
npm --version
```

### 4.2 进入前端目录

```bash
cd frontend
```

### 4.3 安装前端依赖

```bash
# 清除npm缓存（可选）
npm cache clean --force

# 安装依赖
npm install

# 如果安装速度慢，可以使用淘宝镜像
npm install --registry=https://registry.npmmirror.com
```

### 4.4 配置API代理

检查`frontend/vite.config.js`文件，确保代理配置正确：

```javascript
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### 4.5 启动前端开发服务器

```bash
# 开发模式启动
npm run dev

# 如果端口被占用，修改package.json中的端口
# 或使用环境变量
npm run dev -- --port 3000
```

启动成功后，访问 http://localhost:5173 应该能看到登录页面。

### 4.6 测试前端功能

```bash
# 使用默认账号登录
# 管理员：admin / admin123
# 测试用户：tester1 / tester123
```

## 五、运行测试

### 5.1 运行所有测试

```bash
# 确保虚拟环境已激活
venv\Scripts\activate

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_users.py

# 运行特定测试类
pytest tests/test_users.py::TestUserLogin

# 运行特定测试方法
pytest tests/test_users.py::TestUserLogin::test_login_success
```

### 5.2 生成Allure测试报告

```bash
# 安装allure命令行工具
# 下载：https://github.com/allure-framework/allure2/releases
# 解压后配置环境变量

# 运行测试并生成报告
pytest --alluredir=allure-results

# 查看报告
allure serve allure-results

# 或生成HTML报告
allure generate allure-results --clean -o allure-report
# 然后打开 allure-report/index.html
```

## 六、常见问题排查

### 6.1 数据库连接失败

```bash
# 问题：Can't connect to MySQL server
# 解决：
# 1. 检查虚拟机MySQL服务是否运行
sudo systemctl status mysql

# 2. 检查防火墙
sudo ufw allow 3306
# 或
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload

# 3. 检查网络连接
ping 192.168.1.100
telnet 192.168.1.100 3306

# 4. 检查MySQL用户权限
mysql -u root -p -e "SELECT user, host FROM mysql.user WHERE user='root';"
```

### 6.2 Redis连接失败

```bash
# 问题：Redis connection refused
# 解决：
# 1. 检查Redis服务状态
redis-cli ping

# 2. 启动Redis服务
redis-server

# 3. 检查Redis端口
netstat -an | findstr 6379
```

### 6.3 依赖安装失败

```bash
# 问题：pip install失败
# 解决：
# 1. 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 升级pip和setuptools
python -m pip install --upgrade pip setuptools wheel

# 3. 单独安装问题包
pip install mysqlclient --binary-only
```

### 6.4 前端启动失败

```bash
# 问题：npm install失败
# 解决：
# 1. 清除缓存
npm cache clean --force

# 2. 删除node_modules重新安装
rmdir /s node_modules
npm install

# 3. 使用淘宝镜像
npm config set registry https://registry.npmmirror.com
```

## 七、验证平台运行

### 7.1 后端验证

```bash
# 访问Django管理后台
http://localhost:8000/admin/
# 使用admin账号登录

# 访问API文档（如果安装了drf-yasg）
http://localhost:8000/swagger/
```

### 7.2 前端验证

```bash
# 访问前端页面
http://localhost:5173

# 测试功能：
# 1. 用户登录
# 2. 创建测试用例
# 3. 创建测试计划
# 4. 执行测试
```

## 八、启动顺序总结

1. **启动MySQL虚拟机**
2. **启动Redis服务**
3. **启动Django后端**
4. **启动Vue3前端**

## 九、默认账号信息

- 管理员: admin / admin123
- 测试用户: tester1 / tester123
- 测试开发: tester_dev1 / testerdev123

## 十、注意事项

1. 确保虚拟机网络与Windows在同一网段
2. 检查虚拟机防火墙设置
3. 确保MySQL服务正常运行
4. 确保Redis服务正常运行
5. 按顺序启动服务：MySQL -> Redis -> Django -> Vue3
6. 遇到问题先查看错误日志
7. 开发环境使用DEBUG=True，生产环境务必改为False
