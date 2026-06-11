"""
Views de documentos: atualização de seções e exportação (PDF, DOCX, ODT).
"""
import base64
import logging
import re

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import GeneratedDocument, DocumentBlueprint
from ._helpers import _build_blueprint_config

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Atualizar Seções do Documento",
    description="Atualiza o conteúdo das seções de um documento e regenera o PDF",
    tags=["Assistente Inteligente - Documentos"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'sections': {
                    'type': 'object',
                    'description': 'Mapa de seções editadas (ex: {"section_01": "novo conteúdo"})'
                }
            },
            'required': ['sections']
        }
    },
    responses={
        200: OpenApiResponse(description="Documento atualizado com sucesso"),
        400: OpenApiResponse(description="Dados inválidos"),
        404: OpenApiResponse(description="Documento não encontrado")
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_document_sections(request, document_id):
    """
    PUT /api/v1/intelligent-assistant/documents/{document_id}/update-sections/

    Atualiza o conteúdo das seções de um documento existente e regenera o PDF.
    """
    from ..services.persistence_service import ETPPersistenceService

    data = request.data
    sections = data.get('sections', {})

    if not sections:
        return Response({
            'error': 'Nenhuma seção fornecida para atualização'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Buscar documento
    try:
        document = GeneratedDocument.objects.select_related('session').get(id=document_id)
    except GeneratedDocument.DoesNotExist:
        return Response({
            'error': 'Documento não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    # Verificar permissão (documento pertence ao usuário)
    if document.session.user != request.user:
        return Response({
            'error': 'Sem permissão para editar este documento'
        }, status=status.HTTP_403_FORBIDDEN)

    # Atualizar markdown_content com as seções editadas
    markdown_content = document.markdown_content

    for section_key, new_content in sections.items():
        # Extrair número da seção (ex: "section_01" -> 1)
        try:
            section_num = int(section_key.replace('section_', ''))
        except ValueError:
            continue

        # Padrão para encontrar seções
        patterns = [
            rf'(## {section_num}\.\s*[^\n]+\n)(.*?)(?=## (?!{section_num}\.)\d+\.|$)',
            rf'(## Seção {section_num}[:\s]*[^\n]*\n)(.*?)(?=## (?!Seção {section_num}[:\s])\d+\.|## Seção (?!{section_num}[:\s])\d+|$)',
        ]

        replaced = False
        for pattern in patterns:
            match = re.search(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
            if match:
                header = match.group(1)
                markdown_content = re.sub(
                    pattern,
                    f'{header}{new_content}\n\n',
                    markdown_content,
                    count=1,
                    flags=re.DOTALL | re.IGNORECASE
                )
                replaced = True
                logger.info(f"Seção {section_num} atualizada no documento {document_id}")
                break

        if not replaced:
            logger.warning(f"Seção {section_num} não encontrada no markdown do documento {document_id}")

    # Salvar markdown atualizado (sem regenerar PDF - PDF é gerado sob demanda)
    document.markdown_content = markdown_content
    document.pdf_generated = False  # Marcar que PDF precisa ser re-gerado
    document.save(update_fields=['markdown_content', 'pdf_generated', 'updated_at'])

    logger.info(f"Documento {document_id} atualizado (PDF marcado para re-geração)")

    return Response({
        'success': True,
        'message': 'Documento atualizado com sucesso'
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Atualizar HTML do Documento",
    description="Salva o conteúdo HTML editado pelo usuário no editor visual",
    tags=["Assistente Inteligente - Documentos"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'html_content': {
                    'type': 'string',
                    'description': 'Conteúdo HTML completo do documento editado'
                }
            },
            'required': ['html_content']
        }
    },
    responses={
        200: OpenApiResponse(description="Documento atualizado com sucesso"),
        400: OpenApiResponse(description="Dados inválidos"),
        404: OpenApiResponse(description="Documento não encontrado")
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_document_html(request, document_id):
    """
    PUT /api/v1/intelligent-assistant/documents/{document_id}/update-html/

    Salva o conteúdo HTML editado pelo usuário no editor visual.
    Armazena no campo markdown_content (que aceita tanto markdown quanto HTML).
    """
    html_content = request.data.get('html_content', '')

    if not html_content:
        return Response({
            'error': 'Nenhum conteúdo HTML fornecido'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        document = GeneratedDocument.objects.select_related('session').get(id=document_id)
    except GeneratedDocument.DoesNotExist:
        return Response({
            'error': 'Documento não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    if document.session.user != request.user:
        return Response({
            'error': 'Sem permissão para editar este documento'
        }, status=status.HTTP_403_FORBIDDEN)

    document.markdown_content = html_content
    document.pdf_generated = False
    document.save(update_fields=['markdown_content', 'pdf_generated', 'updated_at'])

    logger.info(f"Documento {document_id} HTML atualizado pelo editor visual")

    return Response({
        'success': True,
        'message': 'Documento atualizado com sucesso'
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="Gerar PDF do Documento",
    description="Gera PDF do documento e faz upload para R2 em background. Retorna imediatamente.",
    tags=["Assistente Inteligente - Documentos"],
    responses={
        200: OpenApiResponse(description="Geração de PDF iniciada"),
        404: OpenApiResponse(description="Documento não encontrado")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_document_pdf(request, document_id):
    """
    Gera PDF do documento, retorna os bytes imediatamente e
    faz upload para R2 em background.

    POST /api/v1/intelligent-assistant/documents/{document_id}/generate-pdf/
    """
    import time
    from django.http import HttpResponse
    from django.core.files.base import ContentFile

    try:
        document = GeneratedDocument.objects.select_related('session').get(
            id=document_id,
            session__user=request.user
        )
    except GeneratedDocument.DoesNotExist:
        return Response({
            'error': 'Documento não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    # Buscar blueprint
    blueprint = None
    if document.session.blueprint_id:
        try:
            blueprint = DocumentBlueprint.objects.get(id=document.session.blueprint_id)
        except DocumentBlueprint.DoesNotExist:
            pass

    # Gerar PDF em memória
    try:
        t0 = time.time()
        from ..services.pdf_service import PDFService
        pdf_service = PDFService()

        objective = document.metadata.get('objective', document.title) if document.metadata else document.title

        if blueprint:
            blueprint_config = _build_blueprint_config(blueprint)
            pdf_bytes = pdf_service.generate_pdf_from_blueprint(
                markdown_content=document.markdown_content,
                objective=objective,
                blueprint_config=blueprint_config
            )
        else:
            pdf_bytes = pdf_service.markdown_to_pdf(
                markdown_content=document.markdown_content,
                title=document.title
            )

        elapsed_gen = round(time.time() - t0, 1)
        logger.info(f"PDF gerado em memória: {document_id} ({elapsed_gen}s, {len(pdf_bytes)} bytes)")

    except Exception as e:
        logger.error(f"Erro ao gerar PDF {document_id}: {str(e)}")
        return Response({
            'error': f'Erro ao gerar PDF: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Upload para R2 via Celery (async com retry)
    from ..tasks import save_pdf_to_r2_task
    save_pdf_to_r2_task.delay(
        str(document_id),
        base64.b64encode(pdf_bytes).decode('ascii'),
        str(blueprint.id) if blueprint else None,
    )

    # Retornar PDF imediatamente ao frontend
    doc_type_prefix = blueprint.document_type.code if blueprint and blueprint.document_type else 'documento'
    filename = f"{doc_type_prefix}_{document_id}.pdf"

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@extend_schema(
    summary="Status do PDF do Documento",
    description="Retorna o status da geração do PDF (generating, ready, failed).",
    tags=["Assistente Inteligente - Documentos"],
    responses={
        200: OpenApiResponse(description="Status do PDF"),
        404: OpenApiResponse(description="Documento não encontrado")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_pdf_status(request, document_id):
    """
    Consulta status da geração do PDF.

    GET /api/v1/intelligent-assistant/documents/{document_id}/pdf-status/
    """
    try:
        document = GeneratedDocument.objects.get(
            id=document_id,
            session__user=request.user
        )
    except GeneratedDocument.DoesNotExist:
        return Response({
            'error': 'Documento não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    pdf_status = 'none'
    if document.metadata:
        pdf_status = document.metadata.get('pdf_status', 'none')

    # Se o PDF já foi gerado (campo legado), considerar ready
    if document.pdf_generated and document.pdf_url and pdf_status == 'none':
        pdf_status = 'ready'

    return Response({
        'status': pdf_status,
        'pdf_url': document.pdf_url if pdf_status == 'ready' else None,
        'pdf_generated': document.pdf_generated,
    })


@extend_schema(
    summary="Gerar DOCX do Documento",
    description="Converte o documento gerado para DOCX com estilização do blueprint.",
    tags=["Assistente Inteligente - Documentos"],
    responses={
        200: OpenApiResponse(description="Arquivo DOCX"),
        404: OpenApiResponse(description="Documento não encontrado"),
        500: OpenApiResponse(description="Erro na geração"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_document_docx(request, document_id):
    """
    Gera DOCX do documento, retorna os bytes imediatamente e
    faz upload para R2 em background.

    POST /api/v1/intelligent-assistant/documents/{document_id}/generate-docx/
    """
    import time
    from django.http import HttpResponse
    from django.core.files.base import ContentFile

    try:
        document = GeneratedDocument.objects.select_related('session').get(
            id=document_id,
            session__user=request.user
        )
    except GeneratedDocument.DoesNotExist:
        return Response({'error': 'Documento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    blueprint = None
    if document.session.blueprint_id:
        try:
            blueprint = DocumentBlueprint.objects.get(id=document.session.blueprint_id)
        except DocumentBlueprint.DoesNotExist:
            pass

    try:
        t0 = time.time()
        from ..services.document_export_service import DocumentExportService
        export_service = DocumentExportService()

        objective = document.metadata.get('objective', document.title) if document.metadata else document.title
        blueprint_config = _build_blueprint_config(blueprint) if blueprint else {}

        docx_bytes = export_service.generate_docx(
            markdown_content=document.markdown_content,
            objective=objective,
            blueprint_config=blueprint_config,
        )

        if not docx_bytes:
            return Response({'error': 'Falha ao gerar DOCX'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elapsed = round(time.time() - t0, 1)
        logger.info(f"DOCX gerado em memória: {document_id} ({elapsed}s, {len(docx_bytes)} bytes)")

    except Exception as e:
        logger.error(f"Erro ao gerar DOCX {document_id}: {str(e)}")
        return Response({'error': f'Erro ao gerar DOCX: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Upload para R2 em background
    # Upload para R2 via Celery (async com retry)
    from ..tasks import save_docx_to_r2_task
    save_docx_to_r2_task.delay(
        str(document_id),
        base64.b64encode(docx_bytes).decode('ascii'),
        str(blueprint.id) if blueprint else None,
    )

    doc_type_prefix = blueprint.document_type.code if blueprint and blueprint.document_type else 'doc'
    filename = f"{doc_type_prefix}_{document_id}.docx"

    response = HttpResponse(
        docx_bytes,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@extend_schema(
    summary="Gerar ODT do Documento",
    description="Converte o documento gerado para ODT com estilização do blueprint.",
    tags=["Assistente Inteligente - Documentos"],
    responses={
        200: OpenApiResponse(description="Arquivo ODT"),
        404: OpenApiResponse(description="Documento não encontrado"),
        500: OpenApiResponse(description="Erro na geração"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_document_odt(request, document_id):
    """
    Gera ODT do documento, retorna os bytes imediatamente e
    faz upload para R2 em background.

    POST /api/v1/intelligent-assistant/documents/{document_id}/generate-odt/
    """
    import threading
    import time
    from django.http import HttpResponse
    from django.core.files.base import ContentFile

    try:
        document = GeneratedDocument.objects.select_related('session').get(
            id=document_id,
            session__user=request.user
        )
    except GeneratedDocument.DoesNotExist:
        return Response({'error': 'Documento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    blueprint = None
    if document.session.blueprint_id:
        try:
            blueprint = DocumentBlueprint.objects.get(id=document.session.blueprint_id)
        except DocumentBlueprint.DoesNotExist:
            pass

    try:
        t0 = time.time()
        from ..services.document_export_service import DocumentExportService
        export_service = DocumentExportService()

        objective = document.metadata.get('objective', document.title) if document.metadata else document.title
        blueprint_config = _build_blueprint_config(blueprint) if blueprint else {}

        odt_bytes = export_service.generate_odt(
            markdown_content=document.markdown_content,
            objective=objective,
            blueprint_config=blueprint_config,
        )

        if not odt_bytes:
            return Response({'error': 'Falha ao gerar ODT'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elapsed = round(time.time() - t0, 1)
        logger.info(f"ODT gerado em memória: {document_id} ({elapsed}s, {len(odt_bytes)} bytes)")

    except Exception as e:
        logger.error(f"Erro ao gerar ODT {document_id}: {str(e)}")
        return Response({'error': f'Erro ao gerar ODT: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Upload para R2 em background
    def _save_odt_to_r2(doc_id, content, bp):
        try:
            t0 = time.time()
            doc = GeneratedDocument.objects.get(id=doc_id)
            doc_type_prefix = bp.document_type.code if bp and bp.document_type else 'doc'
            filename = f"{doc_type_prefix}_{doc_id}.odt"

            # ODT não tem campo dedicado - salvar na metadata
            if not doc.metadata:
                doc.metadata = {}
            doc.metadata['odt_status'] = 'ready'
            doc.metadata['odt_size'] = len(content)
            doc.save(update_fields=['metadata'])

            elapsed = round(time.time() - t0, 1)
            logger.info(f"[Background] ODT metadata salva: {filename} ({elapsed}s)")
        except Exception as e:
            logger.error(f"[Background] Erro ao salvar ODT metadata {doc_id}: {str(e)}")

    thread = threading.Thread(target=_save_odt_to_r2, args=(document_id, odt_bytes, blueprint), daemon=True)
    thread.start()

    doc_type_prefix = blueprint.document_type.code if blueprint and blueprint.document_type else 'doc'
    filename = f"{doc_type_prefix}_{document_id}.odt"

    response = HttpResponse(
        odt_bytes,
        content_type='application/vnd.oasis.opendocument.text'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
