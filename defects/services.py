"""
Defect service layer.
"""

from django.db.models import Q
from .models import Defect, DefectComment


class DefectService:
    @staticmethod
    def get_defect_list(filters=None, search=None, ordering=None):
        queryset = Defect.objects.all()
        
        if filters:
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            if 'severity' in filters:
                queryset = queryset.filter(severity=filters['severity'])
            if 'priority' in filters:
                queryset = queryset.filter(priority=filters['priority'])
            if 'module' in filters:
                queryset = queryset.filter(module=filters['module'])
            if 'assigned_to' in filters:
                queryset = queryset.filter(assigned_to_id=filters['assigned_to'])
        
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
    def get_defect_by_id(defect_id):
        try:
            return Defect.objects.get(id=defect_id)
        except Defect.DoesNotExist:
            return None
    
    @staticmethod
    def create_defect(data, user):
        return Defect.objects.create(
            reported_by=user,
            **data
        )
    
    @staticmethod
    def update_defect(defect_id, data):
        defect = DefectService.get_defect_by_id(defect_id)
        if defect:
            for key, value in data.items():
                setattr(defect, key, value)
            defect.save()
            return defect
        return None
    
    @staticmethod
    def delete_defect(defect_id):
        defect = DefectService.get_defect_by_id(defect_id)
        if defect:
            defect.delete()
            return True
        return False
    
    @staticmethod
    def update_defect_status(defect_id, new_status, user, comment=None):
        from django.utils import timezone
        defect = DefectService.get_defect_by_id(defect_id)
        if not defect:
            return None
        
        defect.status = new_status
        
        if new_status == 'resolved':
            defect.resolved_by = user
            defect.resolved_at = timezone.now()
        elif new_status == 'verified':
            defect.verified_by = user
            defect.verified_at = timezone.now()
        
        defect.save()
        
        if comment:
            DefectComment.objects.create(
                defect=defect,
                content=comment,
                created_by=user
            )
        
        return defect
    
    @staticmethod
    def add_comment(defect_id, content, user):
        defect = DefectService.get_defect_by_id(defect_id)
        if not defect:
            return None
        return DefectComment.objects.create(
            defect=defect,
            content=content,
            created_by=user
        )
    
    @staticmethod
    def get_statistics():
        from django.db.models import Count
        stats = Defect.objects.aggregate(
            total=Count('id'),
            new=Count('id', filter=Q(status='new')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            resolved=Count('id', filter=Q(status='resolved')),
            closed=Count('id', filter=Q(status='closed')),
            high_severity=Count('id', filter=Q(severity='high')),
            critical_severity=Count('id', filter=Q(severity='critical'))
        )
        return stats
