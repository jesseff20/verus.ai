"""
Add MinisterProfile, CourtVote models and new simulation types (stf, acordao_2inst, stj).
"""
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('simulations', '0003_simulation_is_deleted'),
    ]

    operations = [
        # 1. Alter simulation_type choices
        migrations.AlterField(
            model_name='simulation',
            name='simulation_type',
            field=models.CharField(
                choices=[
                    ('jury', 'Simulação de Júri'),
                    ('judge', 'Simulação de Sentença'),
                    ('stf', 'Simulação STF'),
                    ('acordao_2inst', 'Acórdão 2a Instância'),
                    ('stj', 'Simulação STJ'),
                ],
                max_length=20,
            ),
        ),
        # 2. MinisterProfile
        migrations.CreateModel(
            name='MinisterProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('court_type', models.CharField(choices=[('STF', 'STF'), ('STJ', 'STJ')], max_length=10)),
                ('name', models.CharField(max_length=200)),
                ('full_name', models.CharField(blank=True, max_length=300)),
                ('appointed_by', models.CharField(blank=True, max_length=100)),
                ('appointment_date', models.DateField(blank=True, null=True)),
                ('turma', models.CharField(blank=True, max_length=50)),
                ('judicial_philosophy', models.CharField(
                    choices=[
                        ('progressista', 'Progressista'),
                        ('conservador', 'Conservador'),
                        ('centrista', 'Centrista'),
                        ('pragmatico', 'Pragmático'),
                    ],
                    default='centrista',
                    max_length=20,
                )),
                ('specialty_areas', models.JSONField(blank=True, default=list)),
                ('notable_positions', models.JSONField(blank=True, default=list)),
                ('profile_data', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['court_type', 'turma', 'name'],
                'verbose_name': 'Perfil de Ministro',
                'verbose_name_plural': 'Perfis de Ministros',
            },
        ),
        # 3. CourtVote
        migrations.CreateModel(
            name='CourtVote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('voter_name', models.CharField(max_length=200)),
                ('voter_role', models.CharField(default='ministro', max_length=20)),
                ('vote', models.CharField(max_length=30)),
                ('vote_text', models.TextField(blank=True)),
                ('is_relator', models.BooleanField(default=False)),
                ('is_dissent', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('minister_profile', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='simulations.ministerprofile',
                )),
                ('simulation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='court_votes',
                    to='simulations.simulation',
                )),
            ],
            options={
                'ordering': ['created_at'],
                'verbose_name': 'Voto de Ministro',
                'verbose_name_plural': 'Votos de Ministros',
            },
        ),
    ]
