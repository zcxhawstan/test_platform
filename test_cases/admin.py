"""
Test case admin.
"""

from django.contrib import admin
from .models import TestCase


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'priority', 'status', 'created_by', 'created_at']
    list_filter = ['module', 'priority', 'status', 'created_at']
    search_fields = ['title', 'description', 'module']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
