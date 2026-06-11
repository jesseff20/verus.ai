"""
Migra todos os agentes de mistralai/mistral-medium-2505 para mistral-large-2512.

Uso em produção:
    python manage.py upgrade_to_mistral_large
    python manage.py upgrade_to_mistral_large --dry-run
"""
from django.core.management.base import BaseCommand
from apps.intelligent_assistant.models import SectionAgentConfig
from apps.core.models import LLMModel, LLMProvider


OLD_MODEL = 'mistralai/mistral-medium-2505'
NEW_MODEL = 'mistral-large-2512'


class Command(BaseCommand):
    help = 'Migra agentes de mistral-medium-2505 para mistral-large-2512'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Apenas mostra o que seria feito')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # 1. Garantir que mistral-large-2512 existe na tabela LLMModel
        provider = LLMProvider.objects.filter(code='watsonx').first()
        if not provider:
            self.stderr.write('Provider watsonx nao encontrado no banco.')
            return

        model, created = LLMModel.objects.get_or_create(
            provider=provider,
            model_id=NEW_MODEL,
            defaults={
                'display_name': 'Mistral Large',
                'description': 'Mistral Large 2512 via IBM watsonx',
                'max_tokens_limit': 4096,
                'default_temperature': 0.7,
                'display_order': 0,
                'is_active': True,
            },
        )
        if created:
            self.stdout.write(f'[+] LLMModel criado: {NEW_MODEL}')
        else:
            self.stdout.write(f'[=] LLMModel ja existe: {NEW_MODEL}')

        # 2. Contar agentes com modelo antigo
        agents = SectionAgentConfig.objects.filter(model_name=OLD_MODEL)
        count = agents.count()
        self.stdout.write(f'\nAgentes com {OLD_MODEL}: {count}')

        if count == 0:
            self.stdout.write('Nenhum agente para atualizar.')
            return

        if dry_run:
            self.stdout.write(f'[dry-run] {count} agentes SERIAM atualizados para {NEW_MODEL}')
            for a in agents[:10]:
                self.stdout.write(f'  - {a.name}')
            if count > 10:
                self.stdout.write(f'  ... e mais {count - 10}')
            return

        # 3. Atualizar
        updated = agents.update(model_name=NEW_MODEL)
        self.stdout.write(self.style.SUCCESS(f'\n{updated} agentes atualizados para {NEW_MODEL}'))

        # 4. Verificar
        remaining = SectionAgentConfig.objects.filter(model_name=OLD_MODEL).count()
        if remaining:
            self.stderr.write(f'AVISO: {remaining} agentes ainda com modelo antigo!')
        else:
            self.stdout.write(self.style.SUCCESS('Todos os agentes migrados com sucesso.'))
