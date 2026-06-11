"""
Section10Agent - Agente para gerar Seção 10 do ETP.

Seção 10: Providências Prévias ao Contrato

Fundamentação: Providências a serem adotadas pela administração previamente à celebração
do contrato, inclusive quanto à capacitação de servidores ou de empregados para fiscalização
e gestão contratual ou adequação do ambiente da organização.
(inciso X do § 1° do art. 18 da Lei 14.133/21 e inciso X, do § 1° do art. 8° do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section10Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 10 - Providências Prévias ao Contrato.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 10 - Providências Prévias ao Contrato** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso X**: Providências a serem adotadas pela administração
  previamente à celebração do contrato, inclusive quanto à capacitação de servidores ou de
  empregados para fiscalização e gestão contratual ou adequação do ambiente da organização.
- **Lei 14.133/2021, Art. 117**: Fiscalização e gestão do contrato.
- **Decreto regulamentador local, Art. 8°, § 1°, inciso X**: Mesma fundamentação aplicada ao
  âmbito municipal.

## REQUISITOS DA SEÇÃO 10

Esta seção deve:

1. **Identificar providências de CAPACITAÇÃO**
   - Treinamentos necessários para gestores
   - Treinamentos necessários para fiscais
   - Conhecimentos técnicos específicos
   - Capacitação em sistemas ou ferramentas

2. **Identificar providências de INFRAESTRUTURA**
   - Adequação de espaço físico
   - Aquisição de equipamentos
   - Instalações necessárias
   - Preparação de ambiente

3. **Identificar providências ADMINISTRATIVAS**
   - Designação de gestores e fiscais
   - Elaboração de procedimentos internos
   - Criação de fluxos de trabalho
   - Documentação necessária

4. **Identificar providências TÉCNICAS**
   - Sistemas de TI a serem preparados
   - Integrações necessárias
   - Testes e homologações
   - Adequações de processos

5. **Definir cronograma de providências**
   - Sequência de ações
   - Prazos estimados
   - Responsáveis por cada ação
   - Marcos importantes

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo)
2. Providências de capacitação (1-2 parágrafos)
3. Providências de infraestrutura (1-2 parágrafos)
4. Providências administrativas (1-2 parágrafos)
5. Providências técnicas (1 parágrafo, se aplicável)
6. Cronograma de providências (tabela)
7. Conclusão (1 parágrafo)

## FORMATO DE TABELA DE PROVIDÊNCIAS (Markdown)

| Providência | Descrição | Responsável | Prazo |
|-------------|-----------|-------------|-------|
| Capacitação de fiscais | Treinamento em gestão contratual | SEAD | Antes da assinatura |
| Adequação de espaço | Preparação de sala | Setor Demandante | 30 dias |
| Designação de equipe | Portaria de designação | Autoridade Competente | 15 dias |

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 300 e 600 palavras
- Usar tabelas para cronograma
- Ser específico nas providências
- Indicar responsáveis quando possível

## IMPORTANTE

- As providências devem ser REALIZÁVEIS antes da contratação
- Considere o tempo necessário para cada providência
- A fiscalização é OBRIGATÓRIA (Art. 117 da Lei 14.133/2021)
- Se não houver providências necessárias, JUSTIFIQUE
- Mantenha coerência com as seções anteriores (1 a 9)
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 10 - Providências Prévias ao Contrato
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 10 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- As providências devem ser realizáveis
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 10 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 10."""
        super().__init__(
            name="Section10Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_07_content: Optional[str] = None,
        section_09_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 10 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_07_content: Conteúdo da Seção 7 para contexto (opcional)
            section_09_content: Conteúdo da Seção 9 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 10
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 10 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"providências prévias capacitação fiscalização gestão contrato {objective}"
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

        if section_07_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 7 (DESCRIÇÃO DA SOLUÇÃO)\n\n{section_07_content[:600]}..."
            )

        if section_09_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 9 (RESULTADOS PRETENDIDOS)\n\n{section_09_content[:500]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação, nas seções anteriores e nos documentos de referência fornecidos,
gere a **Seção 10 - Providências Prévias ao Contrato** do Estudo Técnico Preliminar.

Identifique as providências necessárias antes da celebração do contrato:
- Capacitação de servidores
- Adequação de infraestrutura
- Providências administrativas
- Providências técnicas

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 10" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=4096
        )

        self._log_reasoning("Seção 10 gerada com sucesso")

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
        Refina a Seção 10 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 10
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 10
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 10")

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
                query=f"providências capacitação {feedback[:100]}",
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

        self._log_reasoning("Seção 10 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
