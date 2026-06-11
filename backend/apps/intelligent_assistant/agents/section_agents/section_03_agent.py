"""
Section03Agent - Agente para gerar Seção 3 do ETP.

Seção 3: Requisitos da Contratação

Fundamentação: Descrição dos requisitos necessários e suficientes à escolha da solução.
(inciso III do § 1° do art. 18 da Lei 14.133/2021 e inciso III, do § 1° do art. 8° do Decreto
regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section03Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 3 - Requisitos da Contratação.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 3 - Requisitos da Contratação** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso III**: Descrição dos requisitos necessários e
  suficientes à escolha da solução.
- **Decreto regulamentador local, Art. 8°, § 1°, inciso III**: Mesma fundamentação aplicada ao
  âmbito municipal.

## REQUISITOS DA SEÇÃO 3

Esta seção deve:

1. **Listar requisitos ESSENCIAIS da contratação**
   - Requisitos técnicos obrigatórios
   - Requisitos funcionais mínimos
   - Requisitos de qualidade
   - Requisitos de desempenho

2. **Examinar normativos aplicáveis**
   - Legislação específica do objeto
   - Normas técnicas (ABNT, ISO, etc.)
   - Regulamentos setoriais
   - Instruções normativas

3. **Destacar práticas de SUSTENTABILIDADE**
   - Dimensão ambiental (materiais, energia, resíduos)
   - Dimensão social (acessibilidade, inclusão)
   - Dimensão econômica (eficiência, durabilidade)

4. **Evitar restrições indevidas**
   - NÃO incluir requisitos desnecessários
   - NÃO fazer especificações excessivas
   - PRESERVAR o caráter competitivo da licitação

## ESTRUTURA RECOMENDADA

1. Introdução sobre os requisitos da contratação (1 parágrafo)
2. Requisitos técnicos essenciais (lista ou parágrafos)
3. Requisitos funcionais (lista ou parágrafos)
4. Normativos aplicáveis (lista com referências)
5. Práticas de sustentabilidade (1-2 parágrafos)
6. Conclusão (1 parágrafo)

## CATEGORIAS DE REQUISITOS

**Requisitos Técnicos:**
- Especificações técnicas mínimas
- Compatibilidade com sistemas existentes
- Padrões de qualidade exigidos
- Certificações necessárias

**Requisitos Funcionais:**
- O que o objeto deve fazer/entregar
- Funcionalidades obrigatórias
- Capacidades mínimas

**Requisitos de Qualificação:**
- Experiência mínima do fornecedor
- Capacidade técnica e operacional
- Certidões e documentos obrigatórios

**Requisitos de Sustentabilidade:**
- Eficiência energética
- Materiais recicláveis ou sustentáveis
- Destinação adequada de resíduos
- Logística reversa (quando aplicável)

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 400 e 800 palavras
- Usar listas quando apropriado
- Citar normas e legislação aplicável
- Ser específico mas não restritivo

## ALINHAMENTO COM LEI 14.133/2021

- Art. 18, § 1°, III: requisitos necessários e suficientes
- Art. 6°, XXIII: especificações técnicas
- Art. 11: objetivos de desenvolvimento nacional sustentável

## IMPORTANTE

- Use APENAS informações fornecidas no contexto e no objetivo
- NÃO invente normas ou legislações específicas
- Liste requisitos REALISTAS para o tipo de contratação
- Mantenha coerência com as Seções 1 e 2
- EVITE requisitos que possam frustrar a competição
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 3 - Requisitos da Contratação
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 3 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- NÃO adicione requisitos restritivos demais
- Mantenha coerência com as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 3 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 3."""
        super().__init__(
            name="Section03Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_02_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 3 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_02_content: Conteúdo da Seção 2 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 3
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 3 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"requisitos contratação especificações técnicas sustentabilidade {objective}"
        context_docs = self._get_context_from_kb(
            collection_name=collection_name,
            query=query_for_kb,
            n_results=5
        )

        # Construir prompt com contexto das seções anteriores
        context_parts = [f"## OBJETIVO DA CONTRATAÇÃO\n\n{objective}"]

        if section_01_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 1 (DESCRIÇÃO DA NECESSIDADE)\n\n{section_01_content[:800]}..."
            )

        if section_02_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 2 (PREVISÃO NO PAC)\n\n{section_02_content[:500]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação e nos documentos de referência fornecidos,
gere a **Seção 3 - Requisitos da Contratação** do Estudo Técnico Preliminar.

Liste os requisitos ESSENCIAIS, evitando especificações excessivas que possam
frustrar o caráter competitivo da futura licitação.

Destaque as práticas de sustentabilidade nas dimensões ambiental, social e econômica.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 3" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=4096
        )

        self._log_reasoning("Seção 3 gerada com sucesso")

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
        Refina a Seção 3 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 3
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 3
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 3")

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
                query=f"requisitos {feedback[:100]}",
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

        self._log_reasoning("Seção 3 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
