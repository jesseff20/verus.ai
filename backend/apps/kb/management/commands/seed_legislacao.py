"""
Management command para importar legislacao brasileira oficial na base de conhecimento.

Carrega textos integrais a partir de arquivos locais em data/legislacao/ (preferencial)
ou faz download do planalto.gov.br como fallback.
Cria Documents com category='lei' e processa chunks com embeddings via EmbeddingService.
"""
import os
import re
import time
import logging
import unicodedata

import requests
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.kb.models import Document, DocumentChunk
from apps.kb.services import DocumentProcessingService
from apps.agents.services import EmbeddingService

User = get_user_model()
logger = logging.getLogger(__name__)

LEGISLACOES = [
    {
        'name': 'Constituicao Federal de 1988',
        'url': 'https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm',
        'category': 'lei',
        'tags': ['constituicao', 'CF/88', 'direito constitucional'],
    },
    {
        'name': 'Codigo de Processo Civil (CPC/2015)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm',
        'category': 'lei',
        'tags': ['CPC', 'processo civil', 'CPC/2015'],
    },
    {
        'name': 'Codigo Civil (CC/2002)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm',
        'category': 'lei',
        'tags': ['codigo civil', 'CC/2002', 'direito civil'],
    },
    {
        'name': 'Codigo Penal (CP/1940)',
        'url': 'https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm',
        'category': 'lei',
        'tags': ['codigo penal', 'CP', 'direito penal'],
    },
    {
        'name': 'Codigo de Processo Penal (CPP/1941)',
        'url': 'https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm',
        'category': 'lei',
        'tags': ['CPP', 'processo penal'],
    },
    {
        'name': 'CLT - Consolidacao das Leis do Trabalho',
        'url': 'https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm',
        'category': 'lei',
        'tags': ['CLT', 'direito trabalhista', 'trabalho'],
    },
    {
        'name': 'Codigo de Defesa do Consumidor (CDC)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm',
        'category': 'lei',
        'tags': ['CDC', 'consumidor', 'direito do consumidor'],
    },
    {
        'name': 'Codigo Tributario Nacional (CTN)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm',
        'category': 'lei',
        'tags': ['CTN', 'direito tributario', 'tributos'],
    },
    {
        'name': 'Lei de Improbidade Administrativa',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8429.htm',
        'category': 'lei',
        'tags': ['improbidade', 'administrativo'],
    },
    {
        'name': 'Lei de Execucoes Penais (LEP)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l7210.htm',
        'category': 'lei',
        'tags': ['LEP', 'execucao penal'],
    },
    {
        'name': 'Estatuto da Crianca e do Adolescente (ECA)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8069.htm',
        'category': 'lei',
        'tags': ['ECA', 'crianca', 'adolescente', 'familia'],
    },
    {
        'name': 'Lei Maria da Penha',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm',
        'category': 'lei',
        'tags': ['Maria da Penha', 'violencia domestica', 'criminal'],
    },
    {
        'name': 'LGPD - Lei Geral de Protecao de Dados',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm',
        'category': 'lei',
        'tags': ['LGPD', 'protecao de dados', 'digital', 'privacidade'],
    },
    {
        'name': 'Marco Civil da Internet',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm',
        'category': 'lei',
        'tags': ['Marco Civil', 'internet', 'digital'],
    },
    {
        'name': 'Lei de Recuperacao Judicial e Falencia',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/lei/l11101.htm',
        'category': 'lei',
        'tags': ['falencia', 'recuperacao judicial', 'empresarial'],
    },
    {
        'name': 'Lei de Licitacoes (Nova)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm',
        'category': 'lei',
        'tags': ['licitacao', 'administrativo', 'contratos publicos'],
    },
    {
        'name': 'Lei dos Juizados Especiais',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9099.htm',
        'category': 'lei',
        'tags': ['JEC', 'juizados especiais', 'civel'],
    },
    {
        'name': 'Lei do Mandado de Seguranca',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/lei/l12016.htm',
        'category': 'lei',
        'tags': ['mandado de seguranca', 'constitucional'],
    },
    {
        'name': 'Lei da Acao Civil Publica',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l7347orig.htm',
        'category': 'lei',
        'tags': ['ACP', 'acao civil publica', 'ambiental', 'consumidor'],
    },
    {
        'name': 'Estatuto do Idoso',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741.htm',
        'category': 'lei',
        'tags': ['idoso', 'direitos do idoso'],
    },

    # ============================================
    # CÓDIGOS FUNDAMENTAIS (complementares)
    # ============================================
    {
        'name': 'Codigo Penal Militar',
        'url': 'https://www.planalto.gov.br/ccivil_03/decreto-lei/del1001compilado.htm',
        'category': 'lei',
        'tags': ['código penal militar', 'CPM', 'militar'],
    },
    {
        'name': 'Codigo de Processo Penal Militar',
        'url': 'https://www.planalto.gov.br/ccivil_03/decreto-lei/del1002compilado.htm',
        'category': 'lei',
        'tags': ['CPPM', 'processo penal militar', 'militar'],
    },
    {
        'name': 'Codigo Eleitoral',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l4737compilado.htm',
        'category': 'lei',
        'tags': ['código eleitoral', 'eleitoral', 'eleições'],
    },
    {
        'name': 'Codigo de Transito Brasileiro (CTB)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm',
        'category': 'lei',
        'tags': ['CTB', 'trânsito', 'administrativo'],
    },

    # ============================================
    # DIREITO PREVIDENCIÁRIO E TRABALHO
    # ============================================
    {
        'name': 'Lei de Beneficios da Previdencia Social (8.213/91)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8213cons.htm',
        'category': 'lei',
        'tags': ['previdência', 'INSS', 'benefícios', 'previdenciário'],
    },
    {
        'name': 'Lei Organica da Seguridade Social (8.212/91)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8212cons.htm',
        'category': 'lei',
        'tags': ['seguridade social', 'custeio', 'previdenciário'],
    },
    {
        'name': 'Lei do FGTS',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8036consol.htm',
        'category': 'lei',
        'tags': ['FGTS', 'trabalhista', 'trabalho'],
    },

    # ============================================
    # DIREITO IMOBILIÁRIO E LOCAÇÃO
    # ============================================
    {
        'name': 'Lei do Inquilinato (8.245/91)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8245.htm',
        'category': 'lei',
        'tags': ['inquilinato', 'locação', 'imobiliário', 'despejo'],
    },
    {
        'name': 'Lei de Registros Publicos (6.015/73)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm',
        'category': 'lei',
        'tags': ['registros públicos', 'cartório', 'imobiliário'],
    },
    {
        'name': 'Lei do Condominio (4.591/64)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l4591.htm',
        'category': 'lei',
        'tags': ['condomínio', 'imobiliário', 'incorporação'],
    },

    # ============================================
    # DIREITO PENAL ESPECIAL
    # ============================================
    {
        'name': 'Lei de Crimes Hediondos (8.072/90)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8072.htm',
        'category': 'lei',
        'tags': ['crimes hediondos', 'penal'],
    },
    {
        'name': 'Lei de Drogas (11.343/06)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11343.htm',
        'category': 'lei',
        'tags': ['drogas', 'tráfico', 'penal'],
    },
    {
        'name': 'Lei de Abuso de Autoridade (13.869/19)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/lei/l13869.htm',
        'category': 'lei',
        'tags': ['abuso de autoridade', 'penal', 'administrativo'],
    },
    {
        'name': 'Lei de Crimes Ambientais (9.605/98)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9605.htm',
        'category': 'lei',
        'tags': ['crimes ambientais', 'ambiental', 'penal'],
    },
    {
        'name': 'Lei Anticorrupcao Empresarial (12.846/13)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/lei/l12846.htm',
        'category': 'lei',
        'tags': ['anticorrupção', 'compliance', 'empresarial'],
    },
    {
        'name': 'Lei de Lavagem de Dinheiro (9.613/98)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9613.htm',
        'category': 'lei',
        'tags': ['lavagem de dinheiro', 'penal', 'financeiro'],
    },
    {
        'name': 'Lei de Organizacoes Criminosas (12.850/13)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/lei/l12850.htm',
        'category': 'lei',
        'tags': ['organização criminosa', 'delação premiada', 'penal'],
    },
    {
        'name': 'Lei de Tortura (9.455/97)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9455.htm',
        'category': 'lei',
        'tags': ['tortura', 'penal', 'direitos humanos'],
    },

    # ============================================
    # DIREITO ADMINISTRATIVO
    # ============================================
    {
        'name': 'Lei do Processo Administrativo Federal (9.784/99)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9784.htm',
        'category': 'lei',
        'tags': ['processo administrativo', 'administrativo'],
    },
    {
        'name': 'Lei de Acesso a Informacao (12.527/11)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm',
        'category': 'lei',
        'tags': ['acesso à informação', 'LAI', 'administrativo', 'transparência'],
    },
    {
        'name': 'Estatuto dos Servidores Publicos Federais (8.112/90)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8112cons.htm',
        'category': 'lei',
        'tags': ['servidor público', 'administrativo', 'funcional'],
    },
    {
        'name': 'Lei de Responsabilidade Fiscal (LC 101/2000)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp101.htm',
        'category': 'lei',
        'tags': ['responsabilidade fiscal', 'finanças públicas', 'administrativo'],
    },
    {
        'name': 'Lei de Concessoes (8.987/95)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8987cons.htm',
        'category': 'lei',
        'tags': ['concessões', 'serviço público', 'administrativo'],
    },

    # ============================================
    # DIREITO EMPRESARIAL E SOCIETÁRIO
    # ============================================
    {
        'name': 'Lei das Sociedades por Acoes (6.404/76)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l6404consol.htm',
        'category': 'lei',
        'tags': ['sociedades anônimas', 'S.A.', 'empresarial', 'societário'],
    },
    {
        'name': 'Lei de Arbitragem (9.307/96)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9307.htm',
        'category': 'lei',
        'tags': ['arbitragem', 'ADR', 'empresarial'],
    },
    {
        'name': 'Lei do Registro de Empresas (8.934/94)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8934.htm',
        'category': 'lei',
        'tags': ['registro de empresas', 'junta comercial', 'empresarial'],
    },

    # ============================================
    # ESTATUTOS ESPECIAIS (FAMÍLIA E VULNERÁVEIS)
    # ============================================
    {
        'name': 'Estatuto da Pessoa com Deficiencia (13.146/15)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm',
        'category': 'lei',
        'tags': ['deficiência', 'acessibilidade', 'inclusão'],
    },
    {
        'name': 'Estatuto da Juventude (12.852/13)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/lei/l12852.htm',
        'category': 'lei',
        'tags': ['juventude', 'jovem', 'direitos'],
    },
    {
        'name': 'Estatuto da Igualdade Racial (12.288/10)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/lei/l12288.htm',
        'category': 'lei',
        'tags': ['igualdade racial', 'racismo', 'direitos humanos'],
    },
    {
        'name': 'Lei de Alienacao Parental (12.318/10)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/lei/l12318.htm',
        'category': 'lei',
        'tags': ['alienação parental', 'família', 'guarda'],
    },
    {
        'name': 'Lei da Guarda Compartilhada (13.058/14)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l13058.htm',
        'category': 'lei',
        'tags': ['guarda compartilhada', 'família', 'filhos'],
    },

    # ============================================
    # DIREITO AMBIENTAL E URBANÍSTICO
    # ============================================
    {
        'name': 'Estatuto da Cidade (10.257/01)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10257.htm',
        'category': 'lei',
        'tags': ['estatuto da cidade', 'urbanismo', 'imobiliário'],
    },
    {
        'name': 'Codigo Florestal (12.651/12)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12651.htm',
        'category': 'lei',
        'tags': ['código florestal', 'ambiental', 'APP', 'reserva legal'],
    },
    {
        'name': 'Politica Nacional do Meio Ambiente (6.938/81)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l6938.htm',
        'category': 'lei',
        'tags': ['meio ambiente', 'PNMA', 'ambiental'],
    },
    {
        'name': 'Lei de Recursos Hidricos (9.433/97)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9433.htm',
        'category': 'lei',
        'tags': ['recursos hídricos', 'água', 'ambiental'],
    },

    # ============================================
    # DIREITO ELEITORAL
    # ============================================
    {
        'name': 'Lei das Eleicoes (9.504/97)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9504.htm',
        'category': 'lei',
        'tags': ['eleições', 'campanha', 'eleitoral'],
    },
    {
        'name': 'Lei das Inelegibilidades (LC 64/90)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp64.htm',
        'category': 'lei',
        'tags': ['inelegibilidade', 'ficha limpa', 'eleitoral'],
    },
    {
        'name': 'Lei dos Partidos Politicos (9.096/95)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9096.htm',
        'category': 'lei',
        'tags': ['partidos políticos', 'eleitoral'],
    },

    # ============================================
    # DIREITO MILITAR
    # ============================================
    {
        'name': 'Estatuto dos Militares (6.880/80)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l6880.htm',
        'category': 'lei',
        'tags': ['estatuto militar', 'forças armadas', 'militar'],
    },

    # ============================================
    # DIREITO PROFISSIONAL E OAB
    # ============================================
    {
        'name': 'Estatuto da Advocacia e OAB (8.906/94)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8906.htm',
        'category': 'lei',
        'tags': ['OAB', 'advocacia', 'advogado', 'ética'],
    },

    # ============================================
    # DIREITO DO CONSUMIDOR COMPLEMENTAR
    # ============================================
    {
        'name': 'Lei do Superendividamento (14.181/21)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14181.htm',
        'category': 'lei',
        'tags': ['superendividamento', 'consumidor', 'crédito'],
    },

    # ============================================
    # DIREITO AGRÁRIO
    # ============================================
    {
        'name': 'Estatuto da Terra (4.504/64)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l4504.htm',
        'category': 'lei',
        'tags': ['estatuto da terra', 'agrário', 'reforma agrária'],
    },

    # ============================================
    # DIREITO DIGITAL E TECNOLOGIA
    # ============================================
    {
        'name': 'Lei de Crimes Ciberneticos (12.737/12)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12737.htm',
        'category': 'lei',
        'tags': ['crimes cibernéticos', 'Carolina Dieckmann', 'digital', 'penal'],
    },
    {
        'name': 'Lei de Direitos Autorais (9.610/98)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9610.htm',
        'category': 'lei',
        'tags': ['direitos autorais', 'copyright', 'propriedade intelectual'],
    },
    {
        'name': 'Lei de Propriedade Industrial (9.279/96)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9279.htm',
        'category': 'lei',
        'tags': ['propriedade industrial', 'patentes', 'marcas'],
    },

    # ============================================
    # DIREITO DESPORTIVO
    # ============================================
    {
        'name': 'Lei Geral do Esporte (14.597/23)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14597.htm',
        'category': 'lei',
        'tags': ['esporte', 'desportivo', 'atleta'],
    },

    # ============================================
    # DIREITO INTERNACIONAL PRIVADO
    # ============================================
    {
        'name': 'LINDB - Lei de Introducao (Decreto-Lei 4.657/42)',
        'url': 'https://www.planalto.gov.br/ccivil_03/decreto-lei/del4657compilado.htm',
        'category': 'lei',
        'tags': ['LINDB', 'introdução', 'direito internacional', 'conflito de leis'],
    },

    # ============================================
    # DIREITO SANITÁRIO / SAÚDE
    # ============================================
    {
        'name': 'Lei Organica da Saude - SUS (8.080/90)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l8080.htm',
        'category': 'lei',
        'tags': ['SUS', 'saúde', 'sanitário'],
    },

    # ============================================
    # LEIS PROCESSUAIS ESPECIAIS
    # ============================================
    {
        'name': 'Lei de Mediacao (13.140/15)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13140.htm',
        'category': 'lei',
        'tags': ['mediação', 'conciliação', 'ADR'],
    },
    {
        'name': 'Lei dos Juizados Especiais Federais (10.259/01)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10259.htm',
        'category': 'lei',
        'tags': ['JEF', 'juizado federal', 'previdenciário'],
    },
    {
        'name': 'Lei dos Juizados da Fazenda Publica (12.153/09)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2009/lei/l12153.htm',
        'category': 'lei',
        'tags': ['JEFaz', 'fazenda pública', 'administrativo'],
    },
    {
        'name': 'Lei de Acao Popular (4.717/65)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l4717.htm',
        'category': 'lei',
        'tags': ['ação popular', 'constitucional', 'administrativo'],
    },
    {
        'name': 'Lei da ADPF (9.882/99)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9882.htm',
        'category': 'lei',
        'tags': ['ADPF', 'constitucional'],
    },
    {
        'name': 'Lei da ADI/ADC (9.868/99)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9868.htm',
        'category': 'lei',
        'tags': ['ADI', 'ADC', 'constitucional', 'controle de constitucionalidade'],
    },
    {
        'name': 'Lei do Mandado de Injuncao (13.300/16)',
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2016/lei/l13300.htm',
        'category': 'lei',
        'tags': ['mandado de injunção', 'constitucional'],
    },
    {
        'name': 'Lei do Habeas Data (9.507/97)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l9507.htm',
        'category': 'lei',
        'tags': ['habeas data', 'constitucional', 'dados pessoais'],
    },

    # ============================================
    # TRIBUTÁRIO COMPLEMENTAR
    # ============================================
    {
        'name': 'Lei de Execucao Fiscal (6.830/80)',
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/l6830.htm',
        'category': 'lei',
        'tags': ['execução fiscal', 'tributário', 'fiscal'],
    },
]

# Chunk size maior para legislacao (textos longos e estruturados)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# Batch size para embeddings (evita timeout em textos muito grandes)
EMBEDDING_BATCH_SIZE = 50

# Diretorio com arquivos .txt pre-baixados (evita dependencia de rede em producao)
LOCAL_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )))),
    'data', 'legislacao',
)


def _slugify(name: str) -> str:
    """Converte nome da lei em slug seguro para nome de arquivo."""
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = nfkd.encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_str.lower()).strip('-')
    return re.sub(r'-+', '-', slug)


def _get_system_user():
    """
    Retorna o primeiro superuser para uso como uploaded_by em imports do sistema.

    Se nenhum usuario existir, cria um usuario-sistema automaticamente para
    permitir que o seed rode em deploy inicial (antes do primeiro login).
    """
    user = User.objects.filter(is_superuser=True, is_active=True).first()
    if user is None:
        user = User.objects.filter(is_active=True).first()
    if user is None:
        # Deploy inicial: cria usuario-sistema para seeds automaticos
        logger.warning(
            "Nenhum usuario encontrado. Criando usuario-sistema para seeds..."
        )
        user = User.objects.create_user(
            username='sistema_verus',
            email='sistema@verus.ai',
            password=None,  # login desabilitado (unusable password)
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )
        # Garante que a senha e inutilizavel (ninguem loga com este usuario)
        user.set_unusable_password()
        user.save(update_fields=['password'])
        logger.info("Usuario-sistema criado: sistema@verus.ai")
    return user


def _load_from_local(name: str) -> str | None:
    """Tenta carregar texto da legislacao a partir de arquivo local pre-baixado."""
    slug = _slugify(name)
    filepath = os.path.join(LOCAL_DATA_DIR, f"{slug}.txt")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        if text and len(text.strip()) >= 100:
            logger.info(f"Carregado do arquivo local: {filepath} ({len(text)} chars)")
            return text
    return None


def _download_and_extract(url: str, name: str = '', timeout: int = 60, retries: int = 3) -> str:
    """Carrega texto da legislacao: primeiro tenta arquivo local, depois download.

    Arquivos locais ficam em data/legislacao/{slug}.txt e sao preferidos
    para evitar dependencia de rede em ambientes de producao (containers/cloud).
    Se nao existir localmente, faz download do planalto.gov.br como fallback.
    """
    # 1. Tentar arquivo local primeiro
    if name:
        local_text = _load_from_local(name)
        if local_text is not None:
            return local_text

    # 2. Fallback: download da internet
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    }

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()

            # Planalto usa diferentes encodings; tentar detectar
            if response.encoding and response.encoding.lower() != 'utf-8':
                response.encoding = response.apparent_encoding or 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remover elementos irrelevantes
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript']):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)

            # Limpar linhas vazias consecutivas
            lines = [line for line in text.splitlines() if line.strip()]
            return '\n'.join(lines)

        except (requests.RequestException, ConnectionError) as e:
            last_error = e
            if attempt < retries:
                wait = 2 ** attempt  # 2s, 4s
                logger.warning(
                    f"Download falhou (tentativa {attempt}/{retries}): {url} - {e}. "
                    f"Aguardando {wait}s..."
                )
                time.sleep(wait)

    raise last_error  # type: ignore[misc]


class Command(BaseCommand):
    help = 'Importa legislacao brasileira oficial do planalto.gov.br na base de conhecimento (KB)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reimporta mesmo se o documento ja existir (deleta chunks anteriores)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria importado sem efetuar alteracoes',
        )
        parser.add_argument(
            '--no-embeddings',
            action='store_true',
            help='Cria chunks sem gerar embeddings (util para teste local sem API)',
        )
        parser.add_argument(
            '--only',
            type=str,
            default=None,
            help='Importa apenas legislacoes cujo nome contenha este texto (case-insensitive)',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        no_embeddings = options['no_embeddings']
        only_filter = options.get('only')

        if not dry_run:
            system_user = _get_system_user()
            self.stdout.write(f"  Usuario do sistema: {system_user.email}")

        legislacoes = LEGISLACOES
        if only_filter:
            legislacoes = [
                leg for leg in LEGISLACOES
                if only_filter.lower() in leg['name'].lower()
            ]
            if not legislacoes:
                self.stdout.write(self.style.WARNING(
                    f"  Nenhuma legislacao encontrada com filtro '{only_filter}'"
                ))
                return

        total = len(legislacoes)
        imported = 0
        skipped = 0
        errors = 0

        self.stdout.write(f"\n  Importando {total} legislacoes da base do Planalto...\n")

        for i, leg in enumerate(legislacoes, 1):
            prefix = f"  [{i}/{total}]"

            # Verificar se ja existe
            exists = Document.objects.filter(title=leg['name']).exists()
            if exists and not force:
                self.stdout.write(f"{prefix} Ja existe: {leg['name']}")
                skipped += 1
                continue

            if dry_run:
                action = "Reimportaria" if exists else "Importaria"
                self.stdout.write(f"{prefix} [dry-run] {action}: {leg['name']}")
                continue

            try:
                t0 = time.time()

                # 1. Download e extracao do texto
                self.stdout.write(f"{prefix} Baixando: {leg['name']}...")
                text = _download_and_extract(leg['url'], name=leg['name'])

                if not text or len(text.strip()) < 100:
                    raise ValueError(
                        f"Texto extraido muito curto ({len(text)} chars). "
                        "Possivel erro no download ou na estrutura HTML."
                    )

                # 2. Criar/atualizar Document
                doc, created = Document.objects.update_or_create(
                    title=leg['name'],
                    defaults={
                        'description': f"Texto integral: {leg['name']}",
                        'category': leg['category'],
                        'extracted_text': text,
                        'status': 'completed',
                        'tags': leg['tags'],
                        'uploaded_by': system_user,
                        'is_public': True,
                        'metadata': {
                            'source': 'planalto.gov.br',
                            'url': leg['url'],
                            'import_type': 'seed_legislacao',
                            'text_length': len(text),
                        },
                    },
                )

                # 3. Deletar chunks anteriores se reimportando
                if not created:
                    deleted_count = doc.chunks.all().delete()[0]
                    if deleted_count:
                        self.stdout.write(f"{prefix}   Removidos {deleted_count} chunks anteriores")

                # 4. Criar chunks usando o servico existente (chunk_size maior para legislacao)
                chunks_data = DocumentProcessingService.chunk_text(
                    text,
                    chunk_size=CHUNK_SIZE,
                    overlap=CHUNK_OVERLAP,
                )

                valid_chunks = [c for c in chunks_data if c['content'].strip()]

                if not valid_chunks:
                    raise ValueError("Nenhum chunk valido gerado a partir do texto.")

                # 5. Gerar embeddings (em batches para textos muito grandes)
                embeddings = None
                if not no_embeddings:
                    chunk_contents = [c['content'] for c in valid_chunks]
                    embeddings = []
                    for batch_start in range(0, len(chunk_contents), EMBEDDING_BATCH_SIZE):
                        batch = chunk_contents[batch_start:batch_start + EMBEDDING_BATCH_SIZE]
                        batch_embeddings = EmbeddingService.generate_batch(batch)
                        embeddings.extend(batch_embeddings)

                # 6. Criar DocumentChunks
                chunk_objects = []
                for idx, chunk_data in enumerate(valid_chunks):
                    chunk_obj = DocumentChunk(
                        document=doc,
                        content=chunk_data['content'],
                        chunk_index=chunk_data['chunk_index'],
                        metadata={
                            **chunk_data.get('metadata', {}),
                            'source': 'seed_legislacao',
                        },
                    )
                    if embeddings is not None:
                        chunk_obj.embedding = embeddings[idx]
                    chunk_objects.append(chunk_obj)

                DocumentChunk.objects.bulk_create(chunk_objects)

                elapsed = round(time.time() - t0, 1)
                emb_label = "com embeddings" if embeddings else "sem embeddings"
                self.stdout.write(self.style.SUCCESS(
                    f"{prefix} OK: {leg['name']} "
                    f"({len(valid_chunks)} chunks, {len(text)} chars, {emb_label}, {elapsed}s)"
                ))
                imported += 1

            except Exception as e:
                errors += 1
                logger.exception(f"Erro ao importar {leg['name']}")
                self.stdout.write(self.style.ERROR(
                    f"{prefix} ERRO: {leg['name']}: {e}"
                ))

        # Resumo final
        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.WARNING("  [dry-run] Nenhuma alteracao realizada."))
        else:
            self.stdout.write(
                f"  Resultado: {imported} importados, {skipped} ja existiam, {errors} erros"
            )
        self.stdout.write("")
