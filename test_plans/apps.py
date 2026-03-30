"""
Test plans app configuration.
"""

from django.apps import AppConfig


class TestPlansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'test_plans'
    verbose_name = '测试计划管理'
