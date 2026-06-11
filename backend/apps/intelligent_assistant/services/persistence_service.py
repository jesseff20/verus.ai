"""
ETP Persistence Service - Serviço de persistência para documentos ETP.

Responsável por:
1. Salvar seções individuais no banco (GeneratedSection)
2. Salvar documento completo (GeneratedDocument)
3. Orquestrar upload de arquivos para R2
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.db import transaction
from django.core.files.base import ContentFile

from apps.intelligent_assistant.models import (
    IntelligentSession,
    GeneratedSection,
    GeneratedDocument,
    DocumentBlueprint
)
from apps.intelligent_assistant.agents.etp_graph.state import (
    ETPState, get_section_key, get_section_name, SECTION_NAMES
)
from apps.intelligent_assistant.utils import strip_generation_suffix

logger = logging.getLogger(__name__)


def inject_ai_disclaimer(content: str, session_id: str, blueprint_name: str) -> str:
    """Mantida por compatibilidade — retorna o conteúdo sem modificações."""
    return content


class ETPPersistenceService:
    """
    Serviço para persistir documentos ETP no banco de dados.

    Uso:
        >>> persistence = ETPPersistenceService()
        >>> doc = persistence.save_etp_from_state(session, final_state)
        >>> print(doc.id)
    """

    def save_etp_from_state(
        self,
        session: IntelligentSession,
        state: ETPState,
        generate_pdf: bool = True,
        blueprint: Optional[DocumentBlueprint] = None
    ) -> GeneratedDocument:
        """
        Salva o ETP completo a partir do estado final do grafo.

        Args:
            session: Sessão do assistente inteligente
            state: Estado final do grafo LangGraph
            generate_pdf: Se deve gerar e salvar PDF
            blueprint: Blueprint para personalização do PDF (opcional)

        Returns:
            GeneratedDocument criado
        """
        logger.info(f"Salvando ETP para sessão {session.id}")

        with transaction.atomic():
            # 1. Salvar seções individuais
            sections_data = self._save_sections(session, state)

            # 2. Compilar markdown completo
            markdown_content = self._compile_markdown(state, blueprint)

            # 3. Calcular estatísticas
            stats = self._calculate_stats(state)

            # 4. Criar documento
            document = GeneratedDocument.objects.create(
                session=session,
                title=self._generate_title(state),
                markdown_content=markdown_content,
                file_size_markdown=len(markdown_content.encode('utf-8')),
                overall_score=stats['average_score'],
                valid_sections_count=stats['valid_count'],
                total_sections=stats['total_sections'],
                metadata={
                    'objective': state.get('objective', ''),
                    'generated_at': datetime.utcnow().isoformat(),
                    'sections_stats': stats,
                    'errors': state.get('errors', []),
                    'blueprint_id': str(blueprint.id) if blueprint else None,
                    'blueprint_name': blueprint.name if blueprint else None,
                }
            )

            logger.info(
                f"Documento ETP salvo: {document.id} "
                f"({stats['valid_count']}/{stats['total_sections']} seções válidas)"
            )

            # 5. Gerar PDF se solicitado
            if generate_pdf:
                self._generate_and_save_pdf(document, blueprint)

            return document

    def _save_sections(
        self,
        session: IntelligentSession,
        state: ETPState
    ) -> List[GeneratedSection]:
        """
        Salva todas as seções individualmente no banco.

        Args:
            session: Sessão
            state: Estado do grafo

        Returns:
            Lista de GeneratedSection criadas
        """
        sections = []
        sections_to_save = state.get('sections_to_generate', list(range(1, 16)))

        for section_num in sections_to_save:
            section_key = get_section_key(section_num)
            section_data = state.get(section_key, {})

            if not section_data:
                continue

            content = section_data.get('content', '')
            validation = section_data.get('validation', {})

            # Criar ou atualizar seção
            section, created = GeneratedSection.objects.update_or_create(
                session=session,
                section_number=section_num,
                defaults={
                    'section_name': get_section_name(section_num),
                    'content': content,
                    'is_valid': validation.get('is_valid', False),
                    'validation_errors': validation.get('structural_issues', []) +
                                        validation.get('semantic_issues', []),
                    'validation_warnings': validation.get('suggestions', []),
                    'generation_attempts': section_data.get('generation_attempts', 1),
                }
            )

            sections.append(section)
            logger.debug(
                f"Seção {section_num} salva: "
                f"{'válida' if section.is_valid else 'inválida'}"
            )

        return sections

    def _compile_markdown(self, state: ETPState, blueprint=None) -> str:
        """
        Compila todas as seções em um documento Markdown único.

        Args:
            state: Estado do grafo
            blueprint: Blueprint para determinar tipo de documento

        Returns:
            Documento completo em Markdown
        """
        # Verifica se já tem documento compilado no state
        if state.get('final_document'):
            session_id = str(state.get('session_id', ''))
            bp_name = blueprint.name if blueprint else 'padrão'
            return inject_ai_disclaimer(state['final_document'], session_id, bp_name)

        # Compila manualmente
        parts = []

        # Cabeçalho - usa tipo de documento do blueprint ou fallback
        objective = state.get('objective', 'Não especificado')
        doc_type_name = blueprint.document_type.name if blueprint and blueprint.document_type else 'ESTUDO TÉCNICO PRELIMINAR'
        parts.append(f"# {doc_type_name}")
        parts.append("")
        parts.append(f"**Objeto:** {objective}")
        parts.append("")
        parts.append("---")
        parts.append("")

        # Seções - só incluir as que foram selecionadas para geração
        sections_to_include = state.get('sections_to_generate', list(range(1, 16)))
        for section_num in sections_to_include:
            section_key = get_section_key(section_num)
            section_data = state.get(section_key, {})
            content = section_data.get('content', '')

            if content:
                section_name = SECTION_NAMES.get(section_num, f'Seção {section_num}')
                parts.append(f"## {section_num}. {strip_generation_suffix(section_name)}")
                parts.append("")
                parts.append(content)
                parts.append("")
                parts.append("---")
                parts.append("")

        # Rodapé
        parts.append("")
        parts.append("---")
        parts.append("")
        parts.append(f"*Data de elaboração: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")

        compiled = "\n".join(parts)

        # Injetar aviso obrigatório de IA ao final
        session_id = str(state.get('session_id', ''))
        bp_name = blueprint.name if blueprint else 'padrão'
        return inject_ai_disclaimer(compiled, session_id, bp_name)

    def _calculate_stats(self, state: ETPState) -> Dict[str, Any]:
        """
        Calcula estatísticas do documento.

        Conta como "gerada" qualquer seção que tenha conteúdo, independente
        de ter passado por validação de IA ou não (seções estruturadas, fixas
        e importadas também contam).
        """
        generated_count = 0
        total_score = 0.0
        word_count = 0
        sections_with_score = 0

        # Usar as seções que foram realmente geradas, não hardcoded 1-15
        sections_to_generate = state.get('sections_to_generate', [])

        # Se não tiver sections_to_generate, tentar detectar do state
        if not sections_to_generate:
            for key in state.keys():
                if key.startswith('section_') and isinstance(state.get(key), dict):
                    try:
                        section_num = int(key.replace('section_', ''))
                        sections_to_generate.append(section_num)
                    except ValueError:
                        pass
            sections_to_generate.sort()

        total_sections = len(sections_to_generate) if sections_to_generate else 0

        for section_num in sections_to_generate:
            section_key = get_section_key(section_num)
            section_data = state.get(section_key, {})
            content = section_data.get('content', '')

            if content:
                generated_count += 1
                word_count += len(content.split())

            # Score: aceitar de validation dict OU direto no section_data
            validation = section_data.get('validation', {})
            score = validation.get('score') or section_data.get('score') or 0.0
            if score > 0:
                total_score += score
                sections_with_score += 1

        average_score = total_score / sections_with_score if sections_with_score > 0 else 0.0
        completion_rate = (generated_count / total_sections * 100) if total_sections > 0 else 0.0

        return {
            'valid_count': generated_count,
            'invalid_count': total_sections - generated_count,
            'total_sections': total_sections,
            'average_score': average_score,
            'completion_rate': completion_rate,
            'total_words': word_count,
        }

    def _generate_title(self, state: ETPState) -> str:
        """
        Gera título para o documento.

        Args:
            state: Estado do grafo

        Returns:
            Título do documento
        """
        objective = state.get('objective', '')
        if objective:
            # Trunca se muito longo
            if len(objective) > 100:
                objective = objective[:97] + "..."
            return f"Estudo Técnico Preliminar - {objective}"
        return "Estudo Técnico Preliminar"

    def _generate_and_save_pdf(
        self,
        document: GeneratedDocument,
        blueprint: Optional[DocumentBlueprint] = None
    ) -> bool:
        """
        Gera PDF e salva no documento.

        Args:
            document: Documento a ser atualizado
            blueprint: Blueprint para personalização do PDF (opcional)

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            from apps.intelligent_assistant.services.pdf_service import PDFService

            pdf_service = PDFService()

            # Extrair objetivo do metadata
            objective = document.metadata.get('objective', document.title) if document.metadata else document.title

            # Se tem blueprint, usar personalização
            if blueprint:
                # Título do documento = tipo de documento (sempre)
                document_title = blueprint.document_type.name.upper() if blueprint.document_type else 'DOCUMENTO'
                # Subtítulo opcional do blueprint
                document_subtitle = blueprint.header_text or ''

                blueprint_config = {
                    # ========================================
                    # ORGANIZAÇÃO
                    # ========================================
                    'organization_name': blueprint.organization_name or 'Órgão Público',
                    'organization_acronym': blueprint.organization_acronym or '',
                    'logo_url': blueprint.logo.url if blueprint.logo else None,

                    # ========================================
                    # CABEÇALHO/RODAPÉ
                    # ========================================
                    'header_text': document_title,  # Tipo de documento no cabeçalho
                    'header_subtitle': document_subtitle,  # Subtítulo adicional
                    'footer_text': blueprint.footer_text or '',
                    'legal_basis': blueprint.legal_basis or '',

                    # ========================================
                    # CORES
                    # ========================================
                    'primary_color': blueprint.primary_color or '#7030A0',
                    'secondary_color': blueprint.secondary_color or '#5B2EE0',
                    'custom_css': blueprint.custom_css or '',

                    # ========================================
                    # PÁGINA DE ROSTO
                    # ========================================
                    'cover_page_enabled': blueprint.cover_page_enabled,
                    'cover_logo_url': blueprint.cover_logo.url if blueprint.cover_logo else None,
                    'cover_title': blueprint.cover_title or document_title,
                    'cover_subtitle': blueprint.cover_subtitle or '',
                    'cover_organization_text': blueprint.cover_organization_text or blueprint.organization_name or '',
                    'cover_footer_text': blueprint.cover_footer_text or '',
                    'cover_background_color': blueprint.cover_background_color or '#FFFFFF',

                    # ========================================
                    # TIPOGRAFIA
                    # ========================================
                    'pdf_font_family': blueprint.pdf_font_family or 'Times New Roman',
                    'pdf_font_size': blueprint.pdf_font_size or '12pt',
                    'pdf_line_height': blueprint.pdf_line_height or '1.5',
                    'pdf_text_align': blueprint.pdf_text_align or 'justify',
                    'pdf_paragraph_indent': blueprint.pdf_paragraph_indent or '1.5cm',
                    'pdf_paragraph_spacing': blueprint.pdf_paragraph_spacing or '12pt',

                    # ========================================
                    # MARGENS
                    # ========================================
                    'pdf_page_margin_top': blueprint.pdf_page_margin_top or '2.5cm',
                    'pdf_page_margin_bottom': blueprint.pdf_page_margin_bottom or '2.5cm',
                    'pdf_page_margin_left': blueprint.pdf_page_margin_left or '3cm',
                    'pdf_page_margin_right': blueprint.pdf_page_margin_right or '2cm',
                }

                pdf_bytes = pdf_service.generate_pdf_from_blueprint(
                    markdown_content=document.markdown_content,
                    objective=objective,
                    blueprint_config=blueprint_config
                )
            else:
                # Fallback para geração padrão
                pdf_bytes = pdf_service.markdown_to_pdf(
                    markdown_content=document.markdown_content,
                    title=document.title
                )

            if pdf_bytes:
                # Gera nome do arquivo baseado no tipo de documento
                doc_type_prefix = blueprint.document_type if blueprint else 'etp'
                filename = f"{doc_type_prefix}_{document.id}.pdf"

                # Salva arquivo
                document.pdf_file.save(
                    filename,
                    ContentFile(pdf_bytes),
                    save=False
                )
                document.file_size_pdf = len(pdf_bytes)
                document.pdf_generated = True

                # Se R2 está configurado, a URL será gerada automaticamente
                if document.pdf_file:
                    document.pdf_url = document.pdf_file.url

                document.save()

                logger.info(f"PDF gerado e salvo: {filename}")
                return True

        except ImportError:
            logger.warning("PDFService não disponível, pulando geração de PDF")
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {str(e)}")

        return False

    def get_document_by_session(
        self,
        session_id: str
    ) -> Optional[GeneratedDocument]:
        """
        Busca documento por ID da sessão.

        Args:
            session_id: UUID da sessão

        Returns:
            GeneratedDocument ou None
        """
        try:
            return GeneratedDocument.objects.filter(
                session_id=session_id
            ).order_by('-generated_at').first()
        except Exception as e:
            logger.error(f"Erro ao buscar documento: {str(e)}")
            return None

    def get_sections_by_session(
        self,
        session_id: str
    ) -> List[GeneratedSection]:
        """
        Busca todas as seções de uma sessão.

        Args:
            session_id: UUID da sessão

        Returns:
            Lista de GeneratedSection
        """
        return list(
            GeneratedSection.objects.filter(
                session_id=session_id
            ).order_by('section_number')
        )

    def regenerate_pdf(self, document_id: str) -> bool:
        """
        Regenera o PDF de um documento existente.

        Args:
            document_id: UUID do documento

        Returns:
            True se sucesso
        """
        try:
            document = GeneratedDocument.objects.get(id=document_id)
            return self._generate_and_save_pdf(document)
        except GeneratedDocument.DoesNotExist:
            logger.error(f"Documento não encontrado: {document_id}")
            return False
