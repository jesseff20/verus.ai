"""
KnowledgeBaseService - Gerenciador de Knowledge Base usando PgVector.

Implementa padrão Singleton para garantir uma única instância do serviço
compartilhada entre todos os agentes.

NOTA: Este serviço foi migrado de ChromaDB para PgVector.
Agora usa PostgreSQL + pgvector para armazenamento de embeddings.

ATUALIZAÇÃO: Agora também consulta a Base de Conhecimento permanente
(KnowledgeBase) além dos documentos da sessão, permitindo RAG híbrido.
"""
import logging
from typing import List, Dict, Optional
from django.db import transaction

from .pgvector_service import PgVectorService
from ..models import IntelligentSession, DocumentEmbedding, KnowledgeBase, AgentKnowledgeBaseLink

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """
    Serviço Singleton para gerenciar Knowledge Base usando PgVector.

    Cada sessão do assistente tem seus próprios embeddings no PostgreSQL,
    permitindo isolamento entre diferentes gerações de documentos.

    Este serviço atua como um wrapper do PgVectorService, mantendo
    compatibilidade com a interface anterior (que usava ChromaDB).
    """

    _instance = None
    _pgvector_service = None

    def __new__(cls):
        """Implementa padrão Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicializa o serviço PgVector."""
        if self._pgvector_service is None:
            try:
                self._pgvector_service = PgVectorService()
                logger.info("KnowledgeBaseService inicializado com PgVector")
            except Exception as e:
                logger.error(f"Erro ao inicializar KnowledgeBaseService: {str(e)}")
                raise

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
        session: Optional[IntelligentSession] = None,
        include_permanent_kb: bool = True,
        blueprint=None,
        agent_config=None,
        section_name: str = None,
        include_global_kb: bool = True,
        include_blueprint_kb: bool = True,
        include_agent_kb: bool = True,
        include_session_docs: bool = True,
    ) -> Dict:
        """
        Busca documentos similares usando PgVector - Arquitetura de 3 Camadas.

        Realiza busca híbrida combinando até 4 fontes:
        - Camada 0: Documentos da sessão do usuário (RAG privado)
        - Camada 1: KB Global - kb.DocumentChunk (normas gerais)
        - Camada 2: KB do Blueprint - KnowledgeBaseEmbedding (normas específicas do tipo de doc)
        - Camada 3: KB do Agente - KnowledgeBaseEmbedding (melhores resultados gerados)

        Args:
            collection_name: ID da sessão (usado para compatibilidade)
            query_text: Texto da query
            n_results: Número máximo de resultados
            where: Filtros (mantido para compatibilidade)
            session: Sessão do assistente (opcional)
            include_permanent_kb: Se True, busca nas KBs permanentes (retrocompatibilidade)
            blueprint: DocumentBlueprint para filtrar Camada 2
            agent_config: SectionAgentConfig para filtrar Camada 3
            include_global_kb: Se True, busca na KB Global (kb.DocumentChunk)
            include_blueprint_kb: Se True, busca nas KBs do blueprint
            include_agent_kb: Se True, busca nas KBs do agente + melhorias
            include_session_docs: Se True, busca nos docs da sessão

        Returns:
            Dict com documents, metadatas, distances, ids
        """
        try:
            all_results = []

            # Resolver sessão a partir do collection_name se necessário
            if session is None:
                try:
                    if collection_name and collection_name != 'default':
                        session = IntelligentSession.objects.get(id=collection_name)
                except (IntelligentSession.DoesNotExist, ValueError):
                    logger.debug(f"Sessão não encontrada para collection: {collection_name}")

            # ── Camada 0: Documentos da sessão do usuário ──
            if include_session_docs and session:
                try:
                    session_results = self._pgvector_service.search_session_documents(
                        session=session,
                        query=query_text,
                        n_results=n_results,
                        min_similarity=0.5
                    )
                    for r in session_results:
                        r['source_type'] = 'session'
                        r['layer'] = 0
                    all_results.extend(session_results)
                    logger.debug(f"[Camada 0] Sessão retornou {len(session_results)} docs")
                except Exception as e:
                    logger.warning(f"[Camada 0] Erro ao buscar na sessão: {e}")

            # ── Camada 1: KB Global (kb.DocumentChunk) ──
            if include_global_kb:
                try:
                    global_results = self._pgvector_service.search_global_kb(
                        query=query_text,
                        n_results=n_results,
                        min_similarity=0.5
                    )
                    for r in global_results:
                        r['layer'] = 1
                    all_results.extend(global_results)
                    logger.debug(f"[Camada 1] KB Global retornou {len(global_results)} docs")
                except Exception as e:
                    logger.warning(f"[Camada 1] Erro ao buscar na KB Global: {e}")

            # ── Camada 2: KB do Blueprint ──
            if include_blueprint_kb and blueprint:
                try:
                    blueprint_kbs = KnowledgeBase.objects.filter(
                        blueprint=blueprint,
                        kb_layer='blueprint',
                        is_active=True
                    )
                    for kb in blueprint_kbs:
                        kb_results = self._pgvector_service.search_knowledge_base(
                            knowledge_base_name=kb.name,
                            query=query_text,
                            n_results=n_results,
                            min_similarity=0.5
                        )
                        for r in kb_results:
                            r['source_type'] = 'blueprint_kb'
                            r['layer'] = 2
                        all_results.extend(kb_results)
                    bp_count = sum(1 for r in all_results if r.get('layer') == 2)
                    logger.debug(f"[Camada 2] KB Blueprint retornou {bp_count} docs")
                except Exception as e:
                    logger.warning(f"[Camada 2] Erro ao buscar na KB Blueprint: {e}")

            # ── Camada 3: KB do Agente (configuradas + melhorias) ──
            if include_agent_kb and agent_config:
                try:
                    # 3a. KBs configuradas no M2M do agente
                    for kb in agent_config.knowledge_bases.filter(is_active=True):
                        kb_results = self._pgvector_service.search_knowledge_base(
                            knowledge_base_name=kb.name,
                            query=query_text,
                            n_results=3,
                            min_similarity=0.6
                        )
                        for r in kb_results:
                            r['source_type'] = 'agent_kb'
                            r['layer'] = 3
                        all_results.extend(kb_results)

                    # 3b. KB de melhorias automática
                    improvement_section = section_name or agent_config.name
                    improvement_results = self._pgvector_service.search_section_improvements(
                        section_name=improvement_section,
                        query=query_text,
                        n_results=3,
                        min_similarity=0.6
                    )
                    for r in improvement_results:
                        r['source_type'] = 'improvements'
                        r['layer'] = 3
                    all_results.extend(improvement_results)

                    agent_count = sum(1 for r in all_results if r.get('layer') == 3)
                    logger.debug(f"[Camada 3] KB Agente retornou {agent_count} docs")
                except Exception as e:
                    logger.warning(f"[Camada 3] Erro ao buscar na KB Agente: {e}")

            # ── Fallback: busca legada em todas as KBs (retrocompatibilidade) ──
            if include_permanent_kb and not blueprint and not agent_config:
                try:
                    kb_results = self._pgvector_service.search_knowledge_base(
                        knowledge_base_name='all',
                        query=query_text,
                        n_results=n_results,
                        min_similarity=0.5
                    )
                    for r in kb_results:
                        r['source_type'] = 'knowledge_base'
                        r['layer'] = 2
                    all_results.extend(kb_results)
                    logger.debug(f"[Fallback] KB permanente retornou {len(kb_results)} docs")
                except Exception as kb_error:
                    logger.warning(f"[Fallback] Erro ao buscar na KB permanente: {kb_error}")

            # ── Ordenar por similaridade e limitar ──
            if all_results:
                all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                all_results = all_results[:n_results]

            if not all_results:
                logger.info(f"Nenhum documento encontrado para query: '{query_text[:50]}...'")
                return self._empty_result()

            # ── Formatar resposta ──
            documents = [r['chunk_text'] for r in all_results]
            metadatas = []
            ids = []

            for r in all_results:
                meta = r.get('metadata', {}).copy() if r.get('metadata') else {}
                meta['source_type'] = r.get('source_type', 'unknown')
                meta['layer'] = r.get('layer', -1)

                source_type = r.get('source_type', 'unknown')
                if source_type in ('knowledge_base', 'blueprint_kb', 'agent_kb', 'improvements'):
                    meta['knowledge_base'] = r.get('knowledge_base', '')
                    meta['source_name'] = r.get('source_name', '')
                    ids.append(f"kb_{r.get('knowledge_base', 'unknown')}_{r.get('chunk_index', 0)}")
                elif source_type == 'global_kb':
                    meta['document_id'] = r.get('document_id', '')
                    meta['source_name'] = r.get('source_name', '')
                    ids.append(f"global_{r.get('document_id', 'doc')}_{r.get('chunk_index', 0)}")
                else:
                    ids.append(f"{r.get('document_name', 'doc')}_{r.get('chunk_index', 0)}")

                metadatas.append(meta)

            similarities = [r.get('similarity', 0) for r in all_results]

            # Log detalhado por camada
            layer_counts = {}
            for r in all_results:
                layer = r.get('layer', -1)
                layer_counts[layer] = layer_counts.get(layer, 0) + 1
            logger.info(
                f"Query retornou {len(documents)} docs — "
                f"Sessão: {layer_counts.get(0, 0)}, "
                f"Global: {layer_counts.get(1, 0)}, "
                f"Blueprint: {layer_counts.get(2, 0)}, "
                f"Agente: {layer_counts.get(3, 0)}"
            )

            return {
                'documents': documents,
                'metadatas': metadatas,
                'distances': similarities,
                'ids': ids
            }

        except Exception as e:
            logger.error(f"Erro ao realizar query: {str(e)}")
            return self._empty_result()

    def query_by_links(
        self,
        agent_config,
        query_text: str,
        session: Optional[IntelligentSession] = None,
        blueprint=None,
        section_name: str = None,
        include_session_docs: bool = True,
        include_global_kb: bool = True,
    ) -> Dict[str, Dict]:
        """
        Consulta KBs na ordem definida pelos AgentKnowledgeBaseLinks.

        Retorna resultados separados por propósito (purpose), cada um com:
        - instruction: como o agente deve usar esses resultados
        - documents: lista de textos recuperados
        - include_summary: se deve incluir summary interpretativo

        Se o agente não tiver links configurados, faz fallback para query() legado.

        Args:
            agent_config: SectionAgentConfig do agente
            query_text: Texto da query para busca vetorial
            session: Sessão (para Camada 0 - docs do usuário)
            blueprint: Blueprint (para fallback Camada 2)
            section_name: Nome da seção (para fallback melhorias)
            include_session_docs: Se True, inclui docs da sessão como 'context'
            include_global_kb: Se True, inclui KB global como fallback normativo

        Returns:
            Dict[purpose] = {
                'instruction': str,
                'documents': List[str],
                'metadata': List[Dict],
                'include_summary': bool,
            }
        """
        try:
            links = AgentKnowledgeBaseLink.objects.filter(
                agent=agent_config,
                is_active=True
            ).select_related('knowledge_base').order_by('priority')

            results_by_purpose: Dict[str, Dict] = {}

            for link in links:
                kb = link.knowledge_base
                purpose = link.purpose

                try:
                    kb_results = self._pgvector_service.search_knowledge_base(
                        knowledge_base_name=kb.name,
                        query=query_text,
                        n_results=link.top_k,
                        min_similarity=link.min_similarity,
                    )

                    # Filtrar por fontes selecionadas (se configurado)
                    if link.selected_sources:
                        kb_results = [
                            r for r in kb_results
                            if r.get('source_name', '') in link.selected_sources
                        ]

                    # Construir documentos com ou sem summary
                    docs = []
                    metas = []
                    for r in kb_results:
                        text = r['chunk_text']
                        if link.include_summary and r.get('summary'):
                            text = f"[Resumo: {r['summary']}]\n\n{text}"
                        docs.append(text)
                        metas.append({
                            'source_name': r.get('source_name', ''),
                            'knowledge_base': r.get('knowledge_base', kb.name),
                            'similarity': r.get('similarity', 0),
                            'purpose': purpose,
                            'kb_layer': kb.kb_layer,
                        })

                    # Acumular ou criar entrada por purpose
                    if purpose in results_by_purpose:
                        results_by_purpose[purpose]['documents'].extend(docs)
                        results_by_purpose[purpose]['metadata'].extend(metas)
                    else:
                        results_by_purpose[purpose] = {
                            'instruction': link.instruction,
                            'documents': docs,
                            'metadata': metas,
                            'include_summary': link.include_summary,
                        }

                    logger.debug(
                        f"  Link P{link.priority} [{purpose}] KB '{kb.name}' → {len(docs)} docs"
                    )

                except Exception as e:
                    logger.warning(f"  Erro no link P{link.priority} KB '{kb.name}': {e}")

            # ── Auto-inclusão de camadas não cobertas por links explícitos ──
            covered_layers = set()
            for link in links:
                covered_layers.add(link.knowledge_base.kb_layer)

            n_results_default = agent_config.rag_top_k or 5

            # Camada 1: KB Global — se nenhum link cobre kb_layer='global'
            if include_global_kb and 'global' not in covered_layers:
                try:
                    global_results = self._pgvector_service.search_global_kb(
                        query=query_text,
                        n_results=n_results_default,
                        min_similarity=0.5,
                    )
                    if global_results:
                        if 'normative' in results_by_purpose:
                            for r in global_results:
                                results_by_purpose['normative']['documents'].append(r['chunk_text'])
                                results_by_purpose['normative']['metadata'].append({
                                    'source_name': r.get('source_name', ''),
                                    'kb_layer': 'global',
                                    'knowledge_base': 'KB Global',
                                    'similarity': r.get('similarity', 0),
                                })
                        else:
                            results_by_purpose['normative'] = {
                                'instruction': 'Normas e legislação aplicáveis.',
                                'documents': [r['chunk_text'] for r in global_results],
                                'metadata': [{
                                    'source_name': r.get('source_name', ''),
                                    'kb_layer': 'global',
                                    'knowledge_base': 'KB Global',
                                    'similarity': r.get('similarity', 0),
                                } for r in global_results],
                                'include_summary': False,
                            }
                    logger.debug(f"  [Auto-Camada 1] KB Global → {len(global_results)} docs")
                except Exception as e:
                    logger.warning(f"  [Auto-Camada 1] Erro KB Global: {e}")

            # Camada 2: KBs do Blueprint — se nenhum link cobre kb_layer='blueprint'
            if blueprint and 'blueprint' not in covered_layers:
                try:
                    blueprint_kbs = KnowledgeBase.objects.filter(
                        blueprint=blueprint,
                        kb_layer='blueprint',
                        is_active=True,
                    )
                    for kb in blueprint_kbs:
                        kb_results = self._pgvector_service.search_knowledge_base(
                            knowledge_base_name=kb.name,
                            query=query_text,
                            n_results=n_results_default,
                            min_similarity=0.5,
                        )
                        if kb_results:
                            if 'reference' in results_by_purpose:
                                for r in kb_results:
                                    results_by_purpose['reference']['documents'].append(r['chunk_text'])
                                    results_by_purpose['reference']['metadata'].append({
                                        'source_name': r.get('source_name', ''),
                                        'kb_layer': 'blueprint',
                                        'knowledge_base': kb.name,
                                        'similarity': r.get('similarity', 0),
                                    })
                            else:
                                results_by_purpose['reference'] = {
                                    'instruction': f'Referência normativa: {kb.name}',
                                    'documents': [r['chunk_text'] for r in kb_results],
                                    'metadata': [{
                                        'source_name': r.get('source_name', ''),
                                        'kb_layer': 'blueprint',
                                        'knowledge_base': kb.name,
                                        'similarity': r.get('similarity', 0),
                                    } for r in kb_results],
                                    'include_summary': False,
                                }
                    bp_count = sum(1 for v in results_by_purpose.values() if any(
                        m.get('kb_layer') == 'blueprint' for m in v.get('metadata', [])
                    ))
                    logger.debug(f"  [Auto-Camada 2] KBs Blueprint → {bp_count} purposes com docs")
                except Exception as e:
                    logger.warning(f"  [Auto-Camada 2] Erro KBs Blueprint: {e}")

            # Camada 3: Melhorias automáticas — se nenhum link com purpose='evaluation'
            if 'evaluation' not in results_by_purpose and agent_config:
                try:
                    section_name_for_improvements = section_name or agent_config.name
                    improvement_results = self._pgvector_service.search_section_improvements(
                        section_name=section_name_for_improvements,
                        query=query_text,
                        n_results=3,
                        min_similarity=0.6,
                    )
                    if improvement_results:
                        results_by_purpose['evaluation'] = {
                            'instruction': 'Melhores resultados anteriores para referência.',
                            'documents': [r['chunk_text'] for r in improvement_results],
                            'metadata': [{'source_type': 'improvements', 'kb_layer': 'agent'} for _ in improvement_results],
                            'include_summary': False,
                        }
                    logger.debug(f"  [Auto-Camada 3] Melhorias → {len(improvement_results)} docs")
                except Exception as e:
                    logger.warning(f"  [Auto-Camada 3] Erro melhorias: {e}")

            # Adicionar docs da sessão como 'context' se não existe purpose 'context'
            if include_session_docs and session and 'context' not in results_by_purpose:
                try:
                    session_results = self._pgvector_service.search_session_documents(
                        session=session,
                        query=query_text,
                        n_results=agent_config.rag_top_k or 5,
                        min_similarity=0.5,
                    )
                    if session_results:
                        results_by_purpose['context'] = {
                            'instruction': 'Documentos fornecidos pelo usuário como referência.',
                            'documents': [r['chunk_text'] for r in session_results],
                            'metadata': [{'source_type': 'session', 'layer': 0} for _ in session_results],
                            'include_summary': False,
                        }
                except Exception as e:
                    logger.warning(f"  Erro ao buscar docs da sessão: {e}")

            # Log resumo
            total = sum(len(v['documents']) for v in results_by_purpose.values())
            purposes_summary = ', '.join(
                f"{k}: {len(v['documents'])}" for k, v in results_by_purpose.items()
            )
            logger.info(
                f"query_by_links '{agent_config.name}' → {total} docs total ({purposes_summary})"
            )

            return results_by_purpose

        except Exception as e:
            logger.error(f"Erro em query_by_links: {e}")
            return {}

    def query_with_session(
        self,
        session: IntelligentSession,
        query_text: str,
        n_results: int = 5
    ) -> Dict:
        """
        Busca documentos similares em uma sessão específica.

        Método mais direto que recebe a sessão diretamente.

        Args:
            session: Sessão do assistente
            query_text: Texto da query
            n_results: Número máximo de resultados

        Returns:
            Dict com documentos encontrados
        """
        return self.query(
            collection_name=str(session.id),
            query_text=query_text,
            n_results=n_results,
            session=session
        )

    def _empty_result(self) -> Dict:
        """Retorna resultado vazio no formato esperado."""
        return {
            'documents': [],
            'metadatas': [],
            'distances': [],
            'ids': []
        }

    def create_collection(self, session_id: str) -> str:
        """
        Cria uma "collection" para uma sessão.

        Com PgVector, não precisamos criar collections explicitamente.
        Os embeddings são associados à sessão via foreign key.

        Mantido para compatibilidade com código existente.

        Args:
            session_id: ID da sessão (UUID)

        Returns:
            Nome da collection (session_id)
        """
        logger.info(f"Collection (sessão) registrada: {session_id}")
        return session_id

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> int:
        """
        Adiciona documentos à sessão.

        NOTA: Este método é mantido para compatibilidade, mas o fluxo
        principal de upload usa PgVectorService.process_document() diretamente.

        Args:
            collection_name: ID da sessão
            documents: Lista de textos a adicionar
            metadatas: Metadados para cada documento
            ids: IDs customizados

        Returns:
            Número de documentos adicionados
        """
        logger.warning(
            "add_documents() chamado - use PgVectorService.process_document() "
            "para o fluxo principal de upload"
        )
        return len(documents) if documents else 0

    def get_collection_info(self, collection_name: str) -> Dict:
        """
        Obtém informações sobre os embeddings de uma sessão.

        Args:
            collection_name: ID da sessão

        Returns:
            Dict com informações da sessão
        """
        try:
            session = IntelligentSession.objects.get(id=collection_name)
            stats = self._pgvector_service.get_session_stats(session)

            return {
                'name': collection_name,
                'count': stats.get('total_chunks', 0),
                'metadata': {
                    'session_id': str(session.id),
                    'documents_processed': stats.get('documents_processed', 0),
                    'total_characters': stats.get('total_characters', 0)
                }
            }
        except IntelligentSession.DoesNotExist:
            return {
                'name': collection_name,
                'count': 0,
                'metadata': {'error': 'Sessão não encontrada'}
            }
        except Exception as e:
            logger.error(f"Erro ao obter info da sessão: {str(e)}")
            return {
                'name': collection_name,
                'count': 0,
                'metadata': {'error': str(e)}
            }

    def delete_collection(self, collection_name: str) -> bool:
        """
        Deleta embeddings de uma sessão.

        Args:
            collection_name: ID da sessão

        Returns:
            True se deletada com sucesso
        """
        try:
            session = IntelligentSession.objects.get(id=collection_name)
            count = self._pgvector_service.delete_session_embeddings(session)
            logger.info(f"Deletados {count} embeddings da sessão {collection_name}")
            return True
        except IntelligentSession.DoesNotExist:
            logger.warning(f"Sessão não encontrada: {collection_name}")
            return False
        except Exception as e:
            logger.error(f"Erro ao deletar embeddings: {str(e)}")
            return False

    def list_collections(self) -> List[str]:
        """
        Lista todas as sessões que têm embeddings.

        Returns:
            Lista de IDs de sessões
        """
        try:
            session_ids = (
                DocumentEmbedding.objects
                .values_list('session_id', flat=True)
                .distinct()
            )
            return [str(sid) for sid in session_ids]
        except Exception as e:
            logger.error(f"Erro ao listar sessões: {str(e)}")
            return []

    def reset(self):
        """
        Remove todos os embeddings de documentos.

        CUIDADO: Usar apenas em testes!
        """
        try:
            count, _ = DocumentEmbedding.objects.all().delete()
            logger.warning(f"RESET: {count} embeddings de documentos deletados!")
        except Exception as e:
            logger.error(f"Erro ao resetar embeddings: {str(e)}")
            raise

    @classmethod
    def get_instance(cls) -> 'KnowledgeBaseService':
        """
        Obtém a instância Singleton do serviço.

        Returns:
            Instância do KnowledgeBaseService
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
