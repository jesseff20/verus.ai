"""
Seed: popula os 7 membros do TSE com dados de template.
Idempotente -- usa get_or_create baseado em (court_type, name).
"""
from django.core.management.base import BaseCommand
from apps.simulations.models import MinisterProfile


TSE_MEMBERS = [
    {
        'name': 'Min. Cármen Lúcia',
        'full_name': 'Cármen Lúcia Antunes Rocha',
        'court_type': 'TSE',
        'appointed_by': 'Composição STF',
        'turma': 'TSE',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Constitucional',
            'Direito Eleitoral',
            'Direitos Fundamentais',
        ],
        'notable_positions': [
            'Presidente do TSE (2012-2014)',
            'Relatora de importantes julgamentos eleitorais',
            'Defensora da transparencia eleitoral',
        ],
        'profile_data': {
            'writing_style': 'Elegante e conciso, com forte fundamentacao constitucional',
            'tendencies': ['Transparencia eleitoral', 'Moralidade publica', 'Protecao do voto'],
            'key_framework': 'Constituicao Federal e Codigo Eleitoral',
            'court_origin': 'STF',
        },
    },
    {
        'name': 'Min. Alexandre de Moraes',
        'full_name': 'Alexandre de Moraes',
        'court_type': 'TSE',
        'appointed_by': 'Composição STF',
        'turma': 'TSE',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Direito Constitucional',
            'Direito Eleitoral',
            'Seguranca Publica',
        ],
        'notable_positions': [
            'Presidente do TSE (2022)',
            'Combate a desinformacao eleitoral',
            'Atuacao firme na garantia da integridade das eleicoes',
        ],
        'profile_data': {
            'writing_style': 'Direto e assertivo, enfase na defesa das instituicoes democraticas',
            'tendencies': ['Combate a desinformacao', 'Integridade eleitoral', 'Democracia militante'],
            'key_framework': 'Democracia militante e protecao do processo eleitoral',
            'court_origin': 'STF',
        },
    },
    {
        'name': 'Min. Dias Toffoli',
        'full_name': 'José Antonio Dias Toffoli',
        'court_type': 'TSE',
        'appointed_by': 'Composição STF',
        'turma': 'TSE',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Direito Eleitoral',
            'Direito Constitucional',
            'Direito Administrativo',
        ],
        'notable_positions': [
            'Presidente do TSE (2014-2016)',
            'Ex-advogado-geral da Uniao',
            'Ampla experiencia em materia eleitoral',
        ],
        'profile_data': {
            'writing_style': 'Pragmatico e institucional, focado em consequencias praticas',
            'tendencies': ['Estabilidade institucional', 'Pragmatismo eleitoral', 'Seguranca juridica'],
            'key_framework': 'Consequencialismo juridico aplicado ao Direito Eleitoral',
            'court_origin': 'STF',
        },
    },
    {
        'name': 'Min. Isabel Gallotti',
        'full_name': 'Maria Isabel Gallotti Rodrigues',
        'court_type': 'TSE',
        'appointed_by': 'Composição STJ',
        'turma': 'TSE',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Civil',
            'Direito Eleitoral',
            'Direito Processual',
        ],
        'notable_positions': [
            'Ministra do STJ',
            'Atuacao equilibrada em materias eleitorais',
            'Experiencia em conflitos de competencia',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e equilibrado, com fundamentacao processual solida',
            'tendencies': ['Equidade processual', 'Legalidade estrita', 'Due process'],
            'key_framework': 'Legislacao infraconstitucional e Codigo Eleitoral',
            'court_origin': 'STJ',
        },
    },
    {
        'name': 'Min. Raul Araújo',
        'full_name': 'Raul Araújo Filho',
        'court_type': 'TSE',
        'appointed_by': 'Composição STJ',
        'turma': 'TSE',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Direito Civil',
            'Direito Eleitoral',
            'Direito do Consumidor',
        ],
        'notable_positions': [
            'Ministro do STJ',
            'Corregedor do TSE',
            'Posicoes firmes em materia de inelegibilidade',
        ],
        'profile_data': {
            'writing_style': 'Formal e legalista, com apego ao texto da lei',
            'tendencies': ['Legalismo estrito', 'Rigor na aplicacao da LC 64/90', 'Moralidade administrativa'],
            'key_framework': 'Lei Complementar 64/90 e Lei 9.504/97',
            'court_origin': 'STJ',
        },
    },
    {
        'name': 'Adv. André Ramos Tavares',
        'full_name': 'André Ramos Tavares',
        'court_type': 'TSE',
        'appointed_by': 'Presidente da República',
        'turma': 'TSE',
        'judicial_philosophy': 'progressista',
        'specialty_areas': [
            'Direito Constitucional',
            'Direito Eleitoral',
            'Direitos Humanos',
        ],
        'notable_positions': [
            'Professor de Direito Constitucional',
            'Advogado indicado pelo Presidente a partir de lista do STF',
            'Defensor da democratizacao do acesso ao poder',
        ],
        'profile_data': {
            'writing_style': 'Academico e didatico, com referencias a doutrina e direito comparado',
            'tendencies': ['Ampliacao de direitos politicos', 'Protecao de minorias', 'Interpretacao evolutiva'],
            'key_framework': 'Constitucionalismo democratico e direitos politicos fundamentais',
            'court_origin': 'Advogado',
        },
    },
    {
        'name': 'Adv. Floriano de Azevedo Marques',
        'full_name': 'Floriano de Azevedo Marques Neto',
        'court_type': 'TSE',
        'appointed_by': 'Presidente da República',
        'turma': 'TSE',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Administrativo',
            'Direito Eleitoral',
            'Regulacao',
        ],
        'notable_positions': [
            'Professor titular da USP',
            'Advogado indicado pelo Presidente a partir de lista do STF',
            'Especialista em regulacao e Direito Publico',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e doutrinario, com analise sistematica',
            'tendencies': ['Regulacao democratica', 'Eficiencia administrativa', 'Seguranca juridica'],
            'key_framework': 'Direito Administrativo aplicado ao processo eleitoral',
            'court_origin': 'Advogado',
        },
    },
]


class Command(BaseCommand):
    help = 'Popula os 7 membros do TSE com dados de template.'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for member_data in TSE_MEMBERS:
            obj, created = MinisterProfile.objects.get_or_create(
                court_type=member_data['court_type'],
                name=member_data['name'],
                defaults=member_data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  + {obj}'))
            else:
                for key, value in member_data.items():
                    setattr(obj, key, value)
                obj.save()
                updated_count += 1
                self.stdout.write(f'  = {obj} (atualizado)')

        self.stdout.write(self.style.SUCCESS(
            f'\nTSE Members: {created_count} criados, {updated_count} atualizados.'
        ))
