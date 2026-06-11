"""
Views do módulo Financeiro - Copilot/IA.
Endpoints para integração com IA para:
- Previsão de fluxo de caixa
- Sugestão de honorários
- Análise de risco de inadimplência
- Geração de mensagens de cobrança
"""
import logging
from decimal import Decimal
from django.db.models import Sum, Q, F
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cases.models import Client, LegalCase, MovimentacaoFinanceira, OABFeeTable
from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
from .services.financial_ai_service import FinancialAIService

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def copilot_predict_cashflow(request):
    """
    Previsão de fluxo de caixa com IA.

    GET: Retorna previsão baseada nos dados atuais
    POST: Aceita parâmetros customizados

    Query params:
    - period: número de dias para previsão (default: 30)
    """
    try:
        period_days = int(request.query_params.get('period', 30))
        if period_days > 90:
            return Response(
                {'error': 'Período máximo de 90 dias'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar histórico de movimentações (últimos 6 meses)
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        movimentacoes = MovimentacaoFinanceira.objects.filter(
            data_vencimento__gte=six_months_ago,
            status='paid'
        ).order_by('data_vencimento')

        # Agrupar por mês
        historical_data = []
        for month in range(6):
            month_start = timezone.now() - timezone.timedelta(days=30 * (month + 1))
            month_end = timezone.now() - timezone.timedelta(days=30 * month)

            month_revenue = movimentacoes.filter(
                data_vencimento__gte=month_start,
                data_vencimento__lt=month_end,
                tipo='receita'
            ).aggregate(total=Sum('valor'))['total'] or 0

            month_expenses = movimentacoes.filter(
                data_vencimento__gte=month_start,
                data_vencimento__lt=month_end,
                tipo='despesa'
            ).aggregate(total=Sum('valor'))['total'] or 0

            historical_data.append({
                'month': f'Mês {-month}' if month > 0 else 'Atual',
                'revenue': float(month_revenue),
                'expenses': float(month_expenses),
            })

        # Buscar contas a receber
        current_receivables = []
        receivables = MovimentacaoFinanceira.objects.filter(
            tipo='receita',
            status__in=['pending', 'overdue']
        ).order_by('data_vencimento')[:20]

        for rec in receivables:
            days_overdue = 0
            if rec.status == 'overdue' or (rec.data_vencimento and rec.data_vencimento < timezone.now().date()):
                days_overdue = (timezone.now().date() - rec.data_vencimento).days if rec.data_vencimento else 0

            current_receivables.append({
                'id': str(rec.id),
                'value': float(rec.valor or 0),
                'status': 'overdue' if days_overdue > 0 else 'pending',
                'days_overdue': days_overdue,
                'description': rec.descricao or '',
            })

        # Buscar contas a pagar
        current_payables = []
        payables = MovimentacaoFinanceira.objects.filter(
            tipo='despesa',
            status__in=['pending', 'overdue']
        ).order_by('data_vencimento')[:20]

        for pay in payables:
            days_until_due = 0
            if pay.data_vencimento:
                days_until_due = (pay.data_vencimento - timezone.now().date()).days

            current_payables.append({
                'id': str(pay.id),
                'value': float(pay.valor or 0),
                'status': 'overdue' if days_until_due < 0 else 'pending',
                'days_until_due': max(0, days_until_due),
                'description': pay.descricao or '',
            })

        # Chamar serviço de IA
        result = FinancialAIService.predict_cash_flow(
            period_days=period_days,
            historical_data=historical_data,
            current_receivables=current_receivables,
            current_payables=current_payables,
        )

        return Response({
            'success': True,
            'data': result,
            'period_days': period_days,
        })

    except Exception as e:
        logger.error(f'Erro na previsão de fluxo de caixa: {e}', exc_info=True)
        return Response(
            {'error': f'Erro ao gerar previsão: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_suggest_fees(request):
    """
    Sugestão de honorários com IA.

    POST body:
    - case_id: UUID do caso (opcional)
    - specialty: especialidade jurídica
    - service_type: tipo de serviço
    - valor_causa: valor da causa
    - complexity: complexidade (baixa/media/alta)
    - client_id: UUID do cliente (opcional)
    """
    try:
        data = request.data

        # Dados do caso
        case_data = {
            'specialty': data.get('specialty', 'civel'),
            'service_type': data.get('service_type', 'acao_simples'),
            'valor_causa': float(data.get('valor_causa', 0) or 0),
            'complexity': data.get('complexity', 'media'),
            'phase': data.get('phase', 'conhecimento'),
        }

        # Dados do cliente
        client_data = {'client_type': 'pessoa_fisica', 'history_summary': 'Sem histórico'}
        client_id = data.get('client_id')
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                client_data['client_type'] = 'pessoa_juridica' if client.cpf_cnpj and len(client.cpf_cnpj) > 14 else 'pessoa_fisica'

                # Buscar histórico de honorários
                historical_fees = MovimentacaoFinanceira.objects.filter(
                    caso__cliente=client,
                    tipo='receita',
                    status='paid'
                ).values('valor', 'descricao')[:5]

                client_data['history_summary'] = f'{historical_fees.count()} pagamentos históricos'
            except Client.DoesNotExist:
                pass

        # Buscar tabela OAB
        oab_table = None
        oab_entry = OABFeeTable.objects.filter(
            service_category=case_data['specialty']
        ).first()

        if oab_entry:
            oab_table = {
                'consulta': float(oab_entry.minimum_value or 500),
                'peticao_inicial': float(oab_entry.suggested_value or 2000),
                'acao_simples': float(oab_entry.suggested_value or 3000),
                'acao_complexa': float(oab_entry.suggested_value or 5000) if oab_entry.suggested_value else 5000,
            }

        # Buscar honorários históricos similares
        historical_fees = []
        if data.get('case_id'):
            similar_cases = LegalCase.objects.filter(
                especialidade=case_data['specialty']
            ).exclude(id=data['case_id'])[:5]

            for case in similar_cases:
                fees = MovimentacaoFinanceira.objects.filter(
                    caso=case,
                    tipo='receita',
                    status='paid'
                ).values('valor', 'descricao').first()

                if fees:
                    historical_fees.append({
                        'service_type': fees['descricao'] or case_data['service_type'],
                        'value': float(fees['valor'] or 0),
                        'outcome': 'paid',
                    })

        # Chamar serviço de IA
        result = FinancialAIService.suggest_fees(
            case_data=case_data,
            client_data=client_data,
            oab_table=oab_table,
            historical_fees=historical_fees if historical_fees else None,
        )

        return Response({
            'success': True,
            'data': result,
        })

    except Exception as e:
        logger.error(f'Erro na sugestão de honorários: {e}', exc_info=True)
        return Response(
            {'error': f'Erro ao gerar sugestão: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_analyze_risk(request):
    """
    Análise de risco de inadimplência com IA.

    POST body:
    - client_id: UUID do cliente
    """
    try:
        client_id = request.data.get('client_id')

        if not client_id:
            return Response(
                {'error': 'client_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar cliente
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Cliente não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Buscar histórico de pagamentos
        payment_history = []
        payments = MovimentacaoFinanceira.objects.filter(
            caso__cliente=client,
            tipo='receita'
        ).order_by('-data_vencimento')[:20]

        for payment in payments:
            status_payment = 'paid_on_time'
            delay_days = 0

            if payment.status == 'paid':
                if payment.data_pagamento and payment.data_vencimento:
                    delta = (payment.data_pagamento - payment.data_vencimento).days
                    if delta > 0:
                        status_payment = 'paid_late'
                        delay_days = delta
            elif payment.status == 'overdue' or (payment.data_vencimento and payment.data_vencimento < timezone.now().date()):
                status_payment = 'overdue'
                delay_days = (timezone.now().date() - payment.data_vencimento).days if payment.data_vencimento else 0

            payment_history.append({
                'status': status_payment,
                'delay_days': delay_days,
                'value': float(payment.valor or 0),
            })

        # Buscar dívidas atuais
        outstanding_debts = []
        debts = MovimentacaoFinanceira.objects.filter(
            caso__cliente=client,
            tipo='receita',
            status__in=['pending', 'overdue']
        ).order_by('data_vencimento')

        for debt in debts:
            days_overdue = 0
            if debt.data_vencimento:
                days_overdue = (timezone.now().date() - debt.data_vencimento).days

            outstanding_debts.append({
                'value': float(debt.valor or 0),
                'days_overdue': max(0, days_overdue),
                'description': debt.descricao or '',
            })

        # Chamar serviço de IA
        result = FinancialAIService.analyze_default_risk(
            client_id=str(client.id),
            client_name=client.name or client.company_name or 'Cliente',
            payment_history=payment_history,
            outstanding_debts=outstanding_debts,
        )

        return Response({
            'success': True,
            'data': result,
            'client': {
                'id': str(client.id),
                'name': client.name or client.company_name,
            }
        })

    except Exception as e:
        logger.error(f'Erro na análise de risco: {e}', exc_info=True)
        return Response(
            {'error': f'Erro ao analisar risco: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def copilot_generate_collection(request):
    """
    Geração de mensagem de cobrança com IA.

    POST body:
    - client_id: UUID do cliente (opcional, para buscar nome)
    - client_name: Nome do cliente
    - debt_value: Valor da dívida
    - days_overdue: Dias em atraso
    - invoice_number: Número da fatura (opcional)
    """
    try:
        data = request.data

        client_name = data.get('client_name', '')
        client_id = data.get('client_id')

        # Buscar nome do cliente se não fornecido
        if not client_name and client_id:
            try:
                client = Client.objects.get(id=client_id)
                client_name = client.name or client.company_name or 'Cliente'
            except Client.DoesNotExist:
                client_name = 'Cliente'

        if not client_name:
            client_name = 'Cliente'

        debt_value = float(data.get('debt_value', 0) or 0)
        days_overdue = int(data.get('days_overdue', 0) or 0)
        invoice_number = data.get('invoice_number', '')

        # Buscar histórico do cliente (opcional)
        client_history = None
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                total_payments = MovimentacaoFinanceira.objects.filter(
                    caso__cliente=client,
                    tipo='receita'
                ).count()

                late_payments = MovimentacaoFinanceira.objects.filter(
                    caso__cliente=client,
                    tipo='receita',
                    status='overdue'
                ).count()

                if total_payments > 0:
                    client_history = f'{total_payments} pagamentos históricos, {late_payments} em atraso'
            except Client.DoesNotExist:
                pass

        # Chamar serviço de IA
        message = FinancialAIService.generate_collection_message(
            client_name=client_name,
            debt_value=debt_value,
            days_overdue=days_overdue,
            invoice_number=invoice_number if invoice_number else None,
            client_history=client_history,
        )

        return Response({
            'success': True,
            'data': {
                'message': message,
                'client_name': client_name,
                'debt_value': debt_value,
                'days_overdue': days_overdue,
            }
        })

    except Exception as e:
        logger.error(f'Erro ao gerar mensagem de cobrança: {e}', exc_info=True)
        return Response(
            {'error': f'Erro ao gerar mensagem: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
