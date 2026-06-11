# Agent Tools — Guia de Configuração e Teste

## O que é

Agent Tools permite que agentes jurídicos executem **buscas reais na web** (Google via Serper.dev) automaticamente durante a geração de peças processuais. Em vez de gerar texto genérico, o agente recebe dados reais de jurisprudência, legislação e doutrina — e incorpora no texto gerado.

---

## Como funciona

```
Usuário clica "Gerar" na peça processual
        ↓
DynamicGraphBuilder inicia geração seção por seção
        ↓
Para cada seção com Tools vinculados:
  1. Busca RAG na KB jurídica
  2. Executa tools vinculados ao agente:
     - Web Search (Serper): busca Google por jurisprudência/legislação
  3. Resultados formatados em markdown
  4. Injetados no {{context}} junto com RAG
  5. LLM gera texto com dados reais
        ↓
Seção gerada com fundamentos jurídicos verificáveis
```

---

## Configuração

### 1. Variável de ambiente necessária

```env
SERPER_API_KEY=sua-chave-aqui
```

Obter chave em: https://serper.dev

### 2. Criar Agent Tools via seed

```bash
python manage.py seed_agent_tools
```

Isso cria o tool **Web Search (Serper)** no banco de dados.

### 3. Vincular tool a um agente de seção

No admin Django ou via BlueprintEditor:
1. Acesse `/admin/intelligent_assistant/sectionagentconfig/`
2. Edite o agente desejado
3. Em "Agent Tools", adicione o tool "Web Search (Serper)"

---

## Tool disponível

| Tool | Tipo | Descrição |
|------|------|-----------|
| Web Search (Serper) | `web_search` | Busca Google para jurisprudência, legislação e doutrina |
