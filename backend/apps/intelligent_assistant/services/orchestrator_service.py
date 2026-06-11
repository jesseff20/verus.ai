"""
Orchestrator Service para geração completa de ETP usando LangGraph.

Este serviço é o ponto de entrada principal para gerar um ETP completo,
orquestrando todos os agentes através do grafo LangGraph com 15 seções
conforme Lei 14.133/2021.
"""
import logging
from typing import Dict, Any, Optional, Generator, List
from datetime import datetime

from apps.intelligent_assistant.agents.etp_graph.etp_graph import (
    ETPGraphRunner, create_etp_graph, compile_etp_graph
)
from apps.intelligent_assistant.agents.etp_graph.state import (
    ETPState, create_initial_state, get_section_key, get_section_name
)
from apps.intelligent_assistant.services.claude_service import ClaudeService
from apps.intelligent_assistant.services.knowledge_base_service import KnowledgeBaseService
from apps.intelligent_assistant.services.persistence_service import ETPPersistenceService
from apps.intelligent_assistant.models import IntelligentSession, GeneratedDocument

logger = logging.getLogger(__name__)


class ETPOrchestratorService:
    """
    Serviço que orquestra a geração completa do ETP usando LangGraph.

    Este serviço:
    1. Cria/gerencia sessão do assistente
    2. Executa o grafo LangGraph com 15 seções
    3. Persiste o resultado no banco de dados
    4. Gera PDF e faz upload para R2

    Lei 14.133/2021 - 15 Seções:
    1. Descrição da Necessidade
    2. Previsão no Plano de Contratações Anual
    3. Requisitos da Contratação
    4. Estimativa das Quantidades
    5. Levantamento de Mercado
    6. Estimativa do Preço
    7. Descrição da Solução
    8. Justificativa para Parcelamento
    9. Resultados Pretendidos
    10. Providências Prévias
    11. Contratações Correlatas
    12. Impactos Ambientais
    13. Viabilidade da Contratação
    14. Publicidade do ETP
    15. Responsáveis pela Elaboração

    Uso:
        >>> orchestrator = ETPOrchestratorService()
        >>> result = orchestrator.generate_etp(
        ...     user=request.user,
        ...     objective="Contratar serviço de impressão",
        ...     collection_name="legislacao"
        ... )
        >>> print(result['document'].pdf_url)
    """

    def __init__(self):
        """Inicializa o orchestrador com os serviços necessários."""
        self.claude_service = ClaudeService()
        self.kb_service = KnowledgeBaseService()
        self.persistence_service = ETPPersistenceService()

        # Runner do grafo (lazy loading)
        self._graph_runner = None

    @property
    def graph_runner(self) -> ETPGraphRunner:
        """Retorna o runner do grafo (lazy loading)."""
        if self._graph_runner is None:
            self._graph_runner = ETPGraphRunner(
                self.claude_service,
                self.kb_service
            )
        return self._graph_runner

    def generate_etp(
        self,
        user,
        objective: str,
        collection_name: str = 'default',
        max_retries: int = 2,
        generate_pdf: bool = True,
        session: Optional[IntelligentSession] = None
    ) -> Dict[str, Any]:
        """
        Gera ETP completo usando o grafo LangGraph e persiste no banco.

        Args:
            user: Usuário Django que está gerando o ETP
            objective: Objetivo da contratação
            collection_name: ID da sessão para buscar embeddings no PgVector
            max_retries: Máximo de tentativas por seção (default: 2)
            generate_pdf: Se deve gerar PDF automaticamente
            session: Sessão existente (opcional)

        Returns:
            Dict com:
                - success (bool): Se geração foi bem-sucedida
                - session (IntelligentSession): Sessão criada/usada
                - document (GeneratedDocument): Documento salvo
                - state (ETPState): Estado final do grafo
                - stats (dict): Estatísticas da geração
                - errors (list): Erros encontrados

        Raises:
            ValueError: Se objective estiver vazio
        """
        # Validar input
        if not objective or not objective.strip():
            raise ValueError("Objetivo da contratação é obrigatório")

        objective = objective.strip()

        logger.info(f"\n{'='*80}")
        logger.info(f"Iniciando geração de ETP (15 seções)")
        logger.info(f"Objetivo: {objective[:100]}...")
        logger.info(f"Collection: {collection_name}")
        logger.info(f"Max retries: {max_retries}")
        logger.info(f"{'='*80}\n")

        try:
            # 1. Tentar usar sessão existente ou criar nova
            if session is None:
                # Tentar buscar sessão pelo collection_name (que é o session_id)
                if collection_name and collection_name != 'default':
                    try:
                        session = IntelligentSession.objects.get(
                            id=collection_name,
                            user=user
                        )
                        logger.info(f"Usando sessão existente: {session.id}")
                    except IntelligentSession.DoesNotExist:
                        logger.warning(f"Sessão {collection_name} não encontrada, criando nova")
                        session = None

                # Se não encontrou, criar nova
                if session is None:
                    session = self._create_session(user, objective, collection_name)

            # 2. Atualizar status da sessão
            session.status = 'generating'
            session.save()

            # 3. Executar grafo
            final_state = self.graph_runner.run(
                objective=objective,
                collection_name=collection_name,
                user_id=str(user.id) if user else None,
                max_retries=max_retries
            )

            # 4. Atualizar status
            session.status = 'validating'
            session.save()

            # 5. Persistir resultado
            document = self.persistence_service.save_etp_from_state(
                session=session,
                state=final_state,
                generate_pdf=generate_pdf
            )

            # 6. Finalizar sessão
            session.status = 'completed'
            session.save()

            # 7. Preparar resultado
            stats = self._calculate_stats(final_state)
            result = {
                'success': stats['valid_count'] > 0,
                'session': session,
                'document': document,
                'state': final_state,
                'stats': stats,
                'errors': final_state.get('errors', []),
                'sections': self._extract_sections(final_state),
                'markdown_content': document.markdown_content,
                'pdf_url': document.pdf_url,
            }

            logger.info(f"\n{'='*80}")
            logger.info(f"Geração de ETP concluída!")
            logger.info(f"Sessão: {session.id}")
            logger.info(f"Documento: {document.id}")
            logger.info(f"Seções válidas: {stats['valid_count']}/15")
            logger.info(f"Score médio: {stats['average_score']:.1f}%")
            logger.info(f"PDF URL: {document.pdf_url or 'Não gerado'}")
            logger.info(f"{'='*80}\n")

            return result

        except Exception as e:
            logger.error(f"Erro durante geração do ETP: {str(e)}")

            if session:
                session.status = 'failed'
                session.error_message = str(e)
                session.save()

            raise

    def generate_etp_stream(
        self,
        user,
        objective: str,
        collection_name: str = 'default',
        max_retries: int = 2
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Gera ETP com streaming de eventos (para UI em tempo real).

        Args:
            user: Usuário Django
            objective: Objetivo da contratação
            collection_name: ID da sessão para buscar embeddings no PgVector

        Yields:
            Dict com eventos do grafo:
                - event: str (ex: "section_generated", "section_validated")
                - section: int (número da seção)
                - data: dict com dados do evento
        """
        if not objective or not objective.strip():
            raise ValueError("Objetivo da contratação é obrigatório")

        objective = objective.strip()

        # Criar sessão
        session = self._create_session(user, objective, collection_name)
        session.status = 'generating'
        session.save()

        yield {
            'event': 'session_created',
            'session_id': str(session.id),
            'data': {'objective': objective}
        }

        try:
            # Executar com streaming
            for state_update in self.graph_runner.stream(
                objective=objective,
                collection_name=collection_name,
                user_id=str(user.id) if user else None,
                max_retries=max_retries
            ):
                # Determinar qual evento ocorreu
                event = self._determine_event(state_update)
                yield event

            # Estado final
            final_state = state_update

            # Persistir
            document = self.persistence_service.save_etp_from_state(
                session=session,
                state=final_state,
                generate_pdf=True
            )

            session.status = 'completed'
            session.save()

            yield {
                'event': 'completed',
                'session_id': str(session.id),
                'document_id': str(document.id),
                'data': {
                    'pdf_url': document.pdf_url,
                    'stats': self._calculate_stats(final_state)
                }
            }

        except Exception as e:
            session.status = 'failed'
            session.error_message = str(e)
            session.save()

            yield {
                'event': 'error',
                'session_id': str(session.id),
                'data': {'error': str(e)}
            }

    def _create_session(
        self,
        user,
        objective: str,
        collection_name: str
    ) -> IntelligentSession:
        """
        Cria nova sessão do assistente.

        Args:
            user: Usuário Django
            objective: Objetivo
            collection_name: ID da sessão para identificação

        Returns:
            IntelligentSession criada
        """
        session = IntelligentSession.objects.create(
            user=user,
            objective=objective,
            document_type='etp',
            status='initialized',
            kb_collection_id=collection_name
        )
        logger.info(f"Sessão criada: {session.id}")
        return session

    def _calculate_stats(self, state: ETPState) -> Dict[str, Any]:
        """
        Calcula estatísticas do estado final.

        Args:
            state: Estado final do grafo

        Returns:
            Dict com estatísticas
        """
        valid_count = 0
        invalid_count = 0
        total_score = 0.0
        total_words = 0

        # Obter número de seções geradas (pode ser menor que 15 se selecionou apenas algumas)
        sections_generated = state.get('sections_to_generate', list(range(1, 16)))
        total_sections_count = len(sections_generated)

        # Iterar apenas nas seções que foram geradas
        for section_num in sections_generated:
            section_key = get_section_key(section_num)
            section_data = state.get(section_key, {})
            validation = section_data.get('validation', {})

            if validation.get('is_valid'):
                valid_count += 1
            else:
                invalid_count += 1

            total_score += validation.get('score', 0.0)

            content = section_data.get('content', '')
            if content:
                total_words += len(content.split())

        return {
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'total_sections': total_sections_count,
            'average_score': (total_score / total_sections_count) if total_score else 0.0,  # Score já é 0-100
            'completion_rate': (valid_count / total_sections_count) * 100,
            'total_words': total_words,
            'errors_count': len(state.get('errors', [])),
            'total_tokens_used': state.get('total_tokens_used', 0),
        }

    def _extract_sections(self, state: ETPState) -> Dict[str, Dict[str, Any]]:
        """
        Extrai dados das seções do estado.

        Args:
            state: Estado do grafo

        Returns:
            Dict com dados de cada seção
        """
        sections = {}

        for section_num in range(1, 16):
            section_key = get_section_key(section_num)
            section_data = state.get(section_key, {})

            sections[section_key] = {
                'number': section_num,
                'name': get_section_name(section_num),
                'content': section_data.get('content', ''),
                'status': str(section_data.get('status', 'pending')),
                'is_valid': section_data.get('validation', {}).get('is_valid', False),
                'score': section_data.get('validation', {}).get('score', 0.0),
                'attempts': section_data.get('generation_attempts', 0),
            }

        return sections

    def _determine_event(self, state_update: Dict) -> Dict[str, Any]:
        """
        Determina qual evento ocorreu baseado na atualização de estado.

        Args:
            state_update: Atualização de estado do grafo

        Returns:
            Dict com evento formatado
        """
        # Detectar qual nó executou
        for key, value in state_update.items():
            if key.startswith('generate_'):
                section_num = int(key.replace('generate_', ''))
                return {
                    'event': 'section_generating',
                    'section': section_num,
                    'section_name': get_section_name(section_num),
                    'data': {}
                }
            elif key.startswith('validate_'):
                section_num = int(key.replace('validate_', ''))
                return {
                    'event': 'section_validated',
                    'section': section_num,
                    'section_name': get_section_name(section_num),
                    'data': {}
                }

        return {'event': 'update', 'data': state_update}

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Retorna status de uma sessão.

        Args:
            session_id: UUID da sessão

        Returns:
            Dict com status
        """
        try:
            session = IntelligentSession.objects.get(id=session_id)
            document = self.persistence_service.get_document_by_session(session_id)
            sections = self.persistence_service.get_sections_by_session(session_id)

            return {
                'session_id': str(session.id),
                'status': session.status,
                'objective': session.objective,
                'document_type': session.document_type,
                'created_at': session.created_at.isoformat(),
                'has_document': document is not None,
                'document_id': str(document.id) if document else None,
                'pdf_url': document.pdf_url if document else None,
                'sections_count': len(sections),
                'valid_sections': sum(1 for s in sections if s.is_valid),
                'error_message': session.error_message,
            }

        except IntelligentSession.DoesNotExist:
            return {'error': 'Sessão não encontrada'}

    def regenerate_pdf(self, document_id: str) -> Dict[str, Any]:
        """
        Regenera PDF de um documento existente.

        Args:
            document_id: UUID do documento

        Returns:
            Dict com resultado
        """
        success = self.persistence_service.regenerate_pdf(document_id)

        if success:
            document = GeneratedDocument.objects.get(id=document_id)
            return {
                'success': True,
                'pdf_url': document.pdf_url,
                'file_size': document.file_size_pdf,
            }

        return {'success': False, 'error': 'Falha ao regenerar PDF'}

    def generate_etp_with_events(
        self,
        user,
        objective: str,
        collection_name: str = 'default',
        max_retries: int = 2,
        sections: Optional[List[int]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Gera ETP emitindo eventos detalhados para streaming SSE.

        Este método executa o grafo seção por seção, emitindo eventos
        que permitem ao frontend atualizar a UI em tempo real.

        Args:
            user: Usuário Django
            objective: Objetivo da contratação
            collection_name: ID da sessão existente ou 'default' para criar nova
            max_retries: Número máximo de tentativas por seção
            sections: Lista de números das seções a gerar (1-15). Se None, gera todas.

        Yields:
            Dict com eventos formatados para SSE:
                - section_start: Início da geração
                - section_generated: Seção gerada
                - section_validated: Seção validada
                - section_content: Conteúdo da seção
                - progress: Progresso geral
                - completed: Geração finalizada
                - error: Erro ocorrido
        """
        if not objective or not objective.strip():
            yield {
                'event': 'error',
                'message': 'Objetivo da contratação é obrigatório'
            }
            return

        import time
        objective = objective.strip()
        session = None
        sections_completed = 0
        start_time = time.time()

        # Seções a gerar (default: todas as 15)
        sections_to_generate = sections if sections else list(range(1, 16))
        total_sections = len(sections_to_generate)

        try:
            # Tentar usar sessão existente ou criar nova
            if collection_name and collection_name != 'default':
                try:
                    session = IntelligentSession.objects.get(
                        id=collection_name,
                        user=user
                    )
                    logger.info(f"Usando sessão existente: {session.id}")
                except IntelligentSession.DoesNotExist:
                    logger.warning(f"Sessão {collection_name} não encontrada, criando nova")
                    session = None

            # Se não encontrou sessão existente, criar nova
            if session is None:
                session = self._create_session(user, objective, collection_name)

            session.status = 'generating'
            session.save()

            yield {
                'event': 'session_created',
                'session_id': str(session.id),
                'message': f'Sessão criada, gerando {total_sections} seções...',
                'sections_to_generate': sections_to_generate
            }

            # Usar streaming do grafo para capturar eventos
            last_state = None

            for state_update in self.graph_runner.stream(
                objective=objective,
                collection_name=collection_name,
                user_id=str(user.id) if user else None,
                max_retries=max_retries,
                sections=sections_to_generate
            ):
                # O state_update contém {node_name: state_after_node}
                for node_name, node_state in state_update.items():
                    last_state = node_state

                    # Detectar geração de seção
                    if node_name.startswith('generate_'):
                        section_num = int(node_name.replace('generate_', ''))

                        # Ignorar seções não selecionadas (puladas)
                        if section_num not in sections_to_generate:
                            continue

                        section_key = get_section_key(section_num)
                        section_data = node_state.get(section_key, {})

                        yield {
                            'event': 'section_start',
                            'section': section_num,
                            'section_name': get_section_name(section_num),
                            'attempt': section_data.get('generation_attempts', 1),
                            'max_attempts': max_retries
                        }

                        # Se tem conteúdo, enviar
                        content = section_data.get('content', '')
                        if content:
                            yield {
                                'event': 'section_generated',
                                'section': section_num,
                                'section_name': get_section_name(section_num),
                                'content_preview': content[:200] + '...' if len(content) > 200 else content
                            }

                    # Detectar validação de seção
                    elif node_name.startswith('validate_'):
                        section_num = int(node_name.replace('validate_', ''))

                        # Ignorar seções não selecionadas (puladas)
                        if section_num not in sections_to_generate:
                            continue

                        section_key = get_section_key(section_num)
                        section_data = node_state.get(section_key, {})
                        validation = section_data.get('validation', {})

                        is_valid = validation.get('is_valid', False)
                        score = validation.get('score', 0.0)  # Score já vem 0-100 do validador

                        # Coletar feedback de reprovação
                        rejection_reasons = []
                        if not is_valid:
                            rejection_reasons = (
                                validation.get('errors', []) +
                                validation.get('structural_issues', []) +
                                validation.get('warnings', [])
                            )[:5]  # Limitar a 5 motivos

                        yield {
                            'event': 'section_validated',
                            'section': section_num,
                            'section_name': get_section_name(section_num),
                            'is_valid': is_valid,
                            'score': round(score, 1),
                            'status': 'approved' if is_valid else 'rejected',
                            'feedback': rejection_reasons,
                            'summary': validation.get('summary', '')
                        }

                        # Enviar conteúdo da seção (aprovada OU reprovada)
                        content = section_data.get('content', '')
                        if is_valid:
                            sections_completed += 1

                        # Sempre enviar conteúdo se existir
                        if content:
                            yield {
                                'event': 'section_content',
                                'section': section_num,
                                'section_name': get_section_name(section_num),
                                'content': content,
                                'is_valid': is_valid
                            }

                        # Atualizar progresso
                        # Calcular índice na lista de seções selecionadas
                        try:
                            section_index = sections_to_generate.index(section_num) + 1
                        except ValueError:
                            section_index = section_num
                        percentage = (section_index / total_sections) * 100
                        yield {
                            'event': 'progress',
                            'current_section': section_num,
                            'total_sections': total_sections,
                            'percentage': round(percentage, 1),
                            'sections_completed': sections_completed
                        }

                    # Detectar finalização
                    elif node_name == 'finalize':
                        yield {
                            'event': 'finalizing',
                            'message': 'Finalizando documento e gerando PDF...'
                        }

            # Persistir resultado
            if last_state:
                session.status = 'validating'
                session.save()

                yield {
                    'event': 'saving',
                    'message': 'Salvando documento e gerando PDF...'
                }

                document = self.persistence_service.save_etp_from_state(
                    session=session,
                    state=last_state,
                    generate_pdf=True
                )

                session.status = 'completed'
                session.save()

                stats = self._calculate_stats(last_state)
                generation_time = time.time() - start_time

                yield {
                    'event': 'completed',
                    'success': True,
                    'session_id': str(session.id),
                    'document_id': str(document.id),
                    'total_sections': total_sections,
                    'valid_sections': stats['valid_count'],
                    'average_score': round(stats['average_score'], 1),
                    'total_tokens_used': stats['total_tokens_used'],
                    'generation_time': round(generation_time, 1),
                    'pdf_url': document.pdf_url,
                    'sections_generated': sections_to_generate,
                    'message': f'ETP gerado com sucesso! {stats["valid_count"]}/{total_sections} seções válidas. Tokens: {stats["total_tokens_used"]:,}'
                }

        except Exception as e:
            logger.error(f"Erro no streaming de ETP: {str(e)}")

            if session:
                session.status = 'failed'
                session.error_message = str(e)
                session.save()

            yield {
                'event': 'error',
                'message': str(e),
                'session_id': str(session.id) if session else None,
                'details': 'Erro durante a geração do ETP'
            }
