"""
Migration: Adiciona watsonx como provider e dependências entre seções.

- AlterField: SectionAgentConfig.llm_provider (novo choice watsonx)
- AddField: BlueprintSection.depends_on (M2M self)
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intelligent_assistant', '0019_make_uploaded_document_file_optional'),
    ]

    operations = [
        # 1. Atualizar choices do llm_provider para incluir watsonx
        migrations.AlterField(
            model_name='sectionagentconfig',
            name='llm_provider',
            field=models.CharField(
                choices=[
                    ('anthropic', 'Anthropic (Claude)'),
                    ('openai', 'OpenAI (GPT)'),
                    ('watsonx', 'IBM watsonx.ai'),
                ],
                default='anthropic',
                max_length=20,
                verbose_name='Provedor LLM',
            ),
        ),

        # 2. Adicionar M2M depends_on no BlueprintSection
        migrations.AddField(
            model_name='blueprintsection',
            name='depends_on',
            field=models.ManyToManyField(
                blank=True,
                help_text='Seções que devem ser concluídas antes desta',
                related_name='required_by',
                to='intelligent_assistant.blueprintsection',
                verbose_name='Depende de',
            ),
        ),
    ]
