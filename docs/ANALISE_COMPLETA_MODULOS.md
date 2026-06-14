# RELATÓRIO FINAL — ANÁLISE COMPLETA DE MÓDULOS, FLUXOS E INTEGRAÇÕES DO VERUS.AI

> **Status**: ✅ Análise concluída | **Data**: 14/06/2026 | **Versão**: 1.0
> **Agentes**: 5 salas especializadas | **Fonte**: Código-fonte + documentação

---

## 1. AUDITORIA INICIAL

| Item | Evidência | Arquivo/Fonte | Observação |
|---|---|---|---|
| Stack detectada | Django 5.0 + DRF 3.15 / Next.js 16.1 + React 19.2 | `backend/requirements.txt`, `frontend/package.json` | Python 3.11, Node 22, TypeScript 5.x |
| Frameworks | Django REST Framework, PostgreSQL+pgvector, Redis, Celery | `config/settings/local.py` | 3 LLM providers (Anthropic, OpenAI, WatsonX) |
| Módulos principais | 21 apps Django (19 ativos + financeiro desativado) | `config/urls.py`, `INSTALLED_APPS` | ~360 endpoints, ~99 modelos |
| Pontos de entrada | `config/urls.py` (backend), `frontend/src/app/` (frontend), proxy Next.js | Route Handler e URLs config | Auth via JWT (simplejwt) |
| Testes existentes | pytest (backend), Jest (frontend) | `pytest.ini`, `jest.config.js` | Cobertura concentrada em cases app |
| Riscos iniciais | Financeiro desativado no backend mas frontend chama; RAG duplicado; módulo collaboration isolado | Verificado em grep | 3 problemas confirmados |

## 2. MAPA DA ARQUITETURA — GRAFO DE DEPENDÊNCIAS

```
organization (raiz, 0 dependências externas)
├── accounts → organization (User.organ, User.unit)
│   ├── core → accounts (AuditLog.user)
│   ├── cases → accounts + organization + intelligent_assistant + simulations + workflow_execution
│   ├── intelligent_assistant → accounts + core + cases
│   ├── agents → accounts + kb
│   ├── forms → accounts + intelligent_assistant
│   ├── templates → accounts + intelligent_assistant + forms
│   ├── documents → accounts + templates + kb + forms
│   ├── kb → accounts
│   ├── rag → accounts + documents + kb
│   ├── collaboration → accounts (módulo em silo potencial)
│   ├── copilot → accounts (orquestrador invisível)
│   ├── integration → accounts
│   ├── jurisprudence → accounts
│   ├── legal_library → accounts
│   ├── simulations → accounts + cases
│   ├── workflow_definition → accounts + organization
│   ├── workflow_execution → accounts + organization + workflow_definition
│   └── signature → accounts + organization
└── financeiro (DESATIVADO — código existe mas URLs não registradas)
```

## 3. MAPA DOS FLUXOS PRINCIPAIS

### Fluxo A — Ciclo de Vida do Processo (cases)
```
Criação (User) → Designação → Prazos → Documentos → Workflow BPMN → Tarefas → Gateway → Encerrar
  Módulos: accounts → cases → organization → workflow_execution
  Dados: LegalCase → LegalDeadline → CaseTask → CaseDocument → FlowInstance
```

### Fluxo B — Geração de Documento com IA
```
Blueprint → Formulário → Upload → Geração IA (SSE) → Revisão → Exportação PDF/DOCX → R2
  Módulos: intelligent_assistant → core (LLMProvider) → kb (RAG) → templates → forms
  Dados: DocumentBlueprint → IntelligentSession → GeneratedDocument → R2 Storage
```

### Fluxo C — Workflow BPMN
```
Admin cria template (workflow_definition) → Publica → Inicia instância → Tasks → Gateways → Encerra
  Módulos: workflow_definition → workflow_execution → accounts → organization
  Dados: FlowTemplate → FlowInstance → TaskInstance → ExecutionEvent
```

### Fluxo D — Copilot Chat
```
Abrir sessão → Chat stream (SSE) → RAG → LLM → Histórico → Compartilhar
  Módulos: copilot → cases (contexto) → kb (RAG) → core (LLM)
  Tasks: sync_user_knowledge_bases (noturna)
```

### Fluxo E — Simulação (18 tipos)
```
Criar simulação → Upload docs → Executar (SSE) → Debate IA → Veredicto
  Módulos: simulations → cases → core (LLM)
  18 endpoints: jury, judge, stf, stj, tst, trt, tre, tse, jec, jecrim, etc.
```

## 4. PONTOS DE DECISÃO CRÍTICOS

| ID | Ponto | Condição | Caminho A | Caminho B | Risco |
|---|---|---|---|---|---|
| D01 | Auth JWT | token expirado? | Refresh automático | Redirect /login | Refresh blacklist não tratado |
| D02 | Workflow Gateway | exclusive_gateway | Caminho definido | Erro/fallback | Quem define? |
| D03 | Geração IA | LLM provider falha? | Retry/fallback | Erro | Fallback não confirmado |
| D04 | Simulação | Demora >2h | cleanup_stuck marca failed | --- | Falso positivo possível |
| D05 | Organ filter | User.organ existe? | Filtra queries | Acessa todos dados | Risco multi-tenancy |

## 5. CONSOLIDAÇÃO DAS SALAS DE ANÁLISE — TOP 15 RISCOS GLOBAIS

| # | Gravidade | Problema | Sala(s) | Impacto no fluxo |
|---|---|---|---|---|
| 1 | 🔴 **CRÍTICO** | Frontend acessa `/api/v1/clientes/` (portal do cliente) mas rota comentada no backend | S1+4 | Páginas de clientes e contratos quebradas em produção (HTTP 404) |
| 2 | 🔴 **CRÍTICO** | Multi-tenancy quebrado em 7 apps (intelligent_assistant, forms, documents, simulations, copilot, kb, rag) — não filtram por `organ` | S2 | Usuários de diferentes órgãos podem acessar dados uns dos outros |
| 3 | 🟠 **ALTO** | Duas pipelines concorrentes de geração de documentos: intelligent_assistant vs documents app | S2 | Duplicação de estado; documento gerado em um não aparece no outro |
| 4 | 🟠 **ALTO** | Financeiro desativado (backend urls comentado) mas frontend ainda tem 6+ chamadas para `/api/v1/processos/financeiro/*` | S5+6 | Usuário vê erro 404 ao acessar páginas financeiras |
| 5 | 🟠 **ALTO** | `process_document_task` em kb/tasks.py NUNCA chamada com `.delay()` | S5+6 | Upload de documentos KB nunca processa chunking/embeddings em background |
| 6 | 🟠 **ALTO** | Upload de arquivos sem validação MIME real (apenas extensão) | S7 | `.pdf` renomeado de `.exe` passa na validação |
| 7 | 🟠 **ALTO** | AuditLog armazena dados sensíveis sem sanitização (CPF, senhas, tokens) | S7 | Dados sensíveis vazam para logs de auditoria |
| 8 | 🟠 **ALTO** | Redis é SPOF (Single Point of Failure) para Celery — sem fallback de broker | S2 | Redis cair = 7 periodic tasks param + upload R2 falha |
| 9 | 🟠 **ALTO** | Dois sistemas de permissão conflitantes: `accounts/permissions.py` (granular) vs `accounts/models.py` (BPMN) | S3+S7 | Role inconsistente: procurador pode assinar por um sistema mas não pelo outro |
| 10 | 🟠 **ALTO** | 15/18 tipos de simulação sem teste; SSE streaming sem teste; Celery tasks sem teste | S5+6 | Regressão não detectada em funcionalidades críticas de IA |
| 11 | 🟡 **MÉDIO** | `FlowInstance` sem status `failed` — erros durante workflow deixam fluxo como `running` sem limpar `active_flow` | S1+4 | Workflow travado nunca é limpo; bloqueia reexecução |
| 12 | 🟡 **MÉDIO** | Duplicação de pipeline RAG: app `rag` (JSON manual) vs intelligent_assistant (pgvector integrado) | S2+S5+6 | Dados RAG fragmentados em dois sistemas |
| 13 | 🟡 **MÉDIO** | 14 serviços de simulação com código minimamente compartilhado; manutenção cara | S3 | Alteração em um tipo de simulação exige replicar em 14+ arquivos |
| 14 | 🟡 **MÉDIO** | Gateway exclusive com fallback silencioso: se `gateway_choice` inválido, usa primeira aresta sem notificar | S3 | Usuário pode seguir caminho não intencional |
| 15 | 🟢 **BAIXO** | Módulo `collaboration` completamente isolado — nenhum outro app o referencia | S2 | Funcionalidade existe mas não é integrada ao restante do sistema |

## 6. MATRIZ DE INTEGRAÇÃO ENTRE MÓDULOS

| Origem | Destino | Tipo | Contrato | Status |
|---|---|---|---|---|
| intelligent_assistant | cases | FK | IntelligentSession.case → LegalCase | ✅ OK |
| cases | intelligent_assistant | FK | CaseDocument.linked_document → GeneratedDocument | ✅ OK |
| cases | workflow_execution | O2O | LegalCase.active_flow → FlowInstance | ⚠️ Signal limpa ao completar; sem status `failed` |
| intelligent_assistant | core | FK | DocumentBlueprint.document_type → DocumentType | ✅ OK |
| intelligent_assistant | kb | M2M | SectionAgentConfig.knowledge_bases → KnowledgeBase | ⚠️ Redundante (2 formas de vinculo) |
| cases ↔ simulations | FK | Simulation.case → LegalCase | ⚠️ Resultado não vinculado a CaseDocument |
| Frontend → clientes | REST | /api/v1/clientes/* | 🔴 ROTA DESATIVADA |
| Frontend → financeiro | REST | /api/v1/processos/financeiro/* | 🔴 ROTA DESATIVADA |
| Frontend → Backend | Proxy | Route Handler Next.js → Django | ✅ OK |
| Celery → Redis | Broker | CELERY_BROKER_URL | 🔴 Sem fallback |
| R2 → intelligent_assistant | Task | save_pdf/docx_to_r2_task | ⚠️ Sem fallback local |
| intelligent_assistant → LLM | API | UnifiedLLMService → Anthropic/OpenAI/WatsonX | ✅ Com retry 3x |
| permission system 1 vs 2 | — | permissions.py vs models.py | 🔴 Conflitantes |

## 7. MÓDULOS EM SILO

| Módulo | Risco | Evidência |
|---|---|---|
| **collaboration** | 🔴 ALTO | Nenhuma FK externa; `document_id` é UUID livre sem FK |
| **documents** | 🟠 ALTO | Duplicação de conceito "documento" com intelligent_assistant |
| **rag** | 🟠 ALTO | Pipeline RAG obsoleta (JSON manual) vs sistema KB+pgvector |
| **copilot** | 🟡 MÉDIO | Orquestrador sem FK; `source_id` é campo livre |
| **financeiro** | 🔴 DESATIVADO | App existe mas URLs não registradas; frontend quebrado |
