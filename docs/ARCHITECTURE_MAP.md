# Verus.AI — Mapa Completo de Arquitetura e Funcionalidades

## Stack

| Camada | Tecnologia | Versao |
|--------|-----------|--------|
| Backend | Django 5.0 + DRF 3.15 | Python 3.11 |
| Frontend | Next.js 16.1 + React 19.2 | TypeScript 5.x |
| Banco | PostgreSQL + pgvector | 15+ |
| Cache/Broker | Redis 7 | Celery 5.3 |
| UI | Radix UI + Tailwind CSS 3.4 | shadcn/ui |
| LLM | WatsonX / OpenAI / Anthropic (legado) | UnifiedLLMService |
| Storage | Cloudflare R2 (S3-compativel) | boto3 |
| Email | Resend | SMTP + API REST |
| Vetores | ChromaDB | embeddings |

---

## Apps Django (19 apps, 88+ models)

| App | Proposito | Models principais |
|-----|----------|-------------------|
| **accounts** | Auth, roles, notificacoes, LGPD, equipes | User, Notification, Team, BrandSettings, ConsentTerm |
| **cases** | Gestao de processos judiciais | LegalCase, Client, LegalDeadline, CaseTask, LegalContract |
| **organization** | Multi-tenancy (orgaos e unidades) | Organ, Unit |
| **workflow_definition** | Design de fluxos BPMN | FlowTemplate, FlowNode, FlowEdge, FlowVersion |
| **workflow_execution** | Execucao runtime de workflows | FlowInstance, TaskInstance, TaskRequest, ExecutionEvent |
| **copilot** | Assistente conversacional IA | CopilotConfig, UserKnowledgeEntry, CopilotSessionShare |
| **intelligent_assistant** | Geracao de documentos com IA | IntelligentSession, DocumentBlueprint, BlueprintSection, GeneratedDocument |
| **documents** | Geradores e versionamento | DocumentGenerator, Document, DocumentVersion |
| **forms** | Formularios dinamicos | FormTemplate, FormField, FormResponse |
| **simulations** | Simulacoes de juri/juiz/tribunal | Simulation, JuryMember, JudgeProfile, MinisterProfile |
| **kb** | Knowledge Base para RAG | Document (KB), DocumentChunk, ChromaCollection |
| **rag** | Pipeline RAG | RAGIndex, RAGQuery, RAGResult |
| **templates** | Templates de documento (DOCX/HTML) | DocumentTemplate, TemplateSection |
| **core** | Config global do sistema | LLMProvider, SystemModule, AuditLog |
| **jurisprudence** | Jurisprudencia e precedentes | JurisprudenceCase, JurisprudenceAnalysis |
| **collaboration** | Colaboracao em tempo real | CollaborationSession, DocumentShare |
| **integration** | Integracoes externas (PJe, DataJud) | TribunalIntegration, APIKey |
| **legal_library** | Argumentos e precedentes legais | LegalArgument, LegalPrecedent |
| **agents** | Agentes de IA especializados | Agent, AgentTool, AgentExecution |

---

## Fluxos Principais

### A) Ciclo de Vida do Processo

```
Criar Processo → Designar Procurador → Definir Prazos
     ↓                                       ↓
Gerar Documentos (IA)              Celery monitora vencimento
     ↓                                       ↓
Workflow BPMN                      Notificacoes automaticas
     ↓
Tarefas atribuidas → Gateway (Aprovar/Rejeitar) → Encerrar
```

### B) Geracao de Documento com IA

```
1. Selecionar Blueprint (peticao, parecer, etc.)
2. Preencher formulario (FormTemplate)
3. Upload de documentos (opcional)
4. IA gera cada secao:
   a) RAG busca contexto na Knowledge Base
   b) LLM gera conteudo (SSE streaming)
   c) Usuario revisa e edita
5. Exportar PDF/DOCX → Cloudflare R2
6. Vincular ao processo
```

### C) Copilot Chat

```
1. Abrir sessao → contexto do processo/prazo/documento
2. Enviar mensagem
3. Backend:
   a) Sync Knowledge Base do usuario
   b) RAG recupera contexto relevante
   c) LLM stream (SSE token por token)
4. Historico salvo
5. Compartilhar sessao (share_code)
6. Exportar conversa (MD/PDF/JSON)
```

### D) Workflow BPMN

```
1. Admin cria template no editor visual (XYFlow)
   - Swim lanes (por papel: distribuidor, procurador, gerente)
   - Tarefas, gateways exclusivos/paralelos, eventos
2. Publicar template
3. Iniciar instancia vinculada a processo
4. Execucao:
   - start_event → criar TaskInstance
   - user_task → aguarda usuario completar
   - exclusive_gateway → avaliar gateway_choice
   - parallel_gateway → criar tasks em paralelo
   - end_event → FlowInstance.status='completed'
5. Cada acao logada em ExecutionEvent (imutavel)
```

### E) Simulacao de Juri/Juiz

```
1. Criar simulacao vinculada a processo
2. Upload de documentos (denuncia, defesa, provas)
3. Executar (SSE streaming):
   - Fase 1: Gerar perfis dos jurados (LLM)
   - Fase 2: Abertura pelo juiz presidente
   - Fase 3: Acusacao (promotor via LLM + RAG)
   - Fase 4: Defesa (defensor via LLM + RAG)
   - Fase 5: Deliberacao (cada jurado vota)
   - Fase 6: Veredicto final
4. Resultado: condenacao/absolvicao + fundamentacao
```

### F) Autenticacao JWT

```
Login → access_token (1h) + refresh_token (7d)
     ↓
Toda request: Authorization: Bearer <token>
     ↓
Token expirou → refresh automatico (single-flight)
     ↓
Refresh expirou → redirect para /login
     ↓
Logout → blacklist do refresh token
```

---

## Dependencias entre Apps

```
accounts ──→ organization (User.organ)
    ↓
cases ──→ accounts (advogado_responsavel)
    ↓    ──→ organization (LegalCase.organ)
    ↓    ──→ workflow_execution (active_flow)
    ↓
copilot ──→ cases (contexto do processo)
    ↓      ──→ kb (RAG retrieval)
    ↓      ──→ intelligent_assistant (sessoes)
    ↓
intelligent_assistant ──→ core (LLMProvider)
    ↓                   ──→ kb (RAG)
    ↓                   ──→ templates (DocumentTemplate)
    ↓                   ──→ forms (FormTemplate)
    ↓
workflow_execution ──→ workflow_definition (FlowTemplate)
    ↓                ──→ organization (Organ)
    ↓                ──→ accounts (User assignment)
    ↓
simulations ──→ cases (Simulation.case)
    ↓          ──→ core (LLM provider)
```

---

## Servicos Externos

| Servico | Uso | Configuracao |
|---------|-----|-------------|
| IBM WatsonX | LLM principal | WATSONX_API_KEY, WATSONX_PROJECT_ID |
| OpenAI | LLM alternativo | OPENAI_API_KEY |
| Resend | Email transacional | RESEND_API_KEY |
| Cloudflare R2 | Storage de documentos | R2_ACCESS_KEY, R2_SECRET_KEY |
| ChromaDB | Vector DB para RAG | Embedded ou CHROMADB_HOST |
| CNJ DataJud | Dados de processos | API publica |
| PJe / e-SAJ | Integracao tribunal | Credenciais por orgao |
| Redis | Cache + Celery broker | REDIS_URL |

---

## Celery Tasks (8 periodicas + on-demand)

| Task | Schedule | Funcao |
|------|----------|--------|
| check_upcoming_deadlines | Cada hora | Alerta prazos vencendo |
| analyze_idle_cases | Diario 8h | Detecta processos parados |
| check_pending_documents | Diario 9h | Sessoes de geracao pendentes |
| process_user_reminders | Cada 5 min | Processa lembretes |
| nightly_case_analysis | Meia-noite | Resumo diario por procurador |
| sync_user_knowledge_bases | 2h da manha | Sincroniza KB dos usuarios |
| cleanup_stuck_simulations | Cada 2h | Limpa simulacoes travadas |
| save_pdf/docx_to_r2 | On-demand | Exporta documentos para R2 |

---

## Frontend — Hooks (40+)

| Hook | Proposito |
|------|----------|
| use-auth | JWT login/logout/refresh |
| use-cases | CRUD processos |
| use-deadlines | Prazos judiciais |
| use-copilot | Chat streaming IA |
| use-documents | Documentos gerados |
| use-blueprints | Blueprints de documentos |
| use-simulations | Simulacoes juri/juiz |
| use-workflows | Templates BPMN |
| use-contracts | Contratos |
| use-brand-settings | Tema/marca |
| use-organization | Orgaos/unidades |
| use-notifications | Notificacoes in-app |
| use-kb | Knowledge Base |
| use-rag | Consultas RAG |
| ... | +25 outros hooks |

---

## Seguranca e Compliance

- **LGPD**: ConsentTerm, ConsentRecord, DataSubjectRequest
- **Auditoria**: ExecutionEvent (imutavel) + AuditLog
- **JWT**: access 1h + refresh 7d + blacklist apos rotacao
- **Multi-tenancy**: Isolamento por Organ em queries
- **RBAC**: 15+ roles com hierarquia (superadmin=100 → visualizador=1)
- **CORS**: Configurado por ambiente
- **Upload**: Validacao MIME + limite 50MB
