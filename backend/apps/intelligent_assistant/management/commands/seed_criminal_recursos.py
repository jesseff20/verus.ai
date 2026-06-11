"""
Seed Criminal - Recursos e Liberdade — Verus.AI.
Apelação criminal, RSE, liberdade provisória.

Uso:
    python manage.py seed_criminal_recursos
    python manage.py seed_criminal_recursos --force
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
        'code': 'apelacao_criminal',
        'name': 'Apelação Criminal',
        'short_name': 'Apelação Criminal',
        'description': 'Recurso criminal contra sentença condenatória ou absolutória imprópria',
        'category': 'criminal',
        'icon': 'TrendingUp',
        'color': '#DC2626',
        'legal_basis': 'CPP, arts. 593-601; CF/88, art. 5º, LV',
        'display_order': 3,
    },
    {
        'code': 'recurso_sentido_estrito',
        'name': 'Recurso em Sentido Estrito',
        'short_name': 'RSE',
        'description': 'Recurso contra decisão interlocutória penal nas hipóteses do CPP art. 581',
        'category': 'criminal',
        'icon': 'TrendingUp',
        'color': '#DC2626',
        'legal_basis': 'CPP, arts. 581-592',
        'display_order': 4,
    },
    {
        'code': 'liberdade_provisoria',
        'name': 'Pedido de Liberdade Provisória / Medida Cautelar Alternativa',
        'short_name': 'Liberdade Provisória',
        'description': 'Pedido de liberdade provisória ou substituição de prisão preventiva por medidas cautelares',
        'category': 'criminal',
        'icon': 'Unlock',
        'color': '#DC2626',
        'legal_basis': 'CPP, arts. 282-319; CF/88, art. 5º, LVII, LXVI; Lei 12.403/2011',
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
"""

PROMPT_GERADOR_CRIMINAL = CONST_ANTI_ALUCINACAO + """Você é advogado criminalista especialista em processo penal brasileiro.

LEGISLAÇÃO VIGENTE:
- CP (DL 2.848/1940); CPP (DL 3.689/1941); CF/88, art. 5º
- Lei 12.403/2011 (medidas cautelares); Lei 7.210/1984 (LEP)

REGRAS ESSENCIAIS:
1. Princípios: in dubio pro reo, presunção de inocência (CF art. 5º LVII), ampla defesa
2. Apelação criminal: CPP art. 593. Prazo: 5 dias (art. 593 §1º)
3. RSE: CPP art. 581 (rol taxativo). Prazo: 5 dias (art. 586)
4. Prisão preventiva: CPP art. 312 (garantia da ordem pública, instrução, aplicação da lei penal)
5. Liberdade provisória: CPP art. 310; medidas cautelares art. 319 (alternativas à prisão)
6. Vedação: CPP art. 313 (limites para decretação da preventiva)
7. Presunção de inocência: prisão antes do trânsito só em casos excepcionais (STF HC 126.292)
8. Súmulas STJ/STF: STF Súmulas 9, 21, 83, 231, 347, 415, 691, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703
9. Acórdãos: [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'apelacao_criminal': 'gerador_criminal',
    'recurso_sentido_estrito': 'gerador_criminal',
    'liberdade_provisoria': 'gerador_criminal',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'apelacao_criminal',
        'name': 'Apelação Criminal - CPP art. 593',
        'description': 'Recurso criminal contra sentença condenatória, absolutória ou de pronúncia',
        'version': '1.0',
        'legal_basis': 'CPP, arts. 593-601',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Apelação Criminal',
        'sections': [
            {
                'number': 1, 'key': 'cabecalho_admissibilidade',
                'name': 'Cabeçalho e Pressupostos de Admissibilidade',
                'description': 'Identificação do recurso e tempestividade',
                'instructions': 'Identifique o apelante, apelado (MP ou acusação), processo de origem. Demonstre tempestividade (CPP art. 593 §1º: 5 dias da intimação). Identifique o fundamento: CPP art. 593 I (erro de fato/direito) ou III (quesitos no júri).',
                'fields': [
                    {'name': 'apelante_nome', 'label': 'Nome do Apelante (réu/MP)', 'type': 'text', 'required': True},
                    {'name': 'processo_origem', 'label': 'Número do Processo de Origem', 'type': 'text', 'required': True},
                    {'name': 'tipo_sentenca', 'label': 'Tipo de Sentença Apelada', 'type': 'select', 'required': True, 'options': ['Condenatória', 'Absolutória imprópria', 'De pronúncia (júri)', 'Que declina competência', 'Que extingue punibilidade']},
                    {'name': 'data_intimacao', 'label': 'Data da Intimação da Sentença', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'razoes_recurso',
                'name': 'I - Das Razões do Recurso',
                'description': 'Fundamentos do recurso criminal',
                'instructions': 'Desenvolva as razões: nulidades absolutas (CPP art. 564), error in procedendo, error in judicando, incorreta valoração das provas, dosimetria da pena (CP arts. 59-68), inaplicabilidade de qualificadoras ou agravantes. Use princípios: presunção de inocência, in dubio pro reo, proporcionalidade.',
                'fields': [
                    {'name': 'tipo_error', 'label': 'Principal Tipo de Erro Arguido', 'type': 'select', 'required': True, 'options': ['Nulidade processual (error in procedendo)', 'Erro na valoração das provas (error in judicando)', 'Dosimetria equivocada da pena', 'Absolvição (ausência de dolo/autoria/materialidade)', 'Desclassificação do crime']},
                    {'name': 'razoes_detalhadas', 'label': 'Razões Detalhadas do Recurso', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos da apelação criminal',
                'instructions': 'Pedidos: conhecimento e provimento do recurso, absolvição ou desclassificação, redução da pena se mantida condenação, aplicação de regime mais brando, substituição por pena restritiva de direitos se cabível (CP art. 44).',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'select', 'required': True, 'options': ['Absolvição plena', 'Desclassificação do crime', 'Redução da pena', 'Regime mais brando', 'Substituição por pena restritiva de direitos', 'Anulação do processo']},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'recurso_sentido_estrito',
        'name': 'Recurso em Sentido Estrito - CPP art. 581',
        'description': 'RSE contra decisão interlocutória penal nas hipóteses taxativas do CPP art. 581',
        'version': '1.0',
        'legal_basis': 'CPP, arts. 581-592',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Recurso em Sentido Estrito',
        'sections': [
            {
                'number': 1, 'key': 'cabimento',
                'name': 'Cabimento e Tempestividade',
                'description': 'Hipótese do CPP art. 581 e prazo',
                'instructions': 'Identifique a hipótese do CPP art. 581 que autoriza o RSE. Demonstre tempestividade (CPP art. 586: 5 dias). Qualifique recorrente e recorrido.',
                'fields': [
                    {'name': 'recorrente_nome', 'label': 'Nome do Recorrente', 'type': 'text', 'required': True},
                    {'name': 'hipotese_art581', 'label': 'Hipótese do CPP art. 581', 'type': 'select', 'required': True, 'options': ['I - não receber denúncia/queixa', 'II - julgar procedente exceção', 'III - conceder/negar habeas corpus', 'IV - pronunciar/impronunciar', 'V - conceder/negar liberdade provisória', 'VI - absolver sumariamente', 'Outra hipótese (especificar)']},
                    {'name': 'data_decisao', 'label': 'Data da Decisão Recorrida', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'razoes_pedidos',
                'name': 'I - Das Razões e Dos Pedidos',
                'description': 'Fundamentos e pedido de reforma',
                'instructions': 'Desenvolva as razões: por que a decisão está equivocada (fundamentos fáticos e jurídicos). Pedidos: conhecimento do recurso, reforma da decisão conforme pedido específico.',
                'fields': [
                    {'name': 'razoes', 'label': 'Razões do Recurso', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_especifico', 'label': 'Pedido Específico de Reforma', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'liberdade_provisoria',
        'name': 'Pedido de Liberdade Provisória / Medida Cautelar - CPP art. 319',
        'description': 'Pedido de liberdade provisória ou substituição de prisão preventiva por medidas cautelares alternativas',
        'version': '1.0',
        'legal_basis': 'CPP, arts. 282-319; CF/88, art. 5º, LVII, LXVI; Lei 12.403/2011',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Pedido de Liberdade Provisória',
        'sections': [
            {
                'number': 1, 'key': 'identificacao_preso',
                'name': 'Identificação do Preso e da Prisão',
                'description': 'Dados do acusado e fundamento da prisão',
                'instructions': 'Identifique o paciente/réu (preso). Informe: processo, crime imputado, data da prisão, fundamento da preventiva (CPP art. 312: ordem pública, instrução, aplicação da lei penal). Demonstre que o preso está em prisão preventiva sem sentença condenatória transitada em julgado.',
                'fields': [
                    {'name': 'preso_nome', 'label': 'Nome do Preso (Paciente/Réu)', 'type': 'text', 'required': True},
                    {'name': 'processo_numero', 'label': 'Número do Processo', 'type': 'text', 'required': True},
                    {'name': 'crime_imputado', 'label': 'Crime Imputado', 'type': 'text', 'required': True},
                    {'name': 'data_prisao', 'label': 'Data da Prisão', 'type': 'text', 'required': True},
                    {'name': 'fundamento_prisao', 'label': 'Fundamento da Prisão (CPP art. 312)', 'type': 'select', 'required': True, 'options': ['Garantia da ordem pública', 'Garantia da ordem econômica', 'Conveniência da instrução criminal', 'Assegurar aplicação da lei penal', 'Prisão em flagrante']},
                ],
            },
            {
                'number': 2, 'key': 'fundamentacao_liberdade',
                'name': 'I - Da Ausência dos Requisitos da Preventiva',
                'description': 'Demonstração de que não estão presentes os requisitos da prisão',
                'instructions': 'Demonstre que não estão presentes os requisitos do CPP art. 312. Apresente: bons antecedentes, residência fixa, ocupação lícita, família constituída, ausência de periculosidade. Cite o princípio da presunção de inocência (CF art. 5º LVII) e proporcionalidade. Proponha medidas cautelares alternativas (CPP art. 319).',
                'fields': [
                    {'name': 'ausencia_requisitos', 'label': 'Por que não estão presentes os requisitos da preventiva', 'type': 'textarea', 'required': True},
                    {'name': 'condicoes_pessoais', 'label': 'Condições Pessoais Favoráveis (residência, trabalho, família)', 'type': 'textarea', 'required': True},
                    {'name': 'medida_alternativa_proposta', 'label': 'Medida Cautelar Alternativa Proposta (CPP art. 319)', 'type': 'select', 'required': True, 'options': ['Comparecimento periódico em juízo', 'Proibição de ausentar-se da comarca', 'Fiança (CPP art. 319 VIII)', 'Monitoração eletrônica', 'Recolhimento domiciliar noturno', 'Proibição de contato com vítima']},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Liberdade provisória ou medida cautelar alternativa',
                'instructions': 'Pedidos: revogação da prisão preventiva (CPP art. 316), concessão de liberdade provisória mediante medida cautelar alternativa (CPP art. 319), ou, subsidiariamente, liberdade com fiança. Urgência justificada pelo cárcere.',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'select', 'required': True, 'options': ['Revogação da preventiva e liberdade sem cautelar', 'Substituição por medida cautelar (art. 319)', 'Liberdade provisória com fiança', 'Prisão domiciliar (art. 317)']},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints criminais: apelação, RSE, liberdade provisória'

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
        self.stdout.write(self.style.SUCCESS('✓ Criminal Recursos concluído!'))

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
            {'key': 'gerador_criminal', 'name': 'Verus.AI - Gerador Criminal', 'description': 'Gera seções de peças criminais', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_CRIMINAL, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_criminal')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint, section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
