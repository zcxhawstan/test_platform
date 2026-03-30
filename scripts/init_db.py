"""
初始化数据库脚本
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def create_superuser():
    username = os.environ.get('ADMIN_USERNAME', 'admin')
    password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            password=password,
            email=email
        )
        print(f'超级管理员创建成功: {username}')
    else:
        print(f'超级管理员已存在: {username}')


def create_test_users():
    test_users = [
        {
            'username': 'tester1',
            'password': 'tester123',
            'email': 'tester1@example.com',
            'role': 'tester'
        },
        {
            'username': 'tester2',
            'password': 'tester123',
            'email': 'tester2@example.com',
            'role': 'tester'
        },
        {
            'username': 'tester_dev1',
            'password': 'testerdev123',
            'email': 'tester_dev1@example.com',
            'role': 'tester_dev'
        }
    ]
    
    for user_data in test_users:
        if not User.objects.filter(username=user_data['username']).exists():
            User.objects.create_user(**user_data)
            print(f'测试用户创建成功: {user_data["username"]}')
        else:
            print(f'测试用户已存在: {user_data["username"]}')


if __name__ == '__main__':
    print('开始初始化数据库...')
    create_superuser()
    create_test_users()
    print('数据库初始化完成!')
