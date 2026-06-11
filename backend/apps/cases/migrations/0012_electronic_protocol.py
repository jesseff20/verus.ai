"""
Add ElectronicProtocol, TribunalPushConfig, and TribunalPushEvent models.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0011_client_portal_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElectronicProtocol',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('protocol_number', models.CharField(blank=True, max_length=50, verbose_name='Número do Protocolo')),
                ('court_system', models.CharField(choices=[('pje', 'PJe'), ('esaj', 'e-SAJ'), ('projudi', 'PROJUDI'), ('eproc', 'e-Proc'), ('sei', 'SEI'), ('manual', 'Manual')], max_length=10, verbose_name='Sistema do Tribunal')),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('pending', 'Pendente'), ('submitted', 'Protocolado'), ('accepted', 'Aceito'), ('rejected', 'Rejeitado'), ('error', 'Erro')], default='draft', max_length=10, verbose_name='Status')),
                ('petition_type', models.CharField(help_text='Ex: Petição Inicial, Contestação, Recurso', max_length=100, verbose_name='Tipo de Petição')),
                ('submitted_at', models.DateTimeField(blank=True, null=True, verbose_name='Submetido em')),
                ('accepted_at', models.DateTimeField(blank=True, null=True, verbose_name='Aceito em')),
                ('protocol_receipt', models.TextField(blank=True, verbose_name='Comprovante do Protocolo')),
                ('error_message', models.TextField(blank=True, verbose_name='Mensagem de Erro')),
                ('retry_count', models.IntegerField(default=0, verbose_name='Tentativas')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadados')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='protocolos', to='cases.legalcase', verbose_name='Caso')),
                ('document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='protocolos', to='cases.casedocument', verbose_name='Documento')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='protocolos_criados', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
            ],
            options={
                'verbose_name': 'Protocolo Eletrônico',
                'verbose_name_plural': 'Protocolos Eletrônicos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='electronicprotocol',
            index=models.Index(fields=['case', 'status'], name='cases_elect_case_id_idx'),
        ),
        migrations.AddIndex(
            model_name='electronicprotocol',
            index=models.Index(fields=['court_system'], name='cases_elect_court_s_idx'),
        ),
        migrations.AddIndex(
            model_name='electronicprotocol',
            index=models.Index(fields=['created_by'], name='cases_elect_created_idx'),
        ),
        migrations.CreateModel(
            name='TribunalPushConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('court_system', models.CharField(choices=[('pje', 'PJe'), ('esaj', 'e-SAJ'), ('projudi', 'PROJUDI'), ('eproc', 'e-Proc'), ('sei', 'SEI'), ('manual', 'Manual')], max_length=10, verbose_name='Sistema do Tribunal')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('check_interval_hours', models.IntegerField(default=24, verbose_name='Intervalo de Verificação (horas)')),
                ('last_checked', models.DateTimeField(blank=True, null=True, verbose_name='Última Verificação')),
                ('notification_types', models.JSONField(blank=True, default=list, help_text='Lista de tipos de evento para monitorar', verbose_name='Tipos de Notificação')),
                ('credentials_encrypted', models.TextField(blank=True, verbose_name='Credenciais (criptografadas)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tribunal_push_configs', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Configuração de Acompanhamento',
                'verbose_name_plural': 'Configurações de Acompanhamento',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='tribunalpushconfig',
            index=models.Index(fields=['user', 'court_system'], name='cases_tribp_user_co_idx'),
        ),
        migrations.AddIndex(
            model_name='tribunalpushconfig',
            index=models.Index(fields=['is_active'], name='cases_tribp_active_idx'),
        ),
        migrations.CreateModel(
            name='TribunalPushEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(help_text='Ex: movimentacao, intimacao, publicacao, despacho', max_length=50, verbose_name='Tipo de Evento')),
                ('event_date', models.DateTimeField(verbose_name='Data do Evento')),
                ('description', models.TextField(verbose_name='Descrição')),
                ('raw_data', models.JSONField(blank=True, default=dict, verbose_name='Dados Brutos')),
                ('is_processed', models.BooleanField(default=False, verbose_name='Processado')),
                ('notification_sent', models.BooleanField(default=False, verbose_name='Notificação Enviada')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='cases.tribunalpushconfig', verbose_name='Configuração')),
                ('case', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tribunal_events', to='cases.legalcase', verbose_name='Caso')),
            ],
            options={
                'verbose_name': 'Evento de Tribunal',
                'verbose_name_plural': 'Eventos de Tribunal',
                'ordering': ['-event_date'],
            },
        ),
        migrations.AddIndex(
            model_name='tribunalpushevent',
            index=models.Index(fields=['config', 'is_processed'], name='cases_tribe_config_idx'),
        ),
        migrations.AddIndex(
            model_name='tribunalpushevent',
            index=models.Index(fields=['event_type'], name='cases_tribe_evtype_idx'),
        ),
        migrations.AddIndex(
            model_name='tribunalpushevent',
            index=models.Index(fields=['event_date'], name='cases_tribe_evdate_idx'),
        ),
    ]
