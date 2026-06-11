"""
DocumentContextService — Extrai texto de uploads inline do Copilot.
Delega para DocumentProcessorService e formata para injeção no prompt.
"""
import logging

logger = logging.getLogger(__name__)

MAX_CHARS = 400_000


def extract_from_upload(uploaded_file) -> dict:
    """
    Extrai texto de um arquivo enviado via upload.
    Retorna o dict de resultado do DocumentProcessorService.

    Raises:
        ValueError: Se o arquivo não for suportado ou inválido.
    """
    from apps.intelligent_assistant.services.document_processor import DocumentProcessorService

    processor = DocumentProcessorService()
    return processor.process_uploaded_file(uploaded_file)


def format_for_prompt(result: dict) -> str:
    """
    Formata o resultado de extração para inclusão no prompt do Copilot.
    Trunca em MAX_CHARS para não estourar o contexto.
    """
    text: str = result.get('text', '') or ''
    filename: str = result.get('filename', 'documento')

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        logger.info(f'[copilot] Texto do upload truncado em {MAX_CHARS} chars')

    return (
        f'\n\n## DOCUMENTO ANEXADO: {filename}\n\n'
        f'{text.strip()}\n'
    )
