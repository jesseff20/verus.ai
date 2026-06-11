"""
ETP Nodes - Funções de nó para o grafo LangGraph.

Define os nós de geração e validação para cada uma das 15 seções.
"""
import logging
from typing import Dict, Any, Callable
from datetime import datetime

from apps.intelligent_assistant.agents.etp_graph.state import (
    ETPState, SectionStatus, get_section_key, get_section_name
)
from apps.intelligent_assistant.utils import strip_generation_suffix
from apps.intelligent_assistant.agents.section_agents import (
    Section01Agent, Section02Agent, Section03Agent, Section04Agent,
    Section05Agent, Section06Agent, Section07Agent, Section08Agent,
    Section09Agent, Section10Agent, Section11Agent, Section12Agent,
    Section13Agent, Section14Agent, Section15Agent, SECTION_AGENTS
)
from apps.intelligent_assistant.agents.validators import (
    Section01Validator, Section02Validator, Section03Validator,
    Section04Validator, Section05Validator, Section06Validator,
    Section07Validator, Section08Validator, Section09Validator,
    Section10Validator, Section11Validator, Section12Validator,
    Section13Validator, Section14Validator, Section15Validator,
    SECTION_VALIDATORS
)

logger = logging.getLogger(__name__)


class ETPNodes:
    """
    Classe que encapsula os nós do grafo ETP.

    Gerencia a injeção de dependências (claude_service, kb_service)
    e fornece as funções de nó para geração e validação.
    """

    def __init__(self, claude_service, kb_service):
        """
        Inicializa os nós com os serviços necessários.

        Args:
            claude_service: Serviço de comunicação com Claude API
            kb_service: Serviço de Knowledge Base (PgVector)
        """
        self.claude_service = claude_service
        self.kb_service = kb_service

        # Inicializa agentes de geração
        self.generators = {}
        for num, agent_class in SECTION_AGENTS.items():
            self.generators[num] = agent_class(claude_service, kb_service)

        # Inicializa validadores
        self.validators = {}
        for num, validator_class in SECTION_VALIDATORS.items():
            self.validators[num] = validator_class(claude_service, kb_service)

    def _generate_section(self, state: ETPState, section_num: int) -> ETPState:
        """
        Gera o conteúdo de uma seção específica.

        Args:
            state: Estado atual do grafo
            section_num: Número da seção (1-15)

        Returns:
            Estado atualizado
        """
        section_key = get_section_key(section_num)
        section_name = get_section_name(section_num)
        now = datetime.utcnow().isoformat()

        # Verifica se a seção deve ser gerada
        sections_to_generate = state.get("sections_to_generate", list(range(1, 16)))
        if section_num not in sections_to_generate:
            logger.info(f"Pulando geração da seção {section_num}: {section_name} (não selecionada)")
            state[section_key]["status"] = "skipped"
            state[section_key]["last_updated"] = now
            return state

        logger.info(f"Gerando seção {section_num}: {section_name}")

        # Atualiza status para "generating"
        state[section_key]["status"] = SectionStatus.GENERATING
        state[section_key]["generation_attempts"] += 1
        state["updated_at"] = now

        try:
            # Gera conteúdo usando o agente específico
            generator = self.generators.get(section_num)
            if not generator:
                raise ValueError(f"Agente não encontrado para seção {section_num}")

            # Chama generate com parâmetros que o agente aceita
            result = generator.generate(
                objective=state["objective"],
                collection_name=state.get("collection_name") or "default"
            )

            # Atualiza estado com conteúdo gerado
            state[section_key]["content"] = result.get("content", "")
            state[section_key]["status"] = SectionStatus.VALIDATING
            state[section_key]["last_updated"] = now
            state[section_key]["error_message"] = None

            logger.info(f"Seção {section_num} gerada com sucesso")

        except Exception as e:
            logger.error(f"Erro ao gerar seção {section_num}: {str(e)}")
            state[section_key]["status"] = SectionStatus.ERROR
            state[section_key]["error_message"] = str(e)
            state["errors"].append(f"Seção {section_num}: {str(e)}")

        return state

    def _validate_section(self, state: ETPState, section_num: int) -> ETPState:
        """
        Valida o conteúdo de uma seção específica.

        Args:
            state: Estado atual do grafo
            section_num: Número da seção (1-15)

        Returns:
            Estado atualizado
        """
        section_key = get_section_key(section_num)
        section_name = get_section_name(section_num)
        now = datetime.utcnow().isoformat()

        # Verifica se a seção deve ser validada (se foi pulada, pula validação também)
        sections_to_generate = state.get("sections_to_generate", list(range(1, 16)))
        if section_num not in sections_to_generate:
            logger.info(f"Pulando validação da seção {section_num}: {section_name} (não selecionada)")
            return state

        logger.info(f"Validando seção {section_num}: {section_name}")

        try:
            content = state[section_key].get("content", "")

            if not content:
                logger.warning(f"Seção {section_num} sem conteúdo para validar")
                state[section_key]["status"] = SectionStatus.INVALID
                state[section_key]["validation"] = {
                    "is_valid": False,
                    "score": 0.0,
                    "structural_issues": ["Conteúdo vazio"],
                    "semantic_issues": [],
                    "suggestions": ["Regenerar a seção"],
                }
                return state

            # Valida usando o validador específico
            validator = self.validators.get(section_num)
            if not validator:
                raise ValueError(f"Validador não encontrado para seção {section_num}")

            validation_result = validator.generate(
                content=content,
                objective=state["objective"],
                collection_name=state.get("collection_name")
            )

            # Atualiza estado com resultado da validação
            state[section_key]["validation"] = validation_result
            state[section_key]["last_updated"] = now

            if validation_result.get("is_valid", False):
                state[section_key]["status"] = SectionStatus.VALID
                logger.info(f"Seção {section_num} validada: APROVADA")
            else:
                # Verifica se ainda pode tentar novamente
                attempts = state[section_key]["generation_attempts"]
                max_retries = state.get("max_retries", 3)

                if attempts < max_retries:
                    state[section_key]["status"] = SectionStatus.REGENERATING
                    logger.info(
                        f"Seção {section_num} validada: REPROVADA "
                        f"(tentativa {attempts}/{max_retries})"
                    )
                else:
                    state[section_key]["status"] = SectionStatus.INVALID
                    logger.warning(
                        f"Seção {section_num} validada: REPROVADA "
                        f"(máximo de tentativas atingido)"
                    )

        except Exception as e:
            logger.error(f"Erro ao validar seção {section_num}: {str(e)}")
            state[section_key]["status"] = SectionStatus.ERROR
            state[section_key]["error_message"] = str(e)
            state["errors"].append(f"Validação seção {section_num}: {str(e)}")

        return state

    # === Nós de Geração (15 nós) ===

    def generate_section_01(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 01 - Descrição da Necessidade."""
        return self._generate_section(state, 1)

    def generate_section_02(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 02 - Previsão no PCA."""
        return self._generate_section(state, 2)

    def generate_section_03(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 03 - Requisitos da Contratação."""
        return self._generate_section(state, 3)

    def generate_section_04(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 04 - Estimativa das Quantidades."""
        return self._generate_section(state, 4)

    def generate_section_05(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 05 - Levantamento de Mercado."""
        return self._generate_section(state, 5)

    def generate_section_06(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 06 - Estimativa do Preço."""
        return self._generate_section(state, 6)

    def generate_section_07(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 07 - Descrição da Solução."""
        return self._generate_section(state, 7)

    def generate_section_08(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 08 - Justificativa Parcelamento."""
        return self._generate_section(state, 8)

    def generate_section_09(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 09 - Resultados Pretendidos."""
        return self._generate_section(state, 9)

    def generate_section_10(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 10 - Providências Prévias."""
        return self._generate_section(state, 10)

    def generate_section_11(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 11 - Contratações Correlatas."""
        return self._generate_section(state, 11)

    def generate_section_12(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 12 - Impactos Ambientais."""
        return self._generate_section(state, 12)

    def generate_section_13(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 13 - Viabilidade da Contratação."""
        return self._generate_section(state, 13)

    def generate_section_14(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 14 - Publicidade do ETP."""
        return self._generate_section(state, 14)

    def generate_section_15(self, state: ETPState) -> ETPState:
        """Nó: Gerar Seção 15 - Responsáveis pela Elaboração."""
        return self._generate_section(state, 15)

    # === Nós de Validação (15 nós) ===

    def validate_section_01(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 01 - Descrição da Necessidade."""
        return self._validate_section(state, 1)

    def validate_section_02(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 02 - Previsão no PCA."""
        return self._validate_section(state, 2)

    def validate_section_03(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 03 - Requisitos da Contratação."""
        return self._validate_section(state, 3)

    def validate_section_04(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 04 - Estimativa das Quantidades."""
        return self._validate_section(state, 4)

    def validate_section_05(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 05 - Levantamento de Mercado."""
        return self._validate_section(state, 5)

    def validate_section_06(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 06 - Estimativa do Preço."""
        return self._validate_section(state, 6)

    def validate_section_07(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 07 - Descrição da Solução."""
        return self._validate_section(state, 7)

    def validate_section_08(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 08 - Justificativa Parcelamento."""
        return self._validate_section(state, 8)

    def validate_section_09(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 09 - Resultados Pretendidos."""
        return self._validate_section(state, 9)

    def validate_section_10(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 10 - Providências Prévias."""
        return self._validate_section(state, 10)

    def validate_section_11(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 11 - Contratações Correlatas."""
        return self._validate_section(state, 11)

    def validate_section_12(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 12 - Impactos Ambientais."""
        return self._validate_section(state, 12)

    def validate_section_13(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 13 - Viabilidade da Contratação."""
        return self._validate_section(state, 13)

    def validate_section_14(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 14 - Publicidade do ETP."""
        return self._validate_section(state, 14)

    def validate_section_15(self, state: ETPState) -> ETPState:
        """Nó: Validar Seção 15 - Responsáveis pela Elaboração."""
        return self._validate_section(state, 15)

    # === Nós Auxiliares ===

    def finalize_document(self, state: ETPState) -> ETPState:
        """
        Nó: Finaliza o documento ETP, compilando todas as seções.
        """
        logger.info("Finalizando documento ETP")
        now = datetime.utcnow().isoformat()

        # Obtém lista de seções que foram geradas
        sections_to_generate = state.get("sections_to_generate", list(range(1, 16)))
        total_sections = len(sections_to_generate)

        try:
            # Compila apenas as seções geradas
            document_parts = []

            for section_num in sections_to_generate:
                section_key = get_section_key(section_num)
                section_name = get_section_name(section_num)
                content = state.get(section_key, {}).get("content", "")

                if content:
                    document_parts.append(
                        f"## {section_num}. {strip_generation_suffix(section_name)}\n\n{content}"
                    )

            # Monta documento final
            state["final_document"] = "\n\n---\n\n".join(document_parts)

            # Calcula validação geral apenas das seções geradas
            valid_count = 0
            invalid_count = 0
            total_score = 0.0

            for section_num in sections_to_generate:
                section_key = get_section_key(section_num)
                validation = state.get(section_key, {}).get("validation", {})

                if validation.get("is_valid"):
                    valid_count += 1
                else:
                    invalid_count += 1

                total_score += validation.get("score", 0.0)

            state["overall_validation"] = {
                "valid_sections": valid_count,
                "invalid_sections": invalid_count,
                "total_sections": total_sections,
                "average_score": total_score / total_sections if total_score else 0.0,
                "is_complete": valid_count == total_sections,
            }

            state["status"] = "completed" if valid_count == total_sections else "completed_with_issues"
            state["updated_at"] = now

            logger.info(
                f"Documento ETP finalizado: {valid_count}/{total_sections} seções válidas"
            )

        except Exception as e:
            logger.error(f"Erro ao finalizar documento: {str(e)}")
            state["status"] = "error"
            state["errors"].append(f"Finalização: {str(e)}")

        return state

    def handle_error(self, state: ETPState) -> ETPState:
        """
        Nó: Tratamento de erros durante o processamento.
        """
        logger.error(f"Tratando erros: {state.get('errors', [])}")
        state["status"] = "error"
        state["updated_at"] = datetime.utcnow().isoformat()
        return state


def create_nodes(claude_service, kb_service) -> ETPNodes:
    """
    Factory function para criar instância de ETPNodes.

    Args:
        claude_service: Serviço Claude API
        kb_service: Serviço Knowledge Base

    Returns:
        Instância de ETPNodes configurada
    """
    return ETPNodes(claude_service, kb_service)
