"""
Procuradoria terminology — rename verbose labels:
- LegalCase.advogado_responsavel verbose_name → 'Procurador Responsável'
- TimeEntry.billing_type choices → Portuguese public-sector labels
"""
from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0021_legalcase_organ_active_flow'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Rename verbose_name for advogado_responsavel FK
        migrations.AlterField(
            model_name='legalcase',
            name='advogado_responsavel',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='casos_responsavel',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Procurador Responsável',
            ),
        ),
        # Update billing_type choices to public-sector labels
        migrations.AlterField(
            model_name='timeentry',
            name='billing_type',
            field=models.CharField(
                choices=[
                    ('billable', 'Atividade Produtiva'),
                    ('non_billable', 'Atividade Administrativa'),
                    ('pro_bono', 'Capacitação / Formação'),
                ],
                default='billable',
                max_length=15,
            ),
        ),
    ]
