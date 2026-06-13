"""
Serviço de IA para geração e revisão de Documentos.
Integração com Copilot para:
- Geração de documentos jurídicos via IA
- Revisão de documentos buscando erros/inconsistências
- Sugestão de templates baseado no tipo de caso
- Preenchimento automático de templates com dados do caso
"""
import logging
import re
import json
from typing import Optional, Dict, Any, List

from django.conf import settings

logger = logging.getLogger(__name__)


class DocumentAIService:
    """Serviço de IA para geração e revisão de documentos jurídicos."""

    # Templates comuns de documentos jurídicos
    DOCUMENT_TEMPLATES = {
        'peticao_inicial': 'Petição Inicial',
        'contestacao': 'Contestação',
        'replica': 'Réplica',
        'recurso_apelacao': 'Recurso de Apelação',
        'recurso_agravo': 'Recurso de Agravo',
        'mandado_seguranca': 'Mandado de Segurança',
        'habeas_corpus': 'Habeas Corpus',
        'procuracao': 'Procuração',
        'contrato_honorarios': 'Contrato de Honorários',
        'notificacao_extrajudicial': 'Notificação Extrajudicial',
        'parecer_juridico': 'Parecer Jurídico',
        'memoriais': 'Memoriais',
        'razoes_finais': 'Razões Finais',
    }

    @classmethod
    async def generate_document(
        cls,
        prompt: str,
        template_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Gera documento jurídico via IA.

        Args:
            prompt: Descrição do documento a ser gerado
            template_type: Tipo de documento (peticao_inicial, contestacao, etc.)
            context: Dados contextuais do caso (cliente, parte contraria, fatos, etc.)

        Returns:
            Dict com:
            - content: conteúdo gerado
            - template_used: template utilizado
            - confidence: confiança da geração (0-100)
            - suggestions: sugestões de melhoria
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        template_name = cls.DOCUMENT_TEMPLATES.get(template_type, template_type)
        context_str = cls._format_context(context) if context else 'Nenhum contexto fornecido'

        system_prompt = f"""Você é um assistente jurídico especializado em redação de documentos jurídicos brasileiros.
Sua tarefa é gerar {template_name} com linguagem técnica apropriada, fundamentação jurídica sólida e formatação adequada.

Regras:
1. Use linguagem jurídica formal e precisa
2. Cite dispositivos legais relevantes quando aplicável
3. Estruture o documento conforme padrão forense
4. Mantenha coerência e coesão textual
5. Não invente fatos ou jurisprudência"""

        prompt_completo = f"""
Gere uma {template_name} completa baseada nas informações abaixo.

**Contexto do Caso:**
{context_str}

**Instruções Específicas:**
{prompt}

**Formato de resposta (JSON):**
{{
    "content": "conteúdo completo do documento em markdown",
    "structure": ["capítulo 1", "capítulo 2", ...],
    "legal_basis": ["artigo 1", "artigo 2", ...],
    "suggestions": ["sugestão de melhoria 1", ...],
    "confidence": 85
}}
"""

        try:
            llm = UnifiedLLMService()
            response = llm.generate(
                user_prompt=prompt_completo,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=8192,
                provider=getattr(settings, 'DEFAULT_LLM_PROVIDER', 'watsonx'),
                model=getattr(settings, 'DEFAULT_LLM_MODEL', 'mistralai/mistral-medium-2505'),
                usage_type='document_generation',
                description=f'Geração de {template_name}',
            )

            content = response.get('content', '')

            # Extrair JSON da resposta
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'content': result.get('content', content),
                    'template_used': template_name,
                    'structure': result.get('structure', []),
                    'legal_basis': result.get('legal_basis', []),
                    'suggestions': result.get('suggestions', []),
                    'confidence': result.get('confidence', 70),
                }
            else:
                return {
                    'content': content,
                    'template_used': template_name,
                    'structure': [],
                    'legal_basis': [],
                    'suggestions': ['Documento gerado sem estrutura JSON'],
                    'confidence': 60,
                }

        except Exception as e:
            logger.error(f'Erro na geração de documento: {e}')
            return {
                'content': '',
                'template_used': template_name,
                'error': str(e),
                'confidence': 0,
            }

    @classmethod
    async def review_document(
        cls,
        content: str,
        doc_type: str,
    ) -> Dict[str, Any]:
        """
        Revisa documento jurídico buscando erros e inconsistências.

        Args:
            content: Conteúdo do documento a revisar
            doc_type: Tipo do documento

        Returns:
            Dict com:
            - issues: lista de problemas encontrados
            - suggestions: sugestões de melhoria
            - score: qualidade geral (0-100)
            - revised_content: versão revisada (opcional)
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        template_name = cls.DOCUMENT_TEMPLATES.get(doc_type, doc_type)

        system_prompt = """Você é um revisor jurídico especializado em análise de documentos.
Sua tarefa é identificar erros, inconsistências e oportunidades de melhoria em documentos jurídicos.

Critérios de análise:
1. Erros gramaticais e ortográficos
2. Inconsistências factuais ou jurídicas
3. Falta de fundamentação legal
4. Problemas de estrutura ou formatação
5. Clareza e coerência textual
6. Completude das informações necessárias"""

        prompt = f"""
Analise este(a) {template_name} e identifique problemas e oportunidades de melhoria.

**Documento para análise:**
{content[:15000]}  # Limitar tamanho para evitar excesso de tokens

**Tarefa:**
1. Liste todos os problemas encontrados (erros, inconsistências, omissões)
2. Sugira melhorias específicas para cada problema
3. Atribua uma nota de qualidade geral (0-100)
4. Se aplicável, forneça versão revisada de trechos problemáticos

**Formato de resposta (JSON):**
{{
    "issues": [
        {{
            "type": "gramatical|juridico|estrutural|omissao",
            "severity": "baixa|media|alta",
            "location": "trecho ou seção",
            "description": "descrição do problema",
            "suggestion": "sugestão de correção"
        }}
    ],
    "suggestions": ["sugestão geral 1", ...],
    "score": 85,
    "revised_content": "versão revisada de trechos críticos (opcional)"
}}
"""

        try:
            llm = UnifiedLLMService()
            response = llm.generate(
                user_prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=4096,
                provider=getattr(settings, 'DEFAULT_LLM_PROVIDER', 'watsonx'),
                model=getattr(settings, 'DEFAULT_LLM_MODEL', 'mistralai/mistral-medium-2505'),
                usage_type='document_review',
                description=f'Revisão de {template_name}',
            )

            content_response = response.get('content', '')

            # Extrair JSON da resposta
            json_match = re.search(r'\{[\s\S]*\}', content_response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'issues': result.get('issues', []),
                    'suggestions': result.get('suggestions', []),
                    'score': result.get('score', 70),
                    'revised_content': result.get('revised_content'),
                    'total_issues': len(result.get('issues', [])),
                }
            else:
                return {
                    'issues': [],
                    'suggestions': ['Análise concluída sem estrutura JSON'],
                    'score': 70,
                    'total_issues': 0,
                }

        except Exception as e:
            logger.error(f'Erro na revisão de documento: {e}')
            return {
                'issues': [],
                'suggestions': [],
                'score': 0,
                'error': str(e),
            }

    @classmethod
    async def suggest_template(
        cls,
        case_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Sugere modelo de documento baseado no tipo de caso.

        Args:
            case_data: Dados do caso (especialidade, fase, tipo_acao, etc.)

        Returns:
            Dict com:
            - suggested_templates: lista de templates sugeridos
            - primary_recommendation: template principal
            - reasoning: justificativa da recomendação
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        specialty = case_data.get('specialty', 'civel')
        phase = case_data.get('phase', 'inicial')
        case_type = case_data.get('case_type', 'acao')

        system_prompt = """Você é um assistente jurídico especializado em seleção de documentos.
Sua tarefa é recomendar o template de documento mais adequado para cada situação processual."""

        prompt = f"""
Sugira o(s) template(s) de documento mais adequado(s) para este caso.

**Dados do Caso:**
- Especialidade: {specialty}
- Fase processual: {phase}
- Tipo de ação: {case_type}

**Templates disponíveis:**
{', '.join(cls.DOCUMENT_TEMPLATES.values())}

**Tarefa:**
1. Selecione 2-4 templates mais relevantes
2. Indique o template principal (mais urgente/necessário)
3. Justifique a recomendação

**Formato de resposta (JSON):**
{{
    "suggested_templates": [
        {{"type": "peticao_inicial", "name": "Petição Inicial", "priority": 1, "reason": "..."}}
    ],
    "primary_recommendation": "peticao_inicial",
    "reasoning": "explicação detalhada da recomendação"
}}
"""

        try:
            llm = UnifiedLLMService()
            response = llm.generate(
                user_prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1024,
                provider=getattr(settings, 'DEFAULT_LLM_PROVIDER', 'watsonx'),
                model=getattr(settings, 'DEFAULT_LLM_MODEL', 'mistralai/mistral-medium-2505'),
                usage_type='template_suggestion',
                description='Sugestão de template de documento',
            )

            content = response.get('content', '')

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'suggested_templates': result.get('suggested_templates', []),
                    'primary_recommendation': result.get('primary_recommendation'),
                    'reasoning': result.get('reasoning', ''),
                }
            else:
                # Fallback heurístico
                return cls._heuristic_template_suggestion(specialty, phase, case_type)

        except Exception as e:
            logger.error(f'Erro na sugestão de template: {e}')
            return cls._heuristic_template_suggestion(specialty, phase, case_type)

    @classmethod
    def _heuristic_template_suggestion(
        cls,
        specialty: str,
        phase: str,
        case_type: str,
    ) -> Dict[str, Any]:
        """Sugestão heurística de templates quando IA não está disponível."""

        suggestions = []

        # Mapeamento básico fase -> template
        phase_templates = {
            'inicial': ['peticao_inicial', 'procuracao'],
            'contestacao': ['contestacao'],
            'recursal': ['recurso_apelacao', 'recurso_agravo'],
            'execucao': ['peticao_inicial'],
            'final': ['razoes_finais', 'memoriais'],
        }

        templates = phase_templates.get(phase, ['peticao_inicial'])

        for i, tmpl in enumerate(templates):
            suggestions.append({
                'type': tmpl,
                'name': cls.DOCUMENT_TEMPLATES.get(tmpl, tmpl),
                'priority': i + 1,
                'reason': f'Template recomendado para fase {phase}',
            })

        return {
            'suggested_templates': suggestions,
            'primary_recommendation': templates[0] if templates else 'peticao_inicial',
            'reasoning': 'Sugestão baseada em regras heurísticas de fase processual.',
        }

    @classmethod
    async def auto_fill_template(
        cls,
        template: str,
        case_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Preenche template automaticamente com dados do caso.

        Args:
            template: Conteúdo do template com placeholders
            case_data: Dados do caso para preenchimento

        Returns:
            Dict com:
            - filled_content: conteúdo preenchido
            - placeholders_found: placeholders encontrados
            - placeholders_filled: placeholders preenchidos
            - missing_data: dados faltantes
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Extrair placeholders do template (formato {{placeholder}})
        placeholders = re.findall(r'\{\{(\w+)\}\}', template)

        # Verificar quais dados temos
        case_data_flat = cls._flatten_case_data(case_data)
        placeholders_found = []
        placeholders_filled = []
        missing_data = []

        for placeholder in placeholders:
            placeholders_found.append(placeholder)
            if placeholder.lower() in case_data_flat:
                placeholders_filled.append(placeholder)
            else:
                missing_data.append(placeholder)

        # Se temos todos os dados, preencher diretamente
        if not missing_data:
            filled_content = template
            for key, value in case_data_flat.items():
                filled_content = filled_content.replace(f'{{{{{key}}}}}', str(value))
            return {
                'filled_content': filled_content,
                'placeholders_found': placeholders_found,
                'placeholders_filled': placeholders_filled,
                'missing_data': missing_data,
                'completion_rate': 100,
            }

        # Se faltam dados, usar IA para preencher ou sugerir
        system_prompt = """Você é um assistente jurídico especializado em preenchimento de documentos.
Preencha os placeholders do template com os dados disponíveis.
Para dados faltantes, use '[DADO NÃO INFORMADO]' ou inferir quando seguro."""

        prompt = f"""
Preencha este template jurídico com os dados disponíveis.

**Template:**
{template[:10000]}

**Dados do Caso:**
{json.dumps(case_data_flat, indent=2, ensure_ascii=False)}

**Placeholders para preencher:**
{', '.join(placeholders_found)}

**Dados faltantes (usar '[DADO NÃO INFORMADO]' ou inferir com cautela):**
{', '.join(missing_data)}

**Instruções:**
1. Substitua todos os placeholders pelos dados correspondentes
2. Para dados faltantes, use '[DADO NÃO INFORMADO]' ou inferir quando seguro
3. Mantenha a formatação e estrutura do template
4. Não altere texto que não seja placeholder

**Formato de resposta (JSON):**
{{
    "filled_content": "conteúdo preenchido",
    "inferences_made": ["campo X foi inferido como Y"],
    "warnings": ["alertas sobre dados faltantes"]
}}
"""

        try:
            llm = UnifiedLLMService()
            response = llm.generate(
                user_prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=8192,
                provider=getattr(settings, 'DEFAULT_LLM_PROVIDER', 'watsonx'),
                model=getattr(settings, 'DEFAULT_LLM_MODEL', 'mistralai/mistral-medium-2505'),
                usage_type='template_filling',
                description='Preenchimento automático de template',
            )

            content = response.get('content', '')

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'filled_content': result.get('filled_content', template),
                    'placeholders_found': placeholders_found,
                    'placeholders_filled': placeholders_filled,
                    'missing_data': missing_data,
                    'inferences_made': result.get('inferences_made', []),
                    'warnings': result.get('warnings', []),
                    'completion_rate': round(len(placeholders_filled) / len(placeholders_found) * 100) if placeholders_found else 100,
                }
            else:
                return {
                    'filled_content': content,
                    'placeholders_found': placeholders_found,
                    'placeholders_filled': placeholders_filled,
                    'missing_data': missing_data,
                    'completion_rate': round(len(placeholders_filled) / len(placeholders_found) * 100) if placeholders_found else 100,
                }

        except Exception as e:
            logger.error(f'Erro no preenchimento de template: {e}')
            return {
                'filled_content': template,
                'placeholders_found': placeholders_found,
                'placeholders_filled': placeholders_filled,
                'missing_data': missing_data,
                'error': str(e),
            }

    @staticmethod
    def _format_context(context: Dict[str, Any]) -> str:
        """Formata dados de contexto para o prompt."""
        lines = []
        for key, value in context.items():
            if isinstance(value, dict):
                lines.append(f"**{key.replace('_', ' ').title()}:**")
                for k, v in value.items():
                    lines.append(f"  - {k.replace('_', ' ').title()}: {v}")
            else:
                lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
        return '\n'.join(lines)

    @staticmethod
    def _flatten_case_data(case_data: Dict[str, Any]) -> Dict[str, str]:
        """Achata dados do caso para mapeamento de placeholders."""
        flat = {}
        for key, value in case_data.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    flat[f'{key}_{k}'] = str(v)
            else:
                flat[key] = str(value)
        return flat
