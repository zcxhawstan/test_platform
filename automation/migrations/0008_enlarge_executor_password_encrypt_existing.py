from django.db import migrations, models


def encrypt_plain_passwords(apps, schema_editor):
    """把库中明文 executor_password 加密为 Fernet 密文"""
    import os
    Environment = apps.get_model('automation', 'Environment')

    if not os.environ.get('ENCRYPTION_KEY'):
        # 未配置密钥时跳过（保持明文，功能不受影响：decrypt_value对明文原样返回）
        print('警告: 未配置 ENCRYPTION_KEY，跳过存量密码加密（decrypt_value兼容明文，不影响功能）')
        return

    from cryptography.fernet import Fernet
    f = Fernet(os.environ['ENCRYPTION_KEY'].encode())

    updated = 0
    for env in Environment.objects.exclude(executor_password__isnull=True).exclude(executor_password=''):
        # gAAAAA 是 Fernet 密文固定前缀，已是密文的跳过
        if env.executor_password.startswith('gAAAAA'):
            continue
        env.executor_password = f.encrypt(env.executor_password.encode('utf-8')).decode('utf-8')
        env.save(update_fields=['executor_password'])
        updated += 1
    if updated:
        print(f'已加密 {updated} 条环境的执行机密码')


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0007_change_docker_image_default'),
    ]

    operations = [
        # executor_password 现在存Fernet密文（比明文长约57字符），扩容避免密文截断
        migrations.AlterField(
            model_name='environment',
            name='executor_password',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='SSH密码'),
        ),
        # 存量明文密码就地加密
        migrations.RunPython(encrypt_plain_passwords, migrations.RunPython.noop),
    ]
