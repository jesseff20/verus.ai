"""
Views de gerenciamento de Knowledge Bases (Camadas 2 + 3).
"""
import logging
import os

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import (
    KnowledgeBase,
    KnowledgeBaseEmbedding,
    KBSourceFile,
    AgentKnowledgeBaseLink,
)
from ..serializers import (
    KnowledgeBaseListSerializer,
    KnowledgeBaseCreateSerializer,
    KBSourceSerializer,
    KBUploadSerializer,
    KBSourceFileSerializer,
    AgentKnowledgeBaseLinkSerializer,
    AgentKnowledgeBaseLinkWriteSerializer,
)
from ..services.document_processor import DocumentProcessorService
from ..services.pgvector_service import PgVectorService

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Listar/Criar Bases de Conhecimento",
    description="GET lista KBs das camadas blueprint e agent. POST cria nova KB.",
    tags=["Knowledge Base Management"],
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_knowledge_bases(request):
    """
    GET  /api/v1/intelligent-assistant/knowledge-bases/manage/
    POST /api/v1/intelligent-assistant/knowledge-bases/manage/
    """
    if request.method == 'GET':
        from django.db.models import Count

        kb_layer_filter = request.query_params.get('kb_layer')

        queryset = KnowledgeBase.objects.select_related(
            'blueprint', 'blueprint__document_type',
            'agent_config', 'created_by'
        ).prefetch_related('embeddings').annotate(
            agent_links_count=Count('agent_links', distinct=True)
        )

        if kb_layer_filter and kb_layer_filter != 'all':
            queryset = queryset.filter(kb_layer=kb_layer_filter)
        elif not kb_layer_filter:
            # Default: blueprint + agent (retrocompatível)
            queryset = queryset.filter(kb_layer__in=['blueprint', 'agent'])
        # kb_layer_filter == 'all': sem filtro, retorna todas as camadas

        all_kbs = queryset.order_by('-updated_at')
        blueprint_kbs = queryset.filter(kb_layer='blueprint')
        agent_kbs = queryset.filter(kb_layer='agent')
        global_kbs = queryset.filter(kb_layer='global')

        serialized_all = KnowledgeBaseListSerializer(all_kbs, many=True).data
        # Injetar agent_links_count nos dados serializados
        kb_map = {kb.id: kb.agent_links_count for kb in all_kbs}
        for item in serialized_all:
            from uuid import UUID
            item['agent_links_count'] = kb_map.get(UUID(item['id']), 0)

        return Response({
            'knowledge_bases': serialized_all,
            'global_kbs': KnowledgeBaseListSerializer(global_kbs, many=True).data,
            'blueprint_kbs': KnowledgeBaseListSerializer(blueprint_kbs, many=True).data,
            'agent_kbs': KnowledgeBaseListSerializer(agent_kbs, many=True).data,
            'total': queryset.count(),
        })

    # POST - Criar nova KB
    serializer = KnowledgeBaseCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    kb = serializer.save(created_by=request.user)

    return Response(
        KnowledgeBaseListSerializer(kb).data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    summary="Atualizar/Deletar Base de Conhecimento",
    tags=["Knowledge Base Management"],
)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_knowledge_base_detail(request, kb_id):
    """
    PATCH  /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/
    DELETE /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/
    """
    try:
        kb = KnowledgeBase.objects.get(id=kb_id)
    except KnowledgeBase.DoesNotExist:
        return Response(
            {'error': 'Base de conhecimento não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'DELETE':
        kb.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH
    allowed_fields = ['name', 'description', 'is_active']
    for field in allowed_fields:
        if field in request.data:
            setattr(kb, field, request.data[field])
    kb.save()

    return Response(KnowledgeBaseListSerializer(kb).data)


@extend_schema(
    summary="Upload de documento para Base de Conhecimento",
    description="Faz upload de PDF/DOCX/TXT, extrai texto, gera embeddings.",
    tags=["Knowledge Base Management"],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_to_knowledge_base(request, kb_id):
    """
    POST /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/upload/
    """
    try:
        kb = KnowledgeBase.objects.get(id=kb_id, is_active=True)
    except KnowledgeBase.DoesNotExist:
        return Response(
            {'error': 'Base de conhecimento não encontrada ou inativa'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = KBUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uploaded_file = serializer.validated_data['file']
    source_name = serializer.validated_data.get('source_name', '').strip()
    if not source_name:
        source_name = uploaded_file.name

    # Criar KBSourceFile para rastreabilidade
    import os
    file_ext = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')

    source_file = KBSourceFile.objects.create(
        knowledge_base=kb,
        file_name=source_name,
        file_size=uploaded_file.size,
        file_type=file_ext,
        status='processing',
        uploaded_by=request.user,
    )

    try:
        import time as _time
        _timings = {}
        _t_total = _time.time()
        size_mb = round(uploaded_file.size / 1024 / 1024, 2)

        # 1. Extrair texto (reutiliza DocumentProcessorService)
        logger.info(f"[Upload Debug] INÍCIO - {uploaded_file.name} ({size_mb}MB), type={type(uploaded_file).__name__}")
        _t0 = _time.time()
        processor = DocumentProcessorService()
        result = processor.process_uploaded_file(uploaded_file)
        _timings['extração'] = round(_time.time() - _t0, 2)
        logger.info(f"[Upload Debug] Extração OK: {result.get('num_chunks', '?')} chunks em {_timings['extração']}s")

        extracted_text = result['text']
        file_type = result['file_type']

        if not extracted_text or not extracted_text.strip():
            source_file.status = 'failed'
            source_file.processing_error = 'Nenhum texto foi extraído do documento.'
            source_file.save()
            return Response(
                {'error': 'Nenhum texto foi extraído do documento.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Gerar embeddings (reutiliza PgVectorService)
        logger.info(f"[Upload Debug] Iniciando embeddings para {result.get('num_chunks', '?')} chunks...")
        _t0 = _time.time()
        pgvector_service = PgVectorService()
        chunks_created = pgvector_service.add_to_knowledge_base(
            knowledge_base=kb,
            source_name=source_name,
            source_type=file_type,
            text=extracted_text,
            source_file=source_file,
            metadata={
                'uploaded_by': str(request.user.id),
                'original_filename': uploaded_file.name,
                'file_size': uploaded_file.size,
                'source_file_id': str(source_file.id),
            }
        )
        _timings['embedding'] = round(_time.time() - _t0, 2)

        # 3. Atualizar KBSourceFile com status e contagem
        source_file.chunk_count = chunks_created
        source_file.status = 'completed'
        source_file.save()

        # 4. Upload do arquivo para R2 em background (se KB Global)
        r2_status = 'n/a'
        if kb.kb_layer == 'global':
            import threading
            r2_status = 'async (background)'

            def upload_file_to_r2(sf_id, file_content, file_name):
                """Upload do arquivo para R2 em background."""
                _r2_start = _time.time()
                try:
                    from django.core.files.base import ContentFile
                    sf = KBSourceFile.objects.get(id=sf_id)
                    sf.file.save(file_name, ContentFile(file_content), save=True)
                    logger.info(
                        f"[Upload R2] '{file_name}' enviado em "
                        f"{round(_time.time() - _r2_start, 2)}s"
                    )
                except Exception as e:
                    logger.error(f"[Upload R2] Erro: {e}")

            # Ler conteúdo do arquivo antes de iniciar thread
            uploaded_file.seek(0)
            file_content = uploaded_file.read()

            thread = threading.Thread(
                target=upload_file_to_r2,
                args=(source_file.id, file_content, uploaded_file.name),
                daemon=True,
            )
            thread.start()

        _timings['TOTAL'] = round(_time.time() - _t_total, 2)

        logger.info(
            f"[Upload] ✓ KB '{kb.name}' - {source_name} ({size_mb}MB)\n"
            f"  Extração+Chunks: {_timings['extração']}s "
            f"({result.get('num_chunks', '?')} chunks, {result.get('char_count', len(extracted_text))} chars)\n"
            f"  Embedding:       {_timings['embedding']}s ({chunks_created} vetores)\n"
            f"  R2:              {r2_status}\n"
            f"  TOTAL:           {_timings['TOTAL']}s"
        )

        return Response({
            'source_name': source_name,
            'chunks_created': chunks_created,
            'char_count': len(extracted_text),
            'file_type': file_type,
            'source_file_id': str(source_file.id),
            'warnings': result.get('warnings', []),
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        logger.warning(f"[Upload] Falha ao processar para KB '{kb.name}': {e}")
        source_file.status = 'failed'
        source_file.processing_error = str(e)
        source_file.save()
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        source_file.status = 'failed'
        source_file.processing_error = str(e)
        source_file.save()
        logger.error(f"Erro ao processar upload para KB '{kb.name}': {e}")
        return Response(
            {'error': f'Erro ao processar documento: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Listar fontes de uma Base de Conhecimento",
    tags=["Knowledge Base Management"],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_kb_sources(request, kb_id):
    """
    GET /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/sources/
    """
    try:
        kb = KnowledgeBase.objects.get(id=kb_id)
    except KnowledgeBase.DoesNotExist:
        return Response(
            {'error': 'Base de conhecimento não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    from django.db.models import Count, Sum, Min

    sources = (
        KnowledgeBaseEmbedding.objects
        .filter(knowledge_base=kb)
        .values('source_name', 'source_type')
        .annotate(
            chunks_count=Count('id'),
            total_characters=Sum('chunk_size'),
            created_at=Min('created_at'),
        )
        .order_by('-created_at')
    )

    serializer = KBSourceSerializer(sources, many=True)

    return Response({
        'kb_id': str(kb.id),
        'kb_name': kb.name,
        'sources': serializer.data,
        'total_sources': len(sources),
    })


@extend_schema(
    summary="Deletar fonte de uma Base de Conhecimento",
    tags=["Knowledge Base Management"],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_kb_source(request, kb_id, source_name):
    """
    DELETE /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/sources/{source_name}/
    """
    try:
        kb = KnowledgeBase.objects.get(id=kb_id)
    except KnowledgeBase.DoesNotExist:
        return Response(
            {'error': 'Base de conhecimento não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    deleted_count, _ = KnowledgeBaseEmbedding.objects.filter(
        knowledge_base=kb,
        source_name=source_name,
    ).delete()

    if deleted_count == 0:
        return Response(
            {'error': f'Fonte "{source_name}" não encontrada nesta KB'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Deletar KBSourceFile associado (se existir)
    KBSourceFile.objects.filter(
        knowledge_base=kb,
        file_name=source_name,
    ).delete()

    logger.info(f"Deletados {deleted_count} embeddings de '{source_name}' da KB '{kb.name}'")

    return Response({
        'deleted_count': deleted_count,
        'source_name': source_name,
    })


# ========== KB STATS & SOURCE FILES ==========


@extend_schema(
    summary="Estatísticas das Bases de Conhecimento",
    tags=["Knowledge Base Management"],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kb_stats(request):
    """
    GET /api/v1/intelligent-assistant/knowledge-bases/stats/
    Retorna estatísticas unificadas de todas as KBs.
    """
    from django.db.models import Count, Sum

    kbs = KnowledgeBase.objects.filter(is_active=True)

    total_kbs = kbs.count()
    by_layer = {}
    for layer_code, layer_label in KnowledgeBase.KB_LAYER_CHOICES:
        layer_kbs = kbs.filter(kb_layer=layer_code)
        layer_embeddings = KnowledgeBaseEmbedding.objects.filter(
            knowledge_base__kb_layer=layer_code,
            knowledge_base__is_active=True,
        )
        by_layer[layer_code] = {
            'label': layer_label,
            'kbs': layer_kbs.count(),
            'embeddings': layer_embeddings.count(),
        }

    total_embeddings = KnowledgeBaseEmbedding.objects.filter(
        knowledge_base__is_active=True
    ).count()
    total_source_files = KBSourceFile.objects.filter(
        knowledge_base__is_active=True
    ).count()

    return Response({
        'total_kbs': total_kbs,
        'total_embeddings': total_embeddings,
        'total_source_files': total_source_files,
        'by_layer': by_layer,
    })


@extend_schema(
    summary="Listar arquivos-fonte de uma KB",
    tags=["Knowledge Base Management"],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_kb_source_files(request, kb_id):
    """
    GET /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/files/
    Lista os KBSourceFile de uma KB (rastreabilidade de arquivos).
    """
    try:
        kb = KnowledgeBase.objects.get(id=kb_id)
    except KnowledgeBase.DoesNotExist:
        return Response(
            {'error': 'Base de conhecimento não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    source_files = KBSourceFile.objects.filter(
        knowledge_base=kb
    ).select_related('uploaded_by').order_by('-created_at')

    return Response({
        'kb_id': str(kb.id),
        'kb_name': kb.name,
        'files': KBSourceFileSerializer(source_files, many=True).data,
        'total': source_files.count(),
    })


@extend_schema(
    summary="Deletar arquivo-fonte de uma KB",
    tags=["Knowledge Base Management"],
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_kb_source_file(request, kb_id, file_id):
    """
    DELETE /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/files/{file_id}/
    Deleta um KBSourceFile e seus embeddings associados.
    """
    try:
        source_file = KBSourceFile.objects.get(id=file_id, knowledge_base_id=kb_id)
    except KBSourceFile.DoesNotExist:
        return Response(
            {'error': 'Arquivo-fonte não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Deletar embeddings associados pelo source_name
    deleted_emb, _ = KnowledgeBaseEmbedding.objects.filter(
        knowledge_base_id=kb_id,
        source_name=source_file.file_name,
    ).delete()

    file_name = source_file.file_name
    source_file.delete()

    logger.info(
        f"Deletado arquivo '{file_name}' + {deleted_emb} embeddings da KB {kb_id}"
    )

    return Response({
        'deleted_file': file_name,
        'deleted_embeddings': deleted_emb,
    })


# ========== AGENT ↔ KB LINKS ==========


@extend_schema(
    summary="Listar/Criar vínculos Agente ↔ KB",
    tags=["Knowledge Base Management"],
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_kb_agent_links(request, kb_id):
    """
    GET  /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/agent-links/
    POST /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/agent-links/
    """
    try:
        kb = KnowledgeBase.objects.get(id=kb_id)
    except KnowledgeBase.DoesNotExist:
        return Response(
            {'error': 'Base de conhecimento não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        links = AgentKnowledgeBaseLink.objects.filter(
            knowledge_base=kb
        ).select_related('agent').order_by('priority')

        return Response({
            'kb_id': str(kb.id),
            'kb_name': kb.name,
            'links': AgentKnowledgeBaseLinkSerializer(links, many=True).data,
            'total': links.count(),
        })

    # POST - Criar novo vínculo
    serializer = AgentKnowledgeBaseLinkWriteSerializer(
        data=request.data,
        context={'knowledge_base': kb}
    )
    serializer.is_valid(raise_exception=True)
    link = serializer.save(knowledge_base=kb)

    return Response(
        AgentKnowledgeBaseLinkSerializer(link).data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    summary="Atualizar/Deletar vínculo Agente ↔ KB",
    tags=["Knowledge Base Management"],
)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_kb_agent_link_detail(request, kb_id, link_id):
    """
    PATCH  /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/agent-links/{link_id}/
    DELETE /api/v1/intelligent-assistant/knowledge-bases/manage/{kb_id}/agent-links/{link_id}/
    """
    try:
        link = AgentKnowledgeBaseLink.objects.select_related('agent').get(
            id=link_id, knowledge_base_id=kb_id
        )
    except AgentKnowledgeBaseLink.DoesNotExist:
        return Response(
            {'error': 'Vínculo não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'DELETE':
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH
    serializer = AgentKnowledgeBaseLinkWriteSerializer(
        link, data=request.data, partial=True,
        context={'knowledge_base': link.knowledge_base}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(AgentKnowledgeBaseLinkSerializer(link).data)
