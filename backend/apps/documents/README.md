# App: Documents

## Descrição

App central do sistema BravoDoc, responsável por gerenciar os Estudos Técnicos Preliminares (Documents). Integra todos os outros apps (forms, templates, agents, kb, rag) para criar um fluxo completo de criação, edição, revisão e geração de documentos Documents.

## Funcionalidades

### 1. Gestão de Documents
- Criação de Documents baseados em templates de formulários
- Preenchimento de dados estruturados (JSON)
- Edição colaborativa com controle de status
- Versionamento para histórico de alterações
- Geração de documentos finais (HTML/PDF/DOCX)

### 2. Sistema de Status
- **Draft (Rascunho)**: ETP em edição
- **In Review (Em Revisão)**: Aguardando aprovação
- **Completed (Completo)**: Finalizado e aprovado
- **Archived (Arquivado)**: Arquivado para referência

### 3. Versionamento
- Criação de novas versões preservando histórico
- Rastreamento de versão pai (parent)
- Numeração automática de versões

### 4. Geração de Documentos
- Renderização de templates com dados do formulário
- Suporte a múltiplos formatos (HTML, PDF, DOCX)
- Armazenamento de conteúdo gerado e arquivo exportado

## Estrutura de Arquivos

```
apps/Documents/
├── __init__.py
├── admin.py           # Interface admin com status coloridos
├── apps.py            # Configuração do app
├── migrations/        # Migrações do banco
├── models.py          # Model ETP
├── permissions.py     # Permissões de acesso
├── serializers.py     # Serializers (List, Detail, Create, Update)
├── urls.py            # Rotas do app
└── views.py           # ViewSets com actions especiais
```

## Models

### ETP
```python
class ETP(models.Model):
    # Relações
    user = ForeignKey(User)
    form_template = ForeignKey(FormTemplate)
    document_template = ForeignKey(DocumentTemplate, null=True)

    # Dados do formulário preenchido
    data = JSONField(default=dict)

    # Documento gerado
    generated_content = TextField(blank=True)
    generated_html = TextField(blank=True)
    exported_file = FileField(upload_to='Documents/exports/')

    # Status e metadata
    status = CharField(choices=STATUS_CHOICES, default='draft')
    title = CharField(max_length=500, blank=True)
    description = TextField(blank=True)

    # Versionamento
    version = IntegerField(default=1)
    parent = ForeignKey('self', null=True)

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    completed_at = DateTimeField(null=True, blank=True)
```

## API Endpoints

Base URL: `/api/v1/Documents/`

### CRUD Básico

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/v1/Documents/` | Listar Documents | Owner/Admin |
| GET | `/api/v1/Documents/{id}/` | Detalhes do ETP | Owner/Admin |
| POST | `/api/v1/Documents/` | Criar ETP | Autenticado |
| PUT/PATCH | `/api/v1/Documents/{id}/` | Atualizar ETP | Owner/Admin |
| DELETE | `/api/v1/Documents/{id}/` | Deletar ETP | Owner/Admin |

### Endpoints Especiais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/Documents/{id}/create_version/` | Criar nova versão |
| POST | `/api/v1/Documents/{id}/complete/` | Marcar como completo |
| POST | `/api/v1/Documents/{id}/generate/` | Gerar documento final |

### Filtros

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `status` | Filtrar por status | `?status=draft` |

## Exemplos de Uso

### 1. Criar Novo ETP

```bash
POST /api/v1/Documents/
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "ETP - Contratação de Sistema de Gestão",
  "description": "Estudo para contratação de sistema integrado",
  "form_template": "uuid-do-form-template",
  "document_template": "uuid-do-doc-template",
  "data": {
    "objeto": "Contratação de empresa especializada...",
    "justificativa": "A contratação se justifica pela necessidade...",
    "valor_estimado": "150000.00",
    "prazo_execucao": "180"
  }
}
```

### 2. Atualizar Dados do ETP

```bash
PATCH /api/v1/Documents/{etp_id}/
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "ETP - Contratação de Sistema de Gestão (Atualizado)",
  "data": {
    "objeto": "Contratação de empresa especializada... (texto atualizado)",
    "justificativa": "Nova justificativa...",
    "valor_estimado": "175000.00",
    "prazo_execucao": "240"
  }
}
```

### 3. Criar Nova Versão

```bash
POST /api/v1/Documents/{etp_id}/create_version/
Authorization: Bearer {token}

Response:
{
  "id": "novo-uuid",
  "title": "ETP - Contratação de Sistema de Gestão",
  "version": 2,
  "parent": "uuid-etp-original",
  "status": "draft",
  "data": { ... },  // Cópia dos dados da versão anterior
  "created_at": "2024-10-09T10:30:00Z"
}
```

### 4. Marcar como Completo

```bash
POST /api/v1/Documents/{etp_id}/complete/
Authorization: Bearer {token}

Response:
{
  "id": "uuid",
  "status": "completed",
  "completed_at": "2024-10-09T10:35:00Z",
  ...
}
```

### 5. Gerar Documento Final

```bash
POST /api/v1/Documents/{etp_id}/generate/
Authorization: Bearer {token}

Response:
{
  "detail": "Geração de documento será implementada",
  "etp_id": "uuid"
}

# TODO: Implementar geração real que:
# 1. Carrega document_template
# 2. Substitui placeholders pelos dados de ETP.data
# 3. Salva em generated_html
# 4. Opcionalmente exporta para PDF/DOCX em exported_file
```

### 6. Listar Documents com Filtros

```bash
# Listar apenas rascunhos
GET /api/v1/Documents/?status=draft
Authorization: Bearer {token}

# Listar Documents completos
GET /api/v1/Documents/?status=completed
Authorization: Bearer {token}
```

## Estrutura de Dados (JSON)

O campo `data` armazena os valores preenchidos no formulário:

```json
{
  "numero_processo": "2024/001-SG",
  "objeto": "Contratação de empresa especializada para desenvolvimento...",
  "justificativa": "A contratação se justifica pela necessidade de modernizar...",
  "descricao_solucao": "A solução proposta consiste em...",
  "valor_estimado": "150000.00",
  "prazo_execucao": "180",
  "requisitos_tecnicos": [
    "Sistema web responsivo",
    "Banco de dados PostgreSQL",
    "API RESTful"
  ],
  "criterios_sustentabilidade": "O sistema deve seguir...",
  "analise_riscos": "Principais riscos identificados..."
}
```

## Status do ETP

```python
STATUS_CHOICES = [
    ('draft', 'Rascunho'),
    ('in_review', 'Em Revisão'),
    ('completed', 'Completo'),
    ('archived', 'Arquivado'),
]
```

### Transições de Status

```
draft → in_review → completed → archived
  ↑         ↓
  └─────────┘ (pode voltar para draft)
```

## Versionamento

### Como Funciona

1. **ETP Original** (v1):
   - `version = 1`
   - `parent = null`

2. **Criar Nova Versão**:
   - Copia dados do original
   - `version = 2`
   - `parent = ETP Original`
   - `status = 'draft'`

3. **Versões Subsequentes**:
   - Sempre referenciam o pai original
   - Numeração incremental

### Exemplo

```python
etp_v1 = ETP.objects.create(
    title="ETP Sistema",
    version=1,
    parent=None
)

# Criar v2
etp_v2 = etp_v1.create_version(user)
# etp_v2.version = 2
# etp_v2.parent = etp_v1

# Criar v3
etp_v3 = etp_v2.create_version(user)
# etp_v3.version = 3
# etp_v3.parent = etp_v1  (sempre referencia o original)
```

## Properties do Model

### is_draft
```python
if etp.is_draft:
    # Permite edição
    pass
```

### is_completed
```python
if etp.is_completed:
    # Bloqueia edição
    # Disponibiliza para exportação
    pass
```

## Admin Interface

Acessível em: `/admin/Documents/etp/`

### Funcionalidades:
- Listagem com filtros por status e template
- Busca por título, descrição e username
- Display de status com badges coloridos
- Preview de dados do formulário
- Preview de conteúdo gerado
- Link para download de arquivo exportado
- Informações de versionamento

## Permissions

### IsOwnerOrAdmin
Permite acesso:
- **Owner**: Ver e editar próprios Documents
- **Admin/Manager**: Ver e editar todos Documents

```python
permission_classes = [IsOwnerOrAdmin]
```

## Fluxo Completo de Criação de ETP

### 1. Preparação
```
1. Admin cria FormTemplate (ex: "Formulário ETP Padrão")
2. Admin cria DocumentTemplate (ex: "Template ETP HTML")
3. Admin vincula DocumentTemplate ao FormTemplate
```

### 2. Criação do ETP
```
1. Usuário acessa interface de novo ETP
2. Seleciona FormTemplate
3. Frontend renderiza campos dinamicamente
4. Usuário preenche formulário
5. POST /api/v1/Documents/ com dados
```

### 3. Edição e Colaboração
```
1. Usuário edita campos via PATCH /api/v1/Documents/{id}/
2. Pode usar agentes de IA para:
   - Corrigir textos (agent: corretor)
   - Gerar exemplos (agent: exemplo)
   - Expandir seções (agent: expansao)
3. Usa RAG para buscar informações na base de conhecimento
```

### 4. Revisão
```
1. Usuário marca como "in_review"
2. Gestor/Admin revisa conteúdo
3. Aprova ou solicita alterações
```

### 5. Finalização
```
1. POST /api/v1/Documents/{id}/complete/
2. Status → "completed"
3. completed_at preenchido
```

### 6. Geração de Documento
```
1. POST /api/v1/Documents/{id}/generate/
2. Sistema carrega document_template
3. Substitui {{placeholders}} pelos dados de ETP.data
4. Salva em generated_html
5. Exporta para PDF/DOCX → exported_file
```

## Integração com Outros Apps

### Forms
```python
# ETP usa template de formulário
etp = ETP.objects.create(
    form_template=FormTemplate.objects.get(name="ETP Padrão"),
    data={...}
)

# Dados devem corresponder aos campos do FormTemplate
form_fields = etp.form_template.fields
# Validar que data contém todos campos required
```

### Templates
```python
# ETP usa template de documento
etp.document_template = DocumentTemplate.objects.get(name="Template ETP HTML")

# Geração de documento
content = etp.document_template.get_template_content()
for key, value in etp.data.items():
    content = content.replace(f'{{{{{key}}}}}', str(value))
etp.generated_html = content
etp.save()
```

### Agents
```python
# Usar agente para melhorar justificativa
from apps.agents.models import AgentPrompt

corretor = AgentPrompt.objects.get(agent_type='corretor')
resultado = corretor.execute({
    'texto': etp.data['justificativa'],
    'tom': 'formal'
})
etp.data['justificativa'] = resultado['response']
etp.save()
```

### RAG
```python
# Buscar informações para enriquecer conteúdo
from apps.rag.services import search_kb

contexto = search_kb(
    query="requisitos para licitação de sistemas",
    top_k=5
)

# Usar contexto para preencher campos
etp.data['referencias_legais'] = contexto
```

## Serializers

### ETPListSerializer
Usado em listagens, campos resumidos:
- id, title, description, user_name, form_template_name
- status, version, created_at, updated_at

### ETPDetailSerializer
Usado em detalhes, todos os campos:
- Todos os campos do model
- Campos read_only: id, user, created_at, updated_at, completed_at

### ETPCreateSerializer
Usado na criação:
- Campos: title, description, form_template, document_template, data
- Seta user automaticamente pelo request.user

### ETPUpdateSerializer
Usado na atualização:
- Campos: title, description, data, generated_content, generated_html, status

## Dependências

- Django 5.0+
- djangorestframework
- drf-spectacular
- Todos os outros apps do BravoDoc (forms, templates, agents, kb, rag)

## Próximos Passos (TODO)

- [ ] Implementar geração real de documentos (action generate)
- [ ] Adicionar exportação para PDF usando WeasyPrint ou similar
- [ ] Adicionar exportação para DOCX usando python-docx
- [ ] Implementar validação de dados contra FormTemplate
- [ ] Criar preview em tempo real do documento
- [ ] Adicionar comentários e anotações
- [ ] Implementar workflow de aprovação com múltiplos níveis
- [ ] Adicionar histórico de alterações (audit log)
- [ ] Implementar assinatura digital de documentos
- [ ] Criar dashboard com métricas de Documents
- [ ] Adicionar notificações por email em mudanças de status

## Validação de Dados

### Validar Campos Required

```python
def validate_etp_data(etp):
    form_template = etp.form_template
    required_fields = [
        field['id']
        for field in form_template.fields
        if field.get('required', False)
    ]

    missing_fields = [
        field_id
        for field_id in required_fields
        if field_id not in etp.data or not etp.data[field_id]
    ]

    if missing_fields:
        raise ValidationError(f"Campos obrigatórios faltando: {missing_fields}")
```

## Exportação de Documentos

### HTML → PDF (TODO)

```python
from weasyprint import HTML

def export_to_pdf(etp):
    html_content = etp.generated_html
    pdf_file = HTML(string=html_content).write_pdf()

    etp.exported_file.save(
        f'etp_{etp.id}.pdf',
        ContentFile(pdf_file)
    )
    return etp.exported_file.url
```

### HTML → DOCX (TODO)

```python
from htmldocx import HtmlToDocx

def export_to_docx(etp):
    html_content = etp.generated_html

    parser = HtmlToDocx()
    docx = parser.parse_html_string(html_content)

    docx_path = f'etp_{etp.id}.docx'
    docx.save(docx_path)

    with open(docx_path, 'rb') as f:
        etp.exported_file.save(docx_path, File(f))

    return etp.exported_file.url
```

## Relacionamentos

Este app utiliza:
- **accounts**: ETP.user (autor)
- **forms**: ETP.form_template (estrutura do formulário)
- **templates**: ETP.document_template (template para documento final)
- **agents**: Para melhorar conteúdo durante edição
- **rag**: Para buscar contexto e informações adicionais

Este app é utilizado por:
- **rag**: RAGQuery.etp, RAGContext.etp (queries relacionadas a ETP)
