"""
Seed: popula os 11 ministros do STF com dados reais.
Idempotente -- usa get_or_create baseado em (court_type, name).
"""
from datetime import date
from django.core.management.base import BaseCommand
from apps.simulations.models import MinisterProfile


STF_MINISTERS = [
    {
        'name': 'Luís Roberto Barroso',
        'full_name': 'Luís Roberto Barroso',
        'court_type': 'STF',
        'appointed_by': 'Dilma Rousseff',
        'appointment_date': date(2013, 6, 26),
        'turma': 'Presidente',
        'judicial_philosophy': 'progressista',
        'specialty_areas': [
            'Direito Constitucional',
            'Direitos Fundamentais',
            'Direito Administrativo',
            'Bioética',
        ],
        'notable_positions': [
            'Relator do casamento homoafetivo (ADPF 132)',
            'Relator da descriminalizacao do porte de drogas para uso pessoal',
            'Defensor da autonomia universitaria',
            'Presidente do STF desde 2023',
        ],
        'profile_data': {
            'writing_style': 'Academico e didatico, com referencias a doutrina internacional e direito comparado',
            'tendencies': ['Ativismo judicial moderado', 'Defesa de direitos individuais', 'Interpretacao evolutiva da Constituicao'],
            'key_framework': 'Ponderacao de principios e proporcionalidade (Alexy)',
        },
    },
    {
        'name': 'Edson Fachin',
        'full_name': 'Luiz Edson Fachin',
        'court_type': 'STF',
        'appointed_by': 'Dilma Rousseff',
        'appointment_date': date(2015, 6, 16),
        'turma': 'Vice-Presidente',
        'judicial_philosophy': 'progressista',
        'specialty_areas': [
            'Direito Civil',
            'Direito Agrario',
            'Direitos Humanos',
            'Direito Penal',
        ],
        'notable_positions': [
            'Relator da Lava Jato no STF',
            'Defensor da funcao social da propriedade',
            'Voto pela descriminalizacao do aborto ate 12 semanas',
            'Posicao firme contra impunidade em crimes de corrupcao',
        ],
        'profile_data': {
            'writing_style': 'Denso e tecnico, com forte fundamentacao doutrinaria civilista',
            'tendencies': ['Garantismo penal moderado', 'Funcao social dos direitos', 'Protecao de vulneraveis'],
            'key_framework': 'Constitucionalismo civil e eficacia horizontal dos direitos fundamentais',
        },
    },
    {
        'name': 'Gilmar Mendes',
        'full_name': 'Gilmar Ferreira Mendes',
        'court_type': 'STF',
        'appointed_by': 'Fernando Henrique Cardoso',
        'appointment_date': date(2002, 6, 20),
        'turma': '1a Turma',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Direito Constitucional',
            'Controle de Constitucionalidade',
            'Direito Eleitoral',
            'Direito Penal',
        ],
        'notable_positions': [
            'Defensor da presuncao de inocencia ate transito em julgado',
            'Critico do ativismo judicial excessivo',
            'Relator de importantes casos de controle concentrado',
            'Ex-presidente do STF (2008-2010)',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e erudito, com forte influencia do direito constitucional alemao',
            'tendencies': ['Deferencia ao legislador', 'Garantismo processual penal', 'Seguranca juridica'],
            'key_framework': 'Proporcionalidade alema e protecao de direitos fundamentais processuais',
        },
    },
    {
        'name': 'Cármen Lúcia',
        'full_name': 'Cármen Lúcia Antunes Rocha',
        'court_type': 'STF',
        'appointed_by': 'Lula',
        'appointment_date': date(2006, 6, 21),
        'turma': '1a Turma',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Constitucional',
            'Direito Administrativo',
            'Direitos Fundamentais',
            'Direito Eleitoral',
        ],
        'notable_positions': [
            'Primeira mulher presidente do STF (2016-2018)',
            'Relatora de importantes acoes de controle constitucional',
            'Defensora da transparencia e combate a corrupcao',
            'Voto pela execucao provisoria apos 2a instancia',
        ],
        'profile_data': {
            'writing_style': 'Elegante e conciso, com citacoes literarias e filosoficas',
            'tendencies': ['Equilibrio entre garantias e efetividade', 'Transparencia publica', 'Republicanismo'],
            'key_framework': 'Dignidade da pessoa humana como nucleo dos direitos fundamentais',
        },
    },
    {
        'name': 'Dias Toffoli',
        'full_name': 'José Antonio Dias Toffoli',
        'court_type': 'STF',
        'appointed_by': 'Lula',
        'appointment_date': date(2009, 10, 23),
        'turma': '1a Turma',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Direito Eleitoral',
            'Direito Constitucional',
            'Direito Administrativo',
            'Direito Tributario',
        ],
        'notable_positions': [
            'Ex-presidente do STF (2018-2020)',
            'Ex-advogado-geral da Uniao',
            'Defensor da estabilidade institucional',
            'Relator de importantes casos tributarios',
        ],
        'profile_data': {
            'writing_style': 'Pragmatico e institucional, focado em consequencias praticas das decisoes',
            'tendencies': ['Deferencia institucional', 'Pragmatismo decisorio', 'Estabilidade juridica'],
            'key_framework': 'Consequencialismo juridico e dialogo institucional',
        },
    },
    {
        'name': 'Alexandre de Moraes',
        'full_name': 'Alexandre de Moraes',
        'court_type': 'STF',
        'appointed_by': 'Michel Temer',
        'appointment_date': date(2017, 3, 22),
        'turma': '1a Turma',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Direito Constitucional',
            'Direito Penal',
            'Direito Eleitoral',
            'Seguranca Publica',
        ],
        'notable_positions': [
            'Relator do Inquerito das Fake News (INQ 4781)',
            'Ex-Ministro da Justica',
            'Presidente do TSE (2022)',
            'Atuacao firme contra desinformacao e ameacas a democracia',
        ],
        'profile_data': {
            'writing_style': 'Direto e assertivo, com enfase na defesa das instituicoes democraticas',
            'tendencies': ['Defesa da democracia', 'Combate a desinformacao', 'Poder de policia constitucional'],
            'key_framework': 'Democracia militante e protecao da ordem constitucional',
        },
    },
    {
        'name': 'Flávio Dino',
        'full_name': 'Flávio Dino de Castro e Costa',
        'court_type': 'STF',
        'appointed_by': 'Lula',
        'appointment_date': date(2024, 2, 22),
        'turma': '1a Turma',
        'judicial_philosophy': 'progressista',
        'specialty_areas': [
            'Direito Constitucional',
            'Direito Administrativo',
            'Direito Ambiental',
            'Direito Financeiro',
        ],
        'notable_positions': [
            'Ex-governador do Maranhao',
            'Ex-Ministro da Justica e Seguranca Publica',
            'Ex-juiz federal',
            'Atuacao firme no controle de emendas parlamentares (orcamento secreto)',
        ],
        'profile_data': {
            'writing_style': 'Didatico e acessivel, com preocupacao social e ambiental',
            'tendencies': ['Controle do orcamento publico', 'Transparencia fiscal', 'Protecao ambiental'],
            'key_framework': 'Constitucionalismo social e controle de politicas publicas',
        },
    },
    {
        'name': 'Nunes Marques',
        'full_name': 'Kassio Nunes Marques',
        'court_type': 'STF',
        'appointed_by': 'Jair Bolsonaro',
        'appointment_date': date(2020, 11, 5),
        'turma': '2a Turma',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Direito Administrativo',
            'Direito Previdenciario',
            'Direito Processual',
            'Direito Constitucional',
        ],
        'notable_positions': [
            'Primeiro ministro indicado por Bolsonaro',
            'Ex-desembargador do TRF-1',
            'Posicoes favoraveis a liberdade religiosa e de culto',
            'Tendencia a deferencia ao Poder Executivo',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e processualista, com enfase em precedentes e seguranca juridica',
            'tendencies': ['Deferencia ao Executivo', 'Liberdade religiosa', 'Autocontencao judicial'],
            'key_framework': 'Originalismo moderado e separacao de poderes',
        },
    },
    {
        'name': 'André Mendonça',
        'full_name': 'André Luiz de Almeida Mendonça',
        'court_type': 'STF',
        'appointed_by': 'Jair Bolsonaro',
        'appointment_date': date(2021, 12, 16),
        'turma': '2a Turma',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Direito Tributario',
            'Direito Constitucional',
            'Direito Administrativo',
            'Liberdade Religiosa',
        ],
        'notable_positions': [
            'Indicado como "terrivelmente evangelico" por Bolsonaro',
            'Ex-advogado-geral da Uniao',
            'Ex-Ministro da Justica',
            'Pastor presbiteriano, defensor da liberdade religiosa',
        ],
        'profile_data': {
            'writing_style': 'Tecnico com forte apego ao texto constitucional e valores conservadores',
            'tendencies': ['Liberdade religiosa', 'Interpretacao textualista', 'Valores tradicionais'],
            'key_framework': 'Textualismo constitucional e liberdade de consciencia',
        },
    },
    {
        'name': 'Luiz Fux',
        'full_name': 'Luiz Fux',
        'court_type': 'STF',
        'appointed_by': 'Dilma Rousseff',
        'appointment_date': date(2011, 3, 3),
        'turma': '2a Turma',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Processual Civil',
            'Direito Constitucional',
            'Direito Tributario',
            'Direito Administrativo',
        ],
        'notable_positions': [
            'Ex-presidente do STF (2020-2022)',
            'Relator da Lei da Ficha Limpa',
            'Especialista em Direito Processual Civil',
            'Defensor da celeridade processual e eficiencia jurisdicional',
        ],
        'profile_data': {
            'writing_style': 'Processualista rigoroso, com fundamentacao tecnica detalhada',
            'tendencies': ['Celeridade processual', 'Eficiencia jurisdicional', 'Combate a corrupcao'],
            'key_framework': 'Processo justo e efetivo, com respeito ao contraditorio',
        },
    },
    {
        'name': 'Cristiano Zanin',
        'full_name': 'Cristiano Zanin Martins',
        'court_type': 'STF',
        'appointed_by': 'Lula',
        'appointment_date': date(2023, 8, 3),
        'turma': '2a Turma',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Penal',
            'Direito Processual Penal',
            'Direito Constitucional',
            'Arbitragem Internacional',
        ],
        'notable_positions': [
            'Ex-advogado de Lula na Lava Jato',
            'Especialista em arbitragem internacional',
            'Defensor das garantias processuais penais',
            'Posicao cautelosa e tecnica em materias penais',
        ],
        'profile_data': {
            'writing_style': 'Cauteloso e tecnico, com forte enfase em garantias processuais',
            'tendencies': ['Garantismo penal', 'Due process', 'Arbitragem e comercio internacional'],
            'key_framework': 'Garantias processuais e presuncao de inocencia',
        },
    },
]


class Command(BaseCommand):
    help = 'Popula os 11 ministros atuais do STF com dados reais de perfil.'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for minister_data in STF_MINISTERS:
            obj, created = MinisterProfile.objects.get_or_create(
                court_type=minister_data['court_type'],
                name=minister_data['name'],
                defaults=minister_data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  + {obj}'))
            else:
                # Update existing
                for key, value in minister_data.items():
                    setattr(obj, key, value)
                obj.save()
                updated_count += 1
                self.stdout.write(f'  = {obj} (atualizado)')

        self.stdout.write(self.style.SUCCESS(
            f'\nSTF Ministers: {created_count} criados, {updated_count} atualizados.'
        ))
