"""
Migration: add_case_fk_to_session

Adds FK 'case' to IntelligentSession pointing to cases.LegalCase.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0002_rename_cases_task_caso_status_idx_cases_caset_caso_id_249916_idx_and_more'),
        ('intelligent_assistant', '0040_add_audit_fields_and_generation_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='intelligentsession',
            name='case',
            field=models.ForeignKey(
                blank=True,
                help_text='Caso jurídico associado a esta sessão de geração de documento',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='intelligent_sessions',
                to='cases.legalcase',
                verbose_name='Caso Jurídico',
            ),
        ),
    ]
