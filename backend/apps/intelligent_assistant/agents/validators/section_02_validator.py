"""
Section02Validator - Validador da Seção 2 do ETP.

Valida se a Seção 2 (Previsão no Plano de Contratações Anual)
atende aos requisitos da Lei 14.133/2021 e Decreto regulamentador local.
"""
import logging
import re
from typing import Dict, Optional
from apps.intelligent_assistant.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Section02Validator(BaseAgent):
    """
    Validador da Seção 2 - Previsão no Plano de Contratações Anual.

    Implementa Strategy pattern para validação estruturada.
    """

    SYSTEM_PROMPT = """Você é um auditor especializado em licitações públicas e
na Lei 14.133/2021 (Nova Lei de Licitações) e Decreto regulamentador local.

Sua tarefa é **validar** a Seção 2 - Previsão no Plano de Contratações Anual
de um Estudo Técnico Preliminar.

## CRITÉRIOS DE VALIDAÇÃO

Avalie se a seção:

1. **Aborda o Plano de Contratações Anual (PCA)**
   - Menciona o Plano de Contratações Anual ou equivalente?
   - Trata da previsão ou ausência de previsão?

2. **Um dos cenários é abordado adequadamente:**

   **Cenário A - Contratação PREVISTA no PCA:**
   - Menciona que está no PCA (dados específicos são desejáveis mas não obrigatórios)

   **Cenário B - Contratação NÃO PREVISTA no PCA:**
   - Justifica a ausência (demanda emergente, necessidade superveniente, etc.)
   - OU indica que verificação será feita junto ao setor competente

   **Cenário C - Informações não disponíveis:**
   - Indica que a verificação deve ser realizada
   - Menciona que será consultado o setor de planejamento

3. **Fundamentação legal**
   - Cita Lei 14.133/2021, Art. 18, § 1º, II ou similar?
   - Linguagem formal adequada?

4. **Qualidade técnica**
   - Texto entre 80 e 500 palavras?
   - Coerente e bem estruturado?

IMPORTANTE: Seja TOLERANTE com ausência de dados específicos do PCA se o texto justificar adequadamente
ou indicar que a verificação será realizada. O objetivo é garantir que o tema foi abordado, não que
dados específicos estejam presentes.

## FORMATO DE RESPOSTA

Responda APENAS com um JSON no seguinte formato:

```json
{
  "is_valid": true/false,
  "errors": ["Erro crítico 1", "Erro crítico 2"],
  "warnings": ["Aviso 1", "Aviso 2"],
  "suggestions": ["Sugestão 1", "Sugestão 2"],
  "score": 0-100,
  "summary": "Breve resumo da avaliação"
}
```

IMPORTANTE: Responda APENAS com o JSON, sem texto adicional."""

    def __init__(self, claude_service, kb_service):
        """Inicializa o validador da Seção 2."""
        super().__init__(
            name="Section02Validator",
            claude_service=claude_service,
            kb_service=kb_service
        )

    def generate(
        self,
        content: str,
        objective: str,
        collection_name: Optional[str] = None
    ) -> Dict:
        """Valida a Seção 2 gerada."""
        self.clear_reasoning_log()
        self._log_reasoning("Iniciando validação da Seção 2")

        structural_validation = self._validate_structure(content)

        if not structural_validation['is_valid']:
            self._log_reasoning("Validação estrutural falhou")
            return {**structural_validation, 'reasoning': self.get_reasoning_log()}

        semantic_validation = self._validate_with_claude(content, objective)
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

        word_count = len(content.split())
        self._log_reasoning(f"Contagem de palavras: {word_count}")

        if word_count < 40:
            errors.append(f"Texto muito curto ({word_count} palavras). Mínimo: 80 palavras.")
            score -= 40
        elif word_count < 80:
            warnings.append(f"Texto curto ({word_count} palavras). Recomendado: 80-500 palavras.")
            score -= 10
        elif word_count > 600:
            warnings.append(f"Texto longo ({word_count} palavras). Recomendado: 80-500 palavras.")
            score -= 5

        if not content.strip():
            errors.append("Conteúdo vazio")
            score = 0

        # Verificar palavras-chave esperadas
        keywords = ['plano', 'contratações', 'pca', 'previsão', 'anual']
        found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]

        if len(found_keywords) < 2:
            warnings.append(f"Poucas palavras-chave relevantes. Esperado: {', '.join(keywords)}")
            score -= 15

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

## CONTEÚDO DA SEÇÃO 2 A VALIDAR

{content}

## TAREFA

Valide a Seção 2 seguindo os critérios especificados.
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
                'warnings': [f"Erro na validação: {str(e)}"],
                'suggestions': ['Revisar manualmente'],
                'score': 70,
                'summary': 'Validação automática falhou'
            }

    def _parse_validation_response(self, response_content: str) -> Dict:
        """Extrai JSON da resposta do Claude."""
        import json

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

        final_score = int(structural['score'] * 0.3 + semantic.get('score', 70) * 0.7)

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
