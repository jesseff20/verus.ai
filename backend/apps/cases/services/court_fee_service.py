"""
Serviço de Custas Judiciais — cálculo de custas por tribunal/estado brasileiro.
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db.models import Sum, Q

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Tabelas de custas por estado (valores de referência 2024/2025)
# ─────────────────────────────────────────────────────────────────────────────

# Cada entrada: { 'percentual': Decimal, 'minimo': Decimal, 'maximo': Decimal, 'formula': str }
COURT_FEE_TABLES = {
    'SP': {
        'custas_iniciais': {
            'percentual': Decimal('1.0'),
            'minimo': Decimal('107.65'),
            'maximo': Decimal('100000.00'),
            'formula': '1% do valor da causa (mín R$107,65 / máx R$100.000,00) — TJSP Lei 11.608/2003',
        },
        'custas_preparo': {
            'percentual': Decimal('4.0'),
            'minimo': Decimal('107.65'),
            'maximo': Decimal('100000.00'),
            'formula': '4% do valor da causa (mín R$107,65 / máx R$100.000,00) — TJSP',
        },
        'porte_remessa': {
            'percentual': Decimal('0'),
            'minimo': Decimal('32.35'),
            'maximo': Decimal('32.35'),
            'formula': 'Valor fixo R$32,35 por volume — TJSP',
        },
    },
    'RJ': {
        'custas_iniciais': {
            'percentual': Decimal('1.0'),
            'minimo': Decimal('83.45'),
            'maximo': Decimal('50000.00'),
            'formula': '1% do valor da causa (mín R$83,45 / máx R$50.000,00) — TJRJ',
        },
        'custas_preparo': {
            'percentual': Decimal('2.0'),
            'minimo': Decimal('83.45'),
            'maximo': Decimal('50000.00'),
            'formula': '2% do valor da causa (mín R$83,45 / máx R$50.000,00) — TJRJ',
        },
        'porte_remessa': {
            'percentual': Decimal('0'),
            'minimo': Decimal('25.00'),
            'maximo': Decimal('25.00'),
            'formula': 'Valor fixo R$25,00 — TJRJ',
        },
    },
    'MG': {
        'custas_iniciais': {
            'percentual': Decimal('1.0'),
            'minimo': Decimal('70.00'),
            'maximo': Decimal('44600.00'),
            'formula': '1% do valor da causa (mín R$70,00 / máx R$44.600,00) — TJMG',
        },
        'custas_preparo': {
            'percentual': Decimal('2.0'),
            'minimo': Decimal('70.00'),
            'maximo': Decimal('44600.00'),
            'formula': '2% do valor da causa (mín R$70,00 / máx R$44.600,00) — TJMG',
        },
    },
    'RS': {
        'custas_iniciais': {
            'percentual': Decimal('1.5'),
            'minimo': Decimal('90.00'),
            'maximo': Decimal('60000.00'),
            'formula': '1,5% do valor da causa (mín R$90,00 / máx R$60.000,00) — TJRS',
        },
        'custas_preparo': {
            'percentual': Decimal('2.0'),
            'minimo': Decimal('90.00'),
            'maximo': Decimal('60000.00'),
            'formula': '2% do valor da causa (mín R$90,00 / máx R$60.000,00) — TJRS',
        },
    },
    'PR': {
        'custas_iniciais': {
            'percentual': Decimal('1.0'),
            'minimo': Decimal('75.00'),
            'maximo': Decimal('50000.00'),
            'formula': '1% do valor da causa (mín R$75,00 / máx R$50.000,00) — TJPR',
        },
        'custas_preparo': {
            'percentual': Decimal('2.0'),
            'minimo': Decimal('75.00'),
            'maximo': Decimal('50000.00'),
            'formula': '2% do valor da causa (mín R$75,00 / máx R$50.000,00) — TJPR',
        },
    },
    'BA': {
        'custas_iniciais': {
            'percentual': Decimal('1.0'),
            'minimo': Decimal('60.00'),
            'maximo': Decimal('40000.00'),
            'formula': '1% do valor da causa (mín R$60,00 / máx R$40.000,00) — TJBA',
        },
    },
    'DF': {
        'custas_iniciais': {
            'percentual': Decimal('1.0'),
            'minimo': Decimal('50.00'),
            'maximo': Decimal('35000.00'),
            'formula': '1% do valor da causa (mín R$50,00 / máx R$35.000,00) — TJDFT',
        },
    },
    # Justiça Federal: sem custas para PF em muitas situações
    'FEDERAL': {
        'custas_iniciais': {
            'percentual': Decimal('1.0'),
            'minimo': Decimal('10.64'),
            'maximo': Decimal('1818.09'),
            'formula': '1% do valor da causa (mín R$10,64 / máx R$1.818,09) — Justiça Federal (Res. CJF 168/2021)',
        },
        'custas_preparo': {
            'percentual': Decimal('1.0'),
            'minimo': Decimal('10.64'),
            'maximo': Decimal('1818.09'),
            'formula': '1% do valor da causa (mín R$10,64 / máx R$1.818,09) — Justiça Federal',
        },
    },
    # Justiça do Trabalho: isento em 1ª instância
    'TRABALHISTA': {
        'custas_iniciais': {
            'percentual': Decimal('0'),
            'minimo': Decimal('0'),
            'maximo': Decimal('0'),
            'formula': 'Isento — Custas trabalhistas são devidas apenas pelo vencido (CLT art. 789)',
        },
        'custas_recursais': {
            'percentual': Decimal('2.0'),
            'minimo': Decimal('10.64'),
            'maximo': Decimal('43478.60'),
            'formula': '2% do valor da condenação (mín R$10,64) — CLT art. 789',
        },
    },
}

# Mapeamento de tribunal para tipo
COURT_TO_TYPE = {
    'TRT': 'TRABALHISTA',
    'TST': 'TRABALHISTA',
    'TRF': 'FEDERAL',
    'STF': 'FEDERAL',
    'STJ': 'FEDERAL',
}


class CourtFeeService:
    """Serviço para cálculo e gestão de custas judiciais."""

    @staticmethod
    def _get_fee_table(court: str, state: str) -> dict:
        """Retorna tabela de custas para o tribunal/estado."""
        # Check tribunal type first
        court_upper = court.upper().strip()
        for prefix, fee_type in COURT_TO_TYPE.items():
            if court_upper.startswith(prefix):
                return COURT_FEE_TABLES.get(fee_type, {})

        # Estadual
        return COURT_FEE_TABLES.get(state.upper().strip(), {})

    @staticmethod
    def calculate_fee(case, fee_type: str, court: str, state: str) -> dict:
        """
        Calcula custas judiciais com base na tabela do tribunal/estado.

        Returns dict: { amount, formula, case_value, fee_type, court, state }
        """
        from apps.cases.models import CourtFeeGuide

        case_value = case.valor_causa or Decimal('0')
        fee_table = CourtFeeService._get_fee_table(court, state)

        if fee_type not in fee_table:
            # Tipo não encontrado — usar custas_iniciais como fallback ou zero
            return {
                'amount': Decimal('0'),
                'formula': f'Tipo "{fee_type}" não encontrado para {court}/{state}. Verifique o tribunal e estado.',
                'case_value': case_value,
                'fee_type': fee_type,
                'court': court,
                'state': state,
            }

        entry = fee_table[fee_type]
        percentual = entry['percentual']
        minimo = entry['minimo']
        maximo = entry['maximo']
        formula = entry['formula']

        if percentual > 0 and case_value > 0:
            calculated = (percentual / Decimal('100')) * case_value
            calculated = max(calculated, minimo)
            calculated = min(calculated, maximo)
        else:
            calculated = minimo

        calculated = calculated.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'amount': calculated,
            'formula': formula,
            'case_value': case_value,
            'fee_type': fee_type,
            'court': court,
            'state': state,
        }

    @staticmethod
    def generate_guide_pdf(fee_id) -> str:
        """
        Gera guia PDF para uma custa. Retorna path do arquivo gerado.
        Implementação simplificada — em produção usaria ReportLab/WeasyPrint.
        """
        from apps.cases.models import CourtFeeGuide

        try:
            fee = CourtFeeGuide.objects.select_related('case', 'created_by').get(id=fee_id)
        except CourtFeeGuide.DoesNotExist:
            raise ValueError('Guia de custas não encontrada.')

        # Gerar HTML simples como placeholder
        html_content = f"""
        <html>
        <head><title>Guia de Custas — {fee.get_fee_type_display()}</title></head>
        <body>
            <h1>Guia de Custas Judiciais</h1>
            <p><strong>Caso:</strong> {fee.case.titulo}</p>
            <p><strong>Tipo:</strong> {fee.get_fee_type_display()}</p>
            <p><strong>Tribunal:</strong> {fee.court} ({fee.state})</p>
            <p><strong>Valor:</strong> R$ {fee.calculated_amount}</p>
            <p><strong>Vencimento:</strong> {fee.due_date.strftime('%d/%m/%Y')}</p>
            <p><strong>Fórmula:</strong> {fee.calculation_formula}</p>
            {f'<p><strong>Código de Barras:</strong> {fee.barcode}</p>' if fee.barcode else ''}
        </body>
        </html>
        """
        return html_content

    @staticmethod
    def check_overdue_fees():
        """Identifica e atualiza custas vencidas."""
        from apps.cases.models import CourtFeeGuide

        today = timezone.now().date()
        overdue = CourtFeeGuide.objects.filter(
            payment_status='pending',
            due_date__lt=today,
        )
        count = overdue.update(payment_status='overdue')
        logger.info(f"[CourtFeeService] {count} custas marcadas como vencidas.")
        return count

    @staticmethod
    def get_fee_summary(user, case=None) -> dict:
        """Retorna resumo agregado de custas."""
        from apps.cases.models import CourtFeeGuide

        qs = CourtFeeGuide.objects.all()
        if case:
            qs = qs.filter(case=case)
        elif not user.is_staff:
            qs = qs.filter(
                Q(case__advogado_responsavel=user) |
                Q(case__created_by=user) |
                Q(created_by=user)
            )

        total_pending = qs.filter(payment_status='pending').aggregate(
            total=Sum('calculated_amount')
        )['total'] or Decimal('0')

        total_paid = qs.filter(payment_status='paid').aggregate(
            total=Sum('calculated_amount')
        )['total'] or Decimal('0')

        total_overdue = qs.filter(payment_status='overdue').aggregate(
            total=Sum('calculated_amount')
        )['total'] or Decimal('0')

        return {
            'total_pending': str(total_pending),
            'total_paid': str(total_paid),
            'total_overdue': str(total_overdue),
            'count_pending': qs.filter(payment_status='pending').count(),
            'count_paid': qs.filter(payment_status='paid').count(),
            'count_overdue': qs.filter(payment_status='overdue').count(),
            'count_exempt': qs.filter(payment_status='exempt').count(),
            'count_waived': qs.filter(payment_status='waived').count(),
        }

    @staticmethod
    def mark_paid(fee_id, payment_date, proof_file=None):
        """Marca uma custa como paga."""
        from apps.cases.models import CourtFeeGuide

        try:
            fee = CourtFeeGuide.objects.get(id=fee_id)
        except CourtFeeGuide.DoesNotExist:
            raise ValueError('Guia de custas não encontrada.')

        fee.payment_status = 'paid'
        fee.payment_date = payment_date
        if proof_file:
            fee.payment_proof = proof_file
        fee.save()
        return fee

    @staticmethod
    def get_available_states():
        """Retorna estados com tabelas de custas disponíveis."""
        return [
            {'code': k, 'name': k}
            for k in COURT_FEE_TABLES.keys()
        ]

    @staticmethod
    def get_available_fee_types(court: str, state: str):
        """Retorna tipos de custas disponíveis para o tribunal/estado."""
        fee_table = CourtFeeService._get_fee_table(court, state)
        from apps.cases.models import CourtFeeGuide
        type_map = dict(CourtFeeGuide.FEE_TYPE_CHOICES)
        return [
            {'code': k, 'name': type_map.get(k, k), 'formula': v['formula']}
            for k, v in fee_table.items()
        ]
