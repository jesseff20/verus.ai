"""
Migration for Team and TeamAssignment models.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_dashboardconfig'),
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='Nome da Equipe')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('specialty', models.CharField(blank=True, max_length=50, verbose_name='Especialidade')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('leader', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teams_leading', to=settings.AUTH_USER_MODEL, verbose_name='Líder')),
                ('members', models.ManyToManyField(blank=True, related_name='teams', to=settings.AUTH_USER_MODEL, verbose_name='Membros')),
            ],
            options={
                'verbose_name': 'Equipe',
                'verbose_name_plural': 'Equipes',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TeamAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role_in_case', models.CharField(choices=[('responsavel', 'Responsável'), ('auxiliar', 'Auxiliar'), ('membro', 'Membro'), ('revisor', 'Revisor')], default='membro', max_length=50, verbose_name='Papel no Caso')),
                ('assigned_at', models.DateTimeField(auto_now_add=True, verbose_name='Atribuído em')),
                ('assigned_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Atribuído por')),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_assignments', to='cases.legalcase', verbose_name='Caso')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='accounts.team', verbose_name='Equipe')),
            ],
            options={
                'verbose_name': 'Atribuição de Equipe',
                'verbose_name_plural': 'Atribuições de Equipe',
                'unique_together': {('team', 'case')},
            },
        ),
    ]
