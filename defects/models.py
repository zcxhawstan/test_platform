"""
Defect models.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Defect(models.Model):
    SEVERITY_CHOICES = (
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '紧急'),
    )

    PRIORITY_CHOICES = (
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    )

    STATUS_CHOICES = (
        ('new', '新建'),
        ('assigned', '已分配'),
        ('in_progress', '处理中'),
        ('resolved', '已解决'),
        ('verified', '已验证'),
        ('closed', '已关闭'),
        ('reopened', '重新打开'),
    )

    title = models.CharField(max_length=200, verbose_name='缺陷标题')
    description = models.TextField(verbose_name='缺陷描述')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', verbose_name='严重程度')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='状态')
    module = models.CharField(max_length=100, verbose_name='所属模块')
    steps_to_reproduce = models.TextField(verbose_name='复现步骤')
    expected_result = models.TextField(verbose_name='预期结果')
    actual_result = models.TextField(verbose_name='实际结果')
    test_case = models.ForeignKey('test_cases.TestCase', on_delete=models.SET_NULL, null=True, blank=True, related_name='defects', verbose_name='关联用例')
    test_plan = models.ForeignKey('test_plans.TestPlan', on_delete=models.SET_NULL, null=True, blank=True, related_name='defects', verbose_name='关联计划')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_defects', verbose_name='分配给')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_defects', verbose_name='报告人')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_defects', verbose_name='解决人')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='解决时间')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_defects', verbose_name='验证人')
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='验证时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'defects'
        verbose_name = '缺陷'
        verbose_name_plural = '缺陷'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['severity']),
            models.Index(fields=['priority']),
            models.Index(fields=['module']),
        ]

    def __str__(self):
        return self.title


class DefectComment(models.Model):
    defect = models.ForeignKey(Defect, on_delete=models.CASCADE, related_name='comments', verbose_name='缺陷')
    content = models.TextField(verbose_name='评论内容')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='defect_comments', verbose_name='评论人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'defect_comments'
        verbose_name = '缺陷评论'
        verbose_name_plural = '缺陷评论'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.defect.title} - {self.content[:50]}'
