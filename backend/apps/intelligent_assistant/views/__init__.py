"""
Views do Assistente Inteligente - organizadas por domínio.

Re-exporta todas as views para manter compatibilidade com urls.py
(from . import views → views.health_check, views.create_session, etc.)
"""

# Health
from .health import health_check

# Sessões
from .session_views import (
    create_session,
    list_sessions,
    list_session_attachments,
    preview_session,
    get_session,
    delete_session,
)

# Upload e deleção de documentos
from .upload_views import (
    upload_documents,
    delete_generated_document,
    delete_uploaded_document,
)

# Busca semântica
from .search_views import (
    search_session,
    list_knowledge_bases,
    search_knowledge_base,
)

# Feedback de seções
from .feedback_views import save_section_feedback

# Documentos (atualização + exportação)
from .document_views import (
    update_document_sections,
    update_document_html,
    generate_document_pdf,
    get_document_pdf_status,
    generate_document_docx,
    generate_document_odt,
)

# Geração de documentos (dinâmico, streaming)
from .generation_views import (
    generate_etp_dynamic,
    generate_etp_dynamic_stream,
    regenerate_section_stream,
    cancel_generation_session,
)

# Sessões de geração dinâmica
from .generation_session_views import (
    list_generation_sessions,
    get_generation_session,
)

# Blueprints CRUD
from .blueprint_views import (
    list_blueprints,
    get_blueprint,
    list_blueprint_sections,
    create_blueprint,
    update_blueprint,
    delete_blueprint,
    duplicate_blueprint,
    create_blueprint_section,
    update_blueprint_section,
    delete_blueprint_section,
    reorder_blueprint_sections,
    create_sub_section,
    update_sub_section,
    delete_sub_section,
)

# Agentes de seção
from .agent_views import (
    list_blueprint_agents,
    get_section_agent,
    update_section_agent,
    create_section_agent,
    delete_section_agent,
    execute_section_agent,
    list_section_agents,
)

# Knowledge Base Management
from .kb_views import (
    manage_knowledge_bases,
    manage_knowledge_base_detail,
    upload_to_knowledge_base,
    list_kb_sources,
    delete_kb_source,
    kb_stats,
    list_kb_source_files,
    delete_kb_source_file,
    manage_kb_agent_links,
    manage_kb_agent_link_detail,
)

# Copilot Jurídico
from .copilot_views import (
    suggest_copilot,
    list_copilot_commands,
    blueprint_copilot_chat,
    blueprint_copilot_create,
)

# Aprimoramento de texto genérico com IA
from .enhance_views import enhance_text

# Preenchimento de formulário a partir de documento
from .fill_form_views import fill_form_from_document

# Extração automática de campos a partir de documentos da sessão
from .extract_fields_views import extract_fields_from_session

# Validação pré-geração e auditoria
from .validation_views import (
    validate_session_inputs,
    session_audit_log,
    jurisprudence_search,
    confirm_review,
    document_placeholders,
)

# Admin utility
from .admin_utils import fix_etp_references_api, fix_pmjp_references_api
