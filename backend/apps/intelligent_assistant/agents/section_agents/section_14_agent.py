"""
Section14Agent - Agente para gerar Seção 14 do ETP.

Seção 14: Publicidade do ETP / Ciência do ETP

Fundamentação: Regras sobre publicidade e disponibilização do ETP.
(Art. 10 do Decreto regulamentador - Publicidade do ETP)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section14Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 14 - Publicidade do ETP / Ciência do ETP.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 14 - Publicidade do ETP / Ciência do ETP** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Decreto regulamentador local, Art. 10**: Dispõe sobre a publicidade do ETP.
- **Lei 14.133/2021, Art. 18, § 2°**: Sobre a disponibilização do ETP.
- **Lei 14.133/2021, Art. 54**: Divulgação de informações da contratação.
- **Lei 12.527/2011 (LAI)**: Lei de Acesso à Informação.

## CONTEÚDO DO ART. 10 DO DECRETO regulamentador local

Art. 10. O ETP deverá ser disponibilizado aos interessados por ocasião da publicação
do edital do certame licitatório ou da contratação direta.

§ 1º O ETP poderá ser classificado como sigiloso, total ou parcialmente, mediante
ato fundamentado da autoridade competente, quando sua divulgação puder prejudicar
a competitividade do certame ou a segurança do órgão ou entidade.

§ 2º Na hipótese de classificação sigilosa, o acesso ao ETP será restrito aos
agentes públicos envolvidos no processo de contratação e aos órgãos de controle.

## REQUISITOS DA SEÇÃO 14

Esta seção deve:

1. **Declarar a forma de publicidade do ETP**
   - Disponibilização integral
   - Disponibilização parcial (com partes sigilosas)
   - Classificação sigilosa total

2. **Se houver SIGILO, justificar**
   - Motivos para classificação sigilosa
   - Partes que serão mantidas em sigilo
   - Prazo do sigilo, se aplicável
   - Fundamentação legal

3. **Indicar meio de disponibilização**
   - Portal de compras
   - Diário Oficial
   - Sistemas eletrônicos
   - Processo administrativo

4. **Registrar ciência dos envolvidos**
   - Equipe de planejamento
   - Área técnica
   - Área demandante
   - Autoridade competente

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo)
2. Forma de publicidade do ETP (1 parágrafo)
3. Informações sobre sigilo (1 parágrafo, se aplicável)
4. Meios de disponibilização (1 parágrafo)
5. Declaração de ciência (parágrafo formal)

## MODELO DE DECLARAÇÃO DE PUBLICIDADE

**Se PUBLICIDADE INTEGRAL:**

"O presente Estudo Técnico Preliminar será disponibilizado integralmente aos
interessados por ocasião da publicação do edital do certame licitatório,
conforme disposto no Art. 10 do Decreto Municipal 10.541/2024.

Não há informações classificadas como sigilosas neste documento.

O ETP estará disponível:
- No Portal de Compras do Governo Federal (Compras.gov.br)
- No Portal da Transparência do Município
- Nos autos do processo administrativo"

**Se PUBLICIDADE COM SIGILO PARCIAL:**

"O presente Estudo Técnico Preliminar será disponibilizado aos interessados
por ocasião da publicação do edital, EXCETO as seguintes partes que foram
classificadas como sigilosas:
- [parte sigilosa 1]
- [parte sigilosa 2]

JUSTIFICATIVA DO SIGILO: [fundamentação]

Fundamentação: Art. 10, § 1° do Decreto Municipal 10.541/2024."

## ESTILO

- Tom técnico e formal
- Terceira pessoa
- Texto entre 150 e 300 palavras
- Ser objetivo e claro
- Indicar precisamente as regras de publicidade

## IMPORTANTE

- A REGRA é a publicidade integral (transparência)
- O sigilo é EXCEÇÃO e deve ser JUSTIFICADO
- A classificação sigilosa requer ato fundamentado da autoridade competente
- Orçamento sigiloso tem tratamento específico (Art. 24 Lei 14.133/2021)
- Mantenha coerência com as seções anteriores
- Cite o Decreto regulamentador local e a Lei 14.133/2021"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 14 - Publicidade do ETP
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 14 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- A publicidade é regra, sigilo é exceção
- Cite o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 14 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 14."""
        super().__init__(
            name="Section14Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_06_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 14 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_06_content: Conteúdo da Seção 6 para verificar sigilo de orçamento (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 14
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 14 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"publicidade ETP sigilo disponibilização transparência {objective}"
        context_docs = self._get_context_from_kb(
            collection_name=collection_name,
            query=query_for_kb,
            n_results=3
        )

        # Construir prompt
        context_parts = [f"## OBJETIVO DA CONTRATAÇÃO\n\n{objective}"]

        if section_06_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 6 (ESTIMATIVA DE PREÇO)\n\n{section_06_content[:400]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação e nos documentos de referência fornecidos,
gere a **Seção 14 - Publicidade do ETP / Ciência do ETP** do Estudo Técnico Preliminar.

Defina:
- Forma de publicidade do ETP (integral ou com sigilo)
- Se houver sigilo, justifique
- Meios de disponibilização
- Declaração formal de publicidade

A regra é a publicidade integral. Sigilo somente se houver justificativa.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 14" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.4,  # Baixa temperatura para seção formal
            max_tokens=2048
        )

        self._log_reasoning("Seção 14 gerada com sucesso")

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
        Refina a Seção 14 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 14
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 14
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 14")

        # Construir prompt de refinamento
        system_prompt = self.SYSTEM_PROMPT
        user_prompt = self.REFINE_PROMPT_TEMPLATE.format(
            previous_content=previous_content,
            feedback=feedback
        )

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            context_documents=None,
            temperature=0.4,
            max_tokens=2048
        )

        self._log_reasoning("Seção 14 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
