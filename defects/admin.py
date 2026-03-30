"""
Defect admin.
"""

from django.contrib import admin
from .models import Defect, DefectComment


@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'priority', 'status', 'module', 'assigned_to', 'reported_by', 'created_at']
    list_filter = ['status', 'severity', 'priority', 'module', 'created_at']
    search_fields = ['title', 'description', 'module']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at', 'verified_at']


@admin.register(DefectComment)
class DefectCommentAdmin(admin.ModelAdmin):
    list_display = ['defect', 'content', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'defect__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
