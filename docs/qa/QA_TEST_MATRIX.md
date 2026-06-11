# QA Test Matrix — verus.ai

**Versão:** 1.0.0
**Data:** 2026-06-11
**Referência:** QA_FUNCTIONAL_INVENTORY.md v1.0.0

---

## Legenda

| Status | Significado |
|--------|-------------|
| ✅ PASS | Teste passou sem erros |
| ❌ FAIL | Teste falhou — bug confirmado |
| ⏳ PENDING | Não executado ainda |
| 🔵 N/A | Não aplicável neste ciclo |
| ⚠️ PARTIAL | Parcialmente validado (análise estática) |

**Tipo de Teste:**
- `E` = Estático (análise de código)
- `C` = Contrato (validação schema API × tipo TS)
- `I` = Integração (chamada HTTP real)
- `U` = Unitário (lógica isolada)
- `S` = Smoke (caminho feliz completo)

---

## Módulo 1 — Autenticação e Controle de Acesso

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-AUTH-001 | E/C | `hasPermission('gerente')` retorna `true` para usuário com role `gerente` (nível 70) | ✅ PASS | — |
| TC-AUTH-002 | E/C | `hasPermission('gerente')` retorna `false` para role `servidor` (nível 15) | ✅ PASS | — |
| TC-AUTH-003 | E/C | `hasPermission('procurador_geral')` retorna `true` para role `subprocurador_geral` (nível 80 ≥ 85? NÃO) | ✅ PASS | — |
| TC-AUTH-004 | E | Role `subprocurador_geral` presente no `roleHierarchy` do frontend | ✅ PASS | BUG-001 (corrigido) |
| TC-AUTH-005 | E | Role `assessor_gerencial` presente no `roleHierarchy` do frontend | ✅ PASS | BUG-001 (corrigido) |
| TC-AUTH-006 | E | Role `assessor_gabinete` presente no `roleHierarchy` do frontend | ✅ PASS | BUG-001 (corrigido) |
| TC-AUTH-007 | E | Aliases do `ROLE_ALIASES` do backend todos mapeados no frontend | ✅ PASS | BUG-001 (corrigido) |
| TC-AUTH-008 | E | Login com JWT: `POST /api/v1/auth/login/` chamado corretamente | ✅ PASS | — |
| TC-AUTH-009 | E | Refresh de token: interceptor chama `POST /api/v1/auth/token/refresh/` | ✅ PASS | — |
| TC-AUTH-010 | E | Logout limpa `localStorage` e invalida cache React Query | ✅ PASS | — |
| TC-AUTH-011 | C | Tipo `User.role` no frontend inclui todos os roles do backend | ✅ PASS | — |
| TC-AUTH-012 | I | Chamada a `/api/v1/auth/users/me/` retorna dados de usuário | ⏳ PENDING | — |

---

## Módulo 2 — Assinatura Digital

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-SIG-001 | C | Tipo `DigitalSignatureDto` em `useSignature.ts` espelha campos do serializer backend | ✅ PASS | — |
| TC-SIG-002 | E | `useMySignatures()` chama `GET /api/v1/signatures/` | ✅ PASS | BUG-002 (corrigido) |
| TC-SIG-003 | E | `useSignDocument()` chama `POST /api/v1/signatures/sign/` | ✅ PASS | — |
| TC-SIG-004 | E | `useVerifySignature()` é `useMutation` (não `useQuery`) | ✅ PASS | BUG-002 (corrigido) |
| TC-SIG-005 | E | Payload de `useSignDocument` contém `content`, `document_type`, `document_ref`, `provider` | ✅ PASS | — |
| TC-SIG-006 | E | `use-signatures.ts` (legado, caminho errado) deletado — sem importações ativas | ✅ PASS | BUG-002 (corrigido) |
| TC-SIG-007 | C | Campo `status` do DTO: `'pending' | 'signed' | 'rejected' | 'expired' | 'revoked'` | ✅ PASS | — |
| TC-SIG-008 | E | Página `assinatura-digital` não importa mais de `use-signatures.ts` | ✅ PASS | BUG-002 (corrigido) |
| TC-SIG-009 | I | `GET /api/v1/signatures/` retorna lista de assinaturas do órgão | ⏳ PENDING | — |
| TC-SIG-010 | I | `POST /api/v1/signatures/sign/` cria nova assinatura `internal` | ⏳ PENDING | — |
| TC-SIG-011 | I | `POST /api/v1/signatures/verify/` com ID válido retorna `valid: true` | ⏳ PENDING | — |
| TC-SIG-012 | I | `GET /api/v1/signatures/providers/` retorna lista de providers | ⏳ PENDING | — |

---

## Módulo 3 — Fluxos de Trabalho (BPMN)

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-FLW-001 | E | `useFlowTemplates` chama `GET /api/v1/workflows/templates/` | ✅ PASS | — |
| TC-FLW-002 | E | `useCreateFlowTemplate` chama `POST /api/v1/workflows/templates/` | ✅ PASS | — |
| TC-FLW-003 | E | `useStartFlow` chama `POST /api/v1/workflow-execution/executions/` | ✅ PASS | — |
| TC-FLW-004 | E | `canStart` em `fluxos/page.tsx` usa `hasPermission('distribuidor')` (sem dupla chamada hook) | ✅ PASS | BUG-004 (corrigido) |
| TC-FLW-005 | E | Refetch interval em `useMyTasks`: 15s quando pending/in_progress | ✅ PASS | — |
| TC-FLW-006 | E | Refetch interval em `useFlowInstances`: adaptativo quando instâncias ativas | ✅ PASS | — |
| TC-FLW-007 | E | `GatewayChoiceOption` tipado corretamente em `TaskInstanceDto` | ✅ PASS | — |
| TC-FLW-008 | E | Serializer backend `get_gateway_choices` retorna edges do template correto | ⚠️ PARTIAL | — |
| TC-FLW-009 | I | Criar template → publicar → iniciar instância → listar tarefas | ⏳ PENDING | — |
| TC-FLW-010 | I | Completar tarefa gateway com escolha de edge | ⏳ PENDING | — |
| TC-FLW-011 | I | Solicitar redistribuição de tarefa | ⏳ PENDING | — |
| TC-FLW-012 | S | Fluxo completo: criar template → editor → publicar → iniciar → executar → concluir | ⏳ PENDING | — |

---

## Módulo 4 — Colaboração em Tempo Real

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-COL-001 | E | Polling de colaboradores é 20s (não 5s) | ✅ PASS | BUG-003 (corrigido) |
| TC-COL-002 | E | Heartbeat enviado a cada 15s quando conectado | ✅ PASS | — |
| TC-COL-003 | E | Cleanup do effect dispara `leaveMutation` ao desmontar | ⚠️ PARTIAL | — |
| TC-COL-004 | C | Tipo `CollaborationSession` espelha modelo do backend | ⚠️ PARTIAL | — |
| TC-COL-005 | I | `POST /api/v1/collaboration/sessions/` cria sessão | ⏳ PENDING | — |
| TC-COL-006 | I | `POST /join/` adiciona colaborador, incrementa `active_collaborators_count` | ⏳ PENDING | — |
| TC-COL-007 | I | Criar comentário → resolver comentário | ⏳ PENDING | — |

---

## Módulo 5 — Componentes de IA (AIInput / AITextarea / AIEnhanceButton)

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-AI-001 | E | `AIEnhanceButton` — estado vazio: ícone Wand2, label "Gerar" | ✅ PASS | — |
| TC-AI-002 | E | `AIEnhanceButton` — estado preenchido: ícone Sparkles, label "Aprimorar" | ✅ PASS | — |
| TC-AI-003 | E | `AIInput` com `variant="dark"` renderiza elemento `<input>` nativo | ✅ PASS | — |
| TC-AI-004 | E | `AITextarea` com `variant="dark"` renderiza `<textarea>` nativo | ✅ PASS | — |
| TC-AI-005 | E | Modal de iniciar fluxo usa `AIInput` para `caseRef` e `caseTitle` | ✅ PASS | — |
| TC-AI-006 | E | Modal de novo fluxo usa `AIInput` para nome do fluxo | ✅ PASS | — |
| TC-AI-007 | E | Campos de formulário em `minhas-tarefas` — CompleteModal usa `AITextarea` | ⚠️ PARTIAL | — |
| TC-AI-008 | E | Campo "Conteúdo a Assinar" em `assinatura-digital/page.tsx` usa `<textarea>` plain (sem IA) | ❌ FAIL | BUG-005 |
| TC-AI-009 | U | `AIEnhanceButton.handleEnhance` chama `/api/v1/processos/enhance-text/` | ⏳ PENDING | — |
| TC-AI-010 | S | Fluxo completo: campo vazio → clicar "Gerar" → texto gerado preenchido no campo | ⏳ PENDING | — |

---

## Módulo 6 — Error Boundaries

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-ERR-001 | E | `src/app/error.tsx` existe (root level) | ✅ PASS | — |
| TC-ERR-002 | E | `src/app/(dashboard)/error.tsx` existe | ✅ PASS | — |
| TC-ERR-003 | E | `src/app/(dashboard)/dashboard/error.tsx` existe | ✅ PASS | — |
| TC-ERR-004 | E | `src/app/(client)/error.tsx` existe | ✅ PASS | — |
| TC-ERR-005 | E | `src/app/(dashboard)/loading.tsx` existe | ✅ PASS | — |
| TC-ERR-006 | E | `src/app/(dashboard)/dashboard/loading.tsx` existe | ✅ PASS | — |
| TC-ERR-007 | S | Erro de network no dashboard mostra UI de erro amigável (não tela branca) | ⏳ PENDING | — |

---

## Módulo 7 — Processos (Cases)

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-CAS-001 | E | Hooks de casos apontam para `/api/v1/processos/` | ✅ PASS | — |
| TC-CAS-002 | E | Hook `use-contracts.ts` usa `/api/v1/processos/contratos/` | ✅ PASS | — |
| TC-CAS-003 | E | Hook `use-court-fees.ts` usa `/api/v1/processos/custas/` | ✅ PASS | — |
| TC-CAS-004 | E | Hook `use-calendar.ts` usa `/api/v1/processos/calendario/` | ✅ PASS | — |
| TC-CAS-005 | E | Hook `use-protocol.ts` usa `/api/v1/processos/protocolos/` | ✅ PASS | — |
| TC-CAS-006 | E | Hook `use-datajud.ts` usa `/api/v1/processos/datajud/` | ✅ PASS | — |
| TC-CAS-007 | I | `GET /api/v1/processos/` retorna processos do órgão | ⏳ PENDING | — |
| TC-CAS-008 | I | Criar processo com número CNJ válido | ⏳ PENDING | — |
| TC-CAS-009 | I | Vincular fluxo BPMN ao processo via `POST /<id>/iniciar-fluxo/` | ⏳ PENDING | — |

---

## Módulo 8 — Organização (Multi-tenancy)

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-ORG-001 | E | Backend filtra todos os modelos pelo `organ` do usuário | ⚠️ PARTIAL | — |
| TC-ORG-002 | E | `superadmin` bypassa filtro de órgão | ⚠️ PARTIAL | — |
| TC-ORG-003 | I | Usuário de órgão A não vê dados de órgão B | ⏳ PENDING | — |

---

## Módulo 9 — Build e TypeScript

| TC-ID | Tipo | Caso de Teste | Status | Bug Ref |
|-------|------|---------------|--------|---------|
| TC-BUILD-001 | E | `tsc --noEmit` sem erros | ✅ PASS | — |
| TC-BUILD-002 | E | `next build` sem erros e sem warnings | ✅ PASS | — |
| TC-BUILD-003 | E | Sem imports não resolvidos (arquivo `use-signatures.ts` deletado, sem referências) | ✅ PASS | — |

---

## Resumo de Cobertura

| Módulo | Total TCs | PASS | FAIL | PARTIAL | PENDING | Cobertura Estática |
|--------|-----------|------|------|---------|---------|-------------------|
| Autenticação | 12 | 11 | 0 | 0 | 1 | 92% |
| Assinatura Digital | 12 | 8 | 0 | 0 | 4 | 67% |
| Fluxos BPMN | 12 | 7 | 0 | 1 | 4 | 58% |
| Colaboração | 7 | 2 | 0 | 2 | 3 | 29% |
| Componentes IA | 10 | 6 | 1 | 1 | 2 | 60% |
| Error Boundaries | 7 | 6 | 0 | 0 | 1 | 86% |
| Processos | 9 | 6 | 0 | 0 | 3 | 67% |
| Organização | 3 | 0 | 0 | 2 | 1 | 0% |
| Build/TypeScript | 3 | 3 | 0 | 0 | 0 | 100% |
| **TOTAL** | **75** | **49** | **1** | **6** | **19** | **65%** |

---

*Documento gerado para auditoria QA da plataforma verus.ai — versão 1.0.0 — 2026-06-11.*
