"""
Defect serializers.
"""

from rest_framework import serializers
from .models import Defect, DefectComment


class DefectCommentSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = DefectComment
        fields = ['id', 'defect', 'content', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']
        extra_kwargs = {
            'defect': {'required': False}
        }

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DefectSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source='reported_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True)
    test_case_title = serializers.CharField(source='test_case.title', read_only=True)
    test_plan_name = serializers.CharField(source='test_plan.name', read_only=True)
    comments = DefectCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Defect
        fields = [
            'id', 'title', 'description', 'severity', 'priority', 'status', 'module',
            'steps_to_reproduce', 'expected_result', 'actual_result',
            'test_case', 'test_case_title', 'test_plan', 'test_plan_name',
            'assigned_to', 'assigned_to_name', 'reported_by', 'reported_by_name',
            'resolved_by', 'resolved_by_name', 'resolved_at',
            'verified_by', 'verified_by_name', 'verified_at',
            'created_at', 'updated_at', 'comments'
        ]
        read_only_fields = ['id', 'reported_by', 'resolved_by', 'resolved_at', 'verified_by', 'verified_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['reported_by'] = self.context['request'].user
        return super().create(validated_data)


class DefectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Defect
        fields = [
            'title', 'description', 'severity', 'priority', 'status', 'module',
            'steps_to_reproduce', 'expected_result', 'actual_result',
            'test_case', 'test_plan', 'assigned_to'
        ]


class DefectStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Defect.STATUS_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True)
