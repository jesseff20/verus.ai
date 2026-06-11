"""
Management command para remover tipos de documento legados do projeto de licitação.

Remove do banco: ETP, Termo de Referência, Mapa de Risco, Pesquisa de Preço,
Formalização de Demanda e qualquer blueprint vinculado a esses tipos.

Usage:
    python manage.py clean_legacy_document_types
"""
from django.core.management.base import BaseCommand

LEGACY_TYPE_CODES = [
    # ETP / Fase Preparatória
    'etp', 'estudo_tecnico_preliminar',
    # DFD / Formalização de Demanda
    'dfd', 'formalizacao_demanda', 'documento_formalizacao_demanda',
    # Mapa de Riscos
    'mapa_risco', 'mapa_riscos',
    # Pesquisa de Preços
    'pesquisa_preco', 'pesquisa_precos',
    # Termo de Referência
    'tr', 'termo_referencia',
    # Outros documentos de licitação
    'ata_registro_preco', 'ata_registro_precos',
    'edital', 'projeto_basico', 'contrato_administrativo',
    'minuta_contrato', 'minuta_ata',
    'instrumento_convocatorio', 'aviso_licitacao',
    'boletim_medicao', 'ordem_servico', 'relatorio_fiscalizacao',
    'termo_adjudicacao', 'termo_homologacao',
    'resposta_impugnacao', 'decisao_recurso',
    'parecer_julgamento', 'parecer_habilitacao',
    'termo_recebimento_provisorio', 'termo_recebimento_definitivo',
    'aditivo_contratual',
    # Pareceres e tipos genéricos criados pela migration 0003
    'parecer', 'parecer_juridico', 'custom',
]

LEGACY_CATEGORY_CODES = [
    'licitacao', 'compras', 'aquisicao', 'planejamento',
    'processos_compras', 'gestao_contratos',
    'fase_preparatoria', 'fase_externa', 'pos_contratacao',
    'fase_contratacao', 'impugnacoes_recursos',
    # Categorias da migration 0017 que não fazem parte do domínio jurídico
    'pareceres', 'outros',
]

LEGACY_BLUEPRINT_NAME_PATTERNS = [
    'Formalização de Demanda', 'Formalizacao de Demanda',
    'Mapa de Riscos', 'Mapa de Risco',
    'Pesquisa de Preços', 'Pesquisa de Precos',
    'Estudo Técnico Preliminar', 'Estudo Tecnico Preliminar',
    'Termo de Referência', 'Termo de Referencia',
    'Lei 14.133', '14.133', 'PMJP', ' ETP',
    'Edital de Licitação', 'Minuta de Contrato Adm',
]


class Command(BaseCommand):
    help = 'Remove tipos e categorias de documentos legados do projeto de licitação'

    def handle(self, *args, **options):
        from apps.core.models import DocumentType, DocumentCategory

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('[clean_legacy] Removendo documentos legados de licitação...')
        self.stdout.write('=' * 60)

        # Remove blueprints por code do document_type
        try:
            from apps.intelligent_assistant.models import DocumentBlueprint
            from django.db.models import Q
            legacy_types = list(DocumentType.objects.filter(code__in=LEGACY_TYPE_CODES))
            bp_count = 0
            for lt in legacy_types:
                bp_qs = DocumentBlueprint.objects.filter(document_type=lt)
                n = bp_qs.count()
                if n:
                    self.stdout.write(self.style.WARNING(
                        f'  Removendo {n} blueprint(s) do tipo "{lt.code}"...'
                    ))
                    bp_qs.delete()
                    bp_count += n
            # Remove blueprints pelo nome (captura variações)
            q_nomes = Q()
            for pattern in LEGACY_BLUEPRINT_NAME_PATTERNS:
                q_nomes |= Q(name__icontains=pattern)
            bp_nome_qs = DocumentBlueprint.objects.filter(q_nomes)
            n2 = bp_nome_qs.count()
            if n2:
                bp_nome_qs.delete()
                bp_count += n2
            self.stdout.write(self.style.WARNING(f'  Total blueprints legados removidos: {bp_count}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Aviso ao remover blueprints: {e}'))

        # Remove os tipos de documento legados
        dt_qs = DocumentType.objects.filter(code__in=LEGACY_TYPE_CODES)
        dt_names = list(dt_qs.values_list('code', flat=True))
        dt_deleted, _ = dt_qs.delete()
        if dt_deleted:
            self.stdout.write(self.style.SUCCESS(
                f'  {dt_deleted} tipo(s) de documento removido(s): {", ".join(dt_names)}'
            ))
        else:
            self.stdout.write('  Nenhum tipo de documento legado encontrado (ok).')

        # Remove categorias legadas (apenas as que não têm mais DocumentTypes)
        cat_qs = DocumentCategory.objects.filter(code__in=LEGACY_CATEGORY_CODES)
        cat_deleted = 0
        cat_names = []
        for cat in cat_qs:
            if cat.document_types.exists():
                self.stdout.write(self.style.WARNING(
                    f'  Categoria "{cat.code}" mantida (ainda tem tipos vinculados)'
                ))
            else:
                cat_names.append(cat.code)
                cat.delete()
                cat_deleted += 1
        if cat_deleted:
            self.stdout.write(self.style.SUCCESS(
                f'  {cat_deleted} categoria(s) removida(s): {", ".join(cat_names)}'
            ))
        else:
            self.stdout.write('  Nenhuma categoria legada encontrada (ok).')

        self.stdout.write('=' * 60)
        self.stdout.write('[clean_legacy] Concluído.\n')
