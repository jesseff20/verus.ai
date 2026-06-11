"""
Seed Especializado Complementar — Verus.AI.
Juizados Especiais, Direito Agrário, Direito Sanitário, Improbidade,
Desapropriação, Mandado de Segurança Coletivo, Execução complementar,
peças incidentais e Direito Desportivo.

Uso:
    python manage.py seed_especializado_complementar
    python manage.py seed_especializado_complementar --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction

MODEL = 'mistralai/mistral-medium-2505'
PROVIDER = 'watsonx'
TEMP_GENERATOR = 0.7
TEMP_VALIDATOR = 0.3
MAX_TOKENS = 4096

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIAS NOVAS
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIAS = [
    {
        'code': 'agrario',
        'name': 'Direito Agrário',
        'description': 'Peças jurídicas de Direito Agrário, usucapião rural e possessórias rurais',
        'display_order': 20,
    },
    {
        'code': 'desportivo',
        'name': 'Direito Desportivo',
        'description': 'Peças jurídicas do Direito Desportivo e Justiça Desportiva (STJD)',
        'display_order': 21,
    },
    {
        'code': 'constitucional',
        'name': 'Constitucional',
        'description': 'Peças de Direito Constitucional, remédios constitucionais e controle de constitucionalidade',
        'display_order': 22,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE DOCUMENTO
# ─────────────────────────────────────────────────────────────────────────────

TIPOS_DOCUMENTO = [
    # Juizados Especiais
    {
        'code': 'peticao_jec',
        'name': 'Petição Inicial - Juizado Especial Cível',
        'short_name': 'Pet. JEC',
        'description': 'Petição inicial para Juizado Especial Cível (Lei 9.099/95)',
        'category': 'acoes_peticoes',
        'icon': 'FileText',
        'color': '#2563EB',
        'legal_basis': 'Lei 9.099/1995, arts. 14-19; CF/88, art. 98, I',
        'display_order': 30,
    },
    {
        'code': 'recurso_inominado',
        'name': 'Recurso Inominado',
        'short_name': 'Rec. Inominado',
        'description': 'Recurso contra sentença proferida em Juizado Especial Cível',
        'category': 'recursos',
        'icon': 'ArrowUpCircle',
        'color': '#7C3AED',
        'legal_basis': 'Lei 9.099/1995, arts. 41-46',
        'display_order': 31,
    },
    {
        'code': 'pedido_contraposto_jec',
        'name': 'Pedido Contraposto - JEC',
        'short_name': 'Ped. Contraposto',
        'description': 'Contestação com pedido contraposto no Juizado Especial Cível',
        'category': 'defesas_respostas',
        'icon': 'ArrowLeftRight',
        'color': '#DC2626',
        'legal_basis': 'Lei 9.099/1995, art. 31',
        'display_order': 32,
    },
    {
        'code': 'peticao_jefaz',
        'name': 'Petição Inicial - Juizado Especial da Fazenda Pública',
        'short_name': 'Pet. JEFaz',
        'description': 'Petição inicial para Juizado Especial da Fazenda Pública (Lei 12.153/2009)',
        'category': 'acoes_peticoes',
        'icon': 'Building',
        'color': '#059669',
        'legal_basis': 'Lei 12.153/2009; Lei 9.099/1995 (subsidiária)',
        'display_order': 33,
    },
    # Direito Agrário
    {
        'code': 'usucapiao_rural',
        'name': 'Usucapião Rural/Constitucional',
        'short_name': 'Usucapião Rural',
        'description': 'Ação de usucapião especial rural (pro labore) - CF art. 191',
        'category': 'agrario',
        'icon': 'Leaf',
        'color': '#16A34A',
        'legal_basis': 'CF/88, art. 191; Lei 6.969/1981; CC/2002, art. 1.239',
        'display_order': 34,
    },
    {
        'code': 'possessoria_rural',
        'name': 'Ação Possessória Rural',
        'short_name': 'Possessória Rural',
        'description': 'Ação possessória de imóvel rural (reintegração, manutenção ou interdito proibitório)',
        'category': 'agrario',
        'icon': 'Map',
        'color': '#16A34A',
        'legal_basis': 'CPC/2015, arts. 554-568; Lei 8.629/1993; Estatuto da Terra (Lei 4.504/1964)',
        'display_order': 35,
    },
    # Direito Sanitário
    {
        'code': 'acao_medicamento_sus',
        'name': 'Ação de Fornecimento de Medicamento',
        'short_name': 'Ação Medicamento',
        'description': 'Ação judicial para fornecimento de medicamento ou tratamento pelo SUS',
        'category': 'acoes_peticoes',
        'icon': 'Heart',
        'color': '#DC2626',
        'legal_basis': 'CF/88, arts. 6º e 196; Lei 8.080/1990 (SUS); STF Tema 793',
        'display_order': 36,
    },
    # Improbidade Administrativa
    {
        'code': 'acao_improbidade',
        'name': 'Ação de Improbidade Administrativa',
        'short_name': 'Ação Improbidade',
        'description': 'Ação civil pública por ato de improbidade administrativa',
        'category': 'administrativo',
        'icon': 'AlertTriangle',
        'color': '#DC2626',
        'legal_basis': 'Lei 8.429/1992 (com alterações da Lei 14.230/2021); CF/88, art. 37, §4º',
        'display_order': 37,
    },
    # Desapropriação
    {
        'code': 'acao_desapropriacao',
        'name': 'Ação de Desapropriação',
        'short_name': 'Desapropriação',
        'description': 'Ação de desapropriação por utilidade pública ou interesse social',
        'category': 'administrativo',
        'icon': 'Landmark',
        'color': '#D97706',
        'legal_basis': 'DL 3.365/1941; Lei 4.132/1962; CF/88, art. 5º, XXIV',
        'display_order': 38,
    },
    {
        'code': 'contestacao_desapropriacao',
        'name': 'Contestação em Desapropriação',
        'short_name': 'Contest. Desapr.',
        'description': 'Contestação do expropriado em ação de desapropriação',
        'category': 'defesas_respostas',
        'icon': 'ShieldAlert',
        'color': '#D97706',
        'legal_basis': 'DL 3.365/1941, art. 20; CF/88, art. 5º, XXIV',
        'display_order': 39,
    },
    # Mandado de Segurança Coletivo
    {
        'code': 'mandado_seguranca_coletivo',
        'name': 'Mandado de Segurança Coletivo',
        'short_name': 'MS Coletivo',
        'description': 'Mandado de segurança impetrado por partido político, sindicato ou associação',
        'category': 'acoes_peticoes',
        'icon': 'Users',
        'color': '#2563EB',
        'legal_basis': 'CF/88, art. 5º, LXX; Lei 12.016/2009, arts. 21-22',
        'display_order': 40,
    },
    # Execução complementar
    {
        'code': 'embargos_arrematacao',
        'name': 'Embargos à Arrematação',
        'short_name': 'Emb. Arrematação',
        'description': 'Impugnação da arrematação em processo de execução',
        'category': 'execucao',
        'icon': 'Hammer',
        'color': '#B91C1C',
        'legal_basis': 'CPC/2015, arts. 903, §1º, e 746 (analogia); Súmula 399/STJ',
        'display_order': 41,
    },
    # Peças Incidentais
    {
        'code': 'conflito_competencia',
        'name': 'Conflito de Competência',
        'short_name': 'Confl. Competência',
        'description': 'Suscitação de conflito de competência positivo ou negativo',
        'category': 'recursos',
        'icon': 'GitBranch',
        'color': '#6D28D9',
        'legal_basis': 'CPC/2015, arts. 66, 951-959; CF/88, art. 105, I, d',
        'display_order': 42,
    },
    {
        'code': 'excecao_suspeicao',
        'name': 'Exceção de Suspeição/Impedimento',
        'short_name': 'Exc. Suspeição',
        'description': 'Arguição de impedimento ou suspeição de magistrado',
        'category': 'defesas_respostas',
        'icon': 'UserX',
        'color': '#B91C1C',
        'legal_basis': 'CPC/2015, arts. 144-148; CF/88, art. 5º, XXXVII',
        'display_order': 43,
    },
    {
        'code': 'assistencia_litisconsorcial',
        'name': 'Assistência Litisconsorcial/Simples',
        'short_name': 'Assistência',
        'description': 'Pedido de intervenção como assistente litisconsorcial ou simples',
        'category': 'acoes_peticoes',
        'icon': 'UserPlus',
        'color': '#059669',
        'legal_basis': 'CPC/2015, arts. 119-124',
        'display_order': 44,
    },
    # Direito Desportivo
    {
        'code': 'recurso_stjd',
        'name': 'Recurso ao STJD',
        'short_name': 'Recurso STJD',
        'description': 'Recurso à instância superior do Superior Tribunal de Justiça Desportiva',
        'category': 'desportivo',
        'icon': 'Trophy',
        'color': '#EA580C',
        'legal_basis': 'Lei 9.615/1998 (Lei Pelé); CBJD (Código Brasileiro de Justiça Desportiva)',
        'display_order': 45,
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

USER_TEMPLATE_SECAO = """Gere o conteúdo da seção "{{section_name}}" para a seguinte peça jurídica:

OBJETIVO DO DOCUMENTO: {{objective}}
INFORMAÇÕES DO CASO: {{context}}
SEÇÕES ANTERIORES JÁ GERADAS: {{previous_sections}}

Instruções específicas: {{instructions}}

Gere apenas o conteúdo desta seção, com linguagem jurídica formal e completa."""

CONST_ANTI_ALUCINACAO = """DIRETRIZES DE SEGURANÇA JURÍDICA — OBRIGATÓRIAS:
- NUNCA invente acórdão, número de processo, relator, Súmula ou OJ inexistentes
- Dado faltante: [INFORMAÇÃO NECESSÁRIA: descrição]
- Jurisprudência: [PESQUISAR JURISPRUDÊNCIA: tema]
- Conteúdo inferido: [SUGESTÃO DA IA - VERIFICAR COM ADVOGADO]
"""

PROMPT_GERADOR_ESPECIALIZADO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em diversas áreas do Direito brasileiro, incluindo Juizados Especiais, Direito Agrário, Direito Sanitário, Direito Administrativo, Direito Constitucional e Direito Desportivo.

LEGISLAÇÃO VIGENTE:
- CF/88; CPC/2015; CC/2002
- Lei 9.099/1995 (Juizados Especiais Cíveis)
- Lei 12.153/2009 (Juizados Especiais da Fazenda Pública)
- Lei 6.969/1981 (Usucapião Especial Rural)
- Lei 8.080/1990 (SUS)
- Lei 8.429/1992 (Improbidade Administrativa, alterada pela Lei 14.230/2021)
- DL 3.365/1941 (Desapropriação)
- Lei 12.016/2009 (Mandado de Segurança)
- Lei 9.615/1998 (Lei Pelé)
- CBJD (Código Brasileiro de Justiça Desportiva)

REGRAS ESSENCIAIS:
1. Juizados Especiais: linguagem acessível, procedimento simplificado (Lei 9.099/95)
2. JEFaz: valor até 60 salários mínimos, entes públicos como réus (Lei 12.153/2009)
3. Usucapião rural: área até 50ha, posse produtiva, moradia (CF art. 191)
4. Medicamentos SUS: direito à saúde (CF arts. 6º e 196), responsabilidade solidária dos entes
5. Improbidade: dolo obrigatório (Lei 14.230/2021), tipicidade dos arts. 9, 10 e 11
6. Desapropriação: justa e prévia indenização em dinheiro (CF art. 5º, XXIV)
7. MS Coletivo: legitimidade restrita (CF art. 5º, LXX)
8. Justiça Desportiva: esgotamento obrigatório da instância desportiva (CF art. 217, §1º)
9. Jurisprudência: Súmulas STJ/STF apenas. Acórdãos: [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

# ─────────────────────────────────────────────────────────────────────────────
# AGENTE POR TIPO DE DOCUMENTO
# ─────────────────────────────────────────────────────────────────────────────

AGENTE_POR_TIPO = {
    'peticao_jec': 'gerador_especializado_complementar',
    'recurso_inominado': 'gerador_especializado_complementar',
    'pedido_contraposto_jec': 'gerador_especializado_complementar',
    'peticao_jefaz': 'gerador_especializado_complementar',
    'usucapiao_rural': 'gerador_especializado_complementar',
    'possessoria_rural': 'gerador_especializado_complementar',
    'acao_medicamento_sus': 'gerador_especializado_complementar',
    'acao_improbidade': 'gerador_especializado_complementar',
    'acao_desapropriacao': 'gerador_especializado_complementar',
    'contestacao_desapropriacao': 'gerador_especializado_complementar',
    'mandado_seguranca_coletivo': 'gerador_especializado_complementar',
    'embargos_arrematacao': 'gerador_especializado_complementar',
    'conflito_competencia': 'gerador_especializado_complementar',
    'excecao_suspeicao': 'gerador_especializado_complementar',
    'assistencia_litisconsorcial': 'gerador_especializado_complementar',
    'recurso_stjd': 'gerador_especializado_complementar',
}

# ─────────────────────────────────────────────────────────────────────────────
# MAPEAMENTO: doc_type_code → lista de codes de categorias (areas) extras
# ─────────────────────────────────────────────────────────────────────────────

AREAS_EXTRAS = {
    # JEFaz → acoes_peticoes (primária) + administrativo
    'peticao_jefaz': ['administrativo'],
    # Agrário → agrario (primária) + imobiliario
    'usucapiao_rural': ['imobiliario'],
    'possessoria_rural': ['imobiliario'],
    # Sanitário → acoes_peticoes (primária) + administrativo
    'acao_medicamento_sus': ['administrativo'],
    # Desapropriação
    'acao_desapropriacao': ['imobiliario'],
    'contestacao_desapropriacao': ['administrativo'],
    # MS Coletivo → acoes_peticoes (primária) + constitucional
    'mandado_seguranca_coletivo': ['constitucional'],
    # Execução tributária complemento
    'embargos_arrematacao': [],
    # Desportivo → desportivo (primária) + recursos
    'recurso_stjd': ['recursos'],
}

# ─────────────────────────────────────────────────────────────────────────────
# BLUEPRINTS
# ─────────────────────────────────────────────────────────────────────────────

BLUEPRINTS_DATA = [
    # ──────────────────────────────────────────────────────────────────────
    # 1. PETIÇÃO INICIAL JEC
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'peticao_jec',
        'name': 'Petição Inicial - Juizado Especial Cível (Lei 9.099/95)',
        'description': 'Petição inicial simplificada para Juizado Especial Cível, com valor da causa até 40 salários mínimos',
        'version': '1.0',
        'legal_basis': 'Lei 9.099/1995, arts. 14-19; CF/88, art. 98, I',
        'primary_color': '#2563EB',
        'secondary_color': '#3B82F6',
        'cover_title': 'Petição Inicial - JEC',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento_juizado',
                'name': 'Endereçamento ao Juizado Especial',
                'description': 'Endereçamento ao Juizado Especial Cível competente',
                'instructions': 'Endereçe ao Juizado Especial Cível da Comarca competente (Lei 9.099/95, art. 4º). Identifique a competência: domicílio do réu, local da obrigação ou local do fato/dano. Lembre que nos JECs não há necessidade de advogado para causas de até 20 salários mínimos (art. 9º).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca / Foro', 'type': 'text', 'required': True},
                    {'name': 'juizado', 'label': 'Juizado Especial Cível (nº, se conhecido)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao_simplificada',
                'name': 'Qualificação Simplificada das Partes',
                'description': 'Qualificação das partes em formato simplificado',
                'instructions': 'Qualifique as partes de forma simplificada, conforme procedimento sumaríssimo dos Juizados Especiais (Lei 9.099/95, art. 14, §1º). Inclua: nome completo, CPF/CNPJ, endereço e contato. Partes vedadas: incapazes, presos, pessoas jurídicas de direito público, empresas públicas da União, massa falida e insolvente civil (art. 8º, §1º).',
                'fields': [
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'autor_cpf', 'label': 'CPF/CNPJ do Autor', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu', 'type': 'text', 'required': True},
                    {'name': 'reu_cpf', 'label': 'CPF/CNPJ do Réu', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'fatos',
                'name': 'I - Dos Fatos',
                'description': 'Narração dos fatos em linguagem acessível',
                'instructions': 'Narre os fatos em linguagem clara, acessível e objetiva, conforme o espírito simplificado dos Juizados Especiais (Lei 9.099/95, arts. 2º e 14). Evite termos excessivamente técnicos. Descreva cronologicamente o que ocorreu, as tentativas de resolução extrajudicial e o prejuízo sofrido pelo autor.',
                'fields': [
                    {'name': 'descricao_fatos', 'label': 'Descrição dos Fatos', 'type': 'textarea', 'required': True},
                    {'name': 'tentativa_resolucao', 'label': 'Tentativas de Resolução Extrajudicial', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'II - Da Fundamentação Jurídica Sucinta',
                'description': 'Fundamentação jurídica de forma sucinta',
                'instructions': 'Apresente a fundamentação jurídica de forma sucinta e direta. Cite a legislação aplicável ao caso (CDC, CC, legislação especial). Nos JECs preza-se pela oralidade e simplicidade (art. 2º), portanto a fundamentação deve ser objetiva e facilmente compreensível.',
                'fields': [
                    {'name': 'fundamento_legal', 'label': 'Fundamentação Legal Aplicável', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'valor_causa',
                'name': 'III - Do Valor da Causa',
                'description': 'Valor da causa limitado a 40 salários mínimos',
                'instructions': 'Indique o valor da causa, que deve ser limitado a 40 salários mínimos (Lei 9.099/95, art. 3º, I). Para causas de até 20 salários mínimos, a assistência de advogado é facultativa (art. 9º). Demonstre a composição do valor pleiteado: danos materiais, morais, restituição, etc.',
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                    {'name': 'composicao_valor', 'label': 'Composição do Valor (materiais, morais, etc.)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos certos e determinados',
                'instructions': 'Formule os pedidos de forma clara e determinada (art. 14, §2º). Inclua: citação do réu para audiência de conciliação (art. 16), pedido principal (condenação, obrigação, declaração), pedidos acessórios (juros, correção, honorários). Lembre que nos JECs a sentença é irrecorrível se não impugnada por recurso inominado em 10 dias (art. 42).',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_danos_morais', 'label': 'Pedido de Danos Morais (R$)', 'type': 'text', 'required': False},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 2. RECURSO INOMINADO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'recurso_inominado',
        'name': 'Recurso Inominado - Turma Recursal (Lei 9.099/95)',
        'description': 'Recurso contra sentença de Juizado Especial Cível dirigido à Turma Recursal',
        'version': '1.0',
        'legal_basis': 'Lei 9.099/1995, arts. 41-46',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Recurso Inominado',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento à Turma Recursal',
                'description': 'Endereçamento à Turma Recursal competente',
                'instructions': 'Endereçe à Turma Recursal do Juizado Especial Cível competente. Identifique o processo de origem, a data da sentença recorrida e o prazo recursal (10 dias da ciência da sentença, art. 42). O recurso deve ser acompanhado do preparo (art. 42, §1º), salvo se o recorrente for beneficiário da gratuidade de justiça.',
                'fields': [
                    {'name': 'turma_recursal', 'label': 'Turma Recursal', 'type': 'text', 'required': True},
                    {'name': 'processo_origem', 'label': 'Número do Processo de Origem', 'type': 'text', 'required': True},
                    {'name': 'recorrente_nome', 'label': 'Nome do Recorrente', 'type': 'text', 'required': True},
                    {'name': 'recorrido_nome', 'label': 'Nome do Recorrido', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'decisao_recorrida',
                'name': 'I - Da Decisão Recorrida',
                'description': 'Síntese da sentença impugnada',
                'instructions': 'Apresente a síntese da sentença recorrida: dispositivo, fundamentos do juízo a quo e resultado. Indique se a sentença foi de procedência, improcedência ou parcial procedência. Descreva os pontos específicos que serão impugnados no recurso.',
                'fields': [
                    {'name': 'data_sentenca', 'label': 'Data da Sentença', 'type': 'text', 'required': True},
                    {'name': 'resultado_sentenca', 'label': 'Resultado da Sentença', 'type': 'select', 'required': True, 'options': ['Procedente', 'Improcedente', 'Parcialmente Procedente']},
                    {'name': 'sintese_sentenca', 'label': 'Síntese da Sentença Recorrida', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'razoes_recurso',
                'name': 'II - Das Razões do Recurso',
                'description': 'Fundamentação recursal',
                'instructions': 'Apresente as razões recursais de forma clara e objetiva. Demonstre o erro da sentença: erro de fato (apreciação equivocada das provas) ou erro de direito (aplicação incorreta da lei). A Turma Recursal rejulga tanto fatos quanto direito (efeito devolutivo amplo). Cite a legislação e jurisprudência das Turmas Recursais aplicáveis.',
                'fields': [
                    {'name': 'razoes', 'label': 'Razões do Recurso', 'type': 'textarea', 'required': True},
                    {'name': 'erro_sentenca', 'label': 'Tipo de Erro da Sentença', 'type': 'select', 'required': True, 'options': ['Erro de fato (valoração da prova)', 'Erro de direito (aplicação da lei)', 'Ambos (fato e direito)']},
                ],
            },
            {
                'number': 4, 'key': 'pedido',
                'name': 'III - Do Pedido',
                'description': 'Pedido de reforma ou anulação da sentença',
                'instructions': 'Formule o pedido recursal: recebimento do recurso, reforma total ou parcial da sentença, ou anulação para novo julgamento. Indique expressamente o que se pretende da Turma Recursal. Se houver pedido de efeito suspensivo, fundamente a urgência (art. 43).',
                'fields': [
                    {'name': 'tipo_pedido', 'label': 'Tipo de Pedido', 'type': 'select', 'required': True, 'options': ['Reforma total da sentença', 'Reforma parcial da sentença', 'Anulação da sentença', 'Reforma com efeito suspensivo']},
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 3. PEDIDO CONTRAPOSTO JEC
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'pedido_contraposto_jec',
        'name': 'Pedido Contraposto - Juizado Especial Cível',
        'description': 'Contestação com pedido contraposto no JEC (Lei 9.099/95, art. 31)',
        'version': '1.0',
        'legal_basis': 'Lei 9.099/1995, art. 31',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Pedido Contraposto - JEC',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao Juizado Especial',
                'instructions': 'Endereçe ao Juizado Especial Cível onde tramita a ação. Identifique o processo, o autor original (ora réu contraposto) e o réu original (ora autor contraposto). O pedido contraposto é formulado na própria contestação, sem necessidade de reconvenção autônoma (art. 31).',
                'fields': [
                    {'name': 'juizado', 'label': 'Juizado Especial Cível', 'type': 'text', 'required': True},
                    {'name': 'processo', 'label': 'Número do Processo', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu (Contestante)', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Originário)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'contestacao',
                'name': 'I - Da Contestação',
                'description': 'Defesa aos fatos e fundamentos do autor',
                'instructions': 'Apresente a contestação aos fatos e fundamentos da petição inicial. Impugne especificamente cada fato narrado pelo autor. Levante preliminares se cabíveis (incompetência, ilegitimidade, litispendência, coisa julgada). Ataque o mérito demonstrando a improcedência da pretensão autoral.',
                'fields': [
                    {'name': 'preliminares', 'label': 'Preliminares (se houver)', 'type': 'textarea', 'required': False},
                    {'name': 'contestacao_merito', 'label': 'Contestação ao Mérito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedido_contraposto',
                'name': 'II - Do Pedido Contraposto',
                'description': 'Pedido contraposto fundado nos mesmos fatos',
                'instructions': 'Formule o pedido contraposto nos termos do art. 31 da Lei 9.099/95. O pedido contraposto deve ser fundado nos mesmos fatos que constituem objeto da controvérsia. Descreva o direito do réu que decorre dos mesmos fatos narrados na inicial e que justifica a pretensão contra o autor.',
                'fields': [
                    {'name': 'fatos_contraposto', 'label': 'Fatos que Fundamentam o Pedido Contraposto', 'type': 'textarea', 'required': True},
                    {'name': 'valor_contraposto', 'label': 'Valor do Pedido Contraposto (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'III - Da Fundamentação',
                'description': 'Fundamentação jurídica do pedido contraposto',
                'instructions': 'Fundamente juridicamente o pedido contraposto. Demonstre o direito do réu à pretensão formulada, com base na legislação e jurisprudência aplicáveis. Lembre que o pedido contraposto é uma forma simplificada de reconvenção, própria dos Juizados Especiais.',
                'fields': [
                    {'name': 'fundamento_legal', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos finais (contestação + contraposto)',
                'instructions': 'Formule os pedidos finais: improcedência da ação principal e procedência do pedido contraposto. Pedidos: rejeição dos pedidos do autor, condenação do autor no pedido contraposto, honorários e custas.',
                'fields': [
                    {'name': 'pedido_improcedencia', 'label': 'Pedido de Improcedência da Ação', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_contraposto_final', 'label': 'Pedido Contraposto Final', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 4. PETIÇÃO JEFaz
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'peticao_jefaz',
        'name': 'Petição Inicial - Juizado Especial da Fazenda Pública (Lei 12.153/2009)',
        'description': 'Petição inicial para o Juizado Especial da Fazenda Pública com valor até 60 salários mínimos',
        'version': '1.0',
        'legal_basis': 'Lei 12.153/2009; Lei 9.099/1995 (subsidiária)',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Petição Inicial - JEFaz',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao Juizado Especial da Fazenda Pública',
                'instructions': 'Endereçe ao Juizado Especial da Fazenda Pública competente (Lei 12.153/2009, art. 2º). A competência é absoluta e abrange causas de até 60 salários mínimos contra Estados, DF, Territórios, Municípios, autarquias, fundações e empresas públicas (art. 5º).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca / Foro', 'type': 'text', 'required': True},
                    {'name': 'juizado', 'label': 'Juizado Especial da Fazenda Pública', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Qualificação do autor e do ente público réu',
                'instructions': 'Qualifique o autor com dados completos (nome, CPF, endereço). Identifique o ente público réu: Estado, Município, autarquia, fundação ou empresa pública a ser demandada. Não são admitidas ações contra a União Federal nos JEFaz (competência dos JEFs, Lei 10.259/2001).',
                'fields': [
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'autor_cpf', 'label': 'CPF do Autor', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'ente_publico',
                'name': 'I - Do Ente Público Réu',
                'description': 'Identificação e legitimidade do ente público réu',
                'instructions': 'Identifique o ente público réu com seu CNPJ e endereço da sede administrativa. Demonstre a legitimidade passiva do ente para responder à demanda. Indique o representante legal para citação e o endereço da Procuradoria responsável.',
                'fields': [
                    {'name': 'ente_publico_nome', 'label': 'Nome do Ente Público Réu', 'type': 'text', 'required': True},
                    {'name': 'tipo_ente', 'label': 'Tipo de Ente Público', 'type': 'select', 'required': True, 'options': ['Estado', 'Município', 'Autarquia', 'Fundação Pública', 'Empresa Pública']},
                    {'name': 'endereco_citacao', 'label': 'Endereço para Citação / Procuradoria', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'fatos',
                'name': 'II - Dos Fatos',
                'description': 'Narração dos fatos',
                'instructions': 'Narre os fatos de forma clara e objetiva. Descreva a relação jurídica com o ente público, o ato administrativo impugnado (se houver), o direito violado e as tentativas de resolução administrativa prévia. Inclua datas, protocolos e referências documentais.',
                'fields': [
                    {'name': 'descricao_fatos', 'label': 'Descrição dos Fatos', 'type': 'textarea', 'required': True},
                    {'name': 'protocolo_administrativo', 'label': 'Protocolo Administrativo (se houver)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'III - Da Fundamentação Jurídica',
                'description': 'Fundamentação jurídica da pretensão',
                'instructions': 'Fundamente juridicamente a pretensão contra o ente público. Cite a legislação aplicável (CF, legislação administrativa, legislação especial). Aborde a responsabilidade do Estado (CF art. 37, §6º) se aplicável. Mencione os princípios da Administração Pública (legalidade, impessoalidade, moralidade, publicidade, eficiência).',
                'fields': [
                    {'name': 'fundamento_legal', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'valor_causa',
                'name': 'IV - Do Valor da Causa',
                'description': 'Valor da causa limitado a 60 salários mínimos',
                'instructions': 'Indique o valor da causa, que deve ser limitado a 60 salários mínimos (Lei 12.153/2009, art. 2º). Demonstre a composição do valor. A renúncia ao excedente deve ser expressa quando o valor real ultrapassar o teto (art. 2º, §4º).',
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                    {'name': 'renuncia_excedente', 'label': 'Renúncia ao Excedente?', 'type': 'select', 'required': True, 'options': ['Não se aplica (valor dentro do teto)', 'Sim, renuncia ao excedente de 60 SM']},
                ],
            },
            {
                'number': 7, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedidos ao Juizado da Fazenda',
                'instructions': 'Formule os pedidos de forma clara: citação do ente público (por oficial de justiça ou correio com AR), pedido principal (condenação, obrigação de fazer, anulação de ato), pedidos acessórios (juros de mora, correção monetária). Lembre que o cumprimento de sentença contra a Fazenda segue regime de RPV (até 60 SM) e não precatório (art. 13).',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_tutela', 'label': 'Pedido de Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (fundamentar urgência)']},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 5. USUCAPIÃO RURAL
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'usucapiao_rural',
        'name': 'Usucapião Rural/Constitucional - CF art. 191',
        'description': 'Ação de usucapião especial rural (pro labore) para áreas de até 50 hectares',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 191; Lei 6.969/1981; CC/2002, art. 1.239',
        'primary_color': '#16A34A',
        'secondary_color': '#22C55E',
        'cover_title': 'Usucapião Rural',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e qualificação das partes',
                'instructions': 'Endereçe ao Juízo da Vara Cível da Comarca onde se situa o imóvel (CPC art. 47 - competência absoluta). Qualifique o autor/requerente (posseiro) e eventuais réus (proprietários registrais, confrontantes). Se o imóvel for público, a usucapião especial rural pode incidir sobre terras devolutas (Lei 6.969/81, art. 2º).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca (localização do imóvel)', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Posseiro)', 'type': 'text', 'required': True},
                    {'name': 'proprietario_registral', 'label': 'Proprietário Registral (se conhecido)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'imovel_rural',
                'name': 'I - Do Imóvel Rural',
                'description': 'Descrição detalhada do imóvel rural',
                'instructions': 'Descreva detalhadamente o imóvel rural: localização (município, distrito, gleba), área em hectares (deve ser até 50ha, conforme CF art. 191), limites e confrontações, matrícula/transcrição no Registro de Imóveis (se existir). Indique se há georreferenciamento (INCRA/SIGEF) e certificação do imóvel rural.',
                'fields': [
                    {'name': 'localizacao_imovel', 'label': 'Localização do Imóvel Rural', 'type': 'textarea', 'required': True},
                    {'name': 'area_hectares', 'label': 'Área em Hectares (até 50ha)', 'type': 'text', 'required': True},
                    {'name': 'matricula', 'label': 'Matrícula / Transcrição no RI', 'type': 'text', 'required': False},
                    {'name': 'ccir', 'label': 'CCIR / Cadastro INCRA', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'posse_produtiva',
                'name': 'II - Da Posse Produtiva e Moradia',
                'description': 'Demonstração da posse produtiva e moradia',
                'instructions': 'Demonstre os requisitos da usucapião especial rural (CF art. 191): posse ininterrupta e sem oposição por cinco anos, de área rural de até cinquenta hectares, tornando-a produtiva por seu trabalho ou de sua família, e tendo nela sua moradia. O possuidor não pode ser proprietário de outro imóvel rural ou urbano. Descreva as atividades produtivas desenvolvidas (agricultura, pecuária, extrativismo) e a moradia estabelecida.',
                'fields': [
                    {'name': 'tempo_posse', 'label': 'Tempo de Posse (anos)', 'type': 'text', 'required': True},
                    {'name': 'atividade_produtiva', 'label': 'Atividade Produtiva Desenvolvida', 'type': 'textarea', 'required': True},
                    {'name': 'moradia', 'label': 'Descrição da Moradia no Imóvel', 'type': 'textarea', 'required': True},
                    {'name': 'possui_outro_imovel', 'label': 'Possui Outro Imóvel?', 'type': 'select', 'required': True, 'options': ['Não possui outro imóvel rural ou urbano', 'Não aplicável']},
                ],
            },
            {
                'number': 4, 'key': 'area_limite',
                'name': 'III - Da Área (até 50ha)',
                'description': 'Comprovação do limite constitucional de 50 hectares',
                'instructions': 'Demonstre que a área objeto da usucapião não excede o limite constitucional de 50 hectares (CF art. 191). Apresente referência à planta e memorial descritivo elaborados por profissional habilitado (engenheiro agrimensor ou topógrafo). Cite eventual certificação pelo INCRA.',
                'fields': [
                    {'name': 'area_exata', 'label': 'Área Exata Levantada (ha)', 'type': 'text', 'required': True},
                    {'name': 'profissional_levantamento', 'label': 'Profissional Responsável pelo Levantamento', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'IV - Da Fundamentação Jurídica',
                'description': 'Fundamentação constitucional e legal',
                'instructions': 'Fundamente com base no art. 191 da CF/88 (usucapião especial rural), art. 1.239 do CC/2002, Lei 6.969/1981 e CPC/2015 arts. 246 e 259 (ação de usucapião). Cite a função social da propriedade rural (CF art. 186). Se aplicável, mencione o Estatuto da Terra (Lei 4.504/1964). Aborde a questão registral e a sentença como título hábil para registro (CPC art. 1.071 c/c LRP art. 167, I, 28).',
                'fields': [
                    {'name': 'fundamento_complementar', 'label': 'Fundamentos Complementares', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedido de declaração de domínio',
                'instructions': 'Formule os pedidos: citação dos réus (proprietário registral, confrontantes) e intimação do Ministério Público, da Fazenda Pública (União, Estado e Município) e eventual interessado. Pedido principal: declaração de domínio do imóvel por usucapião especial rural, expedição de mandado para registro junto ao Cartório de Registro de Imóveis. Pedido de justiça gratuita se cabível.',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'justica_gratuita', 'label': 'Pedido de Justiça Gratuita?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 6. AÇÃO POSSESSÓRIA RURAL
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'possessoria_rural',
        'name': 'Ação Possessória Rural - CPC/2015',
        'description': 'Ação de reintegração de posse, manutenção de posse ou interdito proibitório de imóvel rural',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 554-568; Lei 8.629/1993; Estatuto da Terra',
        'primary_color': '#16A34A',
        'secondary_color': '#22C55E',
        'cover_title': 'Ação Possessória Rural',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e qualificação das partes',
                'instructions': 'Endereçe ao Juízo da Vara Cível ou Vara Agrária (se existir) da Comarca onde se situa o imóvel rural. Qualifique o autor (possuidor) e o réu (esbulhador/turbador). Em ações possessórias de imóvel rural, se envolver grande número de pessoas, deve haver prévia tentativa de conciliação e intimação do MP (CPC art. 554).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Possuidor)', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'imovel_rural',
                'name': 'I - Do Imóvel Rural',
                'description': 'Descrição do imóvel rural objeto da posse',
                'instructions': 'Descreva o imóvel rural: localização, área, limites e confrontações, matrícula no RI. Indique a destinação do imóvel (produção agrícola, pecuária, extrativismo, moradia). Apresente referência documental da posse (contrato, escritura, declaração de ITR, CCIR).',
                'fields': [
                    {'name': 'descricao_imovel', 'label': 'Descrição do Imóvel Rural', 'type': 'textarea', 'required': True},
                    {'name': 'area', 'label': 'Área (hectares)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'posse',
                'name': 'II - Da Posse',
                'description': 'Demonstração da posse do autor',
                'instructions': 'Demonstre a posse do autor sobre o imóvel rural: data de início, forma de aquisição (originária ou derivada), exercício contínuo de atos possessórios (cultivo, cercamento, construção, moradia). Comprove a posse com documentos, testemunhas e eventuais fotografias.',
                'fields': [
                    {'name': 'data_inicio_posse', 'label': 'Data de Início da Posse', 'type': 'text', 'required': True},
                    {'name': 'forma_aquisicao', 'label': 'Forma de Aquisição da Posse', 'type': 'text', 'required': True},
                    {'name': 'atos_possessorios', 'label': 'Atos Possessórios Exercidos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'esbulho_turbacao',
                'name': 'III - Do Esbulho/Turbação',
                'description': 'Descrição do esbulho ou turbação sofridos',
                'instructions': 'Descreva detalhadamente o ato de esbulho (perda da posse), turbação (perturbação da posse) ou ameaça (interdito proibitório). Indique: data do ato, forma como ocorreu, autor(es) do esbulho/turbação, prejuízos causados. Se a ação for de força nova (até 1 ano e dia), demonstre a tempestividade para obter liminar (CPC art. 558).',
                'fields': [
                    {'name': 'tipo_violacao', 'label': 'Tipo de Violação', 'type': 'select', 'required': True, 'options': ['Esbulho (perda total da posse)', 'Turbação (perturbação parcial)', 'Ameaça (interdito proibitório)']},
                    {'name': 'data_esbulho', 'label': 'Data do Esbulho/Turbação/Ameaça', 'type': 'text', 'required': True},
                    {'name': 'descricao_violacao', 'label': 'Descrição Detalhada da Violação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'tutela_urgencia',
                'name': 'IV - Da Tutela de Urgência',
                'description': 'Pedido liminar de reintegração/manutenção',
                'instructions': 'Fundamente o pedido liminar possessório (CPC arts. 558-559). Para ação de força nova (até 1 ano e dia), demonstre: posse, turbação ou esbulho, data e perda da posse. Demonstre o periculum in mora: risco de dano irreparável, perda de safra, destruição de benfeitorias, deterioração do imóvel. Se ação de força velha, fundamente a tutela com base no CPC art. 300.',
                'fields': [
                    {'name': 'forca_nova', 'label': 'Ação de Força Nova (até 1 ano e dia)?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (força velha)']},
                    {'name': 'urgencia', 'label': 'Fundamentação da Urgência', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedido de proteção possessória',
                'instructions': 'Formule os pedidos: concessão de liminar de reintegração/manutenção de posse (ou interdito proibitório), citação do réu, confirmação da liminar em sentença, condenação do réu em perdas e danos (CPC art. 555), cominação de multa diária em caso de descumprimento, honorários e custas.',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'perdas_danos', 'label': 'Pedido de Perdas e Danos (R$)', 'type': 'text', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 7. AÇÃO DE FORNECIMENTO DE MEDICAMENTO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'acao_medicamento_sus',
        'name': 'Ação de Fornecimento de Medicamento/Tratamento - SUS',
        'description': 'Ação judicial para obrigar o Poder Público a fornecer medicamento ou tratamento de saúde',
        'version': '1.0',
        'legal_basis': 'CF/88, arts. 6º e 196; Lei 8.080/1990; STF Tema 793',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Ação de Fornecimento de Medicamento',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e qualificação das partes',
                'instructions': 'Endereçe ao Juízo competente (Vara da Fazenda Pública ou Vara Federal, conforme o ente demandado). Qualifique o autor (paciente). Identifique o(s) réu(s): responsabilidade solidária entre União, Estado e Município (STF Tema 793). Inclua a Secretaria de Saúde competente.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Paciente)', 'type': 'text', 'required': True},
                    {'name': 'entes_reus', 'label': 'Ente(s) Público(s) Réu(s)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'doenca_cid',
                'name': 'I - Da Doença e do Diagnóstico',
                'description': 'Descrição da doença e diagnóstico clínico',
                'instructions': 'Descreva a doença do paciente, incluindo o CID (Classificação Internacional de Doenças). Relate o histórico clínico, tratamentos anteriores realizados, evolução do quadro e prognóstico. Demonstre a gravidade da situação e a necessidade do tratamento pleiteado.',
                'fields': [
                    {'name': 'doenca', 'label': 'Doença / Patologia', 'type': 'text', 'required': True},
                    {'name': 'cid', 'label': 'CID (Código Internacional de Doenças)', 'type': 'text', 'required': True},
                    {'name': 'historico_clinico', 'label': 'Histórico Clínico e Tratamentos Anteriores', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'medicamento',
                'name': 'II - Do Medicamento/Tratamento Prescrito',
                'description': 'Identificação do medicamento ou tratamento necessário',
                'instructions': 'Identifique o medicamento ou tratamento prescrito: nome comercial e princípio ativo, posologia, duração do tratamento. Informe se o medicamento consta das listas oficiais do SUS (RENAME/REMUME) ou se é de uso off-label. Em caso de medicamento não padronizado, demonstre os requisitos do STJ Tema 106: imprescindibilidade, ineficácia dos medicamentos disponíveis no SUS e impossibilidade financeira do paciente.',
                'fields': [
                    {'name': 'medicamento_nome', 'label': 'Nome do Medicamento / Tratamento', 'type': 'text', 'required': True},
                    {'name': 'principio_ativo', 'label': 'Princípio Ativo', 'type': 'text', 'required': True},
                    {'name': 'posologia', 'label': 'Posologia e Duração do Tratamento', 'type': 'text', 'required': True},
                    {'name': 'consta_rename', 'label': 'Consta nas Listas Oficiais do SUS?', 'type': 'select', 'required': True, 'options': ['Sim (RENAME/REMUME)', 'Não (medicamento não padronizado)']},
                ],
            },
            {
                'number': 4, 'key': 'laudo_medico',
                'name': 'III - Do Laudo Médico',
                'description': 'Referência ao laudo médico que embasa a pretensão',
                'instructions': 'Faça referência ao laudo médico que prescreve o medicamento/tratamento. O laudo deve conter: diagnóstico com CID, indicação do medicamento com posologia, justificativa da prescrição (por que o medicamento/tratamento é necessário), ineficácia de alternativas terapêuticas disponíveis no SUS e assinatura do médico com CRM.',
                'fields': [
                    {'name': 'medico_nome', 'label': 'Nome do Médico Prescritor', 'type': 'text', 'required': True},
                    {'name': 'crm', 'label': 'CRM', 'type': 'text', 'required': True},
                    {'name': 'justificativa_medica', 'label': 'Justificativa Médica para o Tratamento', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'recusa_administrativa',
                'name': 'IV - Da Recusa Administrativa',
                'description': 'Demonstração da negativa administrativa',
                'instructions': 'Demonstre a recusa ou omissão do Poder Público em fornecer o medicamento/tratamento. Apresente referência ao protocolo administrativo de solicitação, resposta da Secretaria de Saúde (se houver) e prazo transcorrido sem atendimento. Se não houve requerimento administrativo prévio, justifique a urgência que dispensa essa exigência.',
                'fields': [
                    {'name': 'protocolo_solicitacao', 'label': 'Protocolo de Solicitação Administrativa', 'type': 'text', 'required': False},
                    {'name': 'recusa_descricao', 'label': 'Descrição da Recusa/Omissão', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'tutela_urgencia',
                'name': 'V - Da Tutela de Urgência',
                'description': 'Pedido liminar de fornecimento imediato',
                'instructions': 'Fundamente o pedido de tutela de urgência (CPC art. 300): probabilidade do direito (direito à saúde, CF arts. 6º e 196) e perigo de dano irreparável (risco de agravamento da doença, risco de morte). Demonstre que a demora pode comprometer a saúde ou a vida do paciente. Cite jurisprudência consolidada sobre fornecimento de medicamentos.',
                'fields': [
                    {'name': 'risco_saude', 'label': 'Risco à Saúde / Vida do Paciente', 'type': 'textarea', 'required': True},
                    {'name': 'prazo_necessidade', 'label': 'Prazo de Necessidade do Tratamento', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 7, 'key': 'pedido',
                'name': 'VI - Do Pedido',
                'description': 'Pedidos de fornecimento de medicamento',
                'instructions': 'Formule os pedidos: concessão de tutela de urgência para fornecimento imediato do medicamento/tratamento em prazo de 48/72 horas, sob pena de multa diária e bloqueio de verbas públicas; citação do(s) ente(s) público(s); confirmação da tutela em sentença definitiva; condenação em honorários e custas. Se cabível, peça justiça gratuita.',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'multa_diaria', 'label': 'Multa Diária Sugerida (R$)', 'type': 'text', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 8. AÇÃO DE IMPROBIDADE ADMINISTRATIVA
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'acao_improbidade',
        'name': 'Ação de Improbidade Administrativa - Lei 8.429/1992',
        'description': 'Ação civil pública por ato de improbidade administrativa com pedido de sanções',
        'version': '1.0',
        'legal_basis': 'Lei 8.429/1992 (alt. Lei 14.230/2021); CF/88, art. 37, §4º',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Ação de Improbidade Administrativa',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação do Réu',
                'description': 'Juízo e identificação do agente público réu',
                'instructions': 'Endereçe ao Juízo da Vara da Fazenda Pública ou Vara Cível competente. A ação de improbidade é de competência do juízo de primeiro grau, salvo hipóteses de foro por prerrogativa de função (art. 22). Identifique e qualifique o(s) réu(s): agente(s) público(s) e eventuais particulares beneficiados ou partícipes (art. 3º). Identifique o legitimado ativo: Ministério Público ou pessoa jurídica interessada (art. 17).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'legitimado_ativo', 'label': 'Legitimado Ativo (MP ou PJ interessada)', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu (Agente Público)', 'type': 'text', 'required': True},
                    {'name': 'cargo_funcao', 'label': 'Cargo/Função do Agente Público', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'agente_publico',
                'name': 'I - Do Agente Público',
                'description': 'Identificação e vinculação funcional do agente',
                'instructions': 'Identifique detalhadamente o agente público (art. 2º): cargo, função ou mandato exercido, órgão ou entidade à qual está vinculado, período de exercício. Demonstre a vinculação funcional com a conduta ímproba. Se houver particulares coautores ou beneficiários, identifique-os e demonstre a participação (art. 3º).',
                'fields': [
                    {'name': 'orgao_entidade', 'label': 'Órgão/Entidade do Agente', 'type': 'text', 'required': True},
                    {'name': 'periodo_exercicio', 'label': 'Período de Exercício do Cargo', 'type': 'text', 'required': True},
                    {'name': 'particulares_coautores', 'label': 'Particulares Coautores/Beneficiários (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'ato_improbidade',
                'name': 'II - Do Ato de Improbidade (art. 9/10/11)',
                'description': 'Tipificação e descrição do ato de improbidade',
                'instructions': 'Tipifique o ato de improbidade administrativa conforme a Lei 8.429/1992 (com alterações da Lei 14.230/2021). Classifique em: art. 9º (enriquecimento ilícito), art. 10 (lesão ao erário) ou art. 11 (atentado contra princípios). ATENÇÃO: após a Lei 14.230/2021, é necessário demonstrar DOLO ESPECÍFICO para todos os tipos (art. 1º, §2º). Descreva a conduta com riqueza de detalhes: o que fez, quando, como, com qual objetivo ilícito.',
                'fields': [
                    {'name': 'tipo_improbidade', 'label': 'Tipo de Ato de Improbidade', 'type': 'select', 'required': True, 'options': ['Art. 9º - Enriquecimento Ilícito', 'Art. 10 - Lesão ao Erário', 'Art. 11 - Violação de Princípios']},
                    {'name': 'inciso_especifico', 'label': 'Inciso Específico', 'type': 'text', 'required': True},
                    {'name': 'descricao_conduta', 'label': 'Descrição Detalhada da Conduta', 'type': 'textarea', 'required': True},
                    {'name': 'dolo', 'label': 'Demonstração do Dolo (obrigatório pós Lei 14.230/2021)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'dano_erario',
                'name': 'III - Do Dano ao Erário',
                'description': 'Demonstração do dano ao patrimônio público',
                'instructions': 'Demonstre o dano ao erário, se aplicável (arts. 9º e 10). Quantifique o prejuízo aos cofres públicos: valores desviados, superfaturamento, contratações irregulares, perdas patrimoniais. Para atos do art. 11 (princípios), o dano pode ser presumido, mas deve-se demonstrar o nexo entre a conduta e a violação aos princípios da administração pública.',
                'fields': [
                    {'name': 'valor_dano', 'label': 'Valor Estimado do Dano ao Erário (R$)', 'type': 'text', 'required': False},
                    {'name': 'descricao_dano', 'label': 'Descrição do Dano ao Patrimônio Público', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'provas',
                'name': 'IV - Das Provas',
                'description': 'Conjunto probatório que sustenta a ação',
                'instructions': 'Apresente o conjunto probatório: documentos (contratos, notas fiscais, extratos bancários, relatórios de auditoria), depoimentos, perícias, inquérito civil do Ministério Público, procedimentos administrativos disciplinares, relatórios do Tribunal de Contas. Indique as provas que pretende produzir em juízo.',
                'fields': [
                    {'name': 'provas_documentais', 'label': 'Provas Documentais Reunidas', 'type': 'textarea', 'required': True},
                    {'name': 'provas_a_produzir', 'label': 'Provas a Produzir em Juízo', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido de Sanções',
                'description': 'Pedido de aplicação das sanções do art. 12',
                'instructions': 'Formule o pedido de aplicação das sanções previstas no art. 12 da Lei 8.429/1992 (com graduação da Lei 14.230/2021). Conforme o tipo: perda dos bens ou valores acrescidos ilicitamente, ressarcimento integral do dano, perda da função pública, suspensão dos direitos políticos (de 8 a 14 anos para art. 9º; de 4 a 12 anos para art. 10; de 1 a 4 anos para art. 11), multa civil e proibição de contratar com o Poder Público. Peça indisponibilidade de bens se cabível (art. 16).',
                'fields': [
                    {'name': 'sancoes_pleiteadas', 'label': 'Sanções Pleiteadas', 'type': 'textarea', 'required': True},
                    {'name': 'indisponibilidade_bens', 'label': 'Pedido de Indisponibilidade de Bens?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 9. AÇÃO DE DESAPROPRIAÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'acao_desapropriacao',
        'name': 'Ação de Desapropriação - DL 3.365/1941',
        'description': 'Ação de desapropriação por utilidade pública ou interesse social',
        'version': '1.0',
        'legal_basis': 'DL 3.365/1941; Lei 4.132/1962; CF/88, art. 5º, XXIV',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Ação de Desapropriação',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo competente',
                'instructions': 'Endereçe ao Juízo da Vara da Fazenda Pública ou Vara Federal competente, conforme o ente expropriante. O foro é o da situação do imóvel (DL 3.365/41, art. 11). Identifique o ente expropriante (União, Estado, Município, autarquia) e o decreto expropriatório que fundamenta a ação.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca / Seção Judiciária', 'type': 'text', 'required': True},
                    {'name': 'ente_expropriante', 'label': 'Ente Expropriante', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'ente_expropriante',
                'name': 'I - Do Ente Expropriante',
                'description': 'Identificação e legitimidade do ente expropriante',
                'instructions': 'Identifique o ente expropriante com seus dados cadastrais. Demonstre a competência para desapropriar: União, Estado, DF e Município (CF art. 184 para reforma agrária; art. 5º, XXIV, para utilidade pública). Apresente o decreto expropriatório: número, data, publicação no DO, fundamentação legal.',
                'fields': [
                    {'name': 'decreto_numero', 'label': 'Número do Decreto Expropriatório', 'type': 'text', 'required': True},
                    {'name': 'data_decreto', 'label': 'Data do Decreto', 'type': 'text', 'required': True},
                    {'name': 'publicacao_do', 'label': 'Data de Publicação no Diário Oficial', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'imovel',
                'name': 'II - Do Imóvel',
                'description': 'Descrição do imóvel objeto da desapropriação',
                'instructions': 'Descreva detalhadamente o imóvel objeto da desapropriação: localização, área, limites, confrontações, matrícula no RI, benfeitorias existentes. Para imóvel rural, indique os dados cadastrais do INCRA (CCIR, ITR). Para imóvel urbano, indique IPTU e dados da prefeitura.',
                'fields': [
                    {'name': 'descricao_imovel', 'label': 'Descrição do Imóvel', 'type': 'textarea', 'required': True},
                    {'name': 'matricula', 'label': 'Matrícula no Registro de Imóveis', 'type': 'text', 'required': True},
                    {'name': 'proprietario', 'label': 'Proprietário/Expropriado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'utilidade_publica',
                'name': 'III - Da Utilidade Pública/Interesse Social',
                'description': 'Fundamentação da utilidade pública ou interesse social',
                'instructions': 'Fundamente a necessidade/utilidade pública ou o interesse social que justifica a desapropriação (DL 3.365/41, art. 5º, ou Lei 4.132/62, art. 2º). Descreva o projeto ou finalidade a que se destina o imóvel. Demonstre que a desapropriação é o meio adequado e proporcional para atingir a finalidade pública.',
                'fields': [
                    {'name': 'fundamento_desapropriacao', 'label': 'Fundamento da Desapropriação', 'type': 'select', 'required': True, 'options': ['Utilidade Pública (DL 3.365/41)', 'Interesse Social (Lei 4.132/62)', 'Reforma Agrária (CF art. 184)']},
                    {'name': 'finalidade', 'label': 'Finalidade/Projeto', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'oferta_preco',
                'name': 'IV - Da Oferta de Preço',
                'description': 'Oferta de indenização prévia e justa',
                'instructions': 'Apresente a oferta de preço: valor da avaliação administrativa prévia, laudo de avaliação que embasa a oferta, critérios de avaliação utilizados (valor de mercado, benfeitorias, potencial econômico). A indenização deve ser justa, prévia e em dinheiro (CF art. 5º, XXIV), salvo reforma agrária (títulos da dívida agrária). Informe o depósito judicial da oferta (DL 3.365/41, art. 15).',
                'fields': [
                    {'name': 'valor_oferta', 'label': 'Valor da Oferta (R$)', 'type': 'text', 'required': True},
                    {'name': 'criterio_avaliacao', 'label': 'Critério de Avaliação Utilizado', 'type': 'textarea', 'required': True},
                    {'name': 'deposito_judicial', 'label': 'Depósito Judicial Efetuado?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (a ser efetuado)']},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido de Imissão na Posse',
                'description': 'Pedido de imissão provisória na posse e desapropriação',
                'instructions': 'Formule os pedidos: citação do expropriado, imissão provisória na posse (DL 3.365/41, art. 15, mediante depósito da oferta ou avaliação provisória), nomeação de perito para avaliação definitiva, decreto de desapropriação definitiva com fixação da justa indenização, expedição de mandado para averbação no Registro de Imóveis.',
                'fields': [
                    {'name': 'pedido_imissao', 'label': 'Pedido de Imissão Provisória na Posse?', 'type': 'select', 'required': True, 'options': ['Sim (art. 15 do DL 3.365/41)', 'Não']},
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 10. CONTESTAÇÃO EM DESAPROPRIAÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'contestacao_desapropriacao',
        'name': 'Contestação em Desapropriação',
        'description': 'Contestação do expropriado em ação de desapropriação, impugnando o valor da oferta',
        'version': '1.0',
        'legal_basis': 'DL 3.365/1941, art. 20; CF/88, art. 5º, XXIV',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Contestação em Desapropriação',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e identificação do expropriado',
                'instructions': 'Endereçe ao Juízo onde tramita a ação de desapropriação. Qualifique o expropriado (réu na desapropriação). Identifique o processo e o ente expropriante. Na contestação de desapropriação, a matéria de defesa é restrita: somente pode versar sobre vício do processo judicial ou impugnação do preço ofertado (DL 3.365/41, art. 20).',
                'fields': [
                    {'name': 'processo', 'label': 'Número do Processo', 'type': 'text', 'required': True},
                    {'name': 'expropriado_nome', 'label': 'Nome do Expropriado (Réu)', 'type': 'text', 'required': True},
                    {'name': 'ente_expropriante', 'label': 'Ente Expropriante (Autor)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'impugnacao_valor',
                'name': 'I - Da Impugnação do Valor Ofertado',
                'description': 'Impugnação do preço oferecido pelo expropriante',
                'instructions': 'Impugne o valor ofertado pelo ente expropriante. Demonstre que a oferta é insuficiente para constituir justa indenização (CF art. 5º, XXIV). Apresente avaliação divergente elaborada por profissional habilitado, indicando o valor de mercado real do imóvel, benfeitorias não computadas, potencial econômico do imóvel e depreciação desconsiderada.',
                'fields': [
                    {'name': 'valor_ofertado', 'label': 'Valor Ofertado pelo Expropriante (R$)', 'type': 'text', 'required': True},
                    {'name': 'valor_pretendido', 'label': 'Valor Pretendido pelo Expropriado (R$)', 'type': 'text', 'required': True},
                    {'name': 'fundamento_impugnacao', 'label': 'Fundamentos da Impugnação ao Valor', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'vicios_decreto',
                'name': 'II - Dos Vícios do Decreto Expropriatório',
                'description': 'Arguição de vícios no decreto de desapropriação',
                'instructions': 'Se cabível, argua vícios do decreto expropriatório ou do processo judicial: desvio de finalidade, caducidade do decreto (5 anos para utilidade pública, 2 anos para interesse social), nulidade formal, ausência de fundamentação, incompetência do ente. ATENÇÃO: embora o art. 20 do DL 3.365/41 restrinja a defesa ao preço, a jurisprudência admite discussão de vícios processuais e constitucionais.',
                'fields': [
                    {'name': 'vicios_identificados', 'label': 'Vícios Identificados (se houver)', 'type': 'textarea', 'required': False},
                    {'name': 'caducidade', 'label': 'Há Caducidade do Decreto?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (decreto expirado)']},
                ],
            },
            {
                'number': 4, 'key': 'laudo_divergente',
                'name': 'III - Do Laudo Divergente',
                'description': 'Laudo de avaliação divergente do expropriado',
                'instructions': 'Apresente referência ao laudo de avaliação divergente elaborado por perito do expropriado. O laudo deve conter: metodologia de avaliação (ABNT NBR 14653), valor de mercado do imóvel, benfeitorias úteis e necessárias (inclusive as realizadas após o decreto, se autorizadas), fundo de comércio (se imóvel comercial), prejuízos especiais decorrentes da desapropriação. Peça nomeação de perito judicial para avaliação definitiva.',
                'fields': [
                    {'name': 'perito_nome', 'label': 'Nome do Perito/Avaliador', 'type': 'text', 'required': False},
                    {'name': 'valor_laudo', 'label': 'Valor Apurado no Laudo Divergente (R$)', 'type': 'text', 'required': True},
                    {'name': 'metodologia', 'label': 'Metodologia de Avaliação', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedido de fixação de justa indenização',
                'instructions': 'Formule os pedidos: fixação da justa indenização em valor superior ao ofertado, com juros compensatórios (Súmula 618/STF: 12% a.a. sobre diferença), juros moratórios (6% a.a. a partir do trânsito em julgado), correção monetária, honorários advocatícios sobre a diferença (Súmula 141/STJ), nomeação de perito judicial para avaliação definitiva, custas pelo expropriante.',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'juros_compensatorios', 'label': 'Pedido de Juros Compensatórios?', 'type': 'select', 'required': True, 'options': ['Sim (12% a.a. - Súmula 618/STF)', 'Não se aplica']},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 11. MANDADO DE SEGURANÇA COLETIVO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'mandado_seguranca_coletivo',
        'name': 'Mandado de Segurança Coletivo - CF/88 e Lei 12.016/2009',
        'description': 'Mandado de segurança coletivo impetrado por partido político, sindicato ou associação',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 5º, LXX; Lei 12.016/2009, arts. 21-22',
        'primary_color': '#2563EB',
        'secondary_color': '#3B82F6',
        'cover_title': 'Mandado de Segurança Coletivo',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo competente',
                'instructions': 'Endereçe ao Juízo competente conforme a autoridade coatora: Vara da Fazenda Pública (autoridades estaduais/municipais), Vara Federal (autoridades federais), Tribunal de Justiça ou TRF (autoridades com prerrogativa de foro). A competência segue a regra do mandado de segurança individual (Lei 12.016/2009, art. 2º).',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo / Tribunal', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'legitimidade',
                'name': 'I - Da Legitimidade do Impetrante',
                'description': 'Demonstração da legitimidade ativa coletiva',
                'instructions': 'Demonstre a legitimidade ativa do impetrante conforme CF art. 5º, LXX: (a) partido político com representação no Congresso Nacional; (b) organização sindical, entidade de classe ou associação legalmente constituída e em funcionamento há pelo menos um ano, em defesa dos interesses de seus membros ou associados. Apresente o estatuto social, ata de constituição, comprovação de funcionamento há mais de um ano e demonstração de pertinência temática.',
                'fields': [
                    {'name': 'tipo_impetrante', 'label': 'Tipo de Impetrante', 'type': 'select', 'required': True, 'options': ['Partido Político', 'Organização Sindical', 'Entidade de Classe', 'Associação']},
                    {'name': 'impetrante_nome', 'label': 'Nome do Impetrante', 'type': 'text', 'required': True},
                    {'name': 'cnpj', 'label': 'CNPJ', 'type': 'text', 'required': True},
                    {'name': 'pertinencia_tematica', 'label': 'Pertinência Temática (relação entre finalidade estatutária e direito defendido)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'direito_coletivo',
                'name': 'II - Do Direito Líquido e Certo Coletivo',
                'description': 'Demonstração do direito líquido e certo de natureza coletiva',
                'instructions': 'Demonstre o direito líquido e certo de natureza coletiva violado ou ameaçado. Classifique: direito coletivo stricto sensu (art. 21, I - transindividuais, de natureza indivisível, de que seja titular grupo ou categoria de pessoas ligadas entre si ou com a parte contrária por relação jurídica base) ou direito individual homogêneo (art. 21, II - decorrentes de origem comum). Comprove com prova pré-constituída (documentos).',
                'fields': [
                    {'name': 'tipo_direito', 'label': 'Tipo de Direito', 'type': 'select', 'required': True, 'options': ['Coletivo stricto sensu (art. 21, I)', 'Individual homogêneo (art. 21, II)']},
                    {'name': 'direito_violado', 'label': 'Direito Líquido e Certo Violado', 'type': 'textarea', 'required': True},
                    {'name': 'grupo_beneficiado', 'label': 'Grupo/Categoria Beneficiada', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'ato_coator',
                'name': 'III - Do Ato Coator',
                'description': 'Identificação da autoridade e do ato impugnado',
                'instructions': 'Identifique a autoridade coatora (nome, cargo, órgão) e descreva o ato impugnado: ato comissivo (ação) ou omissivo (inação), data, fundamento legal invocado pela autoridade (se houver), ilegalidade ou abuso de poder. Demonstre que o ato afeta a coletividade representada pelo impetrante.',
                'fields': [
                    {'name': 'autoridade_coatora', 'label': 'Autoridade Coatora (nome e cargo)', 'type': 'text', 'required': True},
                    {'name': 'orgao', 'label': 'Órgão da Autoridade Coatora', 'type': 'text', 'required': True},
                    {'name': 'descricao_ato', 'label': 'Descrição do Ato Coator', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'IV - Da Fundamentação Jurídica',
                'description': 'Fundamentos constitucionais e legais',
                'instructions': 'Fundamente juridicamente a impetração: CF art. 5º, LXX (MS coletivo), Lei 12.016/2009, arts. 21-22. Demonstre a ilegalidade ou abuso de poder no ato da autoridade coatora. Cite a legislação específica violada. Diferencie do MS individual, demonstrando a adequação da via coletiva. Mencione que a sentença faz coisa julgada limitadamente aos membros do grupo ou categoria substituídos pelo impetrante (art. 22, §1º).',
                'fields': [
                    {'name': 'fundamentacao', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedido de concessão da segurança coletiva',
                'instructions': 'Formule os pedidos: notificação da autoridade coatora para prestar informações em 10 dias (art. 7º, I), ciência ao órgão de representação judicial da pessoa jurídica (art. 7º, II), oitiva do Ministério Público (art. 12), concessão da segurança para anular/cessar o ato coator, com efeitos para toda a coletividade representada. Se cabível, peça medida liminar (art. 7º, III).',
                'fields': [
                    {'name': 'pedido_liminar', 'label': 'Pedido de Medida Liminar?', 'type': 'select', 'required': True, 'options': ['Sim (fundamentar urgência)', 'Não']},
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 12. EMBARGOS À ARREMATAÇÃO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'embargos_arrematacao',
        'name': 'Embargos à Arrematação - CPC/2015',
        'description': 'Impugnação da arrematação judicial por nulidade, preço vil ou outro vício',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 903, §1º; Súmula 399/STJ',
        'primary_color': '#B91C1C',
        'secondary_color': '#DC2626',
        'cover_title': 'Embargos à Arrematação',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo da execução',
                'instructions': 'Endereçe ao Juízo da execução onde ocorreu a arrematação impugnada. Identifique o processo de execução, a data da arrematação e o prazo para apresentação dos embargos (10 dias contados da assinatura do auto de arrematação, CPC art. 903, §2º). Qualifique o embargante (executado/devedor) e o arrematante.',
                'fields': [
                    {'name': 'processo', 'label': 'Número do Processo de Execução', 'type': 'text', 'required': True},
                    {'name': 'embargante_nome', 'label': 'Nome do Embargante', 'type': 'text', 'required': True},
                    {'name': 'arrematante_nome', 'label': 'Nome do Arrematante', 'type': 'text', 'required': True},
                    {'name': 'data_arrematacao', 'label': 'Data da Arrematação', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'arrematacao_impugnada',
                'name': 'I - Da Arrematação Impugnada',
                'description': 'Descrição da arrematação e do bem arrematado',
                'instructions': 'Descreva a arrematação impugnada: bem arrematado (imóvel, veículo, etc.), valor da avaliação, valor da arrematação, leilão (1ª ou 2ª praça/leilão), leiloeiro responsável. Identifique o auto de arrematação e todos os documentos relevantes.',
                'fields': [
                    {'name': 'bem_arrematado', 'label': 'Descrição do Bem Arrematado', 'type': 'textarea', 'required': True},
                    {'name': 'valor_avaliacao', 'label': 'Valor da Avaliação (R$)', 'type': 'text', 'required': True},
                    {'name': 'valor_arrematacao', 'label': 'Valor da Arrematação (R$)', 'type': 'text', 'required': True},
                    {'name': 'praca_leilao', 'label': 'Praça/Leilão', 'type': 'select', 'required': True, 'options': ['1ª Praça/Leilão', '2ª Praça/Leilão']},
                ],
            },
            {
                'number': 3, 'key': 'nulidades',
                'name': 'II - Das Nulidades',
                'description': 'Nulidades da arrematação',
                'instructions': 'Argua as nulidades da arrematação conforme CPC art. 903, §1º: vício na intimação do executado (art. 889), falta de publicação do edital (art. 886), irregularidades no leilão, impedimento do arrematante (art. 890), ausência de condições legais. Cite as nulidades processuais que contaminam a arrematação. Se aplicável, argua a hipótese de fraude ou conluio.',
                'fields': [
                    {'name': 'nulidades_arguidas', 'label': 'Nulidades Arguidas', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'preco_vil',
                'name': 'III - Do Preço Vil',
                'description': 'Arguição de preço vil na arrematação',
                'instructions': 'Se aplicável, demonstre que a arrematação ocorreu por preço vil (CPC art. 891). O preço vil é aquele inferior ao mínimo estipulado pelo juiz (não inferior a 50% do valor da avaliação para bens em geral). Compare o valor da arrematação com o valor de mercado e com a avaliação. Cite jurisprudência sobre preço vil.',
                'fields': [
                    {'name': 'preco_vil', 'label': 'Há Arguição de Preço Vil?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_mercado', 'label': 'Valor de Mercado Estimado (R$)', 'type': 'text', 'required': False},
                    {'name': 'percentual_avaliacao', 'label': 'Percentual em Relação à Avaliação (%)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'IV - Da Fundamentação Jurídica',
                'description': 'Fundamentos legais dos embargos',
                'instructions': 'Fundamente juridicamente os embargos com base no CPC/2015, arts. 903, §1º (hipóteses de invalidação), 886-903 (leilão judicial). Cite a Súmula 399/STJ se aplicável. Aborde os princípios da menor onerosidade da execução (CPC art. 805) e da proteção do devedor contra abusos processuais.',
                'fields': [
                    {'name': 'fundamentacao', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedido de anulação da arrematação',
                'instructions': 'Formule os pedidos: recebimento dos embargos, suspensão dos efeitos da arrematação (efeito suspensivo), declaração de nulidade da arrematação, determinação de novo leilão em condições regulares, condenação do arrematante e/ou exequente em custas e honorários. Se cabível, peça tutela de urgência para impedir a expedição da carta de arrematação.',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'efeito_suspensivo', 'label': 'Pedido de Efeito Suspensivo?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 14. CONFLITO DE COMPETÊNCIA
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'conflito_competencia',
        'name': 'Conflito de Competência - CPC/2015',
        'description': 'Suscitação de conflito de competência positivo ou negativo entre juízos',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 66, 951-959; CF/88, art. 105, I, d',
        'primary_color': '#6D28D9',
        'secondary_color': '#7C3AED',
        'cover_title': 'Conflito de Competência',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao tribunal competente para dirimir o conflito',
                'instructions': 'Endereçe ao Tribunal competente para dirimir o conflito: TJ (conflito entre juízes vinculados ao mesmo TJ), TRF (conflito entre juízes federais do mesmo TRF ou entre juiz federal e estadual na mesma região), STJ (conflito entre juízos vinculados a tribunais diversos, CF art. 105, I, d). Identifique o suscitante (parte, MP ou juiz).',
                'fields': [
                    {'name': 'tribunal', 'label': 'Tribunal Competente', 'type': 'text', 'required': True},
                    {'name': 'suscitante', 'label': 'Suscitante', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'juizos_conflito',
                'name': 'I - Dos Juízos em Conflito',
                'description': 'Identificação dos juízos conflitantes',
                'instructions': 'Identifique os juízos em conflito: nome das varas/juízos, comarca/seção judiciária, tribunal a que estão vinculados. Classifique o conflito: positivo (dois ou mais juízos se declaram competentes, CPC art. 66, I) ou negativo (dois ou mais juízos se declaram incompetentes, CPC art. 66, II). Indique o número dos processos nos juízos conflitantes.',
                'fields': [
                    {'name': 'juizo_1', 'label': 'Primeiro Juízo', 'type': 'text', 'required': True},
                    {'name': 'processo_1', 'label': 'Processo no 1º Juízo', 'type': 'text', 'required': True},
                    {'name': 'juizo_2', 'label': 'Segundo Juízo', 'type': 'text', 'required': True},
                    {'name': 'processo_2', 'label': 'Processo no 2º Juízo', 'type': 'text', 'required': False},
                    {'name': 'tipo_conflito', 'label': 'Tipo de Conflito', 'type': 'select', 'required': True, 'options': ['Positivo (ambos se declaram competentes)', 'Negativo (ambos se declaram incompetentes)']},
                ],
            },
            {
                'number': 3, 'key': 'causa',
                'name': 'II - Da Causa',
                'description': 'Descrição da causa e objeto da demanda',
                'instructions': 'Descreva a causa subjacente: objeto da demanda, partes envolvidas, valor da causa. Relate como surgiu o conflito: decisões declinatórias de competência, prevenção, conexão ou continência alegada por um dos juízos, competência funcional vs. territorial. Inclua cópias das decisões conflitantes.',
                'fields': [
                    {'name': 'descricao_causa', 'label': 'Descrição da Causa Subjacente', 'type': 'textarea', 'required': True},
                    {'name': 'historico_conflito', 'label': 'Histórico do Surgimento do Conflito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'III - Da Fundamentação Jurídica',
                'description': 'Fundamentos para a fixação da competência',
                'instructions': 'Fundamente qual juízo deve ser declarado competente. Aplique as regras de competência: CPC arts. 42-66 (competência territorial, funcional, absoluta, relativa), normas de organização judiciária, regras de prevenção (CPC art. 59), conexão (CPC art. 55) e continência (CPC art. 56). Cite jurisprudência do tribunal competente sobre conflitos análogos.',
                'fields': [
                    {'name': 'juizo_competente', 'label': 'Juízo que Deve Ser Declarado Competente', 'type': 'text', 'required': True},
                    {'name': 'fundamentacao', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedido de fixação de competência',
                'instructions': 'Formule os pedidos: conhecimento do conflito de competência, designação de juízo para responder ao conflito com urgência, fixação da competência do juízo indicado, anulação dos atos decisórios praticados pelo juízo incompetente (se houver). Se cabível, peça designação de juízo provisório para atos urgentes enquanto pendente o julgamento do conflito (CPC art. 955).',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'medida_urgente', 'label': 'Pedido de Medida Urgente?', 'type': 'select', 'required': True, 'options': ['Sim (designação de juízo provisório)', 'Não']},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 15. EXCEÇÃO DE SUSPEIÇÃO/IMPEDIMENTO
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'excecao_suspeicao',
        'name': 'Exceção de Suspeição/Impedimento - CPC/2015',
        'description': 'Arguição de impedimento ou suspeição de magistrado',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 144-148',
        'primary_color': '#B91C1C',
        'secondary_color': '#DC2626',
        'cover_title': 'Exceção de Suspeição/Impedimento',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo ou tribunal competente',
                'instructions': 'Endereçe ao juízo onde tramita a causa (a exceção é dirigida ao próprio juiz arguido, que terá 15 dias para se manifestar, CPC art. 146, §1º). Se o juiz não reconhecer o impedimento ou suspeição, os autos serão remetidos ao tribunal competente (CPC art. 146, §1º). Identifique o processo e as partes.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo', 'type': 'text', 'required': True},
                    {'name': 'processo', 'label': 'Número do Processo', 'type': 'text', 'required': True},
                    {'name': 'excipiente_nome', 'label': 'Nome do Excipiente (Arguinte)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'magistrado',
                'name': 'I - Do Magistrado',
                'description': 'Identificação do magistrado arguido',
                'instructions': 'Identifique o magistrado cuja suspeição ou impedimento se argui: nome completo, cargo (juiz titular, substituto, desembargador), vara/câmara em que atua. Indique desde quando o magistrado atua no processo e se houve decisões proferidas que possam ser anuladas.',
                'fields': [
                    {'name': 'magistrado_nome', 'label': 'Nome do Magistrado', 'type': 'text', 'required': True},
                    {'name': 'cargo', 'label': 'Cargo do Magistrado', 'type': 'text', 'required': True},
                    {'name': 'tipo_arguicao', 'label': 'Tipo de Arguição', 'type': 'select', 'required': True, 'options': ['Impedimento (CPC art. 144)', 'Suspeição (CPC art. 145)']},
                ],
            },
            {
                'number': 3, 'key': 'hipotese_legal',
                'name': 'II - Da Hipótese Legal',
                'description': 'Enquadramento da hipótese de impedimento ou suspeição',
                'instructions': 'Enquadre a hipótese legal. IMPEDIMENTO (CPC art. 144): juiz é parte, interveio como MP/perito/testemunha, proferiu decisão em outro grau, é cônjuge/parente de advogado/parte, recebeu presentes, é herdeiro/donatário/empregador de parte. SUSPEIÇÃO (CPC art. 145): amigo íntimo ou inimigo, interesse na causa, aconselhamento, recebeu presentes antes/depois do processo, interesse de instituição de ensino/entidade ligada ao juiz. Descreva os fatos concretos que configuram a hipótese.',
                'fields': [
                    {'name': 'hipotese_legal', 'label': 'Hipótese Legal (artigo e inciso)', 'type': 'text', 'required': True},
                    {'name': 'descricao_fatos', 'label': 'Fatos Concretos que Configuram a Hipótese', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'provas',
                'name': 'III - Das Provas',
                'description': 'Provas do impedimento ou suspeição',
                'instructions': 'Apresente as provas que demonstram o impedimento ou a suspeição: documentos, certidões, declarações, publicações em redes sociais, registros de parentesco (certidões de nascimento/casamento), comprovantes de relações profissionais ou pessoais. A arguição deve ser instruída com prova documental (CPC art. 146, §1º). Se não for possível prova documental imediata, indique as provas a produzir.',
                'fields': [
                    {'name': 'provas_documentais', 'label': 'Provas Documentais', 'type': 'textarea', 'required': True},
                    {'name': 'provas_a_produzir', 'label': 'Provas a Produzir (se necessário)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedido de afastamento do magistrado',
                'instructions': 'Formule os pedidos: acolhimento da exceção de impedimento/suspeição, afastamento do magistrado do processo, remessa dos autos ao substituto legal, anulação dos atos decisórios praticados pelo magistrado impedido/suspeito (CPC art. 146, §6º — no impedimento, são anuláveis; na suspeição, os atos anteriores à arguição são preservados, salvo se houve conduta dolosa). Se cabível, peça a suspensão do processo até julgamento da exceção.',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'suspensao_processo', 'label': 'Pedido de Suspensão do Processo?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 16. ASSISTÊNCIA LITISCONSORCIAL/SIMPLES
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'assistencia_litisconsorcial',
        'name': 'Assistência Litisconsorcial/Simples - CPC/2015',
        'description': 'Pedido de intervenção como assistente litisconsorcial ou simples em processo alheio',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 119-124',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Pedido de Assistência',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo do processo principal',
                'instructions': 'Endereçe ao Juízo do processo em que pretende intervir como assistente. Identifique o processo (número, partes, objeto) e a posição que pretende assumir (assistente do autor ou do réu). A assistência pode ser requerida a qualquer tempo e grau de jurisdição (CPC art. 119, parágrafo único).',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo', 'type': 'text', 'required': True},
                    {'name': 'processo', 'label': 'Número do Processo', 'type': 'text', 'required': True},
                    {'name': 'assistido', 'label': 'Parte a Ser Assistida (autor ou réu)', 'type': 'select', 'required': True, 'options': ['Autor', 'Réu']},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao_assistente',
                'name': 'I - Da Qualificação do Assistente',
                'description': 'Qualificação completa do requerente da assistência',
                'instructions': 'Qualifique o requerente da assistência com dados completos: nome, qualificação civil, CPF/CNPJ, endereço. Esclareça a relação do assistente com a parte assistida e com o objeto do processo. O assistente deve ter interesse jurídico na causa (CPC art. 119).',
                'fields': [
                    {'name': 'assistente_nome', 'label': 'Nome do Assistente', 'type': 'text', 'required': True},
                    {'name': 'assistente_cpf', 'label': 'CPF/CNPJ do Assistente', 'type': 'text', 'required': True},
                    {'name': 'relacao_partes', 'label': 'Relação com a Parte Assistida', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'interesse_juridico',
                'name': 'II - Do Interesse Jurídico',
                'description': 'Demonstração do interesse jurídico na intervenção',
                'instructions': 'Demonstre o interesse jurídico que justifica a assistência (CPC art. 119). Diferencie: assistência SIMPLES (interesse jurídico indireto — a sentença pode afetar relação jurídica entre o assistente e o adversário do assistido) e assistência LITISCONSORCIAL (o assistente é titular da relação jurídica discutida — poderia ser litisconsorte, CPC art. 124). Fundamente por que a decisão a ser proferida pode afetar a esfera jurídica do assistente.',
                'fields': [
                    {'name': 'tipo_assistencia', 'label': 'Tipo de Assistência', 'type': 'select', 'required': True, 'options': ['Assistência Simples (CPC art. 121)', 'Assistência Litisconsorcial (CPC art. 124)']},
                    {'name': 'interesse_juridico', 'label': 'Interesse Jurídico (por que a decisão afeta o assistente)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'III - Da Fundamentação Jurídica',
                'description': 'Fundamentos da admissibilidade da assistência',
                'instructions': 'Fundamente a admissibilidade da assistência nos arts. 119-124 do CPC/2015. Na assistência simples (art. 121), o assistente atua como auxiliar da parte assistida, recebendo o processo no estado em que se encontra, podendo praticar atos processuais, mas sem contrariar a vontade do assistido. Na assistência litisconsorcial (art. 124), o assistente é considerado litisconsorte da parte assistida, podendo praticar todos os atos, inclusive os que contrariem o assistido.',
                'fields': [
                    {'name': 'fundamentacao', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedido de admissão como assistente',
                'instructions': 'Formule os pedidos: admissão como assistente (simples ou litisconsorcial) da parte indicada, intimação das partes para se manifestarem sobre o pedido de assistência em 15 dias (CPC art. 120), e, após admissão, que o assistente receba o processo no estado em que se encontra. Se houver impugnação ao pedido de assistência, peça que seja decidido incidentalmente (CPC art. 120, parágrafo único).',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────────
    # 17. RECURSO AO STJD
    # ──────────────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'recurso_stjd',
        'name': 'Recurso ao STJD - Justiça Desportiva',
        'description': 'Recurso à instância superior do Superior Tribunal de Justiça Desportiva',
        'version': '1.0',
        'legal_basis': 'Lei 9.615/1998 (Lei Pelé); CBJD',
        'primary_color': '#EA580C',
        'secondary_color': '#F97316',
        'cover_title': 'Recurso ao STJD',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento ao STJD',
                'description': 'Endereçamento ao Superior Tribunal de Justiça Desportiva',
                'instructions': 'Endereçe ao Tribunal Pleno do STJD da modalidade esportiva correspondente (futebol, basquete, vôlei, etc.). Identifique o processo disciplinar de origem no TJD (Tribunal de Justiça Desportiva) de primeiro grau, o número do inquérito/processo, e o tipo de recurso (recurso voluntário, embargos, revisão). O prazo para recurso é de 3 dias úteis da publicação da decisão (CBJD art. 136).',
                'fields': [
                    {'name': 'stjd_modalidade', 'label': 'STJD da Modalidade', 'type': 'text', 'required': True},
                    {'name': 'processo_origem', 'label': 'Processo/Inquérito de Origem no TJD', 'type': 'text', 'required': True},
                    {'name': 'recorrente_nome', 'label': 'Nome do Recorrente', 'type': 'text', 'required': True},
                    {'name': 'recorrido', 'label': 'Recorrido (Procuradoria do STJD ou parte adversa)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'decisao_recorrida',
                'name': 'I - Da Decisão Recorrida',
                'description': 'Síntese da decisão do TJD recorrida',
                'instructions': 'Apresente a síntese da decisão do TJD de primeiro grau: composição da comissão julgadora, resultado (punição aplicada, absolvição), placar da votação, fundamentos utilizados. Indique a infração disciplinar julgada (CBJD: artigo infringido), a penalidade aplicada (multa, suspensão de jogos/dias, eliminação, interdição de praça desportiva).',
                'fields': [
                    {'name': 'data_decisao', 'label': 'Data da Decisão do TJD', 'type': 'text', 'required': True},
                    {'name': 'infracao_julgada', 'label': 'Infração Disciplinar Julgada (artigo CBJD)', 'type': 'text', 'required': True},
                    {'name': 'penalidade_aplicada', 'label': 'Penalidade Aplicada', 'type': 'text', 'required': True},
                    {'name': 'sintese_decisao', 'label': 'Síntese da Decisão Recorrida', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'infracao',
                'name': 'II - Da Infração Desportiva',
                'description': 'Contextualização da infração desportiva',
                'instructions': 'Contextualize a infração desportiva: partida/competição em que ocorreu, circunstâncias do evento (lance de jogo, conduta do atleta/dirigente/torcida), relatório do árbitro, súmula da partida. Analise se a conduta tipificada no CBJD corresponde efetivamente aos fatos ocorridos. Se aplicável, questione a tipicidade da infração.',
                'fields': [
                    {'name': 'partida', 'label': 'Partida/Competição', 'type': 'text', 'required': True},
                    {'name': 'data_partida', 'label': 'Data da Partida', 'type': 'text', 'required': True},
                    {'name': 'descricao_fatos', 'label': 'Descrição dos Fatos (conforme súmula/relatório)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'razoes',
                'name': 'III - Das Razões do Recurso',
                'description': 'Razões recursais',
                'instructions': 'Apresente as razões recursais: erro na tipificação da infração (CBJD), desproporcionalidade da pena aplicada, nulidade processual (cerceamento de defesa, composição irregular da comissão), divergência jurisprudencial entre os TJDs, violação ao CBJD ou à Lei Pelé (Lei 9.615/98). Aplique os princípios do direito desportivo: proporcionalidade, contraditório, ampla defesa e tipicidade.',
                'fields': [
                    {'name': 'razoes_recurso', 'label': 'Razões do Recurso', 'type': 'textarea', 'required': True},
                    {'name': 'tipo_erro', 'label': 'Tipo de Erro Arguido', 'type': 'select', 'required': True, 'options': ['Erro na tipificação', 'Desproporcionalidade da pena', 'Nulidade processual', 'Divergência jurisprudencial', 'Violação ao CBJD/Lei Pelé']},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedido de reforma ou anulação',
                'instructions': 'Formule os pedidos: conhecimento e provimento do recurso, reforma da decisão do TJD (absolvição, redução da pena, reclassificação da infração), ou anulação para novo julgamento. Se cabível, peça efeito suspensivo ao recurso para que o recorrente possa atuar/participar durante o julgamento. Indique se há urgência (partida iminente, campeonato em andamento).',
                'fields': [
                    {'name': 'pedido_detalhado', 'label': 'Pedido Detalhado', 'type': 'textarea', 'required': True},
                    {'name': 'efeito_suspensivo', 'label': 'Pedido de Efeito Suspensivo?', 'type': 'select', 'required': True, 'options': ['Sim (justificar urgência)', 'Não']},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints especializados complementares no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Especializado Complementar'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN\n'))
            return
        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)
            self._fix_excecao_pre_executividade_tributario()
        self.stdout.write(self.style.SUCCESS('\n✓ Especializado Complementar concluído!\n'))

    def _criar_categorias(self):
        from apps.core.models import DocumentCategory
        self.stdout.write('\n[1/5] Categorias...')
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
            self.stdout.write(f'  {"✓ Criada" if created else "⊘ Existe"}: {obj.name}')

    def _criar_tipos_documento(self):
        from apps.core.models import DocumentType, DocumentCategory
        self.stdout.write('\n[2/5] Tipos de documento...')
        cats = {c.code: c for c in DocumentCategory.objects.all()}
        for data in TIPOS_DOCUMENTO:
            cat = cats.get(data['category'])
            if not cat:
                self.stdout.write(self.style.ERROR(f'  ✗ Categoria não encontrada: {data["category"]}'))
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
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {obj.name}')

    def _criar_agentes_secao(self):
        from apps.intelligent_assistant.models import SectionAgentConfig
        self.stdout.write('\n[3/5] Agentes de seção...')
        specs = [
            {
                'key': 'gerador_especializado_complementar',
                'name': 'Verus.AI - Gerador Especializado Complementar',
                'description': 'Gera peças de Juizados Especiais, Agrário, Sanitário, Improbidade, Desapropriação, MS Coletivo, Execução e Desportivo',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_ESPECIALIZADO,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'validador_juridico',
                'name': 'Verus.AI - Validador Jurídico',
                'description': 'Valida o conteúdo jurídico gerado',
                'agent_type': 'validator',
                'system_prompt': PROMPT_VALIDADOR_JURIDICO,
                'temperature': TEMP_VALIDATOR,
                'max_tokens': 1024,
                'is_default': False,
            },
        ]
        agentes = {}
        for spec in specs:
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
            self.stdout.write(f'  {"✓ Criado" if created else "↻ Atualizado"}: {obj.name}')
        return agentes

    def _criar_blueprints(self, agentes, force):
        from apps.core.models import DocumentType, DocumentCategory
        from apps.intelligent_assistant.models import DocumentBlueprint, BlueprintSection
        self.stdout.write('\n[4/5] Blueprints...')
        tipos = {t.code: t for t in DocumentType.objects.all()}
        cats = {c.code: c for c in DocumentCategory.objects.all()}
        for bp_data in BLUEPRINTS_DATA:
            doc_type = tipos.get(bp_data['doc_type_code'])
            if not doc_type:
                self.stdout.write(self.style.ERROR(f'  ✗ Tipo não encontrado: {bp_data["doc_type_code"]}'))
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
                    'cover_subtitle': bp_data['description'],
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
                blueprint.save()
                blueprint.sections.all().delete()
                created = True
            # Adiciona área primária (category do doc_type) — FORA do if created
            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)
            # Adiciona áreas extras — FORA do if created
            extras = AREAS_EXTRAS.get(bp_data['doc_type_code'], [])
            for area_code in extras:
                area_cat = cats.get(area_code)
                if area_cat:
                    blueprint.areas.add(area_cat)
                else:
                    self.stdout.write(self.style.WARNING(f'    ⚠ Área extra não encontrada: {area_code}'))
            # Garante is_default=True em re-execução
            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {blueprint.name}')
            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_especializado_complementar')
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
                            'generator_agent': agentes.get(agente_key),
                            'validator_agent': agentes.get('validador_juridico'),
                            'section_fields': sec.get('fields', []),
                            'is_active': True,
                        }
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')

    def _fix_excecao_pre_executividade_tributario(self):
        """Adiciona a área 'tributario' como secundária à Exceção de Pré-Executividade existente."""
        from apps.core.models import DocumentType, DocumentCategory
        from apps.intelligent_assistant.models import DocumentBlueprint
        self.stdout.write('\n[5/5] Fix: Exceção de Pré-Executividade → área tributário...')
        try:
            doc_type = DocumentType.objects.get(code='excecao_pre_executividade')
            cat_tributario = DocumentCategory.objects.get(code='tributario')
            blueprints = DocumentBlueprint.objects.filter(document_type=doc_type)
            for bp in blueprints:
                bp.areas.add(cat_tributario)
                self.stdout.write(f'  ✓ Área "tributario" adicionada ao blueprint: {bp.name}')
            if not blueprints.exists():
                self.stdout.write(self.style.WARNING('  ⚠ Nenhum blueprint encontrado para excecao_pre_executividade'))
        except DocumentType.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠ DocumentType excecao_pre_executividade não encontrado'))
        except DocumentCategory.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠ DocumentCategory tributario não encontrada'))
