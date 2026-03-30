"""
Environment models.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Environment(models.Model):
    ENV_TYPE_CHOICES = (
        ('dev', '开发环境'),
        ('test', '测试环境'),
        ('staging', '预发布环境'),
        ('prod', '生产环境'),
    )

    STATUS_CHOICES = (
        ('active', '激活'),
        ('inactive', '未激活'),
        ('maintenance', '维护中'),
    )

    name = models.CharField(max_length=100, unique=True, verbose_name='环境名称')
    env_type = models.CharField(max_length=20, choices=ENV_TYPE_CHOICES, verbose_name='环境类型')
    description = models.TextField(blank=True, null=True, verbose_name='环境描述')
    host = models.CharField(max_length=200, verbose_name='主机地址')
    port = models.IntegerField(verbose_name='端口号')
    database_name = models.CharField(max_length=100, verbose_name='数据库名称')
    database_user = models.CharField(max_length=100, verbose_name='数据库用户')
    database_password = models.CharField(max_length=200, verbose_name='数据库密码')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    config = models.JSONField(default=dict, verbose_name='环境配置')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='environments', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'environments'
        verbose_name = '环境'
        verbose_name_plural = '环境'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['env_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.name


class EnvironmentVariable(models.Model):
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='variables', verbose_name='环境')
    key = models.CharField(max_length=100, verbose_name='变量名')
    value = models.TextField(verbose_name='变量值')
    description = models.TextField(blank=True, null=True, verbose_name='变量描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'environment_variables'
        verbose_name = '环境变量'
        verbose_name_plural = '环境变量'
        ordering = ['environment', 'key']
        unique_together = ['environment', 'key']

    def __str__(self):
        return f'{self.environment.name} - {self.key}'
