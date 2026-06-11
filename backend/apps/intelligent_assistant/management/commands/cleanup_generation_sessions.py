"""
Management command para limpar GenerationSessions travadas em 'generating'.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.intelligent_assistant.models import GenerationSession


class Command(BaseCommand):
    help = 'Remove GenerationSessions travadas em "generating" há mais de N horas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=2,
            help='Mínimo de horas travadas para considerar fantasma (padrão: 2)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas exibe quantas sessões seriam afetadas, sem deletar',
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        qs = GenerationSession.objects.filter(
            status='generating',
            created_at__lt=cutoff,
        )
        count = qs.count()
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'[dry-run] {count} sessão(ões) seriam deletadas')
            )
        else:
            qs.delete()
            self.stdout.write(
                self.style.SUCCESS(f'{count} sessão(ões) deletadas com sucesso')
            )
