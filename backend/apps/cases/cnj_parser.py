"""
Utilitário para parsing do número CNJ de processo judicial.

Formato padrão CNJ (Resolução 65/2008):
  NNNNNNN-DD.AAAA.J.TT.OOOO

Campos:
  NNNNNNN  — número sequencial do processo (7 dígitos)
  DD       — dígitos verificadores (2 dígitos)
  AAAA     — ano de ajuizamento (4 dígitos)
  J        — código da justiça (1 dígito)
  TT       — código do tribunal (2 dígitos)
  OOOO     — código da origem/vara (4 dígitos)

Exemplos:
  0001234-12.2024.8.26.0100  →  TJSP, São Paulo, 2024
  0005678-99.2023.1.00.0001  →  STF, 2023
"""
import re
from dataclasses import dataclass
from typing import Optional

CNJ_PATTERN = re.compile(
    r'^(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})$'
)

# Código da Justiça (campo J)
JUSTICE_CODES = {
    '1': 'STF',
    '2': 'CNJ',
    '3': 'STJ',
    '4': 'Justiça Federal',
    '5': 'Justiça do Trabalho',
    '6': 'Justiça Eleitoral',
    '7': 'Justiça Militar da União',
    '8': 'Justiça Estadual',
    '9': 'Justiça Militar Estadual',
}

# Principais tribunais estaduais (J=8) — código TT → sigla
TRIBUNAL_ESTADUAL = {
    '01': 'TJAC', '02': 'TJAL', '03': 'TJAP', '04': 'TJAM', '05': 'TJBA',
    '06': 'TJCE', '07': 'TJDF', '08': 'TJES', '09': 'TJGO', '10': 'TJMA',
    '11': 'TJMT', '12': 'TJMS', '13': 'TJMG', '14': 'TJPA', '15': 'TJPB',
    '16': 'TJPR', '17': 'TJPE', '18': 'TJPI', '19': 'TJRJ', '20': 'TJRN',
    '21': 'TJRS', '22': 'TJRO', '23': 'TJRR', '24': 'TJSC', '25': 'TJSE',
    '26': 'TJSP', '27': 'TJTO',
}

# Tribunais Regionais Federais (J=4)
TRIBUNAL_FEDERAL = {
    '01': 'TRF-1', '02': 'TRF-2', '03': 'TRF-3',
    '04': 'TRF-4', '05': 'TRF-5', '06': 'TRF-6',
}

# Tribunais Regionais do Trabalho (J=5)
TRIBUNAL_TRABALHO = {f'{i:02d}': f'TRT-{i}' for i in range(1, 25)}


@dataclass
class CNJParseResult:
    raw: str
    is_valid: bool
    numero: Optional[str] = None        # sequencial
    digitos: Optional[str] = None       # verificadores
    ano: Optional[int] = None
    justica: Optional[str] = None       # código J
    justica_label: Optional[str] = None
    tribunal_code: Optional[str] = None
    tribunal: Optional[str] = None      # sigla do tribunal
    origem: Optional[str] = None        # código OOOO
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'raw': self.raw,
            'is_valid': self.is_valid,
            'numero': self.numero,
            'digitos': self.digitos,
            'ano': self.ano,
            'justica': self.justica,
            'justica_label': self.justica_label,
            'tribunal_code': self.tribunal_code,
            'tribunal': self.tribunal,
            'origem': self.origem,
            'error': self.error,
        }


def parse_cnj(numero: str) -> CNJParseResult:
    """
    Faz o parse de um número CNJ.

    Args:
        numero: String com o número CNJ (com ou sem formatação)

    Returns:
        CNJParseResult com todos os campos extraídos
    """
    # Normaliza: remove espaços
    raw = numero.strip()

    # Tenta reintroduzir a formatação se vier sem ela
    # ex: "00012341220248260100" → "0001234-12.2024.8.26.0100"
    normalized = raw
    if re.match(r'^\d{20}$', raw):
        normalized = f'{raw[:7]}-{raw[7:9]}.{raw[9:13]}.{raw[13]}.{raw[14:16]}.{raw[16:]}'

    match = CNJ_PATTERN.match(normalized)
    if not match:
        return CNJParseResult(
            raw=raw,
            is_valid=False,
            error='Formato inválido. Esperado: NNNNNNN-DD.AAAA.J.TT.OOOO',
        )

    seq, dig, ano, j, tt, orig = match.groups()

    # Resolve tribunal
    tribunal = None
    if j == '8':
        tribunal = TRIBUNAL_ESTADUAL.get(tt)
    elif j == '4':
        tribunal = TRIBUNAL_FEDERAL.get(tt)
    elif j == '5':
        tribunal = TRIBUNAL_TRABALHO.get(tt)
    elif j in ('1', '3'):
        tribunal = JUSTICE_CODES.get(j)

    return CNJParseResult(
        raw=raw,
        is_valid=True,
        numero=seq,
        digitos=dig,
        ano=int(ano),
        justica=j,
        justica_label=JUSTICE_CODES.get(j, f'Justiça {j}'),
        tribunal_code=tt,
        tribunal=tribunal,
        origem=orig,
    )
