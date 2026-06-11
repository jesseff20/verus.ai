"""
Management command para criar módulos do Verus.AI.

Cria SystemModule para cada módulo do sistema, baseado no INSTALLED_APPS.
O frontend consulta esses módulos para saber o que exibir no sidebar.

Usage:
    python manage.py seed_modules
    python manage.py seed_modules --force  # Recria mesmo se existir
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.core.models import SystemModule


# Definição dos módulos do sistema
MODULES_DATA = [
    {
        'key': 'forms',
        'name': 'Formulários',
        'description': 'Gerenciamento de formulários dinâmicos',
        'icon': 'FileText',
        'route': '/dashboard/forms',
        'permission_codename': 'can_access_forms',
        'display_order': 1,
    },
    {
        'key': 'documents',
        'name': 'Documentos',
        'description': 'Gestão de documentos gerados',
        'icon': 'FileText',
        'route': '/dashboard/documents',
        'permission_codename': 'can_access_documents',
        'display_order': 2,
    },
    {
        'key': 'templates',
        'name': 'Templates',
        'description': 'Templates de documentos',
        'icon': 'Layout',
        'route': '/dashboard/templates',
        'permission_codename': 'can_access_templates',
        'display_order': 3,
    },
    {
        'key': 'kb',
        'name': 'Base de Conhecimento',
        'description': 'Gestão de base de conhecimento',
        'icon': 'Database',
        'route': '/dashboard/kb',
        'permission_codename': 'can_access_kb',
        'display_order': 4,
    },
    {
        'key': 'rag',
        'name': 'RAG',
        'description': 'Retrieval Augmented Generation',
        'icon': 'Search',
        'route': '/dashboard/rag',
        'permission_codename': 'can_access_rag',
        'display_order': 5,
    },
    {
        'key': 'intelligent_assistant',
        'name': 'Assistente Jurídico',
        'description': 'Geração de peças jurídicas com IA',
        'icon': 'Bot',
        'route': '/dashboard/intelligent-assistant',
        'permission_codename': 'can_access_intelligent_assistant',
        'display_order': 6,
    },
    {
        'key': 'jurisprudence',
        'name': 'Jurisprudência',
        'description': 'Pesquisa de jurisprudência e doutrina',
        'icon': 'Scale',
        'route': '/dashboard/jurisprudencia',
        'permission_codename': 'can_access_jurisprudence',
        'display_order': 7,
    },
    {
        'key': 'agents',
        'name': 'Agentes Jurídicos',
        'description': 'Agentes especializados em direito',
        'icon': 'MessageSquare',
        'route': '/dashboard/agents',
        'permission_codename': 'can_access_agents',
        'display_order': 8,
    },
    {
        'key': 'copilot',
        'name': 'Copiloto',
        'description': 'Assistente de IA para advogados',
        'icon': 'Sparkles',
        'route': '/dashboard/copilot',
        'permission_codename': 'can_access_copilot',
        'display_order': 9,
    },
]

class Command(BaseCommand):
    help = 'Cria módulos do sistema baseado no INSTALLED_APPS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recria módulos e grupos mesmo se já existirem',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        self.stdout.write('\n' + '='*60)
        self.stdout.write('SEED: Módulos do Sistema')
        self.stdout.write('='*60 + '\n')

        # Criar módulos
        self.stdout.write(self.style.HTTP_INFO('Criando módulos do sistema...\n'))
        self._create_modules(force)

        # Resumo
        self._print_summary()

    def _create_modules(self, force):
        """Cria ou atualiza módulos do sistema."""
        # Verificar quais apps estão em INSTALLED_APPS
        installed_apps = settings.INSTALLED_APPS

        for data in MODULES_DATA:
            key = data['key']
            app_name = f"apps.{key}"

            # Módulo ativo apenas se o app está instalado
            is_active = app_name in installed_apps

            module, created = SystemModule.objects.get_or_create(
                key=key,
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'icon': data['icon'],
                    'route': data['route'],
                    'permission_codename': data['permission_codename'],
                    'display_order': data['display_order'],
                    'is_active': is_active,
                }
            )

            if not created and force:
                # Atualiza se --force
                module.name = data['name']
                module.description = data['description']
                module.icon = data['icon']
                module.route = data['route']
                module.permission_codename = data['permission_codename']
                module.display_order = data['display_order']
                module.is_active = is_active
                module.save()

            status_icon = '✓' if created else ('↻' if force else '⊘')
            status_text = 'Criado' if created else ('Atualizado' if force else 'Já existe')
            active_text = '✓ Ativo' if is_active else '✗ Inativo'

            if is_active:
                self.stdout.write(f"  {status_icon} {module.name:<25} [{active_text}] - {status_text}")
            else:
                self.stdout.write(self.style.WARNING(f"  {status_icon} {module.name:<25} [{active_text}] - {status_text}"))

    def _print_summary(self):
        """Imprime resumo final."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMO'))
        self.stdout.write('='*60)

        # Módulos ativos
        active_modules = SystemModule.objects.filter(is_active=True)
        inactive_modules = SystemModule.objects.filter(is_active=False)

        self.stdout.write(f"\nMódulos ativos:   {active_modules.count()}")
        for m in active_modules:
            self.stdout.write(f"  • {m.name}")

        if inactive_modules.exists():
            self.stdout.write(f"\nMódulos inativos: {inactive_modules.count()}")
            for m in inactive_modules:
                self.stdout.write(self.style.WARNING(f"  • {m.name} (app não instalado)"))

        self.stdout.write('\n' + '='*60)
        self.stdout.write('Frontend consulta /api/settings/ para saber os módulos ativos.')
        self.stdout.write('='*60 + '\n')
