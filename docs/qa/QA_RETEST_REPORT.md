# QA Retest Report — verus.ai

**Versão:** 1.0.0
**Data:** 2026-06-11
**Ciclo:** Wave 1 — Reteste das Correções Aplicadas

---

## 1. Objetivo

Verificar que os bugs identificados na Wave 1 foram corrigidos corretamente e que as correções não introduziram regressões.

---

## 2. Bugs Retestados

---

### BUG-001 — Role Hierarchy Misalignment ✅ CORRIGIDO

**Correção aplicada:** `src/hooks/use-auth.ts` — adicionados roles `subprocurador_geral`, `assessor_gerencial`, `assessor_gabinete` + aliases do ROLE_ALIASES.

**Testes de reteste:**

| # | Verificação | Método | Resultado |
|---|-------------|--------|-----------|
| 1 | `subprocurador_geral` presente com nível 80 no `roleHierarchy` | Leitura do arquivo | ✅ PASS |
| 2 | `assessor_gerencial` presente com nível 50 | Leitura do arquivo | ✅ PASS |
| 3 | `assessor_gabinete` presente com nível 45 | Leitura do arquivo | ✅ PASS |
| 4 | Todos os aliases (`socio`, `gestor`, `coordenador`, etc.) presentes | Leitura do arquivo | ✅ PASS |
| 5 | `tsc --noEmit` sem erros após mudança | Compilação | ✅ PASS |
| 6 | `User.role` tipo union inclui todos os roles | Leitura de `types/index.ts` | ✅ PASS |

**Regressões identificadas:** Nenhuma.

**Veredicto:** ✅ BUG CORRIGIDO — RETESTE APROVADO

---

### BUG-002 — Assinatura Digital com Hook Errado ✅ CORRIGIDO

**Correção aplicada:**
- `assinatura-digital/page.tsx` migrado para `useSignature.ts`
- `use-signatures.ts` deletado
- `useMySignatures()` adicionado a `useSignature.ts`

**Testes de reteste:**

| # | Verificação | Método | Resultado |
|---|-------------|--------|-----------|
| 1 | Nenhum arquivo importa de `use-signatures.ts` | `grep -r "use-signatures"` | ✅ PASS |
| 2 | `use-signatures.ts` não existe mais no sistema de arquivos | `find` | ✅ PASS |
| 3 | `assinatura-digital/page.tsx` importa de `@/hooks/useSignature` | Leitura do arquivo | ✅ PASS |
| 4 | `useMySignatures` chama `GET /api/v1/signatures/` | Leitura de `useSignature.ts` | ✅ PASS |
| 5 | `useSignDocument` chama `POST /api/v1/signatures/sign/` | Leitura de `useSignature.ts` | ✅ PASS |
| 6 | `useVerifySignature` é `useMutation` (não `useQuery`) | Leitura de `useSignature.ts` | ✅ PASS |
| 7 | Campos da página usam `sig.document_title`, `sig.content_hash`, `sig.status === 'signed'` | Leitura de `page.tsx` | ✅ PASS |
| 8 | `tsc --noEmit` sem erros após migração | Compilação | ✅ PASS |
| 9 | `next build` sem erros | Build | ✅ PASS |

**Verificação de regressão:**

| # | Verificação de Regressão | Resultado |
|---|--------------------------|-----------|
| R1 | Outros hooks de signature (`useDocumentSignatures`, `useSignatureProviders`, `useSignDocument`) permanecem funcionais | ✅ Verificado — não alterados |
| R2 | Nenhuma outra página importa de `use-signatures.ts` | ✅ Verificado — único consumidor era `assinatura-digital/page.tsx` |
| R3 | `useSignature.ts` exporta `useMySignatures` sem quebrar exports existentes | ✅ Verificado — adicionado sem remover nada |

**Veredicto:** ✅ BUG CORRIGIDO — RETESTE APROVADO

---

### BUG-003 — Polling Excessivo de Colaboradores ✅ CORRIGIDO

**Correção aplicada:** `src/hooks/use-collaboration.ts:150` — `refetchInterval: 5000` → `refetchInterval: 20_000`

**Testes de reteste:**

| # | Verificação | Método | Resultado |
|---|-------------|--------|-----------|
| 1 | `refetchInterval` de colaboradores é `20_000` | Leitura do arquivo | ✅ PASS |
| 2 | Nenhum outro `refetchInterval` abaixo de 10s no hook | Leitura do arquivo | ✅ PASS |
| 3 | Heartbeat (mutation manual, não polling) permanece a 15s | Leitura do arquivo linha 272 | ✅ PASS |

**Análise de impacto:**
- **Antes:** 12 req/min por usuário por sessão = 720 req/hora
- **Depois:** 3 req/min por usuário por sessão = 180 req/hora
- **Redução:** 75% de requisições de polling

**Regressões identificadas:** Nenhuma.

**Veredicto:** ✅ BUG CORRIGIDO — RETESTE APROVADO

---

### BUG-004 — Dupla Chamada de `useAuth()` ✅ CORRIGIDO

**Correção aplicada:** `src/app/(dashboard)/dashboard/fluxos/page.tsx` — removida segunda chamada de `useAuth()`, `hasPermission` desestruturado do hook único.

**Testes de reteste:**

| # | Verificação | Método | Resultado |
|---|-------------|--------|-----------|
| 1 | Apenas uma chamada de `useAuth()` no componente `FluxosPage` | Leitura do arquivo | ✅ PASS |
| 2 | `canStart = hasPermission('distribuidor')` (não `user ? useAuth()...`) | Leitura do arquivo | ✅ PASS |
| 3 | Constante `MIN_START_LEVEL` (orfã) removida | Leitura do arquivo | ✅ PASS |
| 4 | `tsc --noEmit` sem erros | Compilação | ✅ PASS |

**Regressões identificadas:** Nenhuma.

**Veredicto:** ✅ BUG CORRIGIDO — RETESTE APROVADO

---

## 3. BUG-005 — AIInput em Formulários (PENDENTE)

**Status atual:** ⏳ PENDENTE — aguarda implementação

**Rastreamento da pendência:**

| # | Formulário | Status | Campos afetados |
|---|------------|--------|-----------------|
| 1 | `assinatura-digital/page.tsx` — "Conteúdo a Assinar" | ❌ Sem AITextarea | `<textarea>` plain na linha ~280 |
| 2 | `processos/novo/` — campos de cadastro | ⏳ Não inspecionado | A verificar |
| 3 | Outros formulários de data entry | ⏳ Não inspecionado | A verificar |

**Critério de conclusão:** Todos os campos `<input type="text">` e `<textarea>` de formulários de cadastro/edição devem usar `<AIInput>` ou `<AITextarea>` com `aiContext` e `aiObjective` adequados.

**Veredicto:** ⏳ BUG PENDENTE — RETESTE NÃO REALIZADO

---

## 4. Resumo do Reteste

| Bug ID | Severidade | Correção | Reteste | Veredicto |
|--------|------------|----------|---------|-----------|
| BUG-001 | 🟠 HIGH | ✅ Aplicada | ✅ Aprovado | FECHADO |
| BUG-002 | 🟠 HIGH | ✅ Aplicada | ✅ Aprovado | FECHADO |
| BUG-003 | 🟡 MEDIUM | ✅ Aplicada | ✅ Aprovado | FECHADO |
| BUG-004 | 🟡 MEDIUM | ✅ Aplicada | ✅ Aprovado | FECHADO |
| BUG-005 | 🟢 LOW | ⏳ Pendente | ⏳ Pendente | ABERTO |

**Taxa de fechamento:** 4/5 bugs (80%)

---

## 5. Estado Final do Build

| Verificação | Resultado |
|-------------|-----------|
| TypeScript (`tsc --noEmit`) | ✅ 0 erros, 0 warnings |
| Next.js Build (`next build`) | ✅ 0 erros, 0 warnings |
| Arquivos orfãos removidos | ✅ `use-signatures.ts` deletado |

---

*Gerado como parte do QA Wave 1 — verus.ai — 2026-06-11*
