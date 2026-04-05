from celery import Celery

# 设置默认的Django设置模块
import os
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')

# 创建Celery实例
app = Celery('Django')

# 从Django设置中加载配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()
