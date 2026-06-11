"""
Section12Agent - Agente para gerar Seção 12 do ETP.

Seção 12: Impactos Ambientais

Fundamentação: Descrição de possíveis impactos ambientais e respectivas medidas de
tratamento ou mitigadoras, incluídos requisitos de baixo consumo de energia e de outros
recursos, bem como logística reversa para desfazimento e reciclagem de bens e refugos,
quando aplicável.
(inciso XII do § 1° do art. 18 da Lei 14.133/21 e inciso XII, do § 1° do art. 8° do Decreto regulamentador local)
"""
import logging
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section12Agent(BaseAgent):
    """
    Agente responsável por gerar a Seção 12 - Impactos Ambientais.

    Implementa o padrão Template Method herdado de BaseAgent.
    """

    SYSTEM_PROMPT = """Você é um especialista em elaboração de Estudos Técnicos Preliminares (ETPs)
para licitações públicas, com profundo conhecimento da Lei 14.133/2021 (Nova Lei de Licitações)
e do Decreto Municipal 10.541/2024 do órgão contratante.

Sua tarefa é gerar a **Seção 12 - Impactos Ambientais** de um ETP.

## FUNDAMENTAÇÃO LEGAL

- **Lei 14.133/2021, Art. 18, § 1°, inciso XII**: Descrição de possíveis impactos ambientais
  e respectivas medidas de tratamento ou mitigadoras.
- **Lei 14.133/2021, Art. 11, inciso IV**: Desenvolvimento nacional sustentável como objetivo.
- **Lei 14.133/2021, Art. 26**: Critérios de sustentabilidade nas compras públicas.
- **Lei 12.305/2010**: Política Nacional de Resíduos Sólidos (logística reversa).
- **Decreto regulamentador local, Art. 8°, § 1°, inciso XII**: Mesma fundamentação aplicada ao
  âmbito municipal.
- **IN SLTI/MPOG 1/2010**: Contratações públicas sustentáveis.

## REQUISITOS DA SEÇÃO 12

Esta seção deve:

1. **Identificar IMPACTOS AMBIENTAIS potenciais**
   - Geração de resíduos
   - Consumo de recursos naturais
   - Emissões atmosféricas
   - Impactos no solo e água
   - Consumo energético

2. **Descrever MEDIDAS DE TRATAMENTO/MITIGAÇÃO**
   - Medidas preventivas
   - Medidas corretivas
   - Compensações ambientais
   - Tecnologias mais limpas

3. **Considerar EFICIÊNCIA ENERGÉTICA**
   - Requisitos de baixo consumo
   - Certificações (PROCEL, CONPET)
   - Fontes alternativas de energia
   - Equipamentos eficientes

4. **Abordar LOGÍSTICA REVERSA (quando aplicável)**
   - Responsabilidade pelo desfazimento
   - Reciclagem de materiais
   - Destinação de resíduos
   - Acordo setorial

5. **Considerar CRITÉRIOS DE SUSTENTABILIDADE**
   - Selo Verde/certificações ambientais
   - Materiais reciclados/recicláveis
   - Produção sustentável
   - Redução de embalagens

## ESTRUTURA RECOMENDADA

1. Introdução e fundamentação legal (1 parágrafo)
2. Impactos ambientais identificados (1-2 parágrafos ou tabela)
3. Medidas de tratamento/mitigação (1-2 parágrafos)
4. Requisitos de eficiência energética (1 parágrafo)
5. Logística reversa e desfazimento (1 parágrafo)
6. Critérios de sustentabilidade aplicáveis (1 parágrafo)
7. Conclusão (1 parágrafo)

## FORMATO DE TABELA (Markdown)

| Impacto Ambiental | Gravidade | Medida Mitigadora | Responsável |
|-------------------|-----------|-------------------|-------------|
| Geração de resíduos | Média | Destinação adequada | Contratada |
| Consumo energético | Baixa | Equipamentos PROCEL A | Contratante |

## CATEGORIAS DE OBJETOS E SEUS IMPACTOS TÍPICOS

**Serviços de TI:**
- Consumo de energia (datacenters)
- Resíduos eletrônicos (logística reversa)
- Emissão de calor

**Aquisição de Equipamentos:**
- Obsolescência e descarte
- Consumo energético
- Embalagens

**Obras e Serviços de Engenharia:**
- Resíduos da construção civil
- Impacto no solo
- Emissões e ruídos

**Serviços Gerais:**
- Uso de produtos químicos
- Geração de efluentes
- Consumo de recursos

## ESTILO

- Tom técnico e objetivo
- Terceira pessoa
- Texto entre 300 e 600 palavras
- Usar tabelas para impactos e medidas
- Citar normas e certificações
- Ser específico nas medidas

## IMPORTANTE

- Considere o CICLO DE VIDA do objeto (aquisição, uso, descarte)
- A sustentabilidade é PRINCÍPIO da Lei 14.133/2021
- Logística reversa é OBRIGATÓRIA para alguns produtos (Lei 12.305/2010)
- Se não houver impactos significativos, DECLARE e JUSTIFIQUE
- Mantenha coerência com as seções anteriores (1 a 11)
- Cite a Lei 14.133/2021, Lei 12.305/2010 e o Decreto regulamentador local"""

    REFINE_PROMPT_TEMPLATE = """Você está refinando a Seção 12 - Impactos Ambientais
de um ETP baseado no feedback da validação.

## CONTEÚDO ANTERIOR

{previous_content}

## FEEDBACK DA VALIDAÇÃO

{feedback}

## TAREFA

Refine a Seção 12 corrigindo os problemas apontados no feedback.

IMPORTANTE:
- Mantenha o que estava bom
- Corrija APENAS os problemas críticos e avisos mencionados
- Mantenha a estrutura e o estilo técnico
- Os impactos e medidas devem ser pertinentes ao objeto
- Mantenha coerência com as seções anteriores
- Cite a legislação ambiental quando apropriado

Responda com a versão refinada da Seção 12 completa."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o agente da Seção 12."""
        super().__init__(
            name="Section12Agent",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        section_01_content: Optional[str] = None,
        section_03_content: Optional[str] = None,
        section_07_content: Optional[str] = None
    ) -> Dict:
        """
        Gera a Seção 12 do ETP.

        Args:
            objective: Objetivo da contratação
            collection_name: Nome da collection na KB (opcional)
            section_01_content: Conteúdo da Seção 1 para contexto (opcional)
            section_03_content: Conteúdo da Seção 3 para contexto (opcional)
            section_07_content: Conteúdo da Seção 7 para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto da Seção 12
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning(
            f"Iniciando geração da Seção 12 para objetivo: '{objective[:100]}...'"
        )

        # Buscar contexto da KB
        query_for_kb = f"impactos ambientais sustentabilidade logística reversa eficiência energética {objective}"
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

        if section_03_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 3 (REQUISITOS DA CONTRATAÇÃO)\n\n{section_03_content[:500]}..."
            )

        if section_07_content:
            context_parts.append(
                f"## CONTEXTO DA SEÇÃO 7 (DESCRIÇÃO DA SOLUÇÃO)\n\n{section_07_content[:600]}..."
            )

        context_parts.append("""## TAREFA

Com base no objetivo da contratação, nas seções anteriores e nos documentos de referência fornecidos,
gere a **Seção 12 - Impactos Ambientais** do Estudo Técnico Preliminar.

Descreva:
- Possíveis impactos ambientais da contratação
- Medidas de tratamento ou mitigação
- Requisitos de eficiência energética e baixo consumo
- Logística reversa para desfazimento (quando aplicável)
- Critérios de sustentabilidade

Se não houver impactos ambientais significativos, declare expressamente e justifique.

Siga rigorosamente os requisitos e a estrutura indicados no prompt de sistema.

Comece diretamente com o texto da seção, sem incluir o título "Seção 12" ou numeração.""")

        user_prompt = "\n\n".join(context_parts)

        # Chamar Claude
        response = self._call_claude(
            user_prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            context_documents=context_docs,
            temperature=0.6,
            max_tokens=4096
        )

        self._log_reasoning("Seção 12 gerada com sucesso")

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
        Refina a Seção 12 baseado no feedback da validação.

        Args:
            previous_content: Conteúdo anterior da Seção 12
            feedback: Feedback da validação (erros, avisos, sugestões)
            collection_name: Nome da collection na KB (opcional)

        Returns:
            Dict contendo:
                - content: Texto refinado da Seção 12
                - reasoning: Lista de raciocínios
                - usage: Estatísticas de tokens
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando refinamento da Seção 12")

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
                query=f"impactos ambientais sustentabilidade {feedback[:100]}",
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

        self._log_reasoning("Seção 12 refinada com sucesso")

        return {
            'content': response['content'],
            'reasoning': self.get_reasoning_log(),
            'usage': response['usage']
        }
