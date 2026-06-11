"""
Views para Knowledge Base
"""
import logging

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from apps.accounts.permissions import is_admin_or_manager
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from django.db.models import Q
from .models import Document, DocumentChunk
from .serializers import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentUploadSerializer,
    DocumentUpdateSerializer,
    DocumentChunkSerializer,
    DocumentSearchSerializer,
    SearchResultSerializer,
)
from .permissions import CanManageDocuments

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="Listar documentos",
        description="Retorna lista de documentos da Knowledge Base (públicos ou próprios)",
        tags=["Knowledge Base - Documentos"],
        responses={200: DocumentListSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Buscar documento por ID",
        description="Retorna detalhes completos de um documento incluindo chunks",
        tags=["Knowledge Base - Documentos"],
        responses={200: DocumentDetailSerializer}
    ),
    create=extend_schema(
        summary="Upload de documento",
        description="Faz upload de um novo documento para a Knowledge Base",
        tags=["Knowledge Base - Documentos"],
        request=DocumentUploadSerializer,
        responses={201: DocumentDetailSerializer}
    ),
    update=extend_schema(
        summary="Atualizar documento",
        description="Atualiza metadados do documento (apenas criador ou admin)",
        tags=["Knowledge Base - Documentos"],
        request=DocumentUpdateSerializer,
        responses={200: DocumentDetailSerializer}
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente documento",
        description="Atualiza campos específicos do documento (apenas criador ou admin)",
        tags=["Knowledge Base - Documentos"],
        request=DocumentUpdateSerializer,
        responses={200: DocumentDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Deletar documento",
        description="Remove documento e seus chunks (apenas criador ou admin)",
        tags=["Knowledge Base - Documentos"],
        responses={204: None}
    ),
)
class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de documentos da Knowledge Base
    """
    queryset = Document.objects.all()
    permission_classes = [CanManageDocuments]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        """Retorna serializer apropriado por ação"""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'create':
            return DocumentUploadSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        return DocumentDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Upload de documento com processamento rápido.

        Fluxo otimizado:
        1. Lê arquivo em memória
        2. Cria Document no DB SEM arquivo (rápido, sem R2)
        3. Processa texto + chunks + embeddings da memória (~3s)
        4. Retorna resposta ao usuário
        5. Upload do arquivo para R2 em background thread (invisível)
        """
        import os
        import logging
        import threading
        logger = logging.getLogger(__name__)

        logger.info(f"=== KB Global: Upload de documento ===")

        # 1. Ler arquivo em memória
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'file': ['Este campo é obrigatório.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_content = uploaded_file.read()
        file_name = uploaded_file.name
        file_size = len(file_content)
        file_type = os.path.splitext(file_name)[1].lower().replace('.', '')

        logger.info(f"=== Arquivo em memória: {file_name} ({file_size} bytes) ===")

        # 2. Criar Document no DB SEM o arquivo (evita upload R2 de ~60s)
        # Construir dict sem 'file' (request.data.copy() faz deepcopy que falha com file handles)
        data = {k: v for k, v in request.data.items() if k != 'file'}

        serializer = self.get_serializer(data=data)

        if not serializer.is_valid():
            logger.error(f"=== Validação falhou: {serializer.errors} ===")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Salvar sem arquivo - insert rápido no DB
        serializer.validated_data.pop('file', None)
        instance = serializer.save(
            file_size=file_size,
            file_type=file_type,
        )

        logger.info(f"=== Document {instance.id} criado no DB (sem R2) ===")

        # 3. Processar texto + chunks + embeddings da memória (~3s)
        #    Status: pending → processing → completed
        from .services import DocumentProcessingService
        try:
            chunk_count = DocumentProcessingService.process_document(
                instance, file_content=file_content
            )
            logger.info(f"=== Documento {instance.id} processado: {chunk_count} chunks ===")
        except Exception as e:
            logger.error(f"=== Erro ao processar {instance.id}: {str(e)} ===")

        # 4. Marcar como "uploading" e retornar resposta ao usuário (~3s total)
        instance.status = 'uploading'
        instance.save(update_fields=['status'])

        detail_serializer = DocumentDetailSerializer(
            instance, context={'request': request}
        )
        headers = self.get_success_headers(serializer.data)

        # 5. Upload do arquivo para R2 em background thread
        #    Status: uploading → ready (ou failed)
        def _upload_to_r2(doc_id, content, filename):
            """Thread que sobe o arquivo para R2 sem bloquear o usuário."""
            import time
            from django.core.files.base import ContentFile
            try:
                t0 = time.time()
                doc = Document.objects.get(id=doc_id)
                doc.file.save(filename, ContentFile(content), save=False)
                doc.status = 'ready'
                doc.save(update_fields=['file', 'status'])
                elapsed = round(time.time() - t0, 1)
                logger.info(f"=== [Background] R2 upload concluído: {filename} ({elapsed}s) - status: ready ===")
            except Exception as e:
                logger.error(f"=== [Background] Erro R2 upload {doc_id}: {str(e)} ===")
                try:
                    doc = Document.objects.get(id=doc_id)
                    doc.status = 'completed'  # Volta para processado (chunks OK, só R2 falhou)
                    doc.processing_error = f'Erro no upload R2: {str(e)}'
                    doc.save(update_fields=['status', 'processing_error'])
                except Exception:
                    logger.error("Failed to update document status after R2 upload failure for doc %s", doc_id, exc_info=True)

        thread = threading.Thread(
            target=_upload_to_r2,
            args=(instance.id, file_content, file_name),
            daemon=True,
        )
        thread.start()
        logger.info(f"=== [Background] R2 upload iniciado em thread ===")

        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        """Filtra documentos por permissão e query params"""
        user = self.request.user
        queryset = Document.objects.select_related('uploaded_by')

        # Admin vê todos, usuários veem públicos + próprios
        if not is_admin_or_manager(user):
            queryset = queryset.filter(Q(is_public=True) | Q(uploaded_by=user))

        # Filtrar por categoria
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filtrar por status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filtrar por tag
        tag = self.request.query_params.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__contains=[tag])

        # Apenas ativos
        if self.request.query_params.get('active_only', 'true').lower() == 'true':
            queryset = queryset.filter(is_active=True)

        return queryset.order_by('-created_at')

    @extend_schema(
        summary="Reprocessar documento",
        description="Reprocessa documento (apaga chunks antigos e processa novamente)",
        tags=["Knowledge Base - Documentos"],
        responses={200: OpenApiResponse(
            description="Reprocessamento iniciado")}
    )
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocessa documento"""
        document = self.get_object()

        # Apagar chunks antigos
        document.chunks.all().delete()

        # Marcar para processamento
        document.status = 'pending'
        document.processing_error = ''
        document.save()

        return Response({
            'detail': 'Documento marcado para reprocessamento.',
            'status': document.status
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Buscar chunks do documento",
        description="Retorna todos os chunks de um documento específico",
        tags=["Knowledge Base - Documentos"],
        responses={200: DocumentChunkSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """Lista chunks do documento"""
        document = self.get_object()
        chunks = document.chunks.all()
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Busca semântica",
        description="Realiza busca semântica nos documentos usando embeddings vetoriais",
        tags=["Knowledge Base - Busca"],
        request=DocumentSearchSerializer,
        responses={200: SearchResultSerializer(many=True)},
        examples=[
            OpenApiExample(
                name="Exemplo de busca",
                value={
                    "query": "Como elaborar justificativa de contratação?",
                    "limit": 5,
                    "category": "manual"
                },
                request_only=True
            )
        ]
    )
    @action(detail=False, methods=['post'], parser_classes=[JSONParser])
    def search(self, request):
        """Busca semântica usando embeddings vetoriais"""
        from .services import VectorSearchService

        serializer = DocumentSearchSerializer(data=request.data)

        if serializer.is_valid():
            query = serializer.validated_data['query']
            limit = serializer.validated_data.get('limit', 5)
            category = serializer.validated_data.get('category')
            tags = serializer.validated_data.get('tags', [])

            try:
                # Busca vetorial com pgvector
                results = VectorSearchService.search(
                    query_text=query,
                    top_k=limit,
                    similarity_threshold=0.5,  # Threshold mais baixo para mais resultados
                    category=category,
                    tags=tags if tags else None
                )

                return Response({
                    'query': query,
                    'results': results,
                    'count': len(results)
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'error': str(e),
                    'query': query
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Estatísticas da KB",
        description="Retorna estatísticas gerais da Knowledge Base",
        tags=["Knowledge Base - Busca"],
        responses={200: OpenApiResponse(description="Estatísticas")}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas da KB"""
        user = request.user
        queryset = Document.objects.all()

        # Filtrar por permissão
        if not is_admin_or_manager(user):
            queryset = queryset.filter(Q(is_public=True) | Q(uploaded_by=user))

        stats = {
            'total_documents': queryset.count(),
            'by_status': {
                'pending': queryset.filter(status='pending').count(),
                'processing': queryset.filter(status='processing').count(),
                'completed': queryset.filter(status='completed').count(),
                'uploading': queryset.filter(status='uploading').count(),
                'ready': queryset.filter(status='ready').count(),
                'failed': queryset.filter(status='failed').count(),
            },
            'by_category': {},
            'total_chunks': DocumentChunk.objects.filter(document__in=queryset).count(),
        }

        # Contar por categoria
        for category, label in Document.CATEGORY_CHOICES:
            stats['by_category'][category] = queryset.filter(
                category=category).count()

        return Response(stats, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Preview do documento",
        description="Retorna o arquivo do documento com headers corretos para preview inline",
        tags=["Knowledge Base - Documentos"],
        responses={200: OpenApiResponse(description="Arquivo do documento")}
    )
    @action(detail=True, methods=['get'], url_path='preview')
    def preview(self, request, pk=None):
        """Serve arquivo do documento com headers corretos para preview inline"""
        from django.http import FileResponse, HttpResponseRedirect
        import mimetypes

        document = self.get_object()

        if not document.file:
            return Response(
                {'error': 'Arquivo ainda nao disponivel.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Para storage remoto (S3/R2), redirecionar para a URL pública.
        # .path só existe em FileSystemStorage local.
        try:
            file_path = document.file.path
        except NotImplementedError:
            # Storage remoto (S3/R2) — redirecionar para URL pública
            return HttpResponseRedirect(document.file.url)

        content_type, _ = mimetypes.guess_type(file_path)

        # Se não conseguir detectar, usar padrão por extensão
        if not content_type:
            if file_path.endswith('.pdf'):
                content_type = 'application/pdf'
            elif file_path.endswith('.docx'):
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_path.endswith('.txt'):
                content_type = 'text/plain'
            else:
                content_type = 'application/octet-stream'

        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type
        )

        # Headers para permitir preview inline
        response['Content-Disposition'] = f'inline; filename="{document.title}"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Access-Control-Allow-Origin'] = request.headers.get(
            'Origin', '*')
        response['Access-Control-Allow-Credentials'] = 'true'

        return response


# ============================================================
# Endpoint de Busca Legislativa
# ============================================================

@extend_schema(
    summary="Buscar legislação oficial",
    description=(
        "Busca legislação em fontes oficiais brasileiras. "
        "Primeiro tenta a KB local (pgvector); se não encontrar resultado "
        "satisfatório, faz scraping em planalto.gov.br, STF e STJ."
    ),
    tags=["Knowledge Base - Legislação"],
    responses={200: OpenApiResponse(description="Resultados da busca legislativa")},
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def legislation_search(request):
    """
    GET /api/v1/kb/legislation/search/?q=<query>

    Fluxo:
    1. Recebe query string
    2. Busca na KB local via pgvector
    3. Se resultado insuficiente, faz scraping nas fontes oficiais
    4. Retorna resultado combinado
    """
    from .services import VectorSearchService
    from .legislation_search import LegislationSearchService

    query = request.query_params.get('q', '').strip()
    if not query or len(query) < 3:
        return Response(
            {'detail': 'Parâmetro "q" deve ter pelo menos 3 caracteres.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Passo 1: buscar na KB local
    kb_results = []
    kb_sufficient = False
    try:
        kb_results = VectorSearchService.search(
            query_text=query,
            top_k=5,
            similarity_threshold=0.7,
            category=None,
        )
        # Considerar suficiente se houver >= 2 resultados com boa similaridade
        high_quality = [r for r in kb_results if r.get('similarity', 0) >= 0.75]
        kb_sufficient = len(high_quality) >= 2
    except Exception as e:
        logger.warning('[legislation_search] Erro na busca KB local: %s', e)

    # Passo 2: se KB insuficiente, buscar nas fontes oficiais
    web_results = {}
    if not kb_sufficient:
        try:
            web_results = LegislationSearchService.search_all(query)
        except Exception as e:
            logger.warning('[legislation_search] Erro na busca web: %s', e)
            web_results = {'error': str(e), 'fontes': {}, 'total_results': 0}

    return Response({
        'query': query,
        'kb_results': kb_results,
        'kb_sufficient': kb_sufficient,
        'web_results': web_results,
        'source': 'kb' if kb_sufficient else 'kb+web',
    })
