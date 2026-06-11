# App: Agents

## Descrição

App responsável por gerenciar prompts de agentes de IA do sistema BravoDoc. Permite criar e configurar diferentes tipos de agentes (corretor, gerador de exemplos, análise, etc.) com prompts customizáveis, escolha de provider LLM (OpenAI/Anthropic) e integração opcional com RAG.

## Funcionalidades

### 1. Gerenciamento de Prompts de Agentes
- Criação de agentes especializados
- System prompts e user prompt templates
- Variáveis dinâmicas em templates
- Versionamento de prompts

### 2. Configuração de LLM
- Suporte a múltiplos providers (OpenAI, Anthropic)
- Seleção de modelos (GPT-4, Claude, etc.)
- Configuração de parâmetros (temperature, max_tokens)

### 3. Integração com RAG
- Opção de usar contexto da base de conhecimento
- Enriquecimento automático de prompts com informações relevantes

### 4. Tipos de Agentes

| Tipo | Descrição | Uso Típico |
|------|-----------|-----------|
| `corretor` | Corretor de Texto | Corrigir gramática e ortografia |
| `exemplo` | Gerador de Exemplos | Gerar exemplos práticos |
| `analise` | Análise de Qualidade | Avaliar qualidade do conteúdo |
| `sugestao` | Sugestões de Melhoria | Sugerir melhorias no texto |
| `expansao` | Expansão de Conteúdo | Expandir seções curtas |
| `simplificacao` | Simplificação | Simplificar texto técnico |

## Estrutura de Arquivos

```
apps/agents/
├── __init__.py
├── admin.py           # Interface admin com preview
├── apps.py            # Configuração do app
├── migrations/        # Migrações do banco
├── models.py          # Model AgentPrompt
├── permissions.py     # Permissões de acesso
├── serializers.py     # Serializers incluindo execução
├── urls.py            # Rotas do app
└── views.py           # ViewSets com action de execução
```

## Models

### AgentPrompt
```python
class AgentPrompt(models.Model):
    name = CharField(max_length=255)
    agent_type = CharField(choices=AGENT_TYPES)
    description = TextField(blank=True)
    system_prompt = TextField()
    user_prompt_template = TextField()
    llm_provider = CharField(choices=[('openai', 'OpenAI'), ('anthropic', 'Anthropic')])
    model_name = CharField(max_length=100, default='gpt-4o-mini')
    temperature = FloatField(default=0.7)
    max_tokens = IntegerField(default=1000)
    use_rag = BooleanField(default=False)
    version = IntegerField(default=1)
    is_active = BooleanField(default=True)
    created_by = ForeignKey(User)
```

## Sistema de Variáveis em Templates

### Sintaxe

Variáveis são marcadores no user_prompt_template que serão substituídos:

```
{{variable_name}}
```

### Exemplo de User Prompt Template

```
Por favor, corrija o seguinte texto:

{{texto}}

Mantenha o tom {{tom}} e o público-alvo é {{publico}}.
```

### Variáveis Extraídas Automaticamente

O método `extract_variables()` extrai todas as variáveis:

```python
prompt = AgentPrompt.objects.get(id=prompt_id)
variables = prompt.extract_variables()
# ['texto', 'tom', 'publico']
```

## API Endpoints

Base URL: `/api/v1/agents/`

### CRUD Básico

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/v1/agents/` | Listar prompts | Admin/Manager |
| GET | `/api/v1/agents/{id}/` | Detalhes do prompt | Admin/Manager |
| POST | `/api/v1/agents/` | Criar prompt | Admin/Manager |
| PUT/PATCH | `/api/v1/agents/{id}/` | Atualizar prompt | Admin/Manager |
| DELETE | `/api/v1/agents/{id}/` | Deletar prompt | Admin/Manager |

### Endpoints Especiais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/agents/{id}/variables/` | Extrair variáveis do template |
| POST | `/api/v1/agents/{id}/execute/` | Executar agente com variáveis |

### Filtros

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `agent_type` | Filtrar por tipo | `?agent_type=corretor` |
| `llm_provider` | Filtrar por provider | `?llm_provider=openai` |
| `is_active` | Apenas ativos | `?is_active=true` |

## Exemplos de Uso

### 1. Criar Agente Corretor

```bash
POST /api/v1/agents/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Corretor de Texto ETP",
  "agent_type": "corretor",
  "description": "Corrige ortografia e gramática em textos de ETP",
  "system_prompt": "Você é um especialista em língua portuguesa e correção de textos técnicos. Corrija apenas erros de ortografia e gramática, mantendo o conteúdo original.",
  "user_prompt_template": "Corrija o seguinte texto:\n\n{{texto}}\n\nMantenha o tom {{tom}}.",
  "llm_provider": "openai",
  "model_name": "gpt-4o-mini",
  "temperature": 0.3,
  "max_tokens": 2000,
  "use_rag": false,
  "is_active": true
}
```

### 2. Criar Agente com RAG

```bash
POST /api/v1/agents/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Gerador de Exemplos com Contexto",
  "agent_type": "exemplo",
  "description": "Gera exemplos baseados na base de conhecimento",
  "system_prompt": "Você é um especialista em licitações. Use o contexto fornecido para gerar exemplos práticos e relevantes.",
  "user_prompt_template": "Gere 3 exemplos de {{conceito}} aplicados a {{contexto}}.",
  "llm_provider": "anthropic",
  "model_name": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "max_tokens": 1500,
  "use_rag": true,
  "is_active": true
}
```

### 3. Extrair Variáveis do Template

```bash
GET /api/v1/agents/{agent_id}/variables/
Authorization: Bearer {token}

Response:
{
  "variables": ["texto", "tom"],
  "count": 2
}
```

### 4. Executar Agente

```bash
POST /api/v1/agents/{agent_id}/execute/
Authorization: Bearer {token}
Content-Type: application/json

{
  "variables": {
    "texto": "A justificativa da contrataçao e necessaria para atender a demanda...",
    "tom": "formal"
  }
}

Response:
{
  "agent_name": "Corretor de Texto ETP",
  "llm_provider": "openai",
  "model_name": "gpt-4o-mini",
  "response": "A justificativa da contratação é necessária para atender à demanda...",
  "tokens_used": 150,
  "execution_time_ms": 1234
}
```

### 5. Executar Agente com RAG

```bash
POST /api/v1/agents/{agent_id}/execute/
Authorization: Bearer {token}
Content-Type: application/json

{
  "variables": {
    "conceito": "dispensa de licitação",
    "contexto": "obras emergenciais"
  }
}

# Se use_rag=true, o sistema:
# 1. Busca contexto relevante na base de conhecimento
# 2. Adiciona ao prompt antes de enviar ao LLM
# 3. LLM gera resposta com base no contexto encontrado
```

## System Prompts por Tipo de Agente

### Corretor
```
Você é um especialista em língua portuguesa e correção de textos técnicos.
Corrija apenas erros de ortografia e gramática, mantendo o conteúdo e estrutura originais.
Retorne apenas o texto corrigido, sem explicações adicionais.
```

### Gerador de Exemplos
```
Você é um especialista em documentação técnica e licitações públicas.
Gere exemplos práticos, claros e aplicáveis ao contexto brasileiro.
Use linguagem formal e técnica apropriada.
```

### Análise de Qualidade
```
Você é um auditor de documentos técnicos especializado em Documents.
Analise a qualidade, completude e adequação do conteúdo.
Identifique pontos fortes e fracos.
Forneça feedback construtivo e objetivo.
```

### Sugestões de Melhoria
```
Você é um consultor especializado em otimização de documentos técnicos.
Sugira melhorias específicas e acionáveis para o conteúdo.
Priorize clareza, completude e conformidade com normas.
```

### Expansão de Conteúdo
```
Você é um redator técnico especializado em documentação de licitações.
Expanda o conteúdo fornecido mantendo precisão e relevância.
Adicione detalhes técnicos, justificativas e contexto quando apropriado.
```

### Simplificação
```
Você é um comunicador especializado em tornar textos técnicos acessíveis.
Simplifique o texto mantendo a precisão das informações.
Use linguagem clara e evite jargões quando possível.
```

## Configuração de Modelos LLM

### OpenAI

| Modelo | Descrição | Tokens | Custo | Velocidade |
|--------|-----------|--------|-------|------------|
| `gpt-4o` | Mais capaz | 128K | $$$ | Média |
| `gpt-4o-mini` | Balanço custo/performance | 128K | $ | Rápida |
| `gpt-4-turbo` | Versão anterior | 128K | $$$ | Média |

### Anthropic

| Modelo | Descrição | Tokens | Custo | Velocidade |
|--------|-----------|--------|-------|------------|
| `claude-3-5-sonnet-20241022` | Mais recente e capaz | 200K | $$$ | Média |
| `claude-3-5-haiku-20241022` | Rápido e econômico | 200K | $ | Rápida |
| `claude-3-opus-20240229` | Mais poderoso | 200K | $$$$ | Lenta |

## Admin Interface

Acessível em: `/admin/agents/agentprompt/`

### Funcionalidades:
- Listagem com filtros por tipo, provider e status
- Busca por nome e descrição
- Display de tipo com badges coloridos
- Preview de prompts
- Extração de variáveis
- Toggle de ativo/inativo

## Permissions

### CanManageAgents
Permite acesso apenas para:
- `superadmin`
- `admin`
- `manager`

```python
permission_classes = [CanManageAgents]
```

## Fluxo de Execução

```
1. Frontend solicita execução do agente
2. Backend valida variáveis necessárias
3. Substitui variáveis no user_prompt_template
4. Se use_rag=true:
   a. Gera embedding da query
   b. Busca chunks relevantes no KB
   c. Adiciona contexto ao prompt
5. Monta payload para LLM provider
   - system_prompt
   - user_prompt (com variáveis substituídas e contexto RAG)
6. Chama API do provider (OpenAI/Anthropic)
7. Recebe resposta
8. Retorna para frontend
```

## Integração com RAG

Quando `use_rag=True`:

```python
# 1. Buscar contexto relevante
from apps.rag.services import search_kb

context = search_kb(
    query=prompt_variables['texto'],
    top_k=5
)

# 2. Enriquecer prompt
enriched_prompt = f"""
Contexto relevante da base de conhecimento:
{context}

---

{user_prompt}
"""

# 3. Enviar para LLM
response = llm.call(enriched_prompt)
```

## Dependências

- Django 5.0+
- djangorestframework
- openai (OpenAI API)
- anthropic (Anthropic API)
- drf-spectacular

## Configuração

### settings.py

```python
# LLM Providers
OPENAI_API_KEY = env('OPENAI_API_KEY')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY')

# Defaults
DEFAULT_LLM_PROVIDER = 'openai'
DEFAULT_MODEL = 'gpt-4o-mini'
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000
```

### .env

```bash
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Próximos Passos (TODO)

- [ ] Implementar chamadas reais às APIs OpenAI/Anthropic
- [ ] Criar serviço LLM abstrato (factory pattern)
- [ ] Adicionar cache de respostas para queries idênticas
- [ ] Implementar rate limiting por usuário
- [ ] Adicionar métricas de uso (tokens, custo, latência)
- [ ] Criar logs de execuções para auditoria
- [ ] Implementar fallback automático entre providers
- [ ] Adicionar suporte a streaming de respostas
- [ ] Criar testes automatizados com mock de LLMs
- [ ] Implementar fine-tuning de modelos

## Exemplos de Integração

### Em Documents
```python
# Corrigir justificativa antes de salvar
from apps.agents.models import AgentPrompt

corretor = AgentPrompt.objects.get(agent_type='corretor', is_active=True)
resultado = corretor.execute({
    'texto': etp.data['justificativa'],
    'tom': 'formal'
})

etp.data['justificativa'] = resultado['response']
etp.save()
```

### Em Templates
```python
# Expandir seção curta
expansor = AgentPrompt.objects.get(agent_type='expansao', is_active=True)
conteudo_expandido = expansor.execute({
    'texto': section_content,
    'detalhes': 'adicione exemplos práticos'
})
```

## Monitoramento de Custos

### Estimativa por Modelo

**OpenAI (gpt-4o-mini)**
- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens
- Média: ~500 tokens/execução = $0.0004

**Anthropic (claude-3-5-haiku)**
- Input: $1.00 / 1M tokens
- Output: $5.00 / 1M tokens
- Média: ~500 tokens/execução = $0.0025

### Calcular Custo

```python
def calculate_cost(tokens_used, model_name):
    pricing = {
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'claude-3-5-haiku': {'input': 1.00, 'output': 5.00}
    }
    # ... cálculo baseado em tokens de input/output
```

## Relacionamentos

Este app é utilizado por:
- **Documents**: Para melhorar conteúdo dos campos durante preenchimento
- **rag**: Agentes podem usar RAG para contexto adicional
