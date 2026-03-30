"""
API test serializers.
"""

from rest_framework import serializers
from .models import ApiEnvironment, ApiTestCase, ApiTestExecution


class ApiEnvironmentSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = ApiEnvironment
        fields = [
            'id', 'name', 'base_url', 'description', 'headers', 'variables',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ApiTestCaseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)

    class Meta:
        model = ApiTestCase
        fields = [
            'id', 'name', 'description', 'method', 'path', 'headers', 'params', 'body',
            'expected_status_code', 'expected_response', 'assertions',
            'environment', 'environment_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ApiTestExecutionSerializer(serializers.ModelSerializer):
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.username', read_only=True)

    class Meta:
        model = ApiTestExecution
        fields = [
            'id', 'test_case', 'test_case_name', 'status', 'request_url',
            'request_headers', 'request_body', 'response_status_code',
            'response_headers', 'response_body', 'response_time',
            'error_message', 'executed_by', 'executed_by_name', 'executed_at'
        ]
        read_only_fields = ['id', 'executed_by', 'executed_at']


class ExecuteApiTestSerializer(serializers.Serializer):
    test_case_id = serializers.IntegerField(required=True)
