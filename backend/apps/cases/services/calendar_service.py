"""
CalendarService - Agrega eventos de prazos, lembretes, audiencias e notificacoes
em formato de calendario para o Verus.AI.
"""
from datetime import date, timedelta
from django.db.models import Q
from django.utils import timezone


# Cores por tipo de evento
EVENT_COLORS = {
    'deadline': '#ef4444',
    'reminder': '#3b82f6',
    'hearing': '#8b5cf6',
    'notification': '#f59e0b',
    'phase': '#10b981',
}

PRIORITY_MAP = {
    'urgente': 4,
    'alta': 3,
    'media': 2,
    'baixa': 1,
    'urgent': 4,
    'high': 3,
    'medium': 2,
    'low': 1,
}


class CalendarService:
    """Servico de calendario que agrega eventos de diversas fontes."""

    @staticmethod
    def _user_cases_filter(user):
        """Retorna Q filter para casos do usuario."""
        if user.is_staff or user.is_superuser:
            return Q()
        return (
            Q(caso__advogado_responsavel=user) |
            Q(caso__created_by=user)
        )

    @staticmethod
    def _user_cases_filter_direct(user):
        """Retorna Q filter para LegalCase diretamente."""
        if user.is_staff or user.is_superuser:
            return Q()
        return (
            Q(advogado_responsavel=user) | Q(created_by=user)
        )

    @classmethod
    def get_events(cls, user, start_date: date, end_date: date) -> list[dict]:
        """
        Agrega todos os eventos relacionados a prazos no intervalo de datas.
        Fontes: LegalDeadline, UserReminder, LegalNotification, CasePhase, Audiencia.
        """
        events = []

        # 1. LegalDeadline
        events.extend(cls._get_deadline_events(user, start_date, end_date))

        # 2. UserReminder
        events.extend(cls._get_reminder_events(user, start_date, end_date))

        # 3. LegalNotification
        events.extend(cls._get_notification_events(user, start_date, end_date))

        # 4. CasePhase
        events.extend(cls._get_phase_events(user, start_date, end_date))

        # 5. Audiencia
        events.extend(cls._get_hearing_events(user, start_date, end_date))

        # Ordenar por data de inicio
        events.sort(key=lambda e: e['start'])

        return events

    @classmethod
    def _get_deadline_events(cls, user, start_date, end_date):
        from apps.cases.models import LegalDeadline

        qs = LegalDeadline.objects.select_related('caso').filter(
            data_prazo__gte=start_date,
            data_prazo__lte=end_date,
        )
        user_filter = cls._user_cases_filter(user)
        if user_filter:
            extra = Q(responsavel=user)
            qs = qs.filter(user_filter | extra).distinct()

        events = []
        for d in qs:
            events.append({
                'id': str(d.id),
                'title': d.titulo,
                'start': d.data_prazo.isoformat(),
                'end': d.data_prazo.isoformat(),
                'type': 'deadline',
                'case_id': str(d.caso_id),
                'case_title': d.caso.titulo if d.caso else '',
                'color': EVENT_COLORS['deadline'],
                'priority': PRIORITY_MAP.get(d.prioridade, 2),
                'status': d.status,
                'description': d.descricao or '',
            })
        return events

    @classmethod
    def _get_reminder_events(cls, user, start_date, end_date):
        from apps.accounts.models import UserReminder

        qs = UserReminder.objects.filter(
            user=user,
            status='active',
            scheduled_date__date__gte=start_date,
            scheduled_date__date__lte=end_date,
        ).select_related('related_case')

        events = []
        for r in qs:
            events.append({
                'id': str(r.id),
                'title': r.title,
                'start': r.scheduled_date.date().isoformat(),
                'end': r.scheduled_date.date().isoformat(),
                'type': 'reminder',
                'case_id': str(r.related_case_id) if r.related_case_id else None,
                'case_title': r.related_case.titulo if r.related_case else '',
                'color': EVENT_COLORS['reminder'],
                'priority': PRIORITY_MAP.get(r.priority, 2),
                'status': r.status,
                'description': r.description or '',
            })
        return events

    @classmethod
    def _get_notification_events(cls, user, start_date, end_date):
        from apps.cases.models import LegalNotification

        qs = LegalNotification.objects.select_related('caso').filter(
            prazo_vencimento__isnull=False,
            prazo_vencimento__gte=start_date,
            prazo_vencimento__lte=end_date,
        )
        user_filter = cls._user_cases_filter(user)
        if user_filter:
            qs = qs.filter(user_filter)

        events = []
        for n in qs:
            events.append({
                'id': str(n.id),
                'title': n.get_tipo_display(),
                'start': n.prazo_vencimento.isoformat(),
                'end': n.prazo_vencimento.isoformat(),
                'type': 'notification',
                'case_id': str(n.caso_id),
                'case_title': n.caso.titulo if n.caso else '',
                'color': EVENT_COLORS['notification'],
                'priority': 3,
                'status': n.status,
                'description': n.conteudo_resumo or '',
            })
        return events

    @classmethod
    def _get_phase_events(cls, user, start_date, end_date):
        from apps.cases.models import CasePhase

        qs = CasePhase.objects.select_related('caso').filter(
            estimated_date__isnull=False,
            estimated_date__gte=start_date,
            estimated_date__lte=end_date,
        )
        # Filter by user cases
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(
                Q(caso__advogado_responsavel=user) | Q(caso__created_by=user)
            )

        events = []
        for p in qs:
            events.append({
                'id': str(p.id),
                'title': f'{p.name}',
                'start': p.estimated_date.isoformat(),
                'end': (p.actual_date or p.estimated_date).isoformat(),
                'type': 'phase',
                'case_id': str(p.caso_id),
                'case_title': p.caso.titulo if p.caso else '',
                'color': EVENT_COLORS['phase'],
                'priority': 2,
                'status': p.status,
                'description': p.description or '',
            })
        return events

    @classmethod
    def _get_hearing_events(cls, user, start_date, end_date):
        from apps.cases.models import Audiencia

        qs = Audiencia.objects.select_related('caso').filter(
            data_hora__date__gte=start_date,
            data_hora__date__lte=end_date,
        )
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(
                Q(caso__advogado_responsavel=user) | Q(caso__created_by=user)
            )

        events = []
        for a in qs:
            events.append({
                'id': str(a.id),
                'title': a.get_tipo_display(),
                'start': a.data_hora.date().isoformat(),
                'end': a.data_hora.date().isoformat(),
                'type': 'hearing',
                'case_id': str(a.caso_id),
                'case_title': a.caso.titulo if a.caso else '',
                'color': EVENT_COLORS['hearing'],
                'priority': 4,
                'status': a.status,
                'description': a.observacoes or '',
            })
        return events

    @classmethod
    def get_upcoming_deadlines(cls, user, days: int = 7) -> list[dict]:
        """Retorna prazos nos proximos N dias."""
        today = timezone.now().date()
        end = today + timedelta(days=days)
        return cls.get_events(user, today, end)

    @classmethod
    def get_overdue_items(cls, user) -> list[dict]:
        """Retorna itens atrasados (prazos pendentes com data passada)."""
        from apps.cases.models import LegalDeadline

        today = timezone.now().date()
        qs = LegalDeadline.objects.select_related('caso').filter(
            status__in=['pendente', 'em_andamento'],
            data_prazo__lt=today,
        )
        user_filter = cls._user_cases_filter(user)
        if user_filter:
            extra = Q(responsavel=user)
            qs = qs.filter(user_filter | extra).distinct()

        items = []
        for d in qs:
            items.append({
                'id': str(d.id),
                'title': d.titulo,
                'start': d.data_prazo.isoformat(),
                'end': d.data_prazo.isoformat(),
                'type': 'deadline',
                'case_id': str(d.caso_id),
                'case_title': d.caso.titulo if d.caso else '',
                'color': EVENT_COLORS['deadline'],
                'priority': PRIORITY_MAP.get(d.prioridade, 2),
                'status': 'atrasado',
                'description': d.descricao or '',
                'days_overdue': (today - d.data_prazo).days,
            })
        return items

    @classmethod
    def get_daily_summary(cls, user, target_date: date) -> dict:
        """Resumo de um dia especifico."""
        events = cls.get_events(user, target_date, target_date)
        by_type = {}
        for e in events:
            t = e['type']
            by_type.setdefault(t, []).append(e)

        return {
            'date': target_date.isoformat(),
            'total_events': len(events),
            'events': events,
            'by_type': {k: len(v) for k, v in by_type.items()},
        }
