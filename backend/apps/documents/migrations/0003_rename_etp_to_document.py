# Generated manually for renaming ETP to Document

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0002_etp_numero_processo_etp_progress"),
    ]

    operations = [
        # Renomear modelo (renomeia a tabela automaticamente)
        migrations.RenameModel(
            old_name="ETP",
            new_name="Document",
        ),
    ]
