"""
Restaura o model DocumentGenerator que foi removido na migration 0007.
O frontend depende do endpoint /api/v1/documents/generators/.
"""
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0017_alter_document_parent_related_name'),
        ('kb', '0002_initial'),
        ('templates', '0003_alter_documenttemplate_category'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentGenerator',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Nome descritivo do gerador', max_length=255, verbose_name='Nome')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('document_type', models.CharField(help_text='Ex: etp, parecer_tecnico, oficio, memorando', max_length=50, verbose_name='Tipo de Documento')),
                ('system_prompt', models.TextField(help_text='Instruções do sistema para o gerador de documentos', verbose_name='System Prompt')),
                ('user_prompt_template', models.TextField(help_text='Template com {{placeholders}} para dados do formulário', verbose_name='User Prompt Template')),
                ('llm_provider', models.CharField(choices=[('openai', 'OpenAI'), ('anthropic', 'Anthropic')], default='openai', max_length=20, verbose_name='Provedor LLM')),
                ('model_name', models.CharField(default='gpt-4o', help_text='Ex: gpt-4o, claude-3-5-sonnet-20241022', max_length=100, verbose_name='Nome do Modelo')),
                ('temperature', models.FloatField(default=0.7, help_text='0.0 = mais determinístico, 2.0 = mais criativo', verbose_name='Temperature')),
                ('max_tokens', models.IntegerField(default=4000, verbose_name='Max Tokens')),
                ('use_rag', models.BooleanField(default=True, help_text='Buscar contexto na Knowledge Base', verbose_name='Usar RAG')),
                ('rag_query_template', models.TextField(blank=True, help_text='Template para busca no RAG.', verbose_name='Template de Query RAG')),
                ('icon', models.CharField(blank=True, default='file-text', help_text='Nome do ícone Lucide para exibição', max_length=50, verbose_name='Ícone')),
                ('color', models.CharField(default='#10b981', help_text='Cor em hexadecimal para identificação visual', max_length=7, verbose_name='Cor')),
                ('display_order', models.IntegerField(default=0, help_text='Ordem de exibição na lista (menor = primeiro)', verbose_name='Ordem de Exibição')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('is_default', models.BooleanField(default=False, help_text='Gerador padrão para este tipo de documento', verbose_name='Gerador Padrão')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_document_generators',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
                ('document_template', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='generators',
                    to='templates.documenttemplate',
                    verbose_name='Template de Documento',
                )),
                ('knowledge_bases', models.ManyToManyField(
                    blank=True,
                    related_name='document_generators',
                    to='kb.document',
                    verbose_name='Bases de Conhecimento',
                )),
            ],
            options={
                'verbose_name': 'Gerador de Documento',
                'verbose_name_plural': 'Geradores de Documento',
                'ordering': ['document_type', 'display_order'],
            },
        ),
        migrations.AddIndex(
            model_name='documentgenerator',
            index=models.Index(fields=['document_type', 'is_active'], name='doc_dg_doctype_active_idx'),
        ),
        migrations.AddConstraint(
            model_name='documentgenerator',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_default=True),
                fields=['document_type', 'is_default'],
                name='unique_default_generator_per_doc_type',
            ),
        ),
        migrations.AddField(
            model_name='document',
            name='document_generator',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='generated_documents',
                to='documents.documentgenerator',
                verbose_name='Gerador de Documento',
                help_text='Gerador usado para criar este documento (se aplicável)',
            ),
        ),
    ]
