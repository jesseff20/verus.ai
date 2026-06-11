"""
Seed Digital/LGPD e Empresarial — Verus.AI.

Uso:
    python manage.py seed_digital_lgpd_empresarial
    python manage.py seed_digital_lgpd_empresarial --force
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
        'code': 'digital_lgpd',
        'name': 'Digital e LGPD',
        'description': 'Peças e documentos de Direito Digital, Proteção de Dados e LGPD',
        'display_order': 14,
    },
    {
        'code': 'empresarial',
        'name': 'Empresarial',
        'description': 'Documentos jurídicos empresariais e societários',
        'display_order': 15,
    },
]

TIPOS_DOCUMENTO = [
    {
        'code': 'politica_privacidade_lgpd',
        'name': 'Política de Privacidade LGPD',
        'short_name': 'Política Privacidade',
        'description': 'Documento de política de privacidade conforme LGPD',
        'category': 'digital_lgpd',
        'icon': 'Shield',
        'color': '#0891B2',
        'legal_basis': 'LGPD, Lei 13.709/2018; Lei 12.965/2014 (MCI); CF/88, art. 5º X',
        'display_order': 1,
    },
    {
        'code': 'termo_uso_plataforma',
        'name': 'Termos de Uso de Plataforma',
        'short_name': 'Termos de Uso',
        'description': 'Termos e condições de uso de plataforma digital',
        'category': 'digital_lgpd',
        'icon': 'FileText',
        'color': '#0891B2',
        'legal_basis': 'CC/2002, arts. 421-480; Lei 12.965/2014 (MCI); Decreto 7.962/2013',
        'display_order': 2,
    },
    {
        'code': 'dpa_tratamento_dados',
        'name': 'Acordo de Processamento de Dados (DPA)',
        'short_name': 'DPA',
        'description': 'Acordo entre controlador e operador para tratamento de dados pessoais',
        'category': 'digital_lgpd',
        'icon': 'Lock',
        'color': '#0891B2',
        'legal_basis': 'LGPD, arts. 37-40; arts. 5º VI e VII (controlador/operador)',
        'display_order': 3,
    },
    {
        'code': 'resposta_titular_dados',
        'name': 'Resposta a Solicitação de Titular',
        'short_name': 'Resp. Titular',
        'description': 'Resposta formal a exercício de direitos pelo titular de dados',
        'category': 'digital_lgpd',
        'icon': 'MessageSquare',
        'color': '#0891B2',
        'legal_basis': 'LGPD, arts. 18-20; LGPD, art. 19 (prazo 15 dias)',
        'display_order': 4,
    },
    {
        'code': 'notificacao_incidente_lgpd',
        'name': 'Notificação de Incidente de Segurança',
        'short_name': 'Notif. Incidente',
        'description': 'Comunicação de incidente de segurança à ANPD e titulares afetados',
        'category': 'digital_lgpd',
        'icon': 'AlertTriangle',
        'color': '#DC2626',
        'legal_basis': 'LGPD, art. 48; Resolução ANPD 04/2023',
        'display_order': 5,
    },
    {
        'code': 'contrato_prestacao_servicos',
        'name': 'Contrato de Prestação de Serviços',
        'short_name': 'Cont. Serviços',
        'description': 'Contrato civil de prestação de serviços entre pessoas físicas ou jurídicas',
        'category': 'empresarial',
        'icon': 'FileSignature',
        'color': '#374151',
        'legal_basis': 'CC/2002, arts. 593-609 e arts. 421-480; Lei Complementar 123/2006',
        'display_order': 1,
    },
    {
        'code': 'ata_reuniao_societaria',
        'name': 'Ata de Reunião Societária',
        'short_name': 'Ata Societária',
        'description': 'Ata de assembleia ou reunião de sócios/acionistas',
        'category': 'empresarial',
        'icon': 'Users',
        'color': '#374151',
        'legal_basis': 'CC/2002, arts. 1.010-1.021 (Ltda); Lei 6.404/1976 (S/A); Lei 14.195/2021',
        'display_order': 2,
    },
    {
        'code': 'distrato_societario',
        'name': 'Distrato Social / Dissolução',
        'short_name': 'Distrato Social',
        'description': 'Documento de dissolução e encerramento de sociedade',
        'category': 'empresarial',
        'icon': 'FileX',
        'color': '#374151',
        'legal_basis': 'CC/2002, arts. 1.033-1.044; Lei 6.404/1976, arts. 206-219; Instrução Normativa DREI',
        'display_order': 3,
    },
]

USER_TEMPLATE_SECAO = """Gere o conteúdo da seção "{{section_name}}" para a seguinte peça jurídica:

OBJETIVO DO DOCUMENTO: {{objective}}
INFORMAÇÕES DO CASO: {{context}}
SEÇÕES ANTERIORES JÁ GERADAS: {{previous_sections}}

Instruções específicas: {{instructions}}

Gere apenas o conteúdo desta seção, com linguagem jurídica formal e completa."""

CONST_ANTI_ALUCINACAO = """DIRETRIZES DE SEGURANÇA JURÍDICA — OBRIGATÓRIAS:
- NUNCA invente acórdão, número de processo, relator, Súmula ou resolução inexistentes
- Dado faltante: [INFORMAÇÃO NECESSÁRIA: descrição]
- Jurisprudência: [PESQUISAR JURISPRUDÊNCIA: tema]
- Conteúdo inferido: [VERIFICAR COM ADVOGADO]
"""

PROMPT_GERADOR_DIGITAL_LGPD = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Digital e Proteção de Dados (LGPD) brasileiro.

LEGISLAÇÃO VIGENTE:
- LGPD, Lei 13.709/2018 e Lei 13.853/2019 (alteração); CF/88, art. 5º X, XII, LXXII
- Lei 12.965/2014 (Marco Civil da Internet); Decreto 8.771/2016
- Lei 12.737/2012 (crimes informáticos); Resoluções da ANPD

REGRAS ESSENCIAIS:
1. Bases legais tratamento: LGPD art. 7º (dados pessoais) — lista EXAUSTIVA; art. 11 (dados sensíveis)
2. Direitos do titular: LGPD art. 18 (confirmação, acesso, correção, anonimização, portabilidade, eliminação, informação, revisão)
3. Dados sensíveis: LGPD art. 11 (origem racial, convicção religiosa, saúde, biometria, etc.)
4. Agentes: controlador (art. 5º VI) e operador (art. 5º VII); DPO/Encarregado (art. 41)
5. Sanções ANPD: LGPD art. 52 (advertência, multa 2% faturamento até 50MM, bloqueio)
6. Incidente: LGPD art. 48 + Resolução ANPD 04/2023 (comunicação em prazo razoável)
7. Consentimento: LGPD art. 8º (livre, informado, inequívoco) — revogável a qualquer tempo
8. Transferência internacional: LGPD arts. 33-36
9. Prazo resposta ao titular: LGPD art. 19 (imediato ou até 15 dias)

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_GERADOR_EMPRESARIAL = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Empresarial e Societário brasileiro.

LEGISLAÇÃO VIGENTE:
- CC/2002, Livro II (Direito de Empresa, arts. 966-1.195); Lei 6.404/1976 (S/A)
- Lei Complementar 123/2006 (Simples Nacional/MEI); Lei 14.195/2021 (Lei do Ambiente de Negócios)
- Instrução Normativa DREI (Departamento de Registro Empresarial)
- CPC/2015 (subsidiário em dissoluções judiciais)

REGRAS ESSENCIAIS:
1. Contratos: função social (CC art. 421), boa-fé objetiva (CC art. 422), relatividade
2. Soc. Limitada: CC/2002 arts. 1.052-1.087. Deliberações por maioria (art. 1.076)
3. S/A: Lei 6.404/1976. Assembleia geral: convocação, quórum, ata (arts. 124-135)
4. Distrato/dissolução Ltda: CC art. 1.033 (hipóteses) e art. 1.034 (judicial)
5. Dissolução S/A: Lei 6.404/1976, arts. 206-219
6. Contratos de prestação de serviços: CC arts. 593-609
7. Cláusulas essenciais: objeto, preço, prazo, rescisão, responsabilidades, foro
8. Sigilo empresarial: Lei 9.279/1996 (propriedade industrial); LC 123/2006

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'politica_privacidade_lgpd': 'gerador_digital_lgpd',
    'termo_uso_plataforma': 'gerador_digital_lgpd',
    'dpa_tratamento_dados': 'gerador_digital_lgpd',
    'resposta_titular_dados': 'gerador_digital_lgpd',
    'notificacao_incidente_lgpd': 'gerador_digital_lgpd',
    'contrato_prestacao_servicos': 'gerador_empresarial',
    'ata_reuniao_societaria': 'gerador_empresarial',
    'distrato_societario': 'gerador_empresarial',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'politica_privacidade_lgpd',
        'name': 'Política de Privacidade LGPD - Lei 13.709/2018',
        'description': 'Documento de política de privacidade e proteção de dados conforme LGPD',
        'version': '1.0',
        'legal_basis': 'LGPD, Lei 13.709/2018; Lei 12.965/2014',
        'primary_color': '#0891B2',
        'secondary_color': '#06B6D4',
        'cover_title': 'Política de Privacidade',
        'sections': [
            {
                'number': 1, 'key': 'identificacao_controlador',
                'name': 'Identificação do Controlador',
                'description': 'Dados do controlador e canal de contato do DPO',
                'instructions': 'Identifique o controlador (LGPD art. 5º VI): razão social, CNPJ, endereço, contato. Informe o Encarregado/DPO (LGPD art. 41): nome ou canal de contato. Mencione data de vigência e versão.',
                'fields': [
                    {'name': 'empresa_nome', 'label': 'Razão Social da Empresa', 'type': 'text', 'required': True},
                    {'name': 'empresa_cnpj', 'label': 'CNPJ', 'type': 'text', 'required': True},
                    {'name': 'dpo_contato', 'label': 'E-mail do DPO/Encarregado', 'type': 'text', 'required': True},
                    {'name': 'plataforma_descricao', 'label': 'Descrição da Plataforma/Serviço', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'dados_coletados_bases',
                'name': 'I - Dados Coletados e Bases Legais',
                'description': 'Quais dados são coletados e com base em qual hipótese legal',
                'instructions': 'Liste os dados pessoais coletados e as bases legais para cada tipo (LGPD art. 7º: consentimento, execução de contrato, obrigação legal, legítimo interesse, etc.). Indique finalidade de cada categoria de dado.',
                'fields': [
                    {'name': 'tipos_dados', 'label': 'Tipos de Dados Coletados (identificação, financeiros, navegação, etc.)', 'type': 'textarea', 'required': True},
                    {'name': 'bases_legais', 'label': 'Bases Legais Utilizadas (art. 7º LGPD)', 'type': 'textarea', 'required': True},
                    {'name': 'ha_dados_sensiveis', 'label': 'Coleta dados sensíveis (art. 11 LGPD)?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (especificar tipos e base legal específica)']},
                ],
            },
            {
                'number': 3, 'key': 'direitos_titular',
                'name': 'II - Direitos do Titular',
                'description': 'Como o titular pode exercer seus direitos (LGPD art. 18)',
                'instructions': 'Descreva todos os direitos do titular (LGPD art. 18): confirmação, acesso, correção, anonimização, portabilidade, eliminação, informação sobre compartilhamento, revisão de decisão automatizada. Informe canal e prazo (art. 19: até 15 dias).',
                'fields': [
                    {'name': 'canal_exercicio_direitos', 'label': 'Canal para Exercício de Direitos (e-mail, formulário)', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'cookies_retencao',
                'name': 'III - Cookies, Retenção e Transferências',
                'description': 'Política de cookies, prazo de retenção e transferências internacionais',
                'instructions': 'Informe: uso de cookies e finalidade, prazo de retenção dos dados por categoria, eventuais transferências internacionais (LGPD arts. 33-36) e países destinatários.',
                'fields': [
                    {'name': 'usa_cookies', 'label': 'Usa cookies?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim - apenas essenciais', 'Sim - essenciais e analíticos', 'Sim - essenciais, analíticos e marketing']},
                    {'name': 'prazo_retencao', 'label': 'Prazo de Retenção dos Dados', 'type': 'textarea', 'required': True},
                    {'name': 'transferencia_internacional', 'label': 'Transfere dados para outros países?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (especificar países e salvaguardas)']},
                ],
            },
            {
                'number': 5, 'key': 'disposicoes_finais_pp',
                'name': 'IV - Disposições Finais',
                'description': 'Atualizações, incidentes e foro',
                'instructions': 'Inclua: procedimento em caso de incidente de segurança (LGPD art. 48), como a política será atualizada e comunicada, foro para resolução de disputas.',
                'fields': [
                    {'name': 'foro_eleito', 'label': 'Foro de Eleição', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'termo_uso_plataforma',
        'name': 'Termos de Uso de Plataforma Digital',
        'description': 'Termos e condições de uso de plataforma ou aplicativo digital',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 421-480; Lei 12.965/2014 (MCI)',
        'primary_color': '#0891B2',
        'secondary_color': '#06B6D4',
        'cover_title': 'Termos de Uso',
        'sections': [
            {
                'number': 1, 'key': 'identificacao_plataforma',
                'name': 'Identificação das Partes e Aceitação',
                'description': 'Empresa, plataforma e condição de aceitação',
                'instructions': 'Identifique a empresa operadora e a plataforma. Estabeleça que o uso da plataforma implica aceitação integral dos termos (Marco Civil art. 7º). Mencione requisito de maioridade ou representação legal para menores.',
                'fields': [
                    {'name': 'empresa_nome', 'label': 'Razão Social da Empresa', 'type': 'text', 'required': True},
                    {'name': 'plataforma_nome', 'label': 'Nome da Plataforma/Aplicativo', 'type': 'text', 'required': True},
                    {'name': 'descricao_servico', 'label': 'Descrição do Serviço Oferecido', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'regras_uso_obrigacoes',
                'name': 'I - Regras de Uso e Obrigações do Usuário',
                'description': 'Condutas permitidas e proibidas na plataforma',
                'instructions': 'Liste obrigações do usuário: veracidade dos dados cadastrais, segurança das credenciais, responsabilidade pelo conteúdo publicado. Proibições: spam, uso de robôs, conteúdo ilícito, violação de direitos autorais. Cite o Marco Civil da Internet (Lei 12.965/2014).',
                'fields': [
                    {'name': 'tipo_conteudo_usuario', 'label': 'O usuário publica conteúdo na plataforma?', 'type': 'select', 'required': True, 'options': ['Não (plataforma apenas para consumo)', 'Sim (usuários podem publicar conteúdo)']},
                    {'name': 'restricoes_especificas', 'label': 'Restrições Específicas da Plataforma', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'responsabilidades_rescisao',
                'name': 'II - Responsabilidades, Rescisão e Foro',
                'description': 'Limitação de responsabilidade e encerramento de conta',
                'instructions': 'Estabeleça limitações de responsabilidade da empresa, condições de suspensão/encerramento de conta por violação dos termos, política de reembolso se houver serviços pagos, lei aplicável e foro de eleição.',
                'fields': [
                    {'name': 'servico_pago', 'label': 'Há serviços pagos?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim (incluir política de pagamento e reembolso)']},
                    {'name': 'foro_eleito', 'label': 'Foro de Eleição', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'dpa_tratamento_dados',
        'name': 'Acordo de Processamento de Dados (DPA) - LGPD',
        'description': 'Contrato entre controlador e operador para tratamento de dados pessoais',
        'version': '1.0',
        'legal_basis': 'LGPD, arts. 37-40; arts. 5º VI e VII',
        'primary_color': '#0891B2',
        'secondary_color': '#06B6D4',
        'cover_title': 'Data Processing Agreement (DPA)',
        'sections': [
            {
                'number': 1, 'key': 'partes_dpa',
                'name': 'Identificação das Partes',
                'description': 'Controlador e Operador conforme LGPD',
                'instructions': 'Identifique o Controlador (LGPD art. 5º VI: decide sobre o tratamento) e o Operador (art. 5º VII: realiza o tratamento em nome do controlador). Inclua dados completos de ambas as partes.',
                'fields': [
                    {'name': 'controlador_nome', 'label': 'Nome/Razão Social do Controlador', 'type': 'text', 'required': True},
                    {'name': 'controlador_cnpj', 'label': 'CNPJ do Controlador', 'type': 'text', 'required': True},
                    {'name': 'operador_nome', 'label': 'Nome/Razão Social do Operador', 'type': 'text', 'required': True},
                    {'name': 'operador_cnpj', 'label': 'CNPJ do Operador', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'objeto_tratamento',
                'name': 'I - Objeto e Natureza do Tratamento',
                'description': 'Escopo do tratamento de dados',
                'instructions': 'Descreva o objeto do DPA: tipos de dados tratados, finalidade, duração, natureza do tratamento, categorias de titulares. Fundamente na LGPD arts. 37-40. Liste as instruções documentadas do controlador ao operador.',
                'fields': [
                    {'name': 'dados_objeto', 'label': 'Tipos de Dados Pessoais Objeto do Tratamento', 'type': 'textarea', 'required': True},
                    {'name': 'finalidade_tratamento', 'label': 'Finalidade do Tratamento', 'type': 'textarea', 'required': True},
                    {'name': 'duracao_tratamento', 'label': 'Duração do Tratamento', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'obrigacoes_seguranca',
                'name': 'II - Obrigações do Operador e Medidas de Segurança',
                'description': 'Deveres do operador e requisitos de segurança',
                'instructions': 'Estabeleça obrigações do operador (LGPD art. 39): tratar apenas conforme instruções do controlador, manter sigilo, implementar medidas de segurança (LGPD art. 46), notificar incidentes (LGPD art. 48), não subtratar sem autorização, devolver/destruir dados ao final.',
                'fields': [
                    {'name': 'permite_subtratamento', 'label': 'Permite suboperadores/subtratamento?', 'type': 'select', 'required': True, 'options': ['Não permitido', 'Sim - com aprovação prévia escrita', 'Sim - lista pré-aprovada']},
                    {'name': 'prazo_notificacao_incidente', 'label': 'Prazo para Notificação de Incidente ao Controlador', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'resposta_titular_dados',
        'name': 'Resposta a Solicitação de Titular - LGPD art. 18',
        'description': 'Resposta formal a exercício de direito pelo titular de dados pessoais',
        'version': '1.0',
        'legal_basis': 'LGPD, arts. 18-20; LGPD, art. 19',
        'primary_color': '#0891B2',
        'secondary_color': '#06B6D4',
        'cover_title': 'Resposta ao Titular de Dados',
        'sections': [
            {
                'number': 1, 'key': 'identificacao_solicitacao',
                'name': 'Identificação da Solicitação',
                'description': 'Dados da solicitação recebida do titular',
                'instructions': 'Identifique a solicitação: nome do titular, data do pedido, canal, direito exercido (LGPD art. 18), número de protocolo se houver. Confirme que o prazo de 15 dias está sendo respeitado (LGPD art. 19).',
                'fields': [
                    {'name': 'titular_nome', 'label': 'Nome do Titular', 'type': 'text', 'required': True},
                    {'name': 'data_solicitacao', 'label': 'Data da Solicitação', 'type': 'text', 'required': True},
                    {'name': 'direito_exercido', 'label': 'Direito Exercido (art. 18 LGPD)', 'type': 'select', 'required': True, 'options': ['Confirmação de tratamento', 'Acesso aos dados', 'Correção de dados', 'Anonimização/Bloqueio/Eliminação', 'Portabilidade', 'Eliminação por revogação do consentimento', 'Informação sobre compartilhamento', 'Revisão de decisão automatizada']},
                ],
            },
            {
                'number': 2, 'key': 'resposta_direito',
                'name': 'I - Resposta ao Direito Exercido',
                'description': 'Atendimento ou justificativa para não atendimento',
                'instructions': 'Elabore a resposta: confirme o atendimento do direito ou justifique a impossibilidade (LGPD art. 18 §§ 3º e 4º: hipóteses de recusa). Se atender, descreva exatamente o que foi feito. Se recusar, cite a base legal da recusa.',
                'fields': [
                    {'name': 'atende_pedido', 'label': 'Atende o pedido?', 'type': 'select', 'required': True, 'options': ['Sim - atende integralmente', 'Sim - atende parcialmente', 'Não - justificar com base legal']},
                    {'name': 'descricao_resposta', 'label': 'Descrição da Resposta / Medidas Adotadas', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'notificacao_incidente_lgpd',
        'name': 'Notificação de Incidente de Segurança - LGPD art. 48',
        'description': 'Comunicação formal de incidente de segurança à ANPD e titulares afetados',
        'version': '1.0',
        'legal_basis': 'LGPD, art. 48; Resolução ANPD 04/2023',
        'primary_color': '#DC2626',
        'secondary_color': '#EF4444',
        'cover_title': 'Notificação de Incidente de Segurança',
        'sections': [
            {
                'number': 1, 'key': 'identificacao_incidente',
                'name': 'Identificação do Incidente',
                'description': 'Natureza e circunstâncias do incidente',
                'instructions': 'Descreva o incidente: natureza (vazamento, acesso não autorizado, exclusão indevida, etc.), data de ocorrência e de descoberta, sistemas afetados. Fundamente na LGPD art. 48 e Resolução ANPD 04/2023.',
                'fields': [
                    {'name': 'tipo_incidente', 'label': 'Tipo de Incidente', 'type': 'select', 'required': True, 'options': ['Acesso não autorizado', 'Vazamento de dados', 'Exclusão indevida', 'Ransomware/Sequestro de dados', 'Phishing/Engenharia social', 'Outro']},
                    {'name': 'data_ocorrencia', 'label': 'Data Provável da Ocorrência', 'type': 'text', 'required': True},
                    {'name': 'data_descoberta', 'label': 'Data de Descoberta pelo Controlador', 'type': 'text', 'required': True},
                    {'name': 'sistemas_afetados', 'label': 'Sistemas/Ambientes Afetados', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'dados_titulares_afetados',
                'name': 'I - Dados e Titulares Afetados',
                'description': 'Categorias de dados e titulares envolvidos',
                'instructions': 'Descreva: categorias de dados pessoais afetados, quantidade estimada de titulares, se há dados sensíveis envolvidos (LGPD art. 11), grupos de risco (crianças, idosos, funcionários, clientes).',
                'fields': [
                    {'name': 'categorias_dados', 'label': 'Categorias de Dados Afetados', 'type': 'textarea', 'required': True},
                    {'name': 'qtd_titulares', 'label': 'Quantidade Estimada de Titulares Afetados', 'type': 'text', 'required': True},
                    {'name': 'ha_dados_sensiveis', 'label': 'Há dados sensíveis afetados?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim']},
                ],
            },
            {
                'number': 3, 'key': 'medidas_comunicacao',
                'name': 'II - Medidas Adotadas e Comunicação',
                'description': 'Ações de contenção e comunicação aos titulares',
                'instructions': 'Descreva medidas adotadas: contenção do incidente, investigação, notificação à ANPD (Resolução ANPD 04/2023), comunicação aos titulares afetados, medidas preventivas futuras. Mencione prazo razoável (LGPD art. 48).',
                'fields': [
                    {'name': 'medidas_contencao', 'label': 'Medidas de Contenção Adotadas', 'type': 'textarea', 'required': True},
                    {'name': 'notifica_anpd', 'label': 'Notificação à ANPD já realizada?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não - será realizada em seguida', 'Em avaliação']},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'contrato_prestacao_servicos',
        'name': 'Contrato de Prestação de Serviços - CC/2002',
        'description': 'Contrato civil de prestação de serviços entre pessoas físicas ou jurídicas',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 593-609 e arts. 421-480',
        'primary_color': '#374151',
        'secondary_color': '#4B5563',
        'cover_title': 'Contrato de Prestação de Serviços',
        'sections': [
            {
                'number': 1, 'key': 'partes_contrato',
                'name': 'Identificação das Partes e Preâmbulo',
                'description': 'Contratante e contratado com qualificação completa',
                'instructions': 'Qualifique as partes: Contratante e Contratado com nome/razão social, CPF/CNPJ, endereço, representante legal se pessoa jurídica. Declare que celebram o presente contrato de prestação de serviços sob as cláusulas seguintes.',
                'fields': [
                    {'name': 'contratante_nome', 'label': 'Nome/Razão Social do Contratante', 'type': 'text', 'required': True},
                    {'name': 'contratante_cpf_cnpj', 'label': 'CPF/CNPJ do Contratante', 'type': 'text', 'required': True},
                    {'name': 'contratado_nome', 'label': 'Nome/Razão Social do Contratado', 'type': 'text', 'required': True},
                    {'name': 'contratado_cpf_cnpj', 'label': 'CPF/CNPJ do Contratado', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'objeto_servico',
                'name': 'Cláusula 1ª - Do Objeto',
                'description': 'Descrição detalhada dos serviços a prestar',
                'instructions': 'Descreva com precisão os serviços a serem prestados (CC art. 593), escopo, entregas esperadas, metodologia, local de prestação. Seja específico para evitar disputas futuras.',
                'fields': [
                    {'name': 'descricao_servico', 'label': 'Descrição Detalhada dos Serviços', 'type': 'textarea', 'required': True},
                    {'name': 'local_prestacao', 'label': 'Local de Prestação dos Serviços', 'type': 'text', 'required': True},
                    {'name': 'prazo_execucao', 'label': 'Prazo de Execução / Vigência do Contrato', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'valor_pagamento',
                'name': 'Cláusula 2ª - Do Valor e Pagamento',
                'description': 'Remuneração e condições de pagamento',
                'instructions': 'Especifique o valor total ou mensal dos serviços, forma e prazo de pagamento, índice de correção monetária, consequências de inadimplência (CC art. 394-401: mora), reajuste anual.',
                'fields': [
                    {'name': 'valor_total', 'label': 'Valor Total ou Mensal dos Serviços (R$)', 'type': 'text', 'required': True},
                    {'name': 'forma_pagamento', 'label': 'Forma de Pagamento (PIX, boleto, transferência)', 'type': 'text', 'required': True},
                    {'name': 'vencimento', 'label': 'Data de Vencimento', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 4, 'key': 'rescisao_disposicoes',
                'name': 'Cláusulas Gerais - Rescisão, Sigilo e Foro',
                'description': 'Rescisão, confidencialidade e disposições finais',
                'instructions': 'Estabeleça: hipóteses de rescisão (por acordo, justa causa, inadimplemento), obrigação de sigilo sobre informações confidenciais, propriedade intelectual das obras geradas, foro de eleição.',
                'fields': [
                    {'name': 'aviso_previo_rescisao', 'label': 'Prazo de Aviso Prévio para Rescisão Imotivada', 'type': 'text', 'required': True},
                    {'name': 'clausula_sigilo', 'label': 'Inclui cláusula de confidencialidade/NDA?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'foro_eleito', 'label': 'Foro de Eleição', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'ata_reuniao_societaria',
        'name': 'Ata de Reunião/Assembleia Societária',
        'description': 'Ata de reunião de sócios (Ltda) ou assembleia geral (S/A)',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.010-1.021 (Ltda); Lei 6.404/1976 (S/A)',
        'primary_color': '#374151',
        'secondary_color': '#4B5563',
        'cover_title': 'Ata de Reunião Societária',
        'sections': [
            {
                'number': 1, 'key': 'abertura_reuniao',
                'name': 'Abertura e Verificação do Quórum',
                'description': 'Formalidades de abertura da reunião/assembleia',
                'instructions': 'Registre: data, hora e local da reunião, tipo (ordinária/extraordinária), sócios/acionistas presentes com participação percentual, verificação de quórum legal, presença de representantes legais, mesa diretora (presidente e secretário).',
                'fields': [
                    {'name': 'tipo_sociedade', 'label': 'Tipo de Sociedade', 'type': 'select', 'required': True, 'options': ['Sociedade Limitada (Ltda)', 'Sociedade Anônima (S/A)', 'EIRELI', 'SLU', 'Outra']},
                    {'name': 'tipo_reuniao', 'label': 'Tipo de Reunião', 'type': 'select', 'required': True, 'options': ['Reunião Ordinária de Sócios', 'Reunião Extraordinária de Sócios', 'Assembleia Geral Ordinária', 'Assembleia Geral Extraordinária']},
                    {'name': 'data_hora', 'label': 'Data e Hora da Reunião', 'type': 'text', 'required': True},
                    {'name': 'socios_presentes', 'label': 'Sócios/Acionistas Presentes e Percentuais', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'deliberacoes',
                'name': 'I - Ordem do Dia e Deliberações',
                'description': 'Assuntos deliberados e votos',
                'instructions': 'Registre cada item da ordem do dia, a deliberação correspondente (aprovada/rejeitada) e o resultado da votação (maioria simples ou qualificada conforme CC art. 1.076 ou estatuto social). Mencione eventuais votos dissidentes.',
                'fields': [
                    {'name': 'pauta_deliberacoes', 'label': 'Pauta e Resultado de cada Deliberação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'encerramento_ata',
                'name': 'II - Encerramento e Assinaturas',
                'description': 'Encerramento formal e assinaturas',
                'instructions': 'Registre o encerramento da reunião, lavramento da ata, que a ata foi lida, aprovada e assinada pelos presentes. Mencione necessidade de registro na Junta Comercial se aplicável.',
                'fields': [
                    {'name': 'requer_registro_junta', 'label': 'Requer registro na Junta Comercial?', 'type': 'select', 'required': True, 'options': ['Sim (alteração contratual/estatutária)', 'Não (reunião ordinária de rotina)']},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'distrato_societario',
        'name': 'Distrato Social / Dissolução de Sociedade',
        'description': 'Documento de dissolução e encerramento voluntário de sociedade empresária',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.033-1.044; Lei 6.404/1976, arts. 206-219',
        'primary_color': '#374151',
        'secondary_color': '#4B5563',
        'cover_title': 'Distrato Social',
        'sections': [
            {
                'number': 1, 'key': 'partes_dissolucao',
                'name': 'Identificação da Sociedade e dos Sócios',
                'description': 'Dados da sociedade e sócios que promovem o distrato',
                'instructions': 'Identifique a sociedade (razão social, CNPJ, sede, registro na Junta Comercial), tipo societário e todos os sócios com qualificação completa e participação percentual. Informe a data de constituição e o número do contrato/estatuto social originário.',
                'fields': [
                    {'name': 'sociedade_razao_social', 'label': 'Razão Social da Sociedade', 'type': 'text', 'required': True},
                    {'name': 'sociedade_cnpj', 'label': 'CNPJ', 'type': 'text', 'required': True},
                    {'name': 'tipo_sociedade', 'label': 'Tipo de Sociedade', 'type': 'select', 'required': True, 'options': ['Sociedade Limitada (Ltda)', 'Sociedade Anônima (S/A)', 'EIRELI/SLU', 'Sociedade Simples', 'Outra']},
                    {'name': 'socios', 'label': 'Sócios (nome, CPF/CNPJ, participação percentual)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'motivacao_dissolucao',
                'name': 'I - Da Dissolução e seus Fundamentos',
                'description': 'Causa e fundamento legal da dissolução',
                'instructions': 'Declare a causa da dissolução (CC art. 1.033: consenso unânime, prazo, objeto ilícito, inatividade, etc.). Fundamente no CC/2002 arts. 1.033-1.037 para Ltda ou Lei 6.404/1976 arts. 206-219 para S/A. Declare que os sócios concordam unanimemente.',
                'fields': [
                    {'name': 'causa_dissolucao', 'label': 'Causa da Dissolução (CC art. 1.033)', 'type': 'select', 'required': True, 'options': ['Consenso de todos os sócios', 'Decisão judicial', 'Expiração do prazo contratual', 'Impossibilidade do objeto social', 'Outra']},
                    {'name': 'data_dissolucao', 'label': 'Data de Efeito da Dissolução', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'partilha_encerramento',
                'name': 'II - Liquidação, Partilha e Registro',
                'description': 'Liquidação do ativo, quitação do passivo e encerramento',
                'instructions': 'Descreva: nomeação do liquidante (CC art. 1.036) se necessário, realização do ativo, pagamento do passivo, partilha do saldo entre os sócios na proporção das cotas, declaração de inexistência de débitos trabalhistas e fiscais, encaminhamento à Junta Comercial para baixa.',
                'fields': [
                    {'name': 'liquidante', 'label': 'Liquidante Nomeado (ou próprio sócio administrador)', 'type': 'text', 'required': True},
                    {'name': 'saldo_partilha', 'label': 'Saldo para Partilha entre os Sócios (R$)', 'type': 'text', 'required': False},
                    {'name': 'declaracao_debitos', 'label': 'Declaração de inexistência de débitos?', 'type': 'select', 'required': True, 'options': ['Sim - declaramos inexistência de débitos trabalhistas, fiscais e previdenciários', 'Não - há débitos pendentes (detalhar)']},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Digital/LGPD e Empresarial no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Digital/LGPD e Empresarial'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            return

        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Digital/LGPD e Empresarial concluído!\n'))

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
            {'key': 'gerador_digital_lgpd', 'name': 'Verus.AI - Gerador Digital e LGPD', 'description': 'Gera documentos de Direito Digital e LGPD', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_DIGITAL_LGPD, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
            {'key': 'gerador_empresarial', 'name': 'Verus.AI - Gerador Empresarial', 'description': 'Gera documentos jurídicos empresariais e societários', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_EMPRESARIAL, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_digital_lgpd')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
