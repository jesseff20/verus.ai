"""
Seed Militar, Internacional, Empresarial (complemento) e Previdenciário/Tributário (complemento) — Verus.AI.

Uso:
    python manage.py seed_militar_internacional_empresarial
    python manage.py seed_militar_internacional_empresarial --force
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
        'code': 'militar',
        'name': 'Militar',
        'description': 'Peças jurídicas de Direito Militar e Justiça Militar',
        'display_order': 20,
    },
    {
        'code': 'internacional',
        'name': 'Internacional',
        'description': 'Peças e procedimentos de Direito Internacional Privado e cooperação jurídica internacional',
        'display_order': 21,
    },
]

TIPOS_DOCUMENTO = [
    # ── Militar ──
    {
        'code': 'habeas_corpus_militar',
        'name': 'Habeas Corpus Militar',
        'short_name': 'HC Militar',
        'description': 'Habeas corpus impetrado perante a Justiça Militar da União ou dos Estados',
        'category': 'militar',
        'icon': 'Shield',
        'color': '#4A5568',
        'legal_basis': 'CF/88, art. 5º LXVIII; CPPM, arts. 466-480; Lei 8.457/1992',
        'display_order': 1,
    },
    {
        'code': 'conselho_disciplina_militar',
        'name': 'Defesa em Conselho de Disciplina',
        'short_name': 'Def. Cons. Disciplina',
        'description': 'Defesa escrita em procedimento de Conselho de Disciplina militar',
        'category': 'militar',
        'icon': 'FileText',
        'color': '#4A5568',
        'legal_basis': 'Decreto 71.500/1972; Lei 6.880/1980 (Estatuto dos Militares); CF/88, art. 5º LV',
        'display_order': 2,
    },
    # ── Internacional ──
    {
        'code': 'carta_rogatoria',
        'name': 'Carta Rogatória',
        'short_name': 'Carta Rog.',
        'description': 'Carta rogatória para diligências no exterior ou proveniente de jurisdição estrangeira',
        'category': 'internacional',
        'icon': 'Globe',
        'color': '#2B6CB0',
        'legal_basis': 'CPC/2015, arts. 36-41; LINDB, arts. 12-17; Resolução STJ 09/2005',
        'display_order': 1,
    },
    {
        'code': 'homologacao_sentenca_estrangeira',
        'name': 'Homologação de Sentença Estrangeira',
        'short_name': 'Homol. Sent. Estrang.',
        'description': 'Pedido de homologação de sentença estrangeira perante o STJ',
        'category': 'internacional',
        'icon': 'CheckCircle',
        'color': '#2B6CB0',
        'legal_basis': 'CF/88, art. 105 I-i; CPC/2015, arts. 960-965; LINDB, art. 15; Resolução STJ 09/2005',
        'display_order': 2,
    },
    {
        'code': 'exequatur',
        'name': 'Exequatur',
        'short_name': 'Exequatur',
        'description': 'Concessão de exequatur para cumprimento de carta rogatória estrangeira',
        'category': 'internacional',
        'icon': 'Scale',
        'color': '#2B6CB0',
        'legal_basis': 'CF/88, art. 105 I-i; CPC/2015, art. 36; Resolução STJ 09/2005',
        'display_order': 3,
    },
    # ── Empresarial (complemento) ──
    {
        'code': 'recuperacao_judicial',
        'name': 'Recuperação Judicial',
        'short_name': 'Recup. Judicial',
        'description': 'Pedido de recuperação judicial de empresa em crise econômico-financeira',
        'category': 'empresarial',
        'icon': 'TrendingUp',
        'color': '#D97706',
        'legal_basis': 'Lei 11.101/2005, arts. 47-72; Lei 14.112/2020; CF/88, art. 170',
        'display_order': 10,
    },
    {
        'code': 'falencia',
        'name': 'Pedido de Falência',
        'short_name': 'Falência',
        'description': 'Pedido de falência do devedor empresário',
        'category': 'empresarial',
        'icon': 'AlertTriangle',
        'color': '#D97706',
        'legal_basis': 'Lei 11.101/2005, arts. 94-99; Lei 14.112/2020',
        'display_order': 11,
    },
    {
        'code': 'habilitacao_credito_falencia',
        'name': 'Habilitação de Crédito',
        'short_name': 'Habil. Crédito',
        'description': 'Habilitação de crédito em processo de falência ou recuperação judicial',
        'category': 'empresarial',
        'icon': 'DollarSign',
        'color': '#D97706',
        'legal_basis': 'Lei 11.101/2005, arts. 7-20; Lei 14.112/2020',
        'display_order': 12,
    },
    {
        'code': 'contrato_social',
        'name': 'Contrato Social',
        'short_name': 'Contrato Social',
        'description': 'Elaboração de contrato social de sociedade limitada',
        'category': 'empresarial',
        'icon': 'Users',
        'color': '#D97706',
        'legal_basis': 'CC/2002, arts. 1.052-1.087; IN DREI 81/2020; Lei 8.934/1994',
        'display_order': 13,
    },
    {
        'code': 'acordo_socios',
        'name': 'Acordo de Sócios',
        'short_name': 'Acordo Sócios',
        'description': 'Acordo de sócios ou acionistas para governança societária',
        'category': 'empresarial',
        'icon': 'Handshake',
        'color': '#D97706',
        'legal_basis': 'CC/2002, arts. 997, 1.053; Lei 6.404/1976, art. 118',
        'display_order': 14,
    },
    {
        'code': 'nda_confidencialidade',
        'name': 'Acordo de Confidencialidade (NDA)',
        'short_name': 'NDA',
        'description': 'Acordo de não divulgação e confidencialidade empresarial',
        'category': 'empresarial',
        'icon': 'Lock',
        'color': '#D97706',
        'legal_basis': 'CC/2002, arts. 186, 927; Lei 9.279/1996, art. 195 XI; LGPD, Lei 13.709/2018',
        'display_order': 15,
    },
    # ── Previdenciário (complemento) ──
    {
        'code': 'auxilio_doenca_judicial',
        'name': 'Auxílio por Incapacidade Temporária',
        'short_name': 'Aux. Incapacidade',
        'description': 'Ação judicial para concessão de auxílio por incapacidade temporária (antigo auxílio-doença)',
        'category': 'previdenciario',
        'icon': 'Heart',
        'color': '#7C3AED',
        'legal_basis': 'Lei 8.213/1991, art. 59; EC 103/2019; Decreto 3.048/1999',
        'display_order': 10,
    },
    {
        'code': 'pensao_morte',
        'name': 'Pensão por Morte',
        'short_name': 'Pensão Morte',
        'description': 'Ação judicial para concessão de pensão por morte de segurado',
        'category': 'previdenciario',
        'icon': 'Users',
        'color': '#7C3AED',
        'legal_basis': 'Lei 8.213/1991, arts. 74-79; EC 103/2019, art. 23; Decreto 3.048/1999',
        'display_order': 11,
    },
    # ── Tributário (complemento) ──
    {
        'code': 'acao_declaratoria_tributaria',
        'name': 'Ação Declaratória Tributária',
        'short_name': 'Decl. Tributária',
        'description': 'Ação declaratória de inexistência de relação jurídico-tributária',
        'category': 'tributario',
        'icon': 'FileText',
        'color': '#059669',
        'legal_basis': 'CPC/2015, art. 19; CTN, arts. 113-118; CF/88, arts. 150-152',
        'display_order': 10,
    },
    {
        'code': 'acao_consignatoria_tributaria',
        'name': 'Ação de Consignação em Pagamento Tributária',
        'short_name': 'Consig. Tributária',
        'description': 'Ação consignatória para depósito judicial de tributo em caso de recusa ou dúvida',
        'category': 'tributario',
        'icon': 'DollarSign',
        'color': '#059669',
        'legal_basis': 'CTN, art. 164; CPC/2015, arts. 539-549; CF/88, art. 150',
        'display_order': 11,
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
- Conteúdo inferido: [SUGESTÃO DA IA - VERIFICAR COM ADVOGADO]
- Todo documento DEVE terminar com: "⚠️ AVISO: Esta minuta foi gerada por IA e requer revisão obrigatória por advogado habilitado perante a OAB."
"""

PROMPT_GERADOR_MILITAR = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Militar brasileiro.

LEGISLAÇÃO VIGENTE:
- CF/88, arts. 122-126 (Justiça Militar da União), arts. 125 §§4-5 (Justiça Militar Estadual)
- Código Penal Militar (Decreto-Lei 1.001/1969); CPPM (Decreto-Lei 1.002/1969)
- Lei 6.880/1980 (Estatuto dos Militares); Lei 8.457/1992 (organização da JMU)
- Decreto 71.500/1972 (Conselho de Disciplina); Decreto 76.322/1975 (Regulamento Disciplinar)

REGRAS ESSENCIAIS:
1. Habeas corpus militar: CPPM arts. 466-480; competência STM (CF art. 124) ou TJM estadual (CF art. 125 §5)
2. Conselho de Disciplina: Decreto 71.500/1972 — praças com mais de 8 anos de serviço; contraditório obrigatório
3. Crime militar próprio vs impróprio: CPM arts. 9 e 10; competência ratione materiae
4. Garantias constitucionais: CF art. 5º LIV (devido processo), LV (ampla defesa), LXVIII (habeas corpus)
5. Prescrição penal militar: CPM arts. 125-132
6. Súmulas STM e STF pertinentes; acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]
7. Cerceamento de defesa e nulidades: CPPM arts. 498-503

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_INTERNACIONAL = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Internacional Privado brasileiro e cooperação jurídica internacional.

LEGISLAÇÃO VIGENTE:
- CF/88, art. 105 I-i (competência STJ para homologação e exequatur)
- LINDB (Decreto-Lei 4.657/1942), arts. 7-19
- CPC/2015, arts. 21-41 (competência internacional), arts. 960-965 (homologação)
- Resolução STJ 09/2005 (carta rogatória e homologação de sentença estrangeira)
- Convenção de Haia sobre Citação (Decreto 11.240/2022); Convenção Interamericana (Decreto 2.022/1996)

REGRAS ESSENCIAIS:
1. Homologação de sentença estrangeira: competência exclusiva do STJ (CF art. 105 I-i); requisitos LINDB art. 15 e CPC arts. 960-965
2. Carta rogatória: CPC arts. 36-41; exequatur concedido pelo STJ (Resolução 09/2005)
3. Requisitos formais: tradução juramentada, autenticação consular ou apostilamento (Convenção de Haia - Apostila)
4. Ordem pública: limite intransponível (LINDB art. 17; CPC art. 963 VI)
5. Competência concorrente vs exclusiva: CPC arts. 21-23 (concorrente) e art. 23 (exclusiva)
6. Tratados e convenções bilaterais: verificar existência entre Brasil e país de origem
7. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_EMPRESARIAL = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Empresarial brasileiro, com ênfase em recuperação judicial, falências e direito societário.

LEGISLAÇÃO VIGENTE:
- Lei 11.101/2005 (Lei de Recuperação e Falências); Lei 14.112/2020 (reforma)
- CC/2002, Livro II (Direito de Empresa), arts. 966-1.195
- Lei 6.404/1976 (Lei das S/A); Lei 8.934/1994 (Registro Público de Empresas Mercantis)
- IN DREI 81/2020 (Instrução Normativa do Departamento de Registro Empresarial)
- Lei 9.279/1996 (Propriedade Industrial); LGPD (Lei 13.709/2018)

REGRAS ESSENCIAIS:
1. Recuperação judicial: legitimidade (art. 48 Lei 11.101); documentação obrigatória (art. 51); stay period 180 dias (art. 6º §4)
2. Falência: hipóteses (art. 94 Lei 11.101 — impontualidade, execução frustrada, atos de falência)
3. Habilitação de crédito: prazo de 15 dias da publicação do edital (art. 7º §1); classes de credores (art. 83)
4. Contrato social: cláusulas obrigatórias (CC art. 997); registro na Junta Comercial (Lei 8.934/1994)
5. Acordo de sócios: cláusulas de tag-along, drag-along, non-compete; Lei 6.404/1976 art. 118
6. NDA: obrigações de sigilo, exceções legais, prazo de vigência, penalidades
7. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_PREVIDENCIARIO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Previdenciário brasileiro.

LEGISLAÇÃO VIGENTE:
- CF/88, arts. 201-204; Lei 8.213/1991; Decreto 3.048/1999; Lei 8.212/1991
- EC 103/2019 (Reforma da Previdência); LC 142/2013 (aposentadoria do deficiente)

REGRAS ESSENCIAIS:
1. Auxílio por incapacidade temporária (antigo auxílio-doença): Lei 8.213/1991, art. 59; carência 12 contribuições (art. 25 I); dispensa de carência em acidente (art. 26 II)
2. Pensão por morte: Lei 8.213/1991, arts. 74-79; EC 103/2019 art. 23 (cota familiar); dependentes art. 16
3. Qualidade de segurado: Lei 8.213/1991, art. 11; período de graça: art. 15
4. Prazos: requerimento de pensão por morte até 180 dias do óbito para retroagir à data do óbito (art. 74 §1)
5. Súmulas STJ e TNU pertinentes; acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_TRIBUTARIO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Tributário brasileiro.

LEGISLAÇÃO VIGENTE:
- CF/88, arts. 145-162 (Sistema Tributário Nacional)
- CTN (Lei 5.172/1966); CPC/2015
- Lei 6.830/1980 (Execução Fiscal)

REGRAS ESSENCIAIS:
1. Ação declaratória: CPC art. 19 I; objeto: inexistência de relação jurídico-tributária ou direito a isenção/imunidade
2. Consignação em pagamento tributária: CTN art. 164 — hipóteses taxativas (recusa de recebimento, subordinação a exigência indevida, exigência por mais de uma pessoa jurídica)
3. Princípios constitucionais: legalidade (art. 150 I), anterioridade (art. 150 III), capacidade contributiva (art. 145 §1)
4. Prescrição e decadência tributária: CTN arts. 150 §4, 173, 174
5. Súmulas STF e STJ em matéria tributária; acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'habeas_corpus_militar': 'gerador_militar',
    'conselho_disciplina_militar': 'gerador_militar',
    'carta_rogatoria': 'gerador_internacional',
    'homologacao_sentenca_estrangeira': 'gerador_internacional',
    'exequatur': 'gerador_internacional',
    'recuperacao_judicial': 'gerador_empresarial',
    'falencia': 'gerador_empresarial',
    'habilitacao_credito_falencia': 'gerador_empresarial',
    'contrato_social': 'gerador_empresarial',
    'acordo_socios': 'gerador_empresarial',
    'nda_confidencialidade': 'gerador_empresarial',
    'auxilio_doenca_judicial': 'gerador_previdenciario',
    'pensao_morte': 'gerador_previdenciario',
    'acao_declaratoria_tributaria': 'gerador_tributario',
    'acao_consignatoria_tributaria': 'gerador_tributario',
}

BLUEPRINTS_DATA = [
    # ══════════════════════════════════════════════════════════════════════
    # MILITAR
    # ══════════════════════════════════════════════════════════════════════
    {
        'doc_type_code': 'habeas_corpus_militar',
        'name': 'Habeas Corpus Militar - CPPM',
        'description': 'Habeas corpus impetrado perante a Justiça Militar contra ato coator ilegal ou abusivo',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 5º LXVIII; CPPM, arts. 466-480; Lei 8.457/1992',
        'primary_color': '#4A5568',
        'secondary_color': '#718096',
        'cover_title': 'Habeas Corpus Militar',
        'secondary_area_codes': ['criminal'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo ou tribunal competente para julgamento do habeas corpus militar',
                'instructions': 'Endereçe ao Superior Tribunal Militar, Tribunal de Justiça Militar estadual ou Auditoria Militar competente, conforme a autoridade coatora. Identifique a competência com base na CF/88, arts. 122-126 e Lei 8.457/1992. Mencione o nome e posto/graduação do impetrante.',
                'fields': [
                    {'name': 'tribunal_competente', 'label': 'Tribunal/Juízo Competente', 'type': 'select', 'required': True, 'options': ['Superior Tribunal Militar', 'Tribunal de Justiça Militar Estadual', 'Auditoria da Justiça Militar']},
                    {'name': 'impetrante_nome', 'label': 'Nome do Impetrante (advogado)', 'type': 'text', 'required': True},
                    {'name': 'impetrante_oab', 'label': 'OAB do Impetrante', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao_paciente',
                'name': 'Qualificação do Paciente',
                'description': 'Dados completos do paciente (militar beneficiado pelo habeas corpus)',
                'instructions': 'Qualifique o paciente com dados pessoais completos: nome, posto/graduação, unidade militar, número funcional, CPF e endereço. Indique se está preso ou em liberdade e, se preso, o local de custódia.',
                'fields': [
                    {'name': 'paciente_nome', 'label': 'Nome Completo do Paciente', 'type': 'text', 'required': True},
                    {'name': 'paciente_posto', 'label': 'Posto/Graduação', 'type': 'text', 'required': True},
                    {'name': 'paciente_unidade', 'label': 'Unidade Militar', 'type': 'text', 'required': True},
                    {'name': 'paciente_situacao', 'label': 'Situação do Paciente', 'type': 'select', 'required': True, 'options': ['Preso', 'Em liberdade com ameaça de prisão', 'Respondendo a procedimento disciplinar']},
                ],
            },
            {
                'number': 3, 'key': 'ato_coator',
                'name': 'Do Ato Coator',
                'description': 'Descrição do ato de autoridade que configura a coação ilegal',
                'instructions': 'Descreva detalhadamente o ato coator: qual autoridade o praticou (nome, posto e função), em que data, qual a natureza do ato (prisão disciplinar, procedimento criminal, punição regulamentar). Identifique o número do procedimento ou boletim, se existente.',
                'fields': [
                    {'name': 'autoridade_coatora', 'label': 'Autoridade Coatora (nome, posto, função)', 'type': 'text', 'required': True},
                    {'name': 'descricao_ato', 'label': 'Descrição do Ato Coator', 'type': 'textarea', 'required': True},
                    {'name': 'data_ato', 'label': 'Data do Ato Coator', 'type': 'text', 'required': True},
                    {'name': 'numero_procedimento', 'label': 'Número do Procedimento/Boletim (se houver)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'ilegalidade',
                'name': 'Da Ilegalidade ou Abuso de Poder',
                'description': 'Demonstração da ilegalidade ou abuso de poder no ato coator',
                'instructions': 'Demonstre a ilegalidade ou abuso de poder: ausência de justa causa, excesso de prazo, incompetência da autoridade, violação do devido processo legal, desrespeito ao contraditório (CF art. 5º LV), ausência de fundamentação. Diferencie punição disciplinar de crime militar, se pertinente.',
                'fields': [
                    {'name': 'fundamento_ilegalidade', 'label': 'Fundamento da Ilegalidade/Abuso', 'type': 'textarea', 'required': True},
                    {'name': 'tipo_ilegalidade', 'label': 'Tipo de Ilegalidade', 'type': 'select', 'required': True, 'options': ['Ausência de justa causa', 'Excesso de prazo', 'Incompetência da autoridade', 'Violação do devido processo legal', 'Cerceamento de defesa', 'Punição desproporcional', 'Outro']},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'Da Fundamentação Jurídica',
                'description': 'Embasamento legal e jurisprudencial do pedido',
                'instructions': 'Fundamente juridicamente: CF/88 art. 5º LXVIII (habeas corpus), CPPM arts. 466-480 (procedimento), art. 5º LIV e LV (devido processo e ampla defesa). Cite precedentes do STM e STF sobre habeas corpus militar. Diferencie transgressão disciplinar (não cabe HC — CF art. 142 §2) de punição com vício de legalidade (cabe HC para análise de legalidade).',
                'fields': [
                    {'name': 'dispositivos_legais', 'label': 'Dispositivos Legais Aplicáveis', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de concessão da ordem de habeas corpus',
                'instructions': 'Formule os pedidos: concessão da ordem de habeas corpus para cessar a coação ilegal, expedição de alvará de soltura (se preso), concessão de liminar (se urgente), notificação da autoridade coatora para prestar informações, sustação do ato coator.',
                'fields': [
                    {'name': 'pedido_liminar', 'label': 'Pedido de Liminar?', 'type': 'select', 'required': True, 'options': ['Sim (risco iminente à liberdade)', 'Não']},
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'conselho_disciplina_militar',
        'name': 'Defesa em Conselho de Disciplina - Decreto 71.500/1972',
        'description': 'Defesa escrita de militar submetido a Conselho de Disciplina',
        'version': '1.0',
        'legal_basis': 'Decreto 71.500/1972; Lei 6.880/1980; CF/88, art. 5º LV',
        'primary_color': '#4A5568',
        'secondary_color': '#718096',
        'cover_title': 'Defesa em Conselho de Disciplina',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao presidente do Conselho de Disciplina',
                'instructions': 'Endereçe ao Presidente do Conselho de Disciplina, identificando a portaria de instauração (número, data e autoridade que determinou), a unidade militar sede do Conselho e os membros nomeados.',
                'fields': [
                    {'name': 'portaria_instauracao', 'label': 'Portaria de Instauração (nº e data)', 'type': 'text', 'required': True},
                    {'name': 'unidade_sede', 'label': 'Unidade Militar Sede do Conselho', 'type': 'text', 'required': True},
                    {'name': 'presidente_conselho', 'label': 'Nome e Posto do Presidente do Conselho', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação do Acusado',
                'description': 'Dados do militar submetido ao Conselho de Disciplina',
                'instructions': 'Qualifique o militar acusado: nome completo, posto/graduação, quadro/arma, tempo de serviço, comportamento militar (excepcional, bom, insuficiente ou mau), unidade de origem, número funcional. Informe se possui defensor constituído ou dativo.',
                'fields': [
                    {'name': 'acusado_nome', 'label': 'Nome Completo do Acusado', 'type': 'text', 'required': True},
                    {'name': 'acusado_posto', 'label': 'Posto/Graduação', 'type': 'text', 'required': True},
                    {'name': 'tempo_servico', 'label': 'Tempo de Serviço', 'type': 'text', 'required': True},
                    {'name': 'comportamento_militar', 'label': 'Comportamento Militar', 'type': 'select', 'required': True, 'options': ['Excepcional', 'Bom', 'Insuficiente', 'Mau']},
                ],
            },
            {
                'number': 3, 'key': 'fatos_imputados',
                'name': 'Dos Fatos Imputados',
                'description': 'Descrição dos fatos que motivaram a instauração do Conselho',
                'instructions': 'Descreva os fatos imputados ao militar conforme constam da portaria de instauração e do libelo acusatório. Identifique as transgressões disciplinares tipificadas, o enquadramento no regulamento disciplinar e as circunstâncias de tempo e lugar.',
                'fields': [
                    {'name': 'fatos_descricao', 'label': 'Descrição dos Fatos Imputados', 'type': 'textarea', 'required': True},
                    {'name': 'transgressoes', 'label': 'Transgressões Disciplinares Tipificadas', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'defesa',
                'name': 'Da Defesa',
                'description': 'Argumentos de defesa do militar acusado',
                'instructions': 'Apresente a defesa: conteste os fatos, apresente versão do acusado, aponte atenuantes (Lei 6.880/1980), demonstre bons antecedentes e contribuição à instituição. Argua nulidades processuais se existentes (cerceamento de defesa, vícios na instauração, inobservância do Decreto 71.500/1972). Invoque o princípio da proporcionalidade.',
                'fields': [
                    {'name': 'argumentos_defesa', 'label': 'Argumentos de Defesa', 'type': 'textarea', 'required': True},
                    {'name': 'nulidades', 'label': 'Nulidades Processuais (se houver)', 'type': 'textarea', 'required': False},
                    {'name': 'atenuantes', 'label': 'Circunstâncias Atenuantes', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'provas',
                'name': 'Das Provas',
                'description': 'Provas produzidas e requerimento de diligências',
                'instructions': 'Indique as provas produzidas em favor do acusado: depoimentos de testemunhas, documentos, elogios e condecorações recebidas, folha de alterações, histórico funcional. Requeira diligências complementares se necessário (oitiva de testemunhas, juntada de documentos).',
                'fields': [
                    {'name': 'provas_produzidas', 'label': 'Provas Produzidas (documentos, testemunhas)', 'type': 'textarea', 'required': True},
                    {'name': 'diligencias_requeridas', 'label': 'Diligências Requeridas', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos finais ao Conselho de Disciplina',
                'instructions': 'Formule os pedidos: absolvição das imputações e declaração de que o acusado é digno de permanecer na instituição (Decreto 71.500/1972, art. 13 c); subsidiariamente, reconhecimento de atenuantes para aplicação de sanção mais branda. Requeira a apreciação de todas as provas produzidas.',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # INTERNACIONAL
    # ══════════════════════════════════════════════════════════════════════
    {
        'doc_type_code': 'carta_rogatoria',
        'name': 'Carta Rogatória - CPC/2015',
        'description': 'Carta rogatória para realização de diligências em cooperação jurídica internacional',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 36-41; LINDB, arts. 12-17; Resolução STJ 09/2005',
        'primary_color': '#2B6CB0',
        'secondary_color': '#3182CE',
        'cover_title': 'Carta Rogatória',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo rogante e do juízo rogado',
                'instructions': 'Identifique o juízo rogante (brasileiro) com vara, comarca e estado, ou o tribunal estrangeiro que expede a rogatória. Identifique o juízo rogado (autoridade do país destinatário). Mencione o processo de origem (número, partes, objeto).',
                'fields': [
                    {'name': 'juizo_rogante', 'label': 'Juízo Rogante (origem)', 'type': 'text', 'required': True},
                    {'name': 'pais_destino', 'label': 'País Destinatário', 'type': 'text', 'required': True},
                    {'name': 'processo_origem', 'label': 'Processo de Origem (número e partes)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'partes',
                'name': 'Das Partes',
                'description': 'Qualificação das partes envolvidas na diligência',
                'instructions': 'Qualifique as partes do processo de origem e as pessoas a serem atingidas pela diligência no exterior: nome completo, nacionalidade, endereço no país destinatário, documentos de identificação disponíveis.',
                'fields': [
                    {'name': 'parte_requerente', 'label': 'Parte Requerente', 'type': 'text', 'required': True},
                    {'name': 'parte_requerida', 'label': 'Parte Requerida / Destinatário da Diligência', 'type': 'text', 'required': True},
                    {'name': 'endereco_exterior', 'label': 'Endereço no País Destinatário', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'diligencia_solicitada',
                'name': 'Da Diligência Solicitada',
                'description': 'Descrição precisa da diligência a ser cumprida no exterior',
                'instructions': 'Descreva detalhadamente a diligência solicitada: citação, intimação, coleta de provas, oitiva de testemunhas, obtenção de documentos, penhora de bens. Especifique os atos a serem praticados, os documentos a serem entregues e os prazos aplicáveis.',
                'fields': [
                    {'name': 'tipo_diligencia', 'label': 'Tipo de Diligência', 'type': 'select', 'required': True, 'options': ['Citação', 'Intimação', 'Coleta de Provas', 'Oitiva de Testemunhas', 'Obtenção de Documentos', 'Penhora/Bloqueio de Bens', 'Outra']},
                    {'name': 'descricao_diligencia', 'label': 'Descrição Detalhada da Diligência', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'Da Fundamentação',
                'description': 'Fundamentação legal para a cooperação jurídica internacional',
                'instructions': 'Fundamente no CPC/2015 arts. 36-41, LINDB arts. 12-17, Resolução STJ 09/2005. Verifique existência de tratado bilateral ou multilateral entre o Brasil e o país destinatário (Convenção de Haia, Protocolo de Las Leñas — MERCOSUL, etc.). Mencione o princípio da reciprocidade se não houver tratado.',
                'fields': [
                    {'name': 'tratado_aplicavel', 'label': 'Tratado ou Convenção Aplicável (se houver)', 'type': 'text', 'required': False},
                    {'name': 'fundamentacao_legal', 'label': 'Fundamentação Legal', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de cumprimento da carta rogatória',
                'instructions': 'Formule os pedidos: cumprimento da diligência solicitada pela autoridade rogada, tradução juramentada dos documentos remetidos, devolução da carta após cumprimento com a certidão de diligência. Informe se há urgência na realização do ato.',
                'fields': [
                    {'name': 'urgencia', 'label': 'Há urgência no cumprimento?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'homologacao_sentenca_estrangeira',
        'name': 'Homologação de Sentença Estrangeira - CPC/2015',
        'description': 'Pedido de homologação de sentença estrangeira perante o Superior Tribunal de Justiça',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 105 I-i; CPC/2015, arts. 960-965; LINDB, art. 15',
        'primary_color': '#2B6CB0',
        'secondary_color': '#3182CE',
        'cover_title': 'Homologação de Sentença Estrangeira',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao STJ para homologação',
                'instructions': 'Endereçe ao Presidente do Superior Tribunal de Justiça, competente para homologação de sentença estrangeira (CF/88, art. 105 I-i). Identifique o requerente e seus dados de contato.',
                'fields': [
                    {'name': 'requerente_nome', 'label': 'Nome do Requerente', 'type': 'text', 'required': True},
                    {'name': 'advogado_nome', 'label': 'Advogado (nome e OAB)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'sentenca_estrangeira',
                'name': 'Da Sentença Estrangeira',
                'description': 'Dados da sentença estrangeira a ser homologada',
                'instructions': 'Descreva a sentença estrangeira: tribunal que a proferiu, país de origem, data, número do processo, objeto da decisão (divórcio, alimentos, obrigações comerciais, etc.). Informe se a sentença transitou em julgado no país de origem.',
                'fields': [
                    {'name': 'tribunal_origem', 'label': 'Tribunal que Proferiu a Sentença', 'type': 'text', 'required': True},
                    {'name': 'pais_origem', 'label': 'País de Origem', 'type': 'text', 'required': True},
                    {'name': 'data_sentenca', 'label': 'Data da Sentença', 'type': 'text', 'required': True},
                    {'name': 'objeto_sentenca', 'label': 'Objeto da Sentença (divórcio, alimentos, etc.)', 'type': 'text', 'required': True},
                    {'name': 'transito_julgado', 'label': 'Transitou em Julgado?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                ],
            },
            {
                'number': 3, 'key': 'requisitos_legais',
                'name': 'Dos Requisitos Legais',
                'description': 'Demonstração do preenchimento dos requisitos para homologação',
                'instructions': 'Demonstre o preenchimento dos requisitos do CPC art. 963 e LINDB art. 15: (i) proferida por autoridade competente; (ii) citação regular do réu ou configuração da revelia legal; (iii) trânsito em julgado; (iv) autenticação consular ou apostilamento (Convenção de Haia); (v) tradução juramentada; (vi) não ofensa à soberania, ordem pública ou bons costumes (LINDB art. 17).',
                'fields': [
                    {'name': 'citacao_regular', 'label': 'Houve Citação Regular do Réu?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (revelia legal configurada)', 'Réu revel por edital']},
                    {'name': 'apostilamento', 'label': 'Documentos Apostilados/Autenticados?', 'type': 'select', 'required': True, 'options': ['Sim — Apostila de Haia', 'Sim — Autenticação Consular', 'Pendente']},
                    {'name': 'traducao', 'label': 'Tradução Juramentada Providenciada?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (será providenciada)']},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'Da Fundamentação',
                'description': 'Fundamentação jurídica para homologação',
                'instructions': 'Fundamente na CF/88 art. 105 I-i, CPC/2015 arts. 960-965, LINDB arts. 15-17, Resolução STJ 09/2005. Demonstre que a sentença não ofende a ordem pública brasileira. Cite precedentes do STJ em homologação de sentenças estrangeiras similares.',
                'fields': [
                    {'name': 'fundamentacao', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de homologação da sentença estrangeira',
                'instructions': 'Formule os pedidos: homologação da sentença estrangeira para que produza efeitos no território brasileiro, citação da parte contrária (CPC art. 961 §1), expedição de carta de sentença após homologação para execução perante o juízo federal competente (CPC art. 965).',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido de Homologação', 'type': 'textarea', 'required': True},
                    {'name': 'execucao_pretendida', 'label': 'Local Pretendido para Execução', 'type': 'text', 'required': False},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'exequatur',
        'name': 'Exequatur - Resolução STJ 09/2005',
        'description': 'Pedido de concessão de exequatur para cumprimento de carta rogatória estrangeira no Brasil',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 105 I-i; CPC/2015, art. 36; Resolução STJ 09/2005',
        'primary_color': '#2B6CB0',
        'secondary_color': '#3182CE',
        'cover_title': 'Exequatur',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao STJ para concessão de exequatur',
                'instructions': 'Endereçe ao Presidente do Superior Tribunal de Justiça, competente para concessão de exequatur (CF/88, art. 105 I-i). Identifique a via de tramitação (Ministério da Justiça, autoridade central, via diplomática).',
                'fields': [
                    {'name': 'via_tramitacao', 'label': 'Via de Tramitação', 'type': 'select', 'required': True, 'options': ['Autoridade Central (Ministério da Justiça)', 'Via Diplomática', 'Direta (tratado específico)']},
                    {'name': 'pais_rogante', 'label': 'País Rogante', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'carta_rogatoria',
                'name': 'Da Carta Rogatória',
                'description': 'Dados da carta rogatória estrangeira cujo cumprimento é solicitado',
                'instructions': 'Descreva a carta rogatória: tribunal estrangeiro expedidor, número do processo no exterior, objeto da diligência solicitada (citação, intimação, coleta de provas, etc.), partes envolvidas. Informe se acompanhada de tradução e documentos apostilados.',
                'fields': [
                    {'name': 'tribunal_expedidor', 'label': 'Tribunal Estrangeiro Expedidor', 'type': 'text', 'required': True},
                    {'name': 'objeto_diligencia', 'label': 'Objeto da Diligência Solicitada', 'type': 'textarea', 'required': True},
                    {'name': 'partes_envolvidas', 'label': 'Partes Envolvidas', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'requisitos',
                'name': 'Dos Requisitos para Concessão',
                'description': 'Demonstração do preenchimento dos requisitos para exequatur',
                'instructions': 'Demonstre os requisitos da Resolução STJ 09/2005: (i) autenticidade da carta rogatória; (ii) competência do juízo rogante; (iii) tradução por tradutor juramentado; (iv) não ofensa à soberania e ordem pública (LINDB art. 17); (v) inexistência de competência exclusiva brasileira sobre a matéria (CPC art. 23).',
                'fields': [
                    {'name': 'autenticidade', 'label': 'Autenticidade Verificada (apostilamento/autenticação)?', 'type': 'select', 'required': True, 'options': ['Sim', 'Pendente']},
                    {'name': 'ofensa_ordem_publica', 'label': 'Há risco de ofensa à ordem pública?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (detalhar)']},
                ],
            },
            {
                'number': 4, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedido de concessão de exequatur',
                'instructions': 'Formule o pedido de concessão de exequatur pelo STJ, com remessa ao juízo federal competente para cumprimento (CPC art. 36 §1). Indique o local de cumprimento da diligência no Brasil.',
                'fields': [
                    {'name': 'local_cumprimento', 'label': 'Local de Cumprimento no Brasil (cidade/estado)', 'type': 'text', 'required': True},
                    {'name': 'pedido_principal', 'label': 'Pedido de Concessão de Exequatur', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # EMPRESARIAL (COMPLEMENTO)
    # ══════════════════════════════════════════════════════════════════════
    {
        'doc_type_code': 'recuperacao_judicial',
        'name': 'Recuperação Judicial - Lei 11.101/2005',
        'description': 'Pedido de recuperação judicial para empresa em crise econômico-financeira',
        'version': '1.0',
        'legal_basis': 'Lei 11.101/2005, arts. 47-72; Lei 14.112/2020; CF/88, art. 170',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Recuperação Judicial',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo competente para a recuperação judicial',
                'instructions': 'Endereçe à Vara de Falências e Recuperações Judiciais da comarca do principal estabelecimento do devedor (Lei 11.101/2005, art. 3º). Identifique a comarca e justifique a competência.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca / Vara de Falências', 'type': 'text', 'required': True},
                    {'name': 'principal_estabelecimento', 'label': 'Principal Estabelecimento do Devedor', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao_empresa',
                'name': 'Qualificação da Empresa Devedora',
                'description': 'Dados societários completos da empresa requerente',
                'instructions': 'Qualifique a empresa: razão social, CNPJ, inscrição estadual/municipal, endereço da sede, ramo de atividade, data de constituição, sócios/administradores. Comprove o exercício regular de atividade econômica há mais de 2 anos (art. 48). Demonstre que não se enquadra nas exclusões do art. 2º.',
                'fields': [
                    {'name': 'razao_social', 'label': 'Razão Social', 'type': 'text', 'required': True},
                    {'name': 'cnpj', 'label': 'CNPJ', 'type': 'text', 'required': True},
                    {'name': 'ramo_atividade', 'label': 'Ramo de Atividade', 'type': 'text', 'required': True},
                    {'name': 'data_constituicao', 'label': 'Data de Constituição', 'type': 'text', 'required': True},
                    {'name': 'socios', 'label': 'Sócios/Administradores', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'crise_economica',
                'name': 'Da Crise Econômico-Financeira',
                'description': 'Descrição da situação de crise que justifica a recuperação',
                'instructions': 'Descreva a crise econômico-financeira: causas (retração de mercado, perda de contratos, pandemia, etc.), impacto no fluxo de caixa, dificuldade de honrar obrigações. Demonstre a viabilidade econômica da empresa (função social — art. 47). Apresente breve diagnóstico financeiro.',
                'fields': [
                    {'name': 'causas_crise', 'label': 'Causas da Crise Econômico-Financeira', 'type': 'textarea', 'required': True},
                    {'name': 'passivo_total', 'label': 'Passivo Total Aproximado', 'type': 'text', 'required': True},
                    {'name': 'num_empregados', 'label': 'Número de Empregados', 'type': 'text', 'required': False},
                    {'name': 'viabilidade', 'label': 'Elementos de Viabilidade Econômica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'plano_recuperacao',
                'name': 'Do Plano de Recuperação',
                'description': 'Diretrizes do plano de recuperação judicial',
                'instructions': 'Apresente as diretrizes do plano de recuperação (art. 50): meios de recuperação pretendidos (concessão de prazos, cisão/fusão, alienação de ativos, trespasse, redução salarial temporária, etc.). O plano completo será apresentado em 60 dias (art. 53). Indique os meios propostos conforme art. 50.',
                'fields': [
                    {'name': 'meios_recuperacao', 'label': 'Meios de Recuperação Pretendidos (art. 50)', 'type': 'textarea', 'required': True},
                    {'name': 'prazo_plano', 'label': 'Prazo para Apresentação do Plano', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'documentacao',
                'name': 'Da Documentação',
                'description': 'Documentos obrigatórios para instrução do pedido',
                'instructions': 'Liste a documentação obrigatória do art. 51 da Lei 11.101/2005: (I) exposição das causas da crise; (II) demonstrações contábeis dos últimos 3 exercícios; (III) relação nominal dos credores; (IV) relação dos empregados; (V) certidão de regularidade no Registro Público; (VI) relação dos bens dos sócios controladores; (VII) extratos das contas bancárias; (VIII) certidões dos cartórios de protesto; (IX) relação das ações judiciais em curso.',
                'fields': [
                    {'name': 'documentos_anexados', 'label': 'Documentos Anexados (listar)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de deferimento do processamento da recuperação judicial',
                'instructions': 'Formule os pedidos: deferimento do processamento da recuperação judicial (art. 52), nomeação de administrador judicial, suspensão das ações e execuções contra o devedor (stay period — art. 6º §4), dispensa de certidões negativas para exercício da atividade, publicação de edital.',
                'fields': [
                    {'name': 'pedido_stay', 'label': 'Pedido de Suspensão das Ações (stay period)?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'pedido_principal', 'label': 'Pedido Principal', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'falencia',
        'name': 'Pedido de Falência - Lei 11.101/2005',
        'description': 'Pedido de decretação de falência do devedor empresário',
        'version': '1.0',
        'legal_basis': 'Lei 11.101/2005, arts. 94-99; Lei 14.112/2020',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Pedido de Falência',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo competente para o pedido de falência',
                'instructions': 'Endereçe à Vara de Falências e Recuperações Judiciais da comarca do principal estabelecimento do devedor (Lei 11.101/2005, art. 3º).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca / Vara de Falências', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Qualificação do credor requerente e do devedor',
                'instructions': 'Qualifique o credor requerente (nome/razão social, CNPJ/CPF, endereço) e o devedor empresário (razão social, CNPJ, principal estabelecimento). Demonstre a legitimidade ativa do credor (art. 97).',
                'fields': [
                    {'name': 'credor_nome', 'label': 'Nome/Razão Social do Credor Requerente', 'type': 'text', 'required': True},
                    {'name': 'credor_cnpj_cpf', 'label': 'CNPJ/CPF do Credor', 'type': 'text', 'required': True},
                    {'name': 'devedor_razao_social', 'label': 'Razão Social do Devedor', 'type': 'text', 'required': True},
                    {'name': 'devedor_cnpj', 'label': 'CNPJ do Devedor', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'devedor',
                'name': 'Do Devedor e da Dívida',
                'description': 'Descrição da relação creditícia e do inadimplemento',
                'instructions': 'Descreva a origem do crédito, valor atualizado, data de vencimento e tentativas de cobrança. Junte comprovação documental (título executivo, contrato, notas fiscais, duplicatas protestadas).',
                'fields': [
                    {'name': 'origem_credito', 'label': 'Origem do Crédito', 'type': 'textarea', 'required': True},
                    {'name': 'valor_credito', 'label': 'Valor Atualizado do Crédito', 'type': 'text', 'required': True},
                    {'name': 'data_vencimento', 'label': 'Data de Vencimento', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'hipotese_legal',
                'name': 'Da Hipótese Legal de Falência',
                'description': 'Enquadramento na hipótese legal que autoriza a falência',
                'instructions': 'Enquadre na hipótese do art. 94 da Lei 11.101/2005: (I) impontualidade injustificada de obrigação líquida (40 salários mínimos); (II) execução frustrada — sem bens suficientes; (III) prática de atos de falência (liquidação precipitada, negócio simulado, etc.). Fundamente em uma das três hipóteses legais.',
                'fields': [
                    {'name': 'hipotese', 'label': 'Hipótese Legal (art. 94)', 'type': 'select', 'required': True, 'options': ['I - Impontualidade injustificada (≥ 40 SM)', 'II - Execução frustrada', 'III - Prática de atos de falência']},
                    {'name': 'fundamentacao_hipotese', 'label': 'Fundamentação da Hipótese', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'Da Fundamentação Jurídica',
                'description': 'Embasamento legal e jurisprudencial',
                'instructions': 'Fundamente na Lei 11.101/2005, arts. 94-99. Cite requisitos formais do pedido (art. 94 §§). Mencione precedentes do TJSP e STJ sobre pedidos de falência. Aborde a possibilidade de depósito elisivo pelo devedor (art. 98).',
                'fields': [
                    {'name': 'fundamentacao', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de decretação de falência',
                'instructions': 'Formule os pedidos: citação do devedor para contestar ou depositar o valor (art. 98), decretação da falência, nomeação de administrador judicial, arrecadação de bens, publicação de edital para habilitação de créditos.',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido de Decretação de Falência', 'type': 'textarea', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'habilitacao_credito_falencia',
        'name': 'Habilitação de Crédito - Lei 11.101/2005',
        'description': 'Habilitação de crédito em processo de falência ou recuperação judicial',
        'version': '1.0',
        'legal_basis': 'Lei 11.101/2005, arts. 7-20; Lei 14.112/2020',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Habilitação de Crédito',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo da falência ou recuperação judicial',
                'instructions': 'Endereçe ao Juízo da Vara de Falências onde tramita o processo. Identifique o número do processo de falência ou recuperação judicial, o nome do devedor e do administrador judicial.',
                'fields': [
                    {'name': 'processo_falencia', 'label': 'Número do Processo de Falência/Recuperação', 'type': 'text', 'required': True},
                    {'name': 'devedor_nome', 'label': 'Nome/Razão Social do Devedor', 'type': 'text', 'required': True},
                    {'name': 'administrador_judicial', 'label': 'Administrador Judicial', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao_credor',
                'name': 'Qualificação do Credor',
                'description': 'Dados completos do credor habilitante',
                'instructions': 'Qualifique o credor: nome/razão social, CNPJ/CPF, endereço completo, representante legal. Informe se o crédito já consta na relação publicada pelo administrador judicial ou se é divergência/retificação.',
                'fields': [
                    {'name': 'credor_nome', 'label': 'Nome/Razão Social do Credor', 'type': 'text', 'required': True},
                    {'name': 'credor_cnpj_cpf', 'label': 'CNPJ/CPF do Credor', 'type': 'text', 'required': True},
                    {'name': 'situacao_credito', 'label': 'Situação do Crédito', 'type': 'select', 'required': True, 'options': ['Crédito não incluído na relação', 'Crédito incluído com valor divergente', 'Crédito incluído em classe incorreta']},
                ],
            },
            {
                'number': 3, 'key': 'credito',
                'name': 'Do Crédito',
                'description': 'Descrição e comprovação do crédito habilitado',
                'instructions': 'Descreva o crédito: origem (contrato, sentença judicial, título executivo, relação trabalhista), valor original, encargos, valor atualizado. Junte documentação comprobatória.',
                'fields': [
                    {'name': 'origem_credito', 'label': 'Origem do Crédito', 'type': 'textarea', 'required': True},
                    {'name': 'valor_original', 'label': 'Valor Original do Crédito', 'type': 'text', 'required': True},
                    {'name': 'valor_atualizado', 'label': 'Valor Atualizado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'classificacao',
                'name': 'Da Classificação do Crédito',
                'description': 'Enquadramento na ordem de preferência legal',
                'instructions': 'Classifique o crédito conforme art. 83 da Lei 11.101/2005: (I) trabalhista (até 150 SM) e acidente de trabalho; (II) com garantia real (até valor do bem); (III) tributário; (IV) com privilégio especial; (V) com privilégio geral; (VI) quirografário; (VII) multas; (VIII) subordinado. Justifique a classificação pleiteada.',
                'fields': [
                    {'name': 'classe_credito', 'label': 'Classe do Crédito (art. 83)', 'type': 'select', 'required': True, 'options': ['I - Trabalhista / Acidente de Trabalho', 'II - Com Garantia Real', 'III - Tributário', 'IV - Com Privilégio Especial', 'V - Com Privilégio Geral', 'VI - Quirografário', 'VII - Multas', 'VIII - Subordinado']},
                    {'name': 'justificativa_classe', 'label': 'Justificativa da Classificação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'documentacao',
                'name': 'Da Documentação',
                'description': 'Documentos comprobatórios do crédito',
                'instructions': 'Liste os documentos que comprovam o crédito: contratos, notas fiscais, duplicatas, sentenças judiciais, certidões de crédito tributário, holerites, CTPS. Mencione que todos os documentos seguem em cópia anexa.',
                'fields': [
                    {'name': 'documentos', 'label': 'Documentos Comprobatórios Anexados', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de habilitação do crédito',
                'instructions': 'Formule os pedidos: habilitação do crédito no valor de R$ [valor] na classe [classe] do quadro geral de credores; intimação do administrador judicial para manifestação; inclusão no edital de credores.',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido de Habilitação', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'contrato_social',
        'name': 'Contrato Social - CC/2002',
        'description': 'Elaboração de contrato social de sociedade limitada conforme Código Civil',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.052-1.087; IN DREI 81/2020; Lei 8.934/1994',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Contrato Social',
        'secondary_area_codes': ['extrajudicial'],
        'sections': [
            {
                'number': 1, 'key': 'identificacao_socios',
                'name': 'Identificação dos Sócios',
                'description': 'Qualificação completa de todos os sócios',
                'instructions': 'Qualifique cada sócio: nome completo, nacionalidade, estado civil (regime de bens se casado), profissão, CPF, RG, endereço completo. Para pessoa jurídica sócia: razão social, CNPJ, endereço da sede, representante legal. Conforme CC art. 997 I e IN DREI 81/2020.',
                'fields': [
                    {'name': 'socios', 'label': 'Dados dos Sócios (qualificação completa de cada um)', 'type': 'textarea', 'required': True},
                    {'name': 'num_socios', 'label': 'Número Total de Sócios', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'objeto_social',
                'name': 'Do Objeto Social',
                'description': 'Definição das atividades econômicas da sociedade',
                'instructions': 'Defina o objeto social de forma clara e precisa, indicando as atividades econômicas (CNAE) que a sociedade exercerá. O objeto deve ser lícito, possível e determinado (CC art. 997 II). Evite objeto social genérico ou excessivamente amplo.',
                'fields': [
                    {'name': 'objeto_social', 'label': 'Descrição do Objeto Social', 'type': 'textarea', 'required': True},
                    {'name': 'cnae_principal', 'label': 'CNAE Principal', 'type': 'text', 'required': True},
                    {'name': 'cnae_secundarios', 'label': 'CNAEs Secundários (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'capital_social',
                'name': 'Do Capital Social',
                'description': 'Valor do capital social e forma de integralização',
                'instructions': 'Defina o capital social: valor total em moeda corrente nacional, forma de integralização (dinheiro, bens, créditos — CC art. 997 III e IV), prazo para integralização. Em caso de bens, descreva-os e indique valor atribuído. Mencione responsabilidade solidária dos sócios pela integralização (CC art. 1.052).',
                'fields': [
                    {'name': 'capital_social_valor', 'label': 'Valor do Capital Social (R$)', 'type': 'text', 'required': True},
                    {'name': 'forma_integralizacao', 'label': 'Forma de Integralização', 'type': 'select', 'required': True, 'options': ['Em moeda corrente', 'Em bens móveis', 'Em bens imóveis', 'Mista (dinheiro e bens)']},
                    {'name': 'prazo_integralizacao', 'label': 'Prazo para Integralização', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'quotas',
                'name': 'Das Quotas Sociais',
                'description': 'Distribuição das quotas entre os sócios',
                'instructions': 'Distribua as quotas entre os sócios: quantidade de quotas de cada sócio, valor nominal unitário, percentual de participação. Defina regras para cessão de quotas (CC arts. 1.057-1.058): direito de preferência dos demais sócios, necessidade de aprovação por 3/4 do capital para cessão a terceiros.',
                'fields': [
                    {'name': 'distribuicao_quotas', 'label': 'Distribuição de Quotas (sócio, quantidade, percentual)', 'type': 'textarea', 'required': True},
                    {'name': 'valor_unitario_quota', 'label': 'Valor Unitário da Quota (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'administracao',
                'name': 'Da Administração',
                'description': 'Regras de administração e representação da sociedade',
                'instructions': 'Defina a administração: quem são os administradores (sócios ou terceiros — CC art. 1.061), poderes e limitações, forma de representação (isolada ou conjunta), pro labore, mandato (prazo determinado ou indeterminado). Estabeleça atos que dependem de deliberação dos sócios (CC art. 1.071).',
                'fields': [
                    {'name': 'administradores', 'label': 'Administrador(es) Designado(s)', 'type': 'textarea', 'required': True},
                    {'name': 'forma_representacao', 'label': 'Forma de Representação', 'type': 'select', 'required': True, 'options': ['Isoladamente por qualquer administrador', 'Conjuntamente por dois administradores', 'Isoladamente até limite de valor, conjuntamente acima']},
                    {'name': 'pro_labore', 'label': 'Pro Labore (valor ou critério)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'clausulas_gerais',
                'name': 'Cláusulas Gerais',
                'description': 'Demais cláusulas do contrato social',
                'instructions': 'Inclua as cláusulas complementares: sede e foro (CC art. 997 II), prazo de duração (determinado ou indeterminado), exercício social e distribuição de lucros, deliberações societárias (quorum — CC art. 1.076), dissolução e liquidação, regência supletiva pela Lei 6.404/1976 (CC art. 1.053 parágrafo único) se aplicável.',
                'fields': [
                    {'name': 'prazo_sociedade', 'label': 'Prazo de Duração da Sociedade', 'type': 'select', 'required': True, 'options': ['Prazo indeterminado', 'Prazo determinado']},
                    {'name': 'endereco_sede', 'label': 'Endereço da Sede', 'type': 'textarea', 'required': True},
                    {'name': 'regencia_supletiva', 'label': 'Regência Supletiva pela Lei 6.404/1976?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (CC/2002 apenas)']},
                    {'name': 'foro', 'label': 'Foro para Dirimir Controvérsias', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acordo_socios',
        'name': 'Acordo de Sócios - CC/2002 e Lei 6.404/1976',
        'description': 'Acordo de sócios ou acionistas para governança e proteção societária',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 997, 1.053; Lei 6.404/1976, art. 118',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Acordo de Sócios',
        'secondary_area_codes': ['extrajudicial'],
        'sections': [
            {
                'number': 1, 'key': 'partes',
                'name': 'Das Partes',
                'description': 'Qualificação dos sócios signatários do acordo',
                'instructions': 'Qualifique cada sócio signatário do acordo: nome, CPF, endereço, participação societária atual (percentual e quantidade de quotas/ações). Identifique a sociedade objeto do acordo (razão social, CNPJ).',
                'fields': [
                    {'name': 'socios_signatarios', 'label': 'Sócios Signatários (qualificação e participação)', 'type': 'textarea', 'required': True},
                    {'name': 'sociedade', 'label': 'Razão Social e CNPJ da Sociedade', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'objeto',
                'name': 'Do Objeto',
                'description': 'Objeto e finalidade do acordo de sócios',
                'instructions': 'Defina o objeto do acordo: regular o exercício de direitos societários, estabelecer regras de governança, disciplinar transferência de participações, proteger investimentos. Fundamente na autonomia privada (CC art. 421) e, para S/A, no art. 118 da Lei 6.404/1976.',
                'fields': [
                    {'name': 'objeto_acordo', 'label': 'Objeto e Finalidade do Acordo', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'direitos_voto',
                'name': 'Dos Direitos de Voto',
                'description': 'Regras de exercício do direito de voto e deliberações',
                'instructions': 'Estabeleça regras para exercício do voto: matérias que exigem unanimidade, matérias com quorum qualificado, direito de veto (veto rights) em decisões estratégicas (alteração do objeto social, emissão de novas quotas, endividamento acima de limites, contratação de partes relacionadas). Defina mecanismos de resolução de impasses (deadlock).',
                'fields': [
                    {'name': 'regras_voto', 'label': 'Regras de Exercício do Voto', 'type': 'textarea', 'required': True},
                    {'name': 'materias_veto', 'label': 'Matérias Sujeitas a Veto', 'type': 'textarea', 'required': False},
                    {'name': 'mecanismo_deadlock', 'label': 'Mecanismo de Resolução de Impasse (deadlock)', 'type': 'select', 'required': True, 'options': ['Mediação seguida de arbitragem', 'Russian roulette (oferta recíproca)', 'Shotgun clause', 'Dissolução parcial', 'Outro']},
                ],
            },
            {
                'number': 4, 'key': 'tag_drag',
                'name': 'Tag-Along e Drag-Along',
                'description': 'Cláusulas de proteção na transferência de participações',
                'instructions': 'Estabeleça cláusulas de tag-along (direito do minoritário de vender junto com o majoritário, nas mesmas condições) e drag-along (direito do majoritário de obrigar o minoritário a vender junto). Defina gatilhos de ativação, prazos de exercício e condições de preço. Inclua direito de preferência (right of first refusal) e lock-up period.',
                'fields': [
                    {'name': 'tag_along', 'label': 'Cláusula de Tag-Along (condições)', 'type': 'textarea', 'required': True},
                    {'name': 'drag_along', 'label': 'Cláusula de Drag-Along (condições)', 'type': 'textarea', 'required': True},
                    {'name': 'lock_up', 'label': 'Período de Lock-Up (meses)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'nao_competicao',
                'name': 'Da Não-Competição',
                'description': 'Cláusula de não-competição e não-solicitação',
                'instructions': 'Estabeleça cláusula de não-competição (non-compete): atividades vedadas, abrangência geográfica, prazo de vigência (durante o acordo e após saída). Inclua cláusula de não-solicitação (non-solicitation) de empregados e clientes. Defina penalidades por descumprimento. Observe limites de razoabilidade conforme jurisprudência do STJ.',
                'fields': [
                    {'name': 'abrangencia_geografica', 'label': 'Abrangência Geográfica da Não-Competição', 'type': 'text', 'required': True},
                    {'name': 'prazo_nao_competicao', 'label': 'Prazo de Não-Competição (anos)', 'type': 'text', 'required': True},
                    {'name': 'penalidade', 'label': 'Penalidade por Descumprimento', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'disposicoes_gerais',
                'name': 'Disposições Gerais',
                'description': 'Cláusulas finais do acordo de sócios',
                'instructions': 'Inclua disposições finais: prazo de vigência do acordo, forma de alteração (unanimidade), confidencialidade, foro ou cláusula arbitral, arquivamento na sede social (Lei 6.404/1976 art. 118 §1 para S/A), vinculação de herdeiros e sucessores.',
                'fields': [
                    {'name': 'prazo_vigencia', 'label': 'Prazo de Vigência do Acordo', 'type': 'text', 'required': True},
                    {'name': 'clausula_arbitral', 'label': 'Cláusula Arbitral?', 'type': 'select', 'required': True, 'options': ['Sim (câmara arbitral)', 'Não (foro judicial)']},
                    {'name': 'foro_arbitragem', 'label': 'Foro ou Câmara de Arbitragem', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'nda_confidencialidade',
        'name': 'Acordo de Confidencialidade (NDA)',
        'description': 'Acordo de não divulgação e confidencialidade para proteção de informações empresariais',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 186, 927; Lei 9.279/1996, art. 195 XI; LGPD, Lei 13.709/2018',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Acordo de Confidencialidade (NDA)',
        'secondary_area_codes': ['extrajudicial'],
        'sections': [
            {
                'number': 1, 'key': 'partes',
                'name': 'Das Partes',
                'description': 'Qualificação das partes do NDA',
                'instructions': 'Qualifique as partes: parte reveladora (disclosing party) e parte receptora (receiving party), ou acordo bilateral (mutual NDA). Dados completos: nome/razão social, CNPJ/CPF, endereço, representante legal. Identifique o contexto da revelação (negociação, due diligence, parceria comercial, etc.).',
                'fields': [
                    {'name': 'parte_reveladora', 'label': 'Parte Reveladora (nome, CNPJ/CPF)', 'type': 'text', 'required': True},
                    {'name': 'parte_receptora', 'label': 'Parte Receptora (nome, CNPJ/CPF)', 'type': 'text', 'required': True},
                    {'name': 'tipo_nda', 'label': 'Tipo de NDA', 'type': 'select', 'required': True, 'options': ['Unilateral', 'Bilateral (Mútuo)']},
                    {'name': 'contexto', 'label': 'Contexto da Revelação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'definicao_informacao',
                'name': 'Definição de Informação Confidencial',
                'description': 'Delimitação do que constitui informação confidencial',
                'instructions': 'Defina de forma ampla e precisa o que constitui informação confidencial: dados técnicos, comerciais, financeiros, estratégicos, know-how, segredos industriais, listas de clientes, planos de negócios, software, dados pessoais. Inclua informações em qualquer suporte (oral, escrito, eletrônico, visual).',
                'fields': [
                    {'name': 'tipos_informacao', 'label': 'Tipos de Informação Confidencial', 'type': 'textarea', 'required': True},
                    {'name': 'marcacao', 'label': 'Exige marcação/identificação como confidencial?', 'type': 'select', 'required': True, 'options': ['Sim (toda informação deve ser marcada)', 'Não (toda informação trocada é confidencial)', 'Mista (escrita marcada; oral confirmada em 10 dias)']},
                ],
            },
            {
                'number': 3, 'key': 'obrigacoes',
                'name': 'Das Obrigações',
                'description': 'Obrigações da parte receptora quanto à informação confidencial',
                'instructions': 'Estabeleça obrigações: manter sigilo absoluto, usar apenas para a finalidade acordada, limitar acesso a funcionários com necessidade de conhecimento (need-to-know), não copiar sem autorização, adotar medidas de segurança compatíveis, notificar imediatamente qualquer violação ou divulgação não autorizada, devolver ou destruir informações ao término.',
                'fields': [
                    {'name': 'obrigacoes_detalhes', 'label': 'Obrigações Específicas', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'excecoes',
                'name': 'Das Exceções',
                'description': 'Informações excluídas da obrigação de confidencialidade',
                'instructions': 'Estabeleça as exceções à confidencialidade: (i) informação já pública sem culpa da receptora; (ii) informação já conhecida antes da revelação; (iii) informação obtida licitamente de terceiro sem restrição; (iv) informação desenvolvida independentemente; (v) divulgação exigida por lei, regulamento ou ordem judicial (com notificação prévia à reveladora).',
                'fields': [
                    {'name': 'excecoes_adicionais', 'label': 'Exceções Adicionais (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'prazo',
                'name': 'Do Prazo',
                'description': 'Prazo de vigência do acordo e da obrigação de sigilo',
                'instructions': 'Defina o prazo de vigência do NDA e o prazo de sobrevivência da obrigação de confidencialidade após o término (survival clause). Prazo típico: 2 a 5 anos de vigência, obrigação de sigilo por 2 a 5 anos após o término. Para segredos industriais, obrigação pode ser por prazo indeterminado.',
                'fields': [
                    {'name': 'prazo_vigencia', 'label': 'Prazo de Vigência do NDA', 'type': 'text', 'required': True},
                    {'name': 'prazo_sobrevivencia', 'label': 'Prazo de Sobrevivência do Sigilo após Término', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'penalidades',
                'name': 'Das Penalidades',
                'description': 'Consequências do descumprimento do NDA',
                'instructions': 'Estabeleça penalidades: multa contratual por violação (valor fixo ou percentual), indenização por perdas e danos (CC arts. 186, 927), possibilidade de tutela específica (obrigação de fazer/não fazer — CPC art. 497), responsabilidade criminal por concorrência desleal (Lei 9.279/1996, art. 195 XI). Defina foro ou cláusula arbitral.',
                'fields': [
                    {'name': 'multa_valor', 'label': 'Valor da Multa por Violação', 'type': 'text', 'required': True},
                    {'name': 'foro', 'label': 'Foro para Dirimir Controvérsias', 'type': 'text', 'required': True},
                    {'name': 'clausula_arbitral', 'label': 'Cláusula Arbitral?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # PREVIDENCIÁRIO (COMPLEMENTO)
    # ══════════════════════════════════════════════════════════════════════
    {
        'doc_type_code': 'auxilio_doenca_judicial',
        'name': 'Auxílio por Incapacidade Temporária - Lei 8.213/1991',
        'description': 'Ação judicial para concessão de auxílio por incapacidade temporária (antigo auxílio-doença)',
        'version': '1.0',
        'legal_basis': 'Lei 8.213/1991, art. 59; EC 103/2019; Decreto 3.048/1999',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Auxílio por Incapacidade Temporária',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo competente para a ação previdenciária',
                'instructions': 'Endereçe ao Juizado Especial Federal ou Vara Federal Previdenciária da Subseção Judiciária do domicílio do segurado (Lei 10.259/2001, art. 3º se valor até 60 SM). Identifique o INSS como réu.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente (JEF ou Vara Federal)', 'type': 'text', 'required': True},
                    {'name': 'subsecao', 'label': 'Subseção Judiciária', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação do Segurado',
                'description': 'Dados pessoais e previdenciários do autor',
                'instructions': 'Qualifique o segurado: nome completo, CPF, NIT/PIS/PASEP, data de nascimento, endereço, profissão. Identifique a categoria de segurado (empregado, contribuinte individual, facultativo, etc. — Lei 8.213/1991 art. 11).',
                'fields': [
                    {'name': 'segurado_nome', 'label': 'Nome Completo', 'type': 'text', 'required': True},
                    {'name': 'cpf', 'label': 'CPF', 'type': 'text', 'required': True},
                    {'name': 'nit_pis', 'label': 'NIT/PIS/PASEP', 'type': 'text', 'required': True},
                    {'name': 'categoria_segurado', 'label': 'Categoria de Segurado', 'type': 'select', 'required': True, 'options': ['Empregado', 'Contribuinte Individual', 'Facultativo', 'Trabalhador Avulso', 'Segurado Especial', 'Empregado Doméstico']},
                ],
            },
            {
                'number': 3, 'key': 'incapacidade',
                'name': 'Da Incapacidade Laboral',
                'description': 'Descrição da doença ou lesão que gera a incapacidade',
                'instructions': 'Descreva a incapacidade: doença ou lesão (CID), data de início, tratamentos realizados, limitações funcionais. Demonstre a incapacidade temporária para o trabalho habitual (Lei 8.213/1991 art. 59). Diferencie de incapacidade permanente (aposentadoria por invalidez). Mencione laudos e atestados médicos.',
                'fields': [
                    {'name': 'doenca_cid', 'label': 'Doença/Lesão (CID)', 'type': 'text', 'required': True},
                    {'name': 'data_inicio_incapacidade', 'label': 'Data de Início da Incapacidade (DII)', 'type': 'text', 'required': True},
                    {'name': 'descricao_incapacidade', 'label': 'Descrição da Incapacidade e Limitações', 'type': 'textarea', 'required': True},
                    {'name': 'tratamentos', 'label': 'Tratamentos Realizados', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'indeferimento_inss',
                'name': 'Do Indeferimento Administrativo',
                'description': 'Descrição do indeferimento pelo INSS',
                'instructions': 'Descreva o indeferimento administrativo: número do requerimento (NB), data do indeferimento, motivo alegado pelo INSS (alta precoce na perícia, não reconhecimento da incapacidade, questões de carência). Demonstre o erro da perícia administrativa ou a evolução do quadro clínico.',
                'fields': [
                    {'name': 'numero_nb', 'label': 'Número do Benefício (NB)', 'type': 'text', 'required': True},
                    {'name': 'data_indeferimento', 'label': 'Data do Indeferimento/Cessação', 'type': 'text', 'required': True},
                    {'name': 'motivo_indeferimento', 'label': 'Motivo do Indeferimento', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'provas',
                'name': 'Das Provas',
                'description': 'Provas documentais e periciais',
                'instructions': 'Liste as provas: atestados e laudos médicos, exames laboratoriais e de imagem, prontuários, CNIS (Cadastro Nacional de Informações Sociais), comprovante de requerimento administrativo. Requeira perícia médica judicial (art. 464 CPC) para comprovar a incapacidade.',
                'fields': [
                    {'name': 'provas_medicas', 'label': 'Provas Médicas Disponíveis', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_pericia', 'label': 'Requerer Perícia Médica Judicial?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (documentação suficiente)']},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de concessão do benefício',
                'instructions': 'Formule os pedidos: concessão do auxílio por incapacidade temporária (art. 59) desde a DII ou cessação indevida, tutela de urgência/antecipada (CPC art. 300) se comprovado risco de dano à subsistência, condenação do INSS em honorários, gratuidade de justiça.',
                'fields': [
                    {'name': 'dib_pleiteada', 'label': 'DIB/DCB Pleiteada', 'type': 'text', 'required': True},
                    {'name': 'tutela_urgencia', 'label': 'Pedido de Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Sim (risco à subsistência)', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'pensao_morte',
        'name': 'Pensão por Morte - Lei 8.213/1991',
        'description': 'Ação judicial para concessão de pensão por morte de segurado do RGPS',
        'version': '1.0',
        'legal_basis': 'Lei 8.213/1991, arts. 74-79; EC 103/2019, art. 23; Decreto 3.048/1999',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Pensão por Morte',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo competente',
                'instructions': 'Endereçe ao Juizado Especial Federal ou Vara Federal Previdenciária do domicílio do dependente (beneficiário). Identifique o INSS como réu.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação do Dependente',
                'description': 'Dados do dependente requerente da pensão',
                'instructions': 'Qualifique o dependente/requerente: nome, CPF, data de nascimento, grau de parentesco/relação com o falecido, endereço. Identifique a classe de dependente conforme art. 16 da Lei 8.213/1991: (I) cônjuge/companheiro e filhos; (II) pais; (III) irmãos menores de 21 anos ou inválidos.',
                'fields': [
                    {'name': 'dependente_nome', 'label': 'Nome do Dependente Requerente', 'type': 'text', 'required': True},
                    {'name': 'dependente_cpf', 'label': 'CPF do Dependente', 'type': 'text', 'required': True},
                    {'name': 'classe_dependente', 'label': 'Classe de Dependente (art. 16)', 'type': 'select', 'required': True, 'options': ['I - Cônjuge/Companheiro(a)', 'I - Filho(a) menor de 21 anos', 'I - Filho(a) inválido ou com deficiência', 'II - Pais', 'III - Irmão menor de 21 anos ou inválido']},
                    {'name': 'relacao_falecido', 'label': 'Relação com o Falecido', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'obito',
                'name': 'Do Óbito do Segurado',
                'description': 'Dados do segurado falecido e circunstâncias do óbito',
                'instructions': 'Informe dados do segurado falecido: nome, CPF, NIT/PIS, data de nascimento e de óbito. Demonstre que o falecido era segurado do RGPS na data do óbito (qualidade de segurado — art. 15). Mencione número da certidão de óbito.',
                'fields': [
                    {'name': 'falecido_nome', 'label': 'Nome do Segurado Falecido', 'type': 'text', 'required': True},
                    {'name': 'falecido_cpf', 'label': 'CPF do Falecido', 'type': 'text', 'required': True},
                    {'name': 'data_obito', 'label': 'Data do Óbito', 'type': 'text', 'required': True},
                    {'name': 'causa_mortis', 'label': 'Causa Mortis (se relevante)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'dependencia',
                'name': 'Da Dependência Econômica',
                'description': 'Comprovação da dependência econômica em relação ao falecido',
                'instructions': 'Demonstre a dependência econômica: para classe I (cônjuge, companheiro, filhos), a dependência é presumida (art. 16 §4); para classes II e III, é necessária comprovação. Comprove união estável se for companheiro(a): documentos de coabitação, conta conjunta, dependência em plano de saúde, declaração de IR, testemunhas.',
                'fields': [
                    {'name': 'tipo_dependencia', 'label': 'Dependência Presumida ou a Comprovar?', 'type': 'select', 'required': True, 'options': ['Presumida (classe I)', 'A comprovar (classes II ou III)']},
                    {'name': 'provas_dependencia', 'label': 'Provas de Dependência/União Estável', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'Da Fundamentação Jurídica',
                'description': 'Embasamento legal para concessão da pensão por morte',
                'instructions': 'Fundamente na Lei 8.213/1991 arts. 74-79 (pensão por morte), art. 16 (dependentes), art. 26 I (sem carência). Após EC 103/2019: cota familiar de 50% + 10% por dependente (art. 23). Mencione prazo de requerimento de 180 dias do óbito para DIB na data do óbito (art. 74 §1). Cite Súmulas e precedentes pertinentes.',
                'fields': [
                    {'name': 'fundamentacao', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de concessão da pensão por morte',
                'instructions': 'Formule os pedidos: concessão da pensão por morte com DIB na data do óbito (se requerido em até 180 dias) ou na data do requerimento administrativo, tutela de urgência se hipossuficiência comprovada, pagamento dos atrasados com correção monetária e juros, honorários advocatícios, gratuidade de justiça.',
                'fields': [
                    {'name': 'dib_pleiteada', 'label': 'DIB Pleiteada (data do óbito ou do requerimento)', 'type': 'text', 'required': True},
                    {'name': 'tutela_urgencia', 'label': 'Pedido de Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # TRIBUTÁRIO (COMPLEMENTO)
    # ══════════════════════════════════════════════════════════════════════
    {
        'doc_type_code': 'acao_declaratoria_tributaria',
        'name': 'Ação Declaratória Tributária - CPC/2015',
        'description': 'Ação declaratória de inexistência de relação jurídico-tributária',
        'version': '1.0',
        'legal_basis': 'CPC/2015, art. 19; CTN, arts. 113-118; CF/88, arts. 150-152',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Ação Declaratória Tributária',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo competente para a ação declaratória',
                'instructions': 'Endereçe à Vara da Fazenda Pública (tributo estadual/municipal) ou Vara Federal/JEF (tributo federal). Identifique o ente tributante como réu (União, Estado, Município ou autarquia).',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente', 'type': 'text', 'required': True},
                    {'name': 'ente_tributante', 'label': 'Ente Tributante (réu)', 'type': 'select', 'required': True, 'options': ['União Federal', 'Estado (especificar)', 'Município (especificar)', 'Autarquia Federal']},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação do Contribuinte',
                'description': 'Dados do contribuinte autor da ação',
                'instructions': 'Qualifique o contribuinte: nome/razão social, CPF/CNPJ, inscrição estadual/municipal, endereço. Identifique a atividade econômica e o tributo objeto da demanda.',
                'fields': [
                    {'name': 'contribuinte_nome', 'label': 'Nome/Razão Social do Contribuinte', 'type': 'text', 'required': True},
                    {'name': 'contribuinte_cnpj_cpf', 'label': 'CNPJ/CPF', 'type': 'text', 'required': True},
                    {'name': 'tributo_objeto', 'label': 'Tributo Objeto da Ação', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'relacao_tributaria',
                'name': 'Da Relação Jurídico-Tributária',
                'description': 'Descrição da relação tributária controvertida',
                'instructions': 'Descreva a relação jurídico-tributária: qual tributo é exigido, qual o fato gerador alegado pelo fisco, qual a base de cálculo e alíquota aplicadas. Contextualize a controvérsia: o fisco pretende cobrar tributo que o contribuinte entende indevido.',
                'fields': [
                    {'name': 'fato_gerador', 'label': 'Fato Gerador Alegado pelo Fisco', 'type': 'textarea', 'required': True},
                    {'name': 'base_calculo', 'label': 'Base de Cálculo e Alíquota Aplicadas', 'type': 'text', 'required': True},
                    {'name': 'valor_exigido', 'label': 'Valor Exigido pelo Fisco', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'inexistencia',
                'name': 'Da Inexistência da Obrigação Tributária',
                'description': 'Demonstração de que a obrigação tributária não existe ou é indevida',
                'instructions': 'Demonstre a inexistência da relação jurídico-tributária: isenção legal, imunidade constitucional (CF art. 150 VI), não ocorrência do fato gerador, inconstitucionalidade da exação, decadência do crédito tributário (CTN art. 150 §4 ou art. 173), ilegalidade da base de cálculo. Fundamente nos princípios constitucionais tributários.',
                'fields': [
                    {'name': 'fundamento_inexistencia', 'label': 'Fundamento da Inexistência da Obrigação', 'type': 'textarea', 'required': True},
                    {'name': 'tipo_fundamento', 'label': 'Tipo de Fundamento', 'type': 'select', 'required': True, 'options': ['Imunidade constitucional', 'Isenção legal', 'Não ocorrência do fato gerador', 'Inconstitucionalidade da exação', 'Decadência', 'Ilegalidade da base de cálculo', 'Outro']},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'Da Fundamentação Jurídica',
                'description': 'Embasamento legal e jurisprudencial',
                'instructions': 'Fundamente no CPC art. 19 I (interesse na declaração), CTN arts. 113-118 (obrigação tributária), CF/88 arts. 150-152 (limitações ao poder de tributar). Cite Súmulas STF e STJ pertinentes ao tributo discutido. Mencione precedentes em recursos repetitivos ou repercussão geral, se existentes.',
                'fields': [
                    {'name': 'fundamentacao', 'label': 'Fundamentação Jurídica', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos declaratórios e acessórios',
                'instructions': 'Formule os pedidos: declaração de inexistência de relação jurídico-tributária, declaração do direito de não recolher o tributo, condenação do réu em repetição de indébito (se houve pagamento — CTN art. 165), tutela de urgência para suspensão da exigibilidade (CTN art. 151), honorários.',
                'fields': [
                    {'name': 'houve_pagamento', 'label': 'Houve Pagamento Indevido a Restituir?', 'type': 'select', 'required': True, 'options': ['Sim (pedir repetição de indébito)', 'Não']},
                    {'name': 'tutela_urgencia', 'label': 'Pedido de Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Sim (suspensão da exigibilidade)', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_consignatoria_tributaria',
        'name': 'Ação de Consignação Tributária - CTN art. 164',
        'description': 'Ação consignatória para depósito judicial de tributo em caso de recusa ou dúvida',
        'version': '1.0',
        'legal_basis': 'CTN, art. 164; CPC/2015, arts. 539-549; CF/88, art. 150',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Ação de Consignação Tributária',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Indicação do juízo competente para a consignatória',
                'instructions': 'Endereçe à Vara da Fazenda Pública (tributo estadual/municipal) ou Vara Federal (tributo federal). Identifique o(s) ente(s) tributante(s) como réu(s) — se a dúvida é sobre a quem pagar, litisconsórcio passivo necessário.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente', 'type': 'text', 'required': True},
                    {'name': 'reus', 'label': 'Réu(s) — Ente(s) Tributante(s)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação do Contribuinte',
                'description': 'Dados do contribuinte consignante',
                'instructions': 'Qualifique o contribuinte: nome/razão social, CNPJ/CPF, endereço, atividade econômica. Demonstre a condição de sujeito passivo da obrigação tributária que se pretende consignar.',
                'fields': [
                    {'name': 'contribuinte_nome', 'label': 'Nome/Razão Social', 'type': 'text', 'required': True},
                    {'name': 'contribuinte_cnpj_cpf', 'label': 'CNPJ/CPF', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'tributo',
                'name': 'Do Tributo',
                'description': 'Identificação do tributo objeto da consignação',
                'instructions': 'Identifique o tributo: espécie (imposto, taxa, contribuição), fato gerador, competência (período), base de cálculo, alíquota, valor a consignar. Demonstre a boa-fé do contribuinte em querer pagar o tributo devido.',
                'fields': [
                    {'name': 'tributo_especie', 'label': 'Espécie do Tributo', 'type': 'text', 'required': True},
                    {'name': 'competencia', 'label': 'Competência/Período', 'type': 'text', 'required': True},
                    {'name': 'valor_consignar', 'label': 'Valor a Consignar (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'recusa_duvida',
                'name': 'Da Recusa ou Dúvida',
                'description': 'Descrição da situação que justifica a consignação',
                'instructions': 'Enquadre em uma das hipóteses taxativas do CTN art. 164: (I) recusa de recebimento ou subordinação ao pagamento de outro tributo/penalidade; (II) subordinação ao cumprimento de obrigação acessória; (III) exigência por mais de uma pessoa jurídica de direito público sobre mesmo fato gerador. Descreva as tentativas de pagamento frustradas e a situação de dúvida.',
                'fields': [
                    {'name': 'hipotese_consignacao', 'label': 'Hipótese de Consignação (CTN art. 164)', 'type': 'select', 'required': True, 'options': ['I - Recusa de recebimento', 'I - Subordinação a pagamento de outro tributo/penalidade', 'II - Subordinação a obrigação acessória', 'III - Exigência por mais de uma PJ de direito público']},
                    {'name': 'descricao_situacao', 'label': 'Descrição da Situação de Recusa/Dúvida', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'deposito',
                'name': 'Do Depósito Judicial',
                'description': 'Depósito do valor do tributo em juízo',
                'instructions': 'Demonstre a intenção de depositar o valor integral do tributo que entende devido (CPC art. 542). O depósito deve ser do valor que o contribuinte reconhece como correto. Mencione que o depósito tem efeito de suspensão da exigibilidade do crédito tributário (CTN art. 151 II). Indique a conta judicial para depósito.',
                'fields': [
                    {'name': 'valor_deposito', 'label': 'Valor do Depósito Judicial (R$)', 'type': 'text', 'required': True},
                    {'name': 'forma_deposito', 'label': 'Forma de Depósito', 'type': 'select', 'required': True, 'options': ['Depósito em conta judicial vinculada', 'Guia de depósito judicial']},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'Dos Pedidos',
                'description': 'Pedidos de consignação e declaração de quitação',
                'instructions': 'Formule os pedidos: autorização para depósito judicial do valor (CPC art. 542), julgamento procedente da consignação com declaração de extinção da obrigação tributária pelo pagamento (CTN art. 156 VIII), suspensão da exigibilidade do crédito tributário (CTN art. 151 II), condenação do réu em honorários.',
                'fields': [
                    {'name': 'pedido_principal', 'label': 'Pedido de Consignação', 'type': 'textarea', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Militar, Internacional, Empresarial (complemento) e Previdenciário/Tributário (complemento)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Militar, Internacional, Empresarial, Previd./Tributário'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            return

        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Militar, Internacional, Empresarial e Previd./Tributário concluído!\n'))

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
            {'key': 'gerador_militar', 'name': 'Verus.AI - Gerador Militar', 'description': 'Gera seções de peças de Direito Militar', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_MILITAR, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'gerador_internacional', 'name': 'Verus.AI - Gerador Internacional', 'description': 'Gera seções de peças de Direito Internacional Privado', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_INTERNACIONAL, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'gerador_empresarial', 'name': 'Verus.AI - Gerador Empresarial Complemento', 'description': 'Gera seções de peças empresariais, falimentares e societárias', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_EMPRESARIAL, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'gerador_previdenciario', 'name': 'Verus.AI - Gerador Previdenciário Complemento', 'description': 'Gera seções de auxílio por incapacidade e pensão por morte', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_PREVIDENCIARIO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'gerador_tributario', 'name': 'Verus.AI - Gerador Tributário Complemento', 'description': 'Gera seções de ações declaratórias e consignatórias tributárias', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_TRIBUTARIO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
        self.stdout.write('\n[4/4] Blueprints...')
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
            # Área primária (FORA do if created)
            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)
            # Áreas secundárias (FORA do if created)
            for area_code in bp_data.get('secondary_area_codes', []):
                sec_cat = cats.get(area_code)
                if sec_cat:
                    blueprint.areas.add(sec_cat)
            # Garante is_default=True em re-execução
            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {blueprint.name}')
            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_militar')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
