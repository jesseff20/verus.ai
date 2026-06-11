"""
Section01Validator - Validador da Seção 1 do ETP.

Valida se a Seção 1 (Descrição da Necessidade da Contratação)
atende aos requisitos da Lei 14.133/2021 e boas práticas.
"""
import logging
import re
from typing import Dict, List, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section01Validator(BaseAgent):
    """
    Validador da Seção 1 - Descrição da Necessidade da Contratação.

    Implementa Strategy pattern para validação estruturada.
    """

    SYSTEM_PROMPT = """Você é um auditor especializado em licitações públicas e
na Lei 14.133/2021 (Nova Lei de Licitações).

Sua tarefa é **validar** a Seção 1 - Descrição da Necessidade da Contratação
de um Estudo Técnico Preliminar.

## CRITÉRIOS DE VALIDAÇÃO

Avalie se a seção:

1. **Descreve claramente a necessidade**
   - A necessidade está explícita?
   - É possível entender o problema ou demanda?
   - O contexto está claro?

2. **Justifica a relevância da contratação**
   - Está claro POR QUE esta contratação é necessária?
   - Os impactos da não contratação são mencionados?

3. **Está alinhada com a Lei 14.133/2021**
   - Atende ao Art. 18, § 1º (necessidade da contratação)?
   - A linguagem é adequada para documentos oficiais?

4. **Tem qualidade técnica adequada**
   - Texto entre 300 e 800 palavras?
   - Sem erros gramaticais graves?
   - Linguagem clara e objetiva?
   - Sem redundâncias excessivas?

5. **Evita problemas comuns**
   - NÃO contém dados obviamente inventados?
   - NÃO tem informações contraditórias?
   - NÃO é excessivamente genérica?

## FORMATO DE RESPOSTA

Responda APENAS com um JSON no seguinte formato:

```json
{
  "is_valid": true/false,
  "errors": [
    "Erro crítico 1 (se houver)",
    "Erro crítico 2 (se houver)"
  ],
  "warnings": [
    "Aviso 1 (se houver)",
    "Aviso 2 (se houver)"
  ],
  "suggestions": [
    "Sugestão de melhoria 1",
    "Sugestão de melhoria 2"
  ],
  "score": 0-100,
  "summary": "Breve resumo da avaliação"
}
```

- **is_valid**: `true` se não há erros críticos, `false` caso contrário
- **errors**: Lista de problemas graves que IMPEDEM aprovação
- **warnings**: Lista de problemas menores que NÃO impedem aprovação
- **suggestions**: Sugestões para melhorar a seção
- **score**: Nota de 0 a 100 (qualidade geral)
- **summary**: Resumo da avaliação em 1-2 frases

IMPORTANTE: Responda APENAS com o JSON, sem texto adicional antes ou depois."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o validador da Seção 1."""
        super().__init__(
            name="Section01Validator",
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
        Valida a Seção 1 gerada.

        Args:
            content: Conteúdo da Seção 1 a validar
            objective: Objetivo da contratação (para contexto)
            collection_name: Nome da collection (opcional, para contexto extra)

        Returns:
            Dict contendo:
                - is_valid: True se passou na validação
                - errors: Lista de erros críticos
                - warnings: Lista de avisos
                - suggestions: Sugestões de melhoria
                - score: Nota de 0 a 100
                - summary: Resumo da validação
                - reasoning: Raciocínio do validador
        """
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando validação da Seção 1")

        # 1. Validações estruturais (rápidas, sem IA)
        structural_validation = self._validate_structure(content)

        # Se falhou nas validações estruturais críticas, retornar imediatamente
        if not structural_validation['is_valid']:
            self._log_reasoning("Validação estrutural falhou")
            return {
                **structural_validation,
                'reasoning': self.get_reasoning_log()
            }

        # 2. Validação semântica com Claude
        semantic_validation = self._validate_with_claude(content, objective)

        # 3. Combinar resultados
        combined_result = self._combine_validations(
            structural_validation,
            semantic_validation
        )

        self._log_reasoning(
            f"Validação concluída: {'✓ APROVADA' if combined_result['is_valid'] else '✗ REPROVADA'}"
        )

        return {
            **combined_result,
            'reasoning': self.get_reasoning_log()
        }

    def _validate_structure(self, content: str) -> Dict:
        """
        Valida aspectos estruturais do conteúdo.

        Args:
            content: Conteúdo a validar

        Returns:
            Dict com resultado da validação estrutural
        """
        errors = []
        warnings = []
        score = 100

        # Validar tamanho
        word_count = len(content.split())
        self._log_reasoning(f"Contagem de palavras: {word_count}")

        if word_count < 100:
            errors.append(
                f"Texto muito curto ({word_count} palavras). "
                "Mínimo esperado: 300 palavras."
            )
            score -= 40
        elif word_count < 300:
            warnings.append(
                f"Texto curto ({word_count} palavras). "
                "Recomendado: 300-800 palavras."
            )
            score -= 15
        elif word_count > 1000:
            warnings.append(
                f"Texto longo ({word_count} palavras). "
                "Recomendado: 300-800 palavras."
            )
            score -= 10

        # Validar se está vazio ou só espaços
        if not content.strip():
            errors.append("Conteúdo vazio")
            score = 0

        # Validar se contém parágrafos
        paragraphs = [p for p in content.split('\n') if p.strip()]
        if len(paragraphs) < 2:
            warnings.append("Seção contém apenas um parágrafo. Recomenda-se estruturar em múltiplos parágrafos.")
            score -= 5

        # Verificar palavras-chave esperadas
        keywords = ['necessidade', 'contratação', 'objetivo']
        found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]

        if len(found_keywords) < 2:
            warnings.append(
                f"Poucas palavras-chave relevantes encontradas. "
                f"Esperado: {', '.join(keywords)}"
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
        """
        Valida semanticamente usando Claude.

        Args:
            content: Conteúdo a validar
            objective: Objetivo da contratação

        Returns:
            Dict com resultado da validação semântica
        """
        self._log_reasoning("Iniciando validação semântica com Claude")

        user_prompt = f"""## OBJETIVO DA CONTRATAÇÃO

{objective}

## CONTEÚDO DA SEÇÃO 1 A VALIDAR

{content}

## TAREFA

Valide a Seção 1 seguindo os critérios especificados.
Responda APENAS com o JSON conforme o formato indicado."""

        try:
            response = self._call_claude(
                user_prompt=user_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                context_documents=None,
                temperature=0.3,  # Temperatura baixa para validação consistente
                max_tokens=2048
            )

            # Extrair JSON da resposta
            result = self._parse_validation_response(response['content'])

            self._log_reasoning(
                f"Validação semântica: score={result.get('score', 0)}, "
                f"errors={len(result.get('errors', []))}, "
                f"warnings={len(result.get('warnings', []))}"
            )

            return result

        except Exception as e:
            logger.error(f"Erro na validação semântica: {str(e)}")
            self._log_reasoning(f"ERRO na validação semântica: {str(e)}")

            # Retornar validação permissiva em caso de erro
            return {
                'is_valid': True,
                'errors': [],
                'warnings': [f"Erro na validação automática: {str(e)}"],
                'suggestions': ['Revisar manualmente'],
                'score': 70,
                'summary': 'Validação automática falhou - requer revisão manual'
            }

    def _parse_validation_response(self, response_content: str) -> Dict:
        """
        Extrai e valida o JSON da resposta do Claude.

        Args:
            response_content: Conteúdo da resposta

        Returns:
            Dict com dados de validação
        """
        import json

        # Tentar extrair JSON da resposta
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)

        if not json_match:
            raise ValueError("JSON não encontrado na resposta")

        json_str = json_match.group(0)

        try:
            data = json.loads(json_str)

            # Validar estrutura obrigatória
            required_keys = ['is_valid', 'errors', 'warnings', 'suggestions', 'score', 'summary']
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Campo obrigatório ausente: {key}")

            return data

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {str(e)}")

    def _combine_validations(
        self,
        structural: Dict,
        semantic: Dict
    ) -> Dict:
        """
        Combina resultados de validação estrutural e semântica.

        Args:
            structural: Resultado da validação estrutural
            semantic: Resultado da validação semântica

        Returns:
            Dict com validação combinada
        """
        # Se qualquer uma reprovou, resultado final é reprovado
        is_valid = structural['is_valid'] and semantic['is_valid']

        # Combinar erros e warnings (sem duplicatas)
        all_errors = list(set(structural['errors'] + semantic['errors']))
        all_warnings = list(set(structural['warnings'] + semantic['warnings']))
        all_suggestions = semantic.get('suggestions', [])

        # Score final é a média ponderada (estrutural 30%, semântica 70%)
        final_score = int(
            structural['score'] * 0.3 + semantic.get('score', 70) * 0.7
        )

        return {
            'is_valid': is_valid,
            'errors': all_errors,
            'warnings': all_warnings,
            'suggestions': all_suggestions,
            'score': final_score,
            'summary': semantic.get('summary', 'Validação concluída'),
            'structural_score': structural['score'],
            'semantic_score': semantic.get('score', 70)
        }
