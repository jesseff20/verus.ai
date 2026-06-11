"""
Seed Cível - Ações Principais — Verus.AI.
Peças cíveis fundamentais ausentes: cobrança, declaratória, monitória,
responsabilidade civil, rescisão contratual, anulação de contrato.

Uso:
    python manage.py seed_civel_acoes
    python manage.py seed_civel_acoes --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction

MODEL = 'mistralai/mistral-medium-2505'
PROVIDER = 'watsonx'
TEMP_GENERATOR = 0.7
TEMP_VALIDATOR = 0.3
MAX_TOKENS = 4096

# Estas categorias já existem — get_or_create é idempotente
CATEGORIAS_EXTRAS = [
    # acoes_peticoes já criada pelo seed_juridico_completo
]

TIPOS_DOCUMENTO = [
    {
        'code': 'acao_cobranca',
        'name': 'Ação de Cobrança',
        'short_name': 'Ação Cobrança',
        'description': 'Ação judicial para cobrança de dívida líquida, certa e exigível',
        'category': 'acoes_peticoes',
        'icon': 'DollarSign',
        'color': '#059669',
        'legal_basis': 'CPC/2015, arts. 319-331; CC/2002, arts. 317-326 (pagamento)',
        'display_order': 20,
    },
    {
        'code': 'acao_declaratoria',
        'name': 'Ação Declaratória',
        'short_name': 'Ação Declaratória',
        'description': 'Ação para declaração judicial da existência, inexistência ou modo de ser de uma relação jurídica',
        'category': 'acoes_peticoes',
        'icon': 'FileSearch',
        'color': '#7030A0',
        'legal_basis': 'CPC/2015, art. 19; CC/2002',
        'display_order': 21,
    },
    {
        'code': 'acao_monitoria',
        'name': 'Ação Monitória',
        'short_name': 'Ação Monitória',
        'description': 'Ação para cobrança de crédito documentado sem força executiva',
        'category': 'acoes_peticoes',
        'icon': 'FileText',
        'color': '#059669',
        'legal_basis': 'CPC/2015, arts. 700-702',
        'display_order': 22,
    },
    {
        'code': 'acao_indenizacao_rc',
        'name': 'Ação de Indenização por Responsabilidade Civil',
        'short_name': 'Ação Inden. RC',
        'description': 'Ação de indenização por dano material e/ou moral decorrente de ato ilícito',
        'category': 'acoes_peticoes',
        'icon': 'AlertCircle',
        'color': '#DC2626',
        'legal_basis': 'CC/2002, arts. 186-188, 927-954; CPC/2015, arts. 319-331',
        'display_order': 23,
    },
    {
        'code': 'acao_rescisao_contratual',
        'name': 'Ação de Rescisão/Resolução Contratual',
        'short_name': 'Rescisão Contratual',
        'description': 'Ação para rescisão de contrato por inadimplemento ou vício',
        'category': 'acoes_peticoes',
        'icon': 'FileX',
        'color': '#DC2626',
        'legal_basis': 'CC/2002, arts. 472-480; arts. 389-420 (inadimplemento)',
        'display_order': 24,
    },
    {
        'code': 'acao_anulacao_contrato',
        'name': 'Ação de Anulação de Contrato',
        'short_name': 'Anulação Contrato',
        'description': 'Ação para anular contrato celebrado com vício de consentimento ou social',
        'category': 'acoes_peticoes',
        'icon': 'XCircle',
        'color': '#DC2626',
        'legal_basis': 'CC/2002, arts. 138-184 (vícios do negócio jurídico)',
        'display_order': 25,
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

PROMPT_GERADOR_CIVEL_AVANCADO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Civil e Processo Civil brasileiro.

LEGISLAÇÃO VIGENTE:
- CPC/2015 (Lei 13.105/2015); CC/2002 (Lei 10.406/2002); CF/88

REGRAS ESSENCIAIS:
1. Petições: CPC/2015 arts. 319-331 (requisitos da petição inicial)
2. Responsabilidade civil: CC art. 186 (ato ilícito), art. 927 (obrigação de indenizar), art. 944 (extensão do dano)
3. Dano moral: STJ Súmula 370 (cartão de crédito); 385 (cadastro negativação); in re ipsa quando patente
4. Contratos: CC arts. 421-480 (princípios); 472-480 (resolução e rescisão); 138-184 (vícios)
5. Ação monitória: CPC arts. 700-702 (crédito documentado sem título executivo)
6. Ação declaratória: CPC art. 19 (interesse processual na declaração)
7. Prescrição: CC arts. 205-206 (prazo geral 10 anos; especiais 1, 3, 5 anos)
8. Jurisprudência: Súmulas STJ apenas. Acórdãos: [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'acao_cobranca': 'gerador_civel_avancado',
    'acao_declaratoria': 'gerador_civel_avancado',
    'acao_monitoria': 'gerador_civel_avancado',
    'acao_indenizacao_rc': 'gerador_civel_avancado',
    'acao_rescisao_contratual': 'gerador_civel_avancado',
    'acao_anulacao_contrato': 'gerador_civel_avancado',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'acao_cobranca',
        'name': 'Ação de Cobrança - CPC/2015',
        'description': 'Petição inicial para cobrança judicial de dívida líquida, certa e exigível',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 319-331; CC/2002, arts. 317-326',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Ação de Cobrança',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação das Partes',
                'description': 'Juízo e identificação do credor e devedor',
                'instructions': 'Endereçe ao Juízo Cível competente (Juizado Especial ou Vara Cível conforme valor). Qualifique credor (autor) e devedor (réu) com dados completos.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'credor_nome', 'label': 'Nome do Credor (Autor)', 'type': 'text', 'required': True},
                    {'name': 'devedor_nome', 'label': 'Nome do Devedor (Réu)', 'type': 'text', 'required': True},
                    {'name': 'origem_divida', 'label': 'Origem da Dívida (contrato, empréstimo, serviço, etc.)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos',
                'name': 'I - Dos Fatos',
                'description': 'Origem e histórico da dívida',
                'instructions': 'Narre: origem da dívida (contrato, prestação de serviço, empréstimo, etc.), valor original, data do vencimento, tentativas de cobrança extrajudicial e inadimplência do devedor.',
                'fields': [
                    {'name': 'valor_original', 'label': 'Valor Original da Dívida (R$)', 'type': 'text', 'required': True},
                    {'name': 'data_vencimento', 'label': 'Data de Vencimento', 'type': 'text', 'required': True},
                    {'name': 'historico_cobranca', 'label': 'Tentativas de Cobrança Extrajudicial', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'direito_pedidos',
                'name': 'II - Do Direito e Dos Pedidos',
                'description': 'Fundamentos jurídicos e pedidos de condenação',
                'instructions': 'Fundamente: inadimplemento (CC art. 389), obrigação de pagar (CC art. 314), mora (CC art. 394). Pedidos: condenação no principal com correção monetária (IPCA-E/INPC), juros moratórios (CC art. 406: 1% a.m. ou Selic), honorários, custas.',
                'fields': [
                    {'name': 'indice_correcao', 'label': 'Índice de Correção Monetária', 'type': 'select', 'required': True, 'options': ['IPCA-E', 'INPC', 'IGP-M', 'Tabela do Tribunal']},
                    {'name': 'juros_pleiteados', 'label': 'Juros Moratórios', 'type': 'select', 'required': True, 'options': ['1% ao mês (CC art. 406)', 'Taxa SELIC', 'Taxa contratual']},
                    {'name': 'valor_atualizado', 'label': 'Valor Atualizado Estimado (R$)', 'type': 'text', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_declaratoria',
        'name': 'Ação Declaratória - CPC/2015',
        'description': 'Petição inicial para declaração judicial da existência, inexistência ou modo de ser de relação jurídica',
        'version': '1.0',
        'legal_basis': 'CPC/2015, art. 19; CC/2002',
        'primary_color': '#7030A0',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Ação Declaratória',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e partes',
                'instructions': 'Endereçe ao Juízo competente. Qualifique autor e réu.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos_interesse',
                'name': 'I - Dos Fatos e do Interesse Declaratório',
                'description': 'Fatos e interesse processual na declaração',
                'instructions': 'Narre os fatos que geram incerteza jurídica. Demonstre o interesse processual (CPC art. 19): necessidade da declaração para afastar insegurança jurídica atual e concreta. Indique o tipo de declaração pleiteada.',
                'fields': [
                    {'name': 'tipo_declaracao', 'label': 'Tipo de Declaração Pleiteada', 'type': 'select', 'required': True, 'options': ['Existência de relação jurídica', 'Inexistência de relação jurídica', 'Modo de ser da relação jurídica', 'Autenticidade de documento', 'Falsidade de documento']},
                    {'name': 'descricao_incerteza', 'label': 'Descrição da Incerteza Jurídica e dos Fatos', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'fundamento_pedidos',
                'name': 'II - Do Direito e Dos Pedidos',
                'description': 'Fundamentos jurídicos e pedido declaratório',
                'instructions': 'Fundamente juridicamente a declaração pleiteada. Formule o pedido declaratório com precisão. Se houver pedidos condenatórios cumulados, inclua-os.',
                'fields': [
                    {'name': 'pedido_declaratorio', 'label': 'Pedido Declaratório (redija com precisão)', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_cumulado', 'label': 'Há pedido condenatório cumulado?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (descreva)']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_monitoria',
        'name': 'Ação Monitória - CPC/2015',
        'description': 'Petição inicial para constituição de título executivo a partir de prova escrita sem eficácia executiva',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 700-702',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Ação Monitória',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e partes da ação monitória',
                'instructions': 'Endereçe ao Juízo Cível competente. Qualifique o autor (credor) e o réu (devedor). Informe o valor do crédito.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Credor)', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu (Devedor)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos_prova_escrita',
                'name': 'I - Dos Fatos e da Prova Escrita',
                'description': 'Origem do crédito e documento comprobatório',
                'instructions': 'Descreva a origem do crédito. Identifique a prova escrita (CPC art. 700: cheque prescrito, nota promissória prescrita, contrato, nota fiscal, etc.) sem força executiva própria. Informe valor e data do vencimento.',
                'fields': [
                    {'name': 'tipo_prova_escrita', 'label': 'Tipo de Prova Escrita (documento)', 'type': 'select', 'required': True, 'options': ['Cheque prescrito', 'Nota promissória prescrita', 'Duplicata sem aceite', 'Contrato', 'Nota fiscal/fatura', 'Outro documento']},
                    {'name': 'valor_credito', 'label': 'Valor do Crédito (R$)', 'type': 'text', 'required': True},
                    {'name': 'descricao_credito', 'label': 'Descrição da Origem do Crédito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedido de expedição de mandado monitório',
                'instructions': 'Formule pedidos: expedição de mandado monitório (CPC art. 701) para pagamento do valor em 15 dias, acrescido de juros, correção e honorários de 5% (art. 701 §1º), com advertência sobre embargos e cumprimento de sentença.',
                'fields': [
                    {'name': 'valor_total_pleiteado', 'label': 'Valor Total Pleiteado com Encargos (R$)', 'type': 'text', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_indenizacao_rc',
        'name': 'Ação de Indenização por Responsabilidade Civil - CC/2002',
        'description': 'Ação de indenização por dano material e/ou moral decorrente de ato ilícito',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 186-188, 927-954',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Ação de Indenização',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e partes da ação indenizatória',
                'instructions': 'Endereçe ao Juízo Cível competente. Qualifique o autor (vítima) e o réu (causador do dano ou responsável).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Vítima)', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu (Causador/Responsável)', 'type': 'text', 'required': True},
                    {'name': 'tipo_responsabilidade', 'label': 'Tipo de Responsabilidade', 'type': 'select', 'required': True, 'options': ['Subjetiva (CC art. 186 - culpa ou dolo)', 'Objetiva (CC art. 927, § único - risco da atividade)', 'Solidária (CC art. 942)']},
                ],
            },
            {
                'number': 2, 'key': 'fatos_danos',
                'name': 'I - Dos Fatos e dos Danos',
                'description': 'Narração do ato ilícito e dos danos sofridos',
                'instructions': 'Narre o ato ilícito (CC art. 186): ação ou omissão, dolo ou culpa. Descreva os danos sofridos: materiais (emergentes e lucros cessantes), morais e estéticos se aplicável. Demonstre o nexo causal entre o ato e o dano.',
                'fields': [
                    {'name': 'descricao_ato_ilicito', 'label': 'Descrição do Ato Ilícito', 'type': 'textarea', 'required': True},
                    {'name': 'danos_materiais', 'label': 'Danos Materiais (dano emergente e lucros cessantes)', 'type': 'textarea', 'required': False},
                    {'name': 'danos_morais', 'label': 'Danos Morais (descrição da lesão à honra/dignidade/etc.)', 'type': 'textarea', 'required': False},
                    {'name': 'nexo_causal', 'label': 'Nexo Causal (como o ato causou o dano)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'direito_pedidos',
                'name': 'II - Do Direito e Dos Pedidos',
                'description': 'Fundamentos e pedidos de indenização',
                'instructions': 'Fundamente: CC art. 186 (ato ilícito), art. 927 (dever de indenizar), art. 944 (extensão do dano). Para responsabilidade objetiva, cite o parágrafo único do art. 927. Pedidos: condenação em danos materiais (valor certo), morais (valor estimado), estéticos se cabível, honorários.',
                'fields': [
                    {'name': 'valor_danos_materiais', 'label': 'Valor dos Danos Materiais (R$)', 'type': 'text', 'required': False},
                    {'name': 'valor_danos_morais', 'label': 'Valor dos Danos Morais Pleiteados (R$)', 'type': 'text', 'required': False},
                    {'name': 'pedido_tutela', 'label': 'Pedido de Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (risco de dano irreparável)']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_rescisao_contratual',
        'name': 'Ação de Rescisão/Resolução Contratual - CC/2002',
        'description': 'Ação para rescisão de contrato por inadimplemento ou vício, com perdas e danos',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 472-480; arts. 389-420 (inadimplemento)',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Ação de Rescisão Contratual',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e partes do contrato',
                'instructions': 'Endereçe ao Juízo Cível competente. Qualifique o autor e o réu. Identifique o contrato: tipo, data de celebração, objeto.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu', 'type': 'text', 'required': True},
                    {'name': 'tipo_contrato', 'label': 'Tipo do Contrato (compra e venda, prestação de serviços, locação, etc.)', 'type': 'text', 'required': True},
                    {'name': 'data_contrato', 'label': 'Data do Contrato', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'inadimplemento',
                'name': 'I - Do Inadimplemento e dos Danos',
                'description': 'Descrição do inadimplemento e seus efeitos',
                'instructions': 'Descreva o inadimplemento: qual obrigação não foi cumprida, quando, valor envolvido. Mencione tentativas de resolução extrajudicial. Descreva os danos sofridos pela inadimplência (CC art. 389: perdas e danos, juros, correção, honorários).',
                'fields': [
                    {'name': 'obrigacao_violada', 'label': 'Obrigação Contratual Violada', 'type': 'textarea', 'required': True},
                    {'name': 'tentativa_extrajudicial', 'label': 'Tentativa de Resolução Extrajudicial', 'type': 'textarea', 'required': False},
                    {'name': 'danos_sofridos', 'label': 'Danos Sofridos em Razão do Inadimplemento', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Rescisão e perdas e danos',
                'instructions': 'Pedidos: rescisão/resolução do contrato (CC art. 475), condenação em perdas e danos (CC art. 389), restituição de valores pagos, cláusula penal se prevista, honorários e custas.',
                'fields': [
                    {'name': 'valor_restituicao', 'label': 'Valor a Ser Restituído (R$)', 'type': 'text', 'required': False},
                    {'name': 'ha_clausula_penal', 'label': 'Há cláusula penal no contrato?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (especificar valor ou percentual)']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_anulacao_contrato',
        'name': 'Ação de Anulação de Contrato - CC/2002',
        'description': 'Ação para anular contrato celebrado com vício de consentimento ou defeito social',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 138-184 (vícios do negócio jurídico)',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Ação de Anulação de Contrato',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo e partes',
                'instructions': 'Endereçe ao Juízo Cível. Qualifique autor e réu. Identifique o contrato e a data.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu', 'type': 'text', 'required': True},
                    {'name': 'descricao_contrato', 'label': 'Descrição do Contrato e Data', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'vicio_juridico',
                'name': 'I - Do Vício do Negócio Jurídico',
                'description': 'Identificação e descrição do vício',
                'instructions': 'Identifique o vício: erro (CC arts. 138-144), dolo (CC arts. 145-150), coação (CC arts. 151-155), estado de perigo (CC art. 156), lesão (CC art. 157), fraude contra credores (CC arts. 158-165). Descreva os fatos que configuram o vício.',
                'fields': [
                    {'name': 'tipo_vicio', 'label': 'Tipo de Vício do Negócio Jurídico', 'type': 'select', 'required': True, 'options': ['Erro (CC arts. 138-144)', 'Dolo (CC arts. 145-150)', 'Coação (CC arts. 151-155)', 'Estado de Perigo (CC art. 156)', 'Lesão (CC art. 157)', 'Fraude contra Credores (CC arts. 158-165)', 'Incapacidade do Agente (CC arts. 3º-4º)']},
                    {'name': 'descricao_vicio', 'label': 'Descrição dos Fatos que Configuram o Vício', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Anulação e consequências',
                'instructions': 'Pedidos: anulação do contrato (CC art. 171 ou 177), retorno ao status quo ante, restituição de valores pagos, perdas e danos se aplicável (CC art. 182). Atente para prazo decadencial (CC art. 178 e 179).',
                'fields': [
                    {'name': 'valor_restituicao', 'label': 'Valor a Ser Restituído (R$)', 'type': 'text', 'required': False},
                    {'name': 'danos_pleiteados', 'label': 'Perdas e Danos Pleiteados', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Ações Cíveis Principais no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Cível: Ações Principais'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN\n'))
            return
        with transaction.atomic():
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)
        self.stdout.write(self.style.SUCCESS('\n✓ Cível: Ações Principais concluído!\n'))

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
            {'key': 'gerador_civel_avancado', 'name': 'Verus.AI - Gerador Cível Avançado', 'description': 'Gera ações cíveis: cobrança, declaratória, monitória, indenização, rescisão', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_CIVEL_AVANCADO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
        self.stdout.write('\n[3/3] Blueprints...')
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
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_civel_avancado')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
