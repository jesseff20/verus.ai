"""
Serviço de IA para análise financeira do módulo Financeiro.
Integração com Copilot para:
- Previsão de fluxo de caixa
- Sugestão de honorários baseada em padrões históricos
- Análise de risco de inadimplência
- Geração de mensagens de cobrança personalizadas
"""
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class FinancialAIService:
    """Serviço de IA para análise financeira."""

    @staticmethod
    async def predict_cash_flow(
        period_days: int,
        historical_data: List[Dict[str, Any]],
        current_receivables: List[Dict[str, Any]],
        current_payables: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Previsão de fluxo de caixa para os próximos dias.

        Args:
            period_days: Número de dias para previsão
            historical_data: Histórico de movimentações (receitas/despesas)
            current_receivables: Contas a receber atuais
            current_payables: Contas a pagar atuais

        Returns:
            Dict com:
            - predicted_revenue: valor previsto de receitas
            - predicted_expenses: valor previsto de despesas
            - net_cash_flow: fluxo líquido
            - daily_forecast: previsão dia a dia
            - confidence: 0-100
            - recommendations: lista de recomendações
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Preparar resumo dos dados históricos
        historical_summary = []
        for entry in historical_data[-12:]:  # Últimos 12 registros
            historical_summary.append({
                'month': entry.get('month', 'N/A'),
                'revenue': float(entry.get('revenue', 0)),
                'expenses': float(entry.get('expenses', 0)),
            })

        # Preparar contas a receber
        receivables_total = sum(
            float(r.get('value', 0)) for r in current_receivables
        )
        receivables_overdue = sum(
            float(r.get('value', 0)) for r in current_receivables
            if r.get('status') == 'overdue'
        )

        # Preparar contas a pagar
        payables_total = sum(
            float(p.get('value', 0)) for p in current_payables
        )
        payables_due_soon = sum(
            float(p.get('value', 0)) for p in current_payables
            if p.get('days_until_due', 999) <= 7
        )

        prompt = f"""
Analise os dados financeiros e faça uma previsão de fluxo de caixa para os próximos {period_days} dias.

**Histórico Mensal (últimos meses):**
{historical_summary}

**Contas a Receber:**
- Total: R$ {receivables_total:.2f}
- Em atraso: R$ {receivables_overdue:.2f}

**Contas a Pagar:**
- Total: R$ {payables_total:.2f}
- Vencendo em 7 dias: R$ {payables_due_soon:.2f}

**Tarefa:**
1. Estime receitas e despesas para o período
2. Projete fluxo de caixa diário (simplificado)
3. Identifique possíveis problemas de caixa
4. Dê recomendações acionáveis

**Formato de resposta (JSON):**
{{
    "predicted_revenue": 0000.00,
    "predicted_expenses": 0000.00,
    "net_cash_flow": 0000.00,
    "daily_forecast": [
        {{"day": 1, "revenue": 000, "expenses": 000, "balance": 000}},
        {{"day": 7, "revenue": 000, "expenses": 000, "balance": 000}},
        {{"day": 15, "revenue": 000, "expenses": 000, "balance": 000}},
        {{"day": 30, "revenue": 000, "expenses": 000, "balance": 000}}
    ],
    "confidence": 75,
    "warnings": ["alerta 1", "alerta 2"],
    "recommendations": ["recomendação 1", "recomendação 2"]
}}
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.3)

            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'predicted_revenue': float(result.get('predicted_revenue', 0)),
                    'predicted_expenses': float(result.get('predicted_expenses', 0)),
                    'net_cash_flow': float(result.get('net_cash_flow', 0)),
                    'daily_forecast': result.get('daily_forecast', []),
                    'confidence': result.get('confidence', 50),
                    'warnings': result.get('warnings', []),
                    'recommendations': result.get('recommendations', []),
                }
        except Exception as e:
            logger.warning(f'Erro na previsão de fluxo de caixa: {e}')

        # Fallback heurístico
        avg_monthly_revenue = sum(h.get('revenue', 0) for h in historical_summary) / max(len(historical_summary), 1)
        avg_monthly_expenses = sum(h.get('expenses', 0) for h in historical_summary) / max(len(historical_summary), 1)

        daily_factor = min(period_days / 30, 1)
        predicted_revenue = receivables_total * 0.7 + (avg_monthly_revenue * daily_factor * 0.3)
        predicted_expenses = payables_total * 0.8 + (avg_monthly_expenses * daily_factor * 0.2)

        return {
            'predicted_revenue': round(predicted_revenue, 2),
            'predicted_expenses': round(predicted_expenses, 2),
            'net_cash_flow': round(predicted_revenue - predicted_expenses, 2),
            'daily_forecast': [],
            'confidence': 40,
            'warnings': ['Previsão baseada em cálculo heurístico (IA indisponível)'],
            'recommendations': [
                'Acompanhe de perto as contas a receber em atraso',
                'Negocie prazos com fornecedores se necessário',
            ],
        }

    @staticmethod
    async def suggest_fees(
        case_data: Dict[str, Any],
        client_data: Dict[str, Any],
        oab_table: Optional[Dict[str, Any]] = None,
        historical_fees: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Sugestão de honorários baseada em caso, cliente e tabela OAB.

        Args:
            case_data: Dados do caso (especialidade, valor_causa, complexidade)
            client_data: Dados do cliente (tipo, histórico)
            oab_table: Tabela OAB de referência
            historical_fees: Honorários históricos similares

        Returns:
            Dict com:
            - min_value, max_value: faixa sugerida
            - suggested_value: valor recomendado
            - percentage: percentual sugerido (se aplicável)
            - fee_type: fixed|percentage|mixed|success
            - factors: fatores considerados
            - justification: justificativa detalhada
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Tabela OAB base (valores de referência)
        oab_base = oab_table or {
            'consulta': 500,
            'peticao_inicial': 2000,
            'contestacao': 2500,
            'acao_simples': 3000,
            'acao_complexa': 5000,
            'recursos': 2000,
        }

        # Multiplicadores por especialidade
        specialty_multipliers = {
            'civel': 1.0,
            'criminal': 1.3,
            'trabalhista': 1.1,
            'tributario': 1.5,
            'familia': 1.2,
            'empresarial': 1.4,
            'previdenciario': 1.0,
            'administrativo': 1.1,
            'consumidor': 0.9,
            'imobiliario': 1.2,
        }

        # Histórico de honorários similares
        historical_summary = []
        if historical_fees:
            for fee in historical_fees[:5]:
                historical_summary.append({
                    'service': fee.get('service_type', 'N/A'),
                    'value': float(fee.get('value', 0)),
                    'outcome': fee.get('outcome', 'N/A'),
                })

        prompt = f"""
Sugira honorários advocatícios justos e competitivos para este caso.

**Dados do Caso:**
- Especialidade: {case_data.get('specialty', 'N/A')}
- Tipo de serviço: {case_data.get('service_type', 'N/A')}
- Valor da causa: R$ {case_data.get('valor_causa', 0):.2f}
- Complexidade: {case_data.get('complexity', 'media')}
- Fase: {case_data.get('phase', 'N/A')}

**Dados do Cliente:**
- Tipo: {client_data.get('client_type', 'pessoa_fisica')}
- Histórico: {client_data.get('history_summary', 'Sem histórico')}

**Tabela OAB Referência:**
- Consulta: R$ {oab_base['consulta']}
- Petição inicial: R$ {oab_base['peticao_inicial']}
- Ação simples: R$ {oab_base['acao_simples']}
- Ação complexa: R$ {oab_base['acao_complexa']}

**Honorários Históricos Similares:**
{historical_summary if historical_summary else 'Nenhum histórico disponível'}

**Tarefa:**
1. Calcule faixa de honorários considerando:
   - Tabela OAB como piso
   - Complexidade e valor da causa
   - Histórico de casos similares
   - Perfil do cliente
2. Sugira tipo de cobrança (fixo, percentual, êxito, misto)
3. Justifique a recomendação

**Formato de resposta (JSON):**
{{
    "min_value": 0000.00,
    "max_value": 0000.00,
    "suggested_value": 0000.00,
    "percentage": 00.0,
    "fee_type": "fixed|percentage|mixed|success",
    "factors": ["fator 1", "fator 2"],
    "justification": "texto detalhado",
    "oab_reference": 0000.00
}}
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.3)

            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'min_value': float(result.get('min_value', 0)),
                    'max_value': float(result.get('max_value', 0)),
                    'suggested_value': float(result.get('suggested_value', 0)),
                    'percentage': float(result.get('percentage', 0)),
                    'fee_type': result.get('fee_type', 'fixed'),
                    'factors': result.get('factors', []),
                    'justification': result.get('justification', ''),
                    'oab_reference': float(result.get('oab_reference', 0)),
                }
        except Exception as e:
            logger.warning(f'Erro na sugestão de honorários: {e}')

        # Fallback heurístico
        base = oab_base.get('acao_simples', 3000)
        multiplier = specialty_multipliers.get(case_data.get('specialty', 'civel'), 1.0)
        complexity_factor = {'baixa': 0.8, 'media': 1.0, 'alta': 1.5}.get(
            case_data.get('complexity', 'media'), 1.0
        )

        valor_causa = float(case_data.get('valor_causa', 0))
        percentage_suggested = 10.0 if valor_causa > 0 else 0

        calculated_by_percentage = (valor_causa * percentage_suggested / 100) if valor_causa > 0 else 0

        base_value = base * multiplier * complexity_factor
        suggested_value = max(base_value, calculated_by_percentage) if valor_causa > 0 else base_value

        return {
            'min_value': round(suggested_value * 0.8, 2),
            'max_value': round(suggested_value * 1.5, 2),
            'suggested_value': round(suggested_value, 2),
            'percentage': percentage_suggested,
            'fee_type': 'mixed' if valor_causa > 0 else 'fixed',
            'factors': [
                f'Especialidade: {case_data.get("specialty", "civel")}',
                f'Complexidade: {case_data.get("complexity", "media")}',
                'Cálculo baseado na tabela OAB',
            ],
            'justification': 'Valor calculado heuristicamente baseado na tabela OAB, especialidade e complexidade.',
            'oab_reference': base,
        }

    @staticmethod
    async def analyze_default_risk(
        client_id: str,
        client_name: str,
        payment_history: List[Dict[str, Any]],
        outstanding_debts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Análise de risco de inadimplência do cliente.

        Args:
            client_id: ID do cliente
            client_name: Nome do cliente
            payment_history: Histórico de pagamentos
            outstanding_debts: Dívidas atuais

        Returns:
            Dict com:
            - risk_level: low|medium|high|critical
            - risk_score: 0-100
            - factors: fatores de risco identificados
            - recommendations: recomendações de ação
            - suggested_payment_terms: condições de pagamento sugeridas
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Analisar histórico de pagamentos
        total_invoices = len(payment_history)
        paid_on_time = sum(1 for p in payment_history if p.get('status') == 'paid_on_time')
        paid_late = sum(1 for p in payment_history if p.get('status') == 'paid_late')
        overdue = sum(1 for p in payment_history if p.get('status') == 'overdue')

        on_time_rate = (paid_on_time / max(total_invoices, 1)) * 100
        avg_delay_days = sum(p.get('delay_days', 0) for p in payment_history if p.get('status') == 'paid_late') / max(paid_late, 1)

        # Total devido atual
        total_outstanding = sum(float(d.get('value', 0)) for d in outstanding_debts)
        oldest_debt_days = max((d.get('days_overdue', 0) for d in outstanding_debts), default=0)

        prompt = f"""
Analise o risco de inadimplência deste cliente.

**Dados do Cliente:**
- Nome: {client_name}
- ID: {client_id}

**Histórico de Pagamentos:**
- Total de faturas: {total_invoices}
- Pagas em dia: {paid_on_time} ({on_time_rate:.1f}%)
- Pagas atrasadas: {paid_late}
- Vencidas: {overdue}
- Atraso médio: {avg_delay_days:.1f} dias

**Dívidas Atuais:**
- Total devido: R$ {total_outstanding:.2f}
- Dias do débito mais antigo: {oldest_debt_days}

**Tarefa:**
1. Classifique o nível de risco (low/medium/high/critical)
2. Atribua um score de 0-100
3. Liste fatores de risco relevantes
4. Sugira condições de pagamento apropriadas
5. Dê recomendações de ação

**Formato de resposta (JSON):**
{{
    "risk_level": "low|medium|high|critical",
    "risk_score": 0-100,
    "factors": ["fator 1", "fator 2"],
    "recommendations": ["recomendação 1", "recomendação 2"],
    "suggested_payment_terms": "termos sugeridos",
    "analysis": "análise detalhada"
}}
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.3)

            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'risk_level': result.get('risk_level', 'medium'),
                    'risk_score': result.get('risk_score', 50),
                    'factors': result.get('factors', []),
                    'recommendations': result.get('recommendations', []),
                    'suggested_payment_terms': result.get('suggested_payment_terms', ''),
                    'analysis': result.get('analysis', ''),
                }
        except Exception as e:
            logger.warning(f'Erro na análise de risco: {e}')

        # Fallback heurístico
        risk_score = 50  # Começa neutro
        factors = []

        # Penalizar por baixa taxa de pagamento em dia
        if on_time_rate < 50:
            risk_score += 30
            factors.append(f'Baixa taxa de pagamento em dia ({on_time_rate:.0f}%)')
        elif on_time_rate < 75:
            risk_score += 15
            factors.append(f'Taxa de pagamento em dia abaixo do ideal ({on_time_rate:.0f}%)')

        # Penalizar por atrasos frequentes
        if paid_late > total_invoices * 0.3:
            risk_score += 20
            factors.append(f'Muitos pagamentos atrasados ({paid_late}/{total_invoices})')

        # Penalizar por dívidas vencidas
        if overdue > 0:
            risk_score += 25
            factors.append(f'{overdue} fatura(s) vencida(s)')

        # Penalizar por débito muito antigo
        if oldest_debt_days > 90:
            risk_score += 20
            factors.append(f'Débito antigo ({oldest_debt_days} dias)')

        # Determinar nível de risco
        if risk_score >= 80:
            risk_level = 'critical'
        elif risk_score >= 60:
            risk_level = 'high'
        elif risk_score >= 40:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        recommendations = []
        if risk_level in ('critical', 'high'):
            recommendations = [
                'Exigir pagamento antecipado ou entrada significativa',
                'Considerar recusa de novos casos até regularização',
                'Enviar notificação formal de cobrança',
            ]
        elif risk_level == 'medium':
            recommendations = [
                'Oferecer plano de parcelamento',
                'Acompanhar de perto vencimentos',
                'Enviar lembretes proativos',
            ]
        else:
            recommendations = [
                'Manter condições padrão de pagamento',
                'Considerar fidelização com condições especiais',
            ]

        return {
            'risk_level': risk_level,
            'risk_score': min(100, max(0, risk_score)),
            'factors': factors[:5],
            'recommendations': recommendations,
            'suggested_payment_terms': 'À vista ou até 3x sem juros' if risk_level == 'low' else 'Entrada + parcelamento',
            'analysis': f'Análise heurística baseada em {total_invoices} pagamentos históricos.',
        }

    @staticmethod
    async def generate_collection_message(
        client_name: str,
        debt_value: float,
        days_overdue: int,
        invoice_number: Optional[str] = None,
        client_history: Optional[str] = None,
    ) -> str:
        """
        Gera mensagem personalizada de cobrança.

        Args:
            client_name: Nome do cliente
            debt_value: Valor da dívida
            days_overdue: Dias em atraso
            invoice_number: Número da fatura (opcional)
            client_history: Histórico do cliente (opcional)

        Returns:
            Mensagem personalizada para envio (email/whatsapp)
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        # Determinar tom baseado nos dias de atraso
        if days_overdue <= 7:
            tone = 'amigável e compreensivo'
        elif days_overdue <= 30:
            tone = 'profissional e direto'
        elif days_overdue <= 60:
            tone = 'firme mas educado'
        else:
            tone = 'formal e urgente'

        prompt = f"""
Gere uma mensagem de cobrança profissional e personalizada.

**Dados da Cobrança:**
- Cliente: {client_name}
- Valor: R$ {debt_value:.2f}
- Dias em atraso: {days_overdue}
- Fatura: {invoice_number or 'N/A'}
- Histórico: {client_history or 'Sem histórico específico'}

**Tom da mensagem:** {tone}

**Objetivo:**
1. Lembrar o cliente do débito de forma educada
2. Informar valor e tempo de atraso claramente
3. Oferecer opções de pagamento/parcelamento
4. Manter relacionamento profissional
5. Ter call-to-action claro

**Formato:** Mensagem pronta para envio (email ou whatsapp), ~80-150 palavras.
Incluir saudação inicial e despedida profissional.
"""

        try:
            llm = UnifiedLLMService.get_service()
            response = await llm.generate_async(prompt, temperature=0.7)
            return response.strip()
        except Exception as e:
            logger.warning(f'Erro ao gerar mensagem de cobrança: {e}')
            return FinancialAIService._fallback_collection_message(
                client_name, debt_value, days_overdue, invoice_number
            )

    @staticmethod
    def _fallback_collection_message(
        client_name: str,
        debt_value: float,
        days_overdue: int,
        invoice_number: Optional[str] = None,
    ) -> str:
        """Fallback de mensagem de cobrança quando IA não está disponível."""

        if days_overdue <= 7:
            return f"""
Olá, {client_name}! Tudo bem?

Passando apenas para lembrar que identificamos um pagamento pendente de R$ {debt_value:.2f} (Fatura {invoice_number or 'N/A'}) com vencimento há {days_overdue} dias.

Sabemos que imprevistos acontecem! Caso já tenha realizado o pagamento, desconsidere esta mensagem.

Se precisar de alguma condição especial ou tiver dúvidas, estamos à disposição.

Atenciosamente,
"""
        elif days_overdue <= 30:
            return f"""
Prezado(a) {client_name},

Identificamos que o pagamento de R$ {debt_value:.2f} (Fatura {invoice_number or 'N/A'}) está em atraso há {days_overdue} dias.

Gostaríamos de ajudar a regularizar esta situação. Estamos disponíveis para negociar condições de pagamento que se adequem à sua situação.

Entre em contato conosco para conversarmos.

Atenciosamente,
"""
        else:
            return f"""
Prezado(a) {client_name},

Informamos que o débito de R$ {debt_value:.2f} (Fatura {invoice_number or 'N/A'}) encontra-se em atraso há {days_overdue} dias.

É importante regularizarmos esta situação o quanto antes para evitarmos medidas mais severas.

Solicitamos que entre em contato urgentemente para negociarmos uma solução.

Atenciosamente,
"""
