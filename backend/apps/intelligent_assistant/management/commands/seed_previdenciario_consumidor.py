"""
Seed Previdenciário e Consumidor — Verus.AI.

Uso:
    python manage.py seed_previdenciario_consumidor
    python manage.py seed_previdenciario_consumidor --force
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
        'code': 'previdenciario',
        'name': 'Previdenciário',
        'description': 'Peças jurídicas de Direito Previdenciário e benefícios INSS',
        'display_order': 10,
    },
    {
        'code': 'consumidor',
        'name': 'Consumidor',
        'description': 'Peças jurídicas de Direito do Consumidor - CDC',
        'display_order': 11,
    },
]

TIPOS_DOCUMENTO = [
    {
        'code': 'peticao_inicial_previdenciaria',
        'name': 'Petição Inicial Previdenciária',
        'short_name': 'Pet. Previdenciária',
        'description': 'Petição inicial para concessão ou revisão de benefício previdenciário',
        'category': 'previdenciario',
        'icon': 'Shield',
        'color': '#7C3AED',
        'legal_basis': 'Lei 8.213/1991; Decreto 3.048/1999; CF/88, art. 201',
        'display_order': 1,
    },
    {
        'code': 'bpc_loas',
        'name': 'BPC/LOAS - Benefício de Prestação Continuada',
        'short_name': 'BPC/LOAS',
        'description': 'Ação para concessão do BPC/LOAS para idoso ou pessoa com deficiência',
        'category': 'previdenciario',
        'icon': 'Heart',
        'color': '#7C3AED',
        'legal_basis': 'Lei 8.742/1993, arts. 20-21; CF/88, art. 203, V; Decreto 6.214/2007',
        'display_order': 2,
    },
    {
        'code': 'aposentadoria_especial',
        'name': 'Aposentadoria Especial',
        'short_name': 'Aposen. Especial',
        'description': 'Ação judicial para concessão de aposentadoria especial por exposição a agentes nocivos',
        'category': 'previdenciario',
        'icon': 'Briefcase',
        'color': '#7C3AED',
        'legal_basis': 'Lei 8.213/1991, arts. 57-58; EC 103/2019, art. 19; Decreto 3.048/1999',
        'display_order': 3,
    },
    {
        'code': 'reclamacao_consumerista',
        'name': 'Ação Indenizatória - CDC',
        'short_name': 'Ação CDC',
        'description': 'Ação de indenização por danos nas relações de consumo',
        'category': 'consumidor',
        'icon': 'ShieldCheck',
        'color': '#2563EB',
        'legal_basis': 'CDC, Lei 8.078/1990; CF/88, art. 5º XXXII; CC/2002, arts. 186-927',
        'display_order': 1,
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

PROMPT_GERADOR_PREVIDENCIARIO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Previdenciário brasileiro.

LEGISLAÇÃO VIGENTE:
- CF/88, arts. 201-204; Lei 8.213/1991; Decreto 3.048/1999; Lei 8.212/1991
- LC 142/2013 (aposentadoria do deficiente); Lei 8.742/1993 (LOAS); Lei 10.741/2003

REGRAS ESSENCIAIS:
1. Qualidade de segurado: Lei 8.213/1991, art. 11 + art. 14. Período de graça: art. 15
2. Carência: 180 contribuições mensais para aposentadoria (art. 25)
3. Aposentadoria por idade: 65 anos homem / 62 anos mulher (EC 103/2019)
4. Aposentadoria especial: 15, 20 ou 25 anos de exposição a agentes nocivos (arts. 57-58); exige PPP e LTCAT
5. BPC/LOAS: 65+ ou pessoa com deficiência, renda per capita < 1/4 SM (Lei 8.742 art. 20)
6. Prazo decadencial de revisão: 10 anos (Lei 8.213/1991, art. 103-A)
7. Súmulas STJ: 9, 25, 39, 320. Súmulas TNU: 05, 09, 14, 18, 32, 47, 48, 64, 79, 80
8. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_CONSUMIDOR = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito do Consumidor brasileiro.

LEGISLAÇÃO VIGENTE:
- CDC, Lei 8.078/1990; CF/88, art. 5º XXXII e art. 170 V
- Decreto 7.962/2013 (comércio eletrônico); Lei 14.181/2021 (superendividamento)

REGRAS ESSENCIAIS:
1. Responsabilidade objetiva: fato do produto/serviço (CDC arts. 12-14); vício (CDC arts. 18-20)
2. Inversão do ônus: CDC art. 6º VIII (hipossuficiência + verossimilhança)
3. Prazos decadenciais: 30 dias (não durável) / 90 dias (durável) — CDC art. 26
4. Prescrição: 5 anos para reparação de danos (CDC art. 27)
5. CDC aplica-se a: bancos (STJ Súmula 297), planos de saúde (STJ Súmulas 302, 469), aéreas (Súmula 473)
6. Distinguir: fato do produto (CDC 12-14) de vício do produto (CDC 18-20)
7. Súmulas STJ: 297, 302, 322, 332, 370, 379, 381, 385, 388, 469, 473, 480, 483, 492, 509
8. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'peticao_inicial_previdenciaria': 'gerador_previdenciario',
    'bpc_loas': 'gerador_previdenciario',
    'aposentadoria_especial': 'gerador_previdenciario',
    'reclamacao_consumerista': 'gerador_consumidor',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'peticao_inicial_previdenciaria',
        'name': 'Petição Inicial Previdenciária - Lei 8.213/1991',
        'description': 'Petição para concessão ou revisão de benefício previdenciário junto ao INSS/Juizado',
        'version': '1.0',
        'legal_basis': 'Lei 8.213/1991; Decreto 3.048/1999; CF/88, art. 201',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Petição Previdenciária',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_segurado',
                'name': 'Qualificação do Segurado e da Causa',
                'description': 'Dados do segurado, benefício pleiteado e competência',
                'instructions': 'Qualifique o segurado (nome, CPF, NIT/PIS/PASEP, data de nascimento, endereço). Identifique o benefício pleiteado e o juízo competente (JEF ou Vara Federal Previdenciária). Mencione o número do requerimento administrativo indeferido (se houver).',
                'fields': [
                    {'name': 'segurado_nome', 'label': 'Nome do Segurado', 'type': 'text', 'required': True},
                    {'name': 'nit_pis', 'label': 'NIT/PIS/PASEP', 'type': 'text', 'required': True},
                    {'name': 'beneficio_pleiteado', 'label': 'Benefício Pleiteado', 'type': 'select', 'required': True, 'options': ['Aposentadoria por Idade', 'Aposentadoria por Tempo de Contribuição', 'Aposentadoria por Incapacidade Permanente', 'Auxílio por Incapacidade Temporária', 'Pensão por Morte', 'Salário-Maternidade', 'Auxílio-Acidente', 'Outro']},
                    {'name': 'num_requerimento_adm', 'label': 'Número do Requerimento Administrativo (se houver)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'historico_previdenciario',
                'name': 'I - Dos Fatos e Histórico Previdenciário',
                'description': 'Histórico laboral e previdenciário do segurado',
                'instructions': 'Narre o histórico previdenciário: períodos de contribuição, empregos, CNIS, qualidade de segurado. Descreva o indeferimento administrativo se ocorreu. Mencione documentação disponível.',
                'fields': [
                    {'name': 'historico_laboral', 'label': 'Histórico Laboral e de Contribuições', 'type': 'textarea', 'required': True},
                    {'name': 'indeferimento_motivo', 'label': 'Motivo do Indeferimento Administrativo (se aplicável)', 'type': 'textarea', 'required': False},
                    {'name': 'documentos_disponíveis', 'label': 'Documentos Disponíveis (CNIS, PPP, laudos, certidões)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'fundamento_direito',
                'name': 'II - Do Direito ao Benefício',
                'description': 'Requisitos legais preenchidos',
                'instructions': 'Demonstre o preenchimento dos requisitos legais do benefício (carência, qualidade de segurado, tempo de contribuição ou condição incapacitante). Cite artigos específicos da Lei 8.213/1991 e EC 103/2019 quando aplicável.',
                'fields': [
                    {'name': 'requisitos_preenchidos', 'label': 'Requisitos Preenchidos (carência, qualidade de segurado, etc.)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'pedidos',
                'name': 'III - Dos Pedidos',
                'description': 'Pedidos de concessão do benefício e DIB',
                'instructions': 'Formule pedidos: concessão/revisão do benefício, DIB (Data de Início do Benefício) retroativa à data do requerimento administrativo ou do implemento das condições, tutela de urgência se necessário, litigância de má-fé se cabível.',
                'fields': [
                    {'name': 'data_inicio_beneficio', 'label': 'Data de Início do Benefício (DIB) Pleiteada', 'type': 'text', 'required': True},
                    {'name': 'pedido_tutela_urgencia', 'label': 'Pedido de Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (risco de dano irreparável)']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (12× benefício pleiteado)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'bpc_loas',
        'name': 'BPC/LOAS - Lei 8.742/1993',
        'description': 'Ação judicial para concessão do Benefício de Prestação Continuada a idoso ou deficiente',
        'version': '1.0',
        'legal_basis': 'Lei 8.742/1993, arts. 20-21; CF/88, art. 203, V',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'BPC/LOAS',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_requerente',
                'name': 'Qualificação do Requerente',
                'description': 'Dados do requerente do BPC/LOAS',
                'instructions': 'Qualifique o requerente (idoso 65+ anos ou pessoa com deficiência). Informe dados pessoais completos, composição familiar e número de requerimento administrativo negado.',
                'fields': [
                    {'name': 'requerente_nome', 'label': 'Nome do Requerente', 'type': 'text', 'required': True},
                    {'name': 'tipo_beneficiario', 'label': 'Tipo de Beneficiário', 'type': 'select', 'required': True, 'options': ['Idoso (65 anos ou mais)', 'Pessoa com Deficiência']},
                    {'name': 'data_nascimento', 'label': 'Data de Nascimento', 'type': 'text', 'required': True},
                    {'name': 'composicao_familiar', 'label': 'Composição do Grupo Familiar e Renda Mensal', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'condicao_beneficiario',
                'name': 'I - Da Condição de Miserabilidade',
                'description': 'Demonstração dos requisitos de hipossuficiência',
                'instructions': 'Demonstre a miserabilidade: renda per capita do grupo familiar inferior a 1/4 do salário mínimo (Lei 8.742 art. 20 §3º). Para PcD: descreva a deficiência e impedimentos de longo prazo. Cite o Decreto 6.214/2007.',
                'fields': [
                    {'name': 'renda_per_capita', 'label': 'Renda Per Capita do Grupo Familiar', 'type': 'text', 'required': True},
                    {'name': 'descricao_deficiencia', 'label': 'Descrição da Deficiência/Impedimentos (para PcD)', 'type': 'textarea', 'required': False},
                    {'name': 'documentos_miserabilidade', 'label': 'Documentos que Comprovam Miserabilidade', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos de concessão do BPC/LOAS',
                'instructions': 'Formule pedidos: concessão do BPC/LOAS, DIB retroativa à data do requerimento administrativo, tutela de urgência se necessário (hipossuficiência evidente), condenação em honorários sucumbenciais.',
                'fields': [
                    {'name': 'data_requerimento_adm', 'label': 'Data do Requerimento Administrativo', 'type': 'text', 'required': True},
                    {'name': 'pedido_tutela', 'label': 'Pedido de Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'aposentadoria_especial',
        'name': 'Aposentadoria Especial - Lei 8.213/1991',
        'description': 'Ação judicial para concessão de aposentadoria especial por agentes nocivos',
        'version': '1.0',
        'legal_basis': 'Lei 8.213/1991, arts. 57-58; EC 103/2019, art. 19; Decreto 3.048/1999',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Aposentadoria Especial',
        'sections': [
            {
                'number': 1, 'key': 'dados_segurado',
                'name': 'Dados do Segurado',
                'description': 'Qualificação do segurado e identificação do benefício',
                'instructions': 'Qualifique o segurado com dados completos. Identifique o período pleiteado de aposentadoria especial (15, 20 ou 25 anos conforme agente nocivo). Mencione o indeferimento administrativo.',
                'fields': [
                    {'name': 'segurado_nome', 'label': 'Nome do Segurado', 'type': 'text', 'required': True},
                    {'name': 'nit_pis', 'label': 'NIT/PIS/PASEP', 'type': 'text', 'required': True},
                    {'name': 'tempo_especial_pleiteado', 'label': 'Tempo de Exposição Pleiteado', 'type': 'select', 'required': True, 'options': ['15 anos (agentes com limite mais restritivo)', '20 anos', '25 anos (regra geral)']},
                ],
            },
            {
                'number': 2, 'key': 'historico_laboral_especial',
                'name': 'I - Do Histórico Laboral e Exposição a Agentes Nocivos',
                'description': 'Períodos de exposição e documentação comprobatória',
                'instructions': 'Descreva os períodos de exposição a agentes nocivos (físicos, químicos ou biológicos). Liste empregadores, atividades, agentes nocivos e concentrações. Mencione PPP (Perfil Profissiográfico Previdenciário) e LTCAT (Laudo Técnico das Condições Ambientais). Cite anexo IV do Decreto 3.048/1999.',
                'fields': [
                    {'name': 'periodos_exposicao', 'label': 'Períodos de Exposição (empresa, cargo, agente nocivo, período)', 'type': 'textarea', 'required': True},
                    {'name': 'agentes_nocivos', 'label': 'Agentes Nocivos (físicos/químicos/biológicos)', 'type': 'textarea', 'required': True},
                    {'name': 'documentos_ppp_ltcat', 'label': 'PPP e LTCAT disponíveis?', 'type': 'select', 'required': True, 'options': ['Sim - ambos disponíveis', 'Apenas PPP', 'Apenas LTCAT', 'Nenhum - será requisitado']},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos de concessão da aposentadoria especial',
                'instructions': 'Formule pedidos: reconhecimento dos períodos de atividade especial, concessão da aposentadoria especial, DIB retroativa ao requerimento administrativo, tutela de urgência se necessário.',
                'fields': [
                    {'name': 'data_requerimento', 'label': 'Data do Requerimento Administrativo', 'type': 'text', 'required': True},
                    {'name': 'pedido_pericia', 'label': 'Necessita de perícia judicial?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (documentação suficiente)']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'reclamacao_consumerista',
        'name': 'Ação Indenizatória - CDC (Lei 8.078/1990)',
        'description': 'Ação de indenização por dano material e moral em relação de consumo',
        'version': '1.0',
        'legal_basis': 'CDC, Lei 8.078/1990; CF/88, art. 5º XXXII; CC/2002, arts. 186-927',
        'primary_color': '#2563EB',
        'secondary_color': '#3B82F6',
        'cover_title': 'Ação Indenizatória - CDC',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação das Partes',
                'description': 'Juízo e identificação do consumidor e fornecedor',
                'instructions': 'Endereçe ao Juizado Especial Cível ou Vara do Consumidor. Qualifique o consumidor (autor) e o fornecedor/empresa (réu). Mencione a relação de consumo estabelecida (CDC arts. 2º e 3º).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca / Juizado', 'type': 'text', 'required': True},
                    {'name': 'consumidor_nome', 'label': 'Nome do Consumidor (Autor)', 'type': 'text', 'required': True},
                    {'name': 'fornecedor_nome', 'label': 'Nome do Fornecedor/Empresa (Réu)', 'type': 'text', 'required': True},
                    {'name': 'tipo_relacao_consumo', 'label': 'Tipo de Relação de Consumo', 'type': 'select', 'required': True, 'options': ['Produto adquirido', 'Serviço contratado', 'Plano de saúde', 'Serviço bancário/financeiro', 'Transporte aéreo', 'Comércio eletrônico', 'Outro']},
                ],
            },
            {
                'number': 2, 'key': 'fatos_consumo',
                'name': 'I - Dos Fatos',
                'description': 'Descrição do problema e danos sofridos',
                'instructions': 'Narre cronologicamente os fatos: produto/serviço adquirido, defeito ou vício, tentativa de resolução extrajudicial, recusa do fornecedor. Distingua fato do produto (CDC arts. 12-14) de vício (CDC arts. 18-20) conforme o caso.',
                'fields': [
                    {'name': 'produto_servico', 'label': 'Produto/Serviço (descrição, data de aquisição, valor)', 'type': 'textarea', 'required': True},
                    {'name': 'problema_descricao', 'label': 'Descrição do Problema / Defeito / Vício', 'type': 'textarea', 'required': True},
                    {'name': 'tentativa_resolucao', 'label': 'Tentativa de Resolução Extrajudicial (SAC, Procon, etc.)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'fundamento_cdc',
                'name': 'II - Do Direito (CDC)',
                'description': 'Fundamentos jurídicos no CDC',
                'instructions': 'Fundamente no CDC: responsabilidade objetiva do fornecedor (arts. 12-14 ou 18-20), inversão do ônus da prova (art. 6º VIII), dano moral in re ipsa quando cabível. Cite Súmulas STJ pertinentes.',
                'fields': [
                    {'name': 'tipo_responsabilidade', 'label': 'Tipo de Responsabilidade', 'type': 'select', 'required': True, 'options': ['Fato do Produto/Serviço (CDC arts. 12-14 - responsabilidade objetiva)', 'Vício do Produto/Serviço (CDC arts. 18-20)', 'Prática Abusiva (CDC art. 39)', 'Publicidade Enganosa/Abusiva (CDC arts. 37-38)']},
                    {'name': 'inversao_onus', 'label': 'Pede inversão do ônus da prova?', 'type': 'select', 'required': True, 'options': ['Sim (hipossuficiência técnica/econômica)', 'Não']},
                ],
            },
            {
                'number': 4, 'key': 'danos_pedidos',
                'name': 'III - Dos Danos e Pedidos',
                'description': 'Quantificação dos danos e pedidos finais',
                'instructions': 'Descreva e quantifique os danos materiais e morais. Formule pedidos: condenação em danos materiais, danos morais, restituição/substituição do produto/serviço se cabível, tutela de urgência, honorários.',
                'fields': [
                    {'name': 'danos_materiais', 'label': 'Danos Materiais (valor e discriminação)', 'type': 'textarea', 'required': False},
                    {'name': 'danos_morais_valor', 'label': 'Valor dos Danos Morais Pleiteados', 'type': 'text', 'required': False},
                    {'name': 'pedido_especifico', 'label': 'Pedido Específico (restituição, substituição, abatimento)', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Previdenciário e Consumidor no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Previdenciário e Consumidor'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            return

        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Previdenciário e Consumidor concluído!\n'))

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
            {'key': 'gerador_previdenciario', 'name': 'Verus.AI - Gerador Previdenciário', 'description': 'Gera seções de peças previdenciárias', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_PREVIDENCIARIO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'gerador_consumidor', 'name': 'Verus.AI - Gerador Consumidor', 'description': 'Gera seções de peças de Direito do Consumidor', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_CONSUMIDOR, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_previdenciario')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
