"""
Test plan admin.
"""

from django.contrib import admin
from .models import TestPlan, TestPlanCase


@admin.register(TestPlan)
class TestPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'start_date', 'end_date', 'created_by', 'created_at']
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TestPlanCase)
class TestPlanCaseAdmin(admin.ModelAdmin):
    list_display = ['test_plan', 'test_case', 'execution_status', 'executed_by', 'executed_at']
    list_filter = ['execution_status', 'executed_at']
    search_fields = ['test_plan__name', 'test_case__title']
    ordering = ['test_plan', 'id']
    readonly_fields = ['created_at', 'updated_at']
