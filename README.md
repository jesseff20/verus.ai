# Verus.AI — Plataforma de Documentos Jurídicos Inteligentes

**Geração automatizada de peças jurídicas com IA, curadoria de precedentes e gestão de casos.**

Verus.AI é um sistema full-stack que combina agentes de IA especializados, blueprints de documentos jurídicos e retrieval-augmented generation (RAG) para produzir petições, contestações, recursos e pareceres com qualidade e consistência jurídica.

---

## Funcionalidades

### Gerador de Documentos Jurídicos
- **69 blueprints** de peças jurídicas cobrindo 12 áreas do direito
- Geração multiagente com agentes especializados por ramo (cível, trabalhista, criminal, tributário, recursal, constitucional, administrativo, extrajudicial)
- Pipeline visual de 6 fases: upload → coleta de dados → geração → avaliação → análise → resultado
- Editor de documentos com TinyMCE e highlighting de placeholders
- Exportação para DOCX e PDF

### Agentes de IA Especializados
- **9 agentes geradores** (cível, recursal, constitucional, trabalhista, criminal, extrajudicial, tributário, administrativo + validador)
- **5 agentes auxiliares**: coleta de dados, verificação de cabimento, cálculo de prazos, sugestão de pedidos, consistência jurídica
- Rate limiting inteligente (6 req/min geração, 10 req/min regeneração)
- Fallback automático entre provedores de LLM

### Base de Conhecimento e RAG
- Embeddings vetoriais com `pgvector`
- Knowledge Base multi-camada (global, blueprint, agente)
- Integração com Tavily para busca de jurisprudência
- Suporte a múltiplos provedores de embedding

### Recursos Adicionais
- Painel de validação jurídica pré-exportação
- Onboarding guiado em 5 etapas (LegalCaseOnboarding)
- Seções dinâmicas com formulários e máscaras de entrada
- Rate limiting por usuário com Redis
- Auditoria completa de geração (SectionGenerationLog)
- Compartilhamento de sessões e colaboração

---

## Stack Tecnológica

### Backend
| Tecnologia | Versão | Uso |
|---|---|---|
| Python + Django | 5.0 | Framework web |
| Django REST Framework | — | API REST |
| PostgreSQL + pgvector | 15 | Banco + embeddings vetoriais |
| Redis | 7 | Cache, rate limiting, Celery broker |
| Celery | — | Filas de tarefas assíncronas |
| OpenAI / Anthropic / Watsonx | — | LLMs para agentes |
| DRF Spectacular | — | Documentação OpenAPI/Swagger |
| Tavily API | — | Busca de jurisprudência |

### Frontend
| Tecnologia | Versão | Uso |
|---|---|---|
| Next.js | 16.1 (App Router) | Framework React |
| TypeScript | — | Tipagem estática |
| React | 19 | UI |
| Shadcn/ui + Radix | — | Componentes acessíveis |
| TailwindCSS | 4 | Estilização utility-first |
| TanStack React Query | 5 | Cache e data fetching |
| React Hook Form + Zod | — | Formulários e validação |
| Zustand | — | Gerenciamento de estado |
| TinyMCE | — | Editor de documentos rico |
| Axios | — | HTTP client |
| Recharts | — | Gráficos e dashboards |
| Lucide React | — | Ícones |
| Sonner | — | Notificações toast |

### Infraestrutura
- Docker Compose (dev, homolog, produção)
- Nginx com SSL
- Entrada em container (entrypoint.sh)

---

## Estrutura do Projeto

```
bravojus/
├── backend/                          # Django REST API
│   ├── apps/
│   │   ├── accounts/                 # Autenticação e usuários
│   │   ├── agents/                   # Prompts de agentes de IA
│   │   ├── cases/                    # Gestão de casos jurídicos
│   │   ├── collaboration/            # Sessões colaborativas
│   │   ├── copilot/                  # Copilot jurídico
│   │   ├── core/                     # Modelos centrais (SystemModule, DocumentType, LegalSource)
│   │   ├── documents/                # Documentos
│   │   ├── forms/                    # Formulários dinâmicos
│   │   ├── integration/              # Integrações externas
│   │   ├── intelligent_assistant/    # ⭐ Núcleo: blueprint, sessões, geração, agentes, RAG
│   │   ├── jurisprudence/            # Jurisprudência (Tavily)
│   │   ├── kb/                       # Knowledge Base
│   │   ├── legal_library/            # Biblioteca jurídica
│   │   ├── rag/                      # RAG (Retrieval-Augmented Generation)
│   │   └── templates/                # Templates de documentos
│   ├── config/                       # Settings Django (local, homolog, produção)
│   ├── static/                       # Arquivos estáticos
│   └── manage.py
│
├── frontend/                         # Next.js App Router
│   ├── src/
│   │   ├── app/                      # Rotas (App Router)
│   │   │   ├── (dashboard)/          # Rotas autenticadas
│   │   │   │   └── dashboard/
│   │   │   │       ├── copilot/      # Copilot
│   │   │   │       └── intelligent-assistant/
│   │   │   │           ├── gerador/  # Gerador de documentos (pipeline 6 fases)
│   │   │   │           └── components/ # Componentes (DocumentEditor, ValidationPanel, etc.)
│   │   │   └── layout.tsx
│   │   ├── components/               # Componentes compartilhados
│   │   │   ├── phases/               # 6 fases do pipeline
│   │   │   ├── ui/                   # Shadcn/ui (button, dialog, form, select, etc.)
│   │   │   ├── copilot/              # PlaceholderBadge, LegalPlaceholderHighlight
│   │   │   ├── graph/                # PipelinePanel, PipelineDialog (React Flow)
│   │   │   └── ...
│   │   ├── hooks/                    # Custom hooks (use-blueprints, use-intelligent-assistant, etc.)
│   │   ├── lib/                      # Utilitários (api, constants, utils)
│   │   └── types/                    # Tipos TypeScript
│   ├── public/tinymce/               # TinyMCE self-hosted
│   └── package.json
│
├── docker-compose.local.yml          # PostgreSQL + Redis (dev)
├── docker-compose.homolog.yml        # Sandbox isolated (homolog)
├── docker-compose.test-local.yml     # Testes
├── nginx/                            # Configuração Nginx + SSL
├── scripts/                          # Scripts de deploy e backup
├── docs/                             # Documentação
│   ├── JURIDICAL_STYLE_GUIDE.md      # Guia de estilo tipográfico ABNT
│   ├── ROADMAP_EVOLUCAO.md           # Roadmap técnico
│   ├── AUDITORIA_COMPLETA.md         # Auditoria de blueprints
│   └── ...
└── ui/                               # Design system e referência visual
```

---

## Blueprints de Documentos

69 blueprints jurídicos organizados em 12 áreas:

| Área | Documentos |
|---|---|
| **Ações/Petições** | Petição Inicial Cível, Mandado de Segurança, Ação de Alimentos, Ação de Execução, Ação Anulatória de Débito Fiscal |
| **Defesas/Respostas** | Contestação Cível, Impugnação ao Cumprimento, Exceção de Pré-Executividade, Réplica, Defesa Administrativa Fiscal |
| **Recursos** | Apelação, Agravo de Instrumento, Embargos de Declaração, Recurso Especial, Recurso Extraordinário, Agravo Interno |
| **Trabalhista** | Reclamação Trabalhista, Contestação Trabalhista, Acordo Trabalhista, Recurso Ordinário Trabalhista, Ação de Consignação em Pagamento |
| **Criminal** | Queixa-Crime, Resposta à Acusação, Alegações Finais, Habeas Corpus, Liberdade Provisória, Trancamento de Inquérito |
| **Tributário** | Embargos à Execução Fiscal, Mandado de Segurança Tributário, Repetição de Indébito |
| **Família** | Divórcio Consensual, Revisional de Alimentos, Regulamentação de Guarda |
| **Consumidor** | Reclamação Consumerista |
| **Previdenciário** | BPC/LOAS, Aposentadoria Especial, Petição Inicial Previdenciária |
| **LGPD** | Política de Privacidade, Termo de Uso, DPA, Resposta a Titular, Notificação de Incidente |
| **Empresarial** | Contrato de Prestação de Serviços, NDA, Contrato de Compra e Venda, Acordo de Sócios |
| **Extrajudicial** | Notificação Extrajudicial, Parecer Jurídico, Procuração |

Cada blueprint possui de 2 a 8 seções com campos de coleta estruturados, agente gerador dedicado e validador jurídico.

---

## Começando (Desenvolvimento Local)

### Pré-requisitos

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ com extensão `pgvector`
- Redis 7+
- Docker (opcional, para bancos)

### 1. Clone e configure variáveis

```bash
git clone https://github.com/LGPDNOW/bravojus.git
cd bravojus
cp .env.example .env
# Edite .env com suas credenciais
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_juridico_completo --force
python manage.py runserver
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker (PostgreSQL + Redis)

```bash
# Ambiente de desenvolvimento (portas 5433 e 6379)
docker compose -f docker-compose.local.yml up -d

# Ambiente de homologação (portas 5435 e 6390 — isolado)
docker compose -f docker-compose.homolog.yml up -d
```

### 5. Acessar

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000/api/v1/
- **Admin:** http://localhost:8000/admin/
- **Swagger:** http://localhost:8000/api/schema/swagger-ui/

---

## Comandos Úteis

```bash
# Seed de blueprints (idempotente)
python manage.py seed_juridico_completo --force

# Criar agentes especializados
python manage.py criar_agentes_especializados

# Migrations
python manage.py makemigrations
python manage.py migrate

# Testes backend
python -m pytest

# Testes frontend
cd frontend && npm test
```

---

## Documentação

- **[GUIA DE ESTILO JURÍDICO](docs/JURIDICAL_STYLE_GUIDE.md)** — Normas ABNT, tipografia e formatação de documentos jurídicos
- **[MAPEAMENTO DE BLUEPRINTS](docs/MAPEAR_BLUEPRINTS.md)** — Catálogo completo dos 69 blueprints
- **[PLANO DE EXECUÇÃO](docs/VERUS.AI_PLANO_EXECUCAO.md)** — Status das entregas por fase
- **[ROADMAP DE EVOLUÇÃO](docs/ROADMAP_EVOLUCAO.md)** — Próximos passos técnicos
- **[BACKEND](backend/README.md)** — Documentação detalhada do Django
- **[FRONTEND](frontend/README.md)** — Documentação detalhada do Next.js
- **[AUDITORIA BLUEPRINTS](docs/AUDITORIA_COMPLETA.md)** — Revisão completa dos blueprints

---

## Autores

- **JesseFF20** — [jesseff20@gmail.com](mailto:jesseff20@gmail.com)

---

## Licença

Este projeto está sob licença proprietária. Consulte o arquivo `LICENSE` para detalhes.
