"""
Section01Agent - Agente gerador da Seção 1 do ETP.

Seção 1: Descrição da Necessidade da Contratação

Responsável por gerar a primeira seção do Estudo Técnico Preliminar,
descrevendo a necessidade que justifica a contratação.
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section01Agent(BaseAgent):
    """
    Agente gerador da Seção 1 - Descrição da Necessidade da Contratação.

    Esta seção deve:
    - Descrever claramente a necessidade que justifica a contratação
    - Contextualizar o problema ou demanda
    - Explicar por que a contratação é necessária
    - Estar alinhada com a Lei 14.133/2021
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (Documents)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações).

Sua tarefa é gerar a **Seção 1 - Descrição da Necessidade da Contratação** de um ETP.

## REQUISITOS DA SEÇÃO 1

Esta seção deve:

1. **Descrever a necessidade de forma clara e objetiva**
   - Qual é o problema ou demanda que motiva a contratação?
   - Por que esta contratação é necessária?
   - Qual é o contexto institucional?

2. **Justificar a relevância**
   - Por que é importante para a administração pública?
   - Quais impactos a ausência desta contratação pode causar?

3. **Estar alinhada com a Lei 14.133/2021**
   - Art. 18, § 1º: necessidade da contratação
   - Art. 18, § 2º: objeto a ser contratado

4. **Ser concisa mas completa**
   - Texto entre 300 e 800 palavras
   - Linguagem técnica mas acessível
   - Sem repetições ou redundâncias

## ESTRUTURA RECOMENDADA

1. Contextualização inicial (1-2 parágrafos)
2. Descrição detalhada da necessidade (2-3 parágrafos)
3. Justificativa da relevância (1-2 parágrafos)
4. Conclusão sintética (1 parágrafo)

## ESTILO

- Tom formal e técnico
- Terceira pessoa
- Tempos verbais: presente para contexto, futuro para expectativas
- Evitar jargões desnecessários
- Preferir verbos de ação

## IMPORTANTE

- Use APENAS informações fornecidas no contexto e no objetivo
- NÃO invente dados, valores ou detalhes técnicos
- Se houver informações insuficientes, seja genérico mas correto
- Cite a Lei 14.133/2021 quando apropriado"""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 1."""
        super().__init__(
            name="Section01Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: str,
        additional_context: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Gera a Seção 1 do ETP.

        Args:
            objective: Objetivo da contratação fornecido pelo usuário
            collection_name: ID da sessão (UUID) para buscar embeddings no PgVector
            additional_context: Contexto adicional (opcional)
            temperature: Temperatura para geração (0.0 a 1.0)

        Returns:
            Dict contendo:
                - content: Conteúdo gerado da seção
                - reasoning: Raciocínio do agente
                - usage: Informações de uso de tokens
                - metadata: Metadados da geração
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 1 para objetivo: '{objective[:100]}...'")

        # 1. Buscar documentos relevantes na KB
        query_for_kb = f"descrição da necessidade da contratação {objective}"
        context_docs = self._get_context_from_kb(
            collection_name=collection_name,
            query=query_for_kb,
            n_results=5
        )

        # 2. Montar prompt do usuário
        user_prompt = self._build_user_prompt(
            objective=objective,
            additional_context=additional_context
        )

        # 3. Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs if context_docs else None,
            temperature=temperature,
            max_tokens=4096
        )

        # 4. Extrair thinking e conteúdo
        thinking, clean_content = self._extract_thinking_from_response(
            response['content']
        )

        self._log_reasoning("Seção 1 gerada com sucesso")

        # 5. Montar resultado
        return {
            'content': clean_content,
            'reasoning': self.get_reasoning_log(),
            'thinking': thinking,
            'usage': response['usage'],
            'metadata': {
                'section_number': 1,
                'section_name': 'Descrição da Necessidade da Contratação',
                'temperature': temperature,
                'context_docs_used': len(context_docs),
                'model': response['model']
            }
        }

    def _build_user_prompt(
        self,
        objective: str,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Constrói o prompt do usuário para a geração.

        Args:
            objective: Objetivo da contratação
            additional_context: Contexto adicional

        Returns:
            Prompt formatado
        """
        prompt = f"""## OBJETIVO DA CONTRATAÇÃO

{objective}
"""

        if additional_context:
            prompt += f"""
## CONTEXTO ADICIONAL

{additional_context}
"""

        prompt += """
## TAREFA

Com base no objetivo da contratação e nos documentos de referência fornecidos,
gere a **Seção 1 - Descrição da Necessidade da Contratação** do Estudo Técnico Preliminar.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 1" ou numeração.
"""

        return prompt

    def refine(
        self,
        previous_content: str,
        feedback: str,
        collection_name: str,
        temperature: float = 0.6
    ) -> Dict:
        """
        Refina uma versão anterior da Seção 1 com base em feedback.

        Args:
            previous_content: Conteúdo anterior gerado
            feedback: Feedback do validador ou usuário
            collection_name: ID da sessão (UUID) para buscar embeddings no PgVector
            temperature: Temperatura (mais baixa para refinamento)

        Returns:
            Dict com conteúdo refinado
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 1")

        # Buscar contexto relevante para o refinamento
        context_docs = self._get_context_from_kb(
            collection_name=collection_name,
            query=f"necessidade da contratação {feedback}",
            n_results=3
        )

        # Montar prompt de refinamento
        user_prompt = f"""## VERSÃO ANTERIOR

{previous_content}

## FEEDBACK PARA MELHORIA

{feedback}

## TAREFA

Refine a Seção 1 incorporando o feedback fornecido.
Mantenha a estrutura e qualidade, mas corrija os pontos indicados.

Retorne APENAS o texto refinado da seção, sem comentários adicionais.
"""

        # Chamar Claude com temperatura mais baixa
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs if context_docs else None,
            temperature=temperature,
            max_tokens=4096
        )

        # Extrair conteúdo
        thinking, clean_content = self._extract_thinking_from_response(
            response['content']
        )

        self._log_reasoning("Refinamento concluído")

        return {
            'content': clean_content,
            'reasoning': self.get_reasoning_log(),
            'thinking': thinking,
            'usage': response['usage'],
            'metadata': {
                'section_number': 1,
                'section_name': 'Descrição da Necessidade da Contratação',
                'temperature': temperature,
                'is_refinement': True,
                'model': response['model']
            }
        }
