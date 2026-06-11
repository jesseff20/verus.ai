"""
Seed Cível - Complemento — Verus.AI.
Peças civis e procedimentais faltantes: réplica, embargos de terceiro,
possessória, usucapião, rescisória, obrigação de fazer, cumprimento de sentença,
tutelas cautelares, contrarrazões e embargos de divergência.

Uso:
    python manage.py seed_civel_complemento
    python manage.py seed_civel_complemento --force
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
        'code': 'replica_civel',
        'name': 'Réplica à Contestação',
        'short_name': 'Réplica',
        'description': 'Manifestação do autor sobre a contestação apresentada pelo réu',
        'category': 'defesas_respostas',
        'icon': 'MessageSquare',
        'color': '#2563EB',
        'legal_basis': 'CPC/2015, art. 351 (réplica); arts. 337-342 (preliminares)',
        'display_order': 30,
    },
    {
        'code': 'embargos_terceiro',
        'name': 'Embargos de Terceiro',
        'short_name': 'Embargos Terceiro',
        'description': 'Ação de terceiro prejudicado por ato de constrição judicial sobre seus bens',
        'category': 'defesas_respostas',
        'icon': 'Shield',
        'color': '#059669',
        'legal_basis': 'CPC/2015, arts. 674-681',
        'display_order': 31,
    },
    {
        'code': 'acao_possessoria',
        'name': 'Ação Possessória',
        'short_name': 'Possessória',
        'description': 'Ação para proteção da posse contra esbulho, turbação ou ameaça',
        'category': 'acoes_peticoes',
        'icon': 'Home',
        'color': '#B45309',
        'legal_basis': 'CPC/2015, arts. 554-568; CC/2002, arts. 1.196-1.224',
        'display_order': 32,
    },
    {
        'code': 'usucapiao',
        'name': 'Ação de Usucapião',
        'short_name': 'Usucapião',
        'description': 'Ação para aquisição originária da propriedade pelo exercício prolongado da posse',
        'category': 'acoes_peticoes',
        'icon': 'MapPin',
        'color': '#B45309',
        'legal_basis': 'CC/2002, arts. 1.238-1.244; CPC/2015, arts. 246, §3º, 259, I',
        'display_order': 33,
    },
    {
        'code': 'acao_rescisoria',
        'name': 'Ação Rescisória',
        'short_name': 'Rescisória',
        'description': 'Ação para desconstituir decisão de mérito transitada em julgado',
        'category': 'acoes_peticoes',
        'icon': 'Scissors',
        'color': '#DC2626',
        'legal_basis': 'CPC/2015, arts. 966-975',
        'display_order': 34,
    },
    {
        'code': 'obrigacao_fazer_nao_fazer',
        'name': 'Ação de Obrigação de Fazer/Não Fazer',
        'short_name': 'Obrigação Fazer',
        'description': 'Ação para compelir ao cumprimento de obrigação de fazer ou não fazer',
        'category': 'acoes_peticoes',
        'icon': 'CheckCircle',
        'color': '#7C3AED',
        'legal_basis': 'CPC/2015, arts. 497, 536-537; CC/2002, arts. 247-249',
        'display_order': 35,
    },
    {
        'code': 'cumprimento_sentenca',
        'name': 'Cumprimento de Sentença',
        'short_name': 'Cumpr. Sentença',
        'description': 'Requerimento de cumprimento de sentença condenatória transitada em julgado ou provisória',
        'category': 'execucao',
        'icon': 'PlayCircle',
        'color': '#059669',
        'legal_basis': 'CPC/2015, arts. 513-538',
        'display_order': 36,
    },
    {
        'code': 'tutela_cautelar_antecedente',
        'name': 'Tutela Cautelar Antecedente',
        'short_name': 'Cautelar Antec.',
        'description': 'Pedido de tutela cautelar em caráter antecedente ao pedido principal',
        'category': 'cautelares_tutelas',
        'icon': 'ShieldAlert',
        'color': '#DC2626',
        'legal_basis': 'CPC/2015, arts. 305-310',
        'display_order': 37,
    },
    {
        'code': 'tutela_evidencia',
        'name': 'Tutela de Evidência',
        'short_name': 'Tutela Evidência',
        'description': 'Pedido de tutela provisória fundada na evidência do direito',
        'category': 'cautelares_tutelas',
        'icon': 'Eye',
        'color': '#2563EB',
        'legal_basis': 'CPC/2015, art. 311',
        'display_order': 38,
    },
    {
        'code': 'producao_antecipada_provas',
        'name': 'Produção Antecipada de Provas',
        'short_name': 'Prod. Antec. Provas',
        'description': 'Ação autônoma para produção antecipada de provas',
        'category': 'cautelares_tutelas',
        'icon': 'Search',
        'color': '#7C3AED',
        'legal_basis': 'CPC/2015, arts. 381-383',
        'display_order': 39,
    },
    {
        'code': 'contrarrazoes_agravo_instrumento',
        'name': 'Contrarrazões de Agravo de Instrumento',
        'short_name': 'Contrarrazões AI',
        'description': 'Resposta ao agravo de instrumento interposto pela parte adversa',
        'category': 'defesas_respostas',
        'icon': 'FileText',
        'color': '#2563EB',
        'legal_basis': 'CPC/2015, art. 1.019, II',
        'display_order': 40,
    },
    {
        'code': 'contrarrazoes_recurso_especial',
        'name': 'Contrarrazões de Recurso Especial',
        'short_name': 'Contrarrazões REsp',
        'description': 'Resposta ao recurso especial interposto pela parte adversa',
        'category': 'defesas_respostas',
        'icon': 'FileText',
        'color': '#7030A0',
        'legal_basis': 'CPC/2015, art. 1.030, caput e §1º',
        'display_order': 41,
    },
    {
        'code': 'contrarrazoes_recurso_extraordinario',
        'name': 'Contrarrazões de Recurso Extraordinário',
        'short_name': 'Contrarrazões RE',
        'description': 'Resposta ao recurso extraordinário interposto pela parte adversa',
        'category': 'defesas_respostas',
        'icon': 'FileText',
        'color': '#7030A0',
        'legal_basis': 'CPC/2015, art. 1.030, caput e §1º; CF/88, art. 102, III',
        'display_order': 42,
    },
    {
        'code': 'embargos_divergencia',
        'name': 'Embargos de Divergência',
        'short_name': 'Embargos Divergência',
        'description': 'Recurso para uniformização de jurisprudência no STJ ou STF',
        'category': 'recursos',
        'icon': 'GitBranch',
        'color': '#DC2626',
        'legal_basis': 'CPC/2015, arts. 1.043-1.044',
        'display_order': 43,
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
- Conteúdo inferido: [SUGESTÃO - VERIFICAR COM ADVOGADO]
- Todo documento DEVE terminar com: "⚠️ AVISO: Esta minuta requer revisão obrigatória por advogado habilitado perante a OAB."
"""

PROMPT_GERADOR_CIVEL_COMPLEMENTO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Civil e Processo Civil brasileiro.

LEGISLAÇÃO VIGENTE:
- CPC/2015 (Lei 13.105/2015); CC/2002 (Lei 10.406/2002); CF/88

REGRAS ESSENCIAIS:
1. Petições: CPC/2015 arts. 319-331 (requisitos da petição inicial)
2. Réplica: CPC art. 351 (manifestação sobre preliminares e fatos novos)
3. Embargos de terceiro: CPC arts. 674-681 (legitimidade, prazo, procedimento)
4. Possessórias: CPC arts. 554-568 (reintegração, manutenção, interdito)
5. Usucapião: CC arts. 1.238-1.244 (modalidades); CPC art. 259, I (citações)
6. Ação rescisória: CPC arts. 966-975 (hipóteses, prazo, competência)
7. Obrigação de fazer: CPC arts. 497, 536-537 (tutela específica, astreintes)
8. Cumprimento de sentença: CPC arts. 513-538 (provisório e definitivo)
9. Tutela cautelar antecedente: CPC arts. 305-310
10. Tutela de evidência: CPC art. 311 (hipóteses I a IV)
11. Produção antecipada de provas: CPC arts. 381-383
12. Contrarrazões: CPC arts. 1.019, II (agravo); 1.030 (REsp/RE)
13. Embargos de divergência: CPC arts. 1.043-1.044

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'replica_civel': 'gerador_civel_complemento',
    'embargos_terceiro': 'gerador_civel_complemento',
    'acao_possessoria': 'gerador_civel_complemento',
    'usucapiao': 'gerador_civel_complemento',
    'acao_rescisoria': 'gerador_civel_complemento',
    'obrigacao_fazer_nao_fazer': 'gerador_civel_complemento',
    'cumprimento_sentenca': 'gerador_civel_complemento',
    'tutela_cautelar_antecedente': 'gerador_civel_complemento',
    'tutela_evidencia': 'gerador_civel_complemento',
    'producao_antecipada_provas': 'gerador_civel_complemento',
    'contrarrazoes_agravo_instrumento': 'gerador_civel_complemento',
    'contrarrazoes_recurso_especial': 'gerador_civel_complemento',
    'contrarrazoes_recurso_extraordinario': 'gerador_civel_complemento',
    'embargos_divergencia': 'gerador_civel_complemento',
}

BLUEPRINTS_DATA = [
    # =========================================================================
    # 1. Réplica à Contestação
    # =========================================================================
    {
        'doc_type_code': 'replica_civel',
        'name': 'Réplica à Contestação - CPC/2015',
        'description': 'Manifestação do autor impugnando a contestação e as preliminares arguidas pelo réu',
        'version': '1.0',
        'legal_basis': 'CPC/2015, art. 351; arts. 337-342',
        'primary_color': '#2563EB',
        'secondary_color': '#3B82F6',
        'cover_title': 'Réplica à Contestação',
        'secondary_area_codes': ['acoes_peticoes'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Identificação do juízo e do processo',
                'instructions': 'Endereçe ao Juízo onde tramita o processo. Identifique o número do processo, o autor (replicante) e o réu (contestante). Faça referência à contestação apresentada e ao prazo para réplica (CPC art. 351).',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo (Vara e Comarca)', 'type': 'text', 'required': True},
                    {'name': 'numero_processo', 'label': 'Número do Processo', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Replicante)', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu (Contestante)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'sintese_contestacao',
                'name': 'I - Síntese da Contestação',
                'description': 'Resumo dos principais pontos da contestação',
                'instructions': 'Sintetize os principais argumentos da contestação: preliminares arguidas (CPC art. 337), fatos impugnados, teses jurídicas apresentadas pelo réu e pedidos formulados na contestação. Organize por tópicos para facilitar a impugnação.',
                'fields': [
                    {'name': 'preliminares_arguidas', 'label': 'Preliminares Arguidas pelo Réu', 'type': 'textarea', 'required': False},
                    {'name': 'principais_argumentos', 'label': 'Principais Argumentos da Contestação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'impugnacao_fatos',
                'name': 'II - Impugnação dos Fatos',
                'description': 'Refutação dos fatos narrados na contestação',
                'instructions': 'Impugne especificamente cada fato alegado pelo réu na contestação (CPC art. 341 — ônus da impugnação especificada). Demonstre as inconsistências factuais, apresente fatos novos se houver, e indique as provas que os sustentam.',
                'fields': [
                    {'name': 'fatos_impugnados', 'label': 'Fatos a Impugnar (descreva ponto a ponto)', 'type': 'textarea', 'required': True},
                    {'name': 'fatos_novos', 'label': 'Fatos Novos (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'impugnacao_direito',
                'name': 'III - Impugnação do Direito',
                'description': 'Refutação dos fundamentos jurídicos da contestação',
                'instructions': 'Refute os fundamentos jurídicos da contestação. Demonstre que a legislação, doutrina e jurisprudência amparam a pretensão do autor. Afaste as preliminares arguidas (CPC arts. 337-342), se houver, demonstrando a presença dos pressupostos processuais e condições da ação.',
                'fields': [
                    {'name': 'fundamentos_refutacao', 'label': 'Fundamentos Jurídicos para Refutação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'provas',
                'name': 'IV - Das Provas',
                'description': 'Requerimento de produção de provas',
                'instructions': 'Requeira a produção das provas necessárias para demonstrar os fatos alegados na réplica: documental (CPC art. 434), testemunhal (CPC art. 450), pericial (CPC art. 464), depoimento pessoal do réu (CPC art. 385). Justifique a pertinência de cada prova requerida.',
                'fields': [
                    {'name': 'provas_requeridas', 'label': 'Provas Requeridas (documental, testemunhal, pericial, etc.)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'V - Do Pedido',
                'description': 'Pedido de rejeição da contestação',
                'instructions': 'Requeira o acolhimento da réplica com a rejeição das preliminares arguidas, a desconsideração dos fatos impugnados não comprovados pelo réu, e a procedência integral dos pedidos formulados na petição inicial. Requeira o prosseguimento do feito.',
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 2. Embargos de Terceiro
    # =========================================================================
    {
        'doc_type_code': 'embargos_terceiro',
        'name': 'Embargos de Terceiro - CPC/2015',
        'description': 'Ação de terceiro para proteger seus bens de constrição judicial indevida',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 674-681',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Embargos de Terceiro',
        'secondary_area_codes': ['execucao'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Juízo competente e identificação do processo principal',
                'instructions': 'Endereçe ao Juízo que determinou a constrição (CPC art. 676). Identifique o processo principal onde ocorreu o ato constritivo, as partes originárias e o terceiro embargante.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo (Vara e Comarca)', 'type': 'text', 'required': True},
                    {'name': 'numero_processo_principal', 'label': 'Número do Processo Principal', 'type': 'text', 'required': True},
                    {'name': 'partes_originarias', 'label': 'Partes do Processo Principal', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação do Embargante',
                'description': 'Dados completos do terceiro embargante',
                'instructions': 'Qualifique o terceiro embargante com dados completos (nome, CPF/CNPJ, endereço). Demonstre que é terceiro em relação ao processo principal — não é parte, nem sucessor, nem responsável patrimonial (CPC art. 674).',
                'fields': [
                    {'name': 'embargante_nome', 'label': 'Nome do Embargante (Terceiro)', 'type': 'text', 'required': True},
                    {'name': 'embargante_cpf_cnpj', 'label': 'CPF/CNPJ do Embargante', 'type': 'text', 'required': True},
                    {'name': 'embargante_endereco', 'label': 'Endereço Completo', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'ato_constritivo',
                'name': 'I - Do Ato Constritivo',
                'description': 'Identificação e descrição do ato de constrição',
                'instructions': 'Descreva o ato constritivo sofrido pelo terceiro: penhora, arresto, sequestro, busca e apreensão ou qualquer outra constrição judicial (CPC art. 674). Identifique os bens atingidos, a data da constrição e como o embargante tomou ciência. Atente para o prazo de 5 dias (CPC art. 675).',
                'fields': [
                    {'name': 'tipo_constricao', 'label': 'Tipo de Constrição', 'type': 'select', 'required': True, 'options': ['Penhora', 'Arresto', 'Sequestro', 'Busca e Apreensão', 'Outro']},
                    {'name': 'bens_atingidos', 'label': 'Bens Atingidos pela Constrição', 'type': 'textarea', 'required': True},
                    {'name': 'data_constricao', 'label': 'Data da Constrição ou Ciência', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'direito_terceiro',
                'name': 'II - Do Direito do Terceiro',
                'description': 'Comprovação da propriedade ou posse do embargante',
                'instructions': 'Demonstre o direito do embargante sobre os bens constritados: propriedade, posse, domínio útil ou outro direito real (CPC art. 674). Apresente os documentos comprobatórios: escritura, contrato, nota fiscal, registro. Comprove que os bens não integram o patrimônio do executado.',
                'fields': [
                    {'name': 'tipo_direito', 'label': 'Tipo de Direito sobre os Bens', 'type': 'select', 'required': True, 'options': ['Propriedade', 'Posse', 'Domínio Útil', 'Usufruto', 'Outro Direito Real']},
                    {'name': 'documentos_comprobatorios', 'label': 'Documentos que Comprovam o Direito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'fundamentacao',
                'name': 'III - Da Fundamentação Jurídica',
                'description': 'Base legal dos embargos de terceiro',
                'instructions': 'Fundamente juridicamente os embargos: CPC arts. 674-681, legitimidade do terceiro (art. 674), cabimento (constrição judicial indevida), prazo (art. 675), efeito suspensivo (art. 678). Cite CC/2002 quanto ao direito de propriedade (arts. 1.228 e ss.) ou posse (arts. 1.196 e ss.).',
                'fields': [
                    {'name': 'fundamentacao_legal', 'label': 'Fundamentação Jurídica Adicional', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos de liberação dos bens',
                'instructions': 'Pedidos: liminar para suspensão das medidas constritivas sobre os bens do embargante (CPC art. 678); no mérito, procedência dos embargos com desconstituição definitiva da constrição; condenação do embargado em honorários e custas. Se houver danos, pleitear indenização.',
                'fields': [
                    {'name': 'pedido_liminar', 'label': 'Requer liminar para suspensão imediata?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 3. Ação Possessória
    # =========================================================================
    {
        'doc_type_code': 'acao_possessoria',
        'name': 'Ação Possessória - CPC/2015',
        'description': 'Petição inicial para proteção possessória contra esbulho, turbação ou ameaça',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 554-568; CC/2002, arts. 1.196-1.224',
        'primary_color': '#B45309',
        'secondary_color': '#D97706',
        'cover_title': 'Ação Possessória',
        'secondary_area_codes': ['imobiliario'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Juízo competente e qualificação das partes',
                'instructions': 'Endereçe ao Juízo Cível da comarca da situação do imóvel (CPC art. 47, §2º). Qualifique o autor (possuidor) e o réu (esbulhador/turbador).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca (situação do imóvel)', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Possuidor)', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu (Esbulhador/Turbador)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Dados completos do autor e réu',
                'instructions': 'Qualifique autor e réu com dados completos: nacionalidade, estado civil, profissão, CPF/CNPJ, RG, endereço. Para ação de força nova (até ano e dia), registre a data do esbulho/turbação com precisão.',
                'fields': [
                    {'name': 'autor_qualificacao', 'label': 'Qualificação Completa do Autor', 'type': 'textarea', 'required': True},
                    {'name': 'reu_qualificacao', 'label': 'Qualificação Completa do Réu', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'posse',
                'name': 'I - Da Posse',
                'description': 'Comprovação do exercício da posse pelo autor',
                'instructions': 'Demonstre o exercício da posse pelo autor (CC art. 1.196): tempo de posse, forma de aquisição, atos possessórios praticados (cultivo, construção, moradia, pagamento de tributos). Indique se a posse é direta ou indireta, justa (CC art. 1.200), de boa-fé (CC art. 1.201).',
                'fields': [
                    {'name': 'tempo_posse', 'label': 'Tempo de Exercício da Posse', 'type': 'text', 'required': True},
                    {'name': 'forma_aquisicao', 'label': 'Como a Posse Foi Adquirida', 'type': 'textarea', 'required': True},
                    {'name': 'atos_possessorios', 'label': 'Atos Possessórios Praticados', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'esbulho_turbacao',
                'name': 'II - Do Esbulho/Turbação',
                'description': 'Descrição do ato ofensivo à posse',
                'instructions': 'Descreva detalhadamente o esbulho (perda total da posse — CC art. 1.200) ou turbação (embaraço ao exercício — CC art. 1.210). Indique data, circunstâncias, meios utilizados e consequências. Classifique a ação: reintegração de posse (esbulho), manutenção de posse (turbação) ou interdito proibitório (ameaça) — CPC art. 554.',
                'fields': [
                    {'name': 'tipo_ofensa', 'label': 'Tipo de Ofensa à Posse', 'type': 'select', 'required': True, 'options': ['Esbulho (perda total da posse)', 'Turbação (embaraço à posse)', 'Ameaça (risco iminente)']},
                    {'name': 'data_ofensa', 'label': 'Data do Esbulho/Turbação/Ameaça', 'type': 'text', 'required': True},
                    {'name': 'descricao_ofensa', 'label': 'Descrição Detalhada da Ofensa', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'tutela_urgencia',
                'name': 'III - Da Tutela de Urgência (Liminar)',
                'description': 'Pedido de liminar possessória',
                'instructions': 'Se a ação for de força nova (esbulho/turbação há menos de ano e dia — CPC art. 558), requeira a liminar possessória: demonstre a posse, a data do esbulho/turbação, a perda ou turbação e a continuação. Se de força velha (mais de ano e dia), requeira tutela de urgência pelo rito comum (CPC art. 300).',
                'fields': [
                    {'name': 'tipo_acao', 'label': 'Tipo da Ação Possessória', 'type': 'select', 'required': True, 'options': ['Força Nova (menos de ano e dia)', 'Força Velha (mais de ano e dia)']},
                    {'name': 'justificativa_liminar', 'label': 'Justificativa para a Liminar', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos possessórios',
                'instructions': 'Pedidos: liminar de reintegração/manutenção de posse ou interdito proibitório; no mérito, confirmação da liminar; condenação do réu em perdas e danos (CPC art. 555); cominação de multa diária (astreintes) em caso de descumprimento; honorários e custas.',
                'fields': [
                    {'name': 'valor_danos', 'label': 'Valor dos Danos (R$), se pleiteados', 'type': 'text', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 4. Usucapião
    # =========================================================================
    {
        'doc_type_code': 'usucapiao',
        'name': 'Ação de Usucapião - CC/2002',
        'description': 'Petição inicial para aquisição originária da propriedade pelo exercício prolongado e ininterrupto da posse',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.238-1.244; CPC/2015, arts. 246, §3º, 259, I',
        'primary_color': '#B45309',
        'secondary_color': '#D97706',
        'cover_title': 'Ação de Usucapião',
        'secondary_area_codes': ['imobiliario'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Juízo competente',
                'instructions': 'Endereçe ao Juízo Cível da comarca da situação do imóvel (CPC art. 47). Identifique a ação como Ação de Usucapião.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca (situação do imóvel)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Dados do usucapiente e confrontantes',
                'instructions': 'Qualifique o autor (usucapiente) com dados completos. Identifique os réus: proprietário tabular, confrontantes, eventuais interessados. Indique a necessidade de citação dos confinantes e da Fazenda Pública (CPC art. 246, §3º; art. 259, I).',
                'fields': [
                    {'name': 'autor_nome', 'label': 'Nome do Autor (Usucapiente)', 'type': 'text', 'required': True},
                    {'name': 'autor_qualificacao', 'label': 'Qualificação Completa do Autor', 'type': 'textarea', 'required': True},
                    {'name': 'proprietario_tabular', 'label': 'Proprietário Tabular (se conhecido)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'imovel',
                'name': 'I - Do Imóvel',
                'description': 'Descrição e individualização do imóvel usucapiendo',
                'instructions': 'Descreva o imóvel com precisão: localização, área, limites, confrontações, matrícula no Registro de Imóveis (se existir). Apresente planta e memorial descritivo. Informe se há registro anterior e situação cadastral junto à Prefeitura.',
                'fields': [
                    {'name': 'endereco_imovel', 'label': 'Endereço Completo do Imóvel', 'type': 'text', 'required': True},
                    {'name': 'area_imovel', 'label': 'Área do Imóvel (m²)', 'type': 'text', 'required': True},
                    {'name': 'matricula_imovel', 'label': 'Matrícula no Registro de Imóveis (se houver)', 'type': 'text', 'required': False},
                    {'name': 'descricao_imovel', 'label': 'Descrição Detalhada (limites, confrontações)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'posse_continua',
                'name': 'II - Da Posse Contínua',
                'description': 'Comprovação dos requisitos de posse para usucapião',
                'instructions': 'Demonstre a posse contínua, pacífica, ininterrupta e com animus domini (CC art. 1.238). Narre o histórico da posse: data de início, forma de aquisição, atos possessórios praticados (moradia, benfeitorias, pagamento de tributos, contas de consumo). Indique testemunhas que possam atestar a posse.',
                'fields': [
                    {'name': 'data_inicio_posse', 'label': 'Data de Início da Posse', 'type': 'text', 'required': True},
                    {'name': 'tempo_posse', 'label': 'Tempo Total de Posse (anos)', 'type': 'text', 'required': True},
                    {'name': 'atos_possessorios', 'label': 'Atos Possessórios Praticados', 'type': 'textarea', 'required': True},
                    {'name': 'benfeitorias', 'label': 'Benfeitorias Realizadas', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'modalidade_usucapiao',
                'name': 'III - Da Modalidade de Usucapião',
                'description': 'Enquadramento legal da modalidade aplicável',
                'instructions': 'Enquadre na modalidade de usucapião aplicável: extraordinária (CC art. 1.238 — 15 anos, reduzido a 10 com moradia/produtividade), ordinária (CC art. 1.242 — 10 anos com justo título e boa-fé, reduzido a 5), especial urbana (CF art. 183; CC art. 1.240 — 5 anos, até 250m²), especial rural (CF art. 191; CC art. 1.239 — 5 anos, até 50ha), familiar (CC art. 1.240-A — 2 anos). Fundamente juridicamente.',
                'fields': [
                    {'name': 'modalidade', 'label': 'Modalidade de Usucapião', 'type': 'select', 'required': True, 'options': ['Extraordinária (CC art. 1.238 - 15/10 anos)', 'Ordinária (CC art. 1.242 - 10/5 anos)', 'Especial Urbana (CF art. 183 - 5 anos, até 250m²)', 'Especial Rural (CF art. 191 - 5 anos, até 50ha)', 'Familiar (CC art. 1.240-A - 2 anos)']},
                    {'name': 'justo_titulo', 'label': 'Justo Título (se usucapião ordinária)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedido de declaração de usucapião',
                'instructions': 'Pedidos: declaração de aquisição da propriedade por usucapião; expedição de mandado de registro ao Cartório de Registro de Imóveis para transcrição; citação dos réus, confrontantes e Fazenda Pública (União, Estado e Município); publicação de edital para citação de eventuais interessados (CPC art. 259, I).',
                'fields': [
                    {'name': 'cartorio_registro', 'label': 'Cartório de Registro de Imóveis Competente', 'type': 'text', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (valor venal do imóvel)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 5. Ação Rescisória
    # =========================================================================
    {
        'doc_type_code': 'acao_rescisoria',
        'name': 'Ação Rescisória - CPC/2015',
        'description': 'Ação para desconstituir decisão de mérito transitada em julgado',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 966-975',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Ação Rescisória',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Tribunal competente',
                'instructions': 'Endereçe ao Tribunal competente para julgar a ação rescisória (CPC art. 968, I): se a decisão rescindenda foi proferida por juiz de primeiro grau, ao Tribunal de Justiça ou TRF; se proferida por tribunal, ao próprio tribunal ou ao tribunal superior. Identifique o autor e o réu.',
                'fields': [
                    {'name': 'tribunal', 'label': 'Tribunal Competente', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'decisao_rescindenda',
                'name': 'I - Da Decisão Rescindenda',
                'description': 'Identificação da decisão a ser rescindida',
                'instructions': 'Identifique a decisão rescindenda: número do processo originário, juízo ou órgão prolator, data da decisão, data do trânsito em julgado. Atente para o prazo decadencial de 2 anos (CPC art. 975). Comprove o depósito de 5% do valor da causa (CPC art. 968, II).',
                'fields': [
                    {'name': 'numero_processo_originario', 'label': 'Número do Processo Originário', 'type': 'text', 'required': True},
                    {'name': 'orgao_prolator', 'label': 'Juízo/Órgão Prolator', 'type': 'text', 'required': True},
                    {'name': 'data_transito_julgado', 'label': 'Data do Trânsito em Julgado', 'type': 'text', 'required': True},
                    {'name': 'resumo_decisao', 'label': 'Resumo da Decisão Rescindenda', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'hipotese_legal',
                'name': 'II - Da Hipótese Legal de Rescisão',
                'description': 'Enquadramento nas hipóteses do art. 966 do CPC',
                'instructions': 'Enquadre o pedido rescisório em uma ou mais hipóteses do CPC art. 966: prevaricação, concussão ou corrupção do juiz (I); impedimento ou incompetência absoluta (II); dolo ou coação da parte vencedora (III); simulação ou colusão (IV); violação manifesta de norma jurídica (V); prova falsa (VI); prova nova (VII); erro de fato (VIII).',
                'fields': [
                    {'name': 'hipotese_rescisao', 'label': 'Hipótese Legal (CPC art. 966)', 'type': 'select', 'required': True, 'options': ['I - Prevaricação, concussão ou corrupção do juiz', 'II - Impedimento ou incompetência absoluta', 'III - Dolo ou coação da parte vencedora', 'IV - Simulação ou colusão', 'V - Violação manifesta de norma jurídica', 'VI - Prova falsa', 'VII - Prova nova', 'VIII - Erro de fato']},
                ],
            },
            {
                'number': 4, 'key': 'fundamentacao',
                'name': 'III - Da Fundamentação',
                'description': 'Fundamentação jurídica da rescisão',
                'instructions': 'Fundamente detalhadamente a hipótese de rescisão escolhida. Para violação de norma jurídica (V): identifique a norma violada e demonstre a violação manifesta. Para prova nova (VII): demonstre que a prova é capaz de assegurar pronunciamento favorável e que a parte não a utilizou no processo por motivo de força maior. Para erro de fato (VIII): demonstre que o erro é verificável no exame dos autos.',
                'fields': [
                    {'name': 'fundamentacao', 'label': 'Fundamentação Detalhada', 'type': 'textarea', 'required': True},
                    {'name': 'norma_violada', 'label': 'Norma Jurídica Violada (se hipótese V)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos rescisório e rescindendo',
                'instructions': 'Pedidos: juízo rescindendo (desconstituição da decisão) e juízo rescisório (novo julgamento da causa, se cabível — CPC art. 968, I). Requeira tutela provisória se houver risco de dano (CPC art. 969). Comprove o depósito de 5% do valor da causa (CPC art. 968, II). Requeira citação do réu, honorários e custas.',
                'fields': [
                    {'name': 'pedido_rescindente', 'label': 'Pedido Rescindente (desconstituição)', 'type': 'textarea', 'required': True},
                    {'name': 'pedido_rescisorio', 'label': 'Pedido Rescisório (novo julgamento)', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 6. Obrigação de Fazer/Não Fazer
    # =========================================================================
    {
        'doc_type_code': 'obrigacao_fazer_nao_fazer',
        'name': 'Ação de Obrigação de Fazer/Não Fazer - CPC/2015',
        'description': 'Ação para compelir o réu ao cumprimento de obrigação de fazer ou para cessar conduta ilícita',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 497, 536-537; CC/2002, arts. 247-249',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Obrigação de Fazer/Não Fazer',
        'secondary_area_codes': ['consumidor'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Juízo competente e qualificação das partes',
                'instructions': 'Endereçe ao Juízo Cível competente. Qualifique autor e réu com dados completos.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Autor', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Réu', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Dados completos das partes',
                'instructions': 'Qualifique as partes com dados completos: nacionalidade, estado civil, profissão, CPF/CNPJ, RG, endereço.',
                'fields': [
                    {'name': 'autor_qualificacao', 'label': 'Qualificação Completa do Autor', 'type': 'textarea', 'required': True},
                    {'name': 'reu_qualificacao', 'label': 'Qualificação Completa do Réu', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'obrigacao',
                'name': 'I - Da Obrigação',
                'description': 'Identificação e origem da obrigação',
                'instructions': 'Identifique a obrigação: de fazer (CC art. 247) ou não fazer (CC art. 251). Descreva sua origem: contratual, legal, judicial ou regulamentar. Especifique com precisão o que o réu deve fazer ou deixar de fazer, com prazo e condições.',
                'fields': [
                    {'name': 'tipo_obrigacao', 'label': 'Tipo de Obrigação', 'type': 'select', 'required': True, 'options': ['Obrigação de Fazer', 'Obrigação de Não Fazer']},
                    {'name': 'origem_obrigacao', 'label': 'Origem da Obrigação (contrato, lei, regulamento)', 'type': 'text', 'required': True},
                    {'name': 'descricao_obrigacao', 'label': 'Descrição da Obrigação (o que deve ser feito/cessado)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'descumprimento',
                'name': 'II - Do Descumprimento',
                'description': 'Narrativa do descumprimento da obrigação',
                'instructions': 'Narre o descumprimento: quando deveria ter sido cumprida, notificações enviadas, mora do devedor (CC art. 394). Para obrigação de não fazer, descreva a conduta praticada em violação. Demonstre os danos sofridos pelo descumprimento.',
                'fields': [
                    {'name': 'descricao_descumprimento', 'label': 'Descrição do Descumprimento', 'type': 'textarea', 'required': True},
                    {'name': 'notificacao_previa', 'label': 'Houve Notificação Prévia?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'danos_sofridos', 'label': 'Danos Sofridos pelo Descumprimento', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 5, 'key': 'tutela_especifica',
                'name': 'III - Da Tutela Específica',
                'description': 'Pedido de tutela específica e medidas coercitivas',
                'instructions': 'Requeira a tutela específica da obrigação (CPC art. 497): determinação judicial para cumprimento. Requeira a fixação de multa diária (astreintes — CPC art. 537) para o caso de descumprimento, indicando valor sugerido. Se a obrigação puder ser convertida em perdas e danos (CC art. 248), mencione subsidiariamente.',
                'fields': [
                    {'name': 'valor_astreintes', 'label': 'Valor Sugerido para Multa Diária (R$)', 'type': 'text', 'required': True},
                    {'name': 'prazo_cumprimento', 'label': 'Prazo para Cumprimento (dias)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 6, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos de cumprimento e cominação',
                'instructions': 'Pedidos: tutela provisória de urgência para cumprimento imediato (CPC art. 300), se cabível; no mérito, condenação do réu ao cumprimento da obrigação de fazer/não fazer, sob pena de multa diária (CPC art. 537); subsidiariamente, conversão em perdas e danos (CC art. 248); honorários e custas.',
                'fields': [
                    {'name': 'pedido_tutela_urgencia', 'label': 'Requer Tutela de Urgência?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 7. Cumprimento de Sentença
    # =========================================================================
    {
        'doc_type_code': 'cumprimento_sentenca',
        'name': 'Cumprimento de Sentença - CPC/2015',
        'description': 'Requerimento de cumprimento de sentença condenatória para pagamento de quantia certa',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 513-538',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Cumprimento de Sentença',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Juízo competente e identificação do processo',
                'instructions': 'Endereçe ao Juízo que proferiu a sentença exequenda (CPC art. 516, II) ou ao juízo do domicílio do executado (art. 516, parágrafo único). Identifique o processo de conhecimento, o exequente e o executado.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo (Vara e Comarca)', 'type': 'text', 'required': True},
                    {'name': 'numero_processo', 'label': 'Número do Processo de Conhecimento', 'type': 'text', 'required': True},
                    {'name': 'exequente_nome', 'label': 'Nome do Exequente (Credor)', 'type': 'text', 'required': True},
                    {'name': 'executado_nome', 'label': 'Nome do Executado (Devedor)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'sentenca',
                'name': 'I - Da Sentença',
                'description': 'Identificação da sentença exequenda',
                'instructions': 'Identifique a sentença: data, teor condenatório, trânsito em julgado (ou justificativa para cumprimento provisório — CPC art. 520). Informe se houve recursos e seu resultado. Anexe cópia da sentença e certidão de trânsito em julgado.',
                'fields': [
                    {'name': 'data_sentenca', 'label': 'Data da Sentença', 'type': 'text', 'required': True},
                    {'name': 'tipo_cumprimento', 'label': 'Tipo de Cumprimento', 'type': 'select', 'required': True, 'options': ['Definitivo (trânsito em julgado)', 'Provisório (CPC art. 520)']},
                    {'name': 'teor_condenacao', 'label': 'Teor da Condenação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'calculo_debito',
                'name': 'II - Do Cálculo do Débito',
                'description': 'Demonstrativo atualizado do débito',
                'instructions': 'Apresente a memória discriminada e atualizada do cálculo (CPC art. 524, caput): valor principal, juros moratórios (taxa, período de incidência), correção monetária (índice, período), multa do art. 523, §1º (10% sobre o débito), honorários fixados em sentença. Demonstre o valor total atualizado.',
                'fields': [
                    {'name': 'valor_principal', 'label': 'Valor Principal (R$)', 'type': 'text', 'required': True},
                    {'name': 'indice_correcao', 'label': 'Índice de Correção Monetária', 'type': 'select', 'required': True, 'options': ['IPCA-E', 'INPC', 'Tabela do Tribunal', 'Taxa SELIC']},
                    {'name': 'taxa_juros', 'label': 'Taxa de Juros Moratórios', 'type': 'select', 'required': True, 'options': ['1% ao mês (CC art. 406)', 'Taxa SELIC', 'Taxa fixada em sentença']},
                    {'name': 'valor_total_atualizado', 'label': 'Valor Total Atualizado (R$)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'intimacao_devedor',
                'name': 'III - Da Intimação do Devedor',
                'description': 'Requerimento de intimação para pagamento',
                'instructions': 'Requeira a intimação do executado para pagar o débito em 15 dias (CPC art. 523), sob pena de multa de 10% e honorários advocatícios de 10% (CPC art. 523, §1º). Indique a forma de intimação: pelo Diário da Justiça, na pessoa do advogado, ou pessoalmente (CPC art. 513, §2º).',
                'fields': [
                    {'name': 'forma_intimacao', 'label': 'Forma de Intimação Requerida', 'type': 'select', 'required': True, 'options': ['Diário da Justiça (advogado do executado)', 'Pessoal (carta AR ou oficial de justiça)', 'Eletrônica (portal do tribunal)']},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'IV - Do Pedido',
                'description': 'Pedidos de cumprimento',
                'instructions': 'Pedidos: intimação do executado para pagamento em 15 dias (CPC art. 523); em caso de não pagamento, incidência de multa de 10% e honorários de 10% (art. 523, §1º); penhora de bens suficientes (art. 523, §3º); expedição de mandado de penhora e avaliação; inclusão no cadastro de inadimplentes (art. 782, §3º) se cabível.',
                'fields': [
                    {'name': 'bens_conhecidos', 'label': 'Bens do Executado Conhecidos (se houver)', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (valor do débito atualizado)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 8. Tutela Cautelar Antecedente
    # =========================================================================
    {
        'doc_type_code': 'tutela_cautelar_antecedente',
        'name': 'Tutela Cautelar Antecedente - CPC/2015',
        'description': 'Pedido de tutela cautelar em caráter antecedente ao pedido principal',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 305-310',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Tutela Cautelar Antecedente',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Juízo competente e qualificação das partes',
                'instructions': 'Endereçe ao Juízo que seria competente para o pedido principal (CPC art. 305, parágrafo único). Qualifique o requerente e o requerido com dados completos.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo (Vara e Comarca)', 'type': 'text', 'required': True},
                    {'name': 'requerente_nome', 'label': 'Nome do Requerente', 'type': 'text', 'required': True},
                    {'name': 'requerido_nome', 'label': 'Nome do Requerido', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Dados completos de requerente e requerido',
                'instructions': 'Qualifique as partes com dados completos. Indique o pedido principal a ser formulado posteriormente (CPC art. 305) e a lide a que se refere.',
                'fields': [
                    {'name': 'requerente_qualificacao', 'label': 'Qualificação Completa do Requerente', 'type': 'textarea', 'required': True},
                    {'name': 'requerido_qualificacao', 'label': 'Qualificação Completa do Requerido', 'type': 'textarea', 'required': True},
                    {'name': 'indicacao_pedido_principal', 'label': 'Indicação do Pedido Principal (CPC art. 305)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'urgencia',
                'name': 'I - Da Urgência',
                'description': 'Demonstração da situação de urgência',
                'instructions': 'Demonstre a situação de urgência contemporânea que justifica a medida cautelar antes da formulação do pedido principal (CPC art. 305). Narre os fatos que evidenciam a probabilidade do direito (fumus boni iuris) e explique por que a medida cautelar não pode aguardar a propositura da ação principal.',
                'fields': [
                    {'name': 'descricao_urgencia', 'label': 'Descrição da Situação de Urgência', 'type': 'textarea', 'required': True},
                    {'name': 'probabilidade_direito', 'label': 'Probabilidade do Direito (fumus boni iuris)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'perigo_dano',
                'name': 'II - Do Perigo de Dano',
                'description': 'Demonstração do risco ao resultado útil do processo',
                'instructions': 'Demonstre o perigo de dano ou risco ao resultado útil do processo (periculum in mora — CPC art. 300). Evidencie que a demora na concessão da medida pode tornar ineficaz o provimento jurisdicional definitivo. Descreva concretamente o dano iminente e sua irreversibilidade.',
                'fields': [
                    {'name': 'descricao_perigo', 'label': 'Descrição do Perigo de Dano', 'type': 'textarea', 'required': True},
                    {'name': 'irreversibilidade', 'label': 'Risco de Irreversibilidade', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido_cautelar',
                'name': 'III - Do Pedido Cautelar',
                'description': 'Medida cautelar requerida',
                'instructions': 'Especifique a medida cautelar requerida: arresto, sequestro, arrolamento de bens, produção antecipada de provas ou outra medida idônea (CPC art. 301). Indique o prazo de 30 dias para formulação do pedido principal (CPC art. 308). Requeira a citação do requerido para contestar em 5 dias (CPC art. 306).',
                'fields': [
                    {'name': 'medida_requerida', 'label': 'Medida Cautelar Requerida', 'type': 'select', 'required': True, 'options': ['Arresto de Bens', 'Sequestro de Bens', 'Arrolamento de Bens', 'Registro de Protesto contra Alienação', 'Outra Medida Idônea']},
                    {'name': 'bens_objeto', 'label': 'Bens Objeto da Medida (se aplicável)', 'type': 'textarea', 'required': False},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 9. Tutela de Evidência
    # =========================================================================
    {
        'doc_type_code': 'tutela_evidencia',
        'name': 'Tutela de Evidência - CPC/2015',
        'description': 'Pedido de tutela provisória fundada na evidência do direito, independente de urgência',
        'version': '1.0',
        'legal_basis': 'CPC/2015, art. 311',
        'primary_color': '#2563EB',
        'secondary_color': '#3B82F6',
        'cover_title': 'Tutela de Evidência',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Juízo competente e qualificação das partes',
                'instructions': 'Endereçe ao Juízo competente. Qualifique o requerente e o requerido. A tutela de evidência pode ser requerida na petição inicial ou incidentalmente.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo (Vara e Comarca)', 'type': 'text', 'required': True},
                    {'name': 'requerente_nome', 'label': 'Nome do Requerente', 'type': 'text', 'required': True},
                    {'name': 'requerido_nome', 'label': 'Nome do Requerido', 'type': 'text', 'required': True},
                    {'name': 'numero_processo', 'label': 'Número do Processo (se incidental)', 'type': 'text', 'required': False},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Dados completos das partes',
                'instructions': 'Qualifique as partes com dados completos. Se o pedido for incidental, faça referência aos autos.',
                'fields': [
                    {'name': 'requerente_qualificacao', 'label': 'Qualificação Completa do Requerente', 'type': 'textarea', 'required': True},
                    {'name': 'requerido_qualificacao', 'label': 'Qualificação Completa do Requerido', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'direito_evidente',
                'name': 'I - Do Direito Evidente',
                'description': 'Demonstração da evidência do direito',
                'instructions': 'Demonstre que o direito do requerente é evidente, dispensando a demonstração de urgência (CPC art. 311). Apresente as provas documentais que comprovam o direito de forma inequívoca. Não é necessário demonstrar periculum in mora — basta a evidência do direito.',
                'fields': [
                    {'name': 'descricao_direito', 'label': 'Descrição do Direito Evidente', 'type': 'textarea', 'required': True},
                    {'name': 'provas_documentais', 'label': 'Provas Documentais que Comprovam o Direito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'hipotese_legal',
                'name': 'II - Da Hipótese Legal',
                'description': 'Enquadramento nas hipóteses do art. 311 do CPC',
                'instructions': 'Enquadre o pedido em uma das hipóteses do CPC art. 311: abuso do direito de defesa ou propósito protelatório (I); alegações comprovadas por prova documental e tese firmada em repetitivos ou súmula vinculante (II); pedido reipersecutório com prova documental (III); petição inicial instruída com prova suficiente contra a qual o réu não oponha prova inequívoca (IV).',
                'fields': [
                    {'name': 'hipotese_evidencia', 'label': 'Hipótese Legal (CPC art. 311)', 'type': 'select', 'required': True, 'options': ['I - Abuso do direito de defesa ou propósito protelatório', 'II - Tese firmada em repetitivos/súmula vinculante + prova documental', 'III - Pedido reipersecutório com prova documental', 'IV - Prova documental suficiente sem contraprova inequívoca']},
                    {'name': 'fundamentacao_hipotese', 'label': 'Fundamentação da Hipótese Escolhida', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'III - Do Pedido',
                'description': 'Pedido de concessão da tutela de evidência',
                'instructions': 'Pedidos: concessão da tutela de evidência (CPC art. 311) para antecipar os efeitos práticos do provimento final; nas hipóteses II e III, a tutela pode ser concedida liminarmente (art. 311, parágrafo único). Especifique os efeitos práticos pretendidos.',
                'fields': [
                    {'name': 'efeitos_praticos', 'label': 'Efeitos Práticos Pretendidos', 'type': 'textarea', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 10. Produção Antecipada de Provas
    # =========================================================================
    {
        'doc_type_code': 'producao_antecipada_provas',
        'name': 'Produção Antecipada de Provas - CPC/2015',
        'description': 'Ação autônoma para produção antecipada de prova antes ou durante o processo',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 381-383',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Produção Antecipada de Provas',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Juízo competente e qualificação das partes',
                'instructions': 'Endereçe ao Juízo que seria competente para a ação principal. Qualifique o requerente e o requerido com dados completos.',
                'fields': [
                    {'name': 'juizo', 'label': 'Juízo (Vara e Comarca)', 'type': 'text', 'required': True},
                    {'name': 'requerente_nome', 'label': 'Nome do Requerente', 'type': 'text', 'required': True},
                    {'name': 'requerido_nome', 'label': 'Nome do Requerido', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'qualificacao',
                'name': 'Qualificação das Partes',
                'description': 'Dados completos das partes',
                'instructions': 'Qualifique requerente e requerido com dados completos. Indique o interesse e a relação jurídica entre as partes.',
                'fields': [
                    {'name': 'requerente_qualificacao', 'label': 'Qualificação Completa do Requerente', 'type': 'textarea', 'required': True},
                    {'name': 'requerido_qualificacao', 'label': 'Qualificação Completa do Requerido', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'prova_a_produzir',
                'name': 'I - Da Prova a Produzir',
                'description': 'Identificação da prova a ser produzida antecipadamente',
                'instructions': 'Identifique a prova que se pretende produzir: pericial, testemunhal, documental, inspeção judicial. Descreva com precisão o objeto da prova, os fatos que se pretende provar e os quesitos (se perícia). Indique se há necessidade de nomeação de perito e assistentes técnicos.',
                'fields': [
                    {'name': 'tipo_prova', 'label': 'Tipo de Prova a Produzir', 'type': 'select', 'required': True, 'options': ['Pericial', 'Testemunhal', 'Documental', 'Inspeção Judicial']},
                    {'name': 'objeto_prova', 'label': 'Objeto da Prova (o que se pretende provar)', 'type': 'textarea', 'required': True},
                    {'name': 'quesitos', 'label': 'Quesitos (se pericial)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 4, 'key': 'urgencia_justificativa',
                'name': 'II - Da Urgência/Justificativa',
                'description': 'Justificativa para a produção antecipada',
                'instructions': 'Fundamente a produção antecipada em uma das hipóteses do CPC art. 381: risco de perecimento da prova (I — fundado receio de que a prova se torne impossível ou muito difícil); conhecimento prévio dos fatos para justificar ou evitar o ajuizamento de ação (II); natureza do litígio permite autocomposição ou outra solução adequada (III). Demonstre concretamente a situação.',
                'fields': [
                    {'name': 'hipotese_legal', 'label': 'Hipótese Legal (CPC art. 381)', 'type': 'select', 'required': True, 'options': ['I - Risco de perecimento da prova', 'II - Conhecimento prévio para justificar/evitar ação', 'III - Viabilizar autocomposição ou solução adequada']},
                    {'name': 'justificativa', 'label': 'Justificativa Detalhada', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 5, 'key': 'pedido',
                'name': 'III - Do Pedido',
                'description': 'Pedido de produção antecipada',
                'instructions': 'Pedidos: deferimento da produção antecipada da prova requerida; citação do requerido para acompanhar a produção da prova (CPC art. 382); nomeação de perito (se prova pericial); designação de audiência (se prova testemunhal); homologação da prova produzida. Não há condenação em honorários (CPC art. 382, §2º).',
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    # =========================================================================
    # 11. Contrarrazões de Agravo de Instrumento
    # =========================================================================
    {
        'doc_type_code': 'contrarrazoes_agravo_instrumento',
        'name': 'Contrarrazões de Agravo de Instrumento - CPC/2015',
        'description': 'Resposta ao agravo de instrumento interposto pela parte adversa',
        'version': '1.0',
        'legal_basis': 'CPC/2015, art. 1.019, II',
        'primary_color': '#2563EB',
        'secondary_color': '#3B82F6',
        'cover_title': 'Contrarrazões de Agravo de Instrumento',
        'secondary_area_codes': ['recursos'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Tribunal e identificação do recurso',
                'instructions': 'Endereçe ao Tribunal competente (Desembargador Relator). Identifique o número do agravo de instrumento, o processo de origem, o agravante e o agravado (contrarrazoante).',
                'fields': [
                    {'name': 'tribunal', 'label': 'Tribunal', 'type': 'text', 'required': True},
                    {'name': 'numero_agravo', 'label': 'Número do Agravo de Instrumento', 'type': 'text', 'required': True},
                    {'name': 'numero_processo_origem', 'label': 'Número do Processo de Origem', 'type': 'text', 'required': True},
                    {'name': 'agravante_nome', 'label': 'Nome do Agravante', 'type': 'text', 'required': True},
                    {'name': 'agravado_nome', 'label': 'Nome do Agravado (Contrarrazoante)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'decisao_agravada',
                'name': 'I - Da Decisão Agravada',
                'description': 'Síntese da decisão interlocutória e do agravo',
                'instructions': 'Resuma a decisão interlocutória agravada: conteúdo, fundamentos do juízo de primeiro grau. Sintetize os argumentos do agravante: teses recursais, pedidos formulados no agravo, eventual pedido de efeito suspensivo ou tutela recursal.',
                'fields': [
                    {'name': 'resumo_decisao', 'label': 'Resumo da Decisão Agravada', 'type': 'textarea', 'required': True},
                    {'name': 'argumentos_agravante', 'label': 'Principais Argumentos do Agravante', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'contrarrazoes',
                'name': 'II - Das Contrarrazões',
                'description': 'Refutação dos argumentos do agravante',
                'instructions': 'Refute ponto a ponto os argumentos do agravante. Demonstre que a decisão agravada está correta, fundamentada e não merece reforma. Se houver preliminares (intempestividade, não cabimento, ausência de peça obrigatória — CPC art. 1.017), arguia-as previamente. Fundamente com legislação, doutrina e jurisprudência.',
                'fields': [
                    {'name': 'preliminares', 'label': 'Preliminares (intempestividade, não cabimento, etc.)', 'type': 'textarea', 'required': False},
                    {'name': 'refutacao_merito', 'label': 'Refutação dos Argumentos de Mérito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'pedido',
                'name': 'III - Do Pedido',
                'description': 'Pedido de desprovimento do agravo',
                'instructions': 'Pedidos: conhecimento e desprovimento do agravo de instrumento; manutenção integral da decisão agravada; condenação do agravante em honorários recursais (CPC art. 85, §11). Se houver efeito suspensivo concedido, requeira sua revogação.',
                'fields': [],
            },
        ],
    },
    # =========================================================================
    # 12. Contrarrazões de Recurso Especial
    # =========================================================================
    {
        'doc_type_code': 'contrarrazoes_recurso_especial',
        'name': 'Contrarrazões de Recurso Especial - CPC/2015',
        'description': 'Resposta ao recurso especial interposto pela parte adversa perante o STJ',
        'version': '1.0',
        'legal_basis': 'CPC/2015, art. 1.030; CF/88, art. 105, III',
        'primary_color': '#7030A0',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Contrarrazões de Recurso Especial',
        'secondary_area_codes': ['recursos'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Tribunal e identificação do recurso',
                'instructions': 'Endereçe ao Presidente/Vice-Presidente do Tribunal de origem (juízo de admissibilidade) ou ao Ministro Relator do STJ. Identifique o número do recurso especial, o processo de origem, o recorrente e o recorrido (contrarrazoante).',
                'fields': [
                    {'name': 'tribunal', 'label': 'Tribunal de Origem', 'type': 'text', 'required': True},
                    {'name': 'numero_recurso', 'label': 'Número do Recurso Especial', 'type': 'text', 'required': True},
                    {'name': 'numero_processo', 'label': 'Número do Processo de Origem', 'type': 'text', 'required': True},
                    {'name': 'recorrente_nome', 'label': 'Nome do Recorrente', 'type': 'text', 'required': True},
                    {'name': 'recorrido_nome', 'label': 'Nome do Recorrido (Contrarrazoante)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'acordao_recorrido',
                'name': 'I - Do Acórdão Recorrido',
                'description': 'Síntese do acórdão e dos argumentos do recorrente',
                'instructions': 'Resuma o acórdão recorrido: ementa, fundamentos, resultado do julgamento. Sintetize os argumentos do recorrente: alíneas invocadas (CF art. 105, III, a, b ou c), dispositivos legais supostamente violados, divergência jurisprudencial alegada.',
                'fields': [
                    {'name': 'resumo_acordao', 'label': 'Resumo do Acórdão Recorrido', 'type': 'textarea', 'required': True},
                    {'name': 'alineas_invocadas', 'label': 'Alíneas Invocadas pelo Recorrente', 'type': 'select', 'required': True, 'options': ['a) Contrariar tratado ou lei federal', 'b) Julgar válido ato de governo local contestado em face de lei federal', 'c) Divergência jurisprudencial']},
                    {'name': 'argumentos_recorrente', 'label': 'Argumentos do Recorrente', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'contrarrazoes',
                'name': 'II - Das Contrarrazões',
                'description': 'Refutação dos argumentos do recorrente',
                'instructions': 'Refute os argumentos do recorrente. Arguia preliminares de inadmissibilidade: Súmula 7/STJ (reexame de provas), Súmula 83/STJ (jurisprudência consolidada), Súmula 211/STJ (prequestionamento), deficiência na fundamentação, intempestividade. No mérito, demonstre que o acórdão recorrido está correto e não violou lei federal.',
                'fields': [
                    {'name': 'preliminares_inadmissibilidade', 'label': 'Preliminares de Inadmissibilidade (Súmulas 7, 83, 211/STJ, etc.)', 'type': 'textarea', 'required': False},
                    {'name': 'refutacao_merito', 'label': 'Refutação dos Argumentos de Mérito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'pedido',
                'name': 'III - Do Pedido',
                'description': 'Pedido de não admissão ou desprovimento',
                'instructions': 'Pedidos: não admissão do recurso especial (juízo de admissibilidade negativo) pelo Tribunal de origem; subsidiariamente, desprovimento do recurso pelo STJ; manutenção integral do acórdão recorrido; condenação do recorrente em honorários recursais (CPC art. 85, §11).',
                'fields': [],
            },
        ],
    },
    # =========================================================================
    # 13. Contrarrazões de Recurso Extraordinário
    # =========================================================================
    {
        'doc_type_code': 'contrarrazoes_recurso_extraordinario',
        'name': 'Contrarrazões de Recurso Extraordinário - CPC/2015',
        'description': 'Resposta ao recurso extraordinário interposto pela parte adversa perante o STF',
        'version': '1.0',
        'legal_basis': 'CPC/2015, art. 1.030; CF/88, art. 102, III',
        'primary_color': '#7030A0',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Contrarrazões de Recurso Extraordinário',
        'secondary_area_codes': ['recursos'],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Tribunal e identificação do recurso',
                'instructions': 'Endereçe ao Presidente/Vice-Presidente do Tribunal de origem (juízo de admissibilidade) ou ao Ministro Relator do STF. Identifique o número do recurso extraordinário, o processo de origem, o recorrente e o recorrido (contrarrazoante).',
                'fields': [
                    {'name': 'tribunal', 'label': 'Tribunal de Origem', 'type': 'text', 'required': True},
                    {'name': 'numero_recurso', 'label': 'Número do Recurso Extraordinário', 'type': 'text', 'required': True},
                    {'name': 'numero_processo', 'label': 'Número do Processo de Origem', 'type': 'text', 'required': True},
                    {'name': 'recorrente_nome', 'label': 'Nome do Recorrente', 'type': 'text', 'required': True},
                    {'name': 'recorrido_nome', 'label': 'Nome do Recorrido (Contrarrazoante)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'acordao_recorrido',
                'name': 'I - Do Acórdão Recorrido',
                'description': 'Síntese do acórdão e dos argumentos do recorrente',
                'instructions': 'Resuma o acórdão recorrido: ementa, fundamentos, resultado. Sintetize os argumentos do recorrente: alíneas invocadas (CF art. 102, III, a, b, c ou d), dispositivos constitucionais supostamente violados, repercussão geral alegada.',
                'fields': [
                    {'name': 'resumo_acordao', 'label': 'Resumo do Acórdão Recorrido', 'type': 'textarea', 'required': True},
                    {'name': 'alineas_invocadas', 'label': 'Alíneas Invocadas pelo Recorrente', 'type': 'select', 'required': True, 'options': ['a) Contrariar dispositivo da Constituição', 'b) Declarar inconstitucionalidade de tratado ou lei federal', 'c) Julgar válida lei ou ato de governo local contestado em face da CF', 'd) Julgar válida lei local contestada em face de lei federal']},
                    {'name': 'argumentos_recorrente', 'label': 'Argumentos do Recorrente', 'type': 'textarea', 'required': True},
                    {'name': 'repercussao_geral', 'label': 'Repercussão Geral Alegada pelo Recorrente', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'contrarrazoes',
                'name': 'II - Das Contrarrazões',
                'description': 'Refutação dos argumentos do recorrente',
                'instructions': 'Refute os argumentos do recorrente. Arguia preliminares de inadmissibilidade: ausência de repercussão geral (CF art. 102, §3º), ausência de prequestionamento (Súmula 282/STF), ofensa reflexa à Constituição (violação indireta), deficiência na fundamentação. No mérito, demonstre que o acórdão recorrido é constitucional e correto.',
                'fields': [
                    {'name': 'preliminares_inadmissibilidade', 'label': 'Preliminares de Inadmissibilidade', 'type': 'textarea', 'required': False},
                    {'name': 'ausencia_repercussao', 'label': 'Ausência de Repercussão Geral (se aplicável)', 'type': 'textarea', 'required': False},
                    {'name': 'refutacao_merito', 'label': 'Refutação dos Argumentos de Mérito', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'pedido',
                'name': 'III - Do Pedido',
                'description': 'Pedido de não admissão ou desprovimento',
                'instructions': 'Pedidos: não admissão do recurso extraordinário pelo Tribunal de origem; negativa de repercussão geral; subsidiariamente, desprovimento do recurso pelo STF; manutenção integral do acórdão recorrido; condenação do recorrente em honorários recursais (CPC art. 85, §11).',
                'fields': [],
            },
        ],
    },
    # =========================================================================
    # 14. Embargos de Divergência
    # =========================================================================
    {
        'doc_type_code': 'embargos_divergencia',
        'name': 'Embargos de Divergência - CPC/2015',
        'description': 'Recurso para uniformização de jurisprudência no STJ ou STF em caso de divergência entre turmas',
        'version': '1.0',
        'legal_basis': 'CPC/2015, arts. 1.043-1.044',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Embargos de Divergência',
        'secondary_area_codes': [],
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento',
                'description': 'Tribunal Superior e identificação do recurso',
                'instructions': 'Endereçe ao Ministro Relator do acórdão embargado no STJ ou STF. Identifique o número do recurso originário (REsp/RE), o embargante e o embargado. Os embargos de divergência cabem de acórdão que, em recurso especial ou extraordinário, divergir de julgamento de outra turma, seção ou do plenário (CPC art. 1.043).',
                'fields': [
                    {'name': 'tribunal', 'label': 'Tribunal (STJ ou STF)', 'type': 'select', 'required': True, 'options': ['STJ', 'STF']},
                    {'name': 'numero_recurso', 'label': 'Número do Recurso Originário (REsp/RE)', 'type': 'text', 'required': True},
                    {'name': 'embargante_nome', 'label': 'Nome do Embargante', 'type': 'text', 'required': True},
                    {'name': 'embargado_nome', 'label': 'Nome do Embargado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'acordao_embargado',
                'name': 'I - Do Acórdão Embargado',
                'description': 'Identificação e síntese do acórdão impugnado',
                'instructions': 'Identifique o acórdão embargado: turma julgadora, relator, data do julgamento, ementa, tese jurídica adotada. Demonstre a matéria de direito objeto da divergência.',
                'fields': [
                    {'name': 'turma_julgadora', 'label': 'Turma Julgadora', 'type': 'text', 'required': True},
                    {'name': 'relator', 'label': 'Ministro Relator', 'type': 'text', 'required': True},
                    {'name': 'data_julgamento', 'label': 'Data do Julgamento', 'type': 'text', 'required': True},
                    {'name': 'tese_adotada', 'label': 'Tese Jurídica Adotada no Acórdão Embargado', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'divergencia',
                'name': 'II - Da Divergência',
                'description': 'Demonstração da divergência jurisprudencial',
                'instructions': 'Demonstre a divergência: identifique o(s) acórdão(s) paradigma(s) — outra turma, seção, órgão especial ou plenário do mesmo tribunal — que adotou(aram) tese jurídica diversa sobre a mesma questão de direito (CPC art. 1.043, I, II, III ou IV). Faça o cotejo analítico entre as teses divergentes, demonstrando a similitude fática e a diversidade na interpretação jurídica.',
                'fields': [
                    {'name': 'acordao_paradigma', 'label': 'Acórdão(s) Paradigma(s) (número, turma, relator)', 'type': 'textarea', 'required': True},
                    {'name': 'tese_paradigma', 'label': 'Tese Jurídica do Paradigma', 'type': 'textarea', 'required': True},
                    {'name': 'cotejo_analitico', 'label': 'Cotejo Analítico (similitude fática e divergência jurídica)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'pedido',
                'name': 'III - Do Pedido',
                'description': 'Pedido de provimento dos embargos',
                'instructions': 'Pedidos: conhecimento e provimento dos embargos de divergência; uniformização da jurisprudência no sentido da tese do paradigma; reforma do acórdão embargado; condenação do embargado em honorários.',
                'fields': [],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Peças Cíveis e Procedimentais Complementares no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Cível: Complemento'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN\n'))
            return
        with transaction.atomic():
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)
        self.stdout.write(self.style.SUCCESS('\n✓ Cível: Complemento concluído!\n'))

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
            {'key': 'gerador_civel_complemento', 'name': 'Verus.AI - Gerador Cível Complemento', 'description': 'Gera peças cíveis complementares: réplica, embargos de terceiro, possessória, usucapião, rescisória, obrigação de fazer, cumprimento de sentença, tutelas e contrarrazões', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_CIVEL_COMPLEMENTO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
            # Garante is_default=True em re-execução
            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {blueprint.name}')
            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_civel_complemento')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
