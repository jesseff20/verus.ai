# BravoDoc Backend

Sistema de geração de Estudos Técnicos Preliminares (Documents) com IA

## 🚀 Tecnologias

- **Django 5.0** - Framework web
- **Django REST Framework** - API REST
- **PostgreSQL 15 + pgvector** - Banco de dados com suporte a vetores
- **Redis 7** - Cache e broker Celery
- **OpenAI / Anthropic** - LLMs para agentes de IA
- **DRF Spectacular** - Documentação OpenAPI/Swagger

## 📁 Estrutura do Projeto

```
backend/
├── apps/
│   ├── accounts/     # Gerenciamento de usuários e autenticação
│   ├── forms/        # Templates de formulários dinâmicos
│   ├── templates/    # Templates de documentos (HTML/DOCX)
│   ├── kb/           # Base de conhecimento (Knowledge Base)
│   ├── agents/       # Prompts de agentes de IA
│   ├── Documents/         # Documents (core do sistema)
│   └── rag/          # RAG (Retrieval-Augmented Generation)
├── config/           # Configurações Django
├── static/           # Arquivos estáticos
├── media/            # Uploads de usuários
└── manage.py
```

## 🔧 Instalação

### 1. Pré-requisitos

- Python 3.11+
- PostgreSQL 15+ com extensão pgvector
- Redis 7+
- Docker (opcional, para bancos de dados)

### 2. Clonar Repositório

```bash
cd backend
```

### 3. Criar Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 4. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 5. Configurar Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=bravodoc
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM APIs
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# TinyMCE
TINYMCE_API_KEY=your-tinymce-key
```

### 6. Subir Bancos de Dados com Docker

```bash
docker-compose -f docker-compose.dev.yml up -d
```

Isso irá subir:
- PostgreSQL 15 com pgvector na porta 5433
- Redis 7 na porta 6379

### 7. Executar Migrações

```bash
python manage.py migrate
```

### 8. Popular Banco com Dados de Exemplo

```bash
python manage.py populate_all
```

Isso criará:
- 5 usuários de exemplo (admin, gestor, 2 analistas, visualizador)
- 3 templates de formulários (ETP Completo, ETP Simplificado, Parecer Técnico)

### 9. Criar Superusuário (Opcional)

```bash
python manage.py createsuperuser
```

### 10. Executar Servidor

```bash
python manage.py runserver
```

Servidor rodará em: http://localhost:8000

## 🔐 Credenciais de Acesso

Após executar `populate_all`, use estas credenciais:

| Usuário | Senha | Role |
|---------|-------|------|
| admin | admin123 | Administrador |
| gestor | gestor123 | Gestor |
| analista1 | analista123 | Analista |
| analista2 | analista123 | Analista |
| visualizador | viewer123 | Visualizador |

## 📚 Documentação

### Admin Interface
Acesse: http://localhost:8000/admin/

### API Swagger
Acesse: http://localhost:8000/api/swagger/

### API ReDoc
Acesse: http://localhost:8000/api/redoc/

### API Schema JSON
Acesse: http://localhost:8000/api/schema/

## 🔌 Endpoints Principais

### Autenticação
```
POST /api/auth/token/         # Obter token JWT
POST /api/auth/token/refresh/ # Renovar token
```

### Apps
```
/api/v1/accounts/users/       # Usuários
/api/v1/forms/                # Templates de formulários
/api/v1/templates/            # Templates de documentos
/api/v1/kb/                   # Base de conhecimento
/api/v1/agents/               # Agentes de IA
/api/v1/Documents/                 # Documents
/api/v1/rag/queries/          # Queries RAG
/api/v1/rag/contexts/         # Contextos RAG
```

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Testar app específico
python manage.py test apps.accounts

# Com coverage
coverage run --source='.' manage.py test
coverage report
```

## 📦 Apps Detalhados

Cada app possui um README próprio com documentação detalhada:

- [accounts/README.md](apps/accounts/README.md) - Gerenciamento de usuários
- [forms/README.md](apps/forms/README.md) - Formulários dinâmicos
- [templates/README.md](apps/templates/README.md) - Templates de documentos
- [kb/README.md](apps/kb/README.md) - Base de conhecimento
- [agents/README.md](apps/agents/README.md) - Agentes de IA
- [Documents/README.md](apps/Documents/README.md) - Documents (core)
- [rag/README.md](apps/rag/README.md) - RAG

## 🔄 Workflow Típico

### 1. Admin configura sistema

```
1. Cria templates de formulários (forms)
2. Cria templates de documentos (templates)
3. Vincula form_template → document_template
4. Configura prompts de agentes (agents)
5. Faz upload de documentos de referência (kb)
```

### 2. Usuário cria ETP

```
1. Seleciona template de formulário
2. Preenche campos do formulário
3. Usa agentes de IA para melhorar conteúdo
4. Usa RAG para buscar informações
5. Marca como "em revisão"
```

### 3. Gestor aprova ETP

```
1. Revisa conteúdo
2. Solicita alterações ou aprova
3. Marca como "completo"
```

### 4. Sistema gera documento

```
1. Carrega document_template
2. Substitui placeholders por dados do ETP
3. Gera HTML final
4. Exporta para PDF/DOCX
```

## 🛠️ Comandos Úteis

### Gerenciamento de Apps

```bash
# Criar novo app
python manage.py startapp nome_app apps/nome_app

# Criar migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Reverter migration
python manage.py migrate app_name 0001
```

### Banco de Dados

```bash
# Shell do Django
python manage.py shell

# Shell do PostgreSQL
python manage.py dbshell

# Resetar banco (CUIDADO!)
python manage.py flush

# Dump de dados
python manage.py dumpdata > backup.json

# Load de dados
python manage.py loaddata backup.json
```

### População de Dados

```bash
# Popular todos os apps
python manage.py populate_all

# Popular app específico
python manage.py populate_users
python manage.py populate_forms
```

### Desenvolvimento

```bash
# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic

# Verificar problemas
python manage.py check

# Mostrar migrações
python manage.py showmigrations
```

## 🐳 Docker

### Desenvolvimento (Apenas Bancos)

```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml logs -f
```

### Produção (TODO)

```bash
docker-compose up -d
docker-compose down
docker-compose logs -f
```

## 🔐 Segurança

### Em Desenvolvimento

- DEBUG=True
- SECRET_KEY simples
- CORS liberado
- CSRF exempt para SessionAuthentication

### Em Produção (TODO)

- [ ] DEBUG=False
- [ ] SECRET_KEY forte e único
- [ ] CORS restrito
- [ ] HTTPS obrigatório
- [ ] Rate limiting
- [ ] Logging de segurança
- [ ] Backup automático

## 📈 Performance

### Otimizações Implementadas

- `select_related` e `prefetch_related` em queries
- Índices em campos frequentemente consultados
- Cache de queries idênticas (TODO)
- Índice pgvector IVFFLAT/HNSW (TODO)

### Métricas

- Busca semântica: ~100-500ms
- Chamada LLM: ~1000-3000ms
- Query RAG completa: ~1100-3500ms

## 🚧 TODOs Principais

### Funcionalidades

- [ ] Implementar geração real de documentos (PDF/DOCX)
- [ ] Implementar busca vetorial com pgvector
- [ ] Implementar chamadas reais aos LLMs
- [ ] Adicionar processamento assíncrono com Celery
- [ ] Implementar extração de texto de PDFs/DOCX
- [ ] Adicionar assinatura digital de documentos

### Infraestrutura

- [ ] Configurar CI/CD
- [ ] Adicionar testes automatizados
- [ ] Implementar monitoramento (Sentry, etc)
- [ ] Configurar backup automático
- [ ] Criar Docker para produção

### Segurança

- [ ] Adicionar rate limiting
- [ ] Implementar 2FA
- [ ] Adicionar logs de auditoria
- [ ] Configurar HTTPS

## 📞 Suporte

Para dúvidas ou problemas:

1. Verifique os READMEs dos apps individuais
2. Consulte a documentação no Swagger
3. Abra uma issue no repositório

## 📄 Licença

MIT License

---

**BravoDoc** - Sistema Inteligente de Geração de Documents
