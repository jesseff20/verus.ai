"""
Management command para corrigir BrandSettings com dados do projeto anterior (contrata.ai).
Garante que o banco reflita a identidade Verus.AI.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Corrige BrandSettings para Verus.AI (remove referências a contrata.ai/BravoGov)'

    def handle(self, *args, **options):
        from apps.accounts.models import BrandSettings

        settings = BrandSettings.load()

        updates = {}

        # Garante identidade Verus.AI — sempre aplica os valores canônicos
        CANONICAL = {
            'system_name': 'Verus.AI',
            'system_tagline': 'Assistente Jurídico',
            'primary_color': '#7030A0',
            'secondary_color': '#5B2EE0',
            'accent_color': '#8B5CF6',
        }

        for field, expected in CANONICAL.items():
            current = getattr(settings, field, '')
            if current != expected:
                updates[field] = expected

        if updates:
            for key, value in updates.items():
                setattr(settings, key, value)
            settings.save()
            self.stdout.write(self.style.SUCCESS(f'BrandSettings atualizado: {updates}'))
        else:
            self.stdout.write('BrandSettings já está correto.')

        # ── CopilotConfig ────────────────────────────────────────────────
        try:
            from apps.copilot.models import CopilotConfig as CopilotCfg
            config = CopilotCfg.get_config()
            if 'contrata' in config.name.lower():
                old_name = config.name
                config.name = 'Copilot Verus.AI'
                config.save(update_fields=['name'])
                self.stdout.write(self.style.SUCCESS(
                    f'CopilotConfig.name atualizado: "{old_name}" → "Copilot Verus.AI"'
                ))
            else:
                self.stdout.write(f'CopilotConfig.name já está correto: "{config.name}"')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'CopilotConfig não pôde ser verificado: {e}'))
