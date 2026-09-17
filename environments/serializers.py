"""
Environment serializers.
"""

from rest_framework import serializers
from utils.crypto import encrypt_value, is_encrypted
from .models import Environment, EnvironmentVariable


class EnvironmentVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvironmentVariable
        fields = ['id', 'environment', 'key', 'value', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EnvironmentSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    variables = EnvironmentVariableSerializer(many=True, read_only=True)
    # 密码只写不读：响应中永不回传
    database_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, allow_null=True,
        style={'input_type': 'password'}, label='数据库密码'
    )

    class Meta:
        model = Environment
        fields = [
            'id', 'name', 'env_type', 'description', 'host', 'port',
            'database_name', 'database_user', 'database_password',
            'status', 'config', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'variables'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        # 密码加密后存储，避免明文落库
        password = ret.get('database_password')
        if password and not is_encrypted(password):
            ret['database_password'] = encrypt_value(password)
        return ret

    def update(self, instance, validated_data):
        # 未提交密码时保留原值（表单留空表示不修改）
        if not validated_data.get('database_password'):
            validated_data.pop('database_password', None)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EnvironmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = [
            'name', 'env_type', 'description', 'host', 'port',
            'database_name', 'database_user', 'database_password',
            'status', 'config'
        ]
        # 密码加密在 EnvironmentSerializer.to_internal_value 之外，这里同样处理
        database_password = serializers.CharField(
            write_only=True, required=False, allow_blank=True, allow_null=True,
            style={'input_type': 'password'}, label='数据库密码'
        )

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        password = ret.get('database_password')
        if password and not is_encrypted(password):
            ret['database_password'] = encrypt_value(password)
        return ret
