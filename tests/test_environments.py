"""
Environment management tests.
"""

import pytest
from environments.models import Environment


@pytest.mark.django_db
class TestEnvironmentCRUD:
    
    def test_create_environment_success(self, authenticated_client):
        data = {
            'name': '测试环境',
            'env_type': 'test',
            'description': '测试环境描述',
            'host': 'test.example.com',
            'port': 3306,
            'database_name': 'test_db',
            'database_user': 'root',
            'database_password': 'password123',
            'status': 'active'
        }
        response = authenticated_client.post('/api/environments/', data)
        assert response.status_code == 201
        assert response.data['data']['name'] == data['name']
    
    def test_create_environment_without_auth(self, api_client):
        data = {
            'name': '测试环境',
            'env_type': 'test',
            'host': 'test.example.com',
            'port': 3306,
            'database_name': 'test_db',
            'database_user': 'root',
            'database_password': 'password123'
        }
        response = api_client.post('/api/environments/', data)
        assert response.status_code == 401
    
    def test_get_environment_list(self, authenticated_client):
        data = {
            'name': '测试环境',
            'env_type': 'test',
            'host': 'test.example.com',
            'port': 3306,
            'database_name': 'test_db',
            'database_user': 'root',
            'database_password': 'password123'
        }
        authenticated_client.post('/api/environments/', data)
        response = authenticated_client.get('/api/environments/')
        assert response.status_code == 200
        assert len(response.data['data']['results']) >= 1
    
    def test_update_environment_success(self, authenticated_client):
        data = {
            'name': '测试环境',
            'env_type': 'test',
            'host': 'test.example.com',
            'port': 3306,
            'database_name': 'test_db',
            'database_user': 'root',
            'database_password': 'password123'
        }
        create_response = authenticated_client.post('/api/environments/', data)
        env_id = create_response.data['data']['id']
        
        update_data = {'name': '更新后的环境', 'status': 'maintenance'}
        response = authenticated_client.patch(f'/api/environments/{env_id}/', update_data)
        assert response.status_code == 200
        assert response.data['data']['name'] == '更新后的环境'


@pytest.mark.django_db
class TestEnvironmentVariables:
    
    def test_add_variable_to_environment(self, authenticated_client):
        env_data = {
            'name': '测试环境',
            'env_type': 'test',
            'host': 'test.example.com',
            'port': 3306,
            'database_name': 'test_db',
            'database_user': 'root',
            'database_password': 'password123'
        }
        create_response = authenticated_client.post('/api/environments/', env_data)
        env_id = create_response.data['data']['id']
        
        response = authenticated_client.post(
            f'/api/environments/{env_id}/add_variable/',
            {'key': 'API_KEY', 'value': 'secret123', 'description': 'API密钥'}
        )
        assert response.status_code == 200
        assert response.data['data']['key'] == 'API_KEY'
    
    def test_delete_variable_from_environment(self, authenticated_client):
        env_data = {
            'name': '测试环境',
            'env_type': 'test',
            'host': 'test.example.com',
            'port': 3306,
            'database_name': 'test_db',
            'database_user': 'root',
            'database_password': 'password123'
        }
        create_response = authenticated_client.post('/api/environments/', env_data)
        env_id = create_response.data['data']['id']
        
        var_response = authenticated_client.post(
            f'/api/environments/{env_id}/add_variable/',
            {'key': 'API_KEY', 'value': 'secret123'}
        )
        var_id = var_response.data['data']['id']
        
        response = authenticated_client.delete(f'/api/environments/{env_id}/variables/{var_id}/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestEnvironmentFiltering:
    
    def test_filter_by_env_type(self, authenticated_client):
        data = {
            'name': '测试环境',
            'env_type': 'test',
            'host': 'test.example.com',
            'port': 3306,
            'database_name': 'test_db',
            'database_user': 'root',
            'database_password': 'password123'
        }
        authenticated_client.post('/api/environments/', data)
        response = authenticated_client.get('/api/environments/?env_type=test')
        assert response.status_code == 200
        assert len(response.data['data']['results']) >= 1
    
    def test_filter_by_status(self, authenticated_client):
        data = {
            'name': '测试环境',
            'env_type': 'test',
            'host': 'test.example.com',
            'port': 3306,
            'database_name': 'test_db',
            'database_user': 'root',
            'database_password': 'password123',
            'status': 'active'
        }
        authenticated_client.post('/api/environments/', data)
        response = authenticated_client.get('/api/environments/?status=active')
        assert response.status_code == 200
        assert len(response.data['data']['results']) >= 1


@pytest.mark.django_db
class TestEnvironmentStatistics:
    
    def test_get_statistics(self, authenticated_client):
        response = authenticated_client.get('/api/environments/statistics/')
        assert response.status_code == 200
        assert 'total' in response.data['data']
