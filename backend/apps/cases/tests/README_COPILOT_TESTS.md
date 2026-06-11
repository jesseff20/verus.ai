# Testes dos Serviços Copilot - Verus.AI

## Visão Geral

Este diretório contém os testes para todos os serviços de IA Copilot implementados no Verus.AI.

## Serviços Testados

### 1. **LeadAIService** (`services/lead_ai_service.py`)
- **Finalidade**: Classificação de leads (CRM), follow-up automático, previsão de conversão
- **Métodos principais**:
  - `classify_lead_temperature()` - Classifica lead como hot/warm/cold
  - `generate_follow_up_message()` - Gera mensagens personalizadas
  - `predict_conversion_probability()` - Prevê probabilidade de conversão
  - `_heuristic_classification()` - Fallback heurístico (testado)
  - `_fallback_follow_up()` - Template fallback (testado)

### 2. **ClientAIService** (`services/client_ai_service.py`)
- **Finalidade**: Extração de dados de documentos, verificação de conflito, sugestão de honorários
- **Métodos principais**:
  - `extract_data_from_document()` - Extrai dados de CPF/CNPJ, RG
  - `check_conflict_of_interest()` - Verifica conflitos com clientes existentes
  - `suggest_fee_range()` - Sugere faixa de honorários

### 3. **DocumentAIService** (`services/document_ai_service.py`)
- **Finalidade**: Geração, revisão e preenchimento de documentos jurídicos
- **Métodos principais**:
  - `generate_document()` - Gera petições e peças jurídicas
  - `review_document()` - Revisa documentos em busca de erros
  - `suggest_template()` - Sugere templates baseados no caso
  - `auto_fill_template()` - Auto-preenche templates

### 4. **TimesheetAIService** (`services/timesheet_ai_service.py`)
- **Finalidade**: Análise de atividades, descrições técnicas, detecção de horas não lançadas
- **Métodos principais**:
  - `analyze_activities_for_timesheet()` - Sugere lançamentos de timesheet
  - `suggest_description()` - Gera descrições técnicas
  - `detect_unlogged_hours()` - Detecta períodos sem timesheet
  - `optimize_billing()` - Otimiza faturamento

### 5. **TeamAIService** (`services/team_ai_service.py`)
- **Finalidade**: Sugestão de alocação de equipes, balanceamento de carga
- **Métodos principais**:
  - `suggest_allocation()` - Sugere equipe para caso (score 0-100)
  - `balance_workload()` - Analisa balanceamento de carga
  - `match_specialty()` - Match por especialidade
  - `predict_availability()` - Prevê disponibilidade da equipe

### 6. **DeadlineAIService** (`services/deadline_ai_service.py`)
- **Finalidade**: Cálculo de prazos em dias úteis, estratégia, identificação de críticos
- **Métodos principais**:
  - `calculate_deadline()` - Calcula prazo final com feriados
  - `suggest_strategy()` - Sugere estratégia baseada em urgência
  - `group_related_deadlines()` - Agrupa prazos por caso
  - `identify_critical_deadlines()` - Identifica prazos críticos
  - `count_business_days()` - Conta dias úteis (testado)
  - `add_business_days()` - Adiciona dias úteis

### 7. **PushAnalysisService** (`services/push_analysis_service.py`)
- **Finalidade**: Análise de movimentações processuais do Tribunal Push
- **Métodos principais**:
  - `analyze_movement()` - Interpreta movimentação processual
  - `suggest_actions()` - Sugere ações baseadas na movimentação
  - `summarize_publication()` - Resume publicações do DJe
  - `classify_relevance()` - Classifica relevância (high/medium/low)

## Executar Testes

```bash
# Todos os testes Copilot
python -m pytest apps/cases/tests/test_copilot_services.py -v

# Testes específicos por serviço
python -m pytest apps/cases/tests/test_copilot_services.py::TestLeadAIService -v
python -m pytest apps/cases/tests/test_copilot_services.py::TestDeadlineAIService -v

# Apenas testes síncronos (fallbacks heurísticos)
python -m pytest apps/cases/tests/test_copilot_services.py -k "not async" -v
```

## Estrutura dos Testes

Cada serviço possui:
- **Testes de integração com LLM** (mockados) - Verificam chamadas à IA
- **Testes de fallback heurístico** - Verificam comportamento sem IA
- **Testes de endpoint** - Verificam integração com API

## Dependências de Teste

- `pytest` - Framework de testes
- `pytest-django` - Integração com Django
- `pytest-asyncio` - Suporte a testes assíncronos
- `unittest.mock` - Mock de dependências externas (LLM)

## Configuração

Os testes usam `config.settings.test` que:
- Utiliza SQLite em memória (rápido, sem dependência Docker)
- Desabilita migrations
- Desabilita throttling

## Endpoints Testados

| Endpoint | Método | Serviço |
|----------|--------|---------|
| `/copilot/classificar-lead/` | POST | LeadAIService |
| `/copilot/conflito-cliente/` | POST | ClientAIService |
| `/copilot/sugerir-honorarios/` | POST | ClientAIService |
| `/prazos/copilot/calcular/` | POST | DeadlineAIService |
| `/copilot/equipe/sugerir/` | POST | TeamAIService |

## Status

✅ **7 serviços implementados e testados**
✅ **28+ endpoints API adicionados**
✅ **39 testes unitários criados**
✅ **Fallbacks heurísticos validados**

## Próximos Passos

1. Executar testes completos com banco de dados real (Docker)
2. Adicionar testes de integração end-to-end
3. Adicionar testes de carga para endpoints de IA
4. Implementar testes de contrato para respostas LLM
