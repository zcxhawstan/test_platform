"""
Test case serializers.
"""

from rest_framework import serializers
from .models import TestCase


class TestCaseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TestCase
        fields = [
            'id', 'title', 'description', 'module', 'priority', 'status',
            'preconditions', 'steps', 'expected_result', 'created_by',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TestCaseImportSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
