"""
Django settings for Django project.
"""

from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

if DEBUG:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-8!67b^9z#^4=ps5yd-aq2!j03h)47kvxvrbqm0h*!v66&p9(pf')
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
else:
    # 生产环境强制要求环境变量，缺失即拒绝启动，避免弱密钥/任意主机被访问
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('生产环境(DEBUG=False)必须通过环境变量 SECRET_KEY 提供密钥')
    _hosts = os.environ.get('ALLOWED_HOSTS', '').strip()
    if not _hosts or _hosts == '*':
        raise RuntimeError('生产环境(DEBUG=False)必须通过环境变量 ALLOWED_HOSTS 提供明确的域名/IP列表（禁止 *）')
    ALLOWED_HOSTS = [h.strip() for h in _hosts.split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'users',
    'test_cases',
    'test_plans',
    'defects',
    'api_test',
    'environments',
    'logs',
    'automation',
]

# 自定义用户模型
AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Django.wsgi.application'

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 缓存配置 (使用Redis数据库0)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://{os.environ.get('REDIS_HOST', '192.168.3.100')}:{os.environ.get('REDIS_PORT', '6379')}/{os.environ.get('REDIS_DB_CACHE', '0')}",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.environ.get('REDIS_PASSWORD', ''),
        }
    }
}

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = 'static/'

# 媒体文件
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery 配置 (使用Redis数据库隔离)
# Redis数据库1用于消息代理(Broker)，数据库2用于结果后端(Result Backend)
REDIS_HOST = os.environ.get('REDIS_HOST', '192.168.3.100')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
REDIS_DB_BROKER = os.environ.get('REDIS_DB_BROKER', '1')
REDIS_DB_RESULT = os.environ.get('REDIS_DB_RESULT', '2')

# 构建Redis URL
REDIS_BASE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
if REDIS_PASSWORD:
    REDIS_BASE_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

CELERY_BROKER_URL = f"{REDIS_BASE_URL}/{REDIS_DB_BROKER}"
CELERY_RESULT_BACKEND = f"{REDIS_BASE_URL}/{REDIS_DB_RESULT}"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SOFT_TIME_LIMIT = 3600
CELERY_TASK_TIME_LIMIT = 7200

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 纯Token认证：/api/ 已全局豁免CSRF，不能再保留会话认证
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS 白名单：生产环境必须通过 CORS_ALLOWED_ORIGINS 配置明确的前端来源
_cors_env = os.environ.get('CORS_ALLOWED_ORIGINS', '').strip()
if _cors_env:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_env.split(',') if o.strip()]
else:
    # 未配置时仅放行本机开发环境
    CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']
CORS_ALLOW_CREDENTIALS = True

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
