"""
Section04Agent - Agente para gerar Seção 4 do ETP.

Seção 4: Estimativa das Quantidades e Memória de Cálculo

Fundamentação: Estimativa das quantidades a serem contratadas, acompanhada das
memórias de cálculo e dos documentos que lhe dão suporte, considerando a interdependência
com outras contratações, de modo a possibilitar economia de escala.
(inciso IV do § 1° do art. 18 da Lei 14.133/21 e inciso IV, do § 1° do art. 8° do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section04Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 4 - Estimativa das Quantidades e Memória de Cálculo.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 4 - Estimativa das Quantidades e Memória de Cálculo** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso IV**: Estimativa das quantidades a serem
  contratadas, acompanhada das memórias de cálculo e dos documentos que lhe dão suporte,
  considerando a interdependência com outras contratações, de modo a possibilitar
  economia de escala.
- **Decreto regulamentador local, Art. 8°, § 1°, inciso IV**: Mesma fundamentação aplicada ao
  âmbito municipal.

## REQUISITOS DA SEÇÃO 4

Esta seção deve:

1. **Apresentar estimativa das quantidades**
   - Quantidade de cada item/serviço a ser contratado
   - Unidade de medida adequada
   - Período de vigência considerado

2. **Apresentar memória de cálculo**
   - Metodologia utilizada para estimar as quantidades
   - Dados que fundamentam o cálculo
   - Fórmulas ou critérios aplicados

3. **Considerar bases de estimativa**
   - Consumo anterior (série histórica)
   - Provável utilização futura
   - Normas internas do órgão
   - Outros fundamentos justificados

4. **Avaliar economia de escala**
   - Possibilidade de agrupar itens
   - Interdependência com outras contratações
   - Ganhos de escala esperados

## ESTRUTURA RECOMENDADA

1. Introdução sobre a estimativa de quantidades (1 parágrafo)
2. Metodologia de cálculo utilizada (1-2 parágrafos)
3. Memória de cálculo detalhada (tabela ou lista)
4. Justificativa das quantidades (1-2 parágrafos)
5. Considerações sobre economia de escala (1 parágrafo)
6. Conclusão (1 parágrafo)

## BASES PARA ESTIMATIVA

As quantidades podem ser estimadas com base em:

1. **Consumo anterior (série histórica)**
   - Dados de contratos anteriores
   - Perfil de consumo dos últimos anos
   - Tendências identificadas

2. **Provável utilização**
   - Projeção de demanda futura
   - Crescimento esperado
   - Novos projetos ou expansões

3. **Normas internas**
   - Parâmetros estabelecidos pelo órgão
   - Índices de produtividade
   - Padrões de dimensionamento

4. **Outros fundamentos**
   - Benchmarking com outros órgãos
   - Estudos técnicos específicos
   - Consultas ao mercado

## FORMATO DE TABELA SUGERIDO (Markdown)

| Item | Descrição | Unidade | Quantidade | Justificativa |
|------|-----------|---------|------------|---------------|
| 1 | Item/Serviço 1 | un/mês/hora | X | Base de cálculo |
| 2 | Item/Serviço 2 | un/mês/hora | Y | Base de cálculo |

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 400 e 800 palavras
- Usar tabelas para quantitativos
- Apresentar cálculos de forma clara
- Justificar cada quantidade estimada

## IMPORTANTE

- Use APENAS informações fornecidas no contexto e no objetivo
- Se não houver dados históricos, indique a metodologia alternativa utilizada
- NÃO invente quantidades específicas sem base de cálculo
- Mantenha coerência com as seções anteriores (1, 2 e 3)
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 4 - Estimativa das Quantidades e Memória de Cálculo
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 4 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- As quantidades devem ter justificativa clara
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 4 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 4."""
        super().__init__(
            name="Section04Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_03_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 4 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_03_content: Conteúdo da Seção 3 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 4
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 4 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"estimativa quantidades memória cálculo dimensionamento {objective}"
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

        if section_03_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 3 (REQUISITOS DA CONTRATAÇÃO)\n\n{section_03_content[:800]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação e nos documentos de referência fornecidos,
gere a **Seção 4 - Estimativa das Quantidades e Memória de Cálculo** do Estudo Técnico Preliminar.

Apresente as quantidades estimadas com a respectiva memória de cálculo.
Utilize tabela para apresentar os quantitativos de forma clara.

Se não houver dados históricos disponíveis, indique a metodologia alternativa
que seria utilizada para dimensionar as quantidades.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 4" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=4096
        )

        self._log_reasoning("Seção 4 gerada com sucesso")

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
        Refina a Seção 4 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 4
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 4
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 4")

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
                query=f"quantidades cálculo {feedback[:100]}",
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

        self._log_reasoning("Seção 4 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
