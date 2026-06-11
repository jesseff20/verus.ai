"""
Management command para corrigir referências "ETP -" no banco de dados,
renomeando para "Estudo Técnico Preliminar -".

Uso: python manage.py fix_etp_references
     python manage.py fix_etp_references --dry-run

Idempotente — só altera registros que ainda começam com "ETP -".
"""
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):
    help = 'Renomeia títulos "ETP -" para "Estudo Técnico Preliminar -" em documentos e sessões.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas lista as alterações sem aplicá-las.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        total_changes = 0

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN — nenhuma alteração será salva ===\n"))

        # 1. GeneratedDocument (intelligent_assistant) — campo title
        total_changes += self._fix_generated_documents(dry_run)

        # 2. IntelligentSession — campo objective (display text)
        total_changes += self._fix_intelligent_sessions(dry_run)

        # 3. CaseDocument (cases) — campo titulo
        total_changes += self._fix_case_documents(dry_run)

        # Resumo
        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"DRY RUN concluído. {total_changes} registro(s) seriam alterados."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Concluído. {total_changes} registro(s) alterados."
            ))

    def _fix_generated_documents(self, dry_run):
        from apps.intelligent_assistant.models.session import GeneratedDocument

        docs = GeneratedDocument.objects.filter(title__startswith='ETP -')
        count = docs.count()
        self.stdout.write(f"\n--- GeneratedDocument (title starts with 'ETP -'): {count} encontrado(s) ---")

        changed = 0
        for doc in docs:
            old_title = doc.title
            new_title = old_title.replace('ETP -', 'Estudo Técnico Preliminar -', 1)
            self.stdout.write(f"  [{doc.id}] '{old_title}' -> '{new_title}'")
            if not dry_run:
                doc.title = new_title
                doc.save(update_fields=['title'])
            changed += 1

        return changed

    def _fix_intelligent_sessions(self, dry_run):
        from apps.intelligent_assistant.models.session import IntelligentSession

        # Check objective field for "ETP -" at start
        sessions = IntelligentSession.objects.filter(
            Q(objective__startswith='ETP -') | Q(objective__startswith='ETP -')
        )
        count = sessions.count()
        self.stdout.write(f"\n--- IntelligentSession (objective starts with 'ETP -'): {count} encontrado(s) ---")

        changed = 0
        for session in sessions:
            old_val = session.objective
            new_val = old_val.replace('ETP -', 'Estudo Técnico Preliminar -', 1)
            self.stdout.write(f"  [{session.id}] objective: '{old_val[:80]}' -> '{new_val[:80]}'")
            if not dry_run:
                session.objective = new_val
                session.save(update_fields=['objective'])
            changed += 1

        return changed

    def _fix_case_documents(self, dry_run):
        from apps.cases.models import CaseDocument

        docs = CaseDocument.objects.filter(titulo__startswith='ETP -')
        count = docs.count()
        self.stdout.write(f"\n--- CaseDocument (titulo starts with 'ETP -'): {count} encontrado(s) ---")

        changed = 0
        for doc in docs:
            old_titulo = doc.titulo
            new_titulo = old_titulo.replace('ETP -', 'Estudo Técnico Preliminar -', 1)
            self.stdout.write(f"  [{doc.id}] '{old_titulo}' -> '{new_titulo}'")
            if not dry_run:
                doc.titulo = new_titulo
                doc.save(update_fields=['titulo'])
            changed += 1

        return changed
