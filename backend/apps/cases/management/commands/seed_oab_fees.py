"""
Seed da Tabela OAB de Honorarios — todos os 27 estados com dados realistas.
Valores de referencia 2024, baseados nas tabelas de honorarios das seccionais da OAB.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.cases.models import OABFeeTable

# ---------------------------------------------------------------------------
# Multiplicadores regionais de custo (SP = 1.00 como referencia)
# SP/RJ/DF sao os mais caros; Norte/Nordeste tendem a ser mais baratos.
# ---------------------------------------------------------------------------
STATE_MULTIPLIERS = {
    'AC': Decimal('0.60'), 'AL': Decimal('0.62'), 'AM': Decimal('0.65'),
    'AP': Decimal('0.58'), 'BA': Decimal('0.72'), 'CE': Decimal('0.68'),
    'DF': Decimal('0.95'), 'ES': Decimal('0.78'), 'GO': Decimal('0.74'),
    'MA': Decimal('0.60'), 'MG': Decimal('0.82'), 'MS': Decimal('0.72'),
    'MT': Decimal('0.73'), 'PA': Decimal('0.64'), 'PB': Decimal('0.61'),
    'PE': Decimal('0.70'), 'PI': Decimal('0.58'), 'PR': Decimal('0.83'),
    'RJ': Decimal('0.92'), 'RN': Decimal('0.63'), 'RO': Decimal('0.62'),
    'RR': Decimal('0.59'), 'RS': Decimal('0.84'), 'SC': Decimal('0.82'),
    'SE': Decimal('0.61'), 'SP': Decimal('1.00'), 'TO': Decimal('0.63'),
}

# ---------------------------------------------------------------------------
# Tabela-base de servicos (valores de SP como referencia)
# Cada entrada: (category, service_type, min_value, suggested_value, percentage)
# percentage pode ser None quando nao se aplica.
# ---------------------------------------------------------------------------
BASE_SERVICES = [
    # ── CIVEL ──────────────────────────────────────────────────────
    ('civel', 'Acao ordinaria', 5500, 8500, 20),
    ('civel', 'Acao de cobranca', 3800, 5500, 20),
    ('civel', 'Acao de indenizacao', 4500, 7000, 20),
    ('civel', 'Execucao de titulo extrajudicial', 3800, 5500, 15),
    ('civel', 'Medida cautelar', 3500, 5000, 15),
    ('civel', 'Recurso de apelacao', 4000, 6000, None),
    ('civel', 'Agravo de instrumento', 3000, 4500, None),
    ('civel', 'Habeas data', 3500, 5500, None),

    # ── TRABALHISTA ────────────────────────────────────────────────
    ('trabalhista', 'Reclamacao trabalhista', 3500, 5500, 20),
    ('trabalhista', 'Recurso ordinario', 3000, 5000, None),
    ('trabalhista', 'Mandado de seguranca trabalhista', 4000, 6000, None),

    # ── CRIMINAL ───────────────────────────────────────────────────
    ('criminal', 'Defesa em inquerito policial', 5000, 8000, None),
    ('criminal', 'Defesa em acao penal', 8000, 15000, None),
    ('criminal', 'Habeas corpus', 5000, 8000, None),
    ('criminal', 'Recurso criminal', 4000, 6500, None),

    # ── FAMILIA ────────────────────────────────────────────────────
    ('familia', 'Divorcio consensual', 4000, 6000, None),
    ('familia', 'Divorcio litigioso', 6000, 10000, None),
    ('familia', 'Acao de alimentos', 3500, 5000, None),
    ('familia', 'Inventario e partilha', 6000, 12000, 6),
    ('familia', 'Guarda de menores', 4000, 6500, None),

    # ── TRIBUTARIO ─────────────────────────────────────────────────
    ('tributario', 'Acao anulatoria de debito fiscal', 5500, 9000, 20),
    ('tributario', 'Mandado de seguranca tributario', 5000, 8000, 20),
    ('tributario', 'Execucao fiscal (defesa)', 4500, 7500, 15),

    # ── EMPRESARIAL ────────────────────────────────────────────────
    ('empresarial', 'Constituicao de sociedade', 5000, 8000, None),
    ('empresarial', 'Recuperacao judicial', 15000, 30000, 5),
    ('empresarial', 'Falencia', 12000, 25000, 5),

    # ── PREVIDENCIARIO ─────────────────────────────────────────────
    ('previdenciario', 'Aposentadoria', 3500, 5500, 20),
    ('previdenciario', 'Auxilio-doenca', 3000, 4500, 20),
    ('previdenciario', 'BPC/LOAS', 3000, 4500, 20),

    # ── IMOBILIARIO ────────────────────────────────────────────────
    ('imobiliario', 'Acao de despejo', 3500, 5500, 20),
    ('imobiliario', 'Usucapiao', 5000, 8000, 10),
    ('imobiliario', 'Acao possessoria', 4000, 6500, 15),

    # ── CONSUMIDOR ─────────────────────────────────────────────────
    ('consumidor', 'Acao de reparacao de danos', 2500, 4000, 20),
    ('consumidor', 'Acao de obrigacao de fazer', 2800, 4500, 20),

    # ── ADMINISTRATIVO ─────────────────────────────────────────────
    ('administrativo', 'Mandado de seguranca administrativo', 5500, 9000, None),
    ('administrativo', 'Impugnacao a edital', 4500, 7000, None),
]

YEAR = 2024


def _round_to_50(value):
    """Arredonda para o multiplo de 50 mais proximo (valores mais 'reais')."""
    return Decimal(str(int(round(float(value) / 50.0) * 50)))


def generate_fee_data():
    """Gera os registros para todos os 27 estados."""
    records = []
    for state, multiplier in STATE_MULTIPLIERS.items():
        for category, stype, base_min, base_sug, pct in BASE_SERVICES:
            min_val = _round_to_50(Decimal(str(base_min)) * multiplier)
            sug_val = _round_to_50(Decimal(str(base_sug)) * multiplier)
            # Garante que sugerido >= minimo
            if sug_val < min_val:
                sug_val = min_val
            records.append({
                'state': state,
                'service_category': category,
                'service_type': stype,
                'minimum_value': min_val,
                'suggested_value': sug_val,
                'percentage': Decimal(str(pct)) if pct is not None else None,
                'year': YEAR,
            })
    return records


class Command(BaseCommand):
    help = 'Popula a tabela OAB de honorarios com dados de todos os 27 estados (2024)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Atualiza valores de registros ja existentes ao inves de pular.',
        )

    def handle(self, *args, **options):
        force_update = options.get('force_update', False)
        records = generate_fee_data()

        created = 0
        updated = 0
        skipped = 0

        for entry in records:
            lookup = {
                'state': entry['state'],
                'service_category': entry['service_category'],
                'service_type': entry['service_type'],
                'year': entry['year'],
            }
            defaults = {
                'minimum_value': entry['minimum_value'],
                'suggested_value': entry['suggested_value'],
                'percentage': entry['percentage'],
            }

            obj, was_created = OABFeeTable.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )

            if was_created:
                created += 1
            elif force_update:
                for attr, val in defaults.items():
                    setattr(obj, attr, val)
                obj.save()
                updated += 1
            else:
                skipped += 1

        total = len(records)
        msg = (
            f'Seed OAB concluido: {total} registros processados — '
            f'{created} criados, {updated} atualizados, {skipped} ja existiam.'
        )
        self.stdout.write(self.style.SUCCESS(msg))
