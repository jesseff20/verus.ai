"""
Serviço de Controle de Prazos Inteligente com IA.

Utiliza LLM para análise, priorização e predição de riscos
relacionados a prazos processuais.
"""
import json
import logging
from django.utils import timezone
from apps.cases.models import LegalCase, LegalDeadline

logger = logging.getLogger(__name__)


class SmartDeadlineService:
    """Serviço inteligente de análise de prazos com IA."""

    def __init__(self):
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        self.llm = UnifiedLLMService()

    def analyze_deadlines(self, user) -> dict:
        """
        Analisa todos os prazos pendentes do usuário e retorna
        recomendações de priorização via IA.
        """
        today = timezone.now().date()

        # Buscar prazos pendentes do usuário
        deadlines = LegalDeadline.objects.filter(
            caso__advogado_responsavel=user,
            status__in=['pendente', 'em_andamento'],
        ).select_related('caso').order_by('data_prazo')[:50]

        if not deadlines.exists():
            return {
                'analise': 'Nenhum prazo pendente encontrado.',
                'prazos_analisados': 0,
                'recomendacoes': [],
            }

        # Montar contexto dos prazos para a IA
        prazos_info = []
        for d in deadlines:
            dias_restantes = (d.data_prazo - today).days
            prazos_info.append({
                'id': str(d.id),
                'titulo': d.titulo,
                'caso': d.caso.titulo if d.caso else 'Sem caso',
                'numero_processo': d.caso.numero_processo if d.caso else '',
                'tipo': d.get_tipo_display(),
                'prioridade': d.get_prioridade_display(),
                'data_prazo': d.data_prazo.isoformat(),
                'dias_restantes': dias_restantes,
                'status': d.get_status_display(),
                'atrasado': dias_restantes < 0,
            })

        prompt = f"""Analise os seguintes prazos processuais de um advogado brasileiro e forneça:
1. Uma análise geral da situação
2. Priorização dos prazos mais críticos
3. Recomendações de ação

Prazos:
{json.dumps(prazos_info, ensure_ascii=False, indent=2)}

Responda em JSON com a estrutura:
{{
  "analise_geral": "texto da análise geral",
  "prazos_priorizados": [
    {{
      "id": "uuid do prazo",
      "titulo": "título",
      "risco": "alto|medio|baixo",
      "motivo": "razão da priorização",
      "acao_sugerida": "ação recomendada"
    }}
  ],
  "recomendacoes": ["recomendação 1", "recomendação 2"]
}}"""

        system_prompt = (
            "Você é um assistente jurídico especializado em gestão de prazos processuais "
            "do sistema judiciário brasileiro. Analise os prazos e forneça orientações "
            "práticas e objetivas. Responda SOMENTE com o JSON solicitado."
        )

        try:
            result = self.llm.generate(
                user_prompt=prompt,
                system_prompt=system_prompt,
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
                max_tokens=500,
                temperature=0.3,
            )

            content = result.get('content', '') if isinstance(result, dict) else str(result)

            # Extrair JSON da resposta
            parsed = self._extract_json(content)

            return {
                'analise': parsed.get('analise_geral', content),
                'prazos_analisados': len(prazos_info),
                'prazos_priorizados': parsed.get('prazos_priorizados', []),
                'recomendacoes': parsed.get('recomendacoes', []),
            }

        except Exception as exc:
            logger.error(f"[SmartDeadlineService.analyze_deadlines] Erro: {exc}", exc_info=True)
            return {
                'analise': 'Erro ao processar análise com IA. Tente novamente.',
                'prazos_analisados': len(prazos_info),
                'recomendacoes': [],
                'error': str(exc),
            }

    def suggest_actions(self, deadline_id) -> dict:
        """Sugere próximas ações para um prazo específico usando IA."""
        try:
            deadline = LegalDeadline.objects.select_related('caso').get(pk=deadline_id)
        except LegalDeadline.DoesNotExist:
            return {'error': 'Prazo não encontrado.'}

        today = timezone.now().date()
        dias_restantes = (deadline.data_prazo - today).days

        prompt = f"""Sugira próximas ações para o seguinte prazo processual:

Título: {deadline.titulo}
Descrição: {deadline.descricao or 'Não informada'}
Tipo: {deadline.get_tipo_display()}
Prioridade: {deadline.get_prioridade_display()}
Data do Prazo: {deadline.data_prazo.isoformat()}
Dias Restantes: {dias_restantes}
Status: {deadline.get_status_display()}
Caso: {deadline.caso.titulo if deadline.caso else 'Não vinculado'}
Número do Processo: {deadline.caso.numero_processo if deadline.caso else 'N/A'}
Especialidade: {deadline.caso.get_especialidade_display() if deadline.caso else 'N/A'}
Base Legal: {deadline.base_legal or 'Não informada'}

Responda em JSON:
{{
  "sugestoes": [
    {{
      "acao": "descrição da ação",
      "urgencia": "alta|media|baixa",
      "prazo_sugerido": "prazo para executar"
    }}
  ],
  "observacoes": "observações adicionais"
}}"""

        system_prompt = (
            "Você é um assistente jurídico brasileiro especializado em prazos processuais. "
            "Forneça sugestões práticas e objetivas. Responda SOMENTE com o JSON."
        )

        try:
            result = self.llm.generate(
                user_prompt=prompt,
                system_prompt=system_prompt,
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
                max_tokens=500,
                temperature=0.3,
            )

            content = result.get('content', '') if isinstance(result, dict) else str(result)
            parsed = self._extract_json(content)

            return {
                'deadline_id': str(deadline_id),
                'titulo': deadline.titulo,
                'sugestoes': parsed.get('sugestoes', []),
                'observacoes': parsed.get('observacoes', content),
            }

        except Exception as exc:
            logger.error(f"[SmartDeadlineService.suggest_actions] Erro: {exc}", exc_info=True)
            return {
                'deadline_id': str(deadline_id),
                'sugestoes': [],
                'error': str(exc),
            }

    def predict_risk(self, case_id) -> dict:
        """Prediz o nível de risco de um caso com base nos padrões de prazos."""
        try:
            case = LegalCase.objects.get(pk=case_id)
        except LegalCase.DoesNotExist:
            return {'error': 'Caso não encontrado.'}

        today = timezone.now().date()

        # Buscar todos os prazos do caso
        deadlines = LegalDeadline.objects.filter(caso=case).order_by('data_prazo')
        total = deadlines.count()
        pendentes = deadlines.filter(status='pendente').count()
        atrasados = deadlines.filter(status='pendente', data_prazo__lt=today).count()
        concluidos = deadlines.filter(status='concluido').count()

        prompt = f"""Avalie o nível de risco do seguinte caso jurídico com base nos prazos:

Caso: {case.titulo}
Número do Processo: {case.numero_processo or 'N/A'}
Especialidade: {case.get_especialidade_display()}
Status: {case.get_status_display()}
Fase: {case.get_fase_display()}
Tribunal: {case.tribunal or 'N/A'}

Estatísticas de Prazos:
- Total de prazos: {total}
- Pendentes: {pendentes}
- Atrasados: {atrasados}
- Concluídos: {concluidos}

Responda em JSON:
{{
  "nivel_risco": "alto|medio|baixo",
  "score": 0-100,
  "explicacao": "explicação do nível de risco",
  "fatores_risco": ["fator 1", "fator 2"],
  "recomendacoes": ["recomendação 1", "recomendação 2"]
}}"""

        system_prompt = (
            "Você é um analista de risco jurídico especializado no sistema judiciário brasileiro. "
            "Avalie o risco do caso com base nos dados fornecidos. Responda SOMENTE com o JSON."
        )

        try:
            result = self.llm.generate(
                user_prompt=prompt,
                system_prompt=system_prompt,
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
                max_tokens=500,
                temperature=0.3,
            )

            content = result.get('content', '') if isinstance(result, dict) else str(result)
            parsed = self._extract_json(content)

            return {
                'case_id': str(case_id),
                'titulo': case.titulo,
                'nivel_risco': parsed.get('nivel_risco', 'medio'),
                'score': parsed.get('score', 50),
                'explicacao': parsed.get('explicacao', content),
                'fatores_risco': parsed.get('fatores_risco', []),
                'recomendacoes': parsed.get('recomendacoes', []),
                'estatisticas': {
                    'total_prazos': total,
                    'pendentes': pendentes,
                    'atrasados': atrasados,
                    'concluidos': concluidos,
                },
            }

        except Exception as exc:
            logger.error(f"[SmartDeadlineService.predict_risk] Erro: {exc}", exc_info=True)
            return {
                'case_id': str(case_id),
                'nivel_risco': 'medio',
                'explicacao': 'Erro ao processar predição com IA.',
                'error': str(exc),
            }

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extrai JSON de uma resposta que pode conter markdown."""
        clean = text.strip()
        if '```json' in clean:
            clean = clean.split('```json')[1].split('```')[0]
        elif '```' in clean:
            clean = clean.split('```')[1].split('```')[0]

        try:
            return json.loads(clean.strip())
        except (json.JSONDecodeError, IndexError):
            return {}
