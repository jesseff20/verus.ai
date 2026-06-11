# QA Bug Report — verus.ai

**Versão:** 1.0.0
**Data:** 2026-06-11
**Ambiente:** Frontend Next.js 14 / Backend Django 5.0
**Metodologia:** Análise estática de código + validação de contrato API + inspeção de hooks

---

## Legenda de Severidade

| Código | Severidade | Critério |
|--------|------------|---------|
| 🔴 CRITICAL | Sistema fora de serviço | Funcionalidade principal quebrada, dados corrompidos ou perda de dados |
| 🟠 HIGH | Funcionalidade principal indisponível | Feature principal não funciona, sem workaround |
| 🟡 MEDIUM | Funcionalidade parcialmente degradada | Feature funciona com limitações ou workaround tedioso |
| 🟢 LOW | Impacto cosmético / menor | Pequenos erros de UI, mensagens incorretas, performance menor que esperada |
| ⚪ TRIVIAL | Sem impacto funcional | Typos, comentários desatualizados, código morto |

---

## Resumo

| Severidade | Confirmados | Corrigidos | Pendentes |
|------------|-------------|------------|-----------|
| 🔴 CRITICAL | 0 | 0 | 0 |
| 🟠 HIGH | 2 | 2 | 0 |
| 🟡 MEDIUM | 2 | 2 | 0 |
| 🟢 LOW | 1 | 0 | 1 |
| ⚪ TRIVIAL | 0 | 0 | 0 |
| **Total** | **5** | **4** | **1** |

---

## Bugs Confirmados

---

### BUG-001 — Role Hierarchy Misalignment Frontend/Backend

| Campo | Valor |
|-------|-------|
| **ID** | BUG-001 |
| **Severidade** | 🟠 HIGH |
| **Módulo** | Autenticação / Controle de Acesso |
| **Status** | ✅ CORRIGIDO (2026-06-11) |
| **Arquivo** | `src/hooks/use-auth.ts` |

**Descrição:**
O hook `useAuth.hasPermission()` no frontend usava uma hierarquia de roles incompleta — faltavam os roles `subprocurador_geral` (nível 80), `assessor_gerencial` (nível 50) e `assessor_gabinete` (nível 45) que existem no backend (`ROLE_HIERARCHY` em `apps/accounts/models.py`).

**Impacto:**
Usuários com esses roles teriam `hasPermission()` retornando nível 0, fazendo com que guards de permissão no frontend bloqueassem incorretamente o acesso a funcionalidades para as quais esses usuários têm autorização.

**Evidência:**
```typescript
// ANTES (incompleto):
const roleHierarchy = {
  superadmin: 100, admin: 90,
  gerente: 70, procurador: 60,
  // subprocurador_geral, assessor_gerencial, assessor_gabinete AUSENTES
  servidor: 15, visualizador: 1,
};

// DEPOIS (completo — mirrors backend):
const roleHierarchy = {
  superadmin: 100, admin: 90,
  procurador_geral: 85, subprocurador_geral: 80,
  gerente: 70, procurador: 60,
  assessor_gerencial: 50, assessor_gabinete: 45,
  distribuidor: 30, servidor: 15, visualizador: 1,
  // + todos os aliases BravoJus
};
```

**RCA — 5 Porquês:**
1. **Por que** usuários com role `subprocurador_geral` eram bloqueados incorretamente? → Porque `hasPermission('gerente')` retornava `false` para eles.
2. **Por que** retornava `false`? → Porque o nível deles era 0 (role não encontrado no mapa).
3. **Por que** o role não estava no mapa? → Porque o mapa frontend foi escrito manualmente e não estava em sincronia com o backend.
4. **Por que** estava dessincronizado? → Porque não havia verificação automática de paridade entre a hierarquia do backend e do frontend.
5. **Por que** não havia verificação automática? → Porque as permissões frontend são `Record<string, number>` hardcoded sem geração de código ou contrato compartilhado.

**Correção aplicada:** Adicionados todos os roles procuradoria + aliases do `ROLE_ALIASES` do backend ao `roleHierarchy` em `use-auth.ts`.

---

### BUG-002 — Página de Assinatura Digital Usando Hook com Caminho API Errado

| Campo | Valor |
|-------|-------|
| **ID** | BUG-002 |
| **Severidade** | 🟠 HIGH |
| **Módulo** | Assinatura Digital |
| **Status** | ✅ CORRIGIDO (2026-06-11) |
| **Arquivo** | `src/app/(dashboard)/dashboard/assinatura-digital/page.tsx` |

**Descrição:**
A página `assinatura-digital/page.tsx` importava `useSignatures`, `useCreateSignature`, `useVerifySignature` do hook `use-signatures.ts`, que usava o caminho de API legado `BASE = '/api/v1/processos/assinaturas'`. O endpoint correto do backend é `/api/v1/signatures/` (app `signature`, separado do app `cases`).

Adicionalmente, havia dois problemas secundários:
1. **Tipo incompatível:** `use-signatures.ts` usava o tipo `DigitalSignature` com campos `document`, `contract`, `signature_hash`, `is_valid` — mas o serializer do backend retorna `document_ref`, `document_title`, `content_hash`, `status`.
2. **Anti-pattern de Query como Mutation:** `useVerifySignature(id)` era implementado como `useQuery` com estado `verifyTriggerId` para simular trigger, ao invés de `useMutation`.

**Impacto:**
Todas as chamadas da página retornariam 404, tornando o módulo de assinatura digital completamente inoperante — nenhuma assinatura seria listada ou criada.

**Evidência:**
```typescript
// ANTES (hook errado):
import { useSignatures, useCreateSignature, useVerifySignature } from '@/hooks/use-signatures';
// BASE = '/api/v1/processos/assinaturas'  ← caminho ERRADO (404)

// DEPOIS (hook correto):
import { useMySignatures, useSignDocument, useVerifySignature } from '@/hooks/useSignature';
// BASE = '/api/v1/signatures'  ← caminho CORRETO
```

**RCA — 5 Porquês:**
1. **Por que** as chamadas retornavam 404? → Porque a URL base era `/api/v1/processos/assinaturas/` que não existe.
2. **Por que** a URL estava errada? → Porque existiam dois hooks para assinatura (`use-signatures.ts` legado e `useSignature.ts` correto) e a página importava o errado.
3. **Por que** existiam dois hooks? → Refatoração incompleta: o novo hook foi criado mas a página não foi migrada.
4. **Por que** a migração não foi feita ao mesmo tempo? → Trabalho realizado em sessões separadas sem rastreamento de todos os consumidores do hook antigo.
5. **Por que** não havia rastreamento de consumidores? → Falta de automação de análise de imports (type-check não cobre divergências de URL).

**Correção aplicada:**
- Página migrada para usar `useMySignatures`, `useSignDocument`, `useVerifySignature` (mutation) de `useSignature.ts`
- Campos atualizados: `sig.document || sig.contract` → `sig.document_title || sig.document_ref`, `sig.is_valid` → `sig.status === 'signed'`, `sig.signature_hash` → `sig.content_hash`
- `use-signatures.ts` deletado (arquivo orfão)
- `useMySignatures()` adicionado ao `useSignature.ts`

---

### BUG-003 — Polling de Colaboradores com Frequência Excessiva

| Campo | Valor |
|-------|-------|
| **ID** | BUG-003 |
| **Severidade** | 🟡 MEDIUM |
| **Módulo** | Colaboração em Tempo Real |
| **Status** | ✅ CORRIGIDO (2026-06-11) |
| **Arquivo** | `src/hooks/use-collaboration.ts:150` |

**Descrição:**
O hook `useCollaboration` revalidava a lista de colaboradores a cada 5 segundos (`refetchInterval: 5000`), resultando em 12 requisições por minuto por sessão de colaboração aberta. Com múltiplos usuários na mesma sessão, o servidor receberia `N_users × 12 req/min` apenas para este endpoint.

**Impacto:**
- Sobrecarga desnecessária no servidor Django e banco de dados
- Consumo elevado de banda do cliente
- Possível rate limiting em produção

**RCA — 5 Porquês:**
1. **Por que** o polling era de 5s? → Valor inicial para "simular" near real-time.
2. **Por que** não usa WebSocket? → A implementação atual é via REST; WebSocket está comentado no código (`// via WebSocket em implementação real`).
3. **Por que** 5s em vez de 20s é problemático? → 240% mais requisições sem benefício equivalente — a lista de colaboradores muda raramente.
4. **Por que** não foi ajustado antes? → Prototipagem rápida sem revisão de impacto em produção.
5. **Por que** não há alerta de polling excessivo? → Falta de lint rule ou performance budget para `refetchInterval`.

**Correção aplicada:** `refetchInterval: 5000` → `refetchInterval: 20_000`

---

### BUG-004 — fluxos/page.tsx — Dupla Chamada de `useAuth()` (Violação de Regras de Hooks)

| Campo | Valor |
|-------|-------|
| **ID** | BUG-004 |
| **Severidade** | 🟡 MEDIUM |
| **Módulo** | Fluxos de Trabalho |
| **Status** | ✅ CORRIGIDO (2026-06-11) |
| **Arquivo** | `src/app/(dashboard)/dashboard/fluxos/page.tsx:265` |

**Descrição:**
A variável `canStart` era computada com uma segunda chamada ao hook `useAuth()` dentro do corpo do componente, após a desestruturação inicial do hook na linha anterior:

```typescript
const { user } = useAuth();  // linha 265
// ...
const canStart = user ? (useAuth().hasPermission('distribuidor')) : false;  // ← SEGUNDA CHAMADA
```

Isto viola as Regras dos Hooks do React — um hook não pode ser chamado condicionalmente. Adicionalmente, a expressão `user ? useAuth()...` executa o hook condicionalmente (quando `user` é falsy, o segundo `useAuth()` seria ignorado pelo short-circuit, mas ainda assim é chamado — em produção com StrictMode duplo, isso causaria comportamentos inesperados).

**Impacto:**
- Comportamento inesperado em desenvolvimento (React StrictMode detecta violação)
- Dois subscritores distintos do mesmo query key criam overhead de React Query
- Em builds futuros com React 19 Compiler, o comportamento pode ser breaking

**Correção aplicada:**
```typescript
// DEPOIS (correto):
const { user, hasPermission } = useAuth();
const canStart = hasPermission('distribuidor');
```

---

### BUG-005 — Ausência de AIInput em Campos de Formulário (Parcialmente Implementado)

| Campo | Valor |
|-------|-------|
| **ID** | BUG-005 |
| **Severidade** | 🟢 LOW |
| **Módulo** | UX / Formulários |
| **Status** | ⏳ PENDENTE |
| **Escopo** | Múltiplos arquivos — ver lista abaixo |

**Descrição:**
O requisito funcional exige que todos os campos de texto/textarea da plataforma tenham um botão de IA inline ("Aprimorar com IA" / "Gerar com IA"). Os componentes `AIInput` e `AITextarea` foram criados e integrados em formulários críticos (modal de iniciar fluxo, modal de novo fluxo, etc.), mas ainda existem formulários que usam `<input>` e `<textarea>` simples sem a integração IA.

**Páginas identificadas com campos sem AIInput (análise estática):**
- `assinatura-digital/page.tsx` — campo "Conteúdo a Assinar" usa `<textarea>` plain (introduzido na correção do BUG-002)
- `processos/novo/` — campos de cadastro de processo
- `clientes/` — campos de cadastro de cliente
- Outros formulários de cadastro a verificar via inspeção manual

**Impacto:**
Experiência do usuário inconsistente — alguns formulários têm IA, outros não. Não bloqueia funcionalidade.

**Ação requerida:**
Varredura sistemática de todos os formulários e substituição de `<input type="text">` / `<textarea>` por `<AIInput>` / `<AITextarea>` com contexto adequado.

---

## Bugs Descartados / Falsos Positivos

| ID | Descrição | Motivo do Descarte |
|----|-----------|-------------------|
| FP-001 | `use-workflows.ts` com path `/api/v1/processos/workflows` potencialmente obsoleto | O endpoint existe no backend `cases/urls.py` (linha 122-125) — é um sistema legado separado do novo BPMN, não um bug |
| FP-002 | `QA_FUNCTIONAL_INVENTORY.md` lista endpoint de verify como `/<id>/verify/` | Inventário com erro de documentação; código real (`useSignature.ts`) chama corretamente `/verify/` (list-level action, `detail=False`) |

---

## Histórico de Alterações

| Data | Versão | Alteração |
|------|--------|-----------|
| 2026-06-11 | 1.0.0 | Criação inicial com BUG-001 a BUG-005 |

---

*Gerado como parte do QA Wave 1 — verus.ai — 2026-06-11*
