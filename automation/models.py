from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Environment(models.Model):
    """环境配置模型"""
    ENVIRONMENT_TYPES = (
        ('test', '测试环境'),
        ('staging', '预发环境'),
        ('production', '生产环境'),
        ('custom', '自定义环境'),
    )
    
    name = models.CharField(max_length=100, verbose_name='环境名称')
    environment_type = models.CharField(max_length=20, choices=ENVIRONMENT_TYPES, verbose_name='环境类型')
    variables = models.JSONField(default=dict, verbose_name='环境变量')
    description = models.TextField(blank=True, null=True, verbose_name='环境描述')
    
    # 执行机配置
    executor_ip = models.CharField(max_length=50, blank=True, null=True, verbose_name='执行机IP')
    executor_port = models.IntegerField(default=22, verbose_name='SSH端口')
    executor_username = models.CharField(max_length=50, blank=True, null=True, verbose_name='SSH用户名')
    executor_password = models.CharField(max_length=100, blank=True, null=True, verbose_name='SSH密码')
    
    # Docker配置
    docker_image = models.CharField(max_length=200, default='python:3.11', verbose_name='Docker镜像')
    docker_container_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='容器名称')
    docker_ports = models.JSONField(default=list, verbose_name='端口映射')
    docker_volumes = models.JSONField(default=list, verbose_name='卷映射')
    
    # 连接状态
    is_connected = models.BooleanField(default=False, verbose_name='连接状态')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'automation_environment'
        verbose_name = '环境配置'
        verbose_name_plural = '环境配置'
    
    def __str__(self):
        return self.name


class AutomationTask(models.Model):
    """自动化任务模型"""
    SCRIPT_SOURCES = (
        ('git', 'Git仓库'),
    )
    
    EXECUTION_TYPES = (
        ('manual', '手动执行'),
        ('scheduled', '定时执行'),
    )
    
    STATUS_CHOICES = (
        ('pending', '待执行'),
        ('running', '执行中'),
        ('success', '执行成功'),
        ('failed', '执行失败'),
        ('error', '执行异常'),
        ('stopped', '已停止'),
    )
    
    name = models.CharField(max_length=200, verbose_name='任务名称')
    description = models.TextField(blank=True, null=True, verbose_name='任务描述')
    script_source = models.CharField(max_length=20, choices=SCRIPT_SOURCES, verbose_name='脚本来源')
    script_path = models.CharField(max_length=500, verbose_name='脚本路径')
    git_repo = models.CharField(max_length=500, blank=True, null=True, verbose_name='Git仓库地址')
    git_branch = models.CharField(max_length=100, default='main', verbose_name='Git分支')
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='执行环境')
    execution_type = models.CharField(max_length=20, choices=EXECUTION_TYPES, default='manual', verbose_name='执行方式')
    cron_expression = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cron表达式')
    retry_count = models.IntegerField(default=0, verbose_name='失败重跑次数')
    timeout = models.IntegerField(default=1800, verbose_name='超时时间(秒)')
    enable_allure = models.BooleanField(default=True, verbose_name='启用Allure报告')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'automation_task'
        verbose_name = '自动化任务'
        verbose_name_plural = '自动化任务'
    
    def __str__(self):
        return self.name


class ExecutionHistory(models.Model):
    """执行历史模型"""
    STATUS_CHOICES = (
        ('pending', '待执行'),
        ('running', '执行中'),
        ('success', '执行成功'),
        ('failed', '执行失败'),
        ('error', '执行异常'),
        ('stopped', '已停止'),
    )
    
    task = models.ForeignKey(AutomationTask, on_delete=models.CASCADE, related_name='executions', verbose_name='关联任务')
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='执行环境')
    executor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='执行人')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='执行状态')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.FloatField(null=True, blank=True, verbose_name='执行时长(秒)')
    exit_code = models.IntegerField(null=True, blank=True, verbose_name='退出码')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'automation_execution_history'
        verbose_name = '执行历史'
        verbose_name_plural = '执行历史'
    
    def __str__(self):
        return f"{self.task.name} - {self.start_time}"


class Log(models.Model):
    """日志模型"""
    execution = models.ForeignKey(ExecutionHistory, on_delete=models.CASCADE, related_name='logs', verbose_name='关联执行')
    level = models.CharField(max_length=20, verbose_name='日志级别')
    message = models.TextField(verbose_name='日志内容')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='日志时间')
    
    class Meta:
        db_table = 'automation_log'
        verbose_name = '日志'
        verbose_name_plural = '日志'
    
    def __str__(self):
        return f"{self.execution.task.name} - {self.level}"


class Report(models.Model):
    """报告模型"""
    REPORT_TYPES = (
        ('allure', 'Allure报告'),
        ('junit', 'JUnit报告'),
        ('html', 'HTML报告'),
    )
    
    execution = models.ForeignKey(ExecutionHistory, on_delete=models.CASCADE, related_name='reports', verbose_name='关联执行')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='allure', verbose_name='报告类型')
    report_path = models.CharField(max_length=500, verbose_name='报告路径')
    report_url = models.URLField(blank=True, null=True, verbose_name='报告访问URL')
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')
    summary = models.JSONField(default=dict, verbose_name='报告摘要')
    
    class Meta:
        db_table = 'automation_report'
        verbose_name = '测试报告'
        verbose_name_plural = '测试报告'
    
    def __str__(self):
        return f"{self.execution.task.name} - {self.report_type}"

