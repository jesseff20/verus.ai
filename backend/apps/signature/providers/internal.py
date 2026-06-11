"""
Provider de assinatura interna Verus.AI.

Implementação: RSA-2048 + SHA-256 (PKCS#1 v1.5 via cryptography library).
Cada usuário tem um par de chaves gerado na primeira assinatura.
A chave privada é armazenada cifrada com Fernet (AES-128-CBC + HMAC-SHA256).

Derivação de chave: PBKDF2-HMAC-SHA256 com 100 000 iterações e salt por registro.

Validade jurídica: baixa (sem ICP-Brasil). Indicada para uso interno/informal.
"""
import base64
import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta

from django.conf import settings

from .base import SignatureProviderBase, SignatureResult

logger = logging.getLogger(__name__)

# Iterações PBKDF2 — ajustável conforme política de segurança.
_PBKDF2_ITERATIONS = 100_000


def _derive_fernet_key(secret: str, salt: bytes) -> bytes:
    """
    Deriva uma chave Fernet de 32 bytes a partir de um segredo e um salt
    usando PBKDF2-HMAC-SHA256.

    Args:
        secret: segredo de entrada (normalmente Django SECRET_KEY).
        salt:   salt aleatório de 16 bytes específico do registro.

    Returns:
        Chave Fernet codificada em base64url (44 bytes).
    """
    key_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        secret.encode(),
        salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(key_bytes)


def _get_fernet_for_record(salt: bytes):
    """Retorna uma instância Fernet derivada do SECRET_KEY + salt do registro."""
    from cryptography.fernet import Fernet
    fernet_key = _derive_fernet_key(settings.SECRET_KEY, salt)
    return Fernet(fernet_key)


def _get_fernet_legacy():
    """
    Compatibilidade com registros criados antes da migração para PBKDF2.
    A derivação legada usava SHA-256 simples sem salt.

    ATENÇÃO: use apenas para descriptografar chaves antigas. Novos registros
    devem sempre usar _get_fernet_for_record().
    """
    from cryptography.fernet import Fernet
    key_material = settings.SECRET_KEY.encode()
    derived = hashlib.sha256(key_material).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


class InternalSignatureProvider(SignatureProviderBase):
    """
    Assinatura digital interna Verus.AI usando RSA-2048.
    """

    @classmethod
    def metadata(cls) -> dict:
        return {
            'id': 'internal',
            'name': 'Assinatura Interna Verus.AI',
            'description': 'Assinatura digital gerada pelo sistema Verus.AI usando RSA-2048. '
                           'Válida para uso interno e registros de auditoria.',
            'icon': 'shield-check',
            'available': True,
            'requires_config': [],
            'validade_anos': 2,
            'aceito_juridicamente': False,
            'observacao': 'Não tem validade jurídica externa (não é ICP-Brasil). '
                         'Use para controle interno e auditoria.',
        }

    def is_available(self) -> bool:
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa
            return True
        except ImportError:
            return False

    def _get_or_create_key(self, signer):
        """Retorna ou cria o par de chaves RSA para o usuário."""
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import hashes, serialization
        from apps.signature.models import SignerKey

        try:
            key_record = SignerKey.objects.get(user=signer)
            if not key_record.is_active:
                raise ValueError('Chave do usuário foi revogada.')

            # Descriptografa a chave privada.
            # Registros sem salt usam a derivação legada (SHA-256 simples).
            # Registros com salt usam PBKDF2 — caminho seguro.
            salt = bytes(key_record.private_key_salt) if key_record.private_key_salt else None
            if salt:
                fernet = _get_fernet_for_record(salt)
            else:
                logger.warning(
                    'SignerKey do usuário %s usa derivação legada (sem PBKDF2). '
                    'A chave será re-cifrada com PBKDF2 na próxima operação de escrita.',
                    signer.id,
                )
                fernet = _get_fernet_legacy()

            private_key_pem = fernet.decrypt(bytes(key_record.private_key_encrypted))
            private_key = serialization.load_pem_private_key(private_key_pem, password=None)
            return private_key, key_record.fingerprint

        except SignerKey.DoesNotExist:
            # Gera novo par de chaves RSA-2048
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            public_key = private_key.public_key()

            # Serializa
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode()

            # Fingerprint = SHA-256 da chave pública
            pub_der = public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            fingerprint = hashlib.sha256(pub_der).hexdigest()

            # Cifra a chave privada com Fernet + PBKDF2
            salt = os.urandom(16)
            fernet = _get_fernet_for_record(salt)
            private_encrypted = fernet.encrypt(private_pem)

            SignerKey.objects.create(
                user=signer,
                public_key_pem=public_pem,
                private_key_encrypted=private_encrypted,
                private_key_salt=salt,
                fingerprint=fingerprint,
            )

            logger.info('Par de chaves RSA gerado para usuário %s (PBKDF2)', signer.id)
            return private_key, fingerprint

    def sign(self, content_hash: str, signer, **kwargs) -> SignatureResult:
        try:
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes

            private_key, fingerprint = self._get_or_create_key(signer)

            # Converte o hash hex para bytes
            hash_bytes = bytes.fromhex(content_hash)

            # Assina com RSA-PKCS1v15 e SHA-256
            signature_bytes = private_key.sign(
                hash_bytes,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            signature_b64 = base64.b64encode(signature_bytes).decode()

            now = datetime.now(tz=timezone.utc)
            expires = now + timedelta(days=365 * 2)

            return SignatureResult(
                success=True,
                signature_data=signature_b64,
                public_key_fingerprint=fingerprint,
                signed_at=now.isoformat(),
                expires_at=expires.isoformat(),
            )

        except Exception as exc:
            logger.exception('Erro na assinatura interna: %s', exc)
            return SignatureResult(
                success=False,
                signature_data='',
                public_key_fingerprint='',
                signed_at='',
                expires_at=None,
                error=str(exc),
            )

    def verify(self, content_hash: str, signature_data: str,
               public_key_fingerprint: str = '') -> bool:
        try:
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes, serialization
            from apps.signature.models import SignerKey

            if not public_key_fingerprint:
                return False

            key_record = SignerKey.objects.filter(
                fingerprint=public_key_fingerprint
            ).first()
            if not key_record:
                return False

            public_key = serialization.load_pem_public_key(
                key_record.public_key_pem.encode()
            )

            hash_bytes = bytes.fromhex(content_hash)
            sig_bytes = base64.b64decode(signature_data)

            public_key.verify(
                sig_bytes,
                hash_bytes,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True

        except Exception:
            return False
