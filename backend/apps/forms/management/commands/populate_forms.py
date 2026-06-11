"""
Management command para popular templates de formulários
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.forms.models import FormTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula banco com templates de formulários de exemplo'

    def handle(self, *args, **options):
        self.stdout.write('Criando templates de formulários...')

        # Buscar usuário admin para criar os templates
        try:
            admin_user = User.objects.filter(role__in=['superadmin', 'admin', 'gestor', 'manager']).first()
            if not admin_user:
                admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('Nenhum usuário admin encontrado. Execute populate_users primeiro.'))
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Nenhum usuário encontrado. Execute populate_users primeiro.'))
            return

        # Template ETP Completo
        etp_completo_fields = [
            {
                "id": "numero_processo",
                "type": "text",
                "label": "Número do Processo",
                "required": True,
                "placeholder": "Ex: 2024/001-SG",
                "help_text": "Número do processo administrativo"
            },
            {
                "id": "objeto",
                "type": "textarea",
                "label": "Objeto da Contratação",
                "required": True,
                "placeholder": "Descreva detalhadamente o objeto...",
                "help_text": "Descrição completa do objeto da contratação"
            },
            {
                "id": "justificativa",
                "type": "textarea",
                "label": "Justificativa da Contratação",
                "required": True,
                "help_text": "Justifique a necessidade da contratação"
            },
            {
                "id": "descricao_solucao",
                "type": "textarea",
                "label": "Descrição da Solução Proposta",
                "required": True,
                "help_text": "Descreva a solução que atenderá a necessidade"
            },
            {
                "id": "valor_estimado",
                "type": "number",
                "label": "Valor Estimado (R$)",
                "required": True,
                "validation": {"min": 0},
                "help_text": "Valor estimado da contratação em reais"
            },
            {
                "id": "prazo_execucao",
                "type": "number",
                "label": "Prazo de Execução (dias)",
                "required": True,
                "validation": {"min": 1},
                "help_text": "Prazo previsto para execução"
            },
            {
                "id": "modalidade",
                "type": "select",
                "label": "Modalidade de Licitação",
                "required": True,
                "options": [
                    "Pregão Eletrônico",
                    "Pregão Presencial",
                    "Concorrência",
                    "Dispensa",
                    "Inexigibilidade"
                ]
            },
            {
                "id": "criterio_julgamento",
                "type": "select",
                "label": "Critério de Julgamento",
                "required": True,
                "options": [
                    "Menor Preço",
                    "Melhor Técnica",
                    "Técnica e Preço",
                    "Maior Lance ou Oferta"
                ]
            },
            {
                "id": "requisitos_tecnicos",
                "type": "textarea",
                "label": "Requisitos Técnicos",
                "required": False,
                "help_text": "Liste os principais requisitos técnicos"
            },
            {
                "id": "criterios_sustentabilidade",
                "type": "textarea",
                "label": "Critérios de Sustentabilidade",
                "required": False,
                "help_text": "Critérios de sustentabilidade aplicáveis"
            },
            {
                "id": "analise_riscos",
                "type": "textarea",
                "label": "Análise de Riscos",
                "required": False,
                "help_text": "Principais riscos identificados"
            }
        ]

        # Template ETP Simplificado
        etp_simples_fields = [
            {
                "id": "objeto",
                "type": "textarea",
                "label": "Objeto da Contratação",
                "required": True,
                "placeholder": "Descreva o objeto..."
            },
            {
                "id": "justificativa",
                "type": "textarea",
                "label": "Justificativa",
                "required": True
            },
            {
                "id": "valor_estimado",
                "type": "number",
                "label": "Valor Estimado (R$)",
                "required": True,
                "validation": {"min": 0}
            },
            {
                "id": "prazo_execucao",
                "type": "number",
                "label": "Prazo de Execução (dias)",
                "required": True,
                "validation": {"min": 1}
            }
        ]

        # Template Parecer Técnico
        parecer_fields = [
            {
                "id": "numero_parecer",
                "type": "text",
                "label": "Número do Parecer",
                "required": True
            },
            {
                "id": "processo_referencia",
                "type": "text",
                "label": "Processo de Referência",
                "required": True
            },
            {
                "id": "assunto",
                "type": "text",
                "label": "Assunto",
                "required": True
            },
            {
                "id": "analise",
                "type": "textarea",
                "label": "Análise Técnica",
                "required": True,
                "help_text": "Análise detalhada do objeto"
            },
            {
                "id": "conclusao",
                "type": "textarea",
                "label": "Conclusão",
                "required": True
            },
            {
                "id": "parecer_favoravel",
                "type": "select",
                "label": "Parecer",
                "required": True,
                "options": ["Favorável", "Desfavorável", "Favorável com ressalvas"]
            }
        ]

        templates_data = [
            {
                'name': 'ETP Completo',
                'description': 'Template completo de Estudo Técnico Preliminar com todos os campos necessários',
                'fields': etp_completo_fields,
                'is_active': True,
            },
            {
                'name': 'ETP Simplificado',
                'description': 'Template simplificado de ETP para contratações de menor complexidade',
                'fields': etp_simples_fields,
                'is_active': True,
            },
            {
                'name': 'Parecer Técnico',
                'description': 'Template para elaboração de pareceres técnicos',
                'fields': parecer_fields,
                'is_active': True,
            },
        ]

        created_count = 0
        for template_data in templates_data:
            name = template_data['name']

            if FormTemplate.objects.filter(name=name).exists():
                self.stdout.write(
                    self.style.WARNING(f'Template "{name}" já existe. Pulando...')
                )
                continue

            template = FormTemplate.objects.create(
                name=template_data['name'],
                description=template_data['description'],
                fields=template_data['fields'],
                is_active=template_data['is_active'],
                created_by=admin_user,
            )

            created_count += 1
            field_count = len(template.fields)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Criado: {template.name} ({field_count} campos)'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n{created_count} templates de formulários criados com sucesso!')
        )
