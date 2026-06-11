"""
Add CasePhase model — fases processuais de um caso jurídico brasileiro.
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0006_casedocument_universal_linker'),
    ]

    operations = [
        migrations.CreateModel(
            name='CasePhase',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order', models.IntegerField(verbose_name='Ordem')),
                ('name', models.CharField(max_length=200, verbose_name='Nome da Fase')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('status', models.CharField(
                    choices=[
                        ('completed', 'Concluída'),
                        ('in_progress', 'Em Andamento'),
                        ('pending', 'Pendente'),
                        ('skipped', 'Não Aplicável'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('estimated_date', models.DateField(blank=True, null=True, verbose_name='Data Estimada')),
                ('actual_date', models.DateField(blank=True, null=True, verbose_name='Data Real')),
                ('copilot_prompt', models.TextField(blank=True, verbose_name='Prompt para Copilot')),
                ('suggested_documents', models.JSONField(blank=True, default=list, verbose_name='Documentos Sugeridos')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('caso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='phases',
                    to='cases.legalcase',
                    verbose_name='Caso',
                )),
            ],
            options={
                'verbose_name': 'Fase Processual',
                'verbose_name_plural': 'Fases Processuais',
                'ordering': ['order'],
                'unique_together': {('caso', 'order')},
            },
        ),
        migrations.AddIndex(
            model_name='casephase',
            index=models.Index(fields=['caso', 'status'], name='cases_casep_caso_id_status_idx'),
        ),
    ]
