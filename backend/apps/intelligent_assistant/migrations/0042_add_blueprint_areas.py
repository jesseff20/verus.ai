"""
Migration: Adiciona campo areas (M2M) ao DocumentBlueprint.

Permite que cada blueprint seja classificado com múltiplas áreas jurídicas
(DocumentCategory), possibilitando filtragem no wizard do gerador.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_activate_watsonx_if_configured'),
        ('intelligent_assistant', '0041_add_case_fk_to_session'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentblueprint',
            name='areas',
            field=models.ManyToManyField(
                blank=True,
                help_text='Áreas do direito onde este blueprint pode ser utilizado (permite multi-seleção)',
                related_name='blueprints',
                to='core.documentcategory',
                verbose_name='Áreas Jurídicas',
            ),
        ),
    ]
