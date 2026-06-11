"""
Management command para corrigir domínios de email de todos os usuários.

Altera qualquer domínio de email para @verus.ai, mantendo o username.
Exemplos:
    admin@contrata.ai       → admin@verus.ai
    jesse@bravonix.ai       → jesse@verus.ai
    gestor@proderj.rj.gov.br → gestor@verus.ai

Idempotente: seguro para executar múltiplas vezes.

Usage:
    python manage.py fix_user_emails
    python manage.py fix_user_emails --dry-run   # Apenas mostra o que seria alterado
"""
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

TARGET_DOMAIN = 'verus.ai'

User = get_user_model()


class Command(BaseCommand):
    help = 'Corrige domínio de email de todos os usuários para @verus.ai'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria alterado, sem salvar',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN] Nenhuma alteração será salva.\n'))

        users = User.objects.all()
        changed = 0
        skipped = 0

        for user in users:
            email = (user.email or '').strip()

            if not email or '@' not in email:
                skipped += 1
                continue

            local_part, domain = email.rsplit('@', 1)

            if domain.lower() == TARGET_DOMAIN:
                skipped += 1
                continue

            new_email = f'{local_part}@{TARGET_DOMAIN}'

            if dry_run:
                self.stdout.write(
                    f'  [DRY-RUN] {user.username}: {email} → {new_email}'
                )
            else:
                old_email = email
                user.email = new_email
                user.save(update_fields=['email'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {user.username}: {old_email} → {new_email}'
                    )
                )
                logger.info(
                    'fix_user_emails: %s alterado de %s para %s',
                    user.username, old_email, new_email,
                )

            changed += 1

        self.stdout.write('')
        if changed:
            verb = 'seriam alterados' if dry_run else 'alterados'
            self.stdout.write(
                self.style.SUCCESS(f'{changed} email(s) {verb}.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Nenhum email precisou ser alterado. Todos já usam @verus.ai.')
            )

        if skipped:
            self.stdout.write(f'{skipped} usuário(s) já corretos ou sem email.')
