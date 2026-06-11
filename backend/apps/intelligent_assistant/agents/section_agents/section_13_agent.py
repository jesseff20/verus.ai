"""
Section13Agent - Agente para gerar Seção 13 do ETP.

Seção 13: Viabilidade da Contratação / Declaração de Viabilidade

Fundamentação: Posicionamento conclusivo sobre a adequação da contratação para o
atendimento da necessidade a que se destina.
(incisos XIII e XIV do § 1° do art. 18 da Lei 14.133/21 e incisos XIII e XIV do § 1° do art. 8°
do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section13Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 13 - Viabilidade da Contratação.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 13 - Viabilidade da Contratação / Declaração de Viabilidade** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso XIII**: Posicionamento conclusivo sobre a
  adequação da contratação para o atendimento da necessidade a que se destina.
- **Lei 14.133/2021, Art. 18, § 1°, inciso XIV**: Declaração de viabilidade ou não
  da contratação.
- **Decreto regulamentador local, Art. 8°, § 1°, incisos XIII e XIV**: Mesma fundamentação
  aplicada ao âmbito municipal.

## REQUISITOS DA SEÇÃO 13

Esta seção deve:

1. **Avaliar VIABILIDADE TÉCNICA**
   - A solução atende aos requisitos técnicos?
   - Há fornecedores capazes de executar?
   - O prazo é realizável?
   - A tecnologia está disponível?

2. **Avaliar VIABILIDADE ECONÔMICA**
   - O custo estimado é compatível com o orçamento?
   - A relação custo-benefício é adequada?
   - Há recursos orçamentários disponíveis?
   - Os preços estão compatíveis com o mercado?

3. **Avaliar VIABILIDADE LEGAL**
   - Há amparo legal para a contratação?
   - Os requisitos atendem à legislação vigente?
   - Há impedimentos legais identificados?

4. **Avaliar VIABILIDADE OPERACIONAL**
   - A administração tem capacidade de gestão?
   - Há estrutura para fiscalização?
   - Os riscos estão mapeados e tratáveis?

5. **Emitir POSICIONAMENTO CONCLUSIVO**
   - Declarar se a contratação é VIÁVEL ou NÃO
   - Fundamentar a decisão
   - Indicar ressalvas ou condicionantes, se houver

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo)
2. Análise da viabilidade técnica (1-2 parágrafos)
3. Análise da viabilidade econômica (1-2 parágrafos)
4. Análise da viabilidade legal (1 parágrafo)
5. Análise da viabilidade operacional (1 parágrafo)
6. Posicionamento conclusivo (1-2 parágrafos)
7. Declaração de Viabilidade (parágrafo formal)

## FORMATO DA DECLARAÇÃO DE VIABILIDADE

**Se VIÁVEL:**

"Diante do exposto, DECLARAMOS que a contratação objeto deste Estudo Técnico Preliminar
é VIÁVEL, uma vez que: (i) atende à necessidade da Administração; (ii) a solução proposta
é tecnicamente adequada; (iii) o custo estimado é compatível com o orçamento disponível;
e (iv) não há impedimentos legais identificados.

Assim, recomenda-se o prosseguimento do processo de contratação, com a elaboração do
respectivo Termo de Referência."

**Se NÃO VIÁVEL:**

"Diante do exposto, DECLARAMOS que a contratação objeto deste Estudo Técnico Preliminar
NÃO É VIÁVEL pelos seguintes motivos: [listar motivos].

Recomenda-se [alternativa ou ação a ser adotada]."

## FORMATO DE TABELA RESUMO (Markdown)

| Dimensão | Avaliação | Observações |
|----------|-----------|-------------|
| Viabilidade Técnica | Viável/Inviável | ... |
| Viabilidade Econômica | Viável/Inviável | ... |
| Viabilidade Legal | Viável/Inviável | ... |
| Viabilidade Operacional | Viável/Inviável | ... |
| **CONCLUSÃO** | **VIÁVEL/INVIÁVEL** | ... |

## ESTILO

- Tom técnico e conclusivo
- Terceira pessoa
- Texto entre 400 e 700 palavras
- Usar tabela resumo
- Ser objetivo na análise
- Declaração formal ao final

## IMPORTANTE

- Esta seção é CONCLUSIVA do ETP
- A declaração deve ser FUNDAMENTADA em todo o estudo
- Se houver ressalvas, indique claramente
- A viabilidade depende de TODAS as dimensões
- Mantenha coerência com TODAS as seções anteriores (1 a 12)
- Esta seção determina se o processo segue ou não
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 13 - Viabilidade da Contratação
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 13 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- A declaração deve ser clara e fundamentada
- Mantenha coerência com todas as seções anteriores
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 13 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 13."""
        super().__init__(
            name="Section13Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_06_content: Optional[str] = None,
        section_07_content: Optional[str] = None,
        section_09_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 13 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_06_content: Conteúdo da Seção 6 para contexto (opcional)
            section_07_content: Conteúdo da Seção 7 para contexto (opcional)
            section_09_content: Conteúdo da Seção 9 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 13
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 13 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"viabilidade contratação declaração adequação necessidade {objective}"
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

        if section_09_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 9 (RESULTADOS PRETENDIDOS)\n\n{section_09_content[:500]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação, nas seções anteriores e nos documentos de referência fornecidos,
gere a **Seção 13 - Viabilidade da Contratação / Declaração de Viabilidade** do Estudo Técnico Preliminar.

Analise a viabilidade nas dimensões:
- Técnica
- Econômica
- Legal
- Operacional

Emita posicionamento conclusivo e a declaração formal de viabilidade (ou inviabilidade).

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 13" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.5,  # Menor temperatura para seção conclusiva
            max_tokens=4096
        )

        self._log_reasoning("Seção 13 gerada com sucesso")

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
        Refina a Seção 13 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 13
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 13
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 13")

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
                query=f"viabilidade declaração {feedback[:100]}",
                n_results=3
            )

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            context_documents=context_docs,
            temperature=0.4,
            max_tokens=4096
        )

        self._log_reasoning("Seção 13 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
