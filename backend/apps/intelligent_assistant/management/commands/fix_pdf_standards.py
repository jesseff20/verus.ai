"""
Aplica padrão PDF ABNT NBR 14724 a todos os DocumentBlueprints.

Atualiza configurações tipográficas e de margem conforme norma ABNT
para peças jurídicas brasileiras.

Usage:
    python manage.py fix_pdf_standards
    python manage.py fix_pdf_standards --dry-run
"""
from django.core.management.base import BaseCommand
from apps.intelligent_assistant.models import DocumentBlueprint


PDF_LEGAL_STANDARDS = {
    'pdf_font_family': 'Times New Roman',
    'pdf_font_size': '12pt',
    'pdf_line_height': '1.5',
    'pdf_text_align': 'justify',
    'pdf_paragraph_indent': '1.25cm',
    'pdf_paragraph_spacing': '0pt',   # sem espaço extra entre parágrafos
    'pdf_page_margin_top': '3cm',     # ABNT: 3cm superior
    'pdf_page_margin_bottom': '2cm',  # ABNT: 2cm inferior
    'pdf_page_margin_left': '3cm',    # ABNT: 3cm esquerda (encadernação)
    'pdf_page_margin_right': '2cm',   # ABNT: 2cm direita
}


class Command(BaseCommand):
    help = 'Aplica padrão PDF ABNT NBR 14724 a todos os DocumentBlueprints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Simula a atualização sem persistir no banco',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        total = DocumentBlueprint.objects.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY-RUN] Seriam atualizados {total} blueprints com as seguintes configurações:'
                )
            )
            for key, value in PDF_LEGAL_STANDARDS.items():
                self.stdout.write(f'  {key} = {value}')
            return

        updated = DocumentBlueprint.objects.update(**PDF_LEGAL_STANDARDS)

        self.stdout.write(
            self.style.SUCCESS(
                f'[fix_pdf_standards] {updated} blueprints atualizados com padrão PDF ABNT NBR 14724.'
            )
        )
