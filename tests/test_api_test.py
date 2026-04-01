"""
API test management tests.
"""

import pytest
from unittest.mock import Mock, patch
from api_test.models import ApiEnvironment, ApiTestCase


@pytest.mark.django_db
class TestApiEnvironmentCRUD:
    
    def test_create_environment_success(self, authenticated_client, api_environment_data):
        response = authenticated_client.post('/api/apitest/environments/', api_environment_data, format='json')
        assert response.status_code == 201
        assert response.data['data']['name'] == api_environment_data['name']
    
    def test_create_environment_without_auth(self, api_client, api_environment_data):
        response = api_client.post('/api/apitest/environments/', api_environment_data, format='json')
        assert response.status_code == 401
    
    def test_get_environment_list(self, authenticated_client, api_environment_data):
        authenticated_client.post('/api/apitest/environments/', api_environment_data, format='json')
        response = authenticated_client.get('/api/apitest/environments/')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1
    
    def test_update_environment_success(self, authenticated_client, api_environment_data):
        create_response = authenticated_client.post('/api/apitest/environments/', api_environment_data, format='json')
        env_id = create_response.data['data']['id']
        update_data = {'name': '更新后的环境', 'base_url': 'http://updated.example.com'}
        response = authenticated_client.patch(f'/api/apitest/environments/{env_id}/', update_data, format='json')
        assert response.status_code == 200
        assert response.data['data']['name'] == '更新后的环境'


@pytest.mark.django_db
class TestApiTestCaseCRUD:
    
    def test_create_api_test_case_success(self, authenticated_client, api_test_case_data):
        response = authenticated_client.post('/api/apitest/cases/', api_test_case_data, format='json')
        assert response.status_code == 201
        assert response.data['data']['name'] == api_test_case_data['name']
    
    def test_get_api_test_case_list(self, authenticated_client, api_test_case_data):
        authenticated_client.post('/api/apitest/cases/', api_test_case_data, format='json')
        response = authenticated_client.get('/api/apitest/cases/')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1
    
    def test_filter_by_method(self, authenticated_client, api_test_case_data):
        authenticated_client.post('/api/apitest/cases/', api_test_case_data, format='json')
        response = authenticated_client.get('/api/apitest/cases/?method=GET')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1


@pytest.mark.django_db
class TestApiTestExecution:
    
    @patch('api_test.services.requests.get')
    def test_execute_get_request_success(self, mock_get, authenticated_client, api_test_case_data):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'status': 'success'}
        mock_response.text = '{"status": "success"}'
        mock_get.return_value = mock_response
        
        create_response = authenticated_client.post('/api/apitest/cases/', api_test_case_data, format='json')
        case_id = create_response.data['data']['id']
        
        response = authenticated_client.post('/api/apitest/cases/execute/', {'test_case_id': case_id}, format='json')
        assert response.status_code == 200
        assert response.data['data']['status'] == 'passed'
    
    @patch('api_test.services.requests.get')
    def test_execute_request_failed_status(self, mock_get, authenticated_client, api_test_case_data):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = {'error': 'Not found'}
        mock_response.text = '{"error": "Not found"}'
        mock_get.return_value = mock_response
        
        create_response = authenticated_client.post('/api/apitest/cases/', api_test_case_data, format='json')
        case_id = create_response.data['data']['id']
        
        response = authenticated_client.post('/api/apitest/cases/execute/', {'test_case_id': case_id}, format='json')
        assert response.status_code == 200
        assert response.data['data']['status'] == 'failed'
    
    @patch('api_test.services.requests.get')
    def test_execute_request_error(self, mock_get, authenticated_client, api_test_case_data):
        mock_get.side_effect = Exception('Connection error')
        
        create_response = authenticated_client.post('/api/apitest/cases/', api_test_case_data, format='json')
        case_id = create_response.data['data']['id']
        
        response = authenticated_client.post('/api/apitest/cases/execute/', {'test_case_id': case_id}, format='json')
        assert response.status_code == 200
        assert response.data['data']['status'] == 'error'


@pytest.mark.django_db
class TestApiTestStatistics:
    
    def test_get_statistics(self, authenticated_client):
        response = authenticated_client.get('/api/apitest/executions/statistics/')
        assert response.status_code == 200
        assert 'total' in response.data['data']
