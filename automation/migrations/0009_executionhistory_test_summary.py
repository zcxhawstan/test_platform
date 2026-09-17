from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0008_enlarge_executor_password_encrypt_existing'),
    ]

    operations = [
        # junitxml解析出的用例统计（{total, passed, failed, skipped, errors}）
        migrations.AddField(
            model_name='executionhistory',
            name='test_summary',
            field=models.JSONField(blank=True, default=dict, verbose_name='用例统计'),
        ),
    ]
