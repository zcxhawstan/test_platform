"""
Defect management tests.
"""

import pytest
from defects.models import Defect


@pytest.mark.django_db
class TestDefectCRUD:
    
    def test_create_defect_success(self, authenticated_client, defect_data):
        response = authenticated_client.post('/api/defects/', defect_data)
        assert response.status_code == 201
        assert response.data['data']['title'] == defect_data['title']
    
    def test_create_defect_without_auth(self, api_client, defect_data):
        response = api_client.post('/api/defects/', defect_data)
        assert response.status_code == 401
    
    def test_get_defect_list(self, authenticated_client, defect_data):
        authenticated_client.post('/api/defects/', defect_data)
        response = authenticated_client.get('/api/defects/')
        assert response.status_code == 200
        assert len(response.data['data']['results']) >= 1
    
    def test_get_defect_detail(self, authenticated_client, defect_data):
        create_response = authenticated_client.post('/api/defects/', defect_data)
        defect_id = create_response.data['data']['id']
        response = authenticated_client.get(f'/api/defects/{defect_id}/')
        assert response.status_code == 200
        assert response.data['data']['title'] == defect_data['title']
    
    def test_update_defect_success(self, authenticated_client, defect_data):
        create_response = authenticated_client.post('/api/defects/', defect_data)
        defect_id = create_response.data['data']['id']
        update_data = {'title': '更新后的缺陷', 'priority': 'high'}
        response = authenticated_client.patch(f'/api/defects/{defect_id}/', update_data)
        assert response.status_code == 200
        assert response.data['data']['title'] == '更新后的缺陷'


@pytest.mark.django_db
class TestDefectStatusManagement:
    
    def test_update_defect_status(self, authenticated_client, defect_data):
        create_response = authenticated_client.post('/api/defects/', defect_data)
        defect_id = create_response.data['data']['id']
        
        response = authenticated_client.post(
            f'/api/defects/{defect_id}/update_status/',
            {'status': 'in_progress', 'comment': '开始处理'}
        )
        assert response.status_code == 200
        assert response.data['data']['status'] == 'in_progress'
    
    def test_resolve_defect(self, authenticated_client, defect_data):
        create_response = authenticated_client.post('/api/defects/', defect_data)
        defect_id = create_response.data['data']['id']
        
        response = authenticated_client.post(
            f'/api/defects/{defect_id}/update_status/',
            {'status': 'resolved', 'comment': '已修复'}
        )
        assert response.status_code == 200
        assert response.data['data']['status'] == 'resolved'
    
    def test_verify_defect(self, authenticated_client, defect_data):
        create_response = authenticated_client.post('/api/defects/', defect_data)
        defect_id = create_response.data['data']['id']
        
        authenticated_client.post(f'/api/defects/{defect_id}/update_status/', {'status': 'resolved'})
        response = authenticated_client.post(
            f'/api/defects/{defect_id}/update_status/',
            {'status': 'verified', 'comment': '验证通过'}
        )
        assert response.status_code == 200
        assert response.data['data']['status'] == 'verified'


@pytest.mark.django_db
class TestDefectComments:
    
    def test_add_comment_to_defect(self, authenticated_client, defect_data):
        create_response = authenticated_client.post('/api/defects/', defect_data)
        defect_id = create_response.data['data']['id']
        
        response = authenticated_client.post(
            f'/api/defects/{defect_id}/add_comment/',
            {'content': '这是一个评论'}
        )
        assert response.status_code == 200
        assert response.data['data']['content'] == '这是一个评论'
    
    def test_get_defect_with_comments(self, authenticated_client, defect_data):
        create_response = authenticated_client.post('/api/defects/', defect_data)
        defect_id = create_response.data['data']['id']
        
        authenticated_client.post(f'/api/defects/{defect_id}/add_comment/', {'content': '评论1'})
        authenticated_client.post(f'/api/defects/{defect_id}/add_comment/', {'content': '评论2'})
        
        response = authenticated_client.get(f'/api/defects/{defect_id}/')
        assert response.status_code == 200
        assert len(response.data['data']['comments']) >= 2


@pytest.mark.django_db
class TestDefectFiltering:
    
    def test_filter_by_status(self, authenticated_client, defect_data):
        authenticated_client.post('/api/defects/', defect_data)
        response = authenticated_client.get('/api/defects/?status=new')
        assert response.status_code == 200
        assert len(response.data['data']['results']) >= 1
    
    def test_filter_by_severity(self, authenticated_client, defect_data):
        authenticated_client.post('/api/defects/', defect_data)
        response = authenticated_client.get('/api/defects/?severity=high')
        assert response.status_code == 200
        assert len(response.data['data']['results']) >= 1
    
    def test_filter_by_module(self, authenticated_client, defect_data):
        authenticated_client.post('/api/defects/', defect_data)
        response = authenticated_client.get('/api/defects/?module=用户模块')
        assert response.status_code == 200
        assert len(response.data['data']['results']) >= 1


@pytest.mark.django_db
class TestDefectStatistics:
    
    def test_get_statistics(self, authenticated_client, defect_data):
        authenticated_client.post('/api/defects/', defect_data)
        response = authenticated_client.get('/api/defects/statistics/')
        assert response.status_code == 200
        assert 'total' in response.data['data']
