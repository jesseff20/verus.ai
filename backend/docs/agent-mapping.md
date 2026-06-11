# Mapeamento Completo de Agentes Jurídicos — Verus.AI

> Gerado em 2026-05-27
> Fonte: código-fonte em `/mnt/c/bravonix/bravojus/backend/`

---

## 1. VISÃO GERAL DA ARQUITETURA

O sistema Verus.AI possui **três grandes famílias** de agentes, com papéis distintos:

| Família | Modelo | App | Propósito |
|---------|--------|-----|-----------|
| **SectionAgentConfig** (agentes de seção) | `SectionAgentConfig` | `intelligent_assistant` | Geradores, validadores, analisadores e refinadores de seções de documentos (ETP e peças jurídicas) |
| **AgentPrompt** (agentes de chat) | `AgentPrompt` | `agents` | Assistentes conversacionais (copilot jurídico) por especialidade |
| **Python Classes** (agentes code-behind) | Classes em `agents/` | `intelligent_assistant` | Implementações concretas: 15 geradores + 15 validadores de ETP |

---

## 2. AGENTES DE SEÇÃO (SectionAgentConfig) — 11 agentes do seed jurídico

Criados pelo seed `seed_juridico_completo.py`. Usam `watsonx` + `mistralai/mistral-medium-2505`. Template de usuário padrão: `USER_TEMPLATE_SECAO`.

### 2.1 Geradores (agent_type='generator')

| # | Nome | Key | Descrição | Temp | Max Tokens | Default |
|---|------|-----|-----------|------|------------|---------|
| 1 | **Verus.AI - Gerador Cível** | `gerador_civel` | Gera seções de peças cíveis: petições, contestações, execuções e embargos | 0.7 | 4096 | Sim |
| 2 | **Verus.AI - Gerador Recursal** | `gerador_recursal` | Gera seções de recursos: apelação, agravo, REsp, RE, embargos de declaração | 0.7 | 4096 | Não |
| 3 | **Verus.AI - Gerador Constitucional** | `gerador_constitucional` | Gera seções de remédios constitucionais: HC, MS e tutelas de urgência | 0.7 | 4096 | Não |
| 4 | **Verus.AI - Gerador Trabalhista** | `gerador_trabalhista` | Gera seções de peças trabalhistas: reclamação, contestação e contratos CLT | 0.7 | 4096 | Não |
| 5 | **Verus.AI - Gerador Tributário** | `gerador_tributario` | Gera seções de peças tributárias: embargos execução fiscal, MS tributário, defesa adm. fiscal | 0.7 | 4096 | Não |
| 6 | **Verus.AI - Gerador Criminal** | `gerador_criminal` | Gera seções de peças criminais: queixa-crime e alegações finais | 0.7 | 4096 | Não |
| 7 | **Verus.AI - Gerador Extrajudicial** | `gerador_extrajudicial` | Gera seções de documentos extrajudiciais: contratos, notificações, pareceres e procurações | 0.7 | 4096 | Não |
| 8 | **Verus.AI - Gerador Administrativo** | `gerador_administrativo` | Gera seções de peças administrativas: defesa em PAD, recurso adm., requerimento adm. | 0.7 | 4096 | Não |
| 9 | **Verus.AI - Sugestão de Pedidos** | `agente_sugestao_pedidos` | Sugere pedidos processuais estratégicos implícitos, alternativos e sucessivos | 0.5 | 2048 | Não |

### 2.2 Validadores (agent_type='validator')

| # | Nome | Key | Descrição | Temp | Max Tokens |
|---|------|-----|-----------|------|------------|
| 10 | **Verus.AI - Validador Jurídico** | `validador_juridico` | Valida o conteúdo jurídico gerado para todas as áreas do direito | 0.3 | 1024 |
| 11 | **Verus.AI - Verificação de Cabimento** | `agente_verificacao_cabimento` | Verifica se o instrumento jurídico é cabível para o caso concreto | 0.2 | 2048 |
| 12 | **Verus.AI - Consistência Jurídica** | `agente_consistencia` | Verifica consistência interna: coerência fato-fundamento-pedido, contradições, placeholders | 0.2 | 2048 |

### 2.3 Analisadores (agent_type='analyzer')

| # | Nome | Key | Descrição | Temp | Max Tokens |
|---|------|-----|-----------|------|------------|
| 13 | **Verus.AI - Coleta de Dados** | `agente_coleta_dados` | Identifica dados obrigatórios faltantes e solicita informações ao usuário | 0.3 | 2048 |
| 14 | **Verus.AI - Cálculo de Prazos** | `agente_calculo_prazos` | Calcula prazos processuais (dias úteis/corridos, feriados, recesso forense) | 0.2 | 2048 |

### 2.4 Tools disponíveis (AgentTool)

Criados pelo seed `seed_agent_tools.py`:

| Tool | Tipo | Service Path | Config |
|------|------|-------------|--------|
| **Web Search (Serper)** | `web_search` | `WebSearchTool.execute` | `max_results: 10` |
| **PNCP Search** (declarado no TOOL_REGISTRY) | `pncp_search` | `PNCPSearchTool.execute` | `max_results: 10` (padrão) |

Os tools são vinculados via `AgentToolLink` (M2M com prioridade). O `AgentToolsService.execute_agent_tools()` é chamado antes da geração de cada seção.

---

## 3. AGENTES DE CHAT (AgentPrompt) — 6 agentes conversacionais

Criados no seed `seed_juridico_completo.py` no método `_atualizar_agentes_chat()`. Usam `watsonx` + `mistralai/mistral-medium-2505`. Template de usuário: `{{user_message}}`.

| # | Nome | agent_type | Descrição | Temp | Default |
|---|------|-----------|-----------|------|---------|
| 1 | **Assistente Jurídico Verus.AI** | `consultor_juridico` | Assistente geral — dúvidas de direito, legislação, jurisprudência | 0.5 | **Sim** |
| 2 | **Especialista em Direito Civil** | `especialista_civil` | Obrigações, contratos, responsabilidade civil, família | 0.4 | Não |
| 3 | **Especialista em Direito do Trabalho** | `especialista_trabalhista` | CLT, reforma trabalhista, processo do trabalho, TST | 0.4 | Não |
| 4 | **Especialista em Direito do Consumidor** | `especialista_consumidor` | CDC, responsabilidade por fato/vício, superendividamento | 0.4 | Não |
| 5 | **Especialista em Processo Civil** | `especialista_processual` | CPC/2015, procedimentos, recursos, execução | 0.4 | Não |
| 6 | **Especialista em Direito Tributário** | `especialista_tributario` | CTN, impostos federais/estaduais/municipais, execução fiscal | 0.4 | Não |

Cada um tem `system_prompt` próprio com `_BLOCO_ANTI_ALUCINACAO` + instruções especializadas.

---

## 4. AGENTES DE SEÇÃO ETP (LangGraph) — 30 classes Python

### 4.1 Geradores de ETP (15 classes)

Local: `backend/apps/intelligent_assistant/agents/section_agents/`

Herdeiras de `BaseAgent`, usam `ClaudeService`. Cada uma tem `SYSTEM_PROMPT` próprio.

| # | Classe | Seção |
|---|--------|-------|
| 1 | `Section01Agent` | Descrição da Necessidade |
| 2 | `Section02Agent` | Previsão no Plano de Contratações Anual |
| 3 | `Section03Agent` | Requisitos da Contratação |
| 4 | `Section04Agent` | Estimativa das Quantidades e Memória de Cálculo |
| 5 | `Section05Agent` | Levantamento de Mercado |
| 6 | `Section06Agent` | Estimativa do Preço da Contratação |
| 7 | `Section07Agent` | Descrição da Solução como um Todo |
| 8 | `Section08Agent` | Justificativa para Parcelamento ou Não |
| 9 | `Section09Agent` | Demonstrativo dos Resultados Pretendidos |
| 10 | `Section10Agent` | Providências Prévias ao Contrato |
| 11 | `Section11Agent` | Contratações Correlatas e/ou Interdependentes |
| 12 | `Section12Agent` | Impactos Ambientais |
| 13 | `Section13Agent` | Viabilidade da Contratação / Declaração de Viabilidade |
| 14 | `Section14Agent` | Publicidade do ETP |
| 15 | `Section15Agent` | Responsáveis pela Elaboração do ETP |

Registro central: `SECTION_AGENTS` dict no `__init__.py`.

### 4.2 Validadores de ETP (15 classes + base)

Local: `backend/apps/intelligent_assistant/agents/validators/`

Herdeiras de `BaseValidator` (que herda de `BaseAgent`). Cada uma tem `SYSTEM_PROMPT`, `SECTION_NAME`, `SECTION_NUMBER`, `MIN_WORDS`, `MAX_WORDS`, `KEYWORDS`.

| # | Classe | Seção |
|---|--------|-------|
| — | `BaseValidator` | Classe base — Template Method com validação estrutural + semântica |
| 1 | `Section01Validator` | Descrição da Necessidade |
| 2 | `Section02Validator` | Previsão no PCA |
| 3 | `Section03Validator` | Requisitos da Contratação |
| 4 | `Section04Validator` | Estimativa das Quantidades |
| 5 | `Section05Validator` | Levantamento de Mercado |
| 6 | `Section06Validator` | Estimativa do Preço |
| 7 | `Section07Validator` | Descrição da Solução |
| 8 | `Section08Validator` | Justificativa Parcelamento |
| 9 | `Section09Validator` | Resultados Pretendidos |
| 10 | `Section10Validator` | Providências Prévias |
| 11 | `Section11Validator` | Contratações Correlatas |
| 12 | `Section12Validator` | Impactos Ambientais |
| 13 | `Section13Validator` | Viabilidade da Contratação |
| 14 | `Section14Validator` | Publicidade do ETP |
| 15 | `Section15Validator` | Responsáveis pela Elaboração |

Registro central: `SECTION_VALIDATORS` dict no `__init__.py`.

Regra de validação: cada validador faz 2 passos:
1. **Validação estrutural** (sem IA): contagem de palavras, parágrafos, keywords
2. **Validação semântica** (com Claude): análise técnica via JSON estruturado

Score final = `structural_score * 0.3 + semantic_score * 0.7`

---

## 5. GRAFO LANGGRAPH (ETP) — Fluxo de Delegação

Local: `backend/apps/intelligent_assistant/agents/etp_graph/`

### 5.1 Estrutura do Grafo

```
START -> generate_01 -> validate_01 -> [regenerate: volta generate_01 | next: generate_02 | error: handle_error]
generate_02 -> validate_02 -> [regenerate | next: generate_03 | error]
... (idem para seções 03–14)
generate_15 -> validate_15 -> [regenerate | next: finalize | error]
finalize -> END
handle_error -> END
```

### 5.2 Componentes do Grafo

| Arquivo | Função |
|---------|--------|
| `state.py` | `ETPState` (TypedDict) — 15 seções `section_01` a `section_15` + metadados |
| `nodes.py` | `ETPNodes` — 30 nós (15 generate + 15 validate) + finalize + handle_error |
| `edges.py` | 15 funções de roteamento `route_after_validate_XX` + `ROUTE_FUNCTIONS` dict |
| `etp_graph.py` | `create_etp_graph()` + `compile_etp_graph()` + `ETPGraphRunner` |

### 5.3 ETPGraphRunner (Orquestrador)

Classe `ETPGraphRunner` no `etp_graph.py` — métodos:
- `run()` — execução síncrona
- `arun()` — execução assíncrona
- `stream()` — streaming de estados intermediários

Chamado pelo `ETPOrchestratorService` no `orchestrator_service.py`.

---

## 6. COPILOT JURÍDICO — Serviço de Sugestões em Tempo Real

### 6.1 LegalCopilotService

Local: `backend/apps/intelligent_assistant/services/copilot_service.py`

Não é um "agente" no sentido de modelo, mas um serviço de sugestões contextuais baseado em padrões de texto.

8 tipos de sugestão:

| Tipo | Descrição |
|------|-----------|
| `citation` | Citações jurídicas (doutrina, leis, princípios) |
| `jurisprudence` | Jurisprudência dos tribunais (consulta `JurisprudenceResult`) |
| `clause` | Cláusulas e modelos de documentos |
| `deadline` | Cálculo de prazos processuais |
| `argument` | Argumentos jurídicos |
| `definition` | Definições de termos técnicos |
| `statute` | Legislação aplicável |
| `correction` | Correções gramaticais/técnicas |

### 6.2 Endpoints

| Método | Rota | Função |
|--------|------|--------|
| POST | `/api/v1/intelligent-assistant/copilot/suggest/` | `suggest_copilot` |
| GET | `/api/v1/intelligent-assistant/copilot/commands/` | `list_copilot_commands` |

---

## 7. BLUEPRINTS E VINCULAÇÃO DE AGENTES

### 7.1 Modelo `DocumentBlueprint`

Define a estrutura de um documento. FK para `core.DocumentType`.

### 7.2 Modelo `BlueprintSection`

Cada seção tem:
- `generator_agent` (FK → `SectionAgentConfig`) — agente que gera o conteúdo
- `validator_agent` (FK → `SectionAgentConfig`) — agente que valida o conteúdo
- `sub_sections` (FK para si mesmo) — sub-seções, cada uma com seu `generator_agent`

### 7.3 Endpoints de Agentes

| Método | Rota | Função |
|--------|------|--------|
| GET | `/api/v1/intelligent-assistant/blueprints/{id}/agents/` | `list_blueprint_agents` — lista TODOS agentes do blueprint |
| GET | `/api/v1/intelligent-assistant/agents/{id}/` | `get_section_agent` — detalhe |
| POST | `/api/v1/intelligent-assistant/agents/create/` | `create_section_agent` |
| PUT/PATCH | `/api/v1/intelligent-assistant/agents/{id}/update/` | `update_section_agent` |
| DELETE | `/api/v1/intelligent-assistant/agents/{id}/delete/` | `delete_section_agent` |
| POST | `/api/v1/intelligent-assistant/agents/{id}/execute/` | `execute_section_agent` — executa isoladamente (Formulário Guiado) |
| GET | `/api/v1/intelligent-assistant/section-agents/` | `list_section_agents` — lista para selects do frontend |

---

## 8. RESUMO NUMÉRICO

| Categoria | Quantidade |
|-----------|-----------|
| SectionAgentConfig (seed jurídico) | 14 |
| → Geradores | 9 |
| → Validadores | 3 |
| → Analisadores | 2 |
| AgentPrompt (chat) | 6 |
| Classes Geradoras ETP (Python) | 15 |
| Classes Validadoras ETP (Python) | 15 |
| BaseValidator (classe base) | 1 |
| AgentTool (tools) | 2 (Web Search + PNCP) |
| **Total de agentes distintos** | **~52** (14 DB + 6 chat + 30 classes + 1 base + 2 tools = 53) |

### Observações importantes

1. Os **14 SectionAgentConfig** do seed jurídico e os **30 agentes Python** do ETP são **sistemas paralelos**: os primeiros são configuráveis via Django Admin/PgAdmin para peças jurídicas; os segundos são código fixo para geração de ETP via LangGraph.

2. O **Assistente Jurídico Verus.AI** (`consultor_juridico`) é o agente chat padrão (is_default=True).

3. Os **tools** (Web Search, PNCP) são compartilháveis entre qualquer `SectionAgentConfig` via `AgentToolLink` — a vinculação é configurada em Admin.

4. O grafo LangGraph **não usa** `SectionAgentConfig` — ele instancia diretamente as classes Python `SectionXXAgent` e `SectionXXValidator`.

5. O `ETPOrchestratorService` é o orquestrador central para geração de ETP, enquanto os `SectionAgentConfig` são usados pelo fluxo de `Formulário Guiado` (execução isolada).
