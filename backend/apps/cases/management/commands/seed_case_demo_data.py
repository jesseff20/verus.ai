"""
Management command para popular dados demo (prazos, tarefas, audiencias,
movimentacoes financeiras) nos casos existentes do Verus.AI.

Uso: python manage.py seed_case_demo_data

Idempotente — usa get_or_create em todos os registros.
"""
from datetime import date, timedelta, datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.cases.models import (
    LegalCase,
    LegalDeadline,
    CaseTask,
    Audiencia,
    MovimentacaoFinanceira,
)


# ---------------------------------------------------------------------------
# Dados por caso (match via icontains no titulo)
# ---------------------------------------------------------------------------

CASE_DATA = [
    # 1. Costa vs TransLog (Trabalhista)
    {
        'match': 'Costa',
        'deadlines': [
            {
                'titulo': 'Prazo para Contestação',
                'tipo': 'processual',
                'prioridade': 'urgente',
                'status': 'pendente',
                'dias': 5,
                'descricao': 'Prazo fatal para apresentação de contestação trabalhista',
            },
            {
                'titulo': 'Audiência de Conciliação',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 30,
                'descricao': 'Audiência de conciliação na Vara do Trabalho',
            },
            {
                'titulo': 'Juntada de documentos complementares',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'pendente',
                'dias': 15,
                'descricao': 'Prazo para juntada de holerites e comprovantes',
            },
        ],
        'tasks': [
            {
                'titulo': 'Calcular verbas rescisórias',
                'descricao': 'Elaborar planilha detalhada com todas as verbas rescisórias devidas: saldo de salário, férias proporcionais, 13o proporcional, FGTS + multa 40%, aviso prévio',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 8,
            },
            {
                'titulo': 'Reunir holerites e CTPS',
                'descricao': 'Solicitar ao cliente cópias de todos os holerites, CTPS com anotações e extrato do FGTS',
                'status': 'pendente',
                'prioridade': 'urgente',
                'dias_limite': 3,
            },
            {
                'titulo': 'Preparar rol de testemunhas',
                'descricao': 'Identificar e qualificar testemunhas que possam depor sobre as condições de trabalho e demissão',
                'status': 'pendente',
                'prioridade': 'media',
                'dias_limite': 20,
            },
        ],
        'audiencias': [
            {
                'tipo': 'conciliacao',
                'status': 'agendada',
                'dias': 30,
                'hora': 14,
                'local': '5a Vara do Trabalho de São Paulo',
                'juiz': 'Dr. Marcos Antônio Ferreira',
            },
        ],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Custas processuais iniciais',
                'valor': '350.00',
                'status': 'pago',
                'dias_vencimento': -5,
            },
            {
                'tipo': 'honorario',
                'descricao': 'Honorários advocatícios - parcela 1/3',
                'valor': '5000.00',
                'status': 'pendente',
                'dias_vencimento': 15,
            },
        ],
    },

    # 2. Silva vs Pereira (Criminal)
    {
        'match': 'Silva',
        'deadlines': [
            {
                'titulo': 'Resposta à Acusação',
                'tipo': 'processual',
                'prioridade': 'urgente',
                'status': 'pendente',
                'dias': 10,
                'descricao': 'Prazo para apresentação de resposta à acusação (art. 396 CPP)',
            },
            {
                'titulo': 'Audiência de Instrução e Julgamento',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 45,
                'descricao': 'AIJ com oitiva de testemunhas e interrogatório do réu',
            },
            {
                'titulo': 'Prazo para Alegações Finais',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'pendente',
                'dias': 60,
                'descricao': 'Prazo para apresentação de memoriais / alegações finais',
            },
        ],
        'tasks': [
            {
                'titulo': 'Organizar prints e provas digitais',
                'descricao': 'Coletar, autenticar e organizar todas as provas digitais (prints de conversas, e-mails, registros de acesso)',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 7,
            },
            {
                'titulo': 'Arrolar testemunhas de defesa',
                'descricao': 'Identificar e arrolar até 8 testemunhas de defesa conforme art. 401 CPP',
                'status': 'pendente',
                'prioridade': 'alta',
                'dias_limite': 8,
            },
            {
                'titulo': 'Solicitar perícia em dispositivos',
                'descricao': 'Requerer perícia técnica nos dispositivos eletrônicos apreendidos',
                'status': 'pendente',
                'prioridade': 'media',
                'dias_limite': 12,
            },
        ],
        'audiencias': [
            {
                'tipo': 'instrucao',
                'status': 'agendada',
                'dias': 45,
                'hora': 9,
                'local': '2a Vara Criminal da Comarca de São Paulo',
                'juiz': 'Dra. Patrícia Helena Costa',
            },
        ],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Custas processuais - criminal',
                'valor': '200.00',
                'status': 'pago',
                'dias_vencimento': -10,
            },
            {
                'tipo': 'pericia',
                'descricao': 'Perícia técnica em dispositivos eletrônicos',
                'valor': '8000.00',
                'status': 'pendente',
                'dias_vencimento': 30,
            },
        ],
    },

    # 3. Oliveira vs Banco Central (Consumidor)
    {
        'match': 'Oliveira',
        'deadlines': [
            {
                'titulo': 'Prazo para Réplica',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 15,
                'descricao': 'Prazo para réplica à contestação do banco',
            },
            {
                'titulo': 'Audiência de Conciliação',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'pendente',
                'dias': 60,
                'descricao': 'Audiência de conciliação no Juizado Especial Cível',
            },
            {
                'titulo': 'Prazo para especificação de provas',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'pendente',
                'dias': 20,
                'descricao': 'Indicar provas que pretende produzir',
            },
        ],
        'tasks': [
            {
                'titulo': 'Solicitar extratos bancários',
                'descricao': 'Requerer ao banco réu cópia de todos os extratos dos últimos 24 meses com detalhamento de tarifas cobradas',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 10,
            },
            {
                'titulo': 'Preparar cálculo de danos morais',
                'descricao': 'Elaborar memorial de cálculo dos danos morais e materiais sofridos pelo consumidor, incluindo juros e correção monetária',
                'status': 'pendente',
                'prioridade': 'alta',
                'dias_limite': 12,
            },
            {
                'titulo': 'Pesquisar jurisprudência favorável',
                'descricao': 'Levantar precedentes do STJ e TJSP sobre cobrança indevida de tarifas bancárias',
                'status': 'concluida',
                'prioridade': 'media',
                'dias_limite': -3,
            },
        ],
        'audiencias': [
            {
                'tipo': 'conciliacao',
                'status': 'agendada',
                'dias': 60,
                'hora': 10,
                'local': '15o Juizado Especial Cível de São Paulo',
                'juiz': 'Dr. Eduardo Nascimento',
            },
        ],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Isento - Juizado Especial (1o grau)',
                'valor': '0.00',
                'status': 'pago',
                'dias_vencimento': -15,
            },
            {
                'tipo': 'honorario',
                'descricao': 'Honorários advocatícios contratuais (30% do êxito)',
                'valor': '0.00',
                'status': 'pendente',
                'dias_vencimento': 90,
            },
        ],
    },

    # 4. Souza vs Prefeitura (Tributário)
    {
        'match': 'Souza',
        'deadlines': [
            {
                'titulo': 'Juntada de documentos fiscais',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 10,
                'descricao': 'Prazo para juntada de notas fiscais e comprovantes de pagamento de tributos',
            },
            {
                'titulo': 'Perícia contábil',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 45,
                'descricao': 'Prazo para realização de perícia contábil judicial',
            },
            {
                'titulo': 'Impugnação ao laudo pericial',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'pendente',
                'dias': 55,
                'descricao': 'Prazo para impugnação ao laudo do perito judicial',
            },
        ],
        'tasks': [
            {
                'titulo': 'Levantar notas fiscais',
                'descricao': 'Reunir todas as notas fiscais dos últimos 5 anos para demonstrar a base de cálculo correta do ISS',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 8,
            },
            {
                'titulo': 'Contratar perito contábil',
                'descricao': 'Indicar assistente técnico (perito-contador) para acompanhar a perícia judicial e elaborar parecer',
                'status': 'pendente',
                'prioridade': 'urgente',
                'dias_limite': 5,
            },
            {
                'titulo': 'Elaborar quesitos periciais',
                'descricao': 'Redigir quesitos para o perito judicial sobre a metodologia de cálculo do tributo',
                'status': 'pendente',
                'prioridade': 'alta',
                'dias_limite': 7,
            },
        ],
        'audiencias': [],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Custas processuais - Mandado de Segurança',
                'valor': '500.00',
                'status': 'pago',
                'dias_vencimento': -20,
            },
            {
                'tipo': 'pericia',
                'descricao': 'Honorários do perito judicial',
                'valor': '12000.00',
                'status': 'pendente',
                'dias_vencimento': 40,
            },
            {
                'tipo': 'honorario',
                'descricao': 'Honorários advocatícios - fase de conhecimento',
                'valor': '15000.00',
                'status': 'pendente',
                'dias_vencimento': 60,
            },
        ],
    },

    # 5. Família Rodrigues (Família/Inventário)
    {
        'match': 'Rodrigues',
        'deadlines': [
            {
                'titulo': 'Avaliação de imóveis',
                'tipo': 'extrajudicial',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 20,
                'descricao': 'Prazo para apresentação de laudos de avaliação dos imóveis do espólio',
            },
            {
                'titulo': 'Recolhimento do ITCMD',
                'tipo': 'processual',
                'prioridade': 'urgente',
                'status': 'pendente',
                'dias': 30,
                'descricao': 'Prazo para recolhimento do Imposto sobre Transmissão Causa Mortis e Doação',
            },
            {
                'titulo': 'Apresentação do plano de partilha',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 40,
                'descricao': 'Prazo para apresentar o esboço de partilha ao juízo',
            },
            {
                'titulo': 'Habilitação de herdeiros',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'concluido',
                'dias': -10,
                'descricao': 'Prazo para habilitação de todos os herdeiros no inventário',
            },
        ],
        'tasks': [
            {
                'titulo': 'Solicitar certidões de óbito',
                'descricao': 'Obter certidões de óbito atualizadas e certidões negativas de débitos do de cujus',
                'status': 'concluida',
                'prioridade': 'alta',
                'dias_limite': -5,
            },
            {
                'titulo': 'Levantar patrimônio do espólio',
                'descricao': 'Inventariar todos os bens: imóveis, veículos, contas bancárias, investimentos e participações societárias',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 15,
            },
            {
                'titulo': 'Calcular ITCMD devido',
                'descricao': 'Elaborar cálculo do ITCMD com base na avaliação dos bens e na legislação estadual vigente',
                'status': 'pendente',
                'prioridade': 'urgente',
                'dias_limite': 25,
            },
        ],
        'audiencias': [],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Custas do inventário judicial',
                'valor': '2500.00',
                'status': 'pago',
                'dias_vencimento': -30,
            },
            {
                'tipo': 'outro',
                'descricao': 'Avaliação imobiliária (2 imóveis)',
                'valor': '4000.00',
                'status': 'pendente',
                'dias_vencimento': 15,
            },
            {
                'tipo': 'honorario',
                'descricao': 'Honorários advocatícios - inventário',
                'valor': '25000.00',
                'status': 'pendente',
                'dias_vencimento': 45,
            },
        ],
    },

    # 6-10: Casos genéricos para qualquer caso adicional encontrado
    # Estes patterns tentam match com palavras comuns em títulos de casos
    {
        'match': 'Indenização',
        'deadlines': [
            {
                'titulo': 'Prazo para Impugnação à Contestação',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 15,
                'descricao': 'Prazo para impugnar a contestação apresentada pelo réu',
            },
            {
                'titulo': 'Audiência de Instrução',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 50,
                'descricao': 'Audiência de instrução e julgamento',
            },
        ],
        'tasks': [
            {
                'titulo': 'Preparar documentação probatória',
                'descricao': 'Reunir e organizar toda a documentação para instrução processual',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 10,
            },
            {
                'titulo': 'Elaborar quesitos para perito',
                'descricao': 'Preparar quesitos técnicos para eventual perícia',
                'status': 'pendente',
                'prioridade': 'media',
                'dias_limite': 20,
            },
        ],
        'audiencias': [
            {
                'tipo': 'instrucao',
                'status': 'agendada',
                'dias': 50,
                'hora': 13,
                'local': '7a Vara Cível de São Paulo',
                'juiz': 'Dr. Ricardo Moreira',
            },
        ],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Custas processuais',
                'valor': '450.00',
                'status': 'pago',
                'dias_vencimento': -8,
            },
        ],
    },

    {
        'match': 'Contrato',
        'deadlines': [
            {
                'titulo': 'Prazo para Contestação',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 15,
                'descricao': 'Prazo para apresentar contestação',
            },
            {
                'titulo': 'Audiência de Mediação',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'pendente',
                'dias': 40,
                'descricao': 'Sessão de mediação para tentativa de acordo',
            },
        ],
        'tasks': [
            {
                'titulo': 'Analisar cláusulas contratuais',
                'descricao': 'Revisar todas as cláusulas do contrato objeto da lide',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 7,
            },
            {
                'titulo': 'Calcular valores devidos',
                'descricao': 'Elaborar planilha com cálculo atualizado dos valores em discussão',
                'status': 'pendente',
                'prioridade': 'media',
                'dias_limite': 12,
            },
        ],
        'audiencias': [],
        'financeiro': [
            {
                'tipo': 'honorario',
                'descricao': 'Honorários advocatícios',
                'valor': '8000.00',
                'status': 'pendente',
                'dias_vencimento': 30,
            },
        ],
    },

    {
        'match': 'Imóvel',
        'deadlines': [
            {
                'titulo': 'Prazo para Emenda à Inicial',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 10,
                'descricao': 'Prazo para emendar a petição inicial conforme determinado pelo juízo',
            },
            {
                'titulo': 'Vistoria do imóvel',
                'tipo': 'processual',
                'prioridade': 'media',
                'status': 'pendente',
                'dias': 25,
                'descricao': 'Vistoria técnica no imóvel objeto da ação',
            },
        ],
        'tasks': [
            {
                'titulo': 'Obter matrícula atualizada',
                'descricao': 'Solicitar matrícula atualizada do imóvel no Cartório de Registro de Imóveis',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 5,
            },
            {
                'titulo': 'Contratar engenheiro para laudo',
                'descricao': 'Indicar assistente técnico (engenheiro civil) para elaborar laudo de avaliação',
                'status': 'pendente',
                'prioridade': 'media',
                'dias_limite': 15,
            },
        ],
        'audiencias': [],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Custas processuais',
                'valor': '600.00',
                'status': 'pago',
                'dias_vencimento': -12,
            },
            {
                'tipo': 'pericia',
                'descricao': 'Honorários do perito avaliador',
                'valor': '6000.00',
                'status': 'pendente',
                'dias_vencimento': 20,
            },
        ],
    },

    {
        'match': 'Previdenciário',
        'deadlines': [
            {
                'titulo': 'Prazo para Recurso Administrativo',
                'tipo': 'administrativo',
                'prioridade': 'urgente',
                'status': 'pendente',
                'dias': 10,
                'descricao': 'Prazo para interposição de recurso contra decisão do INSS',
            },
            {
                'titulo': 'Perícia médica judicial',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 35,
                'descricao': 'Perícia médica designada pelo juízo federal',
            },
        ],
        'tasks': [
            {
                'titulo': 'Reunir laudos médicos',
                'descricao': 'Coletar todos os laudos, exames e atestados médicos do segurado',
                'status': 'em_andamento',
                'prioridade': 'urgente',
                'dias_limite': 5,
            },
            {
                'titulo': 'Elaborar cálculo de RMI',
                'descricao': 'Calcular a Renda Mensal Inicial do benefício previdenciário pretendido',
                'status': 'pendente',
                'prioridade': 'alta',
                'dias_limite': 15,
            },
        ],
        'audiencias': [],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Isento - Justiça Federal (beneficiário)',
                'valor': '0.00',
                'status': 'pago',
                'dias_vencimento': -5,
            },
        ],
    },

    {
        'match': 'Divórcio',
        'deadlines': [
            {
                'titulo': 'Prazo para homologação',
                'tipo': 'processual',
                'prioridade': 'alta',
                'status': 'pendente',
                'dias': 15,
                'descricao': 'Prazo para homologação do acordo de divórcio',
            },
            {
                'titulo': 'Avaliação de bens comuns',
                'tipo': 'extrajudicial',
                'prioridade': 'media',
                'status': 'pendente',
                'dias': 25,
                'descricao': 'Prazo para avaliação dos bens a serem partilhados',
            },
        ],
        'tasks': [
            {
                'titulo': 'Inventariar bens do casal',
                'descricao': 'Levantar todos os bens adquiridos na constância do casamento para partilha',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'dias_limite': 10,
            },
            {
                'titulo': 'Elaborar acordo de guarda',
                'descricao': 'Redigir termos de guarda compartilhada, convivência e alimentos',
                'status': 'pendente',
                'prioridade': 'alta',
                'dias_limite': 12,
            },
        ],
        'audiencias': [
            {
                'tipo': 'conciliacao',
                'status': 'agendada',
                'dias': 20,
                'hora': 15,
                'local': '3a Vara de Família de Belo Horizonte',
                'juiz': 'Dra. Camila de Souza',
            },
        ],
        'financeiro': [
            {
                'tipo': 'custas',
                'descricao': 'Custas processuais - divórcio',
                'valor': '300.00',
                'status': 'pago',
                'dias_vencimento': -7,
            },
            {
                'tipo': 'honorario',
                'descricao': 'Honorários advocatícios - divórcio consensual',
                'valor': '6000.00',
                'status': 'pendente',
                'dias_vencimento': 30,
            },
        ],
    },
]


# Fallback genérico para casos que nao matcham nenhum pattern acima
FALLBACK_DATA = {
    'deadlines': [
        {
            'titulo': 'Prazo para Manifestação',
            'tipo': 'processual',
            'prioridade': 'alta',
            'status': 'pendente',
            'dias': 15,
            'descricao': 'Prazo para manifestação nos autos',
        },
        {
            'titulo': 'Audiência Designada',
            'tipo': 'processual',
            'prioridade': 'media',
            'status': 'pendente',
            'dias': 45,
            'descricao': 'Audiência designada pelo juízo',
        },
    ],
    'tasks': [
        {
            'titulo': 'Preparar documentação do caso',
            'descricao': 'Reunir e organizar toda a documentação relevante para instrução processual',
            'status': 'em_andamento',
            'prioridade': 'alta',
            'dias_limite': 10,
        },
        {
            'titulo': 'Revisar petição',
            'descricao': 'Revisar e atualizar a petição com base nos fatos e documentos reunidos',
            'status': 'pendente',
            'prioridade': 'media',
            'dias_limite': 12,
        },
    ],
    'audiencias': [],
    'financeiro': [
        {
            'tipo': 'custas',
            'descricao': 'Custas processuais',
            'valor': '400.00',
            'status': 'pago',
            'dias_vencimento': -5,
        },
        {
            'tipo': 'honorario',
            'descricao': 'Honorários advocatícios',
            'valor': '7000.00',
            'status': 'pendente',
            'dias_vencimento': 30,
        },
    ],
}


class Command(BaseCommand):
    help = 'Popula dados demo (prazos, tarefas, audiencias, financeiro) nos casos existentes'

    def handle(self, *args, **options):
        today = date.today()

        # Buscar usuario responsavel
        admin_user = (
            User.objects.filter(role='superadmin', is_active=True).first()
            or User.objects.filter(role='admin', is_active=True).first()
            or User.objects.filter(is_superuser=True, is_active=True).first()
        )
        if not admin_user:
            self.stderr.write(self.style.ERROR('Nenhum usuario admin encontrado. Abortando.'))
            return

        cases = LegalCase.objects.all()
        if not cases.exists():
            self.stderr.write(self.style.WARNING('Nenhum caso encontrado no banco.'))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Encontrados {cases.count()} casos. Populando dados demo...'
        ))

        total_deadlines = 0
        total_tasks = 0
        total_audiencias = 0
        total_financeiro = 0

        for case in cases:
            data = self._find_matching_data(case)

            # Prazos
            for dl in data.get('deadlines', []):
                _, created = LegalDeadline.objects.get_or_create(
                    caso=case,
                    titulo=dl['titulo'],
                    defaults={
                        'tipo': dl['tipo'],
                        'prioridade': dl['prioridade'],
                        'status': dl['status'],
                        'data_prazo': today + timedelta(days=dl['dias']),
                        'descricao': dl['descricao'],
                        'responsavel': admin_user,
                        'created_by': admin_user,
                    },
                )
                if created:
                    total_deadlines += 1

            # Tarefas
            for tk in data.get('tasks', []):
                defaults = {
                    'descricao': tk['descricao'],
                    'status': tk['status'],
                    'prioridade': tk['prioridade'],
                    'data_limite': today + timedelta(days=tk['dias_limite']),
                    'responsavel': admin_user,
                    'created_by': admin_user,
                }
                # Tarefas concluidas recebem data_conclusao
                if tk['status'] == 'concluida':
                    defaults['data_conclusao'] = today + timedelta(days=tk['dias_limite'])

                _, created = CaseTask.objects.get_or_create(
                    caso=case,
                    titulo=tk['titulo'],
                    defaults=defaults,
                )
                if created:
                    total_tasks += 1

            # Audiencias
            for aud in data.get('audiencias', []):
                aud_date = today + timedelta(days=aud['dias'])
                aud_datetime = timezone.make_aware(
                    datetime(aud_date.year, aud_date.month, aud_date.day, aud['hora'], 0)
                )
                _, created = Audiencia.objects.get_or_create(
                    caso=case,
                    tipo=aud['tipo'],
                    data_hora=aud_datetime,
                    defaults={
                        'status': aud['status'],
                        'local': aud['local'],
                        'juiz': aud.get('juiz', ''),
                    },
                )
                if created:
                    total_audiencias += 1

            # Movimentacoes Financeiras
            for fin in data.get('financeiro', []):
                venc = today + timedelta(days=fin['dias_vencimento'])
                defaults = {
                    'tipo': fin['tipo'],
                    'status': fin['status'],
                    'valor': fin['valor'],
                    'data_vencimento': venc,
                    'created_by': admin_user,
                }
                if fin['status'] == 'pago':
                    defaults['data_pagamento'] = venc

                _, created = MovimentacaoFinanceira.objects.get_or_create(
                    caso=case,
                    descricao=fin['descricao'],
                    defaults=defaults,
                )
                if created:
                    total_financeiro += 1

            self.stdout.write(f'  Caso: {case.titulo[:60]}... OK')

        self.stdout.write(self.style.SUCCESS(
            f'\nResumo: {total_deadlines} prazos, {total_tasks} tarefas, '
            f'{total_audiencias} audiencias, {total_financeiro} movimentacoes criados.'
        ))

    def _find_matching_data(self, case):
        """Encontra o bloco de dados mais adequado para o caso."""
        titulo = case.titulo or ''
        especialidade = case.especialidade or ''

        for entry in CASE_DATA:
            match_term = entry['match']
            if match_term.lower() in titulo.lower() or match_term.lower() in especialidade.lower():
                return entry

        # Fallback: tenta match por especialidade
        especialidade_map = {
            'trabalhista': 'Costa',
            'criminal': 'Silva',
            'consumidor': 'Oliveira',
            'tributario': 'Souza',
            'familia': 'Rodrigues',
            'previdenciario': 'Previdenciário',
            'imobiliario': 'Imóvel',
        }
        for esp, match_key in especialidade_map.items():
            if esp in especialidade.lower():
                for entry in CASE_DATA:
                    if entry['match'] == match_key:
                        return entry

        return FALLBACK_DATA
