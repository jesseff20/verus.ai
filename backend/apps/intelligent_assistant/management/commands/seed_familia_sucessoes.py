"""
Seed Família e Sucessões — Verus.AI.
Cria categorias, tipos de documento, agente especializado e blueprints.

Uso:
    python manage.py seed_familia_sucessoes
    python manage.py seed_familia_sucessoes --force
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
        'code': 'familia_sucessoes',
        'name': 'Família e Sucessões',
        'description': 'Peças jurídicas de Direito de Família e Sucessório',
        'display_order': 9,
    },
]

TIPOS_DOCUMENTO = [
    {
        'code': 'acao_alimentos',
        'name': 'Ação de Alimentos',
        'short_name': 'Ação Alimentos',
        'description': 'Ação para fixação judicial de alimentos',
        'category': 'familia_sucessoes',
        'icon': 'Heart',
        'color': '#E11D48',
        'legal_basis': 'Lei 5.478/1968; CC/2002, arts. 1.694-1.710; CPC/2015, arts. 693-699',
        'display_order': 1,
    },
    {
        'code': 'divorcio_consensual',
        'name': 'Divórcio Consensual',
        'short_name': 'Divórcio Consensual',
        'description': 'Ação de divórcio de comum acordo entre os cônjuges',
        'category': 'familia_sucessoes',
        'icon': 'Heart',
        'color': '#7C3AED',
        'legal_basis': 'CC/2002, arts. 1.571-1.582; CPC/2015, arts. 731-734; EC 66/2010',
        'display_order': 2,
    },
    {
        'code': 'revisional_alimentos',
        'name': 'Ação Revisional de Alimentos',
        'short_name': 'Rev. Alimentos',
        'description': 'Ação para revisão do valor dos alimentos já fixados',
        'category': 'familia_sucessoes',
        'icon': 'RefreshCw',
        'color': '#E11D48',
        'legal_basis': 'CC/2002, art. 1.699; Lei 5.478/1968, art. 15',
        'display_order': 3,
    },
    {
        'code': 'regulamentacao_guarda',
        'name': 'Regulamentação de Guarda',
        'short_name': 'Reg. Guarda',
        'description': 'Ação de regulamentação da guarda e visitas de filhos menores',
        'category': 'familia_sucessoes',
        'icon': 'Users',
        'color': '#0891B2',
        'legal_basis': 'CC/2002, arts. 1.583-1.590; Lei 13.058/2014; CPC/2015, arts. 693-699',
        'display_order': 4,
    },
    {
        'code': 'inventario_judicial',
        'name': 'Inventário Judicial',
        'short_name': 'Inventário Jud.',
        'description': 'Processo judicial de inventário e partilha de bens do falecido',
        'category': 'familia_sucessoes',
        'icon': 'FileText',
        'color': '#374151',
        'legal_basis': 'CC/2002, arts. 1.784-2.027; CPC/2015, arts. 610-673',
        'display_order': 5,
    },
    {
        'code': 'inventario_extrajudicial',
        'name': 'Inventário Extrajudicial',
        'short_name': 'Inventário Ext.',
        'description': 'Inventário em cartório quando todos os herdeiros são maiores e concordes',
        'category': 'familia_sucessoes',
        'icon': 'FileText',
        'color': '#374151',
        'legal_basis': 'Lei 11.441/2007; CPC/2015, art. 610; Resolução CNJ 35/2007',
        'display_order': 6,
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
- Conteúdo inferido: [VERIFICAR COM ADVOGADO]
"""

PROMPT_GERADOR_FAMILIA = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito de Família e Sucessões brasileiro.

LEGISLAÇÃO VIGENTE:
- CC/2002 Livro IV (arts. 1.511-1.783) e Livro V (arts. 1.784-2.027)
- CPC/2015 arts. 693-734 (família) e arts. 610-673 (inventário)
- Lei 5.478/1968 (alimentos), Lei 13.058/2014 (guarda compartilhada como regra)
- EC 66/2010 (divórcio direto sem separação prévia)
- Lei 11.441/2007 (inventário extrajudicial)

REGRAS:
1. Alimentos: binômio necessidade-possibilidade (CC art. 1.694 §1º)
2. Guarda: compartilhada como regra (Lei 13.058/2014)
3. Divórcio: EC 66/2010 — não exige separação prévia
4. Súmulas STJ consolidadas: 277, 354, 364, 379, 380, 382, 383, 385, 397
5. Acórdãos: marque [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'acao_alimentos': 'gerador_familia',
    'divorcio_consensual': 'gerador_familia',
    'revisional_alimentos': 'gerador_familia',
    'regulamentacao_guarda': 'gerador_familia',
    'inventario_judicial': 'gerador_familia',
    'inventario_extrajudicial': 'gerador_familia',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'acao_alimentos',
        'name': 'Ação de Alimentos - Lei 5.478/1968',
        'description': 'Petição inicial para fixação judicial de alimentos',
        'version': '1.0',
        'legal_basis': 'Lei 5.478/1968; CC/2002, arts. 1.694-1.710',
        'primary_color': '#E11D48',
        'secondary_color': '#F43F5E',
        'cover_title': 'Ação de Alimentos',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação das Partes',
                'description': 'Identificação do juízo e qualificação das partes',
                'instructions': 'Gere endereçamento à Vara de Família. Qualifique autor (alimentando) e réu (alimentante) com dados completos, incluindo parentesco.',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'autor_nome', 'label': 'Nome do Alimentando', 'type': 'text', 'required': True},
                    {'name': 'reu_nome', 'label': 'Nome do Alimentante', 'type': 'text', 'required': True},
                    {'name': 'parentesco', 'label': 'Grau de Parentesco', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos',
                'name': 'I - Dos Fatos',
                'description': 'Narração dos fatos que justificam o pedido',
                'instructions': 'Narre: vínculo familiar, necessidade do alimentando, capacidade do alimentante. Destaque a obrigação alimentar (CC art. 1.694).',
                'fields': [
                    {'name': 'situacao_familiar', 'label': 'Situação Familiar e Contexto', 'type': 'textarea', 'required': True},
                    {'name': 'necessidade_alimentando', 'label': 'Necessidades do Alimentando (despesas mensais estimadas)', 'type': 'textarea', 'required': True},
                    {'name': 'capacidade_alimentante', 'label': 'Capacidade Financeira do Alimentante', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'fundamento_juridico',
                'name': 'II - Do Direito',
                'description': 'Fundamentos jurídicos do direito a alimentos',
                'instructions': 'Fundamente na Lei 5.478/1968 e CC/2002. Cite binômio necessidade-possibilidade (CC art. 1.694 §1º) e obrigação alimentar recíproca entre parentes (art. 1.696).',
                'fields': [
                    {'name': 'tipo_alimentos', 'label': 'Tipo de Alimentos', 'type': 'select', 'required': True, 'options': ['Definitivos', 'Provisórios (art. 4º Lei 5.478/1968)', 'Provisionais (CPC art. 300)']},
                ],
            },
            {
                'number': 4, 'key': 'pedidos',
                'name': 'III - Dos Pedidos',
                'description': 'Pedidos de fixação de alimentos',
                'instructions': 'Formule pedidos: fixação de alimentos (valor ou percentual), tutela de urgência para provisórios se necessário, citação do réu, custas.',
                'fields': [
                    {'name': 'valor_alimentos', 'label': 'Valor dos Alimentos Pleiteados (R$ ou % salário mínimo)', 'type': 'text', 'required': True},
                    {'name': 'pedido_tutela', 'label': 'Pede Alimentos Provisórios?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (12× mensalidade)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'divorcio_consensual',
        'name': 'Divórcio Consensual - CPC/2015',
        'description': 'Petição de divórcio de comum acordo com ou sem filhos menores',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.571-1.582; CPC/2015, arts. 731-734; EC 66/2010',
        'primary_color': '#7C3AED',
        'secondary_color': '#8B5CF6',
        'cover_title': 'Divórcio Consensual',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_partes',
                'name': 'Qualificação das Partes',
                'description': 'Identificação completa dos cônjuges',
                'instructions': 'Qualifique os cônjuges (requerentes) com dados completos. Informe data, cartório e regime de bens do casamento.',
                'fields': [
                    {'name': 'conjuge1_nome', 'label': 'Nome do 1º Cônjuge', 'type': 'text', 'required': True},
                    {'name': 'conjuge2_nome', 'label': 'Nome do 2º Cônjuge', 'type': 'text', 'required': True},
                    {'name': 'data_casamento', 'label': 'Data do Casamento', 'type': 'text', 'required': True},
                    {'name': 'regime_bens', 'label': 'Regime de Bens', 'type': 'select', 'required': True, 'options': ['Comunhão Parcial', 'Comunhão Universal', 'Separação Total', 'Participação Final nos Aquestos']},
                ],
            },
            {
                'number': 2, 'key': 'acordo_filhos',
                'name': 'I - Da Guarda e Alimentos dos Filhos',
                'description': 'Disposições sobre filhos menores (se houver)',
                'instructions': 'Se houver filhos menores: modalidade de guarda (preferencialmente compartilhada — Lei 13.058/2014), regime de visitas, alimentos. Se não houver, declare expressamente.',
                'fields': [
                    {'name': 'tem_filhos_menores', 'label': 'Há filhos menores ou incapazes?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim']},
                    {'name': 'dados_filhos', 'label': 'Filhos: nome, idade, guarda, visitas, alimentos acordados', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'partilha_bens',
                'name': 'II - Da Partilha de Bens',
                'description': 'Acordo sobre a divisão do patrimônio comum',
                'instructions': 'Descreva a partilha dos bens comuns. Liste cada bem e como será dividido. Se não há bens, declare. Informe sobre pensão alimentícia entre cônjuges.',
                'fields': [
                    {'name': 'bens_partilhar', 'label': 'Bens e Critério de Divisão Acordado', 'type': 'textarea', 'required': False},
                    {'name': 'pensao_conjuge', 'label': 'Alimentos entre cônjuges?', 'type': 'select', 'required': True, 'options': ['Não há', 'Cônjuge 1 pagará ao Cônjuge 2', 'Cônjuge 2 pagará ao Cônjuge 1']},
                ],
            },
            {
                'number': 4, 'key': 'pedidos',
                'name': 'III - Dos Pedidos',
                'description': 'Pedidos finais do divórcio',
                'instructions': 'Formule pedidos: homologação do acordo, decretação do divórcio (EC 66/2010), expedição de mandado ao Cartório de Registro Civil, retomada de nome se aplicável.',
                'fields': [
                    {'name': 'retomada_nome', 'label': 'Retomada de nome de solteiro?', 'type': 'select', 'required': True, 'options': ['Não', 'Cônjuge 1', 'Cônjuge 2', 'Ambos']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'revisional_alimentos',
        'name': 'Ação Revisional de Alimentos - CC/2002',
        'description': 'Petição para revisão do valor de alimentos já fixados',
        'version': '1.0',
        'legal_basis': 'CC/2002, art. 1.699; Lei 5.478/1968, art. 15',
        'primary_color': '#E11D48',
        'secondary_color': '#F43F5E',
        'cover_title': 'Revisional de Alimentos',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Processo de Origem',
                'description': 'Juízo, partes e referência ao processo anterior',
                'instructions': 'Endereçamento à Vara de Família. Qualifique as partes. Identifique o processo de origem que fixou os alimentos (número, valor atual).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'processo_origem', 'label': 'Processo de Origem (número e vara)', 'type': 'text', 'required': True},
                    {'name': 'valor_atual', 'label': 'Valor Atual dos Alimentos', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'mudanca_fortuna',
                'name': 'I - Da Mudança de Fortuna',
                'description': 'Fatos novos que justificam a revisão',
                'instructions': 'Descreva a mudança na fortuna das partes que justifica a revisão (CC art. 1.699). Pode ser: alteração de renda, mudança nas necessidades, emancipação, novo emprego, etc.',
                'fields': [
                    {'name': 'tipo_revisao', 'label': 'Tipo de Revisão', 'type': 'select', 'required': True, 'options': ['Redução (diminuição de capacidade do alimentante)', 'Aumento (aumento de necessidade do alimentando)', 'Exoneração (cessação da obrigação)']},
                    {'name': 'fatos_novos', 'label': 'Fatos Novos que Justificam a Revisão', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'fundamento_pedido',
                'name': 'II - Do Direito e dos Pedidos',
                'description': 'Fundamentos e pedidos da revisão',
                'instructions': 'Fundamente no CC art. 1.699 (mudança de fortuna). Formule pedidos: revisão para novo valor, fixação provisória se necessário, valor da causa.',
                'fields': [
                    {'name': 'novo_valor', 'label': 'Novo Valor Pleiteado', 'type': 'text', 'required': True},
                    {'name': 'pedido_provisorio', 'label': 'Pede fixação provisória?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'regulamentacao_guarda',
        'name': 'Regulamentação de Guarda e Visitas - CC/2002',
        'description': 'Ação para regular guarda e convivência dos filhos menores',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.583-1.590; Lei 13.058/2014',
        'primary_color': '#0891B2',
        'secondary_color': '#06B6D4',
        'cover_title': 'Regulamentação de Guarda',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao',
                'name': 'Qualificação das Partes e dos Filhos',
                'description': 'Identificação dos genitores e filhos',
                'instructions': 'Qualifique os genitores e filhos menores (nome, idade, data de nascimento). Informe situação atual da guarda e contexto familiar.',
                'fields': [
                    {'name': 'genitor1_nome', 'label': 'Nome do Genitor Requerente', 'type': 'text', 'required': True},
                    {'name': 'genitor2_nome', 'label': 'Nome do Genitor Requerido', 'type': 'text', 'required': True},
                    {'name': 'filhos', 'label': 'Filhos (nome, data de nascimento)', 'type': 'textarea', 'required': True},
                    {'name': 'situacao_atual', 'label': 'Situação Atual da Guarda', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'proposta_guarda',
                'name': 'I - Da Proposta de Guarda e Convivência',
                'description': 'Modalidade de guarda e regime de visitas',
                'instructions': 'Proponha modalidade de guarda. Fundamente guarda compartilhada como regra (Lei 13.058/2014, CC art. 1.584 §2º). Descreva regime de convivência detalhado (dias, férias, datas especiais).',
                'fields': [
                    {'name': 'modalidade_guarda', 'label': 'Modalidade de Guarda', 'type': 'select', 'required': True, 'options': ['Guarda Compartilhada (regra legal)', 'Guarda Unilateral (justificar)']},
                    {'name': 'residencia_referencia', 'label': 'Residência de Referência dos Filhos', 'type': 'text', 'required': True},
                    {'name': 'regime_visitas', 'label': 'Regime de Convivência Proposto', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos de guarda, visitas e medidas acessórias',
                'instructions': 'Formule pedidos: fixação da guarda (modalidade), regulamentação das visitas, alimentos se não fixados em outro processo, tutela de urgência se necessário.',
                'fields': [
                    {'name': 'pedido_alimentos', 'label': 'Inclui pedido de alimentos?', 'type': 'select', 'required': True, 'options': ['Não (já fixados)', 'Sim']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'inventario_judicial',
        'name': 'Inventário Judicial - CPC/2015',
        'description': 'Petição de abertura de inventário judicial com nomeação de inventariante',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.784-2.027; CPC/2015, arts. 610-673',
        'primary_color': '#374151',
        'secondary_color': '#4B5563',
        'cover_title': 'Inventário Judicial',
        'sections': [
            {
                'number': 1, 'key': 'qualificacao_de_cujus',
                'name': 'Qualificação do De Cujus e dos Herdeiros',
                'description': 'Dados do falecido e relação de herdeiros',
                'instructions': 'Qualifique o de cujus (nome, CPF, data de nascimento, data e local do óbito, domicílio, estado civil). Liste todos os herdeiros com qualificação completa.',
                'fields': [
                    {'name': 'de_cujus_nome', 'label': 'Nome do Falecido', 'type': 'text', 'required': True},
                    {'name': 'data_obito', 'label': 'Data do Óbito', 'type': 'text', 'required': True},
                    {'name': 'estado_civil', 'label': 'Estado Civil do Falecido', 'type': 'select', 'required': True, 'options': ['Casado(a)', 'Divorciado(a)', 'Viúvo(a)', 'Solteiro(a)', 'União Estável']},
                    {'name': 'herdeiros', 'label': 'Relação de Herdeiros (nome, parentesco, CPF)', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'bens_heranca',
                'name': 'I - Dos Bens da Herança',
                'description': 'Descrição e avaliação dos bens a inventariar',
                'instructions': 'Descreva todos os bens: imóveis (matrícula, endereço, valor), veículos, contas bancárias, investimentos. Mencione eventuais dívidas do espólio.',
                'fields': [
                    {'name': 'bens_imoveis', 'label': 'Bens Imóveis (matrícula, endereço, valor estimado)', 'type': 'textarea', 'required': False},
                    {'name': 'bens_moveis_valores', 'label': 'Bens Móveis e Valores Financeiros', 'type': 'textarea', 'required': False},
                    {'name': 'dividas_espolio', 'label': 'Dívidas do Espólio (se houver)', 'type': 'textarea', 'required': False},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos de abertura do inventário',
                'instructions': 'Formule pedidos: abertura do inventário, nomeação do inventariante (art. 617 CPC), expedição de ofícios de bloqueio/transferência, valor da causa (patrimônio líquido do espólio).',
                'fields': [
                    {'name': 'inventariante', 'label': 'Nome do Inventariante Proposto', 'type': 'text', 'required': True},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (patrimônio líquido)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'inventario_extrajudicial',
        'name': 'Inventário Extrajudicial - Lei 11.441/2007',
        'description': 'Escritura pública de inventário e partilha em cartório',
        'version': '1.0',
        'legal_basis': 'Lei 11.441/2007; CPC/2015, art. 610; Resolução CNJ 35/2007',
        'primary_color': '#374151',
        'secondary_color': '#4B5563',
        'cover_title': 'Inventário Extrajudicial',
        'sections': [
            {
                'number': 1, 'key': 'requisitos_admissibilidade',
                'name': 'Verificação dos Requisitos de Admissibilidade',
                'description': 'Confirmação dos requisitos para inventário extrajudicial',
                'instructions': 'Verifique: todos os herdeiros maiores e capazes, concordância unânime, ausência de testamento (ou testamento aberto/cumprido), representação por advogado. Cite Lei 11.441/2007 e Resolução CNJ 35/2007.',
                'fields': [
                    {'name': 'todos_maiores_capazes', 'label': 'Todos os herdeiros são maiores e capazes?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não (inventário deve ser judicial)']},
                    {'name': 'ha_testamento', 'label': 'O falecido deixou testamento?', 'type': 'select', 'required': True, 'options': ['Não', 'Sim - testamento aberto e cumprido', 'Sim - cerrado (judicial obrigatório)']},
                ],
            },
            {
                'number': 2, 'key': 'minuta_escritura',
                'name': 'I - Minuta da Escritura de Inventário e Partilha',
                'description': 'Conteúdo da escritura pública',
                'instructions': 'Elabore minuta da escritura: qualificação das partes (herdeiros e meeiro), identificação do de cujus, relação de bens com matrículas/registros, meação do cônjuge (se aplicável), quinhões de cada herdeiro.',
                'fields': [
                    {'name': 'de_cujus_qualificacao', 'label': 'Qualificação do De Cujus (nome, CPF, óbito, estado civil)', 'type': 'textarea', 'required': True},
                    {'name': 'herdeiros_qualificacao', 'label': 'Qualificação dos Herdeiros', 'type': 'textarea', 'required': True},
                    {'name': 'bens_e_partilha', 'label': 'Bens e Critério de Partilha por Herdeiro', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'itcmd_declaracoes',
                'name': 'II - ITCMD e Declarações Finais',
                'description': 'Questões tributárias e declarações obrigatórias',
                'instructions': 'Inclua: recolhimento do ITCMD (legislação estadual aplicável), declaração de inexistência de outros bens e herdeiros, concordância de todos com a partilha.',
                'fields': [
                    {'name': 'estado_itcmd', 'label': 'Estado (para cálculo do ITCMD)', 'type': 'text', 'required': True},
                    {'name': 'valor_total_heranca', 'label': 'Valor Total da Herança (base de cálculo ITCMD)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Família e Sucessões no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Família e Sucessões'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN — nenhuma alteração será salva\n'))
            return

        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)

        self.stdout.write(self.style.SUCCESS('\n✓ Família e Sucessões concluído!\n'))

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
                'key': 'gerador_familia',
                'name': 'Verus.AI - Gerador Família e Sucessões',
                'description': 'Gera seções de peças de Família e Sucessões',
                'agent_type': 'generator',
                'system_prompt': PROMPT_GERADOR_FAMILIA,
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
            if doc_type.category_id:
                blueprint.areas.add(doc_type.category)
            # Garante is_default=True em re-execução
            if not blueprint.is_default:
                blueprint.is_default = True
                blueprint.save(update_fields=['is_default'])
            self.stdout.write(f'  {"✓ Criado" if created else "⊘ Existe"}: {blueprint.name}')
            if created:
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_familia')
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
