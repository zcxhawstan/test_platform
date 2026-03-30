"""
API test service layer.
"""

import requests
import time
from django.db.models import Q
from .models import ApiEnvironment, ApiTestCase, ApiTestExecution


class ApiTestService:
    @staticmethod
    def get_environment_list(filters=None, search=None, ordering=None):
        queryset = ApiEnvironment.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def get_test_case_list(filters=None, search=None, ordering=None):
        queryset = ApiTestCase.objects.all()
        
        if filters:
            if 'method' in filters:
                queryset = queryset.filter(method=filters['method'])
            if 'environment' in filters:
                queryset = queryset.filter(environment_id=filters['environment'])
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(path__icontains=search)
            )
        
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def get_execution_list(filters=None, ordering=None):
        queryset = ApiTestExecution.objects.all()
        
        if filters:
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            if 'test_case' in filters:
                queryset = queryset.filter(test_case_id=filters['test_case'])
        
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def execute_test_case(test_case_id, user):
        test_case = ApiTestCase.objects.get(id=test_case_id)
        environment = test_case.environment
        
        url = environment.base_url + test_case.path
        headers = {**environment.headers, **test_case.headers}
        
        execution = ApiTestExecution.objects.create(
            test_case=test_case,
            status='running',
            request_url=url,
            request_headers=headers,
            request_body=test_case.body,
            executed_by=user
        )
        
        try:
            start_time = time.time()
            
            if test_case.method == 'GET':
                response = requests.get(url, headers=headers, params=test_case.params, timeout=30)
            elif test_case.method == 'POST':
                response = requests.post(url, headers=headers, params=test_case.params, json=test_case.body, timeout=30)
            elif test_case.method == 'PUT':
                response = requests.put(url, headers=headers, params=test_case.params, json=test_case.body, timeout=30)
            elif test_case.method == 'DELETE':
                response = requests.delete(url, headers=headers, params=test_case.params, timeout=30)
            elif test_case.method == 'PATCH':
                response = requests.patch(url, headers=headers, params=test_case.params, json=test_case.body, timeout=30)
            else:
                response = requests.request(test_case.method, url, headers=headers, timeout=30)
            
            response_time = (time.time() - start_time) * 1000
            
            execution.response_status_code = response.status_code
            execution.response_headers = dict(response.headers)
            
            try:
                execution.response_body = response.json()
            except:
                execution.response_body = {'text': response.text}
            
            execution.response_time = response_time
            
            if response.status_code == test_case.expected_status_code:
                execution.status = 'passed'
            else:
                execution.status = 'failed'
                execution.error_message = f'状态码不匹配: 预期{test_case.expected_status_code}, 实际{response.status_code}'
            
            execution.save()
            
        except Exception as e:
            execution.status = 'error'
            execution.error_message = str(e)
            execution.save()
        
        return execution
    
    @staticmethod
    def get_statistics():
        from django.db.models import Count
        stats = ApiTestExecution.objects.aggregate(
            total=Count('id'),
            passed=Count('id', filter=Q(status='passed')),
            failed=Count('id', filter=Q(status='failed')),
            error=Count('id', filter=Q(status='error'))
        )
        return stats
