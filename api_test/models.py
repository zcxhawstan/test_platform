"""
API test models.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ApiEnvironment(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='环境名称')
    base_url = models.URLField(verbose_name='基础URL')
    description = models.TextField(blank=True, null=True, verbose_name='环境描述')
    headers = models.JSONField(default=dict, verbose_name='公共请求头')
    variables = models.JSONField(default=dict, verbose_name='环境变量')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_environments', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'api_environments'
        verbose_name = 'API环境'
        verbose_name_plural = 'API环境'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ApiTestCase(models.Model):
    METHOD_CHOICES = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    )

    name = models.CharField(max_length=200, verbose_name='用例名称')
    description = models.TextField(blank=True, null=True, verbose_name='用例描述')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, verbose_name='请求方法')
    path = models.CharField(max_length=500, verbose_name='请求路径')
    headers = models.JSONField(default=dict, verbose_name='请求头')
    params = models.JSONField(default=dict, verbose_name='请求参数')
    body = models.JSONField(default=dict, verbose_name='请求体')
    expected_status_code = models.IntegerField(default=200, verbose_name='预期状态码')
    expected_response = models.JSONField(default=dict, verbose_name='预期响应')
    assertions = models.JSONField(default=list, verbose_name='断言规则')
    environment = models.ForeignKey(ApiEnvironment, on_delete=models.CASCADE, related_name='test_cases', verbose_name='所属环境')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_test_cases', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'api_test_cases'
        verbose_name = 'API测试用例'
        verbose_name_plural = 'API测试用例'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['method']),
            models.Index(fields=['environment']),
        ]

    def __str__(self):
        return self.name


class ApiTestExecution(models.Model):
    STATUS_CHOICES = (
        ('pending', '待执行'),
        ('running', '执行中'),
        ('passed', '通过'),
        ('failed', '失败'),
        ('error', '错误'),
    )

    test_case = models.ForeignKey(ApiTestCase, on_delete=models.CASCADE, related_name='executions', verbose_name='测试用例')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='执行状态')
    request_url = models.CharField(max_length=500, verbose_name='请求URL')
    request_headers = models.JSONField(default=dict, verbose_name='请求头')
    request_body = models.JSONField(default=dict, verbose_name='请求体')
    response_status_code = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    response_headers = models.JSONField(default=dict, verbose_name='响应头')
    response_body = models.JSONField(default=dict, verbose_name='响应体')
    response_time = models.FloatField(null=True, blank=True, verbose_name='响应时间(ms)')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_executions', verbose_name='执行人')
    executed_at = models.DateTimeField(auto_now_add=True, verbose_name='执行时间')

    class Meta:
        db_table = 'api_test_executions'
        verbose_name = 'API测试执行记录'
        verbose_name_plural = 'API测试执行记录'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['executed_at']),
        ]

    def __str__(self):
        return f'{self.test_case.name} - {self.status}'
