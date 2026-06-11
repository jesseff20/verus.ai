"""
Serviço de Notificações Jurídicas — auto-cálculo de prazos e criação de deadlines.
"""
import logging
from datetime import timedelta

from apps.cases.utils import adicionar_dias_uteis

logger = logging.getLogger(__name__)

# Prazos padrão por tipo de notificação (dias, tipo)
DEFAULT_DEADLINES = {
    'citacao_pessoal': (15, 'uteis', 'Contestação (CPC art. 335)'),
    'citacao_hora_certa': (15, 'uteis', 'Contestação (CPC art. 335)'),
    'citacao_eletronica': (15, 'uteis', 'Contestação (CPC art. 335)'),
    'citacao_edital': (20, 'uteis', 'Contestação — Citação por Edital (CPC art. 231, IV)'),
    'mandado_citacao': (15, 'uteis', 'Contestação (CPC art. 335)'),
    'intimacao_pessoal': (5, 'uteis', 'Manifestação'),
    'intimacao_dje': (5, 'uteis', 'Manifestação (contagem D+1 publicação)'),
    'intimacao_eletronica': (5, 'uteis', 'Manifestação'),
    'intimacao_publicacao': (5, 'uteis', 'Manifestação por publicação'),
    'mandado_intimacao': (5, 'uteis', 'Manifestação'),
}


class NotificationService:
    """Serviço para processar notificações jurídicas."""

    @staticmethod
    def calculate_prazo_vencimento(notification):
        """
        Calcula prazo_vencimento com base em data_ciencia/data_publicacao_dje,
        prazo_dias e prazo_tipo.
        """
        # Determinar data base para contagem
        data_base = None
        if notification.tipo == 'intimacao_dje' and notification.data_publicacao_dje:
            # DJe: D+1 da publicação é data da intimação
            data_base = notification.data_publicacao_dje + timedelta(days=1)
        elif notification.data_ciencia:
            data_base = notification.data_ciencia
        elif notification.data_publicacao_dje:
            data_base = notification.data_publicacao_dje + timedelta(days=1)

        if not data_base:
            return None

        # Determinar prazo em dias
        prazo_dias = notification.prazo_dias
        if not prazo_dias:
            default = DEFAULT_DEADLINES.get(notification.tipo)
            if default:
                prazo_dias = default[0]
            else:
                return None

        prazo_tipo = notification.prazo_tipo or 'uteis'

        if prazo_tipo == 'uteis':
            return adicionar_dias_uteis(data_base, prazo_dias)
        else:
            return data_base + timedelta(days=prazo_dias)

    @staticmethod
    def process_notification(notification, user=None):
        """
        Processa uma notificação: calcula prazo e opcionalmente cria LegalDeadline.
        Chamado ao salvar/atualizar notificação com data_ciencia.
        """
        from apps.cases.models import LegalDeadline

        # Calcular prazo de vencimento
        vencimento = NotificationService.calculate_prazo_vencimento(notification)
        if vencimento:
            notification.prazo_vencimento = vencimento

            # Preencher prazo_dias se não estiver definido
            if not notification.prazo_dias:
                default = DEFAULT_DEADLINES.get(notification.tipo)
                if default:
                    notification.prazo_dias = default[0]
                    notification.prazo_tipo = default[1]

        # Auto-criar LegalDeadline se não existe ainda
        if vencimento and not notification.deadline_created:
            default = DEFAULT_DEADLINES.get(notification.tipo)
            titulo = f"{notification.get_tipo_display()}"
            if default:
                titulo = f"{default[2]} — {notification.get_tipo_display()}"

            try:
                deadline = LegalDeadline.objects.create(
                    caso=notification.caso,
                    titulo=titulo,
                    descricao=(
                        f"Prazo automático gerado pela notificação: {notification.get_tipo_display()}.\n"
                        f"Destinatário: {notification.destinatario_nome or '—'}\n"
                        f"Base legal: {notification.base_legal or '—'}"
                    ),
                    tipo='processual',
                    prioridade='alta',
                    status='pendente',
                    data_prazo=vencimento,
                    created_by=user,
                )
                notification.deadline_created = deadline
                logger.info(
                    f"[NotificationService] Prazo criado automaticamente: "
                    f"{deadline.titulo} vence em {vencimento}"
                )
            except Exception as exc:
                logger.error(f"[NotificationService] Erro ao criar prazo: {exc}", exc_info=True)

        return notification

    @staticmethod
    def get_default_prazo_for_tipo(tipo):
        """Retorna prazo padrão (dias, tipo, descricao) para um tipo de notificação."""
        return DEFAULT_DEADLINES.get(tipo)
