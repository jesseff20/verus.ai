"""
Management command para popular notificacoes de exemplo com Copilot.

Usage:
    python manage.py seed_notifications
    python manage.py seed_notifications --force   # Recria mesmo se existirem
    python manage.py seed_notifications --user admin  # Para um usuario especifico
"""
from urllib.parse import quote

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Notification

User = get_user_model()


def _copilot_link(prompt: str) -> str:
    return f'/dashboard/copilot?prompt={quote(prompt)}'


SAMPLE_NOTIFICATIONS = [
    # 1 — Deadline urgent (1 day)
    {
        'type': 'deadline',
        'priority': 'urgent',
        'title': 'URGENTE: Prazo vence AMANHA - Contestacao Processo 0012345-67.2026.8.19.0001',
        'message': (
            'O prazo para apresentacao de contestacao no Processo '
            '0012345-67.2026.8.19.0001 vence AMANHA. '
            'Clique para que o Copilot analise as providencias necessarias.'
        ),
        'copilot_prompt': (
            'O prazo de contestacao do processo 0012345-67.2026.8.19.0001 '
            'vence AMANHA. Quais sao as providencias necessarias '
            'e como posso preparar a documentacao a tempo?'
        ),
        'action_type': 'copilot',
        'source': 'cron',
        'metadata': {'deadline_id': 'demo-1', 'days_remaining': 1},
    },
    # 2 — Deadline medium (5 days)
    {
        'type': 'deadline',
        'priority': 'medium',
        'title': 'Prazo vence em 5 dias: Recurso de Apelacao - Costa vs TransLog',
        'message': (
            'O prazo para interposicao de Recurso de Apelacao no caso '
            'Costa vs TransLog vence em 5 dias. '
            'O Copilot pode ajudar a preparar a estrategia recursal.'
        ),
        'copilot_prompt': (
            'O prazo para Recurso de Apelacao no caso Costa vs TransLog '
            'vence em 5 dias. Quais sao as providencias necessarias '
            'e como posso preparar a documentacao?'
        ),
        'action_type': 'copilot',
        'source': 'cron',
        'metadata': {'deadline_id': 'demo-2', 'days_remaining': 5},
    },
    # 3 — Idle case
    {
        'type': 'case',
        'priority': 'medium',
        'title': 'Caso sem movimentacao ha 12 dias',
        'message': (
            'O caso "Silva vs Banco Nacional" esta sem atividade '
            'ha 12 dias. O Copilot pode ajudar a analisar o status '
            'e sugerir proximos passos.'
        ),
        'copilot_prompt': (
            'O caso "Silva vs Banco Nacional" nao tem movimentacao '
            'ha 12 dias. Analise o status atual e sugira proximos passos.'
        ),
        'action_type': 'copilot',
        'source': 'cron',
        'metadata': {'case_id': 'demo-idle', 'days_idle': 12},
    },
    # 4 — Pending document
    {
        'type': 'document',
        'priority': 'medium',
        'title': 'Documento pendente: Peticao Inicial',
        'message': (
            'A geracao da Peticao Inicial esta parada ha mais de 24 horas. '
            'Clique para que o Copilot ajude a concluir.'
        ),
        'copilot_prompt': (
            'A sessao de geracao do documento "Peticao Inicial" esta '
            'pendente ha mais de 24h. O que falta para concluir?'
        ),
        'action_type': 'copilot',
        'source': 'cron',
        'metadata': {'session_id': 'demo-doc', 'document_type': 'peticao_inicial'},
    },
    # 5 — Welcome / onboarding
    {
        'type': 'system',
        'priority': 'low',
        'title': 'Bem-vindo ao Verus.AI! Conheca o Copilot',
        'message': (
            'Bem-vindo ao Verus.AI! O Copilot e seu assistente juridico '
            'com IA. Ele monitora seus prazos, analisa casos e sugere '
            'acoes proativamente. Clique para iniciar uma conversa.'
        ),
        'copilot_prompt': (
            'Ola! Sou novo no Verus.AI. Me explique suas principais '
            'funcionalidades e como voce pode me ajudar no dia a dia juridico.'
        ),
        'action_type': 'copilot',
        'source': 'copilot',
        'metadata': {'event': 'welcome'},
    },
]


class Command(BaseCommand):
    help = 'Popula notificacoes de exemplo com integracao Copilot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recria notificacoes mesmo se ja existirem',
        )
        parser.add_argument(
            '--user',
            type=str,
            default=None,
            help='Username do usuario alvo (padrao: primeiro superadmin ou admin)',
        )

    def handle(self, *args, **options):
        force = options['force']
        username = options.get('user')

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Usuario "{username}" nao encontrado.'))
                return
        else:
            user = User.objects.filter(role__in=['superadmin', 'admin']).first()
            if not user:
                user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()
            if not user:
                self.stderr.write(self.style.ERROR('Nenhum usuario encontrado no sistema.'))
                return

        existing = Notification.objects.filter(user=user).count()
        if existing > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Usuario "{user.username}" ja possui {existing} notificacoes. '
                    f'Use --force para recriar.'
                )
            )
            return

        if force:
            deleted, _ = Notification.objects.filter(user=user).delete()
            if deleted:
                self.stdout.write(f'Removidas {deleted} notificacoes existentes.')

        for data in SAMPLE_NOTIFICATIONS:
            # Build the link from copilot_prompt
            prompt = data.get('copilot_prompt', '')
            link = _copilot_link(prompt) if prompt else ''
            Notification.objects.create(user=user, link=link, **data)

        self.stdout.write(
            self.style.SUCCESS(
                f'{len(SAMPLE_NOTIFICATIONS)} notificacoes com Copilot '
                f'criadas para "{user.username}".'
            )
        )
