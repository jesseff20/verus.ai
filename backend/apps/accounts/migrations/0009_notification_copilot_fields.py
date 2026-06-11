"""
Migration: Adiciona campos de integração com Copilot ao Notification

- copilot_prompt: Prompt pré-preenchido para o Copilot
- action_type: Tipo de ação ao clicar (navigate, copilot, action)
- source: Origem da notificação (system, copilot, user, cron)
- metadata: Dados extras de contexto (JSONField)
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_user_lawyer_profile_fields'),
        ('accounts', '0005_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='copilot_prompt',
            field=models.TextField(
                blank=True, default='',
                help_text='Prompt pré-preenchido para o Copilot quando o usuário clicar',
                verbose_name='Prompt do Copilot',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='action_type',
            field=models.CharField(
                choices=[
                    ('navigate', 'Navegar'),
                    ('copilot', 'Abrir Copilot'),
                    ('action', 'Ação'),
                ],
                default='navigate',
                help_text='O que acontece quando o usuário clica na notificação',
                max_length=10,
                verbose_name='Tipo de Ação',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='source',
            field=models.CharField(
                choices=[
                    ('system', 'Sistema'),
                    ('copilot', 'Copilot'),
                    ('user', 'Usuário'),
                    ('cron', 'Tarefa Agendada'),
                ],
                default='system',
                help_text='Quem gerou a notificação',
                max_length=10,
                verbose_name='Origem',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='metadata',
            field=models.JSONField(
                blank=True, default=dict,
                help_text='Dados extras de contexto',
                verbose_name='Metadados',
            ),
        ),
    ]
