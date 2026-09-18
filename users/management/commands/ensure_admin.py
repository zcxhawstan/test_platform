from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    """确保管理员账号存在（从环境变量读取账号密码，幂等）"""

    help = '确保管理员账号存在（ADMIN_USERNAME/ADMIN_PASSWORD/ADMIN_EMAIL 环境变量）'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        password = os.environ.get('ADMIN_PASSWORD', '')
        email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')

        if not password:
            self.stdout.write(self.style.WARNING(
                '未设置 ADMIN_PASSWORD，跳过管理员创建'))
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'管理员 {username} 已存在，跳过')
            return

        User.objects.create_user(
            username=username, password=password, email=email, role='admin')
        self.stdout.write(self.style.SUCCESS(
            f'管理员 {username} 已创建'))
