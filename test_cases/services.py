"""
Test case service layer.
"""

from django.db.models import Q
from .models import TestCase


class TestCaseService:
    @staticmethod
    def get_test_case_list(filters=None, search=None, ordering=None):
        queryset = TestCase.objects.all()
        
        if filters:
            if 'module' in filters:
                queryset = queryset.filter(module=filters['module'])
            if 'priority' in filters:
                queryset = queryset.filter(priority=filters['priority'])
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(module__icontains=search)
            )
        
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def get_test_case_by_id(case_id):
        try:
            return TestCase.objects.get(id=case_id)
        except TestCase.DoesNotExist:
            return None
    
    @staticmethod
    def create_test_case(data, user):
        return TestCase.objects.create(
            created_by=user,
            **data
        )
    
    @staticmethod
    def update_test_case(case_id, data):
        case = TestCaseService.get_test_case_by_id(case_id)
        if case:
            for key, value in data.items():
                setattr(case, key, value)
            case.save()
            return case
        return None
    
    @staticmethod
    def delete_test_case(case_id):
        case = TestCaseService.get_test_case_by_id(case_id)
        if case:
            case.delete()
            return True
        return False
    
    @staticmethod
    def bulk_update_status(case_ids, new_status):
        return TestCase.objects.filter(id__in=case_ids).update(status=new_status)
    
    @staticmethod
    def get_statistics():
        from django.db.models import Count
        stats = TestCase.objects.aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            active=Count('id', filter=Q(status='active')),
            archived=Count('id', filter=Q(status='archived')),
            high_priority=Count('id', filter=Q(priority='high')),
            critical_priority=Count('id', filter=Q(priority='critical'))
        )
        return stats
