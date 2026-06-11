"""
Seed Família - Complemento — Verus.AI.
Paternidade, união estável, curatela/interdição, adoção.

Uso:
    python manage.py seed_familia_complemento
    python manage.py seed_familia_complemento --force
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
        'code': 'reconhecimento_paternidade',
        'name': 'Ação de Reconhecimento de Paternidade',
        'short_name': 'Rec. Paternidade',
        'description': 'Ação para reconhecimento judicial de vínculo de filiação',
        'category': 'familia_sucessoes',
        'icon': 'Users',
        'color': '#E11D48',
        'legal_basis': 'CC/2002, arts. 1.606-1.614; CF/88, art. 227 §6º; Lei 8.560/1992',
        'display_order': 7,
    },
    {
        'code': 'uniao_estavel',
        'name': 'Ação de Reconhecimento/Dissolução de União Estável',
        'short_name': 'União Estável',
        'description': 'Ação para reconhecimento ou dissolução de união estável',
        'category': 'familia_sucessoes',
        'icon': 'Heart',
        'color': '#E11D48',
        'legal_basis': 'CC/2002, arts. 1.723-1.727; Lei 9.278/1996; STF ADPF 132/ADI 4277',
        'display_order': 8,
    },
    {
        'code': 'curatela_interdição',
        'name': 'Ação de Curatela / Tomada de Decisão Apoiada',
        'short_name': 'Curatela',
        'description': 'Ação para interdição e nomeação de curador para pessoa incapaz',
        'category': 'familia_sucessoes',
        'icon': 'Shield',
        'color': '#0891B2',
        'legal_basis': 'CC/2002, arts. 1.767-1.783; CPC/2015, arts. 747-758; Lei 13.146/2015 (EPD)',
        'display_order': 9,
    },
    {
        'code': 'acao_adocao',
        'name': 'Ação de Adoção',
        'short_name': 'Adoção',
        'description': 'Ação judicial para adoção de criança ou adolescente',
        'category': 'familia_sucessoes',
        'icon': 'Heart',
        'color': '#E11D48',
        'legal_basis': 'ECA, Lei 8.069/1990, arts. 39-52; CC/2002, arts. 1.618-1.629; Lei 13.509/2017',
        'display_order': 10,
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
"""

PROMPT_GERADOR_FAMILIA = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito de Família e Sucessões brasileiro.

LEGISLAÇÃO VIGENTE:
- CC/2002 arts. 1.511-1.783 (família); CF/88 art. 226-227; ECA Lei 8.069/1990
- Lei 8.560/1992 (investigação de paternidade); Lei 13.146/2015 (EPD)
- STF: ADPF 132/ADI 4277 (união homoafetiva equiparada à união estável)
- Súmulas STJ: 277, 354, 364, 379, 380, 382, 383, 385, 397

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'reconhecimento_paternidade': 'gerador_familia',
    'uniao_estavel': 'gerador_familia',
    'curatela_interdição': 'gerador_familia',
    'acao_adocao': 'gerador_familia',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'reconhecimento_paternidade',
        'name': 'Ação de Reconhecimento de Paternidade - CC/2002',
        'description': 'Petição para reconhecimento judicial de filiação com pedido de DNA',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.606-1.614; Lei 8.560/1992',
        'primary_color': '#E11D48',
        'secondary_color': '#F43F5E',
        'cover_title': 'Ação de Reconhecimento de Paternidade',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e partes',
                'instructions': 'Endereçe à Vara de Família. Qualifique: filho(a) - autor(a), representado pelo genitor que tem a guarda, e pretenso pai - réu.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'filho_nome', 'label': 'Nome do Filho(a) Autor(a)', 'type': 'text', 'required': True},
                    {'name': 'representante', 'label': 'Representante Legal do Autor (mãe/pai)', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Pretenso Pai (Réu)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos_paternidade',
                'name': 'I - Dos Fatos',
                'description': 'Relacionamento e indícios de paternidade',
                'instructions': 'Narre o relacionamento entre a mãe e o réu, período de concepção, ausência de reconhecimento voluntário, indícios de paternidade disponíveis. Cite art. 1.606 CC (ação de estado de filiação — imprescritível).',
                'fields': [
                    {'name': 'contexto_relacionamento', 'label': 'Contexto do Relacionamento entre Mãe e Réu', 'type': 'textarea', 'required': True},
                    {'name': 'data_nascimento_filho', 'label': 'Data de Nascimento do Filho(a)', 'type': 'text', 'required': True},
                    {'name': 'indicios_paternidade', 'label': 'Indícios de Paternidade (convivência, fotos, mensagens, etc.)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Reconhecimento de paternidade e pedidos acessórios',
                'instructions': 'Pedidos: tutela de urgência para determinação de exame de DNA (gratuito se hipossuficiente - Lei 10.317/2001), reconhecimento de paternidade, retificação de registro civil (art. 1.609 CC), alimentos provisórios se necessário, alteração do sobrenome.',
                'fields': [
                    {'name': 'pedido_dna', 'label': 'Pedido de exame de DNA?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (já há reconhecimento)']},
                    {'name': 'pedido_alimentos', 'label': 'Pedido de alimentos cumulado?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'uniao_estavel',
        'name': 'Ação de Reconhecimento/Dissolução de União Estável - CC/2002',
        'description': 'Ação para reconhecimento ou dissolução de união estável com partilha de bens',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.723-1.727; Lei 9.278/1996',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'União Estável',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Companheiros e dados da convivência',
                'instructions': 'Qualifique os companheiros. Informe: período de convivência (início e fim), se houve contrato escrito de união estável, caracterização dos requisitos (CC art. 1.723: pública, contínua, duradoura, com intuito de constituir família).',
                'fields': [
                    {'name': 'companheiro1_nome', 'label': 'Nome do 1º Companheiro', 'type': 'text', 'required': True},
                    {'name': 'companheiro2_nome', 'label': 'Nome do 2º Companheiro', 'type': 'text', 'required': True},
                    {'name': 'periodo_convivencia', 'label': 'Período de Convivência (início a fim)', 'type': 'text', 'required': True},
                    {'name': 'tipo_acao', 'label': 'Tipo de Ação', 'type': 'select', 'required': True, 'options': ['Reconhecimento de União Estável', 'Dissolução de União Estável', 'Reconhecimento e Dissolução (cumulados)']},
                ],
            },
            {
                'number': 2, 'key': 'bens_partilha',
                'name': 'I - Do Patrimônio e da Partilha',
                'description': 'Bens adquiridos na constância da união estável',
                'instructions': 'Descreva bens adquiridos na constância da união (CC art. 1.725: regime de comunhão parcial, salvo contrato escrito). Liste imóveis, veículos, contas, etc. Proponha partilha igualitária (50%) de cada bem comum.',
                'fields': [
                    {'name': 'bens_comuns', 'label': 'Bens Adquiridos na Constância da União Estável', 'type': 'textarea', 'required': False},
                    {'name': 'filhos_menores', 'label': 'Há filhos menores?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (incluir guarda e alimentos)']},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos de reconhecimento e/ou dissolução',
                'instructions': 'Pedidos: reconhecimento da união estável, dissolução se for o caso, partilha dos bens comuns (50% a cada companheiro), guarda e alimentos dos filhos se houver, meação previdenciária se aplicável.',
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'curatela_interdição',
        'name': 'Ação de Curatela - CPC/2015',
        'description': 'Ação para decretação de curatela de pessoa com deficiência ou incapacidade',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.767-1.783; CPC/2015, arts. 747-758; Lei 13.146/2015',
        'primary_color': '#0891B2',
        'secondary_color': '#06B6D4',
        'cover_title': 'Ação de Curatela',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_curandado',
                'name': 'Qualificação do Interessado e do Curador Proposto',
                'description': 'Dados da pessoa a ser curatelada',
                'instructions': 'Qualifique o interessado (pessoa a ser curatelada) e o requerente/curador proposto. Informe a condição que justifica a curatela (CC art. 1.767). Atenção: Lei 13.146/2015 (EPD) — curatela é medida excepcional e proporcional.',
                'fields': [
                    {'name': 'curandado_nome', 'label': 'Nome do Interessado (a ser curatelado)', 'type': 'text', 'required': True},
                    {'name': 'curador_proposto', 'label': 'Nome do Curador Proposto (parente mais próximo)', 'type': 'text', 'required': True},
                    {'name': 'causa_curatela', 'label': 'Causa da Curatela (CC art. 1.767)', 'type': 'select', 'required': True, 'options': ['Enfermidade ou deficiência mental', 'Incapacidade de exprimir vontade', 'Pródigo (CC art. 1.782)', 'Ausência (CC art. 22)']},
                ],
            },
            {
                'number': 2, 'key': 'fatos_medicos',
                'name': 'I - Dos Fatos e da Condição de Saúde',
                'description': 'Descrição da incapacidade e necessidade de curatela',
                'instructions': 'Descreva a condição médica/psíquica da pessoa, documentação disponível (laudos médicos, psicológicos). Fundamente a necessidade de curatela respeitando o EPD (Lei 13.146/2015): curatela afeta apenas atos patrimoniais/negociais, não a vida pessoal. Considere Tomada de Decisão Apoiada (CC arts. 1.783-A) como alternativa menos restritiva.',
                'fields': [
                    {'name': 'diagnostico', 'label': 'Diagnóstico/Condição Médica (com CID)', 'type': 'textarea', 'required': True},
                    {'name': 'laudos_disponiveis', 'label': 'Laudos Médicos Disponíveis', 'type': 'textarea', 'required': False},
                    {'name': 'actos_afetados', 'label': 'Atos que a Curatela Deve Abranger', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Decretação da curatela e nomeação do curador',
                'instructions': 'Pedidos: decretação da curatela (CPC art. 749), nomeação do curador proposto, realização de avaliação multidisciplinar (CPC art. 753), intervenção do MP (CPC art. 752).',
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_adocao',
        'name': 'Ação de Adoção - ECA/CC',
        'description': 'Petição inicial para adoção de criança ou adolescente conforme ECA e CC',
        'version': '1.0',
        'legal_basis': 'ECA, Lei 8.069/1990, arts. 39-52; CC/2002, arts. 1.618-1.629; Lei 13.509/2017',
        'primary_color': '#E11D48',
        'secondary_color': '#F43F5E',
        'cover_title': 'Ação de Adoção',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_adotantes',
                'name': 'Qualificação dos Adotantes e do Adotando',
                'description': 'Dados dos adotantes e da criança a ser adotada',
                'instructions': 'Qualifique os adotantes (maiores de 18 anos, pelo menos 16 anos mais velhos que o adotando - CC art. 1.619). Identifique o adotando. Confirme inscrição no cadastro de adotantes (ECA art. 50) ou hipótese de dispensa (art. 50 §13).',
                'fields': [
                    {'name': 'adotante1_nome', 'label': 'Nome do Adotante', 'type': 'text', 'required': True},
                    {'name': 'adotante2_nome', 'label': 'Nome do Co-Adotante (se houver)', 'type': 'text', 'required': False},
                    {'name': 'adotando_nome', 'label': 'Nome do Adotando', 'type': 'text', 'required': True},
                    {'name': 'idade_adotando', 'label': 'Idade do Adotando', 'type': 'text', 'required': True},
                    {'name': 'situacao_guarda', 'label': 'Situação Atual da Guarda do Adotando', 'type': 'select', 'required': True, 'options': ['Guarda fática pelos adotantes há mais de 3 anos', 'Guarda judicial concedida', 'Criança em acolhimento institucional', 'Adoção unilateral (cônjuge do pai/mãe biológico)']},
                ],
            },
            {
                'number': 2, 'key': 'fatos_interesse_adocao',
                'name': 'I - Dos Fatos e do Interesse na Adoção',
                'description': 'Histórico e razões da adoção',
                'instructions': 'Descreva: história do relacionamento adotantes-adotando, tempo de convivência, vínculos afetivos estabelecidos, condições para oferecer ambiente familiar saudável. Fundamente no princípio do melhor interesse da criança (ECA art. 3º) e dignidade humana.',
                'fields': [
                    {'name': 'historico_relacionamento', 'label': 'Histórico do Relacionamento com o Adotando', 'type': 'textarea', 'required': True},
                    {'name': 'condicoes_familia', 'label': 'Condições da Família Adotante (moradia, renda, estabilidade)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos de adoção',
                'instructions': 'Pedidos: deferimento da adoção (ECA art. 47), cancelamento do registro de nascimento original, novo registro com nome dos adotantes, alteração de sobrenome do adotando (se desejado), intervenção do MP (ECA art. 202).',
                'fields': [
                    {'name': 'altera_prenome', 'label': 'O adotando deseja alterar o prenome?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (o adotando concorda - se maior de 12 anos)']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints complementares de Família (paternidade, união estável, curatela, adoção)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY-RUN'))
            return
        with transaction.atomic():
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, options['force'])
        self.stdout.write(self.style.SUCCESS('✓ Família Complemento concluído!'))

    def _criar_tipos_documento(self):
        from apps.core.models import DocumentType, DocumentCategory
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
            self.stdout.write(f'  {"✓" if created else "⊘"}: {obj.name}')

    def _criar_agentes_secao(self):
        from apps.intelligent_assistant.models import SectionAgentConfig
        specs = [
            {'key': 'gerador_familia', 'name': 'Verus.AI - Gerador Família e Sucessões', 'description': 'Gera seções de Família e Sucessões', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_FAMILIA, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'validador_juridico', 'name': 'Verus.AI - Validador Jurídico', 'description': 'Valida conteúdo jurídico', 'agent_type': 'validator', 'system_prompt': PROMPT_VALIDADOR_JURIDICO, 'temperature': TEMP_VALIDATOR, 'max_tokens': 1024, 'is_default': False},
        ]
        agentes = {}
        for spec in specs:
            obj, _ = SectionAgentConfig.objects.update_or_create(
                name=spec['name'],
                defaults={'description': spec['description'], 'agent_type': spec['agent_type'], 'system_prompt': spec['system_prompt'], 'user_prompt_template': USER_TEMPLATE_SECAO, 'llm_provider': PROVIDER, 'model_name': MODEL, 'temperature': spec['temperature'], 'max_tokens': spec['max_tokens'], 'use_rag': False, 'rag_top_k': 5, 'rag_similarity_threshold': 0.7, 'is_active': True, 'is_default': spec['is_default']}
            )
            agentes[spec['key']] = obj
        return agentes

    def _criar_blueprints(self, agentes, force):
        from apps.core.models import DocumentType
        from apps.intelligent_assistant.models import DocumentBlueprint, BlueprintSection
        tipos = {t.code: t for t in DocumentType.objects.all()}
        for bp_data in BLUEPRINTS_DATA:
            doc_type = tipos.get(bp_data['doc_type_code'])
            if not doc_type:
                self.stdout.write(self.style.ERROR(f'  ✗ {bp_data["doc_type_code"]}'))
                continue
            blueprint, created = DocumentBlueprint.objects.get_or_create(
                document_type=doc_type, name=bp_data['name'],
                defaults={'description': bp_data['description'], 'version': bp_data['version'], 'legal_basis': bp_data['legal_basis'], 'primary_color': bp_data['primary_color'], 'secondary_color': bp_data['secondary_color'], 'cover_title': bp_data['cover_title'], 'cover_page_enabled': True, 'cover_subtitle': bp_data['description'], 'organization_name': 'Verus.AI', 'organization_acronym': 'BJus', 'pdf_font_family': 'Times New Roman', 'pdf_font_size': '12pt', 'pdf_line_height': '1.5', 'pdf_text_align': 'justify', 'pdf_paragraph_indent': '1.25cm', 'is_active': True, 'is_default': True}
            )
            if not created and force:
                blueprint.description = bp_data['description']
                blueprint.save()
                blueprint.sections.all().delete()
                created = True
            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)
            # Garante is_default=True em re-execução
            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])
            self.stdout.write(f'  {"✓" if created else "⊘"}: {blueprint.name}')
            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_familia')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint, section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
