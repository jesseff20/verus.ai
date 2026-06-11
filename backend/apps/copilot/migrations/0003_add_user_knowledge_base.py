# Generated migration for User Knowledge Base

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('copilot', '0002_add_session_share'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserKnowledgeEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[
                    ('case', 'Caso Jurídico'),
                    ('document', 'Documento'),
                    ('deadline', 'Prazo'),
                    ('client', 'Cliente'),
                    ('session', 'Sessão de Geração'),
                    ('simulation', 'Simulação'),
                    ('reminder', 'Lembrete'),
                    ('activity', 'Atividade'),
                ], max_length=20)),
                ('title', models.CharField(max_length=500)),
                ('content', models.TextField()),
                ('source_model', models.CharField(max_length=100)),
                ('source_id', models.CharField(max_length=100)),
                ('context_date', models.DateField()),
                ('embedding', models.JSONField(blank=True, null=True)),
                ('last_synced', models.DateTimeField(auto_now=True)),
                ('content_hash', models.CharField(max_length=64)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='knowledge_entries',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Entrada de Conhecimento do Usuário',
                'verbose_name_plural': 'Entradas de Conhecimento dos Usuários',
                'ordering': ['-context_date'],
                'unique_together': {('user', 'source_model', 'source_id')},
            },
        ),
        migrations.AddIndex(
            model_name='userknowledgeentry',
            index=models.Index(fields=['user', 'category'], name='copilot_use_user_id_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='userknowledgeentry',
            index=models.Index(fields=['user', 'source_model', 'source_id'], name='copilot_use_user_id_src_idx'),
        ),
        migrations.CreateModel(
            name='UserKnowledgeSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('entries_created', models.IntegerField(default=0)),
                ('entries_updated', models.IntegerField(default=0)),
                ('entries_unchanged', models.IntegerField(default=0)),
                ('errors', models.JSONField(default=list)),
                ('status', models.CharField(default='running', max_length=20)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='knowledge_sync_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Log de Sincronização de Conhecimento',
                'verbose_name_plural': 'Logs de Sincronização de Conhecimento',
                'ordering': ['-started_at'],
            },
        ),
    ]
