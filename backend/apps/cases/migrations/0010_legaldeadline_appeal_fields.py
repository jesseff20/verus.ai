"""
Migration: adiciona campos appeal_type, base_legal e auto_generated ao LegalDeadline.
Feature #6 — Cálculo de Prazos Recursais.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0009_add_legalnotification_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='legaldeadline',
            name='appeal_type',
            field=models.CharField(
                blank=True,
                help_text='Chave do tipo de recurso (ex: apelacao, agravo_instrumento)',
                max_length=40,
                verbose_name='Tipo de Recurso',
            ),
        ),
        migrations.AddField(
            model_name='legaldeadline',
            name='base_legal',
            field=models.CharField(
                blank=True,
                help_text='Fundamentação legal do prazo (ex: CPC art. 1.003)',
                max_length=200,
                verbose_name='Base Legal',
            ),
        ),
        migrations.AddField(
            model_name='legaldeadline',
            name='auto_generated',
            field=models.BooleanField(
                default=False,
                help_text='Indica se o prazo foi criado automaticamente pelo sistema',
                verbose_name='Gerado Automaticamente',
            ),
        ),
    ]
