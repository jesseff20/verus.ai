"""
Section02Agent - Agente para gerar Seção 2 do ETP.

Seção 2: Previsão no Plano de Contratações Anual

Fundamentação: Demonstração da previsão da contratação no plano de contratações anual,
sempre que elaborado, de modo a indicar o seu alinhamento com o planejamento da
Administração. (inciso II do § 1° do art. 18 da Lei 14.133/21 e inciso II, do § 1° do art. 8°
do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section02Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 2 - Previsão no Plano de Contratações Anual.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 2 - Previsão no Plano de Contratações Anual** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso II**: Demonstração da previsão da contratação
  no plano de contratações anual, sempre que elaborado, de modo a indicar o seu alinhamento
  com o planejamento da Administração.
- **Lei 14.133/2021, Art. 12, inciso VII**: Demonstração do alinhamento entre a contratação
  e o planejamento do órgão ou entidade, identificando a previsão no Plano Anual de
  Contratações ou, se for o caso, justificando a ausência de previsão.
- **Decreto regulamentador local, Art. 8°, § 1°, inciso II**: Mesma fundamentação aplicada ao
  âmbito municipal.

## REQUISITOS DA SEÇÃO 2

Esta seção deve:

1. **Verificar existência do PAC**
   - O órgão possui Plano Anual de Contratações (PAC)?
   - Se sim, qual o exercício de referência?
   - Se não, justificar a ausência

2. **Demonstrar a previsão (se houver PAC)**
   - Número do item no PAC
   - Descrição do item previsto
   - Valor estimado previsto
   - Data de previsão para contratação

3. **Demonstrar alinhamento com o planejamento**
   - Como a contratação se alinha ao planejamento estratégico?
   - Qual a relação com os objetivos institucionais?
   - Há vinculação com metas ou programas específicos?

4. **Se NÃO houver previsão no PAC**
   - Justificar a ausência de previsão
   - Explicar se é demanda emergente ou não prevista
   - Indicar providências para inclusão no próximo PAC

## ESTRUTURA RECOMENDADA

1. Introdução sobre o Plano de Contratações Anual (1 parágrafo)
2. Situação da previsão - se existe ou não (1-2 parágrafos)
3. Detalhamento da previsão ou justificativa de ausência (1-2 parágrafos)
4. Alinhamento com o planejamento institucional (1 parágrafo)
5. Conclusão (1 parágrafo)

## CENÁRIOS POSSÍVEIS

**Cenário 1 - Contratação PREVISTA no PAC:**
- Informar número/código do item no PAC
- Detalhar a previsão (descrição, valor, período)
- Demonstrar alinhamento com planejamento

**Cenário 2 - Contratação NÃO PREVISTA no PAC:**
- Justificar a não previsão (demanda emergente, necessidade superveniente, etc.)
- Explicar as razões da contratação mesmo sem previsão
- Indicar providências para regularização

**Cenário 3 - Órgão NÃO possui PAC:**
- Informar que o órgão ainda não elaborou o PAC
- Demonstrar alinhamento com outros instrumentos de planejamento
- Citar LOA, PPA ou outros documentos de planejamento

## ESTILO

- Tom formal e técnico
- Terceira pessoa
- Texto entre 200 e 500 palavras
- Citar a fundamentação legal quando apropriado
- Ser objetivo e direto

## IMPORTANTE

- Use APENAS informações fornecidas no contexto e no objetivo
- Se não houver informações sobre o PAC, indique que deve ser verificado junto ao setor competente
- NÃO invente números de PAC ou valores específicos
- Mantenha coerência com a Seção 1 (Descrição da Necessidade)
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 2 - Previsão no Plano de Contratações Anual
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 2 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- NÃO invente informações sobre o PAC
- Mantenha coerência com a Seção 1
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 2 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 2."""
        super().__init__(
            name="Section02Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 2 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 2
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 2 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"plano contratações anual PAC planejamento {objective}"
        context_docs = self._get_context_from_kb(
            collection_name=collection_name,
            query=query_for_kb,
            n_results=4
        )

        # Construir prompt com contexto da Seção 1 se disponível
        context_parts = [f"## OBJETIVO DA CONTRATAÇÃO\n\n{objective}"]

        if section_01_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 1 (DESCRIÇÃO DA NECESSIDADE)\n\n{section_01_content}"
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação e nos documentos de referência fornecidos,
gere a **Seção 2 - Previsão no Plano de Contratações Anual** do Estudo Técnico Preliminar.

Se não houver informações específicas sobre o PAC nos documentos de referência,
indique que a verificação deve ser realizada junto ao setor de planejamento competente.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 2" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=3072
        )

        self._log_reasoning("Seção 2 gerada com sucesso")

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
        Refina a Seção 2 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 2
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 2
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 2")

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
                query=f"plano contratações {feedback[:100]}",
                n_results=3
            )

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            context_documents=context_docs,
            temperature=0.5,
            max_tokens=3072
        )

        self._log_reasoning("Seção 2 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
