"""
Adiciona campo specialty ao modelo DocumentGenerator.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0018_restore_documentgenerator'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentgenerator',
            name='specialty',
            field=models.CharField(
                choices=[
                    ('geral', 'Geral (Todas as Especialidades)'),
                    ('civel', 'Direito Civil'),
                    ('penal', 'Direito Penal'),
                    ('trabalhista', 'Direito Trabalhista'),
                    ('tributario', 'Direito Tributário'),
                    ('previdenciario', 'Direito Previdenciário'),
                    ('administrativo', 'Direito Administrativo'),
                    ('constitucional', 'Direito Constitucional'),
                    ('empresarial', 'Direito Empresarial'),
                    ('consumidor', 'Direito do Consumidor'),
                    ('familia', 'Direito de Família e Sucessões'),
                    ('imobiliario', 'Direito Imobiliário'),
                    ('ambiental', 'Direito Ambiental'),
                    ('digital', 'Direito Digital e LGPD'),
                    ('saude', 'Direito da Saúde'),
                    ('eleitoral', 'Direito Eleitoral'),
                    ('internacional', 'Direito Internacional'),
                ],
                default='geral',
                help_text='Especialidade jurídica principal deste gerador',
                max_length=30,
                verbose_name='Especialidade',
            ),
        ),
    ]
