"""
Log admin.
"""

from django.contrib import admin
from .models import OperationLog, ErrorLog


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'request_method', 'response_status', 'execution_time', 'created_at']
    list_filter = ['action', 'module', 'response_status', 'created_at']
    search_fields = ['description', 'request_url']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['level', 'module', 'message', 'user', 'ip_address', 'created_at']
    list_filter = ['level', 'module', 'created_at']
    search_fields = ['message', 'module']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
