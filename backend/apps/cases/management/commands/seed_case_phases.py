"""
Management command para popular fases processuais e tarefas demo
nos casos existentes (produção/demo).
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand

from apps.cases.models import LegalCase, CasePhase, CaseTask
from apps.cases.services.case_phases import create_phases_for_case


class Command(BaseCommand):
    help = 'Popula fases processuais e tarefas demo para os casos existentes.'

    def handle(self, *args, **options):
        cases = LegalCase.objects.all()
        total_cases = cases.count()

        if total_cases == 0:
            self.stdout.write(self.style.WARNING('Nenhum caso encontrado no banco.'))
            return

        self.stdout.write(f'Encontrados {total_cases} caso(s). Gerando fases...')

        created_phases = 0
        created_tasks = 0

        for caso in cases:
            # Limpar fases existentes para recriar
            existing = CasePhase.objects.filter(caso=caso).count()
            if existing > 0:
                self.stdout.write(f'  [{caso.titulo[:40]}] ja possui {existing} fases — pulando fases.')
            else:
                phases = create_phases_for_case(caso)
                created_phases += len(phases)
                self.stdout.write(f'  [{caso.titulo[:40]}] {len(phases)} fases criadas.')

            # Determinar a fase in_progress para criar tarefas demo
            in_progress_phase = CasePhase.objects.filter(
                caso=caso, status='in_progress'
            ).first()

            if in_progress_phase and not CaseTask.objects.filter(caso=caso).exists():
                # Criar tarefas demo para a fase em andamento
                tasks = self._create_demo_tasks(caso, in_progress_phase)
                created_tasks += len(tasks)

        self.stdout.write(self.style.SUCCESS(
            f'Concluido: {created_phases} fases e {created_tasks} tarefas criadas.'
        ))

    def _create_demo_tasks(self, caso, phase):
        """Cria tarefas demo vinculadas ao caso com base na fase em andamento."""
        today = date.today()
        tasks = []

        # Templates de tarefa por nome de fase
        task_templates = {
            'Contestação': [
                {
                    'titulo': 'Preparar contestação',
                    'descricao': 'Elaborar peça de contestação com todos os fundamentos de fato e de direito',
                    'status': 'em_andamento',
                    'prioridade': 'alta',
                    'data_limite': today + timedelta(days=5),
                },
                {
                    'titulo': 'Reunir provas documentais',
                    'descricao': 'Organizar documentos que serão juntados com a contestação',
                    'status': 'pendente',
                    'prioridade': 'alta',
                    'data_limite': today + timedelta(days=3),
                },
            ],
            'Resposta à Acusação': [
                {
                    'titulo': 'Elaborar resposta à acusação',
                    'descricao': 'Preparar resposta escrita nos termos do art. 396 do CPP',
                    'status': 'em_andamento',
                    'prioridade': 'alta',
                    'data_limite': today + timedelta(days=5),
                },
                {
                    'titulo': 'Arrolar testemunhas de defesa',
                    'descricao': 'Identificar e arrolar testemunhas para a instrução criminal',
                    'status': 'pendente',
                    'prioridade': 'media',
                    'data_limite': today + timedelta(days=5),
                },
            ],
            'Audiência de Conciliação': [
                {
                    'titulo': 'Preparar proposta de acordo',
                    'descricao': 'Elaborar proposta de acordo para apresentar na audiência de conciliação',
                    'status': 'em_andamento',
                    'prioridade': 'alta',
                    'data_limite': today + timedelta(days=7),
                },
                {
                    'titulo': 'Orientar cliente sobre audiência',
                    'descricao': 'Reunião com cliente para orientar sobre a audiência de conciliação e possibilidades de acordo',
                    'status': 'pendente',
                    'prioridade': 'media',
                    'data_limite': today + timedelta(days=4),
                },
            ],
            'Audiência de Mediação': [
                {
                    'titulo': 'Preparar proposta de acordo familiar',
                    'descricao': 'Elaborar proposta de acordo para mediação familiar',
                    'status': 'em_andamento',
                    'prioridade': 'alta',
                    'data_limite': today + timedelta(days=7),
                },
                {
                    'titulo': 'Reunir documentação complementar',
                    'descricao': 'Organizar documentos para apresentar na mediação',
                    'status': 'pendente',
                    'prioridade': 'media',
                    'data_limite': today + timedelta(days=5),
                },
            ],
            'Citação da Fazenda': [
                {
                    'titulo': 'Acompanhar citação da Fazenda',
                    'descricao': 'Verificar se a Fazenda Pública foi devidamente citada e acompanhar prazo',
                    'status': 'em_andamento',
                    'prioridade': 'alta',
                    'data_limite': today + timedelta(days=10),
                },
                {
                    'titulo': 'Preparar réplica antecipada',
                    'descricao': 'Iniciar elaboração da réplica prevendo os argumentos da Fazenda',
                    'status': 'pendente',
                    'prioridade': 'media',
                    'data_limite': today + timedelta(days=15),
                },
            ],
        }

        # Fallback genérico
        default_tasks = [
            {
                'titulo': f'Acompanhar fase: {phase.name}',
                'descricao': f'Acompanhar andamento da fase "{phase.name}" e preparar documentação necessária',
                'status': 'em_andamento',
                'prioridade': 'alta',
                'data_limite': today + timedelta(days=7),
            },
            {
                'titulo': 'Atualizar cliente sobre andamento',
                'descricao': 'Enviar comunicação ao cliente sobre o status atual do processo',
                'status': 'pendente',
                'prioridade': 'media',
                'data_limite': today + timedelta(days=3),
            },
        ]

        templates = task_templates.get(phase.name, default_tasks)

        for tmpl in templates:
            task = CaseTask.objects.create(caso=caso, **tmpl)
            tasks.append(task)

        return tasks
