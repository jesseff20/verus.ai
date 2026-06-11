# Análise de Integração do Copilot - Verus.AI

## Visão Geral

Este documento mapeia todas as oportunidades de integração do Copilot nas funcionalidades do Verus.AI para minimizar digitação/cadastro manual e potencializar o uso de IA.

---

## 1. Módulo de Processos/Casos

### 1.1 Novo Caso (`/dashboard/processos/novo`)
**Status atual:** ✅ Possui preenchimento automático via IA
- Upload de documento (PDF/DOCX) → extração automática de dados
- Texto na descrição → botão "Preencher com IA"
- Prazos identificados automaticamente

**Oportunidades de melhoria:**
- [ ] Copilot lateral para sugerir estratégia jurídica baseada na descrição
- [ ] Sugestão automática de documentos necessários para o caso
- [ ] Análise de similaridade com casos anteriores

### 1.2 Edição de Caso (`/dashboard/processos/[id]/editar`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] Copilot para sugerir atualizações de status baseado nas movimentações
- [ ] Análise automática de peças processuais anexadas
- [ ] Sugestão de próximos passos processuais

---

## 2. Módulo de Clientes

### 2.1 Cadastro de Cliente (`/dashboard/clients`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Preenchimento automático via documento**: Upload de CPF/CNPJ, contrato social, RG → extração de dados
- [ ] **Busca de dados públicos**: Integrar com APIs de receita para auto-preenchimento
- [ ] **Análise de conflito de interesses**: Copilot verifica automaticamente se novo cliente tem conflito com clientes existentes
- [ ] **Sugestão de honorários**: Baseado no perfil do cliente e histórico

**Prompt sugerido para Copilot:**
```
Analise os dados do cliente [NOME/CPF/CNPJ] e verifique:
1. Conflito de interesses com clientes atuais
2. Histórico processual público
3. Score de crédito/risco
4. Sugestão de faixa de honorários baseada no perfil
```

---

## 3. Módulo CRM/Leads

### 3.1 Pipeline de Leads (`/dashboard/crm`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Classificação automática de temperatura**: Copilot analisa descrição e sugere hot/warm/cold
- [ ] **Sugestão de abordagem**: Baseado na especialidade e perfil do lead
- [ ] **Previsão de conversão**: IA analisa padrões históricos para prever probabilidade
- [ ] **Auto-preenchimento**: Lead chega via formulário/webhook → Copilot extrai e preenche dados
- [ ] **Follow-up automático**: Copilot gera mensagens personalizadas para cada estágio

**Prompts sugeridos:**
```
Analise este lead e sugira:
1. Temperatura (hot/warm/cold) com justificativa
2. Estratégia de abordagem inicial
3. Objeções comuns neste tipo de caso e como contornar
4. Faixa de honorários sugerida
```

```
Gere uma mensagem de follow-up personalizada para lead no estágio [STAGE]
com interesse em [SPECIALTY], demonstrando [TEMPERATURE]
```

---

## 4. Módulo de Contratos

### 4.1 Contratos (`/dashboard/contratos`)
**Status atual:** ✅ Possui upload com análise IA
- Upload de contrato existente → análise e preenchimento automático
- Geração de contratos via IA

**Oportunidades de melhoria:**
- [ ] Copilot para negociar cláusulas específicas com cliente
- [ ] Análise de riscos contratuais
- [ ] Sugestão de cláusulas baseada no tipo de contrato
- [ ] Comparação automática entre versões de contrato

---

## 5. Módulo Financeiro

### 5.1 Financeiro (`/dashboard/financeiro`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Previsão de fluxo de caixa**: Copilot analisa histórico e projeta recebíveis
- [ ] **Sugestão de honorários**: Baseado em casos similares, complexidade, valor da causa
- [ ] **Análise de inadimplência**: Identifica padrões de clientes inadimplentes
- [ ] **Recomendações de cobrança**: Gera mensagens personalizadas para cobrança

**Prompts sugeridos:**
```
Analise o fluxo de caixa dos últimos 6 meses e projete:
1. Recebíveis esperados para próximos 30/60/90 dias
2. Risco de inadimplência por cliente
3. Sugestão de provisionamento
```

```
Para o caso [CASO_ID] com valor da causa R$ X e complexidade [NÍVEL],
sugira honorários considerando:
- Tabela OAB local
- Histórico de casos similares
- Perfil financeiro do cliente
```

---

## 6. Módulo Timesheet

### 6.1 Timesheet (`/dashboard/timesheet`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Preenchimento automático via análise de atividade**: Copilot analisa e-mails, documentos criados, petições → sugere registros de horas
- [ ] **Sugestão de descrição**: Baseado no tipo de atividade realizada
- [ ] **Detecção de horas não lançadas**: IA identifica atividades não registradas
- [ ] **Otimização de billing**: Sugere melhor alocação de horas entre casos

**Prompts sugeridos:**
```
Analise minhas atividades dos últimos 7 dias (e-mails, documentos, petições)
e sugira registros de timesheet não lançados com:
- Caso vinculado
- Tipo de atividade
- Horas estimadas
- Descrição técnica apropriada
```

---

## 7. Módulo NFS-e

### 7.1 NFS-e (`/dashboard/nfse`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Geração automática de notas**: Baseado em timesheet aprovado → Copilot gera NFS-e
- [ ] **Validação de dados**: IA verifica inconsistências antes de emitir
- [ ] **Classificação fiscal automática**: Sugere código de serviço baseado na descrição

---

## 8. Módulo de Lembretes

### 8.1 Lembretes (`/dashboard/reminders`)
**Status atual:** ✅ Possui campo `copilot_prompt` no cadastro
- Templates rápidos já incluem prompts predefinidos
- Copilot é acionado quando lembrete dispara

**Oportunidades de melhoria:**
- [ ] **Criação automática de lembretes**: Copilot analisa casos e sugere lembretes (prazos, audiências, tarefas)
- [ ] **Priorização inteligente**: Reordena lembretes baseado em urgência real
- [ ] **Agrupamento automático**: Agrupa lembretes relacionados

---

## 9. Módulo de Equipe

### 9.1 Equipe (`/dashboard/equipe`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Sugestão de alocação**: Copilot analisa habilidades, carga atual e sugere alocação ideal
- [ ] **Balanceamento de carga**: Identifica advogados sobrecarregados/subutilizados
- [ ] **Match de especialidade**: Sugere equipe baseada na especialidade do caso

**Prompts sugeridos:**
```
Para o novo caso [CASO_ID] com especialidade [X], sugira a equipe ideal
considerando:
1. Especialidade de cada advogado
2. Carga horária atual
3. Histórico de atuação em casos similares
4. Disponibilidade para prazos urgentes
```

---

## 10. Módulo de Documentos

### 10.1 Documentos (`/dashboard/documentos`)
**Status atual:** ⚠️ Possui gerador de documentos, mas sem Copilot integrado

**Oportunidades:**
- [ ] **Geração de peças via Copilot**: Chat direto para gerar petições, contratos, procurações
- [ ] **Revisão automática**: Copilot revisa documentos antes de salvar
- [ ] **Sugestão de modelos**: Baseado no tipo de documento necessário
- [ ] **Preenchimento automático**: Dados do caso → documento pre-preenchido

---

## 11. Módulo de Prazos Inteligentes

### 11.1 Prazos Inteligentes (`/dashboard/prazos-inteligentes`)
**Status atual:** ⚠️ Funcionalidade existente, sem Copilot visível

**Oportunidades:**
- [ ] **Cálculo automático de prazos**: Copilot identifica tipo de prazo e calcula dias úteis
- [ ] **Sugestão de estratégia**: Baseado no prazo, sugere ações prioritárias
- [ ] **Alerta de prazos críticos**: IA identifica prazos que precisam de atenção imediata

---

## 12. Tribunal Push / Datajud

### 12.1 Tribunal Push (`/dashboard/tribunal-push`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Análise automática de movimentações**: Copilot interpreta cada movimentação processual
- [ ] **Sugestão de ações**: Para cada nova publicação, sugere próximas ações
- [ ] **Resumo de diário oficial**: IA resume publicações relevantes

---

## 13. Módulo de Conflito de Interesses

### 13.1 Conflito de Interesses (`/dashboard/conflito-interesses`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Análise automática**: Copilot varre base completa ao cadastrar novo caso/cliente
- [ ] **Relatório de riscos**: Gera relatório detalhado de potenciais conflitos
- [ ] **Sugestão de medidas**: Recomenda ações para mitigar conflitos identificados

---

## 14. Módulo de Auditoria

### 14.1 Auditoria (`/dashboard/auditoria`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Detecção de anomalias**: IA identifica padrões incomuns em lançamentos
- [ ] **Relatório inteligente**: Copilot gera insights a partir dos dados de auditoria
- [ ] **Recomendações de compliance**: Sugere melhorias baseadas em gaps identificados

---

## 15. Módulo de Honorários

### 15.1 Honorários (`/dashboard/honorarios`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Sugestão de valores**: Baseado em caso similar, tabela OAB, complexidade
- [ ] **Análise de acordos**: Copilot sugere termos de pagamento ideais
- [ ] **Previsão de recebimento**: IA estima probabilidade de recebimento por cliente

---

## 16. Módulo de Email Templates

### 16.1 Email Templates (`/dashboard/email-templates`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Geração de templates via Copilot**: Chat para criar templates personalizados
- [ ] **Personalização automática**: Copilot adapta template para contexto específico
- [ ] **Sugestão de envio**: IA recomenda quando enviar cada tipo de email

---

## 17. Módulo de Blueprints/Workflows

### 17.1 Blueprints (`/dashboard/blueprints`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Criação de workflows via chat**: "Copilot, crie um workflow para divórcio consensual"
- [ ] **Otimização de processos**: IA analisa workflows existentes e sugere melhorias
- [ ] **Detecção de gargalos**: Identifica etapas que mais atrasam

---

## 18. Simulações (Jurisprudência, Acórdãos, etc.)

### 18.1 Simulações (`/dashboard/simulations/*`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Análise preditiva**: Copilot analisa jurisprudência e prevê probabilidade de sucesso
- [ ] **Estratégia processual**: Sugere argumentos baseados em casos similares
- [ ] **Resumo de entendimentos**: IA resume posicionamentos de tribunais sobre tema

---

## 19. Biblioteca Jurídica

### 19.1 Legal Library (`/dashboard/legal-library`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Busca semântica**: Copilot entende contexto da busca, não apenas palavras-chave
- [ ] **Resumo de documentos**: IA gera resumos de leis, jurisprudências, doutrinas
- [ ] **Recomendação de leitura**: Sugere documentos relevantes para casos ativos

---

## 20. Dashboard/KPIs

### 20.1 KPIs (`/dashboard/kpis`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Insights automáticos**: Copilot analisa KPIs e gera insights acionáveis
- [ ] **Alertas proativos**: IA identifica métricas fora do esperado e alerta
- [ ] **Recomendações de melhoria**: Sugere ações baseadas em tendências

---

## 21. Calendário

### 21.1 Calendário (`/dashboard/calendario`, `/dashboard/processos/calendario`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Sugestão de agendamento**: Copilot analisa agenda e sugere melhores horários
- [ ] **Detecção de conflitos**: IA identifica sobreposição de compromissos
- [ ] **Preparação automática**: Para cada audiência, gera checklist de preparação

---

## 22. Mensagens com Clientes

### 22.1 Mensagens Clientes (`/dashboard/mensagens-clientes`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Respostas sugeridas**: Copilot sugere respostas para mensagens de clientes
- [ ] **Tom e estilo**: Ajusta sugestão baseado no perfil do cliente
- [ ] **Tradução automática**: Para clientes estrangeiros

---

## 23. Importação/Exportação

### 23.1 Importar/Exportar (`/dashboard/importar`, `/dashboard/exportar`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Mapeamento inteligente**: Copilot ajuda a mapear colunas de planilhas importadas
- [ ] **Validação de dados**: IA identifica inconsistências antes de importar
- [ ] **Relatórios personalizados**: Geração de exports via comando natural

---

## 24. Configurações/Perfil

### 24.1 Settings (`/dashboard/settings/*`)
**Status atual:** ❌ Sem integração Copilot

**Oportunidades:**
- [ ] **Onboarding guiado**: Copilot ajuda novos usuários a configurarem o sistema
- [ ] **Recomendações de configuração**: IA sugere settings baseados no perfil do escritório

---

## Priorização de Implementação

### Alta Prioridade (Impacto Imediato)
1. **CRM/Leads** - Conversão de leads impacta receita diretamente
2. **Clientes** - Cadastro é ponto de entrada de todo fluxo
3. **Documentos** - Geração de peças é demanda diária
4. **Financeiro/Honorários** - Impacto financeiro direto

### Média Prioridade
5. **Timesheet** - Ganho de eficiência operacional
6. **Equipe** - Otimização de recursos humanos
7. **Prazos Inteligentes** - Redução de risco processual
8. **Tribunal Push** - Valor diferencial competitivo

### Baixa Prioridade (Nice to Have)
9. **Simulações** - Funcionalidade avançada
10. **Biblioteca Jurídica** - Complementar
11. **KPIs/Dashboard** - Já possui dados, IA é incremental

---

## Arquitetura Sugerida

### Padrão de Integração

```typescript
// 1. CopilotFloatingButton - Componente reutilizável
<CopilotFloatingButton
  context="client-create"
  onEnhance={(data) => fillForm(data)}
  promptSuggestion={CLIENT_PROMPTS}
/>

// 2. CopilotSidePanel - Para integrações mais complexas
<CopilotSidePanel
  context="case-detail"
  sessionId={caseId}
  features={['analyze', 'suggest', 'draft']}
/>

// 3. CopilotInline - Para sugestões inline no formulário
<CopilotInline
  field="description"
  onSuggest={() => copilot.suggest('case-description')}
/>
```

### Endpoints Backend Necessários

```python
# Novos endpoints Copilot por contexto
POST /api/v1/copilot/clients/analyze/      # Análise de clientes
POST /api/v1/copilot/crm/classify/         # Classificação de leads
POST /api/v1/copilot/finance/suggest/      # Sugestão de honorários
POST /api/v1/copilot/timesheet/auto-fill/  # Preenchimento automático
POST /api/v1/copilot/documents/draft/      # Geração de documentos
POST /api/v1/copilot/team/allocate/        # Alocação de equipe
```

---

## Estimativa de Esforço

| Módulo | Complexidade | Tempo Est. | Impacto |
|--------|-------------|------------|---------|
| CRM | Média | 3-4 dias | Alto |
| Clientes | Média | 2-3 dias | Alto |
| Documentos | Alta | 5-7 dias | Alto |
| Financeiro | Média | 3-4 dias | Alto |
| Timesheet | Baixa | 1-2 dias | Médio |
| Equipe | Média | 2-3 dias | Médio |
| Prazos | Baixa | 1-2 dias | Médio |

**Total estimado:** 17-25 dias de desenvolvimento

---

## Próximos Passos

1. **Validar priorização** com stakeholders
2. **Detalhar especificação técnica** de cada módulo
3. **Criar componentes reutilizáveis** de Copilot
4. **Implementar por módulo** em ordem de prioridade
5. **Testes de usabilidade** após cada módulo
6. **Coletar feedback** e iterar

---

## Notas

- Todos os prompts devem ser customizáveis pelo usuário
- Manter opção de "desligar Copilot" por módulo
- Logs de uso do Copilot para análise de adoção
- Métricas de economia de tempo por funcionalidade
