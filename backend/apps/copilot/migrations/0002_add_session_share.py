# Generated migration for Copilot Session Sharing

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('copilot', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CopilotSessionShare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(max_length=36)),
                ('share_code', models.CharField(max_length=12, unique=True)),
                ('shared_with_emails', models.JSONField(blank=True, default=list)),
                ('is_public', models.BooleanField(default=False)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('access_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sessão Compartilhada',
                'verbose_name_plural': 'Sessões Compartilhadas',
                'ordering': ['-created_at'],
            },
        ),
    ]
