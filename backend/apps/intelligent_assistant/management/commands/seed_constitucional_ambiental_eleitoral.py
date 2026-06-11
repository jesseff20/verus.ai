"""
Seed Constitucional, Ambiental e Eleitoral — Verus.AI.
Cria categorias, tipos de documento, agente especializado e blueprints.

Uso:
    python manage.py seed_constitucional_ambiental_eleitoral
    python manage.py seed_constitucional_ambiental_eleitoral --force
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
        'code': 'constitucional',
        'name': 'Constitucional',
        'description': 'Peças jurídicas de Direito Constitucional e controle de constitucionalidade',
        'display_order': 16,
    },
    {
        'code': 'ambiental',
        'name': 'Ambiental',
        'description': 'Peças jurídicas de Direito Ambiental e tutela do meio ambiente',
        'display_order': 17,
    },
    {
        'code': 'eleitoral',
        'name': 'Eleitoral',
        'description': 'Peças jurídicas de Direito Eleitoral e processo eleitoral',
        'display_order': 18,
    },
]

TIPOS_DOCUMENTO = [
    # === CONSTITUCIONAL ===
    {
        'code': 'adi',
        'name': 'Ação Direta de Inconstitucionalidade',
        'short_name': 'ADI',
        'description': 'Ação de controle concentrado para declarar a inconstitucionalidade de lei ou ato normativo',
        'category': 'constitucional',
        'icon': 'Scale',
        'color': '#1D4ED8',
        'legal_basis': 'CF/1988, art. 102, I, a; Lei 9.868/1999',
        'display_order': 1,
    },
    {
        'code': 'adpf',
        'name': 'Arguição de Descumprimento de Preceito Fundamental',
        'short_name': 'ADPF',
        'description': 'Ação para evitar ou reparar lesão a preceito fundamental decorrente de ato do Poder Público',
        'category': 'constitucional',
        'icon': 'Shield',
        'color': '#1D4ED8',
        'legal_basis': 'CF/1988, art. 102, §1º; Lei 9.882/1999',
        'display_order': 2,
    },
    {
        'code': 'habeas_data',
        'name': 'Habeas Data',
        'short_name': 'Habeas Data',
        'description': 'Ação constitucional para assegurar acesso ou retificação de informações pessoais em bancos de dados',
        'category': 'constitucional',
        'icon': 'Database',
        'color': '#7C3AED',
        'legal_basis': 'CF/1988, art. 5º, LXXII; Lei 9.507/1997',
        'display_order': 3,
    },
    {
        'code': 'mandado_injuncao',
        'name': 'Mandado de Injunção',
        'short_name': 'Mand. Injunção',
        'description': 'Ação para suprir omissão legislativa que impede o exercício de direito constitucional',
        'category': 'constitucional',
        'icon': 'FileWarning',
        'color': '#B45309',
        'legal_basis': 'CF/1988, art. 5º, LXXI; Lei 13.300/2016',
        'display_order': 4,
    },
    {
        'code': 'acao_popular',
        'name': 'Ação Popular',
        'short_name': 'Ação Popular',
        'description': 'Ação constitucional para anular ato lesivo ao patrimônio público, moralidade administrativa e meio ambiente',
        'category': 'constitucional',
        'icon': 'Users',
        'color': '#059669',
        'legal_basis': 'CF/1988, art. 5º, LXXIII; Lei 4.717/1965',
        'display_order': 5,
    },
    {
        'code': 'reclamacao_constitucional',
        'name': 'Reclamação Constitucional',
        'short_name': 'Reclamação',
        'description': 'Instrumento para preservar a competência e garantir a autoridade das decisões do STF e STJ',
        'category': 'constitucional',
        'icon': 'AlertTriangle',
        'color': '#DC2626',
        'legal_basis': 'CF/1988, art. 102, I, l; CPC/2015, arts. 988-993',
        'display_order': 6,
    },
    # === AMBIENTAL ===
    {
        'code': 'acao_civil_publica',
        'name': 'Ação Civil Pública Ambiental',
        'short_name': 'ACP Ambiental',
        'description': 'Ação coletiva para responsabilização por danos ao meio ambiente',
        'category': 'ambiental',
        'icon': 'TreePine',
        'color': '#15803D',
        'legal_basis': 'CF/1988, art. 225; Lei 7.347/1985; Lei 6.938/1981',
        'display_order': 1,
    },
    {
        'code': 'tac_ambiental',
        'name': 'TAC Ambiental',
        'short_name': 'TAC Ambiental',
        'description': 'Termo de Ajustamento de Conduta em matéria ambiental',
        'category': 'ambiental',
        'icon': 'Handshake',
        'color': '#16A34A',
        'legal_basis': 'Lei 7.347/1985, art. 5º, §6º; Lei 6.938/1981',
        'display_order': 2,
    },
    {
        'code': 'acao_dano_ambiental',
        'name': 'Ação de Dano Ambiental',
        'short_name': 'Dano Ambiental',
        'description': 'Ação indenizatória por dano ambiental com responsabilidade objetiva',
        'category': 'ambiental',
        'icon': 'Leaf',
        'color': '#166534',
        'legal_basis': 'CF/1988, art. 225, §3º; Lei 6.938/1981, art. 14, §1º',
        'display_order': 3,
    },
    # === ELEITORAL ===
    {
        'code': 'aije_eleitoral',
        'name': 'Ação de Investigação Judicial Eleitoral',
        'short_name': 'AIJE',
        'description': 'Ação para apurar abuso de poder econômico ou político nas eleições',
        'category': 'eleitoral',
        'icon': 'Search',
        'color': '#7C2D12',
        'legal_basis': 'LC 64/1990, art. 22; CE, art. 237',
        'display_order': 1,
    },
    {
        'code': 'aime_eleitoral',
        'name': 'Ação de Impugnação de Mandato Eletivo',
        'short_name': 'AIME',
        'description': 'Ação para impugnar mandato obtido por abuso de poder, corrupção ou fraude',
        'category': 'eleitoral',
        'icon': 'Ban',
        'color': '#991B1B',
        'legal_basis': 'CF/1988, art. 14, §10; CE, arts. 262-275',
        'display_order': 2,
    },
    {
        'code': 'recurso_eleitoral',
        'name': 'Recurso Eleitoral',
        'short_name': 'Recurso Eleitoral',
        'description': 'Recurso contra decisão de juízo eleitoral de primeira instância',
        'category': 'eleitoral',
        'icon': 'ArrowUpCircle',
        'color': '#B45309',
        'legal_basis': 'CE, arts. 265-282; Resolução TSE',
        'display_order': 3,
    },
    {
        'code': 'impugnacao_registro_candidatura',
        'name': 'Impugnação de Candidatura',
        'short_name': 'AIRC',
        'description': 'Ação para impugnar registro de candidatura por inelegibilidade ou irregularidade',
        'category': 'eleitoral',
        'icon': 'UserX',
        'color': '#DC2626',
        'legal_basis': 'LC 64/1990, arts. 3º-16; CE, art. 97',
        'display_order': 4,
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
- NUNCA afirme que tese é "pacífica" sem fonte verificável
- Dado faltante: [INFORMAÇÃO NECESSÁRIA: descrição]
- Jurisprudência não verificada: [PESQUISAR JURISPRUDÊNCIA: tema]
- Conteúdo inferido: [SUGESTÃO DA IA - VERIFICAR COM ADVOGADO]
- Todo documento DEVE terminar com: "⚠️ AVISO: Esta minuta foi gerada por IA e requer revisão obrigatória por advogado habilitado perante a OAB."
"""

PROMPT_GERADOR_CONSTITUCIONAL = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Constitucional brasileiro.

LEGISLAÇÃO VIGENTE:
- CF/1988, com especial atenção ao controle de constitucionalidade (arts. 97, 102-103)
- Lei 9.868/1999 (ADI e ADC), Lei 9.882/1999 (ADPF)
- Lei 13.300/2016 (Mandado de Injunção)
- Lei 9.507/1997 (Habeas Data)
- Lei 4.717/1965 (Ação Popular)
- CPC/2015, arts. 988-993 (Reclamação)

REGRAS:
1. Controle concentrado: legitimidade restrita (CF art. 103)
2. Cláusula de reserva de plenário (CF art. 97; Súmula Vinculante 10)
3. ADI/ADPF: efeitos erga omnes e vinculante
4. Mandado de Injunção: posição concretista (STF)
5. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_AMBIENTAL = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Ambiental brasileiro.

LEGISLAÇÃO VIGENTE:
- CF/1988, art. 225 (direito ao meio ambiente ecologicamente equilibrado)
- Lei 6.938/1981 (Política Nacional do Meio Ambiente)
- Lei 7.347/1985 (Ação Civil Pública)
- Lei 9.605/1998 (Crimes Ambientais)
- Lei 12.651/2012 (Código Florestal)
- Princípios: prevenção, precaução, poluidor-pagador, reparação integral

REGRAS:
1. Responsabilidade objetiva por dano ambiental (Lei 6.938/1981, art. 14, §1º)
2. Inversão do ônus da prova em matéria ambiental (STJ)
3. Dano ambiental: reparação in natura prioritária
4. Legitimidade ACP: MP, Defensoria, entes federativos, associações (Lei 7.347/1985, art. 5º)
5. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_ELEITORAL = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Eleitoral brasileiro.

LEGISLAÇÃO VIGENTE:
- CF/1988, arts. 14-16 (direitos políticos)
- Código Eleitoral (Lei 4.737/1965)
- LC 64/1990 (Inelegibilidades)
- LC 135/2010 (Lei da Ficha Limpa)
- Lei 9.504/1997 (Lei das Eleições)
- Resoluções do TSE aplicáveis ao pleito vigente

REGRAS:
1. Prazos eleitorais são decadenciais e improrrogáveis
2. AIJE: prazo até a diplomação (LC 64/1990, art. 22, XIV)
3. AIME: prazo de 15 dias após diplomação (CF art. 14, §10)
4. AIRC: prazo de 5 dias após publicação do edital (LC 64/1990, art. 3º)
5. Abuso de poder: econômico, político ou dos meios de comunicação
6. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'adi': 'gerador_constitucional',
    'adpf': 'gerador_constitucional',
    'habeas_data': 'gerador_constitucional',
    'mandado_injuncao': 'gerador_constitucional',
    'acao_popular': 'gerador_constitucional',
    'reclamacao_constitucional': 'gerador_constitucional',
    'acao_civil_publica': 'gerador_ambiental',
    'tac_ambiental': 'gerador_ambiental',
    'acao_dano_ambiental': 'gerador_ambiental',
    'aije_eleitoral': 'gerador_eleitoral',
    'aime_eleitoral': 'gerador_eleitoral',
    'recurso_eleitoral': 'gerador_eleitoral',
    'impugnacao_registro_candidatura': 'gerador_eleitoral',
}

# Áreas extras para blueprints com múltiplas categorias
AREAS_EXTRAS = {
    'habeas_data': ['digital_lgpd'],
    'acao_popular': ['administrativo'],
    'reclamacao_constitucional': ['recursos'],
    'acao_civil_publica': ['administrativo', 'consumidor'],
    'tac_ambiental': ['extrajudicial'],
    'recurso_eleitoral': ['recursos'],
}

BLUEPRINTS_DATA = [
    # =====================================================================
    # CONSTITUCIONAL
    # =====================================================================
    {
        'doc_type_code': 'adi',
        'name': 'Ação Direta de Inconstitucionalidade - Lei 9.868/1999',
        'description': 'Petição inicial de ADI para declaração de inconstitucionalidade de lei ou ato normativo',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 102, I, a; Lei 9.868/1999',
        'primary_color': '#1D4ED8',
        'secondary_color': '#3B82F6',
        'cover_title': 'Ação Direta de Inconstitucionalidade',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao Supremo Tribunal Federal',
                'instructions': (
                    'Redija o endereçamento ao Excelentíssimo Senhor Ministro Presidente do '
                    'Supremo Tribunal Federal, observando que a ADI é de competência originária '
                    'do STF (CF, art. 102, I, a). Indique o nome completo do requerente e sua '
                    'qualificação como legitimado ativo nos termos do art. 103 da Constituição Federal.'
                ),
                'fields': [
                    {'name': 'legitimado', 'label': 'Legitimado Ativo (art. 103, CF)', 'type': 'text', 'required': True},
                    {'name': 'tipo_legitimado', 'label': 'Tipo de Legitimado', 'type': 'select', 'required': True,
                     'options': ['Presidente da República', 'Mesa do Senado Federal', 'Mesa da Câmara dos Deputados',
                                 'Mesa de Assembleia Legislativa ou Câmara Legislativa do DF',
                                 'Governador de Estado ou do DF', 'Procurador-Geral da República',
                                 'Conselho Federal da OAB', 'Partido Político com representação no CN',
                                 'Confederação sindical ou entidade de classe de âmbito nacional']},
                ],
            },
            {
                'number': 2, 'key': 'legitimidade',
                'name': 'I - Da Legitimidade Ativa',
                'description': 'Demonstração da legitimidade do requerente para propor ADI',
                'instructions': (
                    'Demonstre a legitimidade ativa do requerente conforme o art. 103 da CF/1988, '
                    'especificando em qual inciso se enquadra. Se for legitimado especial (incisos IV, V e IX), '
                    'demonstre a pertinência temática entre o objeto da ADI e as finalidades institucionais '
                    'do requerente, conforme jurisprudência consolidada do STF.'
                ),
                'fields': [
                    {'name': 'pertinencia_tematica', 'label': 'Pertinência Temática (se legitimado especial)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'norma_impugnada',
                'name': 'II - Da Norma Impugnada',
                'description': 'Identificação completa da norma cuja inconstitucionalidade se alega',
                'instructions': (
                    'Identifique com precisão a norma impugnada: número da lei ou ato normativo, '
                    'data de publicação, ente federativo emissor, dispositivos específicos questionados '
                    '(artigos, parágrafos, incisos, alíneas). Transcreva integralmente o texto dos '
                    'dispositivos impugnados. Informe se a impugnação é total ou parcial. '
                    'Em caso de impugnação parcial, delimite exatamente os trechos questionados.'
                ),
                'fields': [
                    {'name': 'norma', 'label': 'Lei ou Ato Normativo Impugnado (número, data, ente)', 'type': 'text', 'required': True},
                    {'name': 'dispositivos', 'label': 'Dispositivos Impugnados (artigos específicos)', 'type': 'textarea', 'required': True},
                    {'name': 'impugnacao_tipo', 'label': 'Tipo de Impugnação', 'type': 'select', 'required': True, 'options': ['Total', 'Parcial']},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao_constitucional',
                'name': 'III - Da Fundamentação Constitucional',
                'description': 'Demonstração das violações constitucionais',
                'instructions': (
                    'Desenvolva a fundamentação jurídica demonstrando por que a norma impugnada viola '
                    'a Constituição Federal. Identifique os parâmetros constitucionais violados '
                    '(direitos fundamentais, princípios constitucionais, competências legislativas, '
                    'cláusulas pétreas). Analise a inconstitucionalidade formal (vício de competência, '
                    'procedimento legislativo) e/ou material (conteúdo incompatível com a CF). '
                    'Cite precedentes do STF em casos análogos, marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'parametros_violados', 'label': 'Dispositivos Constitucionais Violados', 'type': 'textarea', 'required': True},
                    {'name': 'tipo_inconstitucionalidade', 'label': 'Tipo de Inconstitucionalidade', 'type': 'select', 'required': True, 'options': ['Formal', 'Material', 'Formal e Material']},
                ],
            },
            {
                'number': 5, 'key': 'medida_cautelar',
                'name': 'IV - Do Pedido de Medida Cautelar',
                'description': 'Pedido de suspensão liminar da norma impugnada',
                'instructions': (
                    'Fundamente o pedido de medida cautelar nos termos do art. 10 da Lei 9.868/1999. '
                    'Demonstre o fumus boni iuris (plausibilidade jurídica do pedido) e o periculum in mora '
                    '(risco de dano irreparável pela manutenção da norma). Indique se a cautelar deve ter '
                    'eficácia ex nunc ou ex tunc. Se não houver pedido cautelar, indique expressamente.'
                ),
                'fields': [
                    {'name': 'pede_cautelar', 'label': 'Pede Medida Cautelar?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'urgencia', 'label': 'Fundamentos da Urgência', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido_final',
                'name': 'V - Do Pedido Final',
                'description': 'Pedidos de declaração de inconstitucionalidade',
                'instructions': (
                    'Formule os pedidos finais: (1) procedência da ADI para declarar a '
                    'inconstitucionalidade da norma impugnada, com efeitos erga omnes e eficácia '
                    'vinculante (CF, art. 102, §2º); (2) se for o caso, modulação dos efeitos temporais '
                    '(Lei 9.868/1999, art. 27); (3) se requerida, concessão de medida cautelar para '
                    'suspensão imediata da eficácia da norma; (4) notificação dos órgãos que editaram '
                    'a norma impugnada para prestar informações; (5) manifestação do Advogado-Geral da '
                    'União e do Procurador-Geral da República.'
                ),
                'fields': [
                    {'name': 'modulacao_efeitos', 'label': 'Requer Modulação de Efeitos (art. 27, Lei 9.868)?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim — efeitos ex nunc', 'Sim — efeitos a partir de data específica']},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'adpf',
        'name': 'Arguição de Descumprimento de Preceito Fundamental - Lei 9.882/1999',
        'description': 'Petição de ADPF para tutela de preceito fundamental violado por ato do Poder Público',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 102, §1º; Lei 9.882/1999',
        'primary_color': '#1D4ED8',
        'secondary_color': '#3B82F6',
        'cover_title': 'Arguição de Descumprimento de Preceito Fundamental',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao Supremo Tribunal Federal',
                'instructions': (
                    'Redija o endereçamento ao Excelentíssimo Senhor Ministro Presidente do '
                    'Supremo Tribunal Federal. Identifique o arguente com qualificação completa '
                    'e demonstre sua legitimidade nos termos do art. 2º, I, da Lei 9.882/1999 '
                    '(mesmos legitimados do art. 103 da CF).'
                ),
                'fields': [
                    {'name': 'arguente', 'label': 'Arguente (legitimado ativo)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'legitimidade',
                'name': 'I - Da Legitimidade Ativa',
                'description': 'Demonstração da legitimidade para propor ADPF',
                'instructions': (
                    'Demonstre a legitimidade ativa do arguente conforme o art. 2º, I, da Lei 9.882/1999 '
                    '(remissão ao art. 103 da CF). Se for legitimado especial, demonstre a pertinência '
                    'temática. Fundamente a subsidiariedade da ADPF (art. 4º, §1º, Lei 9.882/1999), '
                    'demonstrando a inexistência de outro meio eficaz para sanar a lesividade.'
                ),
                'fields': [
                    {'name': 'subsidiariedade', 'label': 'Demonstração de Subsidiariedade (inexistência de outro meio eficaz)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'preceito_fundamental',
                'name': 'II - Do Preceito Fundamental Violado',
                'description': 'Identificação do preceito fundamental objeto da arguição',
                'instructions': (
                    'Identifique com precisão o preceito fundamental que se alega violado. '
                    'Preceitos fundamentais incluem: direitos e garantias fundamentais (Título II da CF), '
                    'princípios constitucionais sensíveis (art. 34, VII), cláusulas pétreas (art. 60, §4º) '
                    'e princípios fundamentais da República (arts. 1º a 4º). Demonstre por que o dispositivo '
                    'constitucional invocado constitui preceito fundamental na jurisprudência do STF.'
                ),
                'fields': [
                    {'name': 'preceito', 'label': 'Preceito Fundamental Violado (dispositivo constitucional)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'ato_lesivo',
                'name': 'III - Do Ato Lesivo',
                'description': 'Identificação do ato do Poder Público que viola o preceito fundamental',
                'instructions': (
                    'Descreva detalhadamente o ato do Poder Público que descumpre o preceito fundamental: '
                    'pode ser lei ou ato normativo (inclusive municipal e anterior à CF/1988), ato '
                    'administrativo, decisão judicial ou omissão do Poder Público. Identifique o '
                    'órgão ou autoridade responsável. Se for ADPF incidental (art. 1º, parágrafo único, I), '
                    'indique o processo judicial de origem e a controvérsia constitucional relevante.'
                ),
                'fields': [
                    {'name': 'ato_impugnado', 'label': 'Ato do Poder Público Impugnado', 'type': 'textarea', 'required': True},
                    {'name': 'modalidade_adpf', 'label': 'Modalidade de ADPF', 'type': 'select', 'required': True, 'options': ['Autônoma (art. 1º, caput)', 'Incidental (art. 1º, parágrafo único, I)']},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'IV - Da Fundamentação',
                'description': 'Demonstração da violação ao preceito fundamental',
                'instructions': (
                    'Desenvolva a fundamentação jurídica demonstrando o nexo entre o ato lesivo e a '
                    'violação ao preceito fundamental. Aborde: a contrariedade direta ao preceito '
                    'constitucional, o estado de inconstitucionalidade gerado, a relevância do '
                    'fundamento da controvérsia constitucional (art. 1º da Lei 9.882/1999). '
                    'Cite precedentes do STF em ADPFs anteriores sobre temas análogos, marcando '
                    'como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'fundamentacao_detalhada', 'label': 'Fundamentação Jurídica Detalhada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedidos de tutela do preceito fundamental',
                'instructions': (
                    'Formule os pedidos: (1) concessão de medida liminar para suspender o ato lesivo '
                    '(art. 5º, Lei 9.882/1999), se cabível; (2) procedência da ADPF para declarar a '
                    'violação ao preceito fundamental, com fixação das condições e modo de interpretação '
                    'e aplicação do preceito (art. 10); (3) comunicação às autoridades responsáveis; '
                    '(4) efeitos erga omnes e vinculantes (art. 10, §3º).'
                ),
                'fields': [
                    {'name': 'pede_liminar', 'label': 'Pede Medida Liminar?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'habeas_data',
        'name': 'Habeas Data - Lei 9.507/1997',
        'description': 'Ação constitucional para acesso ou retificação de dados pessoais em registros públicos ou bancos de dados',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 5º, LXXII; Lei 9.507/1997',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Habeas Data',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo competente',
                'instructions': (
                    'Redija o endereçamento ao juízo competente conforme a autoridade coatora: '
                    'STF se envolver o Presidente, Mesas do Congresso ou Tribunal de Contas (CF art. 102, I, d); '
                    'STJ se envolver Ministro de Estado ou do próprio STJ (CF art. 105, I, b); '
                    'Justiça Federal se envolver autoridade federal; Justiça Estadual nos demais casos.'
                ),
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente', 'type': 'text', 'required': True},
                    {'name': 'autoridade_coatora', 'label': 'Autoridade ou Entidade Detentora dos Dados', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'I - Da Qualificação das Partes',
                'description': 'Identificação do impetrante e da autoridade coatora',
                'instructions': (
                    'Qualifique o impetrante com dados completos (nome, nacionalidade, estado civil, '
                    'profissão, CPF, RG, endereço). Identifique a autoridade coatora ou entidade '
                    'responsável pelo banco de dados (órgão público, entidade governamental ou de '
                    'caráter público — Lei 9.507/1997, art. 1º), com endereço para notificação.'
                ),
                'fields': [
                    {'name': 'impetrante_nome', 'label': 'Nome do Impetrante', 'type': 'text', 'required': True},
                    {'name': 'impetrante_cpf', 'label': 'CPF do Impetrante', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'informacoes_requeridas',
                'name': 'II - Das Informações Requeridas',
                'description': 'Especificação dos dados cujo acesso ou retificação se pretende',
                'instructions': (
                    'Especifique com clareza as informações cujo conhecimento ou retificação se pretende. '
                    'Se for habeas data para conhecimento (CF art. 5º, LXXII, a): descreva quais dados '
                    'pessoais constam no banco e cujo acesso foi negado. Se for habeas data para '
                    'retificação (CF art. 5º, LXXII, b): descreva os dados incorretos e a informação '
                    'correta que deve substituí-los. Pode ser também para anotação (Lei 9.507/1997, art. 7º, III).'
                ),
                'fields': [
                    {'name': 'finalidade', 'label': 'Finalidade do Habeas Data', 'type': 'select', 'required': True,
                     'options': ['Conhecimento de informações (art. 7º, I)', 'Retificação de dados (art. 7º, II)', 'Anotação de contestação ou explicação (art. 7º, III)']},
                    {'name': 'dados_especificos', 'label': 'Dados Pessoais Objeto da Ação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'recusa_administrativa',
                'name': 'III - Da Recusa Administrativa',
                'description': 'Comprovação da recusa ou omissão no fornecimento/retificação dos dados',
                'instructions': (
                    'Demonstre a recusa administrativa prévia, requisito de admissibilidade do habeas data '
                    '(Súmula 2 do STJ). Descreva o requerimento administrativo formulado, a data do '
                    'protocolo, o prazo de 10 dias para decisão sobre acesso ou 15 dias para retificação '
                    '(Lei 9.507/1997, arts. 2º e 4º) e a resposta negativa ou a omissão da autoridade. '
                    'Anexe comprovante do requerimento e da recusa/omissão.'
                ),
                'fields': [
                    {'name': 'data_requerimento', 'label': 'Data do Requerimento Administrativo', 'type': 'text', 'required': True},
                    {'name': 'resposta_obtida', 'label': 'Resposta Obtida (recusa expressa ou omissão)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'IV - Da Fundamentação',
                'description': 'Fundamentos constitucionais e legais do pedido',
                'instructions': (
                    'Fundamente o pedido no art. 5º, LXXII, da CF/1988 e na Lei 9.507/1997. '
                    'Aborde o direito constitucional à autodeterminação informativa, o direito de '
                    'acesso à informação pessoal e o direito de retificação de dados incorretos. '
                    'Se aplicável, relacione com a LGPD (Lei 13.709/2018) e o direito à proteção '
                    'de dados pessoais (CF art. 5º, LXXIX). Cite precedentes judiciais pertinentes, '
                    'marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'relacao_lgpd', 'label': 'Relação com a LGPD (se aplicável)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedidos de acesso ou retificação dos dados',
                'instructions': (
                    'Formule os pedidos: (1) concessão do habeas data para determinar que a autoridade '
                    'coatora forneça as informações ou proceda à retificação dos dados; '
                    '(2) notificação da autoridade coatora para prestar informações em 10 dias '
                    '(Lei 9.507/1997, art. 9º); (3) oitiva do Ministério Público; '
                    '(4) condenação em custas, se cabível. Indique o valor da causa.'
                ),
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'mandado_injuncao',
        'name': 'Mandado de Injunção - Lei 13.300/2016',
        'description': 'Ação para suprir omissão legislativa que inviabiliza direito constitucional',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 5º, LXXI; Lei 13.300/2016',
        'primary_color': '#B45309',
        'secondary_color': '#D97706',
        'cover_title': 'Mandado de Injunção',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo competente',
                'instructions': (
                    'Redija o endereçamento ao juízo competente conforme a autoridade ou órgão '
                    'responsável pela omissão: STF se a omissão for do Presidente, Congresso, '
                    'Câmara, Senado, TCU, Tribunal Superior ou do próprio STF (CF art. 102, I, q); '
                    'STJ se a omissão for de órgão, entidade ou autoridade federal (CF art. 105, I, h); '
                    'TSE, TRT e TM conforme a matéria.'
                ),
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente', 'type': 'text', 'required': True},
                    {'name': 'orgao_omisso', 'label': 'Órgão ou Autoridade Responsável pela Omissão', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'I - Da Qualificação',
                'description': 'Qualificação do impetrante',
                'instructions': (
                    'Qualifique o impetrante com dados completos. Se for mandado de injunção '
                    'individual (Lei 13.300/2016, art. 3º), identifique a pessoa titular do direito. '
                    'Se for mandado de injunção coletivo (art. 12), identifique o legitimado coletivo '
                    '(Ministério Público, partido político, organização sindical, entidade de classe, '
                    'Defensoria Pública) e demonstre a legitimidade.'
                ),
                'fields': [
                    {'name': 'impetrante_nome', 'label': 'Nome do Impetrante', 'type': 'text', 'required': True},
                    {'name': 'tipo_injuncao', 'label': 'Tipo de Mandado de Injunção', 'type': 'select', 'required': True, 'options': ['Individual', 'Coletivo']},
                ],
            },
            {
                'number': 3, 'key': 'direito_constitucional',
                'name': 'II - Do Direito Constitucional Inviabilizado',
                'description': 'Identificação do direito constitucional que não pode ser exercido',
                'instructions': (
                    'Identifique o direito constitucional, a liberdade ou a prerrogativa inerente à '
                    'nacionalidade, soberania ou cidadania cujo exercício está inviabilizado pela '
                    'ausência de norma regulamentadora (CF art. 5º, LXXI). Transcreva o dispositivo '
                    'constitucional que assegura o direito e demonstre que se trata de norma de '
                    'eficácia limitada, dependente de regulamentação infraconstitucional.'
                ),
                'fields': [
                    {'name': 'dispositivo_cf', 'label': 'Dispositivo Constitucional que Assegura o Direito', 'type': 'text', 'required': True},
                    {'name': 'direito_inviabilizado', 'label': 'Direito Inviabilizado pela Omissão', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'omissao_legislativa',
                'name': 'III - Da Omissão Legislativa',
                'description': 'Demonstração da mora legislativa',
                'instructions': (
                    'Demonstre a omissão normativa: (1) o mandamento constitucional de legislar '
                    '(dever de regulamentação); (2) a mora do Poder competente em editar a norma '
                    'regulamentadora; (3) o transcurso de prazo razoável sem a edição da norma. '
                    'Informe se já houve notificação anterior ao órgão omisso e qual foi o resultado. '
                    'Mencione se o STF já reconheceu a mora em casos análogos.'
                ),
                'fields': [
                    {'name': 'tempo_omissao', 'label': 'Tempo da Omissão (desde a promulgação da CF ou EC)', 'type': 'text', 'required': True},
                    {'name': 'houve_notificacao', 'label': 'Houve notificação prévia ao órgão omisso?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim']},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'IV - Da Fundamentação',
                'description': 'Fundamentos jurídicos do mandado de injunção',
                'instructions': (
                    'Fundamente no art. 5º, LXXI, da CF/1988 e na Lei 13.300/2016. Demonstre '
                    'que a falta de norma regulamentadora torna inviável o exercício do direito. '
                    'Aborde a posição concretista do STF, que autoriza o Judiciário a suprir a omissão '
                    'estabelecendo as condições para o exercício do direito (Lei 13.300/2016, art. 8º). '
                    'Cite precedentes em mandados de injunção paradigmáticos do STF, marcando como '
                    '[VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'efeitos_pretendidos', 'label': 'Efeitos Pretendidos', 'type': 'select', 'required': True,
                     'options': ['Inter partes (apenas ao impetrante)', 'Ultra partes / erga omnes (MI coletivo)']},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedidos do mandado de injunção',
                'instructions': (
                    'Formule os pedidos nos termos da Lei 13.300/2016: (1) reconhecimento da mora '
                    'legislativa; (2) concessão da injunção para determinar as condições de exercício '
                    'do direito, nos termos do art. 8º da Lei 13.300/2016; (3) fixação de prazo '
                    'razoável para que o órgão omisso edite a norma regulamentadora (art. 8º, I); '
                    '(4) subsidiariamente, que o Judiciário estabeleça as condições para o exercício '
                    'do direito até a superveniência da norma (art. 8º, II). '
                    'Indique o valor da causa.'
                ),
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_popular',
        'name': 'Ação Popular - Lei 4.717/1965',
        'description': 'Ação constitucional para anular ato lesivo ao patrimônio público ou à moralidade administrativa',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 5º, LXXIII; Lei 4.717/1965',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Ação Popular',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo competente',
                'instructions': (
                    'Redija o endereçamento ao juízo competente. A competência é determinada pela '
                    'origem do ato impugnado: Justiça Federal para atos de autoridade federal ou '
                    'envolvendo patrimônio da União; Justiça Estadual nos demais casos. Considere '
                    'a prerrogativa de foro se o ato envolver autoridades com foro privilegiado.'
                ),
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao_cidadao',
                'name': 'I - Da Qualificação do Cidadão Autor',
                'description': 'Identificação e comprovação da cidadania do autor',
                'instructions': (
                    'Qualifique o autor popular com dados completos. A legitimidade ativa na ação popular '
                    'é exclusiva do cidadão (CF art. 5º, LXXIII), devendo-se comprovar a cidadania '
                    'com título de eleitor (Lei 4.717/1965, art. 1º, §3º). Qualifique os réus: a '
                    'autoridade que praticou o ato, a pessoa jurídica de direito público ou privado '
                    'beneficiada, e eventuais terceiros beneficiários (Lei 4.717/1965, art. 6º).'
                ),
                'fields': [
                    {'name': 'autor_nome', 'label': 'Nome do Cidadão Autor', 'type': 'text', 'required': True},
                    {'name': 'titulo_eleitor', 'label': 'Número do Título de Eleitor', 'type': 'text', 'required': True},
                    {'name': 'autoridade_re', 'label': 'Autoridade Ré (que praticou o ato)', 'type': 'text', 'required': True},
                    {'name': 'entidade_re', 'label': 'Pessoa Jurídica Ré', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'ato_lesivo',
                'name': 'II - Do Ato Lesivo',
                'description': 'Descrição do ato administrativo lesivo ao patrimônio público',
                'instructions': (
                    'Descreva detalhadamente o ato administrativo impugnado: qual é o ato, quando '
                    'foi praticado, por qual autoridade, em que circunstâncias. Enquadre nos vícios '
                    'previstos na Lei 4.717/1965, art. 2º: incompetência, vício de forma, ilegalidade '
                    'do objeto, inexistência de motivos ou desvio de finalidade. '
                    'Demonstre a lesividade do ato.'
                ),
                'fields': [
                    {'name': 'descricao_ato', 'label': 'Descrição do Ato Impugnado', 'type': 'textarea', 'required': True},
                    {'name': 'vicio', 'label': 'Vício do Ato (art. 2º, Lei 4.717/1965)', 'type': 'select', 'required': True,
                     'options': ['Incompetência', 'Vício de forma', 'Ilegalidade do objeto', 'Inexistência dos motivos', 'Desvio de finalidade']},
                ],
            },
            {
                'number': 4, 'key': 'dano_patrimonio',
                'name': 'III - Do Dano ao Patrimônio Público',
                'description': 'Demonstração do dano ou ameaça de dano ao patrimônio público',
                'instructions': (
                    'Demonstre o dano efetivo ou potencial ao patrimônio público, à moralidade '
                    'administrativa, ao meio ambiente ou ao patrimônio histórico e cultural '
                    '(CF art. 5º, LXXIII). Quantifique o prejuízo ao erário, se possível. '
                    'Se for lesão à moralidade administrativa, demonstre a violação dos princípios '
                    'do art. 37 da CF (legalidade, impessoalidade, moralidade, publicidade, eficiência). '
                    'Não é necessário dano econômico para lesão à moralidade.'
                ),
                'fields': [
                    {'name': 'tipo_dano', 'label': 'Tipo de Lesão', 'type': 'select', 'required': True,
                     'options': ['Patrimônio público (erário)', 'Moralidade administrativa', 'Meio ambiente', 'Patrimônio histórico e cultural']},
                    {'name': 'estimativa_dano', 'label': 'Estimativa do Dano (se quantificável)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'IV - Da Fundamentação',
                'description': 'Fundamentos constitucionais e legais',
                'instructions': (
                    'Fundamente na CF/1988, art. 5º, LXXIII, e na Lei 4.717/1965. Demonstre a '
                    'nulidade ou anulabilidade do ato nos termos dos arts. 2º a 4º da Lei 4.717/1965. '
                    'Se envolver improbidade administrativa, relacione com a Lei 8.429/1992. '
                    'Se envolver licitação, cite a Lei 14.133/2021. Cite precedentes judiciais '
                    'pertinentes, marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'fundamentacao_legal', 'label': 'Fundamentação Legal Detalhada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedidos de anulação e reparação',
                'instructions': (
                    'Formule os pedidos: (1) concessão de medida liminar para suspender o ato lesivo '
                    '(Lei 4.717/1965, art. 5º, §4º); (2) citação dos réus; (3) procedência da ação '
                    'para declarar a nulidade do ato impugnado; (4) condenação dos réus à reparação '
                    'dos danos ao patrimônio público; (5) condenação em custas e honorários '
                    '(o autor popular é isento de custas — art. 5º, LXXIII, CF). Indique o valor da causa.'
                ),
                'fields': [
                    {'name': 'pede_liminar', 'label': 'Pede Medida Liminar?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'reclamacao_constitucional',
        'name': 'Reclamação Constitucional - CPC/2015',
        'description': 'Instrumento para preservar competência e autoridade das decisões do STF e STJ',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 102, I, l; CPC/2015, arts. 988-993',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Reclamação Constitucional',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao tribunal competente',
                'instructions': (
                    'Redija o endereçamento ao tribunal competente para julgar a reclamação: '
                    'STF para preservar sua competência ou garantir autoridade de suas decisões '
                    '(CF art. 102, I, l); STJ para suas decisões (CF art. 105, I, f); ou tribunal '
                    'de segundo grau nos demais casos (CPC art. 988, §1º). Identifique o reclamante '
                    'com qualificação completa.'
                ),
                'fields': [
                    {'name': 'tribunal', 'label': 'Tribunal Competente', 'type': 'select', 'required': True, 'options': ['STF', 'STJ', 'Tribunal de Justiça', 'TRF']},
                    {'name': 'reclamante', 'label': 'Nome do Reclamante', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'decisao_descumprida',
                'name': 'I - Da Decisão Descumprida',
                'description': 'Identificação da decisão cuja autoridade se busca garantir',
                'instructions': (
                    'Identifique com precisão a decisão judicial cuja autoridade se busca garantir: '
                    'número do processo, relator, órgão julgador, data do julgamento, ementa e '
                    'dispositivo. Pode ser: (1) Súmula Vinculante do STF; (2) decisão proferida em '
                    'controle concentrado de constitucionalidade; (3) acórdão em recurso repetitivo; '
                    '(4) precedente qualificado (CPC art. 988, III e IV). '
                    'Transcreva o trecho relevante da decisão paradigma.'
                ),
                'fields': [
                    {'name': 'decisao_paradigma', 'label': 'Decisão Paradigma (número, relator, tribunal)', 'type': 'textarea', 'required': True},
                    {'name': 'hipotese_reclamacao', 'label': 'Hipótese de Cabimento (CPC art. 988)', 'type': 'select', 'required': True,
                     'options': ['Preservar competência do tribunal (inciso I)', 'Garantir autoridade de decisão do tribunal (inciso II)',
                                 'Garantir observância de Súmula Vinculante ou precedente de controle concentrado (inciso III)',
                                 'Garantir observância de acórdão em IRDR ou recurso repetitivo (inciso IV)']},
                ],
            },
            {
                'number': 3, 'key': 'ato_reclamado',
                'name': 'II - Do Ato Reclamado',
                'description': 'Identificação do ato judicial ou administrativo que descumpre a decisão',
                'instructions': (
                    'Descreva o ato reclamado que afronta a decisão paradigma: decisão judicial de '
                    'instância inferior, ato administrativo ou qualquer manifestação que contrarie '
                    'o entendimento fixado. Identifique o órgão ou autoridade que praticou o ato, '
                    'o processo de origem, a data do ato reclamado. Demonstre a aderência estrita '
                    'entre a situação do caso concreto e o precedente vinculante invocado '
                    '(CPC art. 988, §4º).'
                ),
                'fields': [
                    {'name': 'ato_descrito', 'label': 'Descrição do Ato Reclamado', 'type': 'textarea', 'required': True},
                    {'name': 'processo_origem', 'label': 'Processo de Origem do Ato Reclamado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'III - Da Fundamentação',
                'description': 'Demonstração do descumprimento',
                'instructions': (
                    'Fundamente nos arts. 988 a 993 do CPC/2015. Demonstre com clareza o '
                    'descumprimento: compare o entendimento fixado na decisão paradigma com o ato '
                    'reclamado, demonstrando a contradição ponto a ponto. Se for descumprimento de '
                    'Súmula Vinculante, demonstre que o ato administrativo ou decisão judicial contraria '
                    'ou aplica indevidamente a Súmula. Comprove o esgotamento das instâncias ordinárias '
                    'se exigido (CPC art. 988, §5º, II). Cite precedentes do tribunal em reclamações '
                    'análogas, marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'esgotamento_instancias', 'label': 'Houve esgotamento das instâncias ordinárias?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não aplicável']},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos da reclamação',
                'instructions': (
                    'Formule os pedidos: (1) concessão de medida liminar para suspender o ato '
                    'reclamado e o processo em que foi proferido (CPC art. 989, II); '
                    '(2) procedência da reclamação para cassar o ato reclamado; '
                    '(3) determinação para que a autoridade reclamada observe a decisão paradigma; '
                    '(4) requisição de informações à autoridade reclamada (CPC art. 989, I); '
                    '(5) manifestação do Ministério Público.'
                ),
                'fields': [
                    {'name': 'pede_liminar', 'label': 'Pede Medida Liminar para Suspensão?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                ],
            },
        ],
    },
    # =====================================================================
    # AMBIENTAL
    # =====================================================================
    {
        'doc_type_code': 'acao_civil_publica',
        'name': 'Ação Civil Pública Ambiental - Lei 7.347/1985',
        'description': 'Ação coletiva para responsabilização e reparação de danos ao meio ambiente',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 225; Lei 7.347/1985; Lei 6.938/1981',
        'primary_color': '#15803D',
        'secondary_color': '#22C55E',
        'cover_title': 'Ação Civil Pública Ambiental',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo competente',
                'instructions': (
                    'Redija o endereçamento ao juízo competente para processar e julgar a ACP ambiental. '
                    'A competência é do foro do local do dano (Lei 7.347/1985, art. 2º). '
                    'Se o dano afetar área de competência federal (terras da União, unidades de conservação '
                    'federais, rios interestaduais), o juízo será a Vara Federal com competência ambiental.'
                ),
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente (foro do local do dano)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'legitimidade',
                'name': 'I - Da Legitimidade Ativa',
                'description': 'Demonstração da legitimidade para propor a ACP',
                'instructions': (
                    'Demonstre a legitimidade ativa do autor conforme o art. 5º da Lei 7.347/1985: '
                    'Ministério Público, Defensoria Pública, União/Estados/Municípios/DF, '
                    'autarquias, empresas públicas, fundações, sociedades de economia mista, '
                    'ou associações constituídas há pelo menos 1 ano e que incluam a proteção '
                    'ambiental entre suas finalidades institucionais (art. 5º, V). '
                    'Se Ministério Público, mencione o art. 129, III, da CF.'
                ),
                'fields': [
                    {'name': 'autor', 'label': 'Legitimado Ativo', 'type': 'text', 'required': True},
                    {'name': 'tipo_legitimado', 'label': 'Tipo de Legitimado', 'type': 'select', 'required': True,
                     'options': ['Ministério Público', 'Defensoria Pública', 'Ente Federativo', 'Autarquia/Fundação', 'Associação Civil']},
                    {'name': 'reu', 'label': 'Réu (poluidor/degradador)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'fatos',
                'name': 'II - Dos Fatos',
                'description': 'Narração detalhada dos fatos que configuram o dano ambiental',
                'instructions': (
                    'Narre detalhadamente os fatos: qual a atividade ou conduta lesiva ao meio ambiente, '
                    'quando ocorreu ou está ocorrendo, onde se localiza (coordenadas geográficas, '
                    'se possível), qual a extensão territorial afetada. Descreva o contexto: '
                    'existência de licenciamento ambiental, autos de infração, inquérito civil, '
                    'procedimentos administrativos anteriores. Identifique testemunhas e documentos.'
                ),
                'fields': [
                    {'name': 'local_dano', 'label': 'Local do Dano Ambiental', 'type': 'text', 'required': True},
                    {'name': 'descricao_fatos', 'label': 'Descrição Detalhada dos Fatos', 'type': 'textarea', 'required': True},
                    {'name': 'inquerito_civil', 'label': 'Inquérito Civil ou Procedimento Administrativo (se houver)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'dano_ambiental',
                'name': 'III - Do Dano Ambiental',
                'description': 'Caracterização técnica do dano ambiental',
                'instructions': (
                    'Caracterize o dano ambiental com dados técnicos: desmatamento (área em hectares), '
                    'poluição hídrica (corpos d\'água afetados, parâmetros violados), contaminação do solo, '
                    'emissões atmosféricas, destruição de fauna/flora, área de preservação permanente '
                    'ou reserva legal afetada. Classifique: dano patrimonial ambiental e/ou '
                    'extrapatrimonial (dano moral coletivo). Mencione laudo técnico ou perícia '
                    'ambiental que comprove o dano.'
                ),
                'fields': [
                    {'name': 'tipo_dano', 'label': 'Tipo de Dano Ambiental', 'type': 'select', 'required': True,
                     'options': ['Desmatamento/Supressão vegetal', 'Poluição hídrica', 'Contaminação do solo',
                                 'Poluição atmosférica', 'Dano à fauna', 'Dano a APP ou Reserva Legal', 'Múltiplos danos']},
                    {'name': 'extensao_dano', 'label': 'Extensão/Quantificação do Dano', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'IV - Da Fundamentação',
                'description': 'Fundamentos constitucionais e legais',
                'instructions': (
                    'Fundamente no art. 225 da CF/1988 (direito ao meio ambiente ecologicamente '
                    'equilibrado), na Lei 6.938/1981 (responsabilidade objetiva — art. 14, §1º), '
                    'na Lei 7.347/1985 (ACP) e legislação específica aplicável (Código Florestal, '
                    'Lei de Crimes Ambientais, resoluções CONAMA). Aborde os princípios: poluidor-pagador, '
                    'prevenção, precaução, reparação integral. Demonstre que a responsabilidade é objetiva '
                    '(independe de culpa) e solidária entre todos os degradadores. '
                    'Cite precedentes do STJ, marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'legislacao_especifica', 'label': 'Legislação Específica Violada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedidos_tutela',
                'name': 'V - Dos Pedidos de Tutela de Urgência',
                'description': 'Pedidos de medida liminar ou tutela antecipada',
                'instructions': (
                    'Formule os pedidos de tutela de urgência (Lei 7.347/1985, art. 12): '
                    '(1) cessação imediata da atividade lesiva; (2) embargo de obra ou atividade; '
                    '(3) interdição de estabelecimento; (4) imposição de obrigação de fazer '
                    '(medidas de contenção do dano) sob pena de multa diária (astreintes). '
                    'Demonstre a probabilidade do direito (fumus boni iuris) e o perigo de dano '
                    'irreversível ao meio ambiente (periculum in mora).'
                ),
                'fields': [
                    {'name': 'medidas_urgentes', 'label': 'Medidas de Urgência Requeridas', 'type': 'textarea', 'required': True},
                    {'name': 'valor_multa_diaria', 'label': 'Valor Sugerido para Multa Diária (astreintes)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 7, 'key': 'pedido_final',
                'name': 'VI - Do Pedido Final',
                'description': 'Pedidos definitivos de reparação e indenização',
                'instructions': (
                    'Formule os pedidos finais: (1) condenação à reparação in natura do meio ambiente '
                    'degradado (obrigação de fazer — restauração ecológica); (2) subsidiariamente, '
                    'indenização pecuniária correspondente ao dano ambiental (reversão ao Fundo de '
                    'Defesa dos Direitos Difusos — Lei 7.347/1985, art. 13); (3) indenização por dano '
                    'moral coletivo; (4) proibição de reiterar a conduta lesiva (obrigação de não fazer); '
                    '(5) condenação em custas e honorários; (6) inversão do ônus da prova em matéria '
                    'ambiental. Indique o valor da causa.'
                ),
                'fields': [
                    {'name': 'valor_indenizacao', 'label': 'Valor Estimado da Indenização Ambiental', 'type': 'text', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'tac_ambiental',
        'name': 'TAC Ambiental - Termo de Ajustamento de Conduta',
        'description': 'Acordo extrajudicial para adequação de condutas ambientais',
        'version': '1.0',
        'legal_basis': 'Lei 7.347/1985, art. 5º, §6º; Lei 6.938/1981',
        'primary_color': '#16A34A',
        'secondary_color': '#4ADE80',
        'cover_title': 'Termo de Ajustamento de Conduta Ambiental',
        'sections': [
            {
                'number': 1, 'key': 'identificacao_partes',
                'name': 'Identificação das Partes',
                'description': 'Identificação do órgão público e do compromissário',
                'instructions': (
                    'Identifique as partes do TAC: (1) o órgão público legitimado que celebra o '
                    'acordo (Ministério Público, órgão ambiental federal/estadual/municipal, '
                    'Defensoria Pública); (2) o compromissário (pessoa física ou jurídica que assume '
                    'as obrigações). Qualifique ambos com dados completos: razão social, CNPJ/CPF, '
                    'endereço, representante legal. Fundamente na Lei 7.347/1985, art. 5º, §6º '
                    '(compromisso de ajustamento de conduta com eficácia de título executivo extrajudicial).'
                ),
                'fields': [
                    {'name': 'orgao_publico', 'label': 'Órgão Público Compromitente', 'type': 'text', 'required': True},
                    {'name': 'compromissario', 'label': 'Compromissário (empresa/pessoa)', 'type': 'text', 'required': True},
                    {'name': 'cnpj_cpf_compromissario', 'label': 'CNPJ/CPF do Compromissário', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'objeto',
                'name': 'I - Do Objeto',
                'description': 'Descrição do objeto do TAC e do dano ambiental a ser reparado',
                'instructions': (
                    'Descreva detalhadamente o objeto do TAC: qual o dano ambiental ou irregularidade '
                    'a ser sanada, qual a atividade causadora, localização da área afetada, '
                    'extensão do dano. Mencione o inquérito civil, auto de infração ou procedimento '
                    'administrativo que originou o TAC. Cite a legislação ambiental violada '
                    '(Código Florestal, CONAMA, lei estadual/municipal).'
                ),
                'fields': [
                    {'name': 'descricao_objeto', 'label': 'Descrição do Dano/Irregularidade', 'type': 'textarea', 'required': True},
                    {'name': 'procedimento_origem', 'label': 'Procedimento de Origem (IC, auto de infração)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'obrigacoes',
                'name': 'II - Das Obrigações',
                'description': 'Obrigações de fazer e de não fazer assumidas pelo compromissário',
                'instructions': (
                    'Redija as cláusulas com as obrigações de fazer e de não fazer: '
                    '(1) obrigações de recuperação ambiental (PRAD — Plano de Recuperação de Área Degradada); '
                    '(2) obrigações de adequação da atividade à legislação ambiental; '
                    '(3) obrigações de monitoramento e relatórios periódicos; '
                    '(4) obrigações de não fazer (cessação de atividade lesiva, vedação de supressão vegetal). '
                    'Cada obrigação deve ser clara, específica e mensurável.'
                ),
                'fields': [
                    {'name': 'obrigacoes_fazer', 'label': 'Obrigações de Fazer', 'type': 'textarea', 'required': True},
                    {'name': 'obrigacoes_nao_fazer', 'label': 'Obrigações de Não Fazer', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'prazos',
                'name': 'III - Dos Prazos',
                'description': 'Prazos para cumprimento de cada obrigação',
                'instructions': (
                    'Estabeleça prazos claros e razoáveis para o cumprimento de cada obrigação: '
                    'datas de início e término, marcos intermediários para obrigações complexas, '
                    'prazo para apresentação do PRAD, prazo para obtenção de licenciamento ambiental, '
                    'periodicidade dos relatórios de monitoramento. Preveja hipóteses de prorrogação '
                    'justificada e o procedimento para solicitá-la.'
                ),
                'fields': [
                    {'name': 'prazo_cumprimento', 'label': 'Prazo Geral de Cumprimento', 'type': 'text', 'required': True},
                    {'name': 'cronograma', 'label': 'Cronograma Detalhado por Obrigação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'multas',
                'name': 'IV - Das Multas e Penalidades',
                'description': 'Cominações pelo descumprimento das obrigações',
                'instructions': (
                    'Estabeleça as penalidades pelo descumprimento: multa diária (astreintes) por '
                    'obrigação de fazer descumprida, multa por evento para obrigação de não fazer '
                    'violada, multa pelo atraso na apresentação de relatórios. Defina os valores '
                    'proporcionais à gravidade do descumprimento e à capacidade econômica do '
                    'compromissário. Preveja a execução do título extrajudicial em caso de '
                    'descumprimento (CPC arts. 784 e 786).'
                ),
                'fields': [
                    {'name': 'multa_diaria', 'label': 'Valor da Multa Diária por Descumprimento', 'type': 'text', 'required': True},
                    {'name': 'multa_evento', 'label': 'Multa por Evento (descumprimento de não fazer)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'disposicoes_gerais',
                'name': 'V - Das Disposições Gerais',
                'description': 'Cláusulas gerais, fiscalização e vigência',
                'instructions': (
                    'Redija as disposições gerais: (1) o TAC tem eficácia de título executivo '
                    'extrajudicial (Lei 7.347/1985, art. 5º, §6º); (2) mecanismo de fiscalização '
                    'do cumprimento (vistoria pelo órgão ambiental, relatórios periódicos); '
                    '(3) vigência do TAC e condições de encerramento; (4) arquivamento do inquérito '
                    'civil ou procedimento administrativo condicionado ao cumprimento integral; '
                    '(5) foro para dirimir controvérsias; (6) número de vias e assinaturas.'
                ),
                'fields': [
                    {'name': 'vigencia', 'label': 'Vigência do TAC', 'type': 'text', 'required': True},
                    {'name': 'foro', 'label': 'Foro para Controvérsias', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_dano_ambiental',
        'name': 'Ação de Dano Ambiental - Responsabilidade Objetiva',
        'description': 'Ação indenizatória individual ou coletiva por dano ambiental com responsabilidade civil objetiva',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 225, §3º; Lei 6.938/1981, art. 14, §1º',
        'primary_color': '#166534',
        'secondary_color': '#22C55E',
        'cover_title': 'Ação de Dano Ambiental',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo competente',
                'instructions': (
                    'Redija o endereçamento ao juízo competente. A competência é do foro do local '
                    'do dano ambiental. Se o autor for particular lesado, endereçar à Vara Cível '
                    'ou Vara Ambiental (se houver). Vara Federal se a União, autarquia federal ou '
                    'empresa pública federal for parte, ou se envolver terras da União.'
                ),
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Competente', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'I - Da Qualificação das Partes',
                'description': 'Qualificação do autor e do réu (poluidor)',
                'instructions': (
                    'Qualifique o autor (pessoa física ou jurídica lesada pelo dano ambiental) com '
                    'dados completos. Qualifique o réu (poluidor direto ou indireto, conforme art. 3º, IV, '
                    'da Lei 6.938/1981) com razão social, CNPJ, endereço da sede e do empreendimento. '
                    'Se houver múltiplos degradadores, qualifique todos (responsabilidade solidária).'
                ),
                'fields': [
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu (poluidor)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'fatos',
                'name': 'II - Dos Fatos',
                'description': 'Narração dos fatos do dano ambiental',
                'instructions': (
                    'Narre detalhadamente os fatos: a atividade ou conduta que causou o dano ambiental, '
                    'quando e onde ocorreu, a extensão da degradação, os bens ambientais afetados '
                    '(água, solo, ar, flora, fauna, paisagem). Descreva os prejuízos sofridos pelo '
                    'autor em decorrência do dano ambiental (perda de produtividade agrícola, '
                    'comprometimento de fonte de água, danos à saúde, desvalorização imobiliária). '
                    'Mencione laudos técnicos, boletins de ocorrência ou autos de infração.'
                ),
                'fields': [
                    {'name': 'descricao_fatos', 'label': 'Descrição dos Fatos e Danos Sofridos', 'type': 'textarea', 'required': True},
                    {'name': 'local_dano', 'label': 'Local do Dano', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'nexo_causal',
                'name': 'III - Do Nexo Causal',
                'description': 'Demonstração do nexo de causalidade entre a conduta e o dano',
                'instructions': (
                    'Demonstre o nexo de causalidade entre a atividade/conduta do réu e o dano '
                    'ambiental sofrido pelo autor. Na responsabilidade objetiva ambiental, adota-se '
                    'a teoria do risco integral: basta demonstrar a atividade, o dano e o nexo causal '
                    '(não se admitem excludentes como caso fortuito, força maior ou fato de terceiro). '
                    'Invoque laudos periciais e estudos técnicos que comprovem a relação de causalidade.'
                ),
                'fields': [
                    {'name': 'elementos_nexo', 'label': 'Elementos de Prova do Nexo Causal', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'responsabilidade_objetiva',
                'name': 'IV - Da Responsabilidade Objetiva',
                'description': 'Fundamentos da responsabilidade civil objetiva ambiental',
                'instructions': (
                    'Fundamente a responsabilidade civil objetiva: CF/1988, art. 225, §3º; '
                    'Lei 6.938/1981, art. 14, §1º. Demonstre que independe de comprovação de culpa '
                    '(teoria do risco integral). Aborde a solidariedade entre todos os degradadores '
                    'diretos e indiretos. Cite os princípios do poluidor-pagador, da reparação integral '
                    'e da imprescritibilidade da pretensão de reparação de dano ambiental. '
                    'Cite precedentes do STJ, marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'dano_material', 'label': 'Estimativa do Dano Material', 'type': 'text', 'required': False},
                    {'name': 'dano_moral', 'label': 'Dano Moral Ambiental', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedidos de reparação e indenização',
                'instructions': (
                    'Formule os pedidos: (1) tutela de urgência para cessação imediata da atividade '
                    'lesiva, se ainda em curso; (2) condenação do réu à reparação in natura do dano '
                    'ambiental (restauração); (3) indenização por danos materiais sofridos pelo autor; '
                    '(4) indenização por dano moral (individual ou coletivo); (5) inversão do ônus '
                    'da prova em favor do autor (princípio da precaução); (6) custas e honorários. '
                    'Indique o valor da causa.'
                ),
                'fields': [
                    {'name': 'pede_tutela_urgencia', 'label': 'Pede Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =====================================================================
    # ELEITORAL
    # =====================================================================
    {
        'doc_type_code': 'aije_eleitoral',
        'name': 'Ação de Investigação Judicial Eleitoral - LC 64/1990',
        'description': 'Ação para apurar uso indevido, desvio ou abuso de poder econômico ou político nas eleições',
        'version': '1.0',
        'legal_basis': 'LC 64/1990, art. 22; CE, art. 237',
        'primary_color': '#7C2D12',
        'secondary_color': '#EA580C',
        'cover_title': 'Ação de Investigação Judicial Eleitoral',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo eleitoral competente',
                'instructions': (
                    'Redija o endereçamento ao juízo eleitoral competente: Tribunal Regional Eleitoral '
                    'para eleições estaduais e federais; Juiz Eleitoral de primeira instância para '
                    'eleições municipais. Identifique o pleito eleitoral (ano, cargo disputado, '
                    'zona/município/estado).'
                ),
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Eleitoral Competente', 'type': 'text', 'required': True},
                    {'name': 'pleito', 'label': 'Pleito Eleitoral (ano e cargo)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'I - Da Qualificação das Partes',
                'description': 'Identificação do autor e do investigado',
                'instructions': (
                    'Qualifique o autor (representante): candidato, partido político, coligação ou '
                    'Ministério Público Eleitoral (LC 64/1990, art. 22, caput). Qualifique o '
                    'investigado (candidato, partido, representante de partido ou qualquer pessoa '
                    'que tenha contribuído para o abuso). Informe os números de inscrição eleitoral '
                    'e os dados de identificação completos.'
                ),
                'fields': [
                    {'name': 'representante', 'label': 'Representante (autor da AIJE)', 'type': 'text', 'required': True},
                    {'name': 'investigado', 'label': 'Investigado', 'type': 'text', 'required': True},
                    {'name': 'cargo_disputado', 'label': 'Cargo Disputado pelo Investigado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'fatos',
                'name': 'II - Dos Fatos',
                'description': 'Narração dos fatos que configuram o abuso de poder',
                'instructions': (
                    'Narre detalhadamente os fatos que configuram o abuso de poder econômico ou '
                    'político: condutas específicas, datas, locais, valores envolvidos, pessoas '
                    'beneficiadas. Descreva a captação ilícita de sufrágio (art. 41-A da Lei 9.504/1997), '
                    'uso da máquina administrativa (art. 73 da Lei 9.504/1997), compra de votos, '
                    'propaganda irregular, financiamento ilícito de campanha ou qualquer forma de '
                    'abuso que comprometa a normalidade e legitimidade do pleito.'
                ),
                'fields': [
                    {'name': 'descricao_fatos', 'label': 'Descrição Detalhada dos Fatos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'abuso_poder',
                'name': 'III - Do Abuso de Poder',
                'description': 'Enquadramento jurídico do abuso de poder',
                'instructions': (
                    'Enquadre juridicamente os fatos como abuso de poder econômico (uso de recursos '
                    'financeiros para desequilibrar a disputa), abuso de poder político (uso de '
                    'cargo público, máquina administrativa), ou abuso dos meios de comunicação. '
                    'Demonstre a gravidade das circunstâncias que comprometem a legitimidade do '
                    'pleito (LC 64/1990, art. 22, XVI). Fundamente na LC 64/1990, art. 22, '
                    'na Lei 9.504/1997 e no Código Eleitoral.'
                ),
                'fields': [
                    {'name': 'tipo_abuso', 'label': 'Tipo de Abuso de Poder', 'type': 'select', 'required': True,
                     'options': ['Econômico', 'Político', 'Dos meios de comunicação', 'Múltiplos']},
                    {'name': 'gravidade', 'label': 'Gravidade e Potencialidade de Comprometer o Pleito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'provas',
                'name': 'IV - Das Provas',
                'description': 'Indicação das provas do abuso de poder',
                'instructions': (
                    'Indique todas as provas que sustentam a AIJE: documentais (recibos, extratos '
                    'bancários, contratos, publicações em redes sociais, fotografias, vídeos), '
                    'testemunhais (rol de testemunhas com qualificação), periciais (se necessário), '
                    'informações de órgãos públicos. Requeira a produção de provas adicionais: '
                    'requisição de informações bancárias, quebra de sigilo, oitiva de testemunhas.'
                ),
                'fields': [
                    {'name': 'provas_documentais', 'label': 'Provas Documentais Juntadas', 'type': 'textarea', 'required': True},
                    {'name': 'testemunhas', 'label': 'Rol de Testemunhas', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedidos da AIJE',
                'instructions': (
                    'Formule os pedidos: (1) recebimento e processamento da AIJE; (2) citação do '
                    'investigado para apresentar defesa em 5 dias (LC 64/1990, art. 22, V); '
                    '(3) produção de provas; (4) procedência da ação para declarar a existência '
                    'de abuso de poder e decretar a inelegibilidade do investigado por 8 anos '
                    '(LC 64/1990, art. 1º, I, d, com redação da LC 135/2010); '
                    '(5) cassação do registro ou diploma, se já concedido; '
                    '(6) remessa de cópia ao Ministério Público Eleitoral para apuração criminal.'
                ),
                'fields': [
                    {'name': 'pede_liminar', 'label': 'Pede Medida Liminar?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'aime_eleitoral',
        'name': 'Ação de Impugnação de Mandato Eletivo - CF/1988',
        'description': 'Ação para impugnar mandato obtido mediante abuso de poder, corrupção ou fraude',
        'version': '1.0',
        'legal_basis': 'CF/1988, art. 14, §10; CE, arts. 262-275',
        'primary_color': '#991B1B',
        'secondary_color': '#DC2626',
        'cover_title': 'Ação de Impugnação de Mandato Eletivo',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo eleitoral competente',
                'instructions': (
                    'Redija o endereçamento ao juízo eleitoral competente para processar a AIME: '
                    'a competência segue a mesma regra do registro de candidatura. TSE para '
                    'Presidente e Vice; TRE para Governador, Vice, Senador, Deputado Federal e '
                    'Estadual; Juiz Eleitoral para Prefeito, Vice e Vereador. '
                    'Observe o prazo decadencial de 15 dias contados da diplomação (CF art. 14, §10).'
                ),
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Eleitoral Competente', 'type': 'text', 'required': True},
                    {'name': 'data_diplomacao', 'label': 'Data da Diplomação do Impugnado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'I - Da Qualificação das Partes',
                'description': 'Identificação do autor e do impugnado',
                'instructions': (
                    'Qualifique o autor: partido político, coligação, candidato eleito ou '
                    'Ministério Público Eleitoral. Qualifique o impugnado (diplomado cujo mandato '
                    'se pretende invalidar) com dados completos. Demonstre a legitimidade ativa '
                    'e o interesse de agir. Comprove a tempestividade da ação (15 dias da diplomação).'
                ),
                'fields': [
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'impugnado_nome', 'label': 'Nome do Impugnado (diplomado)', 'type': 'text', 'required': True},
                    {'name': 'cargo_eletivo', 'label': 'Cargo Eletivo do Impugnado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'fatos',
                'name': 'II - Dos Fatos',
                'description': 'Narração dos fatos de abuso, corrupção ou fraude',
                'instructions': (
                    'Narre detalhadamente os fatos que configuram abuso de poder econômico, '
                    'corrupção ou fraude (CF art. 14, §10): condutas específicas praticadas durante '
                    'o processo eleitoral, datas, locais, participantes, valores envolvidos. '
                    'Demonstre a relação causal entre a ilicitude e o resultado eleitoral. '
                    'A AIME exige prova de que a irregularidade foi determinante para a eleição.'
                ),
                'fields': [
                    {'name': 'descricao_fatos', 'label': 'Descrição Detalhada dos Fatos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'fundamentos',
                'name': 'III - Dos Fundamentos',
                'description': 'Fundamentação jurídica da impugnação',
                'instructions': (
                    'Fundamente na CF/1988, art. 14, §10 (hipóteses: abuso de poder econômico, '
                    'corrupção, fraude). Diferencie das demais ações eleitorais: a AIME é pós-diplomação '
                    'e visa cassar o mandato. Cite a LC 64/1990, a Lei 9.504/1997 e o Código Eleitoral. '
                    'Demonstre a potencialidade da conduta de influenciar o resultado (não exige '
                    'comprovação de resultado efetivo, mas potencialidade). '
                    'Cite precedentes do TSE, marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'hipotese_cf', 'label': 'Hipótese do art. 14, §10, CF', 'type': 'select', 'required': True,
                     'options': ['Abuso de poder econômico', 'Corrupção', 'Fraude']},
                ],
            },
            {
                'number': 5, 'key': 'provas',
                'name': 'IV - Das Provas',
                'description': 'Indicação e produção de provas',
                'instructions': (
                    'Indique as provas que fundamentam a AIME: documentos (fotos, vídeos, áudios, '
                    'prints de redes sociais, extratos bancários, contratos irregulares), '
                    'rol de testemunhas com qualificação completa, perícias requeridas. '
                    'Requeira provas adicionais: requisição de informações a órgãos públicos, '
                    'quebra de sigilo fiscal/bancário, perícia técnica em material de campanha. '
                    'A AIME tramita em segredo de justiça (CF art. 14, §11).'
                ),
                'fields': [
                    {'name': 'provas', 'label': 'Provas Documentais e Testemunhais', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedidos de cassação do mandato',
                'instructions': (
                    'Formule os pedidos: (1) recebimento e processamento da AIME em segredo de '
                    'justiça (CF art. 14, §11); (2) citação do impugnado para contestar; '
                    '(3) produção de provas requeridas; (4) procedência da ação para cassar o '
                    'mandato eletivo do impugnado; (5) declaração de inelegibilidade (LC 64/1990, '
                    'art. 1º, I, d); (6) convocação do segundo colocado ou realização de novas '
                    'eleições, conforme o caso.'
                ),
                'fields': [
                    {'name': 'providencias_adicionais', 'label': 'Providências Adicionais', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'recurso_eleitoral',
        'name': 'Recurso Eleitoral - Código Eleitoral',
        'description': 'Recurso contra decisão do juízo eleitoral de primeira instância',
        'version': '1.0',
        'legal_basis': 'CE, arts. 265-282; Resolução TSE',
        'primary_color': '#B45309',
        'secondary_color': '#D97706',
        'cover_title': 'Recurso Eleitoral',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao Tribunal Regional Eleitoral',
                'instructions': (
                    'Redija o endereçamento ao Tribunal Regional Eleitoral competente, por '
                    'intermédio do juízo eleitoral de primeira instância prolator da decisão recorrida '
                    '(CE art. 267). Identifique o recorrente com qualificação completa e o '
                    'processo de origem. O prazo para interposição é de 3 dias (CE art. 258).'
                ),
                'fields': [
                    {'name': 'tre_competente', 'label': 'TRE Competente', 'type': 'text', 'required': True},
                    {'name': 'recorrente', 'label': 'Nome do Recorrente', 'type': 'text', 'required': True},
                    {'name': 'recorrido', 'label': 'Nome do Recorrido', 'type': 'text', 'required': True},
                    {'name': 'processo_origem', 'label': 'Processo de Origem (número e zona)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'decisao_recorrida',
                'name': 'I - Da Decisão Recorrida',
                'description': 'Identificação e resumo da decisão atacada',
                'instructions': (
                    'Identifique a decisão recorrida: número do processo, zona eleitoral, juiz prolator, '
                    'data da publicação. Resuma o dispositivo da decisão e os fundamentos adotados '
                    'pelo juízo a quo. Comprove a tempestividade do recurso (prazo de 3 dias — '
                    'CE art. 258). Se houve embargos de declaração, esclareça o efeito interruptivo.'
                ),
                'fields': [
                    {'name': 'data_decisao', 'label': 'Data da Decisão Recorrida', 'type': 'text', 'required': True},
                    {'name': 'resumo_decisao', 'label': 'Resumo da Decisão Recorrida', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'razoes_recurso',
                'name': 'II - Das Razões do Recurso',
                'description': 'Fundamentos para a reforma da decisão',
                'instructions': (
                    'Desenvolva as razões recursais demonstrando o erro da decisão recorrida: '
                    'error in judicando (erro na aplicação do direito) e/ou error in procedendo '
                    '(erro processual). Aborde cada fundamento da decisão recorrida e demonstre '
                    'por que deve ser reformada. Cite a legislação eleitoral aplicável (CE, LC 64/1990, '
                    'Lei 9.504/1997), as resoluções do TSE pertinentes e precedentes '
                    'jurisprudenciais, marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'razoes', 'label': 'Razões Detalhadas do Recurso', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'pedido',
                'name': 'III - Do Pedido',
                'description': 'Pedidos de reforma da decisão',
                'instructions': (
                    'Formule os pedidos: (1) recebimento e processamento do recurso; '
                    '(2) concessão de efeito suspensivo, se cabível (CE art. 257); '
                    '(3) provimento do recurso para reformar a decisão recorrida, especificando '
                    'o resultado pretendido (deferimento do registro, absolvição, anulação do ato, '
                    'etc.); (4) subsidiariamente, anulação da decisão para novo julgamento com '
                    'suprimento da omissão ou vício processual, se for o caso.'
                ),
                'fields': [
                    {'name': 'pede_efeito_suspensivo', 'label': 'Pede Efeito Suspensivo?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'resultado_pretendido', 'label': 'Resultado Pretendido com a Reforma', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'impugnacao_registro_candidatura',
        'name': 'Impugnação de Candidatura - LC 64/1990',
        'description': 'Ação para impugnar registro de candidatura por inelegibilidade ou irregularidade',
        'version': '1.0',
        'legal_basis': 'LC 64/1990, arts. 3º-16; CE, art. 97',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Impugnação de Registro de Candidatura',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Endereçamento ao juízo eleitoral competente',
                'instructions': (
                    'Redija o endereçamento ao juízo eleitoral competente para o registro da '
                    'candidatura impugnada: Juiz Eleitoral para candidatos a Prefeito, Vice e '
                    'Vereador; TRE para candidatos a Governador, Vice, Senador, Deputado Federal '
                    'e Estadual; TSE para candidatos a Presidente e Vice. O prazo para impugnação '
                    'é de 5 dias após a publicação do edital de registro (LC 64/1990, art. 3º).'
                ),
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo Eleitoral Competente', 'type': 'text', 'required': True},
                    {'name': 'pleito', 'label': 'Pleito Eleitoral (ano e esfera)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'I - Da Qualificação das Partes',
                'description': 'Identificação do impugnante e do impugnado',
                'instructions': (
                    'Qualifique o impugnante: candidato, partido político, coligação ou Ministério '
                    'Público Eleitoral (LC 64/1990, art. 3º). Qualifique o impugnado (candidato cujo '
                    'registro se pretende indeferir) com dados completos: nome, número do candidato, '
                    'partido, cargo pretendido, número de inscrição eleitoral.'
                ),
                'fields': [
                    {'name': 'impugnante', 'label': 'Nome do Impugnante', 'type': 'text', 'required': True},
                    {'name': 'impugnado', 'label': 'Nome do Candidato Impugnado', 'type': 'text', 'required': True},
                    {'name': 'cargo_pretendido', 'label': 'Cargo Pretendido pelo Impugnado', 'type': 'text', 'required': True},
                    {'name': 'partido', 'label': 'Partido do Impugnado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'inelegibilidade',
                'name': 'II - Da Inelegibilidade ou Irregularidade',
                'description': 'Demonstração da causa de inelegibilidade ou irregularidade no registro',
                'instructions': (
                    'Descreva a causa de inelegibilidade ou irregularidade que impede o registro: '
                    '(1) inelegibilidades constitucionais (CF art. 14, §§4º a 7º — analfabetismo, '
                    'conscritos, inalistáveis, reeleição, desincompatibilização); '
                    '(2) inelegibilidades infraconstitucionais (LC 64/1990, art. 1º — condenação criminal '
                    'transitada em julgado ou por órgão colegiado, rejeição de contas, etc.); '
                    '(3) irregularidades documentais no pedido de registro (LC 64/1990, art. 11). '
                    'Aplique a Lei da Ficha Limpa (LC 135/2010) quando cabível.'
                ),
                'fields': [
                    {'name': 'causa_inelegibilidade', 'label': 'Causa de Inelegibilidade', 'type': 'textarea', 'required': True},
                    {'name': 'dispositivo_legal', 'label': 'Dispositivo Legal (CF, LC 64/1990, LC 135/2010)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'III - Da Fundamentação',
                'description': 'Fundamentos jurídicos da impugnação',
                'instructions': (
                    'Fundamente juridicamente a impugnação: cite os dispositivos constitucionais e legais '
                    'que estabelecem a inelegibilidade (CF art. 14, LC 64/1990, LC 135/2010). '
                    'Demonstre o enquadramento dos fatos na hipótese legal. Se a inelegibilidade '
                    'decorre de condenação (Ficha Limpa), comprove o trânsito em julgado ou decisão '
                    'de órgão colegiado. Se decorre de rejeição de contas, comprove a decisão '
                    'irrecorrível do Tribunal de Contas. Cite precedentes do TSE e TREs, '
                    'marcando como [VERIFICAR JURISPRUDÊNCIA: tema].'
                ),
                'fields': [
                    {'name': 'fundamentacao_detalhada', 'label': 'Fundamentação Jurídica Detalhada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos de indeferimento do registro',
                'instructions': (
                    'Formule os pedidos: (1) recebimento e processamento da impugnação; '
                    '(2) notificação do impugnado para contestar em 7 dias (LC 64/1990, art. 4º); '
                    '(3) oitiva do Ministério Público Eleitoral em 5 dias (LC 64/1990, art. 5º); '
                    '(4) produção de provas, se necessário; (5) procedência da impugnação para '
                    'indeferir o registro de candidatura do impugnado; (6) declaração de '
                    'inelegibilidade pelo prazo legal, se aplicável.'
                ),
                'fields': [
                    {'name': 'provas_requeridas', 'label': 'Provas Requeridas', 'type': 'textarea', 'required': False},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Constitucional, Ambiental e Eleitoral no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Constitucional, Ambiental e Eleitoral'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            return

        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Constitucional, Ambiental e Eleitoral concluído!\n'))

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
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: [{data["short_name"]}] {obj.name}')

    def _criar_agentes_secao(self):
        from apps.intelligent_assistant.models import SectionAgentConfig
        self.stdout.write('\n[3/4] Agentes de seção...')
        specs = [
            {
                'key': 'gerador_constitucional',
                'name': 'Verus.AI - Gerador Constitucional',
                'description': 'Gera seções de peças de Direito Constitucional',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_CONSTITUCIONAL,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'gerador_ambiental',
                'name': 'Verus.AI - Gerador Ambiental',
                'description': 'Gera seções de peças de Direito Ambiental',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_AMBIENTAL,
                'temperature': TEMP_GENERATOR,
                'max_tokens': MAX_TOKENS,
                'is_default': False,
            },
            {
                'key': 'gerador_eleitoral',
                'name': 'Verus.AI - Gerador Eleitoral',
                'description': 'Gera seções de peças de Direito Eleitoral',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_ELEITORAL,
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
                blueprint.secondary_color = bp_data['secondary_color']
                blueprint.save()
                blueprint.sections.all().delete()
                created = True
            # Adiciona área principal (categoria do doc_type) — FORA do if created
            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)
            # Adiciona áreas extras (multi-área) — FORA do if created
            extras = AREAS_EXTRAS.get(bp_data['doc_type_code'], [])
            for area_code in extras:
                area = cats.get(area_code)
                if area:
                    blueprint.areas.add(area)
                else:
                    self.stdout.write(self.style.WARNING(f'       ⚠ Área extra não encontrada: {area_code}'))
            # Garante is_default=True em re-execução
            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {blueprint.name}')
            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_constitucional')
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
