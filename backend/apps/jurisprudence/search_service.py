"""
Serviço de busca jurisprudencial via API Pública DataJud (CNJ).

Gratuita, oficial, cobre todos os 182 tribunais brasileiros.
A chave pública é disponibilizada pelo próprio CNJ em:
  https://datajud-wiki.cnj.jus.br/api-publica/acesso/

Sem dependência de VPS-friendly ou API keys pagas — IPs de datacenter
são aceitos pela API CNJ sem bloqueio ou rate-limit agressivo.
"""

import hashlib
import logging

import requests
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 60 * 6  # 6 horas

# Chave pública do CNJ — disponibilizada na documentação oficial sem cadastro.
# Pode ser sobrescrita via settings.DATAJUD_API_KEY.
_DEFAULT_API_KEY = 'cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=='

DATAJUD_BASE = 'https://api-publica.datajud.cnj.jus.br'

# Mapa de specialty → endpoints prioritários
SPECIALTY_TRIBUNALS = {
    'CIV': ['stj', 'tjsp', 'tjrj', 'tjmg'],
    'PEN': ['stj', 'tjsp', 'tjrj'],
    'TRB': ['tst', 'trt1', 'trt2', 'trt3'],
    'ADM': ['stj', 'stf'],
    'CON': ['stf', 'stj'],
    'TRI': ['stj', 'stf'],
    'FAM': ['stj', 'tjsp', 'tjrj'],
    'EMP': ['stj', 'tjsp'],
    'AMB': ['stj', 'stf'],
    'OUT': ['stj', 'stf'],
}

DEFAULT_TRIBUNALS = ['stj', 'stf', 'tst']

# Links para visualizar processos nos portais oficiais
TRIBUNAL_PORTAL = {
    'stj':  'https://processo.stj.jus.br/processo/pesquisa/?tipoPesquisa=tipoPesquisaNumeroUnico&termo={numero}',
    'stf':  'https://portal.stf.jus.br/processos/pesquisar.asp?classeNumero={numero}',
    'tst':  'https://consultaprocessual.tst.jus.br/consultaProcessual/consultaTstNumUnica.do?consulta=Consultar&numUnificado={numero}',
    'tse':  'https://www.tse.jus.br/servicos-judiciais/processo/consulta-processual/consulta-de-processos-do-tse',
    'tjsp': 'https://esaj.tjsp.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&dadosConsulta.valorConsultaNuUnificado={numero}&pbEnviar=Pesquisar',
    'tjrj': 'https://www3.tjrj.jus.br/consultaprocessual/#/consultapublica',
    'tjmg': 'https://pje-consulta-publica.tjmg.jus.br/',
    'tjrs': 'https://www.tjrs.jus.br/novo/busca/?numero_processo={numero}&CNJ=S&tipoConsulta=1',
    'trf1': 'https://pje1g-consultapublica.trf1.jus.br/consultapublica/ConsultaPublica/listView.seam',
    'trf2': 'https://eproc-consulta.trf2.jus.br/eproc2trf2/controlador.php?acao=processo_consulta_publica',
    'trt1': 'https://pje.trt1.jus.br/consultaprocessual/consulta-cidadao',
    'trt2': 'https://pje.trt2.jus.br/consultaprocessual/consulta-cidadao',
    'trt3': 'https://pje.trt3.jus.br/consultaprocessual/consulta-cidadao',
    'trt4': 'https://pje.trt4.jus.br/consultaprocessual/consulta-cidadao',
}


def _get_api_key() -> str:
    return getattr(settings, 'DATAJUD_API_KEY', None) or _DEFAULT_API_KEY


def _build_query(query: str, specialty_code: str | None) -> dict:
    """Monta query Elasticsearch para busca em assuntos e classe processual.

    Usa query_string em vez de match porque os campos de assuntos são arrays
    de objetos — match padrão não funciona em campos aninhados no DataJud.
    """
    terms = query.strip()
    # Escapa caracteres especiais que podem quebrar o query_string
    safe_terms = terms.replace('/', '\\/').replace('"', '\\"')

    return {
        'query': {
            'query_string': {
                'query': safe_terms,
                'fields': ['assuntos.nome^3', 'classe.nome^2', 'orgaoJulgador.nome'],
                'default_operator': 'OR',
                'fuzziness': 'AUTO',
            }
        },
        'sort': [{'dataAjuizamento': {'order': 'desc'}}],
        'size': 5,
        '_source': [
            'numeroProcesso', 'tribunal', 'classe',
            'assuntos', 'orgaoJulgador', 'dataAjuizamento', 'grau',
        ],
    }


def _parse_hit(hit: dict, tribunal_code: str) -> dict:
    """Converte um hit do Elasticsearch em formato padronizado."""
    from datetime import datetime

    src = hit.get('_source', {})

    numero = src.get('numeroProcesso', '')
    tribunal_nome = (src.get('tribunal') or tribunal_code.upper()).upper()
    classe_obj = src.get('classe') or {}
    classe = classe_obj.get('nome', '') if isinstance(classe_obj, dict) else ''
    grau = src.get('grau', '') or ''

    assuntos_raw = src.get('assuntos') or []
    assunto_list = [a.get('nome', '') for a in assuntos_raw if a.get('nome')]
    assunto_str = ', '.join(assunto_list[:3])

    orgao = src.get('orgaoJulgador', {})
    orgao_nome = orgao.get('nome', '') if isinstance(orgao, dict) else ''

    # DataJud retorna dataAjuizamento como "YYYYMMDDHHMMSS"
    data_raw = src.get('dataAjuizamento', '') or ''
    data_aj_iso = ''
    if data_raw and len(data_raw) >= 8:
        try:
            data_aj_iso = datetime.strptime(data_raw[:8], '%Y%m%d').strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Monta snippet descritivo (substitui ementa que a API não fornece)
    parts = [p for p in [classe, grau, assunto_str] if p]
    snippet = '. '.join(parts)
    if orgao_nome:
        snippet += f'. Órgão: {orgao_nome}'
    if data_aj_iso:
        snippet += f'. Ajuizado: {data_aj_iso}'

    title = f'{tribunal_nome} – {classe} {numero}'.strip(' –')

    # URL do portal oficial
    portal_tpl = TRIBUNAL_PORTAL.get(tribunal_code.lower())
    url = portal_tpl.format(numero=numero) if portal_tpl and numero else ''

    return {
        'title': title,
        'url': url,
        'snippet': snippet or f'Processo {numero} – {tribunal_nome}',
        'source': tribunal_nome,
        # campos estruturados para persistência e exibição
        'case_number': numero,
        'organ': orgao_nome,
        'assuntos': assunto_list,
        'classe': classe,
        'grau': grau,
        'judgment_date': data_aj_iso,  # '' ou 'YYYY-MM-DD'
    }


def _search_tribunal(query_body: dict, tribunal_code: str, api_key: str) -> list:
    """Busca em um tribunal específico via DataJud."""
    endpoint = f'{DATAJUD_BASE}/api_publica_{tribunal_code}/_search'
    headers = {
        'Authorization': f'APIKey {api_key}',
        'Content-Type': 'application/json',
    }
    try:
        response = requests.post(
            endpoint,
            json=query_body,
            headers=headers,
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        hits = data.get('hits', {}).get('hits', [])
        return [_parse_hit(hit, tribunal_code) for hit in hits]
    except requests.exceptions.Timeout:
        logger.warning('DataJud timeout para tribunal %s', tribunal_code)
    except requests.exceptions.HTTPError as e:
        logger.warning('DataJud HTTP error para %s: %s', tribunal_code, e)
    except Exception as e:
        logger.warning('DataJud erro para %s: %s', tribunal_code, e)
    return []


def search_jurisprudencia(query: str, specialty: str = None, max_results: int = 10) -> list:
    """
    Busca jurisprudência via API Pública DataJud (CNJ).
    Retorna lista de dicts com keys: title, url, snippet, source.
    """
    if not query or len(query.strip()) < 3:
        return []

    cache_key = f'jurisprudencia:datajud:{hashlib.md5(f"{query}:{specialty}".encode()).hexdigest()}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    api_key = _get_api_key()
    query_body = _build_query(query, specialty)

    # Seleciona tribunais com base na especialidade
    tribunals = SPECIALTY_TRIBUNALS.get(specialty or '', DEFAULT_TRIBUNALS)

    results: list = []
    seen_numbers: set = set()

    for trib in tribunals:
        if len(results) >= max_results:
            break
        hits = _search_tribunal(query_body, trib, api_key)
        for hit in hits:
            # Deduplica por título/número
            key = hit['title']
            if key not in seen_numbers:
                seen_numbers.add(key)
                results.append(hit)

    final = results[:max_results]
    cache.set(cache_key, final, CACHE_TTL)
    return final


def _extract_source(url: str) -> str:
    """Extrai nome do tribunal/fonte da URL."""
    source_map = {
        'stj.jus.br': 'STJ', 'stf.jus.br': 'STF', 'trt': 'TRT',
        'tse.jus.br': 'TSE', 'jusbrasil': 'JusBrasil',
        'tjsp': 'TJSP', 'tjrj': 'TJRJ', 'tjmg': 'TJMG',
        'tjrs': 'TJRS', 'tjba': 'TJBA',
    }
    url_lower = url.lower()
    for key, name in source_map.items():
        if key in url_lower:
            return name
    return 'Tribunal'
