"""
Defects app configuration.
"""

from django.apps import AppConfig


class DefectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'defects'
    verbose_name = '缺陷管理'
