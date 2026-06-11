"""
Management command para criar dados de demonstração das novas features.
Timesheet, CRM/Leads, KPIs, NFS-e.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Cria dados de demonstração para Timesheet, CRM, KPIs e NFS-e'

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from apps.cases.models import (
            Client, LegalCase, CaseTask,
            TimeEntry, LeadStage, Lead, LeadActivity,
            LawyerScore, InvoiceNFSe,
        )

        User = get_user_model()

        # Get or create demo user (procuradoria context)
        user, _ = User.objects.get_or_create(
            username='demo_procurador',
            defaults={
                'first_name': 'João',
                'last_name': 'Silva',
                'email': 'joao@verus.ai',
                'role': 'procurador',
                'is_active': True,
            }
        )
        if not user.has_usable_password():
            user.set_password('demo123')
            user.save()

        user2, _ = User.objects.get_or_create(
            username='demo_procuradora',
            defaults={
                'first_name': 'Maria',
                'last_name': 'Santos',
                'email': 'maria@verus.ai',
                'role': 'procurador',
                'is_active': True,
            }
        )
        if not user2.has_usable_password():
            user2.set_password('demo123')
            user2.save()

        # Get or create demo client
        client, _ = Client.objects.get_or_create(
            cpf_cnpj='123.456.789-00',
            defaults={
                'name': 'Carlos Alberto Oliveira',
                'client_type': 'pessoa_fisica',
                'email': 'carlos@email.com',
                'phone': '(11) 99999-1234',
                'address': 'Rua das Flores, 100',
                'city': 'São Paulo',
                'state': 'SP',
                'zipcode': '01000-000',
                'responsible_lawyer': user,
                'created_by': user,
            }
        )

        client2, _ = Client.objects.get_or_create(
            cpf_cnpj='98.765.432/0001-10',
            defaults={
                'name': 'Tech Solutions LTDA',
                'client_type': 'pessoa_juridica',
                'company_name': 'Tech Solutions Tecnologia LTDA',
                'email': 'contato@techsolutions.com',
                'phone': '(11) 3456-7890',
                'responsible_lawyer': user2,
                'created_by': user,
            }
        )

        # Get or create demo case (procuradoria context — execução fiscal)
        case, _ = LegalCase.objects.get_or_create(
            numero_processo='0001234-56.2024.8.15.2001',
            defaults={
                'titulo': 'Execução Fiscal — Município vs. Devedor de ISS',
                'especialidade': 'tributario',
                'status': 'ativo',
                'fase': 'instrucao',
                'client': client,
                'cliente_nome': client.name,
                'cliente_cpf_cnpj': client.cpf_cnpj,
                'parte_contraria': 'Empresa XYZ LTDA',
                'parte_contraria_cpf_cnpj': '12.345.678/0001-90',
                'tribunal': 'TJSP',
                'vara_juizo': '1ª Vara da Fazenda Pública',
                'comarca': 'São Paulo',
                'valor_causa': Decimal('150000.00'),
                'honorarios_combinados': Decimal('0.00'),
                'advogado_responsavel': user,
                'created_by': user,
                'descricao': 'Execução fiscal de crédito tributário de ISS inscrito em dívida ativa.',
            }
        )

        # ─── TIMESHEET ───
        self.stdout.write('Criando registros de timesheet...')
        today = date.today()
        for i in range(15):
            d = today - timedelta(days=i)
            if d.weekday() < 5:  # Dias úteis
                TimeEntry.objects.get_or_create(
                    caso=case,
                    advogado=user,
                    date=d,
                    defaults={
                        'hours': Decimal('3.5') if i % 2 == 0 else Decimal('2.0'),
                        'description': f'Análise de documentos e elaboração de peça processual — dia {d}',
                        'billing_type': 'billable',
                        'hourly_rate': Decimal('250.00'),
                        'notes': 'Atividade regular do caso',
                    }
                )

        # ─── CRM / LEADS ───
        self.stdout.write('Criando pipeline de leads...')
        stages_data = [
            {'name': 'Nova Demanda', 'order': 1, 'color': '#6B7280'},
            {'name': 'Análise Jurídica', 'order': 2, 'color': '#3B82F6'},
            {'name': 'Parecer Elaborado', 'order': 3, 'color': '#F59E0B'},
            {'name': 'Em Aprovação', 'order': 4, 'color': '#8B5CF6'},
            {'name': 'Concluído', 'order': 5, 'color': '#10B981', 'is_won': True},
            {'name': 'Arquivado', 'order': 6, 'color': '#EF4444', 'is_lost': True},
        ]
        stages = {}
        for s in stages_data:
            stage, _ = LeadStage.objects.get_or_create(
                name=s['name'],
                defaults={k: v for k, v in s.items() if k != 'name'}
            )
            stages[s['name']] = stage

        leads_data = [
            {
                'name': 'Secretaria de Obras — Contrato 001/2025', 'email': 'obras@municipio.gov.br',
                'phone': '(83) 3000-1234',
                'description': 'Parecer jurídico sobre legalidade de contratação emergencial de obras.',
                'specialty': 'administrativo', 'source': 'indicacao', 'temperature': 'hot',
                'stage': stages['Análise Jurídica'], 'estimated_value': Decimal('0.00'),
                'responsible': user,
            },
            {
                'name': 'Câmara Municipal — Impugnação Edital', 'email': 'camara@municipio.gov.br',
                'phone': '(11) 3000-5678',
                'description': 'Análise de impugnação ao edital de licitação de pregão eletrônico.',
                'specialty': 'administrativo', 'source': 'interno', 'temperature': 'warm',
                'stage': stages['Parecer Elaborado'], 'estimated_value': Decimal('0.00'),
                'responsible': user2,
            },
            {
                'name': 'Empresa XYZ — Execução Fiscal ISS', 'email': 'fiscalizacao@municipio.gov.br',
                'phone': '(21) 3000-9876',
                'description': 'Propositura de execução fiscal para cobrança de ISS em dívida ativa.',
                'specialty': 'tributario', 'source': 'interno', 'temperature': 'warm',
                'stage': stages['Nova Demanda'], 'estimated_value': Decimal('150000.00'),
                'responsible': user,
            },
            {
                'name': 'Mandado de Segurança — SEMED', 'email': 'semed@municipio.gov.br',
                'phone': '(83) 3000-4321',
                'description': 'Defesa do poder público em MS impetrado contra ato da SEMED.',
                'specialty': 'administrativo', 'source': 'interno', 'temperature': 'cold',
                'stage': stages['Nova Demanda'], 'estimated_value': Decimal('0.00'),
                'responsible': user2,
            },
            {
                'name': 'PAD — Servidor cargo comissionado', 'email': 'rh@municipio.gov.br',
                'phone': '(11) 3000-7890',
                'description': 'Instauração de PAD para apurar irregularidade funcional.',
                'specialty': 'administrativo', 'source': 'interno', 'temperature': 'hot',
                'stage': stages['Em Aprovação'], 'estimated_value': Decimal('0.00'),
                'responsible': user,
            },
        ]

        for ld in leads_data:
            lead, created = Lead.objects.get_or_create(
                name=ld['name'],
                defaults={**ld, 'created_by': user}
            )
            if created:
                LeadActivity.objects.create(
                    lead=lead, activity_type='note',
                    description=f'Lead cadastrado via {lead.get_source_display()}',
                    created_by=user,
                )

        # ─── KPIs ───
        self.stdout.write('Criando scores de KPI...')
        period_start = date(today.year, today.month, 1)
        period_end = period_start + timedelta(days=30)

        for u, metrics in [
            (user, {'cases_won': 3, 'cases_settled': 2, 'deadlines_met': 15, 'deadlines_missed': 1,
                     'tasks_completed': 25, 'hours_logged': 120, 'documents_generated': 18,
                     'revenue_generated': Decimal('45000.00')}),
            (user2, {'cases_won': 5, 'cases_settled': 1, 'deadlines_met': 20, 'deadlines_missed': 0,
                      'tasks_completed': 30, 'hours_logged': 150, 'documents_generated': 22,
                      'revenue_generated': Decimal('62000.00')}),
        ]:
            score, _ = LawyerScore.objects.update_or_create(
                lawyer=u, period_start=period_start, period_end=period_end,
                defaults=metrics,
            )
            score.calculate_score()
            score.badges = []
            if metrics['deadlines_missed'] == 0:
                score.badges.append('speed_demon')
            if metrics['cases_won'] >= 5:
                score.badges.append('closer')
            if metrics['hours_logged'] >= 100:
                score.badges.append('work_horse')
            if metrics['documents_generated'] >= 20:
                score.badges.append('writer')
            score.save()

        # Update rankings
        all_scores = list(LawyerScore.objects.filter(
            period_start=period_start, period_end=period_end
        ).order_by('-total_score'))
        for i, s in enumerate(all_scores, 1):
            s.rank_position = i
            s.save(update_fields=['rank_position'])

        # ─── NFS-e ───
        self.stdout.write('Criando notas fiscais demo...')
        InvoiceNFSe.objects.get_or_create(
            descricao_servico='Custas processuais — Execução Fiscal ISS',
            client=client,
            defaults={
                'caso': case,
                'status': 'draft',
                'codigo_servico': '6911-7/01',
                'valor_servico': Decimal('15000.00'),
                'aliquota_iss': Decimal('5.00'),
                'data_competencia': today.replace(day=1),
                'municipio_prestacao': 'São Paulo',
                'created_by': user,
            }
        )

        InvoiceNFSe.objects.get_or_create(
            descricao_servico='Serviços técnicos de assessoria jurídica — Tech Solutions',
            client=client2,
            defaults={
                'status': 'authorized',
                'numero_nfse': '2024001234',
                'codigo_verificacao': 'ABC123DEF456',
                'codigo_servico': '6911-7/01',
                'valor_servico': Decimal('8000.00'),
                'aliquota_iss': Decimal('5.00'),
                'data_competencia': (today - timedelta(days=30)).replace(day=1),
                'data_emissao': timezone.now() - timedelta(days=25),
                'municipio_prestacao': 'São Paulo',
                'created_by': user,
            }
        )

        self.stdout.write(self.style.SUCCESS(
            '\n Dados de demonstração criados com sucesso!\n'
            '  - Timesheet: 10+ registros de horas\n'
            '  - CRM: 6 etapas + 5 demandas no funil (contexto de Procuradoria)\n'
            '  - KPIs: 2 procuradores com scores e badges\n'
            '  - NFS-e: 2 notas fiscais (rascunho + autorizada)\n'
        ))
