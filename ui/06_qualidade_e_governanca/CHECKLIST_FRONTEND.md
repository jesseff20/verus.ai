# Checklist de Qualidade — Front-end Bravonix

## Idioma e conteúdo

- [ ] Todos os textos estão em português brasileiro.
- [ ] Acentuação preservada corretamente.
- [ ] Não há instruções de ASCII-only ou remoção de acentos.
- [ ] Qualquer ocorrência sem acento em texto visível, prompt ou microcopy foi corrigida.
- [ ] Labels, botões, mensagens de erro e estados vazios são claros.
- [ ] O texto é institucional, direto e auditável.

## Identidade visual

- [ ] Paleta Bravonix aplicada com consistência.
- [ ] Roxo usado como elemento institucional, não como excesso decorativo.
- [ ] Tipografia com hierarquia clara.
- [ ] Espaçamentos consistentes.
- [ ] Visual evita aparência genérica, infantil ou poluída.
- [ ] Para entregas visuais avançadas, a skill `WEB_DESIGNER_PRO_MAX.md` foi aplicada.

## Ritmo visual

- [ ] A tela usa um perfil de ritmo claro: editorial, operacional, executivo ou mobile.
- [ ] Pausas visuais separam mudanças reais de contexto, não apenas decoração.
- [ ] Blocos relacionados permanecem próximos e ações ficam junto do conteúdo acionado.
- [ ] A densidade visual é consistente com a tarefa do usuário.
- [ ] O ritmo de motion acompanha o contexto: direto em ferramentas, mais narrativo em páginas institucionais.

## Motion design

- [ ] Movimento comunica estado, progresso, continuidade ou feedback.
- [ ] Animações decorativas são discretas e não competem com o conteúdo.
- [ ] Durações seguem o padrão Bravonix: 120-180ms para hover, 180-260ms para entrada e 200-300ms para troca de estado.
- [ ] `prefers-reduced-motion` é respeitado em CSS e JavaScript.
- [ ] Animações usam prioritariamente `opacity` e `transform`.

## Performance visual

- [ ] Não há uso desnecessário de `transition: all`.
- [ ] Filtros, blur, sombras grandes e `backdrop-filter` são usados com parcimônia.
- [ ] Dependências pesadas, como gráficos e exportação de imagem, são carregadas sob demanda quando possível.
- [ ] Imagens possuem dimensões explícitas, `loading`/`decoding` adequados e formatos otimizados.
- [ ] Listas longas, mensagens e blocos extensos usam contenção, paginação, virtualização ou `content-visibility` quando aplicável.
- [ ] Fontes externas não são carregadas em duplicidade.

## UX e arquitetura da informação

- [ ] O pedido do usuário foi mapeado para famílias de componentes adequadas usando `CATALOGO_21ST_COMPONENTS.md` quando aplicável.
- [ ] Conteúdo agrupado por lógica de uso.
- [ ] Não há sequência excessiva de cards sem contexto.
- [ ] Ações ficam próximas ao conteúdo acionado.
- [ ] Existe síntese executiva quando a tela é analítica.
- [ ] Tabelas, gráficos e métricas têm contexto suficiente.

## Responsividade

- [ ] Layout funciona em desktop.
- [ ] Layout funciona em tablet.
- [ ] Layout funciona em mobile.
- [ ] Scroll vertical e horizontal funcionam quando necessário.
- [ ] Botões não ficam fora da área visível ou sem contexto.

## Acessibilidade

- [ ] Contraste adequado.
- [ ] Foco visível em elementos interativos.
- [ ] Navegação por teclado considerada.
- [ ] Imagens relevantes possuem texto alternativo.
- [ ] Elementos interativos possuem rótulos compreensíveis.

## Dados e visualização

- [ ] Gráficos têm título.
- [ ] Gráficos têm unidade e período.
- [ ] Métricas indicam fonte ou regra de cálculo.
- [ ] Tabelas são legíveis e exportáveis quando necessário.
- [ ] Inconsistências ou ausência de dados são sinalizadas.

## Governança

- [ ] Decisões importantes são rastreáveis.
- [ ] Limitações são explicitadas.
- [ ] O usuário entende a origem das informações.
- [ ] Há separação entre evidência, interpretação e recomendação.
