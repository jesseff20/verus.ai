"""
Add LegalContract, HonorariosDetail, ProcuracaoDetail, and SubstabelecimentoDetail models.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0012_electronic_protocol'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalContract',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('contract_type', models.CharField(choices=[('honorarios', 'Contrato de Honorários'), ('procuracao', 'Procuração'), ('substabelecimento', 'Substabelecimento')], max_length=20, verbose_name='Tipo de Contrato')),
                ('title', models.CharField(max_length=300, verbose_name='Título')),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('pending_signature', 'Aguardando Assinatura'), ('signed', 'Assinado'), ('cancelled', 'Cancelado'), ('expired', 'Expirado')], default='draft', max_length=20, verbose_name='Status')),
                ('content_html', models.TextField(blank=True, verbose_name='Conteúdo HTML')),
                ('generated_pdf', models.FileField(blank=True, null=True, upload_to='contratos/pdfs/', verbose_name='PDF Gerado')),
                ('signed_at', models.DateTimeField(blank=True, null=True, verbose_name='Assinado em')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expira em')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadados')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('case', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratos', to='cases.legalcase', verbose_name='Caso Jurídico')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contratos', to='cases.client', verbose_name='Cliente')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratos_criados', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
            ],
            options={
                'verbose_name': 'Contrato Jurídico',
                'verbose_name_plural': 'Contratos Jurídicos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='legalcontract',
            index=models.Index(fields=['contract_type'], name='cases_legal_contrac_8f1e2a_idx'),
        ),
        migrations.AddIndex(
            model_name='legalcontract',
            index=models.Index(fields=['status'], name='cases_legal_status_c3d4e5_idx'),
        ),
        migrations.AddIndex(
            model_name='legalcontract',
            index=models.Index(fields=['client'], name='cases_legal_client_f6g7h8_idx'),
        ),
        migrations.AddIndex(
            model_name='legalcontract',
            index=models.Index(fields=['created_by'], name='cases_legal_created_i9j0k1_idx'),
        ),
        migrations.CreateModel(
            name='HonorariosDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fee_type', models.CharField(choices=[('fixed', 'Valor Fixo'), ('hourly', 'Por Hora'), ('success', 'Êxito'), ('mixed', 'Misto')], max_length=10, verbose_name='Tipo de Honorário')),
                ('fixed_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor Fixo (R$)')),
                ('hourly_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor por Hora (R$)')),
                ('success_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Percentual de Êxito (%)')),
                ('estimated_hours', models.IntegerField(blank=True, null=True, verbose_name='Horas Estimadas')),
                ('payment_terms', models.TextField(blank=True, verbose_name='Condições de Pagamento')),
                ('installments', models.IntegerField(default=1, verbose_name='Parcelas')),
                ('includes_expenses', models.BooleanField(default=False, verbose_name='Inclui Despesas')),
                ('contract', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='honorarios_detail', to='cases.legalcontract', verbose_name='Contrato')),
            ],
            options={
                'verbose_name': 'Detalhe de Honorários',
                'verbose_name_plural': 'Detalhes de Honorários',
            },
        ),
        migrations.CreateModel(
            name='ProcuracaoDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('powers_type', models.CharField(choices=[('general', 'Poderes Gerais'), ('special', 'Poderes Especiais'), ('ad_judicia', 'Ad Judicia'), ('ad_judicia_extra', 'Ad Judicia et Extra')], max_length=20, verbose_name='Tipo de Poderes')),
                ('special_powers', models.TextField(blank=True, verbose_name='Poderes Especiais')),
                ('court_scope', models.CharField(blank=True, default='Todos os foros e instâncias', max_length=300, verbose_name='Abrangência')),
                ('valid_until', models.DateField(blank=True, null=True, verbose_name='Válida até')),
                ('is_irrevocable', models.BooleanField(default=False, verbose_name='Irrevogável')),
                ('contract', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='procuracao_detail', to='cases.legalcontract', verbose_name='Contrato')),
            ],
            options={
                'verbose_name': 'Detalhe de Procuração',
                'verbose_name_plural': 'Detalhes de Procuração',
            },
        ),
        migrations.CreateModel(
            name='SubstabelecimentoDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('substabelecido_name', models.CharField(max_length=300, verbose_name='Nome do Substabelecido')),
                ('substabelecido_oab', models.CharField(max_length=20, verbose_name='OAB do Substabelecido')),
                ('substabelecido_oab_state', models.CharField(max_length=2, verbose_name='UF da OAB')),
                ('with_reserve', models.BooleanField(default=True, verbose_name='Com Reserva de Poderes')),
                ('powers_transferred', models.TextField(blank=True, verbose_name='Poderes Transferidos')),
                ('reason', models.TextField(blank=True, verbose_name='Motivo')),
                ('contract', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='substabelecimento_detail', to='cases.legalcontract', verbose_name='Contrato')),
                ('original_procuracao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='substabelecimentos', to='cases.legalcontract', verbose_name='Procuração Original')),
            ],
            options={
                'verbose_name': 'Detalhe de Substabelecimento',
                'verbose_name_plural': 'Detalhes de Substabelecimento',
            },
        ),
    ]
