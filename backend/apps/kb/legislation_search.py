"""
Serviço de busca de legislação em fontes oficiais brasileiras.

Consulta sites como planalto.gov.br, STF, STJ, TST e CNJ quando a
Knowledge Base local não possui informação suficiente.
"""
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Timeout padrão para requisições HTTP
REQUEST_TIMEOUT = 15

# User-Agent para evitar bloqueios
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0 Safari/537.36'
    ),
    'Accept-Language': 'pt-BR,pt;q=0.9',
}

# Limite de caracteres no texto retornado
MAX_TEXT_LENGTH = 8000


class LegislationSearchService:
    """Busca legislação em fontes oficiais quando a KB não é suficiente."""

    FONTES_OFICIAIS = {
        'planalto': 'https://www.planalto.gov.br',
        'stf': 'https://portal.stf.jus.br',
        'stj': 'https://www.stj.jus.br',
        'tst': 'https://www.tst.jus.br',
        'cnj': 'https://atos.cnj.jus.br',
    }

    # ------------------------------------------------------------------ #
    #  Busca no Planalto
    # ------------------------------------------------------------------ #
    @staticmethod
    def search_planalto(query: str) -> Dict:
        """
        Busca legislação no planalto.gov.br via Google site-restricted search.

        Faz scraping dos resultados do Google restrito ao domínio
        planalto.gov.br e tenta baixar o texto da primeira lei encontrada.

        Args:
            query: Termo de busca (ex: "lei 11343 art 33")

        Returns:
            Dict com keys: results (list), text (str), source (str), success (bool)
        """
        encoded_query = quote_plus(f"site:planalto.gov.br {query}")
        search_url = f"https://www.google.com/search?q={encoded_query}&hl=pt-BR&num=5"

        try:
            resp = requests.get(
                search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser')

            results: List[Dict] = []
            for g in soup.select('div.g, div[data-sokoban-container]'):
                link_tag = g.find('a', href=True)
                title_tag = g.find('h3')
                snippet_tag = g.find('span', class_=re.compile(r'aCOpRe|st'))

                if not link_tag or 'planalto.gov.br' not in link_tag['href']:
                    continue

                results.append({
                    'title': title_tag.get_text(strip=True) if title_tag else '',
                    'url': link_tag['href'],
                    'snippet': snippet_tag.get_text(strip=True) if snippet_tag else '',
                })

                if len(results) >= 3:
                    break

            # Tentar baixar texto da primeira lei encontrada
            text = ''
            if results:
                text = LegislationSearchService.fetch_law_text(results[0]['url'])

            return {
                'results': results,
                'text': text,
                'source': 'planalto.gov.br',
                'success': bool(results),
            }

        except Exception as e:
            logger.warning('[LegislationSearch] Erro ao buscar no Planalto: %s', e)
            return {
                'results': [],
                'text': '',
                'source': 'planalto.gov.br',
                'success': False,
                'error': str(e),
            }

    # ------------------------------------------------------------------ #
    #  Fetch do texto de uma lei
    # ------------------------------------------------------------------ #
    @staticmethod
    def fetch_law_text(url: str) -> str:
        """
        Faz download do texto de uma lei a partir de URL oficial.

        Remove scripts, estilos, nav, header e footer, retornando
        apenas o conteúdo textual limitado a MAX_TEXT_LENGTH caracteres.

        Args:
            url: URL completa da lei (ex: https://www.planalto.gov.br/ccivil_03/...)

        Returns:
            Texto limpo da lei (até 8000 caracteres)
        """
        try:
            response = requests.get(
                url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            response.encoding = 'utf-8'
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remover elementos não-textuais
            for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                             'iframe', 'noscript']):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)

            # Normalizar espaços em branco
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)

            return text[:MAX_TEXT_LENGTH]

        except Exception as e:
            logger.warning('[LegislationSearch] Erro ao baixar texto de %s: %s', url, e)
            return ''

    # ------------------------------------------------------------------ #
    #  Súmulas Vinculantes (STF)
    # ------------------------------------------------------------------ #
    @staticmethod
    def search_sumulas_stf(tema: str) -> Dict:
        """
        Busca súmulas vinculantes do STF relacionadas ao tema.

        Usa a página de pesquisa de jurisprudência do STF.

        Args:
            tema: Tema ou palavras-chave (ex: "direito adquirido")

        Returns:
            Dict com keys: results (list), text (str), source (str), success (bool)
        """
        encoded_tema = quote_plus(tema)
        search_url = (
            f"https://jurisprudencia.stf.jus.br/pages/search?"
            f"base=sumulas&pesquisa_inteiro_teor=false"
            f"&sinonimo=true&plural=true&radicais=false"
            f"&buscaExata=true&page=1&pageSize=5"
            f"&queryString={encoded_tema}&sort=_score&sortBy=desc"
        )

        try:
            resp = requests.get(
                search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()

            # A API do STF retorna JSON
            data = resp.json()
            results = []

            for item in data.get('result', [])[:5]:
                results.append({
                    'titulo': item.get('titulo', ''),
                    'enunciado': item.get('enunciado', item.get('resumo', '')),
                    'numero': item.get('numero', ''),
                    'url': item.get('url', ''),
                })

            combined_text = '\n\n'.join(
                f"Súmula {r['numero']}: {r['enunciado']}" for r in results
            )

            return {
                'results': results,
                'text': combined_text[:MAX_TEXT_LENGTH],
                'source': 'stf.jus.br (súmulas)',
                'success': bool(results),
            }

        except Exception as e:
            logger.warning('[LegislationSearch] Erro ao buscar súmulas STF: %s', e)
            # Fallback: buscar via Google
            return LegislationSearchService._google_site_search(
                tema, 'portal.stf.jus.br', 'stf.jus.br (súmulas)',
            )

    # ------------------------------------------------------------------ #
    #  Jurisprudência STJ
    # ------------------------------------------------------------------ #
    @staticmethod
    def search_jurisprudencia_stj(tema: str) -> Dict:
        """
        Busca jurisprudência no STJ.

        Args:
            tema: Tema ou palavras-chave

        Returns:
            Dict com keys: results (list), text (str), source (str), success (bool)
        """
        encoded_tema = quote_plus(tema)
        search_url = (
            f"https://scon.stj.jus.br/SCON/pesquisar.jsp?"
            f"livre={encoded_tema}&operador=e&tipo=null&b=ACOR&thesaurus=JURIDICO"
        )

        try:
            resp = requests.get(
                search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            resp.encoding = 'utf-8'
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser')

            results = []
            # Tentar extrair resultados da página do STJ
            for item in soup.select('.docTitulo, .clsDocTitulo, .resultado'):
                titulo = item.get_text(strip=True)
                link = item.find('a', href=True)
                url = link['href'] if link else ''
                if not url.startswith('http'):
                    url = f"https://scon.stj.jus.br{url}"

                results.append({
                    'titulo': titulo[:200],
                    'url': url,
                })

                if len(results) >= 5:
                    break

            # Extrair texto da página de resultados
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)
            text = re.sub(r'\n{3,}', '\n\n', text)

            return {
                'results': results,
                'text': text[:MAX_TEXT_LENGTH],
                'source': 'stj.jus.br',
                'success': bool(results) or len(text) > 100,
            }

        except Exception as e:
            logger.warning('[LegislationSearch] Erro ao buscar STJ: %s', e)
            return LegislationSearchService._google_site_search(
                tema, 'stj.jus.br', 'stj.jus.br',
            )

    # ------------------------------------------------------------------ #
    #  Busca combinada em todas as fontes
    # ------------------------------------------------------------------ #
    @staticmethod
    def search_all(query: str, fontes: Optional[List[str]] = None) -> Dict:
        """
        Busca em múltiplas fontes oficiais e combina os resultados.

        Args:
            query: Termo de busca
            fontes: Lista de fontes a consultar. Default: ['planalto', 'stf', 'stj']

        Returns:
            Dict com resultados consolidados de todas as fontes
        """
        if fontes is None:
            fontes = ['planalto', 'stf', 'stj']

        all_results: Dict = {
            'query': query,
            'fontes': {},
            'combined_text': '',
            'total_results': 0,
        }

        handlers = {
            'planalto': lambda q: LegislationSearchService.search_planalto(q),
            'stf': lambda q: LegislationSearchService.search_sumulas_stf(q),
            'stj': lambda q: LegislationSearchService.search_jurisprudencia_stj(q),
        }

        texts = []

        for fonte in fontes:
            handler = handlers.get(fonte)
            if not handler:
                continue

            result = handler(query)
            all_results['fontes'][fonte] = result
            all_results['total_results'] += len(result.get('results', []))

            if result.get('text'):
                texts.append(f"--- {result['source']} ---\n{result['text']}")

        all_results['combined_text'] = '\n\n'.join(texts)[:MAX_TEXT_LENGTH]

        return all_results

    # ------------------------------------------------------------------ #
    #  Helper: Google site-restricted search (fallback genérico)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _google_site_search(query: str, site: str, source_label: str) -> Dict:
        """
        Fallback genérico: busca no Google restrito a um site.

        Args:
            query: Termo de busca
            site: Domínio para restringir (ex: stj.jus.br)
            source_label: Label para o campo source no retorno

        Returns:
            Dict com keys: results, text, source, success
        """
        encoded = quote_plus(f"site:{site} {query}")
        url = f"https://www.google.com/search?q={encoded}&hl=pt-BR&num=5"

        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style']):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)
            text = re.sub(r'\n{3,}', '\n\n', text)

            return {
                'results': [],
                'text': text[:MAX_TEXT_LENGTH],
                'source': source_label,
                'success': len(text) > 100,
            }

        except Exception as e:
            logger.warning('[LegislationSearch] Google fallback falhou para %s: %s', site, e)
            return {
                'results': [],
                'text': '',
                'source': source_label,
                'success': False,
                'error': str(e),
            }
