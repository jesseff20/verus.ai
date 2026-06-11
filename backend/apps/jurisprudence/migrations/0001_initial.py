import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JurisprudenceSearch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('query', models.TextField(verbose_name='Consulta')),
                ('specialty', models.CharField(
                    blank=True,
                    choices=[
                        ('CIV', 'Cível'), ('PEN', 'Penal'), ('TRB', 'Trabalhista'),
                        ('ADM', 'Administrativo'), ('CON', 'Constitucional'), ('TRI', 'Tributário'),
                        ('FAM', 'Família'), ('EMP', 'Empresarial'), ('AMB', 'Ambiental'),
                        ('OUT', 'Outros'),
                    ],
                    max_length=3,
                    null=True,
                    verbose_name='Especialidade',
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pendente'), ('processing', 'Processando'),
                        ('completed', 'Concluída'), ('failed', 'Falhou'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='jurisprudence_searches',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
            ],
            options={
                'verbose_name': 'Pesquisa de Jurisprudência',
                'verbose_name_plural': 'Pesquisas de Jurisprudência',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='JurisprudenceResult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tribunal', models.CharField(max_length=50, verbose_name='Tribunal')),
                ('case_number', models.CharField(blank=True, max_length=100, null=True, verbose_name='Número do processo')),
                ('relator', models.CharField(blank=True, max_length=200, null=True, verbose_name='Relator')),
                ('organ', models.CharField(blank=True, max_length=200, null=True, verbose_name='Órgão julgador')),
                ('summary', models.TextField(default='', verbose_name='Ementa/Resumo')),
                ('full_text_url', models.URLField(blank=True, max_length=500, null=True, verbose_name='URL do inteiro teor')),
                ('relevance_score', models.FloatField(default=0.0, verbose_name='Score de relevância')),
                ('judgment_date', models.DateTimeField(blank=True, null=True, verbose_name='Data do julgamento')),
                ('source', models.CharField(blank=True, max_length=100, verbose_name='Fonte')),
                ('content', models.JSONField(blank=True, default=dict, verbose_name='Dados brutos')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('search', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='results',
                    to='jurisprudence.jurisprudencesearch',
                    verbose_name='Pesquisa',
                )),
            ],
            options={
                'verbose_name': 'Resultado de Jurisprudência',
                'verbose_name_plural': 'Resultados de Jurisprudência',
                'ordering': ['-relevance_score', '-judgment_date'],
            },
        ),
    ]
