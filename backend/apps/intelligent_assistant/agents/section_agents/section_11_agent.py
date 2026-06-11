"""
Section11Agent - Agente para gerar Seção 11 do ETP.

Seção 11: Contratações Correlatas e/ou Interdependentes

Fundamentação: Contratações correlatas e/ou interdependentes.
(inciso XI do § 1° do art. 18 da Lei 14.133/21 e inciso XI, do § 1° do art. 8° do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section11Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 11 - Contratações Correlatas e/ou Interdependentes.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 11 - Contratações Correlatas e/ou Interdependentes** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso XI**: Contratações correlatas e/ou interdependentes.
- **Lei 14.133/2021, Art. 18, § 1°, inciso IV**: Economia de escala em contratações
  interdependentes.
- **Decreto regulamentador local, Art. 8°, § 1°, inciso XI**: Mesma fundamentação aplicada ao
  âmbito municipal.

## DEFINIÇÕES

- **Contratações CORRELATAS**: Contratações que possuem relação de similaridade ou
  complementaridade com a contratação em estudo, mas podem ser executadas de forma
  independente.

- **Contratações INTERDEPENDENTES**: Contratações cuja execução depende ou influencia
  diretamente a contratação em estudo, havendo relação de dependência entre elas.

## REQUISITOS DA SEÇÃO 11

Esta seção deve:

1. **Identificar contratações CORRELATAS**
   - Contratos vigentes similares
   - Atas de registro de preços relacionadas
   - Contratações do mesmo objeto em outros setores
   - Oportunidades de agregação de demandas

2. **Identificar contratações INTERDEPENDENTES**
   - Contratos de infraestrutura necessários
   - Serviços de suporte essenciais
   - Licenças ou autorizações prévias
   - Contratos de manutenção vinculados

3. **Analisar IMPACTOS das contratações correlatas/interdependentes**
   - Como afetam o planejamento
   - Oportunidades de economia de escala
   - Riscos de incompatibilidade
   - Cronograma de execução

4. **Propor AÇÕES de integração**
   - Alinhamento de cronogramas
   - Padronização de especificações
   - Compartilhamento de recursos
   - Gestão integrada

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo)
2. Contratações correlatas identificadas (1-2 parágrafos ou tabela)
3. Contratações interdependentes identificadas (1-2 parágrafos ou tabela)
4. Análise de impactos (1-2 parágrafos)
5. Ações de integração propostas (1 parágrafo)
6. Conclusão (1 parágrafo)

## FORMATO DE TABELA (Markdown)

| Contratação | Tipo | Objeto | Vigência | Impacto |
|-------------|------|--------|----------|---------|
| Contrato nº XXX | Correlata | Descrição | XX/XX/XXXX | Descrição do impacto |
| Ata RP nº YYY | Interdependente | Descrição | XX/XX/XXXX | Descrição do impacto |

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 250 e 500 palavras
- Usar tabelas para listar contratações
- Ser específico nas relações identificadas
- Indicar números de contratos quando disponíveis

## IMPORTANTE

- Se NÃO houver contratações correlatas/interdependentes, DECLARE expressamente
- A ausência deve ser JUSTIFICADA
- Considere contratações de todo o órgão, não só do setor demandante
- Considere atas de registro de preços vigentes
- A economia de escala é requisito legal (Art. 18, § 1°, IV)
- Mantenha coerência com as seções anteriores (1 a 10)
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 11 - Contratações Correlatas e/ou Interdependentes
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 11 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- As contratações identificadas devem ser pertinentes
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 11 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 11."""
        super().__init__(
            name="Section11Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_04_content: Optional[str] = None,
        section_07_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 11 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_04_content: Conteúdo da Seção 4 para contexto (opcional)
            section_07_content: Conteúdo da Seção 7 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 11
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 11 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"contratações correlatas interdependentes contratos vigentes ata registro {objective}"
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

        if section_07_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 7 (DESCRIÇÃO DA SOLUÇÃO)\n\n{section_07_content[:500]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação, nas seções anteriores e nos documentos de referência fornecidos,
gere a **Seção 11 - Contratações Correlatas e/ou Interdependentes** do Estudo Técnico Preliminar.

Identifique:
- Contratações correlatas (similares ou complementares)
- Contratações interdependentes (que afetam ou são afetadas por esta contratação)
- Impactos e oportunidades de economia de escala

Se não houver contratações correlatas/interdependentes, declare expressamente e justifique.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 11" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=4096
        )

        self._log_reasoning("Seção 11 gerada com sucesso")

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
        Refina a Seção 11 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 11
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 11
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 11")

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
                query=f"contratações correlatas {feedback[:100]}",
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

        self._log_reasoning("Seção 11 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
