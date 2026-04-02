from rest_framework import serializers
from .models import Environment, AutomationTask, ExecutionHistory, Log, Report


class EnvironmentSerializer(serializers.ModelSerializer):
    """环境配置序列化器"""
    class Meta:
        model = Environment
        fields = ['id', 'name', 'environment_type', 'base_url', 'variables', 'description', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class AutomationTaskSerializer(serializers.ModelSerializer):
    """自动化任务序列化器"""
    class Meta:
        model = AutomationTask
        fields = ['id', 'name', 'description', 'script_source', 'script_path', 'git_repo', 'git_branch', 'execution_command', 'environment', 'execution_type', 'cron_expression', 'retry_count', 'timeout', 'enable_allure', 'status', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_by', 'created_at', 'updated_at']


class ExecutionHistorySerializer(serializers.ModelSerializer):
    """执行历史序列化器"""
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
