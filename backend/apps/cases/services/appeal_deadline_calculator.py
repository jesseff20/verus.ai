"""
Serviço de Cálculo de Prazos Recursais — Verus.AI.

Calcula automaticamente os prazos para os principais recursos do direito
brasileiro (CPC, CLT, CF, Lei 9.099), utilizando dias úteis conforme
Resolução CNJ 65/2008.
"""
from datetime import date
from typing import Optional

from apps.cases.utils import adicionar_dias_uteis


# ─────────────────────────────────────────────────────────────────────────────
# TABELA DE PRAZOS RECURSAIS
# ─────────────────────────────────────────────────────────────────────────────

PRAZOS_RECURSAIS = {
    'recurso_ordinario': {
        'dias': 8,
        'base_legal': 'CLT art. 895',
        'descricao': 'Recurso Ordinário (Trabalhista)',
    },
    'apelacao': {
        'dias': 15,
        'base_legal': 'CPC art. 1.003',
        'descricao': 'Apelação (Cível)',
    },
    'agravo_instrumento': {
        'dias': 15,
        'base_legal': 'CPC art. 1.015',
        'descricao': 'Agravo de Instrumento',
    },
    'agravo_interno': {
        'dias': 15,
        'base_legal': 'CPC art. 1.021',
        'descricao': 'Agravo Interno',
    },
    'recurso_especial': {
        'dias': 15,
        'base_legal': 'CPC art. 1.029',
        'descricao': 'Recurso Especial',
    },
    'recurso_extraordinario': {
        'dias': 15,
        'base_legal': 'CF art. 102',
        'descricao': 'Recurso Extraordinário',
    },
    'embargos_declaracao': {
        'dias': 5,
        'base_legal': 'CPC art. 1.023',
        'descricao': 'Embargos de Declaração',
    },
    'recurso_revista': {
        'dias': 8,
        'base_legal': 'CLT art. 896',
        'descricao': 'Recurso de Revista (Trabalhista)',
    },
    'recurso_inominado': {
        'dias': 10,
        'base_legal': 'Lei 9.099 art. 42',
        'descricao': 'Recurso Inominado (JEC)',
    },
}


class AppealDeadlineCalculator:
    """Calculadora de prazos recursais brasileiros."""

    @staticmethod
    def get_all_types():
        """Retorna todos os tipos de recurso com suas informações."""
        return {
            key: {
                'dias': info['dias'],
                'base_legal': info['base_legal'],
                'descricao': info['descricao'],
            }
            for key, info in PRAZOS_RECURSAIS.items()
        }

    @staticmethod
    def calculate_deadline(
        appeal_type: str,
        intimation_date: date,
        feriados_extras: Optional[list] = None,
    ) -> dict:
        """
        Calcula o prazo final de um recurso a partir da data de intimação.

        Args:
            appeal_type: chave do tipo de recurso (ex: 'apelacao')
            intimation_date: data de intimação/publicação
            feriados_extras: lista de feriados locais adicionais

        Returns:
            dict com deadline_date, dias, base_legal, descricao
        """
        if appeal_type not in PRAZOS_RECURSAIS:
            raise ValueError(f"Tipo de recurso desconhecido: {appeal_type}")

        info = PRAZOS_RECURSAIS[appeal_type]
        deadline_date = adicionar_dias_uteis(intimation_date, info['dias'], feriados_extras)

        return {
            'appeal_type': appeal_type,
            'deadline_date': deadline_date,
            'dias': info['dias'],
            'base_legal': info['base_legal'],
            'descricao': info['descricao'],
            'intimation_date': intimation_date,
        }

    @staticmethod
    def auto_create_appeal_deadlines(case, phase=None, user=None):
        """
        Cria automaticamente prazos recursais quando o caso entra na fase recursal.

        Args:
            case: instância de LegalCase
            phase: fase processual (opcional)
            user: usuário que disparou a ação

        Returns:
            lista de LegalDeadline criados
        """
        from apps.cases.models import LegalDeadline
        from django.utils import timezone

        today = timezone.now().date()
        created_deadlines = []

        # Determinar quais recursos são aplicáveis conforme especialidade
        if case.especialidade == 'trabalhista':
            appeal_types = ['recurso_ordinario', 'recurso_revista', 'embargos_declaracao']
        else:
            appeal_types = ['apelacao', 'agravo_instrumento', 'embargos_declaracao']

        for appeal_type in appeal_types:
            info = PRAZOS_RECURSAIS[appeal_type]

            # Verificar se já existe prazo recursal deste tipo para o caso
            existing = LegalDeadline.objects.filter(
                caso=case,
                appeal_type=appeal_type,
                auto_generated=True,
            ).exists()

            if existing:
                continue

            deadline_date = adicionar_dias_uteis(today, info['dias'])

            prazo = LegalDeadline.objects.create(
                caso=case,
                titulo=f"Prazo — {info['descricao']}",
                descricao=f"Prazo recursal automático. Base legal: {info['base_legal']}. "
                          f"{info['dias']} dias úteis a partir de {today.strftime('%d/%m/%Y')}.",
                tipo='recursal',
                prioridade='alta',
                data_prazo=deadline_date,
                appeal_type=appeal_type,
                base_legal=info['base_legal'],
                auto_generated=True,
                created_by=user,
            )
            created_deadlines.append(prazo)

        return created_deadlines
