"""
Seed Imobiliário e Locação — Verus.AI.
Ação de despejo, contrato de locação, renovatória, adjudicação compulsória,
retificação de registro.

Uso:
    python manage.py seed_imobiliario_locacao
    python manage.py seed_imobiliario_locacao --force
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
        'code': 'imobiliario',
        'name': 'Imobiliário e Locação',
        'description': 'Peças jurídicas de Direito Imobiliário, Registral e Lei do Inquilinato',
        'display_order': 16,
    },
]

TIPOS_DOCUMENTO = [
    {
        'code': 'acao_despejo',
        'name': 'Ação de Despejo',
        'short_name': 'Ação Despejo',
        'description': 'Ação para retomada de imóvel locado por falta de pagamento ou término do prazo',
        'category': 'imobiliario',
        'icon': 'Home',
        'color': '#D97706',
        'legal_basis': 'Lei 8.245/1991 (Lei do Inquilinato), arts. 5º-9º e arts. 59-66',
        'display_order': 1,
    },
    {
        'code': 'contrato_locacao',
        'name': 'Contrato de Locação de Imóvel',
        'short_name': 'Contrato Locação',
        'description': 'Contrato de locação residencial ou comercial conforme Lei do Inquilinato',
        'category': 'imobiliario',
        'icon': 'FileSignature',
        'color': '#D97706',
        'legal_basis': 'Lei 8.245/1991; CC/2002, arts. 565-578',
        'display_order': 2,
    },
    {
        'code': 'acao_renovatoria',
        'name': 'Ação Renovatória',
        'short_name': 'Ação Renovatória',
        'description': 'Ação para renovação compulsória de contrato de locação comercial',
        'category': 'imobiliario',
        'icon': 'RefreshCw',
        'color': '#D97706',
        'legal_basis': 'Lei 8.245/1991, arts. 51-57',
        'display_order': 3,
    },
    {
        'code': 'adjudicacao_compulsoria',
        'name': 'Ação de Adjudicação Compulsória',
        'short_name': 'Adjudicação Comp.',
        'description': 'Ação para obtenção de escritura definitiva quando o vendedor se recusa a outorgá-la',
        'category': 'imobiliario',
        'icon': 'Key',
        'color': '#059669',
        'legal_basis': 'CC/2002, arts. 1.417-1.418; CPC/2015, art. 501; STJ Súmulas 239, 413',
        'display_order': 4,
    },
    {
        'code': 'retificacao_registro_imovel',
        'name': 'Ação de Retificação de Registro Imobiliário',
        'short_name': 'Retificação Registro',
        'description': 'Ação para corrigir erro ou inconsistência na matrícula do imóvel no registro',
        'category': 'imobiliario',
        'icon': 'Edit',
        'color': '#059669',
        'legal_basis': 'Lei 6.015/1973 (LRP), arts. 212-214; CPC/2015, arts. 567-570',
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
- Conteúdo inferido: [VERIFICAR COM ADVOGADO]
"""

PROMPT_GERADOR_IMOBILIARIO = CONST_ANTI_ALUCINACAO + """Você é advogado especialista em Direito Imobiliário, Locação e Direito Registral brasileiro.

LEGISLAÇÃO VIGENTE:
- Lei 8.245/1991 (Lei do Inquilinato); CC/2002, arts. 565-578 (locação)
- Lei 6.015/1973 (Lei de Registros Públicos); CC/2002, arts. 1.196-1.510 (direitos reais)
- CC/2002, arts. 1.417-1.418 (promessa de compra e venda); CPC/2015

REGRAS ESSENCIAIS:
1. Despejo por falta de pagamento: Lei 8.245 art. 62 (rito especial com 15 dias para purga)
2. Despejo por término do prazo: Lei 8.245 art. 46 (30 dias para desocupação)
3. Ação renovatória: requisitos art. 51 (prazo mínimo 5 anos, último contrato mínimo 3 anos)
4. Prazo da renovatória: art. 51 §5º — 1 ano a 6 meses antes do término
5. Adjudicação compulsória: CC arts. 1.417-1.418. STJ Súmula 239 (não exige quitação prévia)
6. Retificação administrativa (LRP art. 213) vs judicial (LRP art. 212)
7. Contrato de locação: Lei 8.245 — cláusulas obrigatórias, garantias (art. 37), multa rescisória
8. Jurisprudência: Súmulas STJ: 239, 248, 259, 265, 322, 370, 371, 373, 385, 404, 408, 413, 449
9. Acórdãos: [VERIFICAR JURISPRUDÊNCIA: tema]

Gere APENAS o conteúdo da seção solicitada, sem preâmbulo."""

PROMPT_VALIDADOR_JURIDICO = """Você é revisor jurídico de peças processuais brasileiras.
Avalie: linguagem formal, embasamento legal correto, coerência e completude.
Retorne SEMPRE JSON: {"valid": true/false, "score": 0-100, "feedback": ["obs1"]}"""

AGENTE_POR_TIPO = {
    'acao_despejo': 'gerador_imobiliario',
    'contrato_locacao': 'gerador_imobiliario',
    'acao_renovatoria': 'gerador_imobiliario',
    'adjudicacao_compulsoria': 'gerador_imobiliario',
    'retificacao_registro_imovel': 'gerador_imobiliario',
}

BLUEPRINTS_DATA = [
    {
        'doc_type_code': 'acao_despejo',
        'name': 'Ação de Despejo - Lei 8.245/1991',
        'description': 'Petição inicial para retomada de imóvel locado por falta de pagamento ou término do prazo',
        'version': '1.0',
        'legal_basis': 'Lei 8.245/1991, arts. 59-66',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Ação de Despejo',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação das Partes',
                'description': 'Juízo e partes',
                'instructions': 'Endereçe ao Juízo Cível competente. Qualifique locador (autor) e locatário (réu). Identifique o imóvel (endereço completo, matrícula).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca', 'type': 'text', 'required': True},
                    {'name': 'locador_nome', 'label': 'Nome do Locador (Autor)', 'type': 'text', 'required': True},
                    {'name': 'locatario_nome', 'label': 'Nome do Locatário (Réu)', 'type': 'text', 'required': True},
                    {'name': 'imovel_endereco', 'label': 'Endereço Completo do Imóvel', 'type': 'text', 'required': True},
                    {'name': 'motivo_despejo', 'label': 'Motivo do Despejo', 'type': 'select', 'required': True, 'options': ['Falta de pagamento (art. 62)', 'Término do prazo determinado (art. 46)', 'Uso próprio do locador (art. 47 III)', 'Denúncia imotivada - locação residencial (art. 46 §1º)', 'Infração contratual (art. 9º II)', 'Necessidade de reparos urgentes (art. 9º IV)']},
                ],
            },
            {
                'number': 2, 'key': 'fatos',
                'name': 'I - Dos Fatos',
                'description': 'Histórico da locação e motivo do despejo',
                'instructions': 'Narre: início da locação, valor do aluguel, histórico de inadimplência ou circunstância que fundamenta o despejo, notificação prévia ao locatário (se realizada), valor em aberto.',
                'fields': [
                    {'name': 'data_inicio_locacao', 'label': 'Data de Início da Locação', 'type': 'text', 'required': True},
                    {'name': 'valor_aluguel', 'label': 'Valor do Aluguel Mensal (R$)', 'type': 'text', 'required': True},
                    {'name': 'debito_total', 'label': 'Débito Total em Aberto (R$)', 'type': 'text', 'required': False},
                    {'name': 'notificacao_previa', 'label': 'Notificação Prévia ao Locatário?', 'type': 'select', 'required': True, 'options': ['Sim (extrajudicial)', 'Sim (carta com AR)', 'Não']},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos de despejo e cobrança',
                'instructions': 'Formule pedidos: decretação do despejo, liminar de desocupação (Lei 8.245 arts. 59 §1º e 63), cobrança dos aluguéis vencidos e vincendos, multa e encargos contratuais, honorários advocatícios.',
                'fields': [
                    {'name': 'pedido_liminar', 'label': 'Pedido de Liminar de Despejo?', 'type': 'select', 'required': True, 'options': ['Sim (art. 59 §1º da Lei 8.245)', 'Não']},
                    {'name': 'pedido_cobranca_cumulado', 'label': 'Pedido de cobrança cumulado?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'contrato_locacao',
        'name': 'Contrato de Locação de Imóvel - Lei 8.245/1991',
        'description': 'Contrato de locação residencial ou comercial conforme a Lei do Inquilinato',
        'version': '1.0',
        'legal_basis': 'Lei 8.245/1991; CC/2002, arts. 565-578',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Contrato de Locação',
        'sections': [
            {
                'number': 1, 'key': 'partes_imovel',
                'name': 'Identificação das Partes e do Imóvel',
                'description': 'Locador, locatário e descrição do imóvel',
                'instructions': 'Qualifique o locador (proprietário) e o locatário. Descreva o imóvel (endereço, matrícula, área, características). Informe a finalidade (residencial ou não residencial).',
                'fields': [
                    {'name': 'locador_nome', 'label': 'Nome/Razão Social do Locador', 'type': 'text', 'required': True},
                    {'name': 'locatario_nome', 'label': 'Nome/Razão Social do Locatário', 'type': 'text', 'required': True},
                    {'name': 'imovel_descricao', 'label': 'Descrição do Imóvel (endereço, tipo, área, matrícula)', 'type': 'textarea', 'required': True},
                    {'name': 'finalidade', 'label': 'Finalidade da Locação', 'type': 'select', 'required': True, 'options': ['Residencial', 'Comercial/Não residencial', 'Temporada (máx. 90 dias)']},
                ],
            },
            {
                'number': 2, 'key': 'prazo_valor',
                'name': 'Cláusula 1ª - Prazo, Valor e Reajuste',
                'description': 'Vigência, aluguel e reajuste anual',
                'instructions': 'Estabeleça: prazo de vigência (determinado ou indeterminado), valor do aluguel mensal, data de vencimento, índice de reajuste anual (IGP-M ou IPCA), forma de pagamento.',
                'fields': [
                    {'name': 'prazo_meses', 'label': 'Prazo de Vigência (meses ou "indeterminado")', 'type': 'text', 'required': True},
                    {'name': 'valor_aluguel', 'label': 'Valor do Aluguel Mensal (R$)', 'type': 'text', 'required': True},
                    {'name': 'vencimento', 'label': 'Dia de Vencimento do Aluguel', 'type': 'text', 'required': True},
                    {'name': 'indice_reajuste', 'label': 'Índice de Reajuste Anual', 'type': 'select', 'required': True, 'options': ['IGP-M (FGV)', 'IPCA (IBGE)', 'INPC (IBGE)', 'IPC-A (IBGE)']},
                ],
            },
            {
                'number': 3, 'key': 'garantia_obrigacoes',
                'name': 'Cláusula 2ª - Garantia e Obrigações das Partes',
                'description': 'Garantia locatícia e deveres de locador e locatário',
                'instructions': 'Especifique a garantia (Lei 8.245 art. 37: fiança, caução, seguro, cessão de crédito — apenas uma por contrato). Descreva obrigações do locador (arts. 22-23) e do locatário (arts. 23-24). Multa por rescisão antecipada.',
                'fields': [
                    {'name': 'tipo_garantia', 'label': 'Tipo de Garantia (art. 37 Lei 8.245)', 'type': 'select', 'required': True, 'options': ['Fiança (fiador)', 'Caução em dinheiro (máx. 3 meses)', 'Seguro fiança', 'Cessão fiduciária de cotas', 'Sem garantia']},
                    {'name': 'multa_rescisao', 'label': 'Multa por Rescisão Antecipada', 'type': 'text', 'required': True},
                    {'name': 'encargos_locatorio', 'label': 'Encargos (IPTU, condomínio: quem paga)', 'type': 'textarea', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'acao_renovatoria',
        'name': 'Ação Renovatória - Lei 8.245/1991',
        'description': 'Petição para renovação compulsória de locação comercial (5+ anos de contrato)',
        'version': '1.0',
        'legal_basis': 'Lei 8.245/1991, arts. 51-57',
        'primary_color': '#D97706',
        'secondary_color': '#F59E0B',
        'cover_title': 'Ação Renovatória',
        'sections': [
            {
                'number': 1, 'key': 'requisitos_admissibilidade',
                'name': 'Requisitos de Admissibilidade da Renovatória',
                'description': 'Verificação dos requisitos legais para a ação renovatória',
                'instructions': 'Demonstre o preenchimento dos requisitos da Lei 8.245 art. 51: contrato escrito com prazo determinado, prazo mínimo de 5 anos (ou somatório), exercício do mesmo ramo por mínimo de 3 anos. Demonstre tempestividade: entre 1 ano e 6 meses antes do término.',
                'fields': [
                    {'name': 'locador_nome', 'label': 'Nome do Locador (Réu)', 'type': 'text', 'required': True},
                    {'name': 'locatario_nome', 'label': 'Nome do Locatário/Empresa (Autor)', 'type': 'text', 'required': True},
                    {'name': 'imovel_endereco', 'label': 'Endereço do Imóvel Comercial', 'type': 'text', 'required': True},
                    {'name': 'tempo_locacao', 'label': 'Tempo Total de Locação (anos)', 'type': 'text', 'required': True},
                    {'name': 'data_termino_contrato', 'label': 'Data de Término do Contrato Atual', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'proposta_renovacao',
                'name': 'I - Da Proposta de Renovação',
                'description': 'Condições da renovação pleiteada',
                'instructions': 'Apresente a proposta de renovação: novo prazo (igual ao anterior), valor do aluguel proposto (laudo pericial de avaliação), demais condições contratuais. Demonstre o fundo de comércio e goodwill do locatário.',
                'fields': [
                    {'name': 'novo_prazo', 'label': 'Novo Prazo Pleiteado (anos)', 'type': 'text', 'required': True},
                    {'name': 'aluguel_proposto', 'label': 'Valor do Aluguel Proposto (R$/mês)', 'type': 'text', 'required': True},
                    {'name': 'atividade_comercial', 'label': 'Atividade Comercial Desenvolvida no Local', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Pedidos da ação renovatória',
                'instructions': 'Pedidos: renovação compulsória do contrato (art. 51 Lei 8.245), pelo prazo e valor propostos, nomeação de perito avaliador para fixar o aluguel justo, indenização pelo fundo de comércio se locador retomar (art. 52 §3º).',
                'fields': [
                    {'name': 'pedido_pericia', 'label': 'Pedido de perícia para fixação do aluguel?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (12× aluguel proposto)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'adjudicacao_compulsoria',
        'name': 'Ação de Adjudicação Compulsória - CC/2002',
        'description': 'Ação para obtenção de escritura definitiva quando o vendedor se recusa a outorgá-la',
        'version': '1.0',
        'legal_basis': 'CC/2002, arts. 1.417-1.418; CPC/2015, art. 501',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Adjudicação Compulsória',
        'sections': [
            {
                'number': 1, 'key': 'enderecamento',
                'name': 'Endereçamento e Qualificação',
                'description': 'Juízo, comprador e vendedor',
                'instructions': 'Endereçe ao Juízo Cível. Qualifique o comprador (autor) e o vendedor (réu). Identifique o imóvel (endereço, matrícula no CRI).',
                'fields': [
                    {'name': 'comarca', 'label': 'Comarca (do imóvel - competência real)', 'type': 'text', 'required': True},
                    {'name': 'comprador_nome', 'label': 'Nome do Comprador (Autor)', 'type': 'text', 'required': True},
                    {'name': 'vendedor_nome', 'label': 'Nome do Vendedor (Réu)', 'type': 'text', 'required': True},
                    {'name': 'imovel_matricula', 'label': 'Matrícula do Imóvel no CRI', 'type': 'text', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fatos_quitacao',
                'name': 'I - Dos Fatos e da Quitação do Preço',
                'description': 'Promessa de compra e venda e quitação do preço',
                'instructions': 'Descreva: contrato de promessa de compra e venda (data, partes, valor, imóvel), pagamento integral do preço (ou quitação conforme STJ Súmula 239), recusa do vendedor em outorgar a escritura definitiva.',
                'fields': [
                    {'name': 'data_promessa', 'label': 'Data da Promessa de Compra e Venda', 'type': 'text', 'required': True},
                    {'name': 'valor_total', 'label': 'Valor Total do Imóvel (R$)', 'type': 'text', 'required': True},
                    {'name': 'quitacao', 'label': 'O preço foi totalmente quitado?', 'type': 'select', 'required': True, 'options': ['Sim - quitação integral', 'Sim - STJ Súmula 239 (não exige quitação)', 'Parcialmente - com oferta de saldo devedor']},
                    {'name': 'motivo_recusa', 'label': 'Motivo da Recusa do Vendedor em Outorgar a Escritura', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 3, 'key': 'pedidos',
                'name': 'II - Dos Pedidos',
                'description': 'Adjudicação e registro',
                'instructions': 'Pedidos: adjudicação compulsória do imóvel (CC art. 1.418), sentença que sirva como título para registro (CPC art. 501), registro da propriedade no CRI, honorários.',
                'fields': [
                    {'name': 'valor_causa', 'label': 'Valor da Causa (valor do imóvel)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
    {
        'doc_type_code': 'retificacao_registro_imovel',
        'name': 'Ação de Retificação de Registro Imobiliário - LRP',
        'description': 'Ação para corrigir erro ou inconsistência na matrícula do imóvel no CRI',
        'version': '1.0',
        'legal_basis': 'Lei 6.015/1973 (LRP), arts. 212-214; CPC/2015, arts. 567-570',
        'primary_color': '#059669',
        'secondary_color': '#10B981',
        'cover_title': 'Retificação de Registro',
        'sections': [
            {
                'number': 1, 'key': 'identificacao_imovel',
                'name': 'Identificação do Imóvel e do Erro',
                'description': 'Dados do imóvel e natureza do erro a corrigir',
                'instructions': 'Identifique o imóvel (matrícula, CRI, endereço). Descreva com precisão o erro a ser corrigido: área, confrontantes, descrição, nome do proprietário, etc. Informe se é retificação administrativa (LRP art. 213) ou judicial (LRP art. 212).',
                'fields': [
                    {'name': 'matricula_imovel', 'label': 'Matrícula do Imóvel', 'type': 'text', 'required': True},
                    {'name': 'cri_nome', 'label': 'Cartório de Registro de Imóveis (CRI)', 'type': 'text', 'required': True},
                    {'name': 'tipo_retificacao', 'label': 'Tipo de Retificação', 'type': 'select', 'required': True, 'options': ['Administrativa - LRP art. 213 (erro sem litígio)', 'Judicial - LRP art. 212 (com litígio ou confrontante não concorda)', 'Judicial - área divergente do levantamento']},
                    {'name': 'descricao_erro', 'label': 'Descrição do Erro na Matrícula (o que está errado)', 'type': 'textarea', 'required': True},
                    {'name': 'descricao_correto', 'label': 'Como Deve Ficar Após a Retificação', 'type': 'textarea', 'required': True},
                ],
            },
            {
                'number': 2, 'key': 'fundamento_pedidos',
                'name': 'I - Do Direito e Dos Pedidos',
                'description': 'Fundamentos e pedidos de retificação',
                'instructions': 'Fundamente: LRP arts. 212-214, georreferenciamento (Lei 10.267/2001 para imóveis rurais), concordância de confrontantes. Pedidos: retificação da matrícula conforme descrição apresentada, averbação da retificação.',
                'fields': [
                    {'name': 'laudo_georreferenciamento', 'label': 'Há laudo de georreferenciamento/levantamento?', 'type': 'select', 'required': True, 'options': ['Sim', 'Não - será produzido', 'Não necessário (erro de nome/textual)']},
                    {'name': 'valor_causa', 'label': 'Valor da Causa (valor venal do imóvel)', 'type': 'text', 'required': True},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria blueprints de Imobiliário e Locação no Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria blueprints existentes')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria feito')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Verus.AI — Seed Imobiliário e Locação'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN\n'))
            return
        with transaction.atomic():
            self._criar_categorias()
            self._criar_tipos_documento()
            agentes = self._criar_agentes_secao()
            self._criar_blueprints(agentes, force)
        self.stdout.write(self.style.SUCCESS('\n✓ Imobiliário e Locação concluído!\n'))

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
            {'key': 'gerador_imobiliario', 'name': 'Verus.AI - Gerador Imobiliário', 'description': 'Gera peças de Direito Imobiliário e Locação', 'agent_type': 'generator', 'system_prompt': PROMPT_GERADOR_IMOBILIARIO, 'temperature': TEMP_GENERATOR, 'max_tokens': MAX_TOKENS, 'is_default': False},
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
                agente_key = AGENTE_POR_TIPO.get(bp_data['doc_type_code'], 'gerador_imobiliario')
                for sec in bp_data['sections']:
                    BlueprintSection.objects.get_or_create(
                        blueprint=blueprint,
                        section_number=sec['number'],
                        defaults={'section_name': sec['name'], 'section_key': sec['key'], 'description': sec.get('description', ''), 'instructions': sec.get('instructions', ''), 'order': sec['number'], 'is_required': True, 'allow_skip': False, 'max_generation_attempts': 2, 'generator_agent': agentes.get(agente_key), 'validator_agent': agentes.get('validador_juridico'), 'section_fields': sec.get('fields', []), 'is_active': True}
                    )
                self.stdout.write(f'       → {len(bp_data["sections"])} seções criadas')
