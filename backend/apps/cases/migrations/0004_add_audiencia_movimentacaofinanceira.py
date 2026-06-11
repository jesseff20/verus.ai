# Generated manually — adiciona Audiencia e MovimentacaoFinanceira

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0003_legalcase_deleted_at'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Audiencia',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo', models.CharField(
                    choices=[
                        ('instrucao', 'Audiência de Instrução'),
                        ('conciliacao', 'Audiência de Conciliação'),
                        ('julgamento', 'Sessão de Julgamento'),
                        ('depoimento', 'Depoimento Pessoal'),
                        ('pericial', 'Audiência Pericial'),
                        ('una', 'Audiência Una'),
                        ('outro', 'Outro'),
                    ],
                    default='instrucao',
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('agendada', 'Agendada'),
                        ('realizada', 'Realizada'),
                        ('cancelada', 'Cancelada'),
                        ('adiada', 'Adiada'),
                    ],
                    default='agendada',
                    max_length=20,
                )),
                ('data_hora', models.DateTimeField(verbose_name='Data e Hora')),
                ('local', models.CharField(blank=True, max_length=300, verbose_name='Local / Sala')),
                ('juiz', models.CharField(blank=True, max_length=200, verbose_name='Juiz')),
                ('resultado', models.TextField(blank=True, verbose_name='Resultado / Ata')),
                ('observacoes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('caso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='audiencias',
                    to='cases.legalcase',
                    verbose_name='Caso',
                )),
            ],
            options={
                'verbose_name': 'Audiência',
                'verbose_name_plural': 'Audiências',
                'ordering': ['data_hora'],
            },
        ),
        migrations.CreateModel(
            name='MovimentacaoFinanceira',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo', models.CharField(
                    choices=[
                        ('honorario', 'Honorário Recebido'),
                        ('despesa', 'Despesa'),
                        ('reembolso', 'Reembolso'),
                        ('custas', 'Custas Processuais'),
                        ('pericia', 'Perícia'),
                        ('outro', 'Outro'),
                    ],
                    default='honorario',
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('pendente', 'Pendente'),
                        ('pago', 'Pago'),
                        ('cancelado', 'Cancelado'),
                    ],
                    default='pendente',
                    max_length=20,
                )),
                ('descricao', models.CharField(max_length=300, verbose_name='Descrição')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Valor (R$)')),
                ('data_vencimento', models.DateField(blank=True, null=True, verbose_name='Data de Vencimento')),
                ('data_pagamento', models.DateField(blank=True, null=True, verbose_name='Data de Pagamento')),
                ('comprovante_url', models.URLField(blank=True, verbose_name='URL do Comprovante')),
                ('observacoes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('caso', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='movimentacoes_financeiras',
                    to='cases.legalcase',
                    verbose_name='Caso',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='movimentacoes_criadas',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Movimentação Financeira',
                'verbose_name_plural': 'Movimentações Financeiras',
                'ordering': ['-data_vencimento'],
            },
        ),
        migrations.AddIndex(
            model_name='audiencia',
            index=models.Index(fields=['caso', 'status'], name='cases_audie_caso_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='audiencia',
            index=models.Index(fields=['data_hora'], name='cases_audie_data_ho_idx'),
        ),
        migrations.AddIndex(
            model_name='movimentacaofinanceira',
            index=models.Index(fields=['caso', 'status'], name='cases_movim_caso_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='movimentacaofinanceira',
            index=models.Index(fields=['data_vencimento'], name='cases_movim_data_ve_idx'),
        ),
    ]
