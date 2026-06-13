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
# 3. CASOS (8 casos cobrindo diferentes especialidades de Procuradoria)
# ═══════════════════════════════════════════════════════════════════

CASES_DATA = [
    # Caso 1 — Execução Fiscal (Dívida Ativa ISS)
    {
        'numero_processo': '1001234-56.2025.8.26.0100',
        'titulo': 'Execução Fiscal — Município vs. Empresa XYZ Transportes (ISS)',
        'especialidade': 'tributario',
        'status': 'ativo',
        'fase': 'instrucao',
        'client_cpf': '341.628.597/0001-04',
        'cliente_nome': 'Empresa XYZ Transportes LTDA',
        'cliente_cpf_cnpj': '341.628.597/0001-04',
        'parte_contraria': 'Empresa XYZ Transportes LTDA (executada)',
        'parte_contraria_cpf_cnpj': '341.628.597/0001-04',
        'tribunal': 'TJSP',
        'vara_juizo': '1a Vara da Fazenda Pública',
        'comarca': 'São Paulo',
        'valor_causa': Decimal('250000.00'),
        'honorarios_combinados': Decimal('0.00'),
        'advogado_username': 'joao.silva',
        'descricao': 'Execução fiscal de crédito tributário de ISS inscrito em Certidão de Dívida Ativa. Requerimento de SISBAJUD em andamento.',
    },
    # Caso 2 — Defesa em Mandado de Segurança
    {
        'numero_processo': '1005678-90.2025.8.26.0100',
        'titulo': 'Defesa em MS — Tech Solutions vs. Secretaria de Licitações',
        'especialidade': 'administrativo',
        'status': 'ativo',
        'fase': 'inicial',
        'client_cpf': '12.345.678/0001-90',
        'cliente_nome': 'Município de São Paulo (autoridade coatora)',
        'cliente_cpf_cnpj': '46.374.254/0001-29',
        'parte_contraria': 'Tech Solutions Brasil LTDA (impetrante)',
        'parte_contraria_cpf_cnpj': '12.345.678/0001-90',
        'tribunal': 'TJSP',
        'vara_juizo': '5a Vara da Fazenda Pública de São Paulo',
        'comarca': 'São Paulo',
        'valor_causa': Decimal('180000.00'),
        'honorarios_combinados': Decimal('0.00'),
        'advogado_username': 'joao.silva',
        'descricao': 'Defesa do ente público em mandado de segurança impetrado contra ato de inabilitação em licitação. Prazo para prestação de informações.',
    },
    # Caso 3 — Execução Fiscal (ICMS)
    {
        'numero_processo': '0002345-67.2025.8.19.0001',
        'titulo': 'Execução Fiscal — Estado vs. Distribuidora BH Alimentos (ICMS)',
        'especialidade': 'tributario',
        'status': 'ativo',
        'fase': 'instrucao',
        'client_cpf': '523.891.704/0001-62',
        'cliente_nome': 'Distribuidora BH Alimentos LTDA',
        'cliente_cpf_cnpj': '523.891.704/0001-62',
        'parte_contraria': 'Distribuidora BH Alimentos LTDA (executada)',
        'parte_contraria_cpf_cnpj': '523.891.704/0001-62',
        'tribunal': 'TJMG',
        'vara_juizo': '2a Vara da Fazenda Pública Estadual de Belo Horizonte',
        'comarca': 'Belo Horizonte',
        'valor_causa': Decimal('320000.00'),
        'honorarios_combinados': Decimal('0.00'),
        'advogado_username': 'maria.santos',
        'descricao': 'Execução fiscal de crédito de ICMS. Executada apresentou embargos à execução fiscal. Análise dos embargos em andamento.',
    },
    # Caso 4 — PAD (Processo Administrativo Disciplinar)
    {
        'numero_processo': 'PAD-2025-00034',
        'titulo': 'PAD — Apuração de Irregularidade em Contrato Administrativo',
        'especialidade': 'administrativo',
        'status': 'ativo',
        'fase': 'instrucao',
        'client_cpf': '196.745.832/0001-19',
        'cliente_nome': 'Construtora Curitiba Obras LTDA',
        'cliente_cpf_cnpj': '196.745.832/0001-19',
        'parte_contraria': 'Servidor Público — indiciado',
        'parte_contraria_cpf_cnpj': '',
        'tribunal': 'Administração Municipal',
        'vara_juizo': 'Comissão Processante PAD',
        'comarca': 'Curitiba',
        'valor_causa': None,
        'honorarios_combinados': Decimal('0.00'),
        'advogado_username': 'pedro.lima',
        'descricao': 'PAD instaurado para apurar irregularidade na execução de contrato administrativo de obras. Fase de instrução com oitiva de testemunhas.',
    },
    # Caso 5 — Ação Civil Pública
    {
        'numero_processo': '0004567-89.2025.4.03.6100',
        'titulo': 'Ação Civil Pública — Município vs. Empresa Poluidora',
        'especialidade': 'administrativo',
        'status': 'ativo',
        'fase': 'instrucao',
        'client_cpf': '658.214.379-53',
        'cliente_nome': 'Município de Curitiba (autor)',
        'cliente_cpf_cnpj': '76.017.353/0001-06',
        'parte_contraria': 'Indústria Poluidora do Rio S.A.',
        'parte_contraria_cpf_cnpj': '98.765.432/0001-10',
        'tribunal': 'TRF-4',
        'vara_juizo': '3a Vara Federal Ambiental de Curitiba',
        'comarca': 'Curitiba',
        'valor_causa': Decimal('5000000.00'),
        'honorarios_combinados': Decimal('0.00'),
        'advogado_username': 'pedro.lima',
        'descricao': 'ACP proposta para reparação de dano ambiental causado por lançamento irregular de efluentes industriais em curso d\'água municipal.',
    },
    # Caso 6 — Impugnação em Licitação / Parecer
    {
        'numero_processo': 'PA-LICIT-2025-001',
        'titulo': 'Parecer Jurídico — Licitação Pregão 012/2025 (Obras Viárias)',
        'especialidade': 'administrativo',
        'status': 'ativo',
        'fase': 'recursal',
        'client_cpf': '45.678.901/0001-23',
        'cliente_nome': 'Secretaria de Obras Municipais',
        'cliente_cpf_cnpj': '46.374.254/0001-29',
        'parte_contraria': 'Licitante Impugnante — Construtora ABC LTDA',
        'parte_contraria_cpf_cnpj': '11.222.333/0001-44',
        'tribunal': 'Administrativo',
        'vara_juizo': 'Comissão de Licitação',
        'comarca': 'São Paulo',
        'valor_causa': Decimal('8000000.00'),
        'honorarios_combinados': Decimal('0.00'),
        'advogado_username': 'joao.silva',
        'descricao': 'Análise jurídica de impugnação ao edital do Pregão 012/2025 de obras viárias. Parecer sobre legalidade das exigências de habilitação técnica.',
    },
    # Caso 7 — Recurso Administrativo Tributário
    {
        'numero_processo': '0006789-01.2025.8.13.0024',
        'titulo': 'Defesa em MS Tributário — Dist. Nacional vs. Município Contagem',
        'especialidade': 'tributario',
        'status': 'ativo',
        'fase': 'recursal',
        'client_cpf': '45.678.901/0001-23',
        'cliente_nome': 'Município de Contagem (réu)',
        'cliente_cpf_cnpj': '18.715.705/0001-74',
        'parte_contraria': 'Distribuidora Nacional de Alimentos LTDA (impetrante)',
        'parte_contraria_cpf_cnpj': '45.678.901/0001-23',
        'tribunal': 'TJMG',
        'vara_juizo': '1a Vara da Fazenda Pública de Contagem',
        'comarca': 'Contagem',
        'valor_causa': Decimal('350000.00'),
        'honorarios_combinados': Decimal('0.00'),
        'advogado_username': 'joao.silva',
        'descricao': 'Defesa do município em MS impetrado contra cobrança de ISS sobre operações de industrialização por encomenda. Apelação contra sentença desfavorável.',
    },
    # Caso 8 — Convênio / Contrato Administrativo
    {
        'numero_processo': 'PA-CONV-2025-007',
        'titulo': 'Análise Jurídica — Convênio Estado/Município (Educação)',
        'especialidade': 'administrativo',
        'status': 'aguardando',
        'fase': 'inicial',
        'client_cpf': '46.374.254/0001-29',
        'cliente_nome': 'Secretaria Municipal de Educação',
        'cliente_cpf_cnpj': '46.374.254/0001-29',
        'parte_contraria': 'Estado de São Paulo (convenente)',
        'parte_contraria_cpf_cnpj': '46.374.254/0001-29',
        'tribunal': 'Administrativo',
        'vara_juizo': 'Procuradoria Geral do Município',
        'comarca': 'São Paulo',
        'valor_causa': Decimal('2000000.00'),
        'honorarios_combinados': Decimal('0.00'),
        'advogado_username': 'maria.santos',
        'descricao': 'Elaboração de parecer jurídico e minutas para celebração de convênio de transferência de recursos estaduais para programa municipal de educação.',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 4. PRAZOS (15 prazos)
# ═══════════════════════════════════════════════════════════════════

DEADLINES_DATA = [
    # Caso 1 — Execução Fiscal ISS
    {'case_idx': 0, 'titulo': 'Prazo SISBAJUD — Penhora Eletrônica', 'tipo': 'processual', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 5, 'descricao': 'Requerimento de penhora via SISBAJUD após citação sem pagamento'},
    {'case_idx': 0, 'titulo': 'Análise de Embargos à Execução', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 45, 'descricao': 'Prazo para resposta aos embargos do executado (Lei 6.830/1980, Art. 19)'},
    # Caso 2 — Defesa em MS
    {'case_idx': 1, 'titulo': 'Prestação de Informações no MS', 'tipo': 'processual', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 10, 'descricao': 'Prazo de 10 dias para prestação de informações pela autoridade coatora (Lei 12.016/2009, Art. 7o)'},
    # Caso 3 — Execução Fiscal ICMS
    {'case_idx': 2, 'titulo': 'Resposta aos Embargos à Execução', 'tipo': 'processual', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 3, 'descricao': 'Prazo para impugnar os embargos à execução fiscal opostos pelo executado'},
    {'case_idx': 2, 'titulo': 'Juntada de CDA Retificada', 'tipo': 'processual', 'prioridade': 'media', 'status': 'concluido', 'dias': -5, 'descricao': 'CDA retificada juntada nos autos. Concluído.'},
    # Caso 4 — PAD
    {'case_idx': 3, 'titulo': 'Notificação do Indiciado — Defesa Escrita', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 15, 'descricao': 'Prazo para notificação do servidor indiciado e início do prazo de defesa escrita'},
    {'case_idx': 3, 'titulo': 'Conclusão do Relatório Final do PAD', 'tipo': 'extrajudicial', 'prioridade': 'media', 'status': 'em_andamento', 'dias': 25, 'descricao': 'Comissão deve concluir relatório final dentro do prazo regimental'},
    # Caso 5 — ACP
    {'case_idx': 4, 'titulo': 'Prazo para Tutela de Urgência — Laudo Pericial', 'tipo': 'processual', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 8, 'descricao': 'Prazo para juntada de laudo ambiental como fundamento de tutela de urgência'},
    {'case_idx': 4, 'titulo': 'Audiência de Instrução — ACP', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 60, 'descricao': 'Audiência de instrução e julgamento da ACP ambiental'},
    # Caso 6 — Licitação / Parecer
    {'case_idx': 5, 'titulo': 'Prazo Resposta à Impugnação do Edital', 'tipo': 'recursal', 'prioridade': 'urgente', 'status': 'pendente', 'dias': 12, 'descricao': 'Prazo para a Comissão de Licitação responder à impugnação ao edital (Lei 14.133/2021, Art. 164)'},
    {'case_idx': 5, 'titulo': 'Publicação do Parecer no DOU/DOE', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'concluido', 'dias': -10, 'descricao': 'Parecer jurídico publicado no Diário Oficial. Concluído.'},
    # Caso 7 — MS Tributário
    {'case_idx': 6, 'titulo': 'Prazo para Recurso de Apelação', 'tipo': 'processual', 'prioridade': 'alta', 'status': 'pendente', 'dias': 15, 'descricao': 'Interposição de apelação contra sentença concessiva do MS tributário'},
    {'case_idx': 6, 'titulo': 'Sustentação Oral no Tribunal', 'tipo': 'processual', 'prioridade': 'media', 'status': 'pendente', 'dias': 90, 'descricao': 'Designação de data para sustentação oral no TJMG'},
    # Caso 8 — Convênio
    {'case_idx': 7, 'titulo': 'Prazo para Assinatura do Convênio', 'tipo': 'administrativo', 'prioridade': 'alta', 'status': 'pendente', 'dias': -2, 'descricao': 'Prazo para assinatura do convênio e publicação no Diário Oficial'},
    {'case_idx': 7, 'titulo': 'Publicação no Diário Oficial', 'tipo': 'administrativo', 'prioridade': 'media', 'status': 'pendente', 'dias': 30, 'descricao': 'Publicação do extrato do convênio no Diário Oficial conforme exigência legal'},
]


# ═══════════════════════════════════════════════════════════════════
# 5. TAREFAS (20 tarefas)
# ═══════════════════════════════════════════════════════════════════

TASKS_DATA = [
    # Caso 1 — Execução Fiscal ISS
    {'case_idx': 0, 'titulo': 'Verificar CDA e localizar bens do executado', 'descricao': 'Conferir a CDA, verificar dados do executado e realizar pesquisa patrimonial via SISBAJUD/SENATRAN', 'status': 'em_andamento', 'prioridade': 'urgente', 'dias_limite': 4},
    {'case_idx': 0, 'titulo': 'Elaborar impugnação aos embargos', 'descricao': 'Redigir impugnação aos embargos à execução fiscal com fundamentos jurídicos e documentação da CDA', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 40},
    {'case_idx': 0, 'titulo': 'Requerer penhora via SISBAJUD', 'descricao': 'Peticionar o bloqueio de ativos financeiros do executado via sistema SISBAJUD', 'status': 'pendente', 'prioridade': 'media', 'dias_limite': 10},
    # Caso 2 — Defesa MS
    {'case_idx': 1, 'titulo': 'Elaborar informações para autoridade coatora', 'descricao': 'Redigir as informações a serem prestadas pela autoridade coatora com defesa do ato administrativo de inabilitação', 'status': 'em_andamento', 'prioridade': 'urgente', 'dias_limite': 7},
    {'case_idx': 1, 'titulo': 'Compilar documentação do processo licitatório', 'descricao': 'Reunir edital, ata de sessão, recursos interpostos e todos os documentos que embasaram o ato de inabilitação', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 5},
    # Caso 3 — Execução Fiscal ICMS
    {'case_idx': 2, 'titulo': 'Analisar embargos à execução fiscal', 'descricao': 'Estudar os embargos interpostos pelo executado, verificar prescrição alegada e preparar impugnação', 'status': 'em_andamento', 'prioridade': 'alta', 'dias_limite': 5},
    {'case_idx': 2, 'titulo': 'Verificar prescrição do crédito tributário', 'descricao': 'Confirmar que o crédito de ICMS não está prescrito (CTN, Art. 174), com análise de eventuais causas interruptivas', 'status': 'concluida', 'prioridade': 'urgente', 'dias_limite': -2},
    {'case_idx': 2, 'titulo': 'Pesquisar jurisprudência sobre ICMS e embargos', 'descricao': 'Levantar precedentes do STJ e STF sobre a matéria de direito alegada nos embargos', 'status': 'pendente', 'prioridade': 'media', 'dias_limite': 15},
    # Caso 4 — PAD
    {'case_idx': 3, 'titulo': 'Elaborar portaria de instauração do PAD', 'descricao': 'Redigir portaria de instauração e nomeação da comissão processante conforme regulamento interno', 'status': 'em_andamento', 'prioridade': 'alta', 'dias_limite': 10},
    {'case_idx': 3, 'titulo': 'Notificar servidor indiciado', 'descricao': 'Elaborar ofício de notificação do servidor indiciado para apresentar defesa escrita no prazo regimental', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 12},
    # Caso 5 — ACP
    {'case_idx': 4, 'titulo': 'Obter laudo ambiental para instrução', 'descricao': 'Coordenar com órgão ambiental municipal a emissão de laudo técnico sobre o dano ao curso d\'água', 'status': 'em_andamento', 'prioridade': 'urgente', 'dias_limite': 6},
    {'case_idx': 4, 'titulo': 'Avaliar cabimento de TAC', 'descricao': 'Verificar se a empresa ré tem capacidade de celebrar TAC para reparação do dano antes do ajuizamento', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 7},
    {'case_idx': 4, 'titulo': 'Elaborar petição inicial da ACP', 'descricao': 'Redigir a petição inicial da ACP com pedido de tutela de urgência para cessação imediata do descarte irregular', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 20},
    # Caso 6 — Licitação
    {'case_idx': 5, 'titulo': 'Elaborar parecer sobre regularidade do edital', 'descricao': 'Analisar legalidade das cláusulas de habilitação técnica contestadas na impugnação', 'status': 'em_andamento', 'prioridade': 'urgente', 'dias_limite': 10},
    {'case_idx': 5, 'titulo': 'Protocolar resposta à impugnação', 'descricao': 'Protocolar resposta fundamentada à impugnação ao edital dentro do prazo legal', 'status': 'concluida', 'prioridade': 'alta', 'dias_limite': -7},
    # Caso 7 — MS Tributário
    {'case_idx': 6, 'titulo': 'Elaborar razões de apelação', 'descricao': 'Redigir peça recursal com fundamentos jurídicos contra a sentença concessiva do MS', 'status': 'em_andamento', 'prioridade': 'urgente', 'dias_limite': 10},
    {'case_idx': 6, 'titulo': 'Solicitar parecer da Consultoria Tributária', 'descricao': 'Consultar equipe de tributário municipal sobre a legalidade da cobrança de ISS no caso', 'status': 'pendente', 'prioridade': 'media', 'dias_limite': 20},
    # Caso 8 — Convênio
    {'case_idx': 7, 'titulo': 'Elaborar minuta do convênio', 'descricao': 'Redigir minuta do convênio de transferência de recursos com base no modelo padrão do TCE/TCU', 'status': 'concluida', 'prioridade': 'alta', 'dias_limite': -1},
    {'case_idx': 7, 'titulo': 'Obter aprovação da Controladoria', 'descricao': 'Submeter a minuta do convênio à Controladoria Geral para verificação de conformidade fiscal', 'status': 'em_andamento', 'prioridade': 'alta', 'dias_limite': 15},
    {'case_idx': 7, 'titulo': 'Publicar extrato no Diário Oficial', 'descricao': 'Providenciar a publicação do extrato do convênio no Diário Oficial Municipal após assinatura', 'status': 'pendente', 'prioridade': 'alta', 'dias_limite': 5},
]


# ═══════════════════════════════════════════════════════════════════
# 6. AUDIÊNCIAS (5 audiências)
# ═══════════════════════════════════════════════════════════════════

AUDIENCIAS_DATA = [
    {'case_idx': 0, 'tipo': 'instrucao', 'status': 'agendada', 'dias': 45, 'hora': 14, 'local': '1a Vara da Fazenda Pública — São Paulo, Sala 305', 'juiz': 'Dr. Ricardo Moreira de Almeida'},
    {'case_idx': 2, 'tipo': 'instrucao', 'status': 'agendada', 'dias': 20, 'hora': 9, 'local': '2a Vara da Fazenda Pública Estadual de BH, Sala 201', 'juiz': 'Dra. Patrícia Helena Costa'},
    {'case_idx': 3, 'tipo': 'instrucao', 'status': 'realizada', 'dias': -10, 'hora': 15, 'local': 'Comissão Processante PAD — Sala de Reuniões da PGM, Sala 102', 'juiz': 'Presidente da Comissão — Dr. Carlos Andrade', 'resultado': 'Oitiva de duas testemunhas realizada. Próxima sessão designada para oitiva do indiciado.'},
    {'case_idx': 4, 'tipo': 'instrucao', 'status': 'agendada', 'dias': 55, 'hora': 10, 'local': '3a Vara Federal Ambiental de Curitiba, Sala 401', 'juiz': 'Dr. Eduardo Nascimento Silva'},
    {'case_idx': 6, 'tipo': 'conciliacao', 'status': 'realizada', 'dias': -30, 'hora': 11, 'local': '1a Vara da Fazenda Pública de Contagem', 'juiz': 'Dra. Mariana Lopes', 'resultado': 'Tentativa de conciliação frustrada. Apelação em tramitação.'},
]


# ═══════════════════════════════════════════════════════════════════
# 7. MOVIMENTAÇÕES FINANCEIRAS (10)
# ═══════════════════════════════════════════════════════════════════

FINANCEIRO_DATA = [
    {'case_idx': 0, 'tipo': 'custas', 'descricao': 'Custas processuais — Execução Fiscal ISS', 'valor': '1250.00', 'status': 'pago', 'dias_vencimento': -15},
    {'case_idx': 0, 'tipo': 'honorario', 'descricao': 'Honorários sucumbenciais — Execução Fiscal ISS (parcial)', 'valor': '0.00', 'status': 'pendente', 'dias_vencimento': 90},
    {'case_idx': 1, 'tipo': 'custas', 'descricao': 'Custas processuais — Defesa em MS', 'valor': '900.00', 'status': 'pago', 'dias_vencimento': -10},
    {'case_idx': 2, 'tipo': 'custas', 'descricao': 'Custas processuais — Execução Fiscal ICMS', 'valor': '1500.00', 'status': 'pago', 'dias_vencimento': -5},
    {'case_idx': 3, 'tipo': 'despesa', 'descricao': 'Despesas com cópias e diligências — PAD', 'valor': '350.00', 'status': 'pago', 'dias_vencimento': -8},
    {'case_idx': 4, 'tipo': 'despesa', 'descricao': 'Despesas com laudo ambiental — ACP', 'valor': '8500.00', 'status': 'pendente', 'dias_vencimento': 20},
    {'case_idx': 5, 'tipo': 'custas', 'descricao': 'Despesas administrativas — Licitação', 'valor': '200.00', 'status': 'pago', 'dias_vencimento': -20},
    {'case_idx': 6, 'tipo': 'custas', 'descricao': 'Custas — Mandado de Segurança Tributário', 'valor': '2500.00', 'status': 'pago', 'dias_vencimento': -25},
    {'case_idx': 6, 'tipo': 'honorario', 'descricao': 'Honorários sucumbenciais — MS Tributário (fase recursal)', 'valor': '0.00', 'status': 'pendente', 'dias_vencimento': 45},
    {'case_idx': 7, 'tipo': 'despesa', 'descricao': 'Despesas com publicação no Diário Oficial', 'valor': '280.00', 'status': 'pago', 'dias_vencimento': -8},
]


# ═══════════════════════════════════════════════════════════════════
# 8. LEADS CRM (6 etapas + 8 leads)
# ═══════════════════════════════════════════════════════════════════

LEAD_STAGES_DATA = [
    {'name': 'Nova Demanda', 'order': 1, 'color': '#6B7280'},
    {'name': 'Análise Jurídica', 'order': 2, 'color': '#3B82F6'},
    {'name': 'Parecer em Elaboração', 'order': 3, 'color': '#F59E0B'},
    {'name': 'Em Aprovação', 'order': 4, 'color': '#8B5CF6'},
    {'name': 'Concluído', 'order': 5, 'color': '#10B981', 'is_won': True},
    {'name': 'Arquivado', 'order': 6, 'color': '#EF4444', 'is_lost': True},
]

LEADS_DATA = [
    {
        'name': 'Secretaria de Saúde — Contrato Emergencial 005/2025',
        'email': 'juridico.saude@municipio.gov.br',
        'phone': '(11) 3000-1111',
        'description': 'Solicitação de parecer jurídico sobre legalidade de contratação emergencial de insumos hospitalares.',
        'specialty': 'administrativo',
        'source': 'indicacao',
        'temperature': 'hot',
        'stage_name': 'Análise Jurídica',
        'estimated_value': Decimal('0.00'),
        'responsible_username': 'joao.silva',
    },
    {
        'name': 'Secretaria de Finanças — Dívida Ativa ISS Lote 12',
        'email': 'divida.ativa@municipio.gov.br',
        'phone': '(11) 3000-2222',
        'description': 'Ajuizamento de lote de execuções fiscais de ISS com valor acima de R$ 50 mil cada.',
        'specialty': 'tributario',
        'source': 'interno',
        'temperature': 'warm',
        'stage_name': 'Parecer em Elaboração',
        'estimated_value': Decimal('500000.00'),
        'responsible_username': 'maria.santos',
    },
    {
        'name': 'SEMAD — Impugnação Edital Pregão 022/2025',
        'email': 'licitacoes@municipio.gov.br',
        'phone': '(21) 3000-3333',
        'description': 'Análise de impugnação ao Pregão Eletrônico 022/2025 de aquisição de equipamentos de informática.',
        'specialty': 'administrativo',
        'source': 'interno',
        'temperature': 'warm',
        'stage_name': 'Nova Demanda',
        'estimated_value': Decimal('0.00'),
        'responsible_username': 'joao.silva',
    },
    {
        'name': 'RH Municipal — PAD Servidor Cargo Comissionado',
        'email': 'rh@municipio.gov.br',
        'phone': '(31) 3000-4444',
        'description': 'Instauração de PAD para apurar abandono de cargo por servidor de nível comissionado.',
        'specialty': 'administrativo',
        'source': 'interno',
        'temperature': 'cold',
        'stage_name': 'Nova Demanda',
        'estimated_value': Decimal('0.00'),
        'responsible_username': 'pedro.lima',
    },
    {
        'name': 'Procuradoria Estadual — Convênio AIS/2025',
        'email': 'convenios@procuradoria.gov.br',
        'phone': '(11) 3000-5555',
        'description': 'Análise e parecer sobre minuta de convênio de repasse estadual para programa de assistência social.',
        'specialty': 'administrativo',
        'source': 'interno',
        'temperature': 'hot',
        'stage_name': 'Em Aprovação',
        'estimated_value': Decimal('0.00'),
        'responsible_username': 'pedro.lima',
    },
    {
        'name': 'SEMED — Mandado de Segurança em Concurso Público',
        'email': 'juridico.semed@municipio.gov.br',
        'phone': '(41) 3000-6666',
        'description': 'Defesa do Município em MS impetrado por candidato excluído de concurso público para professor.',
        'specialty': 'administrativo',
        'source': 'interno',
        'temperature': 'hot',
        'stage_name': 'Concluído',
        'estimated_value': Decimal('0.00'),
        'responsible_username': 'joao.silva',
    },
    {
        'name': 'Controladoria — Revisão de Contrato Vigente',
        'email': 'controladoria@municipio.gov.br',
        'phone': '(51) 3000-7777',
        'description': 'Revisão jurídica de contrato administrativo vigente com suspeita de superfaturamento.',
        'specialty': 'administrativo',
        'source': 'interno',
        'temperature': 'warm',
        'stage_name': 'Análise Jurídica',
        'estimated_value': Decimal('0.00'),
        'responsible_username': 'maria.santos',
    },
    {
        'name': 'TCE — Resposta a Diligência de Auditoria',
        'email': 'auditoria@municipio.gov.br',
        'phone': '(11) 3000-8888',
        'description': 'Elaboração de resposta técnica e jurídica à diligência do TCE sobre execução de convênio educacional.',
        'specialty': 'administrativo',
        'source': 'interno',
        'temperature': 'cold',
        'stage_name': 'Arquivado',
        'estimated_value': Decimal('0.00'),
        'responsible_username': 'joao.silva',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 9. TIMESHEET (30 registros)
# ═══════════════════════════════════════════════════════════════════

TIMESHEET_ACTIVITIES = [
    'Análise de documentos e provas',
    'Elaboração de peça processual',
    'Pesquisa de jurisprudência e doutrina',
    'Reunião com representante do ente público',
    'Audiência judicial / sessão administrativa',
    'Despacho com juiz / autoridade',
    'Revisão de contrato administrativo',
    'Elaboração de parecer jurídico',
    'Acompanhamento processual e diligências',
    'Protocolo de petição e conferência no PJe/EPROC',
]


# ═══════════════════════════════════════════════════════════════════
# 10. LEMBRETES (5)
# ═══════════════════════════════════════════════════════════════════

REMINDERS_DATA = [
    {
        'title': 'Verificar publicações do DJE e Diário Oficial',
        'description': 'Consultar o Diário de Justiça Eletrônico e o Diário Oficial para novas publicações dos processos e atos administrativos.',
        'frequency': 'daily',
        'dias': 1,
        'priority': 'high',
        'username': 'joao.silva',
    },
    {
        'title': 'Reunião semanal de equipe da Procuradoria',
        'description': 'Reunião de alinhamento semanal com todos os procuradores e assessores.',
        'frequency': 'weekly',
        'dias': 7,
        'priority': 'medium',
        'username': 'joao.silva',
    },
    {
        'title': 'Revisar prazos da semana — Execuções Fiscais',
        'description': 'Conferir todos os prazos das execuções fiscais ativas na próxima semana.',
        'frequency': 'weekly',
        'dias': 5,
        'priority': 'high',
        'username': 'maria.santos',
    },
    {
        'title': 'Acompanhar andamento da ACP ambiental',
        'description': 'Consultar movimentações da ACP ambiental no TRF-4 e verificar publicações.',
        'frequency': 'biweekly',
        'dias': 14,
        'priority': 'medium',
        'username': 'pedro.lima',
    },
    {
        'title': 'Entregar relatório mensal de atividades',
        'description': 'Consolidar e entregar relatório mensal de atividades da Procuradoria ao Procurador-Geral.',
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
    {'username': 'joao.silva', 'type': 'deadline', 'priority': 'urgent', 'title': 'Prazo URGENTE: SISBAJUD — Execução Fiscal ISS', 'message': 'O prazo para requerimento de penhora via SISBAJUD na execução fiscal de ISS vence em 5 dias. Ação necessária.', 'link': '/cases', 'is_read': False},
    {'username': 'joao.silva', 'type': 'case', 'priority': 'high', 'title': 'Novo caso atribuído: Defesa em MS Licitatório', 'message': 'Você foi designado como procurador responsável no caso de defesa do MS impetrado pela Tech Solutions.', 'link': '/cases', 'is_read': True},
    {'username': 'maria.santos', 'type': 'deadline', 'priority': 'urgent', 'title': 'Prazo URGENTE: Resposta Embargos Fiscais', 'message': 'Prazo fatal para resposta aos embargos à execução fiscal de ICMS vence em 3 dias.', 'link': '/cases', 'is_read': False},
    {'username': 'maria.santos', 'type': 'task', 'priority': 'medium', 'title': 'Tarefa concluída: CDA Retificada Juntada', 'message': 'A tarefa "Juntada de CDA Retificada" foi marcada como concluída nos autos da execução fiscal.', 'link': '/cases', 'is_read': True},
    {'username': 'pedro.lima', 'type': 'case', 'priority': 'high', 'title': 'Audiência de instrução — ACP Ambiental', 'message': 'AIJ na ACP ambiental agendada para daqui a 55 dias na 3a Vara Federal Ambiental de Curitiba.', 'link': '/cases', 'is_read': False},
    {'username': 'pedro.lima', 'type': 'document', 'priority': 'medium', 'title': 'Documento gerado: Petição Inicial ACP', 'message': 'O documento "Petição Inicial — ACP Ambiental" foi gerado pelo Copilot e está pronto para revisão.', 'link': '/documents', 'is_read': False},
    {'username': 'ana.costa', 'type': 'task', 'priority': 'medium', 'title': 'Nova tarefa atribuída', 'message': 'Você foi designada para a tarefa "Pesquisar jurisprudência sobre execução fiscal e prescrição" no caso tributário.', 'link': '/cases', 'is_read': False},
    {'username': 'joao.silva', 'type': 'case_update', 'priority': 'medium', 'title': 'Movimentação financeira registrada', 'message': 'Pagamento de custas processuais de R$ 2.500,00 registrado no caso de MS tributário.', 'link': '/financeiro', 'is_read': True},
    {'username': 'maria.santos', 'type': 'case_update', 'priority': 'low', 'title': 'Nova demanda registrada no pipeline', 'message': 'A demanda "Secretaria de Finanças — Dívida Ativa ISS Lote 12" foi registrada no pipeline da Procuradoria.', 'link': '/crm', 'is_read': True},
    {'username': 'joao.silva', 'type': 'deadline', 'priority': 'high', 'title': 'Prazo recursal se aproxima', 'message': 'O prazo para interposição de apelação no caso de MS tributário vence em 12 dias.', 'link': '/cases', 'is_read': False},
]


# ═══════════════════════════════════════════════════════════════════
# 12. CONTRATOS (3)
# ═══════════════════════════════════════════════════════════════════

CONTRACTS_DATA = [
    {
        'case_idx': 0,
        'client_cpf': '341.628.597/0001-04',
        'contract_type': 'prestacao_servicos',
        'title': 'Contrato Administrativo de Serviços — Execução Fiscal ISS (Lote 2025-01)',
        'status': 'signed',
        'content_html': '<h1>Instrumento de Formalização de Atuação Processual</h1><p>A <strong>Procuradoria Geral do Município</strong>, representada pelo Procurador-Geral, no exercício de suas atribuições legais, formaliza a atuação do Procurador <strong>João Silva</strong> no acompanhamento da execução fiscal...</p><p>Cláusula 1ª - DO OBJETO: O presente instrumento registra a designação para atuação na execução fiscal referente ao ISS inscrito em dívida ativa...</p>',
        'honorarios_detail': {
            'fee_type': 'fixed',
            'fixed_amount': '0.00',
            'success_percentage': '0.00',
            'payment_terms': 'Não aplicável — procurador é servidor público.',
            'installments': 1,
            'includes_expenses': True,
        },
    },
    {
        'case_idx': 2,
        'client_cpf': '523.891.704/0001-62',
        'contract_type': 'procuracao',
        'title': 'Portaria de Designação — Execução Fiscal ICMS',
        'status': 'signed',
        'content_html': '<h1>Portaria de Designação de Procurador</h1><p>O <strong>Procurador-Geral do Estado</strong>, no uso de suas atribuições legais, <strong>designa</strong> a Dra. <strong>Maria Santos</strong>, Procuradora do Estado, matrícula nº XXXXXX, para atuar na Execução Fiscal nº 0002345-67.2025.8.19.0001...</p><p>Esta portaria entra em vigor na data de sua publicação no Diário Oficial.</p>',
        'procuracao_detail': {
            'powers_type': 'ad_judicia_extra',
            'special_powers': 'Poderes para praticar todos os atos do processo judicial e administrativo, incluindo interpor recursos, desistir de recursos, transigir e firmar acordos em nome do Estado.',
            'court_scope': 'Todas as instâncias do Poder Judiciário do Estado de Minas Gerais e Tribunais Superiores',
        },
    },
    {
        'case_idx': 5,
        'client_cpf': '46.374.254/0001-29',
        'contract_type': 'prestacao_servicos',
        'title': 'Nota de Designação — Parecer Licitação Pregão 012/2025',
        'status': 'draft',
        'content_html': '<h1>Nota de Designação para Elaboração de Parecer Jurídico</h1><p>O <strong>Gerente da Procuradoria</strong> designa o Procurador <strong>João Silva</strong> para elaborar parecer jurídico sobre a regularidade das cláusulas do Pregão 012/2025 — Obras Viárias...</p><p>Prazo: 5 dias úteis. Urgência: Alta.</p>',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 13. WORKFLOW TEMPLATES E EXECUÇÕES
# ═══════════════════════════════════════════════════════════════════

WORKFLOW_TEMPLATE_DATA = {
    'name': 'Execução Fiscal — Procedimento Padrão (Lei 6.830/1980)',
    'description': 'Workflow padrão para execuções fiscais de crédito inscrito em dívida ativa, desde a propositura até a extinção.',
    'specialty': 'tributario',
    'steps': [
        {'name': 'Verificação da CDA', 'description': 'Conferência da Certidão de Dívida Ativa: dados do devedor, valor, multa, juros e prazo prescricional', 'order': 1, 'auto_advance': False, 'deadline_days': 5},
        {'name': 'Petição Inicial', 'description': 'Elaboração e protocolo da petição inicial de execução fiscal na vara competente', 'order': 2, 'auto_advance': False, 'deadline_days': 10},
        {'name': 'Citação do Executado', 'description': 'Acompanhar citação do executado e prazo de 3 dias para pagamento (LEF, Art. 8o)', 'order': 3, 'auto_advance': False, 'deadline_days': 30},
        {'name': 'Penhora / SISBAJUD', 'description': 'Requerer penhora eletrônica via SISBAJUD ou indicar bens à penhora', 'order': 4, 'auto_advance': False, 'deadline_days': 15},
        {'name': 'Embargos à Execução', 'description': 'Analisar e responder eventuais embargos interpostos pelo executado', 'order': 5, 'auto_advance': False, 'deadline_days': 30},
        {'name': 'Hasta Pública', 'description': 'Acompanhar designação e realização de hasta pública para alienação dos bens penhorados', 'order': 6, 'auto_advance': False, 'deadline_days': 60},
        {'name': 'Extinção da Execução', 'description': 'Requerer extinção da execução após satisfação integral do crédito ou outra causa extintiva', 'order': 7, 'auto_advance': False, 'deadline_days': 15},
    ],
}


# ═══════════════════════════════════════════════════════════════════
# 14. AVALIAÇÕES DE RISCO
# ═══════════════════════════════════════════════════════════════════

RISK_ASSESSMENTS_DATA = [
    # Caso 0 — Execução Fiscal ISS — 2 avaliações mostrando evolução
    {
        'case_idx': 0,
        'risk_level': 'medium',
        'risk_score': 55,
        'factors': [
            {'name': 'Embargos à execução opostos', 'weight': 0.3, 'description': 'Executado opôs embargos alegando prescrição e excesso de execução'},
            {'name': 'CDA com dados corretos', 'weight': -0.25, 'description': 'CDA verificada e sem vícios formais — ponto favorável ao Município'},
            {'name': 'Valor expressivo de ISS', 'weight': 0.2, 'description': 'R$ 250.000,00 em dívida ativa — interesse relevante de recuperação'},
        ],
        'analysis': 'Execução fiscal com risco médio em razão dos embargos opostos. A alegação de prescrição precisa ser rebatida com demonstração de causas interruptivas. A CDA não apresenta vícios formais, ponto favorável ao Município.',
        'recommendation': 'Impugnar os embargos com robusta fundamentação sobre as causas interruptivas da prescrição. Apresentar extrato detalhado da inscrição em dívida ativa.',
        'trigger': 'inicio_caso',
        'previous_level': '',
        'level_changed': False,
        'ai_generated': True,
        'ai_model': 'mistralai/mistral-medium-2505',
        'tokens_used': 1250,
        'days_ago': 45,
    },
    {
        'case_idx': 0,
        'risk_level': 'low',
        'risk_score': 30,
        'factors': [
            {'name': 'Embargos rejeitados liminarmente', 'weight': -0.3, 'description': 'Juízo rejeitou preliminar de prescrição alegada'},
            {'name': 'SISBAJUD bloqueou valores', 'weight': -0.25, 'description': 'Penhora eletrônica de R$ 180.000,00 efetivada'},
            {'name': 'Saldo devedor em análise', 'weight': 0.1, 'description': 'Diferença de R$ 70.000,00 ainda pendente de constrição'},
        ],
        'analysis': 'Após rejeição da preliminar de prescrição e efetivação de penhora via SISBAJUD, o risco reduziu substancialmente. O valor bloqueado corresponde a 72% do débito. Aguardar resposta do banco sobre o saldo.',
        'recommendation': 'Prosseguir com a execução. Requerer penhora adicional para o saldo remanescente. Monitorar prazo para impugnar o laudo de avaliação.',
        'trigger': 'nova_prova',
        'previous_level': 'medium',
        'level_changed': True,
        'ai_generated': False,
        'ai_model': '',
        'tokens_used': 0,
        'days_ago': 10,
    },
    # Caso 1 — Defesa em MS — 2 avaliações
    {
        'case_idx': 1,
        'risk_level': 'high',
        'risk_score': 70,
        'factors': [
            {'name': 'Prazo apertado para informações', 'weight': 0.35, 'description': 'Apenas 10 dias para prestar informações (Lei 12.016/2009, Art. 7o)'},
            {'name': 'Liminar concedida contra o ente', 'weight': 0.25, 'description': 'Juízo concedeu liminar suspendendo a inabilitação no pregão'},
            {'name': 'Ato administrativo bem fundamentado', 'weight': -0.2, 'description': 'A inabilitação foi devidamente justificada no processo licitatório'},
        ],
        'analysis': 'Situação de risco alto pela liminar concedida que suspendeu a inabilitação. É necessário elaborar informações robustas e avaliar pedido de suspensão da liminar. O ato administrativo está bem fundamentado, o que favorece a defesa.',
        'recommendation': 'Elaborar as informações com foco na regularidade do ato. Avaliar cabimento de agravo regimental ou pedido de SS. Reunir toda a documentação do processo licitatório.',
        'trigger': 'inicio_caso',
        'previous_level': '',
        'level_changed': False,
        'ai_generated': True,
        'ai_model': 'mistralai/mistral-medium-2505',
        'tokens_used': 980,
        'days_ago': 40,
    },
    {
        'case_idx': 1,
        'risk_level': 'medium',
        'risk_score': 45,
        'factors': [
            {'name': 'Informações protocoladas a tempo', 'weight': -0.3, 'description': 'Informações foram apresentadas no prazo legal'},
            {'name': 'Liminar em vigor', 'weight': 0.25, 'description': 'Liminar ainda em vigor, pregão temporariamente suspenso'},
            {'name': 'Jurisprudência favorável ao ente', 'weight': -0.2, 'description': 'STJ tem mantido inabilitações em licitação quando fundamentadas'},
        ],
        'analysis': 'Informações protocoladas no prazo. A jurisprudência do STJ favorece a Administração quando o ato de inabilitação está bem fundamentado. Risco reduzido após apresentação das informações.',
        'recommendation': 'Acompanhar julgamento do mérito. Preparar sustentação oral. Monitorar publicações do tribunal.',
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
        'calculated_amount': '1250.00',
        'case_value': '250000.00',
        'calculation_formula': 'Custas de distribuição da execução fiscal — valor fixo conforme Tabela de Custas TJSP',
        'due_date_days': -20,
        'payment_status': 'paid',
        'barcode': '23793.38128 60000.000003 00000.000405 1 84340000125000',
        'notes': 'Guia DARE-SP recolhida. Comprovante juntado aos autos da execução fiscal.',
    },
    {
        'case_idx': 6,
        'fee_type': 'custas_recursais',
        'court': 'TJMG',
        'state': 'MG',
        'calculated_amount': '4575.00',
        'case_value': '350000.00',
        'calculation_formula': 'Preparo recursal: 1% sobre o valor atualizado da causa + porte de remessa e retorno',
        'due_date_days': 10,
        'payment_status': 'pending',
        'barcode': '23793.38128 60000.000003 00000.000406 1 95670000457500',
        'notes': 'Guia para preparo do recurso de apelação no MS tributário. Prazo fatal em 10 dias.',
    },
    {
        'case_idx': 4,
        'fee_type': 'pericia',
        'court': 'TRF-4',
        'state': 'PR',
        'calculated_amount': '8500.00',
        'case_value': '5000000.00',
        'calculation_formula': 'Honorários periciais ambientais fixados pelo juízo — laudo de impacto ambiental',
        'due_date_days': 20,
        'payment_status': 'pending',
        'barcode': '23793.38128 60000.000003 00000.000407 1 86780000850000',
        'notes': 'Guia de honorários periciais para laudo ambiental na ACP. Verificar possibilidade de isenção pelo ente público.',
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
        'petition_type': 'Impugnação aos Embargos à Execução Fiscal',
        'protocol_receipt': 'Protocolo recebido pelo sistema e-SAJ em 15/05/2025 às 14:32:15. Número de protocolo: ESAJ-2025-0045678. Prazo atendido.',
    },
    {
        'case_idx': 6,
        'protocol_number': '',
        'court_system': 'projudi',
        'status': 'pending',
        'petition_type': 'Recurso de Apelação — MS Tributário',
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
        'name': 'Notificação à Parte Interessada',
        'subject': 'Notificação — Processo nº {{numero_processo}} — {{nome_parte}}',
        'category': 'client',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Prezado(a) {{nome_parte}},</h2>
<p>A <strong>Procuradoria {{nome_procuradoria}}</strong> informa sobre movimentação no processo abaixo:</p>
<p>Processo nº: <strong>{{numero_processo}}</strong>.</p>
<p>Para acompanhar o processo, acesse o portal ou entre em contato com a Procuradoria.</p>
<p><a href="{{link_portal}}" style="background-color: #2563EB; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Acessar Portal</a></p>
<p>Em caso de dúvidas, estamos à disposição pelo telefone {{telefone_procuradoria}} ou e-mail {{email_procuradoria}}.</p>
<p>Atenciosamente,<br>{{nome_procuradoria}}</p>
</div>''',
        'variables': [
            {'name': 'nome_parte', 'description': 'Nome da parte interessada ou ente notificado'},
            {'name': 'nome_procuradoria', 'description': 'Nome da Procuradoria'},
            {'name': 'numero_processo', 'description': 'Número do processo'},
            {'name': 'link_portal', 'description': 'Link para o portal de acompanhamento'},
            {'name': 'telefone_procuradoria', 'description': 'Telefone da Procuradoria'},
            {'name': 'email_procuradoria', 'description': 'E-mail da Procuradoria'},
        ],
    },
    {
        'name': 'Lembrete de Prazo Judicial',
        'subject': 'URGENTE: Prazo judicial se aproxima — {{titulo_prazo}}',
        'category': 'deadline',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px; margin-bottom: 20px;">
<strong>ATENÇÃO: Prazo judicial próximo do vencimento</strong>
</div>
<p>Prezado(a) {{nome_procurador}},</p>
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
            {'name': 'nome_procurador', 'description': 'Nome do procurador responsável'},
            {'name': 'titulo_caso', 'description': 'Título do caso'},
            {'name': 'numero_processo', 'description': 'Número do processo'},
            {'name': 'titulo_prazo', 'description': 'Título/descrição do prazo'},
            {'name': 'data_vencimento', 'description': 'Data de vencimento do prazo'},
            {'name': 'dias_restantes', 'description': 'Quantidade de dias restantes'},
        ],
    },
    {
        'name': 'Audiência / Sessão Agendada',
        'subject': 'Audiência agendada — {{tipo_audiencia}} — {{titulo_caso}}',
        'category': 'notification',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Audiência / Sessão Agendada</h2>
<p>Prezado(a) {{nome_procurador}},</p>
<p>Informamos que foi agendada uma audiência de <strong>{{tipo_audiencia}}</strong> no processo abaixo:</p>
<table style="width: 100%; border-collapse: collapse;">
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Processo:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{numero_processo}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Data/Hora:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{data_hora_audiencia}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Local:</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{local_audiencia}}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E5E7EB;"><strong>Juiz(a):</strong></td><td style="padding: 8px; border: 1px solid #E5E7EB;">{{nome_juiz}}</td></tr>
</table>
<p><strong>Orientações:</strong></p>
<ul>
<li>Compareça ao local com pelo menos 15 minutos de antecedência</li>
<li>Porte credencial funcional e documentos do processo</li>
<li>Verifique eventual necessidade de sustentação oral ou manifestação prévia</li>
</ul>
<p>O procurador responsável {{nome_procurador}} deverá confirmar ciência pelo sistema.</p>
</div>''',
        'variables': [
            {'name': 'nome_procurador', 'description': 'Nome do procurador responsável'},
            {'name': 'tipo_audiencia', 'description': 'Tipo de audiência (instrução, conciliação, julgamento, etc.)'},
            {'name': 'numero_processo', 'description': 'Número do processo'},
            {'name': 'data_hora_audiencia', 'description': 'Data e hora da audiência'},
            {'name': 'local_audiencia', 'description': 'Local da audiência'},
            {'name': 'nome_juiz', 'description': 'Nome do juiz'},
        ],
    },
    {
        'name': 'Documento Pronto para Revisão',
        'subject': 'Documento pronto: {{nome_documento}} — {{titulo_caso}}',
        'category': 'notification',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Documento Disponível para Revisão</h2>
<p>Prezado(a) {{nome_procurador}},</p>
<p>O documento <strong>{{nome_documento}}</strong> referente ao processo <strong>{{titulo_caso}}</strong> (nº {{numero_processo}}) foi gerado e está pronto para sua revisão.</p>
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
            {'name': 'nome_procurador', 'description': 'Nome do procurador responsável'},
            {'name': 'nome_documento', 'description': 'Nome do documento'},
            {'name': 'titulo_caso', 'description': 'Título do processo/caso'},
            {'name': 'numero_processo', 'description': 'Número do processo'},
            {'name': 'tipo_documento', 'description': 'Tipo do documento'},
            {'name': 'gerado_por', 'description': 'Quem gerou (Copilot, procurador, etc.)'},
            {'name': 'data_geracao', 'description': 'Data de geração'},
            {'name': 'link_documento', 'description': 'Link para o documento'},
        ],
    },
    {
        'name': 'Guia de Custas Processuais',
        'subject': 'Guia nº {{numero_guia}} — Custas Processuais — {{titulo_caso}}',
        'category': 'billing',
        'body_html': '''<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Guia de Recolhimento de Custas Processuais</h2>
<p>Prezado(a) {{nome_procurador}},</p>
<p>Segue guia de recolhimento de custas referente ao processo abaixo:</p>
<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
<tr style="background-color: #F3F4F6;"><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Guia nº</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB;">{{numero_guia}}</td></tr>
<tr><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Processo</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB;">{{numero_processo}}</td></tr>
<tr style="background-color: #F3F4F6;"><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Tipo de custa</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB;">{{tipo_custa}}</td></tr>
<tr><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Valor</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB; font-size: 18px; color: #059669;"><strong>R$ {{valor}}</strong></td></tr>
<tr style="background-color: #F3F4F6;"><td style="padding: 10px; border: 1px solid #E5E7EB;"><strong>Vencimento</strong></td><td style="padding: 10px; border: 1px solid #E5E7EB;">{{data_vencimento}}</td></tr>
</table>
<p>Observação: em caso de isenção ou imunidade tributária do ente público, anexar certidão correspondente ao recolhimento.</p>
<p>Em caso de dúvidas, acesse o sistema ou entre em contato com a Procuradoria.</p>
</div>''',
        'variables': [
            {'name': 'nome_procurador', 'description': 'Nome do procurador responsável'},
            {'name': 'numero_guia', 'description': 'Número da guia de recolhimento'},
            {'name': 'numero_processo', 'description': 'Número do processo'},
            {'name': 'tipo_custa', 'description': 'Tipo de custa (preparo, diligência, pericial, etc.)'},
            {'name': 'valor', 'description': 'Valor a recolher'},
            {'name': 'data_vencimento', 'description': 'Data de vencimento da guia'},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════
# 19. KNOWLEDGE BASE (2 documentos)
# ═══════════════════════════════════════════════════════════════════

KB_DATA = [
    {
        'name': 'Legislação Administrativa e Fiscal',
        'description': 'Base de conhecimento contendo os principais diplomas legais aplicáveis à Procuradoria: Lei 6.830/1980 (LEF), Lei 8.666/1993 e 14.133/2021 (licitações), Lei 8.112/1990 (PAD), Lei 9.784/1999 (processo administrativo), CPC e legislação tributária complementar.',
        'kb_layer': 'global',
    },
    {
        'name': 'Jurisprudência em Execução Fiscal e Mandado de Segurança',
        'description': 'Compilação de súmulas, orientações jurisprudenciais e decisões relevantes do STJ e STF sobre execução fiscal (dívida ativa, penhora, embargos, SISBAJUD), mandado de segurança contra atos do poder público, ação civil pública e controle de legalidade de atos administrativos.',
        'kb_layer': 'global',
    },
]


# ═══════════════════════════════════════════════════════════════════
# 20. NOTIFICAÇÕES ADICIONAIS (mix de tipos)
# ═══════════════════════════════════════════════════════════════════

EXTRA_NOTIFICATIONS_DATA = [
    {'username': 'joao.silva', 'type': 'contract', 'priority': 'high', 'title': 'Portaria de designação pendente de assinatura', 'message': 'A Portaria de Designação do procurador para o PAD nº 001/2025 está aguardando assinatura da chefia. Por favor, encaminhe para assinatura digital.', 'link': '/contratos', 'is_read': False},
    {'username': 'maria.santos', 'type': 'compliance', 'priority': 'medium', 'title': 'Verificação LGPD — processo com dados de servidor', 'message': 'O PAD instaurado contra servidor público contém dados pessoais sensíveis que precisam de revisão de conformidade com a LGPD antes da publicação no Diário Oficial.', 'link': '/compliance', 'is_read': False},
    {'username': 'pedro.lima', 'type': 'system', 'priority': 'low', 'title': 'Backup semanal concluído', 'message': 'O backup semanal dos documentos da Procuradoria foi concluído com sucesso. 1.247 arquivos processados.', 'link': '', 'is_read': True},
    {'username': 'joao.silva', 'type': 'simulation', 'priority': 'medium', 'title': 'Avaliação de risco atualizada — Execução Fiscal ISS', 'message': 'A avaliação de risco da Execução Fiscal ISS foi atualizada: risco reduziu de Alto para Médio após penhora de ativos via SISBAJUD confirmada pelo tribunal.', 'link': '/risk', 'is_read': False},
    {'username': 'ana.costa', 'type': 'message', 'priority': 'high', 'title': 'Nova movimentação processual detectada', 'message': 'O sistema detectou nova movimentação no processo de Defesa em MS Licitatório: decisão liminar publicada. Verifique e adote as providências cabíveis.', 'link': '/messages', 'is_read': False},
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

        # ─── 2. PARTES / CLIENTES ───
        self.stdout.write(self.style.MIGRATE_HEADING('2. Criando partes/clientes (entes públicos e partes adversas)...'))
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
            f'  Partes/Clientes:  {len(CLIENTS_DATA)} (entes públicos e partes adversas)\n'
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
