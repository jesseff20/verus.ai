# BravoDoc Frontend

Frontend moderno para o sistema BravoDoc, construído com Next.js 14, TypeScript e Shadcn/ui.

## 🚀 Tecnologias

- **Next.js 14** (App Router) - Framework React
- **TypeScript** - Type safety
- **Shadcn/ui** - Componentes UI modernos
- **TailwindCSS** - Styling utility-first
- **TanStack Query** - Data fetching e cache
- **React Hook Form** - Gerenciamento de formulários
- **Zod** - Validação de schemas
- **Axios** - HTTP client
- **Zustand** - State management (client)

## 📁 Estrutura do Projeto

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # Rotas de autenticação
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/       # Rotas autenticadas
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── Documents/
│   │   │   ├── documents/
│   │   │   ├── agents/
│   │   │   ├── knowledge-base/
│   │   │   └── settings/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/                # Componentes Shadcn/ui
│   │   ├── forms/             # Componentes de formulários
│   │   ├── tables/            # Tabelas de dados
│   │   └── layouts/           # Layouts reutilizáveis
│   ├── lib/
│   │   ├── api.ts             # Cliente API
│   │   ├── auth.ts            # Autenticação
│   │   └── utils.ts           # Utilitários
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   ├── use-Documents.ts
│   │   └── use-rag.ts
│   ├── types/
│   │   └── index.ts           # TypeScript types
│   └── styles/
│       └── globals.css
├── public/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 🔧 Instalação

### 1. Instalar dependências

```bash
npm install
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.local.example .env.local
```

Edite `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api/v1
```

### 3. Executar em desenvolvimento

```bash
npm run dev
```

Acesse: http://localhost:3000

### 4. Build para produção

```bash
npm run build
npm start
```

## 🎨 Shadcn/ui

### Adicionar novo componente

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add form
```

### Componentes disponíveis

- Button, Badge, Avatar
- Card, Alert, Dialog, Sheet
- Form, Input, Textarea, Select
- Table, Data Table
- Toast, Tooltip, Popover
- Dropdown Menu, Context Menu
- Tabs, Accordion, Separator
- Calendar, Date Picker
- E muito mais...

Veja todos em: https://ui.shadcn.com/docs/components

## 🔐 Autenticação

O sistema usa JWT tokens armazenados em localStorage:

```typescript
// Login
const { data } = await api.post('/auth/token/', {
  username: 'admin',
  password: 'admin123'
})

// Armazena tokens
localStorage.setItem('access_token', data.access)
localStorage.setItem('refresh_token', data.refresh)

// Requisições autenticadas
axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
```

## 📡 API Client

```typescript
// lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
})

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
```

## 🎯 Próximos Passos

### Em Desenvolvimento

- [ ] Páginas de autenticação (Login/Register)
- [ ] Layout do Dashboard
- [ ] CRUD de Documents
- [ ] Editor de formulários dinâmicos
- [ ] Interface de agentes de IA
- [ ] Upload e gestão de documentos
- [ ] Interface RAG
- [ ] Configurações de usuário

### Componentes a Criar

- [ ] Sidebar com navegação
- [ ] Header com perfil de usuário
- [ ] Cards de estatísticas
- [ ] Tabela de Documents com filtros
- [ ] Form builder NoCode
- [ ] Editor de templates
- [ ] Chat interface para agentes
- [ ] Upload zone para documentos
- [ ] Preview de documentos gerados

## 🧪 Testes

```bash
# Adicionar testes (TODO)
npm run test
npm run test:watch
npm run test:coverage
```

## 📦 Scripts Disponíveis

```bash
npm run dev          # Desenvolvimento
npm run build        # Build produção
npm start            # Servidor produção
npm run lint         # ESLint
npm run lint:fix     # ESLint com fix
```

## 🎨 Customização de Tema

Edite `tailwind.config.ts` para personalizar cores:

```typescript
theme: {
  extend: {
    colors: {
      primary: {
        DEFAULT: "hsl(221.2 83.2% 53.3%)",
        foreground: "hsl(210 40% 98%)",
      },
      // ... mais cores
    },
  },
}
```

## 🌓 Dark Mode

Dark mode é suportado nativamente:

```typescript
// Adicionar toggle
import { useTheme } from "next-themes"

const { theme, setTheme } = useTheme()

<Button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
  Toggle Theme
</Button>
```

## 📱 Responsivo

Todos os componentes Shadcn/ui são responsivos por padrão.

Use breakpoints do Tailwind:

```typescript
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Cards */}
</div>
```

## 🔗 Links Úteis

- [Next.js Docs](https://nextjs.org/docs)
- [Shadcn/ui Docs](https://ui.shadcn.com)
- [TailwindCSS Docs](https://tailwindcss.com/docs)
- [TanStack Query](https://tanstack.com/query)
- [React Hook Form](https://react-hook-form.com/)
- [Zod](https://zod.dev/)

## 🐛 Troubleshooting

### Erro de CORS

Certifique-se que o backend está configurado para aceitar requests do frontend:

```python
# backend/config/settings/local.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

### Erro de Autenticação

Verifique se os tokens estão sendo salvos corretamente no localStorage.

### Hot Reload não funciona

```bash
# Limpar cache
rm -rf .next
npm run dev
```

---

**BravoDoc Frontend** - Sistema Inteligente de Gestão de Documents
