"""
Log management tests.
"""

import pytest
from logs.models import OperationLog, ErrorLog


@pytest.mark.django_db
class TestOperationLogs:
    
    def test_get_operation_logs_as_admin(self, admin_client):
        response = admin_client.get('/api/logs/operations/')
        assert response.status_code == 200
    
    def test_get_operation_logs_as_normal_user(self, authenticated_client):
        response = authenticated_client.get('/api/logs/operations/')
        assert response.status_code == 200
    
    def test_get_operation_logs_without_auth(self, api_client):
        response = api_client.get('/api/logs/operations/')
        assert response.status_code == 401
    
    def test_filter_operation_logs_by_action(self, authenticated_client):
        response = authenticated_client.get('/api/logs/operations/?action=create')
        assert response.status_code == 200
    
    def test_filter_operation_logs_by_module(self, authenticated_client):
        response = authenticated_client.get('/api/logs/operations/?module=user')
        assert response.status_code == 200


@pytest.mark.django_db
class TestErrorLogs:
    
    def test_get_error_logs_as_admin(self, admin_client):
        response = admin_client.get('/api/logs/errors/')
        assert response.status_code == 200
    
    def test_get_error_logs_as_normal_user(self, authenticated_client):
        response = authenticated_client.get('/api/logs/errors/')
        assert response.status_code == 403
    
    def test_get_error_logs_without_auth(self, api_client):
        response = api_client.get('/api/logs/errors/')
        assert response.status_code == 401
    
    def test_filter_error_logs_by_level(self, admin_client):
        response = admin_client.get('/api/logs/errors/?level=error')
        assert response.status_code == 200
    
    def test_filter_error_logs_by_module(self, admin_client):
        response = admin_client.get('/api/logs/errors/?module=user')
        assert response.status_code == 200


@pytest.mark.django_db
class TestLogStatistics:
    
    def test_get_operation_statistics(self, authenticated_client):
        response = authenticated_client.get('/api/logs/operations/statistics/')
        assert response.status_code == 200
        assert 'operation_logs' in response.data['data']
    
    def test_get_error_statistics(self, admin_client):
        response = admin_client.get('/api/logs/errors/statistics/')
        assert response.status_code == 200
        assert 'error_logs' in response.data['data']
