"""
Test case management tests.
"""

import pytest
from django.contrib.auth import get_user_model
from test_cases.models import TestCase

User = get_user_model()


@pytest.mark.django_db
class TestTestCaseCRUD:
    
    def test_create_test_case_success(self, authenticated_client, test_case_data):
        response = authenticated_client.post('/api/testcases/', test_case_data)
        assert response.status_code == 201
        assert response.data['data']['title'] == test_case_data['title']
    
    def test_create_test_case_without_auth(self, api_client, test_case_data):
        response = api_client.post('/api/testcases/', test_case_data)
        assert response.status_code == 401
    
    def test_get_test_case_list(self, authenticated_client, test_case_data):
        authenticated_client.post('/api/testcases/', test_case_data)
        response = authenticated_client.get('/api/testcases/')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1
    
    def test_get_test_case_detail(self, authenticated_client, test_case_data):
        create_response = authenticated_client.post('/api/testcases/', test_case_data)
        case_id = create_response.data['data']['id']
        response = authenticated_client.get(f'/api/testcases/{case_id}/')
        assert response.status_code == 200
        assert response.data['data']['title'] == test_case_data['title']
    
    def test_update_test_case_success(self, authenticated_client, test_case_data):
        create_response = authenticated_client.post('/api/testcases/', test_case_data)
        case_id = create_response.data['data']['id']
        update_data = {'title': '更新后的标题', 'priority': 'critical'}
        response = authenticated_client.patch(f'/api/testcases/{case_id}/', update_data)
        assert response.status_code == 200
        assert response.data['data']['title'] == '更新后的标题'
    
    def test_update_test_case_without_permission(self, api_client, test_user, test_case_data):
        from rest_framework.authtoken.models import Token
        other_user = User.objects.create_user(username='other', password='pass123')
        token = Token.objects.create(user=other_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        create_response = api_client.post('/api/testcases/', test_case_data)
        case_id = create_response.data['data']['id']
        
        token2 = Token.objects.create(user=test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token2.key}')
        response = api_client.patch(f'/api/testcases/{case_id}/', {'title': '更新'})
        assert response.status_code == 403
    
    def test_delete_test_case_as_admin(self, admin_client, test_case_data):
        create_response = admin_client.post('/api/testcases/', test_case_data)
        case_id = create_response.data['data']['id']
        response = admin_client.delete(f'/api/testcases/{case_id}/')
        assert response.status_code == 200
    
    def test_delete_test_case_as_normal_user(self, authenticated_client, test_case_data):
        create_response = authenticated_client.post('/api/testcases/', test_case_data)
        case_id = create_response.data['data']['id']
        response = authenticated_client.delete(f'/api/testcases/{case_id}/')
        assert response.status_code == 403


@pytest.mark.django_db
class TestTestCaseFiltering:
    
    def test_filter_by_module(self, authenticated_client, test_case_data):
        authenticated_client.post('/api/testcases/', test_case_data)
        response = authenticated_client.get('/api/testcases/?module=用户模块')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1
    
    def test_filter_by_priority(self, authenticated_client, test_case_data):
        authenticated_client.post('/api/testcases/', test_case_data)
        response = authenticated_client.get('/api/testcases/?priority=high')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1
    
    def test_filter_by_status(self, authenticated_client, test_case_data):
        authenticated_client.post('/api/testcases/', test_case_data)
        response = authenticated_client.get('/api/testcases/?status=active')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1
    
    def test_search_test_cases(self, authenticated_client, test_case_data):
        authenticated_client.post('/api/testcases/', test_case_data)
        response = authenticated_client.get('/api/testcases/?search=测试用例')
        assert response.status_code == 200
        assert len(response.data['data']) >= 1


@pytest.mark.django_db
class TestTestCaseImportExport:
    
    def test_import_excel_success(self, authenticated_client):
        import io
        import openpyxl
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['标题', '描述', '模块', '优先级', '状态', '前置条件', '预期结果'])
        ws.append(['导入用例1', '描述', '模块', 'high', 'active', '前置', '预期'])
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        file = SimpleUploadedFile(
            'test_cases.xlsx',
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        response = authenticated_client.post('/api/testcases/import_excel/', {'file': file}, format='multipart')
        assert response.status_code == 200
        assert response.data['data']['count'] >= 1
    
    def test_export_excel_success(self, authenticated_client, test_case_data):
        authenticated_client.post('/api/testcases/', test_case_data)
        response = authenticated_client.get('/api/testcases/export_excel/')
        assert response.status_code == 200
        assert response['Content-Disposition'].startswith('attachment')


@pytest.mark.django_db
class TestTestCaseStatistics:
    
    def test_get_statistics(self, authenticated_client, test_case_data):
        authenticated_client.post('/api/testcases/', test_case_data)
        response = authenticated_client.get('/api/testcases/statistics/')
        assert response.status_code == 200
        assert 'total' in response.data['data']
