"""
Celery临时内存Broker配置（用于Redis不可用时）
将此配置导入到settings.py中或直接替换CELERY_BROKER_URL
"""

# 临时使用内存Broker（仅用于开发和测试）
# 注意：内存Broker不支持持久化，Worker重启后任务会丢失
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'django-db://'

# 或者使用数据库作为Broker（需要安装django-db）
# CELERY_BROKER_URL = 'django-db://'
# CELERY_RESULT_BACKEND = 'django-db://'

# 使用说明：
# 1. 安装django-db（如果需要使用数据库Broker）:
#    pip install django-celery-results django-celery-beat
# 2. 在settings.py中导入此配置:
#    from .settings_celery_fallback import *
# 3. 重启Celery Worker