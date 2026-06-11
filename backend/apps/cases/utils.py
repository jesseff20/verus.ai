"""
Utilitários para o app cases — incluindo cálculo de prazos em dias úteis CNJ.
Conforme Resolução CNJ 65/2008 e suas atualizações.
"""
from datetime import date, timedelta
from typing import Optional


# Feriados nacionais fixos (dia, mês)
FERIADOS_NACIONAIS_FIXOS = [
    (1, 1),   # Ano Novo
    (21, 4),  # Tiradentes
    (1, 5),   # Dia do Trabalho
    (7, 9),   # Independência
    (12, 10), # Nossa Senhora Aparecida
    (2, 11),  # Finados
    (15, 11), # Proclamação da República
    (20, 11), # Consciência Negra (Lei 14.759/2023)
    (25, 12), # Natal
]


def is_dia_util(d: date, feriados_extras: Optional[list] = None) -> bool:
    """
    Retorna True se a data for um dia útil (sem feriados nacionais fixos).
    feriados_extras: lista de date objects para feriados locais adicionais.
    """
    # Final de semana
    if d.weekday() >= 5:
        return False

    # Feriados nacionais fixos
    if (d.day, d.month) in FERIADOS_NACIONAIS_FIXOS:
        return False

    # Feriados extras (locais, móveis, etc.)
    if feriados_extras and d in feriados_extras:
        return False

    return True


def adicionar_dias_uteis(data_inicio: date, dias: int, feriados_extras: Optional[list] = None) -> date:
    """
    Adiciona N dias úteis a uma data, conforme critério CNJ.
    Se a data_inicio cair em dia não-útil, o prazo começa no próximo dia útil.
    """
    atual = data_inicio
    contados = 0

    while contados < dias:
        atual += timedelta(days=1)
        if is_dia_util(atual, feriados_extras):
            contados += 1

    return atual


def calcular_prazo_util(data_inicio: date, dias: int, feriados_extras: Optional[list] = None) -> date:
    """
    Calcula o prazo final em dias úteis a partir de data_inicio.
    Alias mais semântico para adicionar_dias_uteis.
    """
    return adicionar_dias_uteis(data_inicio, dias, feriados_extras)


def dias_uteis_entre(data_inicio: date, data_fim: date, feriados_extras: Optional[list] = None) -> int:
    """
    Conta quantos dias úteis existem entre duas datas (exclusivo na data_inicio, inclusivo na data_fim).
    """
    if data_fim <= data_inicio:
        return 0

    atual = data_inicio
    count = 0

    while atual < data_fim:
        atual += timedelta(days=1)
        if is_dia_util(atual, feriados_extras):
            count += 1

    return count
