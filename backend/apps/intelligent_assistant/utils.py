"""
Utilitários de transformação de texto/markdown para o intelligent_assistant.
"""
import re

# Matches: single \n antes de **N.N (ex: **1.1, **2.3, **10.2, **1.1.1)
# Lookbehind negativo (?<!\n) garante idempotência (não dobra se já tem \n\n)
_SUBSECTION_BREAK_RE = re.compile(r'(?<!\n)\n(\*\*\d+\.\d+)')


def normalize_subsection_breaks(text: str) -> str:
    """
    Insere quebra de parágrafo (\\n\\n) antes de subseções tipo **1.1, **2.3, etc.

    Agentes de IA frequentemente geram subseções com single newline, que o markdown
    renderiza como soft break (mesma linha). Esta função força paragraph break.

    Idempotente: se já existir \\n\\n, não duplica.
    """
    if not text:
        return text
    return _SUBSECTION_BREAK_RE.sub(r'\n\n\1', text)


# Remove sufixos "(Gerado por IA)" e "(Texto Inserido Manualmente)" que admins
# inseriram manualmente nos nomes de seções/sub-seções (blueprints) para marcar
# o modo de geração. Solução temporária da issue #25 (fase 1) — esses sufixos
# poluem a impressão. A solução definitiva (fase 2) move essa marcação pra um
# campo dedicado no modelo + badge na UI.
_GENERATION_SUFFIX_RE = re.compile(
    r'\s*\((?:Texto\s+Inserido\s+Manualmente|Gerado\s+por\s+IA)\)\s*$',
    flags=re.IGNORECASE,
)


def strip_generation_suffix(text: str) -> str:
    """
    Remove sufixos de modo de geração do final de um nome de seção/sub-seção.

    Aceita: "Foo (Texto Inserido Manualmente)" → "Foo"
    Aceita: "Bar (Gerado por IA)"               → "Bar"
    Idempotente: roda 2x dá o mesmo resultado.
    Conservador: só remove os 2 sufixos exatos da issue #25 — outros parênteses
    no final ("Foo (Lei 14.133)") são preservados.
    """
    if not text:
        return text
    return _GENERATION_SUFFIX_RE.sub('', text).strip()
