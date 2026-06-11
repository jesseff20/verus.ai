"""
Management command para calcular analytics do assistente
Execução: python manage.py calculate_assistant_analytics
Pode ser agendado via cron para rodar diariamente
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime as _datetime
from apps.agents.models_assistant import (
    AssistantConversation,
    AssistantMessage,
    AssistantFeedback,
    AssistantAnalytics,
    AssistantKnowledgeQuery,
)


class Command(BaseCommand):
    help = 'Calcula analytics agregados do assistente para o dia anterior'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Data específica para calcular (formato: YYYY-MM-DD). Se não informado, calcula para ontem.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recalcular mesmo se já existir analytics para a data',
        )

    def handle(self, *args, **options):
        # Determinar data
        if options['date']:
            from datetime import datetime
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            # Ontem por padrão
            target_date = (timezone.now() - timedelta(days=1)).date()

        self.stdout.write(f"📊 Calculando analytics para {target_date}...")

        # Verificar se já existe
        existing = AssistantAnalytics.objects.filter(date=target_date).first()
        if existing and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Analytics para {target_date} já existe (ID: {existing.id}). "
                    "Use --force para recalcular."
                )
            )
            return

        # Período do dia
        start_datetime = timezone.make_aware(
            _datetime.combine(target_date, _datetime.min.time())
        )
        end_datetime = start_datetime + timedelta(days=1)

        # === 1. CONVERSAS ===
        conversations = AssistantConversation.objects.filter(
            started_at__gte=start_datetime,
            started_at__lt=end_datetime
        )
        total_conversations = conversations.count()
        unique_users = conversations.values('user').distinct().count()

        self.stdout.write(f"  💬 Conversas: {total_conversations}")
        self.stdout.write(f"  👥 Usuários únicos: {unique_users}")

        # Se não houver conversas, não criar analytics
        if total_conversations == 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Nenhuma conversa encontrada para {target_date}. Analytics não será criado."
                )
            )
            # Se existir registro antigo, deletá-lo
            if existing:
                existing.delete()
                self.stdout.write(f"  🗑️  Registro antigo deletado (sem dados).")
            return

        # === 2. MENSAGENS ===
        messages = AssistantMessage.objects.filter(
            created_at__gte=start_datetime,
            created_at__lt=end_datetime
        )
        total_messages = messages.count()

        # Métricas de mensagens do assistente
        assistant_messages = messages.filter(role='assistant')
        avg_response_time = assistant_messages.aggregate(
            avg=Avg('response_time_ms')
        )['avg'] or 0
        total_tokens = assistant_messages.aggregate(
            total=Count('tokens_used')
        )['total'] or 0

        self.stdout.write(f"  📝 Mensagens: {total_messages}")
        self.stdout.write(f"  ⏱️  Tempo médio de resposta: {avg_response_time:.0f}ms")
        self.stdout.write(f"  🪙 Tokens usados: {total_tokens}")

        # === 3. FEEDBACKS ===
        feedbacks = AssistantFeedback.objects.filter(
            created_at__gte=start_datetime,
            created_at__lt=end_datetime
        )
        total_feedbacks = feedbacks.count()
        positive_feedbacks = feedbacks.filter(feedback_type='positive').count()
        negative_feedbacks = feedbacks.filter(feedback_type='negative').count()

        # Taxa de satisfação: apenas calcular se houver feedbacks
        # Se não houver, deixa None para não contaminar médias
        if total_feedbacks > 0:
            satisfaction_rate = (positive_feedbacks / total_feedbacks * 100)
        else:
            satisfaction_rate = None  # Não calcular taxa sem feedbacks

        self.stdout.write(f"  👍 Feedbacks positivos: {positive_feedbacks}")
        self.stdout.write(f"  👎 Feedbacks negativos: {negative_feedbacks}")
        if satisfaction_rate is not None:
            self.stdout.write(f"  📈 Taxa de satisfação: {satisfaction_rate:.1f}%")
        else:
            self.stdout.write(f"  📈 Taxa de satisfação: N/A (sem feedbacks)")

        # Breakdown de problemas (feedbacks negativos)
        incorrect_count = feedbacks.filter(reason='incorrect').count()
        incomplete_count = feedbacks.filter(reason='incomplete').count()
        irrelevant_count = feedbacks.filter(reason='irrelevant').count()
        unclear_count = feedbacks.filter(reason='unclear').count()
        outdated_count = feedbacks.filter(reason='outdated').count()

        # === 4. KNOWLEDGE BASE ===
        kb_queries = AssistantKnowledgeQuery.objects.filter(
            created_at__gte=start_datetime,
            created_at__lt=end_datetime
        )
        total_kb_queries = kb_queries.count()

        self.stdout.write(f"  🔍 Queries na KB: {total_kb_queries}")

        # === 5. MÉTRICAS AGREGADAS ===
        avg_messages_per_conversation = (
            total_messages / total_conversations
        ) if total_conversations > 0 else 0

        # === 6. SALVAR NO BANCO ===
        if existing:
            # Atualizar existente
            analytics = existing
            self.stdout.write(f"  🔄 Atualizando analytics existente...")
        else:
            # Criar novo
            analytics = AssistantAnalytics(date=target_date)
            self.stdout.write(f"  ✨ Criando novo registro de analytics...")

        analytics.total_conversations = total_conversations
        analytics.total_messages = total_messages
        analytics.unique_users = unique_users
        analytics.avg_messages_per_conversation = avg_messages_per_conversation
        analytics.avg_response_time_ms = int(avg_response_time)
        analytics.total_tokens_used = total_tokens
        analytics.total_kb_queries = total_kb_queries
        analytics.total_feedbacks = total_feedbacks
        analytics.positive_feedbacks = positive_feedbacks
        analytics.negative_feedbacks = negative_feedbacks
        analytics.satisfaction_rate = satisfaction_rate
        analytics.incorrect_count = incorrect_count
        analytics.incomplete_count = incomplete_count
        analytics.irrelevant_count = irrelevant_count
        analytics.unclear_count = unclear_count
        analytics.outdated_count = outdated_count
        analytics.calculated_at = timezone.now()

        analytics.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Analytics para {target_date} calculados com sucesso! (ID: {analytics.id})"
            )
        )
