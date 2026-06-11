"""
Celery tasks para o intelligent_assistant.

Tasks assíncronas para upload de documentos gerados ao R2.
"""
import base64
import logging
import time

from celery import shared_task
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def save_pdf_to_r2_task(self, doc_id, content_b64, blueprint_id=None):
    """
    Salva PDF gerado no Cloudflare R2 e atualiza o documento.

    Args:
        doc_id: UUID do GeneratedDocument
        content_b64: bytes do PDF em base64
        blueprint_id: UUID do blueprint (opcional, para nome do arquivo)
    """
    from apps.intelligent_assistant.models import GeneratedDocument, DocumentBlueprint

    try:
        t0 = time.time()
        doc = GeneratedDocument.objects.get(id=doc_id)
        content = base64.b64decode(content_b64)

        doc_type_prefix = 'etp'
        if blueprint_id:
            try:
                bp = DocumentBlueprint.objects.get(id=blueprint_id)
                doc_type_prefix = bp.document_type if bp.document_type else 'etp'
            except DocumentBlueprint.DoesNotExist:
                pass

        filename = f"{doc_type_prefix}_{doc_id}.pdf"

        doc.pdf_file.save(filename, ContentFile(content), save=False)
        doc.file_size_pdf = len(content)
        doc.pdf_generated = True
        if doc.pdf_file:
            doc.pdf_url = doc.pdf_file.url
        if not doc.metadata:
            doc.metadata = {}
        doc.metadata['pdf_status'] = 'ready'
        doc.save(update_fields=['pdf_file', 'file_size_pdf', 'pdf_generated', 'pdf_url', 'metadata'])

        elapsed = round(time.time() - t0, 1)
        logger.info(f"[Celery] PDF salvo no R2: {filename} ({elapsed}s)")

    except GeneratedDocument.DoesNotExist:
        logger.error(f"[Celery] Documento {doc_id} não encontrado")
    except Exception as exc:
        logger.error(f"[Celery] Erro ao salvar PDF {doc_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def save_docx_to_r2_task(self, doc_id, content_b64, blueprint_id=None):
    """
    Salva DOCX gerado no Cloudflare R2 e atualiza o documento.

    Args:
        doc_id: UUID do GeneratedDocument
        content_b64: bytes do DOCX em base64
        blueprint_id: UUID do blueprint (opcional, para nome do arquivo)
    """
    from apps.intelligent_assistant.models import GeneratedDocument, DocumentBlueprint

    try:
        t0 = time.time()
        doc = GeneratedDocument.objects.get(id=doc_id)
        content = base64.b64decode(content_b64)

        doc_type_prefix = 'doc'
        if blueprint_id:
            try:
                bp = DocumentBlueprint.objects.get(id=blueprint_id)
                doc_type_prefix = bp.document_type if bp.document_type else 'doc'
            except DocumentBlueprint.DoesNotExist:
                pass

        filename = f"{doc_type_prefix}_{doc_id}.docx"

        doc.docx_file.save(filename, ContentFile(content), save=False)
        doc.file_size_docx = len(content)
        doc.docx_generated = True
        if doc.docx_file:
            doc.docx_url = doc.docx_file.url
        if not doc.metadata:
            doc.metadata = {}
        doc.metadata['docx_status'] = 'ready'
        doc.save(update_fields=['docx_file', 'file_size_docx', 'docx_generated', 'docx_url', 'metadata'])

        elapsed = round(time.time() - t0, 1)
        logger.info(f"[Celery] DOCX salvo no R2: {filename} ({elapsed}s)")

    except GeneratedDocument.DoesNotExist:
        logger.error(f"[Celery] Documento {doc_id} não encontrado")
    except Exception as exc:
        logger.error(f"[Celery] Erro ao salvar DOCX {doc_id}: {exc}")
        raise self.retry(exc=exc)
