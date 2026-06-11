"""
NotificationBridge - Cria notificacoes quando clientes e advogados interagem.

Garante que todos os perfis (superadmin, gestor, advogado_senior, advogado_pleno,
advogado_junior, analista, assessor, defensor, promotor, paralegal)
vejam atualizacoes relevantes.

Todas as operacoes sao protegidas por try/except para nunca
interromper o fluxo principal da view que as invoca.
"""
import logging

from apps.accounts.models import Notification

logger = logging.getLogger(__name__)


class NotificationBridge:
    """Cria notificacoes cross-profile entre clientes e advogados."""

    # ── Cliente → Advogado ──────────────────────────────────────────────────

    @staticmethod
    def notify_lawyer_client_signed_contract(client, contract, case=None):
        """Cliente assinou contrato → notificar advogado responsavel."""
        try:
            lawyer = case.advogado_responsavel if case else None
            if not lawyer:
                logger.debug(
                    'notify_lawyer_client_signed_contract: sem advogado para case=%s',
                    case,
                )
                return
            Notification.objects.create(
                user=lawyer,
                type='contract',
                title=f'Contrato assinado por {client.name}',
                message=(
                    f'O cliente {client.name} assinou o contrato '
                    f'"{contract.title}".'
                ),
                priority='high',
                link=f'/dashboard/contratos/{contract.id}',
                source='portal',
                action_type='info',
            )
        except Exception:
            logger.exception(
                'Erro ao notificar advogado sobre assinatura de contrato '
                '(client=%s, contract=%s)',
                getattr(client, 'id', None),
                getattr(contract, 'id', None),
            )

    @staticmethod
    def notify_lawyer_client_uploaded_document(client, document, case):
        """Cliente enviou documento → notificar advogado responsavel."""
        try:
            lawyer = case.advogado_responsavel if case else None
            if not lawyer:
                logger.debug(
                    'notify_lawyer_client_uploaded_document: sem advogado para case=%s',
                    case,
                )
                return
            Notification.objects.create(
                user=lawyer,
                type='document',
                title=f'Novo documento de {client.name}',
                message=(
                    f'O cliente {client.name} enviou o documento '
                    f'"{document.titulo}" no caso "{case.titulo}".'
                ),
                priority='medium',
                link=f'/dashboard/processos/{case.id}',
                source='portal',
                action_type='action_required',
            )
        except Exception:
            logger.exception(
                'Erro ao notificar advogado sobre upload de documento '
                '(client=%s, document=%s)',
                getattr(client, 'id', None),
                getattr(document, 'id', None),
            )

    @staticmethod
    def notify_lawyer_client_message(client, case=None):
        """Cliente enviou mensagem → notificar advogado responsavel."""
        try:
            if not case:
                return
            lawyer = case.advogado_responsavel
            if not lawyer:
                return
            Notification.objects.create(
                user=lawyer,
                type='message',
                title=f'Nova mensagem de {client.name}',
                message=(
                    f'O cliente {client.name} enviou uma mensagem sobre '
                    f'o caso "{case.titulo}".'
                ),
                priority='medium',
                link='/dashboard/mensagens-clientes',
                source='portal',
                action_type='action_required',
            )
        except Exception:
            logger.exception(
                'Erro ao notificar advogado sobre mensagem do cliente '
                '(client=%s, case=%s)',
                getattr(client, 'id', None),
                getattr(case, 'id', None),
            )

    @staticmethod
    def notify_lawyer_client_consent_accepted(client, term):
        """Cliente aceitou termo de consentimento → notificar admins/gestores."""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(
                role__in=['superadmin', 'gestor'],
                is_active=True,
            )
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    type='compliance',
                    title=f'Consentimento aceito - {client.name}',
                    message=(
                        f'O cliente {client.name} aceitou o termo '
                        f'"{term.title}" v{term.version}.'
                    ),
                    priority='low',
                    source='portal',
                    action_type='info',
                )
        except Exception:
            logger.exception(
                'Erro ao notificar admins sobre consentimento '
                '(client=%s, term=%s)',
                getattr(client, 'id', None),
                getattr(term, 'id', None),
            )

    # ── Advogado / Escritorio → Cliente ─────────────────────────────────────
    #
    # O modelo Notification.user e NOT NULL (ForeignKey sem blank/null).
    # Clientes nao sao Users do Django, entao nao podemos criar Notification
    # com user=None.  Em vez disso, notificamos o advogado responsavel
    # e armazenamos client_id nos metadata para que o portal do cliente
    # possa buscar essas notificacoes via metadata lookup.

    @staticmethod
    def notify_client_case_updated(client, case, update_description):
        """Advogado atualizou caso → registrar notificacao para o portal do cliente.
        Armazena no advogado responsavel com metadata.client_id para consulta no portal."""
        try:
            lawyer = case.advogado_responsavel if case else None
            if not lawyer:
                return
            Notification.objects.create(
                user=lawyer,
                type='case_update',
                title=f'Atualizacao no caso: {case.titulo}',
                message=update_description,
                priority='medium',
                link=f'/portal/casos/{case.id}',
                source='escritorio',
                action_type='info',
                metadata={
                    'client_id': str(client.id),
                    'case_id': str(case.id),
                    'target': 'client_portal',
                },
            )
        except Exception:
            logger.exception(
                'Erro ao registrar notificacao de atualizacao de caso '
                '(client=%s, case=%s)',
                getattr(client, 'id', None),
                getattr(case, 'id', None),
            )

    @staticmethod
    def notify_client_new_document(client, case, document_title):
        """Advogado adicionou documento → registrar notificacao para portal do cliente."""
        try:
            lawyer = case.advogado_responsavel if case else None
            if not lawyer:
                return
            Notification.objects.create(
                user=lawyer,
                type='document',
                title='Novo documento disponivel',
                message=(
                    f'Um novo documento "{document_title}" foi adicionado '
                    f'ao seu caso "{case.titulo}".'
                ),
                priority='medium',
                link=f'/portal/casos/{case.id}',
                source='escritorio',
                action_type='info',
                metadata={
                    'client_id': str(client.id),
                    'case_id': str(case.id),
                    'target': 'client_portal',
                },
            )
        except Exception:
            logger.exception(
                'Erro ao registrar notificacao de novo documento para cliente '
                '(client=%s, case=%s)',
                getattr(client, 'id', None),
                getattr(case, 'id', None),
            )

    @staticmethod
    def notify_client_deadline_approaching(client, case, deadline):
        """Prazo proximo → registrar notificacao para portal do cliente."""
        try:
            lawyer = case.advogado_responsavel if case else None
            if not lawyer:
                return
            Notification.objects.create(
                user=lawyer,
                type='deadline',
                title=f'Prazo proximo: {deadline.titulo}',
                message=(
                    f'O prazo "{deadline.titulo}" no caso "{case.titulo}" '
                    f'vence em {deadline.data_prazo.strftime("%d/%m/%Y")}.'
                ),
                priority='high',
                link=f'/portal/casos/{case.id}',
                source='escritorio',
                action_type='info',
                metadata={
                    'client_id': str(client.id),
                    'case_id': str(case.id),
                    'target': 'client_portal',
                },
            )
        except Exception:
            logger.exception(
                'Erro ao registrar notificacao de prazo para cliente '
                '(client=%s, case=%s, deadline=%s)',
                getattr(client, 'id', None),
                getattr(case, 'id', None),
                getattr(deadline, 'id', None),
            )

    # ── Notificacao para toda equipe do caso ────────────────────────────────

    @staticmethod
    def notify_all_team_members(case, title, message, exclude_user=None):
        """Notifica todos os membros da equipe atribuida ao caso."""
        try:
            from apps.accounts.models import TeamAssignment
            assignments = TeamAssignment.objects.filter(
                case=case,
            ).select_related('team')
            notified = set()
            for assignment in assignments:
                for member in assignment.team.members.all():
                    if member.id not in notified and member != exclude_user:
                        Notification.objects.create(
                            user=member,
                            type='case_update',
                            title=title,
                            message=message,
                            priority='medium',
                            link=f'/dashboard/processos/{case.id}',
                            source='system',
                            action_type='info',
                        )
                        notified.add(member.id)
        except Exception:
            logger.exception(
                'Erro ao notificar membros da equipe (case=%s)',
                getattr(case, 'id', None),
            )
