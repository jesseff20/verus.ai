# Pesquisa UX — Documentos Jurídicos Verus.AI

**Data:** 2026-05-26  
**Objetivo:** Tornar o Verus.AI a melhor ferramenta de construção de documentos jurídicos do mercado brasileiro

---

## 1. Perfil de Usuário Persona

### Persona Primária: Dr. Ricardo Mendes
- **Idade:** 42 anos
- **Cargo:** Advogado Sênior / Sócio de escritório médio
- **Especialidade:** Direito Civil e Trabalhista
- **Rotina:** 10-15 petições/semana, reuniões com clientes, audiências

**Dores principais:**
- Perde 2-3h/dia formatando documentos e copiando dados entre sistemas
- Erros de digitação em prazos e referências processuais
- Dificuldade em manter consistência entre versões de documentos
- Templates desatualizados com mudanças legislativas

**Objetivos:**
- Reduzir tempo de criação de petições em 50%
- Zero erros em prazos e citações legais
- Focar em estratégia, não em formatação

### Persona Secundária: Dra. Ana Paula Souza
- **Idade:** 28 anos
- **Cargo:** Advogada Júnior / Estagiária avançada
- **Especialidade:** Direito Consumidor
- **Rotina:** Primeira versão de documentos, pesquisa jurisprudencial

**Dores principais:**
- Insegurança sobre estrutura correta de peças
- Dificuldade em encontrar jurisprudência relevante
- Medo de cometer erros em prazos processuais
- Curva de aprendizado íngreme em softwares complexos

**Objetivos:**
- Aprender padrões de redação jurídica
- Ganhar confiança com validações automáticas
- Ser produtiva desde o primeiro mês

### Persona Terciária: Servidor Público (Carlos Alberto)
- **Idade:** 51 anos
- **Cargo:** Analista Judiciário / Escrevente
- **Local:** Tribunal de Justiça Estadual
- **Rotina:** Conferência de petições, intimações, certidões

**Dores principais:**
- Sistemas lentos e burocráticos dos tribunais
- Petições mal formatadas dificultam análise
- Dificuldade de comunicação com advogados externos

**Objetivos:**
- Receber documentos padronizados
- Agilizar processo de conferência

---

## 2. Top 20 Funcionalidades Recomendadas (Priorizadas)

### 🔴 P0 — Crítico (Diferenciais Competitivos)

| # | Funcionalidade | Impacto | Esforço |
|---|----------------|---------|---------|
| 1 | **Preenchimento automático com IA de dados processuais** | Alto | Médio |
| 2 | **Validação em tempo real de prazos e referências legais** | Alto | Alto |
| 3 | **Sugestão contextual de cláusulas e fundamentações** | Alto | Alto |
| 4 | **Templates inteligentes adaptáveis por tipo de ação/tribunal** | Alto | Baixo |
| 5 | **Exportação multi-formato (PDF, DOCX, ODT) com formatação ABNT/NBR** | Alto | Médio |

### 🟡 P1 — Alto Valor (Retenção)

| # | Funcionalidade | Impacto | Esforço |
|---|----------------|---------|---------|
| 6 | **Versionamento inteligente com diff semântico** | Médio | Médio |
| 7 | **Colaboração em tempo real (multi-editor)** | Médio | Alto |
| 8 | **Integração com APIs dos tribunais (PJe, e-SAJ, Projudi)** | Alto | Alto |
| 9 | **Busca jurisprudencial contextual durante redação** | Alto | Médio |
| 10 | **Checklist automático de requisitos por tipo de peça** | Médio | Baixo |

### 🟢 P2 — Valor Adicional (Satisfação)

| # | Funcionalidade | Impacto | Esforço |
|---|----------------|---------|---------|
| 11 | **Histórico de alterações com rollback seletivo** | Médio | Médio |
| 12 | **Biblioteca de argumentos vencedores por matéria** | Médio | Baixo |
| 13 | **Calculadora de prazos processuais integrada** | Médio | Médio |
| 14 | **Assinatura digital integrada (Gov.br, certificados A3)** | Alto | Alto |
| 15 | **Modo de revisão com comentários e aprovações** | Médio | Médio |

### 🔵 P3 — "Nice to Have"

| # | Funcionalidade | Impacto | Esforço |
|---|----------------|---------|---------|
| 16 | **Tradução jurídica (PT↔EN↔ES)** | Baixo | Médio |
| 17 | **Análise de similaridade com peças de concorrentes** | Baixo | Alto |
| 18 | **Gerador de resumos executivos automáticos** | Médio | Médio |
| 19 | **Integração com sistemas de gestão (Astrea, ProJuris, SAJ)** | Médio | Alto |
| 20 | **Treinamento gamificado para novos usuários** | Baixo | Baixo |

---

## 3. Fluxos de UX Recomendados

### 3.1 Fluxo de Criação Rápida (Power User)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Dashboard → "Nova Peça" (atalho: N)                     │
│    - Seleção por tipo (Petição Inicial, Contestação, etc.) │
│    - Ou busca textual: "trabalhista horas extras"          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Preenchimento Guiado Inteligente                        │
│    - Campos obrigatórios destacados                        │
│    - Auto-complete de dados do cliente (CPF, OAB, etc.)   │
│    - Sugestão de documentos necessários                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Geração com IA (30-60 segundos)                         │
│    - Progress indicator com preview parcial                │
│    - Opção de "Cancelar e editar manualmente"              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Revisão em Editor Rico                                  │
│    - Highlight de seções geradas por IA                    │
│    - Validações em tempo real (prazos, citações)           │
│    - Sugestões de melhoria contextual                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Exportação / Envio                                       │
│    - Preview PDF antes de exportar                         │
│    - Envio direto para e-SAJ/PJe (se integrado)            │
│    - Salvar como rascunho ou versão final                  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Fluxo de Importação de Documento Existente

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Upload de PDF/DOCX                                       │
│    - Drag & drop ou colar texto                            │
│    - OCR automático para PDF escaneado                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Análise Estrutural com IA                                │
│    - Identificação: tipo de peça, tribunal, partes          │
│    - Extração de: prazos, valores, pedidos                  │
│    - Mapeamento para estrutura Verus.AI                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Confirmação de Mapeamento                               │
│    - Preview lado a lado (original ↔ estruturado)          │
│    - Campos não mapeados destacados                        │
│    - Correção manual se necessário                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Conversão para Template Verus.AI                        │
│    - Geração de versão editável                            │
│    - Preservação de formatação original                    │
│    - Sugestão de melhorias                                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Fluxo de Colaboração (Revisão em Equipe)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Compartilhamento                                         │
│    - Link com permissões (leitura/comentário/edição)       │
│    - Notificação por email/WhatsApp                         │
│    - Prazo para revisão (opcional)                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Revisão Assíncrona                                       │
│    - Comentários por seleção de texto                      │
│    - Sugestões de alteração (track changes)                │
│    - @menções para colegas                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Consolidação                                             │
│    - Dashboard de comentários pendentes                    │
│    - Aceitar/rejeitar por item                             │
│    - Histórico de quem alterou o quê                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Features "Uau" que Diferenciariam o Verus.AI

### 🚀 4.1 "Copilot Jurídico" — Assistente de Redação em Tempo Real

**O que é:** Um assistente tipo GitHub Copilot, mas para petições jurídicas.

**Como funciona:**
- Enquanto o advogado digita, o Copilot sugere:
  - Próximos parágrafos baseados no contexto
  - Fundamentação jurídica relevante (artigos, súmulas, jurisprudência)
  - Cláusulas padrão para a situação
- Atalhos inteligentes:
  - `/citacao [tema]` → Insere citação formatada
  - `/juris [palavra-chave]` → Busca e insere jurisprudência
  - `/prazo [tipo]` → Calcula e insere prazo processual
  - `/modelo [tipo]` → Insere template de seção

**Diferencial:** Nenhum concorrente brasileiro oferece isso nativamente.

---

### 🚀 4.2 "Radar de Precedentes" — Alerta Preventivo de Risco

**O que é:** Análise preditiva de chances de sucesso baseada em jurisprudência.

**Como funciona:**
- Ao redigir uma petição, o sistema analisa:
  - Tribunal específico
  - Juízo/vara
  - Matéria jurídica
  - Argumentos utilizados
- Retorna:
  - % de sucesso para teses similares
  - Jurisprudência contrária que deve ser enfrentada
  - Sugestão de argumentos alternativos

**Diferencial:** Transforma o Verus.AI de "ferramenta de redação" para "consultor estratégico".

---

### 🚀 4.3 "Time Travel" — Versionamento Semântico

**O que é:** Git para documentos jurídicos, mas com compreensão do significado das alterações.

**Como funciona:**
- Cada salvamento cria um "ponto no tempo"
- Diff semântico mostra:
  - "Adicionado fundamento sobre dano moral"
  - "Alterado valor da causa de R$ 50k para R$ 75k"
  - "Removida citação da Súmula 123"
- Rollback seletivo: "Reverter apenas a seção de pedidos"

**Diferencial:** Advogados podem explorar alternativas sem medo de perder trabalho.

---

### 🚀 4.4 "Integração Tribunal Nativa" — Protocolo sem Sair do Verus.AI

**O que é:** Conexão direta com sistemas dos tribunais via API ou automação.

**Como funciona:**
- Configurar credenciais do e-SAJ, PJe, Projudi
- Ao finalizar documento:
  - Validação automática de requisitos
  - Geração de guias de custas
  - Protocolo direto
  - Acompanhamento automático do processo
- Notificações de andamentos processuais

**Diferencial:** Elimina a necessidade de acessar 5+ sistemas diferentes.

---

### 🚀 4.5 "Biblioteca Viva de Argumentos" — Aprendizado Contínuo

**O que é:** Sistema que aprende com as petições vencedoras do usuário/escritório.

**Como funciona:**
- Usuário marca petições como "Vencedora"
- Sistema extrai:
  - Argumentos utilizados
  - Estrutura bem-sucedida
  - Jurisprudência citada
- Sugere automaticamente em casos similares futuros
- Compartilhamento opcional dentro do escritório

**Diferencial:** Capitaliza conhecimento tácito do escritório.

---

## 5. Integrações Recomendadas

### 5.1 Integrações Prioritárias (P0)

| Integração | Finalidade | API Disponível |
|------------|------------|----------------|
| **OAB Nacional** | Validação número OAB, situação cadastral | Sim (REST) |
| **Receita Federal** | Consulta CPF/CNPJ, certidões | Sim (REST) |
| **e-SAJ (TJSP)** | Protocolo, consulta processual | Parcial (necessita credenciamento) |
| **PJe (CNJ)** | Protocolo multi-tribunal | Sim (via API PJe 2.0) |
| **Projudi (TJs)** | Consulta e protocolo | Varia por tribunal |

### 5.2 Integrações de Valor (P1)

| Integração | Finalidade |
|------------|------------|
| **Jusbrasil API** | Pesquisa jurisprudencial ampliada |
| **Cartórios Online** | Certidões de nascimento, casamento, óbito |
| **Gov.br** | Autenticação unificada, procurações |
| **Seal (certificado digital)** | Assinatura digital integrada |
| **Timer** | Calculadora de prazos processuais |

### 5.3 Integrações de Gestão (P2)

| Integração | Finalidade |
|------------|------------|
| **Astrea** | Sincronização de processos |
| **ProJuris** | Importação de dados do caso |
| **SAJ Advogado** | Integração bidirecional |
| **LegalOne** | Gestão financeira + processos |
| **ClickSign/DocuSign** | Assinatura eletrônica de documentos |

---

## 6. Benchmark Competitivo

### 6.1 Principais Concorrentes Brasileiros

| Software | Pontos Fortes | Lacunas |
|----------|---------------|---------|
| **Jusbrasil** | - Maior base jurisprudencial<br>- Marca forte<br>- Ecossistema completo | - Editor de documentos básico<br>- Pouca personalização<br>- IA superficial |
| **ProJuris** | - Gestão completa de escritório<br>- Automação de prazos<br>- Mobile app | - Geração de documentos limitada<br>- UX datada<br>- Curva de aprendizado |
| **Astrea** | - Interface moderna<br>- Bom suporte<br>- Integrações | - Foco em gestão, não em redação<br>- IA inexistente |
| **SAJ Advogado** | - Tradicional no mercado<br>- Funcionalidades completas | - UX ultrapassada<br>- Lentidão<br>- Pouca inovação |
| **LegalOne** | - Completo (jurídico + financeiro)<br>- Training | - Complexo demais<br>- Caro para pequenos escritórios |

### 6.2 Gaps no Mercado Brasileiro

1. **IA genuína para redação jurídica** — Todos falam em IA, mas poucos entregam geração contextual de qualidade
2. **Integração real com tribunais** — Maioria exige upload manual nos sistemas dos tribunais
3. **Colaboração em tempo real** — Ferramentas ainda são "single-player"
4. **Aprendizado contínuo** — Nenhum sistema aprende com as vitórias do usuário
5. **UX focada em produtividade** — Interfaces sobrecarregadas, muitos cliques

### 6.3 Tendências Legal Tech 2025-2026

| Tendência | Maturidade | Oportunidade para Verus.AI |
|-----------|------------|---------------------------|
| **IA Generativa para documentos** | Emergente | 🟢 Liderar com Copilot Jurídico |
| **APIs de tribunais unificadas** | Em crescimento | 🟡 Preparar integração nativa |
| **Assinatura digital cloud** | Consolidada | 🟢 Oferecer integrado (não 3rd party) |
| **Automação de prazos** | Consolidada | 🟡 Manter parity com concorrentes |
| **Análise preditiva de litígios** | Emergente | 🟢 Diferencial competitivo forte |
| **Colaboração remota** | Em crescimento | 🟢 Aproveitar tendência pós-pandemia |

---

## 7. Recomendações de Implementação

### Fase 1 — Fundação (3 meses)
1. Implementar **Templates Inteligentes** (P0 #4)
2. Desenvolver **Preenchimento Automático com IA** (P0 #1)
3. Criar **Validação em Tempo Real** básica (P0 #2)
4. Exportação **PDF/DOCX com formatação jurídica** (P0 #5)

### Fase 2 — Diferenciação (3-6 meses)
1. Lançar **Copilot Jurídico** (Feature "Uau" #4.1)
2. Implementar **Sugestão Contextual de Cláusulas** (P0 #3)
3. Integração **OAB + Receita Federal** (Integrações P0)
4. **Busca Jurisprudencial Contextual** (P1 #9)

### Fase 3 — Liderança (6-12 meses)
1. **Radar de Precedentes** (Feature "Uau" #4.2)
2. **Integração com Tribunais** (Feature "Uau" #4.4)
3. **Biblioteca Viva de Argumentos** (Feature "Uau" #4.5)
4. **Colaboração em Tempo Real** (P1 #7)

---

## 8. Métricas de Sucesso

| Métrica | Baseline | Target (6 meses) | Target (12 meses) |
|---------|----------|------------------|-------------------|
| Tempo médio de criação de petição | ~45 min | 25 min | 15 min |
| Erros de prazo/referência | ~5% das peças | <1% | <0.5% |
| Satisfação do usuário (NPS) | — | 60+ | 75+ |
| Retenção D30 | — | 70% | 85% |
| Pieces geradas/usuário/mês | — | 15 | 25 |

---

## 9. Fontes Consultadas

- Padrões de UX de ferramentas de produtividade (Notion, Coda, Google Docs)
- Documentação de APIs jurídicas brasileiras (OAB, PJe, e-SAJ)
- Reviews de usuários em G2, Capterra para softwares jurídicos
- Fóruns de advogados (Jusbrasil Comunidade, Migalhas)
- Relatórios de tendências Legal Tech (Lawtomation, LegalTech News)
- Benchmark de funcionalidades de concorrentes diretos

---

*Documento criado para guiar o desenvolvimento UX do Verus.AI como ferramenta líder em documentos jurídicos no Brasil.*
