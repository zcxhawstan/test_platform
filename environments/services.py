"""
Environment service layer.
"""

from django.db.models import Q
from .models import Environment, EnvironmentVariable


class EnvironmentService:
    @staticmethod
    def get_environment_list(filters=None, search=None, ordering=None):
        queryset = Environment.objects.all()
        
        if filters:
            if 'env_type' in filters:
                queryset = queryset.filter(env_type=filters['env_type'])
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(host__icontains=search)
            )
        
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def get_environment_by_id(env_id):
        try:
            return Environment.objects.get(id=env_id)
        except Environment.DoesNotExist:
            return None
    
    @staticmethod
    def create_environment(data, user):
        return Environment.objects.create(
            created_by=user,
            **data
        )
    
    @staticmethod
    def update_environment(env_id, data):
        env = EnvironmentService.get_environment_by_id(env_id)
        if env:
            for key, value in data.items():
                setattr(env, key, value)
            env.save()
            return env
        return None
    
    @staticmethod
    def delete_environment(env_id):
        env = EnvironmentService.get_environment_by_id(env_id)
        if env:
            env.delete()
            return True
        return False
    
    @staticmethod
    def add_variable(env_id, key, value, description=''):
        env = EnvironmentService.get_environment_by_id(env_id)
        if not env:
            return None
        variable, created = EnvironmentVariable.objects.get_or_create(
            environment=env,
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            variable.value = value
            variable.description = description
            variable.save()
        return variable
    
    @staticmethod
    def delete_variable(env_id, variable_id):
        try:
            variable = EnvironmentVariable.objects.get(id=variable_id, environment_id=env_id)
            variable.delete()
            return True
        except EnvironmentVariable.DoesNotExist:
            return False
    
    @staticmethod
    def get_statistics():
        from django.db.models import Count
        stats = Environment.objects.aggregate(
            total=Count('id'),
            dev=Count('id', filter=Q(env_type='dev')),
            test=Count('id', filter=Q(env_type='test')),
            staging=Count('id', filter=Q(env_type='staging')),
            prod=Count('id', filter=Q(env_type='prod')),
            active=Count('id', filter=Q(status='active'))
        )
        return stats
