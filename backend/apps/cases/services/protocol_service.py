"""
Serviço de Protocolo Eletrônico — Simulação de peticionamento eletrônico.
"""
import logging
import random
import string
from datetime import datetime
from django.utils import timezone
from django.db.models import Count, Q

logger = logging.getLogger(__name__)


class ProtocolService:
    """Gerencia operações de protocolo eletrônico."""

    @staticmethod
    def create_protocol(case, document, court_system, petition_type, user):
        """Cria um protocolo eletrônico em rascunho."""
        from apps.cases.models import ElectronicProtocol

        protocol = ElectronicProtocol.objects.create(
            case=case,
            document=document,
            court_system=court_system,
            petition_type=petition_type,
            status='draft',
            created_by=user,
        )
        logger.info(f"[ProtocolService] Protocolo criado: {protocol.id}")
        return protocol

    @staticmethod
    def generate_protocol_number(court_system):
        """Gera número de protocolo realista para cada sistema de tribunal."""
        now = datetime.now()
        year = now.year
        seq = ''.join(random.choices(string.digits, k=10))

        formats = {
            'pje': f"PJe-{seq[:7]}-{seq[7:9]}.{year}.8.26.{random.randint(1, 999):04d}",
            'esaj': f"{seq[:7]}{random.randint(10, 99)}.{year}.8.26.{random.randint(1, 600):04d}",
            'projudi': f"PROJUDI-{year}-{seq[:8]}",
            'eproc': f"EPROC-{seq[:4]}.{seq[4:8]}.{year}.4.{random.randint(1, 50):02d}",
            'sei': f"SEI-{random.randint(10000000, 99999999)}/{year}-{random.randint(10, 99)}",
            'manual': f"MAN-{year}-{seq[:6]}",
        }
        return formats.get(court_system, f"PROT-{year}-{seq[:8]}")

    @staticmethod
    def submit_protocol(protocol_id):
        """Simula submissão de protocolo ao tribunal."""
        from apps.cases.models import ElectronicProtocol

        try:
            protocol = ElectronicProtocol.objects.get(id=protocol_id)
        except ElectronicProtocol.DoesNotExist:
            raise ValueError("Protocolo não encontrado.")

        if protocol.status not in ('draft', 'error'):
            raise ValueError(f"Protocolo com status '{protocol.get_status_display()}' não pode ser submetido.")

        # Gerar número de protocolo
        protocol.protocol_number = ProtocolService.generate_protocol_number(protocol.court_system)
        protocol.submitted_at = timezone.now()
        protocol.status = 'submitted'
        protocol.retry_count += 1

        # Simular recibo
        protocol.protocol_receipt = (
            f"RECIBO DE PROTOCOLO ELETRÔNICO\n"
            f"{'=' * 40}\n"
            f"Sistema: {protocol.get_court_system_display()}\n"
            f"Protocolo: {protocol.protocol_number}\n"
            f"Data/Hora: {protocol.submitted_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"Tipo: {protocol.petition_type}\n"
            f"Processo: {protocol.case.numero_processo or 'N/A'}\n"
            f"{'=' * 40}\n"
            f"Documento protocolado com sucesso."
        )
        protocol.error_message = ''
        protocol.save()

        logger.info(f"[ProtocolService] Protocolo submetido: {protocol.id} -> {protocol.protocol_number}")
        return protocol

    @staticmethod
    def check_protocol_status(protocol_id):
        """Verifica e atualiza o status de um protocolo submetido (simulado)."""
        from apps.cases.models import ElectronicProtocol

        try:
            protocol = ElectronicProtocol.objects.get(id=protocol_id)
        except ElectronicProtocol.DoesNotExist:
            raise ValueError("Protocolo não encontrado.")

        if protocol.status == 'submitted':
            # Simular: 85% aceito, 10% continua pendente, 5% rejeitado
            roll = random.random()
            if roll < 0.85:
                protocol.status = 'accepted'
                protocol.accepted_at = timezone.now()
                protocol.protocol_receipt += (
                    f"\n\nATUALIZAÇÃO: Aceito em {protocol.accepted_at.strftime('%d/%m/%Y %H:%M:%S')}"
                )
            elif roll < 0.95:
                protocol.status = 'pending'
            else:
                protocol.status = 'rejected'
                protocol.error_message = 'Documento não atende aos requisitos do tribunal. Verifique formatação e assinatura digital.'
            protocol.save()

        return protocol

    @staticmethod
    def get_protocol_statistics(user):
        """Retorna estatísticas de protocolo para o dashboard."""
        from apps.cases.models import ElectronicProtocol

        qs = ElectronicProtocol.objects.all()
        if not user.is_staff:
            qs = qs.filter(
                Q(created_by=user) |
                Q(case__advogado_responsavel=user) |
                Q(case__created_by=user)
            )

        stats = qs.aggregate(
            total=Count('id'),
            draft=Count('id', filter=Q(status='draft')),
            pending=Count('id', filter=Q(status='pending')),
            submitted=Count('id', filter=Q(status='submitted')),
            accepted=Count('id', filter=Q(status='accepted')),
            rejected=Count('id', filter=Q(status='rejected')),
            error=Count('id', filter=Q(status='error')),
        )

        # Por sistema de tribunal
        by_court = dict(
            qs.values('court_system')
            .annotate(n=Count('id'))
            .values_list('court_system', 'n')
        )

        stats['by_court_system'] = by_court
        return stats
