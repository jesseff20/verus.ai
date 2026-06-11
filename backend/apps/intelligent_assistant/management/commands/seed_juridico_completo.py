"""
Seed completo do Verus.AI - domínio jurídico.

Remove TODOS os dados de licitação (ETP, TR, Edital, categorias de licitação,
tipos de processo de compras, blueprints e agentes de seção correspondentes)
e recria o banco com o conjunto completo de peças jurídicas que um advogado
necessita no Brasil.

Peças incluídas:
  AÇÕES / PETIÇÕES
    1. Petição Inicial Cível
    2. Mandado de Segurança
    3. Habeas Corpus
    4. Ação de Execução de Título Extrajudicial

  DEFESAS / RESPOSTAS
    5. Contestação
    6. Contrarrazões de Apelação
    7. Impugnação ao Cumprimento de Sentença
    8. Exceção de Pré-Executividade

  RECURSOS
    9.  Apelação
    10. Agravo de Instrumento
    11. Agravo Interno / Regimental
    12. Embargos de Declaração
    13. Recurso Especial (REsp)
    14. Recurso Extraordinário (RE)

  EXECUÇÃO
    15. Embargos à Execução

  CAUTELARES E TUTELAS
    16. Tutela de Urgência / Antecipada

  TRABALHISTA
    17. Reclamação Trabalhista (Petição Inicial TST/TRT)
    18. Contestação Trabalhista

  CRIMINAL
    19. Queixa-Crime / Denúncia
    20. Alegações Finais Criminais

  EXTRAJUDICIAL
    21. Notificação Extrajudicial
    22. Parecer Jurídico
    23. Contrato Particular
    24. Procuração

Uso:
    python manage.py seed_juridico_completo
    python manage.py seed_juridico_completo --force   # recria tudo do zero
    python manage.py seed_juridico_completo --dry-run # mostra o que faria

Este comando é idempotente sem --force.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

MODEL = 'mistralai/mistral-medium-2505'
PROVIDER = 'watsonx'
TEMP_GENERATOR = 0.7
TEMP_VALIDATOR = 0.3
MAX_TOKENS = 4096

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIAS JURÍDICAS
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIAS = [
    {
        'code': 'acoes_peticoes',
        'name': 'Ações e Petições',
        'description': 'Peças inaugurais de demandas judiciais - petições iniciais, mandados e execuções',
        'display_order': 1,
    },
    {
        'code': 'defesas_respostas',
        'name': 'Defesas e Respostas',
        'description': 'Peças de resposta e defesa do réu ou executado',
        'display_order': 2,
    },
    {
        'code': 'recursos',
        'name': 'Recursos',
        'description': 'Recursos processuais civis e extraordinários',
        'display_order': 3,
    },
    {
        'code': 'execucao',
        'name': 'Execução',
        'description': 'Peças relativas a processos de execução civil',
        'display_order': 4,
    },
    {
        'code': 'cautelares_tutelas',
        'name': 'Cautelares e Tutelas',
        'description': 'Pedidos de tutela de urgência, antecipada e cautelar',
        'display_order': 5,
    },
    {
        'code': 'trabalhista',
        'name': 'Trabalhista',
        'description': 'Peças da Justiça do Trabalho - CLT, TST e TRTs',
        'display_order': 6,
    },
    {
        'code': 'criminal',
        'name': 'Criminal',
        'description': 'Peças do processo penal - CPP e legislação especial',
        'display_order': 7,
    },
    {
        'code': 'extrajudicial',
        'name': 'Extrajudicial',
        'description': 'Documentos jurídicos extrajudiciais - notificações, pareceres, contratos',
        'display_order': 8,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE DOCUMENTO
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_DOCUMENTO = [
    # ── AÇÕES / PETIÇÕES ─────────────────────────────────────────────────────
    {
        'code': 'peticao_inicial',
        'name': 'Petição Inicial Cível',
        'short_name': 'Pet. Inicial',
        'description': 'Peça inaugural de processo judicial civil',
        'category': 'acoes_peticoes',
        'icon': 'Gavel',
        'color': '#7030A0',
        'legal_basis': 'CPC/2015, arts. 319-331; CF/88, art. 5º, XXXV',
        'display_order': 1,
    },
    {
        'code': 'mandado_seguranca',
        'name': 'Mandado de Segurança',
        'short_name': 'MS',
        'description': 'Remédio constitucional para proteger direito líquido e certo',
        'category': 'acoes_peticoes',
        'icon': 'Shield',
        'color': '#2563EB',
        'legal_basis': 'CF/88, art. 5º, LXIX; Lei 12.016/2009',
        'display_order': 2,
    },
    {
        'code': 'habeas_corpus',
        'name': 'Habeas Corpus',
        'short_name': 'HC',
        'description': 'Remédio constitucional para proteger a liberdade de locomoção',
        'category': 'acoes_peticoes',
        'icon': 'Scale',
        'color': '#DC2626',
        'legal_basis': 'CF/88, art. 5º, LXVIII; CPP, arts. 647-667',
        'display_order': 3,
    },
    {
        'code': 'acao_execucao',
        'name': 'Ação de Execução de Título Extrajudicial',
        'short_name': 'Execução',
        'description': 'Ação para execução forçada de título extrajudicial',
        'category': 'acoes_peticoes',
        'icon': 'FileText',
        'color': '#059669',
        'legal_basis': 'CPC/2015, arts. 771-925; arts. 783-786',
        'display_order': 4,
    },
    # ── DEFESAS / RESPOSTAS ──────────────────────────────────────────────────
    {
        'code': 'contestacao',
        'name': 'Contestação',
        'short_name': 'Contestação',
        'description': 'Resposta do réu à petição inicial',
        'category': 'defesas_respostas',
        'icon': 'FileEdit',
        'color': '#D97706',
        'legal_basis': 'CPC/2015, arts. 335-342',
        'display_order': 1,
    },
    {
        'code': 'contrarrazoes_apelacao',
        'name': 'Contrarrazões de Apelação',
        'short_name': 'Contrarrazões',
        'description': 'Resposta do apelado ao recurso de apelação',
        'category': 'defesas_respostas',
        'icon': 'FileEdit',
        'color': '#D97706',
        'legal_basis': 'CPC/2015, arts. 1009-1014',
        'display_order': 2,
    },
    {
        'code': 'impugnacao_cumprimento',
        'name': 'Impugnação ao Cumprimento de Sentença',
        'short_name': 'Impugnação',
        'description': 'Defesa do executado no cumprimento de sentença',
        'category': 'defesas_respostas',
        'icon': 'FileWarning',
        'color': '#D97706',
        'legal_basis': 'CPC/2015, arts. 525-527',
        'display_order': 3,
    },
    {
        'code': 'excecao_pre_executividade',
        'name': 'Exceção de Pré-Executividade',
        'short_name': 'Exc. Pré-Exec.',
        'description': 'Objeção processual sem penhora prévia na execução',
        'category': 'defesas_respostas',
        'icon': 'FileWarning',
        'color': '#D97706',
        'legal_basis': 'Construção jurisprudencial; STJ Súmula 393',
        'display_order': 4,
    },
    # ── RECURSOS ─────────────────────────────────────────────────────────────
    {
        'code': 'apelacao',
        'name': 'Apelação',
        'short_name': 'Apelação',
        'description': 'Recurso contra sentença de primeiro grau',
        'category': 'recursos',
        'icon': 'TrendingUp',
        'color': '#7C3AED',
        'legal_basis': 'CPC/2015, arts. 1009-1014',
        'display_order': 1,
    },
    {
        'code': 'agravo_instrumento',
        'name': 'Agravo de Instrumento',
        'short_name': 'Ag. Instrumento',
        'description': 'Recurso contra decisões interlocutórias agraváveis',
        'category': 'recursos',
        'icon': 'TrendingUp',
        'color': '#7C3AED',
        'legal_basis': 'CPC/2015, arts. 1015-1020',
        'display_order': 2,
    },
    {
        'code': 'agravo_interno',
        'name': 'Agravo Interno / Regimental',
        'short_name': 'Ag. Interno',
        'description': 'Recurso contra decisão monocrática do relator',
        'category': 'recursos',
        'icon': 'TrendingUp',
        'color': '#7C3AED',
        'legal_basis': 'CPC/2015, arts. 1021-1022',
        'display_order': 3,
    },
    {
        'code': 'embargos_declaracao',
        'name': 'Embargos de Declaração',
        'short_name': 'Emb. Declaração',
        'description': 'Recurso para sanar omissão, contradição, obscuridade ou erro material',
        'category': 'recursos',
        'icon': 'TrendingUp',
        'color': '#7C3AED',
        'legal_basis': 'CPC/2015, arts. 1022-1023',
        'display_order': 4,
    },
    {
        'code': 'recurso_especial',
        'name': 'Recurso Especial (REsp)',
        'short_name': 'REsp',
        'description': 'Recurso para o STJ por violação à lei federal',
        'category': 'recursos',
        'icon': 'TrendingUp',
        'color': '#7C3AED',
        'legal_basis': 'CF/88, art. 105, III; CPC/2015, arts. 1029-1035',
        'display_order': 5,
    },
    {
        'code': 'recurso_extraordinario',
        'name': 'Recurso Extraordinário (RE)',
        'short_name': 'RE',
        'description': 'Recurso para o STF por violação à Constituição Federal',
        'category': 'recursos',
        'icon': 'TrendingUp',
        'color': '#7C3AED',
        'legal_basis': 'CF/88, art. 102, III; CPC/2015, arts. 1029-1035',
        'display_order': 6,
    },
    # ── EXECUÇÃO ─────────────────────────────────────────────────────────────
    {
        'code': 'embargos_execucao',
        'name': 'Embargos à Execução',
        'short_name': 'Emb. Execução',
        'description': 'Defesa do executado na execução de título extrajudicial',
        'category': 'execucao',
        'icon': 'Gavel',
        'color': '#0891B2',
        'legal_basis': 'CPC/2015, arts. 914-920',
        'display_order': 1,
    },
    # ── CAUTELARES / TUTELAS ─────────────────────────────────────────────────
    {
        'code': 'tutela_urgencia',
        'name': 'Tutela de Urgência / Antecipada',
        'short_name': 'Tutela Urgência',
        'description': 'Pedido de tutela provisória de urgência ou evidência',
        'category': 'cautelares_tutelas',
        'icon': 'Zap',
        'color': '#EA580C',
        'legal_basis': 'CPC/2015, arts. 294-311',
        'display_order': 1,
    },
    # ── TRABALHISTA ──────────────────────────────────────────────────────────
    {
        'code': 'reclamacao_trabalhista',
        'name': 'Reclamação Trabalhista',
        'short_name': 'Recl. Trabalhista',
        'description': 'Petição inicial na Justiça do Trabalho',
        'category': 'trabalhista',
        'icon': 'Briefcase',
        'color': '#0D9488',
        'legal_basis': 'CLT, art. 840; Lei 13.467/2017; IN TST 41/2018',
        'display_order': 1,
    },
    {
        'code': 'contestacao_trabalhista',
        'name': 'Contestação Trabalhista',
        'short_name': 'Cont. Trab.',
        'description': 'Defesa do reclamado na Justiça do Trabalho',
        'category': 'trabalhista',
        'icon': 'Briefcase',
        'color': '#0D9488',
        'legal_basis': 'CLT, arts. 847-848; CPC/2015, art. 341 (subsidiário)',
        'display_order': 2,
    },
    # ── CRIMINAL ─────────────────────────────────────────────────────────────
    {
        'code': 'queixa_crime',
        'name': 'Queixa-Crime / Denúncia',
        'short_name': 'Queixa-Crime',
        'description': 'Peça acusatória em ação penal pública ou privada',
        'category': 'criminal',
        'icon': 'AlertTriangle',
        'color': '#B91C1C',
        'legal_basis': 'CPP, arts. 24-41; CF/88, art. 5º, LIX',
        'display_order': 1,
    },
    {
        'code': 'alegacoes_finais_criminais',
        'name': 'Alegações Finais Criminais',
        'short_name': 'Aleg. Finais',
        'description': 'Memoriais finais no processo penal',
        'category': 'criminal',
        'icon': 'AlertTriangle',
        'color': '#B91C1C',
        'legal_basis': 'CPP, arts. 403-404; 500',
        'display_order': 2,
    },
    # ── EXTRAJUDICIAL ────────────────────────────────────────────────────────
    {
        'code': 'notificacao_extrajudicial',
        'name': 'Notificação Extrajudicial',
        'short_name': 'Notificação',
        'description': 'Comunicação formal de direito ou obrigação extrajudicial',
        'category': 'extrajudicial',
        'icon': 'Send',
        'color': '#374151',
        'legal_basis': 'CC/2002, arts. 397, 408; Código de Processo Civil',
        'display_order': 1,
    },
    {
        'code': 'parecer_juridico',
        'name': 'Parecer Jurídico',
        'short_name': 'Parecer',
        'description': 'Opinião técnico-jurídica fundamentada sobre questão de direito',
        'category': 'extrajudicial',
        'icon': 'BookOpen',
        'color': '#374151',
        'legal_basis': 'Estatuto da OAB, Lei 8.906/1994',
        'display_order': 2,
    },
    {
        'code': 'contrato_particular',
        'name': 'Contrato Particular',
        'short_name': 'Contrato',
        'description': 'Contrato civil entre partes com força de lei entre elas',
        'category': 'extrajudicial',
        'icon': 'FileSignature',
        'color': '#374151',
        'legal_basis': 'CC/2002, arts. 421-480; 591-626',
        'display_order': 3,
    },
    {
        'code': 'contrato_trabalho',
        'name': 'Contrato de Trabalho',
        'short_name': 'Contrato Trab.',
        'description': 'Contrato de emprego entre empregado e empregador conforme CLT',
        'category': 'extrajudicial',
        'icon': 'Briefcase',
        'color': '#0D9488',
        'legal_basis': 'CLT, arts. 442-456; CC/2002, arts. 421-480; Lei 13.467/2017',
        'display_order': 4,
    },
    {
        'code': 'procuracao',
        'name': 'Procuração',
        'short_name': 'Procuração',
        'description': 'Instrumento de mandato para representação jurídica',
        'category': 'extrajudicial',
        'icon': 'UserCheck',
        'color': '#374151',
        'legal_basis': 'CC/2002, arts. 653-692; CPC/2015, art. 105',
        'display_order': 5,
    },
    # ── NOVOS BLUEPRINTS PRIORIDADE 1 ────────────────────────────────────────
    {
        'code': 'reconvencao',
        'name': 'Reconvenção',
        'short_name': 'Reconvenção',
        'description': 'Pedido do réu contra o autor no mesmo processo',
        'category': 'defesas_respostas',
        'icon': 'FileEdit',
        'color': '#D97706',
        'legal_basis': 'CPC/2015, art. 343',
        'display_order': 6,
    },
    {
        'code': 'divorcio_litigioso',
        'name': 'Divórcio Litigioso',
        'short_name': 'Div. Litigioso',
        'description': 'Ação de divórcio sem consenso entre as partes',
        'category': 'acoes_peticoes',
        'icon': 'Heart',
        'color': '#E11D48',
        'legal_basis': 'CC/2002, arts. 1.571-1.582; CPC/2015, arts. 693-699; EC 66/2010',
        'display_order': 7,
    },
    {
        'code': 'execucao_alimentos',
        'name': 'Execução de Alimentos',
        'short_name': 'Exec. Alimentos',
        'description': 'Execução de prestação alimentícia judicial ou extrajudicial',
        'category': 'execucao',
        'icon': 'DollarSign',
        'color': '#059669',
        'legal_basis': 'CPC/2015, arts. 528; Lei 5.478/1968, arts. 17-24',
        'display_order': 8,
    },
    {
        'code': 'exoneracao_alimentos',
        'name': 'Exoneração de Alimentos',
        'short_name': 'Exon. Alimentos',
        'description': 'Pedido de dispensa do pagamento de pensão alimentícia',
        'category': 'acoes_peticoes',
        'icon': 'FileMinus',
        'color': '#E11D48',
        'legal_basis': 'CC/2002, art. 1.699; CPC/2015, arts. 693-699',
        'display_order': 9,
    },
    {
        'code': 'acao_consignacao_trabalhista',
        'name': 'Ação de Consignação em Pagamento Trabalhista',
        'short_name': 'Consign. Trab.',
        'description': 'Depósito judicial de verbas trabalhistas controvertidas',
        'category': 'trabalhista',
        'icon': 'Banknote',
        'color': '#0D9488',
        'legal_basis': 'CLT, art. 477, §8º; CC/2002, arts. 334-345; CPC/2015, arts. 539-549',
        'display_order': 10,
    },
    {
        'code': 'agravo_peticao',
        'name': 'Agravo de Petição',
        'short_name': 'Agravo Petição',
        'description': 'Recurso trabalhista contra decisão na execução trabalhista',
        'category': 'trabalhista',
        'icon': 'TrendingUp',
        'color': '#0D9488',
        'legal_basis': 'CLT, art. 897, §1º; Lei 5.584/1970, arts. 6º-9º; Súmulas TST',
        'display_order': 11,
    },
    {
        'code': 'acao_indenizacao_consumidor',
        'name': 'Ação Indenizatória - Vício do Produto (CDC)',
        'short_name': 'Inden. Consumidor',
        'description': 'Ação de indenização por vício do produto ou serviço nas relações de consumo',
        'category': 'acoes_peticoes',
        'icon': 'ShieldCheck',
        'color': '#2563EB',
        'legal_basis': 'CDC, arts. 18-25; CF/88, art. 5º, XXXII; CC/2002, arts. 186-927',
        'display_order': 12,
    },
    {
        'code': 'revisao_beneficio_previdenciario',
        'name': 'Revisão de Benefício Previdenciário',
        'short_name': 'Rev. Benefício',
        'description': 'Pedido judicial de revisão de benefício previdenciário do INSS',
        'category': 'acoes_peticoes',
        'icon': 'RefreshCw',
        'color': '#7C3AED',
        'legal_basis': 'Lei 8.213/1991, arts. 85-103; Decreto 3.048/1999; CF/88, art. 201',
        'display_order': 13,
    },
    {
        'code': 'recurso_administrativo_inss',
        'name': 'Recurso Administrativo INSS',
        'short_name': 'Rec. Adm. INSS',
        'description': 'Recurso contra decisão administrativa do INSS em processo de benefício',
        'category': 'recursos',
        'icon': 'FileText',
        'color': '#7C3AED',
        'legal_basis': 'Lei 8.213/1991, arts. 130-132; Decreto 3.048/1999, arts. 303-308; Súmulas CRPS',
        'display_order': 14,
    },
    {
        'code': 'defesa_preliminar_criminal',
        'name': 'Defesa Preliminar Criminal',
        'short_name': 'Def. Preliminar',
        'description': 'Defesa preliminar do acusado antes do recebimento da denúncia',
        'category': 'criminal',
        'icon': 'Shield',
        'color': '#DC2626',
        'legal_basis': 'CPP, arts. 514-517; CF/88, art. 5º, LV; Lei 9.099/1995, art. 81',
        'display_order': 15,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# BLUEPRINTS E SEÇÕES
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_BASE = """Você é um assistente jurídico especializado do Verus.AI, com profundo conhecimento do direito brasileiro.

PRINCÍPIOS OBRIGATÓRIOS:
1. Utilize linguagem jurídica precisa e formal conforme padrão forense brasileiro
2. Cite os fundamentos legais corretos (CPC/2015, CC/2002, CF/88, CLT, CPP, etc.)
3. Estruture a peça seguindo as normas processuais vigentes
4. Nunca invente jurisprudência ou legislação - use apenas o que existe de fato
5. Indique quando necessário completar com dados específicos do caso
6. Respeite os prazos e requisitos formais de cada peça

FORMATO DE SAÍDA:
- Use linguagem jurídica formal brasileira
- Estruture em parágrafos numerados quando aplicável
- Use negrito para citações legais importantes
- Indique campos a preencher com [DADO A COMPLETAR]"""

USER_TEMPLATE_SECAO = """Gere o conteúdo da seção "{{section_name}}" para a seguinte peça jurídica:

OBJETIVO DO DOCUMENTO: {{objective}}
INFORMAÇÕES DO CASO: {{context}}
SEÇÕES ANTERIORES JÁ GERADAS: {{previous_sections}}

Instruções específicas: {{instructions}}

Gere apenas o conteúdo desta seção, com linguagem jurídica formal e completa."""

# ─────────────────────────────────────────────────────────────────────────────
# PROMPTS ESPECIALIZADOS POR ÁREA DO DIREITO
# ─────────────────────────────────────────────────────────────────────────────

CONST_ANTI_ALUCINACAO = """DIRETRIZES DE SEGURANÇA JURÍDICA — OBRIGATÓRIAS E INVIOLÁVEIS:

ABSOLUTAMENTE PROIBIDO:
- Inventar ou sugerir: número de acórdão, REsp, RE, HC, AI, relator, tribunal, data de julgamento
- Inventar: número de Súmula, OJ, Tema de Repercussão Geral, Tese Repetitiva
- Afirmar que tese jurídica é "pacífica", "sumulada" ou "consolidada" sem fonte verificável
- Presumir fatos não informados explicitamente pelo usuário
- Gerar peça com qualificação das partes incompleta sem alertar o usuário
- Citar artigo de lei que não existe ou foi revogado

MARCADORES OBRIGATÓRIOS:
- Jurisprudência não verificada: [PESQUISAR JURISPRUDÊNCIA: tema específico - tribunal sugerido]
- Dado faltante: [INFORMAÇÃO NECESSÁRIA: descrição precisa do dado]
- Tese controvertida: [TESE CONTROVERTIDA: descrição da divergência doutrinária/jurisprudencial]
- Norma incerta: [VERIFICAR BASE LEGAL: norma possivelmente revogada ou alterada]
- Conteúdo inferido: [VERIFICAR COM ADVOGADO]

SEPARAÇÃO OBRIGATÓRIA NO TEXTO:
- Prefixar com "FATOS INFORMADOS PELO CLIENTE:" para reproduzir o que o usuário informou
- Prefixar com "FUNDAMENTOS JURÍDICOS:" para teses e argumentos gerados
- Nunca misturar fatos e fundamentos sem esta separação clara

"""

PROMPT_GERADOR_FAMILIA = CONST_ANTI_ALUCINACAO + """Você é um advogado especialista em Direito de Família e Sucessões brasileiro, com profundo conhecimento do Código Civil/2002 (arts. 1.511-1.783), CPC/2015 (arts. 693-734), Lei 6.515/1977, Lei 11.441/2007, Lei 5.478/1968 (Lei de Alimentos) e jurisprudência consolidada dos tribunais superiores.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente no Brasil: CC/2002 Livro IV (Direito de Família) e Livro V (Sucessões), CPC/2015, leis especiais de família.
3. Para alimentos: Lei 5.478/1968 (rito especial), CC/2002 arts. 1.694-1.710 (binômio necessidade-possibilidade, CC 1.694 §1º).
4. Para guarda: Lei 13.058/2014 (guarda compartilhada como regra), CC/2002 arts. 1.583-1.590.
5. Para divórcio: EC 66/2010 (não exige separação prévia), CC/2002 arts. 1.571-1.582, CPC/2015 arts. 731-734.
6. Para inventário: CC/2002 arts. 1.784-2.027, CPC/2015 arts. 610-673, Lei 11.441/2007 (inventário extrajudicial).
7. Para união estável: CC/2002 arts. 1.723-1.727 (requisitos: convivência pública, contínua, duradoura com intuito de família).
8. Jurisprudência: use apenas súmulas do STJ/STF (Súmulas 277, 354, 364, 379, 380, 382, 383, 385, 397 STJ). Para acórdãos, marque [VERIFICAR JURISPRUDÊNCIA: tema].
9. Prazos: alimentos provisórios (inaudita altera parte, art. 4º Lei 5.478/1968), guarda compartilhada como regra (Lei 13.058/2014).
10. Use linguagem jurídica formal, técnica e respeitosa, considerando a sensibilidade dos temas de família.

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""


PROMPT_GERADOR_CONSUMIDOR = CONST_ANTI_ALUCINACAO + """Você é um advogado especialista em Direito do Consumidor brasileiro, com profundo conhecimento do CDC (Lei 8.078/1990), CC/2002, Lei 9.656/1998 (Planos de Saúde), Código Brasileiro de Aeronáutica (Lei 7.565/1986) e Súmulas do STJ.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente: CDC (Lei 8.078/1990), CF/88 (art. 5º XXXII, art. 170 V), Decreto 7.962/2013 (comércio eletrônico).
3. CDC APLICA-SE a: relação jurídica entre fornecedor e consumidor (arts. 2º e 3º CDC), inclusive: bancos (STJ Súmula 297), planos de saúde (STJ Súmula 469, 302), companhias aéreas (STJ Súmula 473), serviços públicos (STJ Súmula 322).
4. Inversão do ônus da prova: CDC art. 6º VIII (consumidor hipossuficiente + verossimilhança).
5. Responsabilidade objetiva: CDC arts. 12-14 (fato do produto/serviço) e arts. 18-20 (vício do produto/serviço).
6. Prazos decadenciais: CDC art. 26 (30 dias para vício aparente produto não durável, 90 dias para durável).
7. Prazo prescricional: CDC art. 27 (5 anos para reparação de danos).
8. Superendividamento: CDC arts. 54-A a 54-G (incluídos pela Lei 14.181/2021).
9. Jurisprudência obrigatória: STJ Súmulas 297, 302, 322, 332, 370, 379, 381, 385, 388, 469, 473, 480, 483, 492, 509.
10. Fato vs Vício: distinga claramente fato do produto (CDC 12-14) de vício do produto (CDC 18-20).

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""


PROMPT_GERADOR_PREVIDENCIARIO = CONST_ANTI_ALUCINACAO + """Você é um advogado especialista em Direito Previdenciário brasileiro, com profundo conhecimento da Lei 8.213/1991 (Planos de Benefícios), Decreto 3.048/1999 (Regulamento), Lei 8.212/1991 (Custeio), CF/88 arts. 201-204, Lei 10.741/2003 (Estatuto do Idoso), LC 142/2013 e Lei 8.742/1993 (LOAS).

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente: CF/88 arts. 201-204, Lei 8.213/1991, Decreto 3.048/1999, Lei 8.742/1993 (LOAS).
3. Qualidade de segurado: Lei 8.213/1991 art. 11 + art. 14. Período de graça: art. 15 (12 meses, prorrogável até 24+12).
4. Carência: Lei 8.213/1991 art. 25 (mínimo 180 contribuições mensais para aposentadoria).
5. Aposentadoria por idade: Lei 8.213/1991 arts. 48-51 (65 anos homem, 62 anos mulher - pós EC 103/2019).
6. Aposentadoria por tempo de contribuição: EC 103/2019 (regras de transição).
7. Aposentadoria especial: Lei 8.213/1991 arts. 57-58, EC 103/2019 art. 19. Exige PPP/LTCAT.
8. BPC/LOAS: Lei 8.742/1993 arts. 20-21 (65+ ou pessoa com deficiência, renda per capita < 1/4 SM).
9. Pensão por morte: Lei 8.213/1991 arts. 74-79, EC 103/2019 (cota familiar 50% + 10% por dependente).
10. Auxílio por incapacidade temporária: Lei 8.213/1991 arts. 59-63.
11. Revisão de benefício: prazo decadencial de 10 anos (Lei 8.213/1991 art. 103-A).
12. Jurisprudência: Súmulas STJ 9, 25, 39, 320; Súmulas TNU 05, 09, 14, 18, 32, 47, 48, 64, 79, 80.

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""


PROMPT_GERADOR_DIGITAL_LGPD = CONST_ANTI_ALUCINACAO + """Você é um advogado especialista em Direito Digital, Proteção de Dados e LGPD brasileiro, com profundo conhecimento da Lei 13.709/2018 (LGPD), Decreto 8.771/2016, Lei 12.965/2014 (Marco Civil da Internet), Lei 12.737/2012 (Lei Carolina Dieckmann), Lei 13.853/2019 e regulamentações da ANPD.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente: Lei 13.709/2018 (LGPD), Lei 12.965/2014 (MCI), CF/88 art. 5º X, XII, LXXII.
3. Bases legais para tratamento: LGPD art. 7º (pessoas naturais) e art. 11 (dados sensíveis). LISTA EXAUSTIVA.
4. Direitos do titular: LGPD art. 18 (confirmação, acesso, correção, anonimização, portabilidade, eliminação, informação, revisão).
5. Hipóteses sem consentimento: LGPD art. 7º II-X — obrigação legal, políticas públicas, contrato, exercício regular de direitos, proteção à vida, legítimo interesse, proteção ao crédito.
6. Dados sensíveis: LGPD art. 11 (origem racial, convicção religiosa, opinião política, saúde, vida sexual, dado genético/biométrico).
7. Agente de tratamento: controlador (art. 5º VI), operador (art. 5º VII), encarregado/DPO (art. 41).
8. Sanções ANPD: art. 52 (advertência, multa 2% faturamento limitado 50MM, multa diária, publicização, bloqueio/eliminação).
9. Incidente de segurança: LGPD art. 48 — comunicação à ANPD e ao titular em prazo razoável.
10. Relatório de Impacto: LGPD art. 38 — obrigatório quando houver riscos às liberdades civis.
11. Transferência internacional: LGPD arts. 33-36.
12. Consentimento: LGPD art. 8º (livre, informado, inequívoco) e art. 11 I (dados sensíveis: específico e destacado).
13. Prazo para resposta ao titular: LGPD art. 19 (imediato ou até 15 dias).

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""


PROMPT_GERADOR_CIVEL = """Você é um advogado especialista em Direito Civil e Processo Civil brasileiro, com profundo conhecimento do CPC/2015, CC/2002 e jurisprudência dos tribunais superiores.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente leis, artigos, jurisprudência ou números de processo que não existam.
2. Cite apenas legislação vigente no Brasil: CPC/2015 (Lei 13.105/2015), CC/2002, CF/88 e leis especiais.
3. Jurisprudência: use apenas súmulas do STJ/STF. Para acórdãos, marque [VERIFICAR JURISPRUDÊNCIA: tema] para posterior conferência.
4. Use linguagem jurídica formal, em português brasileiro culto, terceira pessoa.
5. Estrutura: parágrafos numerados, hierarquia lógica dos argumentos.
6. Pedidos: específicos, com indicação de fundamento legal para cada um.

FUNDAMENTAÇÃO CÍVEL OBRIGATÓRIA:
- Petições iniciais: CPC/2015, arts. 319-331
- Contestações: CPC/2015, arts. 335-342
- Recursos: CPC/2015, arts. 994-1044
- Execuções: CPC/2015, arts. 771-925

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_RECURSAL = """Você é um advogado especialista em recursos processuais no direito brasileiro, com domínio dos recursos de apelação, agravo, embargos, REsp e RE.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente artigos legais, jurisprudência ou doutrina que não existam.
2. Fundamente SEMPRE nos artigos corretos do CPC/2015 (arts. 994-1044) e CF/88.
3. Para REsp: arts. 1029-1035 CPC/2015 + CF/88, art. 105, III.
4. Para RE: arts. 1029-1035 CPC/2015 + CF/88, art. 102, III. EXIJA repercussão geral.
5. Para todos os recursos: demonstre tempestividade, preparo (se aplicável) e legitimidade.
6. Jurisprudência dos tribunais superiores: marque [VERIFICAR: tema + tribunal] para conferência.
7. Use linguagem jurídica formal, técnica e objetiva.

ESTRUTURA RECURSAL:
- Demonstre os pressupostos de admissibilidade (tempestividade, interesse, legitimidade, preparo)
- Razões do recurso: específicas, impugnando ponto a ponto os fundamentos da decisão recorrida
- Pedido: conhecimento e provimento com efeito pretendido

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_CONSTITUCIONAL = """Você é um advogado constitucionalista especialista em remédios constitucionais: habeas corpus, mandado de segurança e tutelas de urgência no Brasil.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente dispositivos constitucionais, súmulas ou precedentes vinculantes.
2. Habeas Corpus: fundamente em CF/88, art. 5º, LXVIII; CPP, arts. 647-667.
3. Mandado de Segurança: fundamente em CF/88, art. 5º, LXIX; Lei 12.016/2009.
4. Tutela Urgência: fundamente em CPC/2015, arts. 294-311 (fumus boni iuris + periculum in mora).
5. Para HC: demonstre ilegalidade ou abuso de poder que afeta a liberdade de locomoção.
6. Para MS: demonstre direito líquido e certo violado por ato de autoridade.
7. Precedentes do STF/STJ: use súmulas consolidadas. Acórdãos: [VERIFICAR: número/tema].

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_TRABALHISTA = """Você é um advogado trabalhista especialista em Justiça do Trabalho, CLT, jurisprudência do TST e TRTs.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente Orientações Jurisprudenciais (OJs), Súmulas do TST ou artigos da CLT que não existam.
2. Cite corretamente: CLT (Decreto-Lei 5.452/1943), Lei 13.467/2017 (Reforma Trabalhista), CF/88, art. 7º.
3. Súmulas e OJs do TST: cite apenas as consolidadas. Para dúvidas: [VERIFICAR SÚMULA TST: tema].
4. Verbas rescisórias: calcule com base nas regras corretas da CLT pós-Reforma de 2017.
5. Prazo de prescrição: bienal (pós-extinção) e quinquenal (durante o contrato) — art. 7º, XXIX, CF/88.
6. Use linguagem jurídica formal adequada ao processo do trabalho.

COMPETÊNCIA MATERIAL:
- Justiça do Trabalho: CF/88, art. 114; CLT; Súmulas TST; OJs SBDI-1 e SBDI-2

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_CRIMINAL = """Você é um advogado criminalista especialista em processo penal e direito penal brasileiro.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente tipos penais, artigos do CP/CPP ou jurisprudência criminal que não existam.
2. Fundamente no Código Penal (Decreto-Lei 2.848/1940), CPP (Decreto-Lei 3.689/1941) e CF/88.
3. Princípios: in dubio pro reo, presunção de inocência (CF/88, art. 5º, LVII), ampla defesa.
4. Jurisprudência: STF e STJ. Use apenas súmulas consolidadas. Acórdãos: [VERIFICAR: tema/tribunal].
5. Na defesa: explore atipicidade, excludentes de ilicitude (CP arts. 23-25), culpabilidade, prescrição.
6. Prova: impugne provas obtidas por meios ilícitos (CF/88, art. 5º, LVI; CPP art. 157).
7. Use linguagem jurídica formal do processo penal.

GARANTIAS FUNDAMENTAIS:
- CF/88, art. 5º, XXXVIII (júri), LIII (juiz natural), LIV (devido processo legal), LV (contraditório)

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_EXTRAJUDICIAL = """Você é um advogado especialista em documentos jurídicos extrajudiciais: contratos, notificações, pareceres e procurações conforme o Código Civil brasileiro.

REGRAS ABSOLUTAS — NUNCA VIOLE:
1. NUNCA invente dispositivos do CC/2002, leis ou cláusulas contratuais padrão que não existam.
2. Fundamente em: CC/2002 (Lei 10.406/2002), CLT (para contratos de trabalho), CPC/2015, CF/88.
3. Contratos: observe função social (CC art. 421), boa-fé objetiva (CC art. 422), teoria da imprevisão.
4. Notificações: forma correta de constituição em mora (CC arts. 394-401).
5. Pareceres: opinião fundamentada, indicando limitações e ressalvas de forma clara.
6. Procurações: poderes especiais exigem outorga expressa (CC art. 661, §1º).
7. Use linguagem clara, técnica e precisa. Contratos: cláusulas numeradas e objetivas.

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é um revisor jurídico especializado em análise de peças processuais brasileiras.

Sua função é VALIDAR o conteúdo jurídico gerado avaliando:
1. LINGUAGEM: formal, culta, em português brasileiro. Adequada ao padrão forense.
2. EMBASAMENTO LEGAL: artigos citados existem e estão corretos. Legislação vigente.
3. COERÊNCIA: argumentos lógicos, não contraditórios, adequados ao tipo de peça.
4. COMPLETUDE: seção cobre os elementos necessários para sua função processual.
5. PROIBIÇÕES: não contém jurisprudência inventada, artigos inexistentes ou dados fabricados.

Retorne SEMPRE JSON neste formato:
{"valid": true/false, "score": 0-100, "feedback": ["observação1", "observação2"]}

Score: 90-100 (excelente), 70-89 (bom com ajustes menores), 50-69 (requer revisão), <50 (rejeitar)."""

# Mapeamento: código do tipo de documento → chave do agente especializado
AGENTE_POR_TIPO = {
    # CÍVEL
    'peticao_inicial': 'gerador_civel',
    'contestacao': 'gerador_civel',
    'acao_execucao': 'gerador_civel',
    'embargos_execucao': 'gerador_civel',
    'impugnacao_cumprimento': 'gerador_civel',
    'excecao_pre_executividade': 'gerador_civel',
    'tutela_urgencia': 'gerador_constitucional',
    # RECURSOS
    'apelacao': 'gerador_recursal',
    'agravo_instrumento': 'gerador_recursal',
    'agravo_interno': 'gerador_recursal',
    'embargos_declaracao': 'gerador_recursal',
    'contrarrazoes_apelacao': 'gerador_recursal',
    'recurso_especial': 'gerador_recursal',
    'recurso_extraordinario': 'gerador_recursal',
    # CONSTITUCIONAL
    'habeas_corpus': 'gerador_constitucional',
    'mandado_seguranca': 'gerador_constitucional',
    # TRABALHISTA
    'reclamacao_trabalhista': 'gerador_trabalhista',
    'contestacao_trabalhista': 'gerador_trabalhista',
    'contrato_trabalho': 'gerador_trabalhista',
    # CRIMINAL
    'queixa_crime': 'gerador_criminal',
    'alegacoes_finais_criminais': 'gerador_criminal',
    # EXTRAJUDICIAL
    'notificacao_extrajudicial': 'gerador_extrajudicial',
    'parecer_juridico': 'gerador_extrajudicial',
    'contrato_particular': 'gerador_extrajudicial',
    'procuracao': 'gerador_extrajudicial',
    # NOVOS BLUEPRINTS PRIORIDADE 1
    'reconvencao': 'gerador_civel',
    'divorcio_litigioso': 'gerador_familia',
    'execucao_alimentos': 'gerador_familia',
    'exoneracao_alimentos': 'gerador_familia',
    'acao_consignacao_trabalhista': 'gerador_trabalhista',
    'agravo_peticao': 'gerador_trabalhista',
    'acao_indenizacao_consumidor': 'gerador_consumidor',
    'revisao_beneficio_previdenciario': 'gerador_previdenciario',
    'recurso_administrativo_inss': 'gerador_previdenciario',
    'defesa_preliminar_criminal': 'gerador_criminal',
    # FAMÍLIA E SUCESSÕES (re-mapeados)
    'acao_alimentos': 'gerador_familia',
    'divorcio_consensual': 'gerador_familia',
    'revisional_alimentos': 'gerador_familia',
    'regulamentacao_guarda': 'gerador_familia',
    'inventario_judicial': 'gerador_familia',
    'inventario_extrajudicial': 'gerador_familia',
    # CONSUMIDOR (re-mapeados)
    'reclamacao_consumerista': 'gerador_consumidor',
    # PREVIDENCIÁRIO (re-mapeados)
    'peticao_inicial_previdenciaria': 'gerador_previdenciario',
    'bpc_loas': 'gerador_previdenciario',
    'aposentadoria_especial': 'gerador_previdenciario',
    # LGPD / DIREITO DIGITAL (re-mapeados)
    'politica_privacidade_lgpd': 'gerador_digital_lgpd',
    'termo_uso_plataforma': 'gerador_digital_lgpd',
    'dpa_tratamento_dados': 'gerador_digital_lgpd',
    'resposta_titular_dados': 'gerador_digital_lgpd',
    'notificacao_incidente_lgpd': 'gerador_digital_lgpd',
}

BLUEPRINTS_DATA = [
    # ──────────────────────────────────────────────────────────────────────
    # 1. PETIÇÃO INICIAL CÍVEL
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'peticao_inicial',
        'name': 'Petição Inicial Cível - CPC/2015',
        'description': 'Blueprint completo para petições iniciais cíveis conforme CPC/2015',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 319-331',
        'primary_color': '#7030A0',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Petição Inicial',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Identificação do juízo competente',
                'instructions': 'Gere o endereçamento ao juízo competente identificando comarca, vara e natureza da ação. Inclua identificação completa do autor e réu.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca / Seção Judiciária', 'type': 'text', 'required': True},
                    {'name': 'vara', 'label': 'Vara / Juízo', 'type': 'text', 'required': False},
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'autor_qualificacao', 'label': 'Qualificação do Autor (nacionalidade, estado civil, profissão, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu', 'type': 'text', 'required': True},
                    {'name': 'reu_qualificacao', 'label': 'Qualificação do Réu', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos',
                'name': 'I - Dos Fatos',
                'description': 'Narração clara e objetiva dos fatos que embasam a demanda',
                'instructions': 'Narre os fatos de forma cronológica, clara e objetiva. Evite repetições. Destaque os fatos juridicamente relevantes para a causa.',
                'fields': [
                    {'name': 'fatos_cronologia', 'label': 'Cronologia dos Fatos', 'type': 'textarea', 'required': True},
                    {'name': 'documentos_referenciados', 'label': 'Documentos que embasam os fatos', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'direito',
                'name': 'II - Do Direito',
                'description': 'Fundamentação jurídica da pretensão',
                'instructions': 'Apresente a fundamentação jurídica com base na legislação, doutrina e jurisprudência aplicáveis. Cite artigos específicos do CPC/2015, CC/2002 ou legislação especial conforme o caso.',
                'fields': [
                    {'name': 'natureza_acao', 'label': 'Natureza da Ação (ex: indenizatória, declaratória, condenatória)', 'type': 'text', 'required': True},
                    {'name': 'legislacao_aplicavel', 'label': 'Legislação Aplicável', 'type': 'textarea', 'required': False},
                    {'name': 'tese_juridica', 'label': 'Tese Jurídica Principal', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'danos',
                'name': 'III - Dos Danos e Pedidos',
                'description': 'Especificação dos danos sofridos e quantificação dos pedidos',
                'instructions': 'Descreva os danos materiais e/ou morais sofridos. Quantifique quando possível. Apresente os pedidos de forma clara, certa e determinada, conforme exige o art. 322 do CPC/2015.',
                'fields': [
                    {'name': 'tipo_dano', 'label': 'Tipo de Dano (material, moral, estético, etc.)', 'type': 'text', 'required': True},
                    {'name': 'valor_danos_materiais', 'label': 'Valor dos Danos Materiais (R$)', 'type': 'text', 'required': False},
                    {'name': 'valor_danos_morais', 'label': 'Valor dos Danos Morais Pleiteados (R$)', 'type': 'text', 'required': False},
                    {'name': 'descricao_danos', 'label': 'Descrição Detalhada dos Danos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'provas',
                'name': 'IV - Das Provas',
                'description': 'Rol de provas que pretende produzir',
                'instructions': 'Liste as provas que pretende produzir: documentais já juntadas, testemunhais, periciais, etc. Fundamente na necessidade de cada prova para o julgamento do mérito.',
                'fields': [
                    {'name': 'provas_documentais', 'label': 'Provas Documentais Juntadas', 'type': 'textarea', 'required': False},
                    {'name': 'provas_testemunhais', 'label': 'Testemunhas (nomes e endereços)', 'type': 'textarea', 'required': False},
                    {'name': 'prova_pericial', 'label': 'Necessita de Prova Pericial? Qual?', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedidos',
                'name': 'V - Dos Pedidos',
                'description': 'Pedidos finais cumulados ou alternativos',
                'instructions': 'Formule os pedidos de forma precisa, certa e determinada. Inclua: condenação, declaração, constituição, tutela provisória se cabível, condenação em honorários e custas.',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'textarea', 'required': True},
                    {'name': 'pedidos_acessorios', 'label': 'Pedidos Acessórios (juros, correção, honorários)', 'type': 'textarea', 'required': False},
                    {'name': 'tutela_urgencia', 'label': 'Pedido de Tutela de Urgência?', 'type': 'select', 'required': False, 'options': ['Não', 'Sim - tutela antecipada', 'Sim - tutela cautelar']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 2. CONTESTAÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'contestacao',
        'name': 'Contestação Cível - CPC/2015',
        'description': 'Blueprint completo para contestações cíveis conforme CPC/2015',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 335-342',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Contestação',
        'sections': [
            {
                'number': 1, 'key': 'preliminares',
                'name': 'I - Das Preliminares',
                'description': 'Defesas processuais preliminares (art. 337 CPC)',
                'instructions': 'Analise e apresente as preliminares aplicáveis ao caso: incompetência, inépcia da inicial, falta de interesse de agir, ilegitimidade, litispendência, coisa julgada, etc. Fundamente cada preliminar no art. 337 do CPC/2015.',
                'fields': [
                    {'name': 'preliminares_cabíveis', 'label': 'Preliminares a Arguir', 'type': 'textarea', 'required': False},
                    {'name': 'competencia_juizo', 'label': 'O juízo é competente?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não - indicar o competente']},
                ],
            },
            {
                'number': 2, 'key': 'impugnacao_fatos',
                'name': 'II - Da Impugnação Específica dos Fatos',
                'description': 'Refutação específica dos fatos narrados na inicial',
                'instructions': 'Impugne especificamente cada fato narrado na petição inicial. O ônus da impugnação específica é do réu (art. 341 CPC). Fatos não impugnados presumem-se verdadeiros.',
                'fields': [
                    {'name': 'fatos_inicialresumo', 'label': 'Resumo dos Fatos da Inicial', 'type': 'textarea', 'required': True},
                    {'name': 'fatos_verdadeiros', 'label': 'Quais fatos são verdadeiros?', 'type': 'textarea', 'required': False},
                    {'name': 'fatos_falsos', 'label': 'Quais fatos são falsos/impugnados?', 'type': 'textarea', 'required': True},
                    {'name': 'versao_reu', 'label': 'Versão dos Fatos segundo o Réu', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'merito',
                'name': 'III - Do Mérito',
                'description': 'Defesa de mérito - fundamentos jurídicos da contestação',
                'instructions': 'Apresente a defesa de mérito com fundamentos legais, doutrinários e jurisprudenciais. Refute a tese jurídica do autor. Cite artigos, súmulas e precedentes aplicáveis.',
                'fields': [
                    {'name': 'tese_defesa', 'label': 'Tese Central da Defesa', 'type': 'textarea', 'required': True},
                    {'name': 'legislacao_defesa', 'label': 'Legislação que embasa a defesa', 'type': 'textarea', 'required': False},
                    {'name': 'ausencia_dano', 'label': 'Há dano efetivo? Argumente', 'type': 'textarea', 'required': False},
                    {'name': 'nexo_causal', 'label': 'Há nexo de causalidade? Argumente', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'provas_pedidos',
                'name': 'IV - Das Provas e Pedidos',
                'description': 'Rol de provas e pedido de improcedência',
                'instructions': 'Liste as provas que pretende produzir. Formule pedido de total improcedência da ação, condenação do autor em honorários e demais verbas de sucumbência.',
                'fields': [
                    {'name': 'provas_reu', 'label': 'Provas que o Réu pretende produzir', 'type': 'textarea', 'required': False},
                    {'name': 'honorarios_pleiteados', 'label': 'Percentual de honorários pleiteados (%)', 'type': 'text', 'required': False},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 3. APELAÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'apelacao',
        'name': 'Apelação - CPC/2015',
        'description': 'Blueprint para recursos de apelação contra sentença de primeiro grau',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 1009-1014',
        'primary_color': '#7C3AED',
        'secondary_color': '#A78BFA',
        'cover_title': 'Razões de Apelação',
        'sections': [
            {
                'number': 1, 'key': 'cabimento',
                'name': 'I - Do Cabimento e Tempestividade',
                'description': 'Demonstração do cabimento e tempestividade do recurso',
                'instructions': 'Demonstre o cabimento da apelação (art. 1009 CPC), a tempestividade do recurso (prazo de 15 dias úteis) e o preparo quando exigível.',
                'fields': [
                    {'name': 'data_sentenca', 'label': 'Data da Sentença / Publicação', 'type': 'date', 'required': True},
                    {'name': 'data_interposicao', 'label': 'Data de Interposição do Recurso', 'type': 'date', 'required': True},
                    {'name': 'tipo_sentenca', 'label': 'Tipo de Sentença Impugnada', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'relatorio',
                'name': 'II - Breve Relatório',
                'description': 'Síntese do processo e da sentença recorrida',
                'instructions': 'Apresente um breve relato do processo: partes, natureza da ação, pedidos formulados, decisão recorrida e seus fundamentos.',
                'fields': [
                    {'name': 'resumo_processo', 'label': 'Resumo do Processo', 'type': 'textarea', 'required': True},
                    {'name': 'decisao_recorrida', 'label': 'Decisão Recorrida (síntese)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'razoes',
                'name': 'III - Das Razões do Recurso',
                'description': 'Fundamentação jurídica do recurso com indicação do error in judicando ou in procedendo',
                'instructions': 'Apresente as razões do recurso indicando com precisão: (a) error in judicando - equívoco na aplicação do direito material; e/ou (b) error in procedendo - violação a normas processuais. Cite os artigos violados e como deveriam ter sido aplicados.',
                'fields': [
                    {'name': 'tipo_erro', 'label': 'Tipo de Error (in judicando / in procedendo / ambos)', 'type': 'text', 'required': True},
                    {'name': 'normas_violadas', 'label': 'Normas Violadas pela Sentença', 'type': 'textarea', 'required': True},
                    {'name': 'tese_recursal', 'label': 'Tese Recursal Principal', 'type': 'textarea', 'required': True},
                    {'name': 'jurisprudencia', 'label': 'Jurisprudência Favorável (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'pedido_recursal',
                'name': 'IV - Do Pedido',
                'description': 'Pedido recursal e efeito suspensivo',
                'instructions': 'Formule o pedido recursal: reforma total ou parcial da sentença, com especificação do novo julgamento pretendido. Requeira o recebimento no efeito suspensivo quando cabível.',
                'fields': [
                    {'name': 'pedido_reforma', 'label': 'Reforma Total ou Parcial?', 'type': 'select', 'required': True, 'options': ['Total', 'Parcial - especificar']},
                    {'name': 'novo_julgamento', 'label': 'Como deve ser julgada a causa em novo exame?', 'type': 'textarea', 'required': True},
                    {'name': 'efeito_suspensivo', 'label': 'Requer efeito suspensivo?', 'type': 'select', 'required': False, 'options': ['Não', 'Sim']},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 4. AGRAVO DE INSTRUMENTO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'agravo_instrumento',
        'name': 'Agravo de Instrumento - CPC/2015',
        'description': 'Blueprint para agravo de instrumento contra decisões interlocutórias',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 1015-1020',
        'primary_color': '#7C3AED',
        'secondary_color': '#A78BFA',
        'cover_title': 'Agravo de Instrumento',
        'sections': [
            {
                'number': 1, 'key': 'cabimento_hipoteses',
                'name': 'I - Do Cabimento',
                'description': 'Demonstração da hipótese legal de cabimento',
                'instructions': 'Identifique a hipótese legal de cabimento do agravo de instrumento prevista no art. 1.015 do CPC/2015 ou em lei especial. Demonstre a tempestividade (15 dias úteis).',
                'fields': [
                    {'name': 'hipotese_art1015', 'label': 'Hipótese do art. 1015 CPC aplicável', 'type': 'text', 'required': True},
                    {'name': 'decisao_agravada', 'label': 'Decisão Agravada (transcrição ou síntese)', 'type': 'textarea', 'required': True},
                    {'name': 'data_decisao', 'label': 'Data da Decisão Agravada', 'type': 'date', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'razoes_agravo',
                'name': 'II - Das Razões',
                'description': 'Fundamentação da ilegalidade ou equívoco da decisão agravada',
                'instructions': 'Demonstre a ilegalidade, inconstitucionalidade ou equívoco da decisão interlocutória agravada. Cite a lei violada e a correta interpretação.',
                'fields': [
                    {'name': 'vicio_decisao', 'label': 'Vício da Decisão Agravada', 'type': 'textarea', 'required': True},
                    {'name': 'norma_violada', 'label': 'Norma Legal Violada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedido_efeito',
                'name': 'III - Do Pedido e Efeito Suspensivo',
                'description': 'Requerimento de efeito suspensivo e pedido de reforma',
                'instructions': 'Requeira o efeito suspensivo ativo (art. 1019, I CPC) demonstrando o risco ao resultado útil do processo e a plausibilidade do direito. Formule o pedido de reforma da decisão.',
                'fields': [
                    {'name': 'urgencia_efeito', 'label': 'Fundamento para efeito suspensivo (perigo de dano)', 'type': 'textarea', 'required': False},
                    {'name': 'pedido_reforma_agravo', 'label': 'Como deve ser reformada a decisão?', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 5. EMBARGOS DE DECLARAÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'embargos_declaracao',
        'name': 'Embargos de Declaração - CPC/2015',
        'description': 'Blueprint para embargos de declaração contra qualquer decisão judicial',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 1022-1023',
        'primary_color': '#7C3AED',
        'secondary_color': '#A78BFA',
        'cover_title': 'Embargos de Declaração',
        'sections': [
            {
                'number': 1, 'key': 'vicio_apontado',
                'name': 'I - Do Vício Apontado',
                'description': 'Identificação precisa do vício: omissão, contradição, obscuridade ou erro material',
                'instructions': 'Identifique com precisão o vício da decisão embargada: (a) omissão - ponto não examinado; (b) contradição - premissas inconciliáveis; (c) obscuridade - passagem ininteligível; ou (d) erro material. Transcreva o trecho relevante da decisão.',
                'fields': [
                    {'name': 'tipo_vicio', 'label': 'Tipo de Vício', 'type': 'select', 'required': True, 'options': ['Omissão', 'Contradição', 'Obscuridade', 'Erro Material', 'Omissão + Contradição']},
                    {'name': 'trecho_decisao', 'label': 'Trecho da Decisão com o Vício', 'type': 'textarea', 'required': True},
                    {'name': 'ponto_omitido', 'label': 'Ponto Omitido ou Contraditório', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'pedido_embargo',
                'name': 'II - Do Pedido',
                'description': 'Pedido de saneamento do vício e efeito infringente se cabível',
                'instructions': 'Peça o acolhimento dos embargos para sanar o vício apontado. Se a correção do vício implicar mudança de resultado, requeira o efeito infringente com fundamentação.',
                'fields': [
                    {'name': 'efeito_infringente', 'label': 'Requer efeito infringente?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim - com fundamentação']},
                    {'name': 'resultado_pretendido', 'label': 'Resultado pretendido após saneamento', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 6. MANDADO DE SEGURANÇA
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'mandado_seguranca',
        'name': 'Mandado de Segurança - Lei 12.016/2009',
        'description': 'Blueprint para mandado de segurança individual contra ato de autoridade coatora',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 5º, LXIX; Lei 12.016/2009',
        'primary_color': '#2563EB',
        'secondary_color': '#60A5FA',
        'cover_title': 'Mandado de Segurança',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_partes_ms',
                'name': 'I - Das Partes e Competência',
                'description': 'Identificação do impetrante, impetrado e competência',
                'instructions': 'Qualifique o impetrante, identifique a autoridade coatora e o ente público. Fundamente a competência do juízo/tribunal para conhecer do writ.',
                'fields': [
                    {'name': 'impetrante', 'label': 'Impetrante (nome e qualificação completa)', 'type': 'textarea', 'required': True},
                    {'name': 'autoridade_coatora', 'label': 'Autoridade Coatora (cargo e órgão)', 'type': 'text', 'required': True},
                    {'name': 'ente_publico', 'label': 'Pessoa Jurídica de Direito Público', 'type': 'text', 'required': True},
                    {'name': 'competencia_ms', 'label': 'Fundamento da Competência', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'ato_coator',
                'name': 'II - Do Ato Coator e Direito Líquido e Certo',
                'description': 'Descrição do ato ilegal ou abusivo e do direito violado',
                'instructions': 'Descreva com precisão o ato coator: o que foi praticado ou omitido pela autoridade. Demonstre a ilegalidade ou abuso de poder. Comprove que o direito violado é líquido e certo - demonstrável de plano por prova documental.',
                'fields': [
                    {'name': 'descricao_ato_coator', 'label': 'Descrição do Ato Coator', 'type': 'textarea', 'required': True},
                    {'name': 'direito_violado', 'label': 'Direito Líquido e Certo Violado', 'type': 'textarea', 'required': True},
                    {'name': 'ilegalidade_fundamento', 'label': 'Fundamento da Ilegalidade / Abuso de Poder', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'liminar_pedido_ms',
                'name': 'III - Da Liminar e do Pedido',
                'description': 'Pedido de medida liminar e pedido final em mandado de segurança',
                'instructions': 'Requeira medida liminar demonstrando fumus boni iuris e periculum in mora (art. 7º, III da Lei 12.016/2009). Formule o pedido definitivo de concessão da segurança.',
                'fields': [
                    {'name': 'pedido_liminar', 'label': 'Pedido de Liminar (especificar o que deve ser suspenso/ordenado)', 'type': 'textarea', 'required': True},
                    {'name': 'fumus_boni_iuris', 'label': 'Fumus Boni Iuris', 'type': 'textarea', 'required': True},
                    {'name': 'periculum_mora', 'label': 'Periculum In Mora', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_definitivo_ms', 'label': 'Pedido Definitivo da Segurança', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 7. TUTELA DE URGÊNCIA
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'tutela_urgencia',
        'name': 'Tutela de Urgência / Antecipada - CPC/2015',
        'description': 'Blueprint para pedidos de tutela provisória de urgência ou evidência',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 294-311',
        'primary_color': '#EA580C',
        'secondary_color': '#FB923C',
        'cover_title': 'Tutela de Urgência',
        'sections': [
            {
                'number': 1, 'key': 'natureza_tutela',
                'name': 'I - Da Natureza e Fundamento da Tutela',
                'description': 'Tipo de tutela requerida e seu fundamento legal',
                'instructions': 'Identifique a natureza da tutela: antecipada satisfativa (art. 300), cautelar (art. 301) ou de evidência (art. 311). Apresente o fundamento legal.',
                'fields': [
                    {'name': 'tipo_tutela', 'label': 'Tipo de Tutela', 'type': 'select', 'required': True, 'options': ['Tutela Antecipada (art. 300 CPC)', 'Tutela Cautelar (art. 301 CPC)', 'Tutela de Evidência (art. 311 CPC)']},
                    {'name': 'momento_pedido', 'label': 'Momento do Pedido', 'type': 'select', 'required': True, 'options': ['Antecedente - antes da ação principal', 'Incidental - na ação já em curso']},
                ],
            },
            {
                'number': 2, 'key': 'probabilidade_perigo',
                'name': 'II - Da Probabilidade do Direito e do Perigo de Dano',
                'description': 'Demonstração dos requisitos do art. 300 CPC',
                'instructions': 'Demonstre: (a) probabilidade do direito - verossimilhança das alegações com base em prova documental; e (b) perigo de dano ou risco ao resultado útil do processo - urgência concreta, irreversibilidade.',
                'fields': [
                    {'name': 'probabilidade_direito', 'label': 'Probabilidade do Direito (fumus boni iuris)', 'type': 'textarea', 'required': True},
                    {'name': 'perigo_dano', 'label': 'Perigo de Dano ou Risco ao Resultado Útil (periculum)', 'type': 'textarea', 'required': True},
                    {'name': 'irreversibilidade', 'label': 'O dano é irreversível? Explique', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedido_tutela',
                'name': 'III - Do Pedido',
                'description': 'Pedido específico da tutela e prazo',
                'instructions': 'Formule o pedido da tutela de forma precisa: o que deve ser feito, proibido ou assegurado, em que prazo e sob qual sanção (multa diária se obrigação de fazer).',
                'fields': [
                    {'name': 'pedido_tutela_especifico', 'label': 'Pedido Específico da Tutela', 'type': 'textarea', 'required': True},
                    {'name': 'multa_diaria', 'label': 'Astreinte / Multa Diária (R$)', 'type': 'text', 'required': False},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 8. NOTIFICAÇÃO EXTRAJUDICIAL
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'notificacao_extrajudicial',
        'name': 'Notificação Extrajudicial',
        'description': 'Blueprint para notificações extrajudiciais com efeito jurídico formal',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 397, 408; CPC/2015, art. 726',
        'primary_color': '#374151',
        'secondary_color': '#6B7280',
        'cover_title': 'Notificação Extrajudicial',
        'sections': [
            {
                'number': 1, 'key': 'identificacao_notificacao',
                'name': 'I - Identificação das Partes',
                'description': 'Identificação do notificante e do notificado',
                'instructions': 'Qualifique completamente o notificante e o notificado. Informe o objetivo da notificação.',
                'fields': [
                    {'name': 'notificante', 'label': 'Notificante (nome, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'notificado', 'label': 'Notificado (nome, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'finalidade', 'label': 'Finalidade da Notificação', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'conteudo_notificacao',
                'name': 'II - Do Teor da Notificação',
                'description': 'Conteúdo formal da notificação com os fatos e direito',
                'instructions': 'Narre os fatos que motivam a notificação. Indique o direito violado ou a obrigação descumprida. Fixe prazo para cumprimento e consequências do descumprimento.',
                'fields': [
                    {'name': 'fatos_notificacao', 'label': 'Fatos que motivam a notificação', 'type': 'textarea', 'required': True},
                    {'name': 'obrigacao_exigida', 'label': 'Obrigação exigida do notificado', 'type': 'textarea', 'required': True},
                    {'name': 'prazo_cumprimento', 'label': 'Prazo para cumprimento', 'type': 'text', 'required': True},
                    {'name': 'consequencias_descumprimento', 'label': 'Consequências do descumprimento', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 9. PARECER JURÍDICO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'parecer_juridico',
        'name': 'Parecer Jurídico',
        'description': 'Blueprint para pareceres jurídicos técnicos fundamentados',
        'version': '1.0',
        'legal_basis': 'Estatuto da OAB, Lei 8.906/1994',
        'primary_color': '#374151',
        'secondary_color': '#6B7280',
        'cover_title': 'Parecer Jurídico',
        'sections': [
            {
                'number': 1, 'key': 'consulta',
                'name': 'I - Da Consulta',
                'description': 'Síntese da questão jurídica submetida a parecer',
                'instructions': 'Descreva com precisão a questão ou situação fática submetida a exame. Identifique o consulente.',
                'fields': [
                    {'name': 'consulente', 'label': 'Consulente', 'type': 'text', 'required': True},
                    {'name': 'questao_juridica', 'label': 'Questão Jurídica Submetida', 'type': 'textarea', 'required': True},
                    {'name': 'fatos_relevantes', 'label': 'Fatos Relevantes Apresentados', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'analise_juridica',
                'name': 'II - Da Análise Jurídica',
                'description': 'Análise fundamentada da questão com doutrina e jurisprudência',
                'instructions': 'Analise a questão com base na legislação, doutrina e jurisprudência aplicáveis. Seja objetivo e técnico. Apresente posições doutrinárias e os tribunais superiores quando houver divergência.',
                'fields': [
                    {'name': 'legislacao_aplicavel', 'label': 'Legislação Aplicável', 'type': 'textarea', 'required': True},
                    {'name': 'posicao_doutrinaria', 'label': 'Posição Doutrinária', 'type': 'textarea', 'required': False},
                    {'name': 'jurisprudencia_dominante', 'label': 'Jurisprudência Dominante', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'conclusao_parecer',
                'name': 'III - Da Conclusão',
                'description': 'Conclusão técnica do parecer',
                'instructions': 'Apresente a conclusão do parecer de forma clara, objetiva e fundamentada. Responda diretamente à questão formulada.',
                'fields': [
                    {'name': 'conclusao', 'label': 'Conclusão do Parecer', 'type': 'textarea', 'required': True},
                    {'name': 'recomendacoes', 'label': 'Recomendações ao Consulente', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 10. RECLAMAÇÃO TRABALHISTA
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'reclamacao_trabalhista',
        'name': 'Reclamação Trabalhista - CLT',
        'description': 'Blueprint para reclamações trabalhistas perante a Justiça do Trabalho',
        'version': '1.0',
        'legal_basis': 'CLT, art. 840; CF/88, art. 7º; Lei 13.467/2017; IN TST 41/2018',
        'primary_color': '#0D9488',
        'secondary_color': '#2DD4BF',
        'cover_title': 'Reclamação Trabalhista',
        'sections': [
            {
                'number': 1, 'key': 'partes_trabalhista',
                'name': 'I - Das Partes',
                'description': 'Identificação do reclamante e reclamado',
                'instructions': 'Qualifique o reclamante e o reclamado. Para pessoa física: nome, CPF, CTPS, endereço. Para empresa: razão social, CNPJ, endereço. Informe o vínculo empregatício.',
                'fields': [
                    {'name': 'reclamante', 'label': 'Reclamante (nome completo, CPF, CTPS, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'reclamado', 'label': 'Reclamado (razão social, CNPJ, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'periodo_trabalho', 'label': 'Período de Trabalho (admissão e demissão)', 'type': 'text', 'required': True},
                    {'name': 'cargo_funcao', 'label': 'Cargo / Função exercida', 'type': 'text', 'required': True},
                    {'name': 'salario', 'label': 'Último salário (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos_trabalhista',
                'name': 'II - Dos Fatos',
                'description': 'Narração da relação de emprego e das irregularidades',
                'instructions': 'Narre a relação de emprego: início, funções, jornada, salário, modo de demissão. Descreva as verbas trabalhistas não pagas ou direitos violados.',
                'fields': [
                    {'name': 'descricao_relacao_emprego', 'label': 'Descrição da Relação de Emprego', 'type': 'textarea', 'required': True},
                    {'name': 'jornada_trabalho', 'label': 'Jornada de Trabalho', 'type': 'text', 'required': True},
                    {'name': 'tipo_demissao', 'label': 'Tipo de Demissão / Rescisão', 'type': 'select', 'required': True, 'options': ['Sem justa causa', 'Por justa causa', 'Pedido de demissão', 'Rescisão indireta', 'Demissão discriminatória', 'Término de contrato']},
                    {'name': 'verbas_nao_pagas', 'label': 'Verbas Trabalhistas Não Pagas', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos_trabalhista',
                'name': 'III - Dos Pedidos',
                'description': 'Pedidos trabalhistas com valores estimados',
                'instructions': 'Liste os pedidos trabalhistas com valores estimados: aviso prévio, 13º, férias + 1/3, FGTS + multa 40%, horas extras, adicional noturno, etc. Fundamente cada pedido na CLT e jurisprudência do TST.',
                'fields': [
                    {'name': 'lista_pedidos', 'label': 'Lista de Pedidos Trabalhistas e Valores', 'type': 'textarea', 'required': True},
                    {'name': 'valor_total_estimado', 'label': 'Valor Total Estimado da Causa (R$)', 'type': 'text', 'required': True},
                    {'name': 'pedido_tutela_trabalhista', 'label': 'Requer tutela de urgência?', 'type': 'select', 'required': False, 'options': ['Não', 'Sim - reintegração', 'Sim - depósito do FGTS']},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # CONTRATO DE TRABALHO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'contrato_trabalho',
        'name': 'Contrato de Trabalho - CLT',
        'description': 'Blueprint para contratos de emprego conforme CLT e Lei 13.467/2017',
        'version': '1.0',
        'legal_basis': 'CLT, arts. 442-456; CC/2002, arts. 421-480; Lei 13.467/2017',
        'primary_color': '#0D9488',
        'secondary_color': '#2DD4BF',
        'cover_title': 'Contrato de Trabalho',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_partes',
                'name': '1. Qualificação das Partes',
                'description': 'Identificação completa do empregador e do empregado',
                'instructions': 'Qualifique o empregador (razão social, CNPJ, endereço, representante legal) e o empregado (nome completo, CPF, RG, PIS/PASEP, endereço). Indique a data de início do contrato.',
                'fields': [
                    {'name': 'empregador', 'label': 'Empregador (razão social, CNPJ, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'representante_legal', 'label': 'Representante Legal do Empregador', 'type': 'text', 'required': True},
                    {'name': 'empregado', 'label': 'Empregado (nome completo, CPF, RG, PIS, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'data_inicio', 'label': 'Data de Início do Contrato', 'type': 'text', 'required': True},
                    {'name': 'tipo_contrato', 'label': 'Tipo de Contrato', 'type': 'select', 'required': True, 'options': ['Por prazo indeterminado', 'Por prazo determinado', 'Experiência (máx. 90 dias)', 'Trabalho intermitente']},
                ],
            },
            {
                'number': 2, 'key': 'cargo_funcao',
                'name': '2. Do Cargo e Função',
                'description': 'Descrição do cargo, função e local de trabalho',
                'instructions': 'Descreva o cargo, as atribuições e responsabilidades do empregado, o local de trabalho e a possibilidade de alteração mediante acordo.',
                'fields': [
                    {'name': 'cargo', 'label': 'Cargo / Função', 'type': 'text', 'required': True},
                    {'name': 'atribuicoes', 'label': 'Atribuições e Responsabilidades', 'type': 'textarea', 'required': True},
                    {'name': 'local_trabalho', 'label': 'Local de Trabalho', 'type': 'text', 'required': True},
                    {'name': 'modalidade', 'label': 'Modalidade de Trabalho', 'type': 'select', 'required': True, 'options': ['Presencial', 'Híbrido', 'Teletrabalho (Home Office)']},
                ],
            },
            {
                'number': 3, 'key': 'remuneracao_beneficios',
                'name': '3. Da Remuneração e Benefícios',
                'description': 'Salário, forma de pagamento e benefícios',
                'instructions': 'Especifique o salário base, a forma e periodicidade de pagamento, bem como os benefícios concedidos (vale-transporte, vale-refeição, plano de saúde, etc.).',
                'fields': [
                    {'name': 'salario_base', 'label': 'Salário Base (R$)', 'type': 'text', 'required': True},
                    {'name': 'forma_pagamento', 'label': 'Forma de Pagamento', 'type': 'select', 'required': True, 'options': ['Depósito bancário', 'PIX', 'Cheque']},
                    {'name': 'beneficios', 'label': 'Benefícios Concedidos', 'type': 'textarea', 'required': False},
                    {'name': 'comissoes_bonus', 'label': 'Comissões / Bônus (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'jornada_trabalho',
                'name': '4. Da Jornada de Trabalho',
                'description': 'Horário, jornada semanal e regime de horas extras',
                'instructions': 'Defina a jornada diária e semanal, o horário de trabalho, o intervalo intrajornada e o regime de horas extras, observando os limites da CLT e da Reforma Trabalhista.',
                'fields': [
                    {'name': 'jornada_diaria', 'label': 'Jornada Diária (horas)', 'type': 'text', 'required': True},
                    {'name': 'jornada_semanal', 'label': 'Jornada Semanal (horas)', 'type': 'text', 'required': True},
                    {'name': 'horario', 'label': 'Horário de Trabalho (entrada/saída/intervalos)', 'type': 'text', 'required': True},
                    {'name': 'banco_horas', 'label': 'Regime de Banco de Horas', 'type': 'select', 'required': False, 'options': ['Não adotado', 'Anual - acordo coletivo', 'Semestral - acordo individual escrito']},
                ],
            },
            {
                'number': 5, 'key': 'obrigacoes_empregado',
                'name': '5. Das Obrigações do Empregado',
                'description': 'Deveres, sigilo e conduta do empregado',
                'instructions': 'Liste as obrigações do empregado: sigilo de informações, conduta ética, uso de EPI, cumprimento de normas internas, proibição de atividades concorrentes, etc.',
                'fields': [
                    {'name': 'obrigacoes_gerais', 'label': 'Obrigações Gerais do Empregado', 'type': 'textarea', 'required': True},
                    {'name': 'clausula_sigilo', 'label': 'Cláusula de Sigilo / Confidencialidade', 'type': 'textarea', 'required': False},
                    {'name': 'nao_concorrencia', 'label': 'Cláusula de Não Concorrência (se aplicável)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'obrigacoes_empregador',
                'name': '6. Das Obrigações do Empregador',
                'description': 'Deveres do empregador perante o empregado',
                'instructions': 'Descreva as obrigações do empregador: pagamento em dia, recolhimento de FGTS e INSS, fornecimento de EPI, segurança do trabalho, vale-transporte, etc.',
                'fields': [
                    {'name': 'obrigacoes_empregador', 'label': 'Obrigações do Empregador', 'type': 'textarea', 'required': True},
                    {'name': 'fgts_inss', 'label': 'Recolhimento de FGTS e INSS', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 7, 'key': 'clausulas_gerais_rescisao',
                'name': '7. Das Cláusulas Gerais e Rescisão',
                'description': 'Aviso prévio, rescisão, foro e disposições finais',
                'instructions': 'Estabeleça as regras sobre aviso prévio, hipóteses de rescisão com e sem justa causa, foro competente para dirimir conflitos e demais disposições gerais.',
                'fields': [
                    {'name': 'aviso_previo', 'label': 'Regras de Aviso Prévio', 'type': 'textarea', 'required': False},
                    {'name': 'foro', 'label': 'Foro Competente (Vara do Trabalho da Comarca)', 'type': 'text', 'required': True},
                    {'name': 'disposicoes_finais', 'label': 'Disposições Finais / Observações', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # HABEAS CORPUS
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'habeas_corpus',
        'name': 'Habeas Corpus',
        'description': 'Blueprint para habeas corpus preventivo e liberatório conforme CF/88 e CPP',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 5º, LXVIII; CPP, arts. 647-667',
        'primary_color': '#DC2626',
        'secondary_color': '#F87171',
        'cover_title': 'Habeas Corpus',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento_qualificacao',
                'name': '1. Endereçamento e Qualificação',
                'description': 'Identificação do tribunal, paciente, impetrante e coator',
                'instructions': 'Enderece ao tribunal competente (TJ, TRF, STJ ou STF). Qualifique o paciente (nome, CPF, RG, endereço, situação prisional), o impetrante e a autoridade coatora.',
                'fields': [
                    {'name': 'tribunal', 'label': 'Tribunal Competente', 'type': 'select', 'required': True, 'options': ['Tribunal de Justiça Estadual (TJ)', 'Tribunal Regional Federal (TRF)', 'Superior Tribunal de Justiça (STJ)', 'Supremo Tribunal Federal (STF)']},
                    {'name': 'paciente', 'label': 'Paciente (nome completo, CPF, RG, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'impetrante', 'label': 'Impetrante / Advogado (nome e OAB)', 'type': 'text', 'required': True},
                    {'name': 'autoridade_coatora', 'label': 'Autoridade Coatora (cargo e nome)', 'type': 'text', 'required': True},
                    {'name': 'tipo_hc', 'label': 'Tipo de Habeas Corpus', 'type': 'select', 'required': True, 'options': ['Liberatório (para soltar preso)', 'Preventivo (salvo-conduto)', 'Trancamento de ação penal']},
                ],
            },
            {
                'number': 2, 'key': 'cabimento_legitimidade',
                'name': '2. Do Cabimento e Legitimidade',
                'description': 'Fundamento constitucional e legitimidade ativa/passiva',
                'instructions': 'Demonstre o cabimento do habeas corpus com base na CF/88 e no CPP. Indique a legitimidade ativa do impetrante e a competência do tribunal.',
                'fields': [
                    {'name': 'fundamento_cabimento', 'label': 'Fundamento do Cabimento (legal/constitucional)', 'type': 'textarea', 'required': True},
                    {'name': 'competencia', 'label': 'Justificativa da Competência do Tribunal', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'situacao_fato',
                'name': '3. Da Situação de Fato',
                'description': 'Narração dos fatos que motivam o habeas corpus',
                'instructions': 'Narre de forma clara e objetiva os fatos: a prisão ou ameaça à liberdade do paciente, a data, o motivo alegado pela autoridade e a situação processual atual.',
                'fields': [
                    {'name': 'narracao_fatos', 'label': 'Narração dos Fatos', 'type': 'textarea', 'required': True},
                    {'name': 'situacao_prisional', 'label': 'Situação Prisional Atual (se preso)', 'type': 'select', 'required': False, 'options': ['Em liberdade (HC preventivo)', 'Preso preventivamente', 'Preso em flagrante', 'Preso temporariamente', 'Cumprindo pena']},
                    {'name': 'processo_criminal', 'label': 'Número do Processo / Inquérito (se houver)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'ilegalidade_abuso_poder',
                'name': '4. Da Ilegalidade ou Abuso de Poder',
                'description': 'Demonstração da ilegalidade do constrangimento à liberdade',
                'instructions': 'Demonstre a ilegalidade ou abuso de poder da autoridade coatora: ausência dos requisitos da prisão preventiva, falta de fundamentação, excesso de prazo, ilicitude da prova, etc.',
                'fields': [
                    {'name': 'ilegalidade', 'label': 'Demonstração da Ilegalidade / Abuso de Poder', 'type': 'textarea', 'required': True},
                    {'name': 'ausencia_requisitos', 'label': 'Ausência dos Requisitos Legais da Prisão', 'type': 'textarea', 'required': False},
                    {'name': 'excesso_prazo', 'label': 'Excesso de Prazo (se aplicável)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'fundamentos_juridicos',
                'name': '5. Do Direito (Fundamentos Jurídicos)',
                'description': 'Embasamento legal e jurisprudencial',
                'instructions': 'Fundamente juridicamente o pedido citando a CF/88, o CPP, a legislação penal aplicável e a jurisprudência dos tribunais superiores (STF e STJ).',
                'fields': [
                    {'name': 'fundamentos_legais', 'label': 'Fundamentos Legais (CF/88, CPP, CP, etc.)', 'type': 'textarea', 'required': True},
                    {'name': 'jurisprudencia', 'label': 'Jurisprudência Aplicável (STF/STJ)', 'type': 'textarea', 'required': False},
                    {'name': 'principios', 'label': 'Princípios Constitucionais Invocados', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': '6. Do Pedido (Liminar e Mérito)',
                'description': 'Pedido de liminar e pedido final de mérito',
                'instructions': 'Formule o pedido de liminar inaudita altera pars para que seja expedido o alvará de soltura ou salvo-conduto, e o pedido de mérito para concessão definitiva do writ.',
                'fields': [
                    {'name': 'pedido_liminar', 'label': 'Pedido de Liminar', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_merito', 'label': 'Pedido de Mérito', 'type': 'textarea', 'required': True},
                    {'name': 'documentos_juntados', 'label': 'Documentos Juntados (relação)', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # CONTRARRAZÕES DE APELAÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'contrarrazoes_apelacao',
        'name': 'Contrarrazões de Apelação - CPC/2015',
        'description': 'Blueprint para contrarrazões de apelação conforme CPC/2015 arts. 1009-1014',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 1009-1014',
        'primary_color': '#D97706',
        'secondary_color': '#FCD34D',
        'cover_title': 'Contrarrazões de Apelação',
        'sections': [
            {'number': 1, 'key': 'preliminares', 'name': '1. Preliminares e Tempestividade', 'description': 'Tempestividade das contrarrazões e matérias preliminares', 'instructions': 'Demonstre a tempestividade das contrarrazões e refute eventuais preliminares levantadas pelo apelante.'},
            {'number': 2, 'key': 'dos_fatos', 'name': '2. Dos Fatos e da Sentença', 'description': 'Resumo dos fatos e acerto da sentença recorrida', 'instructions': 'Apresente os fatos favoráveis ao apelado e demonstre o acerto da sentença de primeiro grau.'},
            {'number': 3, 'key': 'do_direito', 'name': '3. Do Direito (Defesa da Sentença)', 'description': 'Fundamentos jurídicos que sustentam a manutenção da sentença', 'instructions': 'Fundamente juridicamente a manutenção da sentença recorrida, refutando ponto a ponto os argumentos do apelante.'},
            {'number': 4, 'key': 'pedido', 'name': '4. Do Pedido', 'description': 'Requerimento de não provimento do recurso', 'instructions': 'Requeira o não provimento do recurso e a manutenção integral da sentença recorrida.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # IMPUGNAÇÃO AO CUMPRIMENTO DE SENTENÇA
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'impugnacao_cumprimento',
        'name': 'Impugnação ao Cumprimento de Sentença - CPC/2015',
        'description': 'Blueprint para impugnação ao cumprimento de sentença conforme CPC/2015 arts. 525-527',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 525-527',
        'primary_color': '#D97706',
        'secondary_color': '#FCD34D',
        'cover_title': 'Impugnação ao Cumprimento de Sentença',
        'sections': [
            {'number': 1, 'key': 'cabimento', 'name': '1. Do Cabimento e Tempestividade', 'description': 'Demonstração do cabimento e tempestividade da impugnação', 'instructions': 'Demonstre o cabimento da impugnação (CPC art. 525, §1º) e sua tempestividade dentro do prazo de 15 dias.'},
            {'number': 2, 'key': 'fundamentos', 'name': '2. Dos Fundamentos da Impugnação', 'description': 'Matérias arguíveis na impugnação (excesso de execução, nulidade, etc.)', 'instructions': 'Apresente os fundamentos da impugnação conforme CPC art. 525, §1º: falta ou nulidade de citação, ilegitimidade da parte, inexequibilidade do título, excesso de execução, incompetência do juízo ou nulidade da sentença.'},
            {'number': 3, 'key': 'efeito_suspensivo', 'name': '3. Do Efeito Suspensivo (se cabível)', 'description': 'Pedido de efeito suspensivo quando houver risco de dano grave', 'instructions': 'Se cabível, requeira efeito suspensivo demonstrando os requisitos do CPC art. 525, §6º: relevância da arguição e risco de dano grave de difícil ou incerta reparação.'},
            {'number': 4, 'key': 'pedido', 'name': '4. Do Pedido', 'description': 'Requerimento de acolhimento da impugnação', 'instructions': 'Requeira o acolhimento da impugnação e a extinção ou redução da execução conforme fundamentos apresentados.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # EXCEÇÃO DE PRÉ-EXECUTIVIDADE
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'excecao_pre_executividade',
        'name': 'Exceção de Pré-Executividade',
        'description': 'Blueprint para exceção de pré-executividade conforme construção jurisprudencial',
        'version': '1.0',
        'legal_basis': 'Construção jurisprudencial; STJ Súmula 393; CPC/2015',
        'primary_color': '#D97706',
        'secondary_color': '#FCD34D',
        'cover_title': 'Exceção de Pré-Executividade',
        'sections': [
            {'number': 1, 'key': 'cabimento', 'name': '1. Do Cabimento', 'description': 'Demonstração do cabimento da exceção de pré-executividade', 'instructions': 'Demonstre o cabimento da exceção de pré-executividade, que é cabível quando a matéria é de ordem pública e cognoscível de ofício, independente de penhora prévia.'},
            {'number': 2, 'key': 'materia', 'name': '2. Da Matéria Arguida', 'description': 'Matéria de ordem pública que fundamenta a exceção', 'instructions': 'Apresente a matéria de ordem pública que fundamenta a exceção: prescrição, ilegitimidade passiva, nulidade do título, excesso de execução, etc.'},
            {'number': 3, 'key': 'pedido', 'name': '3. Do Pedido', 'description': 'Requerimento de extinção ou redução da execução', 'instructions': 'Requeira o acolhimento da exceção com extinção ou redução da execução, além de condenação em honorários advocatícios do exequente.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # AGRAVO INTERNO / REGIMENTAL
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'agravo_interno',
        'name': 'Agravo Interno / Regimental - CPC/2015',
        'description': 'Blueprint para agravo interno/regimental conforme CPC/2015 arts. 1021-1022',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 1021-1022; Regimentos internos dos tribunais',
        'primary_color': '#7C3AED',
        'secondary_color': '#C4B5FD',
        'cover_title': 'Agravo Interno',
        'sections': [
            {'number': 1, 'key': 'cabimento', 'name': '1. Cabimento e Tempestividade', 'description': 'Demonstração do cabimento e tempestividade', 'instructions': 'Demonstre o cabimento do agravo interno (CPC art. 1021: contra decisão monocrática do relator) e sua tempestividade no prazo de 15 dias.'},
            {'number': 2, 'key': 'razoes', 'name': '2. Das Razões do Agravo', 'description': 'Fundamentos contra a decisão monocrática', 'instructions': 'Apresente os fundamentos pelos quais a decisão monocrática deve ser reformada ou cassada pelo colegiado. Indique o erro de julgamento ou violação de lei.'},
            {'number': 3, 'key': 'pedido', 'name': '3. Do Pedido', 'description': 'Requerimento de provimento do agravo', 'instructions': 'Requeira o conhecimento e provimento do agravo interno para que o colegiado decida a questão em substituição à decisão monocrática do relator.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # RECURSO ESPECIAL (REsp)
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'recurso_especial',
        'name': 'Recurso Especial (REsp) - STJ',
        'description': 'Blueprint para recurso especial ao STJ conforme CPC/2015 arts. 1029-1035',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 105, III; CPC/2015, arts. 1029-1035',
        'primary_color': '#7C3AED',
        'secondary_color': '#C4B5FD',
        'cover_title': 'Recurso Especial',
        'sections': [
            {'number': 1, 'key': 'cabimento_prequestionamento', 'name': '1. Cabimento e Prequestionamento', 'description': 'Demonstração do cabimento e do prequestionamento das questões federais', 'instructions': 'Demonstre o cabimento do REsp (violação à lei federal ou divergência jurisprudencial) e o prequestionamento das questões nas instâncias ordinárias.'},
            {'number': 2, 'key': 'violacao_lei_federal', 'name': '2. Da Violação à Lei Federal', 'description': 'Dispositivos legais violados e argumentação', 'instructions': 'Indique com precisão os dispositivos de lei federal violados (art. 105, III, "a" da CF/88) ou a divergência jurisprudencial (art. 105, III, "c"). Fundamente a violação com doutrina e jurisprudência do STJ.'},
            {'number': 3, 'key': 'do_pedido', 'name': '3. Do Pedido', 'description': 'Requerimento de admissão e provimento do REsp', 'instructions': 'Requeira o conhecimento e provimento do recurso especial para que o STJ aplique corretamente a lei federal ao caso concreto.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # RECURSO EXTRAORDINÁRIO (RE)
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'recurso_extraordinario',
        'name': 'Recurso Extraordinário (RE) - STF',
        'description': 'Blueprint para recurso extraordinário ao STF conforme CPC/2015 arts. 1029-1035',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 102, III; CPC/2015, arts. 1029-1035',
        'primary_color': '#7C3AED',
        'secondary_color': '#C4B5FD',
        'cover_title': 'Recurso Extraordinário',
        'sections': [
            {'number': 1, 'key': 'cabimento_repercussao', 'name': '1. Cabimento e Repercussão Geral', 'description': 'Demonstração do cabimento e da repercussão geral', 'instructions': 'Demonstre o cabimento do RE (violação à CF/88) e a repercussão geral da questão constitucional, indicando sua relevância jurídica, política, social ou econômica (CPC art. 1035).'},
            {'number': 2, 'key': 'violacao_constitucional', 'name': '2. Da Violação Constitucional', 'description': 'Dispositivos constitucionais violados e argumentação', 'instructions': 'Indique com precisão os dispositivos da CF/88 violados e fundamente a violação com doutrina constitucional e jurisprudência do STF.'},
            {'number': 3, 'key': 'pedido', 'name': '3. Do Pedido', 'description': 'Requerimento de admissão e provimento do RE', 'instructions': 'Requeira o conhecimento e provimento do recurso extraordinário para que o STF aplique corretamente a CF/88 ao caso concreto.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # EMBARGOS À EXECUÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'embargos_execucao',
        'name': 'Embargos à Execução - CPC/2015',
        'description': 'Blueprint para embargos à execução de título extrajudicial conforme CPC/2015 arts. 914-920',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 914-920',
        'primary_color': '#0891B2',
        'secondary_color': '#67E8F9',
        'cover_title': 'Embargos à Execução',
        'sections': [
            {'number': 1, 'key': 'tempestividade', 'name': '1. Tempestividade e Garantia do Juízo', 'description': 'Demonstração da tempestividade e da garantia do juízo', 'instructions': 'Demonstre a tempestividade dos embargos (prazo de 15 dias após a citação - CPC art. 915) e a garantia do juízo pela penhora de bens suficientes.', 'fields': [{'name': 'data_citacao', 'label': 'Data da Citação na Execução', 'type': 'text', 'required': True}]},
            {'number': 2, 'key': 'fundamentos', 'name': '2. Dos Fundamentos dos Embargos', 'description': 'Matérias arguíveis: inexigibilidade do título, excesso, prescrição, etc.', 'instructions': 'Apresente os fundamentos dos embargos conforme CPC art. 917: inexequibilidade do título, nulidade da execução, penhora incorreta, excesso de execução, prescrição ou decadência do crédito.'},
            {'number': 3, 'key': 'efeito_suspensivo', 'name': '3. Do Efeito Suspensivo (se cabível)', 'description': 'Pedido de suspensão da execução', 'instructions': 'Se cabível, requeira efeito suspensivo dos embargos demonstrando os requisitos: relevância da arguição e risco de dano grave (CPC art. 919, §1º).'},
            {'number': 4, 'key': 'pedido', 'name': '4. Do Pedido', 'description': 'Requerimento de acolhimento dos embargos', 'instructions': 'Requeira o recebimento dos embargos com efeito suspensivo, a procedência dos embargos e a extinção da execução, com condenação do exequente em honorários.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # AÇÃO DE EXECUÇÃO DE TÍTULO EXTRAJUDICIAL
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'acao_execucao',
        'name': 'Ação de Execução de Título Extrajudicial - CPC/2015',
        'description': 'Blueprint para ação de execução de título extrajudicial conforme CPC/2015 arts. 771-925',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 771-925; arts. 783-786',
        'primary_color': '#059669',
        'secondary_color': '#6EE7B7',
        'cover_title': 'Ação de Execução de Título Extrajudicial',
        'sections': [
            {'number': 1, 'key': 'qualificacao', 'name': '1. Qualificação das Partes e Juízo', 'description': 'Identificação das partes e do juízo competente', 'instructions': 'Qualifique o exequente e o executado. Indique o juízo competente conforme CPC art. 781.', 'fields': [{'name': 'exequente', 'label': 'Exequente (nome, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True}, {'name': 'executado', 'label': 'Executado (nome, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True}]},
            {'number': 2, 'key': 'titulo', 'name': '2. Do Título Executivo Extrajudicial', 'description': 'Descrição do título e demonstração de sua executividade', 'instructions': 'Descreva o título executivo extrajudicial (CPC art. 784), demonstre sua certeza, liquidez e exigibilidade conforme CPC art. 783.', 'fields': [{'name': 'tipo_titulo', 'label': 'Tipo do Título Executivo', 'type': 'select', 'required': True, 'options': ['Cheque', 'Nota promissória', 'Duplicata', 'Contrato assinado por 2 testemunhas', 'CDA (Certidão de Dívida Ativa)', 'Outro']}, {'name': 'valor_divida', 'label': 'Valor da Dívida (R$)', 'type': 'text', 'required': True}]},
            {'number': 3, 'key': 'pedido', 'name': '3. Dos Pedidos', 'description': 'Requerimentos de citação, penhora e satisfação do crédito', 'instructions': 'Requeira a citação do executado para pagar ou nomear bens à penhora, a expedição de mandado de penhora e avaliação, e a satisfação integral do crédito acrescido de juros, multa e honorários.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # CONTESTAÇÃO TRABALHISTA
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'contestacao_trabalhista',
        'name': 'Contestação Trabalhista - CLT',
        'description': 'Blueprint para contestação na Justiça do Trabalho conforme CLT e TST',
        'version': '1.0',
        'legal_basis': 'CLT, arts. 847-848; CPC/2015, art. 341 (subsidiário)',
        'primary_color': '#0D9488',
        'secondary_color': '#2DD4BF',
        'cover_title': 'Contestação Trabalhista',
        'sections': [
            {'number': 1, 'key': 'preliminares', 'name': '1. Preliminares', 'description': 'Matérias preliminares de defesa', 'instructions': 'Apresente matérias preliminares: incompetência em razão do lugar ou matéria, ilegitimidade de parte, prescrição (bienal e quinquenal), litispendência, coisa julgada.'},
            {'number': 2, 'key': 'impugnacao_fatos', 'name': '2. Da Impugnação dos Fatos', 'description': 'Impugnação específica dos pedidos da reclamação', 'instructions': 'Impugne especificamente cada pedido da reclamação trabalhista: horas extras, verbas rescisórias, FGTS, aviso prévio, etc. Negar fatos de forma especificada.'},
            {'number': 3, 'key': 'do_direito', 'name': '3. Do Direito', 'description': 'Fundamentos jurídicos da defesa', 'instructions': 'Apresente os fundamentos jurídicos da defesa com base na CLT, OJs e Súmulas do TST e TRT competente.'},
            {'number': 4, 'key': 'pedido', 'name': '4. Do Pedido', 'description': 'Requerimento de improcedência dos pedidos', 'instructions': 'Requeira a improcedência total dos pedidos da reclamação ou, alternativamente, redução dos valores pleiteados, com condenação do reclamante nos ônus de sucumbência.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # QUEIXA-CRIME / DENÚNCIA
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'queixa_crime',
        'name': 'Queixa-Crime / Denúncia',
        'description': 'Blueprint para peça acusatória em ação penal conforme CPP arts. 24-41',
        'version': '1.0',
        'legal_basis': 'CPP, arts. 24-41; CF/88, art. 5º, LIX; Lei 9.099/1995',
        'primary_color': '#B91C1C',
        'secondary_color': '#FCA5A5',
        'cover_title': 'Queixa-Crime',
        'sections': [
            {'number': 1, 'key': 'qualificacao', 'name': '1. Qualificação das Partes', 'description': 'Identificação do querelante/ofendido e do querelado/acusado', 'instructions': 'Qualifique o(a) querelante/ofendido(a) e o(a) querelado(a)/acusado(a). Indique o juízo criminal competente.', 'fields': [{'name': 'querelante', 'label': 'Querelante / Ofendido(a)', 'type': 'textarea', 'required': True}, {'name': 'querelado', 'label': 'Querelado(a) / Acusado(a)', 'type': 'textarea', 'required': True}]},
            {'number': 2, 'key': 'fatos', 'name': '2. Dos Fatos (Narratio Facti)', 'description': 'Descrição dos fatos delituosos de forma clara e circunstanciada', 'instructions': 'Descreva os fatos delituosos de forma clara, objetiva e circunstanciada, indicando lugar, tempo, modo e demais circunstâncias (CPP art. 41). Não omita elementos do tipo penal.'},
            {'number': 3, 'key': 'tipificacao', 'name': '3. Da Tipificação Penal', 'description': 'Enquadramento penal e demonstração dos elementos do tipo', 'instructions': 'Apresente a tipificação penal, demonstrando o preenchimento de todos os elementos do tipo objetivo e subjetivo. Cite jurisprudência dos tribunais superiores sobre o crime imputado.'},
            {'number': 4, 'key': 'pedido', 'name': '4. Do Pedido', 'description': 'Requerimento de recebimento da queixa e condenação', 'instructions': 'Requeira o recebimento da queixa-crime, a citação do querelado, a procedência da ação penal privada e a condenação nas sanções do tipo penal imputado.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # ALEGAÇÕES FINAIS CRIMINAIS
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'alegacoes_finais_criminais',
        'name': 'Alegações Finais Criminais',
        'description': 'Blueprint para memoriais finais no processo penal conforme CPP arts. 403-404',
        'version': '1.0',
        'legal_basis': 'CPP, arts. 403-404; 500',
        'primary_color': '#B91C1C',
        'secondary_color': '#FCA5A5',
        'cover_title': 'Alegações Finais Criminais',
        'sections': [
            {'number': 1, 'key': 'resumo_instrucao', 'name': '1. Resumo da Instrução Processual', 'description': 'Síntese das provas produzidas na instrução', 'instructions': 'Apresente um resumo objetivo das provas produzidas na instrução processual (testemunhas, documentos, perícias), destacando os elementos favoráveis à defesa.'},
            {'number': 2, 'key': 'analise_provas', 'name': '2. Da Análise das Provas', 'description': 'Análise crítica das provas e contradições da acusação', 'instructions': 'Analise criticamente as provas, demonstrando contradições no conjunto probatório da acusação e a insuficiência de provas para condenação. In dubio pro reo.'},
            {'number': 3, 'key': 'teses_defesa', 'name': '3. Das Teses da Defesa', 'description': 'Fundamentos jurídicos para absolvição ou atenuação da pena', 'instructions': 'Apresente as teses jurídicas da defesa: atipicidade, excludentes de ilicitude, de culpabilidade, prescrição, nulidades processuais, ou pedido alternativo de atenuação da pena.'},
            {'number': 4, 'key': 'pedido', 'name': '4. Do Pedido', 'description': 'Requerimento de absolvição ou atenuação de pena', 'instructions': 'Requeira a absolvição do(a) acusado(a) por insuficiência de provas (CPP art. 386, VII) ou, alternativamente, o reconhecimento das teses de defesa para redução da pena ao mínimo legal.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # CONTRATO PARTICULAR
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'contrato_particular',
        'name': 'Contrato Particular',
        'description': 'Blueprint para contratos civis entre particulares conforme CC/2002',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 421-480; 591-626',
        'primary_color': '#374151',
        'secondary_color': '#9CA3AF',
        'cover_title': 'Contrato Particular',
        'sections': [
            {'number': 1, 'key': 'qualificacao_partes', 'name': '1. Qualificação das Partes', 'description': 'Identificação completa das partes contratantes', 'instructions': 'Qualifique as partes contratantes: nome completo, CPF/CNPJ, estado civil, profissão e endereço completo de cada parte.', 'fields': [{'name': 'contratante', 'label': 'Contratante (nome, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True}, {'name': 'contratado', 'label': 'Contratado (nome, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True}, {'name': 'objeto_contrato', 'label': 'Objeto do Contrato', 'type': 'text', 'required': True}]},
            {'number': 2, 'key': 'objeto', 'name': '2. Do Objeto e Obrigações', 'description': 'Descrição detalhada do objeto e obrigações de cada parte', 'instructions': 'Descreva o objeto do contrato e as obrigações de fazer, não fazer ou dar de cada parte. Seja específico e objetivo para evitar ambiguidades.'},
            {'number': 3, 'key': 'valor_pagamento', 'name': '3. Do Valor e Forma de Pagamento', 'description': 'Preço, forma e condições de pagamento', 'instructions': 'Defina o valor total do contrato, a forma de pagamento (à vista, parcelado, transferência, PIX), prazos, juros e multa por inadimplência.', 'fields': [{'name': 'valor_total', 'label': 'Valor Total (R$)', 'type': 'text', 'required': True}, {'name': 'forma_pagamento', 'label': 'Forma e Condições de Pagamento', 'type': 'textarea', 'required': True}]},
            {'number': 4, 'key': 'prazo_rescisao', 'name': '4. Do Prazo e da Rescisão', 'description': 'Vigência do contrato e condições de rescisão', 'instructions': 'Estabeleça o prazo de vigência do contrato e as condições de rescisão: rescisão por mútuo acordo, rescisão por descumprimento, multa rescisória e prazo de aviso prévio.'},
            {'number': 5, 'key': 'clausulas_gerais', 'name': '5. Das Cláusulas Gerais', 'description': 'Disposições finais, foro e assinaturas', 'instructions': 'Inclua cláusulas gerais: eleição de foro, vedação de cessão de direitos sem anuência, reconhecimento de assinatura e validade jurídica do contrato.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # PROCURAÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'procuracao',
        'name': 'Procuração',
        'description': 'Blueprint para instrumento de mandato conforme CC/2002 arts. 653-692',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 653-692; CPC/2015, art. 105',
        'primary_color': '#374151',
        'secondary_color': '#9CA3AF',
        'cover_title': 'Procuração',
        'sections': [
            {'number': 1, 'key': 'qualificacao_outorgante', 'name': '1. Qualificação do(a) Outorgante', 'description': 'Identificação completa de quem confere os poderes', 'instructions': 'Qualifique o(a) outorgante com todos os dados: nome completo, estado civil, profissão, CPF, RG (número e órgão expedidor), endereço completo.', 'fields': [{'name': 'outorgante', 'label': 'Outorgante (nome, estado civil, profissão, CPF, RG, endereço)', 'type': 'textarea', 'required': True}]},
            {'number': 2, 'key': 'qualificacao_outorgado', 'name': '2. Qualificação do(a) Outorgado(a)', 'description': 'Identificação do(a) advogado(a) ou procurador(a)', 'instructions': 'Qualifique o(a) outorgado(a): nome completo, CPF, OAB (número e seccional) se advogado(a), endereço profissional.', 'fields': [{'name': 'outorgado', 'label': 'Outorgado(a) (nome, CPF, OAB, endereço)', 'type': 'textarea', 'required': True}]},
            {'number': 3, 'key': 'poderes', 'name': '3. Dos Poderes Conferidos', 'description': 'Especificação dos poderes outorgados', 'instructions': 'Especifique os poderes conferidos: poderes da cláusula "ad judicia" (representar em juízo), poderes especiais (receber citação, confessar, desistir, transigir, firmar acordos), poderes "ad negotia" (extrajudiciais). Seja específico para evitar impugnação.'},
            {'number': 4, 'key': 'vigencia', 'name': '4. Da Vigência e Foro', 'description': 'Prazo de validade e foro', 'instructions': 'Indique o prazo de validade da procuração (se determinado) ou informe que é por prazo indeterminado. Indique a cidade, data e o foro competente.'},
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 10. RECONVENÇÃO (CÍVEL) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'reconvencao',
        'name': 'Reconvenção - CPC/2015',
        'description': 'Blueprint para reconvenção apresentada pelo réu contra o autor no mesmo processo',
        'version': '1.0',
        'legal_basis': 'CPC/2015, art. 343',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Reconvenção',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento_reconvencao',
                'name': 'I - Endereçamento e Qualificação das Partes',
                'description': 'Endereçamento ao juízo da ação principal e qualificação do reconvinte e reconvindo',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece a petição ao mesmo juízo da ação principal. Qualifique o reconvinte (réu na ação principal) com nome completo, nacionalidade, estado civil, profissão, CPF/CNPJ, endereço eletrônico e residencial. Qualifique o reconvindo (autor na ação principal) com os mesmos dados.',
                'fields': [
                    {'name': 'juizo_competente', 'label': 'Juízo Competente (mesmo da ação principal)', 'type': 'text', 'required': True},
                    {'name': 'reconvinte', 'label': 'Reconvinte (nome, nacionalidade, estado civil, profissão, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'reconvindo', 'label': 'Reconvindo (nome, nacionalidade, estado civil, profissão, CPF/CNPJ, endereço)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fundamentos_reconvencao',
                'name': 'II - Dos Fatos e Fundamentos Jurídicos',
                'description': 'Narração dos fatos que fundamentam o pedido reconvencional',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Exponha os fatos que dão causa à reconvenção, demonstrando a conexão com a ação principal. Apresente os fundamentos jurídicos do pedido reconvencional com citação da legislação aplicável e jurisprudência pertinente.',
                'fields': [
                    {'name': 'conexao_acao_principal', 'label': 'Conexão com a Ação Principal', 'type': 'textarea', 'required': True},
                    {'name': 'fatos_reconvencao', 'label': 'Narração dos Fatos', 'type': 'textarea', 'required': True},
                    {'name': 'fundamentos_juridicos', 'label': 'Fundamentos Jurídicos (legislação, doutrina, jurisprudência)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos_reconvencao',
                'name': 'III - Dos Pedidos e Requerimentos',
                'description': 'Pedidos do reconvinte, valor da causa e requerimentos',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule os pedidos de forma clara e determinada. Indique o valor da causa (art. 292 CPC). Requerimento de provas e outras diligências. Requerimento de intimação do reconvindo para contestar no prazo de 15 dias.',
                'fields': [
                    {'name': 'pedidos', 'label': 'Pedidos', 'type': 'textarea', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                    {'name': 'provas', 'label': 'Requisição de Provas', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 11. DIVÓRCIO LITIGIOSO (FAMÍLIA) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'divorcio_litigioso',
        'name': 'Divórcio Litigioso - CC/2002',
        'description': 'Blueprint para ação de divórcio litigioso sem consenso entre as partes',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.571-1.582; CPC/2015, arts. 693-699; EC 66/2010',
        'primary_color': '#E11D48',
        'secondary_color': '#FB7185',
        'cover_title': 'Divórcio Litigioso',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_divorcio',
                'name': 'I - Endereçamento e Qualificação das Partes',
                'description': 'Endereçamento ao juízo da Vara de Família e qualificação do cônjuge requerente e requerido',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece à Vara de Família competente. Qualifique o requerente: nome completo, nacionalidade, estado civil (casado(a)), profissão, CPF, RG, endereço. Qualifique o requerido com os mesmos dados. Informe o regime de bens do casamento e a data do casamento.',
                'fields': [
                    {'name': 'vara_familia', 'label': 'Vara de Família Competente', 'type': 'text', 'required': True},
                    {'name': 'requerente', 'label': 'Requerente (nome, nacionalidade, profissão, CPF, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'requerido', 'label': 'Requerido (nome, nacionalidade, profissão, CPF, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'regime_bens', 'label': 'Regime de Bens do Casamento', 'type': 'select', 'required': True, 'options': ['Comunhão parcial de bens', 'Comunhão universal de bens', 'Separação total de bens', 'Participação final nos aquestos']},
                    {'name': 'data_casamento', 'label': 'Data do Casamento', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fundamentos_divorcio',
                'name': 'II - Dos Fatos e Fundamentos',
                'description': 'Narração dos fatos que demonstram a dissolução da sociedade conjugal',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Narre os fatos que evidenciam o fim da sociedade conjugal. Destaque que o divórcio é direito potestativo (EC 66/2010). Mencione a existência de filhos menores, se houver, e a necessidade de guarda, visitas e alimentos. Fundamente juridicamente com base nos arts. 1.571-1.582 do CC e EC 66/2010.',
                'fields': [
                    {'name': 'fatos_divorcio', 'label': 'Narração dos Fatos', 'type': 'textarea', 'required': True},
                    {'name': 'filhos_menores', 'label': 'Filhos Menores (nomes e idades)', 'type': 'text', 'required': False},
                    {'name': 'fundamentos_juridicos', 'label': 'Fundamentos Jurídicos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos_divorcio',
                'name': 'III - Dos Pedidos',
                'description': 'Pedidos de divórcio, partilha, guarda, alimentos e visitas',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule os pedidos: decreto de divórcio, partilha de bens, guarda dos filhos, regime de visitas, pensão alimentícia (se aplicável), uso do nome de casado (se aplicável). Requira a produção de provas. Valor da causa. Requira a citação do requerido.',
                'fields': [
                    {'name': 'pedido_divorcio', 'label': 'Pedido Principal (decreto de divórcio)', 'type': 'textarea', 'required': True},
                    {'name': 'pedidos_acessorios', 'label': 'Pedidos Acessórios (guarda, visitas, alimentos, partilha)', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 12. EXECUÇÃO DE ALIMENTOS (FAMÍLIA) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'execucao_alimentos',
        'name': 'Execução de Alimentos - CPC art. 528',
        'description': 'Blueprint para execução de prestação alimentícia com pedido de prisão civil (rito do art. 528 CPC)',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 528; Lei 5.478/1968, arts. 17-24; CF/88, art. 5º, LXVII',
        'primary_color': '#059669',
        'secondary_color': '#34D399',
        'cover_title': 'Execução de Alimentos',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_execucao_alimentos',
                'name': 'I - Endereçamento e Qualificação das Partes',
                'description': 'Endereçamento, qualificação do exequente e executado e dados da obrigação alimentar',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece ao juízo da Vara de Família que proferiu a decisão. Qualifique o exequente (credor de alimentos) e o executado (devedor). Informe o título executivo judicial que fixou os alimentos (ação de alimentos, divórcio, investigação de paternidade, etc.), o valor das parcelas e as parcelas vencidas e não pagas.',
                'fields': [
                    {'name': 'vara_competente', 'label': 'Vara de Família Competente', 'type': 'text', 'required': True},
                    {'name': 'exequente', 'label': 'Exequente (credor dos alimentos - nome, CPF)', 'type': 'textarea', 'required': True},
                    {'name': 'executado', 'label': 'Executado (devedor - nome, CPF, endereço, local de trabalho)', 'type': 'textarea', 'required': True},
                    {'name': 'titulo_executivo', 'label': 'Título Executivo Judicial (nº processo, data da decisão)', 'type': 'text', 'required': True},
                    {'name': 'valor_mensal', 'label': 'Valor Mensal dos Alimentos (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'inadimplencia',
                'name': 'II - Da Inadimplência',
                'description': 'Demonstração do inadimplemento com parcelas em atraso',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Demonstre o inadimplemento: liste cada parcela vencida e não paga com respectivas datas de vencimento e valores. Informe se houve pagamento parcial. Calcule o total devido com atualização monetária e juros. Indique que o devedor foi intimado e permaneceu inerte.',
                'fields': [
                    {'name': 'parcelas_vencidas', 'label': 'Relação de Parcelas Vencidas e Não Pagas', 'type': 'textarea', 'required': True},
                    {'name': 'total_devido', 'label': 'Total Devido (com correção monetária e juros - R$)', 'type': 'text', 'required': True},
                    {'name': 'comprovante_intimacao', 'label': 'Comprovante de Intimação do Devedor', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedido_prisao',
                'name': 'III - Do Pedido de Execução',
                'description': 'Pedido de citação para pagamento, prisão civil e demais requerimentos',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule o pedido principal: requerimento de citação do executado para pagar em 3 dias, provar que pagou ou justificar a impossibilidade, sob pena de prisão civil (art. 528, §§3º e 7º CPC). Pedido de prisão em regime fechado. Pedido de desconto em folha. Requisição de certidão de débito alimentar.',
                'fields': [
                    {'name': 'pedido_citacao', 'label': 'Pedido de Citação e Pagamento (art. 528, §§3º e 7º CPC)', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_prisao_civil', 'label': 'Pedido de Prisão Civil (regime fechado)', 'type': 'textarea', 'required': True},
                    {'name': 'medidas_coercitivas', 'label': 'Medidas Coercitivas Adicionais (desconto em folha, protesto, etc.)', 'type': 'textarea', 'required': False},
                ],
            },
        ],
        'metadata': {
            'prazo_dias': 3,
            'deadline_alert': True,
            'deadline_alert_message': 'Prazo de 3 dias para pagamento sob pena de prisão civil (art. 528 CPC)',
        },
    },
    # ──────────────────────────────────────────────────────────────────────
    # 13. EXONERAÇÃO DE ALIMENTOS (FAMÍLIA) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'exoneracao_alimentos',
        'name': 'Exoneração de Alimentos - CC art. 1.699',
        'description': 'Blueprint para ação de exoneração de alimentos quando cessa a obrigação alimentar',
        'version': '1.0',
        'legal_basis': 'CC/2002, art. 1.699; CPC/2015, arts. 693-699',
        'primary_color': '#E11D48',
        'secondary_color': '#FB7185',
        'cover_title': 'Exoneração de Alimentos',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_exoneracao',
                'name': 'I - Endereçamento e Qualificação das Partes',
                'description': 'Endereçamento e qualificação do requerente e requerido na ação revisional',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece à Vara de Família competente (mesmo juízo que fixou os alimentos). Qualifique o requerente (atual devedor de alimentos) e o requerido (atual credor). Informe o número do processo onde os alimentos foram fixados, o valor atual e a data da fixação.',
                'fields': [
                    {'name': 'vara_familia', 'label': 'Vara de Família Competente', 'type': 'text', 'required': True},
                    {'name': 'requerente', 'label': 'Requerente (devedor - nome, CPF, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'requerido', 'label': 'Requerido (credor - nome, CPF)', 'type': 'textarea', 'required': True},
                    {'name': 'processo_origem', 'label': 'Processo de Origem (nº, valor dos alimentos fixados)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fundamentos_exoneracao',
                'name': 'II - Dos Fatos e Fundamentos Jurídicos',
                'description': 'Demonstração das causas de exoneração (superveniência, maioridade, etc.)',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Demonstre as causas que justificam a exoneração: implemento de maioridade (art. 1.635 CC), conclusão de curso superior, nova situação financeira do alimentante (desemprego, doença, redução de renda), ou ausência de necessidade do alimentado. Fundamente com CC art. 1.699 e jurisprudência do STJ.',
                'fields': [
                    {'name': 'fatos_exoneracao', 'label': 'Narração dos Fatos (causa da exoneração)', 'type': 'textarea', 'required': True},
                    {'name': 'fundamentos_juridicos', 'label': 'Fundamentos Jurídicos', 'type': 'textarea', 'required': True},
                    {'name': 'comprovantes', 'label': 'Comprovantes da Nova Situação', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos_exoneracao',
                'name': 'III - Dos Pedidos',
                'description': 'Pedido principal de exoneração e pedidos acessórios',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule o pedido de exoneração da obrigação alimentar. Pedido de suspensão liminar dos descontos. Requerimento de citação do requerido. Pedido de produção de provas. Valor da causa.',
                'fields': [
                    {'name': 'pedido_exoneracao', 'label': 'Pedido de Exoneração', 'type': 'textarea', 'required': True},
                    {'name': 'tutela_urgencia', 'label': 'Pedido de Tutela de Urgência (suspensão liminar)', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 14. AÇÃO DE CONSIGNAÇÃO EM PAGAMENTO TRABALHISTA (TRABALHISTA) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'acao_consignacao_trabalhista',
        'name': 'Ação de Consignação em Pagamento Trabalhista - CLT',
        'description': 'Blueprint para depósito judicial de verbas trabalhistas quando há recusa ou controvérsia',
        'version': '1.0',
        'legal_basis': 'CLT, art. 477, §8º; CC/2002, arts. 334-345; CPC/2015, arts. 539-549',
        'primary_color': '#0D9488',
        'secondary_color': '#2DD4BF',
        'cover_title': 'Consignação em Pagamento Trabalhista',
        'sections': [
            {
                'number': 1, 'key': 'partes_consignacao',
                'name': 'I - Das Partes e Endereçamento',
                'description': 'Endereçamento à Vara do Trabalho e qualificação das partes',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece à Vara do Trabalho competente. Qualifique o consignante (empregador ou responsável) com razão social, CNPJ e endereço. Qualifique o consignado (empregado ou ex-empregado) com nome, CPF e endereço conhecido. Informe o contrato de trabalho e a data da rescisão.',
                'fields': [
                    {'name': 'vara_trabalho', 'label': 'Vara do Trabalho Competente', 'type': 'text', 'required': True},
                    {'name': 'consignante', 'label': 'Consignante (empregador - razão social, CNPJ, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'consignado', 'label': 'Consignado (empregado - nome, CPF)', 'type': 'textarea', 'required': True},
                    {'name': 'contrato_trabalho', 'label': 'Dados do Contrato de Trabalho', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fundamentos_consignacao',
                'name': 'II - Dos Fatos e Fundamentos',
                'description': 'Narração da recusa ou controvérsia que motivou a consignação',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Narre os fatos: data da rescisão, valor das verbas rescisórias devidas, motivo pelo qual o empregado recusou receber ou não foi encontrado. Fundamente juridicamente com base nos arts. 334-345 CC, art. 477, §8º CLT e jurisprudência do TST.',
                'fields': [
                    {'name': 'fatos_consignacao', 'label': 'Narração dos Fatos (recusa ou impossibilidade de pagamento)', 'type': 'textarea', 'required': True},
                    {'name': 'valor_consignado', 'label': 'Valor Consignado (R$)', 'type': 'text', 'required': True},
                    {'name': 'verbas_discriminadas', 'label': 'Discriminação das Verbas (saldo salário, férias, 13º, FGTS, etc.)', 'type': 'textarea', 'required': True},
                    {'name': 'fundamentos_juridicos', 'label': 'Fundamentos Jurídicos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos_consignacao',
                'name': 'III - Dos Pedidos',
                'description': 'Pedido de depósito, citação e procedência',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule os pedidos: autorização para depósito judicial, citação do consignado para levantar o valor ou apresentar defesa, decreto de extinção da obrigação com pagamento, isenção de custas se houver depósito judicial tempestivo. Valor da causa igual ao valor consignado.',
                'fields': [
                    {'name': 'pedido_deposito', 'label': 'Pedido de Depósito Judicial', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_procedencia', 'label': 'Pedido de Procedência (extinção da obrigação)', 'type': 'textarea', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                ],
            },
        ],
        'metadata': {
            'prazo_dias': 30,
            'deadline_alert': True,
            'deadline_alert_message': 'Prazo de 30 dias para depósito judicial das verbas rescisórias (art. 477 CLT)',
        },
    },
    # ──────────────────────────────────────────────────────────────────────
    # 15. AGRAVO DE PETIÇÃO (TRABALHISTA) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'agravo_peticao',
        'name': 'Agravo de Petição - CLT art. 897',
        'description': 'Blueprint para recurso trabalhista contra decisão na execução trabalhista',
        'version': '1.0',
        'legal_basis': 'CLT, art. 897, §1º; Lei 5.584/1970, arts. 6º-9º; Súmulas TST',
        'primary_color': '#0D9488',
        'secondary_color': '#2DD4BF',
        'cover_title': 'Agravo de Petição',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_agravo',
                'name': 'I - Endereçamento e Qualificação',
                'description': 'Endereçamento, qualificação do agravante e agravado, dados do processo',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece ao Juiz da Vara do Trabalho, com pedido de remessa ao TRT competente. Qualifique o agravante e o agravado. Indique o número do processo na Vara de origem, a decisão agravada e a data da intimação. Mencione o preparo recursal já efetuado.',
                'fields': [
                    {'name': 'vara_origem', 'label': 'Vara do Trabalho de Origem', 'type': 'text', 'required': True},
                    {'name': 'trt_destino', 'label': 'TRT Destino (região)', 'type': 'text', 'required': True},
                    {'name': 'agravante', 'label': 'Agravante (nome, CPF/CNPJ)', 'type': 'textarea', 'required': True},
                    {'name': 'agravado', 'label': 'Agravado (nome, CPF/CNPJ)', 'type': 'textarea', 'required': True},
                    {'name': 'num_processo', 'label': 'Nº do Processo na Vara de Origem', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fundamentos_agravo',
                'name': 'II - Da Decisão Agravada e Fundamentos',
                'description': 'Demonstração do erro, omissão ou excesso da decisão na execução',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Transcreva o trecho da decisão agravada que viola direito do agravante. Demonstre o erro, abuso ou excesso na execução. Fundamente juridicamente com art. 897 CLT, súmulas do TST e jurisprudência consolidada sobre o tema. Destaque a garantia do juízo, se houver.',
                'fields': [
                    {'name': 'decisao_agravada', 'label': 'Decisão Agravada (transcrição)', 'type': 'textarea', 'required': True},
                    {'name': 'fundamentos_recurso', 'label': 'Fundamentos do Recurso', 'type': 'textarea', 'required': True},
                    {'name': 'garantia_juizo', 'label': 'Garantia do Juízo (valor e modalidade)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos_agravo_peticao',
                'name': 'III - Dos Pedidos e Requerimentos',
                'description': 'Pedido de reforma, requerimento de processamento e preparo',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule o pedido de reforma ou nulidade da decisão agravada. Requerimento de processamento e remessa ao TRT. Requerimento de efeito suspensivo, se cabível. Comprovante de preparo recursal (depósito recursal + custas processuais). Intimação do agravado para contrarrazões.',
                'fields': [
                    {'name': 'pedido_reforma', 'label': 'Pedido de Reforma ou Nulidade', 'type': 'textarea', 'required': True},
                    {'name': 'efeito_suspensivo', 'label': 'Pedido de Efeito Suspensivo (se cabível)', 'type': 'textarea', 'required': False},
                    {'name': 'preparo_recursal', 'label': 'Preparo Recursal (depósito + custas - R$)', 'type': 'text', 'required': True},
                ],
            },
        ],
        'metadata': {
            'prazo_dias': 8,
            'deadline_alert': True,
            'deadline_alert_message': 'Prazo de 8 dias para interposição do Agravo de Petição (art. 897, §1º CLT)',
        },
    },
    # ──────────────────────────────────────────────────────────────────────
    # 16. AÇÃO INDENIZATÓRIA - VÍCIO DO PRODUTO (CONSUMIDOR) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'acao_indenizacao_consumidor',
        'name': 'Ação Indenizatória - Vício do Produto / Serviço (CDC)',
        'description': 'Blueprint para ação de indenização por vício do produto ou serviço nas relações de consumo',
        'version': '1.0',
        'legal_basis': 'CDC, arts. 18-25; CF/88, art. 5º, XXXII; CC/2002, arts. 186-927',
        'primary_color': '#2563EB',
        'secondary_color': '#60A5FA',
        'cover_title': 'Ação Indenizatória - Vício do Produto',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_consumidor',
                'name': 'I - Endereçamento e Qualificação das Partes',
                'description': 'Endereçamento ao juízo competente e qualificação do consumidor e fornecedor',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece ao Juizado Especial Cível (se valor até 40 salários mínimos) ou Vara Cível. Qualifique o autor/consumidor: nome, CPF, endereço. Qualifique o réu/fornecedor: razão social, CNPJ, endereço. Descreva a relação de consumo (produto ou serviço adquirido, data, valor).',
                'fields': [
                    {'name': 'juizo_competente', 'label': 'Juízo Competente (JEC ou Vara Cível)', 'type': 'text', 'required': True},
                    {'name': 'autor', 'label': 'Autor/Consumidor (nome, CPF, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'reu_fornecedor', 'label': 'Réu/Fornecedor (razão social, CNPJ, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'produto_servico', 'label': 'Produto ou Serviço Adquirido', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos_vicio',
                'name': 'II - Dos Fatos (Vício do Produto/Serviço)',
                'description': 'Narração do vício, tentativas de solução e danos sofridos',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Narre detalhadamente: aquisição do produto/serviço, surgimento do vício (defeito, mau funcionamento, inadequação, diferença de quantidade), tentativas de solução junto ao fornecedor (protocolos, prazos), danos materiais e morais sofridos. Classifique o vício conforme CDC arts. 18-20.',
                'fields': [
                    {'name': 'descricao_vicio', 'label': 'Descrição do Vício (defeito, inadequação, diferença)', 'type': 'textarea', 'required': True},
                    {'name': 'tentativas_solucao', 'label': 'Tentativas de Solução junto ao Fornecedor', 'type': 'textarea', 'required': True},
                    {'name': 'danos_sofridos', 'label': 'Danos Materiais e Morais Sofridos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'fundamentos_consumidor',
                'name': 'III - Dos Fundamentos Jurídicos',
                'description': 'Fundamentação com base no CDC e jurisprudência',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Fundamente com CDC arts. 18-25 (vício do produto), art. 14 (fato do serviço), art. 6º (direitos básicos do consumidor), arts. 42 e 51. Jurisprudência do STJ sobre responsabilidade objetiva do fornecedor, inversão do ônus da prova (art. 6º, VIII) e dano moral presumido.',
                'fields': [
                    {'name': 'fundamentacao_cdc', 'label': 'Fundamentação no CDC (artigos aplicáveis)', 'type': 'textarea', 'required': True},
                    {'name': 'jurisprudencia', 'label': 'Jurisprudência (STJ, TJs)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'pedidos_indenizacao',
                'name': 'IV - Dos Pedidos',
                'description': 'Pedidos de indenização, tutela de urgência e requerimentos',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule os pedidos: indenização material (reparação do vício, substituição, devolução), indenização por danos morais, tutela de urgência (se risco ao consumidor), inversão do ônus da prova, justiça gratuita (se pessoa física), valor da causa, produção de provas.',
                'fields': [
                    {'name': 'pedido_indenizacao', 'label': 'Pedido de Indenização (material e moral)', 'type': 'textarea', 'required': True},
                    {'name': 'tutela_urgencia', 'label': 'Pedido de Tutela de Urgência', 'type': 'textarea', 'required': False},
                    {'name': 'inversao_onus', 'label': 'Pedido de Inversão do Ônus da Prova', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 17. REVISÃO DE BENEFÍCIO PREVIDENCIÁRIO (PREVIDENCIÁRIO) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'revisao_beneficio_previdenciario',
        'name': 'Revisão de Benefício Previdenciário - Lei 8.213/1991',
        'description': 'Blueprint para ação de revisão de benefício previdenciário do INSS',
        'version': '1.0',
        'legal_basis': 'Lei 8.213/1991, arts. 85-103; Decreto 3.048/1999; CF/88, art. 201',
        'primary_color': '#7C3AED',
        'secondary_color': '#A78BFA',
        'cover_title': 'Revisão de Benefício Previdenciário',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_previdenciario',
                'name': 'I - Endereçamento e Qualificação',
                'description': 'Endereçamento ao juizado ou vara federal e qualificação das partes',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece ao Juizado Especial Federal (se valor até 60 salários mínimos) ou Vara Federal. Qualifique o autor (segurado/beneficiário): nome, CPF, endereço. Qualifique o réu: INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS. Informe o NB (Número do Benefício), a data de concessão/DIB e o valor atual da RMI.',
                'fields': [
                    {'name': 'juizo_competente', 'label': 'Juízo Competente (JEF ou Vara Federal)', 'type': 'text', 'required': True},
                    {'name': 'autor', 'label': 'Autor/Segurado (nome, CPF, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'num_beneficio', 'label': 'Número do Benefício (NB/DIB)', 'type': 'text', 'required': True},
                    {'name': 'valor_atual', 'label': 'Valor Atual do Benefício (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos_revisao',
                'name': 'II - Dos Fatos',
                'description': 'Narração da concessão do benefício e do erro de cálculo',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Narre a história previdenciária: data do requerimento administrativo, concessão do benefício, cálculo da RMI (Renda Mensal Inicial), erro apontado (salários de contribuição excluídos, fator previdenciário errado, conversão de tempo especial em comum não considerada, etc.). Informe se houve requerimento administrativo de revisão e resposta do INSS.',
                'fields': [
                    {'name': 'historico_previdenciario', 'label': 'Histórico Previdenciário', 'type': 'textarea', 'required': True},
                    {'name': 'erro_apontado', 'label': 'Erro de Cálculo Apontado', 'type': 'textarea', 'required': True},
                    {'name': 'requerimento_administrativo', 'label': 'Requerimento Administrativo (data e resposta)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'fundamentos_revisao',
                'name': 'III - Dos Fundamentos Jurídicos',
                'description': 'Fundamentação legal e jurisprudencial para a revisão',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Fundamente com Lei 8.213/1991 (arts. 29, 39, 55, 57, 58), Decreto 3.048/1999, Súmulas STJ/STF/TNU sobre revisão de benefícios, Tema 1.099/STF e Tema 999/STJ. Destaque o direito adquirido e o ato jurídico perfeito quando cabível.',
                'fields': [
                    {'name': 'fundamentacao_legal', 'label': 'Fundamentação Legal', 'type': 'textarea', 'required': True},
                    {'name': 'jurisprudencia', 'label': 'Jurisprudência (Súmulas, Temas STJ/STF/TNU)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'pedidos_revisao',
                'name': 'IV - Dos Pedidos',
                'description': 'Pedido de revisão, cálculos, tutela de urgência',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule os pedidos: revisão do benefício com recálculo da RMI, pagamento das diferenças vencidas com correção monetária e juros, tutela de urgência para implantação/readequação, justiça gratuita (se pessoa física), prova documental e pericial contábil, valor da causa.',
                'fields': [
                    {'name': 'pedido_revisao', 'label': 'Pedido de Revisão do Benefício', 'type': 'textarea', 'required': True},
                    {'name': 'diferencas_atrasadas', 'label': 'Pedido de Diferenças Vencidas (R$)', 'type': 'text', 'required': True},
                    {'name': 'tutela_urgencia', 'label': 'Pedido de Tutela de Urgência', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 18. RECURSO ADMINISTRATIVO INSS (PREVIDENCIÁRIO) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'recurso_administrativo_inss',
        'name': 'Recurso Administrativo INSS - Lei 8.213/1991',
        'description': 'Blueprint para recurso administrativo contra decisão do INSS nos Conselhos de Recursos da Previdência Social (CRPS)',
        'version': '1.0',
        'legal_basis': 'Lei 8.213/1991, arts. 130-132; Decreto 3.048/1999, arts. 303-308; Súmulas CRPS',
        'primary_color': '#7C3AED',
        'secondary_color': '#A78BFA',
        'cover_title': 'Recurso Administrativo INSS',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_recurso_adm',
                'name': 'I - Identificação do Recorrente e do Ato Recorrido',
                'description': 'Identificação completa e dados do ato administrativo contestado',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Identifique o recorrente (segurado/beneficiário): nome, CPF, endereço. Identifique o ato recorrido: número do processo administrativo (NB com dígito), espécie de benefício, data da decisão, órgão que proferiu a decisão (Agência do INSS, Junta de Recursos, etc.). Informe se houve ciência pessoal ou por via postal.',
                'fields': [
                    {'name': 'recorrente', 'label': 'Recorrente (nome, CPF, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'num_processo_adm', 'label': 'Nº do Processo Administrativo (NB + dígito)', 'type': 'text', 'required': True},
                    {'name': 'decisao_recorrida', 'label': 'Decisão Recorrida (data, órgão, fundamento)', 'type': 'textarea', 'required': True},
                    {'name': 'data_ciencia', 'label': 'Data da Ciência da Decisão', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'razoes_recurso_adm',
                'name': 'II - Das Razões do Recurso',
                'description': 'Exposição dos motivos de fato e de direito para reforma da decisão',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Exponha detalhadamente as razões pelas quais a decisão administrativa deve ser reformada. Demonstre o direito do recorrente com base na Lei 8.213/1991, Decreto 3.048/1999 e jurisprudência do CRPS. Apresente provas documentais e/ou testemunhais que comprovem o direito.',
                'fields': [
                    {'name': 'razoes_recurso', 'label': 'Razões do Recurso (fatos e fundamentos)', 'type': 'textarea', 'required': True},
                    {'name': 'fundamentacao_legal', 'label': 'Fundamentação Legal', 'type': 'textarea', 'required': True},
                    {'name': 'provas', 'label': 'Provas e Documentos', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedido_recurso_adm',
                'name': 'III - Do Pedido',
                'description': 'Pedido de conhecimento e provimento do recurso',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule o pedido: conhecimento e provimento do recurso administrativo, reforma da decisão recorrida, concessão/revisão/restabelecimento do benefício previdenciário, intimação do recorrente do resultado. Inclua requerimento de sustentação oral na Junta de Recursos, se desejado.',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido de Provimento do Recurso', 'type': 'textarea', 'required': True},
                    {'name': 'sustentacao_oral', 'label': 'Requerimento de Sustentação Oral', 'type': 'select', 'required': False, 'options': ['Sim', 'Não']},
                ],
            },
        ],
        'metadata': {
            'prazo_dias': 30,
            'deadline_alert': True,
            'deadline_alert_message': 'Prazo de 30 dias para interposição de recurso administrativo ordinário (art. 305, Decreto 3.048/1999)',
        },
    },
    # ──────────────────────────────────────────────────────────────────────
    # 19. DEFESA PRELIMINAR CRIMINAL (CRIMINAL) - PRIORIDADE 1
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'defesa_preliminar_criminal',
        'name': 'Defesa Preliminar Criminal - CPP art. 514',
        'description': 'Blueprint para defesa preliminar do acusado antes do recebimento da denúncia em ação penal',
        'version': '1.0',
        'legal_basis': 'CPP, arts. 514-517; CF/88, art. 5º, LV; Lei 9.099/1995, art. 81',
        'primary_color': '#DC2626',
        'secondary_color': '#F87171',
        'cover_title': 'Defesa Preliminar Criminal',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_defesa_criminal',
                'name': 'I - Endereçamento e Qualificação',
                'description': 'Endereçamento ao juízo e qualificação do acusado',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Enderece ao Juízo da Vara Criminal onde tramita o inquérito/ação penal. Qualifique o acusado: nome completo, nacionalidade, estado civil, profissão, CPF, RG, endereço. Informe o número do inquérito policial ou do procedimento investigatório criminal. Identifique os advogados constituídos.',
                'fields': [
                    {'name': 'vara_criminal', 'label': 'Vara Criminal Competente', 'type': 'text', 'required': True},
                    {'name': 'acusado', 'label': 'Acusado (nome, nacionalidade, estado civil, profissão, CPF, RG, endereço)', 'type': 'textarea', 'required': True},
                    {'name': 'num_inquerito', 'label': 'Nº do Inquérito Policial / Procedimento', 'type': 'text', 'required': True},
                    {'name': 'num_acao_penal', 'label': 'Nº da Ação Penal (se já distribuída)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'sintese_acusacao',
                'name': 'II - Síntese da Acusação',
                'description': 'Resumo dos fatos imputados ao acusado na denúncia',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Transcreva ou resuma os fatos imputados ao acusado na denúncia/queixa-crime. Identifique o tipo penal imputado (artigo do CP ou lei especial). Mencione a classificação do crime (doloso, culposo, tentado, consumado) e as circunstâncias judiciais apontadas na denúncia.',
                'fields': [
                    {'name': 'fatos_imputados', 'label': 'Fatos Imputados na Denúncia/Queixa', 'type': 'textarea', 'required': True},
                    {'name': 'tipificacao_penal', 'label': 'Tipificação Penal (artigo CP/lei especial)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'razoes_defesa_preliminar',
                'name': 'III - Das Razões de Defesa Preliminar',
                'description': 'Argumentos defensivos prévios ao recebimento da denúncia',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Apresente os argumentos defensivos: preliminares (inépcia da denúncia, falta de justa causa, ilegitimidade de parte, decadência/prescrição, violação de direito processual), mérito (negativa de autoria, ausência de materialidade, excludentes de ilicitude ou culpabilidade, atipicidade da conduta). Fundamente cada tese defensiva com legislação, doutrina e jurisprudência.',
                'fields': [
                    {'name': 'preliminares', 'label': 'Preliminares Processuais', 'type': 'textarea', 'required': False},
                    {'name': 'merito_defesa', 'label': 'Defesa de Mérito (negativa de autoria, excludentes, atipicidade)', 'type': 'textarea', 'required': True},
                    {'name': 'fundamentacao_defesa', 'label': 'Fundamentação Legal e Jurisprudencial', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'pedidos_defesa_preliminar',
                'name': 'IV - Dos Pedidos',
                'description': 'Pedidos de rejeição da denúncia e requerimentos probatórios',
                'instructions': '_BLOCO_ANTI_ALUCINACAO Formule os pedidos: rejeição da denúncia (art. 395 CPP) por inépcia, falta de justa causa ou ausência de condição da ação; ou absolvição sumária (art. 397 CPP). Pedido de produção de provas (documental, testemunhal, pericial). Requerimento de prazo para arrolar testemunhas. Pedido de liberdade (se preso).',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido de Rejeição da Denúncia ou Absolvição Sumária', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_provas', 'label': 'Pedido de Produção de Provas', 'type': 'textarea', 'required': False},
                    {'name': 'pedido_liberdade', 'label': 'Pedido de Liberdade (se acusado preso)', 'type': 'textarea', 'required': False},
                ],
            },
        ],
        'metadata': {
            'prazo_dias': 15,
            'deadline_alert': True,
            'deadline_alert_message': 'Prazo de 15 dias para defesa preliminar (art. 514 CPP)',
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE PROCESSO JURÍDICO (substituem os de licitação)
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_PROCESSO = [
    {'code': 'civel', 'name': 'Processo Cível', 'short_name': 'Cível', 'description': 'Processo de natureza cível (obrigações, responsabilidade civil, família, etc.)', 'category': 'outros', 'legal_basis': 'CPC/2015', 'display_order': 1},
    {'code': 'criminal', 'name': 'Processo Criminal', 'short_name': 'Criminal', 'description': 'Processo de natureza penal', 'category': 'outros', 'legal_basis': 'CPP; CP; Leis Especiais', 'display_order': 2},
    {'code': 'trabalhista', 'name': 'Processo Trabalhista', 'short_name': 'Trabalhista', 'description': 'Processo perante a Justiça do Trabalho', 'category': 'outros', 'legal_basis': 'CLT; CF/88, art. 114; TST', 'display_order': 3},
    {'code': 'tributario', 'name': 'Processo Tributário', 'short_name': 'Tributário', 'description': 'Execução fiscal, embargos e litígios tributários', 'category': 'outros', 'legal_basis': 'CTN; Lei 6.830/1980; CF/88', 'display_order': 4},
    {'code': 'familia', 'name': 'Processo de Família', 'short_name': 'Família', 'description': 'Divórcio, guarda, alimentos, inventário, etc.', 'category': 'outros', 'legal_basis': 'CPC/2015, Parte Especial, Livro I; CC/2002', 'display_order': 5},
    {'code': 'previdenciario', 'name': 'Processo Previdenciário', 'short_name': 'Previdenciário', 'description': 'Benefícios previdenciários e assistenciais', 'category': 'outros', 'legal_basis': 'Lei 8.213/1991; Lei 8.742/1993', 'display_order': 6},
    {'code': 'ambiental', 'name': 'Processo Ambiental', 'short_name': 'Ambiental', 'description': 'Litígios de direito ambiental', 'category': 'outros', 'legal_basis': 'CF/88, art. 225; Lei 9.605/1998; Lei 12.651/2012', 'display_order': 7},
    {'code': 'administrativo', 'name': 'Processo Administrativo', 'short_name': 'Administrativo', 'description': 'Ações contra o Poder Público', 'category': 'outros', 'legal_basis': 'Lei 9.784/1999; Lei 4.717/1965', 'display_order': 8},
    {'code': 'consumidor', 'name': 'Processo do Consumidor', 'short_name': 'Consumidor', 'description': 'Relações de consumo e direitos do consumidor', 'category': 'outros', 'legal_basis': 'CDC - Lei 8.078/1990', 'display_order': 9},
    {'code': 'empresarial', 'name': 'Processo Empresarial', 'short_name': 'Empresarial', 'description': 'Direito empresarial, societário e falimentar', 'category': 'outros', 'legal_basis': 'CC/2002; Lei 6.404/1976; Lei 11.101/2005', 'display_order': 10},
]

# ─────────────────────────────────────────────────────────────────────────────
# STATUS DE PROCESSO JURÍDICO
# ─────────────────────────────────────────────────────────────────────────────

STATUS_PROCESSO = [
    {'code': 'distribuicao', 'name': 'Distribuição', 'description': 'Processo distribuído, aguardando despacho inicial', 'category': 'inicial', 'is_default': True, 'is_final': False, 'display_order': 1},
    {'code': 'citacao_pendente', 'name': 'Citação Pendente', 'description': 'Aguardando citação do réu', 'category': 'andamento', 'is_default': False, 'is_final': False, 'display_order': 2},
    {'code': 'contestacao_prazo', 'name': 'Prazo de Contestação', 'description': 'Réu citado, prazo de contestação em curso', 'category': 'andamento', 'is_default': False, 'is_final': False, 'display_order': 3},
    {'code': 'instrucao', 'name': 'Instrução Processual', 'description': 'Fase de instrução - produção de provas', 'category': 'andamento', 'is_default': False, 'is_final': False, 'display_order': 4},
    {'code': 'julgamento_pendente', 'name': 'Aguardando Julgamento', 'description': 'Processo concluso para sentença/acórdão', 'category': 'andamento', 'is_default': False, 'is_final': False, 'display_order': 5},
    {'code': 'recursal', 'name': 'Fase Recursal', 'description': 'Recurso interposto, aguardando julgamento em instância superior', 'category': 'andamento', 'is_default': False, 'is_final': False, 'display_order': 6},
    {'code': 'execucao_status', 'name': 'Execução', 'description': 'Fase de execução da sentença ou título extrajudicial', 'category': 'andamento', 'is_default': False, 'is_final': False, 'display_order': 7},
    {'code': 'suspenso', 'name': 'Suspenso', 'description': 'Processo suspenso por acordo ou decisão judicial', 'category': 'suspenso', 'is_default': False, 'is_final': False, 'display_order': 8},
    {'code': 'transitado_julgado', 'name': 'Transitado em Julgado', 'description': 'Decisão final com trânsito em julgado', 'category': 'finalizado', 'is_default': False, 'is_final': True, 'display_order': 9},
    {'code': 'arquivado', 'name': 'Arquivado', 'description': 'Processo arquivado após extinção', 'category': 'finalizado', 'is_default': False, 'is_final': True, 'display_order': 10},
    {'code': 'acordo_homologado', 'name': 'Acordo Homologado', 'description': 'Encerrado por acordo entre as partes', 'category': 'finalizado', 'is_default': False, 'is_final': True, 'display_order': 11},
]


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Seed completo do domínio jurídico Verus.AI - remove licitação e cria peças jurídicas'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria dados mesmo se já existirem')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito sem executar')
        parser.add_argument('--keep-procurement', action='store_true', help='Mantém dados de licitação (não remove)')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        keep_procurement = options['keep_procurement']

        self.stdout.write('\n' + '=' * 65)
        self.stdout.write(self.style.SUCCESS('  VERUS.AI - SEED JURÍDICO COMPLETO'))
        self.stdout.write('=' * 65)
        if dry_run:
            self.stdout.write(self.style.WARNING('  MODO DRY-RUN - nenhuma alteração será feita'))
        self.stdout.write('')

        with transaction.atomic():
            if not dry_run:
                if not keep_procurement:
                    self._remover_dados_licitacao()
                self._criar_categorias()
                self._criar_tipos_documento()
                self._criar_tipos_processo()
                self._criar_status_processo()
                agentes = self._criar_agentes_secao()
                self._criar_blueprints(agentes, force)
                self._atualizar_agentes_chat()
            else:
                self.stdout.write(self.style.WARNING('  Dry-run: pulando todas as operações de banco.'))

        self.stdout.write('')
        self.stdout.write('=' * 65)
        self.stdout.write(self.style.SUCCESS('  SEED CONCLUÍDO COM SUCESSO'))
        self.stdout.write('=' * 65 + '\n')

    # ─────────────────────────────────────────────────────────────────────
    # REMOVER DADOS DE LICITAÇÃO
    # ─────────────────────────────────────────────────────────────────────

    def _remover_dados_licitacao(self):
        from apps.intelligent_assistant.models import DocumentBlueprint, SectionAgentConfig
        from apps.core.models import DocumentType, DocumentCategory, ProcessType, ProcessStatus

        self.stdout.write(self.style.WARNING('  → Removendo dados de licitação...'))

        # Todos os tipos que NÃO são peças jurídicas propriamente ditas
        codigos_licitacao = [
            'dfd', 'etp', 'mapa_riscos', 'pesquisa_precos', 'termo_referencia',
            'projeto_basico', 'projeto_executivo', 'edital', 'contrato',
            'ata_sessao', 'parecer_julgamento', 'parecer_habilitacao',
            'termo_adjudicacao', 'termo_homologacao', 'resposta_impugnacao',
            'decisao_recurso', 'minuta_contrato', 'minuta_ata',
            'instrumento_convocatorio', 'aviso_licitacao', 'ata_registro_precos',
            'boletim_medicao', 'ordem_servico', 'relatorio_fiscalizacao',
            'peca_juridica', 'recurso', 'notificacao',
            # tipos com códigos reais no DB
            'impugnacao', 'contrarrazoes', 'parecer', 'parecer_juridico',
            'termo_recebimento_provisorio', 'termo_recebimento_definitivo',
            'aditivo_contratual', 'custom',
        ]

        codigos_categoria_licitacao = [
            'fase_preparatoria', 'fase_externa', 'pos_contratacao', 'outros',
            'fase_contratacao', 'impugnacoes_recursos', 'pareceres',
        ]

        # Blueprints por code do document_type
        blueprints_del = DocumentBlueprint.objects.filter(
            document_type__code__in=codigos_licitacao
        )
        n = blueprints_del.count()
        blueprints_del.delete()
        self.stdout.write(f'     Blueprints removidos (por code): {n}')

        # Blueprints por nome (captura variações de código) — Lei 14.133
        nomes_licitacao = [
            'Formalização de Demanda', 'Formalizacao de Demanda',
            'Mapa de Riscos', 'Mapa de Risco',
            'Pesquisa de Preços', 'Pesquisa de Precos',
            'Estudo Técnico Preliminar', 'Estudo Tecnico Preliminar',
            'Termo de Referência', 'Termo de Referencia',
            'Edital', 'Minuta de Contrato', 'Ata de Registro',
            'Lei 14.133', '14.133', 'PMJP', 'ETP',
        ]
        from django.db.models import Q
        q_nomes = Q()
        for nome in nomes_licitacao:
            q_nomes |= Q(name__icontains=nome)
        blueprints_nome = DocumentBlueprint.objects.filter(q_nomes)
        n2 = blueprints_nome.count()
        if n2:
            blueprints_nome.delete()
            self.stdout.write(f'     Blueprints removidos (por nome): {n2}')

        # Agentes de seção ligados a blueprints de licitação
        agentes_del = SectionAgentConfig.objects.filter(
            name__icontains='ETP'
        ) | SectionAgentConfig.objects.filter(
            name__icontains='Edital'
        ) | SectionAgentConfig.objects.filter(
            name__icontains='Licitação'
        ) | SectionAgentConfig.objects.filter(
            name__icontains='PMJP'
        ) | SectionAgentConfig.objects.filter(
            name__icontains='TR '
        ) | SectionAgentConfig.objects.filter(
            name__icontains='Mapa de Risco'
        ) | SectionAgentConfig.objects.filter(
            name__icontains='Minuta'
        ) | SectionAgentConfig.objects.filter(
            name='Verus.AI - Gerador de Seção Jurídica'
        ) | SectionAgentConfig.objects.filter(
            name='Verus.AI - Validador de Seção Jurídica'
        )
        n = agentes_del.count()
        agentes_del.delete()
        self.stdout.write(f'     SectionAgentConfigs removidos: {n}')

        # Tipos de documento de licitação
        tipos_del = DocumentType.objects.filter(code__in=codigos_licitacao)
        n = tipos_del.count()
        tipos_del.delete()
        self.stdout.write(f'     DocumentTypes removidos: {n}')

        # Categorias de licitação — tenta remover, ignora se ainda
        # houver DocumentTypes apontando (ProtectedError)
        cats_qs = DocumentCategory.objects.filter(code__in=codigos_categoria_licitacao)
        n = 0
        for cat in cats_qs:
            if not cat.document_types.exists():
                cat.delete()
                n += 1
            else:
                self.stdout.write(
                    f'     Categoria "{cat.code}" mantida (ainda tem tipos vinculados)'
                )
        self.stdout.write(f'     DocumentCategories removidas: {n}')

        # Tipos e status de processo de licitação
        n_pt = ProcessType.objects.filter(
            code__in=['pregao_eletronico', 'pregao_presencial', 'concorrencia',
                      'tomada_preco', 'convite', 'concurso', 'leilao',
                      'dispensa', 'inexigibilidade', 'chamamento_publico',
                      'srp', 'pregao', 'chamamento']
        ).delete()[0]
        self.stdout.write(f'     ProcessTypes removidos: {n_pt}')

        n_ps = ProcessStatus.objects.filter(
            code__in=['planejamento', 'em_andamento', 'suspenso',
                      'concluido', 'cancelado', 'arquivado',
                      'licitacao', 'contratacao', 'execucao_contratual',
                      'encerrado']
        ).delete()[0]
        self.stdout.write(f'     ProcessStatuses removidos: {n_ps}')

        self.stdout.write(self.style.SUCCESS('  ✓ Dados de licitação removidos\n'))

    # ─────────────────────────────────────────────────────────────────────
    # CRIAR CATEGORIAS
    # ─────────────────────────────────────────────────────────────────────

    def _criar_categorias(self):
        from apps.core.models import DocumentCategory

        self.stdout.write('  → Criando categorias jurídicas...')
        for data in CATEGORIAS:
            obj, created = DocumentCategory.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'display_order': data['display_order'],
                    'is_active': True,
                }
            )
            status = '✓ Criada' if created else '⊘ Existe'
            style = self.style.SUCCESS if created else self.style.HTTP_INFO
            self.stdout.write(style(f'     {status:<12} {obj.name}'))

        self.stdout.write('')

    # ─────────────────────────────────────────────────────────────────────
    # CRIAR TIPOS DE DOCUMENTO
    # ─────────────────────────────────────────────────────────────────────

    def _criar_tipos_documento(self):
        from apps.core.models import DocumentType, DocumentCategory

        self.stdout.write('  → Criando tipos de documento jurídicos...')
        cats = {c.code: c for c in DocumentCategory.objects.all()}

        for data in TIPOS_DOCUMENTO:
            cat = cats.get(data['category'])
            if not cat:
                self.stdout.write(self.style.ERROR(f'     ✗ Categoria não encontrada: {data["category"]}'))
                continue

            obj, created = DocumentType.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'short_name': data['short_name'],
                    'description': data['description'],
                    'category': cat,
                    'icon': data['icon'],
                    'color': data['color'],
                    'legal_basis': data['legal_basis'],
                    'display_order': data['display_order'],
                    'is_active': True,
                }
            )
            status = '✓ Criado' if created else '⊘ Existe'
            style = self.style.SUCCESS if created else self.style.HTTP_INFO
            self.stdout.write(style(f'     {status:<12} [{data["short_name"]}] {obj.name}'))

        self.stdout.write('')

    # ─────────────────────────────────────────────────────────────────────
    # CRIAR TIPOS DE PROCESSO
    # ─────────────────────────────────────────────────────────────────────

    def _criar_tipos_processo(self):
        from apps.core.models import ProcessType

        self.stdout.write('  → Criando tipos de processo jurídicos...')
        for data in TIPOS_PROCESSO:
            obj, created = ProcessType.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'short_name': data['short_name'],
                    'description': data['description'],
                    'category': data['category'],
                    'legal_basis': data['legal_basis'],
                    'icon': 'Scale',
                    'color': '#7030A0',
                    'display_order': data['display_order'],
                    'is_active': True,
                }
            )
            status = '✓ Criado' if created else '⊘ Existe'
            style = self.style.SUCCESS if created else self.style.HTTP_INFO
            self.stdout.write(style(f'     {status:<12} {obj.name}'))

        self.stdout.write('')

    # ─────────────────────────────────────────────────────────────────────
    # CRIAR STATUS DE PROCESSO
    # ─────────────────────────────────────────────────────────────────────

    def _criar_status_processo(self):
        from apps.core.models import ProcessStatus

        self.stdout.write('  → Criando status de processo jurídicos...')
        for data in STATUS_PROCESSO:
            obj, created = ProcessStatus.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'category': data['category'],
                    'icon': 'Circle',
                    'color': '#7030A0',
                    'display_order': data['display_order'],
                    'is_default': data['is_default'],
                    'is_final': data['is_final'],
                    'is_active': True,
                }
            )
            status = '✓ Criado' if created else '⊘ Existe'
            style = self.style.SUCCESS if created else self.style.HTTP_INFO
            self.stdout.write(style(f'     {status:<12} {obj.name}'))

        self.stdout.write('')

    # ─────────────────────────────────────────────────────────────────────
    # CRIAR AGENTES DE SEÇÃO
    # ─────────────────────────────────────────────────────────────────────

    def _criar_agentes_secao(self):
        from apps.intelligent_assistant.models import SectionAgentConfig

        self.stdout.write('  → Criando SectionAgentConfigs especializados...')

        agentes_specs = [
            {
                'key': 'gerador_civel',
                'name': 'Verus.AI - Gerador Cível',
                'description': 'Gera seções de peças cíveis: petições, contestações, execuções e embargos',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_CIVEL,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': True,
            },
            {
                'key': 'gerador_recursal',
                'name': 'Verus.AI - Gerador Recursal',
                'description': 'Gera seções de recursos: apelação, agravo, REsp, RE, embargos de declaração',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_RECURSAL,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'gerador_constitucional',
                'name': 'Verus.AI - Gerador Constitucional',
                'description': 'Gera seções de remédios constitucionais: HC, MS e tutelas de urgência',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_CONSTITUCIONAL,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'gerador_trabalhista',
                'name': 'Verus.AI - Gerador Trabalhista',
                'description': 'Gera seções de peças trabalhistas: reclamação, contestação e contratos CLT',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_TRABALHISTA,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'gerador_criminal',
                'name': 'Verus.AI - Gerador Criminal',
                'description': 'Gera seções de peças criminais: queixa-crime e alegações finais',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_CRIMINAL,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'gerador_extrajudicial',
                'name': 'Verus.AI - Gerador Extrajudicial',
                'description': 'Gera seções de documentos extrajudiciais: contratos, notificações, pareceres e procurações',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_EXTRAJUDICIAL,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'validador_juridico',
                'name': 'Verus.AI - Validador Jurídico',
                'description': 'Valida o conteúdo jurídico gerado para todas as áreas do direito',
                'agent_type': 'validator',
                'system_prompt': PROMPT_VALIDADOR_JURIDICO,
                'temperature': TEMP_VALIDATOR,
                'max_tokens': 1024,
                'is_default': False,
            },
        ]

        agentes = {}
        for spec in agentes_specs:
            obj, created = SectionAgentConfig.objects.update_or_create(
                name=spec['name'],
                defaults={
                    'description': spec['description'],
                    'agent_type': spec['agent_type'],
                    'system_prompt': spec['system_prompt'],
                    'user_prompt_template': USER_TEMPLATE_SECAO,
                    'llm_provider': PROVIDER,
                    'model_name': MODEL,
                    'temperature': spec['temperature'],
                    'max_tokens': spec['max_tokens'],
                    'use_rag': False,
                    'rag_top_k': 5,
                    'rag_similarity_threshold': 0.7,
                    'is_active': True,
                    'is_default': spec['is_default'],
                }
            )
            agentes[spec['key']] = obj
            self.stdout.write(self.style.SUCCESS(
                f'     {"✓ Criado" if created else "↻ Atualizado":<12} {obj.name}'
            ))

        self.stdout.write('')
        return agentes

    # ─────────────────────────────────────────────────────────────────────
    # CRIAR BLUEPRINTS E SEÇÕES
    # ─────────────────────────────────────────────────────────────────────

    def _criar_blueprints(self, agentes, force):
        from apps.core.models import DocumentType
        from apps.intelligent_assistant.models import DocumentBlueprint, BlueprintSection

        self.stdout.write('  → Criando blueprints e seções...')

        tipos = {t.code: t for t in DocumentType.objects.all()}

        for bp_data in BLUEPRINTS_DATA:
            doc_type = tipos.get(bp_data['doc_type_code'])
            if not doc_type:
                self.stdout.write(self.style.ERROR(
                    f'     ✗ Tipo não encontrado: {bp_data["doc_type_code"]}'
                ))
                continue

            blueprint, created = DocumentBlueprint.objects.get_or_create(
                document_type=doc_type,
                name=bp_data['name'],
                defaults={
                    'description': bp_data['description'],
                    'version': bp_data['version'],
                    'legal_basis': bp_data['legal_basis'],
                    'primary_color': bp_data['primary_color'],
                    'secondary_color': bp_data['secondary_color'],
                    'cover_title': bp_data['cover_title'],
                    'cover_page_enabled': True,
                    'cover_subtitle': bp_data.get('description', ''),
                    'organization_name': 'Verus.AI',
                    'organization_acronym': 'BJus',
                    'pdf_font_family': 'Times New Roman',
                    'pdf_font_size': '12pt',
                    'pdf_line_height': '1.5',
                    'pdf_text_align': 'justify',
                    'pdf_paragraph_indent': '1.25cm',
                    'is_active': True,
                    'is_default': True,
                }
            )

            if not created and force:
                blueprint.description = bp_data['description']
                blueprint.primary_color = bp_data['primary_color']
                blueprint.secondary_color = bp_data['secondary_color']
                blueprint.save()
                blueprint.sections.all().delete()
                created = True  # recria seções

            # Sempre sincroniza áreas com base na category do document_type
            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)

            # Garante is_default=True em re-execução
            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])

            flag = '✓ Criado' if created else '⊘ Existe'
            style = self.style.SUCCESS if created else self.style.HTTP_INFO
            self.stdout.write(style(f'     {flag:<12} {blueprint.name}'))

            if created:
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={
                            'section_name': sec['name'],
                            'section_key': sec['key'],
                            'description': sec.get('description', ''),
                            'instructions': sec.get('instructions', ''),
                            'order': sec['number'],
                            'is_required': True,
                            'allow_skip': False,
                            'max_generation_attempts': 2,
                            'generator_agent': agentes.get(AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_civel')),
                            'validator_agent': agentes.get('validador_juridico'),
                            'section_fields': sec.get('fields', []),
                            'is_active': True,
                        }
                    )
                self.stdout.write(f'          → {len(bp_data["sections"])} seções criadas')

        self.stdout.write('')

    # ─────────────────────────────────────────────────────────────────────
    # ATUALIZAR AGENTES DE CHAT (AgentPrompt)
    # ─────────────────────────────────────────────────────────────────────

    def _atualizar_agentes_chat(self):
        from apps.agents.models import AgentPrompt

        self.stdout.write('  → Atualizando AgentPrompts para contexto jurídico...')

        AGENTES_CHAT = [
            {
                'name': 'Assistente Jurídico Verus.AI',
                'description': 'Assistente jurídico geral para advogados - responde dúvidas de direito, legislação e jurisprudência',
                'agent_type': 'consultor_juridico',
                'system_prompt': (
                    'Você é o Assistente Jurídico do Verus.AI, um assistente especializado em Direito Brasileiro.\n\n'
                    'Você auxilia advogados e operadores do direito com:\n'
                    '- Pesquisa de legislação (CPC, CC, CLT, CPP, CF, leis especiais)\n'
                    '- Análise de jurisprudência dos tribunais superiores (STF, STJ, TST)\n'
                    '- Estratégia processual e escolha da melhor peça\n'
                    '- Prazos processuais e requisitos formais\n'
                    '- Fundamentos legais para argumentação\n\n'
                    'REGRAS:\n'
                    '1. Nunca invente legislação, súmulas ou jurisprudência\n'
                    '2. Quando citar precedentes, informe que devem ser verificados nas fontes oficiais\n'
                    '3. Seja preciso na indicação de artigos de lei\n'
                    '4. Recomende sempre consulta às fontes primárias\n'
                    '5. Use linguagem jurídica adequada mas compreensível'
                ),
                'user_prompt_template': '{{user_message}}',
                'llm_provider': 'watsonx',
                'model_name': MODEL,
                'temperature': 0.5,
                'max_tokens': 4096,
                'is_default': True,
            },
            {
                'name': 'Especialista em Direito Civil',
                'description': 'Especialista em obrigações, contratos, responsabilidade civil e direito de família',
                'agent_type': 'especialista_civil',
                'system_prompt': (
                    'Você é um especialista em Direito Civil Brasileiro com foco em:\n'
                    '- Direito das Obrigações (arts. 233-420 CC)\n'
                    '- Contratos (arts. 421-480 CC)\n'
                    '- Responsabilidade Civil (arts. 927-954 CC)\n'
                    '- Direito de Família (arts. 1511-1783 CC)\n'
                    '- Direito das Coisas (arts. 1196-1510 CC)\n'
                    '- Direito Sucessório (arts. 1784-2027 CC)\n\n'
                    'Fundamente sempre no Código Civil de 2002 e jurisprudência do STJ.'
                ),
                'user_prompt_template': '{{user_message}}',
                'llm_provider': 'watsonx',
                'model_name': MODEL,
                'temperature': 0.4,
                'max_tokens': 4096,
                'is_default': False,
            },
            {
                'name': 'Especialista em Direito do Trabalho',
                'description': 'Especialista em CLT, relações trabalhistas e processo do trabalho',
                'agent_type': 'especialista_trabalhista',
                'system_prompt': (
                    'Você é um especialista em Direito do Trabalho Brasileiro com foco em:\n'
                    '- CLT - Consolidação das Leis do Trabalho\n'
                    '- Reforma Trabalhista (Lei 13.467/2017)\n'
                    '- Processo do trabalho - TRTs e TST\n'
                    '- Súmulas e OJs do TST\n'
                    '- FGTS, férias, 13º salário, verbas rescisórias\n'
                    '- Saúde e segurança do trabalho\n\n'
                    'Fundamente sempre na CLT, legislação trabalhista e jurisprudência do TST.'
                ),
                'user_prompt_template': '{{user_message}}',
                'llm_provider': 'watsonx',
                'model_name': MODEL,
                'temperature': 0.4,
                'max_tokens': 4096,
                'is_default': False,
            },
            {
                'name': 'Especialista em Direito do Consumidor',
                'description': 'Especialista em CDC - Código de Defesa do Consumidor e relações de consumo',
                'agent_type': 'especialista_consumidor',
                'system_prompt': (
                    'Você é um especialista em Direito do Consumidor Brasileiro com foco em:\n'
                    '- CDC - Lei 8.078/1990\n'
                    '- Responsabilidade por fato e vício do produto/serviço\n'
                    '- Práticas abusivas e publicidade enganosa\n'
                    '- Superendividamento (Lei 14.871/2024)\n'
                    '- Jurisprudência do STJ em direito do consumidor\n'
                    '- Procon e órgãos de defesa do consumidor\n\n'
                    'Fundamente sempre no CDC e jurisprudência do STJ.'
                ),
                'user_prompt_template': '{{user_message}}',
                'llm_provider': 'watsonx',
                'model_name': MODEL,
                'temperature': 0.4,
                'max_tokens': 4096,
                'is_default': False,
            },
            {
                'name': 'Especialista em Processo Civil',
                'description': 'Especialista em CPC/2015 - procedimentos, recursos e execução',
                'agent_type': 'especialista_processual',
                'system_prompt': (
                    'Você é um especialista em Direito Processual Civil Brasileiro com foco em:\n'
                    '- CPC/2015 - Código de Processo Civil\n'
                    '- Procedimentos comuns e especiais\n'
                    '- Sistema recursal - apelação, agravo, embargos, REsp, RE\n'
                    '- Tutelas provisórias - urgência e evidência\n'
                    '- Execução e cumprimento de sentença\n'
                    '- Prazos e preclusões\n'
                    '- Jurisprudência do STJ e STF sobre processo\n\n'
                    'Fundamente sempre no CPC/2015 e jurisprudência dos tribunais superiores.'
                ),
                'user_prompt_template': '{{user_message}}',
                'llm_provider': 'watsonx',
                'model_name': MODEL,
                'temperature': 0.4,
                'max_tokens': 4096,
                'is_default': False,
            },
            {
                'name': 'Especialista em Direito Tributário',
                'description': 'Especialista em tributos, planejamento tributário e contencioso fiscal',
                'agent_type': 'especialista_tributario',
                'system_prompt': (
                    'Você é um especialista em Direito Tributário Brasileiro com foco em:\n'
                    '- CTN - Código Tributário Nacional\n'
                    '- Impostos federais (IR, IPI, PIS, COFINS, CSLL)\n'
                    '- Impostos estaduais (ICMS, IPVA, ITCMD)\n'
                    '- Impostos municipais (ISS, IPTU, ITBI)\n'
                    '- Execução fiscal - Lei 6.830/1980\n'
                    '- Planejamento tributário e elisão fiscal\n'
                    '- Jurisprudência do STF e STJ em matéria tributária\n\n'
                    'Fundamente sempre no CTN e legislação tributária aplicável.'
                ),
                'user_prompt_template': '{{user_message}}',
                'llm_provider': 'watsonx',
                'model_name': MODEL,
                'temperature': 0.4,
                'max_tokens': 4096,
                'is_default': False,
            },
        ]

        for data in AGENTES_CHAT:
            # Tenta atualizar agente existente pelo agent_type, ou cria novo
            obj, created = AgentPrompt.objects.update_or_create(
                agent_type=data['agent_type'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'system_prompt': data['system_prompt'],
                    'user_prompt_template': data['user_prompt_template'],
                    'llm_provider': 'openai',  # campo choices do modelo
                    'model_name': data['model_name'],
                    'temperature': data['temperature'],
                    'max_tokens': data['max_tokens'],
                    'use_rag': False,
                    'is_active': True,
                    'is_default': data['is_default'],
                }
            )
            status = '✓ Criado' if created else '↻ Atualizado'
            style = self.style.SUCCESS if created else self.style.WARNING
            self.stdout.write(style(f'     {status:<12} {obj.name}'))

        self.stdout.write('')
