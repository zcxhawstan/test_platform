from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from utils.crypto import encrypt_value, is_encrypted
from .models import Environment, AutomationTask, ExecutionHistory, Log, Report

# 路径类输入只允许字母数字和 . _ - / 组成，杜绝空格、分号、引号、$、反引号等注入字符
PATH_VALIDATOR = RegexValidator(
    regex=r'^[A-Za-z0-9._/\-]+$',
    message='路径只允许包含字母、数字和 . _ - / 字符'
)
# git仓库地址额外放行 http(s):// 和 git@host: 形式（仅 : @ 冒号，不含其他shell元字符）
GIT_REPO_VALIDATOR = RegexValidator(
    regex=r'^(https?://|git@)?[A-Za-z0-9._\-/:@]+$',
    message='仓库地址只允许包含字母、数字、. _ - / : @ 和 http(s):// 前缀'
)
# git分支名合法字符集（排除 ~ ^ : ? * [ \ 空格及控制字符）
BRANCH_VALIDATOR = RegexValidator(
    regex=r'^[A-Za-z0-9._\-/]+$',
    message='分支名只允许包含字母、数字和 . _ - / 字符'
)


class EnvironmentSerializer(serializers.ModelSerializer):
    """环境配置序列化器"""
    # 密码只写不读：响应中永不回传
    executor_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, allow_null=True,
        style={'input_type': 'password'}, label='执行机密码'
    )

    class Meta:
        model = Environment
        fields = ['id', 'name', 'environment_type', 'variables', 'description',
                  'executor_ip', 'executor_port', 'executor_username', 'executor_password',
                  'docker_image', 'docker_container_name', 'docker_ports', 'docker_volumes',
                  'is_connected', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_variables(self, value):
        """环境变量名只允许合法标识符，变量值会被拼入docker命令，禁止shell元字符"""
        import re
        if not isinstance(value, dict):
            raise serializers.ValidationError('variables必须是对象')
        for key, val in value.items():
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', str(key)):
                raise serializers.ValidationError(f'环境变量名 {key} 不合法：只允许字母、数字和下划线，且不能以数字开头')
            if not re.fullmatch(r'[A-Za-z0-9._\-/:=,@+]*', str(val)):
                raise serializers.ValidationError(f'环境变量 {key} 的值包含不允许的字符')
        return value

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        # 密码加密后存储，避免明文落库
        password = ret.get('executor_password')
        if password and not is_encrypted(password):
            ret['executor_password'] = encrypt_value(password)
        return ret

    def update(self, instance, validated_data):
        # 未提交密码时保留原值（表单留空表示不修改）
        if not validated_data.get('executor_password'):
            validated_data.pop('executor_password', None)
        return super().update(instance, validated_data)


class AutomationTaskSerializer(serializers.ModelSerializer):
    """自动化任务序列化器"""
    script_source = serializers.CharField(default='git', read_only=True)
    environment = EnvironmentSerializer(read_only=True)
    environment_id = serializers.PrimaryKeyRelatedField(queryset=Environment.objects.all(), source='environment', write_only=True)
    # 这些字段会被拼入远程shell命令，必须在入口处做白名单校验
    script_path = serializers.CharField(validators=[PATH_VALIDATOR])
    git_repo = serializers.CharField(required=False, allow_blank=True, allow_null=True,
                                     validators=[GIT_REPO_VALIDATOR])
    git_branch = serializers.CharField(required=False, validators=[BRANCH_VALIDATOR])

    class Meta:
        model = AutomationTask
        fields = ['id', 'name', 'description', 'script_source', 'script_path', 'git_repo', 'git_branch', 'environment', 'environment_id', 'execution_type', 'cron_expression', 'retry_count', 'timeout', 'enable_allure', 'status', 'created_by', 'created_at', 'updated_at']
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

    # 添加直接字段，方便前端处理
    task_name = serializers.CharField(source='task.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    executor_username = serializers.CharField(source='executor.username', read_only=True)

    class Meta:
        model = ExecutionHistory
        fields = ['id', 'task', 'task_name', 'environment', 'environment_name', 'executor', 'executor_username', 'status', 'start_time', 'end_time', 'duration', 'exit_code', 'created_at']
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
