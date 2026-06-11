# App: KB (Knowledge Base)

## Descrição

App responsável por gerenciar a base de conhecimento do sistema BravoDoc. Permite upload de documentos (PDF, DOCX, TXT), extração de texto, chunking (divisão em fragmentos), geração de embeddings vetoriais e busca semântica usando PostgreSQL com extensão pgvector.

## Funcionalidades

### 1. Gerenciamento de Documentos
- Upload de múltiplos formatos (PDF, DOCX, TXT)
- Extração automática de texto
- Categorização e tagueamento
- Versionamento de documentos

### 2. Processamento de Documentos
- Extração de texto de PDFs e DOCX
- Divisão em chunks (fragmentos) para processamento
- Geração de embeddings vetoriais (1536 dimensões - OpenAI)
- Armazenamento em PostgreSQL com pgvector

### 3. Busca Semântica
- Busca por similaridade vetorial usando pgvector
- Filtros por categoria, tags e data
- Ranking por relevância

### 4. Integração com RAG
- Fornece contexto para agentes de IA
- Busca de informações relevantes para geração de conteúdo

## Estrutura de Arquivos

```
apps/kb/
├── __init__.py
├── admin.py           # Interface admin com processamento
├── apps.py            # Configuração do app
├── migrations/
│   ├── 0001_enable_pgvector.py    # Habilita extensão pgvector
│   └── 0002_initial.py            # Cria models
├── models.py          # Models Document e DocumentChunk
├── permissions.py     # Permissões de acesso
├── serializers.py     # Serializers incluindo busca
├── urls.py            # Rotas do app
└── views.py           # ViewSets com actions de processamento
```

## Models

### Document
```python
class Document(models.Model):
    title = CharField(max_length=500)
    file = FileField(upload_to='kb/documents/')
    category = CharField(choices=CATEGORY_CHOICES)
    tags = JSONField(default=list)
    extracted_text = TextField(blank=True)
    status = CharField(choices=STATUS_CHOICES)
    uploaded_by = ForeignKey(User)
    file_size = BigIntegerField()
    file_type = CharField(max_length=50)
```

### DocumentChunk
```python
class DocumentChunk(models.Model):
    document = ForeignKey(Document)
    content = TextField()
    embedding = VectorField(dimensions=1536)  # pgvector
    chunk_index = IntegerField()
    metadata = JSONField(default=dict)
```

## Extensão pgvector

### Configuração

O app requer a extensão pgvector habilitada no PostgreSQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Isso é feito automaticamente pela migration `0001_enable_pgvector.py`.

### Verificar Instalação

```bash
# No PostgreSQL
\dx vector

# Deve mostrar:
# vector | 0.x.x | public | vector data type and ivfflat access method
```

## API Endpoints

Base URL: `/api/v1/kb/`

### CRUD de Documentos

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/v1/kb/` | Listar documentos | Autenticado |
| GET | `/api/v1/kb/{id}/` | Detalhes do documento | Autenticado |
| POST | `/api/v1/kb/` | Upload de documento | Autenticado |
| PUT/PATCH | `/api/v1/kb/{id}/` | Atualizar documento | Owner/Admin |
| DELETE | `/api/v1/kb/{id}/` | Deletar documento | Owner/Admin |

### Endpoints de Processamento

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/kb/{id}/process/` | Processar documento (extrair texto e gerar embeddings) |
| GET | `/api/v1/kb/{id}/chunks/` | Listar chunks do documento |
| POST | `/api/v1/kb/search/` | Busca semântica na base de conhecimento |

### Filtros

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `category` | Filtrar por categoria | `?category=etp` |
| `tags` | Filtrar por tags | `?tags=licitacao,contrato` |
| `status` | Filtrar por status | `?status=processed` |

## Exemplos de Uso

### 1. Upload de Documento

```bash
POST /api/v1/kb/
Authorization: Bearer {token}
Content-Type: multipart/form-data

title: Manual de Licitações 2024
file: [arquivo.pdf]
category: reference
tags: ["licitacao", "manual", "2024"]
description: Manual completo de licitações
```

### 2. Processar Documento

```bash
POST /api/v1/kb/{document_id}/process/
Authorization: Bearer {token}

Response:
{
  "detail": "Processamento iniciado",
  "status": "processing"
}
```

**Processamento inclui:**
1. Extração de texto do PDF/DOCX
2. Divisão em chunks de ~500 tokens
3. Geração de embeddings para cada chunk
4. Armazenamento no banco com pgvector

### 3. Buscar na Base de Conhecimento

```bash
POST /api/v1/kb/search/
Authorization: Bearer {token}
Content-Type: application/json

{
  "query": "Quais são os requisitos para licitação?",
  "top_k": 5,
  "category": "reference",
  "tags": ["licitacao"]
}

Response:
{
  "results": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_title": "Manual de Licitações",
      "content": "Os requisitos para licitação são...",
      "similarity_score": 0.89,
      "chunk_index": 5
    },
    ...
  ],
  "count": 5
}
```

### 4. Listar Chunks de um Documento

```bash
GET /api/v1/kb/{document_id}/chunks/
Authorization: Bearer {token}

Response:
[
  {
    "id": "uuid",
    "chunk_index": 0,
    "content": "Texto do primeiro chunk...",
    "metadata": {
      "page": 1,
      "section": "Introdução"
    }
  },
  ...
]
```

## Categorias de Documentos

```python
CATEGORY_CHOICES = [
    ('etp', 'Documents'),
    ('reference', 'Documentos de Referência'),
    ('legislation', 'Legislação'),
    ('manual', 'Manuais'),
    ('template', 'Templates'),
    ('other', 'Outros'),
]
```

## Status de Processamento

```python
STATUS_CHOICES = [
    ('pending', 'Pendente'),
    ('processing', 'Processando'),
    ('processed', 'Processado'),
    ('error', 'Erro'),
]
```

## Fluxo de Processamento

```
1. Upload do documento → status = 'pending'
2. Extração de texto → extracted_text preenchido
3. Chunking → Divisão em fragmentos de ~500 tokens
4. Embeddings → Geração de vetores 1536D via OpenAI
5. Armazenamento → Chunks salvos com embeddings
6. Finalização → status = 'processed'
```

## Busca Semântica (pgvector)

### Como Funciona

1. **Query do usuário**: "Quais são os requisitos para licitação?"
2. **Gerar embedding**: Converte query em vetor 1536D
3. **Busca por similaridade**: Usa pgvector para encontrar chunks similares
4. **Ranking**: Ordena por score de similaridade (cosine distance)
5. **Retorno**: Top K chunks mais relevantes

### Exemplo de Query SQL (pgvector)

```sql
SELECT
    dc.id,
    dc.content,
    dc.embedding <=> '[0.123, 0.456, ...]' AS distance
FROM kb_documentchunk dc
JOIN kb_document d ON dc.document_id = d.id
WHERE d.category = 'reference'
ORDER BY distance ASC
LIMIT 5;
```

### Operadores pgvector

| Operador | Descrição | Uso |
|----------|-----------|-----|
| `<->` | Euclidean distance | Distância L2 |
| `<#>` | Inner product | Produto interno |
| `<=>` | Cosine distance | Distância de cosseno (mais comum) |

## Admin Interface

Acessível em: `/admin/kb/document/`

### Funcionalidades:
- Listagem com filtros por categoria, status e data
- Busca por título e texto extraído
- Display de status com cores
- Preview de texto extraído
- Botão de processamento manual
- Contagem de chunks por documento
- Visualização de tags

## Permissions

### IsOwnerOrAdmin
Permite:
- **Owner**: Ver e editar próprios documentos
- **Admin/Manager**: Ver e editar todos documentos

```python
permission_classes = [IsOwnerOrAdmin]
```

## Dependências

- Django 5.0+
- PostgreSQL 15+ com extensão pgvector
- djangorestframework
- drf-spectacular
- pgvector-python
- PyPDF2 ou pdfplumber (extração de PDF)
- python-docx (extração de DOCX)
- openai ou anthropic (geração de embeddings)

## Configuração

### settings.py

```python
# Database com pgvector
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bravodoc',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

# OpenAI para embeddings
OPENAI_API_KEY = env('OPENAI_API_KEY')
EMBEDDING_MODEL = 'text-embedding-3-small'  # 1536 dimensions
EMBEDDING_DIMENSIONS = 1536
```

### Habilitar pgvector

```bash
# No container PostgreSQL
docker exec -it postgres_container psql -U postgres -d bravodoc

# SQL
CREATE EXTENSION IF NOT EXISTS vector;

# Verificar
\dx vector
```

## Próximos Passos (TODO)

- [ ] Implementar extração de texto de PDFs
- [ ] Implementar extração de texto de DOCX
- [ ] Adicionar chunking inteligente (por parágrafos/seções)
- [ ] Implementar geração de embeddings via OpenAI
- [ ] Criar índice IVFFLAT no pgvector para performance
- [ ] Adicionar processamento assíncrono com Celery
- [ ] Implementar OCR para PDFs escaneados
- [ ] Adicionar suporte a mais formatos (RTF, ODT, etc)
- [ ] Criar cache de embeddings para queries comuns
- [ ] Implementar reprocessamento de documentos

## Integração com Outros Apps

### RAG
```python
# RAG usa KB para buscar contexto
from apps.kb.models import DocumentChunk

chunks = DocumentChunk.objects.filter(
    document__category='etp'
).order_by(
    DocumentChunk.embedding.cosine_distance(query_embedding)
)[:5]
```

### Agents
```python
# Agentes usam KB para contexto adicional
if agent_prompt.use_rag:
    context_chunks = search_kb(query)
    prompt = f"Contexto: {context_chunks}\n\nQuery: {query}"
```

## Chunking Strategy

### Tamanho de Chunks

- **Pequenos (100-200 tokens)**: Maior precisão, menos contexto
- **Médios (300-500 tokens)**: Balanço entre precisão e contexto
- **Grandes (800-1000 tokens)**: Mais contexto, menos precisão

**Recomendação**: 400-500 tokens por chunk

### Overlap

Chunks podem ter overlap para manter contexto:

```python
chunk_size = 500
overlap = 50  # 10% de overlap

chunks = [
    text[0:500],
    text[450:950],    # overlap de 50 tokens
    text[900:1400],
    ...
]
```

## Exemplos de Metadata de Chunks

```json
{
  "page": 5,
  "section": "2. Justificativa",
  "paragraph": 3,
  "document_date": "2024-01-15",
  "author": "João Silva",
  "confidence": 0.95
}
```

## Performance

### Índices pgvector

Para melhor performance em buscas:

```sql
-- Criar índice IVFFLAT (recomendado para +100k vetores)
CREATE INDEX ON kb_documentchunk
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Criar índice HNSW (melhor performance, PostgreSQL 16+)
CREATE INDEX ON kb_documentchunk
USING hnsw (embedding vector_cosine_ops);
```

### Tamanho Estimado

- **1 documento PDF (50 páginas)**: ~10-20 chunks
- **1 chunk**: ~500 tokens + 1536 float32 = ~6KB
- **1000 documentos**: ~200K chunks = ~1.2GB de embeddings

## Relacionamentos

Este app é utilizado por:
- **rag**: RAGContext.documents (documentos em contextos RAG)
- **agents**: AgentPrompt.use_rag (busca contexto no KB)
