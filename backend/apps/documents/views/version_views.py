"""
Views para Versionamento Semântico de Documentos.

Endpoints:
  POST /api/v1/documents/{id}/versions/
    - Cria nova versão do documento

  GET /api/v1/documents/{id}/versions/
    - Lista histórico de versões

  GET /api/v1/documents/{id}/versions/{version_id}/
    - Retorna detalhes de uma versão

  GET /api/v1/documents/{id}/versions/{version_id}/diff/
    - Calcula diff entre duas versões

  POST /api/v1/documents/{id}/versions/{version_id}/rollback/
    - Executa rollback para versão anterior
"""

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import Document, DocumentVersion
from ..serializers import DocumentVersionSerializer, VersionDiffSerializer
from ..services.version_control_service import (
    VersionControlService,
    VersionType,
    SemanticDiff,
)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_version(request, document_id):
    """
    POST /api/v1/documents/{id}/versions/

    Cria nova versão do documento.

    Request:
    {
        "sections": [
            {"id": "uuid", "title": "Título", "content": "Conteúdo"},
            ...
        ],
        "change_summary": "Resumo das alterações",
        "version_type": "minor"  // major, minor, patch (opcional, default: minor)
        "tags": ["tag1", "tag2"]  // opcional
    }
    """
    document = get_object_or_404(Document, id=document_id)

    # Verificar permissão
    if document.user != request.user and not request.user.is_staff:
        return Response(
            {'detail': 'Sem permissão para criar versão'},
            status=status.HTTP_403_FORBIDDEN
        )

    sections = request.data.get('sections', [])
    change_summary = request.data.get('change_summary', '')
    version_type_str = request.data.get('version_type', 'minor')
    tags = request.data.get('tags', [])

    # Validar sections
    if not sections:
        return Response(
            {'detail': 'Seções são obrigatórias'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Mapear version_type
    try:
        version_type = VersionType(version_type_str)
    except ValueError:
        return Response(
            {'detail': f'Tipo de versão inválido: {version_type_str}. Use major, minor ou patch.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        service = VersionControlService(document)
        version_metadata = service.create_version(
            user=request.user,
            sections=sections,
            change_summary=change_summary,
            version_type=version_type,
            tags=tags,
        )

        # Buscar versão criada no banco
        version = DocumentVersion.objects.get(id=version_metadata.version_id)
        serializer = DocumentVersionSerializer(version)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'detail': f'Erro ao criar versão: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_versions(request, document_id):
    """
    GET /api/v1/documents/{id}/versions/

    Lista histórico de versões do documento.
    """
    document = get_object_or_404(Document, id=document_id)

    # Verificar permissão
    if document.user != request.user and not request.user.is_staff:
        return Response(
            {'detail': 'Sem permissão para visualizar versões'},
            status=status.HTTP_403_FORBIDDEN
        )

    service = VersionControlService(document)
    history = service.get_version_history()

    # Serializar manualmente
    versions_data = [
        {
            'version_id': str(h.version_id),
            'version_number': h.version_number,
            'version_type': h.version_type.value,
            'created_at': h.created_at.isoformat(),
            'created_by': h.created_by,
            'change_summary': h.change_summary,
            'tags': h.tags,
            'parent_version': str(h.parent_version) if h.parent_version else None,
        }
        for h in history
    ]

    return Response({
        'count': len(versions_data),
        'results': versions_data,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_version_detail(request, document_id, version_id):
    """
    GET /api/v1/documents/{id}/versions/{version_id}/

    Retorna detalhes de uma versão específica.
    """
    document = get_object_or_404(Document, id=document_id)

    # Verificar permissão
    if document.user != request.user and not request.user.is_staff:
        return Response(
            {'detail': 'Sem permissão para visualizar versão'},
            status=status.HTTP_403_FORBIDDEN
        )

    version = get_object_or_404(DocumentVersion, id=version_id, document=document)
    serializer = DocumentVersionSerializer(version)

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_version_diff(request, document_id):
    """
    GET /api/v1/documents/{id}/versions/diff/

    Calcula diff entre duas versões.

    Query params:
    - old_version: UUID da versão antiga
    - new_version: UUID da versão nova
    - include_semantic: true/false (default: true)
    """
    document = get_object_or_404(Document, id=document_id)

    # Verificar permissão
    if document.user != request.user and not request.user.is_staff:
        return Response(
            {'detail': 'Sem permissão para visualizar diff'},
            status=status.HTTP_403_FORBIDDEN
        )

    old_version_id = request.query_params.get('old_version')
    new_version_id = request.query_params.get('new_version')
    include_semantic = request.query_params.get('include_semantic', 'true').lower() == 'true'

    if not old_version_id or not new_version_id:
        return Response(
            {'detail': 'Parâmetros old_version e new_version são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        import uuid
        old_uuid = uuid.UUID(old_version_id)
        new_uuid = uuid.UUID(new_version_id)

        service = VersionControlService(document)
        diff: SemanticDiff = service.get_diff(
            old_version_id=old_uuid,
            new_version_id=new_uuid,
            include_semantic=include_semantic,
        )

        # Serializar diff
        diff_data = {
            'old_version_id': str(diff.old_version_id),
            'new_version_id': str(diff.new_version_id),
            'summary': diff.summary,
            'similarity_score': round(diff.similarity_score, 4),
            'changes': [
                {
                    'section_id': c['section_id'],
                    'section_title': c['section_title'],
                    'change_type': c['change_type'],
                    'old_content': c.get('old_content', ''),
                    'new_content': c.get('new_content', ''),
                    'diff': c.get('diff', []),
                }
                for c in diff.changes
            ],
            'semantic_changes': diff.semantic_changes,
        }

        return Response(diff_data)

    except ValueError as e:
        return Response(
            {'detail': f'UUID inválido: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except DocumentVersion.DoesNotExist as e:
        return Response(
            {'detail': f'Versão não encontrada: {str(e)}'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Erro ao calcular diff: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def rollback_version(request, document_id, version_id):
    """
    POST /api/v1/documents/{id}/versions/{version_id}/rollback/

    Executa rollback para uma versão anterior.

    Request:
    {
        "sections": ["uuid1", "uuid2"],  // Seções específicas para rollback (opcional)
        "create_new_version": true  // Criar nova versão após rollback (default: true)
    }
    """
    document = get_object_or_404(Document, id=document_id)

    # Verificar permissão
    if document.user != request.user and not request.user.is_staff:
        return Response(
            {'detail': 'Sem permissão para executar rollback'},
            status=status.HTTP_403_FORBIDDEN
        )

    sections = request.data.get('sections')
    create_new_version = request.data.get('create_new_version', True)

    try:
        import uuid
        target_uuid = uuid.UUID(version_id)

        service = VersionControlService(document)
        result = service.rollback_to_version(
            version_id=target_uuid,
            user=request.user,
            sections=sections,
            create_new_version=create_new_version,
        )

        return Response({
            'detail': 'Rollback executado com sucesso',
            'version_number': result.version_number,
            'version_type': result.version_type.value,
            'change_summary': result.change_summary,
        })

    except ValueError as e:
        return Response(
            {'detail': f'UUID inválido: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except DocumentVersion.DoesNotExist as e:
        return Response(
            {'detail': f'Versão não encontrada: {str(e)}'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Erro ao executar rollback: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
