"""
Seed Trabalhista - Complemento — Verus.AI.
Recurso Ordinário, Impugnação à Sentença, Dissídio Coletivo, Ação de Cumprimento.

Uso:
    python manage.py seed_trabalhista_complemento
    python manage.py seed_trabalhista_complemento --force
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
        'code': 'recurso_ordinario_trabalhista',
        'name': 'Recurso Ordinário Trabalhista',
        'short_name': 'RO Trabalhista',
        'description': 'Recurso contra sentença trabalhista de primeiro grau (equivalente à apelação)',
        'category': 'trabalhista',
        'icon': 'TrendingUp',
        'color': '#0D9488',
        'legal_basis': 'CLT, arts. 895-896; CF/88, art. 7º; TST - Súmulas',
        'display_order': 12,
    },
    {
        'code': 'impugnacao_sentenca_trabalhista',
        'name': 'Impugnação à Sentença de Liquidação Trabalhista',
        'short_name': 'Impug. Sent. Trab.',
        'description': 'Impugnação ao cálculo da sentença de liquidação trabalhista',
        'category': 'trabalhista',
        'icon': 'FileWarning',
        'color': '#0D9488',
        'legal_basis': 'CLT, arts. 879-884; CPC/2015, arts. 525-527 (subsidiário)',
        'display_order': 13,
    },
    {
        'code': 'dissidio_coletivo',
        'name': 'Dissídio Coletivo',
        'short_name': 'Dissídio Coletivo',
        'description': 'Ação coletiva para criação ou revisão de normas trabalhistas via Justiça do Trabalho',
        'category': 'trabalhista',
        'icon': 'Users',
        'color': '#0D9488',
        'legal_basis': 'CLT, arts. 856-875; CF/88, art. 114 §2º',
        'display_order': 14,
    },
    {
        'code': 'acao_cumprimento_trabalhista',
        'name': 'Ação de Cumprimento Trabalhista',
        'short_name': 'Ação Cumprimento',
        'description': 'Ação para cumprimento de cláusulas de acordo coletivo ou sentença normativa',
        'category': 'trabalhista',
        'icon': 'FileCheck',
        'color': '#0D9488',
        'legal_basis': 'CLT, art. 872; CF/88, art. 7º XXVI (acordos/convenções coletivas)',
        'display_order': 15,
    },
]

USER_TEMPLATE_SECAO = """Gere o conteúdo da seção "{{section_name}}" para a seguinte peça jurídica:
OBJETIVO DO DOCUMENTO: {{objective}}
INFORMAÇÕES DO CASO: {{context}}
SEÇÕES ANTERIORES JÁ GERADAS: {{previous_sections}}
Instruções específicas: {{instructions}}
Gere apenas o conteúdo desta seção, com linguagem jurídica formal e completa."""

CONST_ANTI_ALUCINACAO = """DIRETRIZES DE SEGURANÇA JURÍDICA — OBRIGATÓRIAS:
- NUNCA invente Súmulas TST, OJs ou artigos CLT que não existam
- Dado faltante: [INFORMAÇÃO NECESSÁRIA: descrição]
- Jurisprudência: [PESQUISAR JURISPRUDÊNCIA: tema TST]
"""

PROMPT_GERADOR_TRABALHISTA = CONST_ANTI_ALUCINACAO + """Você é advogado trabalhista especialista em Justiça do Trabalho, CLT e TST.

LEGISLAÇÃO VIGENTE:
- CLT (DL 5.452/1943); Lei 13.467/2017 (Reforma Trabalhista); CF/88, art. 7º
- IN TST 39/2016 (CPC subsidiário); IN TST 41/2018 (reforma trabalhista)

REGRAS ESSENCIAIS:
1. RO: CLT art. 895. Prazo 8 dias (art. 895 caput). Depósito recursal obrigatório
2. Recurso de Revista: CLT art. 896 (violação literal de lei ou divergência jurisprudencial)
3. Liquidação: CLT art. 879. Impugnação: CLT art. 884. Prazo: 10 dias
4. Dissídio coletivo: CF art. 114 §2º (negociação prévia obrigatória)
5. Ação de cumprimento: CLT art. 872 (descumprimento de sentença normativa ou ACT/CCT)
6. Verbas rescisórias: CLT arts. 477-487 (cálculo pós-reforma 2017)
7. Prescrição: bienal (CLT art. 11; CF art. 7º XXIX) e quinquenal durante o contrato
8. Súmulas TST consolidadas: 85 (banco de horas), 291 (horas extras habituais), 331 (terceirização), 342, 369, 437, 444
9. OJs SBDI-1 do TST: apenas as consolidadas

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'recurso_ordinario_trabalhista': 'gerador_trabalhista',
    'impugnacao_sentenca_trabalhista': 'gerador_trabalhista',
    'dissidio_coletivo': 'gerador_trabalhista',
    'acao_cumprimento_trabalhista': 'gerador_trabalhista',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'recurso_ordinario_trabalhista',
        'name': 'Recurso Ordinário Trabalhista - CLT art. 895',
        'description': 'Recurso contra sentença trabalhista de primeiro grau para o TRT',
        'version': '1.0',
        'legal_basis': 'CLT, arts. 895-896',
        'primary_color': '#0D9488',
        'secondary_color': '#14B8A6',
        'cover_title': 'Recurso Ordinário Trabalhista',
        'sections': [
            {
                'number': 1, 'key': 'admissibilidade',
                'name': 'Pressupostos de Admissibilidade',
                'description': 'Tempestividade, preparo e legitimidade',
                'instructions': 'Demonstre: tempestividade (CLT art. 895: 8 dias da publicação da sentença), regularidade do preparo (depósito recursal + custas), legitimidade do recorrente. Identifique processo, recorrente e recorrido.',
                'fields': [
                    {'name': 'recorrente_nome', 'label': 'Nome do Recorrente (Empregado/Empregador)', 'type': 'text', 'required': True},
                    {'name': 'processo_numero', 'label': 'Número do Processo (PJET)', 'type': 'text', 'required': True},
                    {'name': 'data_publicacao', 'label': 'Data de Publicação da Sentença', 'type': 'text', 'required': True},
                    {'name': 'deposito_recursal', 'label': 'Depósito Recursal Recolhido?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (hipossuficiente econômico - isenção)', 'Não se aplica (reclamante sempre isento)']},
                ],
            },
            {
                'number': 2, 'key': 'razoes_recurso',
                'name': 'I - Das Razões do Recurso',
                'description': 'Impugnação específica dos fundamentos da sentença',
                'instructions': 'Impugne especificamente cada capítulo da sentença recorrida (CLT art. 899 §1º: fundamentação específica). Desenvolva: erro na valoração das provas, violação de norma material (CLT, CF, CCT/ACT), dosimetria equivocada de verbas trabalhistas.',
                'fields': [
                    {'name': 'capitulos_impugnados', 'label': 'Capítulos da Sentença Impugnados', 'type': 'textarea', 'required': True},
                    {'name': 'razoes_detalhadas', 'label': 'Razões Detalhadas por Capítulo', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos do recurso ordinário',
                'instructions': 'Pedidos: conhecimento e provimento do recurso, reforma da sentença nos capítulos impugnados, com a consequente improcedência dos pedidos (se empregador) ou procedência (se empregado), redistribuição de ônus da sucumbência.',
                'fields': [
                    {'name': 'pedido_especifico', 'label': 'Pedido Específico de Reforma', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'impugnacao_sentenca_trabalhista',
        'name': 'Impugnação à Sentença de Liquidação - CLT art. 884',
        'description': 'Impugnação ao cálculo da sentença de liquidação na fase de execução trabalhista',
        'version': '1.0',
        'legal_basis': 'CLT, arts. 879-884',
        'primary_color': '#0D9488',
        'secondary_color': '#14B8A6',
        'cover_title': 'Impugnação à Sentença de Liquidação',
        'sections': [
            {
                'number': 1, 'key': 'cabecalho_admissibilidade',
                'name': 'Identificação e Tempestividade',
                'description': 'Processo e prazo da impugnação',
                'instructions': 'Identifique o processo de execução, a data de homologação da conta (CLT art. 884: impugnação no prazo de 10 dias), impugnante e valor da conta.',
                'fields': [
                    {'name': 'processo_numero', 'label': 'Número do Processo', 'type': 'text', 'required': True},
                    {'name': 'impugnante_nome', 'label': 'Nome do Impugnante', 'type': 'text', 'required': True},
                    {'name': 'valor_conta', 'label': 'Valor da Conta Homologada (R$)', 'type': 'text', 'required': True},
                    {'name': 'data_homologacao', 'label': 'Data de Homologação da Conta', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'erros_calculo',
                'name': 'I - Dos Erros de Cálculo',
                'description': 'Identificação dos erros na conta de liquidação',
                'instructions': 'Aponte especificamente os erros: verbas indevidas incluídas, valores calculados incorretamente, juros e correção equivocados (TST Súmula 439: IPCA-E ou TR), base de cálculo errada. Para cada erro, indique o valor correto.',
                'fields': [
                    {'name': 'erros_identificados', 'label': 'Erros de Cálculo Identificados (discriminados)', 'type': 'textarea', 'required': True},
                    {'name': 'valor_correto_proposto', 'label': 'Valor Correto Proposto (R$)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos da impugnação',
                'instructions': 'Pedidos: conhecimento da impugnação, reforma da conta de liquidação nos pontos impugnados, realização de nova conta pelo perito ou pelo contador do juízo.',
                'fields': [
                    {'name': 'pedido_nova_conta', 'label': 'Pede nova conta?', 'type': 'select', 'required': True, 'options': ['Sim - nova perícia contábil', 'Sim - nova conta pelo contador do juízo', 'Não - apenas correção pontual']},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'dissidio_coletivo',
        'name': 'Dissídio Coletivo - CLT arts. 856-875',
        'description': 'Ação coletiva para criação ou revisão de normas trabalhistas via Justiça do Trabalho',
        'version': '1.0',
        'legal_basis': 'CLT, arts. 856-875; CF/88, art. 114 §2º',
        'primary_color': '#0D9488',
        'secondary_color': '#14B8A6',
        'cover_title': 'Dissídio Coletivo',
        'sections': [
            {
                'number': 1, 'key': 'legitimidade_negociacao',
                'name': 'Legitimidade e Prévia Negociação',
                'description': 'Sindicato suscitante e comprovação de tentativa de negociação',
                'instructions': 'Identifique o sindicato suscitante (representante da categoria) e o suscitado (sindicato patronal ou empresa). Comprove a tentativa de negociação coletiva prévia (CF art. 114 §2º: negociação prévia OBRIGATÓRIA). Informe o tipo de dissídio.',
                'fields': [
                    {'name': 'sindicato_suscitante', 'label': 'Sindicato Suscitante (categoria profissional)', 'type': 'text', 'required': True},
                    {'name': 'suscitado', 'label': 'Suscitado (sindicato patronal ou empresa)', 'type': 'text', 'required': True},
                    {'name': 'tipo_dissidio', 'label': 'Tipo de Dissídio', 'type': 'select', 'required': True, 'options': ['Econômico (criação de novas condições de trabalho)', 'Jurídico (interpretação de norma coletiva existente)', 'De revisão (modificação de sentença normativa vigente)']},
                    {'name': 'negociacao_previa', 'label': 'Comprovação de Negociação Prévia Frustrada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'cláusulas_pleiteadas',
                'name': 'I - Das Cláusulas Pleiteadas',
                'description': 'Condições de trabalho que se pretende normatizar',
                'instructions': 'Liste as cláusulas pleiteadas: reajuste salarial (índice, percentual), benefícios (vale-refeição, VT, PLR), jornada, saúde e segurança, etc. Fundamente cada cláusula no CF art. 7º e CLT.',
                'fields': [
                    {'name': 'cláusulas_economicas', 'label': 'Cláusulas Econômicas (salário, benefícios)', 'type': 'textarea', 'required': True},
                    {'name': 'clausulas_sociais', 'label': 'Cláusulas Sociais (jornada, saúde, segurança)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos do dissídio coletivo',
                'instructions': 'Pedidos: instauração do dissídio, homologação das cláusulas pleiteadas, prolação de sentença normativa com vigência de 1 ano (CLT art. 868), aplicação às empresas da categoria.',
                'fields': [
                    {'name': 'base_territorial', 'label': 'Base Territorial (municípios/estados abrangidos)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_cumprimento_trabalhista',
        'name': 'Ação de Cumprimento - CLT art. 872',
        'description': 'Ação para cumprimento de cláusula de acordo/convenção coletiva ou sentença normativa descumprida',
        'version': '1.0',
        'legal_basis': 'CLT, art. 872; CF/88, art. 7º XXVI',
        'primary_color': '#0D9488',
        'secondary_color': '#14B8A6',
        'cover_title': 'Ação de Cumprimento',
        'sections': [
            {
                'number': 1, 'key': 'norma_descumprida',
                'name': 'Identificação da Norma Descumprida',
                'description': 'Cláusula coletiva ou sentença normativa violada',
                'instructions': 'Identifique a norma coletiva descumprida: ACT, CCT ou sentença normativa. Informe: partes do acordo, data de registro no MTE, vigência, cláusula específica violada.',
                'fields': [
                    {'name': 'tipo_norma', 'label': 'Tipo de Norma Coletiva', 'type': 'select', 'required': True, 'options': ['Acordo Coletivo de Trabalho (ACT)', 'Convenção Coletiva de Trabalho (CCT)', 'Sentença Normativa']},
                    {'name': 'clausula_violada', 'label': 'Cláusula Específica Violada', 'type': 'textarea', 'required': True},
                    {'name': 'vigencia_norma', 'label': 'Período de Vigência da Norma', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'descumprimento_danos',
                'name': 'I - Do Descumprimento e dos Valores Devidos',
                'description': 'Como a empresa descumpriu e valores não pagos',
                'instructions': 'Demonstre o descumprimento: período, trabalhadores afetados, como a cláusula deixou de ser cumprida. Calcule os valores devidos por trabalhador (diferenças salariais, benefícios não pagos, etc.).',
                'fields': [
                    {'name': 'periodo_descumprimento', 'label': 'Período do Descumprimento', 'type': 'text', 'required': True},
                    {'name': 'descricao_violacao', 'label': 'Descrição da Violação e Valores Devidos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Cumprimento e indenização',
                'instructions': 'Pedidos: condenação da empresa ao cumprimento da cláusula violada, pagamento de diferenças devidas com juros e correção (TST Súmula 439), multa por descumprimento (CLT art. 872 parágrafo único).',
                'fields': [
                    {'name': 'valor_total_pleiteado', 'label': 'Valor Total Pleiteado (R$)', 'type': 'text', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints trabalhistas complementares: RO, impugnação, dissídio, cumprimento'

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
        self.stdout.write(self.style.SUCCESS('✓ Trabalhista Complemento concluído!'))

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
            {'key': 'gerador_trabalhista', 'name': 'Verus.AI - Gerador Trabalhista', 'description': 'Gera seções de peças trabalhistas', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_TRABALHISTA, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_trabalhista')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint, section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
