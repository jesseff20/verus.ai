"""
Migration inicial para o app signature.
Cria as tabelas DigitalSignature e SignerKey.
"""
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
            name='SignerKey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('public_key_pem', models.TextField(verbose_name='Chave Pública (PEM)')),
                ('private_key_encrypted', models.BinaryField(verbose_name='Chave Privada (cifrada)')),
                ('fingerprint', models.CharField(max_length=64, unique=True, verbose_name='Fingerprint')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='signer_key',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Chave do Assinante',
                'verbose_name_plural': 'Chaves dos Assinantes',
            },
        ),
        migrations.CreateModel(
            name='DigitalSignature',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('document_type', models.CharField(
                    help_text='Ex: despacho, parecer, petição, ata',
                    max_length=50,
                    verbose_name='Tipo de Documento',
                )),
                ('document_ref', models.CharField(
                    help_text='ID do objeto assinado (UUID do despacho, tarefa, etc.)',
                    max_length=255,
                    verbose_name='Referência do Documento',
                )),
                ('document_title', models.CharField(blank=True, max_length=500, verbose_name='Título')),
                ('content_hash', models.CharField(
                    help_text='SHA-256 hex do conteúdo no momento da assinatura',
                    max_length=64,
                    verbose_name='Hash do Conteúdo',
                )),
                ('provider', models.CharField(
                    choices=[
                        ('internal', 'Assinatura Interna (Verus.AI)'),
                        ('govbr', 'Gov.BR (Governo Federal)'),
                        ('icpbrasil', 'ICP-Brasil (Certificado Digital A1/A3)'),
                        ('docusign', 'DocuSign'),
                        ('certisign', 'Certisign'),
                        ('serpro', 'Serpro (Assinador SERPRO)'),
                    ],
                    default='internal',
                    max_length=20,
                    verbose_name='Provider',
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Aguardando Assinatura'),
                        ('signed', 'Assinado'),
                        ('rejected', 'Rejeitado'),
                        ('expired', 'Expirado'),
                        ('revoked', 'Revogado'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('signature_data', models.TextField(
                    blank=True,
                    help_text='Base64 da assinatura RSA (internal) ou token do provider externo',
                    verbose_name='Dados da Assinatura',
                )),
                ('public_key_fingerprint', models.CharField(
                    blank=True,
                    help_text='SHA-256 da chave pública usada (apenas para provider interno)',
                    max_length=64,
                    verbose_name='Fingerprint da Chave Pública',
                )),
                ('signed_at', models.DateTimeField(blank=True, null=True, verbose_name='Assinado em')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Válido até')),
                ('signer_ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP do Assinante')),
                ('signer_user_agent', models.CharField(blank=True, max_length=500, verbose_name='User-Agent')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organ', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='signatures',
                    to='organization.organ',
                )),
                ('signer', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='signatures',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Assinante',
                )),
            ],
            options={
                'verbose_name': 'Assinatura Digital',
                'verbose_name_plural': 'Assinaturas Digitais',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='digitalsignature',
            index=models.Index(fields=['document_ref', 'document_type'], name='sig_docref_type_idx'),
        ),
        migrations.AddIndex(
            model_name='digitalsignature',
            index=models.Index(fields=['signer', 'status'], name='sig_signer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='digitalsignature',
            index=models.Index(fields=['content_hash'], name='sig_content_hash_idx'),
        ),
    ]
