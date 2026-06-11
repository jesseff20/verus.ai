"""
Management command para criar tipos de documento jurídico.

Cria DocumentCategory e DocumentType para cada tipo de documento do Verus.AI.
O frontend consulta esses tipos para exibir no wizard do Assistente Inteligente.

Taxonomia: 15 categorias unificadas, compatível com seed_juridico_completo.py
e seed_juridico_avancado.py.

Usage:
    python manage.py seed_document_types
    python manage.py seed_document_types --force  # Atualiza mesmo se existir
"""
from django.core.management.base import BaseCommand


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIAS (15 — taxonomia unificada)
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIAS = [
    {'code': 'acoes_peticoes',    'name': 'Ações e Petições',      'display_order': 1},
    {'code': 'defesas_respostas', 'name': 'Defesas e Respostas',   'display_order': 2},
    {'code': 'recursos',          'name': 'Recursos',              'display_order': 3},
    {'code': 'execucao',          'name': 'Execução',              'display_order': 4},
    {'code': 'cautelares_tutelas','name': 'Cautelares e Tutelas',  'display_order': 5},
    {'code': 'trabalhista',       'name': 'Trabalhista',           'display_order': 6},
    {'code': 'criminal',          'name': 'Criminal',              'display_order': 7},
    {'code': 'extrajudicial',     'name': 'Extrajudicial',         'display_order': 8},
    {'code': 'familia_sucessoes', 'name': 'Família e Sucessões',   'display_order': 9},
    {'code': 'previdenciario',    'name': 'Previdenciário',        'display_order': 10},
    {'code': 'consumidor',        'name': 'Consumidor',            'display_order': 11},
    {'code': 'tributario',        'name': 'Tributário',            'display_order': 12},
    {'code': 'administrativo',    'name': 'Administrativo',        'display_order': 13},
    {'code': 'digital_lgpd',      'name': 'Digital e LGPD',        'display_order': 14},
    {'code': 'empresarial',       'name': 'Empresarial',           'display_order': 15},
]

# Categorias legadas (4 antigas) a remover antes de criar as novas
CATEGORIAS_LEGADAS = ['peticoes', 'contratos', 'pareceres', 'acoes_constitucionais']

# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE DOCUMENTO
# ─────────────────────────────────────────────────────────────────────────────

DOCUMENT_TYPES_DATA = [

    # === AÇÕES E PETIÇÕES ===
    {'code': 'peticao_inicial',    'name': 'Petição Inicial',                    'short_name': 'PI',
     'description': 'Peça inaugural da ação judicial, com exposição dos fatos, fundamentos e pedidos.',
     'category': 'acoes_peticoes', 'icon': 'FileText',    'color': 'blue',
     'legal_basis': 'CPC, Art. 319', 'display_order': 1,  'is_active': True},

    {'code': 'mandado_seguranca',  'name': 'Mandado de Segurança',               'short_name': 'MS',
     'description': 'Remédio constitucional para proteção de direito líquido e certo contra ato ilegal de autoridade.',
     'category': 'acoes_peticoes', 'icon': 'ShieldCheck', 'color': 'violet',
     'legal_basis': 'CF/88, Art. 5º, LXIX; Lei 12.016/2009', 'display_order': 2, 'is_active': True},

    {'code': 'habeas_corpus',      'name': 'Habeas Corpus',                      'short_name': 'HC',
     'description': 'Remédio constitucional para proteção da liberdade de locomoção.',
     'category': 'acoes_peticoes', 'icon': 'Shield',      'color': 'red',
     'legal_basis': 'CF/88, Art. 5º, LXVIII; CPP, Art. 647', 'display_order': 3, 'is_active': True},

    {'code': 'acao_execucao',      'name': 'Ação de Execução de Título Extrajudicial', 'short_name': 'Exec.',
     'description': 'Ação para satisfação de obrigação constante em título extrajudicial.',
     'category': 'acoes_peticoes', 'icon': 'Gavel',       'color': 'orange',
     'legal_basis': 'CPC, Art. 783', 'display_order': 4,  'is_active': True},

    {'code': 'acao_popular',       'name': 'Ação Popular',                       'short_name': 'AP',
     'description': 'Instrumento constitucional de controle judicial de atos lesivos ao patrimônio público.',
     'category': 'acoes_peticoes', 'icon': 'Users',       'color': 'indigo',
     'legal_basis': 'CF/88, Art. 5º, LXXIII; Lei 4.717/1965', 'display_order': 5, 'is_active': True},

    {'code': 'acao_civil_publica', 'name': 'Ação Civil Pública',                 'short_name': 'ACP',
     'description': 'Instrumento para tutela de interesses difusos, coletivos e individuais homogêneos.',
     'category': 'acoes_peticoes', 'icon': 'Globe',       'color': 'green',
     'legal_basis': 'Lei 7.347/1985', 'display_order': 6, 'is_active': True},

    {'code': 'acao_rescisoria',    'name': 'Ação Rescisória',                    'short_name': 'AR',
     'description': 'Ação para desconstituir sentença de mérito transitada em julgado.',
     'category': 'acoes_peticoes', 'icon': 'RotateCcw',   'color': 'rose',
     'legal_basis': 'CPC, Art. 966', 'display_order': 7,  'is_active': True},

    # === DEFESAS E RESPOSTAS ===
    {'code': 'contestacao',               'name': 'Contestação',                        'short_name': 'Contest.',
     'description': 'Resposta do réu à petição inicial com impugnação dos fatos e fundamentos.',
     'category': 'defesas_respostas', 'icon': 'Scale',        'color': 'amber',
     'legal_basis': 'CPC, Art. 335', 'display_order': 1, 'is_active': True},

    {'code': 'contrarrazoes_apelacao',    'name': 'Contrarrazões de Apelação',          'short_name': 'Contrarr.',
     'description': 'Resposta do apelado às razões apresentadas no recurso de apelação.',
     'category': 'defesas_respostas', 'icon': 'MessageSquare','color': 'teal',
     'legal_basis': 'CPC, Art. 1.010, §1º', 'display_order': 2, 'is_active': True},

    {'code': 'impugnacao_cumprimento',    'name': 'Impugnação ao Cumprimento de Sentença', 'short_name': 'Imp.CS',
     'description': 'Impugnação do executado ao cumprimento de sentença.',
     'category': 'defesas_respostas', 'icon': 'AlertCircle', 'color': 'red',
     'legal_basis': 'CPC, Art. 525', 'display_order': 3, 'is_active': True},

    {'code': 'excecao_pre_executividade', 'name': 'Exceção de Pré-Executividade',        'short_name': 'EPE',
     'description': 'Defesa do executado em execução, sem necessidade de garantia do juízo.',
     'category': 'defesas_respostas', 'icon': 'ShieldAlert', 'color': 'yellow',
     'legal_basis': 'Jurisprudência consolidada (STJ)', 'display_order': 4, 'is_active': True},

    {'code': 'reconvencao',               'name': 'Reconvenção',                         'short_name': 'Reconv.',
     'description': 'Ação do réu contra o autor apresentada na mesma demanda.',
     'category': 'defesas_respostas', 'icon': 'ArrowLeftRight','color': 'purple',
     'legal_basis': 'CPC, Art. 343', 'display_order': 5, 'is_active': True},

    {'code': 'impugnacao_tutela',         'name': 'Impugnação à Tutela',                 'short_name': 'Imp.Tut.',
     'description': 'Impugnação ou pedido de reconsideração de decisão que concedeu tutela de urgência.',
     'category': 'defesas_respostas', 'icon': 'XCircle',     'color': 'slate',
     'legal_basis': 'CPC, Art. 300', 'display_order': 6, 'is_active': True},

    # === RECURSOS ===
    {'code': 'apelacao',                'name': 'Apelação',                          'short_name': 'Apel.',
     'description': 'Recurso contra sentença definitiva ou terminativa proferida em 1ª instância.',
     'category': 'recursos', 'icon': 'ArrowUpCircle', 'color': 'blue',
     'legal_basis': 'CPC, Art. 1.009', 'display_order': 1, 'is_active': True},

    {'code': 'agravo_instrumento',      'name': 'Agravo de Instrumento',             'short_name': 'AI',
     'description': 'Recurso contra decisões interlocutórias nas hipóteses do art. 1.015 do CPC.',
     'category': 'recursos', 'icon': 'TrendingUp',   'color': 'orange',
     'legal_basis': 'CPC, Art. 1.015', 'display_order': 2, 'is_active': True},

    {'code': 'agravo_interno',          'name': 'Agravo Interno',                    'short_name': 'Ag.Int.',
     'description': 'Recurso contra decisão monocrática de relator para o órgão colegiado.',
     'category': 'recursos', 'icon': 'ChevronUp',    'color': 'amber',
     'legal_basis': 'CPC, Art. 1.021', 'display_order': 3, 'is_active': True},

    {'code': 'embargos_declaracao',     'name': 'Embargos de Declaração',            'short_name': 'ED',
     'description': 'Pedido de esclarecimento de decisão com omissão, contradição ou obscuridade.',
     'category': 'recursos', 'icon': 'MessageSquare','color': 'slate',
     'legal_basis': 'CPC, Art. 1.022', 'display_order': 4, 'is_active': True},

    {'code': 'recurso_especial',        'name': 'Recurso Especial',                  'short_name': 'REsp',
     'description': 'Recurso ao STJ contra acórdão que viola lei federal.',
     'category': 'recursos', 'icon': 'Star',         'color': 'indigo',
     'legal_basis': 'CF/88, Art. 105, III; CPC, Art. 1.029', 'display_order': 5, 'is_active': True},

    {'code': 'recurso_extraordinario',  'name': 'Recurso Extraordinário',            'short_name': 'RE',
     'description': 'Recurso ao STF contra acórdão que viola a Constituição Federal.',
     'category': 'recursos', 'icon': 'Landmark',     'color': 'violet',
     'legal_basis': 'CF/88, Art. 102, III; CPC, Art. 1.029', 'display_order': 6, 'is_active': True},

    {'code': 'agravo_regimental',       'name': 'Agravo Regimental',                 'short_name': 'AgRg',
     'description': 'Recurso interno contra decisão monocrática em tribunais superiores.',
     'category': 'recursos', 'icon': 'CornerUpRight','color': 'teal',
     'legal_basis': 'RISTF, Art. 317; RISTJ, Art. 258', 'display_order': 7, 'is_active': True},

    # === EXECUÇÃO ===
    {'code': 'embargos_execucao',      'name': 'Embargos à Execução',               'short_name': 'Emb.Exec.',
     'description': 'Ação incidental do executado para desconstituir ou modificar a execução.',
     'category': 'execucao', 'icon': 'Hammer',       'color': 'red',
     'legal_basis': 'CPC, Art. 914', 'display_order': 1, 'is_active': True},

    {'code': 'cumprimento_sentenca',   'name': 'Cumprimento de Sentença',            'short_name': 'CS',
     'description': 'Fase executiva para satisfação de obrigação reconhecida em sentença.',
     'category': 'execucao', 'icon': 'CheckSquare',  'color': 'green',
     'legal_basis': 'CPC, Art. 513', 'display_order': 2, 'is_active': True},

    {'code': 'penhora_online',         'name': 'Penhora Online (BACEN JUD)',          'short_name': 'Penhor.',
     'description': 'Requerimento de penhora eletrônica de ativos financeiros via SISBAJUD.',
     'category': 'execucao', 'icon': 'CreditCard',   'color': 'amber',
     'legal_basis': 'CPC, Art. 835, I; Res. CNJ 547/2024', 'display_order': 3, 'is_active': True},

    {'code': 'impugnacao_execucao',    'name': 'Impugnação à Execução Fiscal',       'short_name': 'Imp.EF',
     'description': 'Defesa do executado em execução fiscal.',
     'category': 'execucao', 'icon': 'AlertOctagon', 'color': 'orange',
     'legal_basis': 'Lei 6.830/1980, Art. 16', 'display_order': 4, 'is_active': True},

    # === CAUTELARES E TUTELAS ===
    {'code': 'tutela_urgencia',    'name': 'Tutela de Urgência',              'short_name': 'Tut.Urg.',
     'description': 'Pedido de tutela antecipada ou cautelar para situações de urgência ou perigo.',
     'category': 'cautelares_tutelas', 'icon': 'Zap',        'color': 'yellow',
     'legal_basis': 'CPC, Art. 300-310', 'display_order': 1, 'is_active': True},

    {'code': 'tutela_antecipada',  'name': 'Tutela Antecipada de Evidência',   'short_name': 'Tut.Ant.',
     'description': 'Tutela fundada na evidência do direito, independente de urgência.',
     'category': 'cautelares_tutelas', 'icon': 'FastForward','color': 'lime',
     'legal_basis': 'CPC, Art. 311', 'display_order': 2, 'is_active': True},

    {'code': 'tutela_cautelar',    'name': 'Tutela Cautelar',                  'short_name': 'Tut.Caut.',
     'description': 'Medida para assegurar a utilidade do processo principal.',
     'category': 'cautelares_tutelas', 'icon': 'Lock',       'color': 'teal',
     'legal_basis': 'CPC, Art. 305', 'display_order': 3, 'is_active': True},

    {'code': 'arresto_sequestro',  'name': 'Arresto e Sequestro',              'short_name': 'Arr./Seq.',
     'description': 'Medidas constritivas de bens para garantir futura execução.',
     'category': 'cautelares_tutelas', 'icon': 'Archive',    'color': 'slate',
     'legal_basis': 'CPC, Art. 830', 'display_order': 4, 'is_active': True},

    # === TRABALHISTA ===
    {'code': 'reclamacao_trabalhista',          'name': 'Reclamação Trabalhista',                 'short_name': 'RT',
     'description': 'Peça inicial de ação trabalhista perante a Justiça do Trabalho.',
     'category': 'trabalhista', 'icon': 'Briefcase',    'color': 'blue',
     'legal_basis': 'CLT, Art. 840; Lei 13.467/2017; IN TST 41/2018', 'display_order': 1, 'is_active': True},

    {'code': 'contestacao_trabalhista',         'name': 'Contestação Trabalhista',               'short_name': 'Contest.TRT',
     'description': 'Defesa do reclamado na ação trabalhista.',
     'category': 'trabalhista', 'icon': 'Scale',        'color': 'amber',
     'legal_basis': 'CLT, Art. 847; CPC/2015, Art. 341 (subsidiário)', 'display_order': 2, 'is_active': True},

    {'code': 'agravo_peticao',                  'name': 'Agravo de Petição',                     'short_name': 'AgPet.',
     'description': 'Recurso trabalhista contra decisão em execução na Justiça do Trabalho.',
     'category': 'trabalhista', 'icon': 'TrendingUp',   'color': 'orange',
     'legal_basis': 'CLT, Art. 897, alínea a', 'display_order': 3, 'is_active': True},

    {'code': 'recurso_ordinario_trt',           'name': 'Recurso Ordinário (TRT)',               'short_name': 'RO',
     'description': 'Recurso da sentença trabalhista para o Tribunal Regional do Trabalho.',
     'category': 'trabalhista', 'icon': 'ArrowUpCircle','color': 'indigo',
     'legal_basis': 'CLT, Art. 895', 'display_order': 4, 'is_active': True},

    {'code': 'recurso_revista_tst',             'name': 'Recurso de Revista (TST)',              'short_name': 'RR',
     'description': 'Recurso ao TST contra acórdão de TRT com violação de norma federal.',
     'category': 'trabalhista', 'icon': 'Star',         'color': 'violet',
     'legal_basis': 'CLT, Art. 896', 'display_order': 5, 'is_active': True},

    {'code': 'acao_consignacao_trabalhista',     'name': 'Ação de Consignação em Pagamento (TRT)', 'short_name': 'ConsigPag.',
     'description': 'Ação para depositar valores devidos ao trabalhador com extinção da obrigação.',
     'category': 'trabalhista', 'icon': 'DollarSign',   'color': 'green',
     'legal_basis': 'CPC, Art. 539; CC, Art. 334; CLT, Art. 477, §8º', 'display_order': 6, 'is_active': True},

    # === CRIMINAL ===
    {'code': 'queixa_crime',                'name': 'Queixa-Crime',                        'short_name': 'Queixa',
     'description': 'Peça inaugural da ação penal privada.',
     'category': 'criminal', 'icon': 'AlertTriangle','color': 'red',
     'legal_basis': 'CPP, Art. 30', 'display_order': 1, 'is_active': True},

    {'code': 'alegacoes_finais_criminais',   'name': 'Alegações Finais Criminais',          'short_name': 'AlegFin.',
     'description': 'Manifestação conclusiva das partes ao final da instrução criminal.',
     'category': 'criminal', 'icon': 'BookOpen',     'color': 'slate',
     'legal_basis': 'CPP, Art. 403', 'display_order': 2, 'is_active': True},

    {'code': 'defesa_preliminar_criminal',  'name': 'Defesa Preliminar Criminal',          'short_name': 'DefPreCrim.',
     'description': 'Defesa apresentada antes do recebimento da denúncia ou queixa.',
     'category': 'criminal', 'icon': 'Shield',       'color': 'indigo',
     'legal_basis': 'CPP, Art. 396-A', 'display_order': 3, 'is_active': True},

    {'code': 'recurso_criminal',            'name': 'Recurso Criminal',                    'short_name': 'RecCrim.',
     'description': 'Recurso contra decisão proferida em processo penal.',
     'category': 'criminal', 'icon': 'CornerUpRight','color': 'orange',
     'legal_basis': 'CPP, Art. 574', 'display_order': 4, 'is_active': True},

    {'code': 'habeas_corpus_criminal',      'name': 'Habeas Corpus (Criminal)',            'short_name': 'HC Crim.',
     'description': 'Habeas corpus para liberação de preso ou prevenção de ameaça à liberdade.',
     'category': 'criminal', 'icon': 'Unlock',       'color': 'amber',
     'legal_basis': 'CF/88, Art. 5º, LXVIII; CPP, Art. 647', 'display_order': 5, 'is_active': True},

    {'code': 'resposta_acusacao',           'name': 'Resposta à Acusação',                 'short_name': 'RespAcus.',
     'description': 'Peça de defesa apresentada após o recebimento da denúncia ou queixa.',
     'category': 'criminal', 'icon': 'MessageCircle','color': 'teal',
     'legal_basis': 'CPP, Art. 396-A', 'display_order': 6, 'is_active': True},

    # === EXTRAJUDICIAL ===
    {'code': 'notificacao_extrajudicial',       'name': 'Notificação Extrajudicial',            'short_name': 'Notif.',
     'description': 'Comunicação formal extrajudicial para constituição em mora ou aviso de direitos.',
     'category': 'extrajudicial', 'icon': 'Mail',          'color': 'slate',
     'legal_basis': 'CC, Art. 397', 'display_order': 1, 'is_active': True},

    {'code': 'parecer_juridico',                'name': 'Parecer Jurídico',                     'short_name': 'PAR',
     'description': 'Opinião técnica fundamentada sobre questão jurídica.',
     'category': 'extrajudicial', 'icon': 'Lightbulb',    'color': 'yellow',
     'legal_basis': '', 'display_order': 2, 'is_active': True},

    {'code': 'contrato_particular',             'name': 'Contrato Particular',                  'short_name': 'CTR',
     'description': 'Instrumento contratual firmado entre as partes sem intervenção notarial.',
     'category': 'extrajudicial', 'icon': 'FileSignature','color': 'green',
     'legal_basis': 'CC, Art. 421', 'display_order': 3, 'is_active': True},

    {'code': 'procuracao',                      'name': 'Procuração',                           'short_name': 'Proc.',
     'description': 'Instrumento de mandato outorgando poderes ao advogado ou representante.',
     'category': 'extrajudicial', 'icon': 'UserCheck',    'color': 'teal',
     'legal_basis': 'CC, Art. 653', 'display_order': 4, 'is_active': True},

    {'code': 'contrato_trabalho',               'name': 'Contrato de Trabalho',                 'short_name': 'CTrab.',
     'description': 'Instrumento contratual de vínculo empregatício entre empregador e empregado.',
     'category': 'extrajudicial', 'icon': 'Briefcase',    'color': 'blue',
     'legal_basis': 'CLT, Art. 442', 'display_order': 5, 'is_active': True},

    {'code': 'substabelecimento',               'name': 'Substabelecimento',                    'short_name': 'Subst.',
     'description': 'Instrumento pelo qual o advogado transfere poderes a outro causídico.',
     'category': 'extrajudicial', 'icon': 'Share2',       'color': 'indigo',
     'legal_basis': 'CC, Art. 667; OAB, Art. 26', 'display_order': 6, 'is_active': True},

    # === FAMÍLIA E SUCESSÕES ===
    {'code': 'divorcio_consensual',               'name': 'Divórcio Consensual',                   'short_name': 'Div.Cons.',
     'description': 'Ação de dissolução do vínculo conjugal por mútuo consentimento.',
     'category': 'familia_sucessoes', 'icon': 'Heart',        'color': 'rose',
     'legal_basis': 'CC, Art. 1.574; CPC, Art. 731', 'display_order': 1, 'is_active': True},

    {'code': 'divorcio_litigioso',                'name': 'Divórcio Litigioso',                    'short_name': 'Div.Lit.',
     'description': 'Ação de dissolução do vínculo conjugal sem acordo entre os cônjuges.',
     'category': 'familia_sucessoes', 'icon': 'HeartCrack',   'color': 'red',
     'legal_basis': 'CC, Art. 1.572; CPC, Art. 693', 'display_order': 2, 'is_active': True},

    {'code': 'acao_alimentos',                    'name': 'Ação de Alimentos',                     'short_name': 'Alim.',
     'description': 'Ação para fixação ou revisão de alimentos (pensão alimentícia).',
     'category': 'familia_sucessoes', 'icon': 'Utensils',     'color': 'amber',
     'legal_basis': 'Lei 5.478/1968; CC, Art. 1.694', 'display_order': 3, 'is_active': True},

    {'code': 'regulamentacao_guarda',             'name': 'Regulamentação de Guarda',              'short_name': 'Guard.',
     'description': 'Ação para estabelecimento ou modificação da guarda de menor.',
     'category': 'familia_sucessoes', 'icon': 'Users',        'color': 'blue',
     'legal_basis': 'CC, Art. 1.583; ECA, Art. 33', 'display_order': 4, 'is_active': True},

    {'code': 'inventario_extrajudicial',          'name': 'Inventário Extrajudicial',              'short_name': 'Inv.Extra.',
     'description': 'Inventário realizado em cartório por escritura pública.',
     'category': 'familia_sucessoes', 'icon': 'FileArchive',  'color': 'teal',
     'legal_basis': 'CPC, Art. 610; Lei 11.441/2007', 'display_order': 5, 'is_active': True},

    {'code': 'inventario_judicial',               'name': 'Inventário Judicial',                   'short_name': 'Inv.Jud.',
     'description': 'Inventário processado perante a Vara de Família e Sucessões.',
     'category': 'familia_sucessoes', 'icon': 'BookMarked',   'color': 'indigo',
     'legal_basis': 'CPC, Art. 615', 'display_order': 6, 'is_active': True},

    {'code': 'acao_investigacao_paternidade',      'name': 'Ação de Investigação de Paternidade',  'short_name': 'Patern.',
     'description': 'Ação para reconhecimento judicial da filiação.',
     'category': 'familia_sucessoes', 'icon': 'Search',       'color': 'violet',
     'legal_basis': 'CC, Art. 1.606; Lei 8.560/1992', 'display_order': 7, 'is_active': True},

    {'code': 'execucao_alimentos',                'name': 'Execução de Alimentos',                 'short_name': 'Exec.Alim.',
     'description': 'Execução de prestação alimentícia com possibilidade de prisão civil.',
     'category': 'familia_sucessoes', 'icon': 'AlertCircle',  'color': 'orange',
     'legal_basis': 'CPC, Art. 528; Lei 5.478/1968', 'display_order': 8, 'is_active': True},

    {'code': 'exoneracao_alimentos',              'name': 'Exoneração de Alimentos',               'short_name': 'Exon.Alim.',
     'description': 'Ação para extinção ou redução da obrigação alimentar.',
     'category': 'familia_sucessoes', 'icon': 'MinusCircle',  'color': 'slate',
     'legal_basis': 'CC, Art. 1.699', 'display_order': 9, 'is_active': True},

    # === PREVIDENCIÁRIO ===
    {'code': 'peticao_concessao_beneficio',       'name': 'Petição de Concessão de Benefício',    'short_name': 'PetBenef.',
     'description': 'Ação judicial para concessão de benefício previdenciário negado administrativamente.',
     'category': 'previdenciario', 'icon': 'Shield',       'color': 'blue',
     'legal_basis': 'Lei 8.213/1991', 'display_order': 1, 'is_active': True},

    {'code': 'revisao_beneficio_previdenciario',  'name': 'Revisão de Benefício Previdenciário',  'short_name': 'RevBenef.',
     'description': 'Ação para revisão do valor ou data de início de benefício previdenciário.',
     'category': 'previdenciario', 'icon': 'RefreshCw',    'color': 'teal',
     'legal_basis': 'Lei 8.213/1991, Art. 103', 'display_order': 2, 'is_active': True},

    {'code': 'recurso_administrativo_inss',       'name': 'Recurso Administrativo INSS',           'short_name': 'RecINSS',
     'description': 'Recurso à JRPS/CRPS contra indeferimento ou cancelamento de benefício.',
     'category': 'previdenciario', 'icon': 'CornerUpRight', 'color': 'amber',
     'legal_basis': 'Decreto 3.048/1999 (RPS); Lei 8.213/1991, Art. 126', 'display_order': 3, 'is_active': True},

    {'code': 'acao_bpc_loas',                     'name': 'Ação BPC/LOAS',                         'short_name': 'BPC',
     'description': 'Ação para concessão do Benefício de Prestação Continuada ao deficiente ou idoso.',
     'category': 'previdenciario', 'icon': 'Heart',        'color': 'green',
     'legal_basis': 'Lei 8.742/1993, Art. 20', 'display_order': 4, 'is_active': True},

    {'code': 'acao_aposentadoria_especial',        'name': 'Ação de Aposentadoria Especial',        'short_name': 'Apos.Esp.',
     'description': 'Ação para reconhecimento de atividade especial e concessão de aposentadoria.',
     'category': 'previdenciario', 'icon': 'Clock',        'color': 'indigo',
     'legal_basis': 'Lei 8.213/1991, Art. 57', 'display_order': 5, 'is_active': True},

    # === CONSUMIDOR ===
    {'code': 'acao_indenizatoria_cdc',    'name': 'Ação Indenizatória (CDC)',          'short_name': 'IndCDC',
     'description': 'Ação de indenização por dano material e/ou moral nas relações de consumo.',
     'category': 'consumidor', 'icon': 'DollarSign', 'color': 'red',
     'legal_basis': 'CDC, Art. 6º, VI; Art. 14', 'display_order': 1, 'is_active': True},

    {'code': 'acao_vicio_produto',        'name': 'Ação por Vício de Produto/Serviço', 'short_name': 'Vício',
     'description': 'Ação para reparação, substituição ou ressarcimento por vício de produto ou serviço.',
     'category': 'consumidor', 'icon': 'Package',    'color': 'orange',
     'legal_basis': 'CDC, Art. 18; Art. 20', 'display_order': 2, 'is_active': True},

    {'code': 'acao_plano_saude',          'name': 'Ação contra Plano de Saúde',        'short_name': 'PlanoSaude',
     'description': 'Ação para obrigar plano de saúde a cobrir procedimento negado.',
     'category': 'consumidor', 'icon': 'Activity',   'color': 'green',
     'legal_basis': 'CDC; Lei 9.656/1998; RN ANS', 'display_order': 3, 'is_active': True},

    {'code': 'acao_indenizacao_consumidor','name': 'Ação de Indenização ao Consumidor', 'short_name': 'IndCons.',
     'description': 'Ação indenizatória genérica por prática abusiva, cobrança indevida ou falha de serviço.',
     'category': 'consumidor', 'icon': 'AlertOctagon','color': 'amber',
     'legal_basis': 'CDC, Art. 39; Art. 42', 'display_order': 4, 'is_active': True},

    # === TRIBUTÁRIO ===
    {'code': 'embargos_execucao_fiscal',        'name': 'Embargos à Execução Fiscal',          'short_name': 'Emb.EF',
     'description': 'Ação incidental do executado em execução fiscal para discutir o débito.',
     'category': 'tributario', 'icon': 'Hammer',       'color': 'red',
     'legal_basis': 'Lei 6.830/1980, Art. 16', 'display_order': 1, 'is_active': True},

    {'code': 'mandado_seguranca_tributario',    'name': 'Mandado de Segurança Tributário',     'short_name': 'MS Trib.',
     'description': 'Mandado de segurança para afastar cobrança tributária ilegal.',
     'category': 'tributario', 'icon': 'ShieldCheck',  'color': 'violet',
     'legal_basis': 'CF/88, Art. 5º, LXIX; CTN, Art. 151, IV', 'display_order': 2, 'is_active': True},

    {'code': 'recurso_administrativo_tributario','name': 'Recurso Administrativo Tributário',  'short_name': 'RecAdmTrib.',
     'description': 'Recurso perante o CARF ou JARE contra autuação fiscal.',
     'category': 'tributario', 'icon': 'CornerUpRight','color': 'amber',
     'legal_basis': 'Decreto 70.235/1972; Portaria MF 343/2015; Lei 9.784/1999', 'display_order': 3, 'is_active': True},

    {'code': 'acao_anulatoria_debito',          'name': 'Ação Anulatória de Débito Fiscal',   'short_name': 'Anulatória',
     'description': 'Ação para anular lançamento tributário eivado de vício.',
     'category': 'tributario', 'icon': 'XOctagon',     'color': 'orange',
     'legal_basis': 'CPC, Art. 38; CTN, Art. 149', 'display_order': 4, 'is_active': True},

    # === ADMINISTRATIVO ===
    {'code': 'recurso_administrativo_geral',         'name': 'Recurso Administrativo',                    'short_name': 'RecAdm.',
     'description': 'Recurso no âmbito administrativo contra decisão de órgão público.',
     'category': 'administrativo', 'icon': 'CornerUpRight','color': 'slate',
     'legal_basis': 'Lei 9.784/1999, Art. 56', 'display_order': 1, 'is_active': True},

    {'code': 'acao_anulacao_ato_administrativo',     'name': 'Ação de Anulação de Ato Administrativo',   'short_name': 'Anulatória Adm.',
     'description': 'Ação judicial para anular ato administrativo ilegal ou abusivo.',
     'category': 'administrativo', 'icon': 'XCircle',      'color': 'red',
     'legal_basis': 'Lei 9.784/1999; CPC, Art. 19', 'display_order': 2, 'is_active': True},

    {'code': 'mandado_seguranca_administrativo',     'name': 'Mandado de Segurança Administrativo',      'short_name': 'MS Adm.',
     'description': 'Mandado de segurança contra ato de autoridade administrativa.',
     'category': 'administrativo', 'icon': 'ShieldCheck',  'color': 'indigo',
     'legal_basis': 'CF/88, Art. 5º, LXIX; Lei 12.016/2009', 'display_order': 3, 'is_active': True},

    # === DIGITAL E LGPD ===
    {'code': 'notificacao_incidente_lgpd',      'name': 'Notificação de Incidente LGPD',         'short_name': 'Inc.LGPD',
     'description': 'Notificação à ANPD e titulares em caso de incidente de segurança com dados pessoais.',
     'category': 'digital_lgpd', 'icon': 'AlertTriangle', 'color': 'red',
     'legal_basis': 'LGPD, Art. 48', 'display_order': 1, 'is_active': True},

    {'code': 'resposta_titular_dados',          'name': 'Resposta a Titular de Dados',           'short_name': 'Titular',
     'description': 'Resposta formal a requisição de titular exercendo direitos da LGPD.',
     'category': 'digital_lgpd', 'icon': 'User',          'color': 'teal',
     'legal_basis': 'LGPD, Art. 18', 'display_order': 2, 'is_active': True},

    {'code': 'politica_privacidade',            'name': 'Política de Privacidade',               'short_name': 'Priv.',
     'description': 'Documento descrevendo o tratamento de dados pessoais pela organização.',
     'category': 'digital_lgpd', 'icon': 'Lock',          'color': 'slate',
     'legal_basis': 'LGPD, Art. 9º', 'display_order': 3, 'is_active': True},

    {'code': 'contrato_prestacao_servicos_ti',  'name': 'Contrato de Prestação de Serviços TI',  'short_name': 'CTR-TI',
     'description': 'Contrato de prestação de serviços de tecnologia com cláusulas de proteção de dados.',
     'category': 'digital_lgpd', 'icon': 'Monitor',       'color': 'blue',
     'legal_basis': 'CC, Art. 421; LGPD, Art. 26', 'display_order': 4, 'is_active': True},

    {'code': 'dpa_tratamento_dados',            'name': 'DPA - Acordo de Tratamento de Dados',   'short_name': 'DPA',
     'description': 'Data Processing Agreement entre controlador e operador conforme exigido pela LGPD.',
     'category': 'digital_lgpd', 'icon': 'FileLock',      'color': 'indigo',
     'legal_basis': 'LGPD, Art. 37-40', 'display_order': 5, 'is_active': True},

    # === EMPRESARIAL ===
    {'code': 'contrato_social_ltda',                        'name': 'Contrato Social (LTDA)',                         'short_name': 'ContSocial',
     'description': 'Instrumento de constituição ou alteração de sociedade limitada.',
     'category': 'empresarial', 'icon': 'Building2',    'color': 'blue',
     'legal_basis': 'CC, Art. 1.052; Lei 14.195/2021', 'display_order': 1, 'is_active': True},

    {'code': 'recuperacao_judicial',                        'name': 'Recuperação Judicial',                           'short_name': 'RecupJud.',
     'description': 'Petição inicial de recuperação judicial para soerguer empresa em crise.',
     'category': 'empresarial', 'icon': 'TrendingUp',   'color': 'green',
     'legal_basis': 'Lei 11.101/2005, Art. 51', 'display_order': 2, 'is_active': True},

    {'code': 'dissolucao_sociedade',                        'name': 'Dissolução de Sociedade',                        'short_name': 'Dissolução',
     'description': 'Ação ou instrumento para encerramento de sociedade empresária.',
     'category': 'empresarial', 'icon': 'XCircle',      'color': 'red',
     'legal_basis': 'CC, Art. 1.033; Lei 6.404/1976, Art. 206', 'display_order': 3, 'is_active': True},

    {'code': 'contrato_prestacao_servicos_empresarial',     'name': 'Contrato de Prestação de Serviços Empresarial',  'short_name': 'CTR-Emp.',
     'description': 'Contrato B2B de prestação de serviços entre empresas.',
     'category': 'empresarial', 'icon': 'FileSignature','color': 'teal',
     'legal_basis': 'CC, Art. 421; CC, Art. 593', 'display_order': 4, 'is_active': True},
]


class Command(BaseCommand):
    help = 'Cria/atualiza tipos de documento jurídico do Verus.AI (15 categorias unificadas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Atualiza tipos e categorias mesmo se já existirem',
        )

    def handle(self, *args, **options):
        from apps.core.models import DocumentCategory, DocumentType

        force = options.get('force', False)

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('SEED: Tipos de Documento Jurídico (taxonomia unificada)')
        self.stdout.write('=' * 60 + '\n')

        # ── 1. Remove categorias legadas ─────────────────────────────────────
        # Primeiro remove DocumentTypes que apontem para categorias legadas
        # (evita ProtectedError ao deletar as categorias)
        legadas_cats = DocumentCategory.objects.filter(code__in=CATEGORIAS_LEGADAS)
        if legadas_cats.exists():
            orphan_types = DocumentType.objects.filter(category__in=legadas_cats)
            orphan_count = orphan_types.count()
            if orphan_count:
                orphan_types.delete()
                self.stdout.write(self.style.WARNING(
                    f'  Removidos {orphan_count} tipo(s) de documento vinculados a categorias legadas'
                ))
            legadas_count = legadas_cats.count()
            legadas_cats.delete()
            self.stdout.write(self.style.WARNING(
                f'  Removidas {legadas_count} categoria(s) legada(s): {CATEGORIAS_LEGADAS}'
            ))

        # ── 2. Cria/atualiza as 15 categorias ───────────────────────────────
        self.stdout.write('\n  Categorias:')
        for cat_data in CATEGORIAS:
            defaults = {
                'name': cat_data['name'],
                'description': '',
                'display_order': cat_data['display_order'],
                'is_active': True,
            }
            if force:
                cat_obj, created = DocumentCategory.objects.update_or_create(
                    code=cat_data['code'], defaults=defaults
                )
            else:
                cat_obj, created = DocumentCategory.objects.get_or_create(
                    code=cat_data['code'], defaults=defaults
                )
            status = self.style.SUCCESS('✓ Criada') if created else self.style.HTTP_INFO('⊘ Existe')
            self.stdout.write(f'    {status}  {cat_obj.code}')

        # Índice de categorias por code
        category_by_code = {c.code: c for c in DocumentCategory.objects.all()}

        # ── 3. Cria/atualiza tipos de documento ──────────────────────────────
        self.stdout.write('\n  Tipos de documento:')
        created_count = updated_count = skipped_count = 0

        for data in DOCUMENT_TYPES_DATA:
            category_obj = category_by_code.get(data['category'])
            if category_obj is None:
                self.stdout.write(self.style.ERROR(
                    f"    ✗ Categoria '{data['category']}' não encontrada — ignorando '{data['code']}'"
                ))
                continue

            defaults = {
                'name': data['name'],
                'short_name': data['short_name'],
                'description': data['description'],
                'category': category_obj,
                'icon': data['icon'],
                'color': data['color'],
                'legal_basis': data['legal_basis'],
                'display_order': data['display_order'],
                'is_active': data['is_active'],
            }

            if force:
                doc_type, created = DocumentType.objects.update_or_create(
                    code=data['code'], defaults=defaults
                )
                if created:
                    created_count += 1
                    marker, style = '✓ Criado', self.style.SUCCESS
                else:
                    updated_count += 1
                    marker, style = '↻ Atualizado', self.style.WARNING
            else:
                doc_type, created = DocumentType.objects.get_or_create(
                    code=data['code'], defaults=defaults
                )
                if created:
                    created_count += 1
                    marker, style = '✓ Criado', self.style.SUCCESS
                else:
                    skipped_count += 1
                    marker, style = '⊘ Já existe', self.style.HTTP_INFO

            active_mark = '✓' if doc_type.is_active else '✗'
            self.stdout.write(style(
                f'    {marker:<15} [{active_mark}] {doc_type.short_name:<20} - {doc_type.name}'
            ))

        # ── 4. Resumo ────────────────────────────────────────────────────────
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('RESUMO'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Categorias legadas removidas: {legadas_count}')
        self.stdout.write(f'  Tipos criados:     {created_count}')
        self.stdout.write(f'  Tipos atualizados: {updated_count}')
        self.stdout.write(f'  Tipos ignorados:   {skipped_count}')
        self.stdout.write('  Total de tipos:    ' + str(len(DOCUMENT_TYPES_DATA)))
        self.stdout.write('\n' + '=' * 60 + '\n')
