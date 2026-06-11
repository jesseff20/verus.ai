"""
Migration to create the Notification model.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_brandsettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[
                    ('deadline', 'Prazo Judicial'),
                    ('document', 'Documento'),
                    ('case', 'Caso'),
                    ('system', 'Sistema'),
                    ('simulation', 'Simulação'),
                    ('task', 'Tarefa'),
                ], max_length=20, verbose_name='Tipo')),
                ('priority', models.CharField(choices=[
                    ('low', 'Baixa'),
                    ('medium', 'Média'),
                    ('high', 'Alta'),
                    ('urgent', 'Urgente'),
                ], default='medium', max_length=10, verbose_name='Prioridade')),
                ('title', models.CharField(max_length=300, verbose_name='Título')),
                ('message', models.TextField(verbose_name='Mensagem')),
                ('link', models.CharField(blank=True, max_length=500, verbose_name='Link')),
                ('is_read', models.BooleanField(default=False, verbose_name='Lida')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
            ],
            options={
                'verbose_name': 'Notificação',
                'verbose_name_plural': 'Notificações',
                'ordering': ['-created_at'],
            },
        ),
    ]
