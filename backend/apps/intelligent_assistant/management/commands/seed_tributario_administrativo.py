"""
Seed Tributário e Administrativo — Verus.AI.

Uso:
    python manage.py seed_tributario_administrativo
    python manage.py seed_tributario_administrativo --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction

MODEL = 'mistralai/mistral-medium-2505'
PROVIDER = 'watsonx'
TEMP_GENERATOR = 0.7
TEMP_VALIDATOR = 0.3
MAX_TOKENS = 4096

CATEGORIAS = [
    {
        'code': 'tributario',
        'name': 'Tributário',
        'description': 'Peças jurídicas de Direito Tributário e Fiscal',
        'display_order': 12,
    },
    {
        'code': 'administrativo',
        'name': 'Administrativo',
        'description': 'Peças jurídicas de Direito Administrativo e controle da Administração Pública',
        'display_order': 13,
    },
]

TIPOS_DOCUMENTO = [
    {
        'code': 'embargos_execucao_fiscal',
        'name': 'Embargos à Execução Fiscal',
        'short_name': 'Emb. Exec. Fiscal',
        'description': 'Defesa do executado em execução fiscal promovida pela Fazenda Pública',
        'category': 'tributario',
        'icon': 'FileWarning',
        'color': '#D97706',
        'legal_basis': 'Lei 6.830/1980 (LEF), arts. 16-22; CTN, arts. 142-173; CPC/2015, arts. 914-920',
        'display_order': 1,
    },
    {
        'code': 'excecao_executividade_fiscal',
        'name': 'Exceção de Pré-Executividade Fiscal',
        'short_name': 'Exc. Pré-Exec. Fisc.',
        'description': 'Objeção ao crédito tributário sem penhora prévia na execução fiscal',
        'category': 'tributario',
        'icon': 'FileWarning',
        'color': '#D97706',
        'legal_basis': 'Construção jurisprudencial; STJ Súmula 393; CTN arts. 142-173',
        'display_order': 2,
    },
    {
        'code': 'recurso_administrativo',
        'name': 'Recurso Administrativo',
        'short_name': 'Rec. Administrativo',
        'description': 'Recurso contra decisão administrativa desfavorável',
        'category': 'administrativo',
        'icon': 'TrendingUp',
        'color': '#059669',
        'legal_basis': 'Lei 9.784/1999 (processo adm. federal); CF/88, art. 5º, LV; Lei 10.522/2002',
        'display_order': 1,
    },
    {
        'code': 'mandado_seguranca_administrativo',
        'name': 'Mandado de Segurança contra Ato Administrativo',
        'short_name': 'MS Administrativo',
        'description': 'MS para proteger direito líquido e certo violado por autoridade administrativa',
        'category': 'administrativo',
        'icon': 'Shield',
        'color': '#059669',
        'legal_basis': 'CF/88, art. 5º, LXIX; Lei 12.016/2009; Lei 9.784/1999',
        'display_order': 2,
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

PROMPT_GERADOR_TRIBUTARIO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Tributário brasileiro.

LEGISLAÇÃO VIGENTE:
- CTN (Lei 5.172/1966); CF/88, arts. 145-162; Lei 6.830/1980 (LEF)
- CPC/2015 (subsidiário à LEF); LC 87/1996 (ICMS); LC 116/2003 (ISS)
- Lei 9.430/1996; Lei 10.522/2002 (CADIN)

REGRAS ESSENCIAIS:
1. Prescrição tributária: CTN art. 174 (5 anos do lançamento definitivo)
2. Decadência: CTN art. 173 (5 anos para lançamento)
3. Exclusão do crédito: CTN arts. 175-182 (isenção e anistia)
4. Suspensão: CTN art. 151 (moratória, depósito, liminar, parcelamento, recurso)
5. Extinção: CTN art. 156 (pagamento, compensação, prescrição, remissão, etc.)
6. Exceção de pré-executividade: STJ Súmula 393 (matérias de ordem pública)
7. Embargos à execução fiscal: LEF art. 16 (prazo 30 dias após penhora ou depósito)
8. Súmulas STJ em matéria tributária: 7, 213, 355, 393, 430, 436, 446, 452, 460, 497, 555, 558, 560
9. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_ADMINISTRATIVO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Administrativo brasileiro.

LEGISLAÇÃO VIGENTE:
- CF/88, arts. 37-43 (Administração Pública); Lei 9.784/1999 (processo adm. federal)
- Lei 8.429/1992 (improbidade adm.); Lei 8.666/1993 e Lei 14.133/2021 (licitações)
- Lei 12.016/2009 (Mandado de Segurança); DL 4.657/1942 (LINDB)
- Lei 9.784/1999 para recursos administrativos federais

REGRAS ESSENCIAIS:
1. Princípios: legalidade, impessoalidade, moralidade, publicidade, eficiência (CF art. 37)
2. Recurso administrativo: Lei 9.784/1999, arts. 56-65. Prazo: 10 dias (art. 59)
3. Mandado de Segurança: direito líquido e certo (CF art. 5º LXIX; Lei 12.016/2009)
4. MS preventivo: ameaça concreta de lesão a direito líquido e certo
5. Prazo MS: 120 dias do ato coator (Lei 12.016/2009, art. 23)
6. Poder discricionário vs vinculado: controle judicial dos limites da discricionariedade
7. Súmulas STJ/STF em Administrativo: STF Súmulas 266, 272, 429, 473, 510, 632, 633
8. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'embargos_execucao_fiscal': 'gerador_tributario',
    'excecao_executividade_fiscal': 'gerador_tributario',
    'recurso_administrativo': 'gerador_administrativo',
    'mandado_seguranca_administrativo': 'gerador_administrativo',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'embargos_execucao_fiscal',
        'name': 'Embargos à Execução Fiscal - LEF',
        'description': 'Defesa do contribuinte executado em execução fiscal da Fazenda Pública',
        'version': '1.0',
        'legal_basis': 'Lei 6.830/1980, arts. 16-22; CTN arts. 142-173',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Embargos à Execução Fiscal',
        'sections': [
            {
                'number': 1, 'key': 'cabecalho_admissibilidade',
                'name': 'Cabeçalho e Admissibilidade',
                'description': 'Identificação do processo e requisitos dos embargos',
                'instructions': 'Qualifique o embargante (executado). Identifique o processo de execução fiscal (número, exequente/Fazenda, valor, tributo). Demonstre a tempestividade (LEF art. 16: 30 dias após garantia do juízo).',
                'fields': [
                    {'name': 'comarca_vara', 'label': 'Comarca/Vara de Execuções Fiscais', 'type': 'text', 'required': True},
                    {'name': 'processo_execucao', 'label': 'Número do Processo de Execução Fiscal', 'type': 'text', 'required': True},
                    {'name': 'exequente', 'label': 'Exequente (Fazenda Federal/Estadual/Municipal)', 'type': 'text', 'required': True},
                    {'name': 'tributo_cobrado', 'label': 'Tributo e Exercício Cobrado', 'type': 'text', 'required': True},
                    {'name': 'valor_execucao', 'label': 'Valor da Execução (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'materia_embargos',
                'name': 'I - Da Matéria dos Embargos',
                'description': 'Fundamentos jurídicos da defesa tributária',
                'instructions': 'Apresente as matérias de defesa: prescrição (CTN art. 174), decadência (CTN art. 173), pagamento, compensação, nulidade da CDA, ilegitimidade de partes, erro de cálculo, parcelamento, imunidade ou isenção. Fundamente em cada defesa com artigos do CTN.',
                'fields': [
                    {'name': 'materia_principal', 'label': 'Principal Matéria de Defesa', 'type': 'select', 'required': True, 'options': ['Prescrição (CTN art. 174)', 'Decadência (CTN art. 173)', 'Pagamento (CTN art. 156, I)', 'Compensação (CTN art. 156, II)', 'Nulidade da CDA', 'Ilegitimidade de Parte', 'Imunidade/Isenção', 'Erro de Cálculo/Valor', 'Outra']},
                    {'name': 'descricao_defesa', 'label': 'Descrição Detalhada da Defesa', 'type': 'textarea', 'required': True},
                    {'name': 'documentos_prova', 'label': 'Documentos de Prova (comprovantes de pagamento, etc.)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos dos embargos à execução fiscal',
                'instructions': 'Formule pedidos: recebimento dos embargos com efeito suspensivo (LEF art. 19), julgamento procedente, extinção da execução, cancelamento da penhora, condenação da Fazenda em honorários.',
                'fields': [
                    {'name': 'pedido_efeito_suspensivo', 'label': 'Pede efeito suspensivo à execução?', 'type': 'select', 'required': True, 'options': ['Sim (garantia integral do juízo)', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'excecao_executividade_fiscal',
        'name': 'Exceção de Pré-Executividade Fiscal - STJ Súmula 393',
        'description': 'Objeção processual ao crédito tributário sem necessidade de penhora prévia',
        'version': '1.0',
        'legal_basis': 'Construção jurisprudencial; STJ Súmula 393; CTN arts. 142-173',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Exceção de Pré-Executividade',
        'sections': [
            {
                'number': 1, 'key': 'cabimento',
                'name': 'Do Cabimento da Exceção de Pré-Executividade',
                'description': 'Fundamentação do cabimento da exceção',
                'instructions': 'Fundamente o cabimento: matérias de ordem pública passíveis de conhecimento de ofício (STJ Súmula 393). Liste as matérias que dispensam penhora: prescrição, ilegitimidade, inexigibilidade do título, nulidade da CDA por vício formal insanável.',
                'fields': [
                    {'name': 'processo_execucao', 'label': 'Número do Processo de Execução Fiscal', 'type': 'text', 'required': True},
                    {'name': 'materia_ordem_publica', 'label': 'Matéria de Ordem Pública Arguida', 'type': 'select', 'required': True, 'options': ['Prescrição (CTN art. 174)', 'Ilegitimidade passiva (não é contribuinte)', 'Inexigibilidade do título (CDA com vícios formais)', 'Extinção do crédito por pagamento', 'Imunidade tributária constitucional']},
                ],
            },
            {
                'number': 2, 'key': 'fundamentacao',
                'name': 'I - Da Fundamentação Jurídica',
                'description': 'Argumentação jurídica da exceção',
                'instructions': 'Desenvolva os fundamentos jurídicos: demonstre com precisão a matéria arguida, cite artigos do CTN, jurisprudência do STJ e STF (usando marcadores para acórdãos não verificados). Apresente provas documentais se disponíveis.',
                'fields': [
                    {'name': 'argumentacao_juridica', 'label': 'Argumentação Jurídica Detalhada', 'type': 'textarea', 'required': True},
                    {'name': 'prova_documental', 'label': 'Provas Documentais (comprovantes, CDA, etc.)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos da exceção de pré-executividade',
                'instructions': 'Formule pedidos: acolhimento da exceção, extinção da execução sem resolução de mérito (ilegitimidade) ou com resolução (prescrição/extinção), cancelamento de eventuais constrições, condenação em honorários.',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'recurso_administrativo',
        'name': 'Recurso Administrativo - Lei 9.784/1999',
        'description': 'Recurso administrativo contra decisão desfavorável da Administração Pública',
        'version': '1.0',
        'legal_basis': 'Lei 9.784/1999, arts. 56-65; CF/88, art. 5º, LV',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Recurso Administrativo',
        'sections': [
            {
                'number': 1, 'key': 'cabecalho_recurso',
                'name': 'Identificação e Tempestividade',
                'description': 'Dados do recorrente, autoridade e prazo',
                'instructions': 'Identifique o recorrente, autoridade que proferiu a decisão recorrida, processo administrativo e demonstre a tempestividade (Lei 9.784/1999, art. 59: 10 dias da ciência). Mencione a instância revisora.',
                'fields': [
                    {'name': 'recorrente_nome', 'label': 'Nome do Recorrente', 'type': 'text', 'required': True},
                    {'name': 'orgao_autoridade', 'label': 'Órgão/Autoridade que Proferiu a Decisão', 'type': 'text', 'required': True},
                    {'name': 'numero_processo_adm', 'label': 'Número do Processo Administrativo', 'type': 'text', 'required': True},
                    {'name': 'data_ciencia', 'label': 'Data da Ciência da Decisão Recorrida', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'razoes_recurso',
                'name': 'I - Das Razões do Recurso',
                'description': 'Fundamentos jurídicos e fáticos do recurso',
                'instructions': 'Exponha as razões do recurso: resuma a decisão recorrida e seus fundamentos, apresente os erros (fáticos e jurídicos), demonstre como os fatos e o direito foram mal aplicados. Cite princípios da Administração Pública (CF art. 37).',
                'fields': [
                    {'name': 'decisao_recorrida_resumo', 'label': 'Resumo da Decisão Recorrida', 'type': 'textarea', 'required': True},
                    {'name': 'razoes_impugnacao', 'label': 'Razões de Impugnação (erros fáticos e jurídicos)', 'type': 'textarea', 'required': True},
                    {'name': 'documentos_novos', 'label': 'Documentos Novos (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos do recurso administrativo',
                'instructions': 'Formule pedidos: conhecimento e provimento do recurso, reforma ou anulação da decisão recorrida, concessão de efeito suspensivo se necessário (Lei 9.784/1999, art. 61).',
                'fields': [
                    {'name': 'pedido_efeito_suspensivo', 'label': 'Requer efeito suspensivo?', 'type': 'select', 'required': True, 'options': ['Sim (risco de dano irreparável)', 'Não']},
                    {'name': 'pedido_especifico', 'label': 'Pedido Específico (reforma, anulação, etc.)', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'mandado_seguranca_administrativo',
        'name': 'Mandado de Segurança contra Ato Administrativo - Lei 12.016/2009',
        'description': 'MS para proteger direito líquido e certo violado por autoridade administrativa pública',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 5º, LXIX; Lei 12.016/2009; Lei 9.784/1999',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Mandado de Segurança',
        'sections': [
            {
                'number': 1, 'key': 'autoridade_coatora',
                'name': 'Identificação da Autoridade Coatora',
                'description': 'Qualificação da autoridade e do ato impugnado',
                'instructions': 'Identifique a autoridade coatora (nome, cargo, órgão) e o ato coator (data, natureza, número do processo administrativo). Demonstre que é autoridade pública para fins da Lei 12.016/2009. Demonstre a tempestividade: prazo de 120 dias do ato coator (art. 23).',
                'fields': [
                    {'name': 'impetrante_nome', 'label': 'Nome do Impetrante', 'type': 'text', 'required': True},
                    {'name': 'autoridade_coatora', 'label': 'Autoridade Coatora (nome, cargo, órgão)', 'type': 'text', 'required': True},
                    {'name': 'ato_coator', 'label': 'Ato Coator (data, natureza, número do processo)', 'type': 'textarea', 'required': True},
                    {'name': 'data_ato_coator', 'label': 'Data do Ato Coator', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'direito_liquido_certo',
                'name': 'I - Do Direito Líquido e Certo',
                'description': 'Demonstração do direito violado',
                'instructions': 'Demonstre o direito líquido e certo violado: apresente a norma que confere o direito, prove documentalmente que o impetrante preenche os requisitos, demonstre a ilegalidade ou abuso de poder do ato coator. Cite legislação administrativa pertinente.',
                'fields': [
                    {'name': 'direito_violado', 'label': 'Direito Violado e Base Legal', 'type': 'textarea', 'required': True},
                    {'name': 'ilegalidade_abuso', 'label': 'Ilegalidade ou Abuso de Poder do Ato', 'type': 'textarea', 'required': True},
                    {'name': 'prova_pre_constituida', 'label': 'Prova Pré-Constituída (documentos que provam o direito)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos do mandado de segurança',
                'instructions': 'Formule pedidos: liminar inaudita altera parte (fumus boni iuris + periculum in mora), notificação da autoridade coatora, ciência do Ministério Público, segurança definitiva com anulação/desconstituição do ato.',
                'fields': [
                    {'name': 'pedido_liminar', 'label': 'Pedido de Liminar?', 'type': 'select', 'required': True, 'options': ['Sim (urgência e periculum in mora)', 'Não']},
                    {'name': 'pedido_especifico', 'label': 'Pedido Específico (anulação, desconstituição, abstenção)', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Tributário e Administrativo no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Tributário e Administrativo'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            return

        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Tributário e Administrativo concluído!\n'))

    def _criar_categorias(self):
        from apps.core.models import DocumentCategory
        self.stdout.write('\n[1/4] Categorias...')
        for data in CATEGORIAS:
            obj, created = DocumentCategory.objects.get_or_create(
                code=data['code'],
                defaults={'name': data['name'], 'description': data['description'], 'display_order': data['display_order'], 'is_active': True}
            )
            self.stdout.write(f'  {"✓ Criada" if created else "⊘ Existe"}: {obj.name}')

    def _criar_tipos_documento(self):
        from apps.core.models import DocumentType, DocumentCategory
        self.stdout.write('\n[2/4] Tipos de documento...')
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
        self.stdout.write('\n[3/4] Agentes de seção...')
        specs = [
            {'key': 'gerador_tributario', 'name': 'Verus.AI - Gerador Tributário', 'description': 'Gera seções de peças tributárias e fiscais', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_TRIBUTARIO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'gerador_administrativo', 'name': 'Verus.AI - Gerador Administrativo', 'description': 'Gera seções de peças de Direito Administrativo', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_ADMINISTRATIVO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
        from apps.core.models import DocumentType
        from apps.intelligent_assistant.models import DocumentBlueprint, BlueprintSection
        self.stdout.write('\n[4/4] Blueprints...')
        tipos = {t.code: t for t in DocumentType.objects.all()}
        for bp_data in BLUEPRINTS_DATA:
            doc_type = tipos.get(bp_data['doc_type_code'])
            if not doc_type:
                self.stdout.write(self.style.ERROR(f'  ✗ Tipo não encontrado: {bp_data["doc_type_code"]}'))
                continue
            blueprint, created = DocumentBlueprint.objects.get_or_create(
                document_type=doc_type,
                name=bp_data['name'],
                defaults={'description': bp_data['description'], 'version': bp_data['version'], 'legal_basis': bp_data['legal_basis'], 'primary_color': bp_data['primary_color'], 'secondary_color': bp_data['secondary_color'], 'cover_title': bp_data['cover_title'], 'cover_page_enabled': True, 'cover_subtitle': bp_data['description'], 'organization_name': 'Verus.AI', 'organization_acronym': 'BJus', 'pdf_font_family': 'Times New Roman', 'pdf_font_size': '12pt', 'pdf_line_height': '1.5', 'pdf_text_align': 'justify', 'pdf_paragraph_indent': '1.25cm', 'is_active': True, 'is_default': True}
            )
            if not created and force:
                blueprint.description = bp_data['description']
                blueprint.primary_color = bp_data['primary_color']
                blueprint.save()
                blueprint.sections.all().delete()
                created = True
            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)
            # Garante is_default=True em re-execução
            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {blueprint.name}')
            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_tributario')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
