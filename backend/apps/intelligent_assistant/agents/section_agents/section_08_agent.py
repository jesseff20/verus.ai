"""
Section08Agent - Agente para gerar Seção 8 do ETP.

Seção 8: Justificativa para Parcelamento

Fundamentação: Justificativas para o parcelamento ou não da solução.
(inciso VIII do § 1° do art. 18 da Lei 14.133/21 e art. 7°, inciso VII da IN 40/2020
e inciso VIII, do § 1° do art. 8° do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section08Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 8 - Justificativa para Parcelamento.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 8 - Justificativa para Parcelamento** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso VIII**: Justificativas para o parcelamento
  ou não da solução.
- **Lei 14.133/2021, Art. 40, § 3°**: Regra do parcelamento e suas exceções.
- **Lei 14.133/2021, Art. 47**: Tratamento diferenciado para ME/EPP.
- **IN SEGES 40/2020, Art. 7°, inciso VII**: Parcelamento da solução.
- **Decreto regulamentador local, Art. 8°, § 1°, inciso VIII**: Mesma fundamentação aplicada ao
  âmbito municipal.

## REQUISITOS DA SEÇÃO 8

Esta seção deve:

1. **Identificar se o objeto é DIVISÍVEL ou não**
   - Análise das características técnicas do objeto
   - Verificar se há itens tecnicamente independentes
   - Peculiaridades de comercialização no mercado

2. **Se PARCELAR - justificar a divisão**
   - Em quantos lotes/itens será dividido
   - Critério de divisão adotado
   - Benefícios esperados (ampliação da competição, participação ME/EPP)

3. **Se NÃO PARCELAR - justificar a não divisão**
   - Aplicar uma das exceções do Art. 40, § 3°:
     * I - Economia de escala justifica contratação global
     * II - Objeto é tecnicamente indivisível
     * III - Risco de perda de economia de escala
   - Demonstrar que o parcelamento é inviável ou desvantajoso

4. **Considerar impacto em ME/EPP**
   - Como a decisão afeta a participação de ME/EPP
   - Aplicação do Art. 47 (tratamento diferenciado)
   - Cota reservada, se aplicável

5. **Definir critério de adjudicação**
   - Por item
   - Por grupo/lote
   - Global

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo)
2. Análise de divisibilidade técnica (1-2 parágrafos)
3. Análise de viabilidade econômica do parcelamento (1-2 parágrafos)
4. Impacto na competitividade e ME/EPP (1 parágrafo)
5. Decisão fundamentada (1-2 parágrafos)
6. Critério de adjudicação (1 parágrafo)
7. Conclusão (1 parágrafo)

## EXCEÇÕES AO PARCELAMENTO (Art. 40, § 3°)

O parcelamento NÃO será adotado quando:
- **I** - A economia de escala justificar a contratação global
- **II** - O objeto for tecnicamente indivisível
- **III** - Houver risco de perda de economia de escala

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 300 e 600 palavras
- Justificativa clara e fundamentada
- Citar artigos da Lei 14.133/2021
- Analisar prós e contras objetivamente

## IMPORTANTE

- A REGRA é o parcelamento (Art. 40, § 3° da Lei 14.133/2021)
- O NÃO parcelamento é EXCEÇÃO e deve ser JUSTIFICADO
- A decisão deve considerar viabilidade técnica E econômica
- Mantenha coerência com as seções anteriores (1 a 7)
- Considere o impacto na participação de ME/EPP
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 8 - Justificativa para Parcelamento
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 8 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- Justifique adequadamente a decisão de parcelar ou não
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 8 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 8."""
        super().__init__(
            name="Section08Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_04_content: Optional[str] = None,
        section_06_content: Optional[str] = None,
        section_07_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 8 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_04_content: Conteúdo da Seção 4 para contexto (opcional)
            section_06_content: Conteúdo da Seção 6 para contexto (opcional)
            section_07_content: Conteúdo da Seção 7 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 8
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 8 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"parcelamento divisão lotes adjudicação contratação {objective}"
        context_docs = self._get_context_from_kb(
            collection_name=collection_name,
            query=query_for_kb,
            n_results=4
        )

        # Construir prompt com contexto das seções anteriores
        context_parts = [f"## OBJETIVO DA CONTRATAÇÃO\n\n{objective}"]

        if section_01_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 1 (DESCRIÇÃO DA NECESSIDADE)\n\n{section_01_content[:500]}..."
            )

        if section_04_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 4 (ESTIMATIVA DE QUANTIDADES)\n\n{section_04_content[:500]}..."
            )

        if section_06_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 6 (ESTIMATIVA DE PREÇO)\n\n{section_06_content[:500]}..."
            )

        if section_07_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 7 (DESCRIÇÃO DA SOLUÇÃO)\n\n{section_07_content[:600]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação, nas seções anteriores e nos documentos de referência fornecidos,
gere a **Seção 8 - Justificativa para Parcelamento** do Estudo Técnico Preliminar.

Analise se o objeto deve ser parcelado ou não, considerando:
- Divisibilidade técnica
- Viabilidade econômica
- Impacto na competitividade
- Impacto na participação de ME/EPP

A decisão deve ser JUSTIFICADA com base na Lei 14.133/2021.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 8" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=4096
        )

        self._log_reasoning("Seção 8 gerada com sucesso")

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
        Refina a Seção 8 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 8
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 8
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 8")

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
                query=f"parcelamento divisão {feedback[:100]}",
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

        self._log_reasoning("Seção 8 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
