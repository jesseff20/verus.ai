"""
Fase 4 — Vincula LegalCase ao órgão (multi-tenancy) e ao FlowInstance ativo.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0020_client_unique_cpf_cnpj_constraint'),
        ('organization', '0001_initial'),
        ('workflow_execution', '0001_initial'),
    ]

    operations = [
        # Órgão — multi-tenancy para procuradorias
        migrations.AddField(
            model_name='legalcase',
            name='organ',
            field=models.ForeignKey(
                to='organization.Organ',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True, blank=True,
                related_name='legal_cases',
                verbose_name='Órgão (Procuradoria)',
                help_text='Procuradoria responsável pelo caso',
            ),
        ),
        # Fluxo ativo
        migrations.AddField(
            model_name='legalcase',
            name='active_flow',
            field=models.OneToOneField(
                to='workflow_execution.FlowInstance',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True, blank=True,
                related_name='linked_case',
                verbose_name='Fluxo ativo',
                help_text='Instância de fluxo de trabalho em andamento para este caso',
            ),
        ),
    ]
