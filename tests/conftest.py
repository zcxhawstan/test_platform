"""
Test configuration and fixtures.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')

import pytest
import django
django.setup()

from django.conf import settings
from django.test import Client
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com',
        role='tester'
    )
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_superuser(
        username='admin',
        password='admin123',
        email='admin@example.com'
    )
    user.role = 'admin'
    user.save()
    return user


@pytest.fixture
def authenticated_client(api_client, test_user):
    from rest_framework.authtoken.models import Token
    token, _ = Token.objects.get_or_create(user=test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    from rest_framework.authtoken.models import Token
    token, _ = Token.objects.get_or_create(user=admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def test_case_data(test_user):
    import json
    return {
        'title': '测试用例1',
        'description': '这是一个测试用例',
        'module': '用户模块',
        'priority': 'high',
        'status': 'active',
        'preconditions': '用户已登录',
        'steps': json.dumps([{'step': '点击登录按钮', 'expected': '显示登录页面'}]),
        'expected_result': '成功登录'
    }


@pytest.fixture
def test_plan_data(test_user):
    from datetime import date, timedelta
    return {
        'name': '测试计划1',
        'description': '这是一个测试计划',
        'status': 'active',
        'start_date': date.today(),
        'end_date': date.today() + timedelta(days=7)
    }


@pytest.fixture
def defect_data(test_user):
    return {
        'title': '缺陷1',
        'description': '这是一个缺陷',
        'severity': 'high',
        'priority': 'high',
        'status': 'new',
        'module': '用户模块',
        'steps_to_reproduce': '1. 打开应用\n2. 点击登录',
        'expected_result': '成功登录',
        'actual_result': '登录失败'
    }


@pytest.fixture
def api_environment_data(test_user):
    return {
        'name': '测试环境',
        'base_url': 'http://test.example.com',
        'description': '测试环境配置',
        'headers': {'Content-Type': 'application/json'},
        'variables': {'env': 'test'}
    }


@pytest.fixture
def api_test_case_data(test_user, api_environment):
    return {
        'name': 'API测试用例',
        'description': 'API测试',
        'method': 'GET',
        'path': '/api/users',
        'headers': {},
        'params': {},
        'body': {},
        'expected_status_code': 200,
        'expected_response': {},
        'assertions': [],
        'environment': api_environment.id
    }


@pytest.fixture
def api_environment(test_user, db):
    from api_test.models import ApiEnvironment
    return ApiEnvironment.objects.create(
        name='测试环境',
        base_url='http://test.example.com',
        description='测试环境',
        created_by=test_user
    )
