"""
Management command para popular usuários de exemplo - ProdeRJ

Senhas padrão:
- Superadmin: Demonstração@@2026@@
- Demais usuários: Bravojus@2026#

Usage:
    python manage.py populate_users
    python manage.py populate_users --force  # Recria mesmo se existir
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

# Senhas padrão
SUPERADMIN_PASSWORD = 'Demonstração@@2026@@'
DEFAULT_PASSWORD = 'Bravojus@2026#'


class Command(BaseCommand):
    help = 'Popula banco com usuários de exemplo para ProdeRJ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recria usuários mesmo se já existirem (atualiza senha)',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        self.stdout.write('Criando usuários de exemplo...\n')

        users_data = [
            {
                'username': 'usuario_demo',
                'email': 'usuario_demo@bravonix.anon',
                'password': SUPERADMIN_PASSWORD,
                'first_name': 'Usuário',
                'last_name': 'Demonstração',
                'role': 'superadmin',
                'department': 'TI',
                'position': 'Usuário de Demonstração',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'gestor',
                'email': 'gestor@verus.ai',
                'password': DEFAULT_PASSWORD,
                'first_name': 'Carlos',
                'last_name': 'Silva',
                'role': 'manager',
                'department': 'Diretoria de Gestão',
                'position': 'Gestor de Contratos',
                'phone': '(21) 2333-4444',
            },
            {
                'username': 'analista1',
                'email': 'ana.santos@verus.ai',
                'password': DEFAULT_PASSWORD,
                'first_name': 'Ana',
                'last_name': 'Santos',
                'role': 'analyst',
                'department': 'Diretoria de Planejamento',
                'position': 'Analista de Licitações',
                'phone': '(21) 2333-5555',
            },
            {
                'username': 'analista2',
                'email': 'joao.oliveira@verus.ai',
                'password': DEFAULT_PASSWORD,
                'first_name': 'João',
                'last_name': 'Oliveira',
                'role': 'analyst',
                'department': 'Diretoria de TI',
                'position': 'Analista Técnico',
                'phone': '(21) 2333-6666',
            },
            {
                'username': 'revisor',
                'email': 'pedro.souza@verus.ai',
                'password': DEFAULT_PASSWORD,
                'first_name': 'Pedro',
                'last_name': 'Souza',
                'role': 'reviewer',
                'department': 'Diretoria de Planejamento',
                'position': 'Revisor de Documentos',
                'phone': '(21) 2333-7777',
            },
            {
                'username': 'visualizador',
                'email': 'maria.costa@verus.ai',
                'password': DEFAULT_PASSWORD,
                'first_name': 'Maria',
                'last_name': 'Costa',
                'role': 'viewer',
                'department': 'Controladoria',
                'position': 'Assistente',
            },
        ]

        created_count = 0
        updated_count = 0

        for user_data in users_data:
            username = user_data['username']
            password = user_data.pop('password')

            existing_user = User.objects.filter(username=username).first()

            if existing_user:
                if force:
                    # Atualiza senha e dados
                    existing_user.set_password(password)
                    for key, value in user_data.items():
                        if key != 'username':
                            setattr(existing_user, key, value)
                    existing_user.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Atualizado: {username}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⊘ Usuário {username} já existe. Use --force para atualizar.')
                    )
                continue

            # Cria novo usuário
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=password,
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                department=user_data.get('department', ''),
                position=user_data.get('position', ''),
                phone=user_data.get('phone', ''),
                is_staff=user_data.get('is_staff', False),
                is_superuser=user_data.get('is_superuser', False),
            )

            created_count += 1
            role_display = user.get_role_display() if hasattr(user, 'get_role_display') else user.role
            self.stdout.write(
                self.style.SUCCESS(f'✓ Criado: {user.username} ({role_display})')
            )

        self.stdout.write('')
        if created_count:
            self.stdout.write(
                self.style.SUCCESS(f'{created_count} usuários criados!')
            )
        if updated_count:
            self.stdout.write(
                self.style.SUCCESS(f'{updated_count} usuários atualizados!')
            )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.HTTP_INFO('CREDENCIAIS DE ACESSO:'))
        self.stdout.write('='*50)
        self.stdout.write(f'  usuario_demo / {SUPERADMIN_PASSWORD} (Super Administrador)')
        self.stdout.write(f'  gestor       / {DEFAULT_PASSWORD} (Gestor)')
        self.stdout.write(f'  analista1    / {DEFAULT_PASSWORD} (Analista)')
        self.stdout.write(f'  analista2    / {DEFAULT_PASSWORD} (Analista)')
        self.stdout.write(f'  revisor      / {DEFAULT_PASSWORD} (Revisor)')
        self.stdout.write(f'  visualizador / {DEFAULT_PASSWORD} (Visualizador)')
        self.stdout.write('='*50 + '\n')
