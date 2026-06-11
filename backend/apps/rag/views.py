"""
Views para RAG
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from django.utils import timezone
from apps.accounts.permissions import is_admin_or_manager
from .models import RAGQuery, RAGContext
from .serializers import (
    RAGQueryListSerializer, RAGQueryDetailSerializer, RAGQueryExecuteSerializer,
    RAGContextListSerializer, RAGContextDetailSerializer,
    RAGContextCreateSerializer, RAGContextUpdateSerializer
)
from .permissions import IsOwnerOrAdmin
import time


@extend_schema_view(
    list=extend_schema(
        summary="Listar Queries RAG",
        description="Retorna lista de queries RAG do usuário (ou todas para admin)",
        tags=["RAG"],
        responses={200: RAGQueryListSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Buscar Query RAG por ID",
        description="Retorna detalhes completos de uma query RAG",
        tags=["RAG"],
        responses={200: RAGQueryDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Deletar Query RAG",
        description="Remove query RAG (apenas dono ou admin)",
        tags=["RAG"],
        responses={204: None}
    ),
)
class RAGQueryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para RAGQuery (read-only, criado via execute action)"""
    queryset = RAGQuery.objects.all()
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return RAGQueryListSerializer
        return RAGQueryDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = RAGQuery.objects.select_related('user', 'etp')

        # Admin vê todos, usuários veem apenas os próprios
        if not is_admin_or_manager(user):
            queryset = queryset.filter(user=user)

        # Filtro por ETP
        etp_id = self.request.query_params.get('etp_id')
        if etp_id:
            queryset = queryset.filter(etp_id=etp_id)

        # Filtro por provider
        provider = self.request.query_params.get('llm_provider')
        if provider:
            queryset = queryset.filter(llm_provider=provider)

        return queryset.order_by('-created_at')

    @extend_schema(
        summary="Executar Query RAG",
        description="Executa busca semântica e gera resposta com LLM",
        tags=["RAG"],
        request=RAGQueryExecuteSerializer,
        responses={200: RAGQueryDetailSerializer}
    )
    @action(detail=False, methods=['post'])
    def execute(self, request):
        """Executa query RAG completa com busca vetorial e LLM"""
        from apps.kb.services import VectorSearchService
        from apps.agents.services import LLMService

        serializer = RAGQueryExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query_text = serializer.validated_data['query_text']
        etp_id = serializer.validated_data.get('etp_id')
        top_k = serializer.validated_data.get('top_k', 5)
        threshold = serializer.validated_data.get('similarity_threshold', 0.7)
        filter_categories = serializer.validated_data.get('filter_categories', [])
        filter_tags = serializer.validated_data.get('filter_tags', [])
        filter_processo = serializer.validated_data.get('filter_processo')
        context_id = serializer.validated_data.get('use_context_id')
        llm_provider = serializer.validated_data.get('llm_provider', 'openai')
        model_name = serializer.validated_data.get('model_name', 'gpt-4o-mini')

        # Se filtrar por processo, adicionar tag automaticamente
        if filter_processo:
            filter_tags = filter_tags.copy() if filter_tags else []
            filter_tags.append(f'processo:{filter_processo}')

        try:
            # 1. Buscar documentos relevantes
            start_time = time.time()

            # Se usar contexto, pegar document_ids do contexto
            document_ids = None
            if context_id:
                try:
                    context = RAGContext.objects.get(id=context_id)
                    document_ids = [str(doc.id) for doc in context.documents.all()]
                except RAGContext.DoesNotExist:
                    pass

            # Busca vetorial
            retrieved_chunks = VectorSearchService.search(
                query_text=query_text,
                top_k=top_k,
                similarity_threshold=threshold,
                category=filter_categories[0] if filter_categories else None,
                tags=filter_tags if filter_tags else None,
                document_ids=document_ids
            )

            search_time = int((time.time() - start_time) * 1000)

            # 2. Montar contexto para LLM
            context_text = "\n\n---\n\n".join([
                f"Documento: {chunk['document_title']}\n"
                f"Similaridade: {chunk['similarity']}\n\n"
                f"{chunk['content']}"
                for chunk in retrieved_chunks
            ])

            # 3. Chamar LLM com contexto
            llm_start = time.time()

            system_prompt = """Você é um assistente especializado em licitações públicas e documentação técnica.
Responda com base EXCLUSIVAMENTE nas informações fornecidas no contexto.
Se a informação não estiver no contexto, diga que não encontrou.
Seja preciso, cite as fontes quando relevante, e use linguagem formal."""

            user_prompt = f"""Contexto recuperado da base de conhecimento:

{context_text}

---

Pergunta do usuário: {query_text}

Responda com base no contexto acima."""

            llm_result = LLMService.call(
                provider=llm_provider,
                model=model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2000
            )

            llm_response = llm_result['response']
            total_tokens = llm_result['tokens_used']
            llm_time = int((time.time() - llm_start) * 1000)

            # 4. Salvar query no banco
            rag_query = RAGQuery.objects.create(
                user=request.user,
                etp_id=etp_id,
                query_text=query_text,
                top_k=top_k,
                similarity_threshold=threshold,
                filter_categories=filter_categories,
                filter_tags=filter_tags,
                retrieved_chunks=retrieved_chunks,
                chunk_count=len(retrieved_chunks),
                llm_response=llm_response,
                llm_provider=llm_provider,
                llm_model=model_name,
                search_time_ms=search_time,
                llm_time_ms=llm_time,
                total_tokens=total_tokens
            )

            result_serializer = RAGQueryDetailSerializer(rag_query)
            return Response(result_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e),
                'query_text': query_text
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        summary="Listar Contextos RAG",
        description="Retorna lista de contextos RAG do usuário (ou todos para admin)",
        tags=["RAG Contexts"],
        responses={200: RAGContextListSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Buscar Contexto RAG por ID",
        description="Retorna detalhes completos de um contexto RAG",
        tags=["RAG Contexts"],
        responses={200: RAGContextDetailSerializer}
    ),
    create=extend_schema(
        summary="Criar Contexto RAG",
        description="Cria novo contexto RAG",
        tags=["RAG Contexts"],
        request=RAGContextCreateSerializer,
        responses={201: RAGContextDetailSerializer}
    ),
    update=extend_schema(
        summary="Atualizar Contexto RAG",
        description="Atualiza contexto RAG (apenas dono ou admin)",
        tags=["RAG Contexts"],
        request=RAGContextUpdateSerializer,
        responses={200: RAGContextDetailSerializer}
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente Contexto RAG",
        description="Atualiza campos específicos",
        tags=["RAG Contexts"],
        request=RAGContextUpdateSerializer,
        responses={200: RAGContextDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Deletar Contexto RAG",
        description="Remove contexto RAG (apenas dono ou admin)",
        tags=["RAG Contexts"],
        responses={204: None}
    ),
)
class RAGContextViewSet(viewsets.ModelViewSet):
    """ViewSet para RAGContext"""
    queryset = RAGContext.objects.all()
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return RAGContextListSerializer
        elif self.action == 'create':
            return RAGContextCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RAGContextUpdateSerializer
        return RAGContextDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = RAGContext.objects.select_related('user', 'etp').prefetch_related('documents')

        # Admin vê todos, usuários veem apenas os próprios
        if not is_admin_or_manager(user):
            queryset = queryset.filter(user=user)

        # Filtro por ETP
        etp_id = self.request.query_params.get('etp_id')
        if etp_id:
            queryset = queryset.filter(etp_id=etp_id)

        return queryset.order_by('-created_at')

    @extend_schema(
        summary="Adicionar Documentos ao Contexto",
        description="Adiciona documentos a um contexto RAG existente",
        tags=["RAG Contexts"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'document_ids': {
                        'type': 'array',
                        'items': {'type': 'string', 'format': 'uuid'}
                    }
                }
            }
        },
        responses={200: RAGContextDetailSerializer}
    )
    @action(detail=True, methods=['post'], url_path='add-documents')
    def add_documents(self, request, pk=None):
        """Adiciona documentos ao contexto"""
        context = self.get_object()
        document_ids = request.data.get('document_ids', [])

        from apps.kb.models import Document
        documents = Document.objects.filter(id__in=document_ids)
        context.documents.add(*documents)

        serializer = RAGContextDetailSerializer(context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Remover Documentos do Contexto",
        description="Remove documentos de um contexto RAG",
        tags=["RAG Contexts"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'document_ids': {
                        'type': 'array',
                        'items': {'type': 'string', 'format': 'uuid'}
                    }
                }
            }
        },
        responses={200: RAGContextDetailSerializer}
    )
    @action(detail=True, methods=['post'], url_path='remove-documents')
    def remove_documents(self, request, pk=None):
        """Remove documentos do contexto"""
        context = self.get_object()
        document_ids = request.data.get('document_ids', [])

        from apps.kb.models import Document
        documents = Document.objects.filter(id__in=document_ids)
        context.documents.remove(*documents)

        serializer = RAGContextDetailSerializer(context)
        return Response(serializer.data, status=status.HTTP_200_OK)
