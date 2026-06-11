# Generated migration for DocumentVersion model

from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0007_remove_documentgenerator'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('version_number', models.CharField(help_text='Formato semântico: MAJOR.MINOR.PATCH (ex: 1.2.3)', max_length=20, verbose_name='Número da Versão')),
                ('version_type', models.CharField(choices=[('major', 'Major - Mudança substantiva'), ('minor', 'Minor - Alterações menores'), ('patch', 'Patch - Correções/ajustes')], default='minor', max_length=10, verbose_name='Tipo de Versão')),
                ('sections_data', models.JSONField(default=list, help_text='Lista de seções com id, título e conteúdo', verbose_name='Dados das Seções')),
                ('section_hashes', models.TextField(blank=True, help_text='JSON com mapeamento section_id -> hash', null=True, verbose_name='Hashes das Seções (JSON)')),
                ('change_summary', models.TextField(blank=True, help_text='Descrição das mudanças feitas nesta versão', verbose_name='Resumo da Alteração')),
                ('tags', models.JSONField(default=list, help_text='Lista de tags para categorização', verbose_name='Tags')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('document', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='versions', to='documents.document', verbose_name='Documento')),
                ('created_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='document_versions', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
                ('parent_version', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='child_versions', to='documents.documentversion', verbose_name='Versão Pai')),
            ],
            options={
                'verbose_name': 'Versão de Documento',
                'verbose_name_plural': 'Versões de Documento',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['document', '-created_at'], name='dvers_doc_created_idx'),
                    models.Index(fields=['document', 'version_number'], name='dvers_doc_version_idx'),
                ],
            },
        ),
    ]
