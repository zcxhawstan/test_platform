"""
Test plan models.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TestPlan(models.Model):
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('active', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )

    name = models.CharField(max_length=200, verbose_name='计划名称')
    description = models.TextField(blank=True, null=True, verbose_name='计划描述')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_plans', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'test_plans'
        verbose_name = '测试计划'
        verbose_name_plural = '测试计划'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
        ]

    def __str__(self):
        return self.name


class TestPlanCase(models.Model):
    EXECUTION_STATUS_CHOICES = (
        ('not_run', '未执行'),
        ('passed', '通过'),
        ('failed', '失败'),
        ('blocked', '阻塞'),
        ('skipped', '跳过'),
    )

    test_plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='plan_cases', verbose_name='测试计划')
    test_case = models.ForeignKey('test_cases.TestCase', on_delete=models.CASCADE, related_name='plan_cases', verbose_name='测试用例')
    execution_status = models.CharField(max_length=20, choices=EXECUTION_STATUS_CHOICES, default='not_run', verbose_name='执行状态')
    actual_result = models.TextField(blank=True, null=True, verbose_name='实际结果')
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='执行人')
    executed_at = models.DateTimeField(null=True, blank=True, verbose_name='执行时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'test_plan_cases'
        verbose_name = '测试计划用例'
        verbose_name_plural = '测试计划用例'
        ordering = ['test_plan', 'id']
        unique_together = ['test_plan', 'test_case']
        indexes = [
            models.Index(fields=['execution_status']),
        ]

    def __str__(self):
        return f'{self.test_plan.name} - {self.test_case.title}'
