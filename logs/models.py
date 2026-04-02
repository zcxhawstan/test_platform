"""
Log models.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class OperationLog(models.Model):
    ACTION_CHOICES = (
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('query', '查询'),
        ('execute', '执行'),
        ('login', '登录'),
        ('logout', '登出'),
    )

    MODULE_CHOICES = (
        ('user', '用户管理'),
        ('test_case', '测试用例'),
        ('test_plan', '测试计划'),
        ('defect', '缺陷管理'),
        ('api_test', '接口测试'),
        ('environment', '环境管理'),
        ('system', '系统管理'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='operation_logs', verbose_name='操作人')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='操作类型')
    module = models.CharField(max_length=20, choices=MODULE_CHOICES, verbose_name='操作模块')
    description = models.CharField(max_length=500, verbose_name='操作描述')
    request_method = models.CharField(max_length=10, verbose_name='请求方法')
    request_url = models.CharField(max_length=500, verbose_name='请求URL')
    request_params = models.JSONField(default=dict, verbose_name='请求参数')
    request_body = models.JSONField(default=dict, verbose_name='请求体')
    response_status = models.IntegerField(verbose_name='响应状态码')
    response_body = models.JSONField(default=dict, verbose_name='响应体')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')
    user_agent = models.TextField(verbose_name='用户代理')
    execution_time = models.FloatField(verbose_name='执行时间(ms)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'operation_logs'
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['module']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.user} - {self.action} - {self.module}'


class ErrorLog(models.Model):
    LEVEL_CHOICES = (
        ('debug', 'DEBUG'),
        ('info', 'INFO'),
        ('warning', 'WARNING'),
        ('error', 'ERROR'),
        ('critical', 'CRITICAL'),
    )

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, verbose_name='日志级别')
    module = models.CharField(max_length=100, verbose_name='模块')
    message = models.TextField(verbose_name='错误信息')
    traceback = models.TextField(verbose_name='堆栈信息')
    request_url = models.CharField(max_length=500, blank=True, null=True, verbose_name='请求URL')
    request_params = models.JSONField(default=dict, verbose_name='请求参数')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='error_logs', verbose_name='用户')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'error_logs'
        verbose_name = '错误日志'
        verbose_name_plural = '错误日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['module']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.level} - {self.module} - {self.message[:50]}'
