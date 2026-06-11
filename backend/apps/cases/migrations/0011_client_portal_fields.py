"""
Add portal_password and portal_active fields to Client model.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0010_add_oabfeetable_model'),
        ('cases', '0010_legaldeadline_appeal_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='portal_password',
            field=models.CharField(
                blank=True,
                help_text='Senha hash para acesso ao portal do cliente',
                max_length=128,
                verbose_name='Senha do Portal',
            ),
        ),
        migrations.AddField(
            model_name='client',
            name='portal_active',
            field=models.BooleanField(
                default=False,
                help_text='Habilita acesso do cliente ao portal',
                verbose_name='Portal Ativo',
            ),
        ),
    ]
