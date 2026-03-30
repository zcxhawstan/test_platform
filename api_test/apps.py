"""
API test app configuration.
"""

from django.apps import AppConfig


class ApiTestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_test'
    verbose_name = '接口测试'
