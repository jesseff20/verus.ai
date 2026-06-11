"""
Migration: Adiciona campos de perfil de advogado ao User

- oab_number: Número de inscrição na OAB
- oab_state: Estado da seccional OAB
- lawyer_specialties: Especialidades jurídicas (JSONField)
- signature_image: Imagem de assinatura digitalizada
- signature_name: Nome como aparece na assinatura
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_expand_legal_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="oab_number",
            field=models.CharField(
                blank=True,
                help_text="Número de inscrição na OAB (ex: 123.456)",
                max_length=20,
                verbose_name="Número OAB",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="oab_state",
            field=models.CharField(
                blank=True,
                help_text="Estado da seccional (ex: SP, RJ)",
                max_length=2,
                verbose_name="Seccional OAB",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="lawyer_specialties",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Lista de especialidades jurídicas (ex: ["Trabalhista", "Civil"])',
                verbose_name="Especialidades",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="signature_image",
            field=models.ImageField(
                blank=True,
                help_text="Imagem da assinatura digitalizada",
                null=True,
                upload_to="signatures/",
                verbose_name="Imagem de Assinatura",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="signature_name",
            field=models.CharField(
                blank=True,
                help_text="Nome como aparece na assinatura de documentos",
                max_length=200,
                verbose_name="Nome na Assinatura",
            ),
        ),
    ]
