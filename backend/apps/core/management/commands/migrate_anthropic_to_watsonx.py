"""
Management command para migrar registros com provider 'anthropic' para 'watsonx'.

Após adicionar 'anthropic' de volta às choices (backwards compatibility),
este comando atualiza todos os registros existentes para usar 'watsonx',
permitindo que a remoção futura de 'anthropic' das choices seja segura.

Uso:
    python manage.py migrate_anthropic_to_watsonx
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Migra todos os registros com llm_provider/provider "anthropic" '
        'para "watsonx" e atualiza model_name quando aplicável.'
    )

    DEFAULT_WATSONX_MODEL = 'mistralai/mistral-medium-2505'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            'Migrando registros anthropic → watsonx...'
        ))

        total = 0

        # 1. SectionAgentConfig
        total += self._migrate_model(
            'intelligent_assistant', 'SectionAgentConfig',
            provider_field='llm_provider',
            update_model_name=True,
        )

        # 2. AgentPrompt
        total += self._migrate_model(
            'agents', 'AgentPrompt',
            provider_field='llm_provider',
            update_model_name=True,
        )

        # 3. DocumentGenerator
        total += self._migrate_model(
            'documents', 'DocumentGenerator',
            provider_field='llm_provider',
            update_model_name=True,
        )

        # 4. FormAssistant
        total += self._migrate_model(
            'forms', 'FormAssistant',
            provider_field='llm_provider',
            update_model_name=True,
        )

        # 5. CopilotConfig
        total += self._migrate_model(
            'copilot', 'CopilotConfig',
            provider_field='provider',
            update_model_name=False,
        )

        # 6. User (preferred_llm_provider)
        total += self._migrate_model(
            'accounts', 'User',
            provider_field='preferred_llm_provider',
            update_model_name=False,
        )

        # 7. TokenUsageLog
        total += self._migrate_model(
            'core', 'TokenUsageLog',
            provider_field='model_provider',
            update_model_name=False,
        )

        self.stdout.write('')
        if total:
            self.stdout.write(self.style.SUCCESS(
                f'Concluido! {total} registro(s) migrado(s) no total.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                'Nenhum registro com anthropic encontrado. Nada a fazer.'
            ))

    # ------------------------------------------------------------------ #

    def _migrate_model(
        self,
        app_label: str,
        model_name: str,
        provider_field: str,
        update_model_name: bool,
    ) -> int:
        """
        Atualiza registros de um modelo específico.
        Retorna a quantidade de registros atualizados.
        """
        from django.apps import apps

        Model = apps.get_model(app_label, model_name)
        qs = Model.objects.filter(**{provider_field: 'anthropic'})
        count = qs.count()

        if count == 0:
            self.stdout.write(f'  {app_label}.{model_name}: 0 registros (nenhum anthropic)')
            return 0

        update_fields = {provider_field: 'watsonx'}
        if update_model_name:
            update_fields['model_name'] = self.DEFAULT_WATSONX_MODEL

        updated = qs.update(**update_fields)
        self.stdout.write(self.style.WARNING(
            f'  {app_label}.{model_name}: {updated} registro(s) migrado(s)'
        ))
        return updated
