"""
Migration: Add OABFeeTable model for honorarios reference table.
"""
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0009_add_legalnotification_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='OABFeeTable',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('state', models.CharField(
                    choices=[
                        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AM', 'Amazonas'), ('AP', 'Amapá'),
                        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
                        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MG', 'Minas Gerais'), ('MS', 'Mato Grosso do Sul'),
                        ('MT', 'Mato Grosso'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PE', 'Pernambuco'),
                        ('PI', 'Piauí'), ('PR', 'Paraná'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
                        ('RO', 'Rondônia'), ('RR', 'Roraima'), ('RS', 'Rio Grande do Sul'), ('SC', 'Santa Catarina'),
                        ('SE', 'Sergipe'), ('SP', 'São Paulo'), ('TO', 'Tocantins'),
                    ],
                    max_length=2, verbose_name='Estado (UF)',
                )),
                ('service_category', models.CharField(
                    choices=[
                        ('civel', 'Cível'), ('criminal', 'Criminal'), ('trabalhista', 'Trabalhista'),
                        ('tributario', 'Tributário'), ('familia', 'Família e Sucessões'),
                        ('previdenciario', 'Previdenciário'), ('administrativo', 'Administrativo'),
                        ('empresarial', 'Empresarial'), ('consumidor', 'Consumidor'),
                        ('imobiliario', 'Imobiliário'), ('ambiental', 'Ambiental'), ('outros', 'Outros'),
                    ],
                    max_length=20, verbose_name='Categoria',
                )),
                ('service_type', models.CharField(max_length=200, verbose_name='Tipo de Serviço')),
                ('minimum_value', models.DecimalField(
                    blank=True, decimal_places=2, max_digits=15, null=True,
                    verbose_name='Valor Mínimo (R$)',
                )),
                ('suggested_value', models.DecimalField(
                    blank=True, decimal_places=2, max_digits=15, null=True,
                    verbose_name='Valor Sugerido (R$)',
                )),
                ('percentage', models.DecimalField(
                    blank=True, decimal_places=2,
                    help_text='Percentual sobre o valor da causa, quando aplicável',
                    max_digits=5, null=True, verbose_name='Percentual (%)',
                )),
                ('year', models.IntegerField(default=2024, verbose_name='Ano de Referência')),
            ],
            options={
                'verbose_name': 'Tabela OAB de Honorários',
                'verbose_name_plural': 'Tabelas OAB de Honorários',
                'ordering': ['state', 'service_category', 'service_type'],
            },
        ),
        migrations.AddIndex(
            model_name='oabfeetable',
            index=models.Index(fields=['state', 'service_category'], name='cases_oabfe_state_6a1b2c_idx'),
        ),
        migrations.AddIndex(
            model_name='oabfeetable',
            index=models.Index(fields=['year'], name='cases_oabfe_year_3d4e5f_idx'),
        ),
    ]
