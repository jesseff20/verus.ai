"""
Migration for WorkflowTemplate and WorkflowExecution models (#18).
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0014_courtfeeguide_digitalsignature_signatureverification'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='Nome')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('specialty', models.CharField(
                    choices=[
                        ('civel', 'Cível'), ('criminal', 'Criminal'), ('trabalhista', 'Trabalhista'),
                        ('tributario', 'Tributário'), ('administrativo', 'Administrativo'),
                        ('previdenciario', 'Previdenciário'), ('familia', 'Família e Sucessões'),
                        ('empresarial', 'Empresarial'), ('ambiental', 'Ambiental'),
                        ('consumidor', 'Direito do Consumidor'), ('imobiliario', 'Imobiliário'),
                        ('outros', 'Outros'),
                    ],
                    max_length=50, verbose_name='Especialidade',
                )),
                ('steps', models.JSONField(default=list, help_text='Lista de etapas [{name, description, order, auto_advance, deadline_days}]')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='workflow_templates_created', to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Template de Workflow',
                'verbose_name_plural': 'Templates de Workflow',
                'ordering': ['specialty', 'name'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowExecution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('template', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='executions', to='cases.workflowtemplate',
                    verbose_name='Template',
                )),
                ('case', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='workflows', to='cases.legalcase',
                    verbose_name='Caso',
                )),
                ('current_step', models.IntegerField(default=0, verbose_name='Etapa Atual')),
                ('status', models.CharField(
                    choices=[('active', 'Ativo'), ('paused', 'Pausado'), ('completed', 'Concluído'), ('cancelled', 'Cancelado')],
                    default='active', max_length=20, verbose_name='Status',
                )),
                ('step_history', models.JSONField(default=list, help_text='[{step, started_at, completed_at, notes}]')),
                ('started_at', models.DateTimeField(auto_now_add=True, verbose_name='Iniciado em')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Concluído em')),
            ],
            options={
                'verbose_name': 'Execução de Workflow',
                'verbose_name_plural': 'Execuções de Workflow',
                'ordering': ['-started_at'],
            },
        ),
    ]
