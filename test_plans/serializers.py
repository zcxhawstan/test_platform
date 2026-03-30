"""
Test plan serializers.
"""

from rest_framework import serializers
from .models import TestPlan, TestPlanCase


class TestPlanCaseSerializer(serializers.ModelSerializer):
    test_case_title = serializers.CharField(source='test_case.title', read_only=True)
    test_case_module = serializers.CharField(source='test_case.module', read_only=True)
    test_case_priority = serializers.CharField(source='test_case.priority', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.username', read_only=True)

    class Meta:
        model = TestPlanCase
        fields = [
            'id', 'test_plan', 'test_case', 'test_case_title', 'test_case_module',
            'test_case_priority', 'execution_status', 'actual_result',
            'executed_by', 'executed_by_name', 'executed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'executed_at', 'created_at', 'updated_at']


class TestPlanSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    cases_count = serializers.SerializerMethodField()
    passed_count = serializers.SerializerMethodField()
    failed_count = serializers.SerializerMethodField()
    not_run_count = serializers.SerializerMethodField()

    class Meta:
        model = TestPlan
        fields = [
            'id', 'name', 'description', 'status', 'start_date', 'end_date',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'cases_count', 'passed_count', 'failed_count', 'not_run_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_cases_count(self, obj):
        return obj.plan_cases.count()

    def get_passed_count(self, obj):
        return obj.plan_cases.filter(execution_status='passed').count()

    def get_failed_count(self, obj):
        return obj.plan_cases.filter(execution_status='failed').count()

    def get_not_run_count(self, obj):
        return obj.plan_cases.filter(execution_status='not_run').count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TestPlanDetailSerializer(TestPlanSerializer):
    plan_cases = TestPlanCaseSerializer(many=True, read_only=True)

    class Meta(TestPlanSerializer.Meta):
        fields = TestPlanSerializer.Meta.fields + ['plan_cases']


class AddCaseToPlanSerializer(serializers.Serializer):
    test_case_ids = serializers.ListField(child=serializers.IntegerField(), required=True)


class ExecuteCaseSerializer(serializers.Serializer):
    execution_status = serializers.ChoiceField(choices=TestPlanCase.EXECUTION_STATUS_CHOICES)
    actual_result = serializers.CharField(required=False, allow_blank=True)
