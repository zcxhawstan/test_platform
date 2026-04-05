"""
Test case serializers.
"""

from rest_framework import serializers
from .models import TestCase


class TestCaseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    formatted_created_at = serializers.SerializerMethodField()
    formatted_updated_at = serializers.SerializerMethodField()

    class Meta:
        model = TestCase
        fields = [
            'id', 'title', 'description', 'module', 'priority', 'status',
            'preconditions', 'steps', 'expected_result', 'created_by',
            'created_by_name', 'created_at', 'formatted_created_at', 'updated_at', 'formatted_updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def get_formatted_created_at(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_formatted_updated_at(self, obj):
        if obj.updated_at:
            return obj.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        return None


class TestCaseImportSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
