"""
Define visibilidade dos blueprints para contexto de Procuradoria Municipal.

Blueprints de categorias irrelevantes são desativados (is_active=False).
Blueprints de áreas pertinentes à procuradoria permanecem ativos.

Uso:
    python manage.py set_blueprint_visibility
    python manage.py set_blueprint_visibility --dry-run
    python manage.py set_blueprint_visibility --list
"""
from django.core.management.base import BaseCommand
from django.db import transaction

# Categorias que NÃO fazem sentido para uma procuradoria municipal
CATEGORIAS_INATIVAS = [
    'criminal',
    'penal',
    'familia',
    'sucessoes',
    'heranca',
    'trabalhista',
    'militar',
    'empresarial',
    'societario',
    'imobiliario',
    'locacao',
    'consumidor',
    'digital',
    'eleitoral',
    'internacional',
]

# Categorias que SÃO pertinentes à procuradoria municipal
CATEGORIAS_ATIVAS = [
    'tributario',
    'administrativo',
    'constitucional',
    'ambiental',
    'civel',
    'previdenciario',
    'licitacoes',
    'contratos',
    'divida_ativa',
    'urbanismo',
    'improbidade',
    'lgpd',
    'compliance',
]


class Command(BaseCommand):
    help = 'Ativa/desativa blueprints conforme pertinência à Procuradoria Municipal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Exibe o que seria alterado sem salvar',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista todos os blueprints e seu status atual',
        )

    def handle(self, *args, **options):
        from apps.intelligent_assistant.models import DocumentBlueprint

        dry_run = options['dry_run']
        list_mode = options['list']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Visibilidade de Blueprints (Procuradoria)'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if list_mode:
            self._list_blueprints()
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))

        with transaction.atomic():
            self._set_visibility(dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY-RUN] Nenhuma alteração foi salva.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Visibilidade configurada com sucesso!\n'))

    def _list_blueprints(self):
        from apps.intelligent_assistant.models import DocumentBlueprint
        blueprints = DocumentBlueprint.objects.select_related(
            'document_type', 'document_type__category'
        ).order_by('document_type__category__name', 'name')

        self.stdout.write('\nBlueprints cadastrados:\n')
        current_cat = None
        for bp in blueprints:
            cat = bp.document_type.category.name if bp.document_type and bp.document_type.category else '(sem categoria)'
            if cat != current_cat:
                self.stdout.write(f'\n  [{cat}]')
                current_cat = cat
            status = '✓ ATIVO  ' if bp.is_active else '✗ inativo'
            self.stdout.write(f'    {status} — {bp.name}')

    def _set_visibility(self, dry_run: bool):
        from apps.intelligent_assistant.models import DocumentBlueprint

        blueprints = DocumentBlueprint.objects.select_related(
            'document_type', 'document_type__category'
        ).all()

        activated = 0
        deactivated = 0
        unchanged = 0

        for bp in blueprints:
            cat_code = (
                bp.document_type.category.code
                if bp.document_type and bp.document_type.category
                else None
            )

            should_be_active = True  # default: mantém ativo se categoria desconhecida

            if cat_code:
                if cat_code in CATEGORIAS_INATIVAS:
                    should_be_active = False
                elif cat_code in CATEGORIAS_ATIVAS:
                    should_be_active = True
                # Categorias não listadas: mantém estado atual

            if bp.is_active == should_be_active:
                unchanged += 1
                continue

            if should_be_active:
                action = 'ATIVAR'
                activated += 1
            else:
                action = 'DESATIVAR'
                deactivated += 1

            self.stdout.write(f'  [{action}] {bp.name} (categoria: {cat_code or "?"})')

            if not dry_run:
                bp.is_active = should_be_active
                bp.save(update_fields=['is_active'])

        self.stdout.write(f'\nResumo:')
        self.stdout.write(f'  Ativados:    {activated}')
        self.stdout.write(f'  Desativados: {deactivated}')
        self.stdout.write(f'  Sem mudança: {unchanged}')
