"""
Celery tasks para processamento assíncrono de documentos
"""
from celery import shared_task
import logging
from .models import Document
from .services import DocumentProcessingService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """
    Task Celery para processar documento em background

    Args:
        document_id: UUID do documento
    """
    try:
        logger.info(f"=== Iniciando processamento do documento {document_id} ===")

        document = Document.objects.get(id=document_id)

        # Processar documento (extrai texto, cria chunks, gera embeddings)
        chunk_count = DocumentProcessingService.process_document(document)

        logger.info(f"=== Documento {document_id} processado com sucesso ===")
        logger.info(f"Chunks criados: {chunk_count}")
        logger.info(f"Texto extraído: {len(document.extracted_text)} caracteres")

        return {
            'document_id': str(document_id),
            'status': 'completed',
            'chunk_count': chunk_count,
            'text_length': len(document.extracted_text)
        }

    except Document.DoesNotExist:
        logger.error(f"Documento {document_id} não encontrado")
        raise

    except Exception as e:
        logger.error(f"Erro ao processar documento {document_id}: {str(e)}")

        # Marcar documento como failed
        try:
            document = Document.objects.get(id=document_id)
            document.status = 'failed'
            document.processing_error = str(e)
            document.save()
        except Exception as e:
            logger.warning(f"Falha ao marcar documento {document_id} como failed: {e}")

        # Retry com backoff exponencial
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
