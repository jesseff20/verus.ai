"""
Models para o Assistente Inteligente de Documentos.

Re-exporta todos os modelos dos sub-módulos para manter compatibilidade
com imports existentes: `from .models import X` continua funcionando.
"""

# 1. Agentes (sem dependências internas)
from .agent import SectionAgentConfig

# 2. Knowledge Base (depende de SectionAgentConfig via FK string)
from .knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseEmbedding,
    KBSourceFile,
    AgentKnowledgeBaseLink,
)

# 3. Blueprints (depende de SectionAgentConfig via FK string)
from .blueprint import (
    DocumentBlueprint,
    BlueprintSection,
    SectionImportConfig,
    BlueprintSubSection,
)

# 4. Pipeline (depende de BlueprintSection, SectionAgentConfig)
from .pipeline import (
    SectionPipelineStep,
    GenerationSession,
    SectionGeneration,
)

# 5. Sessão legada e documentos
from .session import (
    IntelligentSession,
    UploadedDocument,
    GeneratedSection,
    GeneratedDocument,
    DocumentEmbedding,
    SectionGenerationLog,
)

# 6. Feedback
from .feedback import SectionFeedback

# 7. Auditoria
from .audit import LLMAuditLog

# 8. Agent Tools
from .agent_tools import AgentTool, AgentToolLink

__all__ = [
    # Agent
    'SectionAgentConfig',
    # Knowledge Base
    'KnowledgeBase',
    'KnowledgeBaseEmbedding',
    'KBSourceFile',
    'AgentKnowledgeBaseLink',
    # Blueprint
    'DocumentBlueprint',
    'BlueprintSection',
    'SectionImportConfig',
    'BlueprintSubSection',
    # Pipeline
    'SectionPipelineStep',
    'GenerationSession',
    'SectionGeneration',
    # Session
    'IntelligentSession',
    'UploadedDocument',
    'GeneratedSection',
    'GeneratedDocument',
    'DocumentEmbedding',
    'SectionGenerationLog',
    # Feedback
    'SectionFeedback',
    # Audit
    'LLMAuditLog',
    # Agent Tools
    'AgentTool',
    'AgentToolLink',
]
