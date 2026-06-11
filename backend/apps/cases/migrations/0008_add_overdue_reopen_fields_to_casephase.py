"""
Add overdue detection, reopening capability, and justification fields to CasePhase.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0007_add_casephase_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casephase',
            name='status',
            field=models.CharField(
                choices=[
                    ('completed', 'Concluída'),
                    ('in_progress', 'Em Andamento'),
                    ('pending', 'Pendente'),
                    ('skipped', 'Não Aplicável'),
                    ('overdue', 'Atrasada'),
                ],
                default='pending',
                max_length=20,
                verbose_name='Status',
            ),
        ),
        migrations.AddField(
            model_name='casephase',
            name='reopened_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Reaberta em'),
        ),
        migrations.AddField(
            model_name='casephase',
            name='reopened_reason',
            field=models.TextField(blank=True, default='', verbose_name='Motivo da Reabertura'),
        ),
        migrations.AddField(
            model_name='casephase',
            name='overdue_since',
            field=models.DateField(blank=True, null=True, verbose_name='Atrasada desde'),
        ),
    ]
