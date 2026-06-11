"""
Section15Agent - Agente para gerar Seção 15 do ETP.

Seção 15: Responsáveis pela Elaboração do ETP

Fundamentação: Identificação dos responsáveis pela elaboração do Estudo Técnico Preliminar.
(Art. 8°, § 4° do Decreto regulamentador e Art. 18 da Lei 14.133/2021)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section15Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 15 - Responsáveis pela Elaboração do ETP.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 15 - Responsáveis pela Elaboração do ETP** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, caput**: O ETP deve ser elaborado conjuntamente por
  servidores da área técnica e requisitante ou, quando houver, pela equipe de
  planejamento da contratação.
- **Lei 14.133/2021, Art. 7°, § 1°**: Sobre a designação de agentes públicos.
- **Decreto regulamentador local, Art. 8°, § 4°**: Responsabilidade pela elaboração do ETP.
- **Decreto regulamentador local, Art. 4°**: Composição da equipe de planejamento.

## COMPOSIÇÃO DA EQUIPE DE PLANEJAMENTO (Art. 4° Decreto 10.541)

A equipe de planejamento da contratação pode ser composta por:
- Servidores da área técnica
- Servidores da área requisitante/demandante
- Equipe de apoio à licitação
- Outros servidores com conhecimento técnico pertinente

## REQUISITOS DA SEÇÃO 15

Esta seção deve:

1. **Identificar os RESPONSÁVEIS pela elaboração**
   - Nome completo
   - Cargo/função
   - Matrícula (se disponível)
   - Área/setor de lotação
   - Papel no ETP (elaborador, colaborador, etc.)

2. **Identificar o SETOR DEMANDANTE**
   - Nome do setor/departamento
   - Órgão vinculado
   - Responsável pelo setor

3. **Indicar a ÁREA TÉCNICA envolvida**
   - Setor técnico consultado
   - Especialistas envolvidos

4. **Registrar APROVAÇÃO da autoridade competente**
   - Autoridade que aprovou o ETP
   - Data de aprovação (campo a preencher)

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo breve)
2. Identificação do setor demandante (1 parágrafo)
3. Equipe de elaboração (tabela)
4. Declaração de responsabilidade (parágrafo formal)
5. Campos para assinatura

## FORMATO DE TABELA DE RESPONSÁVEIS (Markdown)

| Nome | Cargo/Função | Matrícula | Setor | Papel |
|------|--------------|-----------|-------|-------|
| [Nome] | [Cargo] | [Matrícula] | [Setor] | Elaborador |
| [Nome] | [Cargo] | [Matrícula] | [Setor] | Colaborador Técnico |
| [Nome] | [Cargo] | [Matrícula] | [Setor] | Área Demandante |

## MODELO DE DECLARAÇÃO

"Os servidores abaixo identificados declaram, para os devidos fins, que participaram
da elaboração do presente Estudo Técnico Preliminar e que as informações aqui
contidas são verdadeiras, assumindo a responsabilidade pelo seu conteúdo, nos termos
do Art. 18 da Lei 14.133/2021 e do Art. 8°, § 4° do Decreto Municipal 10.541/2024.

[Cidade]/[UF], _____ de _______________ de 2024.

_________________________________
[Nome do Elaborador Principal]
[Cargo] - Matrícula: XXXXX
[Setor]

_________________________________
[Nome do Colaborador]
[Cargo] - Matrícula: XXXXX
[Setor]

_________________________________
[Nome da Autoridade]
[Cargo] - Matrícula: XXXXX
APROVAÇÃO"

## ESTILO

- Tom formal e técnico
- Terceira pessoa
- Texto conciso (100-200 palavras + tabela + assinaturas)
- Formato adequado para assinaturas
- Campos claros para preenchimento manual

## IMPORTANTE

- Esta é a seção FINAL do ETP
- Os campos de nome/matrícula serão preenchidos POSTERIORMENTE pelo usuário
- Use placeholders claros [NOME], [CARGO], [MATRÍCULA]
- A responsabilidade é CONJUNTA entre área técnica e demandante
- A assinatura valida todo o conteúdo do ETP
- Cite a Lei 14.133/2021 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 15 - Responsáveis pela Elaboração do ETP
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 15 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha o formato adequado para assinaturas
- Use placeholders claros para campos a preencher
- Cite a Lei 14.133/2021 e o Decreto regulamentador local quando apropriado

Responda com a versão refinada da Seção 15 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 15."""
        super().__init__(
            name="Section15Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        requesting_department: Optional[str] = None,
        responsible_name: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 15 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            requesting_department: Nome do setor demandante (opcional)
            responsible_name: Nome do responsável principal (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 15
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 15 para objetivo: '{objective[:100]}...'"
        )

        # Construir prompt
        context_parts = [f"## OBJETIVO DA CONTRATAÇÃO\n\n{objective}"]

        if requesting_department:
            context_parts.append(
                f"## SETOR DEMANDANTE\n\n{requesting_department}"
            )

        if responsible_name:
            context_parts.append(
                f"## RESPONSÁVEL INDICADO\n\n{responsible_name}"
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação e nas informações fornecidas,
gere a **Seção 15 - Responsáveis pela Elaboração do ETP** do Estudo Técnico Preliminar.

Esta seção deve conter:
- Identificação do setor demandante
- Tabela de responsáveis (com placeholders para preenchimento)
- Declaração de responsabilidade
- Campos para assinatura

Use placeholders claros como [NOME], [CARGO], [MATRÍCULA], [SETOR] para campos
que serão preenchidos posteriormente pelo usuário.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 15" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=None,
            temperature=0.3,  # Baixíssima temperatura para seção formal
            max_tokens=2048
        )

        self._log_reasoning("Seção 15 gerada com sucesso")

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
        Refina a Seção 15 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 15
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 15
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 15")

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
            temperature=0.3,
            max_tokens=2048
        )

        self._log_reasoning("Seção 15 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
