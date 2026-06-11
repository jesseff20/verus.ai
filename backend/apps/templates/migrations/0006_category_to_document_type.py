import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("templates", "0005_add_form_template_to_document_template"),
    ]

    operations = [
        # 1. Remover constraint antiga
        migrations.RemoveConstraint(
            model_name="documenttemplate",
            name="unique_default_per_category",
        ),
        # 2. Remover indexes antigos (baseados em category)
        migrations.RemoveIndex(
            model_name="documenttemplate",
            name="templates_d_categor_80d1da_idx",
        ),
        migrations.RemoveIndex(
            model_name="documenttemplate",
            name="templates_d_is_defa_8002c2_idx",
        ),
        # 3. Remover campo category
        migrations.RemoveField(
            model_name="documenttemplate",
            name="category",
        ),
        # 4. Adicionar FK document_type
        migrations.AddField(
            model_name="documenttemplate",
            name="document_type",
            field=models.ForeignKey(
                blank=True,
                help_text="Tipo de documento associado (ETP, DOD, etc.)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="document_templates",
                to="core.documenttype",
                verbose_name="Tipo de Documento",
            ),
        ),
        # 5. Adicionar novos indexes
        migrations.AddIndex(
            model_name="documenttemplate",
            index=models.Index(
                fields=["document_type", "is_active"],
                name="templates_do_documen_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="documenttemplate",
            index=models.Index(
                fields=["is_default", "document_type"],
                name="templates_do_is_defa_dt_idx",
            ),
        ),
        # 6. Adicionar nova constraint
        migrations.AddConstraint(
            model_name="documenttemplate",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_default=True),
                fields=("document_type", "is_default"),
                name="unique_default_per_document_type",
            ),
        ),
    ]
