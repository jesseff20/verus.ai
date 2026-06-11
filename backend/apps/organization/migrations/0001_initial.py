import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Organ',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='Nome do Órgão')),
                ('short_name', models.CharField(max_length=30, verbose_name='Sigla')),
                ('organ_type', models.CharField(
                    choices=[
                        ('pgm', 'Procuradoria-Geral do Município'),
                        ('pge', 'Procuradoria-Geral do Estado'),
                        ('pgi', 'Procuradoria-Geral Instituto/Autarquia'),
                        ('other', 'Outro'),
                    ],
                    default='pgm', max_length=10, verbose_name='Tipo',
                )),
                ('cnpj', models.CharField(blank=True, max_length=18, verbose_name='CNPJ')),
                ('state', models.CharField(
                    choices=[
                        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
                        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'),
                        ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'),
                        ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
                        ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'),
                        ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
                        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'),
                        ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'),
                        ('TO', 'Tocantins'),
                    ],
                    max_length=2, verbose_name='Estado (UF)',
                )),
                ('city', models.CharField(max_length=100, verbose_name='Município')),
                ('address', models.CharField(blank=True, max_length=300, verbose_name='Endereço')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Telefone')),
                ('email', models.EmailField(blank=True, verbose_name='E-mail institucional')),
                ('website', models.URLField(blank=True, verbose_name='Site')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='organs/logos/', verbose_name='Logotipo')),
                ('settings', models.JSONField(blank=True, default=dict, verbose_name='Configurações')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Órgão',
                'verbose_name_plural': 'Órgãos',
                'ordering': ['state', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('organ', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='units',
                    to='organization.organ',
                    verbose_name='Órgão',
                )),
                ('name', models.CharField(max_length=200, verbose_name='Nome da Unidade')),
                ('short_name', models.CharField(blank=True, max_length=30, verbose_name='Sigla')),
                ('unit_type', models.CharField(
                    choices=[
                        ('judicial_1', 'Gerência Judicial — 1º Grau'),
                        ('judicial_2', 'Gerência Judicial — 2º Grau'),
                        ('administrative', 'Gerência Administrativa'),
                        ('gabinete', 'Gabinete da Procuradoria-Geral'),
                        ('general', 'Geral / Sem distinção'),
                        ('other', 'Outra'),
                    ],
                    default='general', max_length=20, verbose_name='Tipo',
                )),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Unidade',
                'verbose_name_plural': 'Unidades',
                'ordering': ['organ', 'name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='unit',
            unique_together={('organ', 'name')},
        ),
    ]
