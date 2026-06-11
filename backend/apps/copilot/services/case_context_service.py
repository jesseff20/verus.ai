"""
case_context_service — Injeta contexto dos casos do usuario no prompt do Copilot.

Consulta os casos ativos e prazos proximos do usuario autenticado
e formata como texto de contexto para o LLM, dando ao Copilot
consciencia da situacao do usuario sem que ele precise perguntar.
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def build_case_context(user) -> str:
    """
    Constroi string de contexto com os casos ativos e prazos proximos
    do usuario para injecao no system prompt do Copilot.

    Retorna string vazia se nao houver casos ou se ocorrer erro.
    """
    try:
        from apps.cases.models import LegalCase, LegalDeadline
        from django.db import models

        # Top 5 casos ativos mais recentes
        cases = LegalCase.objects.filter(
            models.Q(advogado_responsavel=user) | models.Q(created_by=user),
            status__in=['ativo', 'aguardando'],
        ).order_by('-updated_at')[:5]

        if not cases:
            return ''

        lines = [
            '## Contexto do usuario (casos ativos e prazos proximos)',
            'O usuario tem os seguintes casos ativos:',
        ]

        for c in cases:
            status = c.get_status_display()
            esp = c.get_especialidade_display()
            cliente = c.cliente_nome or 'N/A'
            lines.append(f'- {c.titulo} ({status}, {esp}) — Cliente: {cliente}')

        # Prazos proximos (7 dias) de todos os casos do usuario
        today = timezone.now().date()
        from datetime import timedelta
        upcoming_date = today + timedelta(days=7)

        deadlines = LegalDeadline.objects.filter(
            models.Q(responsavel=user) | models.Q(caso__advogado_responsavel=user),
            status__in=['pendente', 'em_andamento'],
            data_prazo__lte=upcoming_date,
            caso__deleted_at__isnull=True,
        ).select_related('caso').order_by('data_prazo')[:5]

        if deadlines:
            lines.append('\nPrazos proximos (7 dias):')
            for d in deadlines:
                days_left = (d.data_prazo - today).days
                case_ref = d.caso.titulo if d.caso else 'N/A'
                lines.append(
                    f'- {d.titulo} ({d.data_prazo.strftime("%d/%m/%Y")}, '
                    f'faltam {days_left} dias) — Caso: {case_ref}'
                )

        lines.append(
            '\nUse essas informacoes para oferecer sugestoes proativas '
            'sobre prazos e andamentos dos casos do usuario.'
        )
        return '\n'.join(lines)

    except Exception as e:
        logger.warning(f'[copilot] Falha ao construir contexto de casos: {e}')
        return ''
