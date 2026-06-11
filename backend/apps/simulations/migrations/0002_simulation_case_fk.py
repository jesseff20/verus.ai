"""
Add case FK to Simulation model.
Allows linking simulations to legal cases.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulations', '0001_initial'),
        ('cases', '0005_add_client_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulation',
            name='case',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='simulations',
                to='cases.legalcase',
                verbose_name='Caso Jurídico',
                help_text='Caso jurídico associado a esta simulação',
            ),
        ),
    ]
