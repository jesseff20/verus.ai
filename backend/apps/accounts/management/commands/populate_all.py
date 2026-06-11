"""
Management command para popular todos os dados iniciais do Verus.AI.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados iniciais do Verus.AI'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('POPULANDO BANCO DE DADOS - Verus.AI'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        commands = [
            ('populate_users', 'Usuários'),
            ('seed_modules', 'Módulos do Sistema'),
            ('seed_document_types', 'Tipos de Documento Jurídico'),
            ('seed_legal_domain', 'Domínio Jurídico (especialidades e fontes)'),
            ('seed_legal_agents', 'Agentes Jurídicos'),
            ('seed_legal_blueprints', 'Blueprints Jurídicos'),
            ('seed_agent_tools', 'Ferramentas de Agentes'),
            ('seed_juridico_completo', 'Dados Jurídicos Completos'),
            ('seed_reminders', 'Lembretes de Exemplo'),
        ]

        for command_name, description in commands:
            self.stdout.write(f'\n{"-" * 60}')
            self.stdout.write(self.style.WARNING(f'[{description}]'))
            self.stdout.write(f'{"-" * 60}')

            try:
                call_command(command_name)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erro ao executar {command_name}: {str(e)}')
                )
                continue

        self.stdout.write(f'\n{"=" * 60}')
        self.stdout.write(self.style.SUCCESS('POPULAÇÃO CONCLUÍDA!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('\nVerus.AI configurado com sucesso!')
        self.stdout.write('\nPróximos passos:')
        self.stdout.write('  1. Acesse http://localhost:8000/admin/')
        self.stdout.write('  2. Acesse http://localhost:8000/api/docs/')
        self.stdout.write('  3. Login: admin / admin123')
