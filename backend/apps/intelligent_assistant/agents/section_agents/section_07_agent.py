"""
Section07Agent - Agente para gerar Seção 7 do ETP.

Seção 7: Descrição da Solução como um Todo

Fundamentação: Descrição da solução como um todo, inclusive das exigências relacionadas
à manutenção e à assistência técnica, quando for o caso.
(inciso VII do § 1° do art. 18 da Lei 14.133/21 e art. 7° e inciso VII, do § 1° do art. 8°
do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section07Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 7 - Descrição da Solução como um Todo.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 7 - Descrição da Solução como um Todo** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso VII**: Descrição da solução como um todo,
  inclusive das exigências relacionadas à manutenção e à assistência técnica, quando for o caso.
- **Lei 14.133/2021, Art. 7°**: Regulamentação adicional sobre a solução.
- **Decreto regulamentador local, Art. 8°, § 1°, inciso VII**: Mesma fundamentação aplicada ao
  âmbito municipal.

## REQUISITOS DA SEÇÃO 7

Esta seção deve:

1. **Descrever a solução escolhida**
   - Solução que se mostrou mais vantajosa no levantamento de mercado
   - Descrição detalhada do que será contratado
   - Escopo completo da solução

2. **Detalhar componentes da solução**
   - Itens/serviços que compõem a solução
   - Funcionalidades principais
   - Entregas esperadas

3. **Exigências de manutenção (quando aplicável)**
   - Tipo de manutenção necessária
   - Periodicidade
   - Responsabilidades do contratado

4. **Exigências de assistência técnica (quando aplicável)**
   - Suporte técnico necessário
   - Níveis de serviço (SLA)
   - Tempo de resposta
   - Canais de atendimento

5. **Garantias e transferência de conhecimento**
   - Garantias exigidas
   - Treinamentos necessários
   - Documentação técnica

6. **Integração e implantação**
   - Cronograma de implantação
   - Fases do projeto
   - Requisitos de integração

## ESTRUTURA RECOMENDADA

1. Introdução e justificativa da escolha (1-2 parágrafos)
2. Descrição detalhada da solução (2-3 parágrafos)
3. Componentes e entregas (lista ou tabela)
4. Requisitos de manutenção e assistência técnica (1-2 parágrafos)
5. Garantias e suporte (1 parágrafo)
6. Cronograma de implantação (1 parágrafo ou tabela)
7. Conclusão (1 parágrafo)

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 500 e 1000 palavras
- Usar listas e tabelas quando apropriado
- Ser detalhado mas objetivo
- Focar no "como" a solução atenderá a necessidade

## IMPORTANTE

- A solução descrita deve ser coerente com o LEVANTAMENTO DE MERCADO (Seção 5)
- Justifique por que esta solução foi escolhida
- Detalhe o suficiente para subsidiar o Termo de Referência
- NÃO invente funcionalidades ou características
- Mantenha coerência com todas as seções anteriores (1 a 6)
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 7 - Descrição da Solução como um Todo
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 7 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- A solução deve estar alinhada com o levantamento de mercado
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 7 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 7."""
        super().__init__(
            name="Section07Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_03_content: Optional[str] = None,
        section_05_content: Optional[str] = None,
        section_06_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 7 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_03_content: Conteúdo da Seção 3 para contexto (opcional)
            section_05_content: Conteúdo da Seção 5 para contexto (opcional)
            section_06_content: Conteúdo da Seção 6 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 7
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 7 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"solução contratação descrição manutenção assistência técnica {objective}"
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

        if section_05_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 5 (LEVANTAMENTO DE MERCADO)\n\n{section_05_content[:800]}..."
            )

        if section_06_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 6 (ESTIMATIVA DE PREÇO)\n\n{section_06_content[:500]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação, nas seções anteriores e nos documentos de referência fornecidos,
gere a **Seção 7 - Descrição da Solução como um Todo** do Estudo Técnico Preliminar.

Descreva a solução que se mostrou mais vantajosa no levantamento de mercado (Seção 5),
incluindo exigências de manutenção e assistência técnica quando aplicável.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 7" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=5120
        )

        self._log_reasoning("Seção 7 gerada com sucesso")

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
        Refina a Seção 7 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 7
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 7
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 7")

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
                query=f"solução manutenção {feedback[:100]}",
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

        self._log_reasoning("Seção 7 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
