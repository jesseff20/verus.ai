"""
Fix Notification.action_type max_length: 10 → 20 to accommodate 'action_required'.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_clientmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='action_type',
            field=models.CharField(
                choices=[
                    ('navigate', 'Navegar'),
                    ('copilot', 'Abrir Copilot'),
                    ('action', 'Ação'),
                    ('info', 'Informativo'),
                    ('action_required', 'Ação Necessária'),
                ],
                default='navigate',
                help_text='O que acontece quando o usuário clica na notificação',
                max_length=20,
                verbose_name='Tipo de Ação',
            ),
        ),
    ]
