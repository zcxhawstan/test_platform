from django.db import migrations, models


def encrypt_plain_passwords(apps, schema_editor):
    """把库中明文 database_password 加密为 Fernet 密文"""
    import os
    Environment = apps.get_model('environments', 'Environment')

    if not os.environ.get('ENCRYPTION_KEY'):
        # 未配置密钥时跳过（保持明文，功能不受影响：decrypt_value对明文原样返回）
        print('警告: 未配置 ENCRYPTION_KEY，跳过存量密码加密（decrypt_value兼容明文，不影响功能）')
        return

    from cryptography.fernet import Fernet
    f = Fernet(os.environ['ENCRYPTION_KEY'].encode())

    updated = 0
    for env in Environment.objects.exclude(database_password__isnull=True).exclude(database_password=''):
        # gAAAAA 是 Fernet 密文固定前缀，已是密文的跳过
        if env.database_password.startswith('gAAAAA'):
            continue
        env.database_password = f.encrypt(env.database_password.encode('utf-8')).decode('utf-8')
        env.save(update_fields=['database_password'])
        updated += 1
    if updated:
        print(f'已加密 {updated} 条环境的数据库密码')


class Migration(migrations.Migration):

    dependencies = [
        ('environments', '0001_initial'),
    ]

    operations = [
        # database_password 现在存Fernet密文（比明文长约57字符），扩容避免密文截断
        migrations.AlterField(
            model_name='environment',
            name='database_password',
            field=models.CharField(max_length=300, verbose_name='数据库密码'),
        ),
        # 存量明文密码就地加密
        migrations.RunPython(encrypt_plain_passwords, migrations.RunPython.noop),
    ]
