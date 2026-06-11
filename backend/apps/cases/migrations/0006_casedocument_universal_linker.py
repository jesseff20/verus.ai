"""
Expand CaseDocument to be a universal document linker.

Adds:
- generated_document FK (to intelligent_assistant.GeneratedDocument)
- simulation FK (to simulations.Simulation)
- observacoes TextField
- New TIPO_CHOICES entries (peca, simulacao, copilot)
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0005_add_client_model'),
        ('intelligent_assistant', '0038_unique_attachment_per_parent_type_user'),
        ('simulations', '0001_initial'),
    ]

    operations = [
        # Add FK to GeneratedDocument
        migrations.AddField(
            model_name='casedocument',
            name='linked_document',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='case_documents',
                to='intelligent_assistant.generateddocument',
                verbose_name='Documento Gerado',
            ),
        ),
        # Add FK to Simulation
        migrations.AddField(
            model_name='casedocument',
            name='simulation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='case_documents',
                to='simulations.simulation',
                verbose_name='Simulação',
            ),
        ),
        # Add observacoes
        migrations.AddField(
            model_name='casedocument',
            name='observacoes',
            field=models.TextField(blank=True, verbose_name='Observações'),
        ),
        # Update tipo choices
        migrations.AlterField(
            model_name='casedocument',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('peticao', 'Petição'),
                    ('peca', 'Peça Processual'),
                    ('decisao', 'Decisão / Sentença'),
                    ('intimacao', 'Intimação'),
                    ('contrato', 'Contrato'),
                    ('procuracao', 'Procuração'),
                    ('prova', 'Prova'),
                    ('parecer', 'Parecer'),
                    ('simulacao', 'Simulação'),
                    ('copilot', 'Análise do Copilot'),
                    ('outros', 'Outros'),
                ],
                default='outros',
                max_length=20,
                verbose_name='Tipo',
            ),
        ),
    ]
