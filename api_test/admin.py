"""
API test admin.
"""

from django.contrib import admin
from .models import ApiEnvironment, ApiTestCase, ApiTestExecution


@admin.register(ApiEnvironment)
class ApiEnvironmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_url', 'created_by', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ApiTestCase)
class ApiTestCaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'method', 'path', 'environment', 'created_by', 'created_at']
    list_filter = ['method', 'environment', 'created_at']
    search_fields = ['name', 'description', 'path']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ApiTestExecution)
class ApiTestExecutionAdmin(admin.ModelAdmin):
    list_display = ['test_case', 'status', 'response_status_code', 'response_time', 'executed_by', 'executed_at']
    list_filter = ['status', 'executed_at']
    search_fields = ['test_case__name', 'request_url']
    ordering = ['-executed_at']
    readonly_fields = ['executed_at']
