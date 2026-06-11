"""
Migration: add_audit_fields_and_generation_log

Adds:
- IntelligentSession.collected_data
- IntelligentSession.validation_state
- IntelligentSession.reviewer_oab
- IntelligentSession.reviewed_at
- SectionAgentConfig.fallback_provider
- SectionAgentConfig.fallback_model
- SectionAgentConfig.prompt_version
- SectionAgentConfig.prompt_updated_at
- New model: SectionGenerationLog
"""
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intelligent_assistant', '0039_alter_agenttool_service_path'),
    ]

    operations = [
        # ----------------------------------------------------------------
        # IntelligentSession — audit/review fields
        # ----------------------------------------------------------------
        migrations.AddField(
            model_name='intelligentsession',
            name='collected_data',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Dados coletados do usuário para geração',
                verbose_name='Dados Coletados',
            ),
        ),
        migrations.AddField(
            model_name='intelligentsession',
            name='validation_state',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Resultado da validação pré-geração',
                verbose_name='Estado de Validação',
            ),
        ),
        migrations.AddField(
            model_name='intelligentsession',
            name='reviewer_oab',
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name='OAB do Revisor',
                help_text='OAB do advogado que revisou o documento',
            ),
        ),
        migrations.AddField(
            model_name='intelligentsession',
            name='reviewed_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Revisado em',
                help_text='Timestamp da revisão humana',
            ),
        ),
        # ----------------------------------------------------------------
        # SectionAgentConfig — fallback + prompt versioning
        # ----------------------------------------------------------------
        migrations.AddField(
            model_name='sectionagentconfig',
            name='fallback_provider',
            field=models.CharField(
                blank=True,
                max_length=50,
                verbose_name='Provider de Fallback',
                help_text='Provider de fallback se principal falhar',
            ),
        ),
        migrations.AddField(
            model_name='sectionagentconfig',
            name='fallback_model',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Modelo de Fallback',
                help_text='Modelo de fallback',
            ),
        ),
        migrations.AddField(
            model_name='sectionagentconfig',
            name='prompt_version',
            field=models.CharField(
                default='1.0',
                max_length=20,
                verbose_name='Versão do Prompt',
                help_text='Versão atual do prompt',
            ),
        ),
        migrations.AddField(
            model_name='sectionagentconfig',
            name='prompt_updated_at',
            field=models.DateTimeField(
                auto_now=True,
                verbose_name='Prompt Atualizado em',
                help_text='Última atualização do prompt',
            ),
        ),
        # ----------------------------------------------------------------
        # New model: SectionGenerationLog
        # ----------------------------------------------------------------
        migrations.CreateModel(
            name='SectionGenerationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(blank=True, max_length=50)),
                ('model_name', models.CharField(blank=True, max_length=100)),
                ('prompt_hash', models.CharField(blank=True, help_text='SHA256 do prompt enviado', max_length=64)),
                ('input_tokens', models.IntegerField(default=0)),
                ('output_tokens', models.IntegerField(default=0)),
                ('generation_time_ms', models.IntegerField(default=0)),
                ('output_hash', models.CharField(blank=True, help_text='SHA256 do conteúdo gerado', max_length=64)),
                ('has_unresolved_placeholders', models.BooleanField(default=False)),
                ('unresolved_count', models.IntegerField(default=0)),
                ('placeholder_types', models.JSONField(default=list, help_text='Lista dos tipos de placeholder encontrados')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('agent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='generation_logs',
                    to='intelligent_assistant.sectionagentconfig',
                )),
                ('section', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='generation_logs',
                    to='intelligent_assistant.blueprintsection',
                )),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='generation_logs',
                    to='intelligent_assistant.intelligentsession',
                )),
            ],
            options={
                'verbose_name': 'Log de Geração de Seção',
                'verbose_name_plural': 'Logs de Geração de Seção',
                'ordering': ['-created_at'],
            },
        ),
    ]
