"""
数据库迁移脚本
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')

import django
django.setup()

from django.core.management import execute_from_command_line


def migrate():
    print('开始数据库迁移...')
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    print('数据库迁移完成!')


if __name__ == '__main__':
    migrate()
