"""
User admin.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'department', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'phone']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('role', 'phone', 'avatar', 'department')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('扩展信息', {'fields': ('role', 'phone', 'department')}),
    )
