"""
URLs do app Cases — Gestão de Casos Jurídicos.
"""
from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    # Casos
    path('', views.cases_list_create, name='cases-list'),
    path('<uuid:case_id>/', views.case_detail, name='case-detail'),

    # Prazos de um caso
    path('<uuid:case_id>/prazos/', views.deadlines_list_create, name='case-deadlines'),
    path('<uuid:case_id>/tarefas/', views.tasks_list_create, name='case-tasks'),
    path('<uuid:case_id>/documentos/', views.case_documents_list_create, name='case-documents'),

    # Fases processuais
    path('<uuid:case_id>/phases/', views.case_phases_list, name='case-phases'),
    path('<uuid:case_id>/phases/<uuid:phase_id>/', views.case_phase_update, name='case-phase-update'),

    # Audiências de um caso
    path('<uuid:case_id>/audiencias/', views.case_audiencias, name='case-audiencias'),
    path('<uuid:case_id>/audiencias/<uuid:audiencia_id>/', views.audiencia_detail, name='audiencia-detail'),

    # Notificações jurídicas de um caso
    path('<uuid:case_id>/notificacoes/', views.case_notifications_list_create, name='case-notifications'),
    path('<uuid:case_id>/notificacoes/<uuid:notif_id>/', views.notification_detail, name='notification-detail'),

    # Movimentações financeiras de um caso
    path('<uuid:case_id>/movimentacoes/', views.case_movimentacoes, name='case-movimentacoes'),
    path('<uuid:case_id>/movimentacoes/<uuid:mov_id>/', views.movimentacao_detail, name='movimentacao-detail'),

    # Checklist por tipo de ação (#14)
    path('<uuid:case_id>/checklist/', views.case_checklist, name='case-checklist'),

    # Prazos globais (todos os casos do usuário)
    path('prazos/', views.deadlines_list_create, name='all-deadlines'),
    path('prazos/<uuid:deadline_id>/', views.deadline_detail, name='deadline-detail'),

    # Prazos recursais (#6)
    path('prazos/calcular-recursal/', views.calcular_prazo_recursal, name='calcular-prazo-recursal'),
    path('prazos/tipos-recurso/', views.tipos_recurso_list, name='tipos-recurso'),

    # Tarefas globais
    path('tarefas/<uuid:task_id>/', views.task_detail, name='task-detail'),

    # Activity log
    path('<uuid:case_id>/atividades/', views.case_activity_log, name='case-activity-log'),

    # Timeline do caso (todos os eventos vinculados)
    path('<uuid:case_id>/timeline/', views.case_timeline, name='case-timeline'),

    # Vincular documento gerado ao caso
    path('link-document/', views.link_document_to_case, name='link-document-to-case'),

    # Stats
    path('stats/', views.cases_stats, name='cases-stats'),

    # Aprimoramento de texto com IA
    path('enhance-text/', views.enhance_case_text, name='enhance-case-text'),

    # Extração de dados do caso com IA (a partir de petição/documento)
    path('extract-case-data/', views.extract_case_data, name='extract-case-data'),

    # Extração de dados a partir de arquivo PDF/DOCX/ODT/TXT
    path('extract-from-document/', views.extract_case_from_document, name='extract-case-from-document'),

    # Dashboard Financeiro
    path('financeiro/dashboard/', views.financial_dashboard, name='financial-dashboard'),

    # Tabela OAB de Honorários
    path('honorarios/tabela/', views.oab_fee_table_list, name='oab-fee-table'),
    path('honorarios/calcular/', views.oab_fee_calculate, name='oab-fee-calculate'),

    # Protocolo Eletrônico (#1)
    path('protocolos/', views.protocols_list_create, name='protocols-list'),
    path('protocolos/<uuid:protocol_id>/', views.protocol_detail, name='protocol-detail'),
    path('protocolos/<uuid:protocol_id>/submit/', views.protocol_submit, name='protocol-submit'),
    path('protocolos/<uuid:protocol_id>/check-status/', views.protocol_check_status, name='protocol-check-status'),
    path('protocolos/stats/', views.protocol_statistics, name='protocol-statistics'),

    # Tribunal Push (#5)
    path('tribunal-push/configs/', views.tribunal_push_configs_list_create, name='tribunal-push-configs'),
    path('tribunal-push/configs/<uuid:config_id>/', views.tribunal_push_config_detail, name='tribunal-push-config-detail'),
    path('tribunal-push/configs/<uuid:config_id>/check-now/', views.tribunal_push_check_now, name='tribunal-push-check-now'),
    path('tribunal-push/events/', views.tribunal_push_events_list, name='tribunal-push-events'),
    path('tribunal-push/events/<uuid:event_id>/mark-processed/', views.tribunal_push_event_mark_processed, name='tribunal-push-mark-processed'),

    # Contratos Jurídicos (#8, #9, #10)
    path('contratos/', views.contracts_list_create, name='contracts-list'),
    path('contratos/gerar/', views.contract_generate, name='contract-generate'),
    path('contratos/upload-analyze/', views.contract_upload_analyze, name='contract-upload-analyze'),
    path('contratos/stats/', views.contract_statistics, name='contract-statistics'),
    path('contratos/<uuid:contract_id>/', views.contract_detail, name='contract-detail'),
    path('contratos/<uuid:contract_id>/assinar/', views.contract_mark_signed, name='contract-sign'),

    # Guias de Custas (#11)
    path('custas/', views.court_fees_list_create, name='court-fees-list'),
    path('custas/calcular/', views.court_fee_calculate, name='court-fee-calculate'),
    path('custas/resumo/', views.court_fee_summary, name='court-fee-summary'),
    path('custas/<uuid:fee_id>/', views.court_fee_detail, name='court-fee-detail'),
    path('custas/<uuid:fee_id>/pagar/', views.court_fee_mark_paid, name='court-fee-mark-paid'),

    # Assinatura Digital (#12)
    path('assinaturas/', views.signatures_list_create, name='signatures-list'),
    path('assinaturas/<uuid:signature_id>/verificar/', views.signature_verify, name='signature-verify'),

    # Calendário (#15)
    path('calendario/events/', views.calendar_events, name='calendar-events'),
    path('calendario/proximos/', views.calendar_upcoming, name='calendar-upcoming'),
    path('calendario/atrasados/', views.calendar_overdue, name='calendar-overdue'),

    # Relatórios (#13)
    path('relatorios/caso/<uuid:case_id>/', views.report_case_progress, name='report-case-progress'),
    path('relatorios/portfolio/', views.report_portfolio, name='report-portfolio'),
    path('relatorios/kpis/', views.report_kpis, name='report-kpis'),

    # Workflow Automatizado (#18)
    path('workflows/templates/', views.workflow_templates_list_create, name='workflow-templates-list'),
    path('workflows/templates/<uuid:template_id>/', views.workflow_template_detail, name='workflow-template-detail'),
    path('workflows/', views.workflow_executions_list_create, name='workflow-executions-list'),
    path('workflows/<uuid:execution_id>/', views.workflow_execution_detail, name='workflow-execution-detail'),
    path('workflows/<uuid:execution_id>/avancar/', views.workflow_advance_step, name='workflow-advance-step'),

    # Integração CNJ DataJud (#2)
    path('datajud/buscar/', views.datajud_search, name='datajud-search'),
    path('datajud/sync/<uuid:case_id>/', views.datajud_sync, name='datajud-sync'),
    path('datajud/movimentacoes/', views.datajud_movimentacoes, name='datajud-movimentacoes'),

    # Controle de Prazos Inteligente (#17)
    path('prazos/inteligente/analise/', views.smart_deadline_analysis, name='smart-deadline-analysis'),
    path('prazos/inteligente/<uuid:deadline_id>/sugestoes/', views.smart_deadline_suggest, name='smart-deadline-suggest'),
    path('prazos/inteligente/<uuid:case_id>/risco/', views.smart_deadline_risk, name='smart-deadline-risk'),

    # Copilot Prazos (#115)
    path('prazos/copilot/calcular/', views.copilot_calculate_deadline, name='copilot-calculate-deadline'),
    path('prazos/copilot/estrategia/', views.copilot_suggest_strategy, name='copilot-suggest-strategy'),
    path('prazos/copilot/agrupar/', views.copilot_group_deadlines, name='copilot-group-deadlines'),
    path('prazos/copilot/criticos/', views.copilot_critical_deadlines, name='copilot-critical-deadlines'),

    # Importação em Massa (#21)
    path('importar/casos/', views.import_cases_csv, name='import-cases-csv'),
    path('importar/clientes/', views.import_clients_csv, name='import-clients-csv'),
    path('importar/template/', views.import_template, name='import-template'),

    # Exportação de Dados (#22)
    path('exportar/casos/', views.export_cases, name='export-cases'),
    path('exportar/clientes/', views.export_clients, name='export-clients'),
    path('exportar/prazos/', views.export_deadlines, name='export-deadlines'),

    # Mensagens Cliente-Advogado
    path('mensagens-clientes/', views.client_messages_list, name='client-messages-list'),
    path('mensagens-clientes/responder/', views.client_message_reply, name='client-message-reply'),
    path('mensagens-clientes/marcar-lidas/', views.client_messages_mark_read, name='client-messages-mark-read'),
    path('mensagens-clientes/nao-lidas/', views.client_messages_unread_count, name='client-messages-unread'),

    # Atividade do Portal do Cliente
    path('atividade-portal/', views.client_portal_activity, name='client-portal-activity'),

    # ========== TIMESHEET / CONTROLE DE HORAS ==========
    path('timesheet/', views.time_entries_list_create, name='timesheet-list'),
    path('timesheet/<uuid:entry_id>/', views.time_entry_detail, name='timesheet-detail'),
    path('timesheet/<uuid:entry_id>/aprovar/', views.time_entry_approve, name='timesheet-approve'),
    path('timesheet/relatorio-mensal/', views.timesheet_monthly_report, name='timesheet-monthly-report'),
    path('<uuid:case_id>/timesheet/', views.time_entries_list_create, name='case-timesheet'),
    path('<uuid:case_id>/timesheet/honorarios/', views.timesheet_case_honorarios, name='case-timesheet-honorarios'),

    # ========== COPILOT TIMESHEET ==========
    path('timesheet/copilot/sugerir/', views.copilot_timesheet_suggest, name='copilot-timesheet-suggest'),
    path('timesheet/copilot/descricao/', views.copilot_timesheet_description, name='copilot-timesheet-description'),
    path('timesheet/copilot/detectar/', views.copilot_timesheet_detect, name='copilot-timesheet-detect'),
    path('timesheet/copilot/otimizar/', views.copilot_timesheet_optimize, name='copilot-timesheet-optimize'),

    # ========== VERIFICAÇÃO DE CONFLITO DE INTERESSES ==========
    path('conflito-interesses/', views.check_conflict_of_interest, name='check-conflict'),

    # ========== CRM / PIPELINE DE LEADS ==========
    path('crm/stages/', views.lead_stages_list_create, name='crm-stages'),
    path('crm/leads/', views.leads_list_create, name='crm-leads'),
    path('crm/leads/<uuid:lead_id>/', views.lead_detail, name='crm-lead-detail'),
    path('crm/leads/<uuid:lead_id>/atividade/', views.lead_add_activity, name='crm-lead-activity'),
    path('crm/leads/<uuid:lead_id>/converter/', views.lead_convert, name='crm-lead-convert'),
    path('crm/pipeline/', views.lead_pipeline, name='crm-pipeline'),

    # ========== COPILOT CRM ==========
    path('copilot/classificar-lead/', views.copilot_classify_lead, name='copilot-classify-lead'),
    path('copilot/followup-lead/', views.copilot_generate_followup, name='copilot-followup-lead'),
    path('copilot/prever-conversao/', views.copilot_predict_conversion, name='copilot-predict-conversion'),

    # ========== COPILOT CLIENTES ==========
    path('copilot/extrair-dados-cliente/', views.copilot_extract_client_data, name='copilot-extract-client-data'),
    path('copilot/conflito-cliente/', views.copilot_check_client_conflict, name='copilot-check-client-conflict'),
    path('copilot/sugerir-honorarios/', views.copilot_suggest_client_fees, name='copilot-suggest-client-fees'),

    # ========== KPIs GAMIFICADOS ==========
    path('kpis/leaderboard/', views.kpi_leaderboard, name='kpi-leaderboard'),
    path('kpis/recalcular/', views.kpi_recalculate, name='kpi-recalculate'),
    path('kpis/meus-scores/', views.kpi_my_scores, name='kpi-my-scores'),

    # ========== OCR DE DOCUMENTOS ==========
    path('ocr/extrair/', views.ocr_extract_text, name='ocr-extract'),

    # ========== PETIÇÃO POR IA ==========
    path('peticao-ia/gerar/', views.generate_petition, name='petition-generate'),
    path('peticao-ia/tipos/', views.petition_types_list, name='petition-types'),

    # ========== KANBAN DE TAREFAS ==========
    path('kanban/', views.tasks_kanban, name='tasks-kanban'),
    path('kanban/<uuid:task_id>/mover/', views.task_move, name='task-move'),

    # ========== NFS-e (NOTA FISCAL) ==========
    path('nfse/', views.nfse_list_create, name='nfse-list'),
    path('nfse/<uuid:nfse_id>/', views.nfse_detail, name='nfse-detail'),
    path('nfse/<uuid:nfse_id>/emitir/', views.nfse_emit, name='nfse-emit'),

    # ========== INTEGRAÇÃO ASSINATURA DIGITAL ==========
    path('assinatura-digital/providers/', views.signature_providers_status, name='signature-providers'),

    # ========== INTEGRAÇÃO CALENDÁRIO ==========
    path('calendario/sync/providers/', views.calendar_sync_providers, name='calendar-sync-providers'),

    # ========== INTEGRAÇÃO TRIBUNAIS ==========
    path('tribunais/status/', views.tribunal_integration_status, name='tribunal-status'),

    # ========== HISTÓRICO DE AVALIAÇÃO DE RISCO ==========
    path('<uuid:case_id>/risco/historico/', views.risk_assessments_list_create, name='risk-history'),
    path('<uuid:case_id>/risco/avaliar-ia/', views.risk_assessment_ai, name='risk-ai'),

    # ========== COPILOT CONTEXTUAL ==========
    path('copilot/analisar/', views.copilot_analyze_context, name='copilot-context'),

    # ========== COPILOT DOCUMENTOS ==========
    path('copilot/gerar-documento/', views.copilot_generate_document, name='copilot-generate-document'),
    path('copilot/revisar-documento/', views.copilot_review_document, name='copilot-review-document'),
    path('copilot/sugerir-template/', views.copilot_suggest_template, name='copilot-suggest-template'),
    path('copilot/auto-preencher/', views.copilot_auto_fill, name='copilot-auto-fill'),

    # ========== COPILOT EQUIPE — Sugestão de Alocação ==========
    path('copilot/equipe/sugerir/', views.copilot_team_suggest, name='copilot-team-suggest'),
    path('copilot/equipe/balancear/', views.copilot_team_balance, name='copilot-team-balance'),
    path('copilot/equipe/disponibilidade/', views.copilot_team_availability, name='copilot-team-availability'),
    path('copilot/equipe/match-especialidade/', views.copilot_team_match_specialty, name='copilot-team-match-specialty'),

    # ========== COPILOT TRIBUNAL PUSH ==========
    path('copilot/tribunal-push/analisar/', views.copilot_analyze_movement, name='copilot-analyze-movement'),
    path('copilot/tribunal-push/sugerir-acoes/', views.copilot_suggest_actions, name='copilot-suggest-actions'),
    path('copilot/tribunal-push/resumir/', views.copilot_summarize_publication, name='copilot-summarize'),
    path('copilot/tribunal-push/classificar/', views.copilot_classify_relevance, name='copilot-classify-relevance'),

    # ========== FASE 4 — CNJ Parser + Fluxo por Processo ==========
    path('cnj/parse/', views.cnj_parse, name='cnj-parse'),
    path('<uuid:case_id>/iniciar-fluxo/', views.case_start_flow, name='case-start-flow'),
]

# ========== ViewSets (DRY alternative — v2) ==========
# As rotas function-based acima sao mantidas para compatibilidade retroativa.
# Os ViewSets abaixo oferecem a mesma funcionalidade via endpoints /v2/.
from rest_framework.routers import DefaultRouter
from .viewsets import TimeEntryViewSet, LeadStageViewSet, LeadViewSet, RiskAssessmentViewSet

router = DefaultRouter()
router.register(r'v2/timesheet', TimeEntryViewSet, basename='v2-timesheet')
router.register(r'v2/crm/stages', LeadStageViewSet, basename='v2-crm-stages')
router.register(r'v2/crm/leads', LeadViewSet, basename='v2-crm-leads')
router.register(r'v2/risk-assessments', RiskAssessmentViewSet, basename='v2-risk')

urlpatterns += router.urls
