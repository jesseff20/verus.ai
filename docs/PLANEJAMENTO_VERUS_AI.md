# PLANEJAMENTO TÉCNICO — VERUS.AI
> Versão 1.0 — 2026-06-11 — Pendente de aprovação para implementação

---

## 1. Resumo Executivo

A **verus.ai** será uma plataforma operacional para procuradorias, construída sobre o projeto Verus.AI como base, incorporando a lógica de workflow do FlowchartAI e os padrões visuais do catálogo Bravonix.

O projeto já existe no diretório `E:\01_PROJETOS\bravonix\verus.ai` como fork simplificado do Verus.AI. A estratégia é **evoluir esse fork** — não criar do zero — renomeando a marca, refatorando módulos inadequados para o contexto de procuradoria e adicionando as capacidades ausentes (workflow engine completo, execução de fluxo, landing page institucional).

**Stack confirmada:** Next.js 14 + TypeScript + Tailwind + Radix UI + @xyflow/react + Django 5 + DRF + PostgreSQL + pgvector + Redis + Celery + OpenAI.

**Decisão central sobre Canvas:** @xyflow/react (React Flow v12) já está na codebase e será mantido, com nodes customizados BPMN-like (task, gateway, event, swim lane container) construídos sobre ele. Não será substituído.

---

## 2. Escopo Analisado

| Fonte | O que foi analisado |
|-------|-------------------|
| `E:\01_PROJETOS\bravonix\bravojus` | Código completo: 50+ rotas, 17 apps Django, modelos, APIs, componentes |
| `E:\01_PROJETOS\bravonix\verus.ai` | Estado atual do fork: estrutura idêntica ao bravojus com simplificações |
| `E:\01_PROJETOS\bravonix\flowchartai` | Frontend do editor de workflow: ReactFlow v11 + dagre + framer-motion |
| `E:\01_PROJETOS\bravonix\catalogo-servicos-bravonix` | Landing page de referência: React + Vite + CSS animations puras |
| `verus.ai/ui/` | Design system Bravonix: tokens, cores, tipografia, componentes |
| `FLUXOS VERUS/` | BPM Bizagi/XPDL 2.2 + PNGs dos fluxos judiciais e administrativos |
| `github.com/pbakaus/impeccable` | Referência de frontend (a ser estudada na fase de implementação) |

---

## 3. Diretório Principal e Estratégia de Renomeação

**Diretório final:** `E:\01_PROJETOS\bravonix\verus.ai` ✅ (já existe)

**Estratégia de renomeação:**
1. O fork já existe e tem a mesma estrutura do Verus.AI.
2. Renomear referências de marca: `bravojus` → `verus.ai`, `Verus.AI` → `Verus.AI`, slugs de API, strings de UI.
3. Atualizar variáveis de ambiente, nomes de containers Docker, CORS origins.
4. Remover módulos inapropriados para procuradoria (financeiro de escritório privado, OAB, honorários, NFSe, portal do cliente).
5. Adicionar/refatorar módulos específicos de procuradoria.

**Itens para renomear (fase de implementação):**
- `package.json` → name: "verus-ai-frontend"
- `manage.py` + `config/settings.py` → PROJECT_NAME, SITE_NAME, EMAIL_SUBJECT_PREFIX
- Variáveis de ambiente: VERUS.AI_* → VERUS_*
- Strings de UI: todas as ocorrências de "Verus.AI" em páginas públicas e emails

---

## 4. Projetos e Referências Avaliadas

### 4.1 Verus.AI — Base do Projeto

**Frontend:**
- Framework: Next.js 14 (App Router)
- Linguagem: TypeScript
- UI: Tailwind CSS + Radix UI (Shadcn components)
- Estado: TanStack Query (servidor) + React state local
- Tabelas: TanStack Table
- Canvas/Workflow: **@xyflow/react** (React Flow v12) — já incluso
- Editor de texto: TinyMCE
- DnD: @dnd-kit
- HTTP: Axios

**Backend:**
- Framework: Django 5.0 + DRF 3.15
- Auth: JWT (simplejwt) + django-cors-headers
- Banco: PostgreSQL + pgvector + Redis
- Queue: Celery
- AI: OpenAI SDK
- Storage: boto3 / S3-compatible
- Docs: drf-spectacular (OpenAPI)

**Apps Django identificados:**

| App | Função | Relevância para verus.ai |
|-----|--------|--------------------------|
| accounts | Usuários, roles, permissões | ✅ Alta — refatorar roles p/ procuradoria |
| cases | Processos, clientes, prazos, tarefas, audiências | ✅ Alta — adaptar para processo judicial/administrativo |
| documents | Gestão documental, OCR, análise IA | ✅ Alta — reaproveitar |
| templates | Templates de documentos | ✅ Alta — reaproveitar |
| workflows | Fluxo básico (muito simples) | ⚠️ Substituir por workflow engine completo |
| agents | Agentes IA | ✅ Alta — reaproveitar |
| copilot | Assistente IA conversacional | ✅ Alta — adaptar para contexto de procuradoria |
| kb | Base de conhecimento | ✅ Alta — reaproveitar |
| rag | RAG sobre documentos | ✅ Alta — reaproveitar |
| intelligent_assistant | Análise documental IA | ✅ Alta — reaproveitar |
| collaboration | Colaboração em processos | ✅ Média — reaproveitar |
| jurisprudence | Consulta de jurisprudência | ✅ Média — reaproveitar |
| legal_library | Biblioteca jurídica | ✅ Média — reaproveitar |
| forms | Formulários dinâmicos | ✅ Alta — reaproveitar para etapas de workflow |
| integration | Integrações externas (PJe, etc.) | ✅ Alta — expandir |
| simulations | Simulações jurídicas | ⚠️ Baixa — avaliar se mantém |
| financeiro | Financeiro de escritório privado | ❌ Remover — inadequado para procuradoria |
| core | Utilitários centrais | ✅ Alta — manter |

### 4.2 FlowchartAI — Referência de Workflow

**Stack:** Next.js + ReactFlow v11 (mais antigo que o Verus.AI) + framer-motion + dagre (auto-layout) + zustand + sonner

**Funcionalidades identificadas:**
- Editor de canvas com formas genéricas: Retângulo, Elipse, Losango, Texto, Imagem
- Nós de workflow: Start, End, Process, Decision, AI, Input, Output, Knowledge Base
- Layout automático via dagre
- AI Chat Sidebar para geração de fluxos por prompt
- Undo/Redo
- Exportação (PNG via html2canvas, PDF via jspdf)
- Minimap, Zoom, Pan
- Templates de fluxo
- Propriedades de nó (painel lateral)
- Histórico (useFlowHistory hook)
- Persistência via API (CRUD de flows)

**Limitação crítica identificada:** FlowchartAI usa `reactflow` v11 enquanto Verus.AI já usa `@xyflow/react` v12. O código de FlowchartAI **não pode ser copiado diretamente** — precisará ser adaptado para a API v12.

**Elementos reutilizáveis do conceito (não do código diretamente):**
- AI Chat para criar fluxos por linguagem natural
- Estrutura de nó com painel de propriedades lateral
- Lógica de histórico (undo/redo)
- Exportação de imagem/PDF
- Sistema de templates de fluxo

### 4.3 Catálogo Bravonix — Referência Visual da Landing Page

**Stack:** React + Vite (vanilla, sem framework de animação pesado)

**Técnicas de animação identificadas:**
- `@keyframes heroSlideUp`: entrada suave dos elementos do hero (opacity + translateY)
- `@keyframes orbitScale/orbitRing`: órbitas animadas ao redor do logo
- `@keyframes pageFadeIn`: fade-in ao carregar a página
- `@keyframes gradientFlow`: gradiente de texto animado
- `@keyframes ctaGlowDark`: glow pulsante no CTA em modo escuro
- `@keyframes pulseCta`: escala do botão CTA
- `@keyframes marquee`: ticker de texto contínuo
- IntersectionObserver para scroll-reveal (sem biblioteca)
- Scroll-based sticky header com transição

**Princípios extraídos (aplicar na verus.ai):**
1. CSS puro para animações — sem overhead de biblioteca
2. `prefers-reduced-motion` respeitado
3. Stagger de animação via `transition-delay` programático
4. Elementos orbitando o logo central = identidade de "centro de controle"
5. Gradiente animado em títulos = personalidade tecnológica
6. Header sticky com mudança suave de aparência no scroll
7. Seções com scroll-reveal sem biblioteca externa

### 4.4 Design System Verus.AI (ui/)

**Cores principais:**
```
Bravonix Ink:     #0A0A0A (fundo principal escuro)
Ink Soft:         #1A1A1A (cards/painéis)
Bravonix Purple:  #7030A0 (marca, títulos, CTAs)
Electric Purple:  #5B2EE0 (destaques digitais)
Purple Bright:    #8B5CF6 (highlights em escuro)
Purple Deep:      #2A0E4A (seções imersivas)
```

**Tipografia:**
- Display/UI: `Sora` 700/800 (títulos), 400/500/600 (corpo)
- Código/Labels: `JetBrains Mono` 400/500/700

**Personalidade:** Cockpit de IA, centro de controle, auditável, institucional, soberana.

---

## 5. Auditoria do Verus.AI

### 5.1 Estrutura de Diretórios

```
bravojus/
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── (auth)/              # login, registro, password reset
│       │   ├── (client)/            # portal do cliente (REMOVER para verus.ai)
│       │   ├── (dashboard)/
│       │   │   └── dashboard/       # 50+ módulos (ver lista)
│       │   ├── api/                 # Next.js API routes
│       │   ├── consentimento/
│       │   ├── privacidade/
│       │   └── page.tsx             # Landing page (1165 linhas)
│       ├── components/
│       │   ├── agents/
│       │   ├── analytics/
│       │   ├── auth/
│       │   ├── blueprint/           # Editor de blueprints/formulários
│       │   ├── collaboration/
│       │   ├── copilot/
│       │   ├── documents/
│       │   ├── forms/
│       │   ├── graph/               # Pipeline graph (@xyflow/react)
│       │   ├── kanban/
│       │   ├── layouts/
│       │   ├── navigation/
│       │   ├── notifications/
│       │   ├── templates/
│       │   ├── ui/                  # Shadcn components
│       │   └── ...
│       ├── hooks/
│       ├── lib/
│       ├── middleware.ts
│       ├── styles/
│       └── types/
├── backend/
│   ├── apps/
│   │   ├── accounts/               # Auth, usuários, roles
│   │   ├── agents/                 # Agentes IA
│   │   ├── cases/                  # Processos, clientes, prazos, tarefas
│   │   ├── collaboration/          # Colaboração
│   │   ├── copilot/                # Assistente IA
│   │   ├── core/                   # Utilitários
│   │   ├── documents/              # Documentos
│   │   ├── financeiro/             # REMOVER
│   │   ├── forms/                  # Formulários dinâmicos
│   │   ├── integration/            # Integrações
│   │   ├── intelligent_assistant/  # IA de análise
│   │   ├── jurisprudence/          # Jurisprudência
│   │   ├── kb/                     # Base de conhecimento
│   │   ├── legal_library/          # Biblioteca jurídica
│   │   ├── rag/                    # RAG
│   │   ├── simulations/            # Simulações
│   │   ├── templates/              # Templates
│   │   └── workflows/              # SUBSTITUIR por workflow engine
│   ├── config/
│   ├── core/
│   └── manage.py
├── nginx/
├── docker-compose.*.yml
└── docs/
```

### 5.2 Módulos de Dashboard Identificados (50+)

| Módulo | Rota | Status para verus.ai |
|--------|------|---------------------|
| Processos | /processos | ✅ Adaptar (foco em proc. judicial/admin) |
| Prazos | /prazos, /prazos-inteligentes | ✅ Reaproveitar |
| Documentos | /documents | ✅ Reaproveitar |
| Templates | /templates | ✅ Reaproveitar |
| Kanban | /kanban | ✅ Reaproveitar |
| Workflows | /workflows | ⚠️ Substituir por workflow engine |
| Copilot IA | /copilot | ✅ Adaptar para contexto de procuradoria |
| Agentes IA | /agents | ✅ Reaproveitar |
| Assistente | /intelligent-assistant | ✅ Reaproveitar |
| Base Conhecimento | /knowledge-base | ✅ Reaproveitar |
| Jurisprudência | /jurisprudencia | ✅ Reaproveitar |
| Biblioteca | /legal-library | ✅ Reaproveitar |
| Auditoria | /auditoria | ✅ Expandir significativamente |
| Formulários | /forms | ✅ Reaproveitar para etapas de fluxo |
| Relatórios | /relatorios | ✅ Reaproveitar |
| Análise | /analytics | ✅ Reaproveitar |
| Usuários | /users | ✅ Reaproveitar com roles de procuradoria |
| Configurações | /settings | ✅ Reaproveitar |
| Integrações | /integration | ✅ Expandir (PJe, EPROC) |
| Blueprints | /blueprints | ⚠️ Avaliar — pode ser base do flow builder |
| Financeiro | /financeiro, /honorarios, /custas, /nfse | ❌ Remover |
| Portal Cliente | /(client) | ❌ Remover |
| CRM | /crm | ⚠️ Avaliar — pode ser adaptado para relacionamentos entre órgãos |
| Datajud | /datajud | ✅ Manter — integração com tribunal |
| Simulações | /simulations | ⚠️ Avaliar |
| Timesheet | /timesheet | ❌ Remover |

### 5.3 Tabela de Auditoria Funcional

| Item | Local | Função atual | Reaproveitar? | Refatorar? | Risco | Evidência |
|------|-------|-------------|---------------|------------|-------|-----------|
| User + Roles | backend/apps/accounts/models.py | Auth + hierarquia de roles | ✅ Sim | Sim — adicionar roles de procuradoria (distribuidor, assessor gerencial, assessor gabinete, PG, Subpg) | Baixo | models.py:ROLE_CHOICES |
| LegalCase | backend/apps/cases/models.py | Caso jurídico = Processo | ✅ Sim | Alto — renomear para Process/Processo, adaptar campos | Médio | models.py:LegalCase |
| CaseTask | backend/apps/cases/models.py | Tarefa de caso | ✅ Sim | Médio — vincular a etapas de workflow | Baixo | models.py:CaseTask |
| LegalDeadline | backend/apps/cases/models.py | Prazo | ✅ Sim | Baixo — reaproveitar | Baixo | models.py:LegalDeadline |
| WorkflowApp | backend/apps/workflows/ | Workflow básico | ❌ Substituir | Alta — criar workflow engine completo | Alto | workflows/models.py |
| Documents | backend/apps/documents/ | Gestão documental | ✅ Sim | Médio — vincular a etapas de workflow | Baixo | documents/ |
| Templates | backend/apps/templates/ | Templates de doc | ✅ Sim | Baixo | Baixo | templates/ |
| @xyflow/react | frontend/package.json | Canvas (React Flow v12) | ✅ Sim | Criar nodes customizados BPMN-like | Médio | package.json |
| Graph components | frontend/src/components/graph/ | Pipeline graph | ⚠️ Base | Refatorar para BPMN workflow | Médio | graph/ |
| Forms | backend/apps/forms + frontend | Formulários dinâmicos | ✅ Sim | Vincular a tarefas de workflow | Baixo | forms/ |
| RAG | backend/apps/rag/ | Busca semântica | ✅ Sim | Baixo | Baixo | rag/ |
| KB | backend/apps/kb/ | Base de conhecimento | ✅ Sim | Baixo | Baixo | kb/ |
| Copilot | backend/apps/copilot/ | Assistente IA | ✅ Sim | Médio — adaptar prompts para procuradoria | Baixo | copilot/ |
| Landing page | frontend/src/app/page.tsx | Landing Verus.AI | ❌ Substituir | Alta — criar landing verus.ai | Baixo | page.tsx:1165 linhas |
| financeiro app | backend/apps/financeiro/ | Financeiro privado | ❌ Remover | N/A | Médio | financeiro/ |
| Docker | docker-compose.*.yml | Infraestrutura | ✅ Sim | Baixo — atualizar nomes | Baixo | docker-compose.*.yml |

---

## 6. Auditoria do FlowchartAI

### 6.1 Arquitetura do Editor de Fluxo

| Funcionalidade | Local | Como funciona | Valor para verus.ai | Reaproveitar | Refatorar | Substituir | Evidência |
|----------------|-------|--------------|---------------------|--------------|-----------|------------|-----------|
| Canvas principal | flows/[id]/page.tsx | ReactFlow v11 + custom nodes | Alto — base do workflow builder | Conceito sim | Sim — migrar para @xyflow/react v12 | Não | flows/[id]/page.tsx |
| Nós de formas | components/canvas/ShapeNodes | Retângulo, Elipse, Losango | Médio — base visual | Não (código) | Sim — criar nodes BPMN | Não | ShapeNodes.tsx |
| Nós de workflow | components/flow/nodes/ | Start, End, Task, Decision, AI | Alto — conceito | Conceito sim | Sim — criar TaskNode, GatewayNode, EventNode | Não | nodes/ |
| Painel de propriedades | NodePropertiesPanel | Formulário lateral para nó selecionado | Alto — UX essencial | Conceito sim | Sim — adaptar para formulários dinâmicos | Não | NodePropertiesPanel.tsx |
| AI Chat | AIChatSidebar | Geração de fluxo por prompt | Alto — diferencial | Conceito sim | Adaptar prompts | Não | AIChatSidebar.tsx |
| Undo/Redo | useFlowHistory hook | Histórico de estados | Alto | Conceito sim | Migrar para v12 | Não | hooks/ |
| Auto-layout | dagre | Layout automático de nós | Médio | Sim (biblioteca) | Manter | Não | package.json:dagre |
| Exportação | html2canvas + jspdf | PNG/PDF do canvas | Médio | Conceito sim | Manter bibliotecas | Não | ExportMenu.tsx |
| Zustand store | stores/ | Estado do canvas | Alto | Conceito sim | Migrar para v12 | Não | stores/ |
| Templates | TemplateLibrary | Templates de fluxo pré-prontos | Alto | Conceito sim | Adaptar para fluxos judiciais | Não | TemplateLibrary.tsx |
| Persistência | services/api | CRUD via REST | Alto | Conceito sim | Usar Django backend | Não | services/ |

**Conclusão:** FlowchartAI é uma referência de **conceito e UX**, não de código diretamente. O código usa ReactFlow v11 e precisaria ser inteiramente reescrito para @xyflow/react v12. Os patterns (painel lateral, AI sidebar, templates, exportação) são valiosos e serão reimplementados.

---

## 7. Auditoria do Catálogo Bravonix

### 7.1 Elementos Identificados

**Stack:** React 18 + Vite (vanilla, sem Next.js) + TypeScript + CSS puro (sem Tailwind, sem Framer Motion, sem GSAP)

**Seções da landing:**
1. Header sticky com logo que desaparece no scroll
2. Hero com logo orbitante + typewriter + scroll reveal em cascata
3. Produtos / Soluções
4. Cases de uso
5. Apresentações
6. Capacidades
7. CTA para acesso/contato

**Animações (CSS puro):**
- `heroSlideUp`: Y+8→0 + opacity 0→1, usado em cascata com `animation-delay`
- `orbitRing/orbitRingReverse`: anéis girando ao redor do logo central
- `orbitScale`: escala+opacidade pulsante nos elementos do orbit
- `pageFadeIn`: fade-in da página inteira ao carregar
- `gradientFlow`: gradiente de texto animado (8s linear infinite)
- `ctaGlowDark`: glow pulsante no botão CTA (dark mode)
- `pulseCta`: escala do CTA (2.4s ease-out infinite)
- `marquee`: ticker de texto correndo (28s linear infinite)
- `cursorBlink`: cursor piscante no typewriter
- IntersectionObserver scroll-reveal (sem biblioteca)

**Princípios extraídos para a landing verus.ai:**
1. Animações por CSS custom properties → sem overhead JS, respeitam `prefers-reduced-motion`
2. Stagger visual via `animation-delay` progressivo
3. Logo como "centro de gravidade" da página (elementos ao redor)
4. Texto com gradiente animado para títulos de impacto
5. Scroll reveal sem biblioteca (só IntersectionObserver + CSS transition)
6. Header que some quando logo hero visível → reforça identidade
7. Modo escuro nativo com `data-theme` no HTML

---

## 8. Estudo do Impeccable (https://github.com/pbakaus/impeccable)

> Análise preliminar baseada no nome/contexto. Análise completa via fetch do repositório na fase de implementação.

**Princípios esperados do repositório (a confirmar):**
- Precisão de pixel em todos os detalhes
- Microinterações que comunicam estado
- Sem artefatos visuais ou animações desnecessárias
- Transições que respeitam física (ease-out para entradas, ease-in para saídas)
- Consistência tipográfica absoluta
- Estados de foco acessíveis
- Loading states que não "piscam"
- Empty states com propósito

**Aplicação para verus.ai:** Antes de qualquer implementação de componente, consultar os princípios do `impeccable` para validar acabamento visual. Criar checklist de "acabamento" para cada componente.

---

## 9. Análise dos Fluxos Anexados

### 9.1 Fluxo Judicial: Gerência Judicial — Processos Eletrônicos — 1º Grau

**Fonte:** `FLUXOS VERUS/Fluxograma Gerência Judicial - Processo Eletrônicos - 1º Grau.bpm` (XPDL 2.2, Bizagi 4.0)
**Contexto:** Fluxograma de Processos Judiciais da Procuradoria de Serra/ES
**Data:** 2023-02-09

#### Pools e Lanes (Swim Lanes)

| Pool | Lane | Ator |
|------|------|------|
| Gerência Judicial - Processos Eletrônicos | Distribuidor(a) | Responsável pela entrada e distribuição |
| Gerência Judicial - Processos Eletrônicos | Procurador(a) | Executor das etapas jurídicas principais |
| Gerência Judicial - Processos Eletrônicos | Gerente | Aprovação, redistribuição, avocação |
| Gerência Judicial - Processos Eletrônicos | Assessor(a) Gerencial | Elaboração de minutas gerenciais |
| Gerência Judicial - Processos Eletrônicos | Procurador(a) Geral / Subprocurador(a) Geral | Avocação e aprovação de alto nível |
| Gerência Judicial - Processos Eletrônicos | Assessor(a) Gabinete | Elaboração de minutas do gabinete |
| Processo principal | (sem lane) | Pool externo de referência |

#### Tarefas e Eventos Identificados

**Evento de Início:**
- `Entrada do processo no fluxo`

**Eventos de Fim:**
- `Processo Armazenado` (múltiplas terminações)
- `Processo armazenado` (variante de capitalização)

**Tarefas Identificadas:**

| Task | Lane Esperada | Tipo |
|------|--------------|------|
| Distribuir ao Procurador(a) | Distribuidor(a) | Atribuição |
| Solicitar Redistribuição | Procurador(a) | Solicitação |
| Elaborar Petição | Procurador(a) | Elaboração de documento |
| Anexar Petição | Procurador(a) | Anexação |
| Realizar Peticionamento | Procurador(a) | Protocolo eletrônico (PJe/EPROC) |
| Despacho de Deferimento | Gerente | Decisão favorável |
| Despacho de Indeferimento | Gerente | Decisão desfavorável |
| Abrir solicitação à Assessoria Gerência | Procurador(a) | Solicitação de apoio |
| Elaborar Minuta de Petição | Assessor(a) Gerencial | Elaboração de minuta |
| Elaborar Minuta de Despacho de Mero Expediente | Assessor(a) Gerencial | Elaboração de minuta |
| Devolver solicitação | Assessor(a) Gerencial | Devolução com documento |
| Assinar Despacho | Gerente/PG | Assinatura de despacho |
| Reabrir Solicitação à Assessoria Gerência | Procurador(a) | Reabertura |
| Avocar Processo | Procurador(a) Geral | Avocação |
| Abrir solicitação à Assessoria Gabinete | Procurador(a) | Solicitação ao gabinete |
| Elaborar Minuta de Petição (Gabinete) | Assessor(a) Gabinete | Elaboração |
| Elaborar Minuta de Despacho Interno | Assessor(a) Gabinete | Elaboração |
| Devolver solicitação (Gabinete) | Assessor(a) Gabinete | Devolução |
| Reabrir Solicitação à Assessoria Gabinete | Procurador(a) | Reabertura |
| Elaborar Despacho de Mero Expediente | Procurador(a) | Elaboração direta |
| Sugerir Avocação pelo(a) Procurador(a) Geral | Procurador(a) | Sugestão |
| Anexar Petição Protocolizada diretamente no PJe | Procurador(a) | Anexação direta |
| Anexar Novos Documentos | Procurador(a) | Anexação |
| Abrir Solicitação à Assessoria Gabinete | Procurador(a) | Solicitação |
| Armazenar Processo | Distribuidor(a) | Arquivamento |

**Gateways (Decisões):**

| Gateway | Tipo | Caminhos |
|---------|------|----------|
| Redistribuição aceita? | Exclusive | Sim → Despacho Deferimento; Não → Despacho Indeferimento |
| (após Despacho Deferimento) | Exclusive | → Elaborar Petição; → Anexar Petição; → Abrir solicitação Assessoria Gerência |
| Processo será peticionado? (Gerência) | Exclusive | Sim → Elaborar Minuta de Petição; Não → Elaborar Minuta de Despacho |
| (após Devolver solicitação Gerência) | Exclusive | Minuta de Mero Expediente → Assinar Despacho; Minuta de Peça → Realizar Peticionamento; Corrigir doc → Reabrir |
| (após Avocar) | Exclusive | → Distribuir; → Elaborar Petição; → Anexar Petição; → Abrir Assessoria Gabinete |
| Processo será peticionado? (Gabinete) | Exclusive | Sim → Elaborar Minuta Petição; Não → Elaborar Minuta Despacho Interno |
| (após Devolver solicitação Gabinete) | Exclusive | Minuta de Despacho Interno → Assinar Despacho; Minuta de Peça → Realizar Peticionamento; Corrigir doc → Reabrir |
| (após Distribuir) | Exclusive | → Anexar Petição; → Elaborar Petição; → Solicitar Redistribuição; → Elaborar Despacho |

#### Fluxo Principal Resumido

```
[INÍCIO] Entrada do processo no fluxo
  → Distribuir ao Procurador(a)
    ↓ O procurador decide:
    ├─ [OPÇÃO A] Solicitar Redistribuição
    │    → Redistribuição aceita?
    │      ├─ Sim: Despacho de Deferimento
    │      └─ Não: Despacho de Indeferimento → [FIM]
    │
    ├─ [OPÇÃO B] Elaborar Petição → Anexar Petição → Realizar Peticionamento → [FIM]
    │
    ├─ [OPÇÃO C] Abrir solicitação à Assessoria Gerência
    │    → Processo será peticionado?
    │      ├─ Sim: Elaborar Minuta de Petição (Assessor Gerencial)
    │      └─ Não: Elaborar Minuta de Despacho (Assessor Gerencial)
    │           → Devolver solicitação ao Procurador
    │             ├─ Minuta de Mero Expediente → Assinar Despacho → [FIM]
    │             ├─ Minuta de Peça → Realizar Peticionamento → [FIM]
    │             └─ Corrigir doc → Reabrir Solicitação → (volta)
    │
    ├─ [OPÇÃO D] Elaborar Despacho de Mero Expediente → [FIM]
    │
    └─ [VIA AVOCAÇÃO] Avocar Processo (PG/Subpg)
         → Distribuir ao Procurador(a)
           ├─ Elaborar Petição → ...
           ├─ Anexar Petição → ...
           └─ Abrir solicitação à Assessoria Gabinete
                → [similar à via Gerência, mas com Assessor Gabinete]

[FIM] Armazenar Processo
```

### 9.2 Fluxo Administrativo: Processos Administrativos Serra

**Fonte:** `Fluxo de Processos Administrativos Serra.png` (PNG — análise visual)

Baseado no nome do arquivo e no contexto da procuradoria de Serra/ES, este fluxo provavelmente descreve:
- Fluxo de entrada de processos administrativos (não judiciais)
- Triagem e distribuição por tipo de demanda
- Possivelmente: SEI ou sistema equivalente
- Responsáveis similares mas com foco em autos administrativos

*Nota: Análise detalhada do PNG requer visualização — será complementada na fase de implementação.*

---

## 10. Requisitos Extraídos dos Fluxos

### 10.1 Requisitos Funcionais por Domínio

| Requisito extraído | Módulo necessário | Existe hoje? | Precisa criar? | Prioridade | Critério de aceite |
|-------------------|-------------------|--------------|----------------|------------|-------------------|
| Criar/distribuir processo judicial | Gestão de Processos | ✅ Parcial (cases) | Refatorar | P0 | Processo criado com número, tipo, responsável, status |
| Redistribuição com aprovação/rejeição | Workflow Engine | ❌ Não | Criar | P0 | Gateway de redistribuição com despacho de deferimento/indeferimento |
| Solicitar apoio à assessoria | Solicitações/Tarefas | ❌ Não | Criar | P0 | Tarefa criada na lane da assessoria com vínculo ao processo |
| Elaborar minuta (petição/despacho) | Editor de Documentos | ✅ Parcial | Expandir | P0 | Minuta gerada, salva e vinculada à etapa do fluxo |
| Assinar despacho | Assinatura Digital | ✅ Parcial (assinatura-digital) | Integrar ao workflow | P0 | Despacho assinado registrado no histórico do processo |
| Realizar peticionamento (PJe/EPROC) | Integração PJe | ✅ Parcial (datajud) | Expandir | P0 | Protocolo registrado com número/data |
| Avocar processo | Workflow Engine | ❌ Não | Criar | P0 | Processo reassumido pelo PG com histórico |
| Reabrir solicitação à assessoria | Workflow Engine | ❌ Não | Criar | P1 | Solicitação reaberta com justificativa |
| Devolver solicitação | Workflow Engine | ❌ Não | Criar | P1 | Solicitação devolvida com documento anexado |
| Armazenar processo | Gestão de Processos | ✅ Parcial | Integrar ao workflow | P1 | Processo arquivado com data e responsável |
| Modelar fluxo com swim lanes | Workflow Builder | ❌ Não | Criar | P0 | Editor visual com lanes por ator, nós BPMN, gateways |
| Executar fluxo sobre processo | Workflow Engine | ❌ Não | Criar | P0 | Instância de fluxo criada ao vincular processo a template de fluxo |
| Auditar todas as ações do fluxo | Auditoria | ✅ Parcial | Expandir | P0 | Log com ator, ação, data, etapa, justificativa |
| Visualizar fluxo em andamento | Workflow Viewer | ❌ Não | Criar | P1 | Canvas mostrando etapa atual destacada |
| Dashboard de gargalos por etapa | Analytics | ✅ Parcial | Expandir | P1 | Tempo médio por etapa, volumetria, responsáveis sobrecarregados |
| IA para geração de minuta | IA de Documento | ✅ Parcial (copilot) | Expandir | P1 | Minuta gerada por IA com contexto do processo |
| Controle de prazos processuais | Prazos | ✅ Sim | Vincular ao workflow | P0 | Prazo criado automaticamente na distribuição |
| Notificação de nova tarefa | Notificações | ✅ Parcial | Expandir | P1 | Notificação ao responsável quando tarefa criada |

---

## 11. Pesquisa de Bibliotecas de Canvas/Workflow

### 11.1 Tabela Comparativa

| Biblioteca | Tipo | Prós | Contras | Licença | Maturidade | Compatibilidade | Risco | Recomendação |
|-----------|------|------|---------|---------|------------|----------------|-------|--------------|
| **@xyflow/react** (React Flow v12) | Canvas geral | Excelente React integration, MIT, comunidade enorme, nodes/edges 100% customizáveis, TypeScript, pan/zoom/minimap/grid, v12 com melhorias significativas | Sem swim lanes nativas (precisa implementar), sem BPMN nativo | MIT | ⭐⭐⭐⭐⭐ (>30k stars) | ✅ Já no Verus.AI | Baixo | ✅ **RECOMENDADO** |
| **bpmn-js** (bpmn.io) | BPMN 2.0 spec | BPMN 2.0 nativo, swim lanes, todos os elementos BPMN, usado pela Camunda, importa/exporta BPMN XML | Não é React-native, customização complexa, UX mais pesada, integração com React via wrapper | Apache 2.0 | ⭐⭐⭐⭐⭐ | Requer wrapper | Médio | ⚠️ Alternativa |
| **AntV X6** | Graph/diagram | Bom suporte a grupos/subgraphs, TypeScript, customizável | Documentação em chinês (traduzida), menor comunidade no Brasil | MIT | ⭐⭐⭐⭐ | React compatible | Médio | ⚠️ Alternativa |
| **tldraw** | Whiteboard | Excelente UX de whiteboard, MIT, infinity canvas | Não é workflow/BPMN, whiteboard de uso geral, não tem conceito de processo | MIT | ⭐⭐⭐⭐ | React | Médio | ❌ Inadequado |
| **JointJS** | Diagram engine | Maduro, BPMN plugin disponível | Licença comercial para uso avançado, pesado | Dual (MIT/Comercial) | ⭐⭐⭐⭐ | React wrapper | Alto | ❌ Risco de lock-in |
| **GoJS** | Diagram engine | Muito poderoso, swim lanes, BPMN | Licença comercial obrigatória ($$$) | Comercial | ⭐⭐⭐⭐⭐ | React wrapper | Alto (custo) | ❌ |
| **Rete.js** | Node editor | Bom para pipelines de dados | Foco em pipeline de nós, não BPMN | MIT | ⭐⭐⭐ | React | Médio | ❌ Inadequado |
| **Drawflow** | Flow editor | Simples, leve | Muito básico, sem React native, comunidade pequena | MIT | ⭐⭐⭐ | React wrapper | Médio | ❌ |
| **reactflow** (v11) | Canvas geral | Usado no FlowchartAI | **OBSOLETO** — substituído por @xyflow/react | MIT | Descontinuado | ❌ Não usar | Alto | ❌ |

### 11.2 Decisão Recomendada: @xyflow/react

**Justificativa:**
1. **Já está na codebase do Verus.AI** — zero custo de adoção
2. **MIT** — sem risco de licença
3. **React-native** — integração perfeita com o stack existente
4. **Comunidade e suporte** — maior ecossistema de React flow libraries
5. **Swim lanes como grupos** — React Flow v12 suporta grupos/subflows que podem simular swim lanes
6. **BPMN-like sem spec overhead** — a verus.ai não precisa exportar BPMN 2.0 XML; precisa de UX similar
7. **Custom nodes** — cada node type (Task, Gateway, Event, Swimlane Container) é 100% controlado

**Como implementar swim lanes com @xyflow/react:**
- Lane container como `Node` com `type: 'swimlane'`, com `style` fixando altura e posição vertical
- Tarefas dentro da lane como nós com posição relativa ao container
- Garantir que ao mover uma tarefa entre lanes, o `parentNode` seja atualizado

---

## 12. Mapa Funcional Atual

### 12.1 Capacidades Existentes (a confirmar com auditoria completa)

| Capacidade | Status | App/Módulo |
|-----------|--------|------------|
| Autenticação/JWT | ✅ Funcional | accounts |
| Usuários e roles | ✅ Funcional | accounts |
| Criação de processo (básico) | ✅ Funcional | cases |
| Gestão de prazos | ✅ Funcional | cases |
| Tarefas por processo | ✅ Funcional | cases |
| Gestão documental | ✅ Funcional | documents |
| Templates de documentos | ✅ Funcional | templates |
| Formulários dinâmicos | ✅ Funcional | forms |
| Copilot IA | ✅ Funcional | copilot |
| RAG sobre documentos | ✅ Funcional | rag |
| Base de conhecimento | ✅ Funcional | kb |
| Kanban | ✅ Funcional | dashboard/kanban |
| Calendário | ✅ Funcional | dashboard/calendario |
| Notificações | ✅ Funcional | dashboard/notifications |
| Auditoria básica | ✅ Parcial | dashboard/auditoria |
| Integração Datajud | ✅ Funcional | dashboard/datajud |
| Canvas (@xyflow/react) | ✅ Presente (grafo de pipeline) | components/graph |

### 12.2 Capacidades Ausentes (Críticas para verus.ai)

| Capacidade | Prioridade | Módulo a criar |
|-----------|-----------|----------------|
| Workflow Builder (editor BPMN-like visual) | P0 | workflow-builder |
| Workflow Engine (execução de instâncias) | P0 | workflow-engine |
| Workflow Versioning | P0 | workflow-version |
| Swim Lanes no editor | P0 | workflow-builder |
| Gateway exclusivo/inclusivo visual | P0 | workflow-builder |
| Solicitações entre raias (redistribuição, avocação, assessoria) | P0 | workflow-engine |
| Assinatura digital integrada ao fluxo | P0 | workflow-engine + assinatura-digital |
| Peticionamento integrado ao fluxo | P1 | workflow-engine + integration |
| Visualização de fluxo em execução | P1 | workflow-viewer |
| Histórico de execução de fluxo | P0 | workflow-audit |
| Indicadores por etapa de fluxo | P1 | analytics |
| Landing page verus.ai | P0 | frontend/app/page.tsx |
| Narrativa e identidade verus.ai | P0 | toda a UI |
| Roles específicos de procuradoria | P0 | accounts |
| App de Órgão/Unidade/Procuradoria | P0 | novo app: organization |

---

## 13. Mapa Funcional Desejado da verus.ai

### 13.1 Módulos da Plataforma

```
verus.ai
├── 🏛️  ORGANIZAÇÃO
│   ├── Órgãos (procuradorias, prefeituras, etc.)
│   ├── Unidades (gerências, gerências judiciais, etc.)
│   └── Cargos e Perfis
│
├── 👤  USUÁRIOS & PERMISSÕES
│   ├── Distribuidor(a)
│   ├── Procurador(a)
│   ├── Gerente
│   ├── Assessor(a) Gerencial
│   ├── Assessor(a) Gabinete
│   ├── Procurador(a) Geral
│   ├── Subprocurador(a) Geral
│   └── Administrador / Superadmin
│
├── ⚡  WORKFLOW ENGINE (CORE)
│   ├── Modelagem (Builder Visual BPMN-like)
│   ├── Versioning
│   ├── Execução (Instâncias por Processo)
│   ├── Monitoramento em Tempo Real
│   ├── Auditoria de Execução
│   └── Templates de Fluxo
│
├── 📋  PROCESSOS
│   ├── Processos Judiciais
│   ├── Processos Administrativos
│   ├── Distribuição e Redistribuição
│   ├── Prazos Processuais
│   └── Vinculação com Fluxo
│
├── ✅  TAREFAS
│   ├── Criação Automática por Fluxo
│   ├── Atribuição e Redistribuição
│   ├── Execução e Transição
│   ├── Kanban Operacional
│   └── Prazos de Tarefa
│
├── 📄  DOCUMENTOS
│   ├── Petições
│   ├── Despachos
│   ├── Minutas
│   ├── Anexos
│   ├── Assinatura Digital
│   └── Geração por IA
│
├── 🤖  INTELIGÊNCIA ARTIFICIAL
│   ├── Classificação de Processo
│   ├── Resumo de Processo/Documento
│   ├── Geração de Minuta
│   ├── Geração de Despacho
│   ├── Sugestão de Próxima Etapa
│   ├── Assistente Jurídico (Copilot)
│   └── RAG sobre Base Documental
│
├── 📊  ANALYTICS & PAINÉIS
│   ├── Dashboard Operacional
│   ├── Indicadores por Fluxo
│   ├── Gargalos e Tempo por Etapa
│   ├── Carga por Responsável
│   └── Relatórios Gerenciais
│
├── 🔗  INTEGRAÇÕES
│   ├── PJe (Processo Judicial Eletrônico)
│   ├── EPROC
│   ├── SEI (Sistema Eletrônico de Informações)
│   ├── Datajud (CNJ)
│   └── APIs externas por webhook
│
├── 🔒  GOVERNANÇA & SEGURANÇA
│   ├── Auditoria Completa (quem/quando/o quê)
│   ├── Controle de Acesso por Unidade
│   ├── Logs de IA
│   └── Trilha de Assinaturas
│
└── 🌐  LANDING PAGE (pré-login)
    └── Narrativa institucional verus.ai
```

---

## 14. Funcionalidades Reaproveitáveis

| Funcionalidade | De onde | Como reaproveitar |
|---------------|---------|------------------|
| Auth JWT completo | bravojus/accounts | Manter com adição de roles de procuradoria |
| Estrutura de processos (LegalCase) | bravojus/cases | Renomear para Process/Processo, adaptar campos |
| Gestão de documentos + OCR | bravojus/documents | Manter e vincular ao workflow |
| Templates de documentos | bravojus/templates | Manter e usar para minutas/despachos |
| Formulários dinâmicos | bravojus/forms | Usar como formulários de etapa de fluxo |
| Copilot IA | bravojus/copilot | Manter, adaptar prompts para procuradoria |
| RAG + pgvector | bravojus/rag | Manter para busca semântica |
| Base de conhecimento | bravojus/kb | Manter |
| Integração Datajud | bravojus/integration | Expandir para PJe/EPROC |
| Kanban | bravojus/dashboard/kanban | Manter como visão alternativa de tarefas |
| Calendário | bravojus/dashboard/calendario | Manter para prazos |
| Notificações | bravojus/dashboard/notifications | Expandir com notificações de fluxo |
| @xyflow/react base | bravojus/components/graph | Usar como base para workflow builder |
| Design system (ui/) | verus.ai/ui/ | Design system completo documentado |
| Docker + nginx | docker-compose.*.yml | Manter e atualizar nomes |
| Assinatura digital | bravojus/assinatura-digital | Integrar ao fluxo de assinatura de despachos |

---

## 15. Funcionalidades a Substituir ou Refatorar

| Funcionalidade | Motivo | Estratégia |
|---------------|--------|------------|
| Landing page (page.tsx) | Narrativa de advocacia privada, sem identidade verus.ai | Criar nova do zero |
| workflows app (backend) | Muito simples, sem engine de execução | Substituir por workflow engine completo |
| LegalCase model | Nomenclatura e campos de advocacia privada | Renomear + adaptar |
| Roles (accounts) | Muitos roles de advocacia privada (socio, oab, etc.) | Adicionar roles de procuradoria, deprecar roles privados |
| Módulo financeiro | Honorários, NFSe — inadequado para procuradoria | Remover |
| Portal do cliente | Contexto B2C de escritório | Remover |
| Graph/pipeline component | Genérico, não BPMN | Evoluir para workflow builder |
| Narrativa de toda a UI | "Verus.AI" e advocacia privada | Substituir por "verus.ai" e procuradoria |

---

## 16. Arquitetura Alvo Proposta

### 16.1 Stack Final (sem mudanças de base)

**Frontend:**
- Next.js 14+ (App Router) + TypeScript
- Tailwind CSS + Radix UI (Shadcn)
- TanStack Query v5 + React State
- **@xyflow/react** (React Flow v12) — Workflow Builder
- Framer Motion — animações da landing page e transições de UI
- TinyMCE — editor de minutas/petições
- @dnd-kit — Kanban e ordenação
- Axios — HTTP client

**Backend:**
- Django 5.0 + DRF 3.15
- JWT (simplejwt) + django-cors-headers
- PostgreSQL 15+ + pgvector + Redis 7+
- Celery 5.3+ — tasks assíncronas
- OpenAI SDK + Claude SDK (Anthropic)
- boto3/S3 — storage de documentos
- drf-spectacular — OpenAPI docs

### 16.2 Novos Apps Django para verus.ai

| App | Responsabilidade |
|-----|----------------|
| `organization` | Órgão, Unidade, Procuradoria — modelo multi-tenant |
| `workflow_definition` | Definição de fluxo: ProcessTemplate, NodeDefinition, EdgeDefinition, LaneDefinition |
| `workflow_execution` | Execução: FlowInstance, TaskInstance, TransitionLog, DecisionRecord |
| `procurement` | Processos judiciais e administrativos específicos de procuradoria |
| `requests` | Solicitações entre raias (redistribuição, avocação, devolução) |
| `signatures` | Assinaturas digitais integradas ao workflow |

### 16.3 Modelo de Dados Central (Novo)

```
Organization
├── Organ (Órgão/Procuradoria)
│   └── Unit (Unidade/Gerência)
│       └── User (com role de procuradoria)

ProcessTemplate (Definição de Fluxo)
├── version: SemVer
├── status: draft|published|archived
├── LaneDefinition[] (swim lanes por ator)
│   └── NodeDefinition[] (tasks, events, gateways)
│       └── EdgeDefinition[] (transições com condições)
└── FormDefinition[] (formulários por node)

FlowInstance (Execução por Processo)
├── process: Process
├── template: ProcessTemplate (versão específica)
├── status: active|paused|completed|aborted
├── current_node: NodeDefinition
└── TaskInstance[]
    ├── assigned_to: User
    ├── lane: LaneDefinition
    ├── status: pending|in_progress|completed|returned|reopened
    ├── due_date: datetime
    └── ExecutionLog[]

Process (Processo — judicial ou administrativo)
├── number: str (número CNJ ou administrativo)
├── type: judicial|administrative
├── phase: 1st_degree|2nd_degree|superior|administrative
├── unit: Unit
├── responsible: User
├── flow_instance: FlowInstance (null=True)
└── Document[], Deadline[], Request[]

Request (Solicitação entre raias)
├── process: Process
├── from_user: User
├── to_lane: LaneDefinition
├── type: redistribution|avocation|gerencial|gabinete
├── status: pending|accepted|rejected|returned|reopened
└── documents[], decision_record
```

### 16.4 Diagrama de Arquitetura

```
                    ┌─────────────────┐
                    │   verus.ai      │
                    │  Next.js 14     │
                    │  (App Router)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         Landing Page   Workflow        Dashboard
         (pré-login)    Builder         Operacional
                        (@xyflow)       (processos,
                                         tarefas, docs)
                             │
                    ┌────────▼────────┐
                    │   Django API    │
                    │   (DRF/JWT)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
     PostgreSQL          Redis/Celery       OpenAI/Claude
     (+ pgvector)        (Tasks/Queue)      (IA Assistiva)
```

---

## 17. Planejamento do Core de Workflow

### 17.1 Workflow Builder (Frontend)

**Componentes a criar (baseados em @xyflow/react):**

| Componente | Responsabilidade |
|-----------|----------------|
| `WorkflowCanvas` | Container principal, ReactFlow + providers |
| `SwimlaneNode` | Container de raia (pool horizontal) com label |
| `TaskNode` | Retângulo de tarefa com ícone, label, assignee |
| `GatewayNode` | Losango de decisão (exclusivo/inclusivo/paralelo) |
| `StartEventNode` | Círculo verde de início |
| `EndEventNode` | Círculo vermelho de fim |
| `IntermediateEventNode` | Círculo de evento intermediário |
| `ConnectorEdge` | Aresta com label de condição e animação de fluxo ativo |
| `NodePropertiesPanel` | Painel lateral: configurar nome, responsável, formulário, prazo |
| `FlowToolbar` | Barra de ferramentas: adicionar nó, zoom, exportar |
| `FlowMinimap` | Minimapa de navegação |
| `FlowValidator` | Validação antes de publicar (nós desconectados, etc.) |
| `AIFlowAssistant` | Chat de IA para geração de fluxo por linguagem natural |
| `TemplateLibrary` | Biblioteca de templates (incluindo os fluxos judiciais) |
| `VersionHistory` | Histórico de versões do fluxo |

**UX do Builder:**
1. Usuário arrasta nó do painel esquerdo para o canvas
2. Conecta nós arrastando da porta de saída para entrada
3. Duplo-clique no nó abre painel de propriedades
4. Propriedades incluem: nome, responsável (lane), tipo, formulário vinculado, prazo padrão
5. Gateway: configurar condições nas arestas de saída
6. Antes de publicar: validação automática
7. Publicação cria nova versão; versão anterior mantida para instâncias em andamento

### 17.2 Workflow Engine (Backend)

**Endpoints necessários:**

```
# Definição de Fluxo
GET/POST   /api/workflows/templates/
GET/PUT    /api/workflows/templates/{id}/
POST       /api/workflows/templates/{id}/publish/
POST       /api/workflows/templates/{id}/duplicate/

# Execução
POST       /api/workflows/instances/          # Iniciar fluxo para processo
GET        /api/workflows/instances/{id}/
POST       /api/workflows/instances/{id}/execute-step/   # Executar etapa atual
POST       /api/workflows/instances/{id}/pause/
POST       /api/workflows/instances/{id}/abort/

# Tarefas
GET/POST   /api/workflows/tasks/
GET/PUT    /api/workflows/tasks/{id}/
POST       /api/workflows/tasks/{id}/complete/
POST       /api/workflows/tasks/{id}/return/
POST       /api/workflows/tasks/{id}/reopen/

# Solicitações (redistribuição, avocação)
POST       /api/workflows/requests/
POST       /api/workflows/requests/{id}/accept/
POST       /api/workflows/requests/{id}/reject/
POST       /api/workflows/requests/{id}/return/
POST       /api/workflows/requests/{id}/reopen/

# Auditoria
GET        /api/workflows/instances/{id}/history/
GET        /api/workflows/instances/{id}/audit-trail/
```

**Lógica de execução:**
1. Ao receber processo → selecionar template de fluxo → criar FlowInstance
2. Estado inicial → criar TaskInstance para o nó inicial
3. Ao completar tarefa → avaliar transições disponíveis (condições do gateway)
4. Se gateway exclusivo → apresentar opções ao usuário (quem executa a tarefa)
5. Ao selecionar caminho → mover instância para o próximo nó → criar nova tarefa
6. Solicitações entre raias → criar Request + notificar destinatário
7. Ao aceitar/rejeitar redistribuição → despacho automático gerado (template)
8. Avocação → reatribuir FlowInstance ao PG + log

---

## 18. Planejamento de Front-End

| Área | Evidência analisada | Decisão proposta | Alternativas | Critério de escolha | Status |
|------|-------------------|-----------------|--------------|---------------------|--------|
| Landing page | catalogo-servicos (CSS puro) + design system verus.ai | Next.js + Tailwind + CSS animations puras + IntersectionObserver | Framer Motion | CSS puro = zero overhead, já funcionou bem no catálogo | Pendente aprovação |
| Workflow Builder | @xyflow/react já no Verus.AI | @xyflow/react v12 com custom nodes BPMN-like | bpmn-js | Já na codebase, MIT, excelente React integration | Pendente aprovação |
| Editor de minutas/documentos | TinyMCE já no Verus.AI | Manter TinyMCE | Quill, Tiptap | Já configurado e funcional | Pendente aprovação |
| Design system | ui/ folder completo com tokens | Sora + JetBrains Mono + paleta Bravonix Purple | N/A | Já documentado | Pendente aprovação |
| Estado global | TanStack Query no Verus.AI | Manter TanStack Query + React state | Zustand, Redux | Já configurado, excelente para server state | Pendente aprovação |
| Animações UI | catalogo (CSS) + Verus.AI (Tailwind transitions) | Framer Motion para componentes de UI + CSS para landing | GSAP | Framer Motion tem melhor DX em React; CSS para landing = performance | Pendente aprovação |
| Notificações toast | Nenhuma mencionada | Sonner (já no FlowchartAI) | React-hot-toast | Sonner: sem manutenção de boilerplate, API simples | Pendente aprovação |

### 18.1 Planejamento de Telas

**Grupo 1: Pré-login (Landing Page)**
- Hero: identidade verus.ai, logo orbital, tagline
- Problema das procuradorias (narrativa emocional)
- Plataforma como centro de comando
- Fluxos processuais inteligentes
- IA auditável
- Gestão de tarefas e prazos
- Painéis e inteligência gerencial
- Segurança e rastreabilidade
- CTA para acesso

**Grupo 2: Autenticação**
- Login (já existe)
- Recuperação de senha (já existe)
- Onboarding inicial (configurar órgão/unidade)

**Grupo 3: Dashboard Principal**
- Visão geral: processos ativos, tarefas pendentes, prazos próximos, gargalos
- Cards de ação rápida
- Feed de atividade recente

**Grupo 4: Workflow Builder (NOVO)**
- Lista de templates de fluxo
- Editor visual (canvas @xyflow + swim lanes)
- Painel de propriedades de nó
- Histórico de versões
- Publicação de fluxo

**Grupo 5: Processos**
- Lista de processos (filtros por tipo, status, responsável, unidade)
- Detalhe do processo (timeline, documentos, tarefas, fluxo ativo)
- Criação de processo
- Vincular processo a template de fluxo

**Grupo 6: Tarefas**
- Minhas tarefas (visão pessoal)
- Kanban por processo/fluxo
- Lista de solicitações pendentes (redistribuição, avocação)
- Detalhe da tarefa com formulário da etapa

**Grupo 7: Documentos**
- Lista de documentos
- Editor de minuta (TinyMCE)
- Visualizador de documento
- Geração por IA

**Grupo 8: Painéis/Analytics**
- Indicadores operacionais por fluxo
- Gargalos por etapa
- Carga por procurador
- Volume de processos por período

---

## 19. Planejamento de Back-End

| Domínio | Entidades prováveis | Responsabilidade | APIs prováveis | Riscos | Decisão pendente |
|---------|--------------------|-----------------|-----------------------|--------|-----------------|
| Organization | Organ, Unit, Position | Multi-tenancy por órgão | CRUD órgão/unidade | Isolamento de dados entre órgãos | Confirmar modelo multi-tenant |
| Users | User, Role, Permission | Auth + autorização | CRUD users, login, me | Migração de roles | Validar roles de procuradoria |
| Process | Process, ProcessType | Gestão de processos | CRUD processos, filtros | Compatibilidade com LegalCase existente | Estratégia de migração |
| Workflow Def. | ProcessTemplate, NodeDef, EdgeDef, LaneDef | Modelagem de fluxo | CRUD templates, publish | Versionamento | Estratégia de versão |
| Workflow Exec. | FlowInstance, TaskInstance, TransitionLog | Execução e rastreamento | execute-step, complete, audit | Consistência de estado | Transações atômicas |
| Requests | Request, Decision | Redistribuição, avocação, assessoria | CRUD requests, accept, reject | Notificações em tempo real | WebSocket vs polling |
| Documents | Document, DocumentVersion | Gestão documental | CRUD docs, upload, geração | OCR e IA latência | Workers async (Celery) |
| AI | AIRequest, AIResult, Prompt | IA assistiva | generate-summary, generate-draft | Custo, latência, alucinação | Rate limiting, fallback |
| Audit | AuditLog, AuditEvent | Trilha completa | GET audit-trail | Volume de logs | Particionamento da tabela |
| Notifications | Notification, Channel | Alertas e mensagens | GET/POST notifications | Real-time | Considerar WebSocket |

---

## 20. Planejamento de Banco de Dados

### 20.1 Entidades Novas (além das existentes)

| Entidade | Campos principais | Relacionamentos | Constraints | Índices | Auditoria |
|---------|------------------|----------------|-------------|---------|-----------|
| Organ | id, name, slug, cnpj, city, state | units[], users[] | name unique | name, slug | created_at, updated_at |
| Unit | id, organ, name, slug, type | organ, users[] | (organ, slug) unique | organ, type | created_at |
| ProcessTemplate | id, name, version, status, created_by, published_at | nodes[], edges[], lanes[] | (name, version) unique | status, name | created_at, published_at |
| NodeDefinition | id, template, name, type, lane, form, position_x, position_y | template, lane, edges_from, edges_to | — | template, type | — |
| EdgeDefinition | id, template, source_node, target_node, label, condition | template, source, target | — | template, source | — |
| LaneDefinition | id, template, name, role, order | template | (template, role) unique | template | — |
| FlowInstance | id, process, template_version, status, current_node, started_at, ended_at | process, template, tasks | — | status, process | created_at, updated_at |
| TaskInstance | id, flow_instance, node_def, assigned_to, status, created_at, due_date, completed_at | flow_instance, node, user | — | assigned_to, status, due_date | status_changed_at |
| TransitionLog | id, flow_instance, from_node, to_node, decision, actor, timestamp, justification | flow_instance, actor | — | flow_instance, timestamp | — |
| Request | id, process, from_user, to_lane, type, status, created_at | process, from_user, to_lane | — | process, status, type | created_at, updated_at |
| AuditLog | id, entity_type, entity_id, action, actor, before_state, after_state, timestamp, ip, context | actor | — | entity_type, entity_id, timestamp | timestamp |

### 20.2 Entidades a Adaptar

| Entidade atual | Mudança | Impacto |
|---------------|---------|---------|
| User | Adicionar: organ (FK), unit (FK), procuradoria_roles | Médio — migration + UI |
| LegalCase | Renomear para Process, adicionar: type, phase, flow_instance | Médio — migration |
| CaseTask | Renomear para Task, vincular a TaskInstance de fluxo | Médio |
| Document | Adicionar: flow_instance (FK), task_instance (FK), document_type_v2 | Baixo |

---

## 21. Planejamento de IA

### 21.1 Recursos de IA Planejados

| Recurso | Entrada | Contexto | Saída | Schema | Revisão Humana | Risco |
|---------|---------|---------|------|--------|----------------|-------|
| Classificação de processo | Número + ementa + tipo | Histórico de processos similares | `{type: str, phase: str, urgency: low/mid/high, confidence: float}` | JSON validado | Opcional | Alucinação de fase |
| Resumo de processo | Processo + documentos | Histórico de movimentações | `{summary: str, key_dates: [], key_parties: [], next_action: str}` | JSON validado | Recomendada | Omissão de fato relevante |
| Geração de minuta de petição | Processo + fatos + pedidos + template | Jurisprudência relevante | Texto em HTML (TinyMCE) | Texto livre | **Obrigatória** | Erro jurídico |
| Geração de despacho | Processo + solicitação + contexto | Minutas anteriores | Texto em HTML | Texto livre | **Obrigatória** | Erro jurídico |
| Sugestão de próxima etapa | FlowInstance + contexto atual | Template de fluxo ativo | `{suggested_node: id, rationale: str, confidence: float}` | JSON validado | Recomendada | Sugestão inapropriada |
| Sugestão de responsável | TaskInstance + carga dos procuradores | Histórico de distribuições | `{suggested_user: id, reason: str}` | JSON validado | Recomendada | Viés de distribuição |
| Extração de partes | Documento | — | `{polo_ativo: [], polo_passivo: [], advogados: []}` | JSON validado | Recomendada | OCR + extração errada |
| Extração de prazos | Documento | — | `{prazos: [{tipo, data, descricao}]}` | JSON validado | **Obrigatória** | Erro de prazo fatal |

**Regras de IA (inegociáveis):**
- IA **nunca** assina despacho — apenas gera minuta para revisão humana
- IA **nunca** realiza peticionamento — apenas prepara petição
- Todo uso de IA registrado em `AuditLog` com prompt_id e resultado_id
- Prompts versionados em tabela `PromptTemplate`
- Fallback para "IA indisponível" com degradação graciosa
- Dados sensíveis não incluídos em logs de prompt

---

## 22. Planejamento de Segurança

| Risco | Área afetada | Impacto | Mitigação | Teste obrigatório |
|-------|-------------|---------|-----------|------------------|
| Acesso cruzado entre órgãos | Organization model | Alto — vazamento de dados jurídicos | Filtro por `organ` em TODOS os querysets; `OrganPermission` no DRF | Teste: usuário de órgão A não vê dados do órgão B |
| Escalação de privilégio | accounts/permissions | Alto | Role hierarchy, never trust frontend role | Teste: procurador não pode avocar, PG não pode elaborar petição como procurador |
| Injeção via formulário de etapa | forms app | Médio | Sanitização server-side; DOMPurify no frontend | Teste com payload XSS e SQL injection |
| Dados sensíveis em prompt IA | copilot/ai | Alto — conformidade LGPD | Mascarar CPF/CNPJ antes de enviar à IA; no-log em provider | Teste: CPF não aparece em logs da OpenAI |
| Upload de documento malicioso | documents/upload | Médio | Validação MIME, antivírus, scan de conteúdo | Teste com PDF com macro, DOCX com script |
| JWT sem expiração adequada | accounts/auth | Alto | Access token 15min, refresh token 7d, blacklist no logout | Teste: token revogado não funciona |
| CORS aberto | backend/cors | Médio | CORS whitelist com origins específicos de produção | Teste: request de origem não autorizada bloqueado |
| Rate limit em IA | copilot/ai | Médio (custo) | Rate limit por usuário (10 req/min), Celery queue | Teste: burst de requests dispara throttle |
| Prompt injection em inputs do usuário | IA em geral | Alto | Sanitização de inputs antes do prompt, schema validation de output | Teste com prompt injection no campo de "justificativa" |
| Logs com dados sensíveis | audit/logs | Alto — LGPD | Mascarar PII em logs; separate sensitive log level | Auditoria de logs em homologação |

---

## 23. Planejamento de Testes

### 23.1 Frontend
- Lint: ESLint + Prettier (já configurados)
- Type-check: `tsc --noEmit`
- Testes de componente: Vitest + Testing Library
- Testes E2E: Playwright (fluxo completo de processo)
- Responsividade: breakpoints mobile, tablet, desktop
- Acessibilidade: axe-core no CI
- Canvas/workflow: testes de interação (adicionar nó, conectar, publicar)

### 23.2 Backend
- Unittest Django: por app
- Cobertura mínima: 80% dos serviços críticos
- Testes de API: pytest + DRF test client
- Testes de permissão: isolamento entre órgãos
- Testes de workflow: iniciar fluxo, executar etapas, redistribuir, avocar
- Testes de IA: mock de API, validação de schema, fallback

### 23.3 Banco de Dados
- Migrations: test de aplicação limpa
- Constraints: test de violação
- Índices: EXPLAIN ANALYZE nas queries principais

---

## 24. Roadmap de Implementação

### Fase 1 — Fundação e Identidade (2-3 semanas)
1. Renomeação de marca: bravojus → verus.ai em toda UI/backend
2. Novo modelo Organization (Organ, Unit)
3. Refatoração de roles de usuário (adicionar roles de procuradoria)
4. Remover módulos inadequados (financeiro, portal cliente)
5. Landing page verus.ai (nova)
6. Atualização de variáveis de ambiente e Docker

### Fase 2 — Workflow Builder (3-4 semanas)
1. Novo app `workflow_definition` no Django
2. APIs CRUD de templates de fluxo
3. Componentes @xyflow/react: SwimLane, TaskNode, GatewayNode, EventNodes
4. Editor visual com painel de propriedades
5. Validação antes de publicação
6. Versionamento de templates
7. Templates pré-carregados dos fluxos judiciais

### Fase 3 — Workflow Engine (3-4 semanas)
1. Novo app `workflow_execution`
2. Serviço de execução de fluxo
3. Criação automática de tarefas por nó
4. Avaliação de gateways (condições)
5. Sistema de solicitações (redistribuição, avocação, assessoria)
6. Notificações por tarefa criada/modificada
7. Histórico de execução e auditoria

### Fase 4 — Processos e Integração (2-3 semanas)
1. Refatorar LegalCase → Process
2. Vincular processo a FlowInstance
3. Dashboard de processo com timeline de fluxo
4. Integração PJe/EPROC (peticionamento)
5. Assinatura digital integrada ao workflow

### Fase 5 — IA e Analytics (2-3 semanas)
1. Prompt templates para procuradoria
2. Geração de minuta por IA
3. Resumo de processo por IA
4. Sugestão de próxima etapa por IA
5. Dashboard de indicadores por fluxo
6. Relatório gerencial

### Fase 6 — Qualidade e Go-live (2 semanas)
1. Testes E2E dos fluxos completos
2. Testes de performance
3. Testes de segurança
4. Documentação de usuário
5. Deploy de produção

---

## 25. Checklist Funcional com Evidências

| ID | Funcionalidade | Problema que resolve | Entrega isoladamente? | Depende de | Como entrega | Evidência encontrada | Status | Critério de aceite |
|----|---------------|---------------------|----------------------|-----------|-------------|---------------------|--------|------------------|
| WF-01 | Editor de Workflow Visual | Impossibilidade de modelar fluxos como os judiciais | Sim (modelagem) | @xyflow/react, API | Canvas com swim lanes, nós BPMN-like, exportação | @xyflow/react em bravojus; FlowchartAI conceito | Pendente | Usuário consegue recriar o fluxo judicial no editor |
| WF-02 | Execução de Workflow | Processo sem fluxo estruturado | Não | WF-01, PROC-01 | Instância de fluxo criada ao vincular processo a template | — | Pendente | FlowInstance criada ao vincular processo ao template |
| WF-03 | Versionamento de Workflow | Processos antigos perdem histórico se fluxo muda | Sim (versionamento) | WF-01 | Cada publicação cria nova versão; instâncias mantêm versão | — | Pendente | Instâncias antigas mantêm versão original do fluxo |
| WF-04 | Swim Lanes por Ator | Impossível distinguir responsabilidades no fluxo | Não | WF-01 | Cada lane é um ator; nós vinculados à lane | — | Pendente | Editor exibe raia por Distribuidor, Procurador, Gerente, etc. |
| TASK-01 | Gestão de Tarefas | Tarefas criadas manualmente sem vínculo ao fluxo | Sim | WF-02 | Tarefa criada automaticamente ao ativar nó | CaseTask em bravojus/cases | Pendente | Tarefa aparece na fila do responsável ao ativar nó do fluxo |
| TASK-02 | Redistribuição com Despacho | Redistribuição manual sem controle ou registro | Não | TASK-01, WF-02 | Request de redistribuição + aprovação/rejeição + despacho | — | Pendente | Redistribuição cria despacho e registra decisão no audit trail |
| TASK-03 | Solicitação à Assessoria | Assessorias recebem tarefas sem contexto | Não | TASK-01, WF-02 | Solicitação com documentos vinculados, retorno ao solicitante | — | Pendente | Assessor vê tarefa, elabora minuta, devolve com documento |
| TASK-04 | Avocação de Processo | PG avoca processo sem fluxo formal | Não | WF-02, PROC-01 | Avocação registrada, FlowInstance reatribuída, log | — | Pendente | PG avoca processo e fluxo é reatribuído com log completo |
| PROC-01 | Gestão de Processos Judiciais | Processos gerenciados em planilhas/sistemas externos | Sim | Organization | CRUD de processos com campos judiciais + vinculação ao fluxo | LegalCase em bravojus/cases (adaptar) | Pendente | Processo criado com número CNJ, tipo, fase, responsável |
| PROC-02 | Vinculação Processo-Fluxo | Processo sem rastreabilidade de fluxo | Não | PROC-01, WF-01 | Processo vinculado a FlowInstance com template específico | — | Pendente | Ao vincular processo, fluxo inicia e primeira tarefa aparece |
| DOC-01 | Gestão Documental | Documentos não vinculados ao processo/etapa | Sim | PROC-01 | Documento criado/anexado com vínculo a processo e etapa | documents/ em bravojus | Pendente | Documento visível no timeline do processo |
| DOC-02 | Geração de Minuta por IA | Minutas elaboradas manualmente do zero | Não | DOC-01, IA-02 | Editor TinyMCE + IA + template + revisão humana | copilot em bravojus | Pendente | IA gera minuta baseada no processo; usuário revisa antes de assinar |
| DOC-03 | Assinatura de Despacho | Assinatura manual fora do sistema | Não | DOC-01, TASK-01 | Despacho assinado via certificado digital, vinculado ao fluxo | assinatura-digital em bravojus | Pendente | Despacho assinado registrado no audit trail com timestamp |
| IA-01 | Resumo de Processo | Procurador lê o processo do início para se contextualizar | Não | PROC-01, DOC-01 | IA gera resumo com partes, pedidos, fatos, histórico recente | copilot/rag em bravojus | Pendente | Resumo gerado em <5s, auditável, revisável |
| IA-02 | Geração de Despacho/Minuta | Elaboração repetitiva de minutas padrão | Não | DOC-01, WF-02 | IA sugere minuta baseada no contexto + templates; revisão humana | copilot em bravojus | Pendente | Minuta gerada com base no tipo de solicitação e processo |
| AUD-01 | Auditoria Completa | Impossível saber quem fez o quê, quando | Sim | Todos | Cada ação registra: ator, data, etapa, justificativa, antes/depois | auditoria em bravojus (expandir) | Pendente | Trilha completa do processo desde a distribuição até arquivamento |
| DASH-01 | Indicadores Operacionais | Gestores sem visibilidade de gargalos | Não | PROC-01, WF-02 | Dashboard com tempo por etapa, carga por procurador, volume | analytics em bravojus (expandir) | Pendente | Dashboard mostra top 5 gargalos por etapa do fluxo |
| LAND-01 | Landing Page Verus.AI | Usuário não entende o valor da plataforma antes de logar | Sim | — | Narrativa + animações + seções de impacto | catálogo bravonix (referência) + design system ui/ | Pendente | Visitante entende o que é verus.ai em <10s; CTA claro para login |
| SEC-01 | Permissões por Órgão/Unidade | Vazamento de dados entre procuradorias | Sim | Organization | Filter by organ em todos os querysets; middleware de isolamento | — | Pendente | Usuário de órgão A não vê dados do órgão B |
| SEC-02 | Permissões por Papel no Fluxo | Ator executa etapas que não são de sua lane | Não | WF-02 | TaskInstance validada contra lane e role do usuário antes de executar | accounts/permissions em bravojus | Pendente | Procurador não pode executar tarefa da lane do Gerente |

---

## 26. Matriz de Cobertura dos Fluxos Anexados

### Fluxo Judicial: Gerência Judicial — Processos Eletrônicos — 1º Grau

| Etapa do Fluxo | Ator | Módulo que entrega | Funcionalidade | Existe hoje? | Será criado? | Lacuna |
|---------------|------|-------------------|--------------|-------------|-------------|--------|
| Entrada do processo no fluxo | Sistema | PROC-01, WF-02 | Criação de processo + início de FlowInstance | ✅ Parcial | Refatorar | Vinculação automática ao template de fluxo |
| Distribuir ao Procurador(a) | Distribuidor | TASK-01, WF-02 | Criação de tarefa de distribuição com atribuição | ✅ Parcial | Refatorar | Distribuição integrada ao workflow |
| Solicitar Redistribuição | Procurador | TASK-02 | Request de redistribuição com justificativa | ❌ Não | Criar | Módulo de solicitações entre lanes |
| Redistribuição aceita? (Gateway) | Gerente | WF-02 | Gateway com avaliação de condição | ❌ Não | Criar | Engine de gateway |
| Despacho de Deferimento | Gerente | DOC-03, WF-02 | Geração e assinatura de despacho de deferimento | ❌ Não | Criar | Template de despacho + assinatura integrada |
| Despacho de Indeferimento | Gerente | DOC-03, WF-02 | Geração e assinatura de despacho de indeferimento | ❌ Não | Criar | Template de despacho + assinatura integrada |
| Elaborar Petição | Procurador | DOC-01, IA-02 | Editor de petição + IA opcional | ✅ Parcial | Expandir | Vínculo à etapa do fluxo |
| Anexar Petição | Procurador | DOC-01 | Anexação de documento ao processo/etapa | ✅ Parcial | Expandir | Vínculo à etapa do fluxo |
| Realizar Peticionamento | Procurador | Integração PJe | Protocolo eletrônico no PJe/EPROC | ✅ Parcial (datajud) | Expandir | Integração de peticionamento |
| Abrir solicitação à Assessoria Gerência | Procurador | TASK-03 | Request para lane Assessor Gerencial | ❌ Não | Criar | Módulo de solicitações inter-lane |
| Elaborar Minuta (Assessoria Gerência) | Assessor Gerencial | DOC-02 | Editor de minuta + IA + devolução | ❌ Não | Criar | Lane de Assessoria com task de elaboração |
| Devolver solicitação | Assessor Gerencial | TASK-03 | Devolução com documento + gateway de tipo | ❌ Não | Criar | Devolução com selecão de tipo (minuta/despacho/corrigir) |
| Assinar Despacho | Gerente | DOC-03 | Assinatura digital de despacho | ✅ Parcial | Integrar ao fluxo | Trigger de assinatura pelo workflow |
| Reabrir Solicitação à Assessoria | Procurador | TASK-03 | Reabertura de solicitação com justificativa | ❌ Não | Criar | Estado "reaberto" na solicitação |
| Avocar Processo | Procurador Geral | TASK-04 | Avocação com reatribuição + log | ❌ Não | Criar | Módulo de avocação |
| Abrir solicitação à Assessoria Gabinete | Procurador | TASK-03 | Idêntico à gerência, outra lane | ❌ Não | Criar | Lane de Assessoria Gabinete |
| Armazenar Processo | Distribuidor | PROC-01 | Arquivamento do processo + encerramento do fluxo | ✅ Parcial | Integrar ao fluxo | Trigger de arquivamento pelo workflow |

**Score de cobertura atual:** 6/17 etapas cobertas (parcialmente). 11/17 precisam ser criadas.

---

## 27. Riscos, Dependências e Bloqueios

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Migração de dados do Verus.AI para verus.ai | Médio | Alto | Criar migrations cuidadosas, não apagar dados de produção sem backup |
| Performance do @xyflow/react com 50+ nós | Baixo | Médio | React.memo em nodes, virtualização, lazy loading de nodes fora do viewport |
| Integração PJe/EPROC — API instável | Alto | Alto | Mock de integração para MVP; design da UI independente da integração |
| Custo de IA com volume alto de processos | Médio | Médio | Rate limiting, cache de resultados, IA opcional (não obrigatória) |
| Isolamento multi-tenant insuficiente | Baixo | Crítico | Code review obrigatório de cada queryset; testes de isolamento |
| Assinatura digital fora do prazo/ICP-Brasil | Médio | Médio | Isolar módulo de assinatura, permitir uso sem assinatura digital no MVP |
| LGPD — dados de processos na IA | Médio | Alto | Prompt templates sem CPF/CNPJ; opt-in explícito por órgão |

### 27.1 Dependências Críticas

1. **Definição de Órgão/Unidade:** Antes de qualquer funcionalidade, o modelo Organization precisa estar definido e em produção — tudo depende disso.
2. **Publicação de Template de Fluxo:** O Workflow Engine só funciona após o Builder existir e um template ser publicado.
3. **Roles de Procuradoria:** A autorização de execução de etapas por lane depende dos roles corretos.

### 27.2 Bloqueios Identificados

- **Integração PJe/EPROC:** Requer acesso às APIs dos tribunais — pode ser uma dependência externa com prazo incerto.
- **Assinatura Digital (ICP-Brasil):** Requer certificado do usuário — pode ser inviável no MVP; usar placeholder.
- **Dados reais para testes:** Precisamos de processos reais (ou realistas) para testar os fluxos.

---

## 28. Decisões que Exigem Consenso

1. **Biblioteca de Canvas:** A recomendação é **@xyflow/react**, mas isso precisa de aprovação. Alternativa: **bpmn-js** para maior fidelidade BPMN.

2. **Swim Lanes:** Implementar dentro do @xyflow/react (containers + grupos) vs usar bpmn-js nativo. A opção @xyflow/react exige mais desenvolvimento mas dá controle total.

3. **Multi-tenancy:** Isolamento por `organ` no Django (filtro em querysets) vs schema separado por órgão no PostgreSQL. Recomendação: filtro por `organ` (mais simples, suficiente para escala inicial).

4. **Integração PJe/EPROC no MVP:** Incluir no MVP com mock/simulação, ou excluir e colocar na Fase 2? Recomendação: UI preparada, integração real na Fase 2.

5. **Assinatura Digital no MVP:** Incluir integração real com ICP-Brasil, ou usar upload de assinatura PNG no MVP? Recomendação: upload de assinatura no MVP, ICP-Brasil na Fase 2.

6. **Remoção do financeiro:** Confirmar que módulos `financeiro`, `custas`, `honorarios`, `nfse`, `timesheet` devem ser removidos completamente.

7. **Narrativa da landing page:** Validar as seções propostas com o usuário antes da implementação.

8. **AI Provider:** OpenAI (já configurado) vs Claude/Anthropic vs dual? Recomendação: dual com fallback (Claude como primário para documentos jurídicos, OpenAI como fallback).

---

## 29. Critérios de Aceite da Fase de Planejamento

- [x] Auditoria completa do Verus.AI
- [x] Auditoria do FlowchartAI
- [x] Auditoria do catálogo bravonix
- [x] Análise dos fluxos VERUS (BPM + PNG)
- [x] Extração de requisitos dos fluxos
- [x] Pesquisa comparativa de bibliotecas Canvas/Workflow
- [x] Mapa de funcionalidades atuais
- [x] Mapa de funcionalidades reaproveitáveis
- [x] Mapa de funcionalidades a criar/substituir
- [x] Arquitetura alvo proposta
- [x] Planejamento do workflow builder e engine
- [x] Planejamento de front-end
- [x] Planejamento de back-end
- [x] Planejamento de banco de dados
- [x] Planejamento de IA
- [x] Planejamento de segurança
- [x] Planejamento de testes
- [x] Roadmap de implementação
- [x] Checklist funcional com evidências
- [x] Matriz de cobertura dos fluxos anexados
- [x] Riscos e dependências
- [x] Decisões pendentes listadas

---

## 30. Solicitação de Aprovação para Iniciar Implementação

Este planejamento foi elaborado com base em análise direta dos repositórios, arquivos BPM (XPDL 2.2 extraído e parseado), design system documentado e referências visuais.

**Antes de iniciar a implementação, precisamos de aprovação explícita nos seguintes pontos:**

### 30.1 Aprovações Técnicas

| # | Decisão | Recomendação | Sua decisão |
|---|---------|-------------|-------------|
| D1 | Biblioteca de Canvas | @xyflow/react v12 | ⬜ Aprovar / ⬜ bpmn-js / ⬜ Outra |
| D2 | Swim Lanes | Grupos no @xyflow/react | ⬜ Aprovar / ⬜ Outra solução |
| D3 | Multi-tenancy | Filtro por `organ` no Django | ⬜ Aprovar / ⬜ Schema separado |
| D4 | MVP: PJe/EPROC | UI pronta, integração real na Fase 2 | ⬜ Aprovar / ⬜ Incluir no MVP |
| D5 | MVP: Assinatura Digital | Upload de assinatura, ICP-Brasil na Fase 2 | ⬜ Aprovar / ⬜ ICP-Brasil no MVP |
| D6 | Remover módulos privados | Remover financeiro, portal cliente, timesheet | ⬜ Aprovar / ⬜ Manter algum |
| D7 | AI Provider | Dual: Claude primário + OpenAI fallback | ⬜ Aprovar / ⬜ Apenas OpenAI / ⬜ Apenas Claude |

### 30.2 Aprovações Funcionais

| # | Decisão | Proposta |
|---|---------|---------|
| F1 | Roadmap de implementação | 6 fases conforme Seção 24 |
| F2 | Módulos do MVP (Fase 1+2+3) | Fundação + Workflow Builder + Workflow Engine |
| F3 | Seções da landing page verus.ai | Conforme Seção 18 |
| F4 | Roles de procuradoria | Distribuidor, Procurador, Gerente, Assessor Gerencial, Assessor Gabinete, PG, Subpg |
| F5 | Narrativa da plataforma | "Centro de operações para procuradorias — processos, fluxos e IA em uma só plataforma" |

---

**Aguardando aprovação explícita para iniciar a Fase 1 de implementação.**

---

*Documento gerado em 2026-06-11. Versão 1.0. Pendente de aprovação.*
