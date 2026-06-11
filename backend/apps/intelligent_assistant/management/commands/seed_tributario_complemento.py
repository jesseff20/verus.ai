"""
Seed Tributário - Complemento — Verus.AI.
Mandado de Segurança Tributário, Ação Anulatória de Débito Fiscal,
Repetição de Indébito Tributário.

Uso:
    python manage.py seed_tributario_complemento
    python manage.py seed_tributario_complemento --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction

MODEL = 'mistralai/mistral-medium-2505'
PROVIDER = 'watsonx'
TEMP_GENERATOR = 0.7
TEMP_VALIDATOR = 0.3
MAX_TOKENS = 4096

TIPOS_DOCUMENTO = [
    {
        'code': 'mandado_seguranca_tributario',
        'name': 'Mandado de Segurança Tributário',
        'short_name': 'MS Tributário',
        'description': 'MS para suspender exigibilidade de tributo e proteger direito líquido e certo do contribuinte',
        'category': 'tributario',
        'icon': 'Shield',
        'color': '#D97706',
        'legal_basis': 'CF/88, art. 5º, LXIX; Lei 12.016/2009; CTN, art. 151, II',
        'display_order': 3,
    },
    {
        'code': 'acao_anulatoria_debito_fiscal',
        'name': 'Ação Anulatória de Débito Fiscal',
        'short_name': 'Anulatória Fiscal',
        'description': 'Ação para anular lançamento tributário eivado de vício de legalidade',
        'category': 'tributario',
        'icon': 'FileX',
        'color': '#D97706',
        'legal_basis': 'CTN, arts. 142-150; CPC/2015, art. 38; CF/88, art. 5º, XXXV',
        'display_order': 4,
    },
    {
        'code': 'repeticao_indbito_tributario',
        'name': 'Repetição de Indébito Tributário',
        'short_name': 'Repet. Indébito',
        'description': 'Ação para restituição de tributo pago indevidamente ou a maior',
        'category': 'tributario',
        'icon': 'RefreshCw',
        'color': '#D97706',
        'legal_basis': 'CTN, arts. 165-169; STJ Súmulas 162 e 188',
        'display_order': 5,
    },
]

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
- Conteúdo inferido: [VERIFICAR COM ADVOGADO]
"""

PROMPT_GERADOR_TRIBUTARIO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Tributário e Fiscal brasileiro.

LEGISLAÇÃO VIGENTE:
- CTN (Lei 5.172/1966); CF/88, arts. 145-162; Lei 6.830/1980 (LEF)
- Lei 12.016/2009 (Mandado de Segurança); CPC/2015 (subsidiário)
- LC 87/1996 (ICMS); LC 116/2003 (ISS); Lei 9.430/1996; Lei 10.522/2002

REGRAS ESSENCIAIS:
1. MS Tributário: suspensão de exigibilidade pelo CTN art. 151, II (liminar) e V (recurso)
2. Prazo MS: 120 dias do ato coator (Lei 12.016/2009, art. 23)
3. Ação anulatória: CPC art. 38 — depósito preparatório suspende exigibilidade (CTN art. 151, II)
4. Repetição de indébito: CTN art. 165 — prazo de 5 anos (art. 168); SELIC como correção (STJ Súmula 162)
5. Decadência: CTN art. 173 (5 anos para lançamento); Prescrição: CTN art. 174 (5 anos)
6. Lançamento: tipos (de ofício, por declaração, por homologação) — CTN arts. 147-150
7. Súmulas STJ: 162, 188, 213, 355, 393, 430, 436, 446, 460, 497, 555, 558, 560
8. Acórdãos específicos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'mandado_seguranca_tributario': 'gerador_tributario_complemento',
    'acao_anulatoria_debito_fiscal': 'gerador_tributario_complemento',
    'repeticao_indbito_tributario': 'gerador_tributario_complemento',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'mandado_seguranca_tributario',
        'name': 'Mandado de Segurança Tributário - Lei 12.016/2009',
        'description': 'MS para proteger direito líquido e certo do contribuinte e suspender exigibilidade de tributo',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 5º, LXIX; Lei 12.016/2009; CTN, art. 151, II',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Mandado de Segurança Tributário',
        'secondary_area_codes': ['cautelares_tutelas'],
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_partes',
                'name': 'Qualificação das Partes e Tempestividade',
                'description': 'Identificação do impetrante, autoridade coatora e prazo',
                'instructions': 'Qualifique o impetrante (contribuinte — nome, CPF/CNPJ, endereço, representação). Identifique a autoridade coatora (cargo, órgão fazendário). Descreva o ato coator (auto de infração, notificação, despacho — número, data, tributo, exercício). Demonstre tempestividade: 120 dias do ato coator (Lei 12.016/2009, art. 23). ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'impetrante_nome', 'label': 'Nome/Razão Social do Impetrante', 'type': 'text', 'required': True},
                    {'name': 'impetrante_cpf_cnpj', 'label': 'CPF/CNPJ do Impetrante', 'type': 'text', 'required': True},
                    {'name': 'autoridade_coatora', 'label': 'Autoridade Coatora (cargo e órgão)', 'type': 'text', 'required': True},
                    {'name': 'ato_coator', 'label': 'Ato Coator (tipo, número, data)', 'type': 'textarea', 'required': True},
                    {'name': 'tributo_exercicio', 'label': 'Tributo e Exercício Discutido', 'type': 'text', 'required': True},
                    {'name': 'valor_exigido', 'label': 'Valor Exigido (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'ato_coator',
                'name': 'I - Do Ato Coator e sua Ilegalidade',
                'description': 'Descrição do ato coator e demonstração da ilegalidade',
                'instructions': 'Descreva o ato coator com precisão. Demonstre a ilegalidade: violação de norma tributária (CTN), vício formal do lançamento, decadência, prescrição, imunidade constitucional ou isenção legal. Cite dispositivos do CTN e CF art. 150 (limitações ao poder de tributar). ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'descricao_ato_coator', 'label': 'Descrição Detalhada do Ato Coator', 'type': 'textarea', 'required': True},
                    {'name': 'ilegalidade_apontada', 'label': 'Ilegalidade ou Inconstitucionalidade Apontada', 'type': 'select', 'required': True, 'options': ['Decadência do lançamento (CTN art. 173)', 'Prescrição do crédito (CTN art. 174)', 'Vício formal da autuação', 'Imunidade tributária (CF art. 150)', 'Isenção legal', 'Bis in idem / Bitributação', 'Erro de cálculo/base de cálculo', 'Outra ilegalidade']},
                    {'name': 'fundamentacao_ilegalidade', 'label': 'Fundamentação Jurídica da Ilegalidade', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'direito_liquido_certo',
                'name': 'II - Do Direito Líquido e Certo',
                'description': 'Demonstração do direito líquido e certo violado',
                'instructions': 'Demonstre que o direito é líquido e certo (comprovado por prova documental pré-constituída, sem necessidade de dilação probatória). Cite o artigo do CTN ou da CF que confere o direito. Demonstre que o ato coator ameaça ou viola esse direito de forma concreta e atual. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'direito_invocado', 'label': 'Direito Líquido e Certo Invocado', 'type': 'textarea', 'required': True},
                    {'name': 'prova_pre_constituida', 'label': 'Provas Pré-Constituídas (documentos disponíveis)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'suspensao_exigibilidade',
                'name': 'III - Da Suspensão da Exigibilidade do Crédito',
                'description': 'Pedido de liminar para suspensão de exigibilidade',
                'instructions': 'Fundamente a suspensão da exigibilidade pelo CTN art. 151, II (liminar em MS). Demonstre fumus boni iuris (direito aparente ao contribuinte) e periculum in mora (risco de cobrança imediata, execução fiscal, inscrição em CADIN, protestos). Cite Lei 12.016/2009, art. 7º, III. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'fumus_boni_iuris', 'label': 'Fumus Boni Iuris (resumo do direito aparente)', 'type': 'textarea', 'required': True},
                    {'name': 'periculum_in_mora', 'label': 'Periculum in Mora (risco de dano imediato)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido_final',
                'name': 'IV - Dos Pedidos',
                'description': 'Pedidos finais do mandado de segurança tributário',
                'instructions': 'Formule os pedidos: (a) liminar para suspensão da exigibilidade do crédito (CTN art. 151, II; Lei 12.016/2009, art. 7º, III); (b) notificação da autoridade coatora; (c) ouvida do Ministério Público; (d) concessão definitiva da segurança, anulando o ato coator; (e) condenação em honorários advocatícios. Valor da causa. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'pede_liminar', 'label': 'Requer Liminar de Suspensão?', 'type': 'select', 'required': True, 'options': ['Sim — urgência comprovada', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                    {'name': 'pedidos_especificos', 'label': 'Pedidos Específicos Adicionais', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_anulatoria_debito_fiscal',
        'name': 'Ação Anulatória de Débito Fiscal - CTN arts. 142-150',
        'description': 'Ação para desconstituir lançamento tributário ilegal ou inconstitucional',
        'version': '1.0',
        'legal_basis': 'CTN, arts. 142-150; CPC/2015, art. 38; CF/88, art. 5º, XXXV',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Ação Anulatória de Débito Fiscal',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_partes',
                'name': 'Qualificação das Partes',
                'description': 'Identificação do autor e da Fazenda Pública ré',
                'instructions': 'Qualifique o autor (contribuinte). Identifique a Fazenda Pública ré (União/Estado/Município). Indique o juízo competente (Vara de Fazenda Pública ou Vara Federal). Mencione o processo administrativo de origem, se houver. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'autor_nome', 'label': 'Nome/Razão Social do Autor', 'type': 'text', 'required': True},
                    {'name': 'autor_cpf_cnpj', 'label': 'CPF/CNPJ do Autor', 'type': 'text', 'required': True},
                    {'name': 'fazenda_re', 'label': 'Fazenda Pública Ré (Federal/Estadual/Municipal)', 'type': 'select', 'required': True, 'options': ['Fazenda Nacional (União Federal)', 'Fazenda Estadual', 'Fazenda Municipal']},
                    {'name': 'processo_adm', 'label': 'Processo Administrativo de Origem (se houver)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'descricao_debito',
                'name': 'I - Dos Fatos e Descrição do Débito',
                'description': 'Narrativa dos fatos e identificação do lançamento contestado',
                'instructions': 'Narre os fatos: como o débito surgiu (autuação fiscal, notificação de lançamento, inscrição em dívida ativa). Identifique o tributo, exercício, base de cálculo, alíquota e valor cobrado. Descreva como o contribuinte tomou ciência do lançamento. Mencione eventual processo administrativo e seu resultado. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'tributo', 'label': 'Tributo Cobrado (ex: ICMS, ISS, IRPJ)', 'type': 'text', 'required': True},
                    {'name': 'exercicio', 'label': 'Exercício Fiscal', 'type': 'text', 'required': True},
                    {'name': 'valor_debito', 'label': 'Valor do Débito (R$)', 'type': 'text', 'required': True},
                    {'name': 'numero_lancamento', 'label': 'Número do Auto de Infração/Lançamento', 'type': 'text', 'required': False},
                    {'name': 'narrativa_fatos', 'label': 'Narrativa dos Fatos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'vicios_lancamento',
                'name': 'II - Dos Vícios do Lançamento',
                'description': 'Fundamentação dos vícios que tornam o lançamento nulo',
                'instructions': 'Apresente os vícios jurídicos do lançamento: (a) decadência — CTN art. 173 (lançamento de ofício) ou art. 150 §4º (homologação); (b) prescrição — CTN art. 174; (c) erro na base de cálculo ou alíquota; (d) nulidade por falta de motivação ou por cerceamento de defesa; (e) imunidade ou isenção aplicável. Cite os artigos do CTN correspondentes. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'vicio_principal', 'label': 'Vício Principal do Lançamento', 'type': 'select', 'required': True, 'options': ['Decadência (CTN art. 173)', 'Prescrição (CTN art. 174)', 'Erro na base de cálculo', 'Erro na alíquota', 'Nulidade formal (falta de motivação)', 'Cerceamento de defesa', 'Imunidade tributária', 'Isenção legal', 'Bis in idem', 'Outro']},
                    {'name': 'descricao_vicios', 'label': 'Descrição Detalhada dos Vícios', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'base_legal',
                'name': 'III - Da Base Legal e Jurídica',
                'description': 'Fundamentação legal e jurisprudencial',
                'instructions': 'Desenvolva os fundamentos jurídicos: cite artigos do CTN pertinentes ao vício apontado, princípios constitucionais tributários (CF art. 150 — legalidade, anterioridade, capacidade contributiva), e jurisprudência dos tribunais superiores (usando marcadores para acórdãos não verificados). Mencione Súmulas do STJ aplicáveis. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'artigos_ctn', 'label': 'Artigos do CTN Aplicáveis', 'type': 'textarea', 'required': True},
                    {'name': 'principios_constitucionais', 'label': 'Princípios Constitucionais Invocados', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'pedidos',
                'name': 'IV - Dos Pedidos',
                'description': 'Pedidos da ação anulatória',
                'instructions': 'Formule os pedidos: (a) tutela de urgência para suspensão da exigibilidade (CPC art. 300 ou depósito integral — CTN art. 151, II); (b) anulação do lançamento tributário; (c) cancelamento de eventual inscrição em dívida ativa; (d) condenação da Fazenda em honorários (CPC art. 85); (e) valor da causa (valor do débito discutido). ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'pede_tutela_urgencia', 'label': 'Requer Tutela de Urgência (suspensão)?', 'type': 'select', 'required': True, 'options': ['Sim — risco de execução fiscal imediata', 'Não — depósito integral do débito', 'Não requer']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'repeticao_indbito_tributario',
        'name': 'Repetição de Indébito Tributário - CTN arts. 165-169',
        'description': 'Ação para restituição de tributo pago indevidamente com correção pela SELIC',
        'version': '1.0',
        'legal_basis': 'CTN, arts. 165-169; STJ Súmulas 162 e 188',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Repetição de Indébito Tributário',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_partes',
                'name': 'Qualificação das Partes',
                'description': 'Identificação do autor (contribuinte) e da Fazenda Pública ré',
                'instructions': 'Qualifique o autor (contribuinte que pagou indevidamente). Identifique a Fazenda Pública ré. Mencione o juízo competente. Se houver pedido administrativo anterior negado, mencione-o. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'autor_nome', 'label': 'Nome/Razão Social do Autor', 'type': 'text', 'required': True},
                    {'name': 'autor_cpf_cnpj', 'label': 'CPF/CNPJ do Autor', 'type': 'text', 'required': True},
                    {'name': 'fazenda_re', 'label': 'Fazenda Pública Ré', 'type': 'select', 'required': True, 'options': ['Fazenda Nacional (União Federal)', 'Fazenda Estadual', 'Fazenda Municipal']},
                    {'name': 'pedido_adm_anterior', 'label': 'Houve pedido administrativo de restituição anterior?', 'type': 'select', 'required': True, 'options': ['Sim — negado/sem resposta', 'Não']},
                ],
            },
            {
                'number': 2, 'key': 'pagamentos_indevidos',
                'name': 'I - Dos Pagamentos Indevidos',
                'description': 'Demonstração dos pagamentos realizados indevidamente',
                'instructions': 'Identifique os pagamentos indevidos: tributo, exercícios, valores, datas de recolhimento, guias e comprovantes. Demonstre que foram pagos sem que houvesse obrigação tributária válida, ou pagos a maior. Enumere cada recolhimento. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'tributo', 'label': 'Tributo Pago Indevidamente', 'type': 'text', 'required': True},
                    {'name': 'periodo_pagamentos', 'label': 'Período dos Pagamentos Indevidos', 'type': 'text', 'required': True},
                    {'name': 'valor_total_pago', 'label': 'Valor Total Pago Indevidamente (R$)', 'type': 'text', 'required': True},
                    {'name': 'descricao_pagamentos', 'label': 'Descrição dos Pagamentos (datas, valores, guias)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'fundamento_legal',
                'name': 'II - Do Fundamento Legal da Restituição',
                'description': 'Base legal para a repetição do indébito',
                'instructions': 'Fundamente juridicamente o direito à restituição: CTN art. 165 (hipóteses de restituição), art. 166 (tributos indiretos — prova de não repasse), art. 168 (prazo de 5 anos). Demonstre que o pagamento foi indevido (sem fato gerador, com isenção, com imunidade, por erro de cálculo, etc.). Cite Súmulas do STJ aplicáveis. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'hipotese_restituicao', 'label': 'Hipótese de Restituição (CTN art. 165)', 'type': 'select', 'required': True, 'options': ['I — cobrança ou pagamento espontâneo de tributo indevido', 'II — erro na identificação do sujeito passivo', 'III — reforma, anulação, revogação ou rescisão de decisão condenatória']},
                    {'name': 'fundamentacao_juridica', 'label': 'Fundamentação Jurídica Detalhada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'juros_selic',
                'name': 'III - Da Correção pela Taxa SELIC',
                'description': 'Atualização monetária e juros pelo índice SELIC',
                'instructions': 'Requeira a atualização dos valores pela Taxa SELIC, conforme STJ Súmula 162 (juros de mora na repetição de indébito tributário) e Súmula 188 (os juros moratórios, na repetição do indébito tributário, são devidos a partir do trânsito em julgado da sentença). Mencione a Lei 9.250/1995, art. 39 §4º (SELIC para tributos federais). Calcule ou indique o montante atualizado. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'data_pagamentos_inicio', 'label': 'Data do Primeiro Pagamento Indevido', 'type': 'text', 'required': True},
                    {'name': 'valor_atualizado_estimado', 'label': 'Valor Atualizado Estimado (se calculado)', 'type': 'text', 'required': False},
                    {'name': 'tributo_federal_estadual', 'label': 'Tributo Federal ou Estadual/Municipal?', 'type': 'select', 'required': True, 'options': ['Federal — SELIC (Lei 9.250/1995, art. 39 §4º)', 'Estadual/Municipal — legislação específica do ente']},
                ],
            },
            {
                'number': 5, 'key': 'pedidos',
                'name': 'IV - Dos Pedidos',
                'description': 'Pedidos da repetição de indébito',
                'instructions': 'Formule os pedidos: (a) condenação da Fazenda à restituição do valor pago indevidamente; (b) atualização pela Taxa SELIC desde os respectivos pagamentos (STJ Súmula 162); (c) honorários advocatícios (CPC art. 85); (d) produção de provas (juntada de documentos, perícia contábil se necessária). Valor da causa = valor total atualizado pleiteado. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                    {'name': 'pede_pericia_contabil', 'label': 'Requer Perícia Contábil?', 'type': 'select', 'required': True, 'options': ['Sim — para apuração dos valores', 'Não — valores já apurados documentalmente']},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Tributário - Complemento no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Tributário Complemento'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            return

        with transaction.atomic():
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Tributário Complemento concluído!\n'))

    def _criar_tipos_documento(self):
        from apps.core.models import DocumentType, DocumentCategory
        self.stdout.write('\n[1/3] Tipos de documento...')
        cats = {c.code: c for c in DocumentCategory.objects.all()}
        for data in TIPOS_DOCUMENTO:
            cat = cats.get(data['category'])
            if not cat:
                self.stdout.write(self.style.ERROR(f'  ✗ Categoria não encontrada: {data["category"]}'))
                continue
            obj, created = DocumentType.objects.get_or_create(
                code=data['code'],
                defaults={'name': data['name'], 'short_name': data['short_name'], 'description': data['description'], 'category': cat, 'icon': data['icon'], 'color': data['color'], 'legal_basis': data['legal_basis'], 'display_order': data['display_order'], 'is_active': True}
            )
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {obj.name}')

    def _criar_agentes_secao(self):
        from apps.intelligent_assistant.models import SectionAgentConfig
        self.stdout.write('\n[2/3] Agentes de seção...')
        specs = [
            {'key': 'gerador_tributario_complemento', 'name': 'Verus.AI - Gerador Tributário Complemento', 'description': 'Gera MS tributário, anulatória e repetição de indébito', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_TRIBUTARIO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'validador_juridico', 'name': 'Verus.AI - Validador Jurídico', 'description': 'Valida o conteúdo jurídico gerado', 'agent_type': 'validator', 'system_prompt': PROMPT_VALIDADOR_JURIDICO, 'temperature': TEMP_VALIDATOR, 'max_tokens': 1024, 'is_default': False},
        ]
        agentes = {}
        for spec in specs:
            obj, created = SectionAgentConfig.objects.update_or_create(
                name=spec['name'],
                defaults={'description': spec['description'], 'agent_type': spec['agent_type'], 'system_prompt': spec['system_prompt'], 'user_prompt_template': USER_TEMPLATE_SECAO, 'llm_provider': PROVIDER, 'model_name': MODEL, 'temperature': spec['temperature'], 'max_tokens': spec['max_tokens'], 'use_rag': False, 'rag_top_k': 5, 'rag_similarity_threshold': 0.7, 'is_active': True, 'is_default': spec['is_default']}
            )
            agentes[spec['key']] = obj
            self.stdout.write(f'  {"✓ Criado" if created else "↻ Atualizado"}: {obj.name}')
        return agentes

    def _criar_blueprints(self, agentes, force):
        from apps.core.models import DocumentType, DocumentCategory
        from apps.intelligent_assistant.models import DocumentBlueprint, BlueprintSection
        self.stdout.write('\n[3/3] Blueprints...')
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
                defaults={'description': bp_data['description'], 'version': bp_data['version'], 'legal_basis': bp_data['legal_basis'], 'primary_color': bp_data['primary_color'], 'secondary_color': bp_data['secondary_color'], 'cover_title': bp_data['cover_title'], 'cover_page_enabled': True, 'cover_subtitle': bp_data['description'], 'organization_name': 'Verus.AI', 'organization_acronym': 'BJus', 'pdf_font_family': 'Times New Roman', 'pdf_font_size': '12pt', 'pdf_line_height': '1.5', 'pdf_text_align': 'justify', 'pdf_paragraph_indent': '1.25cm', 'pdf_page_margin_top': '3cm', 'pdf_page_margin_bottom': '2cm', 'pdf_page_margin_left': '3cm', 'pdf_page_margin_right': '2cm', 'is_active': True, 'is_default': True}
            )
            if not created and force:
                blueprint.description = bp_data['description']
                blueprint.primary_color = bp_data['primary_color']
                blueprint.pdf_page_margin_top = '3cm'
                blueprint.pdf_page_margin_bottom = '2cm'
                blueprint.pdf_page_margin_left = '3cm'
                blueprint.pdf_page_margin_right = '2cm'
                blueprint.save()
                blueprint.sections.all().delete()
                created = True
            # Área primária
            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)
            # Áreas secundárias
            for area_code in bp_data.get('secondary_area_codes', []):
                sec_cat = cats.get(area_code)
                if sec_cat:
                    blueprint.areas.add(sec_cat)
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {blueprint.name}')
            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_tributario_complemento')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
