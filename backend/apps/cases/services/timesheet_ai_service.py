"""
TimesheetAIService — Serviço de IA para preenchimento automático de timesheet.

Integração com Copilot para:
- Analisar atividades do usuário e sugerir registros de horas
- Sugerir descrições técnicas para atividades
- Detectar horas não lançadas baseado em atividades
- Otimizar alocação de horas entre casos
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class TimesheetAIService:
    """Serviço de IA para análise e sugestão de registros de timesheet."""

    @staticmethod
    async def analyze_activities_for_timesheet(
        user_id: str,
        days_back: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Analisa atividades do usuário (emails, documentos, tarefas) e sugere registros de timesheet.

        Args:
            user_id: ID do usuário
            days_back: Quantos dias atrás buscar atividades

        Returns:
            Lista de sugestões com:
            - date: data da atividade
            - case_id: ID do caso relacionado
            - case_title: título do caso
            - activity_type: tipo de atividade
            - activity_description: descrição da atividade
            - suggested_hours: horas sugeridas (0.25, 0.5, 1.0, etc.)
            - suggested_description: descrição técnica sugerida
            - confidence: confiança da sugestão (0-100)
        """
        from apps.cases.models import LegalCase, CaseTask, Document
        from apps.cases.services.activity_log_service import ActivityLogService

        start_date = timezone.now() - timedelta(days=days_back)
        suggestions = []

        # Buscar atividades do usuário
        try:
            activities = ActivityLogService.get_user_activities(
                user_id=user_id,
                start_date=start_date,
            )
        except Exception as e:
            logger.warning(f'Erro ao buscar atividades: {e}')
            activities = []

        # Buscar documentos criados pelo usuário
        documents = Document.objects.filter(
            created_by_id=user_id,
            created_at__gte=start_date,
        ).select_related('case').order_by('-created_at')[:50]

        # Buscar tarefas concluídas
        tasks = CaseTask.objects.filter(
            assigned_to_id=user_id,
            completed_at__gte=start_date,
        ).select_related('case').order_by('-completed_at')[:50]

        # Processar documentos
        for doc in documents:
            if doc.case:
                suggestion = await TimesheetAIService._analyze_document_activity(
                    document=doc,
                    case=doc.case,
                )
                if suggestion:
                    suggestions.append(suggestion)

        # Processar tarefas
        for task in tasks:
            if task.case:
                suggestion = await TimesheetAIService._analyze_task_activity(
                    task=task,
                    case=task.case,
                )
                if suggestion:
                    suggestions.append(suggestion)

        # Processar activities do log
        for activity in activities[:100]:
            if activity.get('case_id'):
                suggestion = await TimesheetAIService._analyze_log_activity(
                    activity=activity,
                )
                if suggestion:
                    suggestions.append(suggestion)

        # Remover duplicatas e ordenar por data
        seen = set()
        unique_suggestions = []
        for s in sorted(suggestions, key=lambda x: x.get('date', ''), reverse=True):
            key = (s.get('date'), s.get('case_id'), s.get('activity_type'))
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(s)

        return unique_suggestions[:50]  # Limite de 50 sugestões

    @staticmethod
    async def _analyze_document_activity(
        document: Any,
        case: Any,
    ) -> Optional[Dict[str, Any]]:
        """Analisa documento criado e gera sugestão de timesheet."""
        if not document.document_type:
            return None

        # Mapear tipo de documento para horas sugeridas
        doc_type = document.document_type.lower()
        hours_map = {
            'petição': 2.0,
            'peticao': 2.0,
            'contrato': 1.5,
            'procuração': 0.5,
            'procuracao': 0.5,
            'relatório': 1.0,
            'relatorio': 1.0,
            'manifestação': 1.5,
            'manifestacao': 1.5,
            'recurso': 2.5,
            'contestação': 3.0,
            'contestacao': 3.0,
            'inicial': 2.5,
        }

        suggested_hours = hours_map.get(doc_type, 1.0)
        description = f"Elaboração de {document.document_type}"

        if document.title:
            description += f": {document.title[:50]}"

        return {
            'date': document.created_at.strftime('%Y-%m-%d') if document.created_at else None,
            'case_id': str(case.id),
            'case_title': case.titulo or 'Caso sem título',
            'activity_type': 'document_creation',
            'activity_description': f"Documento criado: {document.document_type}",
            'suggested_hours': suggested_hours,
            'suggested_description': description,
            'confidence': 75,
            'metadata': {
                'document_id': str(document.id),
                'document_type': document.document_type,
            },
        }

    @staticmethod
    async def _analyze_task_activity(
        task: Any,
        case: Any,
    ) -> Optional[Dict[str, Any]]:
        """Analisa tarefa concluída e gera sugestão de timesheet."""
        # Mapear tipo de tarefa para horas sugeridas
        task_title = (task.title or '').lower()
        hours_map = {
            'reunião': 1.0,
            'reuniao': 1.0,
            'ligação': 0.5,
            'ligacao': 0.5,
            'análise': 1.5,
            'analise': 1.5,
            'pesquisa': 1.0,
            'redação': 1.5,
            'redacao': 1.5,
            'revisão': 1.0,
            'revisao': 1.0,
        }

        suggested_hours = 1.0
        for keyword, hours in hours_map.items():
            if keyword in task_title:
                suggested_hours = hours
                break

        description = f"Execução de tarefa: {task.title}"
        if task.description:
            description += f" - {task.description[:50]}"

        return {
            'date': task.completed_at.strftime('%Y-%m-%d') if task.completed_at else None,
            'case_id': str(case.id),
            'case_title': case.titulo or 'Caso sem título',
            'activity_type': 'task_completion',
            'activity_description': f"Tarefa concluída: {task.title}",
            'suggested_hours': suggested_hours,
            'suggested_description': description,
            'confidence': 70,
            'metadata': {
                'task_id': str(task.id),
            },
        }

    @staticmethod
    async def _analyze_log_activity(
        activity: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Analisa atividade do log e gera sugestão de timesheet."""
        action = activity.get('action', '').lower()
        case_id = activity.get('case_id')

        if not case_id:
            return None

        # Mapear ações para horas e descrições
        action_map = {
            'case_viewed': (0.25, 'Consulta de processo'),
            'case_updated': (0.5, 'Atualização de caso'),
            'deadline_created': (0.5, 'Cadastro de prazo'),
            'deadline_updated': (0.25, 'Atualização de prazo'),
            'document_uploaded': (0.25, 'Upload de documento'),
            'client_contact': (0.5, 'Contato com cliente'),
            'court_access': (1.0, 'Acesso ao tribunal'),
            'petition_filed': (0.5, 'Protocolo de petição'),
        }

        hours, base_desc = action_map.get(action, (0.5, 'Atividade realizada'))

        return {
            'date': activity.get('timestamp', '')[:10] if activity.get('timestamp') else None,
            'case_id': str(case_id),
            'case_title': activity.get('case_title', 'Caso'),
            'activity_type': 'log_activity',
            'activity_description': activity.get('description', action),
            'suggested_hours': hours,
            'suggested_description': base_desc,
            'confidence': 50,  # Menor confiança para atividades genéricas
            'metadata': {
                'activity_id': activity.get('id'),
                'action': action,
            },
        }

    @staticmethod
    async def suggest_description(
        activity_type: str,
        case_title: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Sugere descrição técnica para registro de timesheet.

        Args:
            activity_type: Tipo de atividade (reuniao, peticao, analise, etc.)
            case_title: Título do caso
            details: Detalhes adicionais (opcional)

        Returns:
            Descrição técnica formatada
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        details_str = str(details) if details else ''

        prompt = f"""
Gere uma descrição técnica profissional para registro de timesheet jurídico.

**Atividade:** {activity_type}
**Caso:** {case_title[:100]}
**Detalhes:** {details_str[:200] if details_str else 'N/A'}

**Requisitos:**
1. Use linguagem técnica jurídica apropriada
2. Seja específico sobre a natureza do trabalho
3. Mantenha entre 50-150 caracteres
4. Formato: "[Tipo de trabalho] referente a [assunto]"

**Exemplos:**
- "Elaboração de petição inicial de ação indenizatória por danos morais"
- "Análise de documentos e pesquisa jurisprudencial para fundamentação de recurso"
- "Reunião com cliente para coleta de informações e documentação"

**Descrição sugerida:**
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.5, max_tokens=100)
            return response.strip()[:200]
        except Exception as e:
            logger.warning(f'Erro ao gerar descrição: {e}')
            return TimesheetAIService._fallback_description(activity_type, case_title)

    @staticmethod
    def _fallback_description(activity_type: str, case_title: str) -> str:
        """Fallback de descrição quando IA não está disponível."""
        templates = {
            'reuniao': f'Reunião referente ao caso: {case_title[:50]}',
            'reunião': f'Reunião referente ao caso: {case_title[:50]}',
            'peticao': f'Elaboração de petição - {case_title[:50]}',
            'petição': f'Elaboração de petição - {case_title[:50]}',
            'analise': f'Análise técnica do caso: {case_title[:50]}',
            'análise': f'Análise técnica do caso: {case_title[:50]}',
            'pesquisa': f'Pesquisa jurisprudencial e doutrinária - {case_title[:50]}',
            'redacao': f'Redação de documento jurídico - {case_title[:50]}',
            'redação': f'Redação de documento jurídico - {case_title[:50]}',
            'revisao': f'Revisão técnica de documentos - {case_title[:50]}',
            'revisão': f'Revisão técnica de documentos - {case_title[:50]}',
            'ligacao': f'Contato telefônico com cliente/tribunal - {case_title[:50]}',
            'ligação': f'Contato telefônico com cliente/tribunal - {case_title[:50]}',
        }

        return templates.get(activity_type.lower(), f'Atividade jurídica - {case_title[:50]}')

    @staticmethod
    async def detect_unlogged_hours(
        user_id: str,
        date_range: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """
        Detecta possíveis horas não lançadas baseado em atividades.

        Args:
            user_id: ID do usuário
            date_range: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}

        Returns:
            Lista de períodos com atividades mas sem registros de timesheet
        """
        from apps.cases.models import TimeEntry, LegalCase
        from apps.cases.services.activity_log_service import ActivityLogService
        from datetime import datetime

        start_date = datetime.strptime(date_range['start'], '%Y-%m-%d')
        end_date = datetime.strptime(date_range['end'], '%Y-%m-%d')

        # Buscar atividades no período
        activities = ActivityLogService.get_user_activities(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Buscar registros de timesheet no período
        existing_entries = TimeEntry.objects.filter(
            advogado_id=user_id,
            date__gte=start_date,
            date__lte=end_date,
        ).values_list('date', flat=True)

        # Agrupar atividades por data
        activities_by_date = {}
        for activity in activities:
            date_str = activity.get('timestamp', '')[:10]
            if date_str not in activities_by_date:
                activities_by_date[date_str] = []
            activities_by_date[date_str].append(activity)

        # Detectar datas com atividades mas sem timesheet
        unlogged = []
        for date_str, date_activities in activities_by_date.items():
            if date_str not in [str(d) for d in existing_entries]:
                if len(date_activities) >= 3:  # Mínimo de atividades para sugerir
                    unlogged.append({
                        'date': date_str,
                        'activity_count': len(date_activities),
                        'activity_types': list(set(
                            a.get('action', 'unknown') for a in date_activities
                        )),
                        'suggestion': f"Foram detectadas {len(date_activities)} atividades em {date_str} sem registro de horas.",
                    })

        return sorted(unlogged, key=lambda x: x['date'], reverse=True)[:20]

    @staticmethod
    async def optimize_billing(
        entries: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Otimiza alocação de horas entre casos para melhor faturamento.

        Args:
            entries: Lista de registros de horas

        Returns:
            Lista com sugestões de otimização
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        if not entries:
            return []

        # Agrupar horas por caso
        case_hours = {}
        for entry in entries:
            case_id = entry.get('case_id')
            if case_id:
                if case_id not in case_hours:
                    case_hours[case_id] = {
                        'hours': 0,
                        'entries': [],
                        'case_title': entry.get('case_title', ''),
                    }
                case_hours[case_id]['hours'] += float(entry.get('hours', 0))
                case_hours[case_id]['entries'].append(entry)

        # Analisar distribuição e sugerir otimizações
        suggestions = []
        total_hours = sum(c['hours'] for c in case_hours.values())

        for case_id, data in case_hours.items():
            # Verificar se horas estão abaixo do mínimo faturável
            if data['hours'] < 0.5:
                suggestions.append({
                    'case_id': case_id,
                    'case_title': data['case_title'],
                    'current_hours': data['hours'],
                    'issue': 'Horas abaixo do mínimo faturável (0.5h)',
                    'recommendation': 'Agrupar com outras atividades do mesmo caso ou arredondar para 0.5h',
                    'priority': 'medium',
                })

            # Verificar concentração excessiva
            if total_hours > 0 and data['hours'] / total_hours > 0.6:
                suggestions.append({
                    'case_id': case_id,
                    'case_title': data['case_title'],
                    'current_hours': data['hours'],
                    'issue': f"Concentração de {data['hours']/total_hours*100:.1f}% das horas em um único caso",
                    'recommendation': 'Revisar se atividades foram distribuídas corretamente entre casos',
                    'priority': 'low',
                })

        return suggestions
