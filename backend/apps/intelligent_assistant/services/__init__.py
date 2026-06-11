"""
Serviços do Assistente Inteligente.

Este módulo contém:
- ClaudeService: Wrapper para API do Claude (Anthropic)
- DocumentProcessorService: Processa e extrai texto de PDFs/DOCX
- KnowledgeBaseService: Gerencia Knowledge Base usando PgVector (Singleton)
- PgVectorService: Serviço de embeddings usando PostgreSQL + pgvector
"""
from .claude_service import ClaudeService
from .document_processor import DocumentProcessorService
from .knowledge_base_service import KnowledgeBaseService
from .pgvector_service import PgVectorService

__all__ = [
    'ClaudeService',
    'DocumentProcessorService',
    'KnowledgeBaseService',
    'PgVectorService',
]
