"""
Views para upload e deleção de documentos.
"""
import logging
import threading

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db import transaction

from ..models import IntelligentSession, UploadedDocument, GeneratedDocument
from ..services.document_processor import DocumentProcessorService
from ..services.pgvector_service import PgVectorService

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Upload de Documentos para Sessão",
    description="""
    Faz upload de documentos para uma sessão do assistente.

    O sistema:
    1. Recebe os arquivos (PDF, DOCX, TXT)
    2. Extrai o texto de cada documento
    3. Divide em chunks
    4. Gera embeddings usando OpenAI
    5. Armazena no PostgreSQL (pgvector)

    **Formatos suportados:** PDF, DOCX, TXT
    **Tamanho máximo:** 50MB por arquivo
    """,
    tags=["Assistente Inteligente - Documentos"],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'files': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'binary'},
                    'description': 'Arquivos para upload (PDF, DOCX, TXT)'
                }
            }
        }
    },
    responses={
        200: OpenApiResponse(description="Documentos processados com sucesso"),
        400: OpenApiResponse(description="Erro no upload ou processamento"),
        404: OpenApiResponse(description="Sessão não encontrada")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_documents(request, session_id):
    """
    Upload e processamento de documentos para uma sessão.

    Fluxo otimizado:
    1. Lê arquivos em memória
    2. Extrai texto em memória (~1s)
    3. Cria UploadedDocument SEM arquivo no R2 (insert rápido no DB)
    4. Gera embeddings (~2s)
    5. Retorna resposta ao usuário (~3s total)
    6. Thread background sobe arquivos para R2 (invisível)

    POST /api/v1/intelligent-assistant/sessions/{session_id}/upload/
    """
    # Verificar sessão
    try:
        session = IntelligentSession.objects.get(
            id=session_id,
            user=request.user
        )
    except IntelligentSession.DoesNotExist:
        return Response({
            'error': 'Sessão não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)

    # Verificar arquivos
    files = request.FILES.getlist('files')
    if not files:
        return Response({
            'error': 'Nenhum arquivo enviado',
            'detail': 'Envie ao menos um arquivo no campo "files"'
        }, status=status.HTTP_400_BAD_REQUEST)

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    for f in files:
        if f.size > MAX_FILE_SIZE:
            return Response({
                'error': f'Arquivo "{f.name}" excede o limite de 50 MB ({f.size // (1024*1024)} MB).'
            }, status=status.HTTP_400_BAD_REQUEST)

    # Atualizar status da sessão
    session.status = 'uploading'
    session.save()

    # Processar documentos
    doc_processor = DocumentProcessorService()
    pgvector_service = PgVectorService()

    processed_docs = []
    errors = []
    # Lista de (doc_id, file_content, filename) para upload R2 em background
    r2_upload_queue = []

    for uploaded_file in files:
        try:
            # Ler arquivo em memória antes de tudo
            file_content = uploaded_file.read()
            uploaded_file.seek(0)

            with transaction.atomic():
                # 1. Processar arquivo e extrair texto (em memória, ~1s)
                logger.info(f"[Upload Debug] INÍCIO process_uploaded_file: {uploaded_file.name}")
                extraction = doc_processor.process_uploaded_file(uploaded_file)
                logger.info(f"[Upload Debug] FIM process_uploaded_file: {extraction.get('num_chunks', '?')} chunks, {extraction.get('char_count', '?')} chars")

                # 2. Criar UploadedDocument SEM arquivo (evita R2 de ~60s)
                logger.info(f"[Upload Debug] Criando UploadedDocument...")
                doc = UploadedDocument.objects.create(
                    session=session,
                    # file omitido - upload R2 em background
                    filename=extraction['filename'],
                    file_type=extraction['file_type'],
                    file_size=extraction['size'],
                    extracted_text=extraction['text'],
                    extraction_status='completed'
                )

                # 3. Gerar embeddings e salvar no pgvector (~2s)
                logger.info(f"[Upload Debug] Iniciando embeddings (process_document)...")
                num_embeddings = pgvector_service.process_document(
                    document=doc,
                    session=session
                )

                processed_docs.append({
                    'id': str(doc.id),
                    'filename': doc.filename,
                    'file_type': doc.file_type,
                    'file_size': doc.file_size,
                    'char_count': extraction['char_count'],
                    'word_count': extraction['word_count'],
                    'num_chunks': extraction['num_chunks'],
                    'num_embeddings': num_embeddings,
                    'warnings': extraction.get('warnings', [])
                })

                # Enfileirar para upload R2 em background
                r2_upload_queue.append((str(doc.id), file_content, extraction['filename']))

        except ValueError as e:
            logger.warning(f"Upload rejeitado ({uploaded_file.name}): {str(e)}")
            errors.append({
                'filename': uploaded_file.name,
                'error': str(e)
            })
        except Exception as e:
            logger.error(f"Erro inesperado no upload ({uploaded_file.name}): {str(e)}")
            errors.append({
                'filename': uploaded_file.name,
                'error': f'Erro inesperado: {str(e)}'
            })

    # Atualizar status da sessão
    if processed_docs:
        session.status = 'processing' if not errors else 'initialized'
    else:
        session.status = 'failed'
        session.error_message = 'Nenhum documento foi processado com sucesso'
    session.save()

    # Upload dos arquivos para R2 em background thread
    if r2_upload_queue:
        def _upload_files_to_r2(queue):
            """Thread que sobe os arquivos para R2 sem bloquear o usuário."""
            import time
            from django.core.files.base import ContentFile
            for doc_id, content, filename in queue:
                try:
                    t0 = time.time()
                    doc = UploadedDocument.objects.get(id=doc_id)
                    doc.file.save(filename, ContentFile(content), save=True)
                    elapsed = round(time.time() - t0, 1)
                    logger.info(f"[Background] R2 upload concluído: {filename} ({elapsed}s)")
                except Exception as e:
                    logger.error(f"[Background] Erro R2 upload {doc_id}: {str(e)}")

        thread = threading.Thread(
            target=_upload_files_to_r2,
            args=(r2_upload_queue,),
            daemon=True,
        )
        thread.start()
        logger.info(f"[Background] R2 upload iniciado para {len(r2_upload_queue)} arquivo(s)")

    # Resposta (retorna em ~3s)
    response_data = {
        'success': len(processed_docs) > 0,
        'processed': processed_docs,
        'total_processed': len(processed_docs),
        'errors': errors if errors else None
    }

    http_status = status.HTTP_200_OK if processed_docs else status.HTTP_400_BAD_REQUEST
    return Response(response_data, status=http_status)


@extend_schema(
    summary="Deletar Documento Gerado",
    description="Remove um documento gerado específico de uma sessão",
    tags=["Assistente Inteligente - Documentos"],
    responses={
        204: OpenApiResponse(description="Documento removido"),
        404: OpenApiResponse(description="Documento não encontrado")
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_generated_document(request, session_id, document_id):
    """
    Remove um documento gerado de uma sessão.

    DELETE /api/v1/intelligent-assistant/sessions/{session_id}/documents/{document_id}/
    """
    try:
        # Verificar se a sessão pertence ao usuário
        session = IntelligentSession.objects.get(
            id=session_id,
            user=request.user
        )
    except IntelligentSession.DoesNotExist:
        return Response({
            'error': 'Sessão não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        document = GeneratedDocument.objects.get(
            id=document_id,
            session=session
        )
    except GeneratedDocument.DoesNotExist:
        return Response({
            'error': 'Documento não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    # Guardar referência do PDF para deletar do R2 em background
    pdf_to_delete = document.pdf_file if document.pdf_file else None

    # Apagar todas as GenerationSessions vinculadas (e SectionGenerations via CASCADE)
    gs_qs = session.generation_sessions.all()
    gs_count = gs_qs.count()
    if gs_count:
        logger.info(f"Removendo {gs_count} GenerationSession(s) vinculadas à sessão {session.id}")
        gs_qs.delete()

    # Deletar documento do banco
    document.delete()

    logger.info(f"Documento {document_id} removido da sessão {session_id}")

    # Deletar PDF do R2 em background
    if pdf_to_delete:
        def _delete_pdf_from_r2(file_field):
            try:
                file_field.delete(save=False)
                logger.info(f"[Background] PDF deletado do R2: {file_field.name}")
            except Exception as e:
                logger.warning(f"[Background] Erro ao deletar PDF do R2: {str(e)}")

        threading.Thread(target=_delete_pdf_from_r2, args=(pdf_to_delete,), daemon=True).start()

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Deletar Documento Enviado",
    description="Remove um documento enviado (uploaded) e seus embeddings associados",
    tags=["Assistente Inteligente - Documentos"],
    responses={
        204: OpenApiResponse(description="Documento removido"),
        404: OpenApiResponse(description="Documento não encontrado")
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_uploaded_document(request, session_id, document_id):
    """
    Remove um documento enviado (UploadedDocument) e seus embeddings.

    DELETE /api/v1/intelligent-assistant/sessions/{session_id}/uploaded-documents/{document_id}/
    """
    try:
        session = IntelligentSession.objects.get(
            id=session_id,
            user=request.user
        )
    except IntelligentSession.DoesNotExist:
        return Response({
            'error': 'Sessão não encontrada'
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        document = UploadedDocument.objects.get(
            id=document_id,
            session=session
        )
    except UploadedDocument.DoesNotExist:
        return Response({
            'error': 'Documento não encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    # Guardar referência do arquivo para deletar do R2 em background
    file_to_delete = document.file if document.file else None

    # Deletar documento do banco (cascade deleta DocumentEmbedding associados)
    document.delete()

    logger.info(f"Documento enviado {document_id} removido da sessão {session_id}")

    # Deletar arquivo do R2 em background (não bloqueia a resposta)
    if file_to_delete:
        def _delete_from_r2(file_field):
            try:
                file_field.delete(save=False)
                logger.info(f"[Background] Arquivo deletado do R2: {file_field.name}")
            except Exception as e:
                logger.warning(f"[Background] Erro ao deletar arquivo do R2: {str(e)}")

        threading.Thread(target=_delete_from_r2, args=(file_to_delete,), daemon=True).start()

    return Response(status=status.HTTP_204_NO_CONTENT)
