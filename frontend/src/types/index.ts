// ========== AUTH ==========
export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role:
    // Procuradoria roles (verus.ai — fonte de verdade: accounts/models.py ROLE_CHOICES)
    | 'superadmin' | 'admin'
    | 'procurador_geral' | 'subprocurador_geral'
    | 'gerente'
    | 'procurador'
    | 'assessor_gerencial' | 'assessor_gabinete'
    | 'distribuidor'
    | 'servidor'
    | 'visualizador'
    // Aliases BravoJus (ROLE_ALIASES — compatibilidade com dados legados)
    | 'socio' | 'advogado_senior' | 'advogado_pleno' | 'advogado_junior' | 'estagiario'
    | 'gestor' | 'coordenador' | 'supervisor'
    | 'analista' | 'assistente' | 'paralegal' | 'secretaria'
    | 'defensor' | 'promotor' | 'assessor'
    | 'revisor' | 'auditor'
    | 'cliente'
    // Aliases em inglês
    | 'manager' | 'reviewer' | 'analyst' | 'viewer';
  phone?: string;
  department?: string;
  position?: string;
  avatar?: string;
  oab_number?: string;
  oab_state?: string;
  lawyer_specialties?: string[];
  signature_image?: string | null;
  signature_name?: string;
  preferred_llm_provider?: 'openai' | 'anthropic' | 'watsonx';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

// ========== NOTIFICATIONS ==========
export interface Notification {
  id: number;
  type: 'deadline' | 'document' | 'case' | 'system' | 'simulation' | 'task';
  type_display: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  priority_display: string;
  title: string;
  message: string;
  link: string;
  is_read: boolean;
  created_at: string;
}

// ========== BRAND SETTINGS ==========
export interface BrandSettings {
  id: number;
  system_name: string;
  system_tagline?: string;
  logo?: string | null;
  logo_dark?: string | null;
  favicon?: string | null;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  created_at: string;
  updated_at: string;
  updated_by?: string | null;
  updated_by_name?: string | null;
}

export interface UpdateBrandSettingsData {
  system_name?: string;
  system_tagline?: string;
  logo?: File | string | null;
  logo_dark?: File | string | null;
  favicon?: File | string | null;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
}

// ========== FORMS ==========
export interface FormField {
  id: string;
  type: 'text' | 'textarea' | 'number' | 'email' | 'date' | 'select' | 'checkbox' | 'radio' | 'file' | 'array';
  label: string;
  required?: boolean;
  help_text?: string;
  placeholder?: string;
  options?: string[] | Array<{ value: string; label: string }>;
  ai_assist?: boolean;
  ai_prompt_types?: string[];
}

export interface SectionField {
  field_id: string;
  field_type: 'text' | 'textarea' | 'number' | 'email' | 'date' | 'select' | 'checkbox' | 'radio' | 'file' | 'array';
  field_name: string;
  required?: boolean;
  help_text?: string;
  placeholder?: string;
  options?: string[] | Array<{ value: string; label: string }>;
  ai_assist?: boolean;
  ai_prompt_types?: string[];
}

export interface FormSection {
  section_id: string;
  section_title: string;
  legal_basis?: string;
  fields: SectionField[];
}

// Agente do Blueprint (para Formulário Guiado)
export interface BlueprintAgent {
  id: string;
  name: string;
  type: 'generator' | 'validator';
  section_name: string;
  section_key: string;
  section_number: number;
}

export interface FormTemplate {
  id: string;
  name: string;
  description?: string;
  version: number;
  is_active: boolean;
  fields?: FormField[];
  sections?: FormSection[];
  // Blueprint vinculado ao formulário
  blueprint?: string;
  blueprint_name?: string;
  blueprint_agents?: BlueprintAgent[];
  // @deprecated Usar blueprint - mantido para compatibilidade
  document_generator?: string;
  document_generator_name?: string;
  has_generator_warning?: boolean;
  field_count?: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

// ========== TEMPLATES ==========
export interface DocumentTemplate {
  id: string;
  name: string;
  description?: string;
  content: string;
  rendered_content?: string;  // Conteúdo renderizado (extraído de .docx se necessário)
  custom_css?: string;
  template_type: 'html' | 'tinymce' | 'docx' | 'markdown';
  blueprint?: string;
  blueprint_name?: string;
  version: string;
  is_active: boolean;
  is_default?: boolean;
  placeholder_count?: number;
  has_file?: boolean;
  form_template?: string;
  form_template_name?: string;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

// ========== KNOWLEDGE BASE ==========
export interface Document {
  id: string;
  title: string;
  file: string;
  file_type: string;
  file_size: number;
  category: string;
  tags: string[];
  description?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  extracted_text?: string;
  metadata?: Record<string, any>;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document: string;
  content: string;
  chunk_index: number;
  metadata?: Record<string, any>;
}

export interface SearchResult {
  chunk_id: string;
  document_title: string;
  content: string;
  similarity: number;
  metadata?: Record<string, any>;
}

// ========== MANAGED KNOWLEDGE BASE ==========
export interface ManagedKnowledgeBase {
  id: string;
  name: string;
  description: string;
  kb_layer: 'global' | 'blueprint' | 'agent' | 'section_example';
  blueprint_id?: string | null;
  blueprint_name?: string | null;
  document_type_name?: string | null;
  agent_config_name?: string | null;
  sources_count: number;
  total_chunks: number;
  agent_links_count: number;
  is_active: boolean;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface KBSource {
  source_name: string;
  source_type: string;
  chunks_count: number;
  total_characters: number;
  created_at: string;
}

export interface KBManageResponse {
  knowledge_bases: ManagedKnowledgeBase[];
  global_kbs: ManagedKnowledgeBase[];
  blueprint_kbs: ManagedKnowledgeBase[];
  agent_kbs: ManagedKnowledgeBase[];
  total: number;
}

// ========== AGENT ↔ KB LINKS ==========
export type KBPurpose = 'examples' | 'evaluation' | 'normative' | 'context' | 'reference';

export interface AgentKnowledgeBaseLink {
  id: string;
  agent: string;
  agent_name: string;
  agent_type: string;
  priority: number;
  purpose: KBPurpose;
  purpose_display: string;
  instruction: string;
  top_k: number;
  min_similarity: number;
  include_summary: boolean;
  selected_sources: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SectionAgent {
  id: string;
  name: string;
  agent_type: string;
  is_active: boolean;
  blueprint_name: string | null;
  context_label: string | null;
  agent_scope: 'section' | 'sub_section' | 'unlinked';
}

export interface SectionAgentConfigDetail {
  id: string;
  name: string;
  description: string;
  agent_type: 'generator' | 'validator' | 'analyzer' | 'refiner';
  system_prompt: string;
  user_prompt_template: string;
  llm_provider: 'anthropic' | 'openai' | 'watsonx';
  model_name: string;
  temperature: number;
  max_tokens: number;
  use_rag: boolean;
  rag_query_template: string;
  rag_top_k: number;
  rag_similarity_threshold: number;
  is_active: boolean;
  is_default: boolean;
  variable_count: number;
  variables: string[];
  created_at: string;
  updated_at: string;
  linked_sections: Array<{
    section_id: string;
    section_number: number;
    section_name: string;
    role: 'generator' | 'validator';
  }>;
  linked_sub_sections: Array<{
    sub_section_id: string;
    sub_number: string;
    sub_name: string;
    parent_section_number: number;
    parent_section_name: string;
    role: 'generator';
  }>;
}

export interface BlueprintAgentsResponse {
  blueprint_id: string;
  blueprint_name: string;
  agents: SectionAgentConfigDetail[];
  total: number;
}

// ========== AGENTS ==========
export interface AgentPrompt {
  id: string;
  name: string;
  description?: string;

  // Tipo de agente chat
  agent_type: string;  // Subtipo específico do chat (ex: especialista_licitacoes, consultor_juridico, analista_tecnico)

  // Customização visual
  icon: string;  // Nome do ícone Lucide (ex: Bot, FileText, Mail)
  color: string;  // Cor em hex (ex: #3b82f6)
  display_order: number;  // Ordem de exibição (menor = primeiro)

  // Prompts e configuração LLM
  system_prompt: string;
  user_prompt_template: string;
  llm_provider: 'openai' | 'anthropic' | 'watsonx';
  provider_display: string;  // Nome amigável do provider (read-only)
  model_name: string;
  temperature: number;
  max_tokens: number;

  // RAG
  use_rag: boolean;
  rag_query_template?: string;

  // Status e flags
  is_active: boolean;
  is_default: boolean;

  // Metadados
  variable_count: number;  // Contagem de variáveis no template (read-only)
  created_by?: string;  // ID do usuário criador
  created_by_name?: string;  // Nome do usuário criador (read-only)
  created_at: string;
  updated_at: string;
}

export interface AgentExecution {
  agent_name: string;
  input_variables: Record<string, any>;
  response: string;
  tokens_used: number;
  execution_time_ms: number;
  provider: string;
  model: string;
}

// Estatísticas de agentes (endpoint /stats/)
export interface AgentStats {
  total: number;
  active: number;
  inactive: number;
  by_category: {
    form_assistant: { count: number; active: number };
    chat_assistant: { count: number; active: number };
    document_generator: { count: number; active: number };
  };
  by_provider: {
    openai: { count: number; active: number };
    anthropic: { count: number; active: number };
  };
}

// Resposta do endpoint /by_category/
export interface AgentsByCategory {
  form_assistant: {
    name: string;
    code: string;
    count: number;
    agents: AgentPrompt[];
  };
  chat_assistant: {
    name: string;
    code: string;
    count: number;
    agents: AgentPrompt[];
  };
  document_generator: {
    name: string;
    code: string;
    count: number;
    agents: AgentPrompt[];
  };
}

// ========== Documents ==========
// @deprecated - use LegalDocument (renomeação em andamento)
export interface ETP {
  id: string;
  title: string;
  numero_processo?: string;
  form_template: string;
  document_template: string;
  data: Record<string, any>;
  progress: number;
  status: 'rascunho' | 'em_analise' | 'aprovado' | 'rejeitado' | 'finalizado';
  version: number;
  generated_content?: string;
  generated_html?: string;
  metadata?: Record<string, any>;
  created_by: string;
  reviewed_by?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// @deprecated - use LegalDocumentVersion (renomeação em andamento)
export interface ETPVersion {
  id: string;
  etp: string;
  version_number: number;
  data: Record<string, any>;
  changes_summary?: string;
  created_by: string;
  created_at: string;
}

// ========== RAG ==========
export interface RAGQuery {
  id: string;
  user: string;
  query_text: string;
  retrieved_chunks: SearchResult[];
  llm_response: string;
  llm_provider: string;
  model_name: string;
  total_tokens: number;
  search_time_ms: number;
  llm_time_ms: number;
  created_at: string;
}

export interface RAGContext {
  id: string;
  name: string;
  description?: string;
  document_filters: {
    category?: string;
    tags?: string[];
    document_ids?: string[];
  };
  llm_config: {
    provider: string;
    model: string;
    temperature: number;
    max_tokens: number;
  };
  is_active: boolean;
  created_by: string;
  created_at: string;
}

// ========== BLUEPRINTS (Sistema Dinâmico de Geração) ==========
// Campos estruturados de uma seção do Blueprint
export interface BlueprintSectionField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'tel' | 'number' | 'date' | 'select' | 'textarea' | 'richtext' | 'array';
  required?: boolean;
  placeholder?: string;
  help_text?: string;
  options?: Array<{ value: string; label: string }>;
  // Para tipo 'textarea' / 'richtext' - controla altura
  rows?: number;
  height?: number;
  // Para tipo 'richtext' - HTML pre-populado quando o campo esta vazio
  // (seed inicial; usuario pode editar/apagar livremente apos carregar)
  default_html?: string;
  // Valor padrao generico - pre-popula qualquer tipo (text, select, date, etc).
  // O usuario pode aceitar ou substituir ao gerar.
  default_value?: any;
  // Para tipo 'array' - campos de cada item
  min_items?: number;
  max_items?: number;
  item_fields?: BlueprintSectionField[];
  item_label?: string;
}

export interface BlueprintSubSection {
  id: string;
  sub_number: string;
  sub_name: string;
  sub_key: string;
  description?: string;
  help_text?: string;
  default_text?: string;
  generator_agent_id?: string | null;
  generator_agent_name?: string | null;
  section_fields?: BlueprintSectionField[];
  order: number;
  is_required: boolean;
  is_active: boolean;
}

export interface SubSectionDecision {
  action: 'generate' | 'default';
  fields_data: Record<string, any>;
  feedback?: string;
}

export interface BlueprintSection {
  id: string;
  section_number: number;
  section_name: string;
  section_key: string;
  description?: string;
  instructions?: string;
  legal_reference?: string;
  section_fields?: BlueprintSectionField[];
  sub_sections?: BlueprintSubSection[];
  order: number;
  is_required: boolean;
  allow_skip: boolean;
  max_generation_attempts?: number;
  is_active: boolean;
  generator_agent_id?: string | null;
  generator_agent_name?: string;
  validator_agent_id?: string | null;
  validator_agent_name?: string;
  generator_agent?: { id: string; name: string; agent_type: string };
  validator_agent?: { id: string; name: string; agent_type: string };
  depends_on_ids?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface BlueprintArea {
  code: string;
  name: string;
}

export interface DocumentBlueprint {
  id: string;
  name: string;
  description?: string;
  document_type: string;
  document_type_id?: string;
  document_type_code: string;
  document_type_display: string;
  areas: BlueprintArea[];
  version: string;
  legal_basis?: string;
  section_count: number;
  is_active: boolean;
  is_default: boolean;
  sections?: BlueprintSection[];
  created_by_name?: string;
  created_at: string;
  updated_at?: string;
  // PDF Customization
  organization_name?: string;
  organization_acronym?: string;
  header_text?: string;
  footer_text?: string;
  cover_page_enabled?: boolean;
  cover_title?: string;
  cover_subtitle?: string;
  cover_organization_text?: string;
  cover_footer_text?: string;
  cover_background_color?: string;
  pdf_font_family?: string;
  pdf_font_size?: number;
  pdf_line_height?: number;
  pdf_text_align?: string;
  pdf_paragraph_indent?: string;
  pdf_paragraph_spacing?: string;
  pdf_page_margin_top?: string;
  pdf_page_margin_bottom?: string;
  pdf_page_margin_left?: string;
  pdf_page_margin_right?: string;
  primary_color?: string;
  secondary_color?: string;
  custom_css?: string;
  metadata?: Record<string, any>;
}

export interface BlueprintListResponse {
  blueprints: DocumentBlueprint[];
  total: number;
}

export interface BlueprintSectionsResponse {
  blueprint_id: string;
  blueprint_name: string;
  sections: BlueprintSection[];
  total: number;
}

// @deprecated - use GenerateDocumentRequest (renomeação em andamento)
export interface GenerateETPDynamicRequest {
  objective: string;
  blueprint_id?: string;
  blueprint_name?: string;
  collection_name?: string;
  section_ids?: string[];
}

export interface GeneratedSectionContent {
  section_number: number;
  section_name: string;
  content: string;
  is_valid: boolean;
}

// @deprecated - use GenerateDocumentResponse (renomeação em andamento)
export interface GenerateETPDynamicResponse {
  success: boolean;
  session_id: string;
  blueprint: {
    id: string;
    name: string;
    section_count: number;
  };
  sections: Record<string, GeneratedSectionContent>;
  stats: {
    total_sections: number;
    generated_sections: number;
  };
}

// ========== API RESPONSES ==========
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface APIError {
  detail?: string;
  error?: string;
  [key: string]: any;
}

// ========== ANALYTICS ==========
export interface AssistantAnalytics {
  id: string;
  date: string;
  total_conversations: number;
  total_messages: number;
  unique_users: number;
  avg_messages_per_conversation: number;
  avg_response_time_ms: number;
  total_tokens_used: number;
  total_kb_queries: number;
  total_feedbacks: number;
  positive_feedbacks: number;
  negative_feedbacks: number;
  satisfaction_rate: number;
  incorrect_count: number;
  incomplete_count: number;
  irrelevant_count: number;
  unclear_count: number;
  outdated_count: number;
  calculated_at: string;
}

export interface AnalyticsSummary {
  total_conversations: number;
  total_messages: number;
  total_feedbacks: number;
  positive_feedbacks: number;
  negative_feedbacks: number;
  avg_satisfaction: number;
  total_tokens: number;
  avg_response_time: number;
}

export interface AnalyticsChartData {
  date: string;
  total_conversations: number;
  total_messages: number;
  satisfaction_rate: number;
  total_feedbacks: number;
  total_tokens_used?: number;
}

export interface AnalyticsPeriod {
  start: string;
  end: string;
  days: number;
}

export interface AnalyticsSummaryResponse {
  summary: AnalyticsSummary;
  chart_data: AnalyticsChartData[];
  feedback_timeline: FeedbackTimelineData[];
  period: AnalyticsPeriod;
}

export interface FeedbackTimelineData {
  date: string;
  positive_feedbacks: number;
  negative_feedbacks: number;
}

export interface WordCloudWord {
  text: string;
  value: number;
}

export interface WordCloudData {
  input_words: WordCloudWord[];
  output_words: WordCloudWord[];
  period: AnalyticsPeriod;
  total_messages_analyzed: {
    input: number;
    output: number;
  };
}

// ========== SIMULATIONS ==========
export interface SimulationResultSummary {
  // Judge
  dispositivo?: 'procedente' | 'improcedente' | 'parcialmente_procedente';
  judge_name?: string;
  // Jury
  verdict?: 'condenacao' | 'absolvicao';
  deliberation_votes?: { condenacao: number; absolvicao: number };
  confidence_level?: number;
  probabilities?: Record<string, number>;
}

export interface Simulation {
  id: string;
  simulation_type: 'jury' | 'judge' | 'stf' | 'acordao_2inst' | 'stj' | 'jec' | 'jecrim' | 'jef' | 'turma_recursal' | 'trabalho' | 'trt' | 'tst' | 'eleitoral' | 'tre' | 'tse' | 'militar' | 'stm';
  title: string;
  description?: string;
  status: 'draft' | 'configuring' | 'running' | 'deliberating' | 'completed' | 'failed';
  case?: string;
  case_title?: string;
  config?: Record<string, any>;
  result?: Record<string, any>;
  result_summary?: SimulationResultSummary;
  is_deleted?: boolean;
  documents_count?: number;
  jury_members_count?: number;
  created_at: string;
  updated_at: string;
}

export interface JuryMember {
  id: string;
  name: string;
  age: number;
  gender: string;
  profession: string;
  education: string;
  personality_traits: string[];
  background: string;
  vote?: 'guilty' | 'not_guilty';
  reasoning?: string;
}

export interface JudgeProfile {
  id: string;
  name: string;
  state: string;
  court: string;
  comarca: string;
  tendencies?: string;
  decision_patterns?: string;
  total_decisions?: number;
  approval_rate?: number;
}

export interface Court {
  id: string;
  name: string;
  court_type: string;
  state: string;
  comarcas: string[];
}

export interface MinisterProfile {
  id: string;
  court_type: 'STF' | 'STJ' | 'TJ' | 'TRT' | 'TST' | 'TSE' | 'STM' | 'TRE';
  name: string;
  full_name: string;
  appointed_by: string;
  turma: string;
  judicial_philosophy: 'progressista' | 'conservador' | 'centrista' | 'pragmatico';
  specialty_areas: string[];
  notable_positions: string[];
  profile_data: Record<string, any>;
  is_active: boolean;
}

// ========== TIMESHEET / CONTROLE DE HORAS ==========
export interface TimeEntry {
  id: string;
  caso: string;
  caso_titulo?: string;
  caso_numero_processo?: string;
  advogado: string;
  advogado_nome?: string;
  date: string;
  hours: number;
  description: string;
  billing_type: 'billable' | 'non_billable' | 'pro_bono';
  billing_type_display?: string;
  hourly_rate?: number | null;
  total_value?: number | null;
  task?: string | null;
  task_titulo?: string | null;
  is_approved: boolean;
  approved_by?: string | null;
  approved_at?: string | null;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface TimesheetMonthlyReport {
  lawyer_id: string;
  year: number;
  month: number;
  summary: {
    total_hours: number;
    billable_hours: number;
    non_billable_hours: number;
    pro_bono_hours: number;
    total_value: number;
    entries_count: number;
    avg_hourly_rate: number;
    utilization_rate: number;
  };
  by_case: Array<{
    caso__id: string;
    caso__titulo: string;
    caso__numero_processo: string;
    hours: number;
    value: number;
    entries: number;
  }>;
  by_day: Array<{
    date: string;
    hours: number;
    entries: number;
  }>;
}

// ========== CRM / PIPELINE DE LEADS ==========
export interface LeadStage {
  id: string;
  name: string;
  order: number;
  color: string;
  is_won: boolean;
  is_lost: boolean;
  leads_count?: number;
  created_at: string;
}

export interface Lead {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  cpf_cnpj?: string;
  description?: string;
  specialty?: string;
  specialty_display?: string;
  source: 'indicacao' | 'site' | 'google' | 'instagram' | 'whatsapp' | 'telefone' | 'evento' | 'outro';
  source_display?: string;
  temperature: 'cold' | 'warm' | 'hot';
  temperature_display?: string;
  stage?: string | null;
  stage_name?: string;
  stage_color?: string;
  estimated_value?: number | null;
  responsible?: string | null;
  responsible_name?: string;
  converted_client?: string | null;
  converted_case?: string | null;
  converted_at?: string | null;
  next_contact_date?: string | null;
  notes?: string;
  intake_form_data?: Record<string, any>;
  activities?: LeadActivity[];
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface LeadActivity {
  id: string;
  lead: string;
  activity_type: 'call' | 'email' | 'meeting' | 'whatsapp' | 'proposal' | 'note' | 'stage_change';
  activity_type_display?: string;
  description: string;
  created_by?: string;
  created_by_name?: string;
  created_at: string;
}

export interface LeadPipelineData {
  stages: LeadStage[];
  leads_by_stage: Record<string, Lead[]>;
  total_leads: number;
  total_value: number;
  conversion_rate: number;
}

// ========== KPIs GAMIFICADOS ==========
export interface LawyerScore {
  id: string;
  lawyer: string;
  lawyer_name?: string;
  period_start: string;
  period_end: string;
  cases_won: number;
  cases_lost: number;
  cases_settled: number;
  deadlines_met: number;
  deadlines_missed: number;
  tasks_completed: number;
  hours_logged: number;
  documents_generated: number;
  revenue_generated: number;
  client_satisfaction?: number | null;
  total_score: number;
  rank_position?: number | null;
  badges: Badge[];
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface Leaderboard {
  rank: number;
  lawyer_id: string;
  lawyer_name: string;
  total_score: number;
  cases_won: number;
  deadlines_met: number;
  deadlines_missed: number;
  tasks_completed: number;
  hours_logged: number;
  revenue_generated: number;
  badges: Badge[];
}

// ========== CONFLITO DE INTERESSES ==========
export interface ConflictCheckResult {
  has_conflicts: boolean;
  total_conflicts: number;
  severity: 'none' | 'warning' | 'critical';
  conflicts: ConflictDetail[];
  oab_reference: string;
  total_cases_checked?: number;
  total_clients_checked?: number;
  total_adverse_parties_checked?: number;
  criteria_used?: string[];
  search_scope?: string[];
}

export interface ConflictDetail {
  type: 'cpf_cnpj_match' | 'name_similarity' | 'reverse_conflict';
  severity: 'warning' | 'critical';
  similarity?: number;
  case_id: string;
  case_titulo: string;
  numero_processo?: string;
  parte_contraria?: string;
  advogado?: string | null;
  client_name?: string;
  existing_client?: string;
  message: string;
}

// ========== OCR ==========
export interface OCRResult {
  success: boolean;
  text: string;
  pages?: number;
  method?: 'text_extraction' | 'ocr_tesseract';
  confidence?: number;
  filename?: string;
  file_size?: number;
  error?: string;
}

// ========== NFS-e (NOTA FISCAL) ==========
export interface InvoiceNFSe {
  id: string;
  caso?: string | null;
  caso_titulo?: string;
  client: string;
  client_name?: string;
  contract?: string | null;
  numero_nfse: string;
  codigo_verificacao: string;
  status: 'draft' | 'pending' | 'processing' | 'authorized' | 'cancelled' | 'error';
  status_display?: string;
  descricao_servico: string;
  codigo_servico: string;
  codigo_tributacao?: string;
  valor_servico: number;
  valor_deducoes: number;
  base_calculo?: number;
  aliquota_iss: number;
  valor_iss?: number;
  valor_liquido?: number;
  irrf: number;
  pis: number;
  cofins: number;
  csll: number;
  inss: number;
  data_emissao?: string | null;
  data_competencia: string;
  municipio_prestacao: string;
  pdf_url?: string;
  error_message?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

// ========== INTEGRAÇÃO ASSINATURA DIGITAL ==========
export interface DigitalSignatureProvider {
  provider: 'd4sign' | 'docusign' | 'govbr';
  is_configured: boolean;
  setup_required?: boolean;
  env_vars?: string[];
}

export interface SignatureRequest {
  document_id: string;
  provider: 'd4sign' | 'docusign' | 'govbr';
  signers: Array<{
    name: string;
    email: string;
    cpf?: string;
    routing_order?: number;
  }>;
  message?: string;
}

export interface SignatureStatus {
  provider: string;
  document_id: string;
  status: 'pending' | 'sent' | 'signed' | 'cancelled' | 'error';
  signers_status?: Array<{
    name: string;
    email: string;
    signed: boolean;
    signed_at?: string;
  }>;
}

// ========== INTEGRAÇÃO TRIBUNAIS (PJe/e-SAJ) ==========
export interface TribunalIntegrationStatus {
  pje: {
    is_configured: boolean;
    supported_tribunals: string[];
  };
  esaj: {
    is_configured: boolean;
    supported_tribunals: string[];
  };
}

// ========== CALENDAR SYNC ==========
export interface CalendarSyncProvider {
  provider: 'google' | 'outlook';
  name: string;
  is_configured: boolean;
  auth_url?: string;
  setup_required?: boolean;
  env_vars?: string[];
}

export interface CalendarSyncResult {
  provider: string;
  total_events: number;
  events_synced: number;
  errors: string[];
}

// ========== PETIÇÃO POR IA ==========
export interface PetitionType {
  id: string;
  name: string;
  sections: string[];
}

export interface PetitionResult {
  success: boolean;
  petition_type: string;
  petition_name: string;
  case_id: string;
  case_titulo: string;
  content: string;
  tokens_used: number;
  sections: string[];
  error?: string;
}

// ========== BLUEPRINT COPILOT ==========
export interface BlueprintCopilotRequest {
  user_request: string;
  conversation_history?: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
}

export interface BlueprintCopilotResponse {
  success: boolean;
  action: 'clarify' | 'generate';
  message?: string;
  questions?: Array<{
    id: string;
    question: string;
    options?: string[];
  }>;
  blueprint?: {
    name: string;
    description: string;
    document_type: string;
    version: string;
    legal_basis?: string;
    organization_name?: string;
    sections: Array<{
      order: number;
      title: string;
      description: string;
      is_required: boolean;
      field_type: string;
      agent_config: {
        agent_type: string;
        system_prompt: string;
        temperature: number;
        max_tokens: number;
        required_inputs: string[];
        output_format: string;
      };
      typography: {
        font_family: string;
        font_size: number;
        alignment: string;
        heading_style?: string;
      };
    }>;
    pdf_config: {
      page_size: string;
      margins: { top: number; bottom: number; left: number; right: number };
      header_text?: string;
      footer_text?: string;
      include_cover?: boolean;
      include_toc?: boolean;
      numbering_style?: string;
    };
  };
  tokens_used?: number;
  error?: string;
}

// ========== KANBAN DE TAREFAS ==========
export interface KanbanColumn {
  id: string;
  title: string;
  status: 'pendente' | 'em_andamento' | 'concluida' | 'cancelada';
  color: string;
  tasks: KanbanTask[];
}

// ========== AVALIACAO DE RISCO ==========
export interface RiskAssessment {
  id: string;
  caso: string;
  risk_level: 'very_low' | 'low' | 'medium' | 'high' | 'very_high' | 'critical';
  risk_level_display?: string;
  risk_score: number;
  factors: Array<{ name: string; weight: number; description: string }>;
  analysis: string;
  recommendation?: string;
  trigger?: string;
  previous_level?: string;
  previous_level_display?: string;
  level_changed: boolean;
  ai_generated: boolean;
  assessed_by_name?: string;
  created_at: string;
}

export interface CopilotContextRequest {
  context_type: 'tribunal' | 'datajud' | 'prazo' | 'risco' | 'calendario';
  context_data: Record<string, any>;
  question: string;
}

export interface CopilotContextResponse {
  answer: string;
  tokens_used: number;
  context_type: string;
}

export interface KanbanTask {
  id: string;
  caso: string;
  caso_titulo?: string;
  titulo: string;
  descricao?: string;
  status: 'pendente' | 'em_andamento' | 'concluida' | 'cancelada';
  prioridade: 'baixa' | 'media' | 'alta' | 'urgente';
  responsavel?: string | null;
  responsavel_nome?: string;
  data_limite?: string | null;
  data_conclusao?: string | null;
  created_at: string;
}

