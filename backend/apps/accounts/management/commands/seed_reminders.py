"""
Management command para popular lembretes de exemplo.

Usage:
    python manage.py seed_reminders
    python manage.py seed_reminders --force   # Recria mesmo se existirem
    python manage.py seed_reminders --user admin  # Para um usuario especifico
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import UserReminder

User = get_user_model()

SAMPLE_REMINDERS = [
    {
        'title': 'Verificar prazo Processo 123/2026',
        'description': 'Verificar documentacao pendente e prazo de contestacao no Processo 123/2026.',
        'frequency': 'once',
        'scheduled_date_offset_days': 2,
        'priority': 'high',
        'copilot_prompt': '',
        'link': '/dashboard/processos',
    },
    {
        'title': 'Revisar andamentos dos casos ativos',
        'description': 'Fazer revisao semanal de todos os casos ativos e identificar pendencias.',
        'frequency': 'weekly',
        'scheduled_date_offset_days': 1,
        'priority': 'medium',
        'copilot_prompt': 'Faca uma revisao geral dos meus casos ativos e indique quais precisam de atencao imediata.',
        'link': '',
    },
    {
        'title': 'Preparar relatorio mensal para cliente',
        'description': 'Consolidar atividades do mes e preparar relatorio para envio ao cliente.',
        'frequency': 'monthly',
        'scheduled_date_offset_days': 3,
        'priority': 'medium',
        'copilot_prompt': 'Ajude-me a preparar o relatorio mensal de atividades juridicas para os clientes.',
        'link': '',
    },
    {
        'title': 'Audiencia - Costa vs TransLog',
        'description': 'Preparar documentacao e argumentos para a audiencia do caso Costa vs TransLog.',
        'frequency': 'once',
        'scheduled_date_offset_days': 5,
        'priority': 'urgent',
        'copilot_prompt': (
            'Preciso me preparar para a audiencia do caso Costa vs TransLog. '
            'Revise os pontos principais, jurisprudencia relevante e '
            'sugira a estrategia de argumentacao.'
        ),
        'link': '/dashboard/processos',
    },
    {
        'title': 'Atualizar base de conhecimento',
        'description': 'Revisar e atualizar a base de conhecimento juridica com novas legislacoes e jurisprudencias.',
        'frequency': 'quarterly',
        'scheduled_date_offset_days': 10,
        'priority': 'low',
        'copilot_prompt': '',
        'link': '/dashboard/knowledge-base',
    },
]


class Command(BaseCommand):
    help = 'Popula lembretes de exemplo para o usuario admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recria lembretes mesmo se ja existirem',
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

        existing = UserReminder.objects.filter(user=user).count()
        if existing > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Usuario "{user.username}" ja possui {existing} lembretes. '
                    f'Use --force para recriar.'
                )
            )
            return

        if force:
            deleted, _ = UserReminder.objects.filter(user=user).delete()
            if deleted:
                self.stdout.write(f'Removidos {deleted} lembretes existentes.')

        now = timezone.now()
        for data in SAMPLE_REMINDERS:
            offset = data.pop('scheduled_date_offset_days')
            scheduled = now + timedelta(days=offset)
            UserReminder.objects.create(
                user=user,
                scheduled_date=scheduled,
                **data,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'{len(SAMPLE_REMINDERS)} lembretes criados para "{user.username}".'
            )
        )
