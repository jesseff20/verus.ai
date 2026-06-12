"""
Seed Procuradoria Municipal — Verus.AI.

Documentos específicos para procuradorias municipais: pareceres, minutas,
defesas, recursos, contratos administrativos e instrumentos de controle.

Uso:
    python manage.py seed_procuradoria_municipal
    python manage.py seed_procuradoria_municipal --force
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
        'code': 'procuradoria',
        'name': 'Procuradoria Municipal',
        'description': 'Documentos exclusivos da Procuradoria Geral do Município',
        'display_order': 1,
    },
    {
        'code': 'divida_ativa',
        'name': 'Dívida Ativa',
        'description': 'Cobrança e execução de créditos municipais inscritos em dívida ativa',
        'display_order': 2,
    },
    {
        'code': 'licitacoes',
        'name': 'Licitações e Contratos',
        'description': 'Minutas e pareceres em licitações, contratos e convênios administrativos',
        'display_order': 3,
    },
    {
        'code': 'controle_interno',
        'name': 'Controle Interno e Compliance',
        'description': 'Instrumentos de controle da legalidade e conformidade',
        'display_order': 4,
    },
]

TIPOS_DOCUMENTO = [
    # ── Procuradoria Municipal ──────────────────────────────────────────
    {
        'code': 'parecer_juridico',
        'name': 'Parecer Jurídico',
        'short_name': 'Parecer',
        'description': 'Opinião técnico-jurídica da Procuradoria sobre questão de direito',
        'category': 'procuradoria',
        'icon': 'FileText',
        'color': '#1D4ED8',
        'legal_basis': 'Lei 9.784/1999; CF/88, art. 131-132; LC Municipal',
        'display_order': 1,
    },
    {
        'code': 'nota_assessoria_juridica',
        'name': 'Nota de Assessoria Jurídica',
        'short_name': 'Nota Jurídica',
        'description': 'Nota técnica da procuradoria sobre consulta ou expediente administrativo',
        'category': 'procuradoria',
        'icon': 'ClipboardList',
        'color': '#1D4ED8',
        'legal_basis': 'Lei 9.784/1999; CF/88, art. 37; Regimento Interno da PGM',
        'display_order': 2,
    },
    {
        'code': 'defesa_improbidade',
        'name': 'Defesa em Ação de Improbidade Administrativa',
        'short_name': 'Defesa Improbidade',
        'description': 'Contestação e defesa do município/agente público em ação de improbidade',
        'category': 'procuradoria',
        'icon': 'Shield',
        'color': '#7C3AED',
        'legal_basis': 'Lei 8.429/1992 (com alterações da Lei 14.230/2021); CPC/2015',
        'display_order': 3,
    },
    {
        'code': 'contestacao_acao_popular',
        'name': 'Contestação em Ação Popular',
        'short_name': 'Cont. Ação Popular',
        'description': 'Defesa do município em ação popular movida por cidadão',
        'category': 'procuradoria',
        'icon': 'Shield',
        'color': '#7C3AED',
        'legal_basis': 'Lei 4.717/1965 (Ação Popular); CF/88, art. 5º, LXXIII; CPC/2015',
        'display_order': 4,
    },
    {
        'code': 'minuta_decreto_municipal',
        'name': 'Minuta de Decreto Municipal',
        'short_name': 'Minuta Decreto',
        'description': 'Minuta de decreto para regulamentação de matéria de competência do Executivo municipal',
        'category': 'procuradoria',
        'icon': 'FileEdit',
        'color': '#0F766E',
        'legal_basis': 'CF/88, art. 30; Lei Orgânica Municipal; Lei 9.784/1999',
        'display_order': 5,
    },
    {
        'code': 'minuta_lei_municipal',
        'name': 'Minuta de Lei Municipal (Projeto de Lei)',
        'short_name': 'Minuta de Lei',
        'description': 'Projeto de lei de iniciativa do Executivo municipal para envio à Câmara',
        'category': 'procuradoria',
        'icon': 'BookOpen',
        'color': '#0F766E',
        'legal_basis': 'CF/88, arts. 29-30; Lei Orgânica Municipal; Regimento Interno da Câmara',
        'display_order': 6,
    },
    {
        'code': 'recurso_processo_administrativo',
        'name': 'Recurso em Processo Administrativo Municipal',
        'short_name': 'Recurso Adm. Municipal',
        'description': 'Recurso administrativo municipal contra autuação, multa ou decisão desfavorável',
        'category': 'procuradoria',
        'icon': 'TrendingUp',
        'color': '#059669',
        'legal_basis': 'Lei 9.784/1999, arts. 56-65; CF/88, art. 5º, LV; Lei Orgânica Municipal',
        'display_order': 7,
    },
    {
        'code': 'nota_tecnica_procuradoria',
        'name': 'Nota Técnica da Procuradoria',
        'short_name': 'Nota Técnica',
        'description': 'Documento técnico-jurídico sobre tema específico para orientar a gestão municipal',
        'category': 'procuradoria',
        'icon': 'FileSearch',
        'color': '#1D4ED8',
        'legal_basis': 'CF/88, art. 37; Lei 9.784/1999; Instrução Normativa da PGM',
        'display_order': 8,
    },
    {
        'code': 'representacao_tce',
        'name': 'Representação ao Tribunal de Contas',
        'short_name': 'Representação TCE',
        'description': 'Representação do município ao TCE sobre irregularidade em licitação ou contrato',
        'category': 'procuradoria',
        'icon': 'AlertTriangle',
        'color': '#DC2626',
        'legal_basis': 'CF/88, arts. 70-75; Lei 8.666/1993; Lei 14.133/2021; Lei Orgânica do TCE',
        'display_order': 9,
    },
    # ── Dívida Ativa ────────────────────────────────────────────────────
    {
        'code': 'representacao_execucao_fiscal',
        'name': 'Representação para Execução Fiscal Municipal',
        'short_name': 'Exec. Fiscal Municipal',
        'description': 'Petição inicial para execução de crédito tributário ou não-tributário municipal',
        'category': 'divida_ativa',
        'icon': 'FileWarning',
        'color': '#D97706',
        'legal_basis': 'Lei 6.830/1980 (LEF); CTN, arts. 201-204; CPC/2015, arts. 771-788',
        'display_order': 1,
    },
    {
        'code': 'peticao_inicial_execucao_fiscal',
        'name': 'Petição Inicial de Execução Fiscal',
        'short_name': 'P.I. Exec. Fiscal',
        'description': 'Petição inicial de execução fiscal com instrução da CDA',
        'category': 'divida_ativa',
        'icon': 'FileWarning',
        'color': '#D97706',
        'legal_basis': 'Lei 6.830/1980, arts. 6-15; CTN arts. 201-204; CPC/2015',
        'display_order': 2,
    },
    {
        'code': 'impugnacao_embargos_execucao',
        'name': 'Impugnação aos Embargos à Execução Fiscal',
        'short_name': 'Impugnação Embargos',
        'description': 'Resposta da Fazenda Municipal aos embargos opostos pelo executado',
        'category': 'divida_ativa',
        'icon': 'FileWarning',
        'color': '#D97706',
        'legal_basis': 'Lei 6.830/1980, arts. 16-22; CTN arts. 142-173; CPC/2015, arts. 914-920',
        'display_order': 3,
    },
    # ── Licitações e Contratos ──────────────────────────────────────────
    {
        'code': 'minuta_contrato_administrativo',
        'name': 'Minuta de Contrato Administrativo',
        'short_name': 'Minuta Contrato',
        'description': 'Minuta de contrato administrativo para licitação ou contratação direta',
        'category': 'licitacoes',
        'icon': 'ClipboardList',
        'color': '#0369A1',
        'legal_basis': 'Lei 14.133/2021, arts. 92-107; CC/2002; Lei 8.666/1993 (transitório)',
        'display_order': 1,
    },
    {
        'code': 'minuta_convenio',
        'name': 'Minuta de Convênio Municipal',
        'short_name': 'Minuta Convênio',
        'description': 'Minuta de convênio entre o município e outro ente público ou entidade privada sem fins lucrativos',
        'category': 'licitacoes',
        'icon': 'Handshake',
        'color': '#0369A1',
        'legal_basis': 'Lei 13.019/2014 (Marco das OSCs); Decreto 10.426/2020; CF/88, art. 241',
        'display_order': 2,
    },
    {
        'code': 'minuta_tac',
        'name': 'Termo de Ajustamento de Conduta (TAC)',
        'short_name': 'TAC',
        'description': 'Instrumento de compromisso para reparação de irregularidades sem litígio',
        'category': 'licitacoes',
        'icon': 'CheckSquare',
        'color': '#0369A1',
        'legal_basis': 'Lei 7.347/1985, art. 5º, §6º; CF/88, art. 129; MP; legislação ambiental/urbanística',
        'display_order': 3,
    },
    {
        'code': 'parecer_juridico_licitacao',
        'name': 'Parecer Jurídico em Processo Licitatório',
        'short_name': 'Parecer Licitação',
        'description': 'Parecer da procuradoria sobre regularidade jurídica de edital e minuta de contrato',
        'category': 'licitacoes',
        'icon': 'FileText',
        'color': '#0369A1',
        'legal_basis': 'Lei 14.133/2021, art. 53; Lei 8.666/1993, art. 38; Lei 9.784/1999',
        'display_order': 4,
    },
    # ── Controle Interno e Compliance ───────────────────────────────────
    {
        'code': 'nota_compliance_lgpd',
        'name': 'Nota de Compliance — LGPD Municipal',
        'short_name': 'Nota LGPD',
        'description': 'Análise de conformidade com a LGPD aplicada a processos e sistemas municipais',
        'category': 'controle_interno',
        'icon': 'ShieldCheck',
        'color': '#4F46E5',
        'legal_basis': 'Lei 13.709/2018 (LGPD); Resolução CD/ANPD 2/2022; CF/88, art. 5º, XII',
        'display_order': 1,
    },
]

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
- Conteúdo inferido: [VERIFICAR COM PROCURADOR]
"""

PROMPT_PROCURADORIA = CONST_ANTI_ALUCINACAO + """Você é procurador(a) municipal especialista em Direito Público.

CONTEXTO:
- Você representa o MUNICÍPIO em juízo e fora dele
- Seus documentos têm linguagem técnica, impessoal e formal
- Siga a estrutura típica de peças da Procuradoria Geral do Município (PGM)

LEGISLAÇÃO VIGENTE:
- CF/88, arts. 29-30 (Municípios), 37-43 (Administração Pública), 70-75 (Controle)
- Lei 9.784/1999 (processo administrativo federal — aplicado subsidiariamente)
- Lei 8.429/1992 alterada pela Lei 14.230/2021 (improbidade administrativa)
- Lei 14.133/2021 (NLLCA) e Lei 8.666/1993 (ainda aplicável em transição)
- CPC/2015 (subsidiário ao processo administrativo e às ações judiciais do município)
- Lei Orgânica Municipal e legislação municipal específica

REGRAS ESSENCIAIS:
1. Prerrogativas da Fazenda Pública: prazos em quádruplo para contestar, em dobro para recorrer (CPC art. 183)
2. Presunção de legalidade dos atos administrativos: cabe ao impugnante o ônus de provar ilegalidade
3. Princípios da Administração Pública: legalidade, impessoalidade, moralidade, publicidade, eficiência (CF art. 37)
4. Controle de legalidade, não de mérito administrativo, pelo Judiciário
5. Municípios têm autonomia administrativa, financeira e legislativa (CF art. 30)
6. Competência do TCE para fiscalizar contas municipais (CF arts. 70-75)
7. Fazenda Pública não paga custas antecipadamente (CPC art. 91)
8. Duplo grau obrigatório (remessa necessária) em decisões contrárias ao Município (CPC arts. 496-497)

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_DIVIDA_ATIVA = CONST_ANTI_ALUCINACAO + """Você é procurador(a) municipal especialista em cobrança de Dívida Ativa.

LEGISLAÇÃO VIGENTE:
- Lei 6.830/1980 (LEF) — lei específica de execução fiscal
- CTN (Lei 5.172/1966), arts. 139-174 (crédito tributário, inscrição em DA)
- CPC/2015 (subsidiário à LEF); Lei 9.492/1997 (protesto)
- CF/88, arts. 145-162 (sistema tributário nacional)

REGRAS ESSENCIAIS:
1. CDA goza de presunção de certeza e liquidez (LEF art. 3º) — ônus do executado em provar defeitos
2. Penhora: LEF art. 11 (ordem preferencial — dinheiro primeiro)
3. Prescrição: CTN art. 174 — 5 anos do lançamento definitivo (tributos); 5 anos da constituição (créditos não-tributários)
4. Redirecionamento: sócio-gerente responde por dissolução irregular (STJ Súmula 435)
5. Embargos: 30 dias após seguro o juízo (LEF art. 16)
6. Certidão Negativa: CTN arts. 205-208
7. Prioridade de recebimento: CF art. 100 (precatórios); LEF art. 29 (preferência do crédito fiscal)
8. Súmulas STJ tributárias: 7, 213, 355, 393, 430, 436, 446, 452, 460, 497, 555, 558, 560

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_LICITACOES = CONST_ANTI_ALUCINACAO + """Você é procurador(a) municipal especialista em Licitações e Contratos Administrativos.

LEGISLAÇÃO VIGENTE:
- Lei 14.133/2021 (NLLCA) — nova lei de licitações e contratos
- Lei 8.666/1993 (ainda aplicável em período de transição)
- Lei 10.520/2002 (pregão) — mantida pela NLLCA
- Lei 13.019/2014 (Marco das OSCs — convênios e parcerias)
- Decreto 10.426/2020 (regulamenta transferências voluntárias)
- CF/88, art. 37, XXI (licitação obrigatória); art. 241 (consórcios)
- CPC/2015 (subsidiário); Lei 9.784/1999 (processo adm.)

REGRAS ESSENCIAIS:
1. Modalidades NLLCA: pregão, concorrência, concurso, leilão, diálogo competitivo (art. 28)
2. Dispensa: NLLCA art. 75 — rol taxativo
3. Inexigibilidade: NLLCA art. 74 — inviabilidade de competição
4. Prazo de vigência: contratos até 5 anos (serviços contínuos até 10 anos — art. 106)
5. Obrigatoriedade de publicação: PNCP (Portal Nacional de Contratações Públicas)
6. Irregularidades: nulidade do contrato não exime remuneração por serviços prestados (NLLCA art. 147)
7. Responsabilidade solidária do gestor em caso de inexecução culposa
8. Garantia contratual: até 5% do valor do contrato (obras complexas até 10%)

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR = """Você é revisor jurídico de peças processuais e administrativas brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

# ─────────────────────────────────────────────────────────────────────────────

BLUEPRINTS_DATA = [
    # ── Parecer Jurídico ─────────────────────────────────────────────────
    {
        'doc_type_code': 'parecer_juridico',
        'name': 'Parecer Jurídico da Procuradoria Municipal',
        'description': 'Opinião técnico-jurídica da PGM sobre questão de direito público',
        'version': '1.0',
        'legal_basis': 'Lei 9.784/1999; CF/88, arts. 131-132; LC Municipal',
        'primary_color': '#1D4ED8',
        'secondary_color': '#3B82F6',
        'cover_title': 'Parecer Jurídico',
        'agent_key': 'gerador_procuradoria',
        'sections': [
            {
                'number': 1, 'key': 'relatorio',
                'name': 'I — Relatório',
                'description': 'Apresentação do expediente consultado',
                'instructions': 'Identifique o número do processo/expediente, o órgão consulente, a questão jurídica formulada e os documentos analisados. Seja objetivo e impessoal.',
                'fields': [
                    {'name': 'processo_numero', 'label': 'Número do Processo/Expediente', 'type': 'text', 'required': True},
                    {'name': 'orgao_consulente', 'label': 'Órgão/Secretaria Consulente', 'type': 'text', 'required': True},
                    {'name': 'questao_juridica', 'label': 'Questão Jurídica Formulada', 'type': 'textarea', 'required': True},
                    {'name': 'documentos_analisados', 'label': 'Documentos Analisados', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'fundamentacao',
                'name': 'II — Da Fundamentação Jurídica',
                'description': 'Análise jurídica da questão',
                'instructions': 'Analise a questão jurídica com base na legislação, doutrina e jurisprudência pertinentes. Organize em subitens se necessário (II.1, II.2...). Cite artigos, leis e súmulas de forma precisa. Use marcadores para jurisprudência não verificada.',
                'fields': [
                    {'name': 'legislacao_aplicavel', 'label': 'Legislação Aplicável', 'type': 'textarea', 'required': True},
                    {'name': 'analise_juridica', 'label': 'Análise Jurídica Detalhada', 'type': 'textarea', 'required': True},
                    {'name': 'jurisprudencia', 'label': 'Jurisprudência (STF/STJ/TCE)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'conclusao',
                'name': 'III — Conclusão',
                'description': 'Resposta objetiva à questão jurídica',
                'instructions': 'Formule a conclusão de forma objetiva e direta. Indique se a medida pretendida é ou não juridicamente viável, com as ressalvas e condições necessárias. Inclua recomendações específicas.',
                'fields': [
                    {'name': 'conclusao_principal', 'label': 'Conclusão Principal', 'type': 'textarea', 'required': True},
                    {'name': 'recomendacoes', 'label': 'Recomendações e Ressalvas', 'type': 'textarea', 'required': False},
                    {'name': 'local_data', 'label': 'Local e Data', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ── Nota de Assessoria Jurídica ──────────────────────────────────────
    {
        'doc_type_code': 'nota_assessoria_juridica',
        'name': 'Nota de Assessoria Jurídica — PGM',
        'description': 'Nota técnica da procuradoria sobre expediente ou consulta do gestor',
        'version': '1.0',
        'legal_basis': 'Lei 9.784/1999; CF/88, art. 37; Regimento Interno da PGM',
        'primary_color': '#1D4ED8',
        'secondary_color': '#3B82F6',
        'cover_title': 'Nota de Assessoria Jurídica',
        'agent_key': 'gerador_procuradoria',
        'sections': [
            {
                'number': 1, 'key': 'objeto',
                'name': 'I — Do Objeto da Consulta',
                'description': 'Identificação da questão submetida à assessoria',
                'instructions': 'Descreva brevemente o expediente recebido, o órgão solicitante e a questão jurídica a ser examinada.',
                'fields': [
                    {'name': 'solicitante', 'label': 'Órgão/Servidor Solicitante', 'type': 'text', 'required': True},
                    {'name': 'materia', 'label': 'Matéria / Questão Apresentada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'analise',
                'name': 'II — Da Análise',
                'description': 'Exame técnico-jurídico da matéria',
                'instructions': 'Analise objetivamente a questão, citando a legislação pertinente, posicionamentos do TCE/TCU e orientações do CGM. Seja conciso mas completo.',
                'fields': [
                    {'name': 'fundamentos', 'label': 'Fundamentos Jurídicos', 'type': 'textarea', 'required': True},
                    {'name': 'legislacao', 'label': 'Legislação e Normas Aplicáveis', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'encaminhamento',
                'name': 'III — Do Encaminhamento',
                'description': 'Orientação objetiva ao solicitante',
                'instructions': 'Conclua com orientação prática e objetiva: o que deve ou não ser feito, riscos jurídicos identificados, necessidade de nova consulta ou documentação adicional.',
                'fields': [
                    {'name': 'orientacao', 'label': 'Orientação / Encaminhamento', 'type': 'textarea', 'required': True},
                    {'name': 'ressalvas', 'label': 'Ressalvas e Alertas Jurídicos', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ── Defesa em Improbidade ────────────────────────────────────────────
    {
        'doc_type_code': 'defesa_improbidade',
        'name': 'Defesa em Ação de Improbidade Administrativa — Lei 14.230/2021',
        'description': 'Contestação e defesa do município ou agente público em ação de improbidade',
        'version': '1.0',
        'legal_basis': 'Lei 8.429/1992 c/c Lei 14.230/2021; CPC/2015; CF/88, art. 37, §4º',
        'primary_color': '#7C3AED',
        'secondary_color': '#A78BFA',
        'cover_title': 'Defesa em Ação de Improbidade',
        'agent_key': 'gerador_procuradoria',
        'sections': [
            {
                'number': 1, 'key': 'preliminares',
                'name': 'I — Das Preliminares',
                'description': 'Questões processuais e de admissibilidade',
                'instructions': 'Verifique e argua preliminares: inépcia da inicial (ausência de dolo específico — Lei 14.230/2021, art. 1º, §1º), legitimidade ativa, prescrição (8 anos — art. 23), litisconsórcio, competência. A nova lei exige dolo específico para configuração de improbidade.',
                'fields': [
                    {'name': 'numero_processo', 'label': 'Número do Processo', 'type': 'text', 'required': True},
                    {'name': 'reu_qualificacao', 'label': 'Qualificação do Réu (cargo/função)', 'type': 'text', 'required': True},
                    {'name': 'preliminares_arguidas', 'label': 'Preliminares a Arguir', 'type': 'select', 'required': True, 'options': ['Ausência de dolo específico (art. 1º §1º)', 'Prescrição (art. 23 — 8 anos)', 'Ilegitimidade ativa do Ministério Público', 'Inépcia da petição inicial', 'Litisconsórcio necessário', 'Não cabimento (ato de mera irregularidade)']},
                    {'name': 'descricao_preliminar', 'label': 'Descrição das Preliminares', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'merito',
                'name': 'II — Do Mérito — Da Ausência de Improbidade',
                'description': 'Defesa de mérito contra os atos imputados',
                'instructions': 'Refute ponto a ponto cada ato imputado na inicial. Demonstre: (a) ausência de dolo específico de lesar o erário ou de enriquecimento ilícito; (b) regularidade formal e material dos atos praticados; (c) ausência de enriquecimento ilícito; (d) atos discricionários dentro dos limites legais. Cite princípios e legislação.',
                'fields': [
                    {'name': 'atos_imputados', 'label': 'Atos Imputados na Inicial', 'type': 'textarea', 'required': True},
                    {'name': 'refutacao_atos', 'label': 'Refutação Detalhada dos Atos', 'type': 'textarea', 'required': True},
                    {'name': 'documentos_defesa', 'label': 'Documentos de Defesa (portarias, despachos, etc.)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'III — Dos Pedidos',
                'description': 'Pedidos da defesa',
                'instructions': 'Formule pedidos: rejeição da ação por ausência de dolo específico (art. 17-D, Lei 14.230/2021), julgamento improcedente, condenação do autor em honorários advocatícios e custas processuais, produção de provas.',
                'fields': [
                    {'name': 'pedido_rejeicao', 'label': 'Pedido de Rejeição da Inicial', 'type': 'select', 'required': True, 'options': ['Sim — ausência de dolo específico (art. 17-D)', 'Não — ir direto ao mérito']},
                    {'name': 'pedidos_especificos', 'label': 'Pedidos Específicos', 'type': 'textarea', 'required': True},
                    {'name': 'provas_requeridas', 'label': 'Provas Requeridas', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ── Contestação Ação Popular ─────────────────────────────────────────
    {
        'doc_type_code': 'contestacao_acao_popular',
        'name': 'Contestação em Ação Popular — Lei 4.717/1965',
        'description': 'Defesa do município em ação popular movida por cidadão',
        'version': '1.0',
        'legal_basis': 'Lei 4.717/1965; CF/88, art. 5º, LXXIII; CPC/2015',
        'primary_color': '#7C3AED',
        'secondary_color': '#A78BFA',
        'cover_title': 'Contestação — Ação Popular',
        'agent_key': 'gerador_procuradoria',
        'sections': [
            {
                'number': 1, 'key': 'preliminares_acao_popular',
                'name': 'I — Das Preliminares',
                'description': 'Pressupostos processuais e questões de admissibilidade',
                'instructions': 'Arguia preliminares: legitimidade ativa do autor popular (precisa ser cidadão — Lei 4.717/1965, art. 1º), ausência de lesividade ao patrimônio público, prescrição de 5 anos (art. 21), ato válido e legal. Posição do município: réu necessário (art. 6º) que pode contestar ou aditar a inicial.',
                'fields': [
                    {'name': 'autor_popular', 'label': 'Nome e CPF do Autor (cidadão)', 'type': 'text', 'required': True},
                    {'name': 'ato_atacado', 'label': 'Ato Administrativo Impugnado', 'type': 'textarea', 'required': True},
                    {'name': 'posicao_municipio', 'label': 'Posição do Município', 'type': 'select', 'required': True, 'options': ['Contestar a ação (ato é regular)', 'Aderir ao polo ativo (ato é ilegal — art. 6º §3º)', 'Contestar parcialmente']},
                ],
            },
            {
                'number': 2, 'key': 'merito_popular',
                'name': 'II — Do Mérito — Da Legalidade do Ato',
                'description': 'Defesa da legalidade do ato administrativo',
                'instructions': 'Demonstre a legalidade do ato impugnado: competência da autoridade, forma legal, motivo real e suficiente, objeto lícito, finalidade pública. Refute a lesividade ao patrimônio. Cite o princípio da presunção de legalidade dos atos administrativos.',
                'fields': [
                    {'name': 'fundamentos_legalidade', 'label': 'Fundamentos da Legalidade do Ato', 'type': 'textarea', 'required': True},
                    {'name': 'ausencia_lesividade', 'label': 'Ausência de Lesividade ao Patrimônio Público', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos_popular',
                'name': 'III — Dos Pedidos',
                'description': 'Pedidos da contestação',
                'instructions': 'Formule pedidos: extinção sem julgamento de mérito (preliminares) ou julgamento improcedente (mérito), condenação do autor em custas se má-fé (Lei 4.717/1965, art. 13).',
                'fields': [
                    {'name': 'pedidos', 'label': 'Pedidos', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ── Minuta de Decreto Municipal ──────────────────────────────────────
    {
        'doc_type_code': 'minuta_decreto_municipal',
        'name': 'Minuta de Decreto Municipal',
        'description': 'Decreto para regulamentação de matéria de competência do Prefeito',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 30; Lei Orgânica Municipal; Lei 9.784/1999',
        'primary_color': '#0F766E',
        'secondary_color': '#14B8A6',
        'cover_title': 'Decreto Municipal',
        'agent_key': 'gerador_procuradoria',
        'sections': [
            {
                'number': 1, 'key': 'ementa_decreto',
                'name': 'Ementa e Preâmbulo',
                'description': 'Identificação e fundamento legal do decreto',
                'instructions': 'Elabore a ementa (descrição resumida do objeto) e o preâmbulo com a autoridade expedidora (Prefeito Municipal), fundamento constitucional e legal (Lei Orgânica, lei municipal específica ou federal) e a competência.',
                'fields': [
                    {'name': 'municipio', 'label': 'Município e Estado', 'type': 'text', 'required': True},
                    {'name': 'objeto_decreto', 'label': 'Objeto do Decreto (o que regulamenta)', 'type': 'textarea', 'required': True},
                    {'name': 'legislacao_base', 'label': 'Legislação que Autoriza o Decreto', 'type': 'textarea', 'required': True},
                    {'name': 'numero_decreto', 'label': 'Número do Decreto (se já definido)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'artigos_decreto',
                'name': 'Artigos do Decreto',
                'description': 'Disposições normativas',
                'instructions': 'Elabore os artigos do decreto com linguagem normativa clara e objetiva. Organize: Art. 1º (objeto/finalidade), Art. 2º e seguintes (disposições substantivas), Penúltimo artigo (revogações), Último artigo (vigência). Use "Art. X. — " para cada artigo.',
                'fields': [
                    {'name': 'disposicoes', 'label': 'Disposições a Regulamentar', 'type': 'textarea', 'required': True},
                    {'name': 'vigencia', 'label': 'Data de Vigência (ou "na data de publicação")', 'type': 'text', 'required': True},
                    {'name': 'normas_revogadas', 'label': 'Normas a Revogar (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ── Execução Fiscal Municipal ────────────────────────────────────────
    {
        'doc_type_code': 'peticao_inicial_execucao_fiscal',
        'name': 'Petição Inicial de Execução Fiscal Municipal — LEF',
        'description': 'PI de execução fiscal para cobrança de crédito tributário ou não-tributário municipal',
        'version': '1.0',
        'legal_basis': 'Lei 6.830/1980, arts. 1-15; CTN, arts. 201-204; CPC/2015',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Petição Inicial — Execução Fiscal',
        'agent_key': 'gerador_divida_ativa',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_execucao',
                'name': 'Qualificação das Partes e CDA',
                'description': 'Identificação do exequente, executado e título executivo',
                'instructions': 'Identifique o Município (Fazenda Pública Municipal) como exequente. Qualifique o executado. Descreva a Certidão de Dívida Ativa (CDA): número de inscrição, tributo ou origem do crédito, período, valor atualizado, acréscimos legais.',
                'fields': [
                    {'name': 'municipio_exequente', 'label': 'Município Exequente', 'type': 'text', 'required': True},
                    {'name': 'executado_nome', 'label': 'Nome/Razão Social do Executado', 'type': 'text', 'required': True},
                    {'name': 'executado_cpf_cnpj', 'label': 'CPF/CNPJ do Executado', 'type': 'text', 'required': True},
                    {'name': 'executado_endereco', 'label': 'Endereço do Executado', 'type': 'text', 'required': True},
                    {'name': 'numero_cda', 'label': 'Número da CDA', 'type': 'text', 'required': True},
                    {'name': 'tributo_origem', 'label': 'Tributo / Origem do Crédito', 'type': 'text', 'required': True},
                    {'name': 'periodo_referencia', 'label': 'Período de Referência', 'type': 'text', 'required': True},
                    {'name': 'valor_total', 'label': 'Valor Total da Execução (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'pedidos_execucao',
                'name': 'Dos Pedidos',
                'description': 'Pedidos da petição inicial de execução fiscal',
                'instructions': 'Formule pedidos: citação do executado para pagar em 5 dias ou garantir o juízo (LEF art. 8º), penhora e arresto de bens, expedição de certidões e ofícios para localização de bens (Bacen Jud, Renajud, registro de imóveis).',
                'fields': [
                    {'name': 'pede_bacen_jud', 'label': 'Requer pesquisa Bacen Jud?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'pede_renajud', 'label': 'Requer pesquisa Renajud?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'outros_pedidos', 'label': 'Outros Pedidos', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ── Impugnação aos Embargos ──────────────────────────────────────────
    {
        'doc_type_code': 'impugnacao_embargos_execucao',
        'name': 'Impugnação aos Embargos à Execução Fiscal — Fazenda Municipal',
        'description': 'Resposta da Fazenda Municipal aos embargos opostos pelo executado',
        'version': '1.0',
        'legal_basis': 'Lei 6.830/1980, arts. 16-22; CTN, arts. 142-173; CPC/2015',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Impugnação aos Embargos à Execução Fiscal',
        'agent_key': 'gerador_divida_ativa',
        'sections': [
            {
                'number': 1, 'key': 'intempestividade_inadmissibilidade',
                'name': 'I — Da Intempestividade / Inadmissibilidade (se cabível)',
                'description': 'Impugnar tempestividade e pressupostos dos embargos',
                'instructions': 'Se os embargos forem intempestivos (além de 30 dias após garantia do juízo — LEF art. 16), argua de imediato. Verifique também se o juízo está garantido (penhora suficiente). Se não houver preliminar, indique que os embargos devem ser conhecidos e passe ao mérito.',
                'fields': [
                    {'name': 'ha_intempestividade', 'label': 'Há intempestividade a arguir?', 'type': 'select', 'required': True, 'options': ['Sim — embargos intempestivos', 'Não — embargos tempestivos, impugnar o mérito']},
                    {'name': 'descricao_preliminar', 'label': 'Descrição (se houver preliminar)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'merito_impugnacao',
                'name': 'II — Do Mérito — Da Legalidade da CDA',
                'description': 'Defesa da regularidade do crédito tributário',
                'instructions': 'Refute as matérias de defesa do embargante: (a) prescrição — demonstre que o prazo não correu ou foi interrompido; (b) nulidade da CDA — demonstre requisitos atendidos (CTN art. 202 + LEF art. 2º §5º); (c) pagamento — conteste com extratos do sistema tributário; (d) ilegitimidade — demonstre sujeição passiva. A CDA goza de presunção de certeza (LEF art. 3º).',
                'fields': [
                    {'name': 'materias_embargantes', 'label': 'Matérias Arguidas pelo Embargante', 'type': 'textarea', 'required': True},
                    {'name': 'refutacao_materias', 'label': 'Refutação das Matérias (ponto a ponto)', 'type': 'textarea', 'required': True},
                    {'name': 'documentos_fazenda', 'label': 'Documentos da Fazenda (extratos, histórico)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos_impugnacao',
                'name': 'III — Dos Pedidos',
                'description': 'Pedidos da impugnação',
                'instructions': 'Formule pedidos: rejeição liminar dos embargos (se intempestivos), julgamento improcedente, manutenção da execução, condenação em honorários (CPC art. 85 c/c LEF art. 26).',
                'fields': [
                    {'name': 'pedidos', 'label': 'Pedidos da Fazenda Municipal', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ── Minuta de Contrato Administrativo ───────────────────────────────
    {
        'doc_type_code': 'minuta_contrato_administrativo',
        'name': 'Minuta de Contrato Administrativo — NLLCA/Lei 14.133/2021',
        'description': 'Minuta de contrato para pregão ou concorrência municipal',
        'version': '1.0',
        'legal_basis': 'Lei 14.133/2021, arts. 92-107; CC/2002; LINDB',
        'primary_color': '#0369A1',
        'secondary_color': '#38BDF8',
        'cover_title': 'Contrato Administrativo',
        'agent_key': 'gerador_licitacoes',
        'sections': [
            {
                'number': 1, 'key': 'partes_objeto',
                'name': 'Partes e Objeto',
                'description': 'Qualificação das partes e definição do objeto contratual',
                'instructions': 'Identifique: CONTRATANTE (Município, CNPJ, representante legal/Prefeito), CONTRATADA (empresa vencedora, CNPJ/CPF, representante). Defina o OBJETO de forma clara e vinculada ao edital e à proposta vencedora (NLLCA art. 92, I). Mencione o processo licitatório de origem.',
                'fields': [
                    {'name': 'municipio_contratante', 'label': 'Município Contratante e CNPJ', 'type': 'text', 'required': True},
                    {'name': 'objeto_contrato', 'label': 'Objeto do Contrato', 'type': 'textarea', 'required': True},
                    {'name': 'modalidade_licitacao', 'label': 'Modalidade Licitatória de Origem', 'type': 'select', 'required': True, 'options': ['Pregão Eletrônico', 'Pregão Presencial', 'Concorrência', 'Concurso', 'Dispensa de Licitação', 'Inexigibilidade']},
                    {'name': 'numero_licitacao', 'label': 'Número do Processo Licitatório', 'type': 'text', 'required': True},
                    {'name': 'valor_total', 'label': 'Valor Total do Contrato (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'obrigacoes_prazo',
                'name': 'Obrigações das Partes e Prazo',
                'description': 'Obrigações do contratante, da contratada e vigência',
                'instructions': 'Defina obrigações do CONTRATANTE (pagar, fiscalizar, fornecer informações) e da CONTRATADA (executar o objeto, manter habilitação, aceitar fiscalização, responder por danos — NLLCA art. 104). Estabeleça prazo de vigência (máx 5 anos — art. 106) e local de execução.',
                'fields': [
                    {'name': 'prazo_vigencia', 'label': 'Prazo de Vigência', 'type': 'text', 'required': True},
                    {'name': 'local_execucao', 'label': 'Local de Execução', 'type': 'text', 'required': True},
                    {'name': 'obrigacoes_especificas', 'label': 'Obrigações Específicas da Contratada', 'type': 'textarea', 'required': True},
                    {'name': 'garantia_contratual', 'label': 'Garantia Contratual (% do valor)', 'type': 'select', 'required': True, 'options': ['Sem garantia', '2%', '5% (padrão)', '10% (obras complexas)']},
                ],
            },
            {
                'number': 3, 'key': 'pagamento_fiscalizacao',
                'name': 'Pagamento, Fiscalização e Penalidades',
                'description': 'Condições de pagamento, gestor/fiscal e sanções',
                'instructions': 'Defina: forma e prazo de pagamento (NLLCA art. 141 — 30 dias úteis), nota fiscal, atesto do fiscal, reajuste (índice e periodicidade mínima de 12 meses — art. 92, V). Nomeie gestor e fiscal do contrato (NLLCA art. 117). Liste sanções: advertência, multa, suspensão, inidoneidade (NLLCA arts. 155-163).',
                'fields': [
                    {'name': 'prazo_pagamento', 'label': 'Prazo de Pagamento', 'type': 'select', 'required': True, 'options': ['30 dias úteis (padrão NLLCA)', '15 dias úteis', 'Outro — especificar']},
                    {'name': 'indice_reajuste', 'label': 'Índice de Reajuste', 'type': 'select', 'required': True, 'options': ['IPCA', 'INPC', 'IGP-M', 'Não aplicável']},
                    {'name': 'fiscal_contrato', 'label': 'Fiscal do Contrato (cargo/matrícula)', 'type': 'text', 'required': False},
                    {'name': 'multa_percentual', 'label': 'Multa por Inadimplência (%)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # ── Parecer em Licitação ─────────────────────────────────────────────
    {
        'doc_type_code': 'parecer_juridico_licitacao',
        'name': 'Parecer Jurídico em Processo Licitatório',
        'description': 'Análise jurídica da Procuradoria sobre regularidade do edital e minuta de contrato',
        'version': '1.0',
        'legal_basis': 'Lei 14.133/2021, art. 53; Lei 8.666/1993, art. 38; Lei 9.784/1999',
        'primary_color': '#0369A1',
        'secondary_color': '#38BDF8',
        'cover_title': 'Parecer Jurídico — Licitação',
        'agent_key': 'gerador_licitacoes',
        'sections': [
            {
                'number': 1, 'key': 'objeto_licitatorio',
                'name': 'I — Do Objeto Licitatório',
                'description': 'Identificação e qualificação do processo licitatório',
                'instructions': 'Identifique: órgão licitante, modalidade, objeto, valor estimado, critério de julgamento. Verifique se a modalidade é adequada ao valor e ao objeto (NLLCA art. 28).',
                'fields': [
                    {'name': 'orgao_licitante', 'label': 'Órgão/Secretaria Licitante', 'type': 'text', 'required': True},
                    {'name': 'modalidade', 'label': 'Modalidade Licitatória', 'type': 'select', 'required': True, 'options': ['Pregão Eletrônico', 'Pregão Presencial', 'Concorrência', 'Dispensa (art. 75)', 'Inexigibilidade (art. 74)']},
                    {'name': 'objeto_licitatorio', 'label': 'Objeto da Licitação', 'type': 'textarea', 'required': True},
                    {'name': 'valor_estimado', 'label': 'Valor Estimado (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'analise_juridica_licitacao',
                'name': 'II — Da Análise Jurídica',
                'description': 'Exame de regularidade do edital e minuta de contrato',
                'instructions': 'Analise: (a) adequação da modalidade ao valor/objeto; (b) requisitos de habilitação (NLLCA art. 62-70) — exija apenas o necessário; (c) critério de julgamento; (d) prazo de vigência do contrato; (e) garantias; (f) cláusulas essenciais (NLLCA art. 92); (g) publicação (PNCP). Indique eventuais pendências ou ressalvas.',
                'fields': [
                    {'name': 'pendencias', 'label': 'Pendências/Ressalvas Identificadas', 'type': 'textarea', 'required': False},
                    {'name': 'analise_edital', 'label': 'Análise do Edital', 'type': 'textarea', 'required': True},
                    {'name': 'analise_minuta_contrato', 'label': 'Análise da Minuta de Contrato', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'conclusao_licitacao',
                'name': 'III — Conclusão',
                'description': 'Aprovação, aprovação com ressalvas ou reprovação',
                'instructions': 'Conclua: aprovação do processo licitatório (sem ressalvas / com as ressalvas indicadas) ou reprovação com fundamentação legal. Seja objetivo.',
                'fields': [
                    {'name': 'conclusao', 'label': 'Conclusão', 'type': 'select', 'required': True, 'options': ['Aprovado — sem ressalvas', 'Aprovado — com ressalvas (a sanar antes da publicação)', 'Reprovado — retornar para correção']},
                    {'name': 'encaminhamento', 'label': 'Encaminhamento', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ── TAC ──────────────────────────────────────────────────────────────
    {
        'doc_type_code': 'minuta_tac',
        'name': 'Termo de Ajustamento de Conduta (TAC) Municipal',
        'description': 'Instrumento de compromisso para reparação de irregularidades sem litígio judicial',
        'version': '1.0',
        'legal_basis': 'Lei 7.347/1985, art. 5º, §6º; CF/88, art. 129; legislação ambiental e urbanística',
        'primary_color': '#0369A1',
        'secondary_color': '#38BDF8',
        'cover_title': 'Termo de Ajustamento de Conduta',
        'agent_key': 'gerador_licitacoes',
        'sections': [
            {
                'number': 1, 'key': 'partes_tac',
                'name': 'Partes e Preâmbulo',
                'description': 'Identificação dos compromitentes e órgão tomador',
                'instructions': 'Identifique: TOMADOR DO COMPROMISSO (Município/PGM ou MP), COMPROMISSÁRIO (pessoa física ou jurídica que causou a irregularidade). Descreva o ato ou situação que motivou o TAC e a legislação violada.',
                'fields': [
                    {'name': 'tomador', 'label': 'Tomador do Compromisso (órgão)', 'type': 'text', 'required': True},
                    {'name': 'compromissario', 'label': 'Compromissário (nome/razão social, CPF/CNPJ)', 'type': 'text', 'required': True},
                    {'name': 'irregularidade', 'label': 'Irregularidade que Motivou o TAC', 'type': 'textarea', 'required': True},
                    {'name': 'legislacao_violada', 'label': 'Legislação Violada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'obrigacoes_tac',
                'name': 'Das Obrigações Assumidas',
                'description': 'Compromissos, prazos e penalidades por descumprimento',
                'instructions': 'Liste de forma clara e numerada as obrigações do compromissário: ações a tomar, prazo para cada uma, forma de comprovação do cumprimento. Estabeleça multa por descumprimento (cláusula penal). O TAC suspende a propositura de ação civil pública.',
                'fields': [
                    {'name': 'obrigacoes', 'label': 'Obrigações (numere cada uma)', 'type': 'textarea', 'required': True},
                    {'name': 'prazo_cumprimento', 'label': 'Prazo para Cumprimento', 'type': 'text', 'required': True},
                    {'name': 'multa_descumprimento', 'label': 'Multa por Descumprimento (R$)', 'type': 'text', 'required': True},
                    {'name': 'forma_comprovacao', 'label': 'Forma de Comprovação do Cumprimento', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    # ── Nota Técnica Procuradoria ────────────────────────────────────────
    {
        'doc_type_code': 'nota_tecnica_procuradoria',
        'name': 'Nota Técnica da Procuradoria Municipal',
        'description': 'Documento técnico-jurídico para orientar a gestão municipal sobre tema específico',
        'version': '1.0',
        'legal_basis': 'CF/88, art. 37; Lei 9.784/1999; Instrução Normativa da PGM',
        'primary_color': '#1D4ED8',
        'secondary_color': '#3B82F6',
        'cover_title': 'Nota Técnica',
        'agent_key': 'gerador_procuradoria',
        'sections': [
            {
                'number': 1, 'key': 'introducao_nota',
                'name': 'I — Introdução e Escopo',
                'description': 'Apresentação do tema e delimitação do escopo',
                'instructions': 'Apresente o tema da nota técnica, motivação (solicitação de órgão, evento, nova legislação), e delimite o escopo da análise.',
                'fields': [
                    {'name': 'tema', 'label': 'Tema da Nota Técnica', 'type': 'text', 'required': True},
                    {'name': 'motivacao', 'label': 'Motivação / Origem (solicitação, nova lei, etc.)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'analise_nota',
                'name': 'II — Análise Jurídica',
                'description': 'Desenvolvimento técnico da matéria',
                'instructions': 'Desenvolva a análise jurídica com base na legislação, jurisprudência dos tribunais superiores e TCE, doutrina administrativa e posicionamentos do CGU/CGM. Estruture em subtópicos numerados.',
                'fields': [
                    {'name': 'analise_detalhada', 'label': 'Análise Jurídica Detalhada', 'type': 'textarea', 'required': True},
                    {'name': 'riscos_identificados', 'label': 'Riscos Jurídicos Identificados', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'orientacoes_nota',
                'name': 'III — Orientações e Recomendações',
                'description': 'Orientações práticas para o gestor municipal',
                'instructions': 'Forneça orientações práticas e objetivas. Quando possível, use linguagem acessível ao gestor não-jurídico. Indique medidas preventivas e corretivas.',
                'fields': [
                    {'name': 'orientacoes', 'label': 'Orientações Práticas', 'type': 'textarea', 'required': True},
                    {'name': 'referencias', 'label': 'Referências Legislativas e Jurisprudenciais', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    # ── Nota Compliance LGPD ─────────────────────────────────────────────
    {
        'doc_type_code': 'nota_compliance_lgpd',
        'name': 'Nota de Compliance — LGPD Municipal',
        'description': 'Análise de conformidade com a LGPD aplicada a sistemas e processos do município',
        'version': '1.0',
        'legal_basis': 'Lei 13.709/2018 (LGPD); Resolução CD/ANPD 2/2022; CF/88, art. 5º, XII',
        'primary_color': '#4F46E5',
        'secondary_color': '#818CF8',
        'cover_title': 'Nota de Compliance — LGPD',
        'agent_key': 'gerador_procuradoria',
        'sections': [
            {
                'number': 1, 'key': 'mapeamento_dados',
                'name': 'I — Mapeamento do Tratamento de Dados',
                'description': 'Identificação dos dados pessoais tratados',
                'instructions': 'Identifique os dados pessoais (e sensíveis) tratados pelo sistema/processo analisado, as bases legais utilizadas pelo Município (LGPD art. 7º, III — obrigação legal; art. 7º, VI — interesse público; art. 23 — poder público), os titulares, os destinatários e o prazo de retenção.',
                'fields': [
                    {'name': 'sistema_processo', 'label': 'Sistema / Processo Analisado', 'type': 'text', 'required': True},
                    {'name': 'tipos_dados', 'label': 'Tipos de Dados Pessoais Tratados', 'type': 'textarea', 'required': True},
                    {'name': 'base_legal', 'label': 'Base Legal do Tratamento (LGPD art. 7º)', 'type': 'select', 'required': True, 'options': ['Art. 7º, III — obrigação legal ou regulatória', 'Art. 7º, VI — exercício regular de direitos', 'Art. 23 — poder público (política pública)', 'Art. 7º, V — contrato/pré-contrato']},
                    {'name': 'prazo_retencao', 'label': 'Prazo de Retenção dos Dados', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'conformidade_lgpd',
                'name': 'II — Análise de Conformidade',
                'description': 'Gaps de conformidade e recomendações',
                'instructions': 'Avalie: (a) existência de aviso de privacidade/política; (b) meios para exercício dos direitos dos titulares (LGPD art. 18); (c) medidas de segurança (art. 46); (d) compartilhamento com terceiros e contratos de processamento; (e) Encarregado de Dados (DPO) nomeado (art. 41). Indique gaps e nível de risco (alto/médio/baixo).',
                'fields': [
                    {'name': 'gaps_conformidade', 'label': 'Gaps de Conformidade Identificados', 'type': 'textarea', 'required': True},
                    {'name': 'nivel_risco', 'label': 'Nível de Risco Geral', 'type': 'select', 'required': True, 'options': ['Baixo — conformidade satisfatória', 'Médio — ajustes necessários', 'Alto — irregularidades graves']},
                ],
            },
            {
                'number': 3, 'key': 'plano_acao_lgpd',
                'name': 'III — Plano de Ação',
                'description': 'Medidas corretivas e preventivas',
                'instructions': 'Apresente plano de ação com: medidas prioritárias (curto prazo — até 30 dias), medidas de médio prazo (30-90 dias), medidas de longo prazo (90+ dias). Indique responsáveis e referências normativas (Resolução ANPD).',
                'fields': [
                    {'name': 'acoes_curto_prazo', 'label': 'Ações de Curto Prazo (até 30 dias)', 'type': 'textarea', 'required': True},
                    {'name': 'acoes_medio_prazo', 'label': 'Ações de Médio Prazo (30-90 dias)', 'type': 'textarea', 'required': False},
                    {'name': 'responsavel_dpo', 'label': 'Encarregado de Dados (DPO) Responsável', 'type': 'text', 'required': False},
                ],
            },
        ],
    },
]

# Mapeamento: doc_type_code → agent_key
AGENTE_POR_TIPO = {
    'parecer_juridico': 'gerador_procuradoria',
    'nota_assessoria_juridica': 'gerador_procuradoria',
    'defesa_improbidade': 'gerador_procuradoria',
    'contestacao_acao_popular': 'gerador_procuradoria',
    'minuta_decreto_municipal': 'gerador_procuradoria',
    'minuta_lei_municipal': 'gerador_procuradoria',
    'recurso_processo_administrativo': 'gerador_procuradoria',
    'nota_tecnica_procuradoria': 'gerador_procuradoria',
    'representacao_tce': 'gerador_procuradoria',
    'nota_compliance_lgpd': 'gerador_procuradoria',
    'peticao_inicial_execucao_fiscal': 'gerador_divida_ativa',
    'representacao_execucao_fiscal': 'gerador_divida_ativa',
    'impugnacao_embargos_execucao': 'gerador_divida_ativa',
    'minuta_contrato_administrativo': 'gerador_licitacoes',
    'minuta_convenio': 'gerador_licitacoes',
    'minuta_tac': 'gerador_licitacoes',
    'parecer_juridico_licitacao': 'gerador_licitacoes',
}


class Command(BaseCommand):
    help = 'Seed de blueprints para Procuradoria Municipal — Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força recriação mesmo que o blueprint já exista',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Exibe o que seria criado sem salvar',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Procuradoria Municipal'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            self.stdout.write(f'Categorias a criar: {len(CATEGORIAS)}')
            self.stdout.write(f'Tipos de documento: {len(TIPOS_DOCUMENTO)}')
            self.stdout.write(f'Blueprints:         {len(BLUEPRINTS_DATA)}')
            return

        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Procuradoria Municipal concluído!\n'))

    def _criar_categorias(self):
        from apps.core.models import DocumentCategory
        self.stdout.write('\n[1/4] Categorias...')
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
        self.stdout.write('\n[2/4] Tipos de documento...')
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
        self.stdout.write('\n[3/4] Agentes de seção...')
        specs = [
            {
                'key': 'gerador_procuradoria',
                'name': 'Verus.AI — Gerador Procuradoria Municipal',
                'description': 'Gera seções de peças de Direito Público para procuradorias municipais',
                'agent_type': 'generator',
                'system_prompt': PROMPT_PROCURADORIA,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'gerador_divida_ativa',
                'name': 'Verus.AI — Gerador Dívida Ativa Municipal',
                'description': 'Gera seções de peças de execução fiscal e cobrança de dívida ativa municipal',
                'agent_type': 'generator',
                'system_prompt': PROMPT_DIVIDA_ATIVA,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'gerador_licitacoes',
                'name': 'Verus.AI — Gerador Licitações e Contratos',
                'description': 'Gera minutas e pareceres em licitações e contratos administrativos',
                'agent_type': 'generator',
                'system_prompt': PROMPT_LICITACOES,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'validador_procuradoria',
                'name': 'Verus.AI — Validador Jurídico Procuradoria',
                'description': 'Valida peças jurídicas e administrativas da procuradoria',
                'agent_type': 'validator',
                'system_prompt': PROMPT_VALIDADOR,
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
                defaults={
                    'description': bp_data['description'],
                    'version': bp_data['version'],
                    'legal_basis': bp_data['legal_basis'],
                    'primary_color': bp_data['primary_color'],
                    'secondary_color': bp_data['secondary_color'],
                    'cover_title': bp_data['cover_title'],
                    'cover_page_enabled': True,
                    'cover_subtitle': bp_data['description'],
                    'organization_name': 'Procuradoria Geral do Município',
                    'organization_acronym': 'PGM',
                    'pdf_font_family': 'Times New Roman',
                    'pdf_font_size': '12pt',
                    'pdf_line_height': '1.5',
                    'pdf_text_align': 'justify',
                    'pdf_paragraph_indent': '1.25cm',
                    'is_active': True,  # ← ATIVO por padrão
                    'is_default': True,
                }
            )

            if not created and force:
                blueprint.description = bp_data['description']
                blueprint.primary_color = bp_data['primary_color']
                blueprint.is_active = True
                blueprint.save()
                blueprint.sections.all().delete()
                created = True

            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)

            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])

            if not blueprint.is_active:
                blueprint.is_active = True
                blueprint.save(update_fields=['is_active'])

            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {blueprint.name}')

            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_procuradoria')
                validador = agentes.get('validador_procuradoria')
                gerador = agentes.get(agente_key)
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
                            'generator_agent': gerador,
                            'validator_agent': validador,
                            'section_fields': sec.get('fields', []),
                            'is_active': True,
                        }
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
