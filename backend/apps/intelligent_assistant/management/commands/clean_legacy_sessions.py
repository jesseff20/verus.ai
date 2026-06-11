"""
Management command para limpar sessoes e documentos legados de ETP/licitacao
do projeto anterior (contrata.ai / BravoGov).

Complementa o clean_legacy_document_types (que remove DocumentType, Category
e Blueprint) limpando os dados de producao:
- IntelligentSession com document_type legado
- GeneratedDocument, GeneratedSection, UploadedDocument, DocumentEmbedding
  vinculados a essas sessoes
- DocumentGenerator com document_type legado (apps.documents)
- Document vinculado a geradores legados
- FormTemplate com nomes de ETP/licitacao
- DocumentTemplate com nomes de ETP/licitacao

Usage:
    python manage.py clean_legacy_sessions
    python manage.py clean_legacy_sessions --dry-run
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

# Tipos legados de licitacao (mesma lista de clean_legacy_document_types)
LEGACY_TYPE_CODES = [
    'etp', 'estudo_tecnico_preliminar',
    'dfd', 'formalizacao_demanda', 'documento_formalizacao_demanda',
    'mapa_risco', 'mapa_riscos',
    'pesquisa_preco', 'pesquisa_precos',
    'tr', 'termo_referencia',
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
]

# Padroes de nome para FormTemplate e DocumentTemplate legados
LEGACY_NAME_PATTERNS = [
    'ETP', 'Estudo Técnico Preliminar', 'Estudo Tecnico Preliminar',
    'Formalização de Demanda', 'Formalizacao de Demanda',
    'Mapa de Riscos', 'Mapa de Risco',
    'Pesquisa de Preços', 'Pesquisa de Precos',
    'Termo de Referência', 'Termo de Referencia',
    'Lei 14.133', 'PMJP',
    'Edital de Licitação', 'Minuta de Contrato Adm',
]


class Command(BaseCommand):
    help = 'Remove sessoes e documentos legados de ETP/licitacao do projeto anterior'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas exibe o que seria removido, sem deletar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        prefix = '[dry-run] ' if dry_run else ''

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'{prefix}[clean_legacy_sessions] Limpando dados legados de licitacao...')
        self.stdout.write('=' * 60)

        total_deleted = 0

        # ---------------------------------------------------------------
        # 1. IntelligentSession + cascata (GeneratedDocument, Section, etc)
        # ---------------------------------------------------------------
        total_deleted += self._clean_intelligent_sessions(dry_run, prefix)

        # ---------------------------------------------------------------
        # 2. DocumentGenerator legados (apps.documents)
        # ---------------------------------------------------------------
        total_deleted += self._clean_document_generators(dry_run, prefix)

        # ---------------------------------------------------------------
        # 3. FormTemplate legados
        # ---------------------------------------------------------------
        total_deleted += self._clean_form_templates(dry_run, prefix)

        # ---------------------------------------------------------------
        # 4. DocumentTemplate legados
        # ---------------------------------------------------------------
        total_deleted += self._clean_document_templates(dry_run, prefix)

        # ---------------------------------------------------------------
        # Resumo
        # ---------------------------------------------------------------
        self.stdout.write('=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'[dry-run] Total de registros que seriam removidos: {total_deleted}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Total de registros removidos: {total_deleted}'
            ))
        self.stdout.write('[clean_legacy_sessions] Concluido.\n')

    def _clean_intelligent_sessions(self, dry_run, prefix):
        """Remove IntelligentSession com document_type legado (cascata deleta filhos)."""
        try:
            from apps.intelligent_assistant.models.session import IntelligentSession
        except ImportError:
            self.stdout.write(self.style.WARNING('  IntelligentSession nao encontrado, pulando.'))
            return 0

        qs = IntelligentSession.objects.filter(document_type__in=LEGACY_TYPE_CODES)
        count = qs.count()

        if count == 0:
            self.stdout.write('  Nenhuma IntelligentSession legada encontrada (ok).')
            return 0

        # Detalhar por tipo
        from django.db.models import Count
        breakdown = (
            qs.values('document_type')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        for item in breakdown:
            self.stdout.write(self.style.WARNING(
                f'  {prefix}{item["total"]} sessao(oes) do tipo "{item["document_type"]}"'
            ))

        # Contar registros filhos que serao deletados em cascata
        from apps.intelligent_assistant.models.session import (
            GeneratedDocument, GeneratedSection, UploadedDocument, DocumentEmbedding,
        )
        session_ids = list(qs.values_list('id', flat=True))

        child_counts = {
            'GeneratedDocument': GeneratedDocument.objects.filter(session_id__in=session_ids).count(),
            'GeneratedSection': GeneratedSection.objects.filter(session_id__in=session_ids).count(),
            'UploadedDocument': UploadedDocument.objects.filter(session_id__in=session_ids).count(),
            'DocumentEmbedding': DocumentEmbedding.objects.filter(session_id__in=session_ids).count(),
        }
        for model_name, child_count in child_counts.items():
            if child_count:
                self.stdout.write(self.style.WARNING(
                    f'    {prefix}{child_count} {model_name}(s) vinculado(s) (cascata)'
                ))

        if not dry_run:
            deleted_total, deleted_detail = qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f'  {deleted_total} registro(s) deletado(s) (sessoes + cascata)'
            ))
            return deleted_total

        return count + sum(child_counts.values())

    def _clean_document_generators(self, dry_run, prefix):
        """Remove DocumentGenerator e Document legados (apps.documents)."""
        try:
            from apps.documents.models import DocumentGenerator, Document
        except ImportError:
            self.stdout.write(self.style.WARNING('  DocumentGenerator nao encontrado, pulando.'))
            return 0

        gen_qs = DocumentGenerator.objects.filter(document_type__in=LEGACY_TYPE_CODES)
        gen_count = gen_qs.count()

        if gen_count == 0:
            self.stdout.write('  Nenhum DocumentGenerator legado encontrado (ok).')
            return 0

        # Documents vinculados a geradores legados
        doc_count = Document.objects.filter(document_generator__in=gen_qs).count()

        self.stdout.write(self.style.WARNING(
            f'  {prefix}{gen_count} DocumentGenerator(s) legado(s)'
        ))
        if doc_count:
            self.stdout.write(self.style.WARNING(
                f'    {prefix}{doc_count} Document(s) vinculado(s)'
            ))

        if not dry_run:
            # Desvincula documents (SET_NULL) antes de deletar geradores
            Document.objects.filter(document_generator__in=gen_qs).update(document_generator=None)
            deleted_total, _ = gen_qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f'  {deleted_total} DocumentGenerator(s) deletado(s), {doc_count} Document(s) desvinculado(s)'
            ))
            return deleted_total

        return gen_count

    def _clean_form_templates(self, dry_run, prefix):
        """Remove FormTemplate com nomes de ETP/licitacao."""
        try:
            from apps.forms.models import FormTemplate
        except ImportError:
            self.stdout.write(self.style.WARNING('  FormTemplate nao encontrado, pulando.'))
            return 0

        q = Q()
        for pattern in LEGACY_NAME_PATTERNS:
            q |= Q(name__icontains=pattern)

        qs = FormTemplate.objects.filter(q)
        count = qs.count()

        if count == 0:
            self.stdout.write('  Nenhum FormTemplate legado encontrado (ok).')
            return 0

        names = list(qs.values_list('name', flat=True))
        for name in names:
            self.stdout.write(self.style.WARNING(
                f'  {prefix}FormTemplate: "{name}"'
            ))

        if not dry_run:
            deleted_total, _ = qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f'  {deleted_total} FormTemplate(s) deletado(s)'
            ))
            return deleted_total

        return count

    def _clean_document_templates(self, dry_run, prefix):
        """Remove DocumentTemplate com nomes de ETP/licitacao."""
        try:
            from apps.templates.models import DocumentTemplate
        except ImportError:
            self.stdout.write(self.style.WARNING('  DocumentTemplate nao encontrado, pulando.'))
            return 0

        q = Q()
        for pattern in LEGACY_NAME_PATTERNS:
            q |= Q(name__icontains=pattern)

        qs = DocumentTemplate.objects.filter(q)
        count = qs.count()

        if count == 0:
            self.stdout.write('  Nenhum DocumentTemplate legado encontrado (ok).')
            return 0

        names = list(qs.values_list('name', flat=True))
        for name in names:
            self.stdout.write(self.style.WARNING(
                f'  {prefix}DocumentTemplate: "{name}"'
            ))

        if not dry_run:
            deleted_total, _ = qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f'  {deleted_total} DocumentTemplate(s) deletado(s)'
            ))
            return deleted_total

        return count
