# Generated manually — adiciona soft delete ao LegalCase

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0002_rename_cases_task_caso_status_idx_cases_caset_caso_id_249916_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='legalcase',
            name='deleted_at',
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text='Preenchido ao realizar soft delete do caso',
                null=True,
                verbose_name='Deletado em',
            ),
        ),
    ]
