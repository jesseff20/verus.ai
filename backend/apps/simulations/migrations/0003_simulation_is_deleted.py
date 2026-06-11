from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulations', '0002_simulation_case_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulation',
            name='is_deleted',
            field=models.BooleanField(
                default=False,
                help_text='Soft delete flag',
            ),
        ),
        migrations.AlterField(
            model_name='simulation',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Rascunho'),
                    ('configuring', 'Configurando'),
                    ('running', 'Em Execução'),
                    ('deliberating', 'Deliberando'),
                    ('completed', 'Concluído'),
                    ('failed', 'Falhou'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
    ]
