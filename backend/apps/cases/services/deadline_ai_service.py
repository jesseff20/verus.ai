"""
Serviço de IA para cálculo e gestão inteligente de prazos processuais.

Funcionalidades:
- Cálculo de prazos em dias úteis considerando feriados
- Sugestão de estratégia baseada em urgência e tipo de prazo
- Agrupamento de prazos relacionados
- Identificação de prazos críticos
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.utils import timezone
from dateutil import rrule
import holidays

logger = logging.getLogger(__name__)


class DeadlineAIService:
    """Serviço de IA para gestão inteligente de prazos processuais."""

    # Tipos de prazo processual com seus padrões de cálculo
    DEADLINE_TYPES = {
        'contestacao': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 335'},
        'replica': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 350'},
        'apelacao': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 1.003'},
        'agravo_instrumento': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 1.018'},
        'agravo_interno': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 1.021'},
        'embargos_declaracao': {'dias': 5, 'tipo': 'uteis', 'base_legal': 'CPC art. 1.023'},
        'recurso_especial': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 1.041'},
        'recurso_extraordinario': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 1.035'},
        'resposta_acusacao': {'dias': 10, 'tipo': 'uteis', 'base_legal': 'CPP art. 396-A'},
        'alegacoes_finais': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPP art. 403'},
        'razoes_recurso': {'dias': 8, 'tipo': 'uteis', 'base_legal': 'CPP art. 600'},
        'contrarrazoes': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 1.010'},
        'impugnacao': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 525'},
        'cumprimento_sentenca': {'dias': 15, 'tipo': 'uteis', 'base_legal': 'CPC art. 523'},
        'execucao': {'dias': 30, 'tipo': 'uteis', 'base_legal': 'CPC art. 910'},
        'provas': {'dias': 10, 'tipo': 'uteis', 'base_legal': 'CPC art. 357'},
        'pericia': {'dias': 30, 'tipo': 'uteis', 'base_legal': 'CPC art. 476'},
        'manifestacao': {'dias': 5, 'tipo': 'uteis', 'base_legal': 'CPC art. 10'},
        'juntada': {'dias': 10, 'tipo': 'uteis', 'base_legal': 'CPC art. 230'},
        'despacho': {'dias': 5, 'tipo': 'uteis', 'base_legal': 'CPC art. 203'},
        'sentenca': {'dias': 30, 'tipo': 'corridos', 'base_legal': 'CPC art. 226'},
        'acordao': {'dias': 30, 'tipo': 'corridos', 'base_legal': 'CPC art. 456'},
    }

    # Feriados nacionais fixos
    NATIONAL_HOLIDAYS = {
        (1, 1): 'Confraternização Universal',
        (4, 21): 'Tiradentes',
        (5, 1): 'Dia do Trabalho',
        (9, 7): 'Independência do Brasil',
        (10, 12): 'Nossa Senhora Aparecida',
        (11, 2): 'Finados',
        (11, 15): 'Proclamação da República',
        (12, 25): 'Natal',
    }

    def __init__(self, state: Optional[str] = None):
        """
        Inicializa o serviço com opção de estado para feriados estaduais.

        Args:
            state: UF do estado para considerar feriados estaduais (ex: 'SP', 'RJ')
        """
        self.state = state or 'BR'
        self._holiday_cache = {}

    def get_brazil_holidays(self, year: int) -> List[datetime]:
        """Obtém feriados brasileiros de um ano específico."""
        cache_key = (year, self.state)
        if cache_key in self._holiday_cache:
            return self._holiday_cache[cache_key]

        # Feriados nacionais
        br_holidays = holidays.Brazil(years=year, subdiv=self.state if self.state != 'BR' else None)

        # Adicionar feriados forenses (quando aplicável)
        forenses = []
        if self.state:
            # 29 de junho - Dia de São Pedro (alguns tribunais)
            forenses.append(datetime(year, 6, 29))
            # 20 de janeiro - Dia de São Sebastião (RJ)
            if self.state == 'RJ':
                forenses.append(datetime(year, 1, 20))
            # 25 de janeiro - Aniversário de São Paulo
            if self.state == 'SP':
                forenses.append(datetime(year, 1, 25))
            # 9 de julho - Revolução Constitucionalista (SP)
            if self.state == 'SP':
                forenses.append(datetime(year, 7, 9))

        holidays_list = [datetime.strptime(str(d), '%Y-%m-%d') for d in br_holidays.keys()]
        holidays_list.extend([h for h in forenses if h.year == year])

        self._holiday_cache[cache_key] = holidays_list
        return holidays_list

    def is_business_day(self, date: datetime) -> bool:
        """Verifica se uma data é dia útil."""
        # Fim de semana
        if date.weekday() >= 5:
            return False

        # Feriados
        year = date.year
        holidays_list = self.get_brazil_holidays(year)

        # Se o feriado cair no fim de semana, já foi tratado
        date_only = date.date() if hasattr(date, 'date') else date
        for holiday in holidays_list:
            holiday_date = holiday.date() if hasattr(holiday, 'date') else holiday
            if date_only == holiday_date:
                return False

        return True

    def count_business_days(self, start_date: datetime, end_date: datetime) -> int:
        """Conta dias úteis entre duas datas."""
        if start_date > end_date:
            return 0

        count = 0
        current = start_date
        while current <= end_date:
            if self.is_business_day(current):
                count += 1
            current += timedelta(days=1)

        return count

    def add_business_days(self, start_date: datetime, days: int) -> datetime:
        """Adiciona dias úteis a uma data."""
        current = start_date
        added = 0

        while added < days:
            current += timedelta(days=1)
            if self.is_business_day(current):
                added += 1

        return current

    def calculate_deadline(
        self,
        deadline_type: str,
        start_date: str,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calcula prazo processual em dias úteis.

        Args:
            deadline_type: Tipo de prazo (contestacao, replica, apelacao, etc.)
            start_date: Data inicial (formato YYYY-MM-DD)
            case_data: Dados adicionais do caso (opcional)

        Returns:
            Dict com:
            - deadline_date: Data final do prazo
            - days_count: Número de dias (úteis ou corridos)
            - type: Tipo de contagem (uteis/corridos)
            - base_legal: Base legal do prazo
            - intermediate_dates: Datas intermediárias importantes
            - warnings: Alertas sobre o prazo
        """
        try:
            # Parse da data inicial
            if isinstance(start_date, str):
                start = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start = start_date

            # Verificar se é dia útil
            if not self.is_business_day(start):
                # Se não for dia útil, começa no próximo dia útil
                start = self.add_business_days(start, 1) if self.is_business_day(start + timedelta(days=1)) else start
                while not self.is_business_day(start):
                    start += timedelta(days=1)

            # Obter configuração do tipo de prazo
            deadline_config = self.DEADLINE_TYPES.get(deadline_type.lower(), {})

            if not deadline_config:
                # Tipo desconhecido - usar padrão
                logger.warning(f"Tipo de prazo '{deadline_type}' não reconhecido, usando padrão")
                days = 15
                count_type = 'uteis'
                base_legal = 'CPC art. 219 (prazo padrão)'
            else:
                days = deadline_config.get('dias', 15)
                count_type = deadline_config.get('tipo', 'uteis')
                base_legal = deadline_config.get('base_legal', '')

            # Calcular data final
            if count_type == 'uteis':
                end_date = self.add_business_days(start, days)
            else:
                end_date = start + timedelta(days=days)

            # Gerar datas intermediárias (50% e 75% do prazo)
            intermediate_dates = []
            if count_type == 'uteis':
                half = days // 2
                three_quarters = (days * 3) // 4
                intermediate_dates = [
                    {'marker': '50% do prazo', 'date': self.add_business_days(start, half).strftime('%Y-%m-%d')},
                    {'marker': '75% do prazo', 'date': self.add_business_days(start, three_quarters).strftime('%Y-%m-%d')},
                ]
            else:
                half = days // 2
                three_quarters = (days * 3) // 4
                intermediate_dates = [
                    {'marker': '50% do prazo', 'date': (start + timedelta(days=half)).strftime('%Y-%m-%d')},
                    {'marker': '75% do prazo', 'date': (start + timedelta(days=three_quarters)).strftime('%Y-%m-%d')},
                ]

            # Gerar alertas
            warnings = []
            today = timezone.now().date()
            days_remaining = (end_date.date() - today).days if hasattr(end_date, 'date') else (end_date - today).days

            if days_remaining < 0:
                warnings.append(f"Prazo já encerrou há {abs(days_remaining)} dias")
            elif days_remaining <= 3:
                warnings.append(f"ATENÇÃO: Prazo vence em {days_remaining} dias!")
            elif days_remaining <= 7:
                warnings.append(f"Prazo vence em {days_remaining} dias - organize-se")

            # Verificar se há audiências ou outros eventos no período
            if case_data:
                if case_data.get('audiencia_agendada'):
                    warnings.append("Audiência agendada no período - verificar compatibilidade")

            return {
                'deadline_date': end_date.strftime('%Y-%m-%d'),
                'days_count': days,
                'type': count_type,
                'base_legal': base_legal,
                'start_date': start.strftime('%Y-%m-%d'),
                'intermediate_dates': intermediate_dates,
                'warnings': warnings,
                'deadline_type': deadline_type,
            }

        except Exception as e:
            logger.error(f"Erro ao calcular prazo: {e}", exc_info=True)
            return {
                'error': f'Erro ao calcular prazo: {str(e)}',
                'deadline_date': None,
                'days_count': None,
            }

    def suggest_strategy(
        self,
        deadline_type: str,
        days_remaining: int,
        case_urgency: str = 'media',
    ) -> str:
        """
        Sugere estratégia de atuação baseada no tipo de prazo e urgência.

        Args:
            deadline_type: Tipo de prazo
            days_remaining: Dias restantes até o vencimento
            case_urgency: Nível de urgência do caso (alta, media, baixa)

        Returns:
            String com sugestão de estratégia
        """
        deadline_type_lower = deadline_type.lower()

        # Estratégias baseadas no tipo de prazo
        strategies = {
            'contestacao': {
                'alta': 'Prioridade máxima. Reunir todas as provas documentais imediatamente. Considerar pedido de dilação de prazo se necessário. Elaborar tese defensiva completa.',
                'media': 'Iniciar elaboração da contestação imediatamente. Reunir documentos em até 3 dias. Revisar tese jurídica com a equipe.',
                'baixa': 'Planejar contestação com calma. Verificar preliminares. Reunir documentação necessária gradualmente.',
            },
            'replica': {
                'alta': 'Analisar urgentemente os argumentos da contestação. Preparar réplica focando nos pontos fracos da defesa. Juntar documentos suplementares.',
                'media': 'Estudar contestação em detalhe. Preparar réplica estruturada. Considerar necessidade de provas suplementares.',
                'baixa': 'Analisar contestação com profundidade. Elaborar réplica bem fundamentada.',
            },
            'apelacao': {
                'alta': 'URGENTE: Elaborar razões de apelação imediatamente. Focar em vícios da sentença. Verificar preparo recursal.',
                'media': 'Analisar sentença em busca de erros. Estruturar razões de apelação. Verificar cabimento de agravo retido.',
                'baixa': 'Estudar sentença detalhadamente. Preparar apelação bem fundamentada.',
            },
            'agravo_instrumento': {
                'alta': 'Preparar agravo com urgência. Verificar requisitos de admissibilidade. Juntar peças obrigatórias.',
                'media': 'Analisar decisão agravada. Preparar instrumento com peças necessárias.',
                'baixa': 'Estudar viabilidade do recurso. Preparar agravo fundamentado.',
            },
            'embargos_declaracao': {
                'alta': 'URGENTE: Prazo de apenas 5 dias. Identificar obscuridade/contradição/omissão. Elaborar embargos objetivos.',
                'media': 'Analisar decisão em busca de vícios. Preparar embargos focados.',
                'baixa': 'Verificar necessidade de esclarecimentos. Elaborar embargos se cabível.',
            },
            'alegacoes_finais': {
                'alta': 'Síntese final urgente. Focar nos pontos decisivos. Reiterar provas produzidas.',
                'media': 'Preparar alegações bem estruturadas. Destacar provas favoráveis.',
                'baixa': 'Elaborar alegações completas. Revisar toda a instrução.',
            },
            'impugnacao': {
                'alta': 'Analisar cálculos/execução imediatamente. Verificar excessos. Preparar impugnação detalhada.',
                'media': 'Estudar petição inicial de execução. Preparar impugnação fundamentada.',
                'baixa': 'Analisar execução com calma. Verificar matérias defensivas.',
            },
            'provas': {
                'alta': 'URGENTE: Especificar provas imediatamente. Requerer perícias/ouvidas. Justificar necessidade.',
                'media': 'Planejar estratégia probatória. Requerer provas necessárias.',
                'baixa': 'Analisar necessidade de provas. Especificar no prazo legal.',
            },
        }

        # Obter estratégia base
        urgency_map = {'alta': 'alta', 'media': 'media', 'baixa': 'baixa'}
        urgency = urgency_map.get(case_urgency.lower(), 'media')

        base_strategy = strategies.get(deadline_type_lower, {}).get(urgency)

        if not base_strategy:
            # Estratégia genérica baseada na urgência
            generic = {
                'alta': 'PRIORIDADE MÁXIMA: Dedique atenção imediata a este prazo. Avalie necessidade de dilação ou medida emergencial.',
                'media': 'Organize-se para cumprir o prazo adequadamente. Planeje as etapas necessárias.',
                'baixa': 'Cumpra o prazo dentro do planejamento normal. Mantenha acompanhamento.',
            }
            base_strategy = generic.get(urgency, generic['media'])

        # Ajustar baseado nos dias restantes
        if days_remaining <= 0:
            return f"⚠️ PRAZO VENCIDO! {base_strategy} Verifique possibilidade de cumprimento extemporâneo ou preclusão."
        elif days_remaining <= 2:
            return f"🚨 URGÊNCIA EXTREMA! {base_strategy} Ação imediata necessária."
        elif days_remaining <= 5:
            return f"⚡ ALTA PRIORIDADE! {base_strategy} Dedique os próximos dias a esta tarefa."
        elif days_remaining <= 10:
            return f"📋 ATENÇÃO NECESSÁRIA! {base_strategy} Planeje a execução nas próximas semanas."
        else:
            return f"📅 PLANEJAMENTO! {base_strategy} Tempo adequado para preparação cuidadosa."

    def group_related_deadlines(self, deadlines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Agrupa prazos relacionados por caso ou por tipo recursal.

        Args:
            deadlines: Lista de prazos com dados (id, caso_id, tipo, titulo, data_prazo)

        Returns:
            Lista de grupos de prazos relacionados
        """
        if not deadlines:
            return []

        # Agrupar por caso
        by_case = {}
        for deadline in deadlines:
            case_id = deadline.get('caso_id') or deadline.get('case_id') or 'sem_caso'
            if case_id not in by_case:
                by_case[case_id] = {
                    'case_id': case_id,
                    'case_name': deadline.get('case_name') or deadline.get('caso_titulo', 'Caso não identificado'),
                    'deadlines': [],
                    'total': 0,
                    'pending': 0,
                    'overdue': 0,
                }

            by_case[case_id]['deadlines'].append(deadline)
            by_case[case_id]['total'] += 1

            if deadline.get('status') == 'pendente':
                by_case[case_id]['pending'] += 1

            # Verificar se está atrasado
            data_prazo = deadline.get('data_prazo')
            if data_prazo:
                try:
                    if isinstance(data_prazo, str):
                        prazo_date = datetime.strptime(data_prazo, '%Y-%m-%d').date()
                    else:
                        prazo_date = data_prazo

                    today = timezone.now().date()
                    if prazo_date < today and deadline.get('status') != 'concluido':
                        by_case[case_id]['overdue'] += 1
                except (ValueError, TypeError):
                    pass

        # Ordenar grupos por urgência (mais atrasados primeiro, depois mais pendentes)
        groups = list(by_case.values())
        groups.sort(key=lambda x: (-x['overdue'], -x['pending']))

        # Adicionar label de prioridade
        for group in groups:
            if group['overdue'] > 0:
                group['priority'] = 'critico'
                group['priority_label'] = f"⚠️ {group['overdue']} prazo(s) atrasado(s)"
            elif group['pending'] > 3:
                group['priority'] = 'alta'
                group['priority_label'] = f"📋 {group['pending']} prazos pendentes"
            else:
                group['priority'] = 'normal'
                group['priority_label'] = f"✓ {group['pending']} prazo(s) pendente(s)"

        return groups

    def identify_critical_deadlines(self, deadlines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identifica prazos críticos baseado em múltiplos fatores.

        Critérios de criticidade:
        - Prazo vencido ou vence em até 3 dias
        - Tipo de prazo importante (contestação, recursos)
        - Caso de alta prioridade
        - Cliente VIP

        Args:
            deadlines: Lista de prazos

        Returns:
            Lista de prazos críticos com justificativa
        """
        if not deadlines:
            return []

        critical = []
        today = timezone.now().date()

        # Tipos de prazo considerados críticos
        critical_types = [
            'contestacao', 'replica', 'apelacao', 'agravo_instrumento',
            'embargos_declaracao', 'resposta_acusacao', 'alegacoes_finais',
            'impugnacao', 'cumprimento_sentenca',
        ]

        for deadline in deadlines:
            reasons = []
            criticality_score = 0

            # Verificar data
            data_prazo = deadline.get('data_prazo')
            if data_prazo:
                try:
                    if isinstance(data_prazo, str):
                        prazo_date = datetime.strptime(data_prazo, '%Y-%m-%d').date()
                    else:
                        prazo_date = data_prazo

                    days_diff = (prazo_date - today).days

                    if days_diff < 0:
                        reasons.append(f"PRAZO VENCIDO há {abs(days_diff)} dias")
                        criticality_score += 100
                    elif days_diff == 0:
                        reasons.append("VENCE HOJE!")
                        criticality_score += 80
                    elif days_diff <= 2:
                        reasons.append(f"Vence em {days_diff} dias")
                        criticality_score += 60
                    elif days_diff <= 5:
                        reasons.append(f"Vence em {days_diff} dias")
                        criticality_score += 30
                except (ValueError, TypeError):
                    pass

            # Verificar tipo de prazo
            deadline_type = (deadline.get('tipo') or deadline.get('deadline_type') or '').lower()
            if deadline_type in critical_types:
                reasons.append(f"Tipo crítico: {deadline.get('tipo') or deadline.get('deadline_type')}")
                criticality_score += 20

            # Verificar prioridade do prazo
            prioridade = (deadline.get('prioridade') or '').lower()
            if prioridade == 'urgente':
                reasons.append("Prioridade: URGENTE")
                criticality_score += 40
            elif prioridade == 'alta':
                reasons.append("Prioridade: ALTA")
                criticality_score += 20

            # Verificar se é de caso prioritário
            case_priority = deadline.get('case_priority') or ''
            if case_priority == 'alta':
                reasons.append("Caso prioritário")
                criticality_score += 15

            # Verificar cliente VIP
            is_vip = deadline.get('client_vip') or deadline.get('cliente_vip') or False
            if is_vip:
                reasons.append("Cliente VIP")
                criticality_score += 10

            # Se tem pelo menos um motivo, adicionar à lista
            if reasons:
                deadline_copy = deadline.copy()
                deadline_copy['critical'] = True
                deadline_copy['criticality_score'] = criticality_score
                deadline_copy['critical_reasons'] = reasons

                # Determinar nível de criticidade
                if criticality_score >= 80:
                    deadline_copy['critical_level'] = 'extremo'
                    deadline_copy['critical_level_label'] = '🔴 EXTREMO'
                elif criticality_score >= 50:
                    deadline_copy['critical_level'] = 'alto'
                    deadline_copy['critical_level_label'] = '🟠 ALTO'
                elif criticality_score >= 30:
                    deadline_copy['critical_level'] = 'medio'
                    deadline_copy['critical_level_label'] = '🟡 MÉDIO'
                else:
                    deadline_copy['critical_level'] = 'baixo'
                    deadline_copy['critical_level_label'] = '🟢 BAIXO'

                critical.append(deadline_copy)

        # Ordenar por criticidade
        critical.sort(key=lambda x: -x['criticality_score'])

        return critical

    async def calculate_deadline_async(
        self,
        deadline_type: str,
        start_date: str,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Versão assíncrona do calculate_deadline."""
        return self.calculate_deadline(deadline_type, start_date, case_data)

    async def suggest_strategy_async(
        self,
        deadline_type: str,
        days_remaining: int,
        case_urgency: str = 'media',
    ) -> str:
        """Versão assíncrona do suggest_strategy."""
        return self.suggest_strategy(deadline_type, days_remaining, case_urgency)
