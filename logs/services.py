"""
Log service layer.
"""

from django.db.models import Q
from .models import OperationLog, ErrorLog


class LogService:
    @staticmethod
    def get_operation_log_list(filters=None, search=None, ordering=None):
        queryset = OperationLog.objects.all()
        
        if filters:
            if 'user' in filters:
                queryset = queryset.filter(user_id=filters['user'])
            if 'action' in filters:
                queryset = queryset.filter(action=filters['action'])
            if 'module' in filters:
                queryset = queryset.filter(module=filters['module'])
        
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(request_url__icontains=search)
            )
        
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def get_error_log_list(filters=None, search=None, ordering=None):
        queryset = ErrorLog.objects.all()
        
        if filters:
            if 'level' in filters:
                queryset = queryset.filter(level=filters['level'])
            if 'module' in filters:
                queryset = queryset.filter(module=filters['module'])
            if 'user' in filters:
                queryset = queryset.filter(user_id=filters['user'])
        
        if search:
            queryset = queryset.filter(
                Q(message__icontains=search) |
                Q(module__icontains=search)
            )
        
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def create_operation_log(data):
        return OperationLog.objects.create(**data)
    
    @staticmethod
    def create_error_log(data):
        return ErrorLog.objects.create(**data)
    
    @staticmethod
    def get_statistics():
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        stats = {
            'operation_logs': OperationLog.objects.aggregate(
                total=Count('id'),
                today=Count('id', filter=Q(created_at__date=today)),
                yesterday=Count('id', filter=Q(created_at__date=yesterday))
            ),
            'error_logs': ErrorLog.objects.aggregate(
                total=Count('id'),
                today=Count('id', filter=Q(created_at__date=today)),
                yesterday=Count('id', filter=Q(created_at__date=yesterday)),
                error=Count('id', filter=Q(level='error')),
                critical=Count('id', filter=Q(level='critical'))
            )
        }
        return stats
