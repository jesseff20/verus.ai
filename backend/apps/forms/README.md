# App: Forms

## Descrição

App responsável por gerenciar templates de formulários dinâmicos do sistema BravoDoc. Permite a criação de formulários customizados através de uma interface NoCode, onde campos podem ser adicionados, editados, removidos e reordenados visualmente.

## Funcionalidades

### 1. Templates de Formulários Dinâmicos
- Criação de formulários com campos configuráveis via JSON
- Suporte a múltiplos tipos de campos
- Validação automática da estrutura JSON dos campos
- Categorização de formulários (ETP, Contratos, Pareceres, etc.)

### 2. Interface NoCode (Visual Form Builder)
- **Field Types API**: Catálogo de tipos de campos disponíveis com ícones e configurações padrão
- **Add Field**: Adicionar campos em posições específicas
- **Update Field**: Editar configuração de campos existentes
- **Delete Field**: Remover campos do formulário
- **Reorder Fields**: Reorganizar campos via drag & drop

### 3. Versionamento e Status
- Status: `draft`, `active`, `archived`
- Versionamento para histórico de alterações

## Estrutura de Arquivos

```
apps/forms/
├── __init__.py
├── admin.py           # Interface admin com preview de campos
├── apps.py            # Configuração do app
├── migrations/        # Migrações do banco
├── models.py          # Model FormTemplate com validação
├── permissions.py     # Permissões de acesso
├── serializers.py     # Serializers incluindo NoCode builders
├── urls.py            # Rotas do app
└── views.py           # ViewSets com actions NoCode
```

## Models

### FormTemplate
```python
class FormTemplate(models.Model):
    name = CharField(max_length=255)
    description = TextField(blank=True)
    category = CharField(choices=CATEGORY_CHOICES)
    fields = JSONField(validators=[validate_form_fields])
    version = IntegerField(default=1)
    status = CharField(choices=STATUS_CHOICES, default='draft')
    created_by = ForeignKey(User)
```

### Estrutura de Campos (JSON)

Cada campo no array `fields` deve ter a seguinte estrutura:

```json
{
  "id": "campo_nome_unico",
  "type": "text|textarea|number|email|date|select|checkbox|radio|file",
  "label": "Rótulo do Campo",
  "required": true,
  "placeholder": "Texto de exemplo",
  "help_text": "Texto de ajuda",
  "options": ["Opção 1", "Opção 2"],  // Para select, radio
  "validation": {
    "min": 0,
    "max": 100,
    "pattern": "regex"
  }
}
```

## Tipos de Campos Suportados

| Tipo | Descrição | Ícone | Configurações |
|------|-----------|-------|---------------|
| `text` | Texto Curto | 📝 | placeholder, maxlength, pattern |
| `textarea` | Texto Longo | 📄 | rows, placeholder, maxlength |
| `number` | Número | 🔢 | min, max, step |
| `email` | Email | 📧 | placeholder, pattern |
| `date` | Data | 📅 | min, max |
| `select` | Lista Suspensa | 📋 | options (array) |
| `checkbox` | Checkbox | ☑️ | default_value (boolean) |
| `radio` | Botão de Rádio | 🔘 | options (array) |
| `file` | Upload de Arquivo | 📎 | accept, max_size |

## API Endpoints

Base URL: `/api/v1/forms/`

### CRUD Básico

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/v1/forms/` | Listar templates | Admin/Manager |
| GET | `/api/v1/forms/{id}/` | Detalhes do template | Admin/Manager |
| POST | `/api/v1/forms/` | Criar template | Admin/Manager |
| PUT/PATCH | `/api/v1/forms/{id}/` | Atualizar template | Admin/Manager |
| DELETE | `/api/v1/forms/{id}/` | Deletar template | Admin/Manager |

### Endpoints NoCode (Visual Builder)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/forms/field-types/` | Listar tipos de campos disponíveis |
| POST | `/api/v1/forms/{id}/fields/add/` | Adicionar campo ao template |
| PUT | `/api/v1/forms/{id}/fields/{field_id}/update/` | Atualizar campo específico |
| DELETE | `/api/v1/forms/{id}/fields/{field_id}/delete/` | Remover campo |
| POST | `/api/v1/forms/{id}/fields/reorder/` | Reordenar campos (drag & drop) |

### Filtros

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `category` | Filtrar por categoria | `?category=etp` |
| `status` | Filtrar por status | `?status=active` |

## Exemplos de Uso

### 1. Obter Tipos de Campos Disponíveis

```bash
GET /api/v1/forms/field-types/
Authorization: Bearer {token}

Response:
[
  {
    "type": "text",
    "label": "Texto Curto",
    "description": "Campo de texto de linha única",
    "icon": "📝",
    "default_config": {
      "type": "text",
      "required": false,
      "placeholder": "",
      "maxlength": 255
    }
  },
  ...
]
```

### 2. Criar Template de Formulário

```bash
POST /api/v1/forms/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Formulário de ETP Básico",
  "description": "Template para Estudo Técnico Preliminar",
  "category": "etp",
  "fields": [
    {
      "id": "objeto",
      "type": "textarea",
      "label": "Objeto da Contratação",
      "required": true,
      "placeholder": "Descreva o objeto...",
      "help_text": "Descreva detalhadamente o objeto da contratação"
    },
    {
      "id": "justificativa",
      "type": "textarea",
      "label": "Justificativa",
      "required": true
    },
    {
      "id": "valor_estimado",
      "type": "number",
      "label": "Valor Estimado (R$)",
      "required": true,
      "validation": {
        "min": 0
      }
    }
  ],
  "status": "draft"
}
```

### 3. Adicionar Campo ao Template (NoCode)

```bash
POST /api/v1/forms/{template_id}/fields/add/
Authorization: Bearer {token}
Content-Type: application/json

{
  "field": {
    "id": "prazo_execucao",
    "type": "number",
    "label": "Prazo de Execução (dias)",
    "required": true,
    "validation": {
      "min": 1,
      "max": 365
    }
  },
  "position": 3  // Adiciona na posição 3 (opcional)
}
```

### 4. Reordenar Campos (Drag & Drop)

```bash
POST /api/v1/forms/{template_id}/fields/reorder/
Authorization: Bearer {token}
Content-Type: application/json

{
  "field_ids": [
    "objeto",
    "prazo_execucao",
    "valor_estimado",
    "justificativa"
  ]
}
```

### 5. Atualizar Campo Específico

```bash
PUT /api/v1/forms/{template_id}/fields/campo_id/update/
Authorization: Bearer {token}
Content-Type: application/json

{
  "label": "Novo Label",
  "required": false,
  "placeholder": "Novo placeholder"
}
```

### 6. Remover Campo

```bash
DELETE /api/v1/forms/{template_id}/fields/campo_id/delete/
Authorization: Bearer {token}
```

## Validação de Campos

O modelo implementa validação automática via `validate_form_fields`:

### Validações Aplicadas:
1. **Estrutura**: `fields` deve ser uma lista
2. **Campos obrigatórios**: Cada field deve ter `id`, `type`, `label`
3. **Tipos válidos**: Apenas tipos suportados são aceitos
4. **IDs únicos**: Não pode haver campos com mesmo `id`

### Exemplo de Erro de Validação:

```json
{
  "fields": [
    "Tipo de campo inválido: textooo"
  ]
}
```

## Admin Interface

Acessível em: `/admin/forms/formtemplate/`

### Funcionalidades:
- Listagem com filtros por categoria e status
- Busca por nome e descrição
- Display de status com cores (Draft/Active/Archived)
- Preview dos campos em formato legível
- Contagem de campos por template

## Permissions

### CanManageTemplates
Permite acesso apenas para:
- `superadmin`
- `admin`
- `manager`

```python
permission_classes = [CanManageTemplates]
```

## Categorias de Formulários

```python
CATEGORY_CHOICES = [
    ('etp', 'Estudo Técnico Preliminar'),
    ('contract', 'Contrato'),
    ('opinion', 'Parecer'),
    ('report', 'Relatório'),
    ('request', 'Solicitação'),
    ('other', 'Outro'),
]
```

## Fluxo de Trabalho Típico

### 1. Criação Visual de Formulário (NoCode)

```
1. Admin/Manager acessa interface de criação
2. Define nome, descrição e categoria
3. Usa endpoint /field-types/ para ver campos disponíveis
4. Adiciona campos um por um via /fields/add/
5. Reordena campos via drag & drop (/fields/reorder/)
6. Edita configurações via /fields/{id}/update/
7. Ativa template (status = 'active')
```

### 2. Uso do Formulário

```
1. App ETP carrega template via GET /forms/{id}/
2. Renderiza campos dinamicamente no frontend
3. Usuário preenche formulário
4. Dados são salvos em ETP.data (JSONField)
```

## Integração com Outros Apps

### Documents
```python
etp = ETP.objects.create(
    form_template=form_template,
    data={
        "objeto": "Contratação de sistema...",
        "justificativa": "Necessidade de...",
        "valor_estimado": 50000
    }
)
```

## Dependências

- Django 5.0+
- djangorestframework
- drf-spectacular

## Próximos Passos (TODO)

- [ ] Implementar preview em tempo real do formulário
- [ ] Adicionar validações customizadas por campo
- [ ] Criar biblioteca de campos pré-configurados
- [ ] Implementar importação/exportação de templates
- [ ] Adicionar campos condicionais (mostrar/ocultar baseado em valores)
- [ ] Implementar calculadora de campos (ex: campo calculado = campo1 + campo2)

## Relacionamentos

Este app é utilizado por:
- **Documents**: ETP.form_template (qual formulário usar)
- **templates**: DocumentTemplate.form_template (mapeamento campos → placeholders)
