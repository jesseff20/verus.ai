"""
Seed: popula ministros do TST com perfis de especializacao trabalhista.
Idempotente -- usa get_or_create baseado em (court_type, name).
"""
from django.core.management.base import BaseCommand
from apps.simulations.models import MinisterProfile


TST_MINISTERS = [
    {
        'name': 'Min. Lelio Bentes Correa',
        'full_name': 'Lelio Bentes Correa',
        'court_type': 'TST',
        'turma': '1a Turma',
        'judicial_philosophy': 'progressista',
        'specialty_areas': [
            'Direito Individual do Trabalho',
            'Direito Internacional do Trabalho',
            'Trabalho Escravo',
            'Direitos Humanos',
        ],
        'notable_positions': [
            'Membro do Comite de Peritos da OIT',
            'Relator de casos emblematicos sobre trabalho escravo',
            'Defensor dos principios fundamentais do trabalho',
            'Posicao firme pela protecao do trabalhador',
        ],
        'profile_data': {
            'writing_style': 'Didatico e protecionista, com forte fundamentacao em convencoes da OIT',
            'tendencies': ['Principio protetor', 'Irrenunciabilidade de direitos', 'Dignidade do trabalhador'],
            'key_framework': 'Principio da protecao e normatividade internacional do trabalho',
        },
    },
    {
        'name': 'Min. Augusto Cesar de Carvalho',
        'full_name': 'Augusto Cesar Leite de Carvalho',
        'court_type': 'TST',
        'turma': '1a Turma',
        'judicial_philosophy': 'progressista',
        'specialty_areas': [
            'Direito Coletivo do Trabalho',
            'Direito Sindical',
            'Greve',
            'Negociacao Coletiva',
        ],
        'notable_positions': [
            'Especialista em direito coletivo do trabalho',
            'Defensor do direito de greve',
            'Relator de dissidios coletivos importantes',
        ],
        'profile_data': {
            'writing_style': 'Detalhado e doutrinario, com enfase nos direitos coletivos',
            'tendencies': ['Valorizacao sindical', 'Direito de greve', 'Negociacao coletiva equilibrada'],
            'key_framework': 'Autonomia coletiva e funcao social do sindicato',
        },
    },
    {
        'name': 'Min. Hugo Carlos Scheuermann',
        'full_name': 'Hugo Carlos Scheuermann',
        'court_type': 'TST',
        'turma': '1a Turma',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Processual do Trabalho',
            'Execucao Trabalhista',
            'Recursos',
            'Admissibilidade Recursal',
        ],
        'notable_positions': [
            'Especialista em admissibilidade recursal',
            'Relator de recursos repetitivos',
            'Enfase na celeridade processual',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e processualista, com rigor na admissibilidade recursal',
            'tendencies': ['Celeridade processual', 'Rigor tecnico', 'Seguranca juridica'],
            'key_framework': 'Instrumentalidade do processo e efetividade da jurisdicao',
        },
    },
    {
        'name': 'Min. Amaury Rodrigues Pinto Junior',
        'full_name': 'Amaury Rodrigues Pinto Junior',
        'court_type': 'TST',
        'turma': '1a Turma',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Direito Individual do Trabalho',
            'Reforma Trabalhista',
            'Terceirizacao',
            'Contrato de Trabalho',
        ],
        'notable_positions': [
            'Aplicacao da Reforma Trabalhista (Lei 13.467/2017)',
            'Posicoes sobre terceirizacao e pejotizacao',
            'Enfase na modernizacao das relacoes de trabalho',
        ],
        'profile_data': {
            'writing_style': 'Formal e legalista, com enfase na literalidade da lei',
            'tendencies': ['Prevalencia do negociado', 'Reforma trabalhista', 'Modernizacao'],
            'key_framework': 'Autonomia da vontade e seguranca juridica empresarial',
        },
    },
    {
        'name': 'Min. Sergio Pinto Martins',
        'full_name': 'Sergio Pinto Martins',
        'court_type': 'TST',
        'turma': '1a Turma',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Direito do Trabalho',
            'Direito Previdenciario',
            'Doutrina Trabalhista',
            'Verbas Rescisorias',
        ],
        'notable_positions': [
            'Autor de obras doutrinarias de referencia em Direito do Trabalho',
            'Posicoes pragmaticas sobre calculo de verbas',
            'Enfase na aplicacao pratica da lei',
        ],
        'profile_data': {
            'writing_style': 'Pragmatico e doutrinario, com citacoes de doutrina propria e alheia',
            'tendencies': ['Aplicacao pratica da CLT', 'Doutrina como fonte', 'Equilibrio'],
            'key_framework': 'Sistematizacao doutrinaria e aplicacao coerente da CLT',
        },
    },
]


class Command(BaseCommand):
    help = 'Popula ministros do TST com perfis de especializacao trabalhista.'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for minister_data in TST_MINISTERS:
            obj, created = MinisterProfile.objects.get_or_create(
                court_type=minister_data['court_type'],
                name=minister_data['name'],
                defaults=minister_data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  + {obj}'))
            else:
                for key, value in minister_data.items():
                    setattr(obj, key, value)
                obj.save()
                updated_count += 1
                self.stdout.write(f'  = {obj} (atualizado)')

        self.stdout.write(self.style.SUCCESS(
            f'\nTST Ministers: {created_count} criados, {updated_count} atualizados.'
        ))
