"""
Seed Consumidor - Complemento — Verus.AI.
Ação Coletiva de Consumidor, Reclamação de Produto/Serviço.

Uso:
    python manage.py seed_consumidor_complemento
    python manage.py seed_consumidor_complemento --force
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
        'code': 'acao_coletiva_consumidor',
        'name': 'Ação Coletiva de Consumidor',
        'short_name': 'Ação Coletiva CDC',
        'description': 'Ação coletiva para tutela de direitos individuais homogêneos ou coletivos de consumidores',
        'category': 'consumidor',
        'icon': 'Users',
        'color': '#7C3AED',
        'legal_basis': 'CDC, arts. 81-104; Lei 7.347/1985 (LACP); CF/88, art. 129, III',
        'display_order': 5,
    },
    {
        'code': 'reclamacao_produto_servico',
        'name': 'Reclamação de Produto/Serviço Defeituoso',
        'short_name': 'Recl. Produto/Serviço',
        'description': 'Ação para reparação de danos por produto defeituoso ou serviço inadequado',
        'category': 'consumidor',
        'icon': 'AlertTriangle',
        'color': '#7C3AED',
        'legal_basis': 'CDC, arts. 18-25 (vício do produto), 26-27 (prazos decadenciais)',
        'display_order': 6,
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

PROMPT_GERADOR_CONSUMIDOR = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito do Consumidor brasileiro.

LEGISLAÇÃO VIGENTE:
- CDC — Lei 8.078/1990 (Código de Defesa do Consumidor)
- LACP — Lei 7.347/1985 (Ação Civil Pública)
- CF/88, art. 5º, XXXII (proteção ao consumidor) e art. 129, III (legitimidade do MP)
- CPC/2015 (subsidiário); Lei 9.099/1995 (JEC)

REGRAS ESSENCIAIS:
1. Vício do produto: CDC art. 18 (prazo 30 dias — bem não durável; 90 dias — durável)
2. Prazos decadenciais: CDC art. 26 (30/90 dias para vício aparente); art. 27 (5 anos — fato do produto/serviço)
3. Responsabilidade objetiva do fornecedor: CDC arts. 12-14 (fato) e 18-20 (vício)
4. Direitos básicos: CDC art. 6º (informação, proteção, reparação integral, acesso à justiça)
5. Inversão do ônus da prova: CDC art. 6º, VIII (hipossuficiência ou verossimilhança)
6. Ação coletiva: CDC arts. 81-104; LACP art. 1º; legitimidade — MP, associações, DP (CDC art. 82)
7. Dano moral coletivo: CDC art. 6º, VI; STJ — dano moral difuso/coletivo
8. Súmulas STJ: 54, 326, 362, 381, 385, 402, 407, 548, 550, 563, 572
9. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'acao_coletiva_consumidor': 'gerador_consumidor_complemento',
    'reclamacao_produto_servico': 'gerador_consumidor_complemento',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'acao_coletiva_consumidor',
        'name': 'Ação Coletiva de Consumidor - CDC arts. 81-104',
        'description': 'Ação coletiva para tutela de direitos difusos, coletivos ou individuais homogêneos de consumidores',
        'version': '1.0',
        'legal_basis': 'CDC, arts. 81-104; Lei 7.347/1985 (LACP); CF/88, art. 129, III',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Ação Coletiva de Consumidor',
        'secondary_area_codes': ['acoes_peticoes'],
        'sections': [
            {
                'number': 1, 'key': 'legitimidade_ativa',
                'name': 'Da Legitimidade Ativa',
                'description': 'Demonstração da legitimidade para a ação coletiva',
                'instructions': 'Identifique o legitimado ativo: Ministério Público (CF art. 129, III), Defensoria Pública, associação (CDC art. 82, IV — constituída há mais de 1 ano, com finalidade de defesa do consumidor), órgão público (art. 82, III). Demonstre que os requisitos legais da legitimidade estão preenchidos (CDC arts. 82-84). Classifique o interesse tutelado: difuso (CDC art. 81, I), coletivo em sentido estrito (art. 81, II) ou individual homogêneo (art. 81, III). ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'legitimado_ativo', 'label': 'Legitimado Ativo (quem propõe)', 'type': 'select', 'required': True, 'options': ['Ministério Público', 'Defensoria Pública', 'Associação de consumidores', 'Órgão público de defesa do consumidor', 'Outro ente legitimado']},
                    {'name': 'tipo_interesse', 'label': 'Tipo de Interesse Tutelado', 'type': 'select', 'required': True, 'options': ['Difuso (CDC art. 81, I) — sujeitos indetermináveis', 'Coletivo stricto sensu (CDC art. 81, II) — grupo determinável', 'Individual homogêneo (CDC art. 81, III) — origem comum']},
                    {'name': 'descricao_grupo', 'label': 'Descrição do Grupo de Consumidores Afetados', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos',
                'name': 'I - Dos Fatos',
                'description': 'Narrativa dos fatos que fundamentam a ação coletiva',
                'instructions': 'Narre os fatos de forma clara e objetiva: qual o produto/serviço; quem é o fornecedor (réu); qual a conduta ilícita ou lesiva (prática abusiva, publicidade enganosa, produto defeituoso, cláusula abusiva, etc.); quando e como ocorreu; quantos consumidores foram afetados. Descreva a extensão do dano coletivo. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'fornecedor_reu', 'label': 'Fornecedor Réu (nome/CNPJ)', 'type': 'text', 'required': True},
                    {'name': 'produto_servico', 'label': 'Produto ou Serviço Envolvido', 'type': 'text', 'required': True},
                    {'name': 'conduta_ilicita', 'label': 'Conduta Ilícita do Fornecedor', 'type': 'select', 'required': True, 'options': ['Produto/serviço defeituoso (CDC art. 12/18)', 'Publicidade enganosa (CDC art. 37)', 'Prática abusiva (CDC art. 39)', 'Cláusula abusiva em contrato (CDC art. 51)', 'Cobrança indevida (CDC art. 42)', 'Outra conduta']},
                    {'name': 'narrativa_fatos', 'label': 'Narrativa Detalhada dos Fatos', 'type': 'textarea', 'required': True},
                    {'name': 'numero_afetados', 'label': 'Número Estimado de Consumidores Afetados', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'dano_coletivo',
                'name': 'II - Do Dano Coletivo e Responsabilidade',
                'description': 'Caracterização do dano coletivo e responsabilidade do fornecedor',
                'instructions': 'Caracterize o dano coletivo: dano material (prejuízo econômico aos consumidores), dano moral coletivo (abalo à coletividade), dano difuso (degradação de direitos transindividuais). Fundamente a responsabilidade objetiva do fornecedor (CDC arts. 12-14 para fato; arts. 18-20 para vício). Demonstre nexo causal entre conduta e dano. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'tipo_dano', 'label': 'Tipo de Dano Coletivo', 'type': 'select', 'required': True, 'options': ['Dano material homogêneo', 'Dano moral coletivo', 'Dano material + moral coletivo', 'Dano difuso (interesse difuso)']},
                    {'name': 'descricao_dano', 'label': 'Descrição do Dano Coletivo', 'type': 'textarea', 'required': True},
                    {'name': 'valor_dano_estimado', 'label': 'Valor do Dano Estimado (se calculável)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'reparacao',
                'name': 'III - Da Reparação e Tutela Coletiva',
                'description': 'Formas de reparação e tutela coletiva cabíveis',
                'instructions': 'Indique as formas de reparação: obrigação de fazer (recall, adequação do produto, cessação da prática), obrigação de não fazer (proibição de publicidade), indenização ao Fundo de Defesa de Direitos Difusos (Lei 7.347/1985, art. 13), reparação fluida (CDC art. 100). Mencione a possibilidade de tutela inibitória (CDC art. 84). ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'forma_reparacao', 'label': 'Forma de Reparação Pleiteada', 'type': 'select', 'required': True, 'options': ['Obrigação de fazer (recall/adequação)', 'Obrigação de não fazer (cessação de prática)', 'Indenização ao Fundo de Defesa (LACP art. 13)', 'Reparação aos consumidores (liquidação individual)', 'Combinação das formas acima']},
                    {'name': 'descricao_reparacao', 'label': 'Descrição da Reparação Pretendida', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedidos',
                'name': 'IV - Dos Pedidos',
                'description': 'Pedidos da ação coletiva',
                'instructions': 'Formule os pedidos: (a) tutela de urgência (CPC arts. 300-311) para cessação imediata da conduta lesiva; (b) procedência da ação com condenação nas obrigações de fazer/não fazer; (c) indenização ao FDD ou liquidação individual pelos consumidores habilitados (CDC art. 97-100); (d) dano moral coletivo; (e) honorários e custas (LACP art. 18 — MP isento); (f) ampla divulgação da decisão (CDC art. 96). Valor da causa. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'pede_tutela_urgencia', 'label': 'Requer Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Sim — urgência comprovada', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                    {'name': 'pedidos_adicionais', 'label': 'Pedidos Adicionais', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'reclamacao_produto_servico',
        'name': 'Reclamação de Produto/Serviço Defeituoso - CDC arts. 18-27',
        'description': 'Ação individual para reparação de danos por vício ou defeito em produto ou serviço',
        'version': '1.0',
        'legal_basis': 'CDC, arts. 18-25 (vício do produto/serviço), 26-27 (prazos)',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Reclamação de Produto/Serviço Defeituoso',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_partes',
                'name': 'Qualificação das Partes',
                'description': 'Identificação do consumidor autor e do fornecedor réu',
                'instructions': 'Qualifique o consumidor (autor): nome, CPF, endereço, dados de contato. Identifique o fornecedor réu: razão social, CNPJ, endereço. Indique o juízo competente (JEC se valor até 40 salários mínimos; Vara Cível se superior). Mencione a relação de consumo. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'consumidor_nome', 'label': 'Nome do Consumidor (Autor)', 'type': 'text', 'required': True},
                    {'name': 'consumidor_cpf', 'label': 'CPF do Consumidor', 'type': 'text', 'required': True},
                    {'name': 'fornecedor_nome', 'label': 'Razão Social do Fornecedor (Réu)', 'type': 'text', 'required': True},
                    {'name': 'fornecedor_cnpj', 'label': 'CNPJ do Fornecedor', 'type': 'text', 'required': False},
                    {'name': 'juizo', 'label': 'Juízo Competente', 'type': 'select', 'required': True, 'options': ['Juizado Especial Cível (até 40 SM)', 'Vara Cível (acima de 40 SM)', 'Vara de Fazenda Pública (fornecedor público)']},
                ],
            },
            {
                'number': 2, 'key': 'produto_servico_defeituoso',
                'name': 'I - Do Produto/Serviço Defeituoso',
                'description': 'Descrição do defeito ou vício e sua ocorrência',
                'instructions': 'Descreva o produto ou serviço adquirido: nome, modelo, data de compra/contratação, valor pago, número da nota fiscal. Descreva o defeito ou vício com precisão: quando foi constatado, natureza do problema (não funciona, apresenta risco, diverge do que foi ofertado). Diferencie vício (CDC art. 18 — impropriedade para uso) de defeito/fato do produto (CDC art. 12 — risco à saúde/segurança). ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'produto_servico', 'label': 'Produto ou Serviço', 'type': 'text', 'required': True},
                    {'name': 'data_compra', 'label': 'Data da Compra/Contratação', 'type': 'text', 'required': True},
                    {'name': 'valor_pago', 'label': 'Valor Pago (R$)', 'type': 'text', 'required': True},
                    {'name': 'tipo_problema', 'label': 'Tipo de Problema', 'type': 'select', 'required': True, 'options': ['Vício do produto (impropriedade para uso — CDC art. 18)', 'Vício do serviço (reexecução, abatimento, rescisão — CDC art. 20)', 'Fato do produto (defeito que causa risco — CDC art. 12)', 'Fato do serviço (defeito que causa dano — CDC art. 14)', 'Publicidade enganosa/abusiva (CDC art. 37)']},
                    {'name': 'descricao_defeito', 'label': 'Descrição Detalhada do Defeito/Vício', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'tentativa_extrajudicial',
                'name': 'II - Da Tentativa Extrajudicial de Solução',
                'description': 'Demonstração das tentativas de resolução antes da ação',
                'instructions': 'Descreva as tentativas extrajudiciais: reclamação ao SAC do fornecedor (data, protocolo), reclamação no PROCON (data, número), reclamação no site consumidor.gov.br, notificação extrajudicial. Demonstre que o fornecedor não solucionou o problema no prazo de 30 dias (CDC art. 18, §1º). ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'reclamacao_sac', 'label': 'Reclamação no SAC (data e protocolo)', 'type': 'text', 'required': False},
                    {'name': 'reclamacao_procon', 'label': 'Reclamação no PROCON (data e número)', 'type': 'text', 'required': False},
                    {'name': 'prazo_30_dias', 'label': 'Fornecedor deixou de solucionar em 30 dias?', 'type': 'select', 'required': True, 'options': ['Sim — decorrido o prazo sem solução', 'Sim — negou o vício', 'Não houve tentativa extrajudicial — urgência/inutilidade']},
                    {'name': 'descricao_tentativas', 'label': 'Descrição das Tentativas', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'danos',
                'name': 'III - Dos Danos Sofridos',
                'description': 'Identificação e quantificação dos danos',
                'instructions': 'Identifique os danos: (a) dano material — valor do produto defeituoso, despesas para conserto/substituição, lucros cessantes; (b) dano moral — constrangimento, angústia, humilhação, tempo perdido com reclamações. Quantifique o dano material. Para o dano moral, apresente os fatos que o caracterizam. Cite CDC art. 6º, VI (reparação integral). ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'dano_material_valor', 'label': 'Valor do Dano Material (R$)', 'type': 'text', 'required': False},
                    {'name': 'descricao_dano_material', 'label': 'Descrição do Dano Material', 'type': 'textarea', 'required': False},
                    {'name': 'pede_dano_moral', 'label': 'Requer Dano Moral?', 'type': 'select', 'required': True, 'options': ['Sim — graves constrangimentos comprovados', 'Não']},
                    {'name': 'descricao_dano_moral', 'label': 'Descrição dos Constrangimentos (dano moral)', 'type': 'textarea', 'required': False},
                    {'name': 'valor_dano_moral_sugerido', 'label': 'Valor Sugerido para Dano Moral (R$)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'pedidos',
                'name': 'IV - Dos Pedidos',
                'description': 'Pedidos da ação de reclamação',
                'instructions': 'Formule os pedidos com base no CDC art. 18 (substituição do produto, reexecução, abatimento ou restituição) e/ou art. 20 (para serviço): (a) substituição do produto/reexecução do serviço OU restituição do valor pago; (b) indenização por danos materiais; (c) indenização por danos morais; (d) inversão do ônus da prova (CDC art. 6º, VIII); (e) honorários. Valor da causa = soma dos pedidos. ' + CONST_ANTI_ALUCINACAO,
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido Principal (CDC art. 18/20)', 'type': 'select', 'required': True, 'options': ['Substituição do produto por outro da mesma espécie', 'Reexecução dos serviços', 'Restituição integral do valor pago', 'Abatimento proporcional do preço', 'Complemento da quantidade (produto pesado/medido)']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (R$)', 'type': 'text', 'required': True},
                    {'name': 'pede_inversao_onus', 'label': 'Requer Inversão do Ônus da Prova?', 'type': 'select', 'required': True, 'options': ['Sim — hipossuficiência do consumidor', 'Não']},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Consumidor - Complemento no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Consumidor Complemento'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            return

        with transaction.atomic():
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Consumidor Complemento concluído!\n'))

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
            {'key': 'gerador_consumidor_complemento', 'name': 'Verus.AI - Gerador Consumidor Complemento', 'description': 'Gera ações coletivas e reclamações de consumidor', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_CONSUMIDOR, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_consumidor_complemento')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
