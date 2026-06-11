# DESIGN.md — Sistema de Design Bravonix

> Guia operacional para criação de interfaces, páginas, apresentações, protótipos e documentos digitais com identidade Bravonix.
>
> Este arquivo substitui a referência anterior inspirada em Ollama por uma linguagem visual própria da Bravonix: tecnológica, editorial, executiva, auditável e orientada a IA em escala.

---

## 1. Princípio Visual Central

A identidade Bravonix deve comunicar **inteligência artificial governada, infraestrutura crítica, precisão técnica e autoridade institucional**. O visual não deve parecer genérico, infantil ou excessivamente colorido. A marca deve parecer preparada para operar em ambientes corporativos, governo, auditoria, segurança, dados e IA de missão crítica.

A estética combina:

- minimalismo escuro de alto contraste;
- roxo Bravonix como sinal de inteligência, tecnologia e decisão;
- tipografia forte, geométrica e editorial;
- elementos visuais de sistemas: grids, linhas, anéis, estados, chips, marcadores, códigos, módulos e telemetria;
- narrativa visual de centro, controle, governança, operação e rastreabilidade.

A marca deve parecer **precisa, confiável e sofisticada**, não apenas bonita.

---

## 2. Personalidade da Interface

### 2.1 Atributos desejados

- **Tecnológica:** aparência de cockpit, sistema operacional, painel de IA ou central de controle.
- **Institucional:** adequada para órgãos públicos, empresas reguladas, apresentações executivas e propostas formais.
- **Auditável:** elementos devem facilitar leitura, rastreabilidade, status, versionamento e evidência.
- **Editorial:** títulos fortes, composições com hierarquia clara, linguagem de relatório premium.
- **Minimalista com presença:** poucos elementos, mas com escala, contraste e intenção.
- **Soberana:** visual que transmite controle, segurança e domínio técnico.

### 2.2 O que evitar

- Gradientes coloridos genéricos sem função.
- Visual SaaS comum com cards arredondados demais e sombras excessivas.
- Excesso de emojis, ilustrações cartoon ou ícones lúdicos.
- Paletas muito abertas, com muitas cores competindo com o roxo.
- Tipografia fraca, leve demais ou sem hierarquia.
- Interfaces poluídas sem respiro entre blocos.

---

## 3. Paleta de Cores

### 3.1 Cores principais

| Papel | Nome | Hex | Uso recomendado |
|---|---:|---:|---|
| Fundo principal escuro | Bravonix Ink | `#0A0A0A` | Fundos de landing pages, capas, decks e telas de impacto |
| Fundo escuro secundário | Ink Soft | `#1A1A1A` | Cards escuros, painéis internos e superfícies elevadas |
| Fundo claro | Paper | `#FFFFFF` | Documentos, páginas claras, formulários e relatórios |
| Fundo editorial quente | Bone | `#EDEAE2` | Seções editoriais, storytelling, páginas especiais |
| Roxo principal | Bravonix Purple | `#7030A0` | Marca, títulos, linhas, botões e destaques institucionais |
| Roxo secundário | Electric Purple | `#5B2EE0` | Destaques digitais, CTAs, gráficos e estados ativos |
| Roxo luminoso | Purple Bright | `#8B5CF6` | Highlights em fundo escuro, chips ativos e marcadores |
| Roxo profundo | Purple Deep | `#2A0E4A` | Fundos de seções imersivas e blocos premium |

### 3.2 Neutros e linhas

| Papel | Hex | Uso recomendado |
|---|---:|---|
| Texto em fundo escuro | `#FFFFFF` | Headlines, labels e informações primárias |
| Texto secundário escuro | `rgba(255,255,255,0.72)` | Parágrafos e descrições em fundo escuro |
| Texto terciário escuro | `rgba(255,255,255,0.55)` | Metadados, chrome, timestamps e notas |
| Texto em fundo claro | `#0A0A0A` | Títulos e corpo em superfícies claras |
| Texto secundário claro | `rgba(10,10,10,0.68)` | Descrições em superfícies claras |
| Linha em fundo escuro | `rgba(255,255,255,0.14)` | Divisórias, bordas e grids |
| Linha em fundo claro | `rgba(10,10,10,0.12)` | Divisórias, bordas e tabelas |

### 3.3 Cores semânticas

Usar com moderação. A cor semântica nunca deve superar a presença do roxo Bravonix.

| Estado | Hex | Uso |
|---|---:|---|
| Sucesso | `#22C55E` | Status ativo, healthy, concluído |
| Atenção | `#F59E0B` | Pendência, alerta, validação necessária |
| Erro | `#EF4444` | Falha, bloqueio, risco crítico |
| Informação | `#3B82F6` | Foco acessível, links técnicos, informação neutra |

---

## 4. Tipografia

### 4.1 Fontes oficiais

- **Display, títulos e seções:** `Sora`, preferencialmente pesos `700` e `800`.
- **Corpo e UI:** `Sora`, pesos `400`, `500` e `600`.
- **Código, labels técnicos e metadados:** `JetBrains Mono`, pesos `400`, `500` e `700`.

Fallback recomendado:

```css
font-family: 'Sora', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
font-family-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
```

### 4.2 Hierarquia para interfaces web

| Papel | Fonte | Tamanho | Peso | Line-height | Uso |
|---|---|---:|---:|---:|---|
| Hero | Sora | 72–128px | 800 | 0.92–1.00 | Capas, landing pages e seções de impacto |
| Display | Sora | 56–72px | 800 | 0.98–1.05 | Títulos de blocos principais |
| H1 | Sora | 40–56px | 800 | 1.05 | Títulos de páginas internas |
| H2 | Sora | 28–36px | 700 | 1.15 | Seções e cards destacados |
| H3 | Sora | 20–24px | 700 | 1.25 | Subcards e módulos |
| Body Large | Sora | 18–20px | 400/500 | 1.45 | Introduções e descrições de alto nível |
| Body | Sora | 15–16px | 400 | 1.55 | Texto principal |
| Small | Sora | 12–14px | 400/500 | 1.4 | Notas, descrições e microcopy |
| Mono Label | JetBrains Mono | 11–13px | 500 | 1.3 | Status, chips, versões, timestamps |
| Code | JetBrains Mono | 13–15px | 400 | 1.5 | Blocos de código, rotas e logs |

### 4.3 Regras de estilo tipográfico

- Títulos podem usar **caixa alta** quando a peça for institucional, editorial ou apresentação executiva.
- Usar `letter-spacing` positivo em labels mono: `0.08em` a `0.14em`.
- Usar `letter-spacing` negativo em títulos grandes: `-0.02em` a `-0.04em`.
- Evitar parágrafos longos em telas: dividir em blocos, bullets e painéis.
- Textos técnicos devem ser diretos, auditáveis e com termos precisos.

---

## 5. Elementos de Marca Bravonix

### 5.1 Wordmark

Usar `BRAVONIX` em caixa alta, peso forte, preferencialmente Sora ExtraBold ou Sora 800. O wordmark deve aparecer em cabeçalhos, rodapés, capas, telas de login, apresentações, documentos comerciais e dashboards institucionais.

Exemplo textual:

```txt
BRAVONIX
BRAVONIX · WORLDWIDE
BRAVONIX INTELIGÊNCIA ARTIFICIAL
```

### 5.2 Motivo do olho / centro

Quando houver símbolo visual, usar o conceito de **olho, centro, foco, inteligência e observabilidade**. O motivo pode aparecer como ícone central em capas, loading state, avatar do agente, marcador em cards, elemento de fundo com anéis concêntricos ou estado de monitoramento inteligente.

Representação CSS simplificada:

```css
.eye {
  display: inline-block;
  width: 1.1em;
  height: 1.1em;
  position: relative;
}
.eye::before,
.eye::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 55%;
  border-radius: 50%;
  background: currentColor;
}
.eye::before { left: 0; }
.eye::after { right: 0; }
.eye-inner {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 38%;
  height: 38%;
  border-radius: 50%;
  background: #0A0A0A;
  z-index: 2;
}
```

### 5.3 Anéis concêntricos

Os anéis são o elemento visual mais importante para transmitir centro de controle, IA observando contexto, ondas de processamento, escaneamento, orquestração e camadas de governança.

Regras:

- usar linhas finas de 1px;
- preferir roxo luminoso sobre fundo escuro;
- variar opacidade entre `0.10` e `0.80`;
- evitar ocupar toda a tela sem respiro;
- usar como fundo, nunca como ruído competitivo.

### 5.4 Chrome institucional

O “chrome” é a moldura informacional da peça: topo, rodapé, labels, timestamps, seção e numeração.

Exemplo:

```txt
BRAVONIX                         // TRACK A · MINIMAL                         01_2026
────────────────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────────────────
BRAVONIX · WORLDWIDE                         PT-BR                         01
```

Uso recomendado: decks, dashboards executivos, landing pages premium, relatórios digitais e telas de produto com contexto técnico.

---

## 6. Layout e Composição

### 6.1 Grid

- Usar grid de 12 colunas para web e dashboards.
- Para apresentações 16:9, usar canvas base `1920 x 1080`.
- Margens recomendadas em slides: `60px` para chrome e `120px` para conteúdo principal.
- Em páginas web, usar container máximo entre `1120px` e `1440px`.
- Em dashboards densos, permitir largura total, mas manter hierarquia por módulos.

### 6.2 Ritmo espacial

Escala base:

```txt
4, 8, 12, 16, 24, 32, 40, 48, 60, 80, 120, 160
```

Regras:

- se a peça é executiva, aumentar respiro;
- se a peça é operacional, reduzir respiro e priorizar densidade controlada;
- blocos críticos devem ter espaço antes/depois para leitura rápida;
- grids e linhas devem organizar, não decorar.

### 6.2.1 Ritmo por tipo de experiência

O ritmo define a cadência de leitura, densidade e pausa visual. Antes de montar uma tela, escolha um perfil de ritmo e mantenha consistência entre seções, cards, tabelas, ações e motion.

| Perfil | Uso | Cadência recomendada |
|---|---|---|
| Editorial | Landing pages, propostas, apresentações e páginas institucionais. | Seções amplas, títulos fortes, poucos blocos por dobra e pausas visuais generosas. |
| Operacional | Dashboards, sistemas internos, agentes e fluxos de trabalho. | Densidade controlada, módulos próximos, ações junto do contexto e leitura por varredura. |
| Executivo | Sínteses, relatórios, painéis de decisão e status. | Poucos números fortes, evidências logo abaixo, hierarquia rígida e baixo ruído visual. |
| Mobile | Interfaces de uso rápido, campo, atendimento e aprovação. | Uma ação principal por tela, blocos verticais curtos, scroll previsível e controles próximos ao conteúdo. |

Regras de ritmo:

- Use uma pausa maior antes de mudanças de assunto ou decisão.
- Mantenha blocos relacionados próximos; distância grande comunica separação.
- Evite alternar densidade alta e baixa sem intenção.
- Em páginas longas, varie a composição a cada 2 ou 3 seções para evitar monotonia.
- Em ferramentas, preserve previsibilidade: filtros, resumo, dados e ações devem aparecer em ordem recorrente.
- Motion deve seguir o ritmo da tela: interfaces operacionais pedem transições mais diretas; experiências editoriais aceitam entradas um pouco mais narrativas.

### 6.3 Composições recomendadas

#### Hero / capa

- fundo escuro;
- wordmark no topo;
- frase de impacto em Sora 800;
- roxo aplicado em uma palavra-chave;
- anéis ou olho no centro;
- chrome com data, versão e idioma.

#### Seção editorial

- fundo Bone ou Paper;
- título grande;
- texto com aparência de relatório;
- blocos numerados;
- uso de mono para edição, versão e capítulo.

#### Dashboard / operação

- fundo Ink;
- cards em Ink Soft;
- bordas finas;
- status em chips;
- números grandes;
- tabelas legíveis;
- telemetria, timestamp e saúde do sistema.

#### Documento formal

- fundo branco;
- títulos em roxo Bravonix;
- cabeçalho e rodapé com linhas roxas;
- texto justificado;
- estrutura numerada;
- linguagem formal e auditável.

---

## 7. Componentes

### 7.1 Botões

#### Primário roxo

```css
.btn-primary {
  background: #7030A0;
  color: #FFFFFF;
  border: 1px solid #7030A0;
  border-radius: 999px;
  padding: 10px 20px;
  font-family: 'Sora', sans-serif;
  font-size: 14px;
  font-weight: 600;
}
.btn-primary:hover {
  background: #5B2EE0;
  border-color: #5B2EE0;
}
```

Uso: ação principal, confirmação, “gerar”, “analisar”, “iniciar agente”.

#### Secundário escuro

```css
.btn-secondary-dark {
  background: transparent;
  color: #FFFFFF;
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 999px;
  padding: 10px 20px;
}
.btn-secondary-dark:hover {
  background: rgba(255,255,255,0.08);
}
```

#### Secundário claro

```css
.btn-secondary-light {
  background: #FFFFFF;
  color: #0A0A0A;
  border: 1px solid rgba(10,10,10,0.14);
  border-radius: 999px;
  padding: 10px 20px;
}
```

### 7.2 Cards

```css
.card-dark {
  background: #1A1A1A;
  color: #FFFFFF;
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 18px;
  padding: 24px;
}
.card-light {
  background: #FFFFFF;
  color: #0A0A0A;
  border: 1px solid rgba(10,10,10,0.12);
  border-radius: 18px;
  padding: 24px;
}
```

Regras:

- Evitar sombras fortes.
- Usar borda fina como principal separador.
- Usar raio entre `14px` e `22px` para cards.
- Para cards técnicos, incluir label mono no topo.

### 7.3 Chips e badges

```css
.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid currentColor;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.chip-active {
  background: #5B2EE0;
  color: #FFFFFF;
  border-color: #5B2EE0;
}
```

Usar para `ACTIVE`, `DRAFT`, `IN REVIEW`, `GOVERNED`, `RAG ENABLED`, `VERSION 2.4`, `HOMOLOGAÇÃO` e `PRODUÇÃO`.

### 7.4 Inputs

```css
.input {
  width: 100%;
  background: rgba(255,255,255,0.04);
  color: #FFFFFF;
  border: 1px solid rgba(255,255,255,0.16);
  border-radius: 14px;
  padding: 12px 14px;
  font-family: 'Sora', sans-serif;
  font-size: 14px;
}
.input:focus {
  outline: 2px solid rgba(139,92,246,0.45);
  border-color: #8B5CF6;
}
```

Para formulários formais em fundo claro, usar `#FFFFFF`, texto `#0A0A0A` e borda `rgba(10,10,10,0.14)`.

### 7.5 Tabelas

Regras:

- Cabeçalho com JetBrains Mono ou Sora 600.
- Linhas com bordas finas.
- Números alinhados à direita.
- Status em chips.
- Evitar zebra colorida forte.

```css
.table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Sora', sans-serif;
}
.table th {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.55);
  text-align: left;
  padding: 12px;
  border-bottom: 1px solid rgba(255,255,255,0.16);
}
.table td {
  padding: 14px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
```

---

## 8. Padrões por Tipo de Entrega

### 8.1 Landing pages e sites

A página deve parecer uma peça de tecnologia institucional premium.

Estrutura recomendada:

1. Header com wordmark, navegação curta e CTA.
2. Hero com promessa clara, roxo em palavra-chave e elemento visual de anéis.
3. Bloco “o que resolve” com 3 a 4 cards.
4. Bloco de arquitetura ou funcionamento.
5. Bloco de governança, segurança e conformidade.
6. Casos de uso por setor.
7. CTA final.

### 8.2 Dashboards

Priorizar leitura operacional.

Componentes obrigatórios:

- timestamp;
- status geral;
- filtros;
- cards de KPI;
- tabela de eventos;
- painéis com evidências;
- trilha de auditoria quando aplicável.

### 8.3 Agentes e chatbots

A experiência de agente Bravonix deve transmitir inteligência e presença, sem virar entretenimento visual.

Regras:

- avatar inspirado no olho/anéis;
- estados visuais: ouvindo, pensando, consultando ferramenta, validando, respondendo;
- resposta longa bem formatada;
- resumo em áudio quando aplicável;
- memória local/sessão sempre transparente ao usuário;
- indicadores de ferramentas e fontes quando usados.

Exemplos de status:

```txt
● ANALISANDO CONTEXTO
● CONSULTANDO BASE DE CONHECIMENTO
● EXECUTANDO FERRAMENTA
● VALIDANDO RESPOSTA
● PRONTO
```

### 8.4 Apresentações

Usar linguagem de deck editorial Bravonix.

Elementos recomendados:

- `BRAVONIX · WORLDWIDE` no rodapé;
- numeração de slide;
- track/capítulo no topo;
- título forte em caixa alta;
- roxo como destaque pontual;
- anéis, grids e linhas finas;
- slides com muito respiro para narrativa executiva;
- slides densos apenas quando forem operacionais.

### 8.5 Documentos formais

Seguir a identidade de documentos Bravonix:

- fonte Sora;
- título em roxo `#7030A0`;
- cabeçalho e rodapé com linha roxa;
- texto justificado;
- estrutura numerada;
- linguagem técnica, formal e auditável;
- evitar excesso de elementos visuais.

---

## 9. Microcopy e Tom de Voz

### 9.1 Tom

- claro;
- técnico;
- objetivo;
- institucional;
- seguro;
- sem exagero comercial;
- com foco em governança, resultado e rastreabilidade.

### 9.2 Frases de marca

Podem ser usadas em capas, seções e campanhas:

```txt
No centro do que importa.
IA governada, auditável e em produção.
Orquestração inteligente para operações críticas.
Da prova de conceito à escala institucional.
Governança não como relatório: como componente vivo da operação.
```

### 9.3 Verbos recomendados

- Orquestrar
- Auditar
- Governar
- Automatizar
- Rastrear
- Validar
- Operacionalizar
- Integrar
- Proteger
- Escalar

### 9.4 Evitar

- “Revolucionário” sem evidência.
- “Mágico”, “incrível”, “absurdo” ou linguagem informal excessiva.
- Promessas absolutas sem restrição.
- Termos vagos como “solução completa” sem explicar escopo.

---

## 10. Iconografia e Ilustrações

### 10.1 Estilo de ícones

- linha fina ou preenchimento simples;
- cantos discretamente arredondados;
- monocromático ou roxo;
- ícones técnicos: banco de dados, escudo, grafo, documento, agente, modelo, API, trilha, lupa, checklist.

### 10.2 Ilustrações

Usar ilustrações abstratas e técnicas:

- anéis;
- redes;
- nós;
- grids;
- módulos;
- fluxos;
- linhas de conexão;
- diagramas de arquitetura.

Evitar personagens 3D genéricos, robôs cartoon, imagens gratuitas sem identidade e excesso de brilho neon.

---

## 11. Movimento e Interação

### 11.1 Princípios

- Movimento deve comunicar estado, não apenas decorar.
- Animações devem ser discretas, rápidas e precisas.
- Em agentes, as ondas/anéis podem reagir ao áudio e ao processamento.
- Motion design deve reforçar continuidade, feedback e hierarquia visual sem atrasar a leitura.
- Toda animação relevante deve ter alternativa estática via `prefers-reduced-motion`.

### 11.2 Durações

| Tipo | Duração |
|---|---:|
| Hover simples | 120–180ms |
| Entrada de card | 180–260ms |
| Troca de estado | 200–300ms |
| Loading/onda contínua | 1200–2400ms |

### 11.3 Easing

```css
transition-timing-function: cubic-bezier(.2,.8,.2,1);
```

### 11.4 Boas práticas de implementação

- Preferir `opacity` e `transform` para entradas, hovers, expansão leve e feedback de botões.
- Evitar `transition: all`; declarar apenas as propriedades necessárias.
- Evitar animar `height`, `width`, `box-shadow`, `filter` e `backdrop-filter` em áreas grandes.
- Usar `will-change` apenas durante a interação ou em componentes realmente animados.
- Limitar stagger a elementos curtos; em tabelas, listas longas e respostas de agente, priorizar performance e leitura imediata.

### 11.5 Oportunidades de performance visual

- Carregar bibliotecas pesadas, como gráficos e exportação de imagem, apenas quando a tela ou bloco precisar delas.
- Evitar fontes duplicadas entre HTML e CSS; manter uma estratégia única de carregamento.
- Definir dimensões explícitas e lazy loading para imagens não críticas.
- Usar `content-visibility`, paginação ou virtualização em mensagens, tabelas e blocos extensos.
- Medir Lighthouse, DevTools Performance e Web Vitals antes de aprovar uma entrega visual.

---

## 12. Acessibilidade

- Contraste mínimo WCAG AA para textos essenciais.
- Não depender apenas de cor para status.
- Estados ativos devem ter texto e ícone/forma.
- Foco visível obrigatório em teclado.
- Tamanho mínimo de clique: `40px` de altura/largura.
- Textos em roxo sobre fundo escuro devem usar `#8B5CF6`, não `#7030A0`, quando o contraste estiver baixo.

---

## 13. Tokens CSS Recomendados

```css
:root {
  --bnx-ink: #0A0A0A;
  --bnx-ink-soft: #1A1A1A;
  --bnx-paper: #FFFFFF;
  --bnx-bone: #EDEAE2;

  --bnx-purple: #7030A0;
  --bnx-purple-2: #5B2EE0;
  --bnx-purple-bright: #8B5CF6;
  --bnx-purple-deep: #2A0E4A;

  --bnx-text-dark: #0A0A0A;
  --bnx-text-light: #FFFFFF;
  --bnx-text-muted-dark: rgba(10,10,10,0.68);
  --bnx-text-muted-light: rgba(255,255,255,0.72);

  --bnx-rule-dark: rgba(255,255,255,0.14);
  --bnx-rule-light: rgba(10,10,10,0.12);

  --bnx-success: #22C55E;
  --bnx-warning: #F59E0B;
  --bnx-danger: #EF4444;
  --bnx-info: #3B82F6;

  --bnx-radius-sm: 10px;
  --bnx-radius-md: 14px;
  --bnx-radius-lg: 18px;
  --bnx-radius-xl: 24px;
  --bnx-radius-pill: 999px;

  --bnx-font-sans: 'Sora', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --bnx-font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
```

---

## 14. Exemplo de Base HTML/CSS

```html
<section class="bnx-hero">
  <header class="bnx-chrome">
    <strong class="bnx-wordmark">BRAVONIX</strong>
    <span>// INTELIGÊNCIA ARTIFICIAL GOVERNADA</span>
    <span>2026</span>
  </header>

  <div class="bnx-hero-grid">
    <div>
      <p class="bnx-eyebrow">// ECOSSISTEMA DE IA _</p>
      <h1>No centro do que <span>importa</span>.</h1>
      <p>Orquestração, governança e auditoria para IA em escala institucional.</p>
      <button class="btn-primary">Iniciar diagnóstico</button>
    </div>
    <div class="bnx-rings" aria-hidden="true"></div>
  </div>
</section>
```

```css
.bnx-hero {
  min-height: 100vh;
  background: var(--bnx-ink);
  color: var(--bnx-text-light);
  font-family: var(--bnx-font-sans);
  padding: 40px 60px;
  overflow: hidden;
}
.bnx-chrome {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--bnx-rule-dark);
  padding-bottom: 14px;
  font-family: var(--bnx-font-mono);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.65);
}
.bnx-wordmark {
  font-family: var(--bnx-font-sans);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #FFFFFF;
}
.bnx-hero-grid {
  min-height: calc(100vh - 120px);
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  align-items: center;
  gap: 80px;
}
.bnx-eyebrow {
  font-family: var(--bnx-font-mono);
  color: var(--bnx-purple-bright);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: 13px;
}
.bnx-hero h1 {
  max-width: 900px;
  font-size: clamp(56px, 8vw, 128px);
  line-height: 0.94;
  letter-spacing: -0.04em;
  text-transform: uppercase;
  margin: 24px 0;
}
.bnx-hero h1 span {
  color: var(--bnx-purple-bright);
}
.bnx-hero p:not(.bnx-eyebrow) {
  max-width: 640px;
  color: var(--bnx-text-muted-light);
  font-size: 20px;
  line-height: 1.5;
}
```

---

## 15. Checklist de Qualidade

Antes de considerar uma entrega visual como aderente à Bravonix, validar:

- [ ] O roxo Bravonix aparece como destaque, não como excesso.
- [ ] A tipografia principal usa Sora.
- [ ] Metadados, código e labels usam JetBrains Mono.
- [ ] O layout tem respiro e hierarquia.
- [ ] O visual transmite tecnologia, governança e confiança.
- [ ] Cards e painéis usam bordas finas e pouca sombra.
- [ ] Há consistência entre botões, chips, inputs e tabelas.
- [ ] Estados são claros: ativo, pendente, erro, concluído.
- [ ] A interface é legível em fundo escuro e claro.
- [ ] O conteúdo técnico é auditável e rastreável.
- [ ] A peça não parece template genérico de SaaS.
- [ ] A peça mantém o conceito visual de centro, controle e inteligência.

---

## 16. Diretriz Final

Toda peça Bravonix deve responder visualmente a três perguntas:

1. **Isso parece confiável para uma operação crítica?**
2. **Isso comunica IA com governança, auditoria e rastreabilidade?**
3. **Isso tem identidade própria ou parece mais um template genérico?**

Se a resposta para qualquer uma delas for “não”, revise a composição antes de entregar.
