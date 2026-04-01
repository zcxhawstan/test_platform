"""
Test plan management tests.
"""

import pytest
from test_plans.models import TestPlan, TestPlanCase
from test_cases.models import TestCase


@pytest.mark.django_db
class TestTestPlanCRUD:
    
    def test_create_test_plan_success(self, authenticated_client, test_plan_data):
        response = authenticated_client.post('/api/testplans/', test_plan_data)
        assert response.status_code == 201
        assert response.data['data']['name'] == test_plan_data['name']
    
    def test_create_test_plan_without_auth(self, api_client, test_plan_data):
        response = api_client.post('/api/testplans/', test_plan_data)
        assert response.status_code == 401
    
    def test_get_test_plan_list(self, authenticated_client, test_plan_data):
        authenticated_client.post('/api/testplans/', test_plan_data)
        response = authenticated_client.get('/api/testplans/')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1
    
    def test_get_test_plan_detail(self, authenticated_client, test_plan_data):
        create_response = authenticated_client.post('/api/testplans/', test_plan_data)
        plan_id = create_response.data['data']['id']
        response = authenticated_client.get(f'/api/testplans/{plan_id}/')
        assert response.status_code == 200
        assert response.data['data']['name'] == test_plan_data['name']
    
    def test_update_test_plan_success(self, authenticated_client, test_plan_data):
        create_response = authenticated_client.post('/api/testplans/', test_plan_data)
        plan_id = create_response.data['data']['id']
        update_data = {'name': '更新后的计划', 'status': 'completed'}
        response = authenticated_client.patch(f'/api/testplans/{plan_id}/', update_data)
        assert response.status_code == 200
        assert response.data['data']['name'] == '更新后的计划'


@pytest.mark.django_db
class TestPlanCaseManagement:
    
    def test_add_cases_to_plan(self, authenticated_client, test_plan_data, test_case_data):
        plan_response = authenticated_client.post('/api/testplans/', test_plan_data)
        plan_id = plan_response.data['data']['id']
        
        case_response = authenticated_client.post('/api/testcases/', test_case_data)
        case_id = case_response.data['data']['id']
        
        response = authenticated_client.post(
            f'/api/testplans/{plan_id}/add_cases/',
            {'test_case_ids': [case_id]}
        )
        assert response.status_code == 200
        assert response.data['data']['count'] >= 1
    
    def test_remove_case_from_plan(self, authenticated_client, test_plan_data, test_case_data):
        plan_response = authenticated_client.post('/api/testplans/', test_plan_data)
        plan_id = plan_response.data['data']['id']
        
        case_response = authenticated_client.post('/api/testcases/', test_case_data)
        case_id = case_response.data['data']['id']
        
        authenticated_client.post(f'/api/testplans/{plan_id}/add_cases/', {'test_case_ids': [case_id]})
        response = authenticated_client.delete(f'/api/testplans/{plan_id}/remove_case/{case_id}/')
        assert response.status_code == 200
    
    def test_execute_case_success(self, authenticated_client, test_plan_data, test_case_data):
        plan_response = authenticated_client.post('/api/testplans/', test_plan_data)
        plan_id = plan_response.data['data']['id']
        
        case_response = authenticated_client.post('/api/testcases/', test_case_data)
        case_id = case_response.data['data']['id']
        
        authenticated_client.post(f'/api/testplans/{plan_id}/add_cases/', {'test_case_ids': [case_id]})
        
        response = authenticated_client.post(
            f'/api/testplans/{plan_id}/cases/{case_id}/execute/',
            {'execution_status': 'passed', 'actual_result': '测试通过'}
        )
        assert response.status_code == 200
    
    def test_execute_case_failed(self, authenticated_client, test_plan_data, test_case_data):
        plan_response = authenticated_client.post('/api/testplans/', test_plan_data)
        plan_id = plan_response.data['data']['id']
        
        case_response = authenticated_client.post('/api/testcases/', test_case_data)
        case_id = case_response.data['data']['id']
        
        authenticated_client.post(f'/api/testplans/{plan_id}/add_cases/', {'test_case_ids': [case_id]})
        
        response = authenticated_client.post(
            f'/api/testplans/{plan_id}/cases/{case_id}/execute/',
            {'execution_status': 'failed', 'actual_result': '测试失败'}
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestPlanStatistics:
    
    def test_get_statistics(self, authenticated_client, test_plan_data):
        authenticated_client.post('/api/testplans/', test_plan_data)
        response = authenticated_client.get('/api/testplans/statistics/')
        assert response.status_code == 200
        assert 'total' in response.data['data']
