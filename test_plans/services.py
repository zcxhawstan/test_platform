"""
Test plan service layer.
"""

from django.db.models import Q
from .models import TestPlan, TestPlanCase


class TestPlanService:
    @staticmethod
    def get_test_plan_list(filters=None, search=None, ordering=None):
        queryset = TestPlan.objects.all()
        
        if filters:
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def get_test_plan_by_id(plan_id):
        try:
            return TestPlan.objects.get(id=plan_id)
        except TestPlan.DoesNotExist:
            return None
    
    @staticmethod
    def create_test_plan(data, user):
        return TestPlan.objects.create(
            created_by=user,
            **data
        )
    
    @staticmethod
    def update_test_plan(plan_id, data):
        plan = TestPlanService.get_test_plan_by_id(plan_id)
        if plan:
            for key, value in data.items():
                setattr(plan, key, value)
            plan.save()
            return plan
        return None
    
    @staticmethod
    def delete_test_plan(plan_id):
        plan = TestPlanService.get_test_plan_by_id(plan_id)
        if plan:
            plan.delete()
            return True
        return False
    
    @staticmethod
    def add_cases_to_plan(plan_id, case_ids):
        plan = TestPlanService.get_test_plan_by_id(plan_id)
        if not plan:
            return None
        
        created_count = 0
        for case_id in case_ids:
            from test_cases.models import TestCase
            try:
                case = TestCase.objects.get(id=case_id)
                TestPlanCase.objects.get_or_create(
                    test_plan=plan,
                    test_case=case
                )
                created_count += 1
            except TestCase.DoesNotExist:
                continue
        
        return created_count
    
    @staticmethod
    def remove_case_from_plan(plan_id, case_id):
        try:
            plan_case = TestPlanCase.objects.get(test_plan_id=plan_id, test_case_id=case_id)
            plan_case.delete()
            return True
        except TestPlanCase.DoesNotExist:
            return False
    
    @staticmethod
    def execute_case(plan_id, case_id, execution_status, actual_result, user):
        try:
            plan_case = TestPlanCase.objects.get(test_plan_id=plan_id, test_case_id=case_id)
            plan_case.execution_status = execution_status
            plan_case.actual_result = actual_result
            plan_case.executed_by = user
            plan_case.save()
            return plan_case
        except TestPlanCase.DoesNotExist:
            return None
    
    @staticmethod
    def get_statistics():
        from django.db.models import Count
        stats = TestPlan.objects.aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            active=Count('id', filter=Q(status='active')),
            completed=Count('id', filter=Q(status='completed'))
        )
        return stats
