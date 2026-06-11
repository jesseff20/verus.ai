"""
Models para assinaturas digitais de documentos e despachos.
"""
import uuid
from django.db import models
from django.conf import settings


class SignatureProvider(models.TextChoices):
    INTERNAL = 'internal', 'Assinatura Interna (Verus.AI)'
    GOVBR = 'govbr', 'Gov.BR (Governo Federal)'
    ICPBRASIL = 'icpbrasil', 'ICP-Brasil (Certificado Digital A1/A3)'
    DOCUSIGN = 'docusign', 'DocuSign'
    CERTISIGN = 'certisign', 'Certisign'
    SERPRO = 'serpro', 'Serpro (Assinador SERPRO)'


class SignatureStatus(models.TextChoices):
    PENDING = 'pending', 'Aguardando Assinatura'
    SIGNED = 'signed', 'Assinado'
    REJECTED = 'rejected', 'Rejeitado'
    EXPIRED = 'expired', 'Expirado'
    REVOKED = 'revoked', 'Revogado'


class DigitalSignature(models.Model):
    """
    Representa a assinatura digital de um documento ou despacho.

    Cada assinatura está vinculada a:
    - Um usuário assinante
    - Um conteúdo a assinar (hash SHA-256 do conteúdo)
    - Um provider de assinatura
    - Metadados de auditoria (IP, data, validade)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Quem assina
    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='signatures',
        verbose_name='Assinante',
    )

    # O que está sendo assinado
    document_type = models.CharField(
        'Tipo de Documento', max_length=50,
        help_text='Ex: despacho, parecer, petição, ata'
    )
    document_ref = models.CharField(
        'Referência do Documento', max_length=255,
        help_text='ID do objeto assinado (UUID do despacho, tarefa, etc.)'
    )
    document_title = models.CharField('Título', max_length=500, blank=True)

    # Hash do conteúdo assinado (SHA-256, hex)
    content_hash = models.CharField(
        'Hash do Conteúdo', max_length=64,
        help_text='SHA-256 hex do conteúdo no momento da assinatura'
    )

    # Provider e dados técnicos
    provider = models.CharField(
        'Provider', max_length=20,
        choices=SignatureProvider.choices,
        default=SignatureProvider.INTERNAL,
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=SignatureStatus.choices,
        default=SignatureStatus.PENDING,
    )

    # Dados da assinatura (variam por provider)
    signature_data = models.TextField(
        'Dados da Assinatura', blank=True,
        help_text='Base64 da assinatura RSA (internal) ou token do provider externo'
    )
    public_key_fingerprint = models.CharField(
        'Fingerprint da Chave Pública', max_length=64, blank=True,
        help_text='SHA-256 da chave pública usada (apenas para provider interno)'
    )

    # Metadados de auditoria
    signed_at = models.DateTimeField('Assinado em', null=True, blank=True)
    expires_at = models.DateTimeField('Válido até', null=True, blank=True)
    signer_ip = models.GenericIPAddressField('IP do Assinante', null=True, blank=True)
    signer_user_agent = models.CharField('User-Agent', max_length=500, blank=True)

    # Vinculação ao órgão
    organ = models.ForeignKey(
        'organization.Organ',
        on_delete=models.PROTECT,
        related_name='signatures',
        null=True, blank=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Assinatura Digital'
        verbose_name_plural = 'Assinaturas Digitais'
        indexes = [
            models.Index(fields=['document_ref', 'document_type']),
            models.Index(fields=['signer', 'status']),
            models.Index(fields=['content_hash']),
        ]

    def __str__(self):
        return f'{self.get_provider_display()} — {self.document_title or self.document_ref} ({self.get_status_display()})'


class SignerKey(models.Model):
    """
    Par de chaves RSA gerado pela Verus.AI para cada usuário.
    Usado apenas pelo provider 'internal'.
    A chave privada é armazenada CRIPTOGRAFADA com a senha do usuário.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='signer_key',
    )
    public_key_pem = models.TextField('Chave Pública (PEM)')
    # ATENÇÃO: chave privada deve ser armazenada em HSM ou criptografada.
    # Em produção, usar AWS KMS ou Vault. Aqui armazenamos criptografada com FERNET.
    private_key_encrypted = models.BinaryField('Chave Privada (cifrada)')
    # Salt PBKDF2 de 16 bytes gerado aleatoriamente por chave.
    # Nullable para compatibilidade com registros legados (pré-KDF).
    private_key_salt = models.BinaryField(
        'Salt KDF (PBKDF2)',
        null=True,
        blank=True,
        help_text='Salt aleatório de 16 bytes usado na derivação PBKDF2 da chave Fernet.',
    )
    fingerprint = models.CharField('Fingerprint', max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Chave do Assinante'
        verbose_name_plural = 'Chaves dos Assinantes'

    def __str__(self):
        return f'Key:{self.fingerprint[:12]}... ({self.user})'

    @property
    def is_active(self):
        return self.revoked_at is None
