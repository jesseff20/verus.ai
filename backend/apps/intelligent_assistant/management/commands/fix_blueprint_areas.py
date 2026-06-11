"""
Corrige o campo areas (ManyToMany) dos DocumentBlueprints.

Para cada blueprint sem areas:
  - Adiciona a category do document_type
  - Para blueprints de recursos, adiciona também categorias secundárias

Para blueprints que já têm areas mas sem a category do document_type:
  - Adiciona a category própria

Usage:
    python manage.py fix_blueprint_areas
"""
from django.core.management.base import BaseCommand
from apps.core.models import DocumentCategory
from apps.intelligent_assistant.models import DocumentBlueprint


# Mapeamento: document_type.code → code da categoria secundária a adicionar
RECURSOS_SECUNDARIOS = {
    'recurso_ordinario_trabalhista': 'trabalhista',
    'apelacao_criminal': 'criminal',
    'rse': 'criminal',
    'apelacao': 'acoes_peticoes',
    'agravo_instrumento': 'acoes_peticoes',
    'embargos_declaracao': 'acoes_peticoes',
    'recurso_especial': 'acoes_peticoes',
    'recurso_extraordinario': 'acoes_peticoes',
    'impugnacao_cumprimento': 'execucao',
    'embargos_execucao': 'execucao',
    'liberdade_provisoria': 'criminal',
}


class Command(BaseCommand):
    help = 'Corrige o campo areas M2M nos DocumentBlueprints'

    def handle(self, *args, **options):
        blueprints = DocumentBlueprint.objects.select_related(
            'document_type__category'
        ).prefetch_related('areas').all()

        total = blueprints.count()
        fixed_empty = 0
        fixed_missing_own = 0
        fixed_secondary = 0

        # Cache de categorias por code
        category_cache = {c.code: c for c in DocumentCategory.objects.all()}

        for bp in blueprints:
            doc_type = bp.document_type
            if not doc_type:
                self.stdout.write(
                    self.style.WARNING(f'  [SKIP] Blueprint #{bp.id} "{bp.name}" sem document_type')
                )
                continue

            category = doc_type.category
            current_areas = set(bp.areas.values_list('id', flat=True))
            added_any = False

            # 1. Garantir que a categoria própria está no M2M
            if category is not None and category.id not in current_areas:
                bp.areas.add(category)
                current_areas.add(category.id)
                if len(current_areas) == 1:
                    # estava vazio antes
                    fixed_empty += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [ADD-OWN] Blueprint "{bp.name}" → área "{category.code}"'
                        )
                    )
                else:
                    fixed_missing_own += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [ADD-MISSING-OWN] Blueprint "{bp.name}" → área "{category.code}"'
                        )
                    )
                added_any = True

            # 2. Para recursos: adicionar categorias secundárias
            doc_type_code = doc_type.code or ''
            secondary_code = RECURSOS_SECUNDARIOS.get(doc_type_code)
            if secondary_code:
                secondary_cat = category_cache.get(secondary_code)
                if secondary_cat and secondary_cat.id not in current_areas:
                    bp.areas.add(secondary_cat)
                    current_areas.add(secondary_cat.id)
                    fixed_secondary += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [ADD-SECONDARY] Blueprint "{bp.name}" → área secundária "{secondary_code}"'
                        )
                    )
                    added_any = True
                elif secondary_cat is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [WARN] Categoria secundária "{secondary_code}" não encontrada no banco'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n[fix_blueprint_areas] Concluído. '
                f'Total: {total} blueprints | '
                f'Área própria adicionada (vazios): {fixed_empty} | '
                f'Área própria adicionada (existentes): {fixed_missing_own} | '
                f'Áreas secundárias adicionadas: {fixed_secondary}'
            )
        )
