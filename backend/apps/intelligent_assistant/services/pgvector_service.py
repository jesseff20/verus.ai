"""
PgVectorService - Serviço para gerenciamento de embeddings com pgvector.

Este serviço usa PostgreSQL + pgvector para:
- Armazenar embeddings no PostgreSQL
- Buscar documentos similares por similaridade de cosseno

Geração de embeddings é delegada ao EmbeddingService (IBM watsonx E5-Large).
"""
import logging
import uuid as uuid_module
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.db import transaction


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza metadata para garantir que seja JSON serializável.
    Converte UUIDs para strings.
    """
    if not metadata:
        return {}

    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, uuid_module.UUID):
            sanitized[key] = str(value)
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_metadata(value)
        elif isinstance(value, list):
            sanitized[key] = [
                str(v) if isinstance(v, uuid_module.UUID) else v
                for v in value
            ]
        else:
            sanitized[key] = value
    return sanitized

from ..models import (
    DocumentEmbedding,
    KnowledgeBaseEmbedding,
    KnowledgeBase,
    UploadedDocument,
    IntelligentSession
)

logger = logging.getLogger(__name__)


class PgVectorService:
    """
    Serviço para gerenciamento de embeddings usando pgvector.

    Responsável por:
    - Delegar geração de embeddings ao EmbeddingService (watsonx E5-Large)
    - Armazenar chunks e embeddings no PostgreSQL
    - Buscar documentos similares por similaridade de cosseno
    """

    # Configurações de chunking
    DEFAULT_CHUNK_SIZE = 1000  # caracteres
    DEFAULT_CHUNK_OVERLAP = 200  # caracteres

    # Importar constantes centralizadas
    from apps.agents.constants import (
        EMBEDDING_MODEL_ID as DEFAULT_EMBEDDING_MODEL,
        EMBEDDING_DIMENSIONS,
        EMBEDDING_BATCH_SIZE,
    )

    def __init__(self):
        """Inicializa o serviço."""
        logger.info("PgVectorService inicializado")

    # ========== EMBEDDING GENERATION ==========

    def generate_embedding(self, text: str, **kwargs) -> List[float]:
        """
        Gera embedding para BUSCA (prefixo "query: ").
        Delega para EmbeddingService.

        Args:
            text: Texto da busca

        Returns:
            Lista de floats (1024 dimensões)
        """
        from apps.agents.services import EmbeddingService
        return EmbeddingService.generate(text)

    def generate_embedding_for_indexing(self, text: str) -> List[float]:
        """
        Gera embedding para INDEXAÇÃO (prefixo "passage: ").
        Delega para EmbeddingService.

        Args:
            text: Texto para indexar

        Returns:
            Lista de floats (1024 dimensões)
        """
        from apps.agents.services import EmbeddingService
        return EmbeddingService.generate_for_indexing(text)

    def generate_embeddings_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Gera embeddings em lote para INDEXAÇÃO (prefixo "passage: ").
        Delega para EmbeddingService.

        Args:
            texts: Lista de textos para indexar

        Returns:
            Lista de embeddings (1024 dimensões cada)
        """
        from apps.agents.services import EmbeddingService
        return EmbeddingService.generate_batch(texts)

    # ========== TEXT CHUNKING ==========

    def chunk_text(
        self,
        text: str,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Divide texto em chunks com overlap.

        Args:
            text: Texto completo para dividir
            chunk_size: Tamanho máximo de cada chunk em caracteres
            chunk_overlap: Sobreposição entre chunks

        Returns:
            Lista de dicts com {index, text, size}
        """
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP

        # Limpar texto
        text = text.strip()
        if not text:
            return []

        chunks = []
        start = 0
        index = 0

        while start < len(text):
            # Calcular fim do chunk
            end = start + chunk_size

            # Se não é o último chunk, tentar quebrar em espaço/parágrafo
            if end < len(text):
                # Procurar último espaço ou quebra de linha
                last_space = text.rfind(' ', start, end)
                last_newline = text.rfind('\n', start, end)
                break_point = max(last_space, last_newline)

                if break_point > start:
                    end = break_point

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    'index': index,
                    'text': chunk_text,
                    'size': len(chunk_text)
                })
                index += 1

            # Próximo início com overlap
            start = end - chunk_overlap if end < len(text) else len(text)

        logger.info(f"Texto dividido em {len(chunks)} chunks")
        return chunks

    # ========== DOCUMENT EMBEDDINGS (SESSION-BASED) ==========

    @transaction.atomic
    def process_document(
        self,
        document: UploadedDocument,
        session: IntelligentSession,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> int:
        """
        Processa um documento: extrai texto, cria chunks e gera embeddings.

        Args:
            document: UploadedDocument com texto já extraído
            session: IntelligentSession associada
            chunk_size: Tamanho dos chunks
            chunk_overlap: Overlap entre chunks

        Returns:
            Número de embeddings criados
        """
        if not document.extracted_text:
            logger.warning(f"Documento {document.id} sem texto extraído")
            return 0

        # 1. Dividir em chunks
        chunks = self.chunk_text(
            document.extracted_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        if not chunks:
            logger.warning(f"Nenhum chunk gerado para documento {document.id}")
            return 0

        # 2. Gerar embeddings em batch
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings_batch(texts)

        # 3. Salvar no banco
        embedding_objects = []
        for chunk, embedding in zip(chunks, embeddings):
            embedding_objects.append(
                DocumentEmbedding(
                    document=document,
                    session=session,
                    chunk_index=chunk['index'],
                    chunk_text=chunk['text'],
                    chunk_size=chunk['size'],
                    embedding=embedding,
                    embedding_model=self.DEFAULT_EMBEDDING_MODEL,
                    metadata=_sanitize_metadata({
                        'filename': document.filename,
                        'file_type': document.file_type
                    })
                )
            )

        DocumentEmbedding.objects.bulk_create(embedding_objects)
        logger.info(f"Criados {len(embedding_objects)} embeddings para documento {document.filename}")

        return len(embedding_objects)

    def search_session_documents(
        self,
        session: IntelligentSession,
        query: str,
        n_results: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos similares na sessão usando similaridade de cosseno.

        Args:
            session: Sessão para buscar
            query: Texto da query
            n_results: Número máximo de resultados
            min_similarity: Similaridade mínima (0-1)

        Returns:
            Lista de dicts com {chunk_text, similarity, document_name, metadata}
        """
        # Gerar embedding da query
        query_embedding = self.generate_embedding(query)

        # Buscar usando pgvector (cosine similarity)
        # O operador <=> retorna distância, então 1 - distância = similaridade
        from django.db.models import F
        from pgvector.django import CosineDistance

        results = (
            DocumentEmbedding.objects
            .filter(session=session)
            .annotate(distance=CosineDistance('embedding', query_embedding))
            .filter(distance__lte=(1 - min_similarity))  # distance <= 1 - min_similarity
            .order_by('distance')[:n_results]
        )

        return [
            {
                'chunk_text': r.chunk_text,
                'similarity': 1 - r.distance,  # Converter distância para similaridade
                'document_name': r.document.filename,
                'chunk_index': r.chunk_index,
                'metadata': r.metadata
            }
            for r in results
        ]

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca genérica que aceita collection_name (session_id) como string.

        Método wrapper para compatibilidade com DynamicGraphBuilder.

        Args:
            collection_name: ID da sessão (string UUID) ou 'default'
            query: Texto da query
            n_results: Número máximo de resultados
            min_similarity: Similaridade mínima (0-1)

        Returns:
            Lista de dicts com {chunk_text, similarity, document_name, metadata}
        """
        import uuid

        # Se collection_name é 'default' ou vazio, retorna lista vazia
        if not collection_name or collection_name == 'default':
            logger.warning("search() chamado com collection_name='default', retornando vazio")
            return []

        # Tentar buscar sessão pelo ID
        try:
            session_uuid = uuid.UUID(collection_name)
            session = IntelligentSession.objects.get(id=session_uuid)
            return self.search_session_documents(
                session=session,
                query=query,
                n_results=n_results,
                min_similarity=min_similarity
            )
        except (ValueError, IntelligentSession.DoesNotExist) as e:
            logger.warning(f"Sessão não encontrada para collection_name={collection_name}: {e}")
            return []

    def delete_session_embeddings(self, session: IntelligentSession) -> int:
        """
        Remove todos os embeddings de uma sessão.

        Args:
            session: Sessão cujos embeddings serão removidos

        Returns:
            Número de embeddings removidos
        """
        count, _ = DocumentEmbedding.objects.filter(session=session).delete()
        logger.info(f"Removidos {count} embeddings da sessão {session.id}")
        return count

    # ========== KNOWLEDGE BASE EMBEDDINGS (PERMANENT) ==========

    @transaction.atomic
    def add_to_knowledge_base(
        self,
        knowledge_base: KnowledgeBase,
        source_name: str,
        source_type: str,
        text: str,
        metadata: Dict[str, Any] = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        source_file=None,
    ) -> int:
        """
        Adiciona conteúdo à base de conhecimento permanente.

        Args:
            knowledge_base: Base de conhecimento
            source_name: Nome da fonte (ex: "Lei_14133_2021.pdf")
            source_type: Tipo da fonte (pdf, docx, txt, url, manual)
            text: Texto completo
            metadata: Metadados adicionais
            chunk_size: Tamanho dos chunks
            chunk_overlap: Overlap
            source_file: KBSourceFile associado (opcional, para rastreabilidade)

        Returns:
            Número de embeddings criados
        """
        # 1. Dividir em chunks
        chunks = self.chunk_text(text, chunk_size, chunk_overlap)

        if not chunks:
            return 0

        # 2. Gerar embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings_batch(texts)

        # 3. Salvar
        embedding_objects = []
        for chunk, embedding in zip(chunks, embeddings):
            obj_metadata = metadata.copy() if metadata else {}
            obj_metadata['source_name'] = source_name

            embedding_objects.append(
                KnowledgeBaseEmbedding(
                    knowledge_base=knowledge_base,
                    source_file=source_file,
                    source_name=source_name,
                    source_type=source_type,
                    chunk_index=chunk['index'],
                    chunk_text=chunk['text'],
                    chunk_size=chunk['size'],
                    embedding=embedding,
                    embedding_model=self.DEFAULT_EMBEDDING_MODEL,
                    metadata=_sanitize_metadata(obj_metadata)
                )
            )

        KnowledgeBaseEmbedding.objects.bulk_create(embedding_objects)
        logger.info(f"Adicionados {len(embedding_objects)} embeddings à KB '{knowledge_base.name}'")

        return len(embedding_objects)

    def search_knowledge_base(
        self,
        knowledge_base_name: str,
        query: str,
        n_results: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca na base de conhecimento permanente.

        Args:
            knowledge_base_name: Nome da KB ou 'all' para todas
            query: Texto da query
            n_results: Número máximo de resultados
            min_similarity: Similaridade mínima

        Returns:
            Lista de resultados com similaridade
        """
        query_embedding = self.generate_embedding(query)

        from pgvector.django import CosineDistance

        queryset = KnowledgeBaseEmbedding.objects.all()

        if knowledge_base_name != 'all':
            queryset = queryset.filter(knowledge_base__name=knowledge_base_name)

        results = (
            queryset
            .filter(knowledge_base__is_active=True)
            .annotate(distance=CosineDistance('embedding', query_embedding))
            .filter(distance__lte=(1 - min_similarity))
            .order_by('distance')[:n_results]
        )

        return [
            {
                'chunk_text': r.chunk_text,
                'similarity': 1 - r.distance,
                'source_name': r.source_name,
                'knowledge_base': r.knowledge_base.name,
                'chunk_index': r.chunk_index,
                'metadata': r.metadata,
                'summary': getattr(r, 'summary', '') or '',
            }
            for r in results
        ]

    def search_global_kb(
        self,
        query: str,
        n_results: int = 5,
        min_similarity: float = 0.5,
        category: str = None,
        tags: list = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca na KB Global (KnowledgeBaseEmbedding com kb_layer='global').
        Camada 1 da hierarquia de 3 camadas.

        Args:
            query: Texto da query
            n_results: Número máximo de resultados
            min_similarity: Similaridade mínima (0-1)
            category: Filtrar por categoria (via metadata)
            tags: Filtrar por tags (via metadata)

        Returns:
            Lista de dicts compatível com as outras buscas
        """
        from pgvector.django import CosineDistance

        query_embedding = self.generate_embedding(query)

        queryset = KnowledgeBaseEmbedding.objects.filter(
            knowledge_base__kb_layer='global',
            knowledge_base__is_active=True,
            embedding__isnull=False,
        )

        if category:
            queryset = queryset.filter(metadata__category=category)

        if tags:
            from django.db.models import Q
            tag_query = Q()
            for tag in tags:
                tag_query |= Q(metadata__tags__contains=[tag])
            queryset = queryset.filter(tag_query)

        results = (
            queryset
            .annotate(distance=CosineDistance('embedding', query_embedding))
            .filter(distance__lte=(1 - min_similarity))
            .order_by('distance')[:n_results]
        )

        return [
            {
                'chunk_text': r.chunk_text,
                'similarity': 1 - r.distance,
                'source_name': r.source_name,
                'source_type': 'global_kb',
                'document_id': str(r.knowledge_base_id),
                'document_category': r.metadata.get('category', ''),
                'chunk_index': r.chunk_index,
                'metadata': r.metadata,
            }
            for r in results
        ]

    def search_combined(
        self,
        session: Optional[IntelligentSession],
        knowledge_base_names: List[str],
        query: str,
        n_results: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca combinada: documentos da sessão + bases de conhecimento.

        Args:
            session: Sessão (opcional)
            knowledge_base_names: Lista de KBs para buscar
            query: Texto da query
            n_results: Número máximo de resultados
            min_similarity: Similaridade mínima

        Returns:
            Lista combinada de resultados ordenada por similaridade
        """
        results = []

        # Buscar na sessão
        if session:
            session_results = self.search_session_documents(
                session, query, n_results, min_similarity
            )
            for r in session_results:
                r['source_type'] = 'session'
            results.extend(session_results)

        # Buscar nas KBs
        for kb_name in knowledge_base_names:
            kb_results = self.search_knowledge_base(
                kb_name, query, n_results, min_similarity
            )
            for r in kb_results:
                r['source_type'] = 'knowledge_base'
            results.extend(kb_results)

        # Ordenar por similaridade e limitar
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:n_results]

    # ========== UTILITIES ==========

    def get_session_stats(self, session: IntelligentSession) -> Dict[str, Any]:
        """Retorna estatísticas de embeddings de uma sessão."""
        from django.db.models import Count, Sum

        stats = (
            DocumentEmbedding.objects
            .filter(session=session)
            .aggregate(
                total_chunks=Count('id'),
                total_chars=Sum('chunk_size')
            )
        )

        docs_count = (
            DocumentEmbedding.objects
            .filter(session=session)
            .values('document')
            .distinct()
            .count()
        )

        return {
            'documents_processed': docs_count,
            'total_chunks': stats['total_chunks'] or 0,
            'total_characters': stats['total_chars'] or 0
        }

    def get_knowledge_base_stats(self, knowledge_base: KnowledgeBase) -> Dict[str, Any]:
        """Retorna estatísticas de uma base de conhecimento."""
        from django.db.models import Count, Sum

        stats = (
            KnowledgeBaseEmbedding.objects
            .filter(knowledge_base=knowledge_base)
            .aggregate(
                total_chunks=Count('id'),
                total_chars=Sum('chunk_size')
            )
        )

        sources_count = (
            KnowledgeBaseEmbedding.objects
            .filter(knowledge_base=knowledge_base)
            .values('source_name')
            .distinct()
            .count()
        )

        return {
            'sources_count': sources_count,
            'total_chunks': stats['total_chunks'] or 0,
            'total_characters': stats['total_chars'] or 0
        }

    # ========== SECTION IMPROVEMENTS (AUTO-LEARNING) ==========

    def add_section_improvement(
        self,
        section_name: str,
        improvement_text: str,
        original_text: str = None,
        metadata: Dict[str, Any] = None,
        agent_config=None,
    ) -> int:
        """
        Adiciona melhoria de seção à KB de auto-aprendizagem.

        Args:
            section_name: Nome da seção (ex: "Justificativa da Contratação")
            improvement_text: Texto melhorado pelo usuário
            original_text: Texto original (opcional, para referência)
            metadata: Metadados adicionais (user_id, ai_score, user_rating, etc.)

        Returns:
            Número de embeddings criados (1 se sucesso)
        """
        from datetime import datetime

        # Normalizar nome da seção para uso como nome da KB
        kb_name = f"section_improvements_{section_name.lower().replace(' ', '_')}"

        # Buscar ou criar KB de melhorias da seção (Camada 3 - Agente)
        kb, created = KnowledgeBase.objects.get_or_create(
            name=kb_name,
            defaults={
                'description': f'Melhorias de usuários para seção: {section_name}',
                'is_active': True,
                'kb_layer': 'agent',
                'agent_config': agent_config,
            }
        )

        if agent_config:
            if created:
                agent_config.knowledge_bases.add(kb)
                logger.info(f"KB '{kb_name}' criada e vinculada ao agente '{agent_config.name}'")
            elif not kb.agent_config:
                kb.agent_config = agent_config
                kb.save(update_fields=['agent_config'])
                agent_config.knowledge_bases.add(kb)
                logger.info(f"KB '{kb_name}' retrovinculada ao agente '{agent_config.name}'")
        elif created:
            logger.info(f"KB de melhorias criada: {kb_name}")

        # Gerar embedding do texto melhorado (indexação, não busca)
        embedding = self.generate_embedding_for_indexing(improvement_text)

        # Preparar metadados
        obj_metadata = metadata.copy() if metadata else {}
        obj_metadata['section_name'] = section_name
        obj_metadata['timestamp'] = datetime.now().isoformat()
        if original_text:
            obj_metadata['original_text_preview'] = original_text[:200]

        # Diferenciar source_name pelo tipo de feedback
        feedback_type = (metadata or {}).get('feedback_type', 'improvement')
        source_prefix = 'approved_content' if feedback_type == 'approved' else 'user_improvement'

        # Criar embedding
        KnowledgeBaseEmbedding.objects.create(
            knowledge_base=kb,
            source_name=f'{source_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            source_type='user_feedback',
            chunk_index=0,
            chunk_text=improvement_text,
            chunk_size=len(improvement_text),
            embedding=embedding,
            embedding_model=self.DEFAULT_EMBEDDING_MODEL,
            metadata=_sanitize_metadata(obj_metadata)
        )

        logger.info(f"Melhoria adicionada à KB '{kb_name}' ({len(improvement_text)} caracteres)")
        return 1

    def search_section_improvements(
        self,
        section_name: str,
        query: str,
        n_results: int = 3,
        min_similarity: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Busca melhorias anteriores para uma seção.

        Args:
            section_name: Nome da seção
            query: Texto para buscar (geralmente o objetivo da contratação)
            n_results: Número máximo de resultados
            min_similarity: Similaridade mínima

        Returns:
            Lista de melhorias relevantes
        """
        kb_name = f"section_improvements_{section_name.lower().replace(' ', '_')}"

        # Verificar se KB existe
        if not KnowledgeBase.objects.filter(name=kb_name, is_active=True).exists():
            logger.debug(f"KB de melhorias não existe: {kb_name}")
            return []

        return self.search_knowledge_base(
            knowledge_base_name=kb_name,
            query=query,
            n_results=n_results,
            min_similarity=min_similarity
        )

    def get_all_section_improvements(
        self,
        query: str,
        n_results: int = 5,
        min_similarity: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Busca melhorias em TODAS as KBs de seções.

        Args:
            query: Texto para buscar
            n_results: Número máximo de resultados
            min_similarity: Similaridade mínima

        Returns:
            Lista de melhorias de todas as seções, ordenadas por similaridade
        """
        from pgvector.django import CosineDistance

        query_embedding = self.generate_embedding(query)

        # Buscar em todas as KBs de melhorias
        results = (
            KnowledgeBaseEmbedding.objects
            .filter(
                knowledge_base__name__startswith='section_improvements_',
                knowledge_base__is_active=True
            )
            .annotate(distance=CosineDistance('embedding', query_embedding))
            .filter(distance__lte=(1 - min_similarity))
            .order_by('distance')[:n_results]
        )

        return [
            {
                'chunk_text': r.chunk_text,
                'similarity': 1 - r.distance,
                'source_name': r.source_name,
                'section_name': r.metadata.get('section_name', 'Desconhecida'),
                'knowledge_base': r.knowledge_base.name,
                'metadata': r.metadata
            }
            for r in results
        ]
