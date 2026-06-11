import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0016_add_document_version'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='children',
                to='documents.document',
                verbose_name='Documento Original',
            ),
        ),
    ]
