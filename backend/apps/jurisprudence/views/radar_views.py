"""
Radar de Precedentes — Views para análise jurisprudencial.

Endpoints:
  POST /api/v1/jurisprudence/radar/analyze/
    - Analisa jurisprudência e retorna relatório completo

  GET /api/v1/jurisprudence/radar/tribunais/
    - Lista tribunais disponíveis com estatísticas

  GET /api/v1/jurisprudence/radar/teses/
    - Lista teses jurídicas mais pesquisadas
"""

import json
import logging

from rest_framework import permissions, status

logger = logging.getLogger(__name__)
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.utils import timezone
from django.http import StreamingHttpResponse
from datetime import timedelta

from ..services.precedent_radar_service import (
    PrecedentRadarService,
    PrecedentOutcome,
    PrecedentWeight,
)
from ..serializers import (
    RadarReportSerializer,
    TribunalStatisticsSerializer,
    ThesisStatisticsSerializer,
)


class RadarAnalysisThrottle(UserRateThrottle):
    """
    Throttle para análise do Radar de Precedentes.
    Limite: 5 análises por minuto (operação intensiva).
    """
    scope = 'radar_analysis'


# ---------------------------------------------------------------------------
# Mapa de specialty: texto livre → código do modelo (max 3 chars)
# ---------------------------------------------------------------------------
SPECIALTY_MAP = {
    'civel': 'CIV', 'civil': 'CIV',
    'penal': 'PEN', 'criminal': 'PEN',
    'trabalhista': 'TRB',
    'administrativo': 'ADM',
    'constitucional': 'CON',
    'tributario': 'TRI', 'tributário': 'TRI',
    'familia': 'FAM', 'família': 'FAM',
    'empresarial': 'EMP',
    'ambiental': 'AMB',
    'consumidor': 'OUT', 'digital': 'OUT',
    'previdenciario': 'OUT', 'previdenciário': 'OUT',
}


@api_view(['POST'])
@throttle_classes([RadarAnalysisThrottle])
@permission_classes([permissions.IsAuthenticated])
def analyze_precedents(request):
    """
    POST /api/v1/jurisprudence/radar/analyze/

    Analisa jurisprudência e gera relatório do Radar de Precedentes.

    Request:
    {
        "query": "responsabilidade civil dano moral",
        "specialty": "CIV",  // opcional
        "date_range": ["2024-01-01", "2026-05-26"],  // opcional
        "tribunals": ["STF", "STJ"],  // opcional
        "include_timeline": true,  // opcional, default: true
        "limit_precedents": 10,  // opcional, default: 10
    }

    Response:
    {
        "query": "responsabilidade civil dano moral",
        "total_analyzed": 42,
        "overall_success_rate": 0.67,
        "tribunal_stats": [...],
        "thesis_stats": [...],
        "timeline": [...],
        "key_precedents": [...],
        "recommendations": [...],
        "generated_at": "2026-05-26T10:30:00Z"
    }
    """
    # Extrair parâmetros do request
    query = request.data.get('query', '')
    specialty = request.data.get('specialty')
    date_range = request.data.get('date_range')
    tribunals = request.data.get('tribunals')
    include_timeline = request.data.get('include_timeline', True)
    limit_precedents = request.data.get('limit_precedents', 10)

    # Validar query
    if not query or len(query) < 3:
        return Response(
            {'detail': 'Query deve ter pelo menos 3 caracteres'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Parse date_range
    parsed_date_range = None
    if date_range and len(date_range) == 2:
        try:
            from datetime import datetime
            start = datetime.fromisoformat(date_range[0])
            end = datetime.fromisoformat(date_range[1])
            parsed_date_range = (start, end)
        except (ValueError, TypeError):
            pass

    try:
        # Executar análise
        service = PrecedentRadarService()
        report = service.analyze_precedents(
            query=query,
            specialty=specialty,
            date_range=parsed_date_range,
            tribunals=tribunals,
            user_id=request.user.id,
        )

        # Serializar relatório
        serializer = RadarReportSerializer(report)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'detail': f'Erro na análise: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_tribunais_stats(request):
    """
    GET /api/v1/jurisprudence/radar/tribunais/

    Lista tribunais com estatísticas gerais.
    """
    from django.db.models import Count, Avg
    from ..models import JurisprudenceResult

    # Período opcional
    days = int(request.query_params.get('days', 90))
    since = timezone.now() - timedelta(days=days)

    # Estatísticas por tribunal
    stats = (
        JurisprudenceResult.objects
        .filter(search__created_at__gte=since)
        .values('tribunal')
        .annotate(
            total=Count('id'),
            avg_score=Avg('relevance_score'),
        )
        .order_by('-total')
    )

    # Formatar resposta
    result = [
        {
            'tribunal': item['tribunal'],
            'total_cases': item['total'],
            'avg_relevance': round(float(item['avg_score']), 2) if item['avg_score'] else 0,
        }
        for item in stats
    ]

    return Response({
        'period_days': days,
        'tribunais': result,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_theses_stats(request):
    """
    GET /api/v1/jurisprudence/radar/teses/

    Lista teses jurídicas mais pesquisadas.
    """
    from django.db.models import Count
    from ..models import JurisprudenceSearch

    # Período opcional
    days = int(request.query_params.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Teses mais pesquisadas
    theses = (
        JurisprudenceSearch.objects
        .filter(created_at__gte=since, status='completed')
        .values('query')
        .annotate(
            total=Count('id'),
            avg_results=Count('results'),
        )
        .order_by('-total')[:20]
    )

    result = [
        {
            'thesis': item['query'],
            'search_count': item['total'],
            'avg_results': item['avg_results'],
        }
        for item in theses
    ]

    return Response({
        'period_days': days,
        'theses': result,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_precedent_detail(request, precedent_id):
    """
    GET /api/v1/jurisprudence/radar/precedents/{id}/

    Retorna detalhes de um precedente específico.
    """
    from ..models import JurisprudenceResult
    from ..serializers import JurisprudenceResultSerializer

    try:
        precedent = JurisprudenceResult.objects.get(id=precedent_id)

        # Verificar permissão (apenas dono ou admin)
        if precedent.search.user != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'Sem permissão para este precedente'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = JurisprudenceResultSerializer(precedent)

        # Adicionar análise do precedente
        service = PrecedentRadarService()
        analysis = service._result_to_precedent(precedent)

        return Response({
            'precedent': serializer.data,
            'analysis': {
                'outcome': analysis.outcome.value,
                'weight': analysis.weight.value,
                'keywords': analysis.keywords,
                'citation': analysis.citation,
            }
        })

    except JurisprudenceResult.DoesNotExist:
        return Response(
            {'detail': 'Precedente não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================================
# Endpoints requeridos pelo frontend de jurisprudência
# ============================================================

SPECIALTIES = [
    {'id': 'civel', 'code': 'civel', 'name': 'Direito Civil'},
    {'id': 'penal', 'code': 'penal', 'name': 'Direito Penal'},
    {'id': 'trabalhista', 'code': 'trabalhista', 'name': 'Direito Trabalhista'},
    {'id': 'tributario', 'code': 'tributario', 'name': 'Direito Tributário'},
    {'id': 'administrativo', 'code': 'administrativo', 'name': 'Direito Administrativo'},
    {'id': 'constitucional', 'code': 'constitucional', 'name': 'Direito Constitucional'},
    {'id': 'empresarial', 'code': 'empresarial', 'name': 'Direito Empresarial'},
    {'id': 'consumidor', 'code': 'consumidor', 'name': 'Direito do Consumidor'},
    {'id': 'familia', 'code': 'familia', 'name': 'Direito de Família'},
    {'id': 'previdenciario', 'code': 'previdenciario', 'name': 'Direito Previdenciário'},
    {'id': 'ambiental', 'code': 'ambiental', 'name': 'Direito Ambiental'},
    {'id': 'digital', 'code': 'digital', 'name': 'Direito Digital e LGPD'},
]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_specialties(request):
    """
    GET /api/v1/jurisprudence/specialties/

    Retorna lista de especialidades jurídicas disponíveis.
    """
    return Response(SPECIALTIES)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def jurisprudence_searches(request):
    """
    GET  /api/v1/jurisprudence/searches/
         Retorna histórico de buscas do usuário (últimas 50).

    POST /api/v1/jurisprudence/searches/
         Processa uma nova busca de jurisprudência, persiste no banco e retorna o resultado.
    """
    from ..models import JurisprudenceSearch, JurisprudenceResult
    from ..serializers import JurisprudenceResultSerializer

    if request.method == 'GET':
        searches_qs = (
            JurisprudenceSearch.objects
            .filter(user=request.user)
            .prefetch_related('results')
            .order_by('-created_at')
        )

        paginator = PageNumberPagination()
        paginator.page_size = 50
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 100
        searches = paginator.paginate_queryset(searches_qs, request)
        if searches is None:
            searches = searches_qs

        results_data = []
        for s in searches:
            results_data.append({
                'id': str(s.id),
                'query': s.query,
                'specialty': s.specialty,
                'status': s.status,
                'created_at': s.created_at.isoformat(),
                'results': [
                    {
                        'id': str(r.id),
                        'tribunal': r.tribunal,
                        'case_number': r.case_number or '',
                        'relator': r.relator or '',
                        'judgment_date': r.judgment_date.strftime('%Y-%m-%d') if r.judgment_date else None,
                        'organ': r.organ or '',
                        'summary': r.summary,
                        'full_text': r.summary,
                        'source_url': r.full_text_url,
                        'is_verified': False,
                        'relevance_score': r.relevance_score,
                        'classe': (r.content or {}).get('classe', ''),
                        'grau': (r.content or {}).get('grau', ''),
                        'assuntos': (r.content or {}).get('assuntos', []),
                        'title': (r.content or {}).get('title', ''),
                    }
                    for r in s.results.all()
                ],
            })

        return paginator.get_paginated_response(results_data)

    # POST — processar nova busca
    query = request.data.get('query', '').strip()
    specialty = request.data.get('specialty', '')

    if not query or len(query) < 3:
        return Response(
            {'detail': 'O campo "query" deve ter pelo menos 3 caracteres.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Converter specialty texto livre → código do modelo
    specialty_code = SPECIALTY_MAP.get(specialty.lower()) if specialty else None

    # Criar registro no banco antes de buscar
    search = JurisprudenceSearch.objects.create(
        user=request.user,
        query=query,
        specialty=specialty_code,
        status='processing',
    )

    try:
        # Buscar via DataJud/CNJ (API pública oficial)
        from ..search_service import search_jurisprudencia
        raw_results = search_jurisprudencia(
            query=query,
            specialty=specialty or None,
            max_results=10,
        )

        # Persistir cada resultado no banco
        from datetime import datetime as _dt
        results = []
        for i, r in enumerate(raw_results):
            jdate_str = r.get('judgment_date') or ''
            jdate = None
            if jdate_str:
                try:
                    jdate = _dt.strptime(jdate_str, '%Y-%m-%d')
                except ValueError:
                    pass
            result = JurisprudenceResult.objects.create(
                search=search,
                tribunal=r.get('source', 'Tribunal'),
                case_number=r.get('case_number', ''),
                organ=r.get('organ', ''),
                relator='',
                judgment_date=jdate,
                summary=r.get('snippet', r.get('title', ''))[:2000],
                full_text_url=r.get('url') or None,
                relevance_score=max(0.0, 1.0 - i * 0.05),
                source=r.get('source', ''),
                content={
                    'title': r.get('title', ''),
                    'url': r.get('url', ''),
                    'classe': r.get('classe', ''),
                    'grau': r.get('grau', ''),
                    'assuntos': r.get('assuntos', []),
                },
            )
            results.append({
                'id': str(result.id),
                'tribunal': result.tribunal,
                'case_number': result.case_number or '',
                'relator': result.relator or '',
                'judgment_date': result.judgment_date.strftime('%Y-%m-%d') if result.judgment_date else None,
                'organ': result.organ or '',
                'summary': result.summary,
                'full_text': result.summary,
                'source_url': result.full_text_url,
                'is_verified': False,
                'relevance_score': result.relevance_score,
                'classe': r.get('classe', ''),
                'grau': r.get('grau', ''),
                'assuntos': r.get('assuntos', []),
                'title': r.get('title', ''),
            })

        # Marcar busca como concluída
        search.status = 'completed'
        search.save(update_fields=['status', 'updated_at'])

    except Exception as e:
        search.status = 'failed'
        search.save(update_fields=['status', 'updated_at'])
        return Response(
            {'detail': f'Erro ao realizar busca: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            'id': str(search.id),
            'query': query,
            'specialty': specialty,
            'status': 'completed',
            'results': results,
            'created_at': search.created_at.isoformat(),
        },
        status=status.HTTP_201_CREATED,
    )


def _search_stream_generator(query, specialty_code, user):
    """
    Generator SSE para busca jurisprudencial em tempo real via DataJud (CNJ).
    Emite eventos de progresso enquanto consulta os tribunais.
    """
    from ..models import JurisprudenceSearch, JurisprudenceResult
    from ..search_service import (
        _get_api_key, _build_query, _search_tribunal,
        SPECIALTY_TRIBUNALS, DEFAULT_TRIBUNALS,
    )

    search = JurisprudenceSearch.objects.create(
        user=user,
        query=query,
        specialty=specialty_code,
        status='processing',
    )

    yield f"data: {json.dumps({'event': 'start', 'search_id': str(search.id), 'message': 'Iniciando busca no DataJud (CNJ)...'})}\n\n"

    results = []

    try:
        api_key = _get_api_key()
        query_body = _build_query(query, specialty_code)
        tribunals = SPECIALTY_TRIBUNALS.get(specialty_code or '', DEFAULT_TRIBUNALS)

        seen_titles: set = set()

        for trib in tribunals[:6]:  # máximo 6 tribunais para não demorar
            tribunal_nome = trib.upper()
            yield f"data: {json.dumps({'event': 'searching', 'site': tribunal_nome, 'message': f'Consultando {tribunal_nome}...'})}\n\n"

            hits = _search_tribunal(query_body, trib, api_key)

            if not hits:
                yield f"data: {json.dumps({'event': 'site_error', 'site': tribunal_nome, 'error': 'Sem resultados'})}\n\n"
                continue

            from datetime import datetime as _dt
            for r in hits:
                title = r.get('title', '')
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                jdate_str = r.get('judgment_date') or ''
                jdate = None
                if jdate_str:
                    try:
                        jdate = _dt.strptime(jdate_str, '%Y-%m-%d')
                    except ValueError:
                        pass

                result = JurisprudenceResult.objects.create(
                    search=search,
                    tribunal=r.get('source', tribunal_nome),
                    case_number=r.get('case_number', ''),
                    organ=r.get('organ', ''),
                    relator='',
                    judgment_date=jdate,
                    summary=(r.get('snippet', r.get('title', '')) or '')[:2000],
                    full_text_url=r.get('url') or None,
                    relevance_score=max(0.0, 0.95 - len(results) * 0.04),
                    source=r.get('source', tribunal_nome),
                    content={
                        'title': r.get('title', ''),
                        'url': r.get('url', ''),
                        'classe': r.get('classe', ''),
                        'grau': r.get('grau', ''),
                        'assuntos': r.get('assuntos', []),
                    },
                )
                results.append(result)
                yield f"data: {json.dumps({'event': 'result', 'count': len(results), 'tribunal': r.get('source', tribunal_nome)})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"

    search.status = 'completed'
    search.save(update_fields=['status', 'updated_at'])

    yield f"data: {json.dumps({'event': 'done', 'search_id': str(search.id), 'total': len(results)})}\n\n"


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def jurisprudence_searches_stream(request):
    """
    POST /api/v1/jurisprudence/searches/stream/

    SSE endpoint — envia eventos em tempo real durante a busca de jurisprudência.
    """
    query = request.data.get('query', '').strip()
    specialty = request.data.get('specialty', '')

    if not query or len(query) < 3:
        return Response({'detail': 'Query muito curta (mínimo 3 caracteres)'}, status=400)

    specialty_code = SPECIALTY_MAP.get(specialty.lower()) if specialty else None

    response = StreamingHttpResponse(
        _search_stream_generator(query, specialty_code, request.user),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_search(request, search_id):
    """
    DELETE /api/v1/jurisprudence/searches/{search_id}/

    Deleta uma busca específica do usuário autenticado.
    """
    from ..models import JurisprudenceSearch

    try:
        search = JurisprudenceSearch.objects.get(id=search_id, user=request.user)
        search.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except JurisprudenceSearch.DoesNotExist:
        return Response({'detail': 'Busca não encontrada.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def clear_all_searches(request):
    """
    DELETE /api/v1/jurisprudence/searches/clear/

    Deleta todo o histórico de buscas do usuário autenticado.
    """
    from ..models import JurisprudenceSearch

    deleted_count, _ = JurisprudenceSearch.objects.filter(user=request.user).delete()
    return Response({'deleted': deleted_count}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def scrape_jurisprudencia(request):
    """
    POST /api/v1/jurisprudence/scrape/
    Body: { "url": "https://..." }

    Tenta buscar o conteúdo textual da página de um tribunal.
    Retorna { "text": "...", "url": "..." } para uso como contexto no Copilot.
    """
    import re
    import requests as http_req

    url = (request.data.get('url') or '').strip()
    if not url or not url.startswith('http'):
        return Response({'detail': 'URL inválida.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        resp = http_req.get(
            url,
            timeout=10,
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/124.0 Safari/537.36'
                ),
                'Accept-Language': 'pt-BR,pt;q=0.9',
            },
            allow_redirects=True,
        )
        resp.raise_for_status()
        # Extrai texto removendo tags HTML e normalizando espaços
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', resp.text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&quot;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return Response({'text': text[:6000], 'url': url, 'success': True})
    except Exception as e:
        logger.warning('Scrape falhou para %s: %s', url, e)
        return Response(
            {'text': '', 'url': url, 'success': False, 'detail': str(e)},
            status=status.HTTP_200_OK,  # retorna 200 mesmo assim — frontend usa fallback
        )
