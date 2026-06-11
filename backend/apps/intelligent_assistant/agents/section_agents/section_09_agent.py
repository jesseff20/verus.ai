"""
Section09Agent - Agente para gerar Seção 9 do ETP.

Seção 9: Demonstrativo dos Resultados Pretendidos

Fundamentação: Demonstrativo dos resultados pretendidos em termos de economicidade e
de melhor aproveitamento dos recursos humanos, materiais e financeiros disponíveis.
(inciso IX do § 1° do art. 18 da Lei 14.133/21 e inciso IX, do § 1° do art. 8° do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section09Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 9 - Demonstrativo dos Resultados Pretendidos.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 9 - Demonstrativo dos Resultados Pretendidos** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso IX**: Demonstrativo dos resultados pretendidos
  em termos de economicidade e de melhor aproveitamento dos recursos humanos, materiais
  e financeiros disponíveis.
- **Decreto regulamentador local, Art. 8°, § 1°, inciso IX**: Mesma fundamentação aplicada ao
  âmbito municipal.

## REQUISITOS DA SEÇÃO 9

Esta seção deve:

1. **Demonstrar resultados em ECONOMICIDADE**
   - Economia esperada com a contratação
   - Comparação com situação atual (se houver)
   - Redução de custos diretos e indiretos
   - Otimização de recursos financeiros

2. **Demonstrar melhor aproveitamento de RECURSOS HUMANOS**
   - Liberação de servidores para atividades finalísticas
   - Redução de sobrecarga de trabalho
   - Capacitação e desenvolvimento
   - Melhoria na qualidade do trabalho

3. **Demonstrar melhor aproveitamento de RECURSOS MATERIAIS**
   - Otimização do uso de materiais
   - Redução de desperdícios
   - Melhor gestão de estoques
   - Aproveitamento de infraestrutura existente

4. **Demonstrar melhor aproveitamento de RECURSOS FINANCEIROS**
   - Otimização do orçamento
   - Melhor relação custo-benefício
   - Previsibilidade de gastos
   - Economia de escala

5. **Apresentar indicadores e metas (quando possível)**
   - Indicadores de desempenho
   - Metas quantitativas e qualitativas
   - Baseline atual (se disponível)
   - Resultados esperados

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo)
2. Resultados em economicidade (1-2 parágrafos)
3. Aproveitamento de recursos humanos (1-2 parágrafos)
4. Aproveitamento de recursos materiais (1 parágrafo)
5. Aproveitamento de recursos financeiros (1 parágrafo)
6. Indicadores e metas (tabela ou lista, se aplicável)
7. Conclusão (1 parágrafo)

## FORMATO DE TABELA DE RESULTADOS (Markdown)

| Dimensão | Situação Atual | Resultado Esperado | Ganho/Benefício |
|----------|----------------|-------------------|-----------------|
| Economicidade | ... | ... | ... |
| Recursos Humanos | ... | ... | ... |
| Recursos Materiais | ... | ... | ... |
| Recursos Financeiros | ... | ... | ... |

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 300 e 600 palavras
- Usar tabelas para indicadores
- Apresentar dados quantitativos quando disponíveis
- Ser realista nas projeções

## IMPORTANTE

- O demonstrativo deve ser REALISTA e FUNDAMENTADO
- NÃO invente números ou percentuais sem base
- Se não houver dados específicos, apresente benefícios qualitativos
- Mantenha coerência com as seções anteriores (1 a 8)
- A economicidade é requisito constitucional (Art. 70 CF/88)
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 9 - Demonstrativo dos Resultados Pretendidos
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 9 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- Os resultados devem ser realistas e fundamentados
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 9 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 9."""
        super().__init__(
            name="Section09Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_06_content: Optional[str] = None,
        section_07_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 9 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_06_content: Conteúdo da Seção 6 para contexto (opcional)
            section_07_content: Conteúdo da Seção 7 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 9
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 9 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"resultados economicidade recursos humanos materiais financeiros {objective}"
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
gere a **Seção 9 - Demonstrativo dos Resultados Pretendidos** do Estudo Técnico Preliminar.

Demonstre os resultados esperados em termos de:
- Economicidade
- Melhor aproveitamento de recursos humanos
- Melhor aproveitamento de recursos materiais
- Melhor aproveitamento de recursos financeiros

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 9" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=4096
        )

        self._log_reasoning("Seção 9 gerada com sucesso")

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
        Refina a Seção 9 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 9
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 9
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 9")

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
                query=f"resultados economicidade {feedback[:100]}",
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

        self._log_reasoning("Seção 9 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
