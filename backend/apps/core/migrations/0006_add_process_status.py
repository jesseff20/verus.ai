# Generated manually

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_populate_process_types"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcessStatus",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Identificador único (ex: planejamento, licitacao, concluido)",
                        max_length=50,
                        unique=True,
                        verbose_name="Código",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Nome completo (ex: Em Planejamento)",
                        max_length=150,
                        verbose_name="Nome",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Descrição do status",
                        verbose_name="Descrição",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("inicial", "Inicial"),
                            ("andamento", "Em Andamento"),
                            ("finalizado", "Finalizado"),
                            ("suspenso", "Suspenso/Cancelado"),
                        ],
                        default="andamento",
                        help_text="Categoria do status para agrupamento",
                        max_length=50,
                        verbose_name="Categoria",
                    ),
                ),
                (
                    "icon",
                    models.CharField(
                        default="Clock",
                        help_text="Nome do ícone Lucide (ex: Clock, Loader2, CheckCircle2)",
                        max_length=50,
                        verbose_name="Ícone",
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        default="bg-blue-100 text-blue-800",
                        help_text="Classes CSS para cor (ex: bg-blue-100 text-blue-800)",
                        max_length=50,
                        verbose_name="Cor",
                    ),
                ),
                (
                    "display_order",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Ordem de Exibição"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Se False, não aparece nas opções de seleção",
                        verbose_name="Ativo",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Se True, é o status inicial de novos processos",
                        verbose_name="Padrão",
                    ),
                ),
                (
                    "is_final",
                    models.BooleanField(
                        default=False,
                        help_text="Se True, indica que o processo foi finalizado",
                        verbose_name="Final",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
            ],
            options={
                "verbose_name": "Status de Processo",
                "verbose_name_plural": "Status de Processo",
                "ordering": ["display_order", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="processstatus",
            index=models.Index(fields=["code"], name="core_proces_code_7a1b2c_idx"),
        ),
        migrations.AddIndex(
            model_name="processstatus",
            index=models.Index(fields=["category"], name="core_proces_categor_8d3e4f_idx"),
        ),
        migrations.AddIndex(
            model_name="processstatus",
            index=models.Index(fields=["is_active"], name="core_proces_is_acti_9e5f6a_idx"),
        ),
    ]
