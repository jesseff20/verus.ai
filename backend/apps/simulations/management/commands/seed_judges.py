"""
Seed: popula magistrados (juizes titulares) para TODAS as comarcas cadastradas.
Idempotente -- usa get_or_create.

Capitais recebem 10 varas (civel, criminal, familia, fazenda, execucoes,
juri, infancia, trabalho). Demais comarcas recebem 3 varas basicas
(civel, criminal, familia).

Duas abordagens:
  1. Dados pre-compilados (padrao) -- gera registros genericos
  2. Scraping real (--scrape) -- tenta extrair de sites dos tribunais
"""
from django.core.management.base import BaseCommand
import logging

from apps.simulations.models import Court, JudgeProfile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapeamento estado -> capital (para determinar quais comarcas sao capitais)
# ---------------------------------------------------------------------------
CAPITAIS = {
    'AC': 'Rio Branco',
    'AL': 'Maceio',
    'AP': 'Macapa',
    'AM': 'Manaus',
    'BA': 'Salvador',
    'CE': 'Fortaleza',
    'DF': 'Brasilia',
    'ES': 'Vitoria',
    'GO': 'Goiania',
    'MA': 'Sao Luis',
    'MT': 'Cuiaba',
    'MS': 'Campo Grande',
    'MG': 'Belo Horizonte',
    'PA': 'Belem',
    'PB': 'Joao Pessoa',
    'PR': 'Curitiba',
    'PE': 'Recife',
    'PI': 'Teresina',
    'RJ': 'Rio de Janeiro',
    'RN': 'Natal',
    'RS': 'Porto Alegre',
    'RO': 'Porto Velho',
    'RR': 'Boa Vista',
    'SC': 'Florianopolis',
    'SP': 'Sao Paulo',
    'SE': 'Aracaju',
    'TO': 'Palmas',
}

# ---------------------------------------------------------------------------
# Varas por tipo de comarca
# ---------------------------------------------------------------------------
VARAS_CAPITAL = [
    ('1a Vara Civel', 'Civel'),
    ('2a Vara Civel', 'Civel'),
    ('1a Vara Criminal', 'Criminal'),
    ('2a Vara Criminal', 'Criminal'),
    ('Vara de Familia e Sucessoes', 'Familia'),
    ('Vara da Fazenda Publica', 'Administrativo'),
    ('Vara de Execucoes Penais', 'Criminal'),
    ('Vara do Juri', 'Criminal'),
    ('Vara da Infancia e Juventude', 'Familia'),
    ('Vara do Trabalho (TRT)', 'Trabalhista'),
]

VARAS_INTERIOR = [
    ('Vara Civel', 'Civel'),
    ('Vara Criminal', 'Criminal'),
    ('Vara de Familia', 'Familia'),
]

# ---------------------------------------------------------------------------
# Fontes para scraping real
# ---------------------------------------------------------------------------
TRIBUNAL_SOURCES = {
    'SP': {
        'court': 'TJSP',
        'url': 'https://www.tjsp.jus.br/PrimeiraInstancia/Juizes',
        'strategy': 'tjsp',
    },
    'RJ': {
        'court': 'TJRJ',
        'url': 'https://www.tjrj.jus.br/consultas/magistrados/juizes',
        'strategy': 'tjrj',
    },
    'BA': {
        'court': 'TJBA',
        'url': 'https://www.tjba.jus.br/portal/relacao-de-magistrados/',
        'strategy': 'generic_html',
    },
    'PR': {
        'court': 'TJPR',
        'url': 'https://www.tjpr.jus.br/magistrados',
        'strategy': 'generic_html',
    },
}


def _build_precompiled_data():
    """Gera lista de magistrados genericos para todas as comarcas cadastradas."""
    records = []

    # Busca comarcas dos TJs cadastrados
    try:
        tjs = Court.objects.filter(court_type='TJ', is_active=True)
    except Exception as e:
        # Se a tabela nao existir ainda, usa fallback
        logger.warning("Failed to query Court table (may not exist yet): %s", e)
        tjs = []

    if tjs:
        for court in tjs:
            state = court.state
            court_name = court.name
            capital = CAPITAIS.get(state, '')

            for comarca in court.comarcas:
                is_capital = (comarca == capital)
                varas = VARAS_CAPITAL if is_capital else VARAS_INTERIOR

                for vara, spec in varas:
                    records.append({
                        'name': f'Juiz Titular - {vara}',
                        'state': state,
                        'court': court_name,
                        'comarca': comarca,
                        'vara': vara,
                        'specialization': spec,
                    })
    else:
        # Fallback: gerar apenas para capitais se Court nao tem dados
        for state, capital in CAPITAIS.items():
            court_name = f'TJDFT' if state == 'DF' else f'TJ{state}'
            for vara, spec in VARAS_CAPITAL:
                records.append({
                    'name': f'Juiz Titular - {vara}',
                    'state': state,
                    'court': court_name,
                    'comarca': capital,
                    'vara': vara,
                    'specialization': spec,
                })

    return records


class Command(BaseCommand):
    help = 'Importa magistrados dos tribunais de justica (todas as comarcas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Atualiza registros existentes (sobrescreve profile_data)',
        )
        parser.add_argument(
            '--scrape',
            action='store_true',
            help='Tenta scraping real dos sites dos tribunais',
        )
        parser.add_argument(
            '--state',
            type=str,
            default=None,
            help='Importa apenas um estado (sigla, ex: SP)',
        )

    def handle(self, *args, **options):
        state_filter = options['state'].upper() if options['state'] else None
        force = options['force']

        # 1. Dados pre-compilados (sempre)
        pre_created, pre_updated = self._seed_precompiled(state_filter, force)

        # 2. Scraping real (se --scrape)
        scrape_created = 0
        if options['scrape']:
            scrape_created = self._seed_from_scraping(state_filter, force)

        total = JudgeProfile.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'seed_judges: {pre_created} criados, {pre_updated} atualizados '
            f'(scraping: {scrape_created}) -- total: {total}'
        ))

    # ------------------------------------------------------------------
    # Abordagem 1: dados pre-compilados
    # ------------------------------------------------------------------
    def _seed_precompiled(self, state_filter, force):
        created_count = 0
        updated_count = 0

        # Gera dados dinamicamente a partir dos Courts cadastrados
        records = _build_precompiled_data()

        for entry in records:
            if state_filter and entry['state'] != state_filter:
                continue

            obj, created = JudgeProfile.objects.get_or_create(
                name=entry['name'],
                court=entry['court'],
                comarca=entry['comarca'],
                defaults={
                    'state': entry['state'],
                    'vara': entry['vara'],
                    'specialization': entry['specialization'],
                    'profile_data': {
                        'source': 'seed_precompiled',
                        'generic': True,
                    },
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
            elif force:
                obj.state = entry['state']
                obj.vara = entry['vara']
                obj.specialization = entry['specialization']
                obj.profile_data = {
                    'source': 'seed_precompiled',
                    'generic': True,
                }
                obj.save()
                updated_count += 1

        return created_count, updated_count

    # ------------------------------------------------------------------
    # Abordagem 2: scraping real
    # ------------------------------------------------------------------
    def _seed_from_scraping(self, state_filter, force):
        try:
            import requests
            from bs4 import BeautifulSoup  # noqa: F401
        except ImportError:
            self.stdout.write(self.style.WARNING(
                'requests/beautifulsoup4 nao instalados -- scraping ignorado'
            ))
            return 0

        created_total = 0
        sources = TRIBUNAL_SOURCES

        if state_filter:
            sources = {k: v for k, v in sources.items() if k == state_filter}

        for state, config in sources.items():
            capital = CAPITAIS.get(state, '')
            judges = self._scrape_tribunal(state, config)
            for judge in judges:
                _, created = JudgeProfile.objects.get_or_create(
                    name=judge['name'],
                    court=judge['court'],
                    comarca=judge.get('comarca', capital),
                    defaults={
                        'state': state,
                        'vara': judge.get('vara', ''),
                        'specialization': judge.get('specialization', ''),
                        'profile_data': {
                            'source': 'scraping',
                            'url': config['url'],
                        },
                        'is_active': True,
                    },
                )
                if created:
                    created_total += 1

        return created_total

    def _scrape_tribunal(self, state, config):
        """Tenta extrair magistrados do site do tribunal."""
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
        }

        try:
            response = requests.get(
                config['url'], timeout=15, headers=headers,
            )
            response.raise_for_status()
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'Scraping falhou para {state} ({config["url"]}): {e}'
            ))
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        strategy = config.get('strategy', 'generic_html')

        if strategy == 'tjsp':
            return self._parse_tjsp(soup, config)
        elif strategy == 'tjrj':
            return self._parse_tjrj(soup, config)
        else:
            return self._parse_generic(soup, config)

    def _parse_tjsp(self, soup, config):
        """Parser especifico para TJSP."""
        judges = []
        for row in soup.select('table tr, .lista-magistrados li, .juiz-item'):
            text = row.get_text(strip=True)
            if text and len(text) > 5 and 'Juiz' in text or 'Dr.' in text:
                judges.append({
                    'name': text[:200],
                    'court': config['court'],
                })
        self.stdout.write(f'  TJSP: {len(judges)} magistrados extraidos')
        return judges

    def _parse_tjrj(self, soup, config):
        """Parser especifico para TJRJ."""
        judges = []
        for row in soup.select('table tr, .magistrado, .juiz'):
            text = row.get_text(strip=True)
            if text and len(text) > 5:
                judges.append({
                    'name': text[:200],
                    'court': config['court'],
                })
        self.stdout.write(f'  TJRJ: {len(judges)} magistrados extraidos')
        return judges

    def _parse_generic(self, soup, config):
        """Parser generico -- busca padroes comuns em paginas de tribunais."""
        judges = []
        # Busca em tabelas
        for row in soup.select('table tbody tr'):
            cells = row.find_all('td')
            if cells and len(cells) >= 1:
                name = cells[0].get_text(strip=True)
                if name and len(name) > 3:
                    judge = {'name': name[:200], 'court': config['court']}
                    if len(cells) >= 2:
                        judge['comarca'] = cells[1].get_text(strip=True)[:200]
                    if len(cells) >= 3:
                        judge['vara'] = cells[2].get_text(strip=True)[:200]
                    judges.append(judge)

        # Fallback: busca em listas
        if not judges:
            for item in soup.select('ul li, ol li'):
                text = item.get_text(strip=True)
                if text and len(text) > 5 and any(
                    kw in text.lower()
                    for kw in ['juiz', 'magistrad', 'dr.', 'dra.', 'desembarg']
                ):
                    judges.append({
                        'name': text[:200],
                        'court': config['court'],
                    })

        court_name = config['court']
        self.stdout.write(f'  {court_name}: {len(judges)} magistrados extraidos')
        return judges
