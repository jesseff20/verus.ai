# Generated migration for Integration models

from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TribunalIntegration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='Nome')),
                ('code', models.CharField(help_text='Ex: TJSP, TJMG, TRT-2, JFSP', max_length=20, unique=True, verbose_name='Código')),
                ('system_type', models.CharField(choices=[('esaj', 'e-SAJ'), ('pje', 'PJe'), ('eproc', 'Eproc'), ('projudi', 'Projudi'), ('outro', 'Outro')], default='esaj', max_length=20, verbose_name='Tipo de Sistema')),
                ('api_endpoint', models.URLField(blank=True, help_text='URL base da API do tribunal', verbose_name='Endpoint da API')),
                ('requires_certificate', models.BooleanField(default=True, verbose_name='Requer Certificado Digital')),
                ('certificate_file', models.FileField(blank=True, null=True, upload_to='integrations/certificates/', verbose_name='Arquivo do Certificado')),
                ('certificate_password', models.CharField(blank=True, max_length=500, verbose_name='Senha do Certificado')),
                ('username', models.CharField(blank=True, max_length=200, verbose_name='Usuário')),
                ('password', models.CharField(blank=True, max_length=500, verbose_name='Senha')),
                ('api_key', models.CharField(blank=True, max_length=500, verbose_name='API Key')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('last_connection_test', models.DateTimeField(blank=True, null=True, verbose_name='Último teste de conexão')),
                ('connection_status', models.CharField(choices=[('connected', 'Conectado'), ('error', 'Erro'), ('testing', 'Testando'), ('unknown', 'Desconhecido')], default='unknown', max_length=20, verbose_name='Status da Conexão')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Integração com Tribunal',
                'verbose_name_plural': 'Integrações com Tribunais',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProcessSync',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('process_number', models.CharField(db_index=True, max_length=50, verbose_name='Número do Processo')),
                ('case_id', models.UUIDField(blank=True, help_text='ID do caso no Verus.AI', null=True, verbose_name='ID do Caso (interno)')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('syncing', 'Sincronizando'), ('completed', 'Completo'), ('error', 'Erro')], default='pending', max_length=20, verbose_name='Status')),
                ('last_sync_at', models.DateTimeField(blank=True, null=True, verbose_name='Última sincronização')),
                ('next_sync_at', models.DateTimeField(blank=True, null=True, verbose_name='Próxima sincronização')),
                ('sync_count', models.IntegerField(default=0, verbose_name='Número de sincronizações')),
                ('last_error', models.TextField(blank=True, verbose_name='Último erro')),
                ('last_error_at', models.DateTimeField(blank=True, null=True, verbose_name='Erro em')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('tribunal', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='process_syncs', to='integration.tribunalintegration', verbose_name='Tribunal')),
            ],
            options={
                'verbose_name': 'Sincronização de Processo',
                'verbose_name_plural': 'Sincronizações de Processo',
                'ordering': ['-last_sync_at'],
            },
        ),
        migrations.CreateModel(
            name='ProcessMovement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('movement_date', models.DateTimeField(verbose_name='Data da Movimentação')),
                ('movement_code', models.CharField(blank=True, help_text='Código CNM do tribunal', max_length=50, verbose_name='Código da Movimentação')),
                ('movement_description', models.TextField(verbose_name='Descrição')),
                ('complement', models.TextField(blank=True, verbose_name='Complemento')),
                ('document_id', models.CharField(blank=True, help_text='ID do documento no tribunal', max_length=100, verbose_name='ID do Documento')),
                ('source', models.CharField(default='tribunal', help_text='Fonte da movimentação', max_length=50, verbose_name='Origem')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('process_sync', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='movements', to='integration.processsync', verbose_name='Sincronização')),
            ],
            options={
                'verbose_name': 'Movimentação Processual',
                'verbose_name_plural': 'Movimentações Processuais',
                'ordering': ['-movement_date'],
            },
        ),
        migrations.CreateModel(
            name='PetitionProtocol',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('process_number', models.CharField(blank=True, help_text='Vazio para protocolo inicial', max_length=50, verbose_name='Número do Processo')),
                ('petition_type', models.CharField(choices=[('inicial', 'Petição Inicial'), ('contestacao', 'Contestação'), ('replica', 'Réplica'), ('recurso', 'Recurso'), ('pedido', 'Pedido'), ('outro', 'Outro')], default='outro', max_length=100, verbose_name='Tipo de Petição')),
                ('petition_title', models.CharField(max_length=500, verbose_name='Título')),
                ('petition_content', models.TextField(verbose_name='Conteúdo')),
                ('attachments', models.JSONField(default=list, help_text='Lista de documentos anexados', verbose_name='Anexos')),
                ('protocol_number', models.CharField(blank=True, help_text='Número gerado pelo tribunal', max_length=100, verbose_name='Número do Protocolo')),
                ('protocol_date', models.DateTimeField(blank=True, null=True, verbose_name='Data do Protocolo')),
                ('protocol_receipt', models.FileField(blank=True, null=True, upload_to='integrations/protocols/', verbose_name='Recibo do Protocolo')),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('sending', 'Enviando'), ('sent', 'Enviada'), ('confirmed', 'Confirmada'), ('rejected', 'Rejeitada'), ('error', 'Erro')], default='draft', max_length=20, verbose_name='Status')),
                ('last_error', models.TextField(blank=True, verbose_name='Último erro')),
                ('last_error_at', models.DateTimeField(blank=True, null=True, verbose_name='Erro em')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('tribunal', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='petitions', to='integration.tribunalintegration', verbose_name='Tribunal')),
                ('created_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='filed_petitions', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
            ],
            options={
                'verbose_name': 'Protocolo de Petição',
                'verbose_name_plural': 'Protocolos de Petição',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='tribunalintegration',
            index=models.Index(fields=['code'], name='integration_code_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='tribunalintegration',
            index=models.Index(fields=['system_type'], name='integration_system_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='processsync',
            index=models.Index(fields=['process_number'], name='integration_process_g7h8i9_idx'),
        ),
        migrations.AddIndex(
            model_name='processsync',
            index=models.Index(fields=['case_id'], name='integration_case_i_j0k1l2_idx'),
        ),
        migrations.AddIndex(
            model_name='processsync',
            index=models.Index(fields=['status'], name='integration_status_m3n4o5_idx'),
        ),
        migrations.AddIndex(
            model_name='processmovement',
            index=models.Index(fields=['process_sync', '-movement_date'], name='integration_process_p6q7r8_idx'),
        ),
        migrations.AddIndex(
            model_name='processmovement',
            index=models.Index(fields=['movement_code'], name='integration_movemen_s9t0u1_idx'),
        ),
        migrations.AddIndex(
            model_name='petitionprotocol',
            index=models.Index(fields=['process_number'], name='integration_process_v2w3x4_idx'),
        ),
        migrations.AddIndex(
            model_name='petitionprotocol',
            index=models.Index(fields=['protocol_number'], name='integration_protoco_y5z6a7_idx'),
        ),
        migrations.AddIndex(
            model_name='petitionprotocol',
            index=models.Index(fields=['status'], name='integration_status_b8c9d0_idx'),
        ),
        migrations.AddConstraint(
            model_name='processsync',
            constraint=models.UniqueConstraint(fields=('tribunal', 'process_number'), name='unique_tribunal_process'),
        ),
    ]
