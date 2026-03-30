"""
Log serializers.
"""

from rest_framework import serializers
from .models import OperationLog, ErrorLog


class OperationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = OperationLog
        fields = [
            'id', 'user', 'username', 'action', 'module', 'description',
            'request_method', 'request_url', 'request_params', 'request_body',
            'response_status', 'response_body', 'ip_address', 'user_agent',
            'execution_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ErrorLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ErrorLog
        fields = [
            'id', 'level', 'module', 'message', 'traceback',
            'request_url', 'request_params', 'user', 'username',
            'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
