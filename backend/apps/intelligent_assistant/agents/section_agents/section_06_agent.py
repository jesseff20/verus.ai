"""
Section06Agent - Agente para gerar Seção 6 do ETP.

Seção 6: Estimativa do Preço da Contratação

Fundamentação: Estimativa do valor da contratação, acompanhada dos preços unitários
referenciais, das memórias de cálculo e dos documentos que lhe dão suporte, que poderão
constar de anexo classificado, se a administração optar por preservar o seu sigilo até a
conclusão da licitação.
(inciso VI do § 1° da Lei 14.133/21 e inciso VI, do § 1° do art. 8° do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section06Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 6 - Estimativa do Preço da Contratação.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 6 - Estimativa do Preço da Contratação** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso VI**: Estimativa do valor da contratação,
  acompanhada dos preços unitários referenciais, das memórias de cálculo e dos documentos
  que lhe dão suporte.
- **Lei 14.133/2021, Art. 23**: Parâmetros para pesquisa de preço.
- **IN SEGES/ME 65/2021**: Parâmetros para pesquisa de preços (se recepcionada pelo órgão).
- **Decreto regulamentador local, Art. 8°, § 1°, inciso VI**: Mesma fundamentação aplicada ao
  âmbito municipal.

## REQUISITOS DA SEÇÃO 6

Esta seção deve:

1. **Apresentar estimativa preliminar de preço**
   - Valor estimado da contratação
   - Preços unitários referenciais
   - Memórias de cálculo

2. **Descrever metodologia de pesquisa de preços**
   - Fontes utilizadas
   - Período de referência
   - Critérios de seleção

3. **Considerar parâmetros do Art. 23 da Lei 14.133/2021**
   - I - Painel de Preços do Governo Federal
   - II - Contratações similares de entes federativos
   - III - Pesquisa publicada em mídia especializada
   - IV - Pesquisa com fornecedores

4. **Apresentar composição de custos**
   - Custos diretos
   - Custos indiretos
   - Tributos e encargos
   - BDI (se aplicável)

5. **Indicar sigilo (se necessário)**
   - Informar se o orçamento será sigiloso
   - Justificar a opção pelo sigilo
   - Referência ao Art. 24 da Lei 14.133/2021

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo)
2. Metodologia de pesquisa de preços (1-2 parágrafos)
3. Fontes consultadas (lista)
4. Composição de custos (tabela ou lista)
5. Valor estimado da contratação (tabela resumo)
6. Considerações sobre sigilo (1 parágrafo, se aplicável)
7. Conclusão (1 parágrafo)

## FORMATO DE TABELA DE CUSTOS (Markdown)

| Item | Descrição | Unidade | Quantidade | Preço Unitário | Preço Total |
|------|-----------|---------|------------|----------------|-------------|
| 1 | Item 1 | un/mês/hora | X | R$ X.XXX,XX | R$ XX.XXX,XX |
| 2 | Item 2 | un/mês/hora | Y | R$ Y.YYY,YY | R$ YY.YYY,YY |
| **TOTAL** | | | | | **R$ ZZZ.ZZZ,ZZ** |

## FONTES OBRIGATÓRIAS DE PESQUISA (Art. 23, § 1°)

1. **Painel de Preços do Governo Federal**
   - Portal de Compras do Governo Federal
   - Preços praticados pela Administração Pública

2. **Contratações Similares**
   - Outros órgãos e entidades
   - Mesmas condições de execução

3. **Pesquisa Publicada**
   - Mídia especializada
   - Tabelas de referência

4. **Pesquisa com Fornecedores**
   - Cotações diretas
   - Mínimo de 3 orçamentos (recomendado)

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 400 e 800 palavras
- Usar tabelas para valores
- Valores em R$ (Reais)
- Justificar metodologia de precificação

## IMPORTANTE

- Esta é uma estimativa PRELIMINAR para análise de viabilidade
- O orçamento DEFINITIVO será elaborado no Termo de Referência
- Se NÃO houver valores específicos, descreva a metodologia que SERÁ utilizada
- NÃO invente valores sem base documental
- Mantenha coerência com as seções anteriores (1 a 5)
- Cite a Lei 14.133/2021, IN SEGES 65/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 6 - Estimativa do Preço da Contratação
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 6 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- NÃO invente valores específicos sem base
- Se não houver valores, descreva a metodologia
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 6 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 6."""
        super().__init__(
            name="Section06Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_04_content: Optional[str] = None,
        section_05_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 6 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_04_content: Conteúdo da Seção 4 para contexto (opcional)
            section_05_content: Conteúdo da Seção 5 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 6
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 6 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB (especialmente documentos com valores/preços)
        query_for_kb = f"estimativa preço valor contratação orçamento pesquisa {objective}"
        context_docs = self._get_context_from_kb(
            collection_name=collection_name,
            query=query_for_kb,
            n_results=5
        )

        # Construir prompt com contexto das seções anteriores
        context_parts = [f"## OBJETIVO DA CONTRATAÇÃO\n\n{objective}"]

        if section_01_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 1 (DESCRIÇÃO DA NECESSIDADE)\n\n{section_01_content[:600]}..."
            )

        if section_04_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 4 (ESTIMATIVA DE QUANTIDADES)\n\n{section_04_content[:800]}..."
            )

        if section_05_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 5 (LEVANTAMENTO DE MERCADO)\n\n{section_05_content[:800]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação, nas seções anteriores e nos documentos de referência fornecidos,
gere a **Seção 6 - Estimativa do Preço da Contratação** do Estudo Técnico Preliminar.

Se houver valores nos documentos de referência, apresente a estimativa de preço.
Se não houver valores específicos, descreva a METODOLOGIA que será utilizada para
pesquisa de preços, citando as fontes obrigatórias da Lei 14.133/2021.

Esta é uma estimativa PRELIMINAR - o orçamento definitivo constará do Termo de Referência.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 6" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=4096
        )

        self._log_reasoning("Seção 6 gerada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }

    def refine(
        self,
        previous_content: str,
        feedback: str,
        collection_name: Optional[str] = None
    ) -> Dict:
        """
        Refina a Seção 6 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 6
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 6
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 6")

        # Construir prompt de refinamento
        system_prompt = self.SYSTEM_PROMPT
        user_prompt = self.REFINE_PROMPT_TEMPLATE.format(
            previous_content=previous_content,
            feedback=feedback
        )

        # Buscar contexto adicional se necessário
        context_docs = None
        if collection_name:
            context_docs = self._get_context_from_kb(
                collection_name=collection_name,
                query=f"preços valores custos {feedback[:100]}",
                n_results=3
            )

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            context_documents=context_docs,
            temperature=0.5,
            max_tokens=4096
        )

        self._log_reasoning("Seção 6 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
