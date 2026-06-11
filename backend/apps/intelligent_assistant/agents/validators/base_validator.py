"""
BaseValidator - Classe base para validadores de seções do ETP.

Fornece funcionalidades comuns para todos os validadores de seção.
"""
import logging
import re
import json
from typing import Dict, List, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class BaseValidator(BaseAgent):
    """
    Classe base para validadores de seções do ETP.

    Implementa o padrão Template Method para validação estruturada.
    Subclasses devem definir:
    - SYSTEM_PROMPT: Prompt específico para validação da seção
    - SECTION_NAME: Nome da seção
    - SECTION_NUMBER: Número da seção
    - MIN_WORDS: Mínimo de palavras esperado
    - MAX_WORDS: Máximo de palavras recomendado
    - KEYWORDS: Lista de palavras-chave esperadas
    """

    SYSTEM_PROMPT = ""
    SECTION_NAME = ""
    SECTION_NUMBER = 0
    MIN_WORDS = 100
    MAX_WORDS = 500
    KEYWORDS: List[str] = []

    def __init__(self, claude_service, kb_service, name: str = None):
        """Inicializa o validador."""
        super().__init__(
            name=name or f"Section{self.SECTION_NUMBER:02d}Validator",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        content: str,
        objective: str,
        collection_name: Optional[str] = None
    ) -> Dict:
        """
        Valida a seção gerada.

        Args:
            content: Conteúdo da seção a validar
            objective: Objetivo da contratação (para contexto)
            collection_name: Nome da collection (opcional)

        Returns:
            Dict com resultado da validação
        """
        self.clear_reasoning_log()
        self._log_reasoning(f"Iniciando validação da Seção {self.SECTION_NUMBER}")

        # 1. Validações estruturais (rápidas, sem IA)
        structural_validation = self._validate_structure(content)

        # Se falhou nas validações estruturais críticas, retornar imediatamente
        if not structural_validation['is_valid']:
            self._log_reasoning("Validação estrutural falhou")
            return {**structural_validation, 'reasoning': self.get_reasoning_log()}

        # 2. Validação semântica com Claude
        semantic_validation = self._validate_with_claude(content, objective)

        # 3. Combinar resultados
        combined_result = self._combine_validations(structural_validation, semantic_validation)

        self._log_reasoning(
            f"Validação concluída: {'✓ APROVADA' if combined_result['is_valid'] else '✗ REPROVADA'}"
        )

        return {**combined_result, 'reasoning': self.get_reasoning_log()}

    def _validate_structure(self, content: str) -> Dict:
        """Valida aspectos estruturais do conteúdo."""
        errors = []
        warnings = []
        score = 100

        # Validar tamanho
        word_count = len(content.split())
        self._log_reasoning(f"Contagem de palavras: {word_count}")

        min_critical = self.MIN_WORDS // 2

        if word_count < min_critical:
            errors.append(
                f"Texto muito curto ({word_count} palavras). "
                f"Mínimo esperado: {self.MIN_WORDS} palavras."
            )
            score -= 40
        elif word_count < self.MIN_WORDS:
            warnings.append(
                f"Texto curto ({word_count} palavras). "
                f"Recomendado: {self.MIN_WORDS}-{self.MAX_WORDS} palavras."
            )
            score -= 15
        elif word_count > self.MAX_WORDS * 1.2:
            warnings.append(
                f"Texto longo ({word_count} palavras). "
                f"Recomendado: {self.MIN_WORDS}-{self.MAX_WORDS} palavras."
            )
            score -= 10

        # Validar se está vazio
        if not content.strip():
            errors.append("Conteúdo vazio")
            score = 0

        # Validar se contém múltiplos parágrafos
        paragraphs = [p for p in content.split('\n') if p.strip()]
        if len(paragraphs) < 2:
            warnings.append("Seção contém apenas um parágrafo. Recomenda-se estruturar em múltiplos parágrafos.")
            score -= 5

        # Verificar palavras-chave esperadas
        if self.KEYWORDS:
            found_keywords = [kw for kw in self.KEYWORDS if kw.lower() in content.lower()]
            if len(found_keywords) < min(2, len(self.KEYWORDS)):
                warnings.append(
                    f"Poucas palavras-chave relevantes encontradas. "
                    f"Esperado: {', '.join(self.KEYWORDS[:5])}"
                )
                score -= 10

        is_valid = len(errors) == 0

        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'suggestions': [],
            'score': max(0, score),
            'summary': "Validação estrutural concluída"
        }

    def _validate_with_claude(self, content: str, objective: str) -> Dict:
        """Valida semanticamente usando Claude."""
        self._log_reasoning("Iniciando validação semântica com Claude")

        user_prompt = f"""## OBJETIVO DA CONTRATAÇÃO

{objective}

## CONTEÚDO DA SEÇÃO {self.SECTION_NUMBER} A VALIDAR

{content}

## TAREFA

Valide a Seção {self.SECTION_NUMBER} seguindo os critérios especificados.
Responda APENAS com o JSON conforme o formato indicado."""

        try:
            response = self._call_claude(
                user_prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                context_documents=None,
                temperature=0.3,
                max_tokens=2048
            )

            result = self._parse_validation_response(response['content'])
            self._log_reasoning(f"Validação semântica: score={result.get('score', 0)}")
            return result

        except Exception as e:
            logger.error(f"Erro na validação semântica: {str(e)}")
            self._log_reasoning(f"ERRO: {str(e)}")
            return {
                'is_valid': True,
                'errors': [],
                'warnings': [f"Erro na validação automática: {str(e)}"],
                'suggestions': ['Revisar manualmente'],
                'score': 70,
                'summary': 'Validação automática falhou - requer revisão manual'
            }

    def _parse_validation_response(self, response_content: str) -> Dict:
        """Extrai JSON da resposta do Claude."""
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if not json_match:
            raise ValueError("JSON não encontrado na resposta")

        data = json.loads(json_match.group(0))

        required_keys = ['is_valid', 'errors', 'warnings', 'suggestions', 'score', 'summary']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Campo ausente: {key}")

        return data

    def _combine_validations(self, structural: Dict, semantic: Dict) -> Dict:
        """Combina resultados de validação estrutural e semântica."""
        is_valid = structural['is_valid'] and semantic['is_valid']

        all_errors = list(set(structural['errors'] + semantic['errors']))
        all_warnings = list(set(structural['warnings'] + semantic['warnings']))
        all_suggestions = semantic.get('suggestions', [])

        final_score = round(structural['score'] * 0.3 + semantic.get('score', 70) * 0.7, 2)

        return {
            'is_valid': is_valid,
            'errors': all_errors,
            'warnings': all_warnings,
            'suggestions': all_suggestions,
            'score': final_score,
            'summary': semantic.get('summary', 'Validação concluída'),
            'structural_score': round(structural['score'], 2),
            'semantic_score': round(semantic.get('score', 70), 2)
        }


def create_validator_system_prompt(section_number: int, section_name: str, criteria: str) -> str:
    """
    Cria o SYSTEM_PROMPT padrão para validadores.

    Args:
        section_number: Número da seção
        section_name: Nome da seção
        criteria: Critérios específicos de validação

    Returns:
        SYSTEM_PROMPT formatado
    """
    return f"""Você é um auditor especializado em licitações públicas e
na Lei 14.133/2021 (Nova Lei de Licitações) e decreto regulamentador local.

Sua tarefa é **validar** a Seção {section_number} - {section_name}
de um Estudo Técnico Preliminar.

## CRITÉRIOS DE VALIDAÇÃO

{criteria}

## FORMATO DE RESPOSTA

Responda APENAS com um JSON no seguinte formato:

```json
{{
  "is_valid": true/false,
  "errors": ["Erro crítico 1", "Erro crítico 2"],
  "warnings": ["Aviso 1", "Aviso 2"],
  "suggestions": ["Sugestão 1", "Sugestão 2"],
  "score": 0-100,
  "summary": "Breve resumo da avaliação"
}}
```

- **is_valid**: `true` se não há erros críticos, `false` caso contrário
- **errors**: Lista de problemas graves que IMPEDEM aprovação
- **warnings**: Lista de problemas menores que NÃO impedem aprovação
- **suggestions**: Sugestões para melhorar a seção
- **score**: Nota de 0 a 100 (qualidade geral)
- **summary**: Resumo da avaliação em 1-2 frases

IMPORTANTE: Responda APENAS com o JSON, sem texto adicional."""
