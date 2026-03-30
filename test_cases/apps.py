"""
Test cases app configuration.
"""

from django.apps import AppConfig


class TestCasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'test_cases'
    verbose_name = '测试用例管理'
