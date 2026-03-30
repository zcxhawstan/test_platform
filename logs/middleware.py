"""
Logging middleware.
"""

import time
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .models import OperationLog, ErrorLog
from .services import LogService

User = get_user_model()


class LoggingMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            execution_time = (time.time() - request.start_time) * 1000
            
            if request.path.startswith('/api/') and request.method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                try:
                    user = request.user if request.user.is_authenticated else None
                    
                    if user and not user.is_superuser:
                        module = self._get_module_from_path(request.path)
                        action = self._get_action_from_method(request.method)
                        
                        log_data = {
                            'user': user,
                            'action': action,
                            'module': module,
                            'description': f'{action} {request.path}',
                            'request_method': request.method,
                            'request_url': request.path,
                            'request_params': dict(request.GET),
                            'request_body': self._get_request_body(request),
                            'response_status': response.status_code,
                            'response_body': self._get_response_body(response),
                            'ip_address': self._get_client_ip(request),
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                            'execution_time': execution_time
                        }
                        
                        LogService.create_operation_log(log_data)
                except Exception as e:
                    pass
        
        return response
    
    def process_exception(self, request, exception):
        if request.path.startswith('/api/'):
            try:
                user = request.user if request.user.is_authenticated else None
                
                log_data = {
                    'level': 'error',
                    'module': self._get_module_from_path(request.path),
                    'message': str(exception),
                    'traceback': traceback.format_exc(),
                    'request_url': request.path,
                    'request_params': dict(request.GET),
                    'user': user,
                    'ip_address': self._get_client_ip(request)
                }
                
                LogService.create_error_log(log_data)
            except Exception as e:
                pass
        
        return None
    
    def _get_module_from_path(self, path):
        if '/auth/' in path:
            return 'user'
        elif '/testcases/' in path:
            return 'test_case'
        elif '/testplans/' in path:
            return 'test_plan'
        elif '/defects/' in path:
            return 'defect'
        elif '/apitest/' in path:
            return 'api_test'
        elif '/environments/' in path:
            return 'environment'
        else:
            return 'system'
    
    def _get_action_from_method(self, method):
        action_map = {
            'GET': 'query',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        return action_map.get(method, 'query')
    
    def _get_request_body(self, request):
        try:
            if hasattr(request, 'body'):
                import json
                return json.loads(request.body.decode('utf-8'))
        except:
            pass
        return {}
    
    def _get_response_body(self, response):
        try:
            if hasattr(response, 'content'):
                import json
                return json.loads(response.content.decode('utf-8'))
        except:
            pass
        return {}
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
