# App: RAG (Retrieval-Augmented Generation)

## Descrição

App responsável pela funcionalidade de RAG (Retrieval-Augmented Generation) do sistema BravoDoc. Permite realizar consultas semânticas na base de conhecimento, gerar respostas com LLMs usando contexto recuperado, e gerenciar contextos personalizados para diferentes casos de uso.

## Funcionalidades

### 1. Execução de Queries RAG
- Busca semântica na base de conhecimento (app kb)
- Geração de embeddings para queries
- Recuperação de chunks relevantes usando pgvector
- Geração de respostas com LLM (OpenAI/Anthropic)
- Histórico completo de queries executadas

### 2. Contextos RAG
- Criação de contextos personalizados
- Vinculação de documentos específicos a contextos
- Configurações customizadas de busca (top_k, threshold)
- Reutilização de contextos em múltiplas queries

### 3. Métricas e Monitoramento
- Tempo de busca (search_time_ms)
- Tempo de LLM (llm_time_ms)
- Contagem de tokens
- Score de similaridade dos chunks recuperados

## Estrutura de Arquivos

```
apps/rag/
├── __init__.py
├── admin.py           # Interface admin com métricas
├── apps.py            # Configuração do app
├── migrations/        # Migrações do banco
├── models.py          # Models RAGQuery e RAGContext
├── permissions.py     # Permissões de acesso
├── serializers.py     # Serializers incluindo execução
├── urls.py            # Rotas do app
└── views.py           # ViewSets com actions de busca
```

## Models

### RAGQuery
```python
class RAGQuery(models.Model):
    # Relações
    user = ForeignKey(User)
    etp = ForeignKey(ETP, null=True, blank=True)

    # Query
    query_text = TextField()
    query_embedding = JSONField(null=True)

    # Parâmetros
    top_k = IntegerField(default=5)
    similarity_threshold = FloatField(default=0.7)
    filter_categories = JSONField(default=list)
    filter_tags = JSONField(default=list)

    # Resultados
    retrieved_chunks = JSONField(default=list)
    chunk_count = IntegerField(default=0)

    # LLM Response
    llm_response = TextField(blank=True)
    llm_provider = CharField(max_length=50)
    llm_model = CharField(max_length=100)

    # Métricas
    search_time_ms = IntegerField(null=True)
    llm_time_ms = IntegerField(null=True)
    total_tokens = IntegerField(null=True)

    # Timestamp
    created_at = DateTimeField(auto_now_add=True)
```

### RAGContext
```python
class RAGContext(models.Model):
    # Relações
    user = ForeignKey(User)
    etp = ForeignKey(ETP, null=True, blank=True)
    documents = ManyToManyField(Document)

    # Info
    name = CharField(max_length=255)
    description = TextField(blank=True)

    # Configurações
    default_top_k = IntegerField(default=5)
    default_threshold = FloatField(default=0.7)

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

## API Endpoints

Base URL: `/api/v1/rag/`

### RAG Queries

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/v1/rag/queries/` | Listar queries executadas | Owner/Admin |
| GET | `/api/v1/rag/queries/{id}/` | Detalhes da query | Owner/Admin |
| POST | `/api/v1/rag/queries/execute/` | **Executar query RAG** | Autenticado |
| DELETE | `/api/v1/rag/queries/{id}/` | Deletar query | Owner/Admin |

### RAG Contexts

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/v1/rag/contexts/` | Listar contextos | Owner/Admin |
| GET | `/api/v1/rag/contexts/{id}/` | Detalhes do contexto | Owner/Admin |
| POST | `/api/v1/rag/contexts/` | Criar contexto | Autenticado |
| PUT/PATCH | `/api/v1/rag/contexts/{id}/` | Atualizar contexto | Owner/Admin |
| DELETE | `/api/v1/rag/contexts/{id}/` | Deletar contexto | Owner/Admin |
| POST | `/api/v1/rag/contexts/{id}/add-documents/` | Adicionar documentos | Owner/Admin |
| POST | `/api/v1/rag/contexts/{id}/remove-documents/` | Remover documentos | Owner/Admin |

### Filtros (Queries)

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `etp_id` | Filtrar por ETP | `?etp_id=uuid` |
| `llm_provider` | Filtrar por provider | `?llm_provider=openai` |

### Filtros (Contexts)

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `etp_id` | Filtrar por ETP | `?etp_id=uuid` |

## Exemplos de Uso

### 1. Executar Query RAG Simples

```bash
POST /api/v1/rag/queries/execute/
Authorization: Bearer {token}
Content-Type: application/json

{
  "query_text": "Quais são os requisitos para dispensa de licitação?",
  "top_k": 5,
  "similarity_threshold": 0.7,
  "llm_provider": "openai",
  "model_name": "gpt-4o-mini"
}

Response:
{
  "id": "uuid",
  "query_text": "Quais são os requisitos...",
  "retrieved_chunks": [
    {
      "document_id": "uuid",
      "chunk_index": 5,
      "content": "A dispensa de licitação é prevista no Art. 24...",
      "similarity": 0.89
    },
    ...
  ],
  "chunk_count": 5,
  "llm_response": "Com base na legislação vigente, a dispensa de licitação...",
  "llm_provider": "openai",
  "llm_model": "gpt-4o-mini",
  "search_time_ms": 234,
  "llm_time_ms": 1456,
  "total_tokens": 850,
  "created_at": "2024-10-09T10:30:00Z"
}
```

### 2. Executar Query RAG com Filtros

```bash
POST /api/v1/rag/queries/execute/
Authorization: Bearer {token}
Content-Type: application/json

{
  "query_text": "Como calcular o valor estimado da contratação?",
  "etp_id": "uuid-do-etp",
  "top_k": 3,
  "similarity_threshold": 0.75,
  "filter_categories": ["reference", "legislation"],
  "filter_tags": ["licitacao", "orcamento"],
  "llm_provider": "anthropic",
  "model_name": "claude-3-5-haiku-20241022"
}
```

### 3. Criar Contexto RAG

```bash
POST /api/v1/rag/contexts/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Contexto Licitações",
  "description": "Documentos sobre legislação de licitações",
  "etp_id": "uuid-do-etp",
  "document_ids": [
    "uuid-doc-1",
    "uuid-doc-2",
    "uuid-doc-3"
  ],
  "default_top_k": 5,
  "default_threshold": 0.7
}
```

### 4. Executar Query com Contexto

```bash
POST /api/v1/rag/queries/execute/
Authorization: Bearer {token}
Content-Type: application/json

{
  "query_text": "Explique a diferença entre pregão e concorrência",
  "use_context_id": "uuid-do-contexto",
  "llm_provider": "openai",
  "model_name": "gpt-4o"
}

# Sistema usa apenas documentos do contexto especificado
```

### 5. Adicionar Documentos a Contexto

```bash
POST /api/v1/rag/contexts/{context_id}/add-documents/
Authorization: Bearer {token}
Content-Type: application/json

{
  "document_ids": [
    "uuid-doc-4",
    "uuid-doc-5"
  ]
}
```

### 6. Remover Documentos de Contexto

```bash
POST /api/v1/rag/contexts/{context_id}/remove-documents/
Authorization: Bearer {token}
Content-Type: application/json

{
  "document_ids": [
    "uuid-doc-3"
  ]
}
```

### 7. Listar Histórico de Queries

```bash
GET /api/v1/rag/queries/
Authorization: Bearer {token}

Response:
[
  {
    "id": "uuid",
    "user_name": "João Silva",
    "etp_title": "ETP Sistema de Gestão",
    "query_text": "Quais são os requisitos...",
    "chunk_count": 5,
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "created_at": "2024-10-09T10:30:00Z"
  },
  ...
]
```

## Fluxo de Execução RAG

```
1. Usuário submete query via POST /queries/execute/

2. Backend processa query:
   ├─ Gera embedding da query (OpenAI text-embedding-3-small)
   ├─ Salva query_embedding no banco
   └─ Inicia contagem de tempo (search_time_ms)

3. Busca semântica no KB:
   ├─ Se use_context_id: Busca apenas em documentos do contexto
   ├─ Senão: Busca em todos documentos (com filtros se fornecidos)
   ├─ Usa pgvector para similaridade de cosseno
   ├─ Aplica similarity_threshold
   ├─ Retorna top_k chunks mais relevantes
   └─ Registra search_time_ms

4. Monta prompt para LLM:
   ├─ System prompt: "Você é um assistente especializado..."
   ├─ Contexto: Chunks recuperados formatados
   └─ User query: Pergunta original

5. Chama LLM (OpenAI/Anthropic):
   ├─ Inicia contagem de tempo (llm_time_ms)
   ├─ Envia prompt completo
   ├─ Recebe resposta
   ├─ Registra llm_time_ms e total_tokens
   └─ Salva llm_response

6. Salva RAGQuery no banco:
   ├─ query_text
   ├─ query_embedding
   ├─ retrieved_chunks (array com metadata)
   ├─ chunk_count
   ├─ llm_response
   ├─ métricas (tempos, tokens)
   └─ created_at

7. Retorna resposta para usuário
```

## Estrutura de retrieved_chunks

```json
[
  {
    "document_id": "uuid",
    "document_title": "Lei 14.133/2021",
    "chunk_index": 15,
    "content": "Art. 24. É dispensável a licitação quando...",
    "similarity": 0.89,
    "metadata": {
      "page": 12,
      "section": "Capítulo IV"
    }
  },
  {
    "document_id": "uuid",
    "document_title": "Manual de Licitações",
    "chunk_index": 8,
    "content": "Para dispensa de licitação, deve-se...",
    "similarity": 0.85,
    "metadata": {
      "page": 23
    }
  }
]
```

## Parâmetros de Busca

### top_k
Quantidade de chunks a recuperar (1-20):
- **3-5**: Para respostas concisas
- **5-10**: Balanceado (recomendado)
- **10-20**: Para análises profundas

### similarity_threshold
Threshold mínimo de similaridade (0.0-1.0):
- **0.5-0.6**: Mais permissivo, mais resultados
- **0.7-0.8**: Balanceado (recomendado)
- **0.8-0.9**: Apenas resultados muito relevantes

### filter_categories
Limita busca a categorias específicas:
```json
["reference", "legislation", "manual"]
```

### filter_tags
Limita busca a tags específicas:
```json
["licitacao", "contrato", "etp"]
```

## Admin Interface

### RAGQuery Admin
Acessível em: `/admin/rag/ragquery/`

Funcionalidades:
- Listagem com filtros por provider e data
- Busca por texto da query
- Preview de chunks recuperados
- Visualização de resposta do LLM
- Métricas de performance

### RAGContext Admin
Acessível em: `/admin/rag/ragcontext/`

Funcionalidades:
- Listagem com contagem de documentos
- Filtros por data
- Gerenciamento de documentos vinculados
- Preview de configurações

## Permissions

### IsOwnerOrAdmin
- **Owner**: Ver e gerenciar próprios queries/contextos
- **Admin/Manager**: Ver e gerenciar todos

```python
permission_classes = [IsOwnerOrAdmin]
```

## Integração com Outros Apps

### KB (Knowledge Base)
```python
# RAG usa chunks do KB para busca
from apps.kb.models import DocumentChunk

chunks = DocumentChunk.objects.filter(
    document__category__in=filter_categories
).order_by(
    DocumentChunk.embedding.cosine_distance(query_embedding)
)[:top_k]
```

### Documents
```python
# Vincular query a um ETP
rag_query = RAGQuery.objects.create(
    user=user,
    etp=etp,
    query_text="Como justificar esta contratação?",
    ...
)

# Usar resposta RAG para preencher campo
etp.data['justificativa'] = rag_query.llm_response
etp.save()
```

### Agents
```python
# Combinar RAG com Agents
# 1. Usar RAG para buscar contexto
rag_result = execute_rag_query("requisitos técnicos de sistemas")

# 2. Usar Agent para formatar resposta
agent = AgentPrompt.objects.get(agent_type='expansao')
formatted = agent.execute({
    'texto': rag_result.llm_response,
    'formato': 'lista com exemplos'
})
```

## Dependências

- Django 5.0+
- PostgreSQL 15+ com pgvector
- djangorestframework
- drf-spectacular
- openai (embeddings e LLM)
- anthropic (LLM alternativo)

## Configuração

### settings.py

```python
# RAG Settings
RAG_DEFAULT_TOP_K = 5
RAG_DEFAULT_THRESHOLD = 0.7
RAG_MAX_TOP_K = 20

# Embedding
EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSIONS = 1536

# LLM
DEFAULT_LLM_PROVIDER = 'openai'
DEFAULT_MODEL = 'gpt-4o-mini'
```

## Próximos Passos (TODO)

- [ ] Implementar busca vetorial real com pgvector
- [ ] Implementar geração de embeddings via OpenAI
- [ ] Criar chamadas reais para LLMs (OpenAI/Anthropic)
- [ ] Adicionar cache de queries idênticas
- [ ] Implementar reranking de resultados
- [ ] Adicionar suporte a conversações multi-turn
- [ ] Criar visualização de chunks no frontend
- [ ] Implementar feedback de usuários sobre qualidade
- [ ] Adicionar métricas de custo por query
- [ ] Criar análise de queries mais comuns
- [ ] Implementar rate limiting por usuário

## Prompt Engineering para RAG

### System Prompt Recomendado

```
Você é um assistente especializado em licitações públicas e documentação técnica.
Responda com base EXCLUSIVAMENTE nas informações fornecidas no contexto.
Se a informação não estiver no contexto, diga que não encontrou.
Seja preciso, cite as fontes quando relevante, e use linguagem formal.
```

### Formatação de Contexto

```
Contexto recuperado da base de conhecimento:

---
Documento: Lei 14.133/2021, Página 12
Similaridade: 0.89

Art. 24. É dispensável a licitação quando...
---

Documento: Manual de Licitações, Página 23
Similaridade: 0.85

Para dispensa de licitação, deve-se...
---

Pergunta do usuário: {query_text}

Responda com base no contexto acima.
```

## Métricas e Performance

### Tempo Médio de Execução

- **Busca semântica**: 100-500ms
- **Chamada LLM**: 1000-3000ms
- **Total**: 1100-3500ms

### Custo Estimado por Query

**OpenAI (gpt-4o-mini)**
- Embedding (query): ~$0.00001
- LLM (500 tokens context + 200 output): ~$0.0003
- **Total: ~$0.00031**

**Anthropic (claude-3-5-haiku)**
- Embedding via OpenAI: ~$0.00001
- LLM (500 tokens context + 200 output): ~$0.0015
- **Total: ~$0.00151**

## Casos de Uso

### 1. Assistente de Preenchimento de ETP
```
Query: "Como justificar contratação emergencial?"
Context: Documentos sobre legislação de licitações
Output: Texto formatado para campo "justificativa"
```

### 2. Consultor de Legislação
```
Query: "Qual o prazo mínimo de vigência de contratos?"
Context: Lei 14.133/2021 e normas relacionadas
Output: Resposta citando artigos específicos
```

### 3. Gerador de Exemplos
```
Query: "Exemplos de requisitos técnicos para sistema web"
Context: Documents anteriores + templates
Output: Lista de requisitos aplicáveis
```

### 4. Validador de Conteúdo
```
Query: "Este texto de justificativa está adequado?"
Context: Manuais de boas práticas + exemplos aprovados
Output: Análise crítica com sugestões
```

## Relacionamentos

Este app utiliza:
- **accounts**: RAGQuery.user, RAGContext.user (autoria)
- **Documents**: RAGQuery.etp, RAGContext.etp (vinculação)
- **kb**: RAGContext.documents (documentos para busca)

Este app é utilizado por:
- **Documents**: Para enriquecer conteúdo durante criação
- **agents**: Agents podem usar RAG para contexto adicional
