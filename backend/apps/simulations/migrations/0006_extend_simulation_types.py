"""Extend SIMULATION_TYPES and MinisterProfile.court_type with new choices."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulations', '0005_ministerprofile_tj_court_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simulation',
            name='simulation_type',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('jury', 'Simulação de Júri'),
                    ('judge', 'Simulação de Sentença'),
                    ('stf', 'Simulação STF'),
                    ('acordao_2inst', 'Acórdão 2a Instância'),
                    ('stj', 'Simulação STJ'),
                    ('jec', 'Juizado Especial Cível'),
                    ('jecrim', 'Juizado Especial Criminal'),
                    ('jef', 'Juizado Especial Federal'),
                    ('turma_recursal', 'Turma Recursal'),
                    ('trabalho', 'Vara do Trabalho'),
                    ('trt', 'TRT'),
                    ('tst', 'TST'),
                    ('eleitoral', 'Justiça Eleitoral'),
                    ('tre', 'TRE'),
                    ('tse', 'TSE'),
                    ('militar', 'Justiça Militar'),
                    ('stm', 'STM'),
                ],
            ),
        ),
        migrations.AlterField(
            model_name='ministerprofile',
            name='court_type',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('STF', 'STF'),
                    ('STJ', 'STJ'),
                    ('TJ', 'TJ/TRF'),
                    ('TRT', 'TRT'),
                    ('TST', 'TST'),
                    ('TSE', 'TSE'),
                    ('STM', 'STM'),
                    ('TRE', 'TRE'),
                ],
            ),
        ),
    ]
