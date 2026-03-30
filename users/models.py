"""
User models.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', '管理员'),
        ('tester_dev', '测试开发'),
        ('tester', '普通测试'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tester', verbose_name='角色')
    phone = models.CharField(max_length=11, blank=True, null=True, verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name='部门')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'users_user'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __str__(self):
        return self.username
