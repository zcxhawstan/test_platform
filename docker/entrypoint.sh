#!/bin/bash
# 容器启动初始化：等库 → migrate → 确保管理员 → 起主进程（参数1：启动命令，默认gunicorn）
set -e

# wait_for_db 不依赖命令注册（Django项目包不在INSTALLED_APPS），
# 直接用等效内联逻辑：循环探测数据库连接
python - <<'EOF'
import os, time, sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')
django.setup()
from django.db import connection
from django.db.utils import OperationalError

deadline = time.time() + 30
while time.time() < deadline:
    try:
        connection.ensure_connection()
        print('数据库已就绪')
        sys.exit(0)
    except OperationalError:
        time.sleep(1)
print('数据库30秒内未就绪', file=sys.stderr)
sys.exit(1)
EOF

python manage.py migrate --noinput
python manage.py ensure_admin

exec "$@"
