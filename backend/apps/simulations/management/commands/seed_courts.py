"""
Seed: popula tribunais (27 TJs + 6 TRFs + Tribunais Superiores) com comarcas.
Idempotente -- usa get_or_create.  Flag --force atualiza registros existentes.

Total: ~750+ comarcas cobrindo cidades com mais de 50-100 mil habitantes
e polos regionais de cada estado brasileiro.
"""
from django.core.management.base import BaseCommand
from apps.simulations.models import Court


# ============================================================================
# TRIBUNAIS SUPERIORES
# ============================================================================
TRIBUNAIS_SUPERIORES = [
    {
        'name': 'Supremo Tribunal Federal',
        'court_type': 'STF',
        'state': 'DF',
        'comarcas': ['Brasilia'],
        'website': 'https://www.stf.jus.br',
    },
    {
        'name': 'Superior Tribunal de Justica',
        'court_type': 'STJ',
        'state': 'DF',
        'comarcas': ['Brasilia'],
        'website': 'https://www.stj.jus.br',
    },
    {
        'name': 'Tribunal Superior do Trabalho',
        'court_type': 'TST',
        'state': 'DF',
        'comarcas': ['Brasilia'],
        'website': 'https://www.tst.jus.br',
    },
]

# ============================================================================
# TRFs (Tribunais Regionais Federais) -- inclui TRF6 criado em 2022
# ============================================================================
TRFS = [
    {
        'name': 'TRF da 1a Regiao',
        'court_type': 'TRF',
        'state': 'DF',
        'states': ['AC', 'AM', 'AP', 'BA', 'DF', 'GO', 'MA', 'MT', 'PA', 'PI', 'RO', 'RR', 'TO'],
        'secoes': [
            'Brasilia', 'Salvador', 'Goiania', 'Sao Luis', 'Belem',
            'Manaus', 'Palmas', 'Cuiaba', 'Porto Velho', 'Rio Branco',
            'Macapa', 'Boa Vista', 'Teresina', 'Feira de Santana',
            'Vitoria da Conquista', 'Ilheus', 'Barreiras', 'Imperatriz',
            'Santarem', 'Maraba', 'Anapolis', 'Rio Verde', 'Sinop',
            'Rondonopolis', 'Ji-Parana', 'Araguaina',
        ],
        'website': 'https://www.trf1.jus.br',
    },
    {
        'name': 'TRF da 2a Regiao',
        'court_type': 'TRF',
        'state': 'RJ',
        'states': ['RJ', 'ES'],
        'secoes': [
            'Rio de Janeiro', 'Niteroi', 'Sao Goncalo', 'Duque de Caxias',
            'Nova Iguacu', 'Campos dos Goytacazes', 'Volta Redonda',
            'Petropolis', 'Macae', 'Vitoria', 'Vila Velha', 'Serra',
            'Cachoeiro de Itapemirim', 'Linhares', 'Cabo Frio',
        ],
        'website': 'https://www.trf2.jus.br',
    },
    {
        'name': 'TRF da 3a Regiao',
        'court_type': 'TRF',
        'state': 'SP',
        'states': ['SP', 'MS'],
        'secoes': [
            'Sao Paulo', 'Campinas', 'Santos', 'Ribeirao Preto',
            'Sao Jose dos Campos', 'Sorocaba', 'Jundiai', 'Bauru',
            'Piracicaba', 'Presidente Prudente', 'Marilia', 'Araraquara',
            'Sao Jose do Rio Preto', 'Franca', 'Taubate', 'Guarulhos',
            'Osasco', 'Santo Andre', 'Sao Bernardo do Campo',
            'Campo Grande', 'Dourados', 'Tres Lagoas',
        ],
        'website': 'https://www.trf3.jus.br',
    },
    {
        'name': 'TRF da 4a Regiao',
        'court_type': 'TRF',
        'state': 'RS',
        'states': ['PR', 'SC', 'RS'],
        'secoes': [
            'Porto Alegre', 'Curitiba', 'Florianopolis',
            'Caxias do Sul', 'Pelotas', 'Santa Maria', 'Passo Fundo',
            'Londrina', 'Maringa', 'Cascavel', 'Foz do Iguacu',
            'Ponta Grossa', 'Joinville', 'Blumenau', 'Chapeco',
            'Criciuma', 'Canoas', 'Novo Hamburgo',
        ],
        'website': 'https://www.trf4.jus.br',
    },
    {
        'name': 'TRF da 5a Regiao',
        'court_type': 'TRF',
        'state': 'PE',
        'states': ['AL', 'CE', 'PB', 'PE', 'RN', 'SE'],
        'secoes': [
            'Recife', 'Fortaleza', 'Natal', 'Joao Pessoa', 'Maceio',
            'Aracaju', 'Caruaru', 'Petrolina', 'Juazeiro do Norte',
            'Sobral', 'Campina Grande', 'Mossoro', 'Arapiraca',
            'Caucaia', 'Jaboatao dos Guararapes', 'Olinda',
        ],
        'website': 'https://www.trf5.jus.br',
    },
    {
        'name': 'TRF da 6a Regiao',
        'court_type': 'TRF',
        'state': 'MG',
        'states': ['MG'],
        'secoes': [
            'Belo Horizonte', 'Uberlandia', 'Juiz de Fora', 'Contagem',
            'Betim', 'Montes Claros', 'Uberaba', 'Governador Valadares',
            'Ipatinga', 'Sete Lagoas', 'Divinopolis', 'Pocos de Caldas',
            'Patos de Minas', 'Barbacena', 'Varginha', 'Teofilo Otoni',
            'Pouso Alegre',
        ],
        'website': 'https://www.trf6.jus.br',
    },
]

# ============================================================================
# TJs ESTADUAIS -- expandido com comarcas de cidades > 50-100k hab + polos
# ============================================================================
TJS = [
    # ── NORTE ───────────────────────────────────────────────────────────────
    ('TJAC', 'AC', [
        'Rio Branco', 'Cruzeiro do Sul', 'Sena Madureira', 'Tarauaca',
        'Feijo', 'Brasileia', 'Epitaciolandia', 'Placido de Castro',
        'Senador Guiomard', 'Xapuri', 'Mancio Lima', 'Rodrigues Alves',
        'Porto Walter', 'Jordao', 'Marechal Thaumaturgo', 'Assis Brasil',
        'Acrelândia', 'Bujari', 'Capixaba', 'Manuel Urbano',
        'Porto Acre', 'Santa Rosa do Purus',
    ], 'https://www.tjac.jus.br'),

    ('TJAM', 'AM', [
        'Manaus', 'Parintins', 'Itacoatiara', 'Manacapuru', 'Tefe',
        'Coari', 'Tabatinga', 'Maues', 'Manicore', 'Humaita',
        'Iranduba', 'Autazes', 'Eirunepe', 'Sao Gabriel da Cachoeira',
        'Benjamin Constant', 'Labrea', 'Boca do Acre', 'Borba',
        'Carauari', 'Fonte Boa', 'Jurua', 'Nova Olinda do Norte',
        'Novo Aripuana', 'Presidente Figueiredo', 'Rio Preto da Eva',
        'Santa Isabel do Rio Negro', 'Sao Paulo de Olivenca',
        'Urucara', 'Barcelos', 'Barreirinha',
    ], 'https://www.tjam.jus.br'),

    ('TJAP', 'AP', [
        'Macapa', 'Santana', 'Laranjal do Jari', 'Oiapoque',
        'Mazagao', 'Porto Grande', 'Tartarugalzinho', 'Pedra Branca do Amapari',
        'Vitoria do Jari', 'Calcoene', 'Amapa', 'Ferreira Gomes',
        'Pracuuba', 'Serra do Navio', 'Cutias', 'Itaubal',
    ], 'https://www.tjap.jus.br'),

    ('TJPA', 'PA', [
        'Belem', 'Ananindeua', 'Santarem', 'Maraba', 'Castanhal',
        'Parauapebas', 'Abaetetuba', 'Cameta', 'Braganca', 'Altamira',
        'Tucurui', 'Itaituba', 'Barcarena', 'Redenao', 'Breves',
        'Capanema', 'Salinopolis', 'Tome-Acu', 'Paragominas',
        'Obidos', 'Oriximina', 'Conceicao do Araguaia',
        'Sao Felix do Xingu', 'Xinguara', 'Jacunda', 'Tailandia',
        'Moju', 'Vigia', 'Igarape-Acu', 'Monte Alegre',
        'Soure', 'Viseu', 'Curuca', 'Benevides', 'Marituba',
        'Santa Izabel do Para', 'Sao Miguel do Guama',
        'Augusto Correa', 'Almeirim', 'Portel',
    ], 'https://www.tjpa.jus.br'),

    ('TJRO', 'RO', [
        'Porto Velho', 'Ji-Parana', 'Ariquemes', 'Vilhena', 'Cacoal',
        'Jaru', 'Rolim de Moura', 'Guajara-Mirim', 'Ouro Preto do Oeste',
        'Buritis', 'Pimenta Bueno', 'Espigao dOeste', 'Colorado do Oeste',
        'Machadinho dOeste', 'Nova Mamore', 'Cerejeiras', 'Alta Floresta dOeste',
        'Presidente Medici', 'Sao Francisco do Guapore', 'Costa Marques',
        'Candeias do Jamari', 'Alto Paraiso',
    ], 'https://www.tjro.jus.br'),

    ('TJRR', 'RR', [
        'Boa Vista', 'Rorainopolis', 'Pacaraima', 'Caracarai',
        'Alto Alegre', 'Canta', 'Bonfim', 'Normandia',
        'Sao Joao da Baliza', 'Caroebe', 'Sao Luiz',
        'Mucajai', 'Iracema', 'Amajari', 'Uiramuta',
    ], 'https://www.tjrr.jus.br'),

    ('TJTO', 'TO', [
        'Palmas', 'Araguaina', 'Gurupi', 'Porto Nacional',
        'Paraiso do Tocantins', 'Colinas do Tocantins', 'Guarai',
        'Dianopolis', 'Tocantinopolis', 'Miracema do Tocantins',
        'Pedro Afonso', 'Augustinopolis', 'Arraias', 'Natividade',
        'Taguatinga', 'Formoso do Araguaia', 'Goiatins',
        'Alvorada', 'Wanderlandia', 'Araguacu',
    ], 'https://www.tjto.jus.br'),

    # ── NORDESTE ────────────────────────────────────────────────────────────
    ('TJMA', 'MA', [
        'Sao Luis', 'Imperatriz', 'Caxias', 'Timon',
        'Sao Jose de Ribamar', 'Paco do Lumiar', 'Acailandia',
        'Bacabal', 'Codó', 'Santa Ines', 'Balsas', 'Chapadinha',
        'Barra do Corda', 'Pinheiro', 'Santa Luzia', 'Itapecuru Mirim',
        'Pedreiras', 'Grajau', 'Presidente Dutra', 'Coroata',
        'Viana', 'Lago da Pedra', 'Tutoia', 'Barreirinhas',
        'Carolina', 'Estreito', 'Porto Franco', 'Rosario',
        'Colinas', 'Ze Doca', 'Buriticupu', 'Dom Pedro',
    ], 'https://www.tjma.jus.br'),

    ('TJPI', 'PI', [
        'Teresina', 'Parnaiba', 'Picos', 'Floriano', 'Piripiri',
        'Campo Maior', 'Barras', 'Pedro II', 'Oeiras', 'Jose de Freitas',
        'Esperantina', 'Corrente', 'Bom Jesus', 'Sao Raimundo Nonato',
        'Uruçui', 'Altos', 'Agua Branca', 'Regeneracao',
        'Valenca do Piaui', 'Simplicio Mendes', 'Canto do Buriti',
        'Amarante', 'Uniao', 'Miguel Alves', 'Batalha',
        'Fronteiras', 'Jaicos', 'Paulistana', 'Sao Joao do Piaui',
        'Luzilândia', 'Guadalupe',
    ], 'https://www.tjpi.jus.br'),

    ('TJCE', 'CE', [
        'Fortaleza', 'Caucaia', 'Juazeiro do Norte', 'Maracanau',
        'Sobral', 'Crato', 'Itapipoca', 'Maranguape', 'Iguatu',
        'Quixada', 'Caninde', 'Pacatuba', 'Russas', 'Tiangua',
        'Aracati', 'Aquiraz', 'Pacajus', 'Ico', 'Limoeiro do Norte',
        'Cascavel', 'Crateus', 'Baturite', 'Camocim', 'Taua',
        'Horizonte', 'Quixeramobim', 'Beberibe', 'Brejo Santo',
        'Acarau', 'Morada Nova', 'Sao Benedito', 'Granja',
        'Lavras da Mangabeira', 'Guaraciaba do Norte', 'Viçosa do Ceará',
        'Uruburetama', 'Pentecoste', 'Senador Pompeu',
        'Eusebio', 'Sao Goncalo do Amarante',
    ], 'https://www.tjce.jus.br'),

    ('TJRN', 'RN', [
        'Natal', 'Mossoro', 'Parnamirim', 'Sao Goncalo do Amarante',
        'Caico', 'Ceara-Mirim', 'Macaiba', 'Acu', 'Currais Novos',
        'Pau dos Ferros', 'Nova Cruz', 'Santa Cruz', 'Apodi',
        'Joao Camara', 'Macau', 'Alexandria', 'Touros',
        'Sao Jose de Mipibu', 'Canguaretama', 'Lajes',
        'Jardim de Piranhas', 'Tangara', 'Jucurutu',
        'Sao Paulo do Potengi', 'Monte Alegre', 'Extremoz',
    ], 'https://www.tjrn.jus.br'),

    ('TJPB', 'PB', [
        'Joao Pessoa', 'Campina Grande', 'Santa Rita', 'Patos',
        'Bayeux', 'Sousa', 'Cajazeiras', 'Cabedelo', 'Guarabira',
        'Sapé', 'Mamanguape', 'Monteiro', 'Itabaiana', 'Pombal',
        'Esperanca', 'Picui', 'Itaporanga', 'Areia',
        'Queimadas', 'Rio Tinto', 'Princesa Isabel', 'Catole do Rocha',
        'Araruna', 'Bananeiras', 'Sume', 'Taperoa',
        'Congo', 'Piancó', 'Serra Branca', 'Solânea',
    ], 'https://www.tjpb.jus.br'),

    ('TJPE', 'PE', [
        'Recife', 'Jaboatao dos Guararapes', 'Olinda', 'Caruaru',
        'Petrolina', 'Paulista', 'Cabo de Santo Agostinho', 'Camaragibe',
        'Garanhuns', 'Vitoria de Santo Antao', 'Igarassu', 'Abreu e Lima',
        'Sao Lourenco da Mata', 'Serra Talhada', 'Arcoverde',
        'Santa Cruz do Capibaribe', 'Goiana', 'Carpina',
        'Gravatá', 'Bezerros', 'Surubim', 'Belo Jardim',
        'Limoeiro', 'Palmares', 'Timbauba', 'Pesqueira',
        'Salgueiro', 'Ouricuri', 'Afogados da Ingazeira',
        'Nazaré da Mata', 'Escada', 'Buique', 'Barreiros',
        'Floresta', 'Custodia', 'Taquaritinga do Norte',
    ], 'https://www.tjpe.jus.br'),

    ('TJAL', 'AL', [
        'Maceio', 'Arapiraca', 'Penedo', 'Uniao dos Palmares',
        'Rio Largo', 'Palmeira dos Indios', 'Delmiro Gouveia',
        'Coruripe', 'Sao Miguel dos Campos', 'Santana do Ipanema',
        'Murici', 'Atalaia', 'Marechal Deodoro', 'Porto Calvo',
        'Pilar', 'Sao Jose da Laje', 'Matriz de Camaragibe',
        'Viçosa', 'Porto Real do Colegio', 'Traipu',
        'Igreja Nova', 'Girau do Ponciano', 'Pao de Acucar',
        'Batalha', 'Major Isidoro', 'Anadia',
    ], 'https://www.tjal.jus.br'),

    ('TJSE', 'SE', [
        'Aracaju', 'Nossa Senhora do Socorro', 'Lagarto', 'Itabaiana',
        'Estancia', 'Sao Cristovao', 'Tobias Barreto', 'Simao Dias',
        'Capela', 'Propria', 'Itabaianinha', 'Boquim',
        'Neopolis', 'Laranjeiras', 'Maruim', 'Canindé de Sao Francisco',
        'Poco Redondo', 'Porto da Folha', 'Poco Verde',
        'Nossa Senhora da Gloria', 'Riachao do Dantas',
    ], 'https://www.tjse.jus.br'),

    ('TJBA', 'BA', [
        'Salvador', 'Feira de Santana', 'Vitoria da Conquista', 'Camacari',
        'Itabuna', 'Juazeiro', 'Lauro de Freitas', 'Ilhéus',
        'Jequie', 'Barreiras', 'Alagoinhas', 'Teixeira de Freitas',
        'Porto Seguro', 'Simoes Filho', 'Paulo Afonso', 'Eunapolis',
        'Santo Antonio de Jesus', 'Valenca', 'Candeias', 'Guanambi',
        'Jacobina', 'Serrinha', 'Itapetinga', 'Senhor do Bonfim',
        'Irecê', 'Cruz das Almas', 'Brumado', 'Itamaraju',
        'Santo Amaro', 'Conceicao do Coite', 'Itaberaba', 'Ipiau',
        'Bom Jesus da Lapa', 'Casa Nova', 'Ribeira do Pombal',
        'Euclides da Cunha', 'Catu', 'Dias dAvila',
        'Sao Francisco do Conde', 'Nazaré', 'Muritiba',
        'Gandu', 'Ubaitaba', 'Santa Maria da Vitoria',
        'Caetite', 'Livramento de Nossa Senhora', 'Mucuri',
        'Medeiros Neto', 'Luís Eduardo Magalhaes', 'Xique-Xique',
        'Ibotirama', 'Morro do Chapeu', 'Macaubas', 'Campo Formoso',
        'Amargosa', 'Cachoeira', 'Sao Felix', 'Pojuca',
        'Madre de Deus', 'Vera Cruz', 'Itaparica',
    ], 'https://www.tjba.jus.br'),

    # ── CENTRO-OESTE ────────────────────────────────────────────────────────
    ('TJDFT', 'DF', [
        'Brasilia', 'Taguatinga', 'Ceilandia', 'Samambaia', 'Gama',
        'Planaltina', 'Sobradinho', 'Brazlandia', 'Nucleo Bandeirante',
        'Paranoa', 'Santa Maria', 'Sao Sebastiao', 'Riacho Fundo',
        'Aguas Claras', 'Guara',
    ], 'https://www.tjdft.jus.br'),

    ('TJGO', 'GO', [
        'Goiania', 'Aparecida de Goiania', 'Anapolis', 'Rio Verde',
        'Luziania', 'Aguas Lindas de Goias', 'Valparaiso de Goias',
        'Trindade', 'Formosa', 'Novo Gama', 'Senador Canedo',
        'Itumbiara', 'Catalao', 'Jatai', 'Planaltina', 'Caldas Novas',
        'Goianesia', 'Mineiros', 'Inhumas', 'Porangatu',
        'Uruacu', 'Niquelandia', 'Ipora', 'Morrinhos',
        'Goianira', 'Jaragua', 'Ceres', 'Pirenopolis',
        'Cristalina', 'Pires do Rio', 'Santa Helena de Goias',
        'Quirinopolis', 'Itaberai', 'Cidade Ocidental',
        'Goias', 'Padre Bernardo', 'Posse', 'Campos Belos',
        'Sao Luis de Montes Belos',
    ], 'https://www.tjgo.jus.br'),

    ('TJMT', 'MT', [
        'Cuiaba', 'Varzea Grande', 'Rondonopolis', 'Sinop',
        'Tangara da Serra', 'Caceres', 'Sorriso', 'Lucas do Rio Verde',
        'Primavera do Leste', 'Alta Floresta', 'Barra do Garcas',
        'Pontes e Lacerda', 'Juina', 'Campo Novo do Parecis',
        'Nova Mutum', 'Colider', 'Guarantã do Norte', 'Juara',
        'Agua Boa', 'Poxoreo', 'Diamantino', 'Sapezal',
        'Confresa', 'Campo Verde', 'Chapada dos Guimaraes',
        'Mirassol dOeste', 'Aripuana', 'Canarana',
        'Sao Felix do Araguaia', 'Vila Rica', 'Paranatinga',
        'Dom Aquino', 'Jaciara', 'Rosario Oeste',
    ], 'https://www.tjmt.jus.br'),

    ('TJMS', 'MS', [
        'Campo Grande', 'Dourados', 'Tres Lagoas', 'Corumba',
        'Ponta Pora', 'Naviraí', 'Nova Andradina', 'Aquidauana',
        'Sidrolandia', 'Paranaiba', 'Maracaju', 'Cassilandia',
        'Coxim', 'Amambai', 'Jardim', 'Chapadao do Sul',
        'Rio Brilhante', 'Costa Rica', 'Mundo Novo', 'Ivinhema',
        'Bataguassu', 'Fatima do Sul', 'Bela Vista', 'Bonito',
        'Miranda', 'Sao Gabriel do Oeste', 'Aparecida do Taboado',
        'Anastacio', 'Itaporã',
    ], 'https://www.tjms.jus.br'),

    # ── SUDESTE ─────────────────────────────────────────────────────────────
    ('TJMG', 'MG', [
        'Belo Horizonte', 'Uberlandia', 'Contagem', 'Juiz de Fora',
        'Betim', 'Montes Claros', 'Uberaba', 'Governador Valadares',
        'Ipatinga', 'Sete Lagoas', 'Divinopolis', 'Pocos de Caldas',
        'Patos de Minas', 'Barbacena', 'Varginha', 'Teofilo Otoni',
        'Pouso Alegre', 'Lavras', 'Conselheiro Lafaiete',
        'Coronel Fabriciano', 'Itabira', 'Araguari', 'Passos',
        'Muriae', 'Uba', 'Itajuba', 'Sao Joao del-Rei',
        'Alfenas', 'Tres Coracoes', 'Caratinga', 'Curvelo',
        'Manhuacu', 'Timoteo', 'Paracatu', 'Unai',
        'Januaria', 'Janauba', 'Joao Monlevade', 'Pedro Leopoldo',
        'Araxá', 'Nova Lima', 'Sabara', 'Santa Luzia',
        'Ribeirao das Neves', 'Ibirite', 'Lagoa Santa',
        'Mariana', 'Ouro Preto', 'Itauna', 'Formiga',
        'Ituiutaba', 'Frutal', 'Visconde do Rio Branco',
        'Cataguases', 'Leopoldina', 'Além Paraiba', 'Santos Dumont',
        'Machado', 'Guaxupe', 'Sao Sebastiao do Paraiso',
        'Monte Carmelo', 'Patrocinio', 'Nanuque',
        'Carlos Chagas', 'Aimorés', 'Resplendor',
        'Mantena', 'Almenara', 'Aracuai', 'Diamantina',
        'Capelinha', 'Salinas', 'Bocaiuva', 'Pirapora',
        'Joao Pinheiro', 'Oliveira', 'Campo Belo',
        'Itapecerica', 'Bom Despacho', 'Nova Serrana',
        'Congonhas', 'Ouro Branco', 'Ponte Nova',
        'Vicosa', 'Manhumirim', 'Carangola',
        'Sao Lourenco', 'Caxambu', 'Andrelândia',
        'Três Pontas', 'Boa Esperanca', 'Campo Belo',
        'Campanha', 'Itajubá', 'Santa Rita do Sapucaí',
    ], 'https://www.tjmg.jus.br'),

    ('TJES', 'ES', [
        'Vitoria', 'Vila Velha', 'Serra', 'Cariacica',
        'Cachoeiro de Itapemirim', 'Linhares', 'Colatina',
        'Sao Mateus', 'Guarapari', 'Aracruz', 'Viana',
        'Nova Venecia', 'Barra de Sao Francisco', 'Domingos Martins',
        'Castelo', 'Alegre', 'Guacui', 'Itapemirim',
        'Marataizes', 'Montanha', 'Pinheiros', 'Ecoporanga',
        'Pedro Canario', 'Afonso Claudio', 'Santa Teresa',
        'Santa Maria de Jetiba', 'Muniz Freire', 'Iuna',
        'Ibatiba', 'Mantenopolis', 'Pancas',
        'Conceicao da Barra', 'Fundao', 'Anchieta',
        'Piuma', 'Iconha', 'Rio Novo do Sul',
    ], 'https://www.tjes.jus.br'),

    ('TJRJ', 'RJ', [
        'Rio de Janeiro', 'Sao Goncalo', 'Duque de Caxias', 'Nova Iguacu',
        'Niteroi', 'Campos dos Goytacazes', 'Belford Roxo', 'Sao Joao de Meriti',
        'Petropolis', 'Volta Redonda', 'Macae', 'Magé',
        'Itaborai', 'Mesquita', 'Nova Friburgo', 'Barra Mansa',
        'Cabo Frio', 'Angra dos Reis', 'Teresopolis', 'Resende',
        'Nilopolis', 'Queimados', 'Itaguai', 'Marica',
        'Japeri', 'Araruama', 'Rio das Ostras', 'Saquarema',
        'Tres Rios', 'Barra do Pirai', 'Valenca', 'Vassouras',
        'Itaperuna', 'Santo Antonio de Padua', 'Miracema',
        'Sao Fidelis', 'Laje do Muriae', 'Cantagalo',
        'Cachoeiras de Macacu', 'Paracambi', 'Mangaratiba',
        'Paraty', 'Cordeiro', 'Casimiro de Abreu', 'Silva Jardim',
        'Sao Pedro da Aldeia', 'Armacao dos Buzios', 'Iguaba Grande',
        'Rio Bonito', 'Tanguá', 'Seropedica',
        'Guapimirim', 'Paty do Alferes', 'Miguel Pereira',
        'Sapucaia', 'Pirai', 'Pinheiral', 'Porto Real',
        'Quatis', 'Rio Claro', 'Mendes', 'Engenheiro Paulo de Frontin',
        'Cambuci', 'Sao Jose de Uba', 'Varre-Sai',
        'Natividade', 'Porciuncula', 'Bom Jesus do Itabapoana',
        'Carapebus', 'Quissama', 'Conceicao de Macabu',
        'Santa Maria Madalena', 'Trajano de Moraes',
        'Sao Jose do Vale do Rio Preto', 'Sumidouro',
        'Duas Barras', 'Bom Jardim',
    ], 'https://www.tjrj.jus.br'),

    ('TJSP', 'SP', [
        # Capital e Grande Sao Paulo
        'Sao Paulo', 'Guarulhos', 'Campinas', 'Sao Bernardo do Campo',
        'Santo Andre', 'Osasco', 'Sao Jose dos Campos', 'Sorocaba',
        'Ribeirao Preto', 'Santos', 'Maua', 'Diadema',
        'Carapicuiba', 'Mogi das Cruzes', 'Suzano', 'Taboao da Serra',
        'Barueri', 'Cotia', 'Itaquaquecetuba', 'Embu das Artes',
        'Itapevi', 'Ferraz de Vasconcelos', 'Francisco Morato',
        'Franco da Rocha', 'Itapecerica da Serra', 'Caieiras',
        'Santana de Parnaiba', 'Poa', 'Aruja', 'Mairipora',
        'Cajamar', 'Vargem Grande Paulista', 'Jandira',
        # Litoral
        'Guaruja', 'Praia Grande', 'Sao Vicente', 'Cubatao',
        'Bertioga', 'Peruibe', 'Itanhaem', 'Mongagua',
        'Registro', 'Iguape', 'Cananeia',
        # Interior - Vale do Paraiba
        'Taubate', 'Jacarei', 'Pindamonhangaba', 'Lorena',
        'Cruzeiro', 'Guaratingueta', 'Caraguatatuba', 'Sao Sebastiao',
        'Ubatuba', 'Ilhabela', 'Cachoeira Paulista', 'Aparecida',
        # Interior - Campinas e regiao
        'Jundiai', 'Piracicaba', 'Limeira', 'Americana',
        'Santa Barbara dOeste', 'Sumaré', 'Hortolandia', 'Indaiatuba',
        'Valinhos', 'Vinhedo', 'Itatiba', 'Atibaia',
        'Braganca Paulista', 'Amparo', 'Serra Negra', 'Socorro',
        'Mogi Guacu', 'Mogi Mirim', 'Itapira', 'Artur Nogueira',
        'Cosmopolis', 'Paulinia',
        # Interior - Ribeirao Preto e regiao
        'Franca', 'Araraquara', 'Sao Carlos', 'Sertaozinho',
        'Barretos', 'Bebedouro', 'Jaboticabal', 'Monte Azul Paulista',
        'Olimpia', 'Viradouro', 'Batatais', 'Ituverava',
        'Patrocinio Paulista', 'Orlandia', 'Pontal', 'Cravinhos',
        # Interior - Sao Jose do Rio Preto e regiao
        'Sao Jose do Rio Preto', 'Catanduva', 'Votuporanga',
        'Fernandopolis', 'Jales', 'Mirassol', 'Jose Bonifacio',
        'Novo Horizonte', 'Santa Fe do Sul',
        # Interior - Bauru e regiao
        'Bauru', 'Marilia', 'Jau', 'Lins', 'Botucatu',
        'Avare', 'Ourinhos', 'Assis', 'Garça',
        'Tupa', 'Pederneiras', 'Agudos',
        # Interior - Presidente Prudente e regiao
        'Presidente Prudente', 'Presidente Epitacio', 'Presidente Venceslau',
        'Dracena', 'Adamantina', 'Osvaldo Cruz', 'Regente Feijo',
        # Interior - Araçatuba e regiao
        'Aracatuba', 'Birigui', 'Penapolis', 'Andradina',
        'Ilha Solteira', 'Pereira Barreto',
        # Interior - Itu / Sorocaba
        'Itu', 'Salto', 'Tatui', 'Itapetininga', 'Piedade',
        'Sao Roque', 'Mairinque', 'Votorantim', 'Aracoiaba da Serra',
        'Ipero', 'Porto Feliz', 'Cerquilho', 'Tietê',
        'Capivari', 'Rafard', 'Boituva',
        # Interior - Rio Claro e regiao
        'Rio Claro', 'Pirassununga', 'Leme', 'Araras',
        'Descalvado', 'Porto Ferreira', 'Santa Cruz das Palmeiras',
        # Interior - Outros polos
        'Itapeva', 'Capao Bonito', 'Sao Miguel Arcanjo',
        'Apiai', 'Buri', 'Itarare',
    ], 'https://www.tjsp.jus.br'),

    # ── SUL ─────────────────────────────────────────────────────────────────
    ('TJPR', 'PR', [
        'Curitiba', 'Londrina', 'Maringa', 'Ponta Grossa', 'Cascavel',
        'Foz do Iguacu', 'Sao Jose dos Pinhais', 'Colombo',
        'Guarapuava', 'Paranagua', 'Araucaria', 'Toledo',
        'Apucarana', 'Campo Largo', 'Arapongas', 'Almirante Tamandare',
        'Umuarama', 'Piraquara', 'Cambe', 'Campo Mourao',
        'Fazenda Rio Grande', 'Francisco Beltrao', 'Pato Branco',
        'Cianorte', 'Telêmaco Borba', 'Ivaipora', 'Irati',
        'Uniao da Vitoria', 'Prudentopolis', 'Cornelio Procopio',
        'Bandeirantes', 'Jacarezinho', 'Santo Antonio da Platina',
        'Wenceslau Braz', 'Ibipora', 'Rolandia', 'Jandaia do Sul',
        'Mandaguari', 'Astorga', 'Marialva', 'Sarandi',
        'Palotina', 'Medianeira', 'Santa Helena', 'Matelândia',
        'Dois Vizinhos', 'Capitao Leonidas Marques',
        'Laranjeiras do Sul', 'Pitanga', 'Goioere',
        'Loanda', 'Paranavaí', 'Nova Esperanca', 'Colorado',
        'Assai', 'Santa Mariana', 'Ibaiti',
        'Castro', 'Piraí do Sul', 'Jaguariaiva',
        'Lapa', 'Rio Negro', 'Sao Mateus do Sul',
        'Matinhos', 'Guaratuba', 'Morretes', 'Antonina',
    ], 'https://www.tjpr.jus.br'),

    ('TJSC', 'SC', [
        'Florianopolis', 'Joinville', 'Blumenau', 'Chapeco', 'Criciuma',
        'Itajai', 'Sao Jose', 'Jaragua do Sul', 'Lages',
        'Palhoca', 'Brusque', 'Tubarao', 'Balneario Camboriu',
        'Camboriu', 'Navegantes', 'Biguacu', 'Gaspar',
        'Indaial', 'Timbo', 'Concordia', 'Mafra',
        'Rio do Sul', 'Canoinhas', 'Sao Bento do Sul',
        'Ararangua', 'Xanxere', 'Cacador', 'Videira',
        'Joacaba', 'Curitibanos', 'Campos Novos', 'Itapema',
        'Imbituba', 'Laguna', 'Garopaba', 'Orleans',
        'Urussanga', 'Içara', 'Sombrio', 'Araranguá',
        'Sao Lourenco do Oeste', 'Maravilha', 'Pinhalzinho',
        'Dionisio Cerqueira', 'Itapiranga', 'Sao Miguel do Oeste',
        'Ibirama', 'Presidente Getulio', 'Taio',
        'Ituporanga', 'Alfredo Wagner', 'Bom Retiro',
        'Sao Joaquim', 'Otacilio Costa', 'Correia Pinto',
        'Porto Uniao', 'Tres Barras', 'Major Vieira',
        'Penha', 'Picarras', 'Bombinhas', 'Tijucas',
        'Santo Amaro da Imperatriz', 'Rancho Queimado',
    ], 'https://www.tjsc.jus.br'),

    ('TJRS', 'RS', [
        'Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas',
        'Santa Maria', 'Novo Hamburgo', 'Gravatai', 'Viamao',
        'Sao Leopoldo', 'Rio Grande', 'Alvorada', 'Passo Fundo',
        'Sapucaia do Sul', 'Cachoeirinha', 'Uruguaiana', 'Bage',
        'Santa Cruz do Sul', 'Bento Goncalves', 'Erechim',
        'Guaiba', 'Lajeado', 'Ijui', 'Sapiranga',
        'Cruz Alta', 'Camaquã', 'Santo Ângelo', 'Alegrete',
        'Santana do Livramento', 'Sao Borja', 'Santiago',
        'Esteio', 'Carazinho', 'Vacaria', 'Farroupilha',
        'Campo Bom', 'Venâncio Aires', 'Montenegro', 'Estancia Velha',
        'Frederico Westphalen', 'Palmeira das Missoes', 'Tres Passos',
        'Santo Augusto', 'Santa Rosa', 'Horizontina', 'Tucunduva',
        'Sao Luiz Gonzaga', 'Itaqui', 'Rosário do Sul',
        'Dom Pedrito', 'Jaguarao', 'Arroio Grande',
        'Camaquã', 'Tapes', 'Sao Lourenco do Sul',
        'Osorio', 'Tramandai', 'Torres', 'Capao da Canoa',
        'Taquara', 'Igrejinha', 'Tres Coroas', 'Gramado',
        'Canela', 'Flores da Cunha', 'Carlos Barbosa',
        'Garibaldi', 'Veranopolis', 'Nova Prata',
        'Marau', 'Lagoa Vermelha', 'Soledade',
        'Encantado', 'Estrela', 'Arroio do Meio',
        'Cachoeira do Sul', 'Sao Sebastiao do Cai',
        'Charqueadas', 'Sao Jeronimo', 'Butiá',
        'Encruzilhada do Sul', 'Rio Pardo', 'Sobradinho',
    ], 'https://www.tjrs.jus.br'),
]


class Command(BaseCommand):
    help = 'Popula tribunais (27 TJs + 6 TRFs + Superiores) com ~750+ comarcas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Atualiza comarcas de tribunais existentes (sobrescreve)',
        )

    def handle(self, *args, **options):
        force = options['force']
        created_count = 0
        updated_count = 0
        total_comarcas = 0

        # Tribunais Superiores
        for data in TRIBUNAIS_SUPERIORES:
            obj, created = Court.objects.get_or_create(
                name=data['name'],
                court_type=data['court_type'],
                defaults={
                    'state': data['state'],
                    'comarcas': data['comarcas'],
                    'website': data['website'],
                },
            )
            if created:
                created_count += 1
            elif force:
                obj.comarcas = data['comarcas']
                obj.website = data['website']
                obj.save()
                updated_count += 1
            total_comarcas += len(data['comarcas'])

        # TRFs
        for data in TRFS:
            obj, created = Court.objects.get_or_create(
                name=data['name'],
                court_type=data['court_type'],
                defaults={
                    'state': data['state'],
                    'comarcas': data['secoes'],
                    'website': data['website'],
                },
            )
            if created:
                created_count += 1
            elif force:
                obj.comarcas = data['secoes']
                obj.website = data['website']
                obj.save()
                updated_count += 1
            total_comarcas += len(data['secoes'])

        # TJs estaduais
        for name, state, comarcas, website in TJS:
            obj, created = Court.objects.get_or_create(
                name=name,
                court_type='TJ',
                defaults={
                    'state': state,
                    'comarcas': comarcas,
                    'website': website,
                },
            )
            if created:
                created_count += 1
            elif force:
                obj.comarcas = comarcas
                obj.website = website
                obj.save()
                updated_count += 1
            total_comarcas += len(comarcas)

        self.stdout.write(self.style.SUCCESS(
            f'seed_courts: {created_count} criados, {updated_count} atualizados '
            f'({total_comarcas} comarcas no total) '
            f'-- total tribunais: {Court.objects.count()}'
        ))
