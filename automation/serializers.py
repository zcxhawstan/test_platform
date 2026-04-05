from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Environment, AutomationTask, ExecutionHistory, Log, Report


class EnvironmentSerializer(serializers.ModelSerializer):
    """环境配置序列化器"""
    class Meta:
        model = Environment
        fields = ['id', 'name', 'environment_type', 'variables', 'description', 
                  'executor_ip', 'executor_port', 'executor_username', 'executor_password', 
                  'docker_image', 'docker_container_name', 'docker_ports', 'docker_volumes',
                  'is_connected', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class AutomationTaskSerializer(serializers.ModelSerializer):
    """自动化任务序列化器"""
    script_source = serializers.CharField(default='git', read_only=True)
    environment = serializers.PrimaryKeyRelatedField(queryset=Environment.objects.all())
    
    class Meta:
        model = AutomationTask
        fields = ['id', 'name', 'description', 'script_source', 'script_path', 'git_repo', 'git_branch', 'environment', 'execution_type', 'cron_expression', 'retry_count', 'timeout', 'enable_allure', 'status', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_by', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    class Meta:
        model = get_user_model()
        fields = ['id', 'username']


class ExecutionHistorySerializer(serializers.ModelSerializer):
    """执行历史序列化器"""
    task = AutomationTaskSerializer(read_only=True)
    environment = EnvironmentSerializer(read_only=True)
    executor = UserSerializer(read_only=True)
    
    class Meta:
        model = ExecutionHistory
        fields = ['id', 'task', 'environment', 'executor', 'status', 'start_time', 'end_time', 'duration', 'exit_code', 'created_at']
        read_only_fields = ['id', 'executor', 'start_time', 'end_time', 'duration', 'exit_code', 'created_at']


class LogSerializer(serializers.ModelSerializer):
    """日志序列化器"""
    class Meta:
        model = Log
        fields = ['id', 'execution', 'level', 'message', 'timestamp']
        read_only_fields = ['id', 'execution', 'timestamp']


class ReportSerializer(serializers.ModelSerializer):
    """报告序列化器"""
    class Meta:
        model = Report
        fields = ['id', 'execution', 'report_type', 'report_path', 'report_url', 'generated_at', 'summary']
        read_only_fields = ['id', 'execution', 'generated_at']
