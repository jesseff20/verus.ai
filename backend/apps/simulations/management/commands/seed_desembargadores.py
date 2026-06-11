"""
Seed: popula desembargadores template para simulacao de 2a Instancia.
Idempotente -- usa get_or_create baseado em (court_type, name).

Cria 3 desembargadores por TJ principal (TJSP, TJRJ, TJMG).
Usa MinisterProfile com court_type='TJ'.
"""
from django.core.management.base import BaseCommand
from apps.simulations.models import MinisterProfile


DESEMBARGADORES = [
    # TJSP
    {
        'name': 'Des. Carlos Alberto Garbi',
        'full_name': 'Carlos Alberto Garbi',
        'court_type': 'TJ',
        'turma': 'TJSP - 10a Camara de Direito Privado',
        'judicial_philosophy': 'centrista',
        'specialty_areas': ['Direito Civil', 'Direito do Consumidor', 'Responsabilidade Civil'],
        'notable_positions': [
            'Relator de importantes casos de responsabilidade civil',
            'Especialista em contratos e obrigacoes',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e objetivo, com fundamentacao concisa e citacoes de precedentes',
            'tendencies': ['Seguranca juridica', 'Celeridade processual', 'Respeito ao pacta sunt servanda'],
            'key_framework': 'Proporcionalidade e razoabilidade na analise contratual',
        },
    },
    {
        'name': 'Des. Maria Helena de Oliveira',
        'full_name': 'Maria Helena de Oliveira',
        'court_type': 'TJ',
        'turma': 'TJSP - 10a Camara de Direito Privado',
        'judicial_philosophy': 'progressista',
        'specialty_areas': ['Direito do Consumidor', 'Direito de Familia', 'Direitos da Personalidade'],
        'notable_positions': [
            'Defensora dos direitos do consumidor',
            'Relatora de casos paradigmaticos em direito de familia',
        ],
        'profile_data': {
            'writing_style': 'Detalhado e didatico, com forte fundamentacao doutrinaria',
            'tendencies': ['Protecao do consumidor', 'Funcao social do contrato', 'Boa-fe objetiva'],
            'key_framework': 'Dignidade da pessoa humana e eficacia horizontal dos direitos fundamentais',
        },
    },
    {
        'name': 'Des. Roberto Nascimento Pereira',
        'full_name': 'Roberto Nascimento Pereira',
        'court_type': 'TJ',
        'turma': 'TJSP - 10a Camara de Direito Privado',
        'judicial_philosophy': 'conservador',
        'specialty_areas': ['Direito Empresarial', 'Direito Tributario', 'Direito Processual Civil'],
        'notable_positions': [
            'Especialista em direito empresarial e recuperacao judicial',
            'Defensor da legalidade estrita em materia tributaria',
        ],
        'profile_data': {
            'writing_style': 'Formal e processualista, com enfase em precedentes e sumulas',
            'tendencies': ['Legalidade estrita', 'Autonomia da vontade', 'Seguranca juridica'],
            'key_framework': 'Separacao de poderes e deferencia ao legislador',
        },
    },
    # TJRJ
    {
        'name': 'Des. Fernando Foch Lemos',
        'full_name': 'Fernando Foch de Lemos Arigony da Silva',
        'court_type': 'TJ',
        'turma': 'TJRJ - 7a Camara Civel',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': ['Direito Civil', 'Direito Imobiliario', 'Direito Administrativo'],
        'notable_positions': [
            'Especialista em direito imobiliario e urbanistico',
            'Relator de casos de desapropriacao',
        ],
        'profile_data': {
            'writing_style': 'Pragmatico e focado em resultados, com analise consequencialista',
            'tendencies': ['Pragmatismo decisorio', 'Eficiencia processual', 'Consequencialismo'],
            'key_framework': 'Analise de consequencias praticas das decisoes judiciais',
        },
    },
    {
        'name': 'Des. Claudia Pires dos Santos',
        'full_name': 'Claudia Pires dos Santos Ferreira',
        'court_type': 'TJ',
        'turma': 'TJRJ - 7a Camara Civel',
        'judicial_philosophy': 'progressista',
        'specialty_areas': ['Direito de Familia', 'Direitos Humanos', 'Direito da Crianca'],
        'notable_positions': [
            'Defensora dos direitos da crianca e do adolescente',
            'Relatora de importantes casos de guarda e alienacao parental',
        ],
        'profile_data': {
            'writing_style': 'Humanista e contextual, com forte apelo a justica social',
            'tendencies': ['Protecao de vulneraveis', 'Melhor interesse da crianca', 'Justica social'],
            'key_framework': 'Principio do melhor interesse da crianca e protecao integral',
        },
    },
    {
        'name': 'Des. Andre Gustavo Correa de Andrade',
        'full_name': 'Andre Gustavo Correa de Andrade',
        'court_type': 'TJ',
        'turma': 'TJRJ - 7a Camara Civel',
        'judicial_philosophy': 'centrista',
        'specialty_areas': ['Direito Civil', 'Responsabilidade Civil', 'Direito do Consumidor'],
        'notable_positions': [
            'Especialista em dano moral e responsabilidade civil',
            'Autor de obras sobre dano moral no direito brasileiro',
        ],
        'profile_data': {
            'writing_style': 'Equilibrado e doutrinario, com citacoes academicas frequentes',
            'tendencies': ['Equilibrio entre partes', 'Reparacao integral', 'Moderacao nos valores'],
            'key_framework': 'Teoria da reparacao integral do dano e funcao compensatoria',
        },
    },
    # TJMG
    {
        'name': 'Des. Marcos Henrique Caldeira Brant',
        'full_name': 'Marcos Henrique Caldeira Brant',
        'court_type': 'TJ',
        'turma': 'TJMG - 4a Camara Civel',
        'judicial_philosophy': 'conservador',
        'specialty_areas': ['Direito Civil', 'Direito Agrario', 'Direito das Sucessoes'],
        'notable_positions': [
            'Especialista em direito agrario e fundiario',
            'Relator de importantes casos de usucapiao e posse',
        ],
        'profile_data': {
            'writing_style': 'Classico e formal, com forte fundamentacao legal e doutrinaria',
            'tendencies': ['Protecao da propriedade', 'Legalidade', 'Tradicao juridica mineira'],
            'key_framework': 'Direito de propriedade e funcao social como limite excepcional',
        },
    },
    {
        'name': 'Des. Ana Paula Caixeta',
        'full_name': 'Ana Paula Gonzaga Caixeta',
        'court_type': 'TJ',
        'turma': 'TJMG - 4a Camara Civel',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': ['Direito do Consumidor', 'Direito Bancario', 'Direito Processual Civil'],
        'notable_positions': [
            'Especialista em revisao de contratos bancarios',
            'Relatora de casos de superendividamento',
        ],
        'profile_data': {
            'writing_style': 'Conciso e pratico, com enfase em resolucao efetiva de conflitos',
            'tendencies': ['Resolucao pratica', 'Equidade contratual', 'Protecao contra abusos'],
            'key_framework': 'Equilibrio contratual e vedacao ao enriquecimento sem causa',
        },
    },
    {
        'name': 'Des. Renato Dresch',
        'full_name': 'Renato Dresch',
        'court_type': 'TJ',
        'turma': 'TJMG - 4a Camara Civel',
        'judicial_philosophy': 'centrista',
        'specialty_areas': ['Direito Civil', 'Direito Empresarial', 'Recuperacao Judicial'],
        'notable_positions': [
            'Especialista em recuperacao judicial e falencia',
            'Palestrante em direito empresarial',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e equilibrado, com visao empresarial e social',
            'tendencies': ['Preservacao da empresa', 'Funcao social da empresa', 'Equilibrio de interesses'],
            'key_framework': 'Principio da preservacao da empresa e funcao social',
        },
    },
]


class Command(BaseCommand):
    help = 'Popula desembargadores template para simulacao de 2a Instancia (TJSP, TJRJ, TJMG).'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for data in DESEMBARGADORES:
            obj, created = MinisterProfile.objects.get_or_create(
                court_type=data['court_type'],
                name=data['name'],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  + {obj}'))
            else:
                for key, value in data.items():
                    setattr(obj, key, value)
                obj.save()
                updated_count += 1
                self.stdout.write(f'  = {obj} (atualizado)')

        self.stdout.write(self.style.SUCCESS(
            f'\nDesembargadores: {created_count} criados, {updated_count} atualizados.'
        ))
