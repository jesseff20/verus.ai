"""
Add CourtFeeGuide, DigitalSignature, and SignatureVerification models.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0013_legal_contracts'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourtFeeGuide',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fee_type', models.CharField(choices=[('custas_iniciais', 'Custas Iniciais'), ('custas_recursais', 'Custas Recursais'), ('custas_preparo', 'Preparo'), ('taxa_judiciaria', 'Taxa Judiciária'), ('porte_remessa', 'Porte de Remessa'), ('diligencia', 'Diligência'), ('pericia', 'Perícia'), ('outros', 'Outros')], max_length=20, verbose_name='Tipo de Custa')),
                ('court', models.CharField(max_length=100, verbose_name='Tribunal')),
                ('state', models.CharField(max_length=2, verbose_name='UF')),
                ('calculated_amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Valor Calculado (R$)')),
                ('case_value', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='Valor da Causa (R$)')),
                ('calculation_formula', models.TextField(blank=True, verbose_name='Fórmula de Cálculo')),
                ('due_date', models.DateField(verbose_name='Data de Vencimento')),
                ('payment_status', models.CharField(choices=[('pending', 'Pendente'), ('paid', 'Pago'), ('overdue', 'Vencido'), ('exempt', 'Isento'), ('waived', 'Justiça Gratuita')], default='pending', max_length=10, verbose_name='Status do Pagamento')),
                ('payment_date', models.DateField(blank=True, null=True, verbose_name='Data do Pagamento')),
                ('payment_proof', models.FileField(blank=True, null=True, upload_to='court_fees/proofs/', verbose_name='Comprovante de Pagamento')),
                ('barcode', models.CharField(blank=True, max_length=100, verbose_name='Código de Barras (Boleto)')),
                ('guide_pdf', models.FileField(blank=True, null=True, upload_to='court_fees/guides/', verbose_name='Guia PDF')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='court_fees', to='cases.legalcase', verbose_name='Caso')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='court_fees_created', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
            ],
            options={
                'verbose_name': 'Guia de Custas',
                'verbose_name_plural': 'Guias de Custas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='courtfeeguide',
            index=models.Index(fields=['case', 'payment_status'], name='cases_court_case_id_payment_idx'),
        ),
        migrations.AddIndex(
            model_name='courtfeeguide',
            index=models.Index(fields=['due_date'], name='cases_court_due_date_idx'),
        ),
        migrations.AddIndex(
            model_name='courtfeeguide',
            index=models.Index(fields=['payment_status'], name='cases_court_pay_status_idx'),
        ),
        migrations.CreateModel(
            name='DigitalSignature',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('signature_type', models.CharField(choices=[('simple', 'Assinatura Simples'), ('advanced', 'Assinatura Avançada'), ('qualified', 'Assinatura Qualificada ICP-Brasil')], default='simple', max_length=10, verbose_name='Tipo de Assinatura')),
                ('signature_hash', models.CharField(help_text='Hash SHA-256 do conteúdo assinado', max_length=64, verbose_name='Hash SHA-256')),
                ('certificate_info', models.JSONField(blank=True, null=True, verbose_name='Informações do Certificado')),
                ('ip_address', models.GenericIPAddressField(verbose_name='Endereço IP')),
                ('signed_at', models.DateTimeField(auto_now_add=True, verbose_name='Assinado em')),
                ('is_valid', models.BooleanField(default=True, verbose_name='Válida')),
                ('verification_url', models.URLField(blank=True, verbose_name='URL de Verificação')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadados')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='digital_signatures', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
                ('document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signatures', to='cases.casedocument', verbose_name='Documento')),
                ('contract', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signatures', to='cases.legalcontract', verbose_name='Contrato')),
            ],
            options={
                'verbose_name': 'Assinatura Digital',
                'verbose_name_plural': 'Assinaturas Digitais',
                'ordering': ['-signed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='digitalsignature',
            index=models.Index(fields=['user', 'signed_at'], name='cases_digsig_user_signed_idx'),
        ),
        migrations.AddIndex(
            model_name='digitalsignature',
            index=models.Index(fields=['signature_hash'], name='cases_digsig_hash_idx'),
        ),
        migrations.AddIndex(
            model_name='digitalsignature',
            index=models.Index(fields=['document'], name='cases_digsig_document_idx'),
        ),
        migrations.CreateModel(
            name='SignatureVerification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('verified_at', models.DateTimeField(auto_now_add=True, verbose_name='Verificado em')),
                ('is_valid', models.BooleanField(verbose_name='Válida')),
                ('verification_details', models.JSONField(blank=True, default=dict, verbose_name='Detalhes da Verificação')),
                ('signature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verifications', to='cases.digitalsignature', verbose_name='Assinatura')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signature_verifications', to=settings.AUTH_USER_MODEL, verbose_name='Verificado por')),
            ],
            options={
                'verbose_name': 'Verificação de Assinatura',
                'verbose_name_plural': 'Verificações de Assinatura',
                'ordering': ['-verified_at'],
            },
        ),
    ]
