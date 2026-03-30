"""
User authentication and management tests.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    
    def test_register_user_success(self, api_client):
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'newuser@example.com',
            'role': 'tester'
        }
        response = api_client.post('/api/auth/register/', data)
        assert response.status_code == 201
        assert response.data['code'] == 201
        assert 'user' in response.data['data']
        assert response.data['data']['user']['username'] == 'newuser'
    
    def test_register_user_missing_fields(self, api_client):
        data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        response = api_client.post('/api/auth/register/', data)
        assert response.status_code == 400
    
    def test_register_user_duplicate_username(self, api_client, test_user):
        data = {
            'username': 'testuser',
            'password': 'newpass123',
            'email': 'another@example.com'
        }
        response = api_client.post('/api/auth/register/', data)
        assert response.status_code == 400


@pytest.mark.django_db
class TestUserLogin:
    
    def test_login_success(self, api_client, test_user):
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = api_client.post('/api/auth/login/', data)
        assert response.status_code == 200
        assert 'token' in response.data['data']
        assert 'user' in response.data['data']
    
    def test_login_wrong_password(self, api_client, test_user):
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = api_client.post('/api/auth/login/', data)
        assert response.status_code == 400
        assert response.data['code'] == 400
    
    def test_login_nonexistent_user(self, api_client):
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        response = api_client.post('/api/auth/login/', data)
        assert response.status_code == 400


@pytest.mark.django_db
class TestUserLogout:
    
    def test_logout_success(self, authenticated_client):
        response = authenticated_client.post('/api/auth/logout/')
        assert response.status_code == 200
    
    def test_logout_without_auth(self, api_client):
        response = api_client.post('/api/auth/logout/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestUserProfile:
    
    def test_get_profile_success(self, authenticated_client, test_user):
        response = authenticated_client.get('/api/auth/profile/')
        assert response.status_code == 200
        assert response.data['data']['username'] == test_user.username
    
    def test_get_profile_without_auth(self, api_client):
        response = api_client.get('/api/auth/profile/')
        assert response.status_code == 401
    
    def test_update_profile_success(self, authenticated_client, test_user):
        data = {
            'email': 'updated@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = authenticated_client.put('/api/auth/profile/', data)
        assert response.status_code == 200
        assert response.data['data']['email'] == 'updated@example.com'
    
    def test_update_profile_without_auth(self, api_client):
        data = {'email': 'updated@example.com'}
        response = api_client.put('/api/auth/profile/', data)
        assert response.status_code == 401


@pytest.mark.django_db
class TestChangePassword:
    
    def test_change_password_success(self, authenticated_client, test_user):
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456'
        }
        response = authenticated_client.post('/api/auth/change-password/', data)
        assert response.status_code == 200
    
    def test_change_password_wrong_old_password(self, authenticated_client):
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass456'
        }
        response = authenticated_client.post('/api/auth/change-password/', data)
        assert response.status_code == 400


@pytest.mark.django_db
class TestUserList:
    
    def test_get_user_list_as_admin(self, admin_client, test_user):
        response = admin_client.get('/api/auth/users/')
        assert response.status_code == 200
        assert len(response.data['data']['results']) >= 1
    
    def test_get_user_list_as_normal_user(self, authenticated_client):
        response = authenticated_client.get('/api/auth/users/')
        assert response.status_code == 403
    
    def test_get_user_list_without_auth(self, api_client):
        response = api_client.get('/api/auth/users/')
        assert response.status_code == 401
