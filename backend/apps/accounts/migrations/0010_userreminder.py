"""
Migration: Cria modelo UserReminder para lembretes e tarefas recorrentes do usuario.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_notification_copilot_fields'),
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300, verbose_name='Título')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('frequency', models.CharField(
                    choices=[
                        ('once', 'Uma vez'),
                        ('daily', 'Diário'),
                        ('weekly', 'Semanal'),
                        ('biweekly', 'Quinzenal'),
                        ('monthly', 'Mensal'),
                        ('quarterly', 'Trimestral'),
                        ('yearly', 'Anual'),
                        ('custom', 'Personalizado'),
                    ],
                    default='once',
                    max_length=20,
                    verbose_name='Frequência',
                )),
                ('scheduled_date', models.DateTimeField(verbose_name='Data agendada')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='Data de término')),
                ('custom_interval_days', models.IntegerField(blank=True, null=True, verbose_name='Intervalo personalizado (dias)')),
                ('copilot_prompt', models.TextField(blank=True, help_text='Prompt pré-preenchido para o Copilot quando o lembrete disparar', verbose_name='Prompt do Copilot')),
                ('link', models.CharField(blank=True, max_length=500, verbose_name='Link direto')),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Ativo'),
                        ('paused', 'Pausado'),
                        ('completed', 'Concluído'),
                        ('cancelled', 'Cancelado'),
                    ],
                    default='active',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('last_triggered', models.DateTimeField(blank=True, null=True, verbose_name='Último disparo')),
                ('trigger_count', models.IntegerField(default=0, verbose_name='Disparos')),
                ('notify_before_minutes', models.IntegerField(default=30, verbose_name='Notificar antes (minutos)')),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Baixa'),
                        ('medium', 'Média'),
                        ('high', 'Alta'),
                        ('urgent', 'Urgente'),
                    ],
                    default='medium',
                    max_length=10,
                    verbose_name='Prioridade',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminders',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
                ('related_case', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reminders',
                    to='cases.legalcase',
                    verbose_name='Caso relacionado',
                )),
            ],
            options={
                'verbose_name': 'Lembrete',
                'verbose_name_plural': 'Lembretes',
                'ordering': ['scheduled_date'],
            },
        ),
    ]
