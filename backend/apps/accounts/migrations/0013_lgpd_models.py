"""
LGPD models: ConsentTerm, ConsentRecord, DataProcessingActivity, DataSubjectRequest.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_notificationchannel_notificationmessage'),
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsentTerm',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=300, verbose_name='Titulo')),
                ('version', models.CharField(max_length=20, verbose_name='Versao')),
                ('content', models.TextField(help_text='HTML do termo', verbose_name='Conteudo')),
                ('purpose', models.CharField(
                    choices=[
                        ('data_processing', 'Tratamento de dados'),
                        ('marketing', 'Marketing'),
                        ('sharing', 'Compartilhamento de dados'),
                    ],
                    default='data_processing',
                    max_length=100,
                    verbose_name='Finalidade',
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='consent_terms_created',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
            ],
            options={
                'verbose_name': 'Termo de Consentimento',
                'verbose_name_plural': 'Termos de Consentimento',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ConsentRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('granted', models.BooleanField(default=True, verbose_name='Concedido')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Endereco IP')),
                ('granted_at', models.DateTimeField(auto_now_add=True, verbose_name='Concedido em')),
                ('revoked_at', models.DateTimeField(blank=True, null=True, verbose_name='Revogado em')),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='consents',
                    to='cases.client',
                    verbose_name='Cliente',
                )),
                ('consent_term', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='records',
                    to='accounts.consentterm',
                    verbose_name='Termo de Consentimento',
                )),
            ],
            options={
                'verbose_name': 'Registro de Consentimento',
                'verbose_name_plural': 'Registros de Consentimento',
                'ordering': ['-granted_at'],
            },
        ),
        migrations.CreateModel(
            name='DataProcessingActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=300, verbose_name='Nome')),
                ('purpose', models.TextField(verbose_name='Finalidade')),
                ('legal_basis', models.CharField(
                    choices=[
                        ('consent', 'Consentimento'),
                        ('contract', 'Execucao de contrato'),
                        ('legal_obligation', 'Obrigacao legal'),
                        ('legitimate_interest', 'Interesse legitimo'),
                        ('judicial_process', 'Exercicio regular de direito em processo'),
                        ('life_protection', 'Protecao da vida'),
                        ('public_policy', 'Politicas publicas'),
                    ],
                    max_length=100,
                    verbose_name='Base legal',
                )),
                ('data_categories', models.JSONField(blank=True, default=list, verbose_name='Categorias de dados')),
                ('retention_period', models.CharField(max_length=100, verbose_name='Periodo de retencao')),
                ('shared_with', models.JSONField(blank=True, default=list, verbose_name='Compartilhado com')),
                ('risk_level', models.CharField(
                    choices=[
                        ('baixo', 'Baixo'),
                        ('medio', 'Medio'),
                        ('alto', 'Alto'),
                    ],
                    default='baixo',
                    max_length=20,
                    verbose_name='Nivel de risco',
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
            ],
            options={
                'verbose_name': 'Atividade de Tratamento de Dados',
                'verbose_name_plural': 'Atividades de Tratamento de Dados',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DataSubjectRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('request_type', models.CharField(
                    choices=[
                        ('access', 'Acesso aos dados'),
                        ('rectification', 'Retificacao'),
                        ('deletion', 'Eliminacao'),
                        ('portability', 'Portabilidade'),
                        ('objection', 'Oposicao'),
                    ],
                    max_length=30,
                    verbose_name='Tipo de solicitacao',
                )),
                ('description', models.TextField(verbose_name='Descricao')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pendente'),
                        ('in_progress', 'Em andamento'),
                        ('completed', 'Concluida'),
                        ('rejected', 'Rejeitada'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('response', models.TextField(blank=True, verbose_name='Resposta')),
                ('requested_at', models.DateTimeField(auto_now_add=True, verbose_name='Solicitado em')),
                ('responded_at', models.DateTimeField(blank=True, null=True, verbose_name='Respondido em')),
                ('client', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dsr_requests',
                    to='cases.client',
                    verbose_name='Cliente',
                )),
            ],
            options={
                'verbose_name': 'Solicitacao do Titular',
                'verbose_name_plural': 'Solicitacoes do Titular',
                'ordering': ['-requested_at'],
            },
        ),
    ]
