import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organization', '0001_initial'),
        ('workflow_definition', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FlowInstance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('case_ref', models.CharField(blank=True, help_text='UUID do caso, número do processo CNJ, etc.', max_length=200, verbose_name='Referência do processo')),
                ('case_title', models.CharField(blank=True, help_text='Nome ou ementa para exibição', max_length=300, verbose_name='Título do processo')),
                ('status', models.CharField(choices=[('pending', 'Aguardando início'), ('running', 'Em andamento'), ('completed', 'Concluído'), ('cancelled', 'Cancelado')], default='pending', max_length=15, verbose_name='Status')),
                ('current_node_id', models.CharField(blank=True, max_length=100, verbose_name='Nó atual (node_id)')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='Iniciado em')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Concluído em')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('template_name_snapshot', models.CharField(blank=True, max_length=200, verbose_name='Nome do template (snapshot)')),
                ('template_version_snapshot', models.PositiveIntegerField(default=1, verbose_name='Versão do template (snapshot)')),
                ('organ', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flow_instances', to='organization.organ', verbose_name='Órgão')),
                ('started_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='started_flow_instances', to=settings.AUTH_USER_MODEL, verbose_name='Iniciado por')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='instances', to='workflow_definition.flowtemplate', verbose_name='Template de fluxo')),
            ],
            options={
                'verbose_name': 'Instância de Fluxo',
                'verbose_name_plural': 'Instâncias de Fluxo',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskInstance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('node_id', models.CharField(max_length=100, verbose_name='ID do nó (node_id)')),
                ('node_type', models.CharField(max_length=30, verbose_name='Tipo do nó')),
                ('label', models.CharField(max_length=200, verbose_name='Rótulo')),
                ('role_required', models.CharField(default='any', max_length=25, verbose_name='Papel requerido')),
                ('instructions', models.TextField(blank=True, verbose_name='Instruções')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('in_progress', 'Em andamento'), ('completed', 'Concluído'), ('skipped', 'Pulado')], default='pending', max_length=15, verbose_name='Status')),
                ('gateway_choice', models.CharField(blank=True, help_text='Handle de saída selecionado no gateway exclusivo', max_length=100, verbose_name='Branch escolhido (gateway)')),
                ('due_date', models.DateField(blank=True, null=True, verbose_name='Prazo')),
                ('notes', models.TextField(blank=True, verbose_name='Observações ao concluir')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='Iniciado em')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Concluído em')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tasks', to=settings.AUTH_USER_MODEL, verbose_name='Atribuído a')),
                ('completed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_tasks', to=settings.AUTH_USER_MODEL, verbose_name='Concluído por')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='workflow_execution.flowinstance', verbose_name='Instância do fluxo')),
            ],
            options={
                'verbose_name': 'Tarefa',
                'verbose_name_plural': 'Tarefas',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('request_type', models.CharField(choices=[('redistribuicao', 'Redistribuição'), ('avocacao', 'Avocação'), ('assessoria', 'Pedido de Assessoria')], max_length=20, verbose_name='Tipo')),
                ('justification', models.TextField(verbose_name='Justificativa')),
                ('status', models.CharField(choices=[('pending', 'Aguardando aprovação'), ('approved', 'Aprovado'), ('rejected', 'Rejeitado')], default='pending', max_length=15, verbose_name='Status')),
                ('resolution_note', models.TextField(blank=True, verbose_name='Nota de resolução')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='Resolvido em')),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_requests_made', to=settings.AUTH_USER_MODEL, verbose_name='Solicitante')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_requests_resolved', to=settings.AUTH_USER_MODEL, verbose_name='Resolvido por')),
                ('target_user', models.ForeignKey(blank=True, help_text='Para redistribuição: quem vai receber a tarefa', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_requests_received', to=settings.AUTH_USER_MODEL, verbose_name='Usuário destino')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='workflow_execution.taskinstance', verbose_name='Tarefa')),
            ],
            options={
                'verbose_name': 'Solicitação de Tarefa',
                'verbose_name_plural': 'Solicitações de Tarefas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ExecutionEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(choices=[('flow_started', 'Fluxo iniciado'), ('flow_completed', 'Fluxo concluído'), ('flow_cancelled', 'Fluxo cancelado'), ('task_created', 'Tarefa criada'), ('task_started', 'Tarefa iniciada'), ('task_completed', 'Tarefa concluída'), ('task_skipped', 'Tarefa pulada'), ('task_reassigned', 'Tarefa reatribuída'), ('gateway_evaluated', 'Gateway avaliado'), ('request_created', 'Solicitação criada'), ('request_approved', 'Solicitação aprovada'), ('request_rejected', 'Solicitação rejeitada')], max_length=30, verbose_name='Tipo de evento')),
                ('node_id', models.CharField(blank=True, max_length=100, verbose_name='Node ID')),
                ('node_label', models.CharField(blank=True, max_length=200, verbose_name='Label do nó')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadados')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data/hora')),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='execution_events', to=settings.AUTH_USER_MODEL, verbose_name='Ator')),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='workflow_execution.flowinstance', verbose_name='Instância do fluxo')),
            ],
            options={
                'verbose_name': 'Evento de Execução',
                'verbose_name_plural': 'Eventos de Execução',
                'ordering': ['created_at'],
            },
        ),
    ]
