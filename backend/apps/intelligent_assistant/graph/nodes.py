"""
Nós do grafo LangGraph para geração de ETP.

Cada nó é uma função que:
1. Recebe o state atual
2. Executa uma operação (gerar, validar, refinar)
3. Retorna um dict com as modificações do state
"""
import logging
from typing import Dict, Any
from .state import ETPGenerationState

logger = logging.getLogger(__name__)
from ..agents.section_agents.section_01_agent import Section01Agent
from ..agents.validators.section_01_validator import Section01Validator
from ..agents.section_agents.section_02_agent import Section02Agent
from ..agents.validators.section_02_validator import Section02Validator
from ..agents.section_agents.section_03_agent import Section03Agent
from ..agents.validators.section_03_validator import Section03Validator
from ..agents.section_agents.section_04_agent import Section04Agent
from ..agents.validators.section_04_validator import Section04Validator
from ..agents.section_agents.section_05_agent import Section05Agent
from ..agents.validators.section_05_validator import Section05Validator
from ..agents.section_agents.section_06_agent import Section06Agent
from ..agents.validators.section_06_validator import Section06Validator


class ETPNodes:
    """
    Classe que encapsula todos os nós do grafo de geração de ETP.

    Cada método é um nó que pode ser adicionado ao StateGraph.
    """

    def __init__(self, claude_service, kb_service):
        """
        Inicializa os nós com os serviços necessários.

        Args:
            claude_service: Instância do ClaudeService
            kb_service: Instância do KnowledgeBaseService
        """
        self.claude_service = claude_service
        self.kb_service = kb_service

        # Instanciar agentes e validadores - Seções 1 e 2
        self.section_01_agent = Section01Agent(claude_service, kb_service)
        self.section_01_validator = Section01Validator(claude_service, kb_service)
        self.section_02_agent = Section02Agent(claude_service, kb_service)
        self.section_02_validator = Section02Validator(claude_service, kb_service)

        # Instanciar agentes e validadores - Seções 3 e 4
        self.section_03_agent = Section03Agent(claude_service, kb_service)
        self.section_03_validator = Section03Validator(claude_service, kb_service)
        self.section_04_agent = Section04Agent(claude_service, kb_service)
        self.section_04_validator = Section04Validator(claude_service, kb_service)

        # Instanciar agentes e validadores - Seções 5 e 6
        self.section_05_agent = Section05Agent(claude_service, kb_service)
        self.section_05_validator = Section05Validator(claude_service, kb_service)
        self.section_06_agent = Section06Agent(claude_service, kb_service)
        self.section_06_validator = Section06Validator(claude_service, kb_service)

    def _get_total_tokens(self, usage: Dict[str, Any]) -> int:
        """
        Calcula o total de tokens a partir do dict usage.

        Args:
            usage: Dict com 'input_tokens' e 'output_tokens'

        Returns:
            Total de tokens
        """
        return usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

    # ========== SEÇÃO 1: DESCRIÇÃO DA NECESSIDADE ==========

    def generate_section_01(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Gerar Seção 1 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_01, reasoning_log, total_tokens_used
        """
        logger.debug("🤖 [NODE] Gerando Seção 1...")

        result = self.section_01_agent.generate(
            objective=state['objective'],
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_01': result['content'],
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage']),
            'current_section': 1
        }

    def validate_section_01(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Validar Seção 1 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_01_validation, errors, warnings
        """
        logger.debug("✅ [NODE] Validando Seção 1...")

        result = self.section_01_validator.generate(
            content=state['section_01'],
            objective=state['objective'],
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        updates = {
            'section_01_validation': result,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result.get('usage', {}))
        }

        # Adicionar erros e warnings
        if not result['is_valid']:
            updates['errors'] = result['errors']
        if result.get('warnings'):
            updates['warnings'] = result['warnings']

        return updates

    def refine_section_01(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Refinar Seção 1 do ETP baseado no feedback da validação.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_01, section_01_refine_attempts, reasoning_log
        """
        logger.debug("🔄 [NODE] Refinando Seção 1...")

        validation = state['section_01_validation']

        # Construir feedback combinando erros e warnings
        feedback_parts = []
        if validation.get('errors'):
            feedback_parts.append("ERROS CRÍTICOS:\n" + "\n".join(f"- {e}" for e in validation['errors']))
        if validation.get('warnings'):
            feedback_parts.append("AVISOS:\n" + "\n".join(f"- {w}" for w in validation['warnings']))
        if validation.get('suggestions'):
            feedback_parts.append("SUGESTÕES:\n" + "\n".join(f"- {s}" for s in validation['suggestions']))

        feedback = "\n\n".join(feedback_parts)

        result = self.section_01_agent.refine(
            previous_content=state['section_01'],
            feedback=feedback,
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_01': result['content'],
            'section_01_refine_attempts': state['section_01_refine_attempts'] + 1,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage'])
        }

    # ========== SEÇÃO 2: ESTUDOS TÉCNICOS PRELIMINARES ==========

    def generate_section_02(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Gerar Seção 2 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_02, reasoning_log, total_tokens_used
        """
        logger.debug("🤖 [NODE] Gerando Seção 2...")

        result = self.section_02_agent.generate(
            objective=state['objective'],
            collection_name=state['collection_name'],
            section_01_content=state.get('section_01')  # Passa Seção 1 como contexto
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_02': result['content'],
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage']),
            'current_section': 2
        }

    def validate_section_02(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Validar Seção 2 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_02_validation, errors, warnings
        """
        logger.debug("✅ [NODE] Validando Seção 2...")

        result = self.section_02_validator.generate(
            content=state['section_02'],
            objective=state['objective'],
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        updates = {
            'section_02_validation': result,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result.get('usage', {}))
        }

        # Adicionar erros e warnings
        if not result['is_valid']:
            updates['errors'] = result['errors']
        if result.get('warnings'):
            updates['warnings'] = result['warnings']

        return updates

    def refine_section_02(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Refinar Seção 2 do ETP baseado no feedback da validação.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_02, section_02_refine_attempts, reasoning_log
        """
        logger.debug("🔄 [NODE] Refinando Seção 2...")

        validation = state['section_02_validation']

        # Construir feedback combinando erros e warnings
        feedback_parts = []
        if validation.get('errors'):
            feedback_parts.append("ERROS CRÍTICOS:\n" + "\n".join(f"- {e}" for e in validation['errors']))
        if validation.get('warnings'):
            feedback_parts.append("AVISOS:\n" + "\n".join(f"- {w}" for w in validation['warnings']))
        if validation.get('suggestions'):
            feedback_parts.append("SUGESTÕES:\n" + "\n".join(f"- {s}" for s in validation['suggestions']))

        feedback = "\n\n".join(feedback_parts)

        result = self.section_02_agent.refine(
            previous_content=state['section_02'],
            feedback=feedback,
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_02': result['content'],
            'section_02_refine_attempts': state['section_02_refine_attempts'] + 1,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage'])
        }

    # ========== SEÇÃO 3: DESCRIÇÃO DA SOLUÇÃO ==========

    def generate_section_03(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Gerar Seção 3 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_03, reasoning_log, total_tokens_used
        """
        logger.debug("🤖 [NODE] Gerando Seção 3...")

        result = self.section_03_agent.generate(
            objective=state['objective'],
            collection_name=state['collection_name'],
            section_01_content=state.get('section_01'),
            section_02_content=state.get('section_02')
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_03': result['content'],
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage']),
            'current_section': 3
        }

    def validate_section_03(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Validar Seção 3 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_03_validation, errors, warnings
        """
        logger.debug("✅ [NODE] Validando Seção 3...")

        result = self.section_03_validator.generate(
            content=state['section_03'],
            objective=state['objective'],
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        updates = {
            'section_03_validation': result,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result.get('usage', {}))
        }

        # Adicionar erros e warnings
        if not result['is_valid']:
            updates['errors'] = result['errors']
        if result.get('warnings'):
            updates['warnings'] = result['warnings']

        return updates

    def refine_section_03(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Refinar Seção 3 do ETP baseado no feedback da validação.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_03, section_03_refine_attempts, reasoning_log
        """
        logger.debug("🔄 [NODE] Refinando Seção 3...")

        validation = state['section_03_validation']

        # Construir feedback combinando erros e warnings
        feedback_parts = []
        if validation.get('errors'):
            feedback_parts.append("ERROS CRÍTICOS:\n" + "\n".join(f"- {e}" for e in validation['errors']))
        if validation.get('warnings'):
            feedback_parts.append("AVISOS:\n" + "\n".join(f"- {w}" for w in validation['warnings']))
        if validation.get('suggestions'):
            feedback_parts.append("SUGESTÕES:\n" + "\n".join(f"- {s}" for s in validation['suggestions']))

        feedback = "\n\n".join(feedback_parts)

        result = self.section_03_agent.refine(
            previous_content=state['section_03'],
            feedback=feedback,
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_03': result['content'],
            'section_03_refine_attempts': state['section_03_refine_attempts'] + 1,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage'])
        }

    # ========== SEÇÃO 4: ESTIMATIVA DE PREÇOS ==========

    def generate_section_04(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Gerar Seção 4 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_04, reasoning_log, total_tokens_used
        """
        logger.debug("🤖 [NODE] Gerando Seção 4...")

        result = self.section_04_agent.generate(
            objective=state['objective'],
            collection_name=state['collection_name'],
            section_01_content=state.get('section_01'),
            section_02_content=state.get('section_02'),
            section_03_content=state.get('section_03')
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_04': result['content'],
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage']),
            'current_section': 4
        }

    def validate_section_04(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Validar Seção 4 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_04_validation, errors, warnings
        """
        logger.debug("✅ [NODE] Validando Seção 4...")

        result = self.section_04_validator.generate(
            content=state['section_04'],
            objective=state['objective'],
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        updates = {
            'section_04_validation': result,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result.get('usage', {}))
        }

        # Adicionar erros e warnings
        if not result['is_valid']:
            updates['errors'] = result['errors']
        if result.get('warnings'):
            updates['warnings'] = result['warnings']

        return updates

    def refine_section_04(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Refinar Seção 4 do ETP baseado no feedback da validação.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_04, section_04_refine_attempts, reasoning_log
        """
        logger.debug("🔄 [NODE] Refinando Seção 4...")

        validation = state['section_04_validation']

        # Construir feedback combinando erros e warnings
        feedback_parts = []
        if validation.get('errors'):
            feedback_parts.append("ERROS CRÍTICOS:\n" + "\n".join(f"- {e}" for e in validation['errors']))
        if validation.get('warnings'):
            feedback_parts.append("AVISOS:\n" + "\n".join(f"- {w}" for w in validation['warnings']))
        if validation.get('suggestions'):
            feedback_parts.append("SUGESTÕES:\n" + "\n".join(f"- {s}" for s in validation['suggestions']))

        feedback = "\n\n".join(feedback_parts)

        result = self.section_04_agent.refine(
            previous_content=state['section_04'],
            feedback=feedback,
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_04': result['content'],
            'section_04_refine_attempts': state['section_04_refine_attempts'] + 1,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage'])
        }

    # ========== SEÇÃO 5: METODOLOGIA DE SELEÇÃO ==========

    def generate_section_05(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Gerar Seção 5 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_05, reasoning_log, total_tokens_used
        """
        logger.debug("🤖 [NODE] Gerando Seção 5...")

        result = self.section_05_agent.generate(
            objective=state['objective'],
            collection_name=state['collection_name'],
            section_01_content=state.get('section_01'),
            section_02_content=state.get('section_02'),
            section_03_content=state.get('section_03'),
            section_04_content=state.get('section_04')
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_05': result['content'],
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage']),
            'current_section': 5
        }

    def validate_section_05(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Validar Seção 5 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_05_validation, errors, warnings
        """
        logger.debug("✅ [NODE] Validando Seção 5...")

        result = self.section_05_validator.generate(
            content=state['section_05'],
            objective=state['objective'],
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        updates = {
            'section_05_validation': result,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result.get('usage', {}))
        }

        # Adicionar erros e warnings
        if not result['is_valid']:
            updates['errors'] = result['errors']
        if result.get('warnings'):
            updates['warnings'] = result['warnings']

        return updates

    def refine_section_05(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Refinar Seção 5 do ETP baseado no feedback da validação.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_05, section_05_refine_attempts, reasoning_log
        """
        logger.debug("🔄 [NODE] Refinando Seção 5...")

        validation = state['section_05_validation']

        # Construir feedback combinando erros e warnings
        feedback_parts = []
        if validation.get('errors'):
            feedback_parts.append("ERROS CRÍTICOS:\n" + "\n".join(f"- {e}" for e in validation['errors']))
        if validation.get('warnings'):
            feedback_parts.append("AVISOS:\n" + "\n".join(f"- {w}" for w in validation['warnings']))
        if validation.get('suggestions'):
            feedback_parts.append("SUGESTÕES:\n" + "\n".join(f"- {s}" for s in validation['suggestions']))

        feedback = "\n\n".join(feedback_parts)

        result = self.section_05_agent.refine(
            previous_content=state['section_05'],
            feedback=feedback,
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_05': result['content'],
            'section_05_refine_attempts': state['section_05_refine_attempts'] + 1,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage'])
        }

    # ========== SEÇÃO 6: JUSTIFICATIVA PARCELAMENTO ==========

    def generate_section_06(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Gerar Seção 6 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_06, reasoning_log, total_tokens_used
        """
        logger.debug("🤖 [NODE] Gerando Seção 6...")

        result = self.section_06_agent.generate(
            objective=state['objective'],
            collection_name=state['collection_name'],
            section_01_content=state.get('section_01'),
            section_02_content=state.get('section_02'),
            section_03_content=state.get('section_03'),
            section_04_content=state.get('section_04'),
            section_05_content=state.get('section_05')
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_06': result['content'],
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage']),
            'current_section': 6
        }

    def validate_section_06(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Validar Seção 6 do ETP.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_06_validation, errors, warnings
        """
        logger.debug("✅ [NODE] Validando Seção 6...")

        result = self.section_06_validator.generate(
            content=state['section_06'],
            objective=state['objective'],
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        updates = {
            'section_06_validation': result,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result.get('usage', {}))
        }

        # Adicionar erros e warnings
        if not result['is_valid']:
            updates['errors'] = result['errors']
        if result.get('warnings'):
            updates['warnings'] = result['warnings']

        return updates

    def refine_section_06(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Refinar Seção 6 do ETP baseado no feedback da validação.

        Args:
            state: Estado atual do grafo

        Returns:
            Dict com atualizações: section_06, section_06_refine_attempts, reasoning_log
        """
        logger.debug("🔄 [NODE] Refinando Seção 6...")

        validation = state['section_06_validation']

        # Construir feedback combinando erros e warnings
        feedback_parts = []
        if validation.get('errors'):
            feedback_parts.append("ERROS CRÍTICOS:\n" + "\n".join(f"- {e}" for e in validation['errors']))
        if validation.get('warnings'):
            feedback_parts.append("AVISOS:\n" + "\n".join(f"- {w}" for w in validation['warnings']))
        if validation.get('suggestions'):
            feedback_parts.append("SUGESTÕES:\n" + "\n".join(f"- {s}" for s in validation['suggestions']))

        feedback = "\n\n".join(feedback_parts)

        result = self.section_06_agent.refine(
            previous_content=state['section_06'],
            feedback=feedback,
            collection_name=state['collection_name']
        )

        # Garantir que reasoning_log seja lista
        reasoning = result.get('reasoning', [])
        if isinstance(reasoning, str):
            reasoning = [reasoning]

        return {
            'section_06': result['content'],
            'section_06_refine_attempts': state['section_06_refine_attempts'] + 1,
            'reasoning_log': reasoning,
            'total_tokens_used': state['total_tokens_used'] + self._get_total_tokens(result['usage'])
        }

    # ========== NÓ FINAL ==========

    def finalize_generation(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Finalizar a geração do ETP.

        Marca a geração como completa e prepara resultado final.
        """
        logger.debug("✨ [NODE] Finalizando geração do ETP...")

        has_errors = len(state.get('errors', [])) > 0

        return {
            'generation_complete': not has_errors,
            'requires_manual_review': has_errors,
            'reasoning_log': [
                f"Geração finalizada. Total de tokens: {state['total_tokens_used']}",
                f"Erros: {len(state.get('errors', []))}",
                f"Avisos: {len(state.get('warnings', []))}"
            ]
        }

    def mark_for_manual_review(self, state: ETPGenerationState) -> Dict[str, Any]:
        """
        Nó: Marcar ETP para revisão manual.

        Usado quando a validação falha após máximo de tentativas de refinamento.
        """
        logger.debug("⚠️  [NODE] Marcando para revisão manual...")

        return {
            'requires_manual_review': True,
            'generation_complete': False,
            'reasoning_log': [
                "Seção não passou na validação após 2 tentativas de refinamento.",
                "Documento marcado para revisão manual."
            ]
        }
