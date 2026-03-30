"""
Test case models.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TestCase(models.Model):
    PRIORITY_CHOICES = (
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '紧急'),
    )

    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('active', '激活'),
        ('archived', '归档'),
    )

    title = models.CharField(max_length=200, verbose_name='用例标题')
    description = models.TextField(blank=True, null=True, verbose_name='用例描述')
    module = models.CharField(max_length=100, verbose_name='所属模块')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    preconditions = models.TextField(blank=True, null=True, verbose_name='前置条件')
    steps = models.JSONField(default=list, verbose_name='测试步骤')
    expected_result = models.TextField(verbose_name='预期结果')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_cases', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'test_cases'
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['module']),
            models.Index(fields=['priority']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title
