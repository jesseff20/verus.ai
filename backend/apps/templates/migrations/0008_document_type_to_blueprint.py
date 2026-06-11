"""
Substitui FK document_type (core.DocumentType) por blueprint (intelligent_assistant.DocumentBlueprint)
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("intelligent_assistant", "0001_initial"),
        ("templates", "0007_rename_templates_do_documen_idx_templates_d_documen_90cec2_idx_and_more"),
    ]

    operations = [
        # 1. Remover constraint antiga (document_type)
        migrations.RemoveConstraint(
            model_name="documenttemplate",
            name="unique_default_per_document_type",
        ),
        # 2. Remover indexes antigos (document_type)
        migrations.RemoveIndex(
            model_name="documenttemplate",
            name="templates_d_documen_90cec2_idx",
        ),
        migrations.RemoveIndex(
            model_name="documenttemplate",
            name="templates_d_is_defa_6690cf_idx",
        ),
        # 3. Remover campo document_type
        migrations.RemoveField(
            model_name="documenttemplate",
            name="document_type",
        ),
        # 4. Adicionar FK blueprint
        migrations.AddField(
            model_name="documenttemplate",
            name="blueprint",
            field=models.ForeignKey(
                blank=True,
                help_text="Blueprint associado (ETP, DOD, etc.)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="document_templates",
                to="intelligent_assistant.documentblueprint",
                verbose_name="Blueprint",
            ),
        ),
        # 5. Adicionar novos indexes (blueprint)
        migrations.AddIndex(
            model_name="documenttemplate",
            index=models.Index(
                fields=["blueprint", "is_active"],
                name="templates_d_bluepri_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="documenttemplate",
            index=models.Index(
                fields=["is_default", "blueprint"],
                name="templates_d_is_defa_bp_idx",
            ),
        ),
        # 6. Adicionar nova constraint (blueprint)
        migrations.AddConstraint(
            model_name="documenttemplate",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_default=True),
                fields=("blueprint", "is_default"),
                name="unique_default_per_blueprint",
            ),
        ),
    ]
