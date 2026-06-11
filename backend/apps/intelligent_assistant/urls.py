"""
URLs do Assistente Inteligente - Verus.AI.
"""
from django.urls import path
from . import views

app_name = 'intelligent_assistant'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health'),

    # Sessões
    path('sessions/', views.create_session, name='create-session'),
    path('sessions/list/', views.list_sessions, name='list-sessions'),
    path('sessions/<uuid:session_id>/', views.get_session, name='get-session'),
    path('sessions/<uuid:session_id>/attachments/', views.list_session_attachments, name='list-session-attachments'),
    path('sessions/<uuid:session_id>/preview/', views.preview_session, name='preview-session'),
    path('sessions/<uuid:session_id>/delete/', views.delete_session, name='delete-session'),

    # Upload de Documentos
    path('sessions/<uuid:session_id>/upload/', views.upload_documents, name='upload-documents'),

    # Deletar Documento Gerado
    path('sessions/<uuid:session_id>/documents/<uuid:document_id>/', views.delete_generated_document, name='delete-generated-document'),

    # Confirmar revisão humana
    path('documents/<uuid:document_id>/confirm-review/', views.confirm_review, name='confirm-review'),

    # Listar placeholders não resolvidos
    path('documents/<uuid:document_id>/placeholders/', views.document_placeholders, name='document-placeholders'),

    # Atualizar Seções do Documento
    path('documents/<uuid:document_id>/update-sections/', views.update_document_sections, name='update-document-sections'),

    # Atualizar HTML do Documento (editor visual)
    path('documents/<uuid:document_id>/update-html/', views.update_document_html, name='update-document-html'),

    # Exportação de documentos (PDF, DOCX, ODT)
    path('documents/<uuid:document_id>/generate-pdf/', views.generate_document_pdf, name='generate-document-pdf'),
    path('documents/<uuid:document_id>/generate-docx/', views.generate_document_docx, name='generate-document-docx'),
    path('documents/<uuid:document_id>/generate-odt/', views.generate_document_odt, name='generate-document-odt'),
    path('documents/<uuid:document_id>/pdf-status/', views.get_document_pdf_status, name='document-pdf-status'),

    # Deletar Documento Enviado (Uploaded)
    path('sessions/<uuid:session_id>/uploaded-documents/<uuid:document_id>/', views.delete_uploaded_document, name='delete-uploaded-document'),

    # Busca Semântica
    path('sessions/<uuid:session_id>/search/', views.search_session, name='search-session'),

    # Feedback de Seções (auto-aprendizagem)
    path('section-feedback/', views.save_section_feedback, name='section-feedback'),

    # Knowledge Base
    path('knowledge-bases/', views.list_knowledge_bases, name='list-knowledge-bases'),
    path('knowledge-bases/search/', views.search_knowledge_base, name='search-knowledge-base'),

    # Knowledge Base Management
    path('knowledge-bases/manage/', views.manage_knowledge_bases, name='manage-kbs'),
    path('knowledge-bases/manage/<uuid:kb_id>/', views.manage_knowledge_base_detail, name='manage-kb-detail'),
    path('knowledge-bases/manage/<uuid:kb_id>/upload/', views.upload_to_knowledge_base, name='upload-to-kb'),
    path('knowledge-bases/manage/<uuid:kb_id>/sources/', views.list_kb_sources, name='list-kb-sources'),
    path('knowledge-bases/manage/<uuid:kb_id>/sources/<str:source_name>/', views.delete_kb_source, name='delete-kb-source'),
    path('knowledge-bases/manage/<uuid:kb_id>/files/', views.list_kb_source_files, name='list-kb-source-files'),
    path('knowledge-bases/manage/<uuid:kb_id>/files/<uuid:file_id>/', views.delete_kb_source_file, name='delete-kb-source-file'),
    path('knowledge-bases/stats/', views.kb_stats, name='kb-stats'),

    # Agent ↔ KB Links
    path('knowledge-bases/manage/<uuid:kb_id>/agent-links/', views.manage_kb_agent_links, name='manage-kb-agent-links'),
    path('knowledge-bases/manage/<uuid:kb_id>/agent-links/<uuid:link_id>/', views.manage_kb_agent_link_detail, name='manage-kb-agent-link-detail'),

    # Section Agents
    path('section-agents/', views.list_section_agents, name='list-section-agents'),

    # ========== BLUEPRINTS DINÂMICOS ==========

    path('blueprints/', views.list_blueprints, name='list-blueprints'),
    path('blueprints/create/', views.create_blueprint, name='create-blueprint'),
    path('blueprints/<uuid:blueprint_id>/', views.get_blueprint, name='get-blueprint'),
    path('blueprints/<uuid:blueprint_id>/update/', views.update_blueprint, name='update-blueprint'),
    path('blueprints/<uuid:blueprint_id>/delete/', views.delete_blueprint, name='delete-blueprint'),
    path('blueprints/<uuid:blueprint_id>/duplicate/', views.duplicate_blueprint, name='duplicate-blueprint'),
    path('blueprints/by-name/<str:blueprint_name>/', views.get_blueprint, name='get-blueprint-by-name'),
    path('blueprints/<uuid:blueprint_id>/sections/', views.list_blueprint_sections, name='list-blueprint-sections'),
    path('blueprints/<uuid:blueprint_id>/sections/create/', views.create_blueprint_section, name='create-blueprint-section'),
    path('blueprints/<uuid:blueprint_id>/sections/<uuid:section_id>/', views.update_blueprint_section, name='update-blueprint-section'),
    path('blueprints/<uuid:blueprint_id>/sections/<uuid:section_id>/delete/', views.delete_blueprint_section, name='delete-blueprint-section'),
    path('blueprints/<uuid:blueprint_id>/sections/reorder/', views.reorder_blueprint_sections, name='reorder-blueprint-sections'),
    path('blueprints/<uuid:blueprint_id>/agents/', views.list_blueprint_agents, name='list-blueprint-agents'),

    # Sub-seções CRUD
    path('sections/<uuid:section_id>/sub-sections/', views.create_sub_section, name='create-sub-section'),
    path('sub-sections/<uuid:sub_id>/', views.update_sub_section, name='update-sub-section'),
    path('sub-sections/<uuid:sub_id>/delete/', views.delete_sub_section, name='delete-sub-section'),

    # Agentes de seção
    path('agents/create/', views.create_section_agent, name='create-section-agent'),
    path('agents/<uuid:agent_id>/', views.get_section_agent, name='get-section-agent'),
    path('agents/<uuid:agent_id>/update/', views.update_section_agent, name='update-section-agent'),
    path('agents/<uuid:agent_id>/delete/', views.delete_section_agent, name='delete-section-agent'),
    path('agents/<uuid:agent_id>/execute/', views.execute_section_agent, name='execute-section-agent'),

    # Geração dinâmica com blueprint
    path('generate/', views.generate_etp_dynamic, name='generate'),
    path('generate-stream/', views.generate_etp_dynamic_stream, name='generate-stream'),
    path('regenerate-section-stream/', views.regenerate_section_stream, name='regenerate-section-stream'),

    # Sessões de geração dinâmica
    path('generation-sessions/', views.list_generation_sessions, name='list-generation-sessions'),
    path('generation-sessions/<uuid:session_id>/', views.get_generation_session, name='get-generation-session'),
    path('generation-sessions/<uuid:session_id>/cancel/', views.cancel_generation_session, name='cancel-gs'),

    # ========== VALIDAÇÃO PRÉ-GERAÇÃO ==========
    path('sessions/<uuid:session_id>/validate-inputs/', views.validate_session_inputs, name='validate-session-inputs'),

    # ========== AUDITORIA ==========
    path('sessions/<uuid:session_id>/audit-log/', views.session_audit_log, name='session-audit-log'),

    # ========== BUSCA DE JURISPRUDÊNCIA (Tavily) ==========
    path('jurisprudence/search/', views.jurisprudence_search, name='jurisprudence-search'),

    # ========== COPILOT JURÍDICO ==========
    path('copilot/suggest/', views.suggest_copilot, name='copilot-suggest'),
    path('copilot/commands/', views.list_copilot_commands, name='copilot-commands'),

    # ========== APRIMORAMENTO DE TEXTO COM IA ==========
    path('enhance-text/', views.enhance_text, name='enhance-text'),

    # ========== PREENCHIMENTO DE FORMULÁRIO VIA DOCUMENTO ==========
    path('fill-form-from-document/', views.fill_form_from_document, name='fill-form-from-document'),

    # ========== EXTRAÇÃO AUTOMÁTICA DE CAMPOS (PRÉ-PREENCHIMENTO) ==========
    path('sessions/<uuid:session_id>/extract-fields/', views.extract_fields_from_session, name='extract-fields'),

    # ========== BLUEPRINT COPILOT (CRIAÇÃO POR LINGUAGEM NATURAL) ==========
    path('blueprints/copilot/chat/', views.blueprint_copilot_chat, name='blueprint-copilot-chat'),
    path('blueprints/copilot/create/', views.blueprint_copilot_create, name='blueprint-copilot-create'),

    # ========== ADMIN: FIX ETP REFERENCES ==========
    path('admin/fix-etp/', views.fix_etp_references_api, name='fix-etp'),
    path('admin/fix-pmjp/', views.fix_pmjp_references_api, name='fix-pmjp'),
]
