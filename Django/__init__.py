from celery import Celery

# 设置默认的Django设置模块
import os
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')

# 创建Celery实例
app = Celery('Django')

# 直接设置Celery配置
app.conf.update(
    broker_url='memory://',
    result_backend='django-db',
    accept_content=['application/json'],
    task_serializer='json',
    result_serializer='json',
    timezone='Asia/Shanghai',
    task_track_started=True,
    task_soft_time_limit=3600,
    task_time_limit=7200
)

# 自动发现任务
app.autodiscover_tasks()
