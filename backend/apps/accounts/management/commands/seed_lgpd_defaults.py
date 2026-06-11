"""
Management command para popular dados padroes de LGPD.

Usage:
    python manage.py seed_lgpd_defaults
    python manage.py seed_lgpd_defaults --force   # Recria mesmo se existirem
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import DataProcessingActivity, ConsentTerm


DEFAULT_DPAS = [
    {
        'name': 'Gestao de processos judiciais e administrativos',
        'purpose': (
            'Tratamento de dados pessoais de clientes para acompanhamento, '
            'elaboracao de pecas processuais, representacao judicial e administrativa.'
        ),
        'legal_basis': 'contract',
        'data_categories': ['nome', 'CPF/CNPJ', 'endereco', 'telefone', 'email', 'dados processuais'],
        'retention_period': '5 anos apos o encerramento do processo (art. 1.056 CC e art. 23 ECA)',
        'shared_with': ['tribunais', 'orgaos publicos'],
        'risk_level': 'medio',
    },
    {
        'name': 'Cadastro e identificacao de clientes',
        'purpose': (
            'Coleta e armazenamento de dados pessoais para cadastro de clientes, '
            'verificacao de identidade e cumprimento de obrigacoes contratuais.'
        ),
        'legal_basis': 'contract',
        'data_categories': ['nome', 'CPF/CNPJ', 'RG', 'endereco', 'telefone', 'email', 'profissao'],
        'retention_period': '5 anos apos encerramento da relacao contratual',
        'shared_with': [],
        'risk_level': 'baixo',
    },
    {
        'name': 'Comunicacao com clientes',
        'purpose': (
            'Envio de notificacoes, atualizacoes de processos, lembretes de prazos '
            'e comunicacoes institucionais por email, telefone ou WhatsApp.'
        ),
        'legal_basis': 'legitimate_interest',
        'data_categories': ['nome', 'email', 'telefone', 'whatsapp'],
        'retention_period': 'Durante a vigencia do contrato',
        'shared_with': ['provedores de email', 'provedores de WhatsApp Business'],
        'risk_level': 'baixo',
    },
    {
        'name': 'Armazenamento de documentos juridicos',
        'purpose': (
            'Guarda e organizacao de documentos, contratos, procuracoes e pecas processuais '
            'contendo dados pessoais de clientes e partes envolvidas.'
        ),
        'legal_basis': 'legal_obligation',
        'data_categories': ['dados pessoais em documentos', 'dados sensiveis quando aplicavel'],
        'retention_period': '10 anos (conforme legislacao aplicavel)',
        'shared_with': ['servicos de armazenamento em nuvem (criptografados)'],
        'risk_level': 'alto',
    },
    {
        'name': 'Cobranca de honorarios e gestao financeira',
        'purpose': (
            'Emissao de notas fiscais, controle de honorarios, cobrancas '
            'e cumprimento de obrigacoes tributarias.'
        ),
        'legal_basis': 'legal_obligation',
        'data_categories': ['nome', 'CPF/CNPJ', 'endereco', 'dados bancarios', 'valores'],
        'retention_period': '5 anos (legislacao tributaria)',
        'shared_with': ['contabilidade', 'sistema ERP', 'Receita Federal'],
        'risk_level': 'medio',
    },
]

DEFAULT_CONSENT_TERMS = [
    {
        'title': 'Termo de Consentimento para Tratamento de Dados Pessoais',
        'version': '1.0',
        'purpose': 'data_processing',
        'content': (
            '<h2>Termo de Consentimento para Tratamento de Dados Pessoais</h2>'
            '<p>Em conformidade com a Lei Geral de Protecao de Dados Pessoais '
            '(Lei n. 13.709/2018 - LGPD), este termo visa registrar a manifestacao '
            'livre, informada e inequivoca pela qual o titular concorda com o '
            'tratamento de seus dados pessoais para as finalidades abaixo especificadas.</p>'
            '<h3>1. Controlador</h3>'
            '<p>[Nome do Escritorio de Advocacia], inscrito no CNPJ sob o n. [CNPJ], '
            'com sede em [endereco].</p>'
            '<h3>2. Dados Coletados</h3>'
            '<p>Nome completo, CPF, RG, endereco, telefone, email, dados processuais '
            'e demais informacoes necessarias a prestacao dos servicos juridicos.</p>'
            '<h3>3. Finalidades</h3>'
            '<ul>'
            '<li>Prestacao de servicos juridicos e representacao processual</li>'
            '<li>Comunicacao sobre andamento de processos</li>'
            '<li>Cumprimento de obrigacoes legais e regulatorias</li>'
            '</ul>'
            '<h3>4. Compartilhamento</h3>'
            '<p>Os dados poderao ser compartilhados com tribunais, orgaos publicos '
            'e parceiros estritamente necessarios a prestacao dos servicos.</p>'
            '<h3>5. Retencao</h3>'
            '<p>Os dados serao mantidos durante a vigencia do contrato e por 5 (cinco) '
            'anos apos seu encerramento, salvo obrigacao legal de guarda por prazo superior.</p>'
            '<h3>6. Direitos do Titular</h3>'
            '<p>O titular pode, a qualquer momento, solicitar: acesso, correcao, '
            'eliminacao, portabilidade ou revogacao do consentimento, '
            'entrando em contato pelo email [email do DPO].</p>'
            '<h3>7. Revogacao</h3>'
            '<p>Este consentimento pode ser revogado a qualquer momento, '
            'sem prejuizo da legalidade do tratamento realizado anteriormente.</p>'
        ),
    },
    {
        'title': 'Termo de Consentimento para Comunicacoes de Marketing',
        'version': '1.0',
        'purpose': 'marketing',
        'content': (
            '<h2>Termo de Consentimento para Comunicacoes de Marketing</h2>'
            '<p>Em conformidade com a Lei Geral de Protecao de Dados Pessoais '
            '(Lei n. 13.709/2018 - LGPD), este termo visa registrar o consentimento '
            'do titular para o recebimento de comunicacoes de marketing.</p>'
            '<h3>1. Finalidade</h3>'
            '<p>Envio de newsletters, informativos juridicos, convites para eventos, '
            'webinars e conteudos educativos relacionados a area juridica.</p>'
            '<h3>2. Dados Utilizados</h3>'
            '<p>Nome, email e preferencias de comunicacao.</p>'
            '<h3>3. Frequencia</h3>'
            '<p>As comunicacoes serao enviadas com periodicidade maxima semanal, '
            'podendo o titular ajustar suas preferencias a qualquer momento.</p>'
            '<h3>4. Cancelamento</h3>'
            '<p>O titular pode cancelar o recebimento a qualquer momento, '
            'clicando no link de descadastro presente em cada comunicacao '
            'ou entrando em contato pelo email [email do DPO].</p>'
            '<h3>5. Revogacao</h3>'
            '<p>Este consentimento pode ser revogado a qualquer momento, '
            'sem prejuizo da legalidade do tratamento realizado anteriormente.</p>'
        ),
    },
    {
        'title': 'Termo de Consentimento para Compartilhamento de Dados',
        'version': '1.0',
        'purpose': 'sharing',
        'content': (
            '<h2>Termo de Consentimento para Compartilhamento de Dados com Terceiros</h2>'
            '<p>Em conformidade com a Lei Geral de Protecao de Dados Pessoais '
            '(Lei n. 13.709/2018 - LGPD), este termo visa registrar o consentimento '
            'do titular para o compartilhamento de seus dados pessoais com terceiros.</p>'
            '<h3>1. Finalidade</h3>'
            '<p>Compartilhamento de dados com escritorios parceiros, peritos, '
            'consultores tecnicos e demais profissionais necessarios a prestacao '
            'dos servicos juridicos contratados.</p>'
            '<h3>2. Dados Compartilhados</h3>'
            '<p>Nome, CPF, dados processuais e documentos pertinentes ao caso, '
            'limitados ao estritamente necessario para cada finalidade.</p>'
            '<h3>3. Destinatarios</h3>'
            '<p>Os dados poderao ser compartilhados com: escritorios de advocacia parceiros, '
            'peritos judiciais, contabilidade, e prestadores de servicos de tecnologia '
            '(armazenamento em nuvem criptografado).</p>'
            '<h3>4. Garantias</h3>'
            '<p>Todos os terceiros receptores estao obrigados contratualmente a observar '
            'as disposicoes da LGPD e a manter a confidencialidade dos dados recebidos.</p>'
            '<h3>5. Revogacao</h3>'
            '<p>Este consentimento pode ser revogado a qualquer momento, '
            'sem prejuizo da legalidade do compartilhamento realizado anteriormente.</p>'
        ),
    },
]


class Command(BaseCommand):
    help = 'Popula dados padroes de LGPD (atividades de tratamento e termo de consentimento)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true',
            help='Recria os registros mesmo se ja existirem',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Seed DataProcessingActivities
        existing_dpas = DataProcessingActivity.objects.count()
        if existing_dpas > 0 and not force:
            self.stdout.write(
                self.style.WARNING(f'{existing_dpas} atividades de tratamento ja existem. Use --force para recriar.')
            )
        else:
            if force:
                DataProcessingActivity.objects.all().delete()
            for dpa_data in DEFAULT_DPAS:
                DataProcessingActivity.objects.create(**dpa_data)
            self.stdout.write(
                self.style.SUCCESS(f'{len(DEFAULT_DPAS)} atividades de tratamento criadas.')
            )

        # Seed ConsentTerms
        existing_terms = ConsentTerm.objects.count()
        if existing_terms > 0 and not force:
            self.stdout.write(
                self.style.WARNING(f'{existing_terms} termos de consentimento ja existem. Use --force para recriar.')
            )
        else:
            if force:
                ConsentTerm.objects.all().delete()
            for term_data in DEFAULT_CONSENT_TERMS:
                ConsentTerm.objects.create(**term_data)
            self.stdout.write(
                self.style.SUCCESS(f'{len(DEFAULT_CONSENT_TERMS)} termos de consentimento padrao criados.')
            )

        self.stdout.write(self.style.SUCCESS('Seed LGPD concluido.'))
