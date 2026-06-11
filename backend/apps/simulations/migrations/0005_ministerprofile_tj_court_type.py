"""Add TJ court_type choice to MinisterProfile."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulations', '0004_stf_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ministerprofile',
            name='court_type',
            field=models.CharField(
                choices=[('STF', 'STF'), ('STJ', 'STJ'), ('TJ', 'TJ/TRF')],
                max_length=10,
            ),
        ),
    ]
