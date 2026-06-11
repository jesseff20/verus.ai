"""
Management command para criar um ambiente demo COMPLETO de produção.

Cria usuários, clientes, casos, prazos, tarefas, audiências,
movimentações financeiras, leads CRM, timesheet, lembretes e notificações.

Uso: python manage.py seed_production_demo

Idempotente — usa get_or_create em todos os registros.
"""
from datetime import date, timedelta, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User, Notification, UserReminder, EmailTemplate
from apps.cases.models import (
    Client,
    LegalCase,
    LegalDeadline,
    CaseTask,
    Audiencia,
    MovimentacaoFinanceira,
    TimeEntry,
    LeadStage,
    Lead,
    LeadActivity,
    LegalContract,
    HonorariosDetail,
    ProcuracaoDetail,
    WorkflowTemplate,
    WorkflowExecution,
    RiskAssessment,
    CourtFeeGuide,
    ElectronicProtocol,
    DigitalSignature,
    SignatureVerification,
)
from apps.intelligent_assistant.models.knowledge_base import KnowledgeBase


# ═══════════════════════════════════════════════════════════════════
# 1. USUARIOS
# ═══════════════════════════════════════════════════════════════════

USERS_DATA = [
    {
        'username': 'usuario_demo',
        'email': 'usuario_demo@bravonix.anon',
        'first_name': 'Usuário',
        'last_name': 'Demonstração',
        'role': 'superadmin',
        'is_superuser': True,
        'is_staff': True,
        'password': 'Demonstração@@2026@@',
        'oab_number': '',
        'oab_state': '',
        'phone': '(11) 99999-0000',
    },
    {
        'username': 'joao.silva',
        'email': 'joao.silva@verus.ai',
        'first_name': 'João',
        'last_name': 'Silva',
        'role': 'procurador_geral',
        'is_superuser': False,
        'is_staff': True,
        'password': 'admin123',
        'oab_number': '',
        'oab_state': '',
        'phone': '(11) 98765-4321',
        'lawyer_specialties': ['Administrativo', 'Tributário', 'Licitações'],
    },
    {
        'username': 'maria.santos',
        'email': 'maria.santos@verus.ai',
        'first_name': 'Maria',
        'last_name': 'Santos',
        'role': 'procurador',
        'is_superuser': False,
        'is_staff': True,
        'password': 'admin123',
        'oab_number': '',
        'oab_state': '',
        'phone': '(11) 97654-3210',
        'lawyer_specialties': ['Dívida Ativa', 'Execução Fiscal', 'Tributário'],
    },
    {
        'username': 'pedro.lima',
        'email': 'pedro.lima@verus.ai',
        'first_name': 'Pedro',
        'last_name': 'Lima',
        'role': 'procurador',
        'is_superuser': False,
        'is_staff': True,
        'password': 'admin123',
        'oab_number': '',
        'oab_state': '',
        'phone': '(21) 96543-2109',
        'lawyer_specialties': ['Constitucional', 'Administrativo Disciplinar'],
    },
    {
        'username': 'ana.costa',
        'email': 'ana.costa@verus.ai',
        'first_name': 'Ana',
        'last_name': 'Costa',
        'role': 'estagiario',
        'is_superuser': False,
        'is_staff': False,
        'password': 'admin123',
        'oab_number': '',
        'oab_state': '',
        'phone': '(11) 95432-1098',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 2. PARTES / ENTES PÚBLICOS (demo — no contexto de Procuradoria,
#    "clientes" representam o próprio ente público ou partes de processos)
# ═══════════════════════════════════════════════════════════════════

CLIENTS_DATA = [
    # --- Ente Público / Parte Passiva demo ---
    {
        'name': 'Empresa XYZ Transportes LTDA',
        'client_type': 'pessoa_juridica',
        'cpf_cnpj': '341.628.597/0001-04',
        'rg': '',
        'email': 'juridico@xyztransportes.com.br',
        'phone': '(11) 99876-5432',
        'address': 'Av. Industrial, 123, Galpão 3',
        'city': 'São Paulo',
        'state': 'SP',
        'zipcode': '01234-567',
        'notes': 'Executada — Execução fiscal de ISS em dívida ativa. Débito inscrito em 2024.',
    },
    {
        'name': 'Construtora Panorama S.A.',
        'client_type': 'pessoa_juridica',
        'cpf_cnpj': '782.453.196/0001-80',
        'rg': '',
        'email': 'juridico@panoramaconstrutora.com.br',
        'phone': '(21) 98765-1234',
        'address': 'Rua dos Construtores, 456, Sala 10',
        'city': 'Rio de Janeiro',
        'state': 'RJ',
        'zipcode': '22010-000',
        'notes': 'Parte em processo administrativo — licitação irregular. Recurso em análise.',
    },
    {
        'name': 'Distribuidora BH Alimentos LTDA',
        'client_type': 'pessoa_juridica',
        'cpf_cnpj': '523.891.704/0001-62',
        'rg': '',
        'email': 'juridico@bhalimentos.com.br',
        'phone': '(31) 97654-3210',
        'address': 'Rua da Bahia, 789, Sala 301',
        'city': 'Belo Horizonte',
        'state': 'MG',
        'zipcode': '30160-011',
        'notes': 'Executada — Dívida ativa de ICMS com prazo de prescrição a verificar.',
    },
    {
        'name': 'Construtora Curitiba Obras LTDA',
        'client_type': 'pessoa_juridica',
        'cpf_cnpj': '196.745.832/0001-19',
        'rg': '',
        'email': 'juridico@curitibaobras.com.br',
        'phone': '(41) 96543-2109',
        'address': 'Rua XV de Novembro, 321',
        'city': 'Curitiba',
        'state': 'PR',
        'zipcode': '80020-310',
        'notes': 'Parte em PAD por irregularidade em contrato administrativo.',
    },
    {
        'name': 'Tech Solutions Brasil LTDA',
        'client_type': 'pessoa_juridica',
        'cpf_cnpj': '12.345.678/0001-90',
        'email': 'juridico@techsolutions.com.br',
        'phone': '(11) 3456-7890',
        'phone_secondary': '(11) 3456-7891',
        'address': 'Av. Paulista, 1000, 15o andar',
        'city': 'São Paulo',
        'state': 'SP',
        'zipcode': '01310-100',
        'company_name': 'Tech Solutions Brasil Serviços de TI LTDA',
        'contact_person': 'Roberto Almeida (Representante Legal)',
        'notes': 'Impetrou MS contra ato administrativo de licitação. Demanda em análise pela PGM.',
    },
    {
        'name': 'Marcos Antônio Pereira',
        'client_type': 'pessoa_fisica',
        'cpf_cnpj': '658.214.379-53',
        'rg': '67.890.123-8',
        'email': 'marcos.pereira@email.com',
        'phone': '(51) 95432-1098',
        'address': 'Av. Borges de Medeiros, 654',
        'city': 'Porto Alegre',
        'state': 'RS',
        'zipcode': '90020-025',
        'notes': 'Servidor público — indiciado em PAD. Processo em fase de defesa.',
    },
    {
        'name': 'Distribuidora Nacional de Alimentos LTDA',
        'client_type': 'pessoa_juridica',
        'cpf_cnpj': '45.678.901/0001-23',
        'email': 'juridico@distnacional.com.br',
        'phone': '(31) 3456-1234',
        'address': 'Rod. BR-040, KM 15, Galpão 3',
        'city': 'Contagem',
        'state': 'MG',
        'zipcode': '32010-050',
        'company_name': 'Distribuidora Nacional de Alimentos LTDA',
        'contact_person': 'Paulo Henrique (Representante Legal)',
        'notes': 'Contencioso tributário — ISS e ICMS em dívida ativa municipal.',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 3. CASOS (8 casos cobrindo diferentes especialidades)
# ═══════════════════════════════════════════════════════════════════

CASES_DATA = [
    # Caso 1 — Cível
    {
        'numero_processo': '1001234-56.2025.8.26.0100',
        'titulo': 'Ação de Indenização — Carlos Oliveira vs. TransLog Transportes',
        'especialidade': 'civel',
        'status': 'ativo',
        'fase': 'instrucao',
        'client_cpf': '341.628.597-04',
        'cliente_nome': 'Carlos Alberto de Oliveira',
        'cliente_cpf_cnpj': '341.628.597-04',
        'parte_contraria': 'TransLog Transportes LTDA',
        'parte_contraria_cpf_cnpj': '11.222.333/0001-44',
        'tribunal': 'TJSP',
        'vara_juizo': '7a Vara Cível do Foro Central',
        'comarca': 'São Paulo',
        'valor_causa': Decimal('250000.00'),
        'honorarios_combinados': Decimal('50000.00'),
        'advogado_username': 'joao.silva',
        'descricao': 'Ação de indenização por danos morais e materiais decorrentes de acidente de trânsito envolvendo veículo da empresa ré.',
    },
    # Caso 2 — Cível
    {
        'numero_processo': '1005678-90.2025.8.26.0100',
        'titulo': 'Ação de Cobrança — Tech Solutions vs. Inovação Digital',
        'especialidade': 'civel',
        'status': 'ativo',
        'fase': 'inicial',
        'client_cpf': '12.345.678/0001-90',
        'cliente_nome': 'Tech Solutions Brasil LTDA',
        'cliente_cpf_cnpj': '12.345.678/0001-90',
        'parte_contraria': 'Inovação Digital Sistemas LTDA',
        'parte_contraria_cpf_cnpj': '55.666.777/0001-88',
        'tribunal': 'TJSP',
        'vara_juizo': '12a Vara Cível do Foro Central',
        'comarca': 'São Paulo',
        'valor_causa': Decimal('180000.00'),
        'honorarios_combinados': Decimal('36000.00'),
        'advogado_username': 'joao.silva',
        'descricao': 'Cobrança de valores referentes a contrato de prestação de serviços de TI inadimplido.',
    },
    # Caso 3 — Trabalhista
    {
        'numero_processo': '0002345-67.2025.5.02.0045',
        'titulo': 'Reclamação Trabalhista — Fernanda Barbosa vs. ComércioMax',
        'especialidade': 'trabalhista',
        'status': 'ativo',
        'fase': 'instrucao',
        'client_cpf': '782.453.196-80',
        'cliente_nome': 'Fernanda Cristina Barbosa',
        'cliente_cpf_cnpj': '782.453.196-80',
        'parte_contraria': 'ComércioMax Varejo LTDA',
        'parte_contraria_cpf_cnpj': '22.333.444/0001-55',
        'tribunal': 'TRT-2',
        'vara_juizo': '45a Vara do Trabalho de São Paulo',
        'comarca': 'São Paulo',
        'valor_causa': Decimal('120000.00'),
        'honorarios_combinados': Decimal('24000.00'),
        'advogado_username': 'maria.santos',
        'descricao': 'Reclamação trabalhista por verbas rescisórias, horas extras, adicional noturno e danos morais por assédio.',
    },
    # Caso 4 — Família
    {
        'numero_processo': '0003456-78.2025.8.13.0024',
        'titulo': 'Divórcio Consensual — Roberto Mendes e Cláudia Souza',
        'especialidade': 'familia',
        'status': 'ativo',
        'fase': 'inicial',
        'client_cpf': '523.891.704-62',
        'cliente_nome': 'Roberto Mendes da Silva',
        'cliente_cpf_cnpj': '523.891.704-62',
        'parte_contraria': 'Cláudia Helena Souza Mendes',
        'parte_contraria_cpf_cnpj': '876.543.210-98',
        'tribunal': 'TJMG',
        'vara_juizo': '2a Vara de Família de Belo Horizonte',
        'comarca': 'Belo Horizonte',
        'valor_causa': Decimal('500000.00'),
        'honorarios_combinados': Decimal('15000.00'),
        'advogado_username': 'maria.santos',
        'descricao': 'Divórcio consensual com partilha de bens, guarda compartilhada de dois filhos menores e fixação de alimentos.',
    },
    # Caso 5 — Criminal
    {
        'numero_processo': '0004567-89.2025.8.16.0001',
        'titulo': 'Defesa Criminal — Luciana Gomes (Estelionato art. 171 CP)',
        'especialidade': 'criminal',
        'status': 'ativo',
        'fase': 'instrucao',
        'client_cpf': '196.745.832-19',
        'cliente_nome': 'Luciana Ferreira Gomes',
        'cliente_cpf_cnpj': '196.745.832-19',
        'parte_contraria': 'Ministério Público do Estado do Paraná',
        'parte_contraria_cpf_cnpj': '',
        'tribunal': 'TJPR',
        'vara_juizo': '3a Vara Criminal de Curitiba',
        'comarca': 'Curitiba',
        'valor_causa': None,
        'honorarios_combinados': Decimal('40000.00'),
        'advogado_username': 'pedro.lima',
        'descricao': 'Defesa em ação penal por suposta prática de estelionato. Ré primária, bons antecedentes.',
    },
    # Caso 6 — Tributário
    {
        'numero_processo': '0005678-90.2025.8.13.0024',
        'titulo': 'Mandado de Segurança Tributário — Dist. Nacional vs. Prefeitura Contagem',
        'especialidade': 'tributario',
        'status': 'ativo',
        'fase': 'recursal',
        'client_cpf': '45.678.901/0001-23',
        'cliente_nome': 'Distribuidora Nacional de Alimentos LTDA',
        'cliente_cpf_cnpj': '45.678.901/0001-23',
        'parte_contraria': 'Prefeitura Municipal de Contagem',
        'parte_contraria_cpf_cnpj': '',
        'tribunal': 'TJMG',
        'vara_juizo': '1a Vara da Fazenda Pública de Contagem',
        'comarca': 'Contagem',
        'valor_causa': Decimal('350000.00'),
        'honorarios_combinados': Decimal('70000.00'),
        'advogado_username': 'joao.silva',
        'descricao': 'Mandado de segurança contra cobrança de ISS sobre operações de industrialização por encomenda.',
    },
    # Caso 7 — Empresarial
    {
        'numero_processo': '1006789-01.2025.8.26.0100',
        'titulo': 'Dissolução Parcial de Sociedade — Tech Solutions',
        'especialidade': 'empresarial',
        'status': 'aguardando',
        'fase': 'inicial',
        'client_cpf': '12.345.678/0001-90',
        'cliente_nome': 'Tech Solutions Brasil LTDA',
        'cliente_cpf_cnpj': '12.345.678/0001-90',
        'parte_contraria': 'Sócio Minoritário — André Luiz Moreira',
        'parte_contraria_cpf_cnpj': '111.222.333-44',
        'tribunal': 'TJSP',
        'vara_juizo': '1a Vara Empresarial de São Paulo',
        'comarca': 'São Paulo',
        'valor_causa': Decimal('2000000.00'),
        'honorarios_combinados': Decimal('120000.00'),
        'advogado_username': 'joao.silva',
        'descricao': 'Dissolução parcial de sociedade com apuração de haveres do sócio minoritário retirante.',
    },
    # Caso 8 — Consumidor
    {
        'numero_processo': '0007890-12.2025.8.21.0001',
        'titulo': 'Ação de Consumidor — Marcos Pereira vs. TeleCom Brasil',
        'especialidade': 'consumidor',
        'status': 'ativo',
        'fase': 'julgamento',
        'client_cpf': '658.214.379-53',
        'cliente_nome': 'Marcos Antônio Pereira',
        'cliente_cpf_cnpj': '658.214.379-53',
        'parte_contraria': 'TeleCom Brasil Telecomunicações S.A.',
        'parte_contraria_cpf_cnpj': '33.444.555/0001-66',
        'tribunal': 'TJRS',
        'vara_juizo': '5o Juizado Especial Cível de Porto Alegre',
        'comarca': 'Porto Alegre',
        'valor_causa': Decimal('45000.00'),
        'honorarios_combinados': Decimal('13500.00'),
        'advogado_username': 'pedro.lima',
        'descricao': 'Ação por cobrança indevida de serviços não contratados, negativação indevida e danos morais.',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 4. PRAZOS (15 prazos)
# ═══════════════════════════════════════════════════════════════════

DEADLINES_DATA = [
    # Caso 1 — Cível (Indenização Carlos)
    {'case_idx': 0, 'titulo': 'Prazo para Réplica à Contestação', 'tipo': 'processual', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 5, 'descricao': 'Prazo fatal para apresentação de réplica à contestação da ré'},
    {'case_idx': 0, 'titulo': 'Audiência de Instrução e Julgamento', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 45, 'descricao': 'AIJ com oitiva de testemunhas'},
    # Caso 2 — Cível (Cobrança Tech Solutions)
    {'case_idx': 1, 'titulo': 'Prazo para Emenda à Inicial', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 10, 'descricao': 'Emenda à petição inicial conforme determinação do juízo'},
    # Caso 3 — Trabalhista
    {'case_idx': 2, 'titulo': 'Prazo para Contestação Trabalhista', 'tipo': 'processual', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 3, 'descricao': 'Prazo fatal para apresentação de defesa na reclamatória'},
    {'case_idx': 2, 'titulo': 'Juntada de Documentos Complementares', 'tipo': 'processual', 'prioridade': 'media', 'status': 'concluido', 'dias': -5, 'descricao': 'Juntada de holerites e comprovantes. Concluído.'},
    # Caso 4 — Família
    {'case_idx': 3, 'titulo': 'Prazo para Homologação do Acordo', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 15, 'descricao': 'Prazo para homologação do acordo de divórcio consensual'},
    {'case_idx': 3, 'titulo': 'Avaliação de Bens do Casal', 'tipo': 'extrajudicial', 'prioridade': 'media', 'status': 'em_andamento', 'dias': 25, 'descricao': 'Avaliação dos imóveis e veículos para partilha'},
    # Caso 5 — Criminal
    {'case_idx': 4, 'titulo': 'Resposta à Acusação (art. 396 CPP)', 'tipo': 'processual', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 8, 'descricao': 'Prazo para apresentação de resposta à acusação'},
    {'case_idx': 4, 'titulo': 'Alegações Finais por Memorial', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 60, 'descricao': 'Prazo para apresentação de memoriais / alegações finais'},
    # Caso 6 — Tributário
    {'case_idx': 5, 'titulo': 'Prazo para Recurso de Apelação', 'tipo': 'recursal', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 12, 'descricao': 'Prazo para interposição de apelação contra sentença desfavorável'},
    {'case_idx': 5, 'titulo': 'Juntada de Notas Fiscais', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'concluido', 'dias': -10, 'descricao': 'Juntada de NFs dos últimos 5 anos. Concluído.'},
    # Caso 7 — Empresarial
    {'case_idx': 6, 'titulo': 'Prazo para Contestação Empresarial', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 15, 'descricao': 'Contestação à ação de dissolução parcial'},
    {'case_idx': 6, 'titulo': 'Perícia Contábil de Haveres', 'tipo': 'processual', 'prioridade': 'media', 'status': 'pendente', 'dias': 90, 'descricao': 'Perícia contábil para apuração de haveres do sócio retirante'},
    # Caso 8 — Consumidor
    {'case_idx': 7, 'titulo': 'Prazo para Manifestação sobre Sentença', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'atrasado', 'dias': -2, 'descricao': 'Prazo para se manifestar sobre a sentença proferida'},
    {'case_idx': 7, 'titulo': 'Cumprimento de Sentença', 'tipo': 'processual', 'prioridade': 'media', 'status': 'pendente', 'dias': 30, 'descricao': 'Prazo para início do cumprimento de sentença'},
]


# ═══════════════════════════════════════════════════════════════════
# 5. TAREFAS (20 tarefas)
# ═══════════════════════════════════════════════════════════════════

TASKS_DATA = [
    # Caso 1
    {'case_idx': 0, 'titulo': 'Elaborar réplica à contestação', 'descricao': 'Redigir réplica detalhada rebatendo todos os pontos da contestação da empresa ré', 'status': 'em_andamento', 'prioridade': 'urgente', 'dias_limite': 4},
    {'case_idx': 0, 'titulo': 'Reunir documentação médica do autor', 'descricao': 'Coletar laudos médicos, receitas e comprovantes de despesas hospitalares', 'status': 'concluida', 'prioridade': 'alta', 'dias_limite': -3},
    {'case_idx': 0, 'titulo': 'Preparar rol de testemunhas', 'descricao': 'Listar e qualificar testemunhas presenciais do acidente', 'status': 'pendente', 'prioridade': 'media', 'dias_limite': 20},
    # Caso 2
    {'case_idx': 1, 'titulo': 'Revisar contrato de prestação de serviços', 'descricao': 'Analisar cláusulas do contrato de TI para fundamentar a cobrança', 'status': 'em_andamento', 'prioridade': 'alta', 'dias_limite': 7},
    {'case_idx': 1, 'titulo': 'Calcular valores atualizados com juros', 'descricao': 'Elaborar planilha de cálculo com juros moratórios e correção monetária', 'status': 'pendente', 'prioridade': 'media', 'dias_limite': 9},
    # Caso 3
    {'case_idx': 2, 'titulo': 'Calcular verbas rescisórias devidas', 'descricao': 'Planilha detalhada: saldo salário, férias, 13o, FGTS, aviso prévio', 'status': 'em_andamento', 'prioridade': 'alta', 'dias_limite': 5},
    {'case_idx': 2, 'titulo': 'Reunir holerites e CTPS', 'descricao': 'Solicitar ao cliente todos os holerites e cópia da CTPS', 'status': 'concluida', 'prioridade': 'urgente', 'dias_limite': -2},
    {'case_idx': 2, 'titulo': 'Pesquisar jurisprudência sobre assédio', 'descricao': 'Levantar precedentes do TST sobre assédio moral no trabalho', 'status': 'pendente', 'prioridade': 'media', 'dias_limite': 15},
    # Caso 4
    {'case_idx': 3, 'titulo': 'Inventariar bens do casal', 'descricao': 'Levantar todos os bens: imóveis, veículos, contas bancárias e investimentos', 'status': 'em_andamento', 'prioridade': 'alta', 'dias_limite': 10},
    {'case_idx': 3, 'titulo': 'Elaborar acordo de guarda compartilhada', 'descricao': 'Redigir termos de guarda, convivência e alimentos para os filhos', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 12},
    # Caso 5
    {'case_idx': 4, 'titulo': 'Organizar provas digitais', 'descricao': 'Coletar e autenticar prints de conversas, e-mails e registros bancários', 'status': 'em_andamento', 'prioridade': 'urgente', 'dias_limite': 6},
    {'case_idx': 4, 'titulo': 'Arrolar testemunhas de defesa', 'descricao': 'Identificar e arrolar até 8 testemunhas de defesa (art. 401 CPP)', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 7},
    {'case_idx': 4, 'titulo': 'Solicitar perícia em dispositivos', 'descricao': 'Requerer perícia técnica nos dispositivos eletrônicos apreendidos', 'status': 'pendente', 'prioridade': 'media', 'dias_limite': 15},
    # Caso 6
    {'case_idx': 5, 'titulo': 'Elaborar razões de apelação', 'descricao': 'Redigir peça recursal com fundamentos de fato e direito', 'status': 'em_andamento', 'prioridade': 'urgente', 'dias_limite': 10},
    {'case_idx': 5, 'titulo': 'Contratar perito contábil assistente', 'descricao': 'Indicar assistente técnico para acompanhar perícia judicial', 'status': 'concluida', 'prioridade': 'alta', 'dias_limite': -7},
    # Caso 7
    {'case_idx': 6, 'titulo': 'Analisar contrato social da empresa', 'descricao': 'Revisar contrato social e alterações para identificar direitos do sócio retirante', 'status': 'em_andamento', 'prioridade': 'alta', 'dias_limite': 12},
    {'case_idx': 6, 'titulo': 'Levantar balanços patrimoniais', 'descricao': 'Solicitar balanços dos últimos 5 anos para cálculo de haveres', 'status': 'pendente', 'prioridade': 'media', 'dias_limite': 20},
    # Caso 8
    {'case_idx': 7, 'titulo': 'Analisar sentença e viabilidade de recurso', 'descricao': 'Estudar a sentença proferida e avaliar oportunidade de recurso', 'status': 'concluida', 'prioridade': 'urgente', 'dias_limite': -1},
    {'case_idx': 7, 'titulo': 'Calcular valor atualizado da condenação', 'descricao': 'Elaborar cálculo de liquidação da sentença com juros e correção', 'status': 'em_andamento', 'prioridade': 'alta', 'dias_limite': 15},
    {'case_idx': 7, 'titulo': 'Requerer exclusão de negativação', 'descricao': 'Peticionar ao juízo para determinar exclusão do nome dos cadastros restritivos', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 5},
]


# ═══════════════════════════════════════════════════════════════════
# 6. AUDIÊNCIAS (5 audiências)
# ═══════════════════════════════════════════════════════════════════

AUDIENCIAS_DATA = [
    {'case_idx': 0, 'tipo': 'instrucao', 'status': 'agendada', 'dias': 45, 'hora': 14, 'local': '7a Vara Cível — Foro Central de São Paulo, Sala 305', 'juiz': 'Dr. Ricardo Moreira de Almeida'},
    {'case_idx': 2, 'tipo': 'conciliacao', 'status': 'agendada', 'dias': 20, 'hora': 9, 'local': '45a Vara do Trabalho de São Paulo, Sala 201', 'juiz': 'Dra. Patrícia Helena Costa'},
    {'case_idx': 3, 'tipo': 'conciliacao', 'status': 'realizada', 'dias': -10, 'hora': 15, 'local': '2a Vara de Família de Belo Horizonte, Sala 102', 'juiz': 'Dra. Camila de Souza Ferreira', 'resultado': 'Partes chegaram a acordo sobre partilha de bens. Guarda compartilhada acordada. Alimentos fixados em 30% dos rendimentos líquidos.'},
    {'case_idx': 4, 'tipo': 'instrucao', 'status': 'agendada', 'dias': 55, 'hora': 10, 'local': '3a Vara Criminal de Curitiba, Sala 401', 'juiz': 'Dr. Eduardo Nascimento Silva'},
    {'case_idx': 7, 'tipo': 'conciliacao', 'status': 'realizada', 'dias': -30, 'hora': 11, 'local': '5o Juizado Especial Cível de Porto Alegre', 'juiz': 'Dra. Mariana Lopes', 'resultado': 'Tentativa de conciliação frustrada. Réu não compareceu. Processo seguiu para julgamento.'},
]


# ═══════════════════════════════════════════════════════════════════
# 7. MOVIMENTAÇÕES FINANCEIRAS (10)
# ═══════════════════════════════════════════════════════════════════

FINANCEIRO_DATA = [
    {'case_idx': 0, 'tipo': 'custas', 'descricao': 'Custas processuais iniciais — Indenização', 'valor': '1250.00', 'status': 'pago', 'dias_vencimento': -15},
    {'case_idx': 0, 'tipo': 'honorario', 'descricao': 'Honorários advocatícios — parcela 1/3', 'valor': '16666.67', 'status': 'pago', 'dias_vencimento': -30},
    {'case_idx': 1, 'tipo': 'custas', 'descricao': 'Custas processuais — Cobrança', 'valor': '900.00', 'status': 'pago', 'dias_vencimento': -10},
    {'case_idx': 2, 'tipo': 'honorario', 'descricao': 'Honorários trabalhistas — entrada', 'valor': '8000.00', 'status': 'pendente', 'dias_vencimento': 15},
    {'case_idx': 3, 'tipo': 'honorario', 'descricao': 'Honorários — Divórcio consensual', 'valor': '15000.00', 'status': 'pendente', 'dias_vencimento': 30},
    {'case_idx': 4, 'tipo': 'despesa', 'descricao': 'Despesas com cópias e autenticações', 'valor': '450.00', 'status': 'pago', 'dias_vencimento': -5},
    {'case_idx': 5, 'tipo': 'custas', 'descricao': 'Custas — Mandado de Segurança', 'valor': '2500.00', 'status': 'pago', 'dias_vencimento': -20},
    {'case_idx': 5, 'tipo': 'honorario', 'descricao': 'Honorários tributários — fase recursal', 'valor': '35000.00', 'status': 'pendente', 'dias_vencimento': 45},
    {'case_idx': 6, 'tipo': 'custas', 'descricao': 'Custas — Dissolução societária', 'valor': '3500.00', 'status': 'pendente', 'dias_vencimento': 10},
    {'case_idx': 7, 'tipo': 'despesa', 'descricao': 'Despesas com certidões e buscas', 'valor': '280.00', 'status': 'pago', 'dias_vencimento': -8},
]


# ═══════════════════════════════════════════════════════════════════
# 8. LEADS CRM (6 etapas + 8 leads)
# ═══════════════════════════════════════════════════════════════════

LEAD_STAGES_DATA = [
    {'name': 'Novo Lead', 'order': 1, 'color': '#6B7280'},
    {'name': 'Consulta Agendada', 'order': 2, 'color': '#3B82F6'},
    {'name': 'Proposta Enviada', 'order': 3, 'color': '#F59E0B'},
    {'name': 'Negociação', 'order': 4, 'color': '#8B5CF6'},
    {'name': 'Cliente Ganho', 'order': 5, 'color': '#10B981', 'is_won': True},
    {'name': 'Perdido', 'order': 6, 'color': '#EF4444', 'is_lost': True},
]

LEADS_DATA = [
    {
        'name': 'Juliana Aparecida Rocha',
        'email': 'juliana.rocha@email.com',
        'phone': '(11) 98765-1111',
        'description': 'Precisa de advogado para reclamação trabalhista. Demissão sem justa causa com verbas em aberto.',
        'specialty': 'trabalhista',
        'source': 'indicacao',
        'temperature': 'hot',
        'stage_name': 'Consulta Agendada',
        'estimated_value': Decimal('60000.00'),
        'responsible_username': 'maria.santos',
    },
    {
        'name': 'Eduardo Campos Neto',
        'email': 'eduardo.campos@empresa.com',
        'phone': '(11) 91234-2222',
        'description': 'Consultoria tributária para planejamento fiscal de holding familiar.',
        'specialty': 'tributario',
        'source': 'google',
        'temperature': 'warm',
        'stage_name': 'Proposta Enviada',
        'estimated_value': Decimal('90000.00'),
        'responsible_username': 'joao.silva',
    },
    {
        'name': 'Patrícia Souza Lima',
        'email': 'patricia.lima@gmail.com',
        'phone': '(21) 99876-3333',
        'description': 'Inventário extrajudicial — espólio com 3 imóveis e aplicações financeiras.',
        'specialty': 'familia',
        'source': 'instagram',
        'temperature': 'warm',
        'stage_name': 'Novo Lead',
        'estimated_value': Decimal('25000.00'),
        'responsible_username': 'maria.santos',
    },
    {
        'name': 'Ricardo Teixeira Alves',
        'email': 'ricardo@alvesteixeira.com',
        'phone': '(31) 98888-4444',
        'description': 'Ação de despejo de imóvel comercial inadimplente há 6 meses.',
        'specialty': 'imobiliario',
        'source': 'site',
        'temperature': 'cold',
        'stage_name': 'Novo Lead',
        'estimated_value': Decimal('30000.00'),
        'responsible_username': 'pedro.lima',
    },
    {
        'name': 'Daniela Vieira Costa',
        'email': 'daniela.vieira@empresa.com',
        'phone': '(11) 97654-5555',
        'description': 'Defesa em ação de consumidor — recall de produto automotivo.',
        'specialty': 'consumidor',
        'source': 'whatsapp',
        'temperature': 'hot',
        'stage_name': 'Negociação',
        'estimated_value': Decimal('45000.00'),
        'responsible_username': 'pedro.lima',
    },
    {
        'name': 'Henrique Bastos Correia',
        'email': 'henrique.correia@outlook.com',
        'phone': '(41) 96543-6666',
        'description': 'Abertura de empresa — contrato social e registro na Junta Comercial.',
        'specialty': 'empresarial',
        'source': 'indicacao',
        'temperature': 'hot',
        'stage_name': 'Cliente Ganho',
        'estimated_value': Decimal('8000.00'),
        'responsible_username': 'joao.silva',
    },
    {
        'name': 'Camila Rodrigues Farias',
        'email': 'camila.farias@email.com',
        'phone': '(51) 95432-7777',
        'description': 'Processo de guarda unilateral contra ex-marido.',
        'specialty': 'familia',
        'source': 'telefone',
        'temperature': 'warm',
        'stage_name': 'Consulta Agendada',
        'estimated_value': Decimal('20000.00'),
        'responsible_username': 'maria.santos',
    },
    {
        'name': 'Bruno Martins Prado',
        'email': 'bruno.prado@hotmail.com',
        'phone': '(11) 94321-8888',
        'description': 'Consulta sobre revisão contratual de financiamento imobiliário.',
        'specialty': 'civel',
        'source': 'google',
        'temperature': 'cold',
        'stage_name': 'Perdido',
        'estimated_value': Decimal('15000.00'),
        'responsible_username': 'joao.silva',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 9. TIMESHEET (30 registros)
# ═══════════════════════════════════════════════════════════════════

TIMESHEET_ACTIVITIES = [
    'Análise de documentos e provas',
    'Elaboração de peça processual',
    'Pesquisa de jurisprudência',
    'Reunião com cliente',
    'Audiência judicial',
    'Despacho com juiz',
    'Revisão de contrato',
    'Elaboração de parecer jurídico',
    'Acompanhamento processual e diligências',
    'Protocolo de petição e conferência',
]


# ═══════════════════════════════════════════════════════════════════
# 10. LEMBRETES (5)
# ═══════════════════════════════════════════════════════════════════

REMINDERS_DATA = [
    {
        'title': 'Verificar publicações do DJE',
        'description': 'Consultar o Diário de Justiça Eletrônico para novas publicações dos processos ativos.',
        'frequency': 'daily',
        'dias': 1,
        'priority': 'high',
        'username': 'joao.silva',
    },
    {
        'title': 'Reunião semanal de equipe',
        'description': 'Reunião de alinhamento semanal com todos os advogados do escritório.',
        'frequency': 'weekly',
        'dias': 7,
        'priority': 'medium',
        'username': 'joao.silva',
    },
    {
        'title': 'Revisar prazos da semana — Trabalhista',
        'description': 'Conferir todos os prazos trabalhistas da próxima semana.',
        'frequency': 'weekly',
        'dias': 5,
        'priority': 'high',
        'username': 'maria.santos',
    },
    {
        'title': 'Acompanhar andamento processual criminal',
        'description': 'Consultar andamento do caso Luciana Gomes no TJPR.',
        'frequency': 'biweekly',
        'dias': 14,
        'priority': 'medium',
        'username': 'pedro.lima',
    },
    {
        'title': 'Entregar relatório mensal de horas',
        'description': 'Consolidar e entregar relatório de horas trabalhadas do mês ao sócio.',
        'frequency': 'monthly',
        'dias': 30,
        'priority': 'medium',
        'username': 'ana.costa',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 11. NOTIFICAÇÕES (10)
# ═══════════════════════════════════════════════════════════════════

NOTIFICATIONS_DATA = [
    {'username': 'joao.silva', 'type': 'deadline', 'priority': 'urgent', 'title': 'Prazo URGENTE: Réplica à Contestação', 'message': 'O prazo para réplica no caso Carlos Oliveira vs. TransLog vence em 5 dias. Ação necessária.', 'link': '/cases', 'is_read': False},
    {'username': 'joao.silva', 'type': 'case', 'priority': 'high', 'title': 'Novo caso atribuído: Dissolução Societária', 'message': 'Você foi designado como advogado responsável no caso de dissolução parcial da Tech Solutions.', 'link': '/cases', 'is_read': True},
    {'username': 'maria.santos', 'type': 'deadline', 'priority': 'urgent', 'title': 'Prazo URGENTE: Contestação Trabalhista', 'message': 'Prazo fatal para contestação no caso Fernanda Barbosa vs. ComércioMax vence em 3 dias.', 'link': '/cases', 'is_read': False},
    {'username': 'maria.santos', 'type': 'task', 'priority': 'medium', 'title': 'Tarefa concluída: Reunir holerites', 'message': 'A tarefa "Reunir holerites e CTPS" do caso trabalhista foi marcada como concluída.', 'link': '/cases', 'is_read': True},
    {'username': 'pedro.lima', 'type': 'case', 'priority': 'high', 'title': 'Audiência de instrução agendada', 'message': 'AIJ no caso Luciana Gomes (Criminal) agendada para daqui a 55 dias na 3a Vara Criminal de Curitiba.', 'link': '/cases', 'is_read': False},
    {'username': 'pedro.lima', 'type': 'document', 'priority': 'medium', 'title': 'Documento gerado: Resposta à Acusação', 'message': 'O documento "Resposta à Acusação" foi gerado pelo Copilot e está pronto para revisão.', 'link': '/documents', 'is_read': False},
    {'username': 'ana.costa', 'type': 'task', 'priority': 'medium', 'title': 'Nova tarefa atribuída', 'message': 'Você foi designada para a tarefa "Pesquisar jurisprudência sobre assédio" no caso trabalhista.', 'link': '/cases', 'is_read': False},
    {'username': 'joao.silva', 'type': 'case_update', 'priority': 'medium', 'title': 'Movimentação financeira registrada', 'message': 'Pagamento de custas processuais de R$ 2.500,00 registrado no caso tributário.', 'link': '/financeiro', 'is_read': True},
    {'username': 'maria.santos', 'type': 'case_update', 'priority': 'low', 'title': 'Lead convertido em cliente', 'message': 'O lead Henrique Bastos Correia foi convertido em cliente. Caso empresarial criado.', 'link': '/crm', 'is_read': True},
    {'username': 'joao.silva', 'type': 'deadline', 'priority': 'high', 'title': 'Prazo recursal se aproxima', 'message': 'O prazo para interposição de apelação no caso tributário vence em 12 dias.', 'link': '/cases', 'is_read': False},
]


# ═══════════════════════════════════════════════════════════════════
# 12. CONTRATOS (3)
# ═══════════════════════════════════════════════════════════════════

CONTRACTS_DATA = [
    {
        'case_idx': 0,
        'client_cpf': '341.628.597-04',
        'contract_type': 'honorarios',
        'title': 'Contrato de Honorários Advocatícios — Ação de Indenização Carlos Oliveira',
        'status': 'signed',
        'content_html': '<h1>Contrato de Honorários Advocatícios</h1><p>Pelo presente instrumento particular, de um lado <strong>Carlos Alberto de Oliveira</strong>, doravante denominado CONTRATANTE, e de outro <strong>Silva & Associados Advocacia</strong>, inscrito na OAB/SP sob nº 123.456, doravante denominado CONTRATADO...</p><p>Cláusula 1ª - DO OBJETO: O presente contrato tem por objeto a prestação de serviços advocatícios na Ação de Indenização por Danos Morais e Materiais...</p><p>Cláusula 2ª - DOS HONORÁRIOS: O valor dos honorários advocatícios fica estipulado em R$ 50.000,00 (cinquenta mil reais), a ser pago em 3 parcelas iguais...</p>',
        'honorarios_detail': {
            'fee_type': 'mixed',
            'fixed_amount': '50000.00',
            'success_percentage': '20.00',
            'payment_terms': 'Entrada de R$ 16.666,67 + 2 parcelas de R$ 16.666,67. Ad êxito de 20% sobre o valor obtido.',
            'installments': 3,
            'includes_expenses': False,
        },
    },
    {
        'case_idx': 2,
        'client_cpf': '782.453.196-80',
        'contract_type': 'procuracao',
        'title': 'Procuração Ad Judicia — Fernanda Cristina Barbosa',
        'status': 'pending_signature',
        'content_html': '<h1>Procuração Ad Judicia et Extra</h1><p>OUTORGANTE: <strong>Fernanda Cristina Barbosa</strong>, brasileira, solteira, CPF nº 782.453.196-80...</p><p>OUTORGADO: <strong>Dra. Maria Santos</strong>, OAB/SP nº 234.567...</p><p>PODERES: Para o foro em geral, com os poderes da cláusula "ad judicia et extra", podendo propor ações, contestar, recorrer, transigir, desistir, dar quitação...</p>',
        'procuracao_detail': {
            'powers_type': 'ad_judicia_extra',
            'special_powers': 'Poderes para transigir, desistir, reconhecer a procedência do pedido, receber e dar quitação, substabelecer com ou sem reserva de poderes.',
            'court_scope': 'Todas as instâncias do Poder Judiciário, Juizados Especiais e Tribunais Superiores',
        },
    },
    {
        'case_idx': 1,
        'client_cpf': '12.345.678/0001-90',
        'contract_type': 'prestacao_servicos',
        'title': 'Contrato de Prestação de Serviços Jurídicos — Assessoria Tech Solutions',
        'status': 'draft',
        'content_html': '<h1>Contrato de Prestação de Serviços Jurídicos</h1><p>CONTRATANTE: <strong>Tech Solutions Brasil Serviços de TI LTDA</strong>, CNPJ nº 12.345.678/0001-90...</p><p>CONTRATADO: <strong>Silva & Associados Advocacia</strong>...</p><p>Cláusula 1ª - Assessoria jurídica empresarial permanente, incluindo análise de contratos, consultoria trabalhista preventiva e contencioso cível...</p>',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 13. WORKFLOW TEMPLATES E EXECUÇÕES
# ═══════════════════════════════════════════════════════════════════

WORKFLOW_TEMPLATE_DATA = {
    'name': 'Ação Cível — Procedimento Comum',
    'description': 'Workflow padrão para ações cíveis de procedimento comum, desde a petição inicial até o trânsito em julgado.',
    'specialty': 'civel',
    'steps': [
        {'name': 'Petição Inicial', 'description': 'Elaboração e protocolo da petição inicial', 'order': 1, 'auto_advance': False, 'deadline_days': 10},
        {'name': 'Citação do Réu', 'description': 'Aguardar citação do réu pelo juízo', 'order': 2, 'auto_advance': False, 'deadline_days': 30},
        {'name': 'Contestação', 'description': 'Prazo para contestação da parte contrária', 'order': 3, 'auto_advance': False, 'deadline_days': 15},
        {'name': 'Réplica', 'description': 'Elaboração e protocolo da réplica', 'order': 4, 'auto_advance': False, 'deadline_days': 15},
        {'name': 'Saneamento', 'description': 'Decisão saneadora e fixação de pontos controvertidos', 'order': 5, 'auto_advance': False, 'deadline_days': 30},
        {'name': 'Instrução Probatória', 'description': 'Produção de provas: documental, testemunhal e pericial', 'order': 6, 'auto_advance': False, 'deadline_days': 60},
        {'name': 'Alegações Finais', 'description': 'Apresentação de alegações finais ou memoriais', 'order': 7, 'auto_advance': False, 'deadline_days': 15},
        {'name': 'Sentença', 'description': 'Aguardar sentença do juízo', 'order': 8, 'auto_advance': False, 'deadline_days': 30},
    ],
}


# ═══════════════════════════════════════════════════════════════════
# 14. AVALIAÇÕES DE RISCO
# ═══════════════════════════════════════════════════════════════════

RISK_ASSESSMENTS_DATA = [
    # Caso 0 — Cível (Carlos Oliveira) — 2 avaliações mostrando evolução
    {
        'case_idx': 0,
        'risk_level': 'high',
        'risk_score': 75,
        'factors': [
            {'name': 'Complexidade processual', 'weight': 0.3, 'description': 'Necessidade de prova pericial e múltiplas testemunhas'},
            {'name': 'Valor da causa elevado', 'weight': 0.25, 'description': 'R$ 250.000,00 — risco financeiro significativo'},
            {'name': 'Jurisprudência desfavorável', 'weight': 0.2, 'description': 'Tribunal tem sido restritivo em indenizações de trânsito'},
        ],
        'analysis': 'Caso apresenta risco alto inicial. A parte contrária é empresa de grande porte com departamento jurídico próprio. A jurisprudência do TJSP para acidentes de trânsito com veículos de empresa tem variado. Recomenda-se reforço na produção probatória.',
        'recommendation': 'Intensificar coleta de provas documentais e testemunhais. Considerar proposta de acordo se o valor for razoável.',
        'trigger': 'inicio_caso',
        'previous_level': '',
        'level_changed': False,
        'ai_generated': True,
        'ai_model': 'claude-3-5-sonnet',
        'tokens_used': 1250,
        'days_ago': 45,
    },
    {
        'case_idx': 0,
        'risk_level': 'medium',
        'risk_score': 55,
        'factors': [
            {'name': 'Prova pericial favorável', 'weight': 0.3, 'description': 'Laudo pericial confirmou nexo causal do acidente'},
            {'name': 'Testemunha ocular confirmada', 'weight': 0.25, 'description': 'Testemunha presencial do acidente confirmada'},
            {'name': 'Valor da causa elevado', 'weight': 0.2, 'description': 'R$ 250.000,00 — risco financeiro persiste'},
        ],
        'analysis': 'Após produção de prova pericial favorável e confirmação de testemunha ocular, o risco reduziu de alto para médio. O laudo pericial é elemento forte. A contestação da ré apresentou argumentos frágeis sobre culpa exclusiva da vítima.',
        'recommendation': 'Manter a estratégia atual. Preparar testemunha para AIJ. Avaliar possibilidade de acordo com base no laudo favorável.',
        'trigger': 'nova_prova',
        'previous_level': 'high',
        'level_changed': True,
        'ai_generated': False,
        'ai_model': '',
        'tokens_used': 0,
        'days_ago': 10,
    },
    # Caso 4 — Criminal (Luciana Gomes) — 2 avaliações
    {
        'case_idx': 4,
        'risk_level': 'high',
        'risk_score': 70,
        'factors': [
            {'name': 'Provas documentais contra a ré', 'weight': 0.35, 'description': 'Registros bancários e conversas em aplicativo'},
            {'name': 'Tipo penal grave', 'weight': 0.25, 'description': 'Estelionato (art. 171 CP) — pena de 1 a 5 anos'},
            {'name': 'Réu primário', 'weight': -0.2, 'description': 'Fator atenuante — ré primária e bons antecedentes'},
        ],
        'analysis': 'Apesar de ré primária, as provas documentais são robustas. O Ministério Público apresentou registros bancários que indicam transferências suspeitas. Necessário contestar a autenticidade das provas digitais.',
        'recommendation': 'Requerer perícia nos dispositivos eletrônicos. Preparar tese de insuficiência probatória. Avaliar possibilidade de acordo de não persecução penal.',
        'trigger': 'inicio_caso',
        'previous_level': '',
        'level_changed': False,
        'ai_generated': True,
        'ai_model': 'claude-3-5-sonnet',
        'tokens_used': 980,
        'days_ago': 40,
    },
    {
        'case_idx': 4,
        'risk_level': 'medium',
        'risk_score': 50,
        'factors': [
            {'name': 'Perícia contestou provas', 'weight': 0.3, 'description': 'Perito identificou inconsistências nos registros digitais'},
            {'name': 'Testemunha de defesa forte', 'weight': 0.25, 'description': 'Testemunha confirma álibi em parte do período'},
            {'name': 'Réu primário', 'weight': -0.2, 'description': 'Fator atenuante mantido'},
        ],
        'analysis': 'A perícia técnica identificou possíveis adulterações nos prints apresentados pelo MP. Uma testemunha de defesa confirmou a presença da ré em outro local durante parte do período apontado. Risco reduzido substancialmente.',
        'recommendation': 'Reforçar tese de insuficiência probatória nas alegações finais. Requerer absolvição por falta de provas (art. 386, VII, CPP).',
        'trigger': 'resultado_pericia',
        'previous_level': 'high',
        'level_changed': True,
        'ai_generated': False,
        'ai_model': '',
        'tokens_used': 0,
        'days_ago': 5,
    },
]


# ═══════════════════════════════════════════════════════════════════
# 15. GUIAS DE CUSTAS JUDICIAIS
# ═══════════════════════════════════════════════════════════════════

COURT_FEES_DATA = [
    {
        'case_idx': 0,
        'fee_type': 'custas_iniciais',
        'court': 'TJSP',
        'state': 'SP',
        'calculated_amount': '3127.50',
        'case_value': '250000.00',
        'calculation_formula': '1% sobre o valor da causa (mínimo R$ 100,00, máximo R$ 3.127,50)',
        'due_date_days': -20,
        'payment_status': 'paid',
        'barcode': '23793.38128 60000.000003 00000.000405 1 84340000312750',
        'notes': 'Guia DARE-SP recolhida. Comprovante juntado aos autos.',
    },
    {
        'case_idx': 5,
        'fee_type': 'custas_recursais',
        'court': 'TJMG',
        'state': 'MG',
        'calculated_amount': '4575.00',
        'case_value': '350000.00',
        'calculation_formula': 'Preparo recursal: 1% sobre o valor atualizado da causa + porte de remessa e retorno',
        'due_date_days': 10,
        'payment_status': 'pending',
        'barcode': '23793.38128 60000.000003 00000.000406 1 95670000457500',
        'notes': 'Guia para preparo do recurso de apelação. Prazo fatal em 10 dias.',
    },
    {
        'case_idx': 2,
        'fee_type': 'pericia',
        'court': 'TRT-2',
        'state': 'SP',
        'calculated_amount': '2800.00',
        'case_value': '120000.00',
        'calculation_formula': 'Honorários periciais fixados pelo juízo — perícia contábil',
        'due_date_days': -3,
        'payment_status': 'overdue',
        'barcode': '23793.38128 60000.000003 00000.000407 1 86780000280000',
        'notes': 'ATENÇÃO: Guia vencida há 3 dias. Risco de preclusão da prova pericial. Entrar em contato com o cliente urgentemente.',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 16. PROTOCOLOS ELETRÔNICOS
# ═══════════════════════════════════════════════════════════════════

PROTOCOLS_DATA = [
    {
        'case_idx': 0,
        'protocol_number': 'ESAJ-2025-0045678',
        'court_system': 'esaj',
        'status': 'accepted',
        'petition_type': 'Réplica à Contestação',
        'protocol_receipt': 'Protocolo recebido pelo sistema e-SAJ em 15/05/2025 às 14:32:15. Número de protocolo: ESAJ-2025-0045678. Prazo atendido.',
    },
    {
        'case_idx': 5,
        'protocol_number': '',
        'court_system': 'projudi',
        'status': 'pending',
        'petition_type': 'Recurso de Apelação',
        'protocol_receipt': '',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 17. ASSINATURAS DIGITAIS
# ═══════════════════════════════════════════════════════════════════

DIGITAL_SIGNATURES_DATA = [
    {
        'user_username': 'joao.silva',
        'contract_idx': 0,  # Contrato de honorários (signed)
        'signature_type': 'qualified',
        'signature_hash': 'a3f2b8c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1',
        'ip_address': '187.32.45.128',
        'is_valid': True,
        'verification_url': 'https://verificador.iti.gov.br/verifier/verify/a3f2b8c1',
        'certificate_info': {
            'subject': 'JOAO SILVA:12345678900',
            'issuer': 'AC SERASA RFB v5',
            'serial_number': '11:22:33:44:55:66:77:88',
            'valid_from': '2024-01-15',
            'valid_until': '2027-01-15',
            'key_usage': 'Digital Signature, Non Repudiation',
        },
        'verified': True,
    },
    {
        'user_username': 'maria.santos',
        'contract_idx': 1,  # Procuração (pending_signature)
        'signature_type': 'advanced',
        'signature_hash': 'b4c3d9e2f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2',
        'ip_address': '200.168.92.55',
        'is_valid': True,
        'verification_url': '',
        'certificate_info': None,
        'verified': False,  # Pending verification
    },
]


# ═══════════════════════════════════════════════════════════════════
# 18. TEMPLATES DE E-MAIL
# ═══════════════════════════════════════════════════════════════════

EMAIL_TEMPLATES_DATA = [
    {
        'name': 'Boas-vindas ao Cliente',
        'subject': 'Bem-vindo(a) ao escritório Silva & Associados — {{nome_cliente}}',
        'category': 'client',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Prezado(a) {{nome_cliente}},</h2>
<p>É com satisfação que informamos que seu cadastro em nosso escritório foi concluído com sucesso.</p>
<p>Seu advogado responsável será <strong>{{nome_advogado}}</strong>, OAB/{{estado_oab}} nº {{numero_oab}}.</p>
<p>Caso já possua um processo em andamento, o número é: <strong>{{numero_processo}}</strong>.</p>
<p>Para acessar o portal do cliente e acompanhar seu caso, utilize o link abaixo:</p>
<p><a href="{{link_portal}}" style="background-color: #2563EB; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Acessar Portal do Cliente</a></p>
<p>Em caso de dúvidas, estamos à disposição pelo telefone {{telefone_escritorio}} ou e-mail {{email_escritorio}}.</p>
<p>Atenciosamente,<br>Equipe Silva & Associados</p>
</div>''',
        'variables': [
            {'name': 'nome_cliente', 'description': 'Nome completo do cliente'},
            {'name': 'nome_advogado', 'description': 'Nome do advogado responsável'},
            {'name': 'estado_oab', 'description': 'Estado da OAB do advogado'},
            {'name': 'numero_oab', 'description': 'Número da OAB do advogado'},
            {'name': 'numero_processo', 'description': 'Número do processo (se houver)'},
            {'name': 'link_portal', 'description': 'Link para o portal do cliente'},
            {'name': 'telefone_escritorio', 'description': 'Telefone do escritório'},
            {'name': 'email_escritorio', 'description': 'E-mail do escritório'},
        ],
    },
    {
        'name': 'Lembrete de Prazo Judicial',
        'subject': 'URGENTE: Prazo judicial se aproxima — {{titulo_prazo}}',
        'category': 'deadline',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px; margin-bottom: 20px;">
<strong>⚠ ATENÇÃO: Prazo judicial próximo do vencimento</strong>
</div>
<p>Prezado(a) {{nome_advogado}},</p>
<p>Informamos que o prazo abaixo vencerá em breve:</p>
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Caso:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{titulo_caso}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Processo:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{numero_processo}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Prazo:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{titulo_prazo}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Vencimento:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB; color: #DC2626;"><strong>{{data_vencimento}}</strong></td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Dias restantes:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{dias_restantes}}</td></tr>
</table>
<p>Acesse o sistema para mais detalhes e providências necessárias.</p>
</div>''',
        'variables': [
            {'name': 'nome_advogado', 'description': 'Nome do advogado responsável'},
            {'name': 'titulo_caso', 'description': 'Título do caso'},
            {'name': 'numero_processo', 'description': 'Número do processo'},
            {'name': 'titulo_prazo', 'description': 'Título/descrição do prazo'},
            {'name': 'data_vencimento', 'description': 'Data de vencimento do prazo'},
            {'name': 'dias_restantes', 'description': 'Quantidade de dias restantes'},
        ],
    },
    {
        'name': 'Audiência Agendada',
        'subject': 'Audiência agendada — {{tipo_audiencia}} — {{titulo_caso}}',
        'category': 'notification',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Audiência Agendada</h2>
<p>Prezado(a) {{nome_cliente}},</p>
<p>Informamos que foi agendada uma audiência de <strong>{{tipo_audiencia}}</strong> no seu processo:</p>
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Processo:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{numero_processo}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Data/Hora:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{data_hora_audiencia}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Local:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{local_audiencia}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Juiz(a):</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{nome_juiz}}</td></tr>
</table>
<p><strong>Orientações importantes:</strong></p>
<ul>
<li>Compareça ao local com pelo menos 15 minutos de antecedência</li>
<li>Leve documento de identidade com foto (RG ou CNH)</li>
<li>Vista-se de forma adequada para o ambiente forense</li>
</ul>
<p>Seu advogado {{nome_advogado}} estará presente e entrará em contato para orientações adicionais.</p>
</div>''',
        'variables': [
            {'name': 'nome_cliente', 'description': 'Nome do cliente'},
            {'name': 'tipo_audiencia', 'description': 'Tipo de audiência (conciliação, instrução, etc.)'},
            {'name': 'numero_processo', 'description': 'Número do processo'},
            {'name': 'data_hora_audiencia', 'description': 'Data e hora da audiência'},
            {'name': 'local_audiencia', 'description': 'Local da audiência'},
            {'name': 'nome_juiz', 'description': 'Nome do juiz'},
            {'name': 'nome_advogado', 'description': 'Nome do advogado'},
        ],
    },
    {
        'name': 'Documento Pronto para Revisão',
        'subject': 'Documento pronto: {{nome_documento}} — {{titulo_caso}}',
        'category': 'notification',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Documento Disponível para Revisão</h2>
<p>Prezado(a) {{nome_advogado}},</p>
<p>O documento <strong>{{nome_documento}}</strong> referente ao caso <strong>{{titulo_caso}}</strong> (Processo nº {{numero_processo}}) foi gerado e está pronto para sua revisão.</p>
<p><strong>Detalhes:</strong></p>
<ul>
<li>Tipo: {{tipo_documento}}</li>
<li>Gerado por: {{gerado_por}}</li>
<li>Data de geração: {{data_geracao}}</li>
</ul>
<p><a href="{{link_documento}}" style="background-color: #2563EB; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Revisar Documento</a></p>
<p>Após revisão, favor aprovar ou solicitar ajustes pelo sistema.</p>
</div>''',
        'variables': [
            {'name': 'nome_advogado', 'description': 'Nome do advogado'},
            {'name': 'nome_documento', 'description': 'Nome do documento'},
            {'name': 'titulo_caso', 'description': 'Título do caso'},
            {'name': 'numero_processo', 'description': 'Número do processo'},
            {'name': 'tipo_documento', 'description': 'Tipo do documento'},
            {'name': 'gerado_por', 'description': 'Quem gerou (Copilot, advogado, etc.)'},
            {'name': 'data_geracao', 'description': 'Data de geração'},
            {'name': 'link_documento', 'description': 'Link para o documento'},
        ],
    },
    {
        'name': 'Fatura / Cobrança de Honorários',
        'subject': 'Fatura nº {{numero_fatura}} — Honorários Advocatícios',
        'category': 'billing',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Fatura de Honorários Advocatícios</h2>
<p>Prezado(a) {{nome_cliente}},</p>
<p>Segue abaixo os detalhes da fatura referente aos serviços jurídicos prestados:</p>
<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
<tr style="background-color: #F3F4F6;"><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Fatura nº</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB;">{{numero_fatura}}</td></tr>
<tr><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Referência</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB;">{{referencia}}</td></tr>
<tr style="background-color: #F3F4F6;"><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Valor</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB; font-size: 18px; color: #059669;"><strong>R$ {{valor}}</strong></td></tr>
<tr><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Vencimento</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB;">{{data_vencimento}}</td></tr>
</table>
<p>O pagamento pode ser realizado via:</p>
<ul>
<li>PIX: {{chave_pix}}</li>
<li>Boleto bancário (em anexo)</li>
<li>Transferência bancária: {{dados_bancarios}}</li>
</ul>
<p>Em caso de dúvidas sobre esta fatura, entre em contato com nosso departamento financeiro.</p>
</div>''',
        'variables': [
            {'name': 'nome_cliente', 'description': 'Nome do cliente'},
            {'name': 'numero_fatura', 'description': 'Número da fatura'},
            {'name': 'referencia', 'description': 'Mês/ano ou descrição de referência'},
            {'name': 'valor', 'description': 'Valor da fatura'},
            {'name': 'data_vencimento', 'description': 'Data de vencimento'},
            {'name': 'chave_pix', 'description': 'Chave PIX do escritório'},
            {'name': 'dados_bancarios', 'description': 'Dados bancários para transferência'},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════
# 19. KNOWLEDGE BASE (2 documentos)
# ═══════════════════════════════════════════════════════════════════

KB_DATA = [
    {
        'name': 'Legislação Civil Brasileira',
        'description': 'Base de conhecimento contendo os principais artigos do Código Civil, Código de Processo Civil e legislação complementar relevante para o contencioso cível.',
        'kb_layer': 'global',
    },
    {
        'name': 'Jurisprudência Trabalhista — TST',
        'description': 'Compilação de súmulas, orientações jurisprudenciais e decisões relevantes do Tribunal Superior do Trabalho sobre temas como verbas rescisórias, horas extras, assédio moral e estabilidades.',
        'kb_layer': 'global',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 20. NOTIFICAÇÕES ADICIONAIS (mix de tipos)
# ═══════════════════════════════════════════════════════════════════

EXTRA_NOTIFICATIONS_DATA = [
    {'username': 'joao.silva', 'type': 'contract', 'priority': 'high', 'title': 'Contrato aguardando assinatura', 'message': 'A procuração da cliente Fernanda Barbosa está aguardando assinatura. Por favor, encaminhe para assinatura digital.', 'link': '/contratos', 'is_read': False},
    {'username': 'maria.santos', 'type': 'compliance', 'priority': 'medium', 'title': 'Verificação LGPD pendente', 'message': 'O caso trabalhista de Fernanda Barbosa contém dados sensíveis que precisam de revisão de conformidade LGPD.', 'link': '/compliance', 'is_read': False},
    {'username': 'pedro.lima', 'type': 'system', 'priority': 'low', 'title': 'Backup semanal concluído', 'message': 'O backup semanal dos documentos do escritório foi concluído com sucesso. 1.247 arquivos processados.', 'link': '', 'is_read': True},
    {'username': 'joao.silva', 'type': 'simulation', 'priority': 'medium', 'title': 'Simulação de risco atualizada', 'message': 'A avaliação de risco do caso Carlos Oliveira foi atualizada: risco reduziu de Alto para Médio após produção de prova pericial favorável.', 'link': '/risk', 'is_read': False},
    {'username': 'ana.costa', 'type': 'message', 'priority': 'high', 'title': 'Nova mensagem do portal do cliente', 'message': 'O cliente Carlos Oliveira enviou uma mensagem pelo portal do cliente solicitando atualização sobre o andamento do processo.', 'link': '/messages', 'is_read': False},
]


class Command(BaseCommand):
    help = 'Cria um ambiente demo COMPLETO de produção para o Verus.AI'

    def handle(self, *args, **options):
        today = date.today()
        now = timezone.now()

        # ─── 1. USUARIOS ───
        self.stdout.write(self.style.MIGRATE_HEADING('1. Criando usuários...'))
        users = {}
        for u_data in USERS_DATA:
            password = u_data.pop('password')
            lawyer_specialties = u_data.pop('lawyer_specialties', [])
            username = u_data['username']

            user, created = User.objects.get_or_create(
                username=username,
                defaults=u_data,
            )
            if created:
                user.set_password(password)
                if lawyer_specialties:
                    user.lawyer_specialties = lawyer_specialties
                user.save()
                self.stdout.write(f'  + Criado: {user.email} ({user.role})')
            else:
                self.stdout.write(f'  = Existe: {user.email}')

            # Restore popped keys for idempotency on re-run
            u_data['password'] = password
            u_data['lawyer_specialties'] = lawyer_specialties
            users[username] = user

        admin_user = users.get('usuario_demo') or users.get('joao.silva')

        # ─── 2. CLIENTES ───
        self.stdout.write(self.style.MIGRATE_HEADING('2. Criando clientes...'))
        clients = {}
        for c_data in CLIENTS_DATA:
            cpf = c_data['cpf_cnpj']
            defaults = {**c_data}
            defaults['responsible_lawyer'] = users.get('joao.silva', admin_user)
            defaults['created_by'] = admin_user

            client, created = Client.objects.get_or_create(
                cpf_cnpj=cpf,
                defaults=defaults,
            )
            clients[cpf] = client
            status = '+' if created else '='
            self.stdout.write(f'  {status} {client.name}')

        # ─── 3. CASOS ───
        self.stdout.write(self.style.MIGRATE_HEADING('3. Criando casos...'))
        cases = []
        for case_data in CASES_DATA:
            client_cpf = case_data.pop('client_cpf')
            advogado_username = case_data.pop('advogado_username')

            client_obj = clients.get(client_cpf)
            advogado_obj = users.get(advogado_username, admin_user)

            defaults = {**case_data}
            defaults['client'] = client_obj
            defaults['advogado_responsavel'] = advogado_obj
            defaults['created_by'] = admin_user
            defaults['data_distribuicao'] = today - timedelta(days=60)

            case, created = LegalCase.objects.get_or_create(
                numero_processo=case_data['numero_processo'],
                defaults=defaults,
            )
            cases.append(case)

            # Restore popped keys
            case_data['client_cpf'] = client_cpf
            case_data['advogado_username'] = advogado_username

            status = '+' if created else '='
            self.stdout.write(f'  {status} {case.titulo[:70]}')

        # ─── 4. PRAZOS ───
        self.stdout.write(self.style.MIGRATE_HEADING('4. Criando prazos...'))
        total_deadlines = 0
        for dl in DEADLINES_DATA:
            caso = cases[dl['case_idx']]
            data_prazo = today + timedelta(days=dl['dias'])
            defaults = {
                'tipo': dl['tipo'],
                'prioridade': dl['prioridade'],
                'status': dl['status'],
                'data_prazo': data_prazo,
                'descricao': dl['descricao'],
                'responsavel': caso.advogado_responsavel,
                'created_by': admin_user,
            }
            if dl['status'] == 'concluido':
                defaults['data_conclusao'] = data_prazo

            _, created = LegalDeadline.objects.get_or_create(
                caso=caso,
                titulo=dl['titulo'],
                defaults=defaults,
            )
            if created:
                total_deadlines += 1
        self.stdout.write(f'  {total_deadlines} prazos criados')

        # ─── 5. TAREFAS ───
        self.stdout.write(self.style.MIGRATE_HEADING('5. Criando tarefas...'))
        total_tasks = 0
        for tk in TASKS_DATA:
            caso = cases[tk['case_idx']]
            data_limite = today + timedelta(days=tk['dias_limite'])
            defaults = {
                'descricao': tk['descricao'],
                'status': tk['status'],
                'prioridade': tk['prioridade'],
                'data_limite': data_limite,
                'responsavel': caso.advogado_responsavel,
                'created_by': admin_user,
            }
            if tk['status'] == 'concluida':
                defaults['data_conclusao'] = data_limite

            _, created = CaseTask.objects.get_or_create(
                caso=caso,
                titulo=tk['titulo'],
                defaults=defaults,
            )
            if created:
                total_tasks += 1
        self.stdout.write(f'  {total_tasks} tarefas criadas')

        # ─── 6. AUDIÊNCIAS ───
        self.stdout.write(self.style.MIGRATE_HEADING('6. Criando audiências...'))
        total_aud = 0
        for aud in AUDIENCIAS_DATA:
            caso = cases[aud['case_idx']]
            aud_date = today + timedelta(days=aud['dias'])
            aud_datetime = timezone.make_aware(
                datetime(aud_date.year, aud_date.month, aud_date.day, aud['hora'], 0)
            )
            defaults = {
                'status': aud['status'],
                'local': aud['local'],
                'juiz': aud.get('juiz', ''),
                'resultado': aud.get('resultado', ''),
            }

            _, created = Audiencia.objects.get_or_create(
                caso=caso,
                tipo=aud['tipo'],
                data_hora=aud_datetime,
                defaults=defaults,
            )
            if created:
                total_aud += 1
        self.stdout.write(f'  {total_aud} audiências criadas')

        # ─── 7. FINANCEIRO ───
        self.stdout.write(self.style.MIGRATE_HEADING('7. Criando movimentações financeiras...'))
        total_fin = 0
        for fin in FINANCEIRO_DATA:
            caso = cases[fin['case_idx']]
            venc = today + timedelta(days=fin['dias_vencimento'])
            defaults = {
                'tipo': fin['tipo'],
                'status': fin['status'],
                'valor': Decimal(fin['valor']),
                'data_vencimento': venc,
                'created_by': admin_user,
            }
            if fin['status'] == 'pago':
                defaults['data_pagamento'] = venc

            _, created = MovimentacaoFinanceira.objects.get_or_create(
                caso=caso,
                descricao=fin['descricao'],
                defaults=defaults,
            )
            if created:
                total_fin += 1
        self.stdout.write(f'  {total_fin} movimentações criadas')

        # ─── 8. CRM LEADS ───
        self.stdout.write(self.style.MIGRATE_HEADING('8. Criando pipeline CRM...'))

        # Stages
        stages = {}
        for s_data in LEAD_STAGES_DATA:
            stage, _ = LeadStage.objects.get_or_create(
                name=s_data['name'],
                defaults={k: v for k, v in s_data.items() if k != 'name'},
            )
            stages[s_data['name']] = stage
        self.stdout.write(f'  {len(stages)} etapas do funil')

        # Leads
        total_leads = 0
        for ld in LEADS_DATA:
            stage = stages.get(ld['stage_name'])
            responsible = users.get(ld['responsible_username'], admin_user)

            lead, created = Lead.objects.get_or_create(
                name=ld['name'],
                defaults={
                    'email': ld['email'],
                    'phone': ld['phone'],
                    'description': ld['description'],
                    'specialty': ld['specialty'],
                    'source': ld['source'],
                    'temperature': ld['temperature'],
                    'stage': stage,
                    'estimated_value': ld['estimated_value'],
                    'responsible': responsible,
                    'created_by': admin_user,
                },
            )
            if created:
                total_leads += 1
                LeadActivity.objects.create(
                    lead=lead,
                    activity_type='note',
                    description=f'Lead cadastrado via {lead.get_source_display()}',
                    created_by=admin_user,
                )
        self.stdout.write(f'  {total_leads} leads criados')

        # ─── 9. TIMESHEET ───
        self.stdout.write(self.style.MIGRATE_HEADING('9. Criando registros de timesheet...'))
        total_time = 0
        lawyer_users = [
            users.get('joao.silva'),
            users.get('maria.santos'),
            users.get('pedro.lima'),
        ]
        lawyer_users = [u for u in lawyer_users if u is not None]
        hourly_rates = {
            'joao.silva': Decimal('350.00'),
            'maria.santos': Decimal('300.00'),
            'pedro.lima': Decimal('250.00'),
        }

        for day_offset in range(30):
            d = today - timedelta(days=day_offset)
            if d.weekday() >= 5:  # Skip weekends
                continue

            lawyer = lawyer_users[day_offset % len(lawyer_users)]
            case = cases[day_offset % len(cases)]
            activity = TIMESHEET_ACTIVITIES[day_offset % len(TIMESHEET_ACTIVITIES)]
            hours = Decimal('2.0') + Decimal(str((day_offset % 5) * 0.5))
            rate = hourly_rates.get(lawyer.username, Decimal('250.00'))

            _, created = TimeEntry.objects.get_or_create(
                caso=case,
                advogado=lawyer,
                date=d,
                defaults={
                    'hours': hours,
                    'description': f'{activity} — {case.titulo[:50]}',
                    'billing_type': 'billable' if day_offset % 4 != 0 else 'non_billable',
                    'hourly_rate': rate,
                    'notes': f'Atividade do dia {d.strftime("%d/%m/%Y")}',
                },
            )
            if created:
                total_time += 1
        self.stdout.write(f'  {total_time} registros de horas criados')

        # ─── 10. LEMBRETES ───
        self.stdout.write(self.style.MIGRATE_HEADING('10. Criando lembretes...'))
        total_rem = 0
        for rem in REMINDERS_DATA:
            user_obj = users.get(rem['username'], admin_user)
            scheduled = now + timedelta(days=rem['dias'])

            _, created = UserReminder.objects.get_or_create(
                user=user_obj,
                title=rem['title'],
                defaults={
                    'description': rem['description'],
                    'frequency': rem['frequency'],
                    'scheduled_date': scheduled,
                    'priority': rem['priority'],
                    'status': 'active',
                },
            )
            if created:
                total_rem += 1
        self.stdout.write(f'  {total_rem} lembretes criados')

        # ─── 11. NOTIFICAÇÕES ───
        self.stdout.write(self.style.MIGRATE_HEADING('11. Criando notificações...'))
        total_notif = 0
        for notif in NOTIFICATIONS_DATA:
            user_obj = users.get(notif['username'], admin_user)

            _, created = Notification.objects.get_or_create(
                user=user_obj,
                title=notif['title'],
                defaults={
                    'type': notif['type'],
                    'priority': notif['priority'],
                    'message': notif['message'],
                    'link': notif.get('link', ''),
                    'is_read': notif.get('is_read', False),
                    'source': 'system',
                    'action_type': 'navigate',
                },
            )
            if created:
                total_notif += 1
        self.stdout.write(f'  {total_notif} notificações criadas')

        # ─── 12. CONTRATOS ───
        self.stdout.write(self.style.MIGRATE_HEADING('12. Criando contratos...'))
        contracts = []
        total_contracts = 0
        for ct in CONTRACTS_DATA:
            caso = cases[ct['case_idx']]
            client_obj = clients.get(ct['client_cpf'])
            defaults = {
                'case': caso,
                'client': client_obj,
                'contract_type': ct['contract_type'],
                'status': ct['status'],
                'content_html': ct['content_html'],
                'created_by': admin_user,
            }
            if ct['status'] == 'signed':
                defaults['signed_at'] = now - timedelta(days=15)

            contract, created = LegalContract.objects.get_or_create(
                title=ct['title'],
                defaults=defaults,
            )
            contracts.append(contract)
            if created:
                total_contracts += 1
                # Create detail records
                if ct['contract_type'] == 'honorarios' and 'honorarios_detail' in ct:
                    hd = ct['honorarios_detail']
                    HonorariosDetail.objects.get_or_create(
                        contract=contract,
                        defaults={
                            'fee_type': hd['fee_type'],
                            'fixed_amount': Decimal(hd.get('fixed_amount', '0')),
                            'success_percentage': Decimal(hd.get('success_percentage', '0')),
                            'payment_terms': hd.get('payment_terms', ''),
                            'installments': hd.get('installments', 1),
                            'includes_expenses': hd.get('includes_expenses', False),
                        },
                    )
                elif ct['contract_type'] == 'procuracao' and 'procuracao_detail' in ct:
                    pd = ct['procuracao_detail']
                    ProcuracaoDetail.objects.get_or_create(
                        contract=contract,
                        defaults={
                            'powers_type': pd['powers_type'],
                            'special_powers': pd.get('special_powers', ''),
                            'court_scope': pd.get('court_scope', ''),
                        },
                    )
            status = '+' if created else '='
            self.stdout.write(f'  {status} {contract.title[:70]}')
        self.stdout.write(f'  {total_contracts} contratos criados')

        # ─── 13. WORKFLOWS ───
        self.stdout.write(self.style.MIGRATE_HEADING('13. Criando workflows...'))
        wf_tmpl, wf_created = WorkflowTemplate.objects.get_or_create(
            name=WORKFLOW_TEMPLATE_DATA['name'],
            defaults={
                'description': WORKFLOW_TEMPLATE_DATA['description'],
                'specialty': WORKFLOW_TEMPLATE_DATA['specialty'],
                'steps': WORKFLOW_TEMPLATE_DATA['steps'],
                'is_active': True,
                'created_by': admin_user,
            },
        )
        self.stdout.write(f'  {"+" if wf_created else "="} Template: {wf_tmpl.name}')

        # Create execution for case 0
        step_history = [
            {
                'step': 0,
                'name': 'Petição Inicial',
                'started_at': (now - timedelta(days=55)).isoformat(),
                'completed_at': (now - timedelta(days=50)).isoformat(),
                'notes': 'Petição inicial elaborada e protocolada no e-SAJ.',
            },
            {
                'step': 1,
                'name': 'Citação do Réu',
                'started_at': (now - timedelta(days=50)).isoformat(),
                'completed_at': (now - timedelta(days=35)).isoformat(),
                'notes': 'Réu citado pessoalmente. AR confirmado.',
            },
            {
                'step': 2,
                'name': 'Contestação',
                'started_at': (now - timedelta(days=35)).isoformat(),
                'completed_at': (now - timedelta(days=20)).isoformat(),
                'notes': 'Contestação apresentada pela empresa ré com documentos.',
            },
            {
                'step': 3,
                'name': 'Réplica',
                'started_at': (now - timedelta(days=20)).isoformat(),
                'completed_at': None,
                'notes': 'Réplica em elaboração — prazo de 5 dias restantes.',
            },
        ]
        wf_exec, wf_exec_created = WorkflowExecution.objects.get_or_create(
            template=wf_tmpl,
            case=cases[0],
            defaults={
                'current_step': 3,
                'status': 'active',
                'step_history': step_history,
            },
        )
        self.stdout.write(f'  {"+" if wf_exec_created else "="} Execução: {wf_exec}')

        # ─── 14. AVALIAÇÕES DE RISCO ───
        self.stdout.write(self.style.MIGRATE_HEADING('14. Criando avaliações de risco...'))
        total_risk = 0
        for ra in RISK_ASSESSMENTS_DATA:
            caso = cases[ra['case_idx']]
            advogado = caso.advogado_responsavel

            _, created = RiskAssessment.objects.get_or_create(
                caso=caso,
                risk_level=ra['risk_level'],
                trigger=ra['trigger'],
                defaults={
                    'risk_score': ra['risk_score'],
                    'factors': ra['factors'],
                    'analysis': ra['analysis'],
                    'recommendation': ra['recommendation'],
                    'previous_level': ra['previous_level'],
                    'level_changed': ra['level_changed'],
                    'ai_generated': ra['ai_generated'],
                    'ai_model': ra['ai_model'],
                    'tokens_used': ra['tokens_used'],
                    'assessed_by': advogado,
                },
            )
            if created:
                total_risk += 1
        self.stdout.write(f'  {total_risk} avaliações de risco criadas')

        # ─── 15. GUIAS DE CUSTAS ───
        self.stdout.write(self.style.MIGRATE_HEADING('15. Criando guias de custas...'))
        total_fees = 0
        for fee in COURT_FEES_DATA:
            caso = cases[fee['case_idx']]
            due = today + timedelta(days=fee['due_date_days'])
            defaults = {
                'court': fee['court'],
                'state': fee['state'],
                'calculated_amount': Decimal(fee['calculated_amount']),
                'case_value': Decimal(fee['case_value']),
                'calculation_formula': fee['calculation_formula'],
                'due_date': due,
                'payment_status': fee['payment_status'],
                'barcode': fee['barcode'],
                'notes': fee['notes'],
                'created_by': admin_user,
            }
            if fee['payment_status'] == 'paid':
                defaults['payment_date'] = due

            _, created = CourtFeeGuide.objects.get_or_create(
                case=caso,
                fee_type=fee['fee_type'],
                defaults=defaults,
            )
            if created:
                total_fees += 1
        self.stdout.write(f'  {total_fees} guias de custas criadas')

        # ─── 16. PROTOCOLOS ELETRÔNICOS ───
        self.stdout.write(self.style.MIGRATE_HEADING('16. Criando protocolos eletrônicos...'))
        total_proto = 0
        for proto in PROTOCOLS_DATA:
            caso = cases[proto['case_idx']]
            defaults = {
                'protocol_number': proto['protocol_number'],
                'status': proto['status'],
                'protocol_receipt': proto['protocol_receipt'],
                'created_by': admin_user,
            }
            if proto['status'] == 'accepted':
                defaults['submitted_at'] = now - timedelta(days=5)
                defaults['accepted_at'] = now - timedelta(days=5)

            _, created = ElectronicProtocol.objects.get_or_create(
                case=caso,
                court_system=proto['court_system'],
                petition_type=proto['petition_type'],
                defaults=defaults,
            )
            if created:
                total_proto += 1
        self.stdout.write(f'  {total_proto} protocolos eletrônicos criados')

        # ─── 17. ASSINATURAS DIGITAIS ───
        self.stdout.write(self.style.MIGRATE_HEADING('17. Criando assinaturas digitais...'))
        total_sigs = 0
        for sig_data in DIGITAL_SIGNATURES_DATA:
            user_obj = users.get(sig_data['user_username'], admin_user)
            contract_obj = contracts[sig_data['contract_idx']] if sig_data['contract_idx'] < len(contracts) else None

            sig, created = DigitalSignature.objects.get_or_create(
                signature_hash=sig_data['signature_hash'],
                defaults={
                    'user': user_obj,
                    'contract': contract_obj,
                    'signature_type': sig_data['signature_type'],
                    'ip_address': sig_data['ip_address'],
                    'is_valid': sig_data['is_valid'],
                    'verification_url': sig_data['verification_url'],
                    'certificate_info': sig_data['certificate_info'],
                },
            )
            if created:
                total_sigs += 1
                # Create verification record if verified
                if sig_data.get('verified'):
                    SignatureVerification.objects.get_or_create(
                        signature=sig,
                        defaults={
                            'verified_by': admin_user,
                            'is_valid': True,
                            'verification_details': {
                                'method': 'ICP-Brasil',
                                'chain_valid': True,
                                'timestamp_valid': True,
                                'certificate_not_revoked': True,
                            },
                        },
                    )
        self.stdout.write(f'  {total_sigs} assinaturas digitais criadas')

        # ─── 18. TEMPLATES DE E-MAIL ───
        self.stdout.write(self.style.MIGRATE_HEADING('18. Criando templates de e-mail...'))
        total_email = 0
        for et in EMAIL_TEMPLATES_DATA:
            _, created = EmailTemplate.objects.get_or_create(
                name=et['name'],
                defaults={
                    'subject': et['subject'],
                    'body_html': et['body_html'],
                    'category': et['category'],
                    'variables': et['variables'],
                    'is_active': True,
                    'created_by': admin_user,
                },
            )
            if created:
                total_email += 1
        self.stdout.write(f'  {total_email} templates de e-mail criados')

        # ─── 19. KNOWLEDGE BASE ───
        self.stdout.write(self.style.MIGRATE_HEADING('19. Criando knowledge base...'))
        total_kb = 0
        for kb in KB_DATA:
            _, created = KnowledgeBase.objects.get_or_create(
                name=kb['name'],
                defaults={
                    'description': kb['description'],
                    'kb_layer': kb['kb_layer'],
                    'is_active': True,
                    'created_by': admin_user,
                },
            )
            if created:
                total_kb += 1
        self.stdout.write(f'  {total_kb} bases de conhecimento criadas')

        # ─── 20. NOTIFICAÇÕES ADICIONAIS ───
        self.stdout.write(self.style.MIGRATE_HEADING('20. Criando notificações adicionais...'))
        total_extra_notif = 0
        for notif in EXTRA_NOTIFICATIONS_DATA:
            user_obj = users.get(notif['username'], admin_user)

            _, created = Notification.objects.get_or_create(
                user=user_obj,
                title=notif['title'],
                defaults={
                    'type': notif['type'],
                    'priority': notif['priority'],
                    'message': notif['message'],
                    'link': notif.get('link', ''),
                    'is_read': notif.get('is_read', False),
                    'source': 'system',
                    'action_type': 'navigate',
                },
            )
            if created:
                total_extra_notif += 1
        self.stdout.write(f'  {total_extra_notif} notificações adicionais criadas')

        # ─── RESUMO FINAL ───
        self.stdout.write(self.style.SUCCESS(
            f'\n=== SEED PRODUCTION DEMO CONCLUIDO ===\n'
            f'  Usuarios:         {len(USERS_DATA)}\n'
            f'  Clientes:         {len(CLIENTS_DATA)} (5 PF + 3 PJ)\n'
            f'  Casos:            {len(CASES_DATA)}\n'
            f'  Prazos:           {total_deadlines}\n'
            f'  Tarefas:          {total_tasks}\n'
            f'  Audiencias:       {total_aud}\n'
            f'  Financeiro:       {total_fin}\n'
            f'  Lead Stages:      {len(LEAD_STAGES_DATA)}\n'
            f'  Leads CRM:        {total_leads}\n'
            f'  Timesheet:        {total_time}\n'
            f'  Lembretes:        {total_rem}\n'
            f'  Notificacoes:     {total_notif + total_extra_notif}\n'
            f'  Contratos:        {total_contracts}\n'
            f'  Workflows:        1 template + 1 execução\n'
            f'  Aval. Risco:      {total_risk}\n'
            f'  Guias Custas:     {total_fees}\n'
            f'  Protocolos:       {total_proto}\n'
            f'  Assinaturas:      {total_sigs}\n'
            f'  Email Templates:  {total_email}\n'
            f'  Knowledge Base:   {total_kb}\n'
            f'\n  Login admin: usuario_demo@bravonix.anon / Demonstração@@2026@@\n'
        ))
