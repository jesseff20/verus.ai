"""
Serviço de Assinatura Digital — criação, verificação e gestão.
"""
import hashlib
import uuid
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class SignatureService:
    """Serviço para gestão de assinaturas digitais."""

    @staticmethod
    def _generate_document_hash(document=None, user=None) -> str:
        """Gera hash SHA-256 do conteúdo do documento ou do contexto do usuário."""
        if document:
            content_parts = [
                str(document.id),
                document.titulo or '',
                document.descricao or '',
                str(document.caso_id) if document.caso_id else '',
                document.created_at.isoformat() if document.created_at else '',
            ]
        else:
            # Assinatura sem documento específico
            content_parts = [
                str(user.id) if user else str(uuid.uuid4()),
                timezone.now().isoformat(),
                str(uuid.uuid4()),
            ]
        content = '|'.join(content_parts)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def sign_document(user, document, signature_type: str, ip_address: str, metadata: dict = None):
        """
        Cria assinatura digital para um documento.

        Args:
            user: Usuário assinante
            document: CaseDocument
            signature_type: 'simple', 'advanced', 'qualified'
            ip_address: IP do assinante
            metadata: Dados adicionais

        Returns:
            DigitalSignature instance
        """
        from apps.cases.models import DigitalSignature

        sig_hash = SignatureService._generate_document_hash(document=document, user=user)

        signature = DigitalSignature.objects.create(
            user=user,
            document=document,
            signature_type=signature_type,
            signature_hash=sig_hash,
            ip_address=ip_address,
            is_valid=True,
            verification_url='',
            metadata=metadata or {
                'user_agent': '',
                'signed_fields': ['titulo', 'descricao', 'caso_id'],
            },
        )

        # Gerar URL de verificação
        signature.verification_url = f'/verificar-assinatura/{signature.id}/'
        signature.save(update_fields=['verification_url'])

        logger.info(
            f"[SignatureService] Documento '{document.titulo}' assinado por {user} "
            f"(tipo: {signature_type}, hash: {sig_hash[:16]}...)"
        )
        return signature

    @staticmethod
    def verify_signature(signature_id) -> dict:
        """
        Verifica a validade de uma assinatura digital.

        Returns dict com resultado da verificação.
        """
        from apps.cases.models import DigitalSignature, SignatureVerification

        try:
            signature = DigitalSignature.objects.select_related(
                'user', 'document', 'contract'
            ).get(id=signature_id)
        except DigitalSignature.DoesNotExist:
            return {
                'is_valid': False,
                'error': 'Assinatura não encontrada.',
                'signature_id': str(signature_id),
            }

        # Verificar hash se documento ainda existe
        is_valid = signature.is_valid
        details = {
            'signature_type': signature.get_signature_type_display(),
            'signed_at': signature.signed_at.isoformat(),
            'signer': signature.user.get_full_name() or signature.user.username,
            'ip_address': signature.ip_address,
        }

        if signature.document:
            current_hash = SignatureService._generate_document_hash(signature.document)
            hash_matches = current_hash == signature.signature_hash
            details['hash_matches'] = hash_matches
            details['document_title'] = signature.document.titulo
            if not hash_matches:
                is_valid = False
                details['warning'] = 'O documento foi modificado após a assinatura.'
        else:
            details['warning'] = 'Documento original não disponível para verificação de integridade.'

        # Criar registro de verificação
        verification = SignatureVerification.objects.create(
            signature=signature,
            is_valid=is_valid,
            verification_details=details,
        )

        return {
            'is_valid': is_valid,
            'signature_id': str(signature.id),
            'verification_id': str(verification.id),
            'details': details,
        }

    @staticmethod
    def generate_signature_page(signatures) -> str:
        """
        Gera página HTML de verificação de assinaturas.

        Args:
            signatures: QuerySet ou lista de DigitalSignature

        Returns:
            HTML string
        """
        rows = []
        for sig in signatures:
            signer = sig.user.get_full_name() or sig.user.username
            doc_title = sig.document.titulo if sig.document else 'N/A'
            status = 'Válida' if sig.is_valid else 'Inválida'
            rows.append(f"""
                <tr>
                    <td>{signer}</td>
                    <td>{sig.get_signature_type_display()}</td>
                    <td>{doc_title}</td>
                    <td>{sig.signed_at.strftime('%d/%m/%Y %H:%M')}</td>
                    <td>{status}</td>
                    <td style="font-family:monospace;font-size:10px">{sig.signature_hash[:16]}...</td>
                </tr>
            """)

        table_rows = '\n'.join(rows)
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Verificação de Assinaturas Digitais — Verus.AI</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #1a365d; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; }}
                th {{ background-color: #2d3748; color: white; }}
                tr:nth-child(even) {{ background-color: #f7fafc; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #718096; }}
            </style>
        </head>
        <body>
            <h1>Página de Verificação de Assinaturas Digitais</h1>
            <p>Documento gerado pelo sistema Verus.AI em {timezone.now().strftime('%d/%m/%Y %H:%M')}.</p>
            <table>
                <thead>
                    <tr>
                        <th>Assinante</th>
                        <th>Tipo</th>
                        <th>Documento</th>
                        <th>Data/Hora</th>
                        <th>Status</th>
                        <th>Hash (parcial)</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            <div class="footer">
                <p>Para verificar a autenticidade de cada assinatura, acesse o sistema Verus.AI
                e insira o ID da assinatura na seção de verificação.</p>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def get_user_signatures(user):
        """Retorna todas as assinaturas de um usuário."""
        from apps.cases.models import DigitalSignature
        return DigitalSignature.objects.filter(user=user).select_related('document', 'contract')
