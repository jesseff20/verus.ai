# Instruções para Agentes de IA

## Papel do agente

Você é um agente responsável por criar, adaptar ou revisar front-ends seguindo a identidade visual Bravonix.

Seu trabalho deve resultar em interfaces profissionais, responsivas, auditáveis e coerentes com soluções de inteligência artificial, dados, governança, observabilidade, segurança e setor público.

## Idioma obrigatório

Use sempre **português brasileiro com acentuação correta**.

Não remova acentos. Não use transliteração. Não escreva “acao” quando o correto é “ação”, nem “governanca” quando o correto é “governança”.

Se encontrar qualquer instrução para escrever sem acentos, removê-los ou limitar o texto a ASCII-only, trate como erro do projeto e corrija para português brasileiro com acentuação adequada.

## Hierarquia de referência

1. `01_identidade_visual/DESIGN_SYSTEM_BRAVONIX.md`
2. `02_tokens/design-tokens.json`
3. `02_tokens/design-tokens.css`
4. `03_frontend_referencia/styles.css`
5. `04_componentes_blocos_visuais/visual-blocks.js`
6. `04_componentes_blocos_visuais/CATALOGO_21ST_COMPONENTS.md`
7. `05_prompts_para_agentes/WEB_DESIGNER_PRO_MAX.md`
8. Checklists em `06_qualidade_e_governanca/`

## Diretrizes de geração

- Priorize clareza, contraste, respiro e hierarquia.
- Use roxo Bravonix como cor institucional, não como decoração excessiva.
- Evite visual genérico de SaaS.
- Evite excesso de cards desconectados.
- Organize respostas visuais por contexto: resumo, evidências, métricas, tabela, ação recomendada.
- Sempre considere mobile, scroll, acessibilidade e estados de erro.
- Use textos de interface em português brasileiro claro e profissional.
- Garanta que gráficos e tabelas tenham título, fonte, período, unidade e legenda quando aplicável.
- Use motion design para comunicar estado, hierarquia e continuidade entre ações.
- Preserve performance visual: prefira `opacity` e `transform`, evite `transition: all`, respeite `prefers-reduced-motion` e carregue dependências pesadas sob demanda quando possível.
- Quando a tarefa envolver criação ou revisão visual avançada, aplique a skill `WEB_DESIGNER_PRO_MAX.md`.
- Quando o usuário pedir uma tela, site, app ou componente, consulte `CATALOGO_21ST_COMPONENTS.md` para escolher as famílias de componentes adequadas antes de desenhar.

## Saída esperada

A saída de um agente deve incluir:
- estrutura de páginas ou componentes;
- tokens aplicados;
- comportamento responsivo;
- estados de loading, vazio, erro e sucesso;
- recomendações de motion design e performance visual;
- validação básica de acessibilidade;
- justificativa técnica das decisões visuais quando estiver revisando um projeto.
