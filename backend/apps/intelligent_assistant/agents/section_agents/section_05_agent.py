"""
Section05Agent - Agente para gerar Seção 5 do ETP.

Seção 5: Levantamento de Mercado

Fundamentação: Levantamento de mercado, que consiste na análise das alternativas
possíveis, e justificativa técnica e econômica da escolha do tipo de solução a contratar.
(inciso V do § 1° do art. 18 da Lei 14.133/2021 e inciso V, do § 1° do art. 8° do Decreto
regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section05Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 5 - Levantamento de Mercado.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 5 - Levantamento de Mercado** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso V**: Levantamento de mercado, que consiste na
  análise das alternativas possíveis, e justificativa técnica e econômica da escolha do
  tipo de solução a contratar.
- **Lei 14.133/2021, Art. 44**: A comparação deve considerar os custos e benefícios
  durante o ciclo de vida do objeto (melhor relação custo-benefício).
- **Decreto regulamentador local, Art. 8°, § 1°, inciso V**: Mesma fundamentação aplicada ao
  âmbito municipal.
- **TCU - Acórdãos 2383/2014 e 214/2020-Plenário**: A Administração deve identificar
  um conjunto representativo dos diversos modelos existentes no mercado.

## REQUISITOS DA SEÇÃO 5

Esta seção deve:

1. **Pesquisar soluções existentes no mercado**
   - Identificar diferentes alternativas disponíveis
   - Descrever cada solução encontrada
   - Apresentar preço estimado de cada solução

2. **Comparar as soluções encontradas**
   - Análise comparativa objetiva
   - Aspectos de conveniência
   - Aspectos de economicidade
   - Aspectos de eficiência

3. **Considerar custos do ciclo de vida**
   - Custo de aquisição/contratação
   - Custo de operação/manutenção
   - Custo de descarte/substituição
   - Melhor relação custo-benefício

4. **Analisar contratações similares**
   - Contratações de outros órgãos
   - Novas metodologias ou tecnologias
   - Inovações que atendam às necessidades

5. **Considerar outras opções**
   - Consultas ou audiências públicas (se realizadas)
   - Diálogo transparente com potenciais contratadas
   - Chamamentos públicos de doação ou permutas

6. **Analisar série histórica (se houver)**
   - Contratações anteriores do órgão
   - Inconsistências identificadas
   - Lições aprendidas

## ESTRUTURA RECOMENDADA

1. Introdução sobre o levantamento de mercado (1 parágrafo)
2. Metodologia de pesquisa utilizada (1 parágrafo)
3. Soluções identificadas no mercado (tabela ou descrições)
   - Solução 1: Descrição e preço estimado
   - Solução 2: Descrição e preço estimado
   - Solução N: Descrição e preço estimado
4. Análise comparativa das soluções (2-3 parágrafos)
5. Análise do ciclo de vida (1-2 parágrafos)
6. Justificativa da escolha (1-2 parágrafos)
7. Conclusão (1 parágrafo)

## FORMATO DE TABELA COMPARATIVA (Markdown)

| Critério | Solução 1 | Solução 2 | Solução 3 |
|----------|-----------|-----------|-----------|
| Descrição | ... | ... | ... |
| Preço Estimado | R$ X | R$ Y | R$ Z |
| Vantagens | ... | ... | ... |
| Desvantagens | ... | ... | ... |
| Custo de Operação | ... | ... | ... |

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 500 e 1000 palavras
- Usar tabelas para comparativos
- Apresentar análise fundamentada
- Justificar a escolha da solução

## IMPORTANTE

- Use APENAS informações fornecidas no contexto e no objetivo
- Se não houver pesquisa de mercado realizada, indique metodologia a ser aplicada
- NÃO invente fornecedores ou preços específicos sem base
- Mantenha coerência com as seções anteriores (1 a 4)
- A escolha deve ser JUSTIFICADA tecnicamente
- Evite direcionamento para solução específica
- Cite a Lei 14.133/2021, TCU e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 5 - Levantamento de Mercado
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 5 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- A comparação deve ser objetiva e fundamentada
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021, TCU e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 5 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 5."""
        super().__init__(
            name="Section05Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_03_content: Optional[str] = None,
        section_04_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 5 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_03_content: Conteúdo da Seção 3 para contexto (opcional)
            section_04_content: Conteúdo da Seção 4 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 5
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 5 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"levantamento mercado alternativas soluções fornecedores {objective}"
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
                f"## CONTEXTO DA SEÇÃO 3 (REQUISITOS DA CONTRATAÇÃO)\n\n{section_03_content[:600]}..."
            )

        if section_04_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 4 (ESTIMATIVA DE QUANTIDADES)\n\n{section_04_content[:500]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação e nos documentos de referência fornecidos,
gere a **Seção 5 - Levantamento de Mercado** do Estudo Técnico Preliminar.

Apresente as alternativas de soluções disponíveis no mercado e faça uma
análise comparativa considerando conveniência, economicidade e eficiência.

Se não houver pesquisa de mercado realizada nos documentos de referência,
apresente a metodologia que deve ser aplicada e exemplifique possíveis soluções.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 5" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=5120
        )

        self._log_reasoning("Seção 5 gerada com sucesso")

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
        Refina a Seção 5 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 5
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 5
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 5")

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
                query=f"mercado soluções {feedback[:100]}",
                n_results=3
            )

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            context_documents=context_docs,
            temperature=0.5,
            max_tokens=5120
        )

        self._log_reasoning("Seção 5 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
