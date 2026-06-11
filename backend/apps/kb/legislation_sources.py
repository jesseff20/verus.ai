"""
Catálogo de fontes oficiais de legislação brasileira.

Organizado em 3 níveis: Federal, Estadual e Municipal.
Usado pelo LegislationSearchService para buscar legislação em fontes oficiais
quando a KB local não for suficiente.
"""

# ============================================
# NÍVEL 1: FONTES FEDERAIS
# ============================================
FONTES_FEDERAIS = {
    'planalto': {
        'name': 'Portal da Legislação - Planalto',
        'base_url': 'https://www.planalto.gov.br',
        'search_url': 'https://legislacao.presidencia.gov.br/',
        'description': 'Todas as leis, decretos, medidas provisórias federais',
        'scraping_strategy': 'html_text',
    },
    'normas_leg': {
        'name': 'Normas.leg.br - Câmara dos Deputados',
        'base_url': 'https://normas.leg.br',
        'search_url': 'https://normas.leg.br/busca',
        'description': 'Legislação federal com busca avançada',
        'scraping_strategy': 'html_text',
    },
    'stf': {
        'name': 'Supremo Tribunal Federal',
        'base_url': 'https://portal.stf.jus.br',
        'search_urls': {
            'sumulas_vinculantes': 'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=26',
            'sumulas': 'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=30',
            'repercussao_geral': 'https://portal.stf.jus.br/jurisprudencia/repercussaoGeral.asp',
            'jurisprudencia': 'https://jurisprudencia.stf.jus.br/pages/search',
        },
        'description': 'Súmulas vinculantes, jurisprudência, repercussão geral',
        'scraping_strategy': 'html_text',
    },
    'stj': {
        'name': 'Superior Tribunal de Justiça',
        'base_url': 'https://www.stj.jus.br',
        'search_urls': {
            'sumulas': 'https://www.stj.jus.br/sites/portalp/Jurisprudencia/Sumulas',
            'repetitivos': 'https://processo.stj.jus.br/repetitivos/temas_repetitivos/',
            'jurisprudencia': 'https://scon.stj.jus.br/SCON/',
        },
        'description': 'Súmulas, temas repetitivos, jurisprudência',
        'scraping_strategy': 'html_text',
    },
    'tst': {
        'name': 'Tribunal Superior do Trabalho',
        'base_url': 'https://www.tst.jus.br',
        'search_urls': {
            'sumulas': 'https://www.tst.jus.br/sumulas',
            'ojs_sdi1': 'https://www.tst.jus.br/ojs-702-sdi1-702-transitoria',
            'ojs_sdi2': 'https://www.tst.jus.br/ojs-sdi2',
            'instrucoes_normativas': 'https://www.tst.jus.br/web/guest/instrucoes-normativas',
        },
        'description': 'Súmulas, OJs, instruções normativas trabalhistas',
        'scraping_strategy': 'html_text',
    },
    'tse': {
        'name': 'Tribunal Superior Eleitoral',
        'base_url': 'https://www.tse.jus.br',
        'search_urls': {
            'legislacao': 'https://www.tse.jus.br/legislacao',
            'jurisprudencia': 'https://www.tse.jus.br/jurisprudencia/pesquisa-de-jurisprudencia',
        },
        'description': 'Legislação e jurisprudência eleitoral',
        'scraping_strategy': 'html_text',
    },
    'stm': {
        'name': 'Superior Tribunal Militar',
        'base_url': 'https://www.stm.jus.br',
        'search_urls': {
            'jurisprudencia': 'https://www.stm.jus.br/servicos-stm/jurisprudencia',
        },
        'description': 'Jurisprudência militar',
        'scraping_strategy': 'html_text',
    },
    'cnj': {
        'name': 'Conselho Nacional de Justiça',
        'base_url': 'https://atos.cnj.jus.br',
        'search_url': 'https://atos.cnj.jus.br/atos/',
        'description': 'Resoluções, recomendações, provimentos do CNJ',
        'scraping_strategy': 'html_text',
    },
    'anpd': {
        'name': 'Autoridade Nacional de Proteção de Dados',
        'base_url': 'https://www.gov.br/anpd',
        'search_url': 'https://www.gov.br/anpd/pt-br/documentos-e-publicacoes',
        'description': 'Regulamentações LGPD, guias orientativos',
        'scraping_strategy': 'html_text',
    },
}

# ============================================
# NÍVEL 2: FONTES ESTADUAIS (27 estados + DF)
# ============================================
# Diretório oficial: https://www4.planalto.gov.br/legislacao/portal-legis/legislacao-estadual/legislacoes-estaduais

FONTES_ESTADUAIS = {
    'AC': {'name': 'Acre', 'assembleia': 'https://www.al.ac.leg.br/', 'diario_oficial': 'https://www.diario.ac.gov.br/'},
    'AL': {'name': 'Alagoas', 'assembleia': 'https://www.al.al.leg.br/', 'diario_oficial': 'https://www.imprensaoficial.al.gov.br/'},
    'AP': {'name': 'Amapá', 'assembleia': 'https://www.al.ap.gov.br/', 'diario_oficial': 'https://www.diariooficial.ap.gov.br/'},
    'AM': {'name': 'Amazonas', 'assembleia': 'https://www.aleam.gov.br/', 'diario_oficial': 'https://diario.imprensaoficial.am.gov.br/'},
    'BA': {'name': 'Bahia', 'assembleia': 'https://www.al.ba.gov.br/', 'diario_oficial': 'https://dool.egba.ba.gov.br/'},
    'CE': {'name': 'Ceará', 'assembleia': 'https://www.al.ce.gov.br/', 'diario_oficial': 'https://www.doe.ce.gov.br/'},
    'DF': {'name': 'Distrito Federal', 'assembleia': 'https://www.cl.df.gov.br/', 'diario_oficial': 'https://www.sinj.df.gov.br/'},
    'ES': {'name': 'Espírito Santo', 'assembleia': 'https://www.al.es.gov.br/', 'diario_oficial': 'https://ioes.dio.es.gov.br/'},
    'GO': {'name': 'Goiás', 'assembleia': 'https://www.al.go.leg.br/', 'diario_oficial': 'https://diariooficial.abc.go.gov.br/'},
    'MA': {'name': 'Maranhão', 'assembleia': 'https://www.al.ma.leg.br/', 'diario_oficial': 'https://www.diariooficial.ma.gov.br/'},
    'MT': {'name': 'Mato Grosso', 'assembleia': 'https://www.al.mt.gov.br/', 'diario_oficial': 'https://www.iomat.mt.gov.br/'},
    'MS': {'name': 'Mato Grosso do Sul', 'assembleia': 'https://www.al.ms.gov.br/', 'diario_oficial': 'https://www.do.ms.gov.br/'},
    'MG': {'name': 'Minas Gerais', 'assembleia': 'https://www.almg.gov.br/', 'diario_oficial': 'https://www.jornalminasgerais.mg.gov.br/'},
    'PA': {'name': 'Pará', 'assembleia': 'https://www.alepa.pa.gov.br/', 'diario_oficial': 'https://www.ioepa.com.br/'},
    'PB': {'name': 'Paraíba', 'assembleia': 'https://www.al.pb.leg.br/', 'diario_oficial': 'https://auniao.pb.gov.br/doe/'},
    'PR': {'name': 'Paraná', 'assembleia': 'https://www.assembleia.pr.leg.br/', 'diario_oficial': 'https://www.legislacao.pr.gov.br/'},
    'PE': {'name': 'Pernambuco', 'assembleia': 'https://www.alepe.pe.gov.br/', 'diario_oficial': 'https://www.cepe.com.br/diariooficial/'},
    'PI': {'name': 'Piauí', 'assembleia': 'https://www.alepi.pi.gov.br/', 'diario_oficial': 'https://www.diariooficial.pi.gov.br/'},
    'RJ': {'name': 'Rio de Janeiro', 'assembleia': 'https://www.alerj.rj.gov.br/', 'diario_oficial': 'https://www.ioerj.com.br/'},
    'RN': {'name': 'Rio Grande do Norte', 'assembleia': 'https://www.al.rn.leg.br/', 'diario_oficial': 'https://www.diariooficial.rn.gov.br/'},
    'RS': {'name': 'Rio Grande do Sul', 'assembleia': 'https://www.al.rs.gov.br/', 'diario_oficial': 'https://www.diariooficial.rs.gov.br/'},
    'RO': {'name': 'Rondônia', 'assembleia': 'https://www.al.ro.leg.br/', 'diario_oficial': 'https://diof.ro.gov.br/'},
    'RR': {'name': 'Roraima', 'assembleia': 'https://www.al.rr.leg.br/', 'diario_oficial': 'https://www.imprensaoficial.rr.gov.br/'},
    'SC': {'name': 'Santa Catarina', 'assembleia': 'https://www.alesc.sc.gov.br/', 'diario_oficial': 'https://www.doe.sea.sc.gov.br/'},
    'SP': {'name': 'São Paulo', 'assembleia': 'https://www.al.sp.gov.br/', 'legislacao': 'https://www.legislacao.sp.gov.br/', 'diario_oficial': 'https://www.doe.sp.gov.br/'},
    'SE': {'name': 'Sergipe', 'assembleia': 'https://al.se.leg.br/', 'diario_oficial': 'https://www.se.gov.br/diario-oficial/'},
    'TO': {'name': 'Tocantins', 'assembleia': 'https://www.al.to.leg.br/', 'diario_oficial': 'https://diariooficial.to.gov.br/'},
}

# ============================================
# NÍVEL 3: FONTES MUNICIPAIS (capitais + agregadores)
# ============================================

FONTES_MUNICIPAIS_CAPITAIS = {
    'Belém': 'https://www.belem.pa.gov.br/',
    'Belo Horizonte': 'https://www.cmbh.mg.gov.br/',
    'Brasília': 'https://www.sinj.df.gov.br/',
    'Campo Grande': 'https://www.camara.ms.gov.br/',
    'Cuiabá': 'https://www.camaracuiaba.mt.gov.br/',
    'Curitiba': 'https://www.cmc.pr.gov.br/',
    'Florianópolis': 'https://www.cmf.sc.gov.br/',
    'Fortaleza': 'https://legislacao.pgm.fortaleza.ce.gov.br/',
    'Goiânia': 'https://www.goiania.go.leg.br/',
    'João Pessoa': 'https://www.cmjp.pb.gov.br/',
    'Macapá': 'https://www.cmm.ap.gov.br/',
    'Maceió': 'https://www.camarademaceio.al.gov.br/',
    'Manaus': 'https://www.cmm.am.gov.br/',
    'Natal': 'https://www.cmnat.rn.gov.br/',
    'Palmas': 'https://legislativo.palmas.to.gov.br/',
    'Porto Alegre': 'https://www.camarapoa.rs.gov.br/',
    'Porto Velho': 'https://www.portovelho.ro.leg.br/',
    'Recife': 'https://www.recife.pe.leg.br/',
    'Rio Branco': 'https://www.riobranco.ac.leg.br/',
    'Rio de Janeiro': 'https://www.camara.rio/',
    'Salvador': 'https://www.cms.ba.gov.br/',
    'São Luís': 'https://www.saoluis.ma.leg.br/',
    'São Paulo': 'https://www.saopaulo.sp.leg.br/',
    'Teresina': 'https://www.teresina.pi.leg.br/',
    'Vitória': 'https://www.cmv.es.gov.br/',
}

AGREGADORES_MUNICIPAIS = {
    'leis_municipais': {
        'name': 'Leis Municipais',
        'url': 'https://leismunicipais.com.br/',
        'description': '11+ milhões de leis municipais de todo o Brasil',
        'scraping_strategy': 'search_and_scrape',
    },
    'legislacao_municipal': {
        'name': 'Legislação Municipal',
        'url': 'https://www.legislacaomunicipal.com/',
        'description': 'Portal de legislação municipal',
        'scraping_strategy': 'search_and_scrape',
    },
}

# ============================================
# AGREGADORES MULTI-NÍVEL
# ============================================

AGREGADORES_GERAIS = {
    'jusbrasil': {
        'name': 'JusBrasil Legislação',
        'url': 'https://www.jusbrasil.com.br/legislacao/',
        'description': 'Legislação federal, estadual e municipal',
        'nota': 'Requer conta para acesso completo',
    },
    'leis_estaduais': {
        'name': 'Leis Estaduais',
        'url': 'https://leisestaduais.com.br/',
        'description': 'Agregador de legislação estadual',
    },
    'vade_mecum_online': {
        'name': 'Vade Mecum Online',
        'url': 'https://www.meuvademecumonline.com.br/',
        'description': 'Legislação compilada e organizada',
    },
}

# ============================================
# PRIORIDADE DE BUSCA (ordem de consulta)
# ============================================

SEARCH_PRIORITY = [
    # 1. KB Local (pgvector) — mais rápido e confiável
    'kb_local',
    # 2. Fontes federais (planalto, tribunais superiores)
    'planalto', 'stf', 'stj', 'tst', 'tse', 'cnj',
    # 3. Agregadores (cobertura ampla)
    'normas_leg', 'leis_estaduais', 'leis_municipais',
    # 4. Fontes estaduais (quando especificado o estado)
    'assembleia_estadual',
    # 5. Fontes municipais (quando especificado o município)
    'camara_municipal',
]
