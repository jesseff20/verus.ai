# App: Templates

## Descrição

App responsável por gerenciar templates de documentos do sistema BravoDoc. Permite criar templates HTML ou DOCX com placeholders que serão substituídos por dados dos formulários preenchidos, gerando documentos finais formatados.

## Funcionalidades

### 1. Templates de Documentos
- Templates HTML com suporte a CSS customizado
- Templates DOCX para geração de documentos Word
- Sistema de placeholders para substituição de dados
- Extração automática de placeholders do template
- Preview de documentos com dados de teste

### 2. Tipos de Template
- **HTML**: Para visualização web e exportação PDF
- **DOCX**: Para geração de arquivos Microsoft Word

### 3. Integração com Formulários
- Vinculação com FormTemplate para validação de placeholders
- Mapeamento automático de campos do formulário para placeholders

## Estrutura de Arquivos

```
apps/templates/
├── __init__.py
├── admin.py           # Interface admin com preview
├── apps.py            # Configuração do app
├── migrations/        # Migrações do banco
├── models.py          # Model DocumentTemplate
├── permissions.py     # Permissões de acesso
├── serializers.py     # Serializers incluindo preview
├── urls.py            # Rotas do app
└── views.py           # ViewSets com actions de preview
```

## Models

### DocumentTemplate
```python
class DocumentTemplate(models.Model):
    name = CharField(max_length=255)
    description = TextField(blank=True)
    content = TextField(blank=True)              # Template HTML
    file = FileField(upload_to='templates/')     # Template DOCX
    custom_css = TextField(blank=True)           # CSS customizado
    form_template = ForeignKey(FormTemplate)     # Formulário vinculado
    version = IntegerField(default=1)
    status = CharField(choices=STATUS_CHOICES)
    created_by = ForeignKey(User)
```

## Sistema de Placeholders

### Sintaxe

Placeholders são marcadores no template que serão substituídos por dados:

```
{{field_id}}
```

Onde `field_id` é o ID de um campo do FormTemplate vinculado.

### Exemplo de Template HTML

```html
<!DOCTYPE html>
<html>
<head>
    <title>Estudo Técnico Preliminar</title>
</head>
<body>
    <h1>ESTUDO TÉCNICO PRELIMINAR</h1>

    <h2>1. OBJETO</h2>
    <p>{{objeto}}</p>

    <h2>2. JUSTIFICATIVA</h2>
    <p>{{justificativa}}</p>

    <h2>3. VALOR ESTIMADO</h2>
    <p>R$ {{valor_estimado}}</p>

    <h2>4. PRAZO DE EXECUÇÃO</h2>
    <p>{{prazo_execucao}} dias</p>
</body>
</html>
```

### Exemplo de CSS Customizado

```css
body {
    font-family: 'Times New Roman', serif;
    font-size: 12pt;
    line-height: 1.5;
    margin: 2cm;
}

h1 {
    text-align: center;
    font-size: 16pt;
    font-weight: bold;
}

h2 {
    font-size: 14pt;
    margin-top: 20px;
}
```

## API Endpoints

Base URL: `/api/v1/templates/`

### CRUD Básico

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/v1/templates/` | Listar templates | Admin/Manager |
| GET | `/api/v1/templates/{id}/` | Detalhes do template | Admin/Manager |
| POST | `/api/v1/templates/` | Criar template | Admin/Manager |
| PUT/PATCH | `/api/v1/templates/{id}/` | Atualizar template | Admin/Manager |
| DELETE | `/api/v1/templates/{id}/` | Deletar template | Admin/Manager |

### Endpoints Especiais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/templates/{id}/placeholders/` | Extrair placeholders do template |
| POST | `/api/v1/templates/{id}/preview/` | Preview com dados de teste |
| POST | `/api/v1/templates/{id}/clone/` | Clonar template |

### Filtros

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `status` | Filtrar por status | `?status=active` |
| `form_template` | Filtrar por formulário | `?form_template={uuid}` |

## Exemplos de Uso

### 1. Criar Template HTML

```bash
POST /api/v1/templates/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Template ETP Padrão",
  "description": "Template padrão para Estudo Técnico Preliminar",
  "form_template": "uuid-do-form-template",
  "content": "<!DOCTYPE html><html>...",
  "custom_css": "body { font-family: Arial; }",
  "status": "draft"
}
```

### 2. Upload de Template DOCX

```bash
POST /api/v1/templates/
Authorization: Bearer {token}
Content-Type: multipart/form-data

name: Template ETP DOCX
description: Template Word para ETP
form_template: uuid-do-form-template
file: [arquivo.docx]
status: draft
```

### 3. Extrair Placeholders

```bash
GET /api/v1/templates/{template_id}/placeholders/
Authorization: Bearer {token}

Response:
{
  "placeholders": [
    "objeto",
    "justificativa",
    "valor_estimado",
    "prazo_execucao"
  ],
  "count": 4
}
```

### 4. Preview com Dados de Teste

```bash
POST /api/v1/templates/{template_id}/preview/
Authorization: Bearer {token}
Content-Type: application/json

{
  "data": {
    "objeto": "Contratação de sistema de gestão",
    "justificativa": "Necessário para modernização...",
    "valor_estimado": "50.000,00",
    "prazo_execucao": "180"
  }
}

Response:
{
  "rendered_content": "<!DOCTYPE html><html>...conteúdo renderizado..."
}
```

### 5. Clonar Template

```bash
POST /api/v1/templates/{template_id}/clone/
Authorization: Bearer {token}

Response:
{
  "id": "novo-uuid",
  "name": "Template ETP Padrão (Cópia)",
  ...
}
```

## Métodos do Model

### extract_placeholders()
Extrai todos os placeholders `{{field_id}}` do template:

```python
template = DocumentTemplate.objects.get(id=template_id)
placeholders = template.extract_placeholders()
# ['objeto', 'justificativa', 'valor_estimado']
```

### get_template_content()
Retorna o conteúdo do template (HTML ou texto extraído do DOCX):

```python
content = template.get_template_content()
```

### render(data)
Renderiza o template substituindo placeholders por dados (TODO):

```python
rendered = template.render({
    'objeto': 'Contratação de...',
    'justificativa': 'Necessário para...'
})
```

## Admin Interface

Acessível em: `/admin/templates/documenttemplate/`

### Funcionalidades:
- Listagem com filtros por status e formulário vinculado
- Busca por nome e descrição
- Display de status com cores
- Preview de conteúdo HTML
- Link para download de arquivo DOCX
- Contagem de placeholders

## Permissions

### CanManageTemplates
Permite acesso apenas para:
- `superadmin`
- `admin`
- `manager`

```python
permission_classes = [CanManageTemplates]
```

## Status de Templates

```python
STATUS_CHOICES = [
    ('draft', 'Rascunho'),
    ('active', 'Ativo'),
    ('archived', 'Arquivado'),
]
```

## Fluxo de Trabalho Típico

### 1. Criação de Template

```
1. Admin/Manager cria FormTemplate primeiro
2. Cria DocumentTemplate vinculado ao FormTemplate
3. Define conteúdo HTML com placeholders {{field_id}}
4. Adiciona CSS customizado (opcional)
5. Usa /placeholders/ para verificar placeholders extraídos
6. Testa com /preview/ usando dados de exemplo
7. Ativa template (status = 'active')
```

### 2. Geração de Documento

```
1. Usuário preenche formulário (ETP.data)
2. Sistema carrega DocumentTemplate vinculado
3. Substitui placeholders pelos dados do formulário
4. Gera HTML final (ETP.generated_html)
5. Opcionalmente exporta para PDF/DOCX (ETP.exported_file)
```

## Validação de Placeholders

O sistema valida que os placeholders no template correspondem aos campos do FormTemplate:

```python
# Placeholders no template
template_placeholders = ['objeto', 'valor', 'prazo']

# Campos no formulário
form_fields = ['objeto', 'justificativa', 'valor']

# Placeholders não encontrados no formulário
missing = ['prazo']  # Aviso: placeholder sem campo correspondente
```

## Integração com Outros Apps

### Forms
```python
# Template vinculado a um formulário
template = DocumentTemplate.objects.create(
    name="Template ETP",
    form_template=form_template,
    content="<h1>{{titulo}}</h1>"
)
```

### Documents
```python
# ETP usa template para gerar documento
etp = ETP.objects.create(
    form_template=form_template,
    document_template=document_template,
    data={'objeto': 'Contratação...'}
)
```

## Dependências

- Django 5.0+
- djangorestframework
- drf-spectacular
- python-docx (para processamento de DOCX)

## Próximos Passos (TODO)

- [ ] Implementar extração de texto de DOCX
- [ ] Adicionar suporte a placeholders condicionais
- [ ] Implementar placeholders com formatação (ex: {{valor|currency}})
- [ ] Criar editor WYSIWYG para templates HTML
- [ ] Adicionar suporte a imagens e logos nos templates
- [ ] Implementar geração de PDF a partir do HTML
- [ ] Adicionar suporte a headers e footers customizados
- [ ] Criar biblioteca de templates prontos

## Exemplos de Templates Completos

### Template ETP Básico

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Estudo Técnico Preliminar</title>
    <style>
        body {
            font-family: 'Times New Roman', serif;
            font-size: 12pt;
            margin: 2cm;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            margin: 20px 0;
        }
        .section-title {
            font-weight: bold;
            font-size: 14pt;
            margin: 15px 0 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>ESTUDO TÉCNICO PRELIMINAR</h1>
        <p>Processo n° {{numero_processo}}</p>
    </div>

    <div class="section">
        <div class="section-title">1. OBJETO</div>
        <p>{{objeto}}</p>
    </div>

    <div class="section">
        <div class="section-title">2. JUSTIFICATIVA DA CONTRATAÇÃO</div>
        <p>{{justificativa}}</p>
    </div>

    <div class="section">
        <div class="section-title">3. DESCRIÇÃO DA SOLUÇÃO</div>
        <p>{{descricao_solucao}}</p>
    </div>

    <div class="section">
        <div class="section-title">4. ESTIMATIVA DE VALORES</div>
        <p>Valor estimado: R$ {{valor_estimado}}</p>
    </div>

    <div class="section">
        <div class="section-title">5. PRAZO DE EXECUÇÃO</div>
        <p>{{prazo_execucao}} dias corridos</p>
    </div>

    <div class="footer">
        <p>{{cidade}}, {{data_elaboracao}}</p>
        <br><br>
        <p>_________________________________</p>
        <p>{{nome_responsavel}}</p>
        <p>{{cargo_responsavel}}</p>
    </div>
</body>
</html>
```

## Relacionamentos

Este app é utilizado por:
- **forms**: DocumentTemplate.form_template (vinculação)
- **Documents**: ETP.document_template (template usado para gerar documento)
