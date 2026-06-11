"""
Copilot autonomous notification tasks — Celery periodic tasks.

These tasks run in the background and proactively generate smart
notifications that link to the Copilot with pre-filled context,
making the Copilot feel like a proactive legal assistant.
"""
import logging
from datetime import timedelta
from urllib.parse import quote

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _copilot_link(prompt: str) -> str:
    """Build a link to the Copilot page with a pre-filled prompt."""
    return f'/dashboard/copilot?prompt={quote(prompt)}'


def _send_notification_channels(user, notification):
    """
    Send notification through active channels (WhatsApp, Email) for the user.
    ONLY sends automatically if the channel has auto_send=True.
    If auto_send=False, the notification is created but the user must send manually.
    Catches all exceptions to avoid breaking the calling task.
    """
    try:
        from apps.accounts.models import NotificationChannel
        from apps.copilot.services.communication_service import CommunicationService

        # Only send through channels that have auto_send enabled
        auto_channels = NotificationChannel.objects.filter(
            user=user, is_active=True, auto_send=True
        )
        if not auto_channels.exists():
            return  # User prefers manual sending — skip

        svc = CommunicationService()
        svc.send_all_channels(user, notification, auto_only=True)
    except Exception as e:
        logger.warning(
            'Failed to send notification channels for user=%s notification=%s: %s',
            user.id, notification.id, e,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Task 1: Check upcoming deadlines (hourly)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name='apps.copilot.tasks.check_upcoming_deadlines')
def check_upcoming_deadlines():
    """
    Scan all active cases for deadlines approaching in 1, 3, or 5 days.
    Creates Notification with type='deadline' and action_type='copilot'.
    """
    from apps.cases.models import LegalDeadline
    from apps.accounts.models import Notification

    today = timezone.localdate()
    thresholds = [
        (1, 'urgent', 'AMANHA'),
        (3, 'high', 'em 3 dias'),
        (5, 'medium', 'em 5 dias'),
    ]

    created_count = 0
    for days, priority, label in thresholds:
        target_date = today + timedelta(days=days)
        deadlines = LegalDeadline.objects.filter(
            data_prazo=target_date,
            status__in=['pendente', 'em_andamento'],
            caso__deleted_at__isnull=True,
        ).select_related('caso', 'responsavel', 'caso__advogado_responsavel')

        for deadline in deadlines:
            # Determine notification recipient
            user = (
                deadline.responsavel
                or deadline.caso.advogado_responsavel
                or deadline.caso.created_by
            )
            if not user:
                continue

            case_ref = deadline.caso.numero_processo or deadline.caso.titulo
            copilot_prompt = (
                f'O prazo "{deadline.titulo}" do processo {case_ref} '
                f'vence {label}. Quais sao as providencias necessarias '
                f'e como posso preparar a documentacao?'
            )

            # Avoid duplicate: check if similar notification already exists today
            already_exists = Notification.objects.filter(
                user=user,
                type='deadline',
                source='cron',
                created_at__date=today,
                metadata__deadline_id=str(deadline.id),
            ).exists()
            if already_exists:
                continue

            notification = Notification.objects.create(
                user=user,
                type='deadline',
                priority=priority,
                title=f'Prazo vence {label}: {deadline.titulo}',
                message=(
                    f'O prazo "{deadline.titulo}" no processo {case_ref} '
                    f'vence {label} ({target_date.strftime("%d/%m/%Y")}). '
                    f'Clique para que o Copilot analise as providencias.'
                ),
                link=_copilot_link(copilot_prompt),
                copilot_prompt=copilot_prompt,
                action_type='copilot',
                source='cron',
                metadata={
                    'deadline_id': str(deadline.id),
                    'case_id': str(deadline.caso.id),
                    'days_remaining': days,
                },
            )
            created_count += 1

            # Send via WhatsApp and Email channels
            _send_notification_channels(user, notification)

    logger.info('check_upcoming_deadlines: %d notifications created', created_count)
    return {'created': created_count}


# ─────────────────────────────────────────────────────────────────────────────
# Task 2: Analyze idle cases (daily)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name='apps.copilot.tasks.analyze_idle_cases')
def analyze_idle_cases():
    """
    Find active cases with no activity (updated_at) in 7+ days
    and suggest review via Copilot notification.
    """
    from apps.cases.models import LegalCase
    from apps.accounts.models import Notification

    today = timezone.localdate()
    threshold = timezone.now() - timedelta(days=7)

    idle_cases = LegalCase.objects.filter(
        status__in=['ativo', 'aguardando'],
        updated_at__lt=threshold,
    ).select_related('advogado_responsavel', 'created_by')

    created_count = 0
    for case in idle_cases:
        user = case.advogado_responsavel or case.created_by
        if not user:
            continue

        days_idle = (timezone.now() - case.updated_at).days
        case_ref = case.numero_processo or case.titulo

        copilot_prompt = (
            f'O caso "{case.titulo}" (processo {case_ref}) nao tem '
            f'movimentacao ha {days_idle} dias. Analise o status atual '
            f'e sugira proximos passos.'
        )

        # Avoid duplicate: one per case per day
        already_exists = Notification.objects.filter(
            user=user,
            type='case',
            source='cron',
            created_at__date=today,
            metadata__case_id=str(case.id),
        ).exists()
        if already_exists:
            continue

        notification = Notification.objects.create(
            user=user,
            type='case',
            priority='medium',
            title=f'Caso sem movimentacao ha {days_idle} dias',
            message=(
                f'O caso "{case.titulo}" ({case_ref}) esta sem '
                f'atividade ha {days_idle} dias. O Copilot pode ajudar '
                f'a analisar o status e sugerir proximos passos.'
            ),
            link=_copilot_link(copilot_prompt),
            copilot_prompt=copilot_prompt,
            action_type='copilot',
            source='cron',
            metadata={
                'case_id': str(case.id),
                'days_idle': days_idle,
            },
        )
        created_count += 1

        # Send via WhatsApp and Email channels
        _send_notification_channels(user, notification)

    logger.info('analyze_idle_cases: %d notifications created', created_count)
    return {'created': created_count}


# ─────────────────────────────────────────────────────────────────────────────
# Task 3: Check pending document sessions (daily)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name='apps.copilot.tasks.check_pending_documents')
def check_pending_documents():
    """
    Find IntelligentSession objects stuck in generation-related phases
    for 24h+ and notify the user to complete or review.
    """
    from apps.intelligent_assistant.models.session import IntelligentSession
    from apps.accounts.models import Notification

    today = timezone.localdate()
    threshold = timezone.now() - timedelta(hours=24)

    stuck_sessions = IntelligentSession.objects.filter(
        status__in=['generating', 'validating', 'formatting'],
        updated_at__lt=threshold,
    ).select_related('user')

    created_count = 0
    for session in stuck_sessions:
        user = session.user
        doc_type = session.document_type

        copilot_prompt = (
            f'A sessao de geracao do documento "{doc_type}" '
            f'(objetivo: {session.objective[:100]}) esta pendente ha mais de 24h. '
            f'O que falta para concluir?'
        )

        # Avoid duplicate
        already_exists = Notification.objects.filter(
            user=user,
            type='document',
            source='cron',
            created_at__date=today,
            metadata__session_id=str(session.id),
        ).exists()
        if already_exists:
            continue

        notification = Notification.objects.create(
            user=user,
            type='document',
            priority='medium',
            title=f'Documento pendente: {doc_type}',
            message=(
                f'A geracao do documento "{doc_type}" esta parada ha mais de 24 horas. '
                f'Clique para que o Copilot ajude a concluir.'
            ),
            link=_copilot_link(copilot_prompt),
            copilot_prompt=copilot_prompt,
            action_type='copilot',
            source='cron',
            metadata={
                'session_id': str(session.id),
                'document_type': doc_type,
            },
        )
        created_count += 1

        # Send via WhatsApp and Email channels
        _send_notification_channels(user, notification)

    logger.info('check_pending_documents: %d notifications created', created_count)
    return {'created': created_count}


# ─────────────────────────────────────────────────────────────────────────────
# Task 4: Welcome / onboarding (on user creation)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name='apps.copilot.tasks.send_welcome_notification')
def send_welcome_notification(user_id: int):
    """
    Send a welcome notification introducing the Copilot to a new user.
    Called programmatically (e.g., from a signal) when a user is created.
    """
    from apps.accounts.models import User, Notification

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning('send_welcome_notification: user %s not found', user_id)
        return {'created': 0}

    copilot_prompt = (
        'Ola! Sou novo no Verus.AI. Me explique suas principais '
        'funcionalidades e como voce pode me ajudar no dia a dia juridico.'
    )

    Notification.objects.create(
        user=user,
        type='system',
        priority='low',
        title='Bem-vindo ao Verus.AI! Conhega o Copilot',
        message=(
            f'Ola, {user.get_full_name() or user.username}! '
            f'O Copilot e seu assistente juridico com IA. Ele monitora seus '
            f'prazos, analisa casos e sugere acoes proativamente. '
            f'Clique para iniciar uma conversa.'
        ),
        link=_copilot_link(copilot_prompt),
        copilot_prompt=copilot_prompt,
        action_type='copilot',
        source='copilot',
        metadata={'event': 'welcome'},
    )

    logger.info('send_welcome_notification: created for user %s', user.username)
    return {'created': 1}


# ─────────────────────────────────────────────────────────────────────────────
# Task 5: Nightly user knowledge base sync
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name='apps.copilot.tasks.sync_user_knowledge_bases')
def sync_user_knowledge_bases():
    """
    Runs nightly at 2am. Collects ALL user data and syncs to vector KB.
    Dispatches one sub-task per active user for parallel processing.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    active_users = User.objects.filter(is_active=True)
    dispatched = 0
    for user in active_users:
        sync_single_user_knowledge.delay(user.id)
        dispatched += 1

    logger.info('sync_user_knowledge_bases: dispatched %d user syncs', dispatched)
    return {'dispatched': dispatched}


@shared_task(name='apps.copilot.tasks.sync_single_user_knowledge')
def sync_single_user_knowledge(user_id):
    """
    Sync one user's knowledge base.

    1. Queries ALL user data (cases, documents, deadlines, clients, sessions)
    2. For each item, creates a text representation
    3. Computes SHA256 hash of the text
    4. If hash changed or entry doesn't exist -> create/update UserKnowledgeEntry
    5. Logs the sync in UserKnowledgeSyncLog
    """
    import hashlib
    from django.contrib.auth import get_user_model
    from django.db.models import Q
    from .models import UserKnowledgeEntry, UserKnowledgeSyncLog

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning('sync_single_user_knowledge: user %s not found', user_id)
        return {'status': 'user_not_found'}

    sync_log = UserKnowledgeSyncLog.objects.create(user=user)
    created = 0
    updated = 0
    unchanged = 0
    errors = []

    def _upsert_entry(category, title, content, source_model, source_id, context_date):
        nonlocal created, updated, unchanged
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        try:
            entry, was_created = UserKnowledgeEntry.objects.get_or_create(
                user=user,
                source_model=source_model,
                source_id=str(source_id),
                defaults={
                    'category': category,
                    'title': title[:500],
                    'content': content,
                    'context_date': context_date,
                    'content_hash': content_hash,
                },
            )
            if was_created:
                created += 1
            elif entry.content_hash != content_hash:
                entry.category = category
                entry.title = title[:500]
                entry.content = content
                entry.context_date = context_date
                entry.content_hash = content_hash
                entry.save()
                updated += 1
            else:
                unchanged += 1
        except Exception as e:
            errors.append(f'{source_model}:{source_id} - {str(e)}')
            logger.exception('Error upserting knowledge entry for user %s', user_id)

    # ── Cases ────────────────────────────────────────────────────────────────
    try:
        from apps.cases.models import LegalCase
        cases = LegalCase.all_objects.filter(
            Q(advogado_responsavel_id=user_id) | Q(created_by_id=user_id),
            deleted_at__isnull=True,
        )
        for case in cases:
            content = (
                f"Caso: {case.titulo}\n"
                f"Status: {case.status}\n"
                f"Especialidade: {case.especialidade}\n"
                f"Cliente: {case.cliente_nome} ({case.cliente_cpf_cnpj})\n"
                f"Tribunal: {case.tribunal} - Vara: {case.vara_juizo}\n"
                f"Comarca: {case.comarca}\n"
                f"Valor: R$ {case.valor_causa}\n"
                f"Fase: {case.fase}\n"
                f"Número: {case.numero_processo}\n"
                f"Observações: {case.observacoes}\n"
                f"Criado em: {case.created_at}\n"
                f"Atualizado em: {case.updated_at}"
            )
            _upsert_entry(
                category='case',
                title=case.titulo,
                content=content,
                source_model='cases.LegalCase',
                source_id=case.id,
                context_date=case.updated_at.date() if case.updated_at else case.created_at.date(),
            )
    except Exception as e:
        errors.append(f'cases: {str(e)}')
        logger.exception('Error syncing cases for user %s', user_id)

    # ── Deadlines ────────────────────────────────────────────────────────────
    try:
        from apps.cases.models import LegalDeadline
        deadlines = LegalDeadline.objects.filter(
            Q(responsavel_id=user_id) | Q(caso__advogado_responsavel_id=user_id),
            caso__deleted_at__isnull=True,
        ).select_related('caso')
        for d in deadlines:
            content = (
                f"Prazo: {d.titulo}\n"
                f"Caso: {d.caso.titulo if d.caso else 'N/A'}\n"
                f"Data: {d.data_prazo}\n"
                f"Tipo: {d.tipo}\n"
                f"Status: {d.status}\n"
                f"Prioridade: {d.prioridade}\n"
                f"Descrição: {d.descricao}"
            )
            _upsert_entry(
                category='deadline',
                title=d.titulo,
                content=content,
                source_model='cases.LegalDeadline',
                source_id=d.id,
                context_date=d.data_prazo,
            )
    except Exception as e:
        errors.append(f'deadlines: {str(e)}')
        logger.exception('Error syncing deadlines for user %s', user_id)

    # ── Documents (generated) ────────────────────────────────────────────────
    try:
        from apps.intelligent_assistant.models import GeneratedDocument
        docs = GeneratedDocument.objects.filter(
            session__user_id=user_id,
        ).select_related('session')
        for doc in docs:
            content = (
                f"Documento: {doc.title}\n"
                f"Tipo: {doc.session.document_type if doc.session else 'N/A'}\n"
                f"Conteúdo resumido: {doc.markdown_content[:1000] if doc.markdown_content else 'N/A'}\n"
                f"Criado em: {doc.generated_at}"
            )
            _upsert_entry(
                category='document',
                title=doc.title or 'Documento sem título',
                content=content,
                source_model='intelligent_assistant.GeneratedDocument',
                source_id=doc.id,
                context_date=doc.generated_at.date() if doc.generated_at else timezone.localdate(),
            )
    except Exception as e:
        errors.append(f'documents: {str(e)}')
        logger.exception('Error syncing documents for user %s', user_id)

    # ── Clients ──────────────────────────────────────────────────────────────
    try:
        from apps.cases.models import Client
        clients = Client.objects.filter(
            Q(responsible_lawyer_id=user_id) | Q(created_by_id=user_id),
        )
        for client in clients:
            content = (
                f"Cliente: {client.name}\n"
                f"Tipo: {client.get_client_type_display()}\n"
                f"CPF/CNPJ: {client.cpf_cnpj}\n"
                f"Email: {client.email}\n"
                f"Telefone: {client.phone}\n"
                f"Cidade: {client.city}/{client.state}\n"
                f"Notas: {client.notes}"
            )
            _upsert_entry(
                category='client',
                title=client.name,
                content=content,
                source_model='cases.Client',
                source_id=client.id,
                context_date=client.updated_at.date() if client.updated_at else client.created_at.date(),
            )
    except Exception as e:
        errors.append(f'clients: {str(e)}')
        logger.exception('Error syncing clients for user %s', user_id)

    # ── Sessions (last 20) ───────────────────────────────────────────────────
    try:
        from apps.intelligent_assistant.models import IntelligentSession
        sessions = IntelligentSession.objects.filter(
            user_id=user_id,
        ).select_related('blueprint').order_by('-created_at')[:20]
        for s in sessions:
            content = (
                f"Sessão de Geração: {s.objective}\n"
                f"Blueprint: {s.blueprint.name if s.blueprint else 'N/A'}\n"
                f"Tipo: {s.document_type}\n"
                f"Status: {s.status}\n"
                f"Criada em: {s.created_at}"
            )
            _upsert_entry(
                category='session',
                title=s.objective[:500] if s.objective else 'Sessão sem objetivo',
                content=content,
                source_model='intelligent_assistant.IntelligentSession',
                source_id=s.id,
                context_date=s.created_at.date(),
            )
    except Exception as e:
        errors.append(f'sessions: {str(e)}')
        logger.exception('Error syncing sessions for user %s', user_id)

    # ── Finalize sync log ────────────────────────────────────────────────────
    sync_log.entries_created = created
    sync_log.entries_updated = updated
    sync_log.entries_unchanged = unchanged
    sync_log.errors = errors
    sync_log.status = 'failed' if errors else 'completed'
    sync_log.completed_at = timezone.now()
    sync_log.save()

    logger.info(
        'sync_single_user_knowledge: user=%s created=%d updated=%d unchanged=%d errors=%d',
        user_id, created, updated, unchanged, len(errors),
    )
    return {
        'user_id': user_id,
        'created': created,
        'updated': updated,
        'unchanged': unchanged,
        'errors': len(errors),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Task 6: Process user reminders (every 5 minutes)
# ─────────────────────────────────────────────────────────────────────────────

def _add_months(dt, months):
    """Add months to a datetime, clamping day to month's last day."""
    import calendar
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def calculate_next_occurrence(current_date, frequency, custom_interval_days=None):
    """Calculate the next occurrence based on frequency type."""
    freq_map = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'biweekly': timedelta(weeks=2),
    }

    if frequency in freq_map:
        return current_date + freq_map[frequency]
    elif frequency == 'monthly':
        return _add_months(current_date, 1)
    elif frequency == 'quarterly':
        return _add_months(current_date, 3)
    elif frequency == 'yearly':
        return _add_months(current_date, 12)
    elif frequency == 'custom' and custom_interval_days:
        return current_date + timedelta(days=custom_interval_days)
    else:
        return current_date + timedelta(days=1)


@shared_task(name='apps.copilot.tasks.process_user_reminders')
def process_user_reminders():
    """
    Runs every 5 minutes. Checks for user-created reminders that need
    to trigger, creates notifications, and handles recurrence.
    """
    from apps.accounts.models import UserReminder, Notification

    now = timezone.now()

    due_reminders = UserReminder.objects.filter(
        status='active',
        scheduled_date__lte=now,
    ).select_related('user', 'related_case')

    created_count = 0
    for reminder in due_reminders:
        # Build notification
        notification_title = f'\u23f0 {reminder.title}'
        notification_message = reminder.description or reminder.title

        # Determine action type and link
        if reminder.copilot_prompt:
            action_type = 'copilot'
            link = _copilot_link(reminder.copilot_prompt)
        elif reminder.link:
            action_type = 'navigate'
            link = reminder.link
        else:
            action_type = 'navigate'
            link = '/dashboard/reminders'

        # Determine notification type
        notif_type = 'task'

        notification = Notification.objects.create(
            user=reminder.user,
            type=notif_type,
            priority=reminder.priority,
            title=notification_title,
            message=notification_message,
            link=link,
            copilot_prompt=reminder.copilot_prompt or '',
            action_type=action_type,
            source='cron',
            metadata={
                'reminder_id': reminder.id,
                'frequency': reminder.frequency,
                'case_id': str(reminder.related_case.id) if reminder.related_case else None,
            },
        )
        created_count += 1

        # Send via WhatsApp and Email channels
        _send_notification_channels(reminder.user, notification)

        # Update reminder state
        reminder.last_triggered = now
        reminder.trigger_count += 1

        if reminder.frequency == 'once':
            reminder.status = 'completed'
        else:
            # Calculate next occurrence
            reminder.scheduled_date = calculate_next_occurrence(
                reminder.scheduled_date,
                reminder.frequency,
                reminder.custom_interval_days,
            )
            # Check if past end_date
            if reminder.end_date and reminder.scheduled_date > reminder.end_date:
                reminder.status = 'completed'

        reminder.save()

    logger.info('process_user_reminders: %d notifications created', created_count)
    return {'created': created_count}


# ─────────────────────────────────────────────────────────────────────────────
# Task 6: Nightly deep analysis of all active cases (daily at midnight)
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(name='apps.copilot.tasks.nightly_case_analysis')
def nightly_case_analysis():
    """
    Runs daily at midnight. Deep analysis of all active cases per user.
    For each user with active cases:
    1. Count cases by status
    2. Find cases with no deadlines set
    3. Find cases with no documents generated
    4. Find cases with overdue deadlines
    5. Create a single digest notification per user
    """
    from apps.cases.models import LegalCase, LegalDeadline
    from apps.accounts.models import User, Notification
    from django.db.models import Count, Q

    today = timezone.localdate()

    # Find all users who have active cases (as owner or responsible)
    user_ids = set()
    active_cases = LegalCase.objects.filter(
        status__in=['ativo', 'aguardando'],
    ).select_related('advogado_responsavel', 'created_by')

    for case in active_cases:
        if case.advogado_responsavel_id:
            user_ids.add(case.advogado_responsavel_id)
        if case.created_by_id:
            user_ids.add(case.created_by_id)

    created_count = 0
    for user_id in user_ids:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            continue

        # Cases belonging to this user
        user_cases = LegalCase.objects.filter(
            Q(advogado_responsavel=user) | Q(created_by=user),
            status__in=['ativo', 'aguardando'],
        )
        total_cases = user_cases.count()
        if total_cases == 0:
            continue

        # Cases with no deadlines
        cases_no_deadlines = user_cases.annotate(
            num_prazos=Count('prazos'),
        ).filter(num_prazos=0).count()

        # Overdue deadlines
        overdue_deadlines = LegalDeadline.objects.filter(
            Q(responsavel=user) | Q(caso__advogado_responsavel=user),
            status__in=['pendente', 'em_andamento'],
            data_prazo__lt=today,
            caso__deleted_at__isnull=True,
        ).count()

        # Upcoming deadlines (next 7 days)
        upcoming_deadlines = LegalDeadline.objects.filter(
            Q(responsavel=user) | Q(caso__advogado_responsavel=user),
            status__in=['pendente', 'em_andamento'],
            data_prazo__gte=today,
            data_prazo__lte=today + timedelta(days=7),
            caso__deleted_at__isnull=True,
        ).count()

        # Avoid duplicate digest per user per day
        already_exists = Notification.objects.filter(
            user=user,
            type='case',
            source='cron',
            created_at__date=today,
            metadata__event='nightly_digest',
        ).exists()
        if already_exists:
            continue

        # Build digest message
        title = (
            f'Resumo diario: {total_cases} casos ativos, '
            f'{upcoming_deadlines} prazos proximos'
        )

        message_parts = [
            f'Voce tem {total_cases} caso(s) ativo(s).',
        ]
        if overdue_deadlines:
            message_parts.append(
                f'{overdue_deadlines} prazo(s) vencido(s) — acao imediata necessaria.'
            )
        if upcoming_deadlines:
            message_parts.append(
                f'{upcoming_deadlines} prazo(s) nos proximos 7 dias.'
            )
        if cases_no_deadlines:
            message_parts.append(
                f'{cases_no_deadlines} caso(s) sem prazos cadastrados.'
            )

        message = ' '.join(message_parts)

        copilot_prompt = (
            'Faca um resumo executivo dos meus casos ativos, '
            'prazos pendentes e acoes recomendadas.'
        )

        # Determine priority
        if overdue_deadlines:
            priority = 'high'
        elif upcoming_deadlines:
            priority = 'medium'
        else:
            priority = 'low'

        notification = Notification.objects.create(
            user=user,
            type='case',
            priority=priority,
            title=title,
            message=message,
            link=_copilot_link(copilot_prompt),
            copilot_prompt=copilot_prompt,
            action_type='copilot',
            source='cron',
            metadata={
                'event': 'nightly_digest',
                'total_cases': total_cases,
                'overdue_deadlines': overdue_deadlines,
                'upcoming_deadlines': upcoming_deadlines,
                'cases_no_deadlines': cases_no_deadlines,
            },
        )
        created_count += 1

        # Send via WhatsApp and Email channels
        _send_notification_channels(user, notification)

    logger.info('nightly_case_analysis: %d digest notifications created', created_count)
    return {'created': created_count}
