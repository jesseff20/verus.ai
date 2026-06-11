"""
Serviço de Copilot Jurídico - Geração de sugestões em tempo real.

Tipos de sugestão:
  - citation: Citações jurídicas (doutrina, leis, princípios)
  - jurisprudence: Jurisprudência dos tribunais
  - clause: Cláusulas e modelos de documentos
  - deadline: Cálculo de prazos processuais
  - argument: Argumentos jurídicos
  - definition: Definições de termos técnicos
  - statute: Legislação aplicável
  - correction: Correções gramaticais/técnicas
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.jurisprudence.models import JurisprudenceResult
from apps.core.models import DocumentType, LegalSource

User = get_user_model()


class CopilotSuggestionType(str, Enum):
    """Tipos de sugestão do Copilot."""
    CITATION = 'citation'
    JURISPRUDENCE = 'jurisprudence'
    CLAUSE = 'clause'
    DEADLINE = 'deadline'
    ARGUMENT = 'argument'
    DEFINITION = 'definition'
    STATUTE = 'statute'
    CORRECTION = 'correction'


@dataclass
class CopilotSuggestion:
    """Uma sugestão do Copilot."""
    id: str
    type: CopilotSuggestionType
    title: str
    content: str
    source: Optional[str] = None
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LegalCopilotService:
    """
    Serviço de Copilot Jurídico.

    Gera sugestões baseadas em:
    1. Análise do texto atual (palavras-chave, contexto)
    2. Tipo de documento
    3. Especialidade jurídica
    4. Histórico do usuário
    """

    # Palavras-chave para cada tipo de sugestão
    KEYWORD_PATTERNS = {
        CopilotSuggestionType.CITATION: [
            r'fundamenta[çc][aã]o?\s+(?:legal|jur[íi]dica)',
            r'com\s+base\s+(?:no|na|nos|nas)',
            r'(?:nos|nas)\s+termos\s+(?:do|da|dos|das)',
            r'(?:artigo|art\.?|arts\.?)\s*\d+',
            r'(?:conforme|segundo)\s+(?:disp[õo]e|preceitua)',
        ],
        CopilotSuggestionType.JURISPRUDENCE: [
            r'(?:jurisprud[êe]ncia|precedente)',
            r'(?:STF|STJ|TST|TSE|TRF|TJ)[-\s]?\d+',
            r'(?:REsp|RE|HC|MS)\s+\d+',
            r'(?:s[úu]mula|orientaç[aã]o jurisprudencial)',
            r'(?:pac[íi]fico|dominante)\s+(?:entendimento|compreens[aã]o)',
        ],
        CopilotSuggestionType.DEADLINE: [
            r'prazo(?:s)?',
            r'(?:contar|contado)\s+(?:da|do|de)?\s+(?:ci[eê]ncia|intimaç[aã]o|publica[çc][aã]o)',
            r'(?:[0-9]+)\s+(?:dias?[úu]teis?|dias? corridos?)',
            r'(?:vencimento|termo final|data limite)',
        ],
        CopilotSuggestionType.ARGUMENT: [
            r'(?:argumento|raz[õo]es?|fundamento)',
            r'(?:imp[õo]e|cumpre)\s+(?:ressaltar|destacar|notar)',
            r'(?:evidente|claro|inequ[íi]voco)',
            r'(?:portanto|logo|assim|pois)',
        ],
        CopilotSuggestionType.STATUTE: [
            r'(?:lei|c[óo]digo|estatuto)\s+(?:n[ºo]\s+)?\d+',
            r'(?:CF|Constitui[çc][aã]o)\s+(?:Federal)?',
            r'(?:CPC|C[óo]digo de Processo Civil)',
            r'(?:CC|C[óo]digo Civil)',
            r'(?:CLT|Consolida[çc][aã]o das Leis do Trabalho)',
        ],
    }

    # Definições jurídicas comuns
    LEGAL_DEFINITIONS = {
        'dano moral': 'Ofensa a direitos da personalidade que causa sofrimento, humilhação ou constrangimento, passível de indenização (STJ - REsp 1.234.567).',
        'responsabilidade civil': 'Obrigação de reparar dano causado a outrem, podendo ser subjetiva (culpa) ou objetiva (independente de culpa).',
        'boa-fé objetiva': 'Princípio que impõe às partes comportamento leal e correto nas relações jurídicas (art. 422, CC).',
        'função social do contrato': 'Princípio que limita a autonomia da vontade em prol do interesse coletivo (art. 421, CC).',
        'coisa julgada': 'Imutabilidade da decisão judicial após esgotados todos os meios de impugnação (art. 502, CPC).',
    }

    # Modelos de cláusulas
    CLAUSE_TEMPLATES = {
        'peticao_inicial': [
            {
                'title': 'Dos Fatos',
                'content': 'EXPOSIÇÃO DOS FATOS\n\nO Autor, [descrição], vem, respeitosamente, à presença de Vossa Excelência, expor os fatos que deram causa à presente demanda...',
            },
            {
                'title': 'Do Direito',
                'content': 'FUNDAMENTAÇÃO JURÍDICA\n\nA presente ação fundamenta-se nos artigos [XXX] da Constituição Federal e [YYY] do Código Civil, que dispõem sobre [matéria]...',
            },
            {
                'title': 'Dos Pedidos',
                'content': 'DOS PEDIDOS\n\nDiante do exposto, requer:\n\na) A citação do Réu para, querendo, apresentar resposta;\nb) A procedência total dos pedidos;\nc) A condenação em honorários advocatícios...\n',
            },
        ],
        'contrato': [
            {
                'title': 'Cláusula de Confidencialidade',
                'content': 'CLÁUSULA X - DA CONFIDENCIALIDADE\n\nAs partes comprometem-se a manter sigilo sobre todas as informações confidenciais a que tiverem acesso em decorrência deste contrato...',
            },
            {
                'title': 'Cláusula de Rescisão',
                'content': 'CLÁUSULA Y - DA RESCISÃO\n\nO presente contrato poderá ser rescindido por qualquer das partes, mediante notificação por escrito com antecedência mínima de 30 (trinta) dias...',
            },
        ],
    }

    def generate_suggestions(
        self,
        current_text: str,
        cursor_position: int,
        current_fragment: str,
        document_type: Optional[str] = None,
        specialty: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        enabled_types: Optional[List[CopilotSuggestionType]] = None,
        max_suggestions: int = 5,
        user: Optional[Any] = None,
    ) -> List[CopilotSuggestion]:
        """
        Gera sugestões baseadas no contexto atual.

        Args:
            current_text: Texto completo atual do documento
            cursor_position: Posição do cursor
            current_fragment: Fragmento sendo digitado
            document_type: Tipo de documento
            specialty: Especialidade jurídica
            extra_context: Contexto adicional
            enabled_types: Tipos de sugestão habilitados
            max_suggestions: Número máximo de sugestões
            user: Usuário atual

        Returns:
            Lista de sugestões ordenadas por relevância
        """
        suggestions = []
        enabled_types = enabled_types or list(CopilotSuggestionType)

        # 1. Detectar tipo de sugestão baseado no contexto
        detected_types = self._detect_suggestion_types(
            current_text, current_fragment, enabled_types
        )

        # 2. Gerar sugestões para cada tipo detectado
        for suggestion_type in detected_types:
            type_suggestions = self._generate_type_suggestions(
                suggestion_type,
                current_text,
                current_fragment,
                document_type,
                specialty,
                extra_context,
                user,
            )
            suggestions.extend(type_suggestions)

        # 3. Ordenar por relevância e limitar
        suggestions.sort(key=lambda s: s.relevance_score, reverse=True)
        return suggestions[:max_suggestions]

    def _detect_suggestion_types(
        self,
        current_text: str,
        current_fragment: str,
        enabled_types: List[CopilotSuggestionType],
    ) -> List[CopilotSuggestionType]:
        """Detecta tipos de sugestão baseado em padrões no texto."""
        detected = []
        text_lower = current_text.lower()
        fragment_lower = current_fragment.lower()

        for suggestion_type in enabled_types:
            patterns = self.KEYWORD_PATTERNS.get(suggestion_type, [])
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    detected.append(suggestion_type)
                    break

        # Se nenhum padrão detectado, usar contexto do fragmento
        if not detected and current_fragment:
            # Fragmentos curtos podem indicar busca por citação
            if len(fragment_lower) >= 3:
                detected.append(CopilotSuggestionType.CITATION)
                detected.append(CopilotSuggestionType.STATUTE)

        return detected or [CopilotSuggestionType.ARGUMENT]

    def _generate_type_suggestions(
        self,
        suggestion_type: CopilotSuggestionType,
        current_text: str,
        current_fragment: str,
        document_type: Optional[str],
        specialty: Optional[str],
        extra_context: Optional[Dict[str, Any]],
        user: Optional[Any],
    ) -> List[CopilotSuggestion]:
        """Gera sugestões para um tipo específico."""

        if suggestion_type == CopilotSuggestionType.JURISPRUDENCE:
            return self._suggest_jurisprudence(current_fragment, specialty, user)
        elif suggestion_type == CopilotSuggestionType.CITATION:
            return self._suggest_citations(current_fragment, specialty)
        elif suggestion_type == CopilotSuggestionType.CLAUSE:
            return self._suggest_clauses(document_type, current_fragment)
        elif suggestion_type == CopilotSuggestionType.DEFINITION:
            return self._suggest_definitions(current_fragment)
        elif suggestion_type == CopilotSuggestionType.STATUTE:
            return self._suggest_statutes(current_fragment, specialty)
        elif suggestion_type == CopilotSuggestionType.ARGUMENT:
            return self._suggest_arguments(current_text, specialty)
        elif suggestion_type == CopilotSuggestionType.DEADLINE:
            return self._suggest_deadlines(current_text)
        elif suggestion_type == CopilotSuggestionType.CORRECTION:
            return self._suggest_corrections(current_text)

        return []

    def _suggest_jurisprudence(
        self,
        fragment: str,
        specialty: Optional[str],
        user: Optional[Any],
    ) -> List[CopilotSuggestion]:
        """Busca jurisprudência relacionada."""
        if not fragment or len(fragment) < 3:
            return []

        suggestions = []

        # Buscar jurisprudência do usuário
        if user:
            results = JurisprudenceResult.objects.filter(
                search__user=user,
                summary__icontains=fragment,
            ).order_by('-relevance_score')[:3]

            for result in results:
                suggestions.append(CopilotSuggestion(
                    id=str(uuid.uuid4()),
                    type=CopilotSuggestionType.JURISPRUDENCE,
                    title=f'{result.tribunal} - {result.case_number or "Sem número"}',
                    content=result.summary[:200] + '...' if len(result.summary) > 200 else result.summary,
                    source=result.full_text_url or f'{result.tribunal}',
                    relevance_score=result.relevance_score,
                    metadata={
                        'judgment_date': str(result.judgment_date) if result.judgment_date else None,
                        'relator': result.relator,
                    },
                ))

        return suggestions

    def _suggest_citations(
        self,
        fragment: str,
        specialty: Optional[str],
    ) -> List[CopilotSuggestion]:
        """Sugere citações jurídicas."""
        suggestions = []

        # Citações genéricas baseadas em palavras-chave
        citation_templates = {
            'responsabilidade': 'A responsabilidade civil fundamenta-se no princípio da reparação integral do dano (art. 944, CC).',
            'dano moral': 'O dano moral configura-se pela ofensa a direitos da personalidade, sendo dispensada a prova do prejuízo (STJ - Súmula 37).',
            'contrato': 'Os contratos devem ser executados de boa-fé, observada sua função social (art. 421 e 422, CC).',
            'prazo': 'Os prazos processuais contam-se em dias úteis, excluindo-se o dia do início e incluindo-se o do vencimento (art. 219, CPC).',
        }

        for keyword, citation in citation_templates.items():
            if keyword in fragment.lower():
                suggestions.append(CopilotSuggestion(
                    id=str(uuid.uuid4()),
                    type=CopilotSuggestionType.CITATION,
                    title=f'Citação sobre {keyword}',
                    content=citation,
                    source='Legislação/Jurisprudência',
                    relevance_score=0.8,
                ))

        return suggestions

    def _suggest_clauses(
        self,
        document_type: Optional[str],
        fragment: str,
    ) -> List[CopilotSuggestion]:
        """Sugere cláusulas/modelos."""
        suggestions = []

        if document_type and document_type in self.CLAUSE_TEMPLATES:
            templates = self.CLAUSE_TEMPLATES[document_type]
            for template in templates:
                # Filtrar por fragmento se houver
                if not fragment or fragment.lower() in template['title'].lower():
                    suggestions.append(CopilotSuggestion(
                        id=str(uuid.uuid4()),
                        type=CopilotSuggestionType.CLAUSE,
                        title=template['title'],
                        content=template['content'],
                        relevance_score=0.9,
                    ))

        return suggestions

    def _suggest_definitions(
        self,
        fragment: str,
    ) -> List[CopilotSuggestion]:
        """Sugere definições de termos técnicos."""
        suggestions = []

        if fragment and len(fragment) >= 3:
            for term, definition in self.LEGAL_DEFINITIONS.items():
                if fragment.lower() in term.lower():
                    suggestions.append(CopilotSuggestion(
                        id=str(uuid.uuid4()),
                        type=CopilotSuggestionType.DEFINITION,
                        title=f'Definição: {term}',
                        content=definition,
                        source='Dicionário Jurídico',
                        relevance_score=0.85,
                    ))

        return suggestions

    def _suggest_statutes(
        self,
        fragment: str,
        specialty: Optional[str],
    ) -> List[CopilotSuggestion]:
        """Sugere legislação aplicável."""
        suggestions = []

        # Mapeamento de termos para artigos
        statute_map = {
            'responsabilidade civil': 'art. 186, 927 e 944, CC',
            'dano moral': 'art. 5º, V e X, CF; art. 186, CC',
            'contrato': 'art. 421 a 480, CC',
            'prazo processual': 'art. 219 a 223, CPC',
            'petição inicial': 'art. 319, CPC',
            'sentença': 'art. 485 e 487, CPC',
        }

        if fragment:
            for term, statute in statute_map.items():
                if term in fragment.lower():
                    suggestions.append(CopilotSuggestion(
                        id=str(uuid.uuid4()),
                        type=CopilotSuggestionType.STATUTE,
                        title=f'Legislação: {term}',
                        content=f'Fundamentação: {statute}',
                        source='Legislação Federal',
                        relevance_score=0.9,
                    ))

        return suggestions

    def _suggest_arguments(
        self,
        current_text: str,
        specialty: Optional[str],
    ) -> List[CopilotSuggestion]:
        """Sugere argumentos jurídicos."""
        suggestions = []

        # Argumentos genéricos baseados em contexto
        argument_templates = [
            {
                'trigger': 'pedido',
                'title': 'Argumento para pedidos',
                'content': 'Diante de todo o exposto, resta evidente o direito do Autor à procedência dos pedidos, uma vez que restaram comprovados tanto os fatos quanto o fundamento jurídico.',
            },
            {
                'trigger': 'prova',
                'title': 'Argumento probatório',
                'content': 'A prova produzida nos autos é inequívoca e demonstra a veracidade dos fatos alegados, impondo-se a procedência do pedido.',
            },
            {
                'trigger': 'direito',
                'title': 'Argumento jurídico',
                'content': 'O ordenamento jurídico pátrio ampara integralmente a pretensão deduzida, conforme demonstrado na fundamentação.',
            },
        ]

        text_lower = current_text.lower()
        for template in argument_templates:
            if template['trigger'] in text_lower:
                suggestions.append(CopilotSuggestion(
                    id=str(uuid.uuid4()),
                    type=CopilotSuggestionType.ARGUMENT,
                    title=template['title'],
                    content=template['content'],
                    relevance_score=0.75,
                ))

        return suggestions

    def _suggest_deadlines(
        self,
        current_text: str,
    ) -> List[CopilotSuggestion]:
        """Sugere cálculos de prazo."""
        suggestions = []

        # Detectar menções a prazo
        if 'prazo' in current_text.lower():
            suggestions.append(CopilotSuggestion(
                id=str(uuid.uuid4()),
                type=CopilotSuggestionType.DEADLINE,
                title='Calcular prazo processual',
                content='Use o comando /prazo para calcular prazos processuais automaticamente.',
                relevance_score=0.7,
            ))

        return suggestions

    def _suggest_corrections(
        self,
        current_text: str,
    ) -> List[CopilotSuggestion]:
        """Sugere correções gramaticais/técnicas."""
        suggestions = []

        # Correções comuns
        corrections = {
            'aonde': 'Use "onde" para lugar ou "aonde" apenas com verbos de movimento.',
            'mal x mau': '"Mal" é advérbio (oposto de bem). "Mau" é adjetivo (oposto de bom).',
            'afim x a fim': '"A fim de" = finalidade. "Afim" = semelhança/parentesco.',
            'senão x se não': '"Senão" = caso contrário. "Se não" = condição.',
        }

        for wrong, correction in corrections.items():
            if wrong in current_text.lower():
                suggestions.append(CopilotSuggestion(
                    id=str(uuid.uuid4()),
                    type=CopilotSuggestionType.CORRECTION,
                    title=f'Correção: "{wrong}"',
                    content=correction,
                    relevance_score=0.8,
                ))

        return suggestions
