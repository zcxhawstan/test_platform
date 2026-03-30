"""
Environment admin.
"""

from django.contrib import admin
from .models import Environment, EnvironmentVariable


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'env_type', 'host', 'port', 'status', 'created_by', 'created_at']
    list_filter = ['env_type', 'status', 'created_at']
    search_fields = ['name', 'description', 'host']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EnvironmentVariable)
class EnvironmentVariableAdmin(admin.ModelAdmin):
    list_display = ['environment', 'key', 'value', 'created_at']
    list_filter = ['created_at']
    search_fields = ['key', 'value', 'environment__name']
    ordering = ['environment', 'key']
    readonly_fields = ['created_at', 'updated_at']
