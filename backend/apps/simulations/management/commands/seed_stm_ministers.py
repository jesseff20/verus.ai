"""
Seed: popula os 15 ministros do STM (Superior Tribunal Militar) com dados template.

Composicao:
  - 5 civis (3 advogados + 1 juiz auditor + 1 membro do MPM)
  - 10 militares (3 Exercito + 4 Marinha + 3 Aeronautica)

Idempotente -- usa get_or_create baseado em (court_type, name).
"""
from django.core.management.base import BaseCommand
from apps.simulations.models import MinisterProfile


STM_MINISTERS = [
    # ── Ministros Civis (5) ──────────────────────────────────────────────
    {
        'name': 'Min. Carlos Eduardo Oliveira',
        'full_name': 'Carlos Eduardo de Souza Oliveira',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Penal Militar',
            'Direito Constitucional',
            'Direitos Humanos',
        ],
        'notable_positions': [
            'Ex-advogado militante em Direito Militar',
            'Defensor do devido processo legal na Justica Militar',
            'Membro da Comissao de Reforma do CPM',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e garantista, com forte fundamentacao constitucional',
            'tendencies': ['Garantismo penal', 'Devido processo legal', 'Proporcionalidade das penas'],
            'key_framework': 'Direitos fundamentais e controle de constitucionalidade',
            'category': 'Civil - Advogado',
            'origin': 'advocacia',
        },
    },
    {
        'name': 'Min. Patricia Ferreira Lima',
        'full_name': 'Patricia Ferreira Lima',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'progressista',
        'specialty_areas': [
            'Direito Penal',
            'Direito Processual Penal',
            'Direito Militar',
        ],
        'notable_positions': [
            'Ex-advogada criminalista',
            'Defensora da modernizacao do CPM',
            'Posicao favoravel a revisao de penas desproporcionais',
        ],
        'profile_data': {
            'writing_style': 'Didatico e acessivel, com preocupacao com direitos fundamentais',
            'tendencies': ['Modernizacao legislativa', 'Humanizacao da pena', 'Presuncao de inocencia'],
            'key_framework': 'Dignidade da pessoa humana e proporcionalidade',
            'category': 'Civil - Advogada',
            'origin': 'advocacia',
        },
    },
    {
        'name': 'Min. Roberto Mendes Alves',
        'full_name': 'Roberto Mendes Alves',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Direito Administrativo Militar',
            'Direito Penal Militar',
            'Processo Penal Militar',
        ],
        'notable_positions': [
            'Ex-advogado especializado em Direito Militar',
            'Autor de obras sobre o CPM',
            'Defensor da especificidade da Justica Militar',
        ],
        'profile_data': {
            'writing_style': 'Formal e tecnico, com enfase na especificidade do Direito Militar',
            'tendencies': ['Especificidade do Direito Militar', 'Tutela da hierarquia', 'Seguranca juridica'],
            'key_framework': 'Autonomia do Direito Penal Militar e tutela dos bens juridicos castrenses',
            'category': 'Civil - Advogado',
            'origin': 'advocacia',
        },
    },
    {
        'name': 'Min. Ana Claudia Santos',
        'full_name': 'Ana Claudia dos Santos',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Direito Penal Militar',
            'Direito Processual Penal Militar',
            'Execucao Penal Militar',
        ],
        'notable_positions': [
            'Ex-juiza auditora da Justica Militar',
            'Ampla experiencia em 1a instancia militar',
            'Defensora da celeridade processual',
        ],
        'profile_data': {
            'writing_style': 'Pragmatico e objetivo, com experiencia pratica de 1a instancia',
            'tendencies': ['Celeridade processual', 'Efetividade', 'Experiencia pratica'],
            'key_framework': 'Pragmatismo judicial e efetividade da Justica Militar',
            'category': 'Civil - Juiz Auditor',
            'origin': 'magistratura',
        },
    },
    {
        'name': 'Min. Marcos Paulo Ribeiro',
        'full_name': 'Marcos Paulo Ribeiro',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Direito Penal Militar',
            'Ministerio Publico Militar',
            'Investigacao Criminal Militar',
        ],
        'notable_positions': [
            'Ex-membro do Ministerio Publico Militar',
            'Atuacao em grandes casos de crimes militares',
            'Defensor da efetividade da persecucao penal militar',
        ],
        'profile_data': {
            'writing_style': 'Acusatorio e tecnico, com enfase na materialidade e autoria',
            'tendencies': ['Efetividade penal', 'Combate a impunidade', 'Protecao institucional'],
            'key_framework': 'Legalidade penal e tutela efetiva dos bens juridicos militares',
            'category': 'Civil - MPM',
            'origin': 'ministerio_publico',
        },
    },

    # ── Ministros Militares - Exercito (3) ───────────────────────────────
    {
        'name': 'Gen. Ex. Antonio Ferreira',
        'full_name': 'General de Exercito Antonio Carlos Ferreira',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Comando e Lideranca',
            'Disciplina Militar',
            'Operacoes Militares',
        ],
        'notable_positions': [
            'Ex-Comandante de Grande Unidade',
            'Experiencia em operacoes de GLO',
            'Defensor da hierarquia e disciplina',
        ],
        'profile_data': {
            'writing_style': 'Direto e objetivo, perspectiva de comando',
            'tendencies': ['Hierarquia e disciplina', 'Exemplo para a tropa', 'Rigor disciplinar'],
            'key_framework': 'Valores militares e coesao institucional',
            'category': 'Militar - Exercito',
            'forca': 'Exercito',
            'patente': 'General de Exercito',
        },
    },
    {
        'name': 'Gen. Div. Pedro Nascimento',
        'full_name': 'General de Divisao Pedro Henrique Nascimento',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Administracao Militar',
            'Gestao de Pessoal',
            'Direito Administrativo Militar',
        ],
        'notable_positions': [
            'Ex-Chefe de Estado-Maior',
            'Experiencia em gestao de pessoal militar',
            'Visao equilibrada entre disciplina e direitos',
        ],
        'profile_data': {
            'writing_style': 'Analitico e ponderado, busca equilibrio',
            'tendencies': ['Equilibrio', 'Justica', 'Proporcionalidade'],
            'key_framework': 'Proporcionalidade entre disciplina e direitos individuais',
            'category': 'Militar - Exercito',
            'forca': 'Exercito',
            'patente': 'General de Divisao',
        },
    },
    {
        'name': 'Gen. Bda. Luis Carvalho',
        'full_name': 'General de Brigada Luis Eduardo Carvalho',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Logistica Militar',
            'Inteligencia',
            'Operacoes Especiais',
        ],
        'notable_positions': [
            'Ex-Comandante de Brigada',
            'Experiencia em missoes de paz (ONU)',
            'Perspectiva internacional do Direito Militar',
        ],
        'profile_data': {
            'writing_style': 'Pragmatico e focado em resultados, perspectiva operacional',
            'tendencies': ['Pragmatismo', 'Contexto operacional', 'Experiencia internacional'],
            'key_framework': 'Analise contextual e impacto operacional',
            'category': 'Militar - Exercito',
            'forca': 'Exercito',
            'patente': 'General de Brigada',
        },
    },

    # ── Ministros Militares - Marinha (4) ────────────────────────────────
    {
        'name': 'Alm. Esq. Ricardo Costa',
        'full_name': 'Almirante de Esquadra Ricardo Souza Costa',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Direito Naval',
            'Disciplina Naval',
            'Operacoes Navais',
        ],
        'notable_positions': [
            'Ex-Comandante da Esquadra',
            'Defensor das tradicoes navais',
            'Rigoroso com disciplina a bordo',
        ],
        'profile_data': {
            'writing_style': 'Formal e tradicional, enfase nas tradicoes navais',
            'tendencies': ['Tradicao naval', 'Disciplina rigorosa', 'Honra militar'],
            'key_framework': 'Tradicoes navais e disciplina a bordo',
            'category': 'Militar - Marinha',
            'forca': 'Marinha',
            'patente': 'Almirante de Esquadra',
        },
    },
    {
        'name': 'V. Alm. Fernando Silva',
        'full_name': 'Vice-Almirante Fernando Augusto Silva',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Engenharia Naval',
            'Administracao Naval',
            'Logistica',
        ],
        'notable_positions': [
            'Ex-Diretor de Material da Marinha',
            'Experiencia em gestao de grandes projetos',
            'Visao tecnica e administrativa',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e analitico, com visao administrativa',
            'tendencies': ['Analise tecnica', 'Gestao eficiente', 'Modernizacao'],
            'key_framework': 'Eficiencia institucional e modernizacao',
            'category': 'Militar - Marinha',
            'forca': 'Marinha',
            'patente': 'Vice-Almirante',
        },
    },
    {
        'name': 'C. Alm. Marcos Pereira',
        'full_name': 'Contra-Almirante Marcos Andre Pereira',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Fuzileiros Navais',
            'Operacoes Anfibias',
            'Combate',
        ],
        'notable_positions': [
            'Ex-Comandante da Tropa de Fuzileiros',
            'Experiencia em combate urbano',
            'Perspectiva operacional de campo',
        ],
        'profile_data': {
            'writing_style': 'Direto e pragmatico, focado na realidade de campo',
            'tendencies': ['Realismo operacional', 'Experiencia de campo', 'Pragmatismo'],
            'key_framework': 'Contexto operacional e circunstancias de combate',
            'category': 'Militar - Marinha',
            'forca': 'Marinha',
            'patente': 'Contra-Almirante',
        },
    },
    {
        'name': 'C. Alm. Jose Tavares',
        'full_name': 'Contra-Almirante Jose Roberto Tavares',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Sistemas de Armas',
            'Defesa',
            'Estrategia Naval',
        ],
        'notable_positions': [
            'Ex-Diretor de Comunicacoes e TI da Marinha',
            'Experiencia em sistemas de defesa',
            'Defensor da modernizacao tecnologica',
        ],
        'profile_data': {
            'writing_style': 'Tecnico e estrategico, com visao de defesa nacional',
            'tendencies': ['Seguranca nacional', 'Defesa', 'Disciplina'],
            'key_framework': 'Seguranca nacional e prontidao militar',
            'category': 'Militar - Marinha',
            'forca': 'Marinha',
            'patente': 'Contra-Almirante',
        },
    },

    # ── Ministros Militares - Aeronautica (3) ────────────────────────────
    {
        'name': 'Ten. Brig. Ar Paulo Gomes',
        'full_name': 'Tenente-Brigadeiro do Ar Paulo Roberto Gomes',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'conservador',
        'specialty_areas': [
            'Aviacao Militar',
            'Disciplina Aeronautica',
            'Seguranca de Voo',
        ],
        'notable_positions': [
            'Ex-Comandante de Forca Aerea',
            'Piloto de caca com milhares de horas de voo',
            'Defensor da seguranca de voo e disciplina',
        ],
        'profile_data': {
            'writing_style': 'Objetivo e disciplinado, enfase em seguranca',
            'tendencies': ['Seguranca de voo', 'Disciplina aeronautica', 'Excelencia operacional'],
            'key_framework': 'Seguranca operacional e disciplina aeronautica',
            'category': 'Militar - Aeronautica',
            'forca': 'Aeronautica',
            'patente': 'Tenente-Brigadeiro do Ar',
        },
    },
    {
        'name': 'Maj. Brig. Ar Andre Santos',
        'full_name': 'Major-Brigadeiro do Ar Andre Luis Santos',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'centrista',
        'specialty_areas': [
            'Controle do Espaco Aereo',
            'Administracao Aeronautica',
            'Formacao Militar',
        ],
        'notable_positions': [
            'Ex-Diretor de Ensino da Aeronautica',
            'Experiencia em formacao de pilotos',
            'Visao educativa e formativa',
        ],
        'profile_data': {
            'writing_style': 'Ponderado e educativo, preocupado com formacao',
            'tendencies': ['Formacao', 'Educacao militar', 'Desenvolvimento profissional'],
            'key_framework': 'Formacao do militar e segunda chance',
            'category': 'Militar - Aeronautica',
            'forca': 'Aeronautica',
            'patente': 'Major-Brigadeiro do Ar',
        },
    },
    {
        'name': 'Brig. Ar Carlos Monteiro',
        'full_name': 'Brigadeiro do Ar Carlos Henrique Monteiro',
        'court_type': 'STM',
        'turma': 'Plenario',
        'judicial_philosophy': 'pragmatico',
        'specialty_areas': [
            'Inteligencia Aeronautica',
            'Operacoes Aereas',
            'Logistica Aeronautica',
        ],
        'notable_positions': [
            'Ex-Chefe do Centro de Inteligencia da Aeronautica',
            'Experiencia em operacoes combinadas',
            'Analise factual e investigativa',
        ],
        'profile_data': {
            'writing_style': 'Investigativo e analitico, busca fatos concretos',
            'tendencies': ['Analise factual', 'Investigacao', 'Evidencias concretas'],
            'key_framework': 'Fatos, evidencias e analise objetiva',
            'category': 'Militar - Aeronautica',
            'forca': 'Aeronautica',
            'patente': 'Brigadeiro do Ar',
        },
    },
]


class Command(BaseCommand):
    help = 'Popula os 15 ministros template do STM (5 civis + 10 militares).'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for minister_data in STM_MINISTERS:
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
            f'\nSTM Ministers: {created_count} criados, {updated_count} atualizados.'
        ))
