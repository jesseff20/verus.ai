# App: Accounts

## Descrição

App responsável pelo gerenciamento de usuários e autenticação do sistema BravoDoc. Implementa um modelo de usuário customizado com sistema de permissões baseado em roles (papéis) para controle de acesso granular.

## Funcionalidades

### 1. Modelo de Usuário Customizado
- Herda de `AbstractUser` do Django
- Campos adicionais:
  - `role`: Define o papel do usuário no sistema
  - `organization`: Organização à qual o usuário pertence (preparado para multi-tenancy)
  - `phone`: Telefone de contato

### 2. Sistema de Roles (Papéis)

O sistema implementa 5 níveis hierárquicos de permissões:

| Role | Descrição | Permissões |
|------|-----------|------------|
| `superadmin` | Super Administrador | Acesso total ao sistema, gerencia todas organizações |
| `admin` | Administrador da Organização | Gerencia usuários, templates e configurações da organização |
| `manager` | Gestor | Cria e gerencia templates, aprova documentos |
| `analyst` | Analista | Cria e edita Documents, acessa templates |
| `viewer` | Visualizador | Apenas visualização de documentos |

### 3. Properties de Permissão

O modelo User possui properties que facilitam verificação de permissões:

```python
user.can_manage_users        # superadmin, admin
user.can_manage_templates     # superadmin, admin, manager
user.can_create_Documents          # superadmin, admin, manager, analyst
user.is_admin_or_higher       # superadmin, admin
```

### 4. Autenticação

- **JWT Authentication**: Tokens de acesso e refresh via `djangorestframework-simplejwt`
- **Session Authentication**: Para uso do Swagger UI (com CSRF exempt para APIs)

## Estrutura de Arquivos

```
apps/accounts/
├── __init__.py
├── admin.py           # Interface admin customizada
├── apps.py            # Configuração do app
├── migrations/        # Migrações do banco
├── models.py          # Model User customizado
├── permissions.py     # Classes de permissão DRF
├── serializers.py     # Serializers para API
├── urls.py            # Rotas do app
└── views.py           # ViewSets da API
```

## Models

### User
```python
class User(AbstractUser):
    role = CharField(choices=ROLE_CHOICES, default='viewer')
    organization = CharField(max_length=255, blank=True)
    phone = CharField(max_length=20, blank=True)
```

## API Endpoints

Base URL: `/api/v1/accounts/users/`

### Endpoints Disponíveis

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/v1/accounts/users/` | Listar usuários | Admin/Manager |
| GET | `/api/v1/accounts/users/{id}/` | Detalhes do usuário | Admin/Manager |
| POST | `/api/v1/accounts/users/` | Criar usuário | Admin/Manager |
| PUT/PATCH | `/api/v1/accounts/users/{id}/` | Atualizar usuário | Admin/Manager |
| DELETE | `/api/v1/accounts/users/{id}/` | Deletar usuário | Admin/Manager |
| GET | `/api/v1/accounts/users/me/` | Perfil do usuário atual | Autenticado |
| PUT/PATCH | `/api/v1/accounts/users/me/` | Atualizar próprio perfil | Autenticado |

### Autenticação JWT

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/token/` | Obter token de acesso |
| POST | `/api/auth/token/refresh/` | Renovar token |

**Exemplo - Obter Token:**
```bash
POST /api/auth/token/
{
  "username": "admin",
  "password": "senha123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbG...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbG..."
}
```

**Exemplo - Usar Token:**
```bash
GET /api/v1/accounts/users/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbG...
```

## Permissions

### IsAdminOrManager
Permite acesso apenas para usuários com role `superadmin`, `admin` ou `manager`.

```python
permission_classes = [IsAdminOrManager]
```

### IsOwnerOrReadOnly
Usuários podem editar apenas seus próprios dados. Admin/Manager podem editar todos.

```python
permission_classes = [IsOwnerOrReadOnly]
```

## Admin Interface

Acessível em: `/admin/accounts/user/`

### Funcionalidades do Admin:
- Listagem com filtros por role, staff status, ativo
- Busca por username, email, first_name, last_name
- Fieldsets organizados (Informações Pessoais, Permissões, Datas)
- Display customizado de role com cores
- Gerenciamento de grupos e permissões

## Uso

### Criar Superusuário

```bash
python manage.py createsuperuser
```

### Criar Usuário via API

```bash
POST /api/v1/accounts/users/
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "joao.silva",
  "email": "joao@example.com",
  "password": "senha123",
  "first_name": "João",
  "last_name": "Silva",
  "role": "analyst",
  "organization": "Prefeitura XYZ"
}
```

### Verificar Permissões no Code

```python
# Em views
if request.user.can_manage_templates:
    # Permite criar/editar templates
    pass

# Em models
if etp.user.can_create_Documents:
    # Usuário pode criar Documents
    pass
```

## Configurações

### settings.py

```python
# Model de usuário customizado
AUTH_USER_MODEL = 'accounts.User'

# Autenticação JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# DRF Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'config.authentication.CsrfExemptSessionAuthentication',
    ],
}
```

## Dependências

- Django 5.0+
- djangorestframework
- djangorestframework-simplejwt
- drf-spectacular (documentação OpenAPI)

## Próximos Passos (TODO)

- [ ] Implementar recuperação de senha via email
- [ ] Adicionar autenticação de dois fatores (2FA)
- [ ] Implementar multi-tenancy completo com django-tenants
- [ ] Adicionar logs de auditoria de ações de usuários
- [ ] Implementar sistema de convites para novos usuários

## Relacionamentos

Este app é utilizado por:
- **forms**: FormTemplate.created_by
- **templates**: DocumentTemplate.created_by
- **kb**: Document.uploaded_by
- **agents**: AgentPrompt.created_by
- **Documents**: ETP.user
- **rag**: RAGQuery.user, RAGContext.user
