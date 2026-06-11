"""
Serviço de fases processuais — gera automaticamente as fases padrão
de um processo judicial brasileiro com base na especialidade do caso.
"""
from datetime import timedelta


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATES DE FASES POR ESPECIALIDADE
# ─────────────────────────────────────────────────────────────────────────────

TRABALHISTA_PHASES = [
    {'order': 1, 'name': 'Petição Inicial', 'description': 'Elaboração e protocolo da petição inicial', 'days_from_start': 0, 'default_status': 'completed'},
    {'order': 2, 'name': 'Distribuição', 'description': 'Distribuição do processo ao juízo competente', 'days_from_start': 1, 'default_status': 'completed'},
    {'order': 3, 'name': 'Citação do Réu', 'description': 'Citação da parte contrária para apresentar defesa', 'days_from_start': 5, 'default_status': 'completed'},
    {'order': 4, 'name': 'Contestação', 'description': 'Prazo para apresentação de contestação (15 dias)', 'days_from_start': 20, 'default_status': 'in_progress'},
    {'order': 5, 'name': 'Réplica', 'description': 'Réplica à contestação (10 dias)', 'days_from_start': 30, 'default_status': 'pending'},
    {'order': 6, 'name': 'Audiência de Conciliação', 'description': 'Tentativa de acordo entre as partes', 'days_from_start': 60, 'default_status': 'pending'},
    {'order': 7, 'name': 'Instrução Processual', 'description': 'Produção de provas, oitiva de testemunhas', 'days_from_start': 90, 'default_status': 'pending'},
    {'order': 8, 'name': 'Alegações Finais', 'description': 'Apresentação das alegações finais pelas partes', 'days_from_start': 100, 'default_status': 'pending'},
    {'order': 9, 'name': 'Sentença', 'description': 'Prolação da sentença pelo juiz', 'days_from_start': 120, 'default_status': 'pending'},
    {'order': 10, 'name': 'Recurso Ordinário', 'description': 'Prazo para interposição de recurso (8 dias)', 'days_from_start': 128, 'default_status': 'pending'},
    {'order': 11, 'name': 'Trânsito em Julgado', 'description': 'Certificação do trânsito em julgado', 'days_from_start': 150, 'default_status': 'pending'},
    {'order': 12, 'name': 'Execução', 'description': 'Fase de execução/cumprimento de sentença', 'days_from_start': 160, 'default_status': 'pending'},
]

CRIMINAL_PHASES = [
    {'order': 1, 'name': 'Queixa-Crime / Denúncia', 'description': 'Oferecimento da queixa-crime ou denúncia', 'days_from_start': 0, 'default_status': 'completed'},
    {'order': 2, 'name': 'Recebimento', 'description': 'Análise e recebimento da denúncia/queixa pelo juiz', 'days_from_start': 10, 'default_status': 'completed'},
    {'order': 3, 'name': 'Citação do Réu', 'description': 'Citação do acusado para apresentar resposta', 'days_from_start': 15, 'default_status': 'completed'},
    {'order': 4, 'name': 'Resposta à Acusação', 'description': 'Prazo para resposta escrita (10 dias)', 'days_from_start': 25, 'default_status': 'in_progress'},
    {'order': 5, 'name': 'Audiência de Instrução', 'description': 'Oitiva de testemunhas e interrogatório', 'days_from_start': 60, 'default_status': 'pending'},
    {'order': 6, 'name': 'Alegações Finais', 'description': 'Memoriais ou debates orais', 'days_from_start': 70, 'default_status': 'pending'},
    {'order': 7, 'name': 'Sentença', 'description': 'Prolação da sentença', 'days_from_start': 90, 'default_status': 'pending'},
    {'order': 8, 'name': 'Apelação', 'description': 'Prazo para recurso de apelação (5 dias)', 'days_from_start': 95, 'default_status': 'pending'},
    {'order': 9, 'name': 'Trânsito em Julgado', 'description': 'Certificação do trânsito em julgado', 'days_from_start': 120, 'default_status': 'pending'},
]

CONSUMIDOR_PHASES = [
    {'order': 1, 'name': 'Petição Inicial', 'description': 'Elaboração e protocolo da petição inicial', 'days_from_start': 0, 'default_status': 'completed'},
    {'order': 2, 'name': 'Distribuição', 'description': 'Distribuição do processo ao juízo competente', 'days_from_start': 1, 'default_status': 'completed'},
    {'order': 3, 'name': 'Citação do Réu', 'description': 'Citação da parte contrária para apresentar defesa', 'days_from_start': 10, 'default_status': 'completed'},
    {'order': 4, 'name': 'Audiência de Conciliação', 'description': 'Audiência de conciliação obrigatória (CPC art. 334)', 'days_from_start': 30, 'default_status': 'in_progress'},
    {'order': 5, 'name': 'Contestação', 'description': 'Prazo para apresentação de contestação (15 dias após audiência)', 'days_from_start': 45, 'default_status': 'pending'},
    {'order': 6, 'name': 'Réplica', 'description': 'Réplica à contestação (15 dias)', 'days_from_start': 60, 'default_status': 'pending'},
    {'order': 7, 'name': 'Saneamento', 'description': 'Decisão de saneamento e organização do processo', 'days_from_start': 75, 'default_status': 'pending'},
    {'order': 8, 'name': 'Instrução Processual', 'description': 'Produção de provas e audiência de instrução', 'days_from_start': 100, 'default_status': 'pending'},
    {'order': 9, 'name': 'Alegações Finais', 'description': 'Apresentação das alegações finais pelas partes', 'days_from_start': 115, 'default_status': 'pending'},
    {'order': 10, 'name': 'Sentença', 'description': 'Prolação da sentença pelo juiz', 'days_from_start': 130, 'default_status': 'pending'},
    {'order': 11, 'name': 'Recurso de Apelação', 'description': 'Prazo para interposição de recurso (15 dias)', 'days_from_start': 145, 'default_status': 'pending'},
    {'order': 12, 'name': 'Trânsito em Julgado', 'description': 'Certificação do trânsito em julgado', 'days_from_start': 180, 'default_status': 'pending'},
]

TRIBUTARIO_PHASES = [
    {'order': 1, 'name': 'Petição Inicial', 'description': 'Elaboração e protocolo da petição inicial ou defesa administrativa', 'days_from_start': 0, 'default_status': 'completed'},
    {'order': 2, 'name': 'Distribuição', 'description': 'Distribuição do processo ao juízo competente', 'days_from_start': 1, 'default_status': 'completed'},
    {'order': 3, 'name': 'Liminar / Tutela', 'description': 'Pedido de tutela antecipada ou liminar', 'days_from_start': 5, 'default_status': 'completed'},
    {'order': 4, 'name': 'Citação da Fazenda', 'description': 'Citação da Fazenda Pública para contestar', 'days_from_start': 15, 'default_status': 'in_progress'},
    {'order': 5, 'name': 'Contestação', 'description': 'Prazo em dobro da Fazenda Pública (30 dias)', 'days_from_start': 45, 'default_status': 'pending'},
    {'order': 6, 'name': 'Réplica', 'description': 'Réplica à contestação (15 dias)', 'days_from_start': 60, 'default_status': 'pending'},
    {'order': 7, 'name': 'Perícia Contábil', 'description': 'Realização de perícia contábil/técnica', 'days_from_start': 90, 'default_status': 'pending'},
    {'order': 8, 'name': 'Alegações Finais', 'description': 'Apresentação das alegações finais', 'days_from_start': 120, 'default_status': 'pending'},
    {'order': 9, 'name': 'Sentença', 'description': 'Prolação da sentença — sujeita a reexame necessário', 'days_from_start': 150, 'default_status': 'pending'},
    {'order': 10, 'name': 'Recurso de Apelação', 'description': 'Prazo para recurso (30 dias — Fazenda)', 'days_from_start': 180, 'default_status': 'pending'},
    {'order': 11, 'name': 'Trânsito em Julgado', 'description': 'Certificação do trânsito em julgado', 'days_from_start': 240, 'default_status': 'pending'},
    {'order': 12, 'name': 'Execução / Precatório', 'description': 'Fase de execução ou expedição de precatório', 'days_from_start': 260, 'default_status': 'pending'},
]

FAMILIA_PHASES = [
    {'order': 1, 'name': 'Petição Inicial', 'description': 'Elaboração e protocolo da petição inicial', 'days_from_start': 0, 'default_status': 'completed'},
    {'order': 2, 'name': 'Distribuição', 'description': 'Distribuição ao juízo de família competente', 'days_from_start': 1, 'default_status': 'completed'},
    {'order': 3, 'name': 'Citação do Réu', 'description': 'Citação da parte contrária', 'days_from_start': 10, 'default_status': 'completed'},
    {'order': 4, 'name': 'Audiência de Mediação', 'description': 'Audiência de mediação/conciliação familiar', 'days_from_start': 30, 'default_status': 'in_progress'},
    {'order': 5, 'name': 'Contestação', 'description': 'Prazo para apresentação de contestação (15 dias)', 'days_from_start': 45, 'default_status': 'pending'},
    {'order': 6, 'name': 'Estudo Social / Psicológico', 'description': 'Laudo social ou avaliação psicológica (se aplicável)', 'days_from_start': 70, 'default_status': 'pending'},
    {'order': 7, 'name': 'Audiência de Instrução', 'description': 'Audiência de instrução e julgamento', 'days_from_start': 100, 'default_status': 'pending'},
    {'order': 8, 'name': 'Alegações Finais', 'description': 'Manifestação final das partes e MP', 'days_from_start': 115, 'default_status': 'pending'},
    {'order': 9, 'name': 'Sentença', 'description': 'Prolação da sentença', 'days_from_start': 130, 'default_status': 'pending'},
    {'order': 10, 'name': 'Recurso de Apelação', 'description': 'Prazo para recurso (15 dias)', 'days_from_start': 145, 'default_status': 'pending'},
    {'order': 11, 'name': 'Trânsito em Julgado', 'description': 'Certificação do trânsito em julgado', 'days_from_start': 180, 'default_status': 'pending'},
]

# Fases genéricas para cível e demais especialidades
CIVEL_PHASES = [
    {'order': 1, 'name': 'Petição Inicial', 'description': 'Elaboração e protocolo da petição inicial', 'days_from_start': 0, 'default_status': 'completed'},
    {'order': 2, 'name': 'Distribuição', 'description': 'Distribuição do processo ao juízo competente', 'days_from_start': 1, 'default_status': 'completed'},
    {'order': 3, 'name': 'Citação do Réu', 'description': 'Citação da parte contrária para apresentar defesa', 'days_from_start': 10, 'default_status': 'completed'},
    {'order': 4, 'name': 'Audiência de Conciliação', 'description': 'Audiência de conciliação ou mediação (CPC art. 334)', 'days_from_start': 30, 'default_status': 'in_progress'},
    {'order': 5, 'name': 'Contestação', 'description': 'Prazo para apresentação de contestação (15 dias)', 'days_from_start': 45, 'default_status': 'pending'},
    {'order': 6, 'name': 'Réplica', 'description': 'Réplica à contestação (15 dias)', 'days_from_start': 60, 'default_status': 'pending'},
    {'order': 7, 'name': 'Saneamento', 'description': 'Decisão de saneamento e organização do processo', 'days_from_start': 75, 'default_status': 'pending'},
    {'order': 8, 'name': 'Instrução Processual', 'description': 'Produção de provas, perícias e audiência de instrução', 'days_from_start': 100, 'default_status': 'pending'},
    {'order': 9, 'name': 'Alegações Finais', 'description': 'Apresentação das alegações finais pelas partes', 'days_from_start': 115, 'default_status': 'pending'},
    {'order': 10, 'name': 'Sentença', 'description': 'Prolação da sentença pelo juiz', 'days_from_start': 130, 'default_status': 'pending'},
    {'order': 11, 'name': 'Recurso de Apelação', 'description': 'Prazo para interposição de recurso (15 dias)', 'days_from_start': 145, 'default_status': 'pending'},
    {'order': 12, 'name': 'Trânsito em Julgado', 'description': 'Certificação do trânsito em julgado', 'days_from_start': 180, 'default_status': 'pending'},
    {'order': 13, 'name': 'Cumprimento de Sentença', 'description': 'Fase de cumprimento de sentença', 'days_from_start': 200, 'default_status': 'pending'},
]

# Mapeamento especialidade -> template de fases
PHASE_TEMPLATES = {
    'trabalhista': TRABALHISTA_PHASES,
    'criminal': CRIMINAL_PHASES,
    'consumidor': CONSUMIDOR_PHASES,
    'tributario': TRIBUTARIO_PHASES,
    'familia': FAMILIA_PHASES,
    # Demais especialidades usam o template cível genérico
    'civel': CIVEL_PHASES,
    'administrativo': CIVEL_PHASES,
    'previdenciario': CIVEL_PHASES,
    'empresarial': CIVEL_PHASES,
    'ambiental': CIVEL_PHASES,
    'imobiliario': CIVEL_PHASES,
    'outros': CIVEL_PHASES,
}


def get_phases_template(especialidade: str):
    """Retorna o template de fases para a especialidade dada."""
    return PHASE_TEMPLATES.get(especialidade, CIVEL_PHASES)


def create_phases_for_case(caso, override_statuses=None):
    """
    Cria os registros CasePhase para um caso recém-criado.

    Args:
        caso: instância de LegalCase
        override_statuses: dict opcional {order: status} para sobrescrever status padrão
    """
    from apps.cases.models import CasePhase

    template = get_phases_template(caso.especialidade)
    start_date = (caso.data_distribuicao or caso.created_at.date())

    phases_to_create = []
    for phase_def in template:
        order = phase_def['order']
        status = phase_def['default_status']
        if override_statuses and order in override_statuses:
            status = override_statuses[order]

        estimated = start_date + timedelta(days=phase_def['days_from_start'])
        actual = estimated if status == 'completed' else None

        phases_to_create.append(CasePhase(
            caso=caso,
            order=order,
            name=phase_def['name'],
            description=phase_def['description'],
            status=status,
            estimated_date=estimated,
            actual_date=actual,
        ))

    CasePhase.objects.bulk_create(phases_to_create)
    return phases_to_create
