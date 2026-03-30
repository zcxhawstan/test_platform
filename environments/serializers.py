"""
Environment serializers.
"""

from rest_framework import serializers
from .models import Environment, EnvironmentVariable


class EnvironmentVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvironmentVariable
        fields = ['id', 'environment', 'key', 'value', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EnvironmentSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    variables = EnvironmentVariableSerializer(many=True, read_only=True)

    class Meta:
        model = Environment
        fields = [
            'id', 'name', 'env_type', 'description', 'host', 'port',
            'database_name', 'database_user', 'database_password',
            'status', 'config', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'variables'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

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
