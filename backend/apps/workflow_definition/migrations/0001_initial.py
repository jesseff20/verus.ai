import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organization', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FlowTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='Nome do Fluxo')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('category', models.CharField(
                    choices=[
                        ('judicial_1', 'Judicial — 1º Grau'),
                        ('judicial_2', 'Judicial — 2º Grau'),
                        ('administrative', 'Administrativo'),
                        ('other', 'Outro'),
                    ],
                    default='judicial_1', max_length=20, verbose_name='Categoria',
                )),
                ('status', models.CharField(
                    choices=[
                        ('draft', 'Rascunho'),
                        ('published', 'Publicado'),
                        ('archived', 'Arquivado'),
                    ],
                    default='draft', max_length=15, verbose_name='Status',
                )),
                ('version', models.PositiveIntegerField(default=1, verbose_name='Versão atual')),
                ('is_system_template', models.BooleanField(default=False, verbose_name='Template de sistema')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('published_at', models.DateTimeField(blank=True, null=True, verbose_name='Publicado em')),
                ('organ', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='flow_templates',
                    to='organization.organ',
                    verbose_name='Órgão',
                )),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_flow_templates',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
            ],
            options={
                'verbose_name': 'Template de Fluxo',
                'verbose_name_plural': 'Templates de Fluxo',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='FlowNode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('node_id', models.CharField(max_length=100, verbose_name='ID do nó (xyflow)')),
                ('node_type', models.CharField(
                    choices=[
                        ('swimlane', 'Swim Lane (Papel)'),
                        ('start_event', 'Evento de Início'),
                        ('end_event', 'Evento de Fim'),
                        ('intermediate_event', 'Evento Intermediário'),
                        ('task', 'Tarefa'),
                        ('user_task', 'Tarefa de Usuário'),
                        ('service_task', 'Tarefa de Serviço'),
                        ('exclusive_gateway', 'Gateway Exclusivo (XOR)'),
                        ('parallel_gateway', 'Gateway Paralelo (AND)'),
                        ('inclusive_gateway', 'Gateway Inclusivo (OR)'),
                    ],
                    max_length=30, verbose_name='Tipo',
                )),
                ('label', models.CharField(max_length=200, verbose_name='Rótulo')),
                ('description', models.TextField(blank=True, verbose_name='Descrição/Instruções')),
                ('role', models.CharField(
                    choices=[
                        ('distribuidor', 'Distribuidor(a)'),
                        ('procurador', 'Procurador(a)'),
                        ('gerente', 'Gerente'),
                        ('assessor_gerencial', 'Assessor(a) Gerencial'),
                        ('assessor_gabinete', 'Assessor(a) de Gabinete'),
                        ('procurador_geral', 'Procurador(a)-Geral'),
                        ('subprocurador_geral', 'Subprocurador(a)-Geral'),
                        ('any', 'Qualquer papel'),
                    ],
                    default='any', max_length=25, verbose_name='Papel responsável',
                )),
                ('parent_node_id', models.CharField(blank=True, max_length=100, verbose_name='ID do nó pai (swim lane)')),
                ('position', models.JSONField(default=dict, verbose_name='Posição')),
                ('data', models.JSONField(blank=True, default=dict, verbose_name='Dados extras')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
                ('template', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='nodes',
                    to='workflow_definition.flowtemplate',
                    verbose_name='Template',
                )),
            ],
            options={
                'verbose_name': 'Nó de Fluxo',
                'verbose_name_plural': 'Nós de Fluxo',
                'ordering': ['template', 'order'],
            },
        ),
        migrations.CreateModel(
            name='FlowEdge',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('edge_id', models.CharField(max_length=100, verbose_name='ID da edge (xyflow)')),
                ('source_node_id', models.CharField(max_length=100, verbose_name='Nó de origem')),
                ('target_node_id', models.CharField(max_length=100, verbose_name='Nó de destino')),
                ('source_handle', models.CharField(blank=True, max_length=50, verbose_name='Handle de origem')),
                ('target_handle', models.CharField(blank=True, max_length=50, verbose_name='Handle de destino')),
                ('label', models.CharField(blank=True, max_length=100, verbose_name='Rótulo')),
                ('condition', models.CharField(blank=True, max_length=200, verbose_name='Condição')),
                ('data', models.JSONField(blank=True, default=dict, verbose_name='Dados extras')),
                ('template', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='edges',
                    to='workflow_definition.flowtemplate',
                    verbose_name='Template',
                )),
            ],
            options={
                'verbose_name': 'Conexão de Fluxo',
                'verbose_name_plural': 'Conexões de Fluxo',
            },
        ),
        migrations.CreateModel(
            name='FlowVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('version_number', models.PositiveIntegerField(verbose_name='Número da versão')),
                ('snapshot', models.JSONField(verbose_name='Snapshot completo')),
                ('published_at', models.DateTimeField(auto_now_add=True, verbose_name='Publicado em')),
                ('notes', models.TextField(blank=True, verbose_name='Notas da versão')),
                ('template', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='versions',
                    to='workflow_definition.flowtemplate',
                    verbose_name='Template',
                )),
                ('published_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='published_flow_versions',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Publicado por',
                )),
            ],
            options={
                'verbose_name': 'Versão do Fluxo',
                'verbose_name_plural': 'Versões do Fluxo',
                'ordering': ['-published_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='flownode',
            unique_together={('template', 'node_id')},
        ),
        migrations.AlterUniqueTogether(
            name='flowedge',
            unique_together={('template', 'edge_id')},
        ),
        migrations.AlterUniqueTogether(
            name='flowversion',
            unique_together={('template', 'version_number')},
        ),
    ]
