"""
Views de validação pré-geração e pós-geração para o Assistente Inteligente.
"""
import logging
import json
import hashlib
import re

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.conf import settings
from django.core.cache import cache as django_cache
from urllib.parse import quote_plus

from ..models import IntelligentSession, BlueprintSection, SectionGenerationLog, GeneratedDocument

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Validar inputs antes da geração",
    description="""
    Verifica se a sessão possui todos os campos obrigatórios preenchidos
    antes de iniciar a geração do documento.

    Analisa os `section_fields` de cada seção do blueprint vinculado à sessão
    e retorna campos ausentes e avisos.
    """,
    tags=["Assistente Inteligente - Validação"],
    responses={
        200: OpenApiResponse(description="Resultado da validação"),
        400: OpenApiResponse(description="Sessão sem blueprint"),
        404: OpenApiResponse(description="Sessão não encontrada"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_session_inputs(request, session_id):
    """
    POST /api/v1/intelligent-assistant/sessions/<uuid:session_id>/validate-inputs/

    Verifica campos obrigatórios do blueprint e retorna:
    - missing_fields: lista de campos obrigatórios não preenchidos
    - warnings: avisos sobre a sessão
    - is_valid: boolean geral
    """
    try:
        session = IntelligentSession.objects.select_related('blueprint').get(
            id=session_id, user=request.user
        )
    except IntelligentSession.DoesNotExist:
        return Response(
            {'error': 'Sessão não encontrada'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not session.blueprint:
        return Response(
            {'error': 'Sessão não possui um blueprint vinculado'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    collected_data = session.collected_data or {}
    missing_fields = []
    warnings = []

    # Buscar seções ativas do blueprint
    sections = BlueprintSection.objects.filter(
        blueprint=session.blueprint,
        is_active=True,
    ).order_by('order', 'section_number')

    for section in sections:
        section_fields = section.section_fields or []

        for field in section_fields:
            field_name = field.get('name', '')
            field_label = field.get('label', field_name)
            required = field.get('required', False)
            field_type = field.get('type', 'text')

            if not field_name:
                continue

            value = collected_data.get(field_name)

            if required:
                if field_type == 'array':
                    if not value or (isinstance(value, list) and len(value) == 0):
                        missing_fields.append({
                            'section_number': section.section_number,
                            'section_name': section.section_name,
                            'field_name': field_name,
                            'field_label': field_label,
                        })
                elif not value or (isinstance(value, str) and not value.strip()):
                    missing_fields.append({
                        'section_number': section.section_number,
                        'section_name': section.section_name,
                        'field_name': field_name,
                        'field_label': field_label,
                    })

    # Avisos
    if not session.objective:
        warnings.append('Objetivo da contratação não definido')

    if not session.collected_data or not isinstance(session.collected_data, dict) or len(session.collected_data) == 0:
        warnings.append('Nenhum dado coletado foi preenchido')

    is_valid = len(missing_fields) == 0

    # Persistir estado de validação na sessão
    session.validation_state = {
        'is_valid': is_valid,
        'missing_fields': missing_fields,
        'warnings': warnings,
        'validated_at': None,  # será preenchido quando o frontend enviar
    }
    session.save(update_fields=['validation_state'])

    return Response({
        'is_valid': is_valid,
        'missing_fields': missing_fields,
        'warnings': warnings,
        'total_sections': sections.count(),
    })


@extend_schema(
    summary="Listar audit log de geração da sessão",
    description="""
    Retorna o histórico completo de geração de seções para uma sessão,
    incluindo provider usado, tokens, tempo e placeholders não resolvidos.
    """,
    tags=["Assistente Inteligente - Auditoria"],
    responses={
        200: OpenApiResponse(description="Lista de logs de geração"),
        404: OpenApiResponse(description="Sessão não encontrada"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_audit_log(request, session_id):
    """
    GET /api/v1/intelligent-assistant/sessions/<uuid:session_id>/audit-log/

    Retorna todos os SectionGenerationLog da sessão, ordenados do mais recente.
    """
    try:
        session = IntelligentSession.objects.get(
            id=session_id, user=request.user
        )
    except IntelligentSession.DoesNotExist:
        return Response(
            {'error': 'Sessão não encontrada'},
            status=status.HTTP_404_NOT_FOUND,
        )

    logs_qs = SectionGenerationLog.objects.filter(
        session=session
    ).select_related(
        'section', 'agent'
    ).order_by('-created_at')

    paginator = PageNumberPagination()
    paginator.page_size = 100
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 200
    page = paginator.paginate_queryset(logs_qs, request)
    logs = page if page is not None else logs_qs

    results = []
    for log in logs:
        results.append({
            'id': str(log.id),
            'section_number': log.section.section_number if log.section else None,
            'section_name': log.section.section_name if log.section else None,
            'agent_name': log.agent.name if log.agent else None,
            'agent_type': log.agent.agent_type if log.agent else None,
            'provider': log.provider,
            'model_name': log.model_name,
            'input_tokens': log.input_tokens,
            'output_tokens': log.output_tokens,
            'generation_time_ms': log.generation_time_ms,
            'has_unresolved_placeholders': log.has_unresolved_placeholders,
            'unresolved_count': log.unresolved_count,
            'created_at': log.created_at.isoformat(),
        })

    response_data = {
        'session_id': str(session_id),
        'total_logs': len(results),
        'logs': results,
    }
    if page is not None:
        return paginator.get_paginated_response(response_data)
    return Response(response_data)


# =============================================================================
# CONFIRM REVIEW — Confirmar revisão humana do documento
# =============================================================================


@extend_schema(
    summary="Confirmar revisão humana do documento",
    description="""
    Registra a OAB do revisor e o timestamp de revisão para um documento gerado.

    Valida que o documento existe e pertence ao usuário autenticado.
    O campo `reviewer_oab` deve ser enviado no corpo da requisição.
    """,
    tags=["Assistente Inteligente - Documentos"],
    responses={
        200: OpenApiResponse(description="Revisão confirmada com sucesso"),
        400: OpenApiResponse(description="reviewer_oab não fornecido"),
        404: OpenApiResponse(description="Documento não encontrado"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_review(request, document_id):
    """
    POST /api/v1/intelligent-assistant/documents/<uuid:document_id>/confirm-review/

    Registra a OAB do revisor e marca o documento como revisado.
    """
    try:
        document = GeneratedDocument.objects.select_related('session').get(
            id=document_id,
            session__user=request.user,
        )
    except GeneratedDocument.DoesNotExist:
        return Response(
            {'error': 'Documento não encontrado ou não pertence ao usuário'},
            status=status.HTTP_404_NOT_FOUND,
        )

    reviewer_oab = request.data.get('reviewer_oab', '').strip()
    if not reviewer_oab:
        return Response(
            {'error': 'O campo "reviewer_oab" é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from django.utils import timezone
    now = timezone.now()

    # Registrar na sessão (campos já existentes: reviewer_oab, reviewed_at)
    session = document.session
    session.reviewer_oab = reviewer_oab
    session.reviewed_at = now
    session.save(update_fields=['reviewer_oab', 'reviewed_at'])

    return Response({
        'status': 'reviewed',
        'reviewer_oab': reviewer_oab,
        'reviewed_at': now.isoformat(),
    })


# =============================================================================
# PLACEHOLDERS — Listar placeholders não resolvidos no documento
# =============================================================================


@extend_schema(
    summary="Listar placeholders não resolvidos no documento",
    description="""
    Analisa o conteúdo do GeneratedDocument e extrai todos os placeholders
    não resolvidos no formato [PESQUISAR...], [INFORMAÇÃO NECESSÁRIA...],
    [TESE CONTROVERTIDA...] e similares.

    Retorna lista de placeholders com tipo, texto, seção e severidade.
    """,
    tags=["Assistente Inteligente - Documentos"],
    responses={
        200: OpenApiResponse(description="Lista de placeholders"),
        404: OpenApiResponse(description="Documento não encontrado"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_placeholders(request, document_id):
    """
    GET /api/v1/intelligent-assistant/documents/<uuid:document_id>/placeholders/

    Retorna todos os placeholders não resolvidos no documento gerado.
    """
    try:
        document = GeneratedDocument.objects.select_related('session').get(
            id=document_id,
            session__user=request.user,
        )
    except GeneratedDocument.DoesNotExist:
        return Response(
            {'error': 'Documento não encontrado ou não pertence ao usuário'},
            status=status.HTTP_404_NOT_FOUND,
        )

    content = document.markdown_content or ''
    placeholders = []

    # Regex para padrões de placeholder
    # [PESQUISAR ...], [INFORMAÇÃO NECESSÁRIA ...], [TESE CONTROVERTIDA ...]
    # [A DEFINIR ...], [REVISAR ...], etc.
    patterns = [
        (r'\[PESQUISAR[^\]]*\]', 'pesquisar', 'alta'),
        (r'\[INFORMAÇÃO\s+NECESSÁRIA[^\]]*\]', 'informacao_necessaria', 'alta'),
        (r'\[TESE\s+CONTROVERTIDA[^\]]*\]', 'tese_controvertida', 'alta'),
        (r'\[A\s+DEFINIR[^\]]*\]', 'a_definir', 'media'),
        (r'\[REVISAR[^\]]*\]', 'revisar', 'media'),
        (r'\[VERIFICAR[^\]]*\]', 'verificar', 'media'),
        (r'\[CONFERIR[^\]]*\]', 'conferir', 'baixa'),
        (r'\[INCLUIR[^\]]*\]', 'incluir', 'media'),
        (r'\[ADICIONAR[^\]]*\]', 'adicionar', 'media'),
        (r'\[COMPLEMENTAR[^\]]*\]', 'complementar', 'media'),
        (r'\[IMAGEM[^\]]*\]', 'imagem', 'baixa'),
        (r'\[ANEXO[^\]]*\]', 'anexo', 'media'),
    ]

    for pattern, placeholder_type, severity in patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            placeholder_text = match.group()
            # Tentar identificar a seção: procurar o último cabeçalho markdown antes do match
            pos = match.start()
            section = _find_section(content, pos)

            placeholders.append({
                'type': placeholder_type,
                'text': placeholder_text,
                'section': section,
                'severity': severity,
            })

    total_count = len(placeholders)
    has_unresolved = total_count > 0

    return Response({
        'placeholders': placeholders,
        'total_count': total_count,
        'has_unresolved': has_unresolved,
    })


def _find_section(content, pos):
    """Encontra o título da seção markdown mais próxima antes da posição."""
    before = content[:pos]
    lines = before.split('\n')
    section = None
    for line in reversed(lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            # Cabeçalho markdown encontrado
            section = stripped.lstrip('#').strip()
            break
        if stripped.startswith('---') or stripped.startswith('==='):
            # Possível cabeçalho setext
            continue

    return section or 'Introdução / Sem seção identificada'


# =============================================================================
# TAVILY - Busca de Jurisprudência
# =============================================================================

TAVILY_API_KEY = getattr(settings, 'TAVILY_API_KEY', '')
TAVILY_SEARCH_URL = 'https://api.tavily.com/search'


@extend_schema(
    summary="Buscar jurisprudência via Tavily",
    description="""
    Realiza busca de jurisprudência na web utilizando a API Tavily.

    Os resultados são cacheados por 1 hora para evitar consumo excessivo da API.

    **Headers necessários:** `Authorization: Bearer <token>` (JWT)

    **Parâmetros no corpo:**
    - `query`: String de busca (obrigatório)
    - `max_results`: Número máximo de resultados (opcional, default: 5, máx: 10)
    """,
    tags=["Jurisprudência"],
    responses={
        200: OpenApiResponse(description="Resultados da busca"),
        400: OpenApiResponse(description="Query não fornecida"),
        503: OpenApiResponse(description="Tavily API key não configurada"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def jurisprudence_search(request):
    """
    POST /api/v1/intelligent-assistant/jurisprudence/search/

    Busca jurisprudência usando a API Tavily.
    """
    if not TAVILY_API_KEY:
        return Response(
            {'error': 'API do Tavily não configurada. Contate o administrador.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    query = request.data.get('query', '').strip()
    if not query:
        return Response(
            {'error': 'O campo "query" é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    max_results = min(int(request.data.get('max_results', 5)), 10)

    # Cache key baseado na query
    cache_key = f'tavily_search:{hashlib.sha256(query.encode()).hexdigest()}:{max_results}'
    cached = django_cache.get(cache_key)
    if cached:
        logger.info(f"Retornando jurisprudência cacheada para: {query[:60]}...")
        return Response(cached)

    try:
        import requests as req_lib
        response = req_lib.post(
            TAVILY_SEARCH_URL,
            json={
                'api_key': TAVILY_API_KEY,
                'query': f'jurisprudência direito brasileiro {query}',
                'search_depth': 'advanced',
                'max_results': max_results,
                'include_answer': True,
                'include_domains': [
                    'jusbrasil.com.br',
                    'stf.jus.br',
                    'stj.jus.br',
                    'tjsp.jus.br',
                    'tjrj.jus.br',
                    'conjur.com.br',
                    'migalhas.com.br',
                ],
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        # Estruturar resposta
        result = {
            'query': query,
            'answer': data.get('answer', ''),
            'results': [],
            'total_results': len(data.get('results', [])),
        }
        for item in data.get('results', []):
            result['results'].append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'content': item.get('content', ''),
                'score': item.get('score', 0),
            })

        # Cache por 1 hora
        django_cache.set(cache_key, result, timeout=3600)

        return Response(result)

    except ImportError:
        return Response(
            {'error': 'Módulo "requests" não disponível no servidor.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        logger.error(f"Erro na busca Tavily: {str(e)}")
        return Response(
            {'error': f'Erro ao buscar jurisprudência: {str(e)}'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
