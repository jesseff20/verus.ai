"""
Seed dos Agent Tools disponíveis no Verus.AI.

Cria os tools padrão para agentes jurídicos.

Uso:
    python manage.py seed_agent_tools
"""
from django.core.management.base import BaseCommand

from apps.intelligent_assistant.models import AgentTool


class Command(BaseCommand):
    help = "Cria os Agent Tools padrão para agentes jurídicos"

    def handle(self, *args, **options):
        self.stdout.write("Criando Agent Tools...\n")

        tool1, created1 = AgentTool.objects.update_or_create(
            name='Web Search (Serper)',
            defaults={
                'tool_type': 'web_search',
                'description': 'Busca jurisprudência, legislação e doutrina jurídica no Google via Serper.dev.',
                'service_path': 'apps.intelligent_assistant.services.tools.web_search_tool.WebSearchTool',
                'method_name': 'execute',
                'default_config': {'max_results': 10},
                'is_active': True,
            },
        )
        self.stdout.write(f"  [{'+'if created1 else '~'}] {tool1.name}")

        tool2, created2 = AgentTool.objects.update_or_create(
            name='Busca Legislação Oficial',
            defaults={
                'tool_type': 'web_search',
                'description': (
                    'Busca legislação brasileira em fontes oficiais '
                    '(planalto.gov.br, STF, STJ, TST, CNJ). '
                    'Faz scraping de leis, súmulas e jurisprudência '
                    'quando a Knowledge Base local não é suficiente.'
                ),
                'service_path': 'apps.kb.legislation_search.LegislationSearchService',
                'method_name': 'search_all',
                'default_config': {
                    'base_urls': [
                        'planalto.gov.br',
                        'stf.jus.br',
                        'stj.jus.br',
                    ],
                    'max_results': 3,
                },
                'is_active': True,
            },
        )
        self.stdout.write(f"  [{'+'if created2 else '~'}] {tool2.name}")

        self.stdout.write(self.style.SUCCESS("\nAgent Tools criados com sucesso."))
