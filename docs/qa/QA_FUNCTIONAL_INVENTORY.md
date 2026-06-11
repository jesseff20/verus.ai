# QA Functional Inventory — verus.ai

**Versão:** 1.0.0
**Data:** 2026-06-11
**Escopo:** Auditoria funcional completa da plataforma verus.ai para procuradorias públicas brasileiras
**Ambiente:** Next.js 14 (frontend) + Django 5.0 / DRF (backend)

---

## Sumário

1. [Módulos Identificados](#1-módulos-identificados)
2. [Funcionalidades por Módulo](#2-funcionalidades-por-módulo)
3. [Rotas Front-end](#3-rotas-front-end)
4. [Endpoints Back-end](#4-endpoints-back-end)
5. [Entidades e Dados](#5-entidades-e-dados)
6. [Integrações Externas](#6-integrações-externas)
7. [Controle de Acesso e Hierarquia de Roles](#7-controle-de-acesso-e-hierarquia-de-roles)
8. [Módulos Desativados / Parcialmente Implementados](#8-módulos-desativados--parcialmente-implementados)

---

## 1. Módulos Identificados

| # | App Django | Namespace API | Descrição Funcional | Status |
|---|------------|---------------|---------------------|--------|
| 1 | `accounts` | `/api/v1/auth/` | Usuários, autenticação JWT, roles, notificações, LGPD, e-mail templates, dashboard config, reminders | Ativo |
| 2 | `cases` | `/api/v1/processos/` | Gestão de processos jurídicos, prazos, tarefas, audiências, contratos, custas, CRM, timesheet, KPIs, OCR, Kanban, NFS-e, importação/exportação, DataJud | Ativo |
| 3 | `workflow_definition` | `/api/v1/workflows/` | Definição de fluxos BPMN (FlowTemplate, FlowNode, FlowEdge, FlowVersion) | Ativo |
| 4 | `workflow_execution` | `/api/v1/workflow-execution/` | Execução de fluxos em runtime (FlowInstance, TaskInstance, TaskRequest, ExecutionEvent) | Ativo |
| 5 | `signature` | `/api/v1/signatures/` | Assinaturas digitais com 6 providers (interno RSA + Gov.BR + ICP-Brasil + DocuSign + Certisign + SERPRO) | Ativo |
| 6 | `organization` | `/api/v1/organization/` | Multi-tenancy por Órgão (Organ) e Unidade (Unit) | Ativo |
| 7 | `agents` | `/api/v1/agents/` | Configuração de agentes de IA (prompts editáveis, LLM provider, KB links) | Ativo |
| 8 | `intelligent_assistant` | `/api/v1/intelligent-assistant/` | Assistente de geração de documentos via blueprints dinâmicos, ETP, sessões, streaming SSE | Ativo |
| 9 | `documents` | `/api/v1/documents/` | Documentos jurídicos (LegalDocument/ETP), versionamento semântico, geradores com IA | Ativo |
| 10 | `forms` | `/api/v1/forms/` | Formulários dinâmicos (FormTemplate, FormSection, FormField, FormAssistant) | Ativo |
| 11 | `templates` | `/api/v1/templates/` | Templates de documento (HTML, TinyMCE, DOCX, Markdown) com placeholders | Ativo |
| 12 | `kb` | `/api/v1/kb/` | Base de conhecimento: upload de documentos, embeddings, busca legislativa | Ativo |
| 13 | `rag` | `/api/v1/rag/` | RAG queries e contextos (pgvector, similaridade semântica) | Ativo |
| 14 | `collaboration` | `/api/v1/collaboration/` | Edição colaborativa em tempo real, comentários, sugestões | Ativo |
| 15 | `jurisprudence` | `/api/v1/jurisprudence/` | Pesquisa de jurisprudência, radar de precedentes, streaming, scraping | Ativo |
| 16 | `copilot` | `/api/v1/copilot/` | Assistente conversacional (chat stream, sessões, compartilhamento, exportação) | Ativo |
| 17 | `legal_library` | `/api/v1/legal-library/` | Biblioteca de argumentos jurídicos reutilizáveis, coleções, métricas de eficácia | Ativo |
| 18 | `simulations` | `/api/v1/simulations/` | Simulações de julgamento: júri, juiz, STF, STJ, JEC, JECRIM, trabalhista, eleitoral, militar | Ativo |
| 19 | `core` | `/api/v1/core/` | Tipos de documento/processo, auditoria de acessos, provedores LLM, uso de tokens | Ativo |
| 20 | `financeiro` | *(desativado)* | Módulo financeiro — desativado para procuradorias | Desativado |
| 21 | `integration` | `/api/v1/integration/` | Integração com tribunais (e-SAJ, PJe, Eproc, Projudi), sincronização processual | Ativo |

> **Nota:** O app `integration` (21) não foi listado nos 20 originais mas existe no codebase como app independente. O módulo `financeiro` (20) está desativado conforme comentário no `config/urls.py`.

---

## 2. Funcionalidades por Módulo

### 2.1 accounts — Autenticação e Usuários

**CRUD principal:**
- Criar, listar, editar, desativar usuários (`/api/v1/auth/users/`)
- Gerenciar perfis (OAB, assinatura digitalizada, especialidades, avatar)

**Ações especiais:**
- Login com JWT (`POST /api/v1/auth/login/`)
- Refresh de token (`POST /api/v1/auth/token/refresh/`)
- Logout (`POST /api/v1/auth/logout/`)
- Confirmação de e-mail (`GET /api/v1/auth/email-confirm/<token>/`)
- Reset de senha
- LGPD: consentimentos, solicitações de acesso/exclusão (`/api/v1/auth/lgpd/`)
- Gestão de equipes (`/api/v1/auth/equipes/`)
- Dashboard configurável por usuário (`/api/v1/auth/dashboard-config/`)
- Templates de e-mail (`/api/v1/auth/email-templates/`)
- Notificações (`/api/v1/auth/notifications/`)
- Reminders pessoais (`/api/v1/auth/reminders/`)
- Canais de notificação (`/api/v1/auth/notification-channels/`)
- Configurações de marca/brand (`/api/v1/auth/brand-settings/`)
- Portal do cliente — acesso separado (`/api/v1/auth/client-portal/`)

### 2.2 cases — Gestão de Processos (core do sistema)

**CRUD de entidades:**
- Processos/casos (`/api/v1/processos/`)
- Clientes (`/api/v1/processos/` — modelo `Client`)
- Prazos (`/api/v1/processos/prazos/`)
- Tarefas (`/api/v1/processos/tarefas/`)
- Documentos do caso (`/api/v1/processos/<id>/documentos/`)
- Audiências (`/api/v1/processos/<id>/audiencias/`)
- Movimentações financeiras (`/api/v1/processos/<id>/movimentacoes/`)
- Contratos (`/api/v1/processos/contratos/`)
- Custas judiciais (`/api/v1/processos/custas/`)
- Timesheet / horas (`/api/v1/processos/timesheet/`)
- CRM / Leads (`/api/v1/processos/crm/leads/`)
- NFS-e (`/api/v1/processos/nfse/`)
- Protocolos eletrônicos (`/api/v1/processos/protocolos/`)
- Tribunal Push configs (`/api/v1/processos/tribunal-push/configs/`)

**Ações especiais com IA:**
- Extração de dados via IA (texto ou arquivo PDF/DOCX) — `extract-case-data`, `extract-from-document`
- Geração de petição por IA (`peticao-ia/gerar/`)
- OCR de documentos (`ocr/extrair/`)
- Aprimoramento de texto (`enhance-text/`)
- Prazos recursais (cálculo automático) (`prazos/calcular-recursal/`)
- Análise inteligente de prazos — risco, sugestões, copilot (`prazos/inteligente/`)
- Copilot para CRM — classificação de lead, previsão de conversão, follow-up
- Copilot para equipe — sugestão de alocação, balanceamento, match de especialidade
- Copilot para tribunal push — análise de movimentações, ações sugeridas
- Copilot para documentos — geração, revisão, template sugerido, auto-preenchimento
- Copilot para timesheet — sugestão de horas, descrição, detecção automática
- Verificação de conflito de interesses (`conflito-interesses/`)
- Avaliação de risco com IA (`<id>/risco/avaliar-ia/`)
- KPIs gamificados — leaderboard, scores pessoais (`kpis/`)
- Kanban de tarefas (`kanban/`)

**Integrações de dados:**
- DataJud — busca e sincronização de processos CNJ (`datajud/`)
- Parser CNJ (número processo no formato NNNNNNN-DD.AAAA.J.TT.OOOO)
- Importação em massa via CSV (casos, clientes)
- Exportação de dados (casos, clientes, prazos)
- Calendário — eventos, próximos, atrasados
- Relatórios — progresso do caso, portfólio, KPIs
- Protocolo eletrônico — submissão e verificação de status

### 2.3 workflow_definition — Definição de Fluxos BPMN

**CRUD:**
- FlowTemplate (criar, listar, detalhar, editar, excluir, publicar, arquivar)
- FlowNode (nós: swimlane, start_event, end_event, task, user_task, service_task, gateways XOR/AND/OR)
- FlowEdge (conexões entre nós com condições)
- FlowVersion (snapshots imutáveis publicados)

**Categorias de fluxo:** judicial 1º grau, judicial 2º grau, administrativo, outro.
**Roles de swim lane:** distribuidor, procurador, gerente, assessor_gerencial, assessor_gabinete, procurador_geral, subprocurador_geral.

### 2.4 workflow_execution — Execução de Fluxos

**CRUD:**
- FlowInstance (execuções de templates)
- TaskInstance (tarefas dentro de instâncias) — completar (`/complete/`), solicitar redistribuição (`/request/`)
- TaskRequest (redistribuição / avocação / assessoria — pending, approved, rejected)
- MyTasks — visão pessoal de tarefas do usuário autenticado
- TaskRequest Admin — aprovação/rejeição por gestores

**Ações especiais:**
- Analytics de execuções (`analytics/`)
- Sugestão de fluxo via IA (`suggest-flow/`)
- ExecutionEvent — log imutável de auditoria de todas as ações do fluxo

### 2.5 signature — Assinaturas Digitais

**CRUD:**
- `DigitalSignature` — criar, listar, detalhar, atualizar, excluir
- Verificar assinatura (`/verify/`)
- Consultar status do provider (`/api/v1/processos/assinatura-digital/providers/`)

**Providers suportados:**
| Provider | Tipo |
|----------|------|
| `internal` | RSA interno Verus.AI (implementado) |
| `govbr` | Gov.BR (stub) |
| `icpbrasil` | ICP-Brasil A1/A3 (stub) |
| `docusign` | DocuSign (stub) |
| `certisign` | Certisign (stub) |
| `serpro` | Assinador SERPRO (stub) |

### 2.6 organization — Órgãos e Unidades

**CRUD:**
- `Organ` — criar, listar, detalhar, editar, excluir (multi-tenancy root)
- `Unit` — criar, listar, detalhar, editar, excluir (sub-unidade do órgão)

Tipos de órgão: PGM (Procuradoria-Geral do Município), PGE, PGI, Outro.

### 2.7 agents — Agentes de IA

**CRUD:**
- `AgentPrompt` — criar, listar, detalhar, editar, excluir agentes configuráveis
- Analytics de uso dos assistentes (`/analytics/`)

Campos configuráveis por agente: system_prompt, user_prompt_template, llm_provider (openai/anthropic/watsonx), model_name, temperature, max_tokens, use_rag.

### 2.8 intelligent_assistant — Assistente Inteligente

**Sessões e documentos:**
- Criar/listar/detalhar/excluir sessões de geração
- Upload de documentos de referência na sessão
- Preview da sessão; auditoria da sessão
- Validação de inputs antes de gerar
- Busca semântica dentro da sessão

**Blueprints dinâmicos:**
- CRUD de blueprints (create, list, get, update, delete, duplicate)
- CRUD de seções e sub-seções dentro de blueprints
- Reordenar seções
- Criação de blueprint via Copilot (linguagem natural) — `blueprints/copilot/chat/` e `blueprints/copilot/create/`

**Agentes de seção:**
- CRUD de SectionAgentConfig
- Executar agente de seção individualmente

**Geração de documentos:**
- Geração dinâmica com blueprint (`generate/`)
- Streaming SSE de geração (`generate-stream/`)
- Regenerar seção específica em stream (`regenerate-section-stream/`)
- Sessões de geração (list, get, cancel)

**Exportação:**
- PDF (`generate-pdf/`)
- DOCX (`generate-docx/`)
- ODT (`generate-odt/`)
- Polling de status PDF (`pdf-status/`)

**Ações adicionais:**
- Confirmar revisão humana do documento
- Atualizar seções do documento
- Atualizar HTML (editor visual)
- Listar placeholders não resolvidos
- Feedback de seções (auto-aprendizagem)
- Busca de jurisprudência via Tavily
- Copilot jurídico — sugestões e comandos
- Aprimoramento de texto com IA
- Preenchimento de formulário via documento
- Extração automática de campos

**Knowledge Base (integrada ao assistente):**
- Listar/buscar bases de conhecimento
- CRUD de KBs (manage)
- Upload de arquivos para KB
- Listar/excluir fontes e arquivos
- Estatísticas da KB
- Vincular/desvincular agentes à KB

### 2.9 documents — Documentos Jurídicos

**CRUD:**
- `LegalDocument` / `ETP` — criar, listar, detalhar, editar, excluir (`/items/`)
- `DocumentGenerator` — criar, listar, detalhar, editar, excluir (`/generators/`)

**Versionamento semântico:**
- Criar versão (`/items/<id>/versions/create/`)
- Listar versões
- Detalhar versão
- Diff entre versões
- Rollback para versão anterior

### 2.10 forms — Formulários Dinâmicos

**CRUD:**
- `FormTemplate` — criar, listar, detalhar, editar, excluir (`/templates/`)
- `FormAssistant` — criar, listar, detalhar, editar, excluir (`/assistants/`)
- Import de formulários (`/forms/import/`)

Campos suportados: text, textarea, number, email, date, select, checkbox, radio, file, array.

### 2.11 templates — Templates de Documentos

**CRUD:**
- `DocumentTemplate` — criar, listar, detalhar, editar, excluir
- Tipos: HTML, TinyMCE, DOCX, Markdown
- Suporte a placeholders `{{field_id}}` e vinculação com `DocumentBlueprint`

### 2.12 kb — Base de Conhecimento

**CRUD:**
- `Document` (KB) — criar, listar, detalhar, editar, excluir (`/documents/`)
- Upload de arquivo (PDF, DOC, DOCX, XLSX, PPTX, CSV, TXT, MD, ODT, HTML, imagens)
- Busca legislativa (`/legislation/search/`)

Status de processamento: pending, processing, completed, uploading, ready, failed.
Armazenamento: Cloudflare R2 (upload assíncrono via Celery).
Embeddings: pgvector (VectorField).

### 2.13 rag — Retrieval-Augmented Generation

**CRUD:**
- `RAGQuery` — criar, listar, detalhar (`/queries/`)
- `RAGContext` — criar, listar, detalhar (`/contexts/`)

Parâmetros de busca: top_k, similarity_threshold, filter_categories, filter_tags.
Métricas registradas: search_time_ms, llm_time_ms, total_tokens, chunk_count.

### 2.14 collaboration — Colaboração em Tempo Real

**CRUD:**
- `CollaborationSession` — criar, listar, detalhar, encerrar (`/sessions/`)
- `Comment` — criar, listar, detalhar, editar, excluir (`/comments/`)
- `Suggestion` — criar, listar, detalhar, aceitar, rejeitar (`/suggestions/`)
- Helper: criar sessão a partir de documento (`/documents/<id>/start-session/`)

Limite de colaboradores por sessão configurável. Suporte a OT/CRDT (histórico de operações).

### 2.15 jurisprudence — Pesquisa de Jurisprudência

**Ações:**
- Analisar precedentes (`/radar/analyze/`)
- Estatísticas por tribunal (`/radar/tribunais/`)
- Estatísticas de teses (`/radar/teses/`)
- Detalhe de precedente (`/radar/precedents/<id>/`)
- Listar especialidades
- Histórico de pesquisas do usuário (`/searches/`)
- Busca com streaming SSE (`/searches/stream/`)
- Excluir pesquisa; limpar todas
- Scraping de jurisprudência (`/scrape/`)

Especialidades: CIV, PEN, TRB, ADM, CON, TRI, FAM, EMP, AMB, OUT.

### 2.16 copilot — Assistente Conversacional

**Sessões:**
- Criar/obter/limpar/sincronizar sessão
- Listar todas as sessões do usuário
- Detalhar sessão por ID

**Chat:**
- Streaming de chat SSE (`/chat/stream/`)

**Exportação:**
- Exportar histórico (`/export/`)
- Exportar sessão específica (`/export-session/`)

**Compartilhamento:**
- Criar/obter/excluir/listar/revogar links de compartilhamento (`/share/`)

Provedor LLM configurável via `CopilotConfig`: watsonx (padrão), anthropic, openai.

### 2.17 legal_library — Biblioteca de Argumentos

**CRUD:**
- `LegalArgument` — criar, listar, detalhar, editar, excluir (`/arguments/`)
- `ArgumentCollection` — criar, listar, detalhar, editar, excluir (`/collections/`)
- Importar argumento (`/import/`)

Categorias: preliminar, mérito, pedido, fundamentação, recurso, contrarrazões.
Métricas: `effectiveness_score` (taxa de sucesso em julgamentos).

### 2.18 simulations — Simulações de Julgamento

**CRUD:**
- `Simulation` — criar, listar, detalhar, editar, excluir
- `JudgeProfile` — criar, listar, detalhar, editar, excluir
- `Court` — criar, listar, detalhar, editar, excluir
- `SimulationDocument` (nested) — CRUD
- `JuryMember` (nested) — CRUD

**Simulações disponíveis (SSE streaming):**

| Tipo | Endpoint de Início |
|------|-------------------|
| Júri popular | `/jury/start/` |
| Sentença do juiz | `/judge/start/` |
| STF (11 ministros) | `/stf/start/` |
| Acórdão 2ª instância | `/acordao/start/` |
| STJ | `/stj/start/` |
| JEC (Juizado Especial Cível) | `/jec/start/` |
| JECRIM | `/jecrim/start/` |
| Vara do Trabalho | `/trabalho/start/` |
| TRT | `/trt/start/` |
| TST | `/tst/start/` |
| Turma Recursal | `/turma-recursal/start/` |
| Justiça Eleitoral 1ª inst. | `/eleitoral/start/` |
| TRE | `/tre/start/` |
| TSE | `/tse/start/` |
| Auditoria Militar | `/militar/start/` |
| STM | `/stm/start/` |

**Ações adicionais:**
- Questionamento pós-simulação (`/question/`)
- Questionamento de veredicto do júri (`/question-verdict/`)
- Geração de PDF da simulação (`/generate-pdf/`)
- Listar perfis de ministros (`/ministers/`)

### 2.19 core — Núcleo do Sistema

**CRUD:**
- `DocumentType` — tipos de documentos cadastrados
- `ProcessType` — tipos de processo
- `ProcessStatus` — status de processo customizáveis
- `AuditLog` — logs de auditoria de acesso (somente leitura)
- `LLMProvider` — configuração de provedores de IA
- `TokenUsageLog` — log de consumo de tokens LLM

Inclui endpoints de auditoria de acessos (`/core/urls_audit`).

### 2.20 financeiro — Módulo Financeiro (DESATIVADO)

Módulo com copilot financeiro (previsão de fluxo, sugestão de honorários, análise de risco, geração de cobrança). **Desativado no `config/urls.py`** — não aplicável ao contexto de procuradorias.

### 2.21 integration — Integração com Tribunais

**CRUD:**
- `TribunalIntegration` — configurar conexão com tribunais (`/tribunais/`)
- `ProcessSync` — registros de sincronização de processos (`/processes/`)
- `PetitionProtocol` — protocolos de petição enviados (`/petitions/`)

**Ações especiais:**
- Sincronizar processo manualmente (`/processes/sync/`)

Sistemas suportados: e-SAJ, PJe, Eproc, Projudi, Outro.

---

## 3. Rotas Front-end

### 3.1 Layout (auth) — Rotas Públicas

| Rota | Arquivo | Proteção | Descrição |
|------|---------|----------|-----------|
| `/` | `app/page.tsx` | Pública | Landing page / homepage |
| `/login` | `app/(auth)/login/` | Pública | Tela de autenticação |
| `/cookies` | `app/cookies/` | Pública | Política de cookies |
| `/privacidade` | `app/privacidade/` | Pública | Política de privacidade |
| `/consentimento` | `app/consentimento/` | Pública | Consentimento LGPD |

### 3.2 Layout (client) — Portal do Cliente

| Rota | Arquivo | Proteção | Descrição |
|------|---------|----------|-----------|
| `/portal/login` | `(client)/portal/login/` | Pública | Login do portal do cliente |
| `/portal/audiencias` | `(client)/portal/audiencias/` | Cliente autenticado | Audiências do cliente |
| `/portal/casos` | `(client)/portal/casos/` | Cliente autenticado | Lista de casos do cliente |
| `/portal/casos/[id]` | `(client)/portal/casos/[id]/` | Cliente autenticado | Detalhe do caso |
| `/portal/consentimento` | `(client)/portal/consentimento/` | Cliente autenticado | Consentimentos LGPD do cliente |
| `/portal/contratos` | `(client)/portal/contratos/` | Cliente autenticado | Contratos do cliente |
| `/portal/copilot` | `(client)/portal/copilot/` | Cliente autenticado | Copilot do cliente |
| `/portal/documentos` | `(client)/portal/documentos/` | Cliente autenticado | Documentos do cliente |
| `/portal/financeiro` | `(client)/portal/financeiro/` | Cliente autenticado | Financeiro do cliente |
| `/portal/mensagens` | `(client)/portal/mensagens/` | Cliente autenticado | Mensagens com a procuradoria |
| `/portal/notificacoes` | `(client)/portal/notificacoes/` | Cliente autenticado | Notificações do cliente |
| `/portal/perfil` | `(client)/portal/perfil/` | Cliente autenticado | Perfil do cliente |
| `/portal/privacidade` | `(client)/portal/privacidade/` | Cliente autenticado | Privacidade no portal |

### 3.3 Layout (dashboard) — Área Administrativa / Procuradoria

Todas as rotas abaixo exigem autenticação JWT válida de usuário staff (role >= `visualizador`).

#### Área Geral / Configurações

| Rota | Proteção mínima | Descrição |
|------|-----------------|-----------|
| `/dashboard/` | Qualquer role | Dashboard principal com widgets configuráveis |
| `/dashboard/dashboard-config` | Qualquer role | Configuração dos widgets do dashboard pessoal |
| `/dashboard/settings` | Qualquer role | Configurações gerais da conta |
| `/dashboard/settings/profile` | Qualquer role | Perfil do usuário (OAB, foto, assinatura) |
| `/dashboard/settings/brand` | admin+ | Configurações de marca/identidade visual do órgão |
| `/dashboard/settings/lgpd` | admin+ | Políticas e configurações LGPD |
| `/dashboard/settings/roles` | admin+ | Gerenciamento de roles e permissões |
| `/dashboard/users` | admin+ | Gestão de usuários do sistema |
| `/dashboard/equipe` | gerente+ | Gestão da equipe da procuradoria |
| `/dashboard/analytics` | gerente+ | Painel de analytics e métricas |
| `/dashboard/auditoria` | admin+ | Log de auditoria de acessos e ações |
| `/dashboard/kpis` | Qualquer role | KPIs gamificados e leaderboard |
| `/dashboard/relatorios` | gerente+ | Relatórios de portfólio e KPIs |
| `/dashboard/exportar` | gerente+ | Exportação de dados (casos, prazos, clientes) |
| `/dashboard/importar` | admin+ | Importação em massa via CSV |
| `/dashboard/reminders` | Qualquer role | Lembretes pessoais |
| `/dashboard/email-templates` | admin+ | Templates de e-mail do sistema |

#### Processos e Casos

| Rota | Proteção mínima | Descrição |
|------|-----------------|-----------|
| `/dashboard/processos` | Qualquer role | Lista de processos jurídicos |
| `/dashboard/processos/novo` | distribuidor+ | Cadastro de novo processo |
| `/dashboard/processos/[id]` | Qualquer role | Detalhe do processo |
| `/dashboard/processos/[id]/editar` | procurador+ | Edição do processo |
| `/dashboard/processos/calendario` | Qualquer role | Calendário de audiências e prazos |
| `/dashboard/processos/prazos` | Qualquer role | Lista global de prazos |
| `/dashboard/clients` | Qualquer role | Gestão de clientes / partes |
| `/dashboard/calendario` | Qualquer role | Calendário geral do sistema |
| `/dashboard/kanban` | Qualquer role | Kanban de tarefas |
| `/dashboard/minhas-tarefas` | Qualquer role | Tarefas pessoais do usuário autenticado |
| `/dashboard/prazos-inteligentes` | Qualquer role | Análise inteligente de prazos com IA |
| `/dashboard/conflito-interesses` | gerente+ | Verificação de conflito de interesses |
| `/dashboard/protocolo` | distribuidor+ | Protocolo eletrônico de petições |
| `/dashboard/tribunal-push` | Qualquer role | Monitoramento de publicações em tribunais |
| `/dashboard/datajud` | Qualquer role | Consulta e sincronização CNJ/DataJud |
| `/dashboard/solicitacoes` | Qualquer role | Solicitações de redistribuição / avocação |

#### Documentos e Geração

| Rota | Proteção mínima | Descrição |
|------|-----------------|-----------|
| `/dashboard/documents` | Qualquer role | Lista de documentos jurídicos |
| `/dashboard/documents/new` | procurador+ | Criar novo documento |
| `/dashboard/documents/[id]` | Qualquer role | Detalhe do documento |
| `/dashboard/documents/[id]/edit` | procurador+ | Editor de documento |
| `/dashboard/documents/[id]/preview` | Qualquer role | Pré-visualização do documento |
| `/dashboard/templates` | Qualquer role | Lista de templates de documento |
| `/dashboard/templates/new` | admin+ | Criar novo template |
| `/dashboard/templates/[id]` | Qualquer role | Detalhe do template |
| `/dashboard/templates/[id]/edit` | admin+ | Editar template |
| `/dashboard/gerador-documentos` | Qualquer role | Gerador de documentos simplificado |
| `/dashboard/document-generators` | admin+ | Gerenciadores de geradores de documento (IA) |
| `/dashboard/document-generators/[id]` | admin+ | Configuração de gerador de documento |
| `/dashboard/ocr` | Qualquer role | Extração de texto via OCR |
| `/dashboard/assinatura-digital` | procurador+ | Assinaturas digitais de documentos |

#### Assistente Inteligente / Blueprints

| Rota | Proteção mínima | Descrição |
|------|-----------------|-----------|
| `/dashboard/intelligent-assistant` | Qualquer role | Assistente inteligente — sessões de geração |
| `/dashboard/intelligent-assistant/etp` | Qualquer role | Geração de ETP (Estudo Técnico Preliminar) |
| `/dashboard/intelligent-assistant/gerador` | Qualquer role | Gerador dinâmico de documentos |
| `/dashboard/intelligent-assistant/editor` | Qualquer role | Editor visual do documento gerado |
| `/dashboard/blueprints` | admin+ | Lista de blueprints dinâmicos |
| `/dashboard/blueprints/[id]` | admin+ | Configuração de blueprint e suas seções |
| `/dashboard/peticao-ia` | procurador+ | Geração de petição via IA |

#### Formulários e Workflows

| Rota | Proteção mínima | Descrição |
|------|-----------------|-----------|
| `/dashboard/forms` | Qualquer role | Lista de formulários dinâmicos |
| `/dashboard/forms/[id]` | Qualquer role | Preenchimento / detalhe de formulário |
| `/dashboard/forms/import` | admin+ | Importar formulário (JSON) |
| `/dashboard/form-assistants` | admin+ | Lista de assistentes de formulário |
| `/dashboard/form-assistants/[id]` | admin+ | Configuração de assistente de formulário |
| `/dashboard/fluxos` | gerente+ | Lista de fluxos BPMN (templates) |
| `/dashboard/fluxos/editor/[id]` | admin+ | Editor visual de fluxo BPMN |
| `/dashboard/execucoes` | Qualquer role | Lista de execuções de fluxo (instâncias) |
| `/dashboard/execucoes/[id]` | Qualquer role | Detalhe de execução de fluxo |
| `/dashboard/workflows` | gerente+ | Visão gerencial de workflows |

#### IA e Pesquisa

| Rota | Proteção mínima | Descrição |
|------|-----------------|-----------|
| `/dashboard/copilot` | Qualquer role | Assistente conversacional (Copilot) |
| `/dashboard/jurisprudencia` | Qualquer role | Radar de jurisprudência e precedentes |
| `/dashboard/knowledge-base` | admin+ | Gestão da base de conhecimento (KB) |
| `/dashboard/agents` | admin+ | Lista de agentes de IA configurados |
| `/dashboard/agents/[id]` | admin+ | Configuração de agente de IA |
| `/dashboard/legal-library` | Qualquer role | Biblioteca de argumentos jurídicos |

#### Simulações

| Rota | Proteção mínima | Descrição |
|------|-----------------|-----------|
| `/dashboard/simulations` | Qualquer role | Lista de simulações criadas |
| `/dashboard/simulations/jury` | Qualquer role | Simulação de júri popular |
| `/dashboard/simulations/judge` | Qualquer role | Simulação de sentença do juiz |
| `/dashboard/simulations/stf` | Qualquer role | Simulação STF |
| `/dashboard/simulations/acordao` | Qualquer role | Simulação de acórdão 2ª instância |
| `/dashboard/simulations/stj` | Qualquer role | Simulação STJ |
| `/dashboard/simulations/jec` | Qualquer role | Simulação JEC |
| `/dashboard/simulations/jecrim` | Qualquer role | Simulação JECRIM |
| `/dashboard/simulations/trabalho` | Qualquer role | Simulação Vara do Trabalho |
| `/dashboard/simulations/trt` | Qualquer role | Simulação TRT |
| `/dashboard/simulations/tst-trabalho` | Qualquer role | Simulação TST |
| `/dashboard/simulations/turma-recursal` | Qualquer role | Simulação Turma Recursal |
| `/dashboard/simulations/eleitoral` | Qualquer role | Simulação Justiça Eleitoral |
| `/dashboard/simulations/militar` | Qualquer role | Simulação Justiça Militar |
| `/dashboard/simulations/stm` | Qualquer role | Simulação STM |

#### CRM, Financeiro e Outros

| Rota | Proteção mínima | Descrição |
|------|-----------------|-----------|
| `/dashboard/crm` | gerente+ | Pipeline de leads / CRM |
| `/dashboard/contratos` | Qualquer role | Lista de contratos jurídicos |
| `/dashboard/contratos/[id]` | Qualquer role | Detalhe do contrato |
| `/dashboard/custas` | Qualquer role | Guias de custas judiciais |
| `/dashboard/honorarios` | gerente+ | Tabela OAB e honorários |
| `/dashboard/timesheet` | Qualquer role | Controle de horas / timesheet |
| `/dashboard/nfse` | admin+ | Notas fiscais de serviço (NFS-e) |
| `/dashboard/financeiro` | admin+ | Módulo financeiro (desativado backend) |
| `/dashboard/mensagens-clientes` | Qualquer role | Canal de mensagens com clientes |

**Total de rotas mapeadas:** 106 (93 dashboard + 13 portal client + 5 públicas)

---

## 4. Endpoints Back-end

### 4.1 accounts — `/api/v1/auth/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/login/` | Autenticação — retorna access + refresh JWT |
| POST | `/logout/` | Invalida o token atual |
| POST | `/token/refresh/` | Renova access token via refresh token |
| GET/PATCH | `/users/me/` | Perfil do usuário autenticado |
| GET/POST | `/users/` | Listar / criar usuários (admin+) |
| GET/PATCH/DELETE | `/users/<id>/` | Detalhar / editar / excluir usuário |
| POST | `/users/<id>/set_password/` | Alterar senha de usuário |
| POST | `/email-confirm/<token>/` | Confirmar e-mail |
| POST | `/password-reset/` | Solicitar reset de senha |
| POST | `/password-reset/confirm/` | Confirmar reset de senha |
| GET/POST | `/notifications/` | Listar / criar notificações |
| PATCH | `/notifications/<id>/mark-read/` | Marcar notificação como lida |
| GET/POST | `/reminders/` | Listar / criar lembretes |
| GET/PATCH/DELETE | `/reminders/<id>/` | Detalhar / editar / excluir lembrete |
| GET/POST | `/brand-settings/` | Configurações de marca |
| GET/PATCH | `/brand-settings/<id>/` | Detalhar / editar brand settings |
| GET/POST | `/email-templates/` | Templates de e-mail |
| GET/PATCH/DELETE | `/email-templates/<id>/` | Detalhar / editar / excluir template |
| GET/POST | `/dashboard-config/` | Configuração de dashboard pessoal |
| GET/PATCH | `/dashboard-config/<id>/` | Detalhar / editar config dashboard |
| GET/POST | `/equipes/` | Times / equipes |
| GET/PATCH/DELETE | `/equipes/<id>/` | Detalhar / editar / excluir time |
| GET/POST | `/lgpd/consents/` | Consentimentos LGPD |
| POST | `/lgpd/request-deletion/` | Solicitar exclusão de dados (art. 18 LGPD) |
| GET/POST | `/notification-channels/` | Canais de notificação |
| GET/POST | `/client-portal/` | Acesso ao portal do cliente |

### 4.2 cases — `/api/v1/processos/`

#### Processos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/` | Listar / criar processos |
| GET/PATCH/DELETE | `/<id>/` | Detalhar / editar / excluir (soft delete) processo |
| GET | `/stats/` | Estatísticas de processos |
| POST | `/extract-case-data/` | Extrair dados do caso via IA (texto) |
| POST | `/extract-from-document/` | Extrair dados via PDF/DOCX/ODT |
| POST | `/enhance-text/` | Aprimorar texto com IA |
| POST | `/cnj/parse/` | Parsear número CNJ |
| POST | `/<id>/iniciar-fluxo/` | Iniciar fluxo BPMN no processo |

#### Prazos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/prazos/` | Listar / criar prazos (global) |
| GET/PATCH/DELETE | `/prazos/<id>/` | Detalhar / editar / excluir prazo |
| GET/POST | `/<id>/prazos/` | Prazos de um processo específico |
| POST | `/prazos/calcular-recursal/` | Calcular prazo recursal |
| GET | `/prazos/tipos-recurso/` | Listar tipos de recurso |
| GET | `/prazos/inteligente/analise/` | Análise inteligente de prazos |
| GET | `/prazos/inteligente/<id>/sugestoes/` | Sugestões para prazo específico |
| GET | `/prazos/inteligente/<id>/risco/` | Risco do processo (IA) |
| POST | `/prazos/copilot/calcular/` | Copilot: calcular prazo |
| POST | `/prazos/copilot/estrategia/` | Copilot: sugerir estratégia |
| POST | `/prazos/copilot/agrupar/` | Copilot: agrupar prazos |
| GET | `/prazos/copilot/criticos/` | Copilot: prazos críticos |

#### Contratos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/contratos/` | Listar / criar contratos |
| GET/PATCH/DELETE | `/contratos/<id>/` | Detalhar / editar / excluir contrato |
| POST | `/contratos/gerar/` | Gerar contrato via IA |
| POST | `/contratos/upload-analyze/` | Upload e análise de contrato |
| GET | `/contratos/stats/` | Estatísticas de contratos |
| POST | `/contratos/<id>/assinar/` | Marcar contrato como assinado |

#### DataJud / CNJ

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/datajud/buscar/` | Buscar processo no DataJud |
| POST | `/datajud/sync/<id>/` | Sincronizar processo com DataJud |
| GET | `/datajud/movimentacoes/` | Movimentações do DataJud |

#### Calendário, Relatórios, KPIs

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/calendario/events/` | Eventos do calendário |
| GET | `/calendario/proximos/` | Próximos eventos |
| GET | `/calendario/atrasados/` | Eventos atrasados |
| GET | `/calendario/sync/providers/` | Providers de sincronização de calendário |
| GET | `/relatorios/caso/<id>/` | Relatório de progresso do caso |
| GET | `/relatorios/portfolio/` | Relatório de portfólio |
| GET | `/relatorios/kpis/` | KPIs do sistema |
| GET | `/kpis/leaderboard/` | Leaderboard gamificado |
| POST | `/kpis/recalcular/` | Recalcular KPIs |
| GET | `/kpis/meus-scores/` | Scores pessoais |

#### Tribunal Push

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/tribunal-push/configs/` | Configs de monitoramento |
| GET/PATCH/DELETE | `/tribunal-push/configs/<id>/` | Detalhar / editar / excluir config |
| POST | `/tribunal-push/configs/<id>/check-now/` | Verificar agora |
| GET | `/tribunal-push/events/` | Eventos capturados |
| POST | `/tribunal-push/events/<id>/mark-processed/` | Marcar como processado |

#### Outros (cases)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/custas/` | Custas judiciais |
| POST | `/custas/calcular/` | Calcular custas |
| GET | `/custas/resumo/` | Resumo de custas |
| POST | `/custas/<id>/pagar/` | Marcar custa como paga |
| GET/POST | `/nfse/` | Notas fiscais de serviço |
| POST | `/nfse/<id>/emitir/` | Emitir NFS-e |
| GET/POST | `/timesheet/` | Registro de horas |
| POST | `/timesheet/<id>/aprovar/` | Aprovar registro de hora |
| GET | `/timesheet/relatorio-mensal/` | Relatório mensal |
| GET/POST | `/crm/leads/` | Leads do CRM |
| POST | `/crm/leads/<id>/converter/` | Converter lead em caso |
| GET | `/crm/pipeline/` | Visualização kanban do pipeline |
| GET/POST | `/kanban/` | Visão kanban de tarefas |
| POST | `/kanban/<id>/mover/` | Mover tarefa no kanban |
| POST | `/conflito-interesses/` | Verificar conflito de interesses |
| POST | `/ocr/extrair/` | Extrair texto via OCR |
| POST | `/peticao-ia/gerar/` | Gerar petição com IA |
| GET/POST | `/importar/casos/` | Importar casos via CSV |
| GET/POST | `/importar/clientes/` | Importar clientes via CSV |
| GET | `/exportar/casos/` | Exportar casos |
| GET | `/exportar/prazos/` | Exportar prazos |

### 4.3 workflow_definition — `/api/v1/workflows/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/templates/` | Listar / criar templates de fluxo |
| GET/PATCH/DELETE | `/templates/<id>/` | Detalhar / editar / excluir template |
| POST | `/templates/<id>/publish/` | Publicar versão do template |
| POST | `/templates/<id>/archive/` | Arquivar template |
| GET/POST | `/templates/<id>/nodes/` | Listar / criar nós do fluxo |
| GET/POST | `/templates/<id>/edges/` | Listar / criar arestas do fluxo |
| GET | `/templates/<id>/versions/` | Listar versões publicadas |

### 4.4 workflow_execution — `/api/v1/workflow-execution/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/executions/` | Listar / criar instâncias de fluxo |
| GET/PATCH/DELETE | `/executions/<id>/` | Detalhar / editar / cancelar instância |
| GET | `/executions/<id>/tasks/` | Tarefas de uma instância |
| GET | `/executions/<id>/tasks/<pk>/` | Detalhar tarefa |
| POST | `/executions/<id>/tasks/<pk>/complete/` | Completar tarefa |
| POST | `/executions/<id>/tasks/<pk>/request/` | Criar solicitação (redistribuição/avocação) |
| GET | `/my-tasks/` | Tarefas do usuário autenticado |
| GET/POST | `/task-requests/` | Solicitações (admin) |
| PATCH | `/task-requests/<id>/approve/` | Aprovar solicitação |
| PATCH | `/task-requests/<id>/reject/` | Rejeitar solicitação |
| GET | `/analytics/` | Analytics de execuções |
| POST | `/suggest-flow/` | Sugerir fluxo via IA |

### 4.5 signature — `/api/v1/signatures/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/` | Listar / criar assinaturas |
| GET/PATCH/DELETE | `/<id>/` | Detalhar / editar / excluir assinatura |
| POST | `/<id>/verify/` | Verificar validade de assinatura |
| POST | `/<id>/revoke/` | Revogar assinatura |

### 4.6 organization — `/api/v1/organization/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/organs/` | Listar / criar órgãos |
| GET/PATCH/DELETE | `/organs/<id>/` | Detalhar / editar / excluir órgão |
| GET/POST | `/units/` | Listar / criar unidades |
| GET/PATCH/DELETE | `/units/<id>/` | Detalhar / editar / excluir unidade |

### 4.7 agents — `/api/v1/agents/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/` | Listar / criar agentes |
| GET/PATCH/DELETE | `/<id>/` | Detalhar / editar / excluir agente |
| GET | `/analytics/` | Analytics de uso dos agentes |

### 4.8 intelligent_assistant — `/api/v1/intelligent-assistant/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/sessions/` | Criar sessão de geração |
| GET | `/sessions/list/` | Listar sessões |
| GET | `/sessions/<id>/` | Detalhar sessão |
| DELETE | `/sessions/<id>/delete/` | Excluir sessão |
| GET | `/sessions/<id>/audit-log/` | Auditoria da sessão |
| POST | `/sessions/<id>/upload/` | Upload de documento de referência |
| GET | `/sessions/<id>/validate-inputs/` | Validar inputs antes de gerar |
| POST | `/generate/` | Gerar documento (síncrono) |
| POST | `/generate-stream/` | Gerar documento (SSE streaming) |
| POST | `/regenerate-section-stream/` | Regenerar seção (SSE streaming) |
| GET/PATCH/DELETE | `/documents/<id>/` | CRUD de documento gerado |
| PATCH | `/documents/<id>/update-sections/` | Atualizar seções |
| PATCH | `/documents/<id>/update-html/` | Atualizar HTML do editor |
| POST | `/documents/<id>/generate-pdf/` | Exportar PDF |
| POST | `/documents/<id>/generate-docx/` | Exportar DOCX |
| POST | `/documents/<id>/generate-odt/` | Exportar ODT |
| GET | `/blueprints/` | Listar blueprints |
| POST | `/blueprints/create/` | Criar blueprint |
| GET/PATCH | `/blueprints/<id>/` | Detalhar / editar blueprint |
| DELETE | `/blueprints/<id>/delete/` | Excluir blueprint |
| POST | `/blueprints/<id>/duplicate/` | Duplicar blueprint |
| GET/POST | `/blueprints/<id>/sections/` | Listar / criar seções do blueprint |
| POST | `/blueprints/copilot/create/` | Criar blueprint via linguagem natural |
| GET | `/knowledge-bases/` | Listar KBs disponíveis |
| POST | `/knowledge-bases/search/` | Busca semântica na KB |
| POST | `/enhance-text/` | Aprimorar texto com IA |
| POST | `/copilot/suggest/` | Sugestão do copilot jurídico |

### 4.9 documents — `/api/v1/documents/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/items/` | Listar / criar documentos |
| GET/PATCH/DELETE | `/items/<id>/` | Detalhar / editar / excluir documento |
| GET/POST | `/generators/` | Listar / criar geradores |
| GET/PATCH/DELETE | `/generators/<id>/` | Detalhar / editar / excluir gerador |
| POST | `/generators/<id>/generate/` | Gerar documento com o gerador |
| POST | `/items/<id>/versions/create/` | Criar nova versão |
| GET | `/items/<id>/versions/` | Listar versões |
| GET | `/items/<id>/versions/<vid>/` | Detalhar versão |
| GET | `/items/<id>/versions/diff/` | Diff entre versões |
| POST | `/items/<id>/versions/<vid>/rollback/` | Rollback para versão |

### 4.10 forms — `/api/v1/forms/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/templates/` | Listar / criar templates de formulário |
| GET/PATCH/DELETE | `/templates/<id>/` | Detalhar / editar / excluir template |
| POST | `/templates/<id>/submit/` | Enviar preenchimento de formulário |
| GET/POST | `/assistants/` | Listar / criar assistentes de formulário |
| GET/PATCH/DELETE | `/assistants/<id>/` | Detalhar / editar / excluir assistente |

### 4.11 templates — `/api/v1/templates/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/` | Listar / criar templates de documento |
| GET/PATCH/DELETE | `/<id>/` | Detalhar / editar / excluir template |
| POST | `/<id>/render/` | Renderizar template com dados |

### 4.12 kb — `/api/v1/kb/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/documents/` | Listar / criar documentos KB |
| GET/PATCH/DELETE | `/documents/<id>/` | Detalhar / editar / excluir documento KB |
| POST | `/documents/<id>/reprocess/` | Reprocessar embeddings |
| GET | `/legislation/search/` | Buscar legislação na KB |

### 4.13 rag — `/api/v1/rag/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/queries/` | Listar / criar queries RAG |
| GET | `/queries/<id>/` | Detalhar query RAG |
| GET/POST | `/contexts/` | Listar / criar contextos RAG |
| GET | `/contexts/<id>/` | Detalhar contexto RAG |

### 4.14 collaboration — `/api/v1/collaboration/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/sessions/` | Listar / criar sessões colaborativas |
| GET/PATCH/DELETE | `/sessions/<id>/` | Detalhar / editar / encerrar sessão |
| POST | `/documents/<id>/start-session/` | Iniciar sessão para documento |
| GET/POST | `/comments/` | Listar / criar comentários |
| GET/PATCH/DELETE | `/comments/<id>/` | Detalhar / editar / excluir comentário |
| GET/POST | `/suggestions/` | Listar / criar sugestões |
| PATCH | `/suggestions/<id>/accept/` | Aceitar sugestão |
| PATCH | `/suggestions/<id>/reject/` | Rejeitar sugestão |

### 4.15 jurisprudence — `/api/v1/jurisprudence/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/radar/analyze/` | Analisar precedentes relevantes |
| GET | `/radar/tribunais/` | Estatísticas por tribunal |
| GET | `/radar/teses/` | Estatísticas de teses |
| GET | `/radar/precedents/<id>/` | Detalhar precedente |
| GET | `/specialties/` | Listar especialidades jurídicas |
| GET | `/searches/` | Histórico de pesquisas do usuário |
| POST | `/searches/stream/` | Pesquisa com streaming SSE |
| DELETE | `/searches/clear/` | Limpar histórico de pesquisas |
| DELETE | `/searches/<id>/` | Excluir pesquisa específica |
| POST | `/scrape/` | Scraping de jurisprudência |

### 4.16 copilot — `/api/v1/copilot/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/session/` | Criar / obter sessão ativa |
| DELETE | `/session/clear/` | Limpar sessão |
| POST | `/session/sync/` | Sincronizar sessão |
| GET | `/sessions/` | Listar sessões |
| GET/DELETE | `/session/<id>/` | Detalhar / excluir sessão |
| POST | `/chat/stream/` | Chat com streaming SSE |
| GET | `/export/` | Exportar histórico |
| POST | `/export-session/` | Exportar sessão específica |
| POST | `/share/create/` | Criar link de compartilhamento |
| GET | `/share/<code>/` | Obter sessão compartilhada |
| DELETE | `/share/<code>/delete/` | Excluir share |
| GET | `/share/list/` | Listar shares |
| POST | `/share/<code>/revoke/` | Revogar share |

### 4.17 legal_library — `/api/v1/legal-library/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/arguments/` | Listar / criar argumentos |
| GET/PATCH/DELETE | `/arguments/<id>/` | Detalhar / editar / excluir argumento |
| GET/POST | `/collections/` | Listar / criar coleções |
| GET/PATCH/DELETE | `/collections/<id>/` | Detalhar / editar / excluir coleção |
| POST | `/import/` | Importar argumento de documento externo |

### 4.18 simulations — `/api/v1/simulations/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/simulations/` | Listar / criar simulações |
| GET/PATCH/DELETE | `/simulations/<id>/` | Detalhar / editar / excluir simulação |
| POST | `/simulations/<id>/jury/start/` | Iniciar simulação de júri (SSE) |
| POST | `/simulations/<id>/judge/start/` | Iniciar simulação de juiz (SSE) |
| POST | `/simulations/<id>/stf/start/` | Iniciar simulação STF (SSE) |
| POST | `/simulations/<id>/stj/start/` | Iniciar simulação STJ (SSE) |
| POST | `/simulations/<id>/acordao/start/` | Iniciar acórdão 2ª inst. (SSE) |
| POST | `/simulations/<id>/jec/start/` | Iniciar JEC (SSE) |
| POST | `/simulations/<id>/jecrim/start/` | Iniciar JECRIM (SSE) |
| POST | `/simulations/<id>/trabalho/start/` | Iniciar Vara do Trabalho (SSE) |
| POST | `/simulations/<id>/trt/start/` | Iniciar TRT (SSE) |
| POST | `/simulations/<id>/tst/start/` | Iniciar TST (SSE) |
| POST | `/simulations/<id>/turma-recursal/start/` | Iniciar Turma Recursal (SSE) |
| POST | `/simulations/<id>/eleitoral/start/` | Iniciar Eleitoral (SSE) |
| POST | `/simulations/<id>/militar/start/` | Iniciar Militar (SSE) |
| POST | `/simulations/<id>/stm/start/` | Iniciar STM (SSE) |
| POST | `/simulations/<id>/question/` | Questionar simulação em curso |
| POST | `/simulations/<id>/question-verdict/` | Questionar veredicto do júri |
| POST | `/simulations/<id>/generate-pdf/` | Gerar PDF da simulação |
| GET | `/judges/` | Listar perfis de juízes |
| GET | `/courts/` | Listar tribunais cadastrados |
| GET | `/ministers/` | Listar perfis de ministros |
| CRUD | `/simulations/<id>/documents/` | Documentos da simulação |
| CRUD | `/simulations/<id>/jury-members/` | Jurados da simulação |

### 4.19 core — `/api/v1/core/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/document-types/` | Tipos de documento |
| GET/POST | `/process-types/` | Tipos de processo |
| GET/POST | `/process-statuses/` | Status de processo |
| GET | `/audit-logs/` | Logs de auditoria (somente leitura) |
| GET/POST | `/llm-providers/` | Provedores LLM configurados |
| GET | `/token-usage/` | Log de consumo de tokens |

### 4.20 integration — `/api/v1/integration/`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/tribunais/` | Configurações de integração com tribunais |
| GET/PATCH/DELETE | `/tribunais/<id>/` | Detalhar / editar / excluir integração |
| GET/POST | `/processes/` | Processos sincronizados |
| POST | `/processes/sync/` | Sincronizar processo |
| GET/POST | `/petitions/` | Petições protocoladas |
| GET/PATCH/DELETE | `/petitions/<id>/` | Detalhar / editar / excluir petição |

---

## 5. Entidades e Dados

### 5.1 User (accounts)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `username` | string | Nome de usuário único |
| `email` | email | E-mail |
| `first_name` / `last_name` | string | Nome completo |
| `role` | string | Role (ver hierarquia §7) |
| `organ` | FK Organ | Órgão vinculado (multi-tenancy) |
| `unit` | FK Unit | Unidade interna |
| `phone` | string | Telefone |
| `department` | string | Departamento |
| `position` | string | Cargo |
| `oab_number` / `oab_state` | string | Registro OAB |
| `lawyer_specialties` | JSON list | Especialidades jurídicas |
| `signature_image` | ImageField | Imagem da assinatura digitalizada |
| `preferred_llm_provider` | string | openai ou anthropic |
| `avatar` | ImageField | Foto do usuário |
| `metadata` | JSON | Metadados extras |
| `created_at` / `updated_at` | datetime | Timestamps |

### 5.2 Organ (organization)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `name` | string | Nome do órgão |
| `short_name` | string | Sigla (ex: PGM-Serra) |
| `organ_type` | string | pgm / pge / pgi / other |
| `cnpj` | string | CNPJ |
| `state` | string | UF (2 letras) |
| `city` | string | Município |
| `settings` | JSON | Configurações da plataforma para o órgão |
| `logo` | ImageField | Logotipo |
| `is_active` | bool | Ativo |

### 5.3 LegalCase (cases)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `numero_processo` | string | Número CNJ (NNNNNNN-DD.AAAA.J.TT.OOOO) |
| `titulo` | string | Título / assunto |
| `especialidade` | string | civel, criminal, trabalhista, tributario, administrativo, previdenciario, familia, empresarial, ambiental, consumidor, imobiliario, outros |
| `status` | string | ativo, aguardando, suspenso, encerrado, arquivado, ganho, perdido, acordo |
| `fase` | string | inicial, instrucao, julgamento, recursal, execucao, transitado, extrajudicial |
| `client` | FK Client | Cliente vinculado |
| `cliente_nome` | string | Parte representada |
| `parte_contraria` | string | Parte contrária |
| `tribunal` | string | Tribunal (ex: TJRJ) |
| `vara_juizo` | string | Vara / Juízo |
| `comarca` | string | Comarca / seção judiciária |
| `valor_causa` | decimal | Valor da causa |
| `honorarios_combinados` | decimal | Honorários combinados |
| `advogado_responsavel` | FK User | Procurador responsável |
| `organ` | FK Organ | Procuradoria responsável |
| `active_flow` | FK FlowInstance | Fluxo de trabalho ativo |
| `deleted_at` | datetime | Soft delete |
| `data_distribuicao` | date | Data de distribuição |
| `data_encerramento` | date | Data de encerramento |

### 5.4 FlowTemplate (workflow_definition)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `name` | string | Nome do fluxo |
| `description` | text | Descrição |
| `status` | string | draft / published / archived |
| `category` | string | judicial_1 / judicial_2 / administrative / other |
| `organ` | FK Organ | Órgão dono do template |
| `nodes` | related | FlowNode[] — nós do fluxo |
| `edges` | related | FlowEdge[] — conexões |
| `versions` | related | FlowVersion[] — snapshots publicados |

### 5.5 FlowInstance (workflow_execution)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `template` | FK FlowTemplate | Template utilizado |
| `organ` | FK Organ | Órgão |
| `status` | string | pending / running / completed / cancelled |
| `process_ref` | string | Número ou UUID do processo vinculado |
| `tasks` | related | TaskInstance[] |
| `events` | related | ExecutionEvent[] (audit log) |

### 5.6 DigitalSignature (signature)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `signer` | FK User | Assinante |
| `document_type` | string | despacho, parecer, petição, ata, etc. |
| `document_ref` | string | UUID do objeto assinado |
| `document_title` | string | Título do documento |
| `content_hash` | string | SHA-256 hex do conteúdo |
| `provider` | string | internal / govbr / icpbrasil / docusign / certisign / serpro |
| `status` | string | pending / signed / rejected / expired / revoked |
| `signature_data` | text | Base64 RSA ou token do provider |
| `public_key_fingerprint` | string | Fingerprint da chave pública |

### 5.7 DocumentBlueprint / Sessions (intelligent_assistant)

| Entidade | Campos-chave |
|----------|-------------|
| `DocumentBlueprint` | id, name, description, sections (related), agents (related), organ |
| `BlueprintSection` | id, blueprint, title, order, sub_sections, agent_config |
| `GenerationSession` | id, blueprint, user, organ, status (running/completed/cancelled), result |
| `UploadedDocument` | id, session, file, content_extracted |

### 5.8 LegalDocument / DocumentGenerator (documents)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK (`LegalDocument`) |
| `title` | string | Título do documento |
| `content` | text | Conteúdo HTML/MD |
| `document_type` | FK DocumentType | Tipo do documento |
| `case` | FK LegalCase | Caso vinculado (opcional) |
| `created_by` | FK User | Autor |
| `organ` | FK Organ | Órgão |
| `versions` | related | DocumentVersion[] |
| — | — | — |
| `id` | UUID | PK (`DocumentGenerator`) |
| `name` | string | Nome do gerador |
| `document_type` | string | tipo de peça (petição, contestação, etc.) |
| `specialty` | string | Especialidade jurídica |
| `system_prompt` | text | System prompt do LLM |
| `llm_provider` | string | openai / anthropic |
| `model_name` | string | ex: gpt-4o |
| `use_rag` | bool | Usar RAG na geração |

### 5.9 FormTemplate (forms)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `name` | string | Nome do formulário |
| `fields` | JSON list | Campos (id, type, label, required, options) |
| `sections` | JSON list | Seções com campos aninhados |
| `organ` | FK Organ | Órgão dono |

### 5.10 KnowledgeBase Document (kb)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `title` | string | Título |
| `category` | string | manual, lei, exemplo, referencia, template, outros |
| `file` | FileField | Arquivo original (R2) |
| `status` | string | pending / processing / completed / uploading / ready / failed |
| `embedding` | VectorField | pgvector embedding (gerado via Celery) |

### 5.11 Simulation (simulations)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `user` | FK User | Dono da simulação |
| `case` | FK LegalCase | Caso associado (opcional) |
| `simulation_type` | string | jury, judge, stf, stj, jec, jecrim, trabalho, trt, tst, eleitoral, tre, tse, militar, stm, turma_recursal |
| `title` | string | Título |
| `status` | string | draft / configuring / running / deliberating / completed / failed |
| `config` | JSON | Configurações específicas do tipo |
| `result` | JSON | Resultado da simulação |
| `documents` | related | SimulationDocument[] |
| `jury_members` | related | JuryMember[] |

### 5.12 CopilotConfig (copilot)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | int | PK (singleton, id=1) |
| `name` | string | Nome do assistente |
| `system_prompt` | text | Instruções de comportamento |
| `provider` | string | watsonx / anthropic / openai |
| `model` | string | ID do modelo LLM |
| `temperature` | float | 0.0 – 2.0 |

### 5.13 JurisprudenceSearch / Result (jurisprudence)

| Entidade | Campos-chave |
|----------|-------------|
| `JurisprudenceSearch` | id, user, query, specialty (CIV/PEN/TRB/ADM/…), status (pending/processing/completed/failed) |
| `JurisprudenceResult` | id, search, tribunal, ementa, data_julgamento, tese, relevance_score |

### 5.14 LegalArgument (legal_library)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `title` | string | Título do argumento |
| `content` | text | Texto do argumento |
| `category` | string | preliminar, merito, pedido, fundamentacao, recurso, contrarrazoes |
| `specialty` | string | CIV, PEN, TRB, FAM, PRE, ADM, TRI, EMP |
| `tribunal` | string | Tribunal de origem |
| `effectiveness_score` | float | Métrica de sucesso em julgamentos |
| `subcategories` | JSON list | Tags para classificação fina |

### 5.15 RAGQuery (rag)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | PK |
| `user` | FK User | Usuário |
| `query_text` | text | Texto da consulta |
| `top_k` | int | Número de chunks recuperados |
| `similarity_threshold` | float | Threshold de similaridade (pgvector) |
| `retrieved_chunks` | JSON | Chunks retornados |
| `llm_response` | text | Resposta gerada pelo LLM |
| `total_tokens` | int | Tokens consumidos |

---

## 6. Integrações Externas

| # | Integração | App(s) | Tipo | Status | Observações |
|---|------------|--------|------|--------|-------------|
| 1 | **OpenAI** (GPT-4o, GPT-4o-mini) | agents, documents, intelligent_assistant, cases, simulations, copilot | API REST (HTTPS) | Ativo | Provider principal de LLM; chave via `OPENAI_API_KEY` |
| 2 | **Anthropic** (Claude 3/4) | agents, documents, intelligent_assistant, copilot | API REST | Ativo (alternativo) | Configurável por usuário ou agente; `ANTHROPIC_API_KEY` |
| 3 | **IBM WatsonX** (Llama 3.3) | copilot | API REST | Ativo (padrão Copilot) | Provider padrão do Copilot conversacional |
| 4 | **DataJud / CNJ** | cases | REST API pública | Ativo | Busca e sincronização de processos pelo número CNJ; endpoint `/datajud/buscar/`, `/datajud/sync/` |
| 5 | **Gov.BR Assinatura** | signature | Stub | Stub (não implementado) | Provider `govbr` declarado em `SignatureProvider`; integração real pendente |
| 6 | **ICP-Brasil (A1/A3)** | signature | Stub | Stub | Certificado digital A1/A3; implementação pendente |
| 7 | **DocuSign** | signature | Stub | Stub | Provider `docusign`; implementação pendente |
| 8 | **Certisign** | signature | Stub | Stub | Provider `certisign`; implementação pendente |
| 9 | **SERPRO Assinador** | signature | Stub | Stub | Provider `serpro`; implementação pendente |
| 10 | **Tavily** (busca web) | intelligent_assistant | API REST | Ativo | Busca de jurisprudência na web; endpoint `/jurisprudence/search/` dentro do assistente |
| 11 | **Cloudflare R2** | kb, documents, intelligent_assistant | S3-compatible | Ativo | Armazenamento de arquivos (PDFs, DOCXs, templates); integração via boto3/S3 |
| 12 | **Celery + Redis** | kb, documents, intelligent_assistant | Task queue | Ativo | Processamento assíncrono: embeddings (Docling), geração de PDF/DOCX, sincronização DataJud |
| 13 | **pgvector (PostgreSQL)** | kb, rag | Extensão PG | Ativo | Busca vetorial semântica; embeddings de chunks de documentos |
| 14 | **e-SAJ / PJe / Eproc / Projudi** | integration | REST/SOAP | Stub | Integração com sistemas de tribunais; `TribunalIntegration` configurável, implementação específica pendente |
| 15 | **Docling** | kb | Python lib | Ativo | Extração e chunking de PDFs, DOCXs, ODTs, imagens para embeddings |
| 16 | **Tribunal Push** | cases | Web scraping / push | Ativo | Monitoramento automático de publicações de tribunais (`TribunalPushConfig`) |
| 17 | **Serviços de calendário externos** | cases | OAuth / API | Stub | Sync de calendário com provedores externos (`/calendario/sync/providers/`); implementação pendente |
| 18 | **NFS-e (Prefeituras)** | cases | WebService SOAP | Parcial | Emissão de nota fiscal de serviço (`/nfse/<id>/emitir/`); depende de configuração do município |

---

## 7. Controle de Acesso e Hierarquia de Roles

### 7.1 Tabela de Roles

| Role | Nível | Descrição |
|------|-------|-----------|
| `superadmin` | 100 | Acesso total à plataforma (Verus.AI) |
| `admin` | 90 | Administrador do órgão |
| `procurador_geral` | 85 | Chefe da procuradoria |
| `subprocurador_geral` | 80 | Vice-chefe da procuradoria |
| `gerente` | 70 | Gerente de núcleo / unidade |
| `procurador` | 60 | Procurador(a) — corpo técnico |
| `assessor_gerencial` | 50 | Assessor(a) gerencial |
| `assessor_gabinete` | 45 | Assessor(a) de gabinete |
| `distribuidor` | 30 | Responsável por protocolo e distribuição |
| `servidor` | 15 | Servidor público genérico |
| `visualizador` | 1 | Acesso somente leitura |

### 7.2 Permissões Específicas do Fluxo de Procuradoria

| Ação | Roles autorizados |
|------|-------------------|
| `distribuir` | superadmin, admin, distribuidor, gerente |
| `redistribuir` | superadmin, admin, distribuidor, gerente |
| `elaborar_peca` | superadmin, admin, procurador, procurador_geral, subprocurador_geral |
| `elaborar_minuta` | superadmin, admin, assessor_gerencial, assessor_gabinete |
| `peticionar` (PJe/EPROC) | superadmin, admin, procurador, procurador_geral, subprocurador_geral |
| `assinar_despacho` | superadmin, admin, gerente, procurador_geral, subprocurador_geral |
| `avocar` | superadmin, admin, procurador_geral, subprocurador_geral |
| `aprovar_redistribuicao` | superadmin, admin, gerente, procurador_geral, subprocurador_geral |

### 7.3 Multi-tenancy

- Todos os modelos de negócio possuem FK para `organization.Organ`.
- O middleware/backend filtra automaticamente pelo `organ` do usuário autenticado.
- `superadmin` pode acessar dados de qualquer órgão.
- Usuários de órgãos distintos não enxergam os dados uns dos outros.

### 7.4 Autenticação

- **JWT** via `djangorestframework-simplejwt`
- Access token: curto prazo (configurável)
- Refresh token: longo prazo
- Portal do cliente: autenticação separada com `portal_password` (hash) no modelo `Client`

---

## 8. Módulos Desativados / Parcialmente Implementados

| Módulo | Status | Observação |
|--------|--------|------------|
| `financeiro` | Desativado | URL comentada em `config/urls.py`; não adequado ao contexto de procuradorias |
| Rota `/api/v1/clientes/` | Desativada | `cases.urls_clients` comentado no `config/urls.py`; clientes acessíveis via `/processos/` |
| Gov.BR Assinatura | Stub | Classe declarada, integração real não implementada |
| ICP-Brasil A1/A3 | Stub | Classe declarada, integração real não implementada |
| DocuSign | Stub | Classe declarada, integração real não implementada |
| Certisign | Stub | Classe declarada, integração real não implementada |
| SERPRO Assinador | Stub | Classe declarada, integração real não implementada |
| Sincronização de calendário externo | Stub | Endpoint `/calendario/sync/providers/` declarado, providers externos não integrados |
| Integração PJe/e-SAJ/Eproc | Parcial | Modelos e ViewSets criados; integração com APIs reais dos tribunais dependente de certificado digital e configuração por tribunal |
| NFS-e | Parcial | Endpoints criados; emissão real dependente de configuração municipal |

---

## Appendix A — Tecnologias e Infraestrutura

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| Frontend framework | Next.js | 14 (App Router) |
| Frontend linguagem | TypeScript | 5.x |
| Frontend UI | Tailwind CSS + Radix UI | — |
| Frontend estado servidor | TanStack Query | v5 |
| Backend framework | Django | 5.0 |
| Backend API | Django REST Framework (DRF) | 3.x |
| Autenticação | djangorestframework-simplejwt | — |
| Banco de dados | PostgreSQL | 15+ |
| Extensão vetorial | pgvector | — |
| Cache / Message broker | Redis | 7.x |
| Task queue | Celery | 5.x |
| Armazenamento de arquivos | Cloudflare R2 (S3-compatible) | — |
| Parsing de documentos | Docling (IBM) | — |
| Streaming | Server-Sent Events (SSE) | — |
| Containerização | Docker / Docker Compose | — |

---

## Appendix B — Contagem de Rotas e Endpoints

| Categoria | Quantidade |
|-----------|------------|
| Rotas frontend — públicas | 5 |
| Rotas frontend — portal do cliente | 13 |
| Rotas frontend — dashboard (staff) | ~106 |
| **Total de rotas frontend** | **~124** |
| Apps backend com URLs | 21 |
| Endpoints backend (estimativa) | ~350+ |

---

*Documento gerado para auditoria QA da plataforma verus.ai — versão 1.0.0 — 2026-06-11.*
*Baseado na análise estática de: `backend/apps/*/urls.py`, `backend/apps/*/models.py`, `frontend/src/app/**` e `backend/config/urls.py`.*
