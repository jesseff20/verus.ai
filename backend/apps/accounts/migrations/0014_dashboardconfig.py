"""
Migration for DashboardConfig model (#24).
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_lgpd_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('layout', models.JSONField(default=list, help_text='Lista de widgets: [{id, type, position, size, config}]', verbose_name='Layout')),
                ('theme', models.CharField(choices=[('default', 'Padrão'), ('compact', 'Compacto'), ('detailed', 'Detalhado')], default='default', max_length=20, verbose_name='Tema')),
                ('auto_refresh', models.BooleanField(default=True, verbose_name='Auto-refresh')),
                ('refresh_interval', models.IntegerField(default=300, help_text='Intervalo em segundos', verbose_name='Intervalo de atualização')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='dashboard_config', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Configuração do Dashboard',
                'verbose_name_plural': 'Configurações do Dashboard',
            },
        ),
    ]
